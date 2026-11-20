from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.country_pack import AllergenTerm, CountryPack
from travel_companion.text_folding import contains_phrase_ignoring_accents_and_case

MENU_LINE_SOURCE = "menu line"


class MenuLineRequest(BaseModel):
    text: str


def matched_allergen_terms(pack: CountryPack, menu_line_text: str, allergens: tuple[str, ...]) -> list[AllergenTerm]:
    return [
        term
        for allergen in allergens
        for term in pack.terms_for(allergen)
        if contains_phrase_ignoring_accents_and_case(menu_line_text, term.text)
    ]


CONTAINS_LABEL = "Contains"
ASK_STAFF_LABEL = "Ask staff"
ALLERGY_STAFF_PHRASE = "allergy"
SHOW_STAFF_PHRASE_LABEL = "Show staff phrase"


class AllergyLabelOnLine(BaseModel):
    allergen: str
    label: Literal["Contains", "Often contains", "Ask staff", "Not typical"]


class StaffPhraseAction(BaseModel):
    label: str
    phrase: str


class MenuLineCard(AnswerCard):
    allergy_labels: list[AllergyLabelOnLine]
    staff_phrase_action: StaffPhraseAction


def allergy_label_sentence(allergen: str, terms_for_allergen: list[AllergenTerm]) -> str:
    if terms_for_allergen:
        named_terms = ", ".join(term.text for term in terms_for_allergen)
        return f"Contains {allergen}: {named_terms}."
    return f"Ask staff about {allergen}: no Allergen Term or Known Dish on this line."


def allergen_terms_card(pack: CountryPack, menu_line_text: str, allergens: tuple[str, ...]) -> MenuLineCard:
    matched_terms = matched_allergen_terms(pack, menu_line_text, allergens)
    terms_by_allergen = {
        allergen: [term for term in matched_terms if term.allergen == allergen] for allergen in allergens
    }
    return MenuLineCard(
        kind="allergen_terms",
        title=menu_line_text,
        body=" ".join(allergy_label_sentence(allergen, terms) for allergen, terms in terms_by_allergen.items()),
        evidence=[Evidence(source=MENU_LINE_SOURCE, text=menu_line_text)]
        + [Evidence(source=str(term.source), text=f"{term.allergen}: {term.text}") for term in matched_terms],
        allergy_labels=[
            AllergyLabelOnLine(allergen=allergen, label=CONTAINS_LABEL if terms else ASK_STAFF_LABEL)
            for allergen, terms in terms_by_allergen.items()
        ],
        staff_phrase_action=StaffPhraseAction(label=SHOW_STAFF_PHRASE_LABEL, phrase=ALLERGY_STAFF_PHRASE),
    )


allergen_terms_router = APIRouter()


@allergen_terms_router.post("/api/menu-line", response_model=MenuLineCard)
def post_menu_line(menu_line_request: MenuLineRequest, request: Request) -> MenuLineCard:
    return allergen_terms_card(
        request.app.state.country_pack, menu_line_request.text, request.app.state.config.active_allergens
    )
