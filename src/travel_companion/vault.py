import base64
import binascii
import json
import math
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.database import connect
from travel_companion.vault_crypto import key_check_for, key_from_pin, key_matches_check, new_salt, open_sealed, seal

VaultState = Literal["needs_pin", "locked", "unlocked"]
Clock = Callable[[], float]

IDLE_LOCK_SECONDS = 120
FREE_WRONG_PIN_ATTEMPTS = 5
FIRST_WRONG_PIN_WAIT_SECONDS = 30
LONGEST_WRONG_PIN_WAIT_SECONDS = 3600
HTTP_TOO_MANY_ATTEMPTS = 429

VAULT_PAGE_PATH = Path(__file__).resolve().parent / "static" / "vault.html"
DOCUMENT_PURPOSE = b"vault-document"
SUMMARY_PURPOSE = b"vault-document-summary"
HTTP_LOCKED = 423
PHOTO_RESPONSE_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "sandbox",
}
PhotoContentType = Literal["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"]

VAULT_SCHEMA_STATEMENTS = [
    "CREATE TABLE IF NOT EXISTS vault_pin (id INTEGER PRIMARY KEY CHECK (id = 1), salt BLOB NOT NULL, key_check BLOB NOT NULL)",
    "CREATE SEQUENCE IF NOT EXISTS vault_document_ids START 1",
    "CREATE TABLE IF NOT EXISTS vault_documents (id INTEGER PRIMARY KEY DEFAULT nextval('vault_document_ids'), sealed_document BLOB NOT NULL)",
    "ALTER TABLE vault_documents ADD COLUMN IF NOT EXISTS sealed_summary BLOB",
]


class VaultSession:
    def __init__(self, clock: Clock = time.monotonic, idle_lock_seconds: float = IDLE_LOCK_SECONDS) -> None:
        self._key: bytes | None = None
        self._clock = clock
        self._idle_lock_seconds = idle_lock_seconds
        self._last_use_at = clock()
        self._wrong_pin_count = 0
        self._next_pin_attempt_at = clock()
        self.pin_check_lock = threading.Lock()
        self._lock_listeners: list[Callable[[], None]] = []

    def call_when_locked(self, listener: Callable[[], None]) -> None:
        self._lock_listeners.append(listener)

    def unlock(self, key: bytes) -> None:
        self._key = key
        self._last_use_at = self._clock()
        self._wrong_pin_count = 0

    def record_wrong_pin(self) -> None:
        self._wrong_pin_count += 1
        extra_wrong_attempts = self._wrong_pin_count - FREE_WRONG_PIN_ATTEMPTS
        if extra_wrong_attempts >= 0:
            wait_seconds = min(FIRST_WRONG_PIN_WAIT_SECONDS * 2**extra_wrong_attempts, LONGEST_WRONG_PIN_WAIT_SECONDS)
            self._next_pin_attempt_at = self._clock() + wait_seconds

    def seconds_until_pin_attempt_allowed(self) -> int:
        return max(0, math.ceil(self._next_pin_attempt_at - self._clock()))

    def lock(self) -> None:
        self._key = None
        for listener in self._lock_listeners:
            listener()

    def _lock_if_idle_too_long(self) -> None:
        if self._key is not None and self.locks_in_seconds() <= 0:
            self.lock()

    def locks_in_seconds(self) -> float:
        return self._idle_lock_seconds - (self._clock() - self._last_use_at)

    def unlocked_key(self) -> bytes | None:
        self._lock_if_idle_too_long()
        return self._key

    def key_for_use(self) -> bytes | None:
        key = self.unlocked_key()
        if key is not None:
            self._last_use_at = self._clock()
        return key


@dataclass(frozen=True)
class DocumentSummary:
    id: int
    label: str
    content_type: str


@dataclass(frozen=True)
class VaultDocument:
    id: int
    label: str
    content_type: str
    photo: bytes


class PinEntry(BaseModel):
    pin: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


class NewDocument(BaseModel):
    label: Annotated[str, Field(min_length=1, max_length=200)]
    content_type: PhotoContentType
    photo_base64: Annotated[str, Field(min_length=1)]


class VaultDocumentSummary(BaseModel):
    id: int
    label: str


class VaultCard(AnswerCard):
    vault_state: VaultState
    documents: list[VaultDocumentSummary]
    photo_url: str | None = None
    locks_in_seconds: int | None = None
    unlock_retry_in_seconds: int | None = None


def whole_seconds_until_lock(session: VaultSession) -> int:
    return max(0, math.ceil(session.locks_in_seconds()))


def set_up_vault_tables(database_path: Path) -> None:
    with connect(database_path) as connection:
        for statement in VAULT_SCHEMA_STATEMENTS:
            connection.execute(statement)


def stored_pin_salt_and_check(database_path: Path) -> tuple[bytes, bytes] | None:
    with connect(database_path) as connection:
        row = connection.execute("SELECT vault_pin.salt, vault_pin.key_check FROM vault_pin WHERE vault_pin.id = 1").fetchone()
    return None if row is None else (bytes(row[0]), bytes(row[1]))


