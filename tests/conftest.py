from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from travel_companion.app import create_app

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.toml"


def write_config_with_data_dir(config_path: Path, data_dir: Path) -> None:
    default_text = DEFAULT_CONFIG_PATH.read_text()
    config_path.write_text(default_text.replace('data_dir = "data"', f'data_dir = "{data_dir}"'))


@pytest.fixture
def data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"


@pytest.fixture
def config_path(tmp_path: Path, data_dir: Path) -> Path:
    path = tmp_path / "config.toml"
    write_config_with_data_dir(path, data_dir)
    return path


@pytest.fixture
def client(config_path: Path):
    with TestClient(create_app(config_path)) as test_client:
        yield test_client
