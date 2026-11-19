import os

import pytest
from conftest import write_config
from fastapi.testclient import TestClient

from travel_companion.app import create_app

REAL_MODEL_URL_VARIABLE = "TRAVEL_COMPANION_REAL_MODEL_URL"

real_model_endpoint_url = os.environ.get(REAL_MODEL_URL_VARIABLE)

pytestmark = pytest.mark.skipif(
    not real_model_endpoint_url,
    reason=f"set {REAL_MODEL_URL_VARIABLE} to a running llama-server chat-completions URL",
)


@pytest.fixture
def real_model_client(tmp_path):
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", real_model_endpoint_url)
    with TestClient(create_app(config_path)) as test_client:
        yield test_client


def test_ask_returns_an_answer_card_written_by_the_real_model(real_model_client):
    response = real_model_client.post(
        "/api/ask", json={"question": "In one word, what language is spoken in Costa Rica?"}
    )

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "answer"
    assert "spanish" in card["body"].lower()
    assert card["evidence"][0]["source"] == real_model_endpoint_url


def test_a_long_question_still_fits_the_real_model_context(real_model_client):
    response = real_model_client.post(
        "/api/ask", json={"question": "Where can I buy a bus ticket in San José? " * 400}
    )

    assert response.status_code == 200
    assert response.json()["kind"] == "answer"
