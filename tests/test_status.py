def test_status_returns_an_answer_card_with_evidence(client):
    response = client.get("/api/status")

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "status"
    assert card["title"]
    assert card["body"]
    assert len(card["evidence"]) > 0
    assert all(item["source"] and item["text"] for item in card["evidence"])


def evidence_texts(card):
    return [item["text"] for item in card["evidence"]]


def test_status_evidence_shows_the_default_trip_config(client):
    texts = evidence_texts(client.get("/api/status").json())

    assert "country = cr" in texts
    assert "active_allergens = shellfish" in texts
    assert "home_currency = USD" in texts
    assert "rate = 510 CRC per USD" in texts
    assert "model.endpoint_url = http://127.0.0.1:8080/v1/chat/completions" in texts


def test_status_reads_values_from_the_given_config_file(tmp_path):
    from fastapi.testclient import TestClient

    from travel_companion.app import create_app

    config_path = tmp_path / "other.toml"
    config_path.write_text(
        'country = "cr"\n'
        'active_allergens = ["shellfish", "peanut"]\n'
        'home_currency = "USD"\n'
        "rate = 25000\n"
        f'data_dir = "{tmp_path / "data"}"\n'
        "[model]\n"
        'endpoint_url = "http://127.0.0.1:9999/v1/chat/completions"\n'
    )

    with TestClient(create_app(config_path)) as client:
        texts = evidence_texts(client.get("/api/status").json())

    assert "active_allergens = shellfish, peanut" in texts
    assert "rate = 25000 CRC per USD" in texts
    assert "model.endpoint_url = http://127.0.0.1:9999/v1/chat/completions" in texts
