from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.ocr import OcrEngine, OcrLine, UnreadablePhoto


class ScoredOcrLine(BaseModel):
    text: str
    confidence: float
    low_confidence: bool


class OcrLinesCard(AnswerCard):
    lines: list[ScoredOcrLine]


def scored_lines(lines: list[OcrLine], low_confidence_threshold: float) -> list[ScoredOcrLine]:
    return [
        ScoredOcrLine(text=line.text, confidence=line.confidence, low_confidence=line.confidence < low_confidence_threshold)
        for line in lines
    ]


def ocr_lines_summary(lines: list[ScoredOcrLine]) -> str:
    if not lines:
        return "No text read from this photo."
    low_confidence_count = sum(line.low_confidence for line in lines)
    read_summary = f"Read {len(lines)} lines."
    if low_confidence_count == 0:
        return read_summary
    return f"{read_summary} {low_confidence_count} unclear: Ask staff."


def ocr_lines_card(engine: OcrEngine, lines: list[OcrLine], low_confidence_threshold: float) -> OcrLinesCard:
    scored = scored_lines(lines, low_confidence_threshold)
    evidence_source = f"OCR line ({engine.name})"
    return OcrLinesCard(
        kind="ocr_lines",
        title="Photo text",
        body=ocr_lines_summary(scored),
        evidence=[Evidence(source=evidence_source, text=line.text) for line in scored],
        lines=scored,
    )


def unreadable_photo_card(engine: OcrEngine, reason: str) -> AnswerCard:
    return AnswerCard(
        kind="unreadable_photo",
        title="Photo not readable",
        body="No text was read from this photo. Retake it.",
        evidence=[Evidence(source=f"OCR engine ({engine.name})", text=reason)],
    )


photo_ocr_router = APIRouter()


@photo_ocr_router.post("/api/photo", response_model=OcrLinesCard)
def post_photo(photo: UploadFile, request: Request):
    engine: OcrEngine = request.app.state.ocr_engine
    try:
        lines = engine.read_lines(photo.file.read())
    except UnreadablePhoto as unreadable:
        return JSONResponse(status_code=422, content=unreadable_photo_card(engine, str(unreadable)).model_dump())
    return ocr_lines_card(engine, lines, request.app.state.config.ocr_low_confidence_threshold)
