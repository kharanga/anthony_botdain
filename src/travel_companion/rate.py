from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.database import connect


@dataclass(frozen=True)
class CurrentRate:
    colones_per_dollar: float
    source: str


class RateChange(BaseModel):
    colones_per_dollar: Annotated[float, Field(gt=0, allow_inf_nan=False)]


def rate_text(colones_per_dollar: float) -> str:
    if colones_per_dollar.is_integer():
        return str(int(colones_per_dollar))
    return repr(colones_per_dollar)


def stored_rate(database_path: Path) -> float | None:
    with connect(database_path) as connection:
        row = connection.execute("SELECT rate.colones_per_dollar FROM rate WHERE rate.id = 1").fetchone()
    return None if row is None else row[0]


def store_rate(database_path: Path, colones_per_dollar: float) -> None:
    with connect(database_path) as connection:
        connection.execute("INSERT OR REPLACE INTO rate (id, colones_per_dollar) VALUES (1, ?)", [colones_per_dollar])


def current_rate(database_path: Path, configured_rate: float, config_path: Path) -> CurrentRate:
    saved_rate = stored_rate(database_path)
    if saved_rate is None:
        return CurrentRate(colones_per_dollar=configured_rate, source=str(config_path))
    return CurrentRate(colones_per_dollar=saved_rate, source=f"{database_path} (rate table)")


def rate_evidence(rate: CurrentRate) -> Evidence:
    return Evidence(source=rate.source, text=f"rate = {rate_text(rate.colones_per_dollar)} CRC per USD")


def rate_card(rate: CurrentRate) -> AnswerCard:
    return AnswerCard(
        kind="rate",
        title="Rate",
        body=f"₡{rate_text(rate.colones_per_dollar)} per US dollar.",
        evidence=[rate_evidence(rate)],
    )


def rate_router(database_path: Path, configured_rate: float, config_path: Path) -> APIRouter:
    router = APIRouter()

    def read_current_rate() -> CurrentRate:
        return current_rate(database_path, configured_rate, config_path)

    @router.get("/api/rate")
    def get_rate() -> AnswerCard:
        return rate_card(read_current_rate())

    @router.put("/api/rate")
    def put_rate(change: RateChange) -> AnswerCard:
        store_rate(database_path, change.colones_per_dollar)
        return rate_card(read_current_rate())

    return router
