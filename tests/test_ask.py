from conftest import write_config
from fake_model_server import FakeModelServer
from fastapi.testclient import TestClient

from travel_companion.app import create_app


def test_ask_returns_an_answer_card_whose_text_comes_from_the_model(client, fake_model):
    fake_model.reply_with("Pura vida means hello, thanks and all good.")

    response = client.post("/api/ask", json={"question": "What does pura vida mean?"})

    assert response.status_code == 200
    card = response.json()
    assert card["kind"] == "answer"
    assert card["body"] == "Pura vida means hello, thanks and all good."
    assert len(card["evidence"]) > 0


def user_message_contents(chat_request):
    return [message["content"] for message in chat_request["messages"] if message["role"] == "user"]


def test_ask_sends_the_question_to_the_endpoint_named_in_config(client, fake_model):
    fake_model.reply_with("Yes.")

    client.post("/api/ask", json={"question": "Is tap water fine in San José?"})

    assert len(fake_model.received_requests) == 1
    assert user_message_contents(fake_model.last_request) == ["Is tap water fine in San José?"]


MODEL_CONTEXT_TOKENS = 2048
WORST_CASE_BYTES_PER_TOKEN_FOR_PROSE = 2


def all_message_contents(chat_request):
    return "".join(message["content"] for message in chat_request["messages"])


def test_a_long_question_is_trimmed_so_prompt_and_reply_fit_the_context(client, fake_model):
    fake_model.reply_with("That is a long question.")

    response = client.post("/api/ask", json={"question": "Where can I buy a bus ticket? " * 400})

    assert response.json()["body"] == "That is a long question."
    sent_request = fake_model.last_request
    prompt_bytes = len(all_message_contents(sent_request).encode())
    reply_tokens = sent_request["max_tokens"]
    assert prompt_bytes / WORST_CASE_BYTES_PER_TOKEN_FOR_PROSE + reply_tokens <= MODEL_CONTEXT_TOKENS


def test_digits_count_as_one_token_each_when_trimming(client, fake_model):
    fake_model.reply_with("Those are many digits.")

    client.post("/api/ask", json={"question": "7" * 10_000})

    sent_request = fake_model.last_request
    sent_digits = sum(character.isdigit() for character in all_message_contents(sent_request))
    assert sent_digits + sent_request["max_tokens"] <= MODEL_CONTEXT_TOKENS


def test_ask_says_the_model_is_unavailable_when_the_endpoint_fails(client, fake_model):
    fake_model.fail_with(503)

    response = client.post("/api/ask", json={"question": "What does pura vida mean?"})

    assert response.status_code == 503
    card = response.json()
    assert card["kind"] == "model_unavailable"
    assert card["evidence"][0]["source"] == fake_model.endpoint_url


def test_ask_says_the_model_is_unavailable_when_nothing_listens_at_the_endpoint(tmp_path):
    stopped_server = FakeModelServer().start()
    stopped_server.stop()
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", stopped_server.endpoint_url)

    with TestClient(create_app(config_path)) as client:
        response = client.post("/api/ask", json={"question": "What does pura vida mean?"})

    assert response.status_code == 503
    assert response.json()["kind"] == "model_unavailable"


def asked_card_status_and_kind(client):
    response = client.post("/api/ask", json={"question": "What does pura vida mean?"})
    return response.status_code, response.json()["kind"]


def test_a_null_reply_content_gives_the_model_unavailable_card(client, fake_model):
    fake_model.reply_with_message_content(None)

    assert asked_card_status_and_kind(client) == (503, "model_unavailable")


def test_a_non_text_reply_content_gives_the_model_unavailable_card(client, fake_model):
    fake_model.reply_with_message_content([{"type": "text", "text": "hi"}])

    assert asked_card_status_and_kind(client) == (503, "model_unavailable")


def test_a_reply_that_is_not_utf8_gives_the_model_unavailable_card(client, fake_model):
    fake_model.reply_with_raw_body(b"\xff\xfe\x00not json")

    assert asked_card_status_and_kind(client) == (503, "model_unavailable")
