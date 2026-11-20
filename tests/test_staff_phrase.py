import shutil

import pytest
from conftest import DEFAULT_MODEL_ENDPOINT_URL, REPO_PACKS_DIR, write_config
from fastapi.testclient import TestClient

from travel_companion.app import create_app
from travel_companion.country_pack import InvalidCountryPack

ALLERGY_SPANISH = "Tengo alergia a los crustáceos: camarón, langosta y cangrejo. Los moluscos sí los puedo comer."
DISH_QUESTION_SPANISH = "¿Este plato contiene camarón, langosta, cangrejo o caldo de mariscos?"
HOSPITAL_PHARMACY_SPANISH = "¿Dónde queda el hospital más cercano o la farmacia más cercana?"


def staff_phrase_card(client, phrase_name=None):
    params = {"phrase": phrase_name} if phrase_name else {}
    response = client.get("/api/staff-phrase", params=params)
    assert response.status_code == 200
    return response.json()


def evidence_texts(card):
    return [evidence["text"] for evidence in card["evidence"]]


def test_the_staff_phrase_card_shows_the_three_phrases_with_their_machine_checked_status(client):
    card = staff_phrase_card(client)

    assert card["kind"] == "staff_phrase"
    assert card["body"] == ALLERGY_SPANISH
    assert evidence_texts(card) == [
        f"allergy (Machine-checked): {ALLERGY_SPANISH}",
        f"dish_question (Machine-checked): {DISH_QUESTION_SPANISH}",
        f"hospital_pharmacy (Machine-checked): {HOSPITAL_PHARMACY_SPANISH}",
    ]
    assert all(evidence["source"].endswith("phrases.yaml") for evidence in card["evidence"])
    assert [phrase["english"] for phrase in card["phrases"]] == [
        "I am allergic to shellfish: shrimp, lobster, crab. Mollusks are OK.",
        "Does this dish contain shrimp, lobster, crab, or seafood broth?",
        "Where is the nearest hospital / pharmacy?",
    ]
    assert {phrase["verification"] for phrase in card["phrases"]} == {"Machine-checked"}


def test_asking_for_one_phrase_leads_the_card_with_it(client):
    card = staff_phrase_card(client, "hospital_pharmacy")

    assert card["body"] == HOSPITAL_PHARMACY_SPANISH
    assert card["phrases"][0]["name"] == "hospital_pharmacy"
    assert len(card["phrases"]) == 3


def test_asking_for_an_unknown_phrase_is_not_found(client):
    response = client.get("/api/staff-phrase", params={"phrase": "taxi"})

    assert response.status_code == 404


def client_for_pack_copy(tmp_path):
    packs_dir = tmp_path / "packs"
    shutil.copytree(REPO_PACKS_DIR / "cr", packs_dir / "cr")
    shutil.copytree(REPO_PACKS_DIR / "global", packs_dir / "global")
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", DEFAULT_MODEL_ENDPOINT_URL)
    config_path.write_text(config_path.read_text().replace(f'packs_dir = "{REPO_PACKS_DIR}"', f'packs_dir = "{packs_dir}"'))
    return packs_dir / "cr" / "phrases.yaml", lambda: TestClient(create_app(config_path))


def test_editing_a_phrase_in_the_yaml_changes_the_card(tmp_path):
    phrases_path, new_client = client_for_pack_copy(tmp_path)
    phrases_path.write_text(phrases_path.read_text().replace("o caldo de mariscos", "o salsa de mariscos"))

    with new_client() as client:
        card = staff_phrase_card(client, "dish_question")

    assert card["body"] == "¿Este plato contiene camarón, langosta, cangrejo o salsa de mariscos?"


@pytest.mark.parametrize(
    ("broken_text", "named_problem"),
    [
        ("{}\n", "phrases.yaml"),
        ("allergy:\n  english: I am allergic.\n  verification: Machine-checked\n", "allergy.spanish"),
        ("allergy:\n  english: I am allergic.\n  spanish: Tengo alergia.\n  verification: verified\n", "allergy.verification"),
    ],
)
def test_an_invalid_phrases_file_stops_the_app_naming_the_problem(tmp_path, broken_text, named_problem):
    phrases_path, new_client = client_for_pack_copy(tmp_path)
    phrases_path.write_text(broken_text)

    with pytest.raises(InvalidCountryPack) as stopped_startup:
        new_client()

    assert "phrases.yaml" in str(stopped_startup.value)
    assert named_problem in str(stopped_startup.value)


def test_the_shell_opens_the_staff_phrase_card_in_one_tap(client):
    shell = client.get("/").text

    assert 'id="staff-phrase-button"' in shell
    assert "/api/staff-phrase" in shell
