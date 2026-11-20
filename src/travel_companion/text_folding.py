import re
import unicodedata


def accent_and_case_folded(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(character for character in decomposed if not unicodedata.combining(character))
    return " ".join(without_accents.casefold().split())


def contains_phrase_ignoring_accents_and_case(text: str, phrase: str) -> bool:
    whole_words_pattern = rf"(?<!\w){re.escape(accent_and_case_folded(phrase))}(?!\w)"
    return re.search(whole_words_pattern, accent_and_case_folded(text)) is not None
