import argparse
from pathlib import Path

from travel_companion.country_pack import GLOBAL_DISHES_FOLDER, KNOWN_DISHES_FILE, KnownDish, loaded_dishes_file

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACKS_DIR = REPO_ROOT / "packs"
DEFAULT_RESULTS_PATH = REPO_ROOT / "docs" / "results" / "T2-unreviewed-known-dishes.md"


def dish_folders_global_first(packs_dir: Path) -> list[Path]:
    folders_with_dishes = sorted(folder for folder in packs_dir.iterdir() if (folder / KNOWN_DISHES_FILE).is_file())
    return sorted(folders_with_dishes, key=lambda folder: folder.name != GLOBAL_DISHES_FOLDER)


def unreviewed_dish_row(dish: KnownDish, group: str) -> str:
    return f"| {dish.name} | {group} | {dish.source} |"


def group_section(folder: Path) -> list[str]:
    dishes = loaded_dishes_file(folder / KNOWN_DISHES_FILE)
    unreviewed_dishes = [dish for dish in dishes if not dish.reviewed]
    heading = f"## `packs/{folder.name}/{KNOWN_DISHES_FILE}`: {len(unreviewed_dishes)} of {len(dishes)} unreviewed"
    if not unreviewed_dishes:
        return [heading, "", "None.", ""]
    return [
        heading,
        "",
        "| Dish | Group | Source |",
        "|---|---|---|",
        *(unreviewed_dish_row(dish, folder.name) for dish in unreviewed_dishes),
        "",
    ]


def unreviewed_dishes_report(packs_dir: Path = DEFAULT_PACKS_DIR) -> str:
    lines = [
        "# T2: Known Dishes still to review",
        "",
        "Generated with `python -m travel_companion.unreviewed_dishes` from the YAML in `packs/`.",
        "A dish leaves this list when its entry says `reviewed: true`. Unreviewed dishes are still used; their cards say \"unreviewed\".",
        "",
    ]
    for folder in dish_folders_global_first(packs_dir):
        lines.extend(group_section(folder))
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="List the Known Dishes still to review.")
    parser.add_argument("--packs-dir", type=Path, default=DEFAULT_PACKS_DIR)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS_PATH)
    arguments = parser.parse_args()
    arguments.results.write_text(unreviewed_dishes_report(arguments.packs_dir), encoding="utf-8")


if __name__ == "__main__":
    main()
