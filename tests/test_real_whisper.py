import os
import shutil
import subprocess
from pathlib import Path

import pytest
from conftest import write_config
from fastapi.testclient import TestClient

from travel_companion.app import create_app

REAL_WHISPER_MODEL_VARIABLE = "TRAVEL_COMPANION_REAL_WHISPER_MODEL"
UNUSED_MODEL_ENDPOINT_URL = "http://127.0.0.1:9/v1/chat/completions"
DEFAULT_WHISPER_MODEL_PATH = "models/ggml-base.en.bin"

real_whisper_model_path = os.environ.get(REAL_WHISPER_MODEL_VARIABLE)

pytestmark = pytest.mark.skipif(
    not real_whisper_model_path or shutil.which("say") is None,
    reason=f"set {REAL_WHISPER_MODEL_VARIABLE} to a whisper.cpp ggml model on a Mac with whisper-cli installed",
)


def spoken_wav(text: str, wav_path: Path) -> bytes:
    subprocess.run(["say", "-o", str(wav_path), "--file-format=WAVE", "--data-format=LEI16@16000", text], check=True)
    return wav_path.read_bytes()


def test_a_spoken_question_is_transcribed_by_real_whisper_and_routed(tmp_path):
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", UNUSED_MODEL_ENDPOINT_URL)
    config_path.write_text(config_path.read_text().replace(DEFAULT_WHISPER_MODEL_PATH, real_whisper_model_path))
    audio = spoken_wav("Show my allergy card.", tmp_path / "question.wav")

    with TestClient(create_app(config_path)) as client:
        response = client.post("/api/speech", content=audio, headers={"Content-Type": "audio/wav"})

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "staff_phrase"
    assert card["intent"] == "show_staff_phrase"
