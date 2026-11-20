from conftest import write_config
from fastapi.testclient import TestClient
from test_intent_router import routed_card

from travel_companion.app import create_app


def user_message_text(chat_request):
    return "".join(message["content"] for message in chat_request["messages"] if message["role"] == "user")


def test_a_paraphrase_the_rules_miss_is_routed_by_the_model(client, fake_model):
    fake_model.reply_with("spending_question")

    card = routed_card(client, "tally up my outgoings")

    assert card["kind"] == "intent"
    assert card["intent"] == "spending_question"
    assert card["title"] == "Spending question"
    assert {"source": "transcript", "text": "tally up my outgoings"} in card["evidence"]
    assert {"source": "intent model", "text": "model label: spending_question"} in card["evidence"]
    assert "tally up my outgoings" in user_message_text(fake_model.last_request)


def assert_i_cant_do_that_yet(card):
    assert card["kind"] == "unsupported_intent"
    assert card["title"] == "I can't do that yet"
    assert card["intent"] is None
    assert "Open the vault" in card["body"]


def test_an_invented_label_from_the_model_gives_i_cant_do_that_yet(client, fake_model):
    fake_model.reply_with("play_music")

    assert_i_cant_do_that_yet(routed_card(client, "put on some salsa"))


def test_a_sentence_instead_of_a_label_gives_i_cant_do_that_yet(client, fake_model):
    fake_model.reply_with("I think this is a spending_question or maybe add_expense.")

    assert_i_cant_do_that_yet(routed_card(client, "tally up my outgoings"))


def test_the_none_label_gives_i_cant_do_that_yet(client, fake_model):
    fake_model.reply_with("none")

    assert_i_cant_do_that_yet(routed_card(client, "set a timer for ten minutes"))


def test_a_down_model_gives_i_cant_do_that_yet_not_an_error(client, fake_model):
    fake_model.fail_with(503)

    assert_i_cant_do_that_yet(routed_card(client, "tally up my outgoings"))


UNREACHABLE_MODEL_ENDPOINT_URL = "http://127.0.0.1:9/v1/chat/completions"


def test_an_unreachable_model_gives_i_cant_do_that_yet_not_an_error(tmp_path):
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", UNREACHABLE_MODEL_ENDPOINT_URL)

    with TestClient(create_app(config_path)) as unreachable_model_client:
        assert_i_cant_do_that_yet(routed_card(unreachable_model_client, "tally up my outgoings"))


MODEL_CONTEXT_TOKENS = 2048
WORST_CASE_BYTES_PER_TOKEN_FOR_PROSE = 2


def test_the_routing_prompt_fits_the_2048_token_budget(client, fake_model):
    fake_model.reply_with("none")

    routed_card(client, "um so basically the thing I wanted " * 300)

    sent_request = fake_model.last_request
    prompt_bytes = len("".join(message["content"] for message in sent_request["messages"]).encode())
    assert prompt_bytes / WORST_CASE_BYTES_PER_TOKEN_FOR_PROSE + sent_request["max_tokens"] <= MODEL_CONTEXT_TOKENS


def test_a_question_that_names_no_place_or_travel_topic_goes_to_the_model(client, fake_model):
    fake_model.reply_with("none")

    assert_i_cant_do_that_yet(routed_card(client, "what's the meaning of life?"))
    assert len(fake_model.received_requests) == 1


def test_a_question_that_names_a_place_stays_a_guide_question_without_the_model(client, fake_model):
    card = routed_card(client, "what should I pack for Monteverde?")

    assert card["intent"] == "guide_question"
    assert fake_model.received_requests == []


def test_a_model_routed_expense_keeps_the_amount_from_the_transcript(client, fake_model):
    fake_model.reply_with("add_expense")

    card = routed_card(client, "put down 12 dollars for lunch")

    assert card["intent"] == "add_expense"
    assert card["details"] == {"amount": "12", "currency": "USD", "category": "food"}
