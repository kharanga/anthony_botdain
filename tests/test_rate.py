from fastapi.testclient import TestClient

from travel_companion.app import create_app


def evidence_texts(card):
    return [item["text"] for item in card["evidence"]]


def test_rate_card_starts_at_the_configured_rate(client):
    response = client.get("/api/rate")

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "rate"
    assert "510" in card["body"]
    assert "rate = 510 CRC per USD" in evidence_texts(card)


def test_changing_the_rate_returns_a_card_with_the_new_rate(client):
    response = client.put("/api/rate", json={"colones_per_dollar": 505.5})

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "rate"
    assert "505.5" in card["body"]
    assert "rate = 505.5 CRC per USD" in evidence_texts(card)


def test_changed_rate_is_read_back(client):
    client.put("/api/rate", json={"colones_per_dollar": 498})

    card = client.get("/api/rate").json()

    assert "rate = 498 CRC per USD" in evidence_texts(card)


def test_changed_rate_survives_an_app_restart(config_path):
    with TestClient(create_app(config_path)) as first_run:
        first_run.put("/api/rate", json={"colones_per_dollar": 520.25})

    with TestClient(create_app(config_path)) as second_run:
        card = second_run.get("/api/rate").json()

    assert "rate = 520.25 CRC per USD" in evidence_texts(card)


def test_status_card_shows_the_changed_rate(client):
    client.put("/api/rate", json={"colones_per_dollar": 499})

    card = client.get("/api/status").json()

    assert "rate = 499 CRC per USD" in evidence_texts(card)


def test_rate_must_be_a_positive_number(client):
    for bad_rate in [0, -3, "lots"]:
        response = client.put("/api/rate", json={"colones_per_dollar": bad_rate})
        assert response.status_code == 422

    assert "rate = 510 CRC per USD" in evidence_texts(client.get("/api/rate").json())


def test_database_file_is_created_in_the_data_folder(client, data_dir):
    client.put("/api/rate", json={"colones_per_dollar": 500})

    assert list(data_dir.glob("*.duckdb"))


def test_ui_shell_can_edit_the_rate(client):
    page = client.get("/").text

    assert "/api/rate" in page
    assert 'id="rate-form"' in page
