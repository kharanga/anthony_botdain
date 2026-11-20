import argparse
import re
import statistics
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from travel_companion.country_pack import load_country_pack
from travel_companion.ocr import OCR_ENGINES_BY_NAME, EngineUnavailable, OcrEngine, UnreadablePhoto
from travel_companion.text_folding import accent_and_case_folded

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PHOTOS_DIR = REPO_ROOT / "specimens" / "photos"
DEFAULT_RESULTS_PATH = REPO_ROOT / "docs" / "results" / "T3-ocr-benchmark-specimen.md"
DEFAULT_PACKS_DIR = REPO_ROOT / "packs"
PHOTO_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff")
TRANSCRIPTION_SUFFIX = ".txt"
COLON_SIGN = "₡"


def case_folded(text: str) -> str:
    return " ".join(text.casefold().split())


MATCHING_MODES: dict[str, Callable[[str], str]] = {
    "accent-aware": case_folded,
    "accent-insensitive": accent_and_case_folded,
}


@dataclass(frozen=True)
class BenchmarkPhoto:
    photo_path: Path
    transcription: str


@dataclass(frozen=True)
class TermCounts:
    expected: int
    found: int
    false_positives: int


@dataclass(frozen=True)
class PhotoReading:
    photo: BenchmarkPhoto
    ocr_text: str
    seconds: float
    unreadable_reason: str | None
    term_counts_by_mode: dict[str, TermCounts]
    missed_terms_by_mode: dict[str, tuple[str, ...]]
    false_positive_terms_by_mode: dict[str, tuple[str, ...]]


def whitespace_collapsed(text: str) -> str:
    return " ".join(text.split())


def edit_distance(reference: str, hypothesis: str) -> int:
    previous_row = list(range(len(hypothesis) + 1))
    for reference_index, reference_character in enumerate(reference, start=1):
        current_row = [reference_index]
        for hypothesis_index, hypothesis_character in enumerate(hypothesis, start=1):
            current_row.append(
                min(
                    previous_row[hypothesis_index] + 1,
                    current_row[hypothesis_index - 1] + 1,
                    previous_row[hypothesis_index - 1] + (reference_character != hypothesis_character),
                )
            )
        previous_row = current_row
    return previous_row[-1]


def benchmark_photos(photos_dir: Path) -> tuple[list[BenchmarkPhoto], list[Path]]:
    photo_paths = sorted(path for path in photos_dir.iterdir() if path.suffix.lower() in PHOTO_SUFFIXES)
    transcribed = [path for path in photo_paths if path.with_suffix(TRANSCRIPTION_SUFFIX).is_file()]
    untranscribed = [path for path in photo_paths if path not in transcribed]
    photos = [
        BenchmarkPhoto(photo_path=path, transcription=path.with_suffix(TRANSCRIPTION_SUFFIX).read_text(encoding="utf-8"))
        for path in transcribed
    ]
    return photos, untranscribed


def term_occurrences(text: str, term: str, fold: Callable[[str], str]) -> int:
    whole_words_pattern = rf"(?<!\w){re.escape(fold(term))}(?!\w)"
    return len(re.findall(whole_words_pattern, fold(text)))


def photo_reading(
    engine: OcrEngine, photo: BenchmarkPhoto, terms: tuple[str, ...]
) -> PhotoReading:
    started = time.perf_counter()
    try:
        ocr_text = "\n".join(line.text for line in engine.read_lines(photo.photo_path.read_bytes()))
        unreadable_reason = None
    except UnreadablePhoto as unreadable:
        ocr_text = ""
        unreadable_reason = str(unreadable)
    seconds = time.perf_counter() - started
    term_counts_by_mode = {}
    missed_terms_by_mode = {}
    false_positive_terms_by_mode = {}
    for mode, fold in MATCHING_MODES.items():
        expected_by_term = {term: term_occurrences(photo.transcription, term, accent_and_case_folded) for term in terms}
        read_by_term = {term: term_occurrences(ocr_text, term, fold) for term in terms}
        found_by_term = {term: min(expected_by_term[term], read_by_term[term]) for term in terms}
        extra_by_term = {term: max(0, read_by_term[term] - expected_by_term[term]) for term in terms}
        term_counts_by_mode[mode] = TermCounts(
            expected=sum(expected_by_term.values()),
            found=sum(found_by_term.values()),
            false_positives=sum(extra_by_term.values()),
        )
        missed_terms_by_mode[mode] = tuple(term for term in terms if found_by_term[term] < expected_by_term[term])
        false_positive_terms_by_mode[mode] = tuple(term for term in terms if extra_by_term[term])
    return PhotoReading(
        photo=photo,
        ocr_text=ocr_text,
        seconds=seconds,
        unreadable_reason=unreadable_reason,
        term_counts_by_mode=term_counts_by_mode,
        missed_terms_by_mode=missed_terms_by_mode,
        false_positive_terms_by_mode=false_positive_terms_by_mode,
    )