def store_pin_salt_and_check(database_path: Path, salt: bytes, key_check: bytes) -> None:
    with connect(database_path) as connection:
        connection.execute("INSERT INTO vault_pin (id, salt, key_check) VALUES (1, ?, ?)", [salt, key_check])


def sealed_document_bytes(key: bytes, label: str, content_type: str, photo: bytes) -> bytes:
    plaintext = json.dumps(
        {"label": label, "content_type": content_type, "photo_base64": base64.b64encode(photo).decode()}
    ).encode()
    return seal(key, plaintext, DOCUMENT_PURPOSE)


def sealed_summary_bytes(key: bytes, label: str, content_type: str) -> bytes:
    return seal(key, json.dumps({"label": label, "content_type": content_type}).encode(), SUMMARY_PURPOSE)


def opened_document(key: bytes, document_id: int, sealed_document: bytes) -> VaultDocument:
    fields = json.loads(open_sealed(key, sealed_document, DOCUMENT_PURPOSE))
    return VaultDocument(
        id=document_id,
        label=fields["label"],
        content_type=fields["content_type"],
        photo=base64.b64decode(fields["photo_base64"]),
    )


def opened_summary(key: bytes, document_id: int, sealed_summary: bytes) -> DocumentSummary:
    fields = json.loads(open_sealed(key, sealed_summary, SUMMARY_PURPOSE))
    return DocumentSummary(id=document_id, label=fields["label"], content_type=fields["content_type"])


def store_sealed_document(database_path: Path, sealed_document: bytes, sealed_summary: bytes) -> int:
    with connect(database_path) as connection:
        row = connection.execute(
            "INSERT INTO vault_documents (sealed_document, sealed_summary) VALUES (?, ?) RETURNING vault_documents.id",
            [sealed_document, sealed_summary],
        ).fetchone()
    return row[0]


def add_missing_summaries(database_path: Path, key: bytes) -> None:
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT vault_documents.id, vault_documents.sealed_document FROM vault_documents "
            "WHERE vault_documents.sealed_summary IS NULL"
        ).fetchall()
        for document_id, sealed in rows:
            document = opened_document(key, document_id, bytes(sealed))
            connection.execute(
                "UPDATE vault_documents SET sealed_summary = ? WHERE vault_documents.id = ?",
                [sealed_summary_bytes(key, document.label, document.content_type), document_id],
            )


def all_document_summaries(database_path: Path, key: bytes) -> list[DocumentSummary]:
    with connect(database_path) as connection:
        rows = connection.execute(
            "SELECT vault_documents.id, vault_documents.sealed_summary FROM vault_documents ORDER BY vault_documents.id"
        ).fetchall()
    return [opened_summary(key, document_id, bytes(sealed)) for document_id, sealed in rows]


def one_document_summary(database_path: Path, key: bytes, document_id: int) -> DocumentSummary | None:
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT vault_documents.sealed_summary FROM vault_documents WHERE vault_documents.id = ?", [document_id]
        ).fetchone()
    return None if row is None else opened_summary(key, document_id, bytes(row[0]))


def one_document(database_path: Path, key: bytes, document_id: int) -> VaultDocument | None:
    with connect(database_path) as connection:
        row = connection.execute(
            "SELECT vault_documents.sealed_document FROM vault_documents WHERE vault_documents.id = ?", [document_id]
        ).fetchone()
    return None if row is None else opened_document(key, document_id, bytes(row[0]))


def photo_from_base64(photo_base64: str) -> bytes:
    try:
        return base64.b64decode(photo_base64, validate=True)
    except binascii.Error as error:
        raise HTTPException(status_code=422, detail="photo_base64 is not valid base64.") from error


def vault_tables_source(database_path: Path) -> str:
    return f"{database_path} (vault tables)"


def photo_url_for(document_id: int) -> str:
    return f"/api/vault/documents/{document_id}/photo"


def needs_pin_card(database_path: Path) -> VaultCard:
    return VaultCard(
        kind="vault",
        title="Set a vault PIN",
        body="Choose a 6-digit PIN to protect your documents.",
        evidence=[Evidence(source=vault_tables_source(database_path), text="no vault PIN set yet")],
        vault_state="needs_pin",
        documents=[],
    )


def locked_card(database_path: Path) -> VaultCard:
    return VaultCard(
        kind="vault",
        title="Vault locked",
        body="Enter your 6-digit PIN to open your documents.",
        evidence=[Evidence(source=vault_tables_source(database_path), text="documents are encrypted under the PIN")],
        vault_state="locked",
        documents=[],
    )


def wrong_pin_card(database_path: Path, retry_in_seconds: int) -> VaultCard:
    card = locked_card(database_path)
    if retry_in_seconds == 0:
        return card
    return card.model_copy(
        update={
            "body": f"Too many wrong PINs. Try again in {retry_in_seconds} seconds.",
            "unlock_retry_in_seconds": retry_in_seconds,
        }
    )


