from fastapi.testclient import TestClient

from test_vault import PIN, SPECIMEN_LABEL, add_specimen_document, vault_with_specimen_document
from travel_companion.app import create_app

TWO_MINUTES = 120


class FakeClock:
    def __init__(self) -> None:
        self.seconds = 1000.0

    def __call__(self) -> float:
        return self.seconds

    def advance(self, seconds: float) -> None:
        self.seconds += seconds


def clocked_client(config_path):
    clock = FakeClock()
    return TestClient(create_app(config_path, clock=clock)), clock


def test_vault_locks_after_two_minutes_of_no_use(config_path):
    client, clock = clocked_client(config_path)
    with client:
        added_card = vault_with_specimen_document(client)

        clock.advance(TWO_MINUTES)
        vault_card = client.get("/api/vault").json()
        photo_response = client.get(added_card["photo_url"])

    assert vault_card["vault_state"] == "locked"
    assert vault_card["documents"] == []
    assert SPECIMEN_LABEL not in str(vault_card)
    assert photo_response.status_code == 423


def test_vault_stays_open_just_under_two_minutes(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)

        clock.advance(TWO_MINUTES - 1)
        vault_card = client.get("/api/vault").json()

    assert vault_card["vault_state"] == "unlocked"
    assert [document["label"] for document in vault_card["documents"]] == [SPECIMEN_LABEL]


def test_opening_a_document_resets_the_timer(config_path):
    client, clock = clocked_client(config_path)
    with client:
        added_card = vault_with_specimen_document(client)
        document_id = added_card["documents"][0]["id"]

        clock.advance(TWO_MINUTES - 10)
        client.get(f"/api/vault/documents/{document_id}")
        clock.advance(TWO_MINUTES - 10)
        document_response = client.get(f"/api/vault/documents/{document_id}")

    assert document_response.status_code == 200
    assert document_response.json()["title"] == SPECIMEN_LABEL


def test_tapping_the_vault_screen_resets_the_timer(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)

        clock.advance(TWO_MINUTES - 10)
        activity_card = client.post("/api/vault/activity").json()
        clock.advance(TWO_MINUTES - 10)
        vault_card = client.get("/api/vault").json()

    assert activity_card["vault_state"] == "unlocked"
    assert vault_card["vault_state"] == "unlocked"


def test_activity_after_the_lock_does_not_reopen_the_vault(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)

        clock.advance(TWO_MINUTES)
        activity_card = client.post("/api/vault/activity").json()
        adding_response = add_specimen_document(client)

    assert activity_card["vault_state"] == "locked"
    assert activity_card["documents"] == []
    assert adding_response.status_code == 423


def test_checking_the_lock_state_is_not_use(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)

        clock.advance(TWO_MINUTES - 10)
        still_open = client.get("/api/vault/state").json()
        clock.advance(10)
        now_locked = client.get("/api/vault/state").json()

    assert still_open["vault_state"] == "unlocked"
    assert now_locked["vault_state"] == "locked"
    assert now_locked["documents"] == []


def test_unlocked_card_tells_the_ui_how_long_until_it_locks(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)
        clock.advance(30)
        state_card = client.get("/api/vault/state").json()
        vault_card = client.get("/api/vault").json()

    assert state_card["locks_in_seconds"] == 90
    assert vault_card["locks_in_seconds"] == 120


def test_locked_card_has_no_lock_countdown(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)
        clock.advance(TWO_MINUTES)
        state_card = client.get("/api/vault/state").json()

    assert state_card["locks_in_seconds"] is None


def test_pin_reopens_the_vault_after_an_auto_lock(config_path):
    client, clock = clocked_client(config_path)
    with client:
        vault_with_specimen_document(client)
        clock.advance(TWO_MINUTES)
        client.get("/api/vault")

        unlocked = client.post("/api/vault/unlock", json={"pin": PIN}).json()
        clock.advance(TWO_MINUTES - 1)
        still_open = client.get("/api/vault/state").json()

    assert unlocked["vault_state"] == "unlocked"
    assert still_open["vault_state"] == "unlocked"


def test_vault_page_reports_taps_and_returns_to_the_pin_screen_when_locked(client):
    page = client.get("/vault").text

    assert "/api/vault/activity" in page
    assert "/api/vault/state" in page
    assert "locks_in_seconds" in page
