import base64
from pathlib import Path

from fastapi.testclient import TestClient

from travel_companion.app import create_app

SPECIMEN_PHOTO_PATH = Path(__file__).resolve().parent.parent / "specimens" / "vault" / "specimen-boarding-pass.png"
SPECIMEN_LABEL = "SPECIMEN boarding pass SJO-LIR"
PIN = "482913"
WRONG_PIN = "482914"


def specimen_photo() -> bytes:
    return SPECIMEN_PHOTO_PATH.read_bytes()


def add_specimen_document(client):
    return client.post(
        "/api/vault/documents",
        json={
            "label": SPECIMEN_LABEL,
            "content_type": "image/png",
            "photo_base64": base64.b64encode(specimen_photo()).decode(),
        },
    )


def vault_with_specimen_document(client):
    client.post("/api/vault/pin", json={"pin": PIN})
    return add_specimen_document(client).json()


def test_first_use_asks_for_a_six_digit_pin(client):
    response = client.get("/api/vault")

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "vault"
    assert card["vault_state"] == "needs_pin"
    assert "6-digit PIN" in card["body"]
    assert card["documents"] == []


def test_setting_a_pin_opens_an_empty_vault(client):
    response = client.post("/api/vault/pin", json={"pin": "482913"})

    assert response.status_code == 200
    card = response.json()
    assert card["vault_state"] == "unlocked"
    assert card["documents"] == []


def test_pin_must_be_six_digits(client):
    for bad_pin in ["12345", "1234567", "12345a", "", 482913]:
        response = client.post("/api/vault/pin", json={"pin": bad_pin})
        assert response.status_code == 422

    assert client.get("/api/vault").json()["vault_state"] == "needs_pin"


def test_pin_cannot_be_set_twice(client):
    client.post("/api/vault/pin", json={"pin": "482913"})

    response = client.post("/api/vault/pin", json={"pin": "111111"})

    assert response.status_code == 409


def test_added_document_shows_in_a_card(client):
    client.post("/api/vault/pin", json={"pin": PIN})

    response = add_specimen_document(client)

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "vault"
    assert card["vault_state"] == "unlocked"
    assert card["title"] == SPECIMEN_LABEL
    assert card["photo_url"]
    assert client.get(card["photo_url"]).content == specimen_photo()


def test_unlocked_vault_lists_the_added_document(client):
    vault_with_specimen_document(client)

    card = client.get("/api/vault").json()

    assert [document["label"] for document in card["documents"]] == [SPECIMEN_LABEL]


def test_locked_vault_returns_no_documents(client):
    added_card = vault_with_specimen_document(client)
    document_id = added_card["documents"][0]["id"]

    lock_card = client.post("/api/vault/lock").json()
    vault_card = client.get("/api/vault").json()
    document_response = client.get(f"/api/vault/documents/{document_id}")
    photo_response = client.get(added_card["photo_url"])

    assert lock_card["vault_state"] == "locked"
    assert vault_card["vault_state"] == "locked"
    assert vault_card["documents"] == []
    assert SPECIMEN_LABEL not in str(vault_card)
    assert document_response.status_code == 423
    assert SPECIMEN_LABEL not in document_response.text
    assert photo_response.status_code == 423
    assert specimen_photo() not in photo_response.content


def test_locked_vault_does_not_accept_new_documents(client):
    vault_with_specimen_document(client)
    client.post("/api/vault/lock")

    response = add_specimen_document(client)

    assert response.status_code == 423


def test_right_pin_unlocks_the_vault_and_shows_the_document(client):
    added_card = vault_with_specimen_document(client)
    client.post("/api/vault/lock")

    unlock_response = client.post("/api/vault/unlock", json={"pin": PIN})
    document_id = unlock_response.json()["documents"][0]["id"]
    document_card = client.get(f"/api/vault/documents/{document_id}").json()

    assert unlock_response.status_code == 200
    assert unlock_response.json()["vault_state"] == "unlocked"
    assert document_card["title"] == SPECIMEN_LABEL
    assert client.get(document_card["photo_url"]).content == specimen_photo()
    assert document_card["photo_url"] == added_card["photo_url"]


def test_wrong_pin_does_not_unlock_the_vault(client):
    added_card = vault_with_specimen_document(client)
    client.post("/api/vault/lock")

    unlock_response = client.post("/api/vault/unlock", json={"pin": WRONG_PIN})

    assert unlock_response.status_code == 401
    assert SPECIMEN_LABEL not in unlock_response.text
    assert client.get("/api/vault").json()["vault_state"] == "locked"
    assert client.get(added_card["photo_url"]).status_code == 423


def test_vault_starts_locked_after_a_restart_and_the_pin_still_opens_it(config_path):
    with TestClient(create_app(config_path)) as first_run:
        vault_with_specimen_document(first_run)

    with TestClient(create_app(config_path)) as second_run:
        locked_state = second_run.get("/api/vault").json()["vault_state"]
        unlocked = second_run.post("/api/vault/unlock", json={"pin": PIN}).json()

    assert locked_state == "locked"
    assert [document["label"] for document in unlocked["documents"]] == [SPECIMEN_LABEL]


def every_file_under(folder: Path) -> list[Path]:
    return [path for path in folder.rglob("*") if path.is_file()]


def test_no_plaintext_document_is_on_disk(config_path, data_dir):
    photo = specimen_photo()
    with TestClient(create_app(config_path)) as client:
        vault_with_specimen_document(client)
        files_while_running = {path: path.read_bytes() for path in every_file_under(data_dir)}
    files_after_shutdown = {path: path.read_bytes() for path in every_file_under(data_dir)}

    assert files_while_running and files_after_shutdown
    for contents in [*files_while_running.values(), *files_after_shutdown.values()]:
        assert photo not in contents
        assert photo[64:128] not in contents
        assert base64.b64encode(photo)[64:128] not in contents
        assert SPECIMEN_LABEL.encode() not in contents
        assert b"SPECIMEN BOARDING PASS" not in contents
        assert PIN.encode() not in contents


def test_ui_shell_links_to_the_vault(client):
    assert "/vault" in client.get("/").text


def test_vault_page_asks_for_the_pin_and_adds_documents(client):
    response = client.get("/vault")

    assert response.status_code == 200
    assert "/api/vault" in response.text
    assert 'id="pin-form"' in response.text
    assert 'id="add-document-form"' in response.text


def test_an_svg_document_is_refused(client):
    client.post("/api/vault/pin", json={"pin": PIN})
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'

    response = client.post(
        "/api/vault/documents",
        json={"label": "Not a photo", "content_type": "image/svg+xml", "photo_base64": base64.b64encode(svg).decode()},
    )

    assert response.status_code == 422
    assert client.get("/api/vault").json()["documents"] == []


def test_a_document_photo_is_served_so_it_cannot_run_script(client):
    photo_url = vault_with_specimen_document(client)["photo_url"]

    response = client.get(photo_url)

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"] == "sandbox"

