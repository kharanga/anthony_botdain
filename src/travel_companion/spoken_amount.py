import re
from dataclasses import dataclass
from decimal import Decimal

UNIT_WORD_VALUES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
    "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
HUNDRED_WORDS = frozenset({"hundred"})
THOUSAND_WORDS = frozenset({"thousand"})
NUMBER_RUN_WORDS = frozenset(UNIT_WORD_VALUES) | HUNDRED_WORDS | THOUSAND_WORDS
COLON_MULTIPLIER_WORDS = {"mil": 1000, "rojo": 1000, "rojos": 1000, "teja": 100, "tejas": 100}
PLAIN_MULTIPLIER_WORDS = HUNDRED_WORDS | THOUSAND_WORDS
CURRENCY_WORDS = {
    "dollar": "USD", "dollars": "USD", "bucks": "USD", "usd": "USD",
    "colon": "CRC", "colón": "CRC", "colones": "CRC", "crc": "CRC",
}
CURRENCY_SYMBOLS = {"₡": "CRC", "$": "USD"}
AMOUNT_TOKEN_PATTERN = re.compile(r"[₡$]|\d[\d.,]*\d|\d|[^\W\d_]+(?:'[^\W\d_]+)?")
THOUSANDS_WITH_COMMAS_PATTERN = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?")
THOUSANDS_WITH_DOTS_PATTERN = re.compile(r"\d{1,3}(?:\.\d{3})+")


@dataclass(frozen=True)
class SpokenAmount:
    amount: Decimal
    currency: str | None


def number_words_value(words: list[str], leading_value: Decimal = Decimal(0)) -> Decimal:
    total = Decimal(0)
    current = leading_value
    for word in words:
        if word in UNIT_WORD_VALUES:
            current += UNIT_WORD_VALUES[word]
        elif word in HUNDRED_WORDS:
            current = (current or 1) * 100
        elif word in THOUSAND_WORDS:
            total += (current or 1) * 1000
            current = 0
    return total + current


def digits_value(digits: str, currency: str | None) -> Decimal:
    if THOUSANDS_WITH_COMMAS_PATTERN.fullmatch(digits):
        return Decimal(digits.replace(",", ""))
    if THOUSANDS_WITH_DOTS_PATTERN.fullmatch(digits) and currency != "USD":
        return Decimal(digits.replace(".", ""))
    return Decimal(digits.replace(",", "."))


def is_amount_start(token: str) -> bool:
    return token in CURRENCY_SYMBOLS or token[0].isdigit() or token in UNIT_WORD_VALUES


def number_word_run_length(tokens: list[str], start: int) -> int:
    end = start
    while end < len(tokens) and tokens[end] in NUMBER_RUN_WORDS:
        end += 1
    return end - start


def amount_from(tokens: list[str], start: int) -> SpokenAmount | None:
    position = start
    currency = None
    if tokens[position] in CURRENCY_SYMBOLS:
        currency = CURRENCY_SYMBOLS[tokens[position]]
        position += 1
        if position == len(tokens) or not tokens[position][0].isdigit():
            return None
    digits = None
    word_value = None
    if tokens[position][0].isdigit():
        digits = tokens[position]
        position += 1
        if position < len(tokens) and tokens[position] in PLAIN_MULTIPLIER_WORDS:
            run_length = number_word_run_length(tokens, position)
            word_value = number_words_value(tokens[position : position + run_length], digits_value(digits, currency))
            digits = None
            position += run_length
    else:
        run_length = number_word_run_length(tokens, position)
        word_value = number_words_value(tokens[position : position + run_length])
        position += run_length
    multiplier = 1
    if position < len(tokens) and tokens[position] in COLON_MULTIPLIER_WORDS:
        multiplier = COLON_MULTIPLIER_WORDS[tokens[position]]
        currency = currency or "CRC"
        position += 1
    if position < len(tokens) and tokens[position] in CURRENCY_WORDS:
        currency = currency or CURRENCY_WORDS[tokens[position]]
    base = digits_value(digits, currency) if digits is not None else Decimal(word_value)
    return SpokenAmount(base * multiplier, currency)


def spoken_amount_in(text: str) -> SpokenAmount | None:
    tokens = AMOUNT_TOKEN_PATTERN.findall(text.lower())
    for start, token in enumerate(tokens):
        if is_amount_start(token):
            amount = amount_from(tokens, start)
            if amount is not None:
                return amount
    return None
