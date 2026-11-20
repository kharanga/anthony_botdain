import csv
import io
import subprocess
from dataclasses import dataclass
from typing import Protocol

TESSERACT_WORD_LEVEL = "5"
TESSERACT_NO_CONFIDENCE = -1.0


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float


class UnreadablePhoto(Exception):
    pass


class OcrEngine(Protocol):
    name: str

    def read_lines(self, photo_bytes: bytes) -> list[OcrLine]: ...


@dataclass(frozen=True)
class TesseractWord:
    line_key: tuple[str, str, str, str]
    text: str
    confidence: float


def tesseract_words(tsv_output: str) -> list[TesseractWord]:
    rows = csv.DictReader(io.StringIO(tsv_output), delimiter="\t", quoting=csv.QUOTE_NONE)
    return [
        TesseractWord(
            line_key=(row["page_num"], row["block_num"], row["par_num"], row["line_num"]),
            text=row["text"].strip(),
            confidence=float(row["conf"]),
        )
        for row in rows
        if row["level"] == TESSERACT_WORD_LEVEL and row["text"].strip() and float(row["conf"]) > TESSERACT_NO_CONFIDENCE
    ]


def lines_from_words(words: list[TesseractWord]) -> list[OcrLine]:
    words_by_line: dict[tuple[str, str, str, str], list[TesseractWord]] = {}
    for word in words:
        words_by_line.setdefault(word.line_key, []).append(word)
    return [
        OcrLine(
            text=" ".join(word.text for word in line_words),
            confidence=round(min(word.confidence for word in line_words), 1),
        )
        for line_words in words_by_line.values()
    ]


@dataclass(frozen=True)
class TesseractEngine:
    language: str = "spa"
    name: str = "tesseract"

    def read_lines(self, photo_bytes: bytes) -> list[OcrLine]:
        completed = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", self.language, "tsv"],
            input=photo_bytes,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise UnreadablePhoto(completed.stderr.decode(errors="replace").strip())
        return lines_from_words(tesseract_words(completed.stdout.decode()))


OCR_ENGINES_BY_NAME = {"tesseract": TesseractEngine}


def ocr_engine_from_config(engine_name: str, language: str) -> OcrEngine:
    return OCR_ENGINES_BY_NAME[engine_name](language=language)