def unlocked_card(database_path: Path, documents: list[DocumentSummary]) -> VaultCard:
    return VaultCard(
        kind="vault",
        title="Vault",
        body=f"{len(documents)} documents.",
        evidence=[Evidence(source=vault_tables_source(database_path), text=f"{len(documents)} encrypted documents")],
        vault_state="unlocked",
        documents=[VaultDocumentSummary(id=document.id, label=document.label) for document in documents],
    )


def document_card(database_path: Path, document: DocumentSummary) -> VaultCard:
    return VaultCard(
        kind="vault",
        title=document.label,
        body=f"Document photo ({document.content_type}).",
        evidence=[Evidence(source=f"{vault_tables_source(database_path)} document {document.id}", text=document.label)],
        vault_state="unlocked",
        documents=[VaultDocumentSummary(id=document.id, label=document.label)],
        photo_url=photo_url_for(document.id),
    )


def vault_router(database_path: Path, session: VaultSession) -> APIRouter:
    set_up_vault_tables(database_path)
    router = APIRouter()

    def vault_card_for(key: bytes | None) -> VaultCard:
        if stored_pin_salt_and_check(database_path) is None:
            return needs_pin_card(database_path)
        if key is None:
            return locked_card(database_path)
        card = unlocked_card(database_path, all_document_summaries(database_path, key))
        return card.model_copy(update={"locks_in_seconds": whole_seconds_until_lock(session)})

    def current_vault_card() -> VaultCard:
        return vault_card_for(session.key_for_use())

    def key_or_locked_error() -> bytes:
        key = session.key_for_use()
        if key is None:
            raise HTTPException(status_code=HTTP_LOCKED, detail=locked_card(database_path).model_dump())
        return key

    def summary_or_not_found(key: bytes, document_id: int) -> DocumentSummary:
        summary = one_document_summary(database_path, key, document_id)
        if summary is None:
            raise HTTPException(status_code=404, detail="No such document in the vault.")
        return summary

    def document_or_not_found(key: bytes, document_id: int) -> VaultDocument:
        document = one_document(database_path, key, document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="No such document in the vault.")
        return document

    @router.get("/vault")
    def get_vault_page() -> FileResponse:
        return FileResponse(VAULT_PAGE_PATH)

    @router.get("/api/vault")
    def get_vault() -> VaultCard:
        return current_vault_card()

    @router.post("/api/vault/pin")
    def post_pin(entry: PinEntry) -> VaultCard:
        with session.pin_check_lock:
            if stored_pin_salt_and_check(database_path) is not None:
                raise HTTPException(status_code=409, detail="The vault PIN is already set.")
            salt = new_salt()
            key = key_from_pin(entry.pin, salt)
            store_pin_salt_and_check(database_path, salt, key_check_for(key))
            session.unlock(key)
        return current_vault_card()

    @router.post("/api/vault/unlock")
    def post_unlock(entry: PinEntry) -> VaultCard:
        with session.pin_check_lock:
            salt_and_check = stored_pin_salt_and_check(database_path)
            if salt_and_check is None:
                raise HTTPException(status_code=409, detail=needs_pin_card(database_path).model_dump())
            wait_seconds = session.seconds_until_pin_attempt_allowed()
            if wait_seconds > 0:
                session.lock()
                raise HTTPException(
                    status_code=HTTP_TOO_MANY_ATTEMPTS, detail=wrong_pin_card(database_path, wait_seconds).model_dump()
                )
            salt, key_check = salt_and_check
            key = key_from_pin(entry.pin, salt)
            if not key_matches_check(key, key_check):
                session.lock()
                session.record_wrong_pin()
                retry_in_seconds = session.seconds_until_pin_attempt_allowed()
                raise HTTPException(status_code=401, detail=wrong_pin_card(database_path, retry_in_seconds).model_dump())
            add_missing_summaries(database_path, key)
            session.unlock(key)
        return current_vault_card()

    @router.post("/api/vault/lock")
    def post_lock() -> VaultCard:
        session.lock()
        return current_vault_card()

    @router.get("/api/vault/state")
    def get_vault_state() -> VaultCard:
        return vault_card_for(session.unlocked_key())

    @router.post("/api/vault/activity")
    def post_activity() -> VaultCard:
        return current_vault_card()

    @router.post("/api/vault/documents")
    def post_document(new_document: NewDocument) -> VaultCard:
        key = key_or_locked_error()
        photo = photo_from_base64(new_document.photo_base64)
        document_id = store_sealed_document(
            database_path,
            sealed_document_bytes(key, new_document.label, new_document.content_type, photo),
            sealed_summary_bytes(key, new_document.label, new_document.content_type),
        )
        return document_card(database_path, summary_or_not_found(key, document_id))

    @router.get("/api/vault/documents/{document_id}")
    def get_document(document_id: int) -> VaultCard:
        key = key_or_locked_error()
        return document_card(database_path, summary_or_not_found(key, document_id))

    @router.get("/api/vault/documents/{document_id}/photo")
    def get_document_photo(document_id: int) -> Response:
        key = key_or_locked_error()
        document = document_or_not_found(key, document_id)
        return Response(content=document.photo, media_type=document.content_type, headers=PHOTO_RESPONSE_HEADERS)

    return router
