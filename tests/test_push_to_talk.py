import pytest
from fastapi.testclient import TestClient

from travel_companion.app import create_app

RECORDED_AUDIO = b"RIFF fake push-to-talk recording"


def transcriber_hearing(transcript):
    heard_recordings = []

    def transcribe(audio: bytes) -> str:
        heard_recordings.append(audio)
        return transcript

    transcribe.heard_recordings = heard_recordings
    return transcribe


def spoken_card(config_path, transcriber=None):
    with TestClient(create_app(config_path, transcriber=transcriber)) as client:
        response = client.post("/api/speech", content=RECORDED_AUDIO, headers={"Content-Type": "audio/wav"})
    assert response.status_code == 200
    return response.json()


def test_releasing_push_to_talk_returns_the_routed_card_for_what_was_said(config_path):
    transcriber = transcriber_hearing(" I spent 5 mil on a taxi.")

    card = spoken_card(config_path, transcriber)

    assert transcriber.heard_recordings == [RECORDED_AUDIO]
    assert card["kind"] == "intent"
    assert card["intent"] == "add_expense"
    assert {"source": "transcript", "text": "I spent 5 mil on a taxi."} in card["evidence"]


def test_saying_show_my_allergy_card_returns_the_staff_phrase_card(config_path):
    card = spoken_card(config_path, transcriber_hearing(" Show my allergy card."))

    assert card["kind"] == "staff_phrase"
    assert card["intent"] == "show_staff_phrase"
    assert card["phrases"][0]["name"] == "allergy"
    assert {"source": "transcript", "text": "Show my allergy card."} in card["evidence"]


def test_whisper_writing_number_four_as_hash_four_still_finds_dish_number_four(config_path):
    card = spoken_card(config_path, transcriber_hearing(" Does #4 have Lobster?"))

    assert card["intent"] == "menu_allergen_question"
    assert card["details"] == {"dish_number": "4", "ingredient": "lobster"}


def test_a_spoken_paraphrase_the_rules_miss_is_routed_by_the_model(config_path, fake_model):
    fake_model.reply_with("spending_question")

    card = spoken_card(config_path, transcriber_hearing(" Tally up my outgoings."))

    assert card["intent"] == "spending_question"
    assert {"source": "intent model", "text": "model label: spending_question"} in card["evidence"]


def test_the_home_screen_has_a_push_to_talk_control_that_sends_speech(client):
    page = client.get("/").text

    assert 'id="push-to-talk"' in page
    assert "/api/speech" in page


def test_silence_returns_a_card_asking_to_hold_the_button_and_speak(config_path):
    card = spoken_card(config_path, transcriber_hearing(" [BLANK_AUDIO]\n"))

    assert card["kind"] == "nothing_heard"
    assert card["title"] == "I didn't catch that"


@pytest.mark.parametrize("whisper_output", [" [ Silence ]\n", " [Music]\n", " (wind blowing)\n", " [BLANK_AUDIO] (SILENCE)\n"])
def test_any_bracketed_non_speech_marker_alone_returns_the_nothing_heard_card(config_path, whisper_output):
    card = spoken_card(config_path, transcriber_hearing(whisper_output))

    assert card["kind"] == "nothing_heard"


def test_a_non_speech_marker_is_dropped_from_a_spoken_question(config_path):
    card = spoken_card(config_path, transcriber_hearing(" [Music] Show my allergy card. (laughs)"))

    assert card["kind"] == "staff_phrase"
    assert {"source": "transcript", "text": "Show my allergy card."} in card["evidence"]


def test_a_missing_whisper_model_returns_a_card_saying_speech_to_text_is_not_available(config_path, tmp_path):
    missing_model_path = tmp_path / "models" / "ggml-base.en.bin"
    config_path.write_text(config_path.read_text().replace("models/ggml-base.en.bin", str(missing_model_path)))

    card = spoken_card(config_path)

    assert card["kind"] == "speech_unavailable"
    assert str(missing_model_path) in card["evidence"][0]["text"]
