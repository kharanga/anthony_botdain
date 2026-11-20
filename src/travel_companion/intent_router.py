import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.chat_message import ChatMessage
from travel_companion.country_pack import CountryPack
from travel_companion.model_client import ModelClient, ModelUnavailable
from travel_companion.prompt_budget import PromptTooLong
from travel_companion.spoken_amount import UNIT_WORD_VALUES, spoken_amount_in
from travel_companion.staff_phrase import StaffPhraseCard, UnknownPhrase, staff_phrase_card

IntentName = Literal[
    "show_staff_phrase",
    "menu_allergen_question",
    "guide_question",
    "add_expense",
    "spending_question",
    "open_vault",
]

INTENT_TITLES: dict[str, str] = {
    "show_staff_phrase": "Show the staff phrase",
    "menu_allergen_question": "Allergen question about the last menu",
    "guide_question": "Guide question",
    "add_expense": "Add an expense",
    "spending_question": "Spending question",
    "open_vault": "Open the vault",
}

TRANSCRIPT_SOURCE = "transcript"
INTENT_RULE_SOURCE = "intent rule"
INTENT_MODEL_SOURCE = "intent model"


class IntentCard(AnswerCard):
    intent: IntentName | None
    details: dict[str, str]


@dataclass(frozen=True)
class RoutedIntent:
    intent: IntentName
    rule: str
    details: dict[str, str] = field(default_factory=dict)
    evidence_source: str = INTENT_RULE_SOURCE


def normalised_transcript(transcript: str) -> str:
    lowered = transcript.lower().replace("’", "'")
    return re.sub(r"\s+", " ", lowered).strip()


