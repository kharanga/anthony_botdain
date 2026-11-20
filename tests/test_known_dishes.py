import shutil

import pytest
import yaml
from conftest import DEFAULT_MODEL_ENDPOINT_URL, REPO_PACKS_DIR, write_config
from fastapi.testclient import TestClient

from travel_companion.app import create_app
from travel_companion.country_pack import InvalidCountryPack
from travel_companion.unreviewed_dishes import DEFAULT_RESULTS_PATH, unreviewed_dishes_report


def looked_up_card(client, dish_name):
    response = client.post("/api/dish", json={"name": dish_name})
    assert response.status_code == 200
    return response.json()


def evidence_texts(card):
    return [evidence["text"] for evidence in card["evidence"]]


def test_looking_up_a_dish_by_an_alias_ignoring_accents_and_case_returns_its_card_with_source(client):
    card = looked_up_card(client, "PATACON")

    assert card["kind"] == "dish"
    assert card["title"] == "Patacones"
    assert "green plantain (usual)" in evidence_texts(card)
    assert "source = https://en.wikipedia.org/wiki/Tostones" in evidence_texts(card)
    assert all(evidence["source"].endswith("packs/cr/dishes.yaml") for evidence in card["evidence"])


def copied_packs_dir(tmp_path):
    packs_dir = tmp_path / "packs"
    shutil.copytree(REPO_PACKS_DIR / "cr", packs_dir / "cr")
    shutil.copytree(REPO_PACKS_DIR / "global", packs_dir / "global")
    return packs_dir


def client_for_packs(tmp_path, packs_dir):
    config_path = tmp_path / "config.toml"
    write_config(config_path, tmp_path / "data", DEFAULT_MODEL_ENDPOINT_URL)
    config_path.write_text(config_path.read_text().replace(f'packs_dir = "{REPO_PACKS_DIR}"', f'packs_dir = "{packs_dir}"'))
    return TestClient(create_app(config_path))


def test_a_global_dish_is_found_from_the_cr_pack(client):
    card = looked_up_card(client, "arroz frito")

    assert card["title"] == "Fried rice"
    assert "shrimp (sometimes)" in evidence_texts(card)
    assert all(evidence["source"].endswith("packs/global/dishes.yaml") for evidence in card["evidence"])


def test_a_country_dish_replaces_the_global_dish_with_the_same_name(client):
    card = looked_up_card(client, "ceviche")

    assert card["title"] == "Ceviche"
    assert "cilantro (usual)" in evidence_texts(card)
    assert "chili pepper (usual)" not in evidence_texts(card)
    assert all(evidence["source"].endswith("packs/cr/dishes.yaml") for evidence in card["evidence"])


def test_an_unknown_dish_is_not_in_my_guide(client):
    card = looked_up_card(client, "Pabellón criollo")

    assert card["kind"] == "unknown_dish"
    assert "not in my guide" in card["body"].lower()
    assert evidence_texts(card) == ["Pabellón criollo"]


def test_an_unreviewed_dish_card_says_unreviewed_until_the_yaml_marks_it_reviewed(tmp_path):
    packs_dir = copied_packs_dir(tmp_path)
    dishes_path = packs_dir / "cr" / "dishes.yaml"
    with client_for_packs(tmp_path, packs_dir) as client:
        card_before = looked_up_card(client, "Chifrijo")
    dishes_path.write_text(
        dishes_path.read_text().replace(
            "source: https://es.wikipedia.org/wiki/Chifrijo\n  reviewed: false",
            "source: https://es.wikipedia.org/wiki/Chifrijo\n  reviewed: true",
        )
    )

    with client_for_packs(tmp_path, packs_dir) as client:
        card_after = looked_up_card(client, "Chifrijo")

    assert "unreviewed" in card_before["body"]
    assert "unreviewed" not in card_after["body"]
    assert "reviewed = true" in evidence_texts(card_after)


VALID_DISH = """- name: Gallo pinto
  ingredients:
    rice: usual
  source: https://en.wikipedia.org/wiki/Gallo_pinto
"""


@pytest.mark.parametrize(
    ("folder", "broken_text", "named_problem"),
    [
        ("cr", "- name: Gallo pinto\n  ingredients:\n    rice: usual\n", "0.source"),
        ("global", "- name: Pizza\n  ingredients:\n    cheese: usual\n  source: '  '\n", "0.source"),
        ("cr", VALID_DISH.replace("rice: usual", "rice: always"), "0.ingredients.rice"),
        ("cr", VALID_DISH.replace("rice: usual", "rice:"), "0.ingredients.rice"),
        ("global", VALID_DISH.replace("    rice: usual\n", ""), "0.ingredients"),
        ("cr", VALID_DISH + "  allergens: [shellfish]\n", "allergens"),
        ("cr", VALID_DISH + VALID_DISH.replace("name: Gallo pinto", "name: Pinto\n  aliases: [GALLO PINTÓ]"), "gallo pinto"),
    ],
)
def test_an_invalid_dish_stops_the_app_with_a_message_naming_the_problem(tmp_path, folder, broken_text, named_problem):
    packs_dir = copied_packs_dir(tmp_path)
    (packs_dir / folder / "dishes.yaml").write_text(broken_text)

    with pytest.raises(InvalidCountryPack) as stopped_startup:
        client_for_packs(tmp_path, packs_dir)

    assert f"{folder}/dishes.yaml" in str(stopped_startup.value)
    assert named_problem in str(stopped_startup.value)


def test_an_alias_clash_between_a_global_and_a_country_dish_names_both_files(tmp_path):
    packs_dir = copied_packs_dir(tmp_path)
    dishes_path = packs_dir / "cr" / "dishes.yaml"
    dishes_path.write_text(dishes_path.read_text().replace("aliases: [pinto, gallopinto]", "aliases: [pinto, gallopinto, arroz frito]"))

    with pytest.raises(InvalidCountryPack) as stopped_startup:
        client_for_packs(tmp_path, packs_dir)

    assert "'arroz frito'" in str(stopped_startup.value)
    assert "global/dishes.yaml" in str(stopped_startup.value)
    assert "cr/dishes.yaml" in str(stopped_startup.value)


def test_a_missing_global_dishes_file_stops_the_app_naming_the_file(tmp_path):
    packs_dir = copied_packs_dir(tmp_path)
    (packs_dir / "global" / "dishes.yaml").unlink()

    with pytest.raises(InvalidCountryPack, match="global/dishes.yaml is missing"):
        client_for_packs(tmp_path, packs_dir)


def test_about_ten_global_dishes_and_ten_cr_dishes_are_seeded_with_sources(client):
    for folder in ("global", "cr"):
        dishes = seeded_dishes(folder)
        assert len(dishes) >= 10
        for dish in dishes:
            assert looked_up_card(client, dish["name"])["kind"] == "dish"


def seeded_dishes(folder):
    return yaml.safe_load((REPO_PACKS_DIR / folder / "dishes.yaml").read_text(encoding="utf-8"))


def test_the_results_file_lists_every_unreviewed_dish():
    results_text = DEFAULT_RESULTS_PATH.read_text(encoding="utf-8")
    unreviewed_rows = [
        f"| {dish['name']} | {folder} |"
        for folder in ("global", "cr")
        for dish in seeded_dishes(folder)
        if not dish.get("reviewed", False)
    ]

    assert unreviewed_rows
    assert all(row in results_text for row in unreviewed_rows)


def test_the_results_file_is_regenerated_from_the_current_yaml():
    assert DEFAULT_RESULTS_PATH.read_text(encoding="utf-8") == unreviewed_dishes_report()
