from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from test_vault import vault_with_specimen_document
from travel_companion.app import create_app


@pytest.fixture
def fake_backlight_dir(tmp_path: Path) -> Path:
    device_dir = tmp_path / "backlight" / "10-0045"
    device_dir.mkdir(parents=True)
    (device_dir / "brightness").write_text("12\n")
    (device_dir / "max_brightness").write_text("31\n")
    return device_dir


@pytest.fixture
def sysfs_client(config_path: Path, fake_backlight_dir: Path):
    config_text = config_path.read_text()
    config_text = config_text.replace('brightness_backend = "recording"', 'brightness_backend = "sysfs"')
    config_path.write_text(config_text.replace('backlight_dir = ""', f'backlight_dir = "{fake_backlight_dir}"'))
    with TestClient(create_app(config_path)) as client:
        yield client


def test_sysfs_backlight_goes_to_maximum_and_back(sysfs_client, fake_backlight_dir: Path):
    document_id = vault_with_specimen_document(sysfs_client)["documents"][0]["id"]

    sysfs_client.post(f"/api/vault/documents/{document_id}/full-screen")
    during = sysfs_client.get("/api/display/brightness").json()
    level_on_disk_during = (fake_backlight_dir / "brightness").read_text().strip()
    closed = sysfs_client.post("/api/vault/full-screen/close").json()

    assert during["level"] == 31
    assert level_on_disk_during == "31"
    assert closed["level"] == 12
    assert (fake_backlight_dir / "brightness").read_text().strip() == "12"
    assert str(fake_backlight_dir) in closed["evidence"][0]["source"]
