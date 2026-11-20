import re
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.intent_router import IntentCard, route_transcript
from travel_companion.model_client import ModelClient

Transcriber = Callable[[bytes], str]

WHISPER_BLANK_MARKERS = ("[BLANK_AUDIO]", "(silence)", "[silence]")
WHISPER_HASH_NUMBER = re.compile(r"#\s*(\d+)")


class SpeechToTextUnavailable(Exception):
    pass


def whisper_command(whisper_cli: str, model_path: Path, audio_path: Path) -> list[str]:
    return [whisper_cli, "-m", str(model_path), "-f", str(audio_path), "-l", "en", "-nt", "-np", "-ng"]


def whisper_transcriber(whisper_cli: str, model_path: Path) -> Transcriber:
    def transcribe(audio: bytes) -> str:
        if shutil.which(whisper_cli) is None:
            raise SpeechToTextUnavailable(f"{whisper_cli} is not installed")
        if not model_path.is_file():
            raise SpeechToTextUnavailable(f"whisper model {model_path} is missing")
        with tempfile.TemporaryDirectory() as recording_dir:
            audio_path = Path(recording_dir) / "push_to_talk.wav"
            audio_path.write_bytes(audio)
            completed = subprocess.run(
                whisper_command(whisper_cli, model_path, audio_path), capture_output=True, text=True
            )
        if completed.returncode != 0:
            raise SpeechToTextUnavailable(last_line_or(completed.stderr, f"{whisper_cli} failed"))
        return completed.stdout

    return transcribe


def last_line_or(output: str, fallback: str) -> str:
    lines = output.strip().splitlines()
    return lines[-1] if lines else fallback


def cleaned_transcript(raw_transcript: str) -> str:
    transcript = " ".join(raw_transcript.split())
    for marker in WHISPER_BLANK_MARKERS:
        transcript = transcript.replace(marker, "")
    return WHISPER_HASH_NUMBER.sub(r"number \1", transcript).strip()


def speech_unavailable_card(reason: str) -> AnswerCard:
    return AnswerCard(
        kind="speech_unavailable",
        title="Speech-to-text is not available",
        body="I couldn't turn your voice into text. Type the question instead.",
        evidence=[Evidence(source="whisper.cpp", text=reason)],
    )


def nothing_heard_card() -> AnswerCard:
    return AnswerCard(
        kind="nothing_heard",
        title="I didn't catch that",
        body="Hold the button, speak, then let go.",
        evidence=[Evidence(source="whisper.cpp", text="empty transcript")],
    )


def spoken_question_card(audio: bytes, transcriber: Transcriber, model_client: ModelClient) -> IntentCard | AnswerCard:
    try:
        transcript = cleaned_transcript(transcriber(audio))
    except SpeechToTextUnavailable as unavailable:
        return speech_unavailable_card(str(unavailable))
    if not transcript:
        return nothing_heard_card()
    return route_transcript(transcript, model_client)


def speech_router(transcriber: Transcriber) -> APIRouter:
    router = APIRouter()

    @router.post("/api/speech", response_model=IntentCard | AnswerCard)
    async def post_speech(request: Request) -> IntentCard | AnswerCard:
        audio = await request.body()
        return await run_in_threadpool(spoken_question_card, audio, transcriber, request.app.state.model_client)

    return router
