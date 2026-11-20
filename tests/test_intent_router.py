import tomllib
from pathlib import Path

import pytest

INTENT_SAMPLES_PATH = Path(__file__).resolve().parent.parent / "specimens" / "intent_samples.toml"
INTENT_SAMPLES = tomllib.loads(INTENT_SAMPLES_PATH.read_text())["sample"]


def routed_card(client, transcript):
    response = client.post("/api/transcript", json={"transcript": transcript})
    assert response.status_code == 200
    return response.json()


ALLERGY_SPANISH = "Tengo alergia a los crustáceos: camarón, langosta y cangrejo. Los moluscos sí los puedo comer."
HOSPITAL_PHARMACY_SPANISH = "¿Dónde queda el hospital más cercano o la farmacia más cercana?"


def test_show_my_allergy_card_returns_the_staff_phrase_card_led_by_the_allergy_phrase(client):
    card = routed_card(client, "show my allergy card")

    assert card["kind"] == "staff_phrase"
    assert card["intent"] == "show_staff_phrase"
    assert card["details"] == {"phrase": "allergy"}
    assert card["body"] == ALLERGY_SPANISH
    assert [phrase["name"] for phrase in card["phrases"]] == ["allergy", "dish_question", "hospital_pharmacy"]
    assert card["evidence"][0]["text"] == f"allergy (Machine-checked): {ALLERGY_SPANISH}"
    assert card["evidence"][0]["source"].endswith("phrases.yaml")
    assert {"source": "transcript", "text": "show my allergy card"} in card["evidence"]


STAFF_PHRASE_SAMPLES = [sample for sample in INTENT_SAMPLES if sample.get("intent") == "show_staff_phrase"]


@pytest.mark.parametrize("sample", STAFF_PHRASE_SAMPLES, ids=[sample["transcript"] for sample in STAFF_PHRASE_SAMPLES])
def test_each_staff_phrase_sample_returns_the_staff_phrase_card_led_by_its_phrase(client, sample):
    card = routed_card(client, sample["transcript"])

    assert card["kind"] == "staff_phrase"
    assert card["phrases"][0]["name"] == sample["details"]["phrase"]
    assert card["body"] == card["phrases"][0]["spanish"]


def test_show_the_hospital_phrase_leads_the_card_with_the_hospital_phrase(client):
    card = routed_card(client, "show the hospital phrase")

    assert card["body"] == HOSPITAL_PHARMACY_SPANISH


def test_the_shell_opens_a_routed_staff_phrase_card_in_the_full_screen_phrase_view(client):
    shell = client.get("/").text

    assert 'id="transcript-form"' in shell
    assert "/api/transcript" in shell
    assert 'card.kind === "staff_phrase"' in shell


SIX_INTENT_TITLES = [
    "Show the staff phrase",
    "Allergen question about the last menu",
    "Guide question",
    "Add an expense",
    "Spending question",
    "Open the vault",
]


def test_an_unmatched_transcript_says_i_cant_do_that_yet_and_lists_the_six_intents(client, fake_model):
    card = routed_card(client, "play some music")

    assert card["kind"] == "unsupported_intent"
    assert card["title"] == "I can't do that yet"
    assert card["intent"] is None
    for title in SIX_INTENT_TITLES:
        assert title in card["body"]



def test_fifty_sample_questions_are_committed():
    assert len(INTENT_SAMPLES) == 50


@pytest.mark.parametrize("sample", INTENT_SAMPLES, ids=[sample["transcript"] for sample in INTENT_SAMPLES])
def test_each_sample_question_routes_to_its_intent_with_its_details(client, fake_model, sample):
    card = routed_card(client, sample["transcript"])

    assert card["intent"] == sample.get("intent")
    assert card["details"] == sample.get("details", {})


def test_no_model_call_is_made_when_a_rule_matches(client, fake_model):
    matched_samples = [sample for sample in INTENT_SAMPLES if "intent" in sample]

    for sample in matched_samples:
        assert routed_card(client, sample["transcript"])["intent"] == sample["intent"]

    assert fake_model.received_requests == []


def test_an_intent_card_names_the_intent_and_spells_out_its_details(client):
    card = routed_card(client, "I spent five mil on a taxi")

    assert card["title"] == "Add an expense"
    assert "5000" in card["body"]
    assert "transport" in card["body"]
