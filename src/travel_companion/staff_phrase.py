from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.country_pack import CountryPack, Phrase

STAFF_PHRASE_TITLE = "Please read this"


class UnknownPhrase(Exception):
    pass


class PhraseOnCard(BaseModel):
    name: str
    english: str
    spanish: str
    verification: str


class StaffPhraseCard(AnswerCard):
    phrases: list[PhraseOnCard]


def phrases_led_by(pack: CountryPack, phrase_name: str | None) -> list[Phrase]:
    if phrase_name is None:
        return list(pack.phrases)
    leading_phrases = [phrase for phrase in pack.phrases if phrase.name == phrase_name]
    if not leading_phrases:
        raise UnknownPhrase(phrase_name)
    return leading_phrases + [phrase for phrase in pack.phrases if phrase.name != phrase_name]


def staff_phrase_card(pack: CountryPack, phrase_name: str | None = None) -> StaffPhraseCard:
    phrases = phrases_led_by(pack, phrase_name)
    return StaffPhraseCard(
        kind="staff_phrase",
        title=STAFF_PHRASE_TITLE,
        body=phrases[0].spanish,
        evidence=[
            Evidence(source=str(phrase.source), text=f"{phrase.name} ({phrase.verification}): {phrase.spanish}")
            for phrase in phrases
        ],
        phrases=[
            PhraseOnCard(name=phrase.name, english=phrase.english, spanish=phrase.spanish, verification=phrase.verification)
            for phrase in phrases
        ],
    )


staff_phrase_router = APIRouter()


@staff_phrase_router.get("/api/staff-phrase", response_model=StaffPhraseCard)
def get_staff_phrase(request: Request, phrase: str | None = None) -> StaffPhraseCard:
    try:
        return staff_phrase_card(request.app.state.country_pack, phrase)
    except UnknownPhrase as error:
        raise HTTPException(status_code=404, detail=f"No Phrase named {error} in the Country Pack") from error
