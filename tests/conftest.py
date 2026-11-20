from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fake_model_server import FakeModelServer
from travel_companion.app import create_app

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.toml"
REPO_PACKS_DIR = Path(__file__).resolve().parent.parent / "packs"
SPECIMEN_PACKS_DIR = Path(__file__).resolve().parent / "packs"
DEFAULT_MODEL_ENDPOINT_URL = "http://127.0.0.1:8080/v1/chat/completions"


def write_config(config_path: Path, data_dir: Path, model_endpoint_url: str) -> None:
    default_text = DEFAULT_CONFIG_PATH.read_text()
    config_text = default_text.replace('data_dir = "data"', f'data_dir = "{data_dir}"')
    config_text = config_text.replace('packs_dir = "packs"', f'packs_dir = "{REPO_PACKS_DIR}"')
    config_path.write_text(config_text.replace(DEFAULT_MODEL_ENDPOINT_URL, model_endpoint_url))


@pytest.fixture
def fake_model():
    server = FakeModelServer().start()
    yield server
    server.stop()


def model_endpoint_url_for(request) -> str:
    if "fake_model" in request.fixturenames:
        return request.getfixturevalue("fake_model").endpoint_url
    return DEFAULT_MODEL_ENDPOINT_URL


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def config_path(request, tmp_path: Path, data_dir: Path) -> Path:
    path = tmp_path / "config.toml"
    write_config(path, data_dir, model_endpoint_url_for(request))
    return path


@pytest.fixture
def client(config_path: Path):
    with TestClient(create_app(config_path)) as test_client:
        yield test_client
