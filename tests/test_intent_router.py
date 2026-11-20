import tomllib
from pathlib import Path

import pytest

INTENT_SAMPLES_PATH = Path(__file__).resolve().parent.parent / "specimens" / "intent_samples.toml"
INTENT_SAMPLES = tomllib.loads(INTENT_SAMPLES_PATH.read_text())["sample"]


def routed_card(client, transcript):
    response = client.post("/api/transcript", json={"transcript": transcript})
    assert response.status_code == 200
    return response.json()


def test_show_my_allergy_card_routes_to_the_staff_phrase_intent(client):
    card = routed_card(client, "show my allergy card")

    assert card["kind"] == "intent"
    assert card["intent"] == "show_staff_phrase"
    assert card["details"] == {"phrase": "allergy"}
    assert {"source": "transcript", "text": "show my allergy card"} in card["evidence"]


SIX_INTENT_TITLES = [
    "Show the staff phrase",
    "Allergen question about the last menu",
    "Guide question",
    "Add an expense",
    "Spending question",
    "Open the vault",
]


def test_an_unmatched_transcript_says_i_cant_do_that_yet_and_lists_the_six_intents(client):
    card = routed_card(client, "play some music")

    assert card["kind"] == "unsupported_intent"
    assert card["title"] == "I can't do that yet"
    assert card["intent"] is None
    for title in SIX_INTENT_TITLES:
        assert title in card["body"]



def test_fifty_sample_questions_are_committed():
    assert len(INTENT_SAMPLES) == 50


@pytest.mark.parametrize("sample", INTENT_SAMPLES, ids=[sample["transcript"] for sample in INTENT_SAMPLES])
def test_each_sample_question_routes_to_its_intent_with_its_details(client, sample):
    card = routed_card(client, sample["transcript"])

    assert card["intent"] == sample.get("intent")
    assert card["details"] == sample.get("details", {})


def test_no_model_call_is_made_when_a_rule_matches(client, fake_model):
    matched_samples = [sample for sample in INTENT_SAMPLES if "intent" in sample]

    for sample in matched_samples:
        assert routed_card(client, sample["transcript"])["kind"] == "intent"

    assert fake_model.received_requests == []


def test_an_intent_card_names_the_intent_and_spells_out_its_details(client):
    card = routed_card(client, "I spent five mil on a taxi")

    assert card["title"] == "Add an expense"
    assert "5000" in card["body"]
    assert "transport" in card["body"]