def character_error_rate(readings: list[PhotoReading], fold: Callable[[str], str]) -> float:
    references = [fold(whitespace_collapsed(reading.photo.transcription)) for reading in readings]
    hypotheses = [fold(whitespace_collapsed(reading.ocr_text)) for reading in readings]
    total_characters = sum(len(reference) for reference in references)
    total_edits = sum(edit_distance(reference, hypothesis) for reference, hypothesis in zip(references, hypotheses))
    return total_edits / total_characters if total_characters else 0.0


def percentage(rate: float) -> str:
    return f"{rate * 100:.1f}%"


def recall_cell(found: int, expected: int) -> str:
    share = f"{round(found / expected * 100)}%" if expected else "n/a"
    return f"{found}/{expected} ({share})"


def summed_term_counts(readings: list[PhotoReading], mode: str) -> TermCounts:
    counts = [reading.term_counts_by_mode[mode] for reading in readings]
    return TermCounts(
        expected=sum(count.expected for count in counts),
        found=sum(count.found for count in counts),
        false_positives=sum(count.false_positives for count in counts),
    )


def colon_signs_kept_cell(readings: list[PhotoReading]) -> str:
    printed = sum(reading.photo.transcription.count(COLON_SIGN) for reading in readings)
    kept = sum(min(reading.ocr_text.count(COLON_SIGN), reading.photo.transcription.count(COLON_SIGN)) for reading in readings)
    return f"{kept}/{printed}"


def engine_summary_row(engine_name: str, readings: list[PhotoReading]) -> str:
    accent_aware = summed_term_counts(readings, "accent-aware")
    accent_insensitive = summed_term_counts(readings, "accent-insensitive")
    median_seconds = statistics.median(reading.seconds for reading in readings)
    return (
        f"| {engine_name} | {len(readings)} "
        f"| {percentage(character_error_rate(readings, lambda text: text))} "
        f"| {percentage(character_error_rate(readings, accent_and_case_folded))} "
        f"| {recall_cell(accent_aware.found, accent_aware.expected)} | {accent_aware.false_positives} "
        f"| {recall_cell(accent_insensitive.found, accent_insensitive.expected)} | {accent_insensitive.false_positives} "
        f"| {colon_signs_kept_cell(readings)} | {median_seconds:.2f} |"
    )


def terms_cell(terms: tuple[str, ...]) -> str:
    return ", ".join(terms) or "none"


def photo_row(engine_name: str, reading: PhotoReading) -> str:
    return (
        f"| {engine_name} | `{reading.photo.photo_path.name}` "
        f"| {percentage(character_error_rate([reading], lambda text: text))} "
        f"| {terms_cell(reading.missed_terms_by_mode['accent-aware'])} "
        f"| {terms_cell(reading.missed_terms_by_mode['accent-insensitive'])} "
        f"| {terms_cell(reading.false_positive_terms_by_mode['accent-insensitive'])} "
        f"| {reading.unreadable_reason or ''} |"
    )


def ocr_text_section(engine_name: str, reading: PhotoReading) -> list[str]:
    return [f"#### {engine_name}: `{reading.photo.photo_path.name}`", "", "```text", reading.ocr_text, "```", ""]


def displayed_path(path: Path) -> Path:
    resolved = path.resolve()
    return resolved.relative_to(REPO_ROOT) if resolved.is_relative_to(REPO_ROOT) else path


