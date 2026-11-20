import hashlib
import os
import subprocess
from pathlib import Path

FETCH_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "fetch_whisper_model.sh"
MODEL_FILE = "ggml-base.en.bin"
GOOD_MODEL_BYTES = b"specimen whisper model bytes"


def run_fetch(models_dir: Path, source: Path) -> subprocess.CompletedProcess:
    environment = {
        **os.environ,
        "MODELS_DIR": str(models_dir),
        "WHISPER_MODEL_URL": source.as_uri(),
        "WHISPER_MODEL_SHA256": hashlib.sha256(GOOD_MODEL_BYTES).hexdigest(),
    }
    return subprocess.run(["bash", str(FETCH_SCRIPT)], env=environment, capture_output=True, text=True)


def test_a_corrupt_download_is_not_kept_and_the_next_run_fetches_again(tmp_path):
    models_dir = tmp_path / "models"
    source = tmp_path / "source" / MODEL_FILE
    source.parent.mkdir()
    source.write_bytes(b"corrupt download")

    failed_run = run_fetch(models_dir, source)

    assert failed_run.returncode != 0
    assert not (models_dir / MODEL_FILE).exists()
    assert not (models_dir / f"{MODEL_FILE}.part").exists()

    source.write_bytes(GOOD_MODEL_BYTES)
    retried_run = run_fetch(models_dir, source)

    assert retried_run.returncode == 0
    assert (models_dir / MODEL_FILE).read_bytes() == GOOD_MODEL_BYTES


def test_a_corrupt_model_left_by_an_earlier_run_is_fetched_again(tmp_path):
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / MODEL_FILE).write_bytes(b"corrupt model from an earlier run")
    source = tmp_path / "source" / MODEL_FILE
    source.parent.mkdir()
    source.write_bytes(GOOD_MODEL_BYTES)

    run = run_fetch(models_dir, source)

    assert run.returncode == 0
    assert (models_dir / MODEL_FILE).read_bytes() == GOOD_MODEL_BYTES
