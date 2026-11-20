import argparse
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from travel_companion.allergen_terms import matched_allergen_terms
from travel_companion.country_pack import CountryPack, load_country_pack

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RESULTS_PATH = REPO_ROOT / "docs" / "results" / "T2-allergen-term-false-positives.md"
DEFAULT_LABELLED_LINES_PATH = REPO_ROOT / "tests" / "fixtures" / "labelled_menu_lines.yaml"
DEFAULT_PACKS = (
    (REPO_ROOT / "packs", "cr", ("shellfish",)),
    (REPO_ROOT / "tests" / "packs", "specimen", ("shellfish", "peanut")),
)


@dataclass(frozen=True)
class LabelledMenuLine:
    text: str
    allergens: tuple[str, ...]


@dataclass(frozen=True)
class LineOutcome:
    line: LabelledMenuLine
    allergen: str
    folded_terms: tuple[str, ...]
    accent_aware_terms: tuple[str, ...]

    @property
    def truly_contains(self) -> bool:
        return self.allergen in self.line.allergens

    @property
    def is_false_positive(self) -> bool:
        return bool(self.folded_terms) and not self.truly_contains

    @property
    def is_missed(self) -> bool:
        return not self.folded_terms and self.truly_contains

    @property
    def is_accent_only_false_positive(self) -> bool:
        return self.is_false_positive and not self.accent_aware_terms

    @property
    def is_accent_only_catch(self) -> bool:
        return bool(self.folded_terms) and self.truly_contains and not self.accent_aware_terms


def loaded_labelled_lines(path: Path) -> list[LabelledMenuLine]:
    raw_lines = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [LabelledMenuLine(text=raw["line"], allergens=tuple(raw["allergens"])) for raw in raw_lines]


def contains_phrase_accent_aware(text: str, phrase: str) -> bool:
    whole_words_pattern = rf"(?<!\w){re.escape(phrase.casefold())}(?!\w)"
    return re.search(whole_words_pattern, " ".join(text.casefold().split())) is not None


def line_outcome(pack: CountryPack, line: LabelledMenuLine, allergen: str) -> LineOutcome:
    folded_terms = tuple(term.text for term in matched_allergen_terms(pack, line.text, (allergen,)))
    accent_aware_terms = tuple(
        term.text for term in pack.terms_for(allergen) if contains_phrase_accent_aware(line.text, term.text)
    )
    return LineOutcome(line=line, allergen=allergen, folded_terms=folded_terms, accent_aware_terms=accent_aware_terms)


def line_outcomes(pack: CountryPack, lines: list[LabelledMenuLine], allergen: str) -> list[LineOutcome]:
    return [line_outcome(pack, line, allergen) for line in lines]


def outcome_row(outcome: LineOutcome) -> str:
    matched = ", ".join(outcome.folded_terms) or "none"
    return f"| {outcome.line.text} | {outcome.allergen} | {matched} | {'yes' if outcome.truly_contains else 'no'} |"


def outcome_table(title: str, outcomes: list[LineOutcome]) -> list[str]:
    if not outcomes:
        return [f"### {title}", "", "None.", ""]
    return [f"### {title}", "", "| Menu Line | Allergen | Matched terms | Truly contains |", "|---|---|---|---|"] + [
        outcome_row(outcome) for outcome in outcomes
    ] + [""]


def pack_section(pack: CountryPack, allergens: tuple[str, ...], lines: list[LabelledMenuLine]) -> list[str]:
    outcomes = [outcome for allergen in allergens for outcome in line_outcomes(pack, lines, allergen)]
    summary_rows = []
    for allergen in allergens:
        allergen_outcomes = [outcome for outcome in outcomes if outcome.allergen == allergen]
        summary_rows.append(
            f"| {allergen} | {sum(outcome.truly_contains for outcome in allergen_outcomes)} "
            f"| {sum(outcome.is_false_positive for outcome in allergen_outcomes)} "
            f"| {sum(outcome.is_accent_only_false_positive for outcome in allergen_outcomes)} "
            f"| {sum(outcome.is_missed for outcome in allergen_outcomes)} "
            f"| {sum(outcome.is_accent_only_catch for outcome in allergen_outcomes)} |"
        )
    return (
        [
            f"## Pack `{pack.folder.relative_to(REPO_ROOT) if pack.folder.is_relative_to(REPO_ROOT) else pack.folder}`",
            "",
            "| Allergen | Lines that truly contain it | False positives | of which accent-only | Missed | Caught only because accents are ignored |",
            "|---|---|---|---|---|---|",
        ]
        + summary_rows
        + [""]
        + outcome_table("False positives", [outcome for outcome in outcomes if outcome.is_false_positive])
        + outcome_table("Missed", [outcome for outcome in outcomes if outcome.is_missed])
        + outcome_table("Caught only because accents are ignored", [outcome for outcome in outcomes if outcome.is_accent_only_catch])
    )


def false_positives_report(
    packs: tuple[tuple[Path, str, tuple[str, ...]], ...], labelled_lines_path: Path, measured_on: date
) -> str:
    lines = loaded_labelled_lines(labelled_lines_path)
    sections = [
        line
        for packs_dir, country, allergens in packs
        for line in pack_section(load_country_pack(packs_dir, country, allergens), allergens, lines)
    ]
    header = [
        "# T2: Allergen Term false positives from accent- and case-insensitive matching",
        "",
        f"Measured {measured_on.isoformat()} with `python -m travel_companion.allergen_term_false_positives`.",
        f"Labelled specimen Menu Lines: `{labelled_lines_path.relative_to(REPO_ROOT) if labelled_lines_path.is_relative_to(REPO_ROOT) else labelled_lines_path}` ({len(lines)} lines, fake).",
        "",
        "Matching folds accents and case and needs whole words (`paella` does not match `Paellera`).",
        "A false positive is a line that names an Allergen Term but is labelled as not containing that Allergen.",
        "Accent-only means the line would not have matched if accents were respected (case still ignored).",
        "",
    ]
    return "\n".join(header + sections)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labelled-lines", type=Path, default=DEFAULT_LABELLED_LINES_PATH)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    arguments = parser.parse_args()
    report = false_positives_report(DEFAULT_PACKS, arguments.labelled_lines, date.today())
    arguments.results.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
