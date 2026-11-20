import argparse
import platform
import re
import statistics
import subprocess
import tempfile
import time
import tomllib
import wave
from datetime import date
from pathlib import Path

from travel_companion.intent_router import route_transcript
from travel_companion.speech_to_text import cleaned_transcript, whisper_transcriber

DEFAULT_SAMPLES_PATH = Path("specimens/intent_samples.toml")
DEFAULT_RESULTS_PATH = Path("docs/results/T6-speech-to-text.md")
DEFAULT_MODEL_PATH = Path("models/ggml-base.en.bin")
DEFAULT_SAMPLE_COUNT = 12
SAY_VOICE = "Samantha"


def load_spoken_samples(samples_path: Path, sample_count: int) -> list[dict]:
    samples = tomllib.loads(samples_path.read_text())["sample"]
    return samples[:: max(1, len(samples) // sample_count)][:sample_count]


def spoken_wav_path(text: str, wav_path: Path) -> Path:
    subprocess.run(
        ["say", "-v", SAY_VOICE, "-o", str(wav_path), "--file-format=WAVE", "--data-format=LEI16@16000", text],
        check=True,
    )
    return wav_path


def audio_seconds(wav_path: Path) -> float:
    with wave.open(str(wav_path)) as recording:
        return recording.getnframes() / recording.getframerate()


def comparable_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def word_edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous_row = list(range(len(hypothesis) + 1))
    for reference_index, reference_word in enumerate(reference, start=1):
        current_row = [reference_index]
        for hypothesis_index, hypothesis_word in enumerate(hypothesis, start=1):
            substitution_cost = previous_row[hypothesis_index - 1] + (reference_word != hypothesis_word)
            current_row.append(min(previous_row[hypothesis_index] + 1, current_row[-1] + 1, substitution_cost))
        previous_row = current_row
    return previous_row[-1]


def routes_like_reference(sample: dict, transcript: str) -> bool:
    card = route_transcript(transcript)
    return card.intent == sample.get("intent") and card.details == sample.get("details", {})


def measured_sample(sample: dict, wav_path: Path, transcribe) -> dict:
    audio = wav_path.read_bytes()
    started = time.perf_counter()
    transcript = cleaned_transcript(transcribe(audio))
    elapsed_seconds = time.perf_counter() - started
    reference_words = comparable_words(sample["transcript"])
    return {
        "reference": sample["transcript"],
        "transcript": transcript,
        "audio_seconds": audio_seconds(wav_path),
        "elapsed_seconds": elapsed_seconds,
        "word_errors": word_edit_distance(reference_words, comparable_words(transcript)),
        "reference_word_count": len(reference_words),
        "routes_like_reference": routes_like_reference(sample, transcript),
    }


def measured_samples(samples: list[dict], model_path: Path, whisper_cli: str) -> list[dict]:
    transcribe = whisper_transcriber(whisper_cli, model_path)
    with tempfile.TemporaryDirectory() as recordings_dir:
        wav_paths = [spoken_wav_path(sample["transcript"], Path(recordings_dir) / f"sample_{index}.wav") for index, sample in enumerate(samples)]
        transcribe(wav_paths[0].read_bytes())
        return [measured_sample(sample, wav_path, transcribe) for sample, wav_path in zip(samples, wav_paths)]


def sample_row(measurement: dict) -> str:
    routed = "yes" if measurement["routes_like_reference"] else "NO"
    return (
        f"| {measurement['reference']} | {measurement['transcript']} | {measurement['word_errors']} | {routed} "
        f"| {measurement['audio_seconds']:.1f} | {measurement['elapsed_seconds']:.2f} |"
    )


def speech_report(measurements: list[dict], model_path: Path, run_date: date) -> str:
    total_errors = sum(measurement["word_errors"] for measurement in measurements)
    total_words = sum(measurement["reference_word_count"] for measurement in measurements)
    routed_count = sum(measurement["routes_like_reference"] for measurement in measurements)
    elapsed = [measurement["elapsed_seconds"] for measurement in measurements]
    real_time_factors = [measurement["elapsed_seconds"] / measurement["audio_seconds"] for measurement in measurements]
    rows = "\n".join(sample_row(measurement) for measurement in measurements)
    return f"""# T6: Speech-to-text accuracy and latency

Run on {run_date.isoformat()} with `.venv/bin/python -m travel_companion.speech_benchmark`.

## Machine

- {platform.machine()}, {platform.system()} {platform.release()}
- Python {platform.python_version()}
- whisper.cpp `whisper-cli` from Homebrew, model `{model_path.name}`, English only, CPU only (`-ng`)

## Method

{len(measurements)} sample questions from `specimens/intent_samples.toml` are spoken by macOS `say` (voice {SAY_VOICE}) into 16 kHz mono WAV files at benchmark time; they are synthetic, so no real voice is recorded or committed. Each file goes through the same `whisper-cli` call that `POST /api/speech` makes, after one warm-up call. Latency is wall time for that call, including loading the model, because the app starts `whisper-cli` once per question. Word error rate compares lowercase words with punctuation removed, so "five" against "5" counts as an error. "Routes the same" checks that the transcript reaches the same intent with the same details as the typed sample, which is what the user sees.

Synthetic speech is cleaner than a real voice in a restaurant, so these numbers are a best case. Measure again with real recordings and the USB mic in T15.

## Summary

- Word error rate: {total_errors} errors in {total_words} words ({100 * total_errors / total_words:.1f}%)
- Routes the same as the typed question: {routed_count} of {len(measurements)}
- Median latency: {statistics.median(elapsed):.2f} s; slowest {max(elapsed):.2f} s
- Median real-time factor (latency / audio length): {statistics.median(real_time_factors):.2f}

## Per sample

| Spoken | whisper.cpp heard | Word errors | Routes the same | Audio, s | Latency, s |
| --- | --- | --- | --- | --- | --- |
{rows}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure whisper.cpp on spoken sample questions.")
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--whisper-cli", default="whisper-cli")
    parser.add_argument("--count", type=int, default=DEFAULT_SAMPLE_COUNT)
    arguments = parser.parse_args()
    measurements = measured_samples(load_spoken_samples(arguments.samples, arguments.count), arguments.model, arguments.whisper_cli)
    report = speech_report(measurements, arguments.model, date.today())
    arguments.results.write_text(report)
    print(report)


if __name__ == "__main__":
    main()
