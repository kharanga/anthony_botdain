from fastapi import APIRouter, Request
from pydantic import BaseModel

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.country_pack import CountryPack, IngredientMark, KnownDish
from travel_companion.text_folding import accent_and_case_folded

DISH_LOOKUP_SOURCE = "dish lookup"
UNKNOWN_DISH_BODY = "Not in my guide. Ask staff."
UNREVIEWED_NOTE = "This dish is unreviewed."


class DishLookupRequest(BaseModel):
    name: str


def known_dish_named(pack: CountryPack, dish_name: str) -> KnownDish | None:
    folded_dish_name = accent_and_case_folded(dish_name)
    return next((dish for dish in pack.known_dishes if folded_dish_name in dish.folded_names), None)


def ingredients_marked(dish: KnownDish, mark: IngredientMark) -> list[str]:
    return [ingredient for ingredient, ingredient_mark in dish.ingredients if ingredient_mark == mark]


def dish_summary(dish: KnownDish) -> str:
    usual_ingredients = ingredients_marked(dish, "usual")
    sometimes_ingredients = ingredients_marked(dish, "sometimes")
    sentences = []
    if usual_ingredients:
        sentences.append(f"Usually has {', '.join(usual_ingredients)}.")
    if sometimes_ingredients:
        sentences.append(f"Sometimes has {', '.join(sometimes_ingredients)}.")
    if not dish.reviewed:
        sentences.append(UNREVIEWED_NOTE)
    return " ".join(sentences)


def dish_card(dish: KnownDish) -> AnswerCard:
    pack_file = str(dish.pack_file)
    return AnswerCard(
        kind="dish",
        title=dish.name,
        body=dish_summary(dish),
        evidence=[Evidence(source=pack_file, text=f"{ingredient} ({mark})") for ingredient, mark in dish.ingredients]
        + [
            Evidence(source=pack_file, text=f"source = {dish.source}"),
            Evidence(source=pack_file, text=f"reviewed = {str(dish.reviewed).lower()}"),
        ],
    )


def unknown_dish_card(dish_name: str) -> AnswerCard:
    return AnswerCard(
        kind="unknown_dish",
        title=dish_name,
        body=UNKNOWN_DISH_BODY,
        evidence=[Evidence(source=DISH_LOOKUP_SOURCE, text=dish_name)],
    )


def looked_up_dish_card(pack: CountryPack, dish_name: str) -> AnswerCard:
    dish = known_dish_named(pack, dish_name)
    return dish_card(dish) if dish else unknown_dish_card(dish_name)


dish_lookup_router = APIRouter()


@dish_lookup_router.post("/api/dish", response_model=AnswerCard)
def post_dish_lookup(dish_lookup_request: DishLookupRequest, request: Request) -> AnswerCard:
    return looked_up_dish_card(request.app.state.country_pack, dish_lookup_request.name)
