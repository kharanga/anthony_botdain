import shutil

import pytest
from conftest import DEFAULT_MODEL_ENDPOINT_URL, REPO_PACKS_DIR, SPECIMEN_PACKS_DIR, write_config
from fastapi.testclient import TestClient

from travel_companion.app import create_app
from travel_companion.country_pack import InvalidCountryPack
from travel_companion.text_folding import contains_phrase_ignoring_accents_and_case


def checked_card(client, menu_line_text):
    response = client.post("/api/menu-line", json={"text": menu_line_text})
    assert response.status_code == 200
    return response.json()


def evidence_texts(card):
    return [evidence["text"] for evidence in card["evidence"]]


def test_a_menu_line_with_a_shellfish_term_names_the_term_as_evidence(client):
    card = checked_card(client, "Arroz con camarones")

    assert card["kind"] == "allergen_terms"
    assert "shellfish: camarones" in evidence_texts(card)
    assert "camarones" in card["body"]


def test_term_matching_ignores_accents_and_case(client):
    card = checked_card(client, "CAMARON AL AJILLO")

    assert "shellfish: camarón" in evidence_texts(card)


@pytest.mark.parametrize(
    "mollusk_line",
    ["Calamares fritos", "Pulpo al ajillo", "Almejas a la marinera", "Mejillones al vapor", "Ceviche de chucheca", "Arroz con piangua"],
)
def test_mollusk_only_lines_name_no_shellfish_terms(client, mollusk_line):
    card = checked_card(client, mollusk_line)

    assert evidence_texts(card) == [mollusk_line]
    assert card["allergy_labels"] == [{"allergen": "shellfish", "label": "Ask staff"}]


def test_a_menu_line_with_a_shellfish_term_is_labelled_contains_with_the_staff_phrase_one_tap_away(client):
    card = checked_card(client, "Arroz con camarones")

    assert card["allergy_labels"] == [{"allergen": "shellfish", "label": "Contains"}]
    assert card["body"].startswith("Contains shellfish")
    assert card["staff_phrase_action"] == {"label": "Show staff phrase", "phrase": "allergy"}


def test_a_menu_line_with_no_term_says_ask_staff_never_an_all_clear(client):
    card = checked_card(client, "Pulpo al ajillo")

    assert card["allergy_labels"] == [{"allergen": "shellfish", "label": "Ask staff"}]
    assert card["body"].startswith("Ask staff about shellfish")
    assert "safe" not in card["body"].lower()
    assert "no allergen terms" not in card["body"].lower()
    assert card["staff_phrase_action"] == {"label": "Show staff phrase", "phrase": "allergy"}


def test_a_term_inside_a_longer_word_does_not_match(client):
    card = checked_card(client, "Paellera de vegetales")

    assert evidence_texts(card) == ["Paellera de vegetales"]


def copied_pack_folder(tmp_path, country):
    packs_dir = tmp_path / "packs"
    shutil.copytree(REPO_PACKS_DIR / country, packs_dir / country)
    shutil.copytree(REPO_PACKS_DIR / "global", packs_dir / "global")
    return packs_dir


def client_for_packs(tmp_path, packs_dir, country="cr", active_allergens='["shellfish"]'):
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", DEFAULT_MODEL_ENDPOINT_URL)
    config_text = config_path.read_text()
    config_text = config_text.replace(f'packs_dir = "{REPO_PACKS_DIR}"', f'packs_dir = "{packs_dir}"')
    config_text = config_text.replace('country = "cr"', f'country = "{country}"')
    config_text = config_text.replace('active_allergens = ["shellfish"]', f"active_allergens = {active_allergens}")
    config_path.write_text(config_text)
    return TestClient(create_app(config_path))


