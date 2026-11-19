import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_booting_creates_the_configured_data_folder(client, data_dir):
    assert data_dir.is_dir()


def test_data_folder_is_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", "data/expenses.duckdb"], cwd=REPO_ROOT
    )
    assert result.returncode == 0


def test_ui_shell_loads_and_asks_for_the_status_card(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "/api/status" in response.text
