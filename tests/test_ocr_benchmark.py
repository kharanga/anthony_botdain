import shutil
from datetime import date
from pathlib import Path

from conftest import REPO_PACKS_DIR

from travel_companion.ocr import EngineUnavailable, OcrLine, TesseractEngine
from travel_companion.ocr_benchmark import ocr_benchmark_report

SPECIMEN_MENU = Path(__file__).resolve().parent.parent / "specimens" / "photos" / "specimen-menu.png"
MEASURED_ON = date(2026, 11, 19)


class ScriptedEngine:
    def __init__(self, name: str, lines: list[str]):
        self.name = name
        self.lines = lines

    def read_lines(self, photo_bytes: bytes) -> list[OcrLine]:
        return [OcrLine(text=line, confidence=90.0) for line in self.lines]


class MissingEngine:
    name = "missing"

    def read_lines(self, photo_bytes: bytes) -> list[OcrLine]:
        raise EngineUnavailable("missing is not installed")


def photo_folder_with(tmp_path: Path, transcriptions: dict[str, str]) -> Path:
    folder = tmp_path / "photos"
    folder.mkdir()
    for stem, transcription in transcriptions.items():
        shutil.copy(SPECIMEN_MENU, folder / f"{stem}.png")
        (folder / f"{stem}.txt").write_text(transcription, encoding="utf-8")
    return folder


def report_for(photo_folder: Path, engines: list) -> str:
    return ocr_benchmark_report(engines, photo_folder, REPO_PACKS_DIR, "cr", MEASURED_ON)


def test_a_perfect_read_has_zero_character_error_and_full_term_recall(tmp_path):
    folder = photo_folder_with(tmp_path, {"menu": "Sopa de camarón\nCasado  ₡3.800\n"})
    engine = ScriptedEngine("perfect", ["Sopa de camarón", "Casado ₡3.800"])

    report = report_for(folder, [engine])

    assert "| perfect | 1 | 0.0% | 0.0% | 1/1 (100%) | 0 | 1/1 (100%) | 0 | 1/1 |" in report


def test_a_dropped_accent_is_missed_only_by_accent_aware_matching(tmp_path):
    folder = photo_folder_with(tmp_path, {"menu": "Sopa de camarón\n"})
    engine = ScriptedEngine("no-accents", ["Sopa de camaron"])

    report = report_for(folder, [engine])

    assert "| no-accents | 1 | 6.7% | 0.0% | 0/1 (0%) | 0 | 1/1 (100%) | 0 | 0/0 |" in report


def test_a_misread_that_creates_an_allergen_term_is_a_false_positive(tmp_path):
    folder = photo_folder_with(tmp_path, {"menu": "Jugo de mora\n"})
    engine = ScriptedEngine("hallucinating", ["Jugo de mora", "MARISCOS"])

    report = report_for(folder, [engine])

    assert "| 0/0 (n/a) | 1 | 0/0 (n/a) | 1 |" in report


def test_photos_without_a_transcription_are_listed_as_skipped(tmp_path):
    folder = photo_folder_with(tmp_path, {"menu": "Jugo de mora\n"})
    shutil.copy(SPECIMEN_MENU, folder / "untyped.png")

    report = report_for(folder, [ScriptedEngine("perfect", ["Jugo de mora"])])

    assert "Skipped (no transcription): `untyped.png`" in report


def test_an_engine_that_is_not_installed_is_reported_instead_of_measured(tmp_path):
    folder = photo_folder_with(tmp_path, {"menu": "Jugo de mora\n"})

    report = report_for(folder, [ScriptedEngine("perfect", ["Jugo de mora"]), MissingEngine()])

    assert "| perfect | 1 | 0.0% |" in report
    assert "`missing` not measured: missing is not installed" in report


def test_tesseract_on_the_specimen_menu_finds_the_shellfish_term_and_drops_the_colon_sign(tmp_path):
    folder = photo_folder_with(
        tmp_path,
        {
            "menu": "SODA LA ESPECIMEN\nGallo pinto con huevo ₡2.500\nArroz con camarones ₡6.000\n"
            "Ceviche de pescado ₡4.500\nPlátanos maduros ₡1.500\nCafé con leche ₡1.200\nJugo de piña ₡1.800\n"
        },
    )

    report = report_for(folder, [TesseractEngine()])

    assert "| tesseract | 1 |" in report
    assert "| 1/1 (100%) | 0 | 1/1 (100%) | 0 | 0/6 |" in report
