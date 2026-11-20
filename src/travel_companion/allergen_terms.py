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


def terms_summary(matched_terms: list[AllergenTerm]) -> str:
    if not matched_terms:
        return "No Allergen Terms on this line."
    named_terms = ", ".join(f"{term.allergen} ({term.text})" for term in matched_terms)
    return f"Allergen Terms on this line: {named_terms}."


def allergen_terms_card(pack: CountryPack, menu_line_text: str, allergens: tuple[str, ...]) -> AnswerCard:
    matched_terms = matched_allergen_terms(pack, menu_line_text, allergens)
    return AnswerCard(
        kind="allergen_terms",
        title=menu_line_text,
        body=terms_summary(matched_terms),
        evidence=[Evidence(source=MENU_LINE_SOURCE, text=menu_line_text)]
        + [Evidence(source=str(term.source), text=f"{term.allergen}: {term.text}") for term in matched_terms],
    )


allergen_terms_router = APIRouter()


@allergen_terms_router.post("/api/menu-line", response_model=AnswerCard)
def post_menu_line(menu_line_request: MenuLineRequest, request: Request) -> AnswerCard:
    return allergen_terms_card(
        request.app.state.country_pack, menu_line_request.text, request.app.state.config.active_allergens
    )