def test_adding_a_term_to_the_yaml_makes_it_match(tmp_path):
    packs_dir = copied_pack_folder(tmp_path, "cr")
    terms_path = packs_dir / "cr" / "allergen_terms.yaml"
    with client_for_packs(tmp_path, packs_dir) as client:
        card_before = checked_card(client, "Cigala a la plancha")
    terms_path.write_text(terms_path.read_text() + "  - cigala\n")

    with client_for_packs(tmp_path, packs_dir) as client:
        card_after = checked_card(client, "Cigala a la plancha")

    assert evidence_texts(card_before) == ["Cigala a la plancha"]
    assert "shellfish: cigala" in evidence_texts(card_after)


def test_removing_a_term_from_the_yaml_stops_it_matching(tmp_path):
    packs_dir = copied_pack_folder(tmp_path, "cr")
    terms_path = packs_dir / "cr" / "allergen_terms.yaml"
    terms_path.write_text(terms_path.read_text().replace("  - paella\n", ""))

    with client_for_packs(tmp_path, packs_dir) as client:
        card = checked_card(client, "Paella valenciana")

    assert evidence_texts(card) == ["Paella valenciana"]


@pytest.mark.parametrize(
    ("file_name", "broken_text", "named_problem"),
    [
        ("pack.yaml", "country: cr\nname: Costa Rica\n", "language"),
        ("pack.yaml", (REPO_PACKS_DIR / "cr" / "pack.yaml").read_text().replace("America/Costa_Rica", "America/Atlantis"), "America/Atlantis"),
        ("pack.yaml", (REPO_PACKS_DIR / "cr" / "pack.yaml").read_text().replace("- CRC", "- colones"), "currencies"),
        ("pack.yaml", (REPO_PACKS_DIR / "cr" / "pack.yaml").read_text() + "flag: red\n", "flag"),
        ("allergen_terms.yaml", "shellfish: []\n", "shellfish"),
        ("allergen_terms.yaml", "shellfish:\n  - camarón\n  - ''\n", "shellfish.1"),
        ("allergen_terms.yaml", "peanut:\n  - maní\n", "no Allergen Terms for active Allergen shellfish"),
        ("allergen_terms.yaml", "shellfish: [camarón\n", "not valid YAML"),
    ],
)
def test_an_invalid_pack_stops_the_app_with_a_message_naming_the_problem(tmp_path, file_name, broken_text, named_problem):
    packs_dir = copied_pack_folder(tmp_path, "cr")
    (packs_dir / "cr" / file_name).write_text(broken_text)

    with pytest.raises(InvalidCountryPack) as stopped_startup:
        client_for_packs(tmp_path, packs_dir)

    assert file_name in str(stopped_startup.value)
    assert named_problem in str(stopped_startup.value)


def test_a_missing_pack_file_stops_the_app_naming_the_file(tmp_path):
    packs_dir = copied_pack_folder(tmp_path, "cr")
    (packs_dir / "cr" / "allergen_terms.yaml").unlink()

    with pytest.raises(InvalidCountryPack, match="allergen_terms.yaml is missing"):
        client_for_packs(tmp_path, packs_dir)


def test_the_status_card_shows_the_cr_pack_currencies_time_zone_and_guide(client):
    texts = evidence_texts(client.get("/api/status").json())

    assert "currencies = CRC, USD" in texts
    assert "time_zone = America/Costa_Rica" in texts
    assert "guide = wikivoyage_en_all_maxi.zim (Costa_Rica)" in texts


def test_the_specimen_pack_matches_the_fake_peanut_allergen(tmp_path):
    with client_for_packs(tmp_path, SPECIMEN_PACKS_DIR, "specimen", '["shellfish", "peanut"]') as client:
        card = checked_card(client, "Pollo en salsa de MANI")

    assert "peanut: maní" in evidence_texts(card)


PEANUT_WORDS = ("peanut", "maní", "cacahuate", "cacahuete")


def test_peanut_terms_appear_only_in_the_test_fixture_pack():
    shipped_pack_texts = [path.read_text(encoding="utf-8") for path in REPO_PACKS_DIR.rglob("*.yaml")]

    assert shipped_pack_texts
    assert not any(
        contains_phrase_ignoring_accents_and_case(text, peanut_word)
        for text in shipped_pack_texts
        for peanut_word in PEANUT_WORDS
    )