def ocr_benchmark_report(
    engines: list[OcrEngine],
    photos_dir: Path,
    packs_dir: Path,
    country: str,
    measured_on: date,
    include_ocr_text: bool = False,
) -> str:
    pack = load_country_pack(packs_dir, country, ())
    terms = tuple(dict.fromkeys(term.text for term in pack.allergen_terms))
    allergens = ", ".join(dict.fromkeys(term.allergen for term in pack.allergen_terms))
    photos, untranscribed = benchmark_photos(photos_dir)
    readings_by_engine: dict[str, list[PhotoReading]] = {}
    unavailable_reasons: dict[str, str] = {}
    for engine in engines:
        try:
            readings_by_engine[engine.name] = [photo_reading(engine, photo, terms) for photo in photos]
        except EngineUnavailable as unavailable:
            unavailable_reasons[engine.name] = str(unavailable)
    header = [
        "# T3: OCR benchmark",
        "",
        f"Measured {measured_on.isoformat()} with `python -m travel_companion.ocr_benchmark`.",
        f"Photos: `{displayed_path(photos_dir)}` ({len(photos)} with a transcription).",
        f"Allergen Terms: `{displayed_path(pack.folder)}` ({allergens}, {len(terms)} terms).",
        "",
        "Character error rate is edit distance over the transcription length, with all whitespace collapsed to one space,"
        " so line breaks and column gaps do not count. The folded column ignores accents and case.",
        "Term recall counts Allergen Term occurrences in the transcription (accents and case ignored) that are also in the"
        " OCR text. Accent-aware matching ignores case but needs the accents to match; accent-insensitive matching is what"
        " the app uses. A false positive is an occurrence in the OCR text beyond those in the transcription.",
        "Colón signs kept counts ₡ that survive OCR. Seconds is the median per photo; the first photo includes model load.",
        "",
    ]
    skipped = [f"Skipped (no transcription): {', '.join(f'`{path.name}`' for path in untranscribed)}", ""] if untranscribed else []
    unavailable = [f"`{name}` not measured: {reason}" for name, reason in unavailable_reasons.items()]
    summary = [
        "## Per engine",
        "",
        "| Engine | Photos | Character error rate | Folded character error rate "
        "| Term recall, accent-aware | False positives, accent-aware "
        "| Term recall, accent-insensitive | False positives, accent-insensitive "
        "| Colón signs kept | Seconds |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ] + [engine_summary_row(name, readings) for name, readings in readings_by_engine.items() if readings]
    per_photo = [
        "",
        "## Per photo",
        "",
        "| Engine | Photo | Character error rate | Missed, accent-aware | Missed, accent-insensitive "
        "| False positives, accent-insensitive | Unreadable |",
        "|---|---|---|---|---|---|---|",
    ] + [photo_row(name, reading) for name, readings in readings_by_engine.items() for reading in readings]
    ocr_texts = (
        ["", "## OCR text", ""]
        + [line for name, readings in readings_by_engine.items() for reading in readings for line in ocr_text_section(name, reading)]
        if include_ocr_text
        else []
    )
    return "\n".join(header + skipped + summary + ([""] + unavailable if unavailable else []) + per_photo + ocr_texts) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--photos", type=Path, default=DEFAULT_PHOTOS_DIR)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    parser.add_argument("--packs-dir", type=Path, default=DEFAULT_PACKS_DIR)
    parser.add_argument("--country", default="cr")
    parser.add_argument("--language", default="spa")
    parser.add_argument("--engines", nargs="+", default=list(OCR_ENGINES_BY_NAME), choices=list(OCR_ENGINES_BY_NAME))
    parser.add_argument("--include-ocr-text", action="store_true")
    arguments = parser.parse_args()
    engines = [OCR_ENGINES_BY_NAME[name](language=arguments.language) for name in arguments.engines]
    report = ocr_benchmark_report(
        engines, arguments.photos, arguments.packs_dir, arguments.country, date.today(), arguments.include_ocr_text
    )
    arguments.results.parent.mkdir(parents=True, exist_ok=True)
    arguments.results.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
