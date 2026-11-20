import csv
import io
import os
import shutil
import subprocess
from dataclasses import dataclass
from functools import cached_property
from typing import Protocol

TESSERACT_WORD_LEVEL = "5"
TESSERACT_NO_CONFIDENCE = -1.0


@dataclass(frozen=True)
class OcrLine:
    text: str
    confidence: float


class UnreadablePhoto(Exception):
    pass


class EngineUnavailable(Exception):
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
        if shutil.which("tesseract") is None:
            raise EngineUnavailable("the tesseract CLI is not on PATH: brew install tesseract tesseract-lang")
        completed = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", self.language, "tsv"],
            input=photo_bytes,
            capture_output=True,
        )
        if completed.returncode != 0:
            raise UnreadablePhoto(completed.stderr.decode(errors="replace").strip())
        return lines_from_words(tesseract_words(completed.stdout.decode()))


PADDLEOCR_LANGUAGE_BY_TESSERACT_LANGUAGE = {"spa": "es", "eng": "en", "vie": "vi"}
PADDLEOCR_SKIP_MODEL_HOSTER_CHECK = "PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"
PADDLEOCR_NOT_INSTALLED ="PaddleOCR is not installed: .venv/bin/pip install -e '.[paddleocr]'"


def paddleocr_language(language: str) -> str:
    return PADDLEOCR_LANGUAGE_BY_TESSERACT_LANGUAGE.get(language, language)


def decoded_image(photo_bytes: bytes):
    import cv2
    import numpy

    image = cv2.imdecode(numpy.frombuffer(photo_bytes, dtype=numpy.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise UnreadablePhoto("the photo could not be decoded as an image")
    return image


@dataclass(frozen=True)
class PaddleOcrEngine:
    language: str = "spa"
    name: str = "paddleocr"

    @cached_property
    def pipeline(self):
        os.environ.setdefault(PADDLEOCR_SKIP_MODEL_HOSTER_CHECK, "True")
        try:
            from paddleocr import PaddleOCR
        except ImportError as missing:
            raise EngineUnavailable(PADDLEOCR_NOT_INSTALLED) from missing
        return PaddleOCR(
            lang=paddleocr_language(self.language),
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    def read_lines(self, photo_bytes: bytes) -> list[OcrLine]:
        pipeline = self.pipeline
        return [
            OcrLine(text=text.strip(), confidence=round(score * 100, 1))
            for page in pipeline.predict(decoded_image(photo_bytes))
            for text, score in zip(page["rec_texts"], page["rec_scores"])
            if text.strip()
        ]


OCR_ENGINES_BY_NAME = {"tesseract": TesseractEngine, "paddleocr": PaddleOcrEngine}


def ocr_engine_from_config(engine_name: str, language: str) -> OcrEngine:
    return OCR_ENGINES_BY_NAME[engine_name](language=language)
