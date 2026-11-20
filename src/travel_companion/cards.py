from typing import Literal

from pydantic import BaseModel

CardKind = Literal["status", "rate", "answer", "model_unavailable", "vault", "display", "intent", "unsupported_intent"]


class Evidence(BaseModel):
    source: str
    text: str


class AnswerCard(BaseModel):
    kind: CardKind
    title: str
    body: str
    evidence: list[Evidence]
