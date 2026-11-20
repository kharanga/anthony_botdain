import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from conftest import write_config
from travel_companion.app import create_app

pytestmark = pytest.mark.skipif(
    not os.environ.get("TRAVEL_COMPANION_PADDLEOCR"), reason="set TRAVEL_COMPANION_PADDLEOCR=1 to run real PaddleOCR"
)

SPECIMEN_MENU = Path(__file__).resolve().parent.parent / "specimens" / "photos" / "specimen-menu.png"


@pytest.fixture
def paddleocr_client(tmp_path: Path):
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", "http://127.0.0.1:9/v1/chat/completions")
    config_text = config_path.read_text()
    assert 'engine = "tesseract"' in config_text
    config_path.write_text(config_text.replace('engine = "tesseract"', 'engine = "paddleocr"'))
    with TestClient(create_app(config_path)) as client:
        yield client


def test_paddleocr_reads_accented_spanish_lines_from_the_specimen_menu(paddleocr_client):
    response = paddleocr_client.post(
        "/api/photo", files={"photo": (SPECIMEN_MENU.name, SPECIMEN_MENU.read_bytes(), "image/png")}
    )

    card = response.json()
    line_texts = [line["text"] for line in card["lines"]]
    assert card["kind"] == "ocr_lines"
    assert any(evidence["source"] == "OCR line (paddleocr)" for evidence in card["evidence"])
    assert any(text.startswith("Plátanos maduros") for text in line_texts)
    assert any(text.startswith("Jugo de piña") for text in line_texts)
    assert all(0 <= line["confidence"] <= 100 for line in card["lines"])
