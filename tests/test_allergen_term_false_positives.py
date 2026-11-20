from datetime import date

from conftest import SPECIMEN_PACKS_DIR

from travel_companion.allergen_term_false_positives import false_positives_report


def test_the_report_lists_accent_only_false_positives_and_catches(tmp_path):
    labelled_lines_path = tmp_path / "lines.yaml"
    labelled_lines_path.write_text(
        "- line: Pizza Mani Rosse\n  allergens: []\n"
        "- line: POLLO EN SALSA DE MANI\n  allergens: [peanut]\n"
        "- line: Salsa de maníes\n  allergens: [peanut]\n"
        "- line: Gallo pinto\n  allergens: []\n"
    )

    report = false_positives_report(
        ((SPECIMEN_PACKS_DIR, "specimen", ("peanut",)),), labelled_lines_path, date(2026, 11, 19)
    )

    assert "| peanut | 2 | 1 | 1 | 1 | 1 |" in report
    assert "| Pizza Mani Rosse | peanut | maní | no |" in report
    assert "| Salsa de maníes | peanut | none | yes |" in report
