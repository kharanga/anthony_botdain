import re
from dataclasses import dataclass
from decimal import Decimal

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.chat_message import ChatMessage
from travel_companion.model_client import ModelClient, ModelUnavailable

PHRASE_FROM_FACTS_SYSTEM_PROMPT = (
    "You are a travel companion. Answer the traveller's question in one or two short sentences, "
    "using only the facts given. Copy every number, term and name exactly as written in the facts. "
    "Do not add any other numbers, terms or names."
)
NUMBER_PATTERN = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
WORD_PATTERN = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*")
SENTENCE_END_PATTERN = re.compile(r"[.!?:]\s*$")
ALWAYS_ALLOWED_CAPITALIZED_WORDS = frozenset({"i"})


@dataclass(frozen=True)
class Fact:
    spellings: tuple[str, ...]
    number_written_next_to: tuple[str, ...] = ()
    number_never_written_next_to: tuple[str, ...] = ()


@dataclass(frozen=True)
class FactualQuestion:
    question: str
    facts: tuple[Fact, ...]
    evidence: tuple[Evidence, ...]
    template_answer: str
    also_allowed: tuple[str, ...] = ()


def numbers_in(text: str) -> set[Decimal]:
    return {Decimal(match.replace(",", "")) for match in NUMBER_PATTERN.findall(text)}


def lowercase_words_in(text: str) -> set[str]:
    return {word.lower() for word in WORD_PATTERN.findall(text)}


def is_numeric(spelling: str) -> bool:
    return NUMBER_PATTERN.fullmatch(spelling) is not None


def whole_word_pattern(spelling: str) -> str:
    leading_boundary = r"(?<!\w)" if spelling[0].isalnum() else ""
    trailing_boundary = r"(?:s|es)?(?!\w)" if spelling[-1].isalnum() else ""
    return f"{leading_boundary}{re.escape(spelling)}{trailing_boundary}"


def text_mentions(text: str, spelling: str) -> bool:
    if is_numeric(spelling):
        return numbers_in(spelling) <= numbers_in(text)
    return re.search(whole_word_pattern(spelling), text, flags=re.IGNORECASE) is not None


def text_around_each_number(text: str, number_spelling: str) -> list[tuple[str, str]]:
    wanted_numbers = numbers_in(number_spelling)
    return [
        (text[: match.start()], text[match.end() :])
        for match in NUMBER_PATTERN.finditer(text)
        if numbers_in(match.group()) <= wanted_numbers
    ]


def unit_touches_number(text_before: str, text_after: str, unit: str) -> bool:
    unit_pattern = whole_word_pattern(unit)
    ends_with_unit = re.search(unit_pattern + r"\s*$", text_before, flags=re.IGNORECASE) is not None
    starts_with_unit = re.match(r"\s*" + unit_pattern, text_after, flags=re.IGNORECASE) is not None
    return ends_with_unit or starts_with_unit


def any_unit_touches_number(text_before: str, text_after: str, units: tuple[str, ...]) -> bool:
    return any(unit_touches_number(text_before, text_after, unit) for unit in units)


def number_is_written_in_the_right_unit(reply: str, fact: Fact) -> bool:
    numeric_spellings = [spelling for spelling in fact.spellings if is_numeric(spelling)]
    surroundings = [around for spelling in numeric_spellings for around in text_around_each_number(reply, spelling)]
    has_wanted_unit = not fact.number_written_next_to or any(
        any_unit_touches_number(before, after, fact.number_written_next_to) for before, after in surroundings
    )
    has_forbidden_unit = any(
        any_unit_touches_number(before, after, fact.number_never_written_next_to) for before, after in surroundings
    )
    return has_wanted_unit and not has_forbidden_unit


def keeps_fact(reply: str, fact: Fact) -> bool:
    mentioned = any(text_mentions(reply, spelling) for spelling in fact.spellings)
    return mentioned and number_is_written_in_the_right_unit(reply, fact)


def keeps_every_fact(reply: str, facts: tuple[Fact, ...]) -> bool:
    return all(keeps_fact(reply, fact) for fact in facts)


def source_texts(factual_question: FactualQuestion) -> list[str]:
    fact_spellings = [spelling for fact in factual_question.facts for spelling in fact.spellings]
    evidence_texts = [item.text for item in factual_question.evidence]
    return [
        factual_question.question,
        factual_question.template_answer,
        *fact_spellings,
        *evidence_texts,
        *factual_question.also_allowed,
    ]


def adds_no_number(reply: str, factual_question: FactualQuestion) -> bool:
    allowed_numbers = set().union(*(numbers_in(text) for text in source_texts(factual_question)))
    return numbers_in(reply) <= allowed_numbers


def capitalized_words_inside_sentences(reply: str) -> set[str]:
    capitalized_words = set()
    for match in WORD_PATTERN.finditer(reply):
        text_before = reply[: match.start()]
        starts_sentence = text_before.strip() == "" or SENTENCE_END_PATTERN.search(text_before)
        if match.group()[0].isupper() and not starts_sentence:
            capitalized_words.add(match.group().lower())
    return capitalized_words


def adds_no_name(reply: str, factual_question: FactualQuestion) -> bool:
    allowed_words = set().union(*(lowercase_words_in(text) for text in source_texts(factual_question)))
    return capitalized_words_inside_sentences(reply) <= allowed_words | ALWAYS_ALLOWED_CAPITALIZED_WORDS


def reply_keeps_the_facts(reply: str, factual_question: FactualQuestion) -> bool:
    return (
        keeps_every_fact(reply, factual_question.facts)
        and adds_no_number(reply, factual_question)
        and adds_no_name(reply, factual_question)
    )


def facts_prompt(factual_question: FactualQuestion) -> str:
    fact_lines = "\n".join(f"- {item.text}" for item in factual_question.evidence)
    return f"Facts:\n{fact_lines}\n\nQuestion: {factual_question.question}"


def phrased_answer(factual_question: FactualQuestion, model_client: ModelClient) -> str:
    return model_client.complete(
        [
            ChatMessage("system", PHRASE_FROM_FACTS_SYSTEM_PROMPT),
            ChatMessage("user", facts_prompt(factual_question)),
        ]
    )


def guarded_answer(factual_question: FactualQuestion, model_client: ModelClient) -> str:
    try:
        reply = phrased_answer(factual_question, model_client).strip()
    except ModelUnavailable:
        return factual_question.template_answer
    if reply_keeps_the_facts(reply, factual_question):
        return reply
    return factual_question.template_answer


def answer_card_from_facts(factual_question: FactualQuestion, model_client: ModelClient) -> AnswerCard:
    return AnswerCard(
        kind="answer",
        title=factual_question.question,
        body=guarded_answer(factual_question, model_client),
        evidence=list(factual_question.evidence),
    )
