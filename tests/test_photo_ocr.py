from pathlib import Path

from fastapi.testclient import TestClient

from conftest import write_config
from travel_companion.app import create_app

SPECIMEN_PHOTOS_DIR = Path(__file__).resolve().parent.parent / "specimens" / "photos"
SPECIMEN_MENU = SPECIMEN_PHOTOS_DIR / "specimen-menu.png"
SPECIMEN_RECEIPT = SPECIMEN_PHOTOS_DIR / "specimen-receipt.png"
DEFAULT_THRESHOLD_LINE = "low_confidence_threshold = 70.0"


def uploaded_photo_card(client: TestClient, photo_path: Path) -> dict:
    response = client.post("/api/photo", files={"photo": (photo_path.name, photo_path.read_bytes(), "image/png")})
    assert response.status_code == 200
    return response.json()


def line_texts(card: dict) -> list[str]:
    return [line["text"] for line in card["lines"]]


def client_with_low_confidence_threshold(tmp_path: Path, threshold: float) -> TestClient:
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", "http://127.0.0.1:9/v1/chat/completions")
    config_text = config_path.read_text()
    assert DEFAULT_THRESHOLD_LINE in config_text
    config_path.write_text(config_text.replace(DEFAULT_THRESHOLD_LINE, f"low_confidence_threshold = {threshold}"))
    return TestClient(create_app(config_path))


def test_an_uploaded_menu_photo_returns_a_card_of_ocr_lines_with_confidence(client):
    card = uploaded_photo_card(client, SPECIMEN_MENU)

    assert card["kind"] == "ocr_lines"
    assert "Arroz con camarones" in " ".join(line_texts(card))
    assert all(0 <= line["confidence"] <= 100 for line in card["lines"])


def test_accented_spanish_on_the_specimen_menu_comes_back_correctly(client):
    menu_text = "\n".join(line_texts(uploaded_photo_card(client, SPECIMEN_MENU)))

    assert "Plátanos maduros" in menu_text
    assert "Café con leche" in menu_text
    assert "Jugo de piña" in menu_text


def test_each_ocr_line_is_shown_as_evidence_on_the_card(client):
    card = uploaded_photo_card(client, SPECIMEN_RECEIPT)

    evidence_texts = [evidence["text"] for evidence in card["evidence"]]
    assert evidence_texts == line_texts(card)
    assert "TOTAL 2.750" in evidence_texts


def test_clear_receipt_lines_are_not_flagged_at_the_default_threshold(client):
    card = uploaded_photo_card(client, SPECIMEN_RECEIPT)

    assert not any(line["low_confidence"] for line in card["lines"])
    assert "Ask staff" not in card["body"]


def test_a_menu_line_whose_colon_sign_is_misread_is_flagged_at_the_default_threshold(client):
    card = uploaded_photo_card(client, SPECIMEN_MENU)

    arroz_line = next(line for line in card["lines"] if line["text"].startswith("Arroz con camarones"))
    assert arroz_line["low_confidence"]
    assert "Ask staff" in card["body"]


def test_every_line_is_flagged_when_the_configured_threshold_is_above_any_confidence(tmp_path):
    with client_with_low_confidence_threshold(tmp_path, 100.5) as client:
        card = uploaded_photo_card(client, SPECIMEN_MENU)

    assert card["lines"]
    assert all(line["low_confidence"] for line in card["lines"])
    assert "Ask staff" in card["body"]


def test_no_line_is_flagged_when_the_configured_threshold_is_zero(tmp_path):
    with client_with_low_confidence_threshold(tmp_path, 0) as client:
        card = uploaded_photo_card(client, SPECIMEN_MENU)

    assert not any(line["low_confidence"] for line in card["lines"])


def test_a_photo_that_is_not_an_image_says_no_text_was_read(client):
    response = client.post("/api/photo", files={"photo": ("note.png", b"not an image", "image/png")})

    assert response.status_code == 422
    assert response.json()["kind"] == "unreadable_photo"


def test_an_ocr_engine_that_is_not_installed_returns_a_card_naming_the_reason(client, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "empty-bin"))

    response = client.post("/api/photo", files={"photo": (SPECIMEN_MENU.name, SPECIMEN_MENU.read_bytes(), "image/png")})

    assert response.status_code == 503
    card = response.json()
    assert card["kind"] == "ocr_unavailable"
    assert card["evidence"] == [
        {"source": "OCR engine (tesseract)", "text": "the tesseract CLI is not on PATH: brew install tesseract tesseract-lang"}
    ]
