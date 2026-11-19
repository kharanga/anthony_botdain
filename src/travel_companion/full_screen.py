from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from travel_companion.brightness import BrightnessBackend
from travel_companion.cards import AnswerCard, Evidence
from travel_companion.vault import HTTP_LOCKED, VaultCard, VaultSession, document_card, locked_card, one_document_summary

FULL_SCREEN_PAGE_PATH = Path(__file__).resolve().parent / "static" / "full_screen.html"


class DisplayCard(AnswerCard):
    level: int
    max_level: int
    full_screen_document_id: int | None


class FullScreenView:
    def __init__(self, brightness: BrightnessBackend) -> None:
        self.brightness = brightness
        self.document_id: int | None = None
        self._level_before_opening: int | None = None

    def open(self, document_id: int) -> None:
        if self._level_before_opening is None:
            self._level_before_opening = self.brightness.level()
        self.document_id = document_id
        self.brightness.set_level(self.brightness.max_level())

    def close(self) -> None:
        if self._level_before_opening is not None:
            self.brightness.set_level(self._level_before_opening)
        self._level_before_opening = None
        self.document_id = None


def display_card(view: FullScreenView) -> DisplayCard:
    level = view.brightness.level()
    max_level = view.brightness.max_level()
    return DisplayCard(
        kind="display",
        title="Screen brightness",
        body=f"Brightness {level} of {max_level}.",
        evidence=[Evidence(source=view.brightness.description(), text=f"brightness = {level}, max_brightness = {max_level}")],
        level=level,
        max_level=max_level,
        full_screen_document_id=view.document_id,
    )


def full_screen_router(database_path: Path, session: VaultSession, view: FullScreenView) -> APIRouter:
    router = APIRouter()
    session.call_when_locked(view.close)

    def key_or_close_and_locked_error() -> bytes:
        key = session.unlocked_key()
        if key is None:
            view.close()
            raise HTTPException(status_code=HTTP_LOCKED, detail=locked_card(database_path).model_dump())
        return key

    def full_screen_card(key: bytes, document_id: int) -> VaultCard:
        document = one_document_summary(database_path, key, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="No such document in the vault.")
        return document_card(database_path, document)

    @router.get("/vault/full-screen/{document_id}")
    def get_full_screen_page(document_id: int) -> FileResponse:
        return FileResponse(FULL_SCREEN_PAGE_PATH)

    @router.post("/api/vault/documents/{document_id}/full-screen")
    def post_open_full_screen(document_id: int) -> VaultCard:
        card = full_screen_card(key_or_close_and_locked_error(), document_id)
        view.open(document_id)
        return card

    @router.get("/api/vault/full-screen")
    def get_full_screen() -> VaultCard:
        key = key_or_close_and_locked_error()
        if view.document_id is None:
            raise HTTPException(status_code=404, detail="No document is open full-screen.")
        return full_screen_card(key, view.document_id)

    @router.post("/api/vault/full-screen/close")
    def post_close_full_screen() -> DisplayCard:
        view.close()
        return display_card(view)

    @router.get("/api/display/brightness")
    def get_brightness() -> DisplayCard:
        return display_card(view)

    return router
