import pytest
import yaml
from conftest import REPO_PACKS_DIR

SHELLFISH_INGREDIENTS = {
    "shrimp",
    "lobster",
    "crab",
    "langostino",
    "crayfish",
    "seafood broth",
    "mixed seafood",
    "imitation crab",
}

WIKI_SOURCE_PREFIXES = tuple(
    f"source = https://{language}.{site}.org/wiki/"
    for language in ("en", "es")
    for site in ("wikipedia", "wikibooks", "wikivoyage")
)


def looked_up_card(client, dish_name):
    response = client.post("/api/dish", json={"name": dish_name})
    assert response.status_code == 200
    return response.json()


def evidence_texts(card):
    return [evidence["text"] for evidence in card["evidence"]]


def cr_dishes():
    return yaml.safe_load((REPO_PACKS_DIR / "cr" / "dishes.yaml").read_text(encoding="utf-8"))


def test_about_a_hundred_cr_dishes_each_return_an_unreviewed_card_with_a_source(client):
    dishes = cr_dishes()

    assert len(dishes) >= 95
    for dish in dishes:
        card = looked_up_card(client, dish["name"])
        assert card["kind"] == "dish"
        assert card["title"] == dish["name"]
        assert any(text.startswith(WIKI_SOURCE_PREFIXES) for text in evidence_texts(card))
        assert "reviewed = false" in evidence_texts(card)


@pytest.mark.parametrize(
    ("menu_line", "dish_title", "expected_evidence"),
    [
        ("Arroz c/ camarones", "Arroz con camarones", "shrimp (usual)"),
        ("arroz c/camarones", "Arroz con camarones", "shrimp (usual)"),
        ("Casado c/ pescado", "Casado con pescado", "fish (usual)"),
        ("CEVICHE DE PESCADO", "Ceviche", "shrimp (sometimes)"),
        ("Sopa de mariscos", "Sopa de mariscos", "mixed seafood (usual)"),
        ("Gallo pinto c/ huevo", "Gallo pinto con huevo", "egg (usual)"),
    ],
)
def test_common_menu_spellings_and_abbreviations_find_the_cr_dish(client, menu_line, dish_title, expected_evidence):
    card = looked_up_card(client, menu_line)

    assert card["title"] == dish_title
    assert expected_evidence in evidence_texts(card)


@pytest.mark.parametrize("mollusk_dish", ["Ceviche de pulpo", "Calamares fritos", "Ceviche de piangua", "Almejas al ajillo"])
def test_a_mollusk_only_dish_carries_no_shellfish_ingredient(client, mollusk_dish):
    card = looked_up_card(client, mollusk_dish)

    assert card["kind"] == "dish"
    shown_ingredients = {text.rsplit(" (", 1)[0] for text in evidence_texts(card) if text.endswith(("(usual)", "(sometimes)"))}
    assert shown_ingredients
    assert not shown_ingredients & SHELLFISH_INGREDIENTS
