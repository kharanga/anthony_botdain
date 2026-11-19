from typing import Literal

from pydantic import BaseModel

CardKind = Literal["status", "answer", "model_unavailable"]


class Evidence(BaseModel):
    source: str
    text: str


class AnswerCard(BaseModel):
    kind: CardKind
    title: str
    body: str
    evidence: list[Evidence]