def contains_any(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()
    return None


def details_without_blanks(**details: str | None) -> dict[str, str]:
    return {name: value for name, value in details.items() if value is not None}


STAFF_PHRASE_PATTERNS = (
    r"\ballerg(?:y|ic) (?:card|phrase)\b",
    r"\bstaff (?:card|phrase)\b",
    r"\b(?:hospital|pharmacy) phrase\b",
    r"\bhow do i (?:say|tell (?:them|someone)) i'?m allergic\b",
    r"\b(?:tell|ask|show) the (?:waiter|waitress|staff|server|cook|kitchen|chef)\b",
)
HOSPITAL_PHRASE_PATTERN = r"\b(?:hospital|pharmacy)\b"
DISH_QUESTION_PHRASE_PATTERN = r"\bask the (?:waiter|waitress|staff|server|cook|kitchen|chef)\b"


def staff_phrase_name(text: str) -> str:
    if re.search(HOSPITAL_PHRASE_PATTERN, text):
        return "hospital_pharmacy"
    if re.search(DISH_QUESTION_PHRASE_PATTERN, text):
        return "dish_question"
    return "allergy"


def staff_phrase_intent(text: str) -> RoutedIntent | None:
    matched = contains_any(text, STAFF_PHRASE_PATTERNS)
    if matched is None:
        return None
    return RoutedIntent("show_staff_phrase", f"staff phrase: {matched}", {"phrase": staff_phrase_name(text)})


VAULT_DOCUMENT_PATTERNS = {
    "boarding_pass": r"boarding pass(?:es)?",
    "passport": r"passports?",
    "insurance": r"(?:travel |health )?insurance(?: card| policy)?",
    "visa": r"visas?",
    "drivers_license": r"driver'?s'? licen[cs]e|driving licen[cs]e",
    "hotel_booking": r"hotel (?:booking|reservation|confirmation)s?",
    "flight_booking": r"flight (?:ticket|booking|reservation|confirmation)s?",
    "vaccination_card": r"vaccination (?:card|record|certificate)s?",
    "car_rental": r"(?:car )?rental (?:booking|agreement|reservation)s?",
}
VAULT_VERB_PATTERN = r"\b(?:show|open|pull up|display|get|find|need|where'?s|where is|where are)(?: me)?(?: my| the)"
OPEN_THE_VAULT_PATTERN = r"\b(?:open|unlock|show)(?: me)? (?:the |my )?(?:vault|documents)\b"


def vault_intent(text: str) -> RoutedIntent | None:
    for document, document_pattern in VAULT_DOCUMENT_PATTERNS.items():
        matched = re.search(rf"{VAULT_VERB_PATTERN} (?:{document_pattern})\b", text)
        if matched:
            return RoutedIntent("open_vault", f"vault document: {matched.group()}", {"document": document})
    matched = re.search(OPEN_THE_VAULT_PATTERN, text)
    if matched:
        return RoutedIntent("open_vault", f"vault: {matched.group()}")
    return None


EXPENSE_CATEGORY_WORDS = {
    "food": (
        "lunch", "dinner", "breakfast", "coffee", "soda", "restaurant", "food", "meal", "grocery",
        "groceries", "snack", "drink", "beer", "casado", "supermarket",
    ),
    "transport": ("taxi", "uber", "bus", "ferry", "shuttle", "gas", "parking", "car rental", "flight", "boat"),
    "lodging": ("hotel", "hostel", "lodge", "airbnb", "room", "cabin", "lodging"),
    "activities": ("tour", "zipline", "canopy", "rafting", "surf lesson", "entrance", "park fee", "activity"),
    "shopping": ("souvenir", "gift", "clothes", "market", "shop", "shopping", "sunscreen"),
}
SPENDING_PERIOD_PATTERNS = {
    "today": r"\btoday\b",
    "yesterday": r"\byesterday\b",
    "this_week": r"\bthis week\b",
}


def mentions_word(text: str, word: str) -> bool:
    return re.search(rf"\b{re.escape(word)}(?:s|es)?\b", text) is not None


def expense_category_in(text: str) -> str | None:
    for category, words in EXPENSE_CATEGORY_WORDS.items():
        if any(mentions_word(text, word) for word in words):
            return category
    return None


def spending_period_in(text: str) -> str | None:
    for period, period_pattern in SPENDING_PERIOD_PATTERNS.items():
        if re.search(period_pattern, text):
            return period
    return None


SPENDING_QUESTION_PATTERNS = (
    r"\bhow much (?:money )?(?:have|did|do) i (?:spent|spend)\b",
    r"\bwhat (?:did|have) i (?:spend|spent)\b",
    r"\b(?:total|my) spending\b",
    r"\bspent so far\b",
)


def spending_question_intent(text: str) -> RoutedIntent | None:
    matched = contains_any(text, SPENDING_QUESTION_PATTERNS)
    if matched is None:
        return None
    details = details_without_blanks(category=expense_category_in(text), period=spending_period_in(text))
    return RoutedIntent("spending_question", f"spending question: {matched}", details)


ADD_EXPENSE_PATTERNS = (
    r"\b(?:spent|paid)\b",
    r"\b(?:add|log|record)(?: an?)? expense\b",
)
ADD_WITH_AMOUNT_PATTERNS = (r"\b(?:add|log|record)\b",)


def amount_text(amount: Decimal) -> str:
    if amount == amount.to_integral():
        return format(amount.quantize(Decimal(1)), "f")
    return format(amount, "f")


def add_expense_intent(text: str) -> RoutedIntent | None:
    spoken_amount = spoken_amount_in(text)
    matched = contains_any(text, ADD_EXPENSE_PATTERNS)
    if matched is None and spoken_amount is not None:
        matched = contains_any(text, ADD_WITH_AMOUNT_PATTERNS)
    if matched is None:
        return None
    details = details_without_blanks(
        amount=amount_text(spoken_amount.amount) if spoken_amount else None,
        currency=spoken_amount.currency if spoken_amount else None,
        category=expense_category_in(text),
    )
    return RoutedIntent("add_expense", f"add expense: {matched}", details)


INGREDIENT_WORDS = {
    "shrimp": "shrimp", "shrimps": "shrimp", "prawn": "prawn", "prawns": "prawn",
    "lobster": "lobster", "lobsters": "lobster", "crab": "crab", "crabs": "crab",
    "shellfish": "shellfish", "seafood": "seafood", "crustacean": "crustacean", "crustaceans": "crustacean",
    "camarones": "camarones", "camaron": "camarones", "camarón": "camarones", "langosta": "langosta",
    "cangrejo": "cangrejo", "mariscos": "mariscos", "peanut": "peanut", "peanuts": "peanut",
}
ALLERGY_WORD_PATTERN = r"\ballerg(?:y|ies|ic|en|ens)\b"
ORDINAL_WORD_NUMBERS = {
    "first": "1", "second": "2", "third": "3", "fourth": "4", "fifth": "5", "sixth": "6",
    "seventh": "7", "eighth": "8", "ninth": "9", "tenth": "10", "last": "last",
}
DISH_NOUN_PATTERN = r"(?:one|dish|item|line|plate)"
ORDINAL_DISH_PATTERN = rf"\b(?P<ordinal>{'|'.join(ORDINAL_WORD_NUMBERS)}|\d+(?:st|nd|rd|th)) {DISH_NOUN_PATTERN}\b"
NUMBERED_DISH_PATTERN = rf"\b(?:number|dish|item|line|no\.?) (?P<number>\d+|{'|'.join(UNIT_WORD_VALUES)})\b"
NAMED_DISH_PATTERNS = (
    r"\b(?:does|do|did) (?:the )?(?P<name>.+?) (?:have|contain|come with)\b",
    r"\b(?:is|are) there (?:any )?\w+ in (?:the )?(?P<name>.+?)[?.!]?$",
)
WHOLE_MENU_PATTERN = r"\b(?:this menu|the menu|which (?:dishes|ones|items)|this|it)\b"
NOT_A_DISH_NAME = frozenset({"this", "it", "that", "they", "these", "those", "i", "you", "this one", "that one"})


def ingredient_in(text: str) -> str | None:
    for word in re.findall(r"[^\W\d_]+", text):
        if word in INGREDIENT_WORDS:
            return INGREDIENT_WORDS[word]
    return None


def dish_number_in(text: str) -> str | None:
    ordinal_match = re.search(ORDINAL_DISH_PATTERN, text)
    if ordinal_match:
        ordinal = ordinal_match.group("ordinal")
        return ORDINAL_WORD_NUMBERS.get(ordinal) or re.sub(r"\D", "", ordinal)
    numbered_match = re.search(NUMBERED_DISH_PATTERN, text)
    if numbered_match:
        number = numbered_match.group("number")
        return str(UNIT_WORD_VALUES[number]) if number in UNIT_WORD_VALUES else number
    return None


def dish_name_in(text: str) -> str | None:
    for named_dish_pattern in NAMED_DISH_PATTERNS:
        matched = re.search(named_dish_pattern, text)
        if matched and matched.group("name") not in NOT_A_DISH_NAME:
            return matched.group("name")
    return None


def numbered_dish_question(text: str, ingredient: str | None) -> RoutedIntent | None:
    dish_number = dish_number_in(text)
    asks_about_allergy = ingredient is not None or re.search(ALLERGY_WORD_PATTERN, text) is not None
    if dish_number is None or not asks_about_allergy:
        return None
    details = details_without_blanks(dish_number=dish_number, ingredient=ingredient)
    return RoutedIntent("menu_allergen_question", f"menu dish {dish_number}", details)


def named_or_whole_menu_question(text: str, ingredient: str | None) -> RoutedIntent | None:
    if ingredient is None:
        return None
    dish_name = dish_name_in(text)
    if dish_name is None and re.search(WHOLE_MENU_PATTERN, text) is None:
        return None
    details = details_without_blanks(dish_name=dish_name, ingredient=ingredient)
    return RoutedIntent("menu_allergen_question", f"menu question about {ingredient}", details)


def menu_allergen_question_intent(text: str) -> RoutedIntent | None:
    ingredient = ingredient_in(text)
    return numbered_dish_question(text, ingredient) or named_or_whole_menu_question(text, ingredient)


GUIDE_QUESTION_START_PATTERN = (
    r"^(?:where|what|what's|when|how|which|who|why|is|are|can|could|do|does|should|will|"
    r"tell me about|any|recommend)\b"
)


TRAVEL_TOPIC_WORDS = (
    "beach", "volcano", "park", "national park", "reserve", "forest", "river", "waterfall", "lake", "island",
    "mountain", "trail", "hike", "hiking", "wildlife", "sloth", "monkey", "bird", "turtle", "whale",
    "season", "weather", "rain", "climate", "water", "visa", "passport", "border", "customs", "vaccine",
    "mosquito", "taxi", "bus", "shuttle", "ferry", "train", "airport", "flight", "car", "drive", "road",
    "hotel", "hostel", "lodge", "restaurant", "eat", "food", "dish", "tour", "surf", "snorkel", "dive",
    "town", "city", "village", "country", "place", "visit", "see", "get to", "tip", "tipping", "currency",
    "colones", "dollars", "atm", "bank", "hospital", "pharmacy", "clinic", "police", "embassy", "festival",
)
WORDS_CAPITALISED_WITHOUT_NAMING_A_PLACE = frozenset({"I", "I'm", "I'd", "I've", "I'll", "OK"})


def names_a_place(transcript: str) -> bool:
    later_words = re.findall(r"[^\W\d_][\w'’]*", transcript)[1:]
    return any(
        word[0].isupper() and word not in WORDS_CAPITALISED_WITHOUT_NAMING_A_PLACE for word in later_words
    )


def names_a_travel_topic(text: str) -> bool:
    return any(mentions_word(text, word) for word in TRAVEL_TOPIC_WORDS)


def guide_question_intent(text: str, transcript: str) -> RoutedIntent | None:
    matched = re.search(GUIDE_QUESTION_START_PATTERN, text)
    if matched is None and not text.endswith("?"):
        return None
    if not names_a_place(transcript) and not names_a_travel_topic(text):
        return None
    rule = f"guide question: {matched.group() if matched else '?'}"
    return RoutedIntent("guide_question", rule, {"question": transcript.strip()})


TEXT_RULES_BEFORE_GUIDE = (
    staff_phrase_intent,
    vault_intent,
    spending_question_intent,
    add_expense_intent,
    menu_allergen_question_intent,
)


def rule_routed_intent(transcript: str) -> RoutedIntent | None:
    text = normalised_transcript(transcript)
    for rule in TEXT_RULES_BEFORE_GUIDE:
        routed = rule(text)
        if routed is not None:
            return routed
    return guide_question_intent(text, transcript)


def details_sentence(details: dict[str, str]) -> str:
    return " ".join(f"{name.replace('_', ' ').capitalize()}: {value}." for name, value in details.items())


def intent_card(transcript: str, routed: RoutedIntent) -> IntentCard:
    return IntentCard(
        kind="intent",
        title=INTENT_TITLES[routed.intent],
        body=details_sentence(routed.details),
        evidence=[
            Evidence(source=TRANSCRIPT_SOURCE, text=transcript),
            Evidence(source=routed.evidence_source, text=routed.rule),
        ],
        intent=routed.intent,
        details=routed.details,
    )


def unsupported_intent_card(transcript: str, model_evidence: list[Evidence] | None = None) -> IntentCard:
    supported_list = "\n".join(f"- {title}" for title in INTENT_TITLES.values())
    return IntentCard(
        kind="unsupported_intent",
        title="I can't do that yet",
        body=f"I can't do that yet. I can:\n{supported_list}",
        evidence=[Evidence(source=TRANSCRIPT_SOURCE, text=transcript), *(model_evidence or [])],
        intent=None,
        details={},
    )


NO_INTENT_LABEL = "none"
INTENT_LABEL_EXAMPLES = {
    "show_staff_phrase": "show my allergy card",
    "menu_allergen_question": "does the third one have shrimp?",
    "guide_question": "where can I see sloths near La Fortuna?",
    "add_expense": "I spent five mil on a taxi",
    "spending_question": "how much have I spent on food?",
    "open_vault": "show my boarding pass",
}
INTENT_LABEL_CHARACTERS_TO_STRIP = " \t\n\"'`.!"


def intent_label_system_prompt() -> str:
    label_lines = "\n".join(f"{label}: e.g. \"{example}\"" for label, example in INTENT_LABEL_EXAMPLES.items())
    return (
        "You route a traveller's spoken request to one intent. The intents are:\n"
        f"{label_lines}\n"
        f"Reply with exactly one label from that list, or {NO_INTENT_LABEL} if none fits. Reply with the label only."
    )


def intent_label_from_reply(reply: str) -> IntentName | None:
    label = reply.strip(INTENT_LABEL_CHARACTERS_TO_STRIP).lower()
    if label in INTENT_TITLES:
        return label
    return None


def model_details_for(intent: IntentName, transcript: str) -> dict[str, str]:
    text = normalised_transcript(transcript)
    if intent == "guide_question":
        return {"question": transcript.strip()}
    if intent == "show_staff_phrase":
        return {"phrase": staff_phrase_name(text)}
    if intent == "spending_question":
        return details_without_blanks(category=expense_category_in(text), period=spending_period_in(text))
    if intent == "add_expense":
        spoken_amount = spoken_amount_in(text)
        return details_without_blanks(
            amount=amount_text(spoken_amount.amount) if spoken_amount else None,
            currency=spoken_amount.currency if spoken_amount else None,
            category=expense_category_in(text),
        )
    if intent == "menu_allergen_question":
        return details_without_blanks(
            dish_number=dish_number_in(text), dish_name=dish_name_in(text), ingredient=ingredient_in(text)
        )
    return {}


def model_routed_card(transcript: str, model_client: ModelClient) -> IntentCard:
    model_evidence_source = f"{INTENT_MODEL_SOURCE} {model_client.endpoint_url}"
    try:
        reply = model_client.complete(
            [ChatMessage("system", intent_label_system_prompt()), ChatMessage("user", transcript)]
        )
    except (ModelUnavailable, PromptTooLong) as error:
        return unsupported_intent_card(transcript, [Evidence(source=model_evidence_source, text=str(error))])
    intent = intent_label_from_reply(reply)
    if intent is None:
        return unsupported_intent_card(transcript, [Evidence(source=model_evidence_source, text=f"model reply: {reply}")])
    routed = RoutedIntent(intent, f"model label: {intent}", model_details_for(intent, transcript), INTENT_MODEL_SOURCE)
    return intent_card(transcript, routed)


def route_transcript(transcript: str, model_client: ModelClient | None = None) -> IntentCard:
    routed = rule_routed_intent(transcript)
    if routed is not None:
        return intent_card(transcript, routed)
    if model_client is None:
        return unsupported_intent_card(transcript)
    return model_routed_card(transcript, model_client)


class TranscriptRequest(BaseModel):
    transcript: str


class StaffPhraseIntentCard(StaffPhraseCard):
    intent: IntentName | None
    details: dict[str, str]


def staff_phrase_card_leading_with(pack: CountryPack, phrase_name: str | None) -> StaffPhraseCard:
    try:
        return staff_phrase_card(pack, phrase_name)
    except UnknownPhrase:
        return staff_phrase_card(pack)


def staff_phrase_intent_card(pack: CountryPack, routed_card: IntentCard) -> StaffPhraseIntentCard:
    phrase_card = staff_phrase_card_leading_with(pack, routed_card.details.get("phrase"))
    return StaffPhraseIntentCard(
        **phrase_card.model_dump(exclude={"evidence"}),
        evidence=phrase_card.evidence + routed_card.evidence,
        intent=routed_card.intent,
        details=routed_card.details,
    )


def answer_card_for_routed_intent(pack: CountryPack, routed_card: IntentCard) -> StaffPhraseIntentCard | IntentCard:
    if routed_card.intent == "show_staff_phrase":
        return staff_phrase_intent_card(pack, routed_card)
    return routed_card


intent_router = APIRouter()


@intent_router.post("/api/transcript", response_model=StaffPhraseIntentCard | IntentCard)
def post_transcript(transcript_request: TranscriptRequest, request: Request) -> StaffPhraseIntentCard | IntentCard:
    routed_card = route_transcript(transcript_request.transcript, request.app.state.model_client)
    return answer_card_for_routed_intent(request.app.state.country_pack, routed_card)
