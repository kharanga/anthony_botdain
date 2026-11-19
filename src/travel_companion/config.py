import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path("config/default.toml")


@dataclass(frozen=True)
class Config:
    country: str
    active_allergens: tuple[str, ...]
    home_currency: str
    rate: float
    data_dir: Path
    model_endpoint_url: str
    brightness_backend: str = "recording"
    backlight_dir: Path | None = None


def load_config(config_path: Path) -> Config:
    raw = tomllib.loads(Path(config_path).read_text())
    return Config(
        country=raw["country"],
        active_allergens=tuple(raw["active_allergens"]),
        home_currency=raw["home_currency"],
        rate=float(raw["rate"]),
        data_dir=Path(raw["data_dir"]),
        model_endpoint_url=raw["model"]["endpoint_url"],
        brightness_backend=raw.get("display", {}).get("brightness_backend", "recording"),
        backlight_dir=backlight_dir_from(raw.get("display", {})),
    )


def backlight_dir_from(display_section: dict) -> Path | None:
    configured_dir = display_section.get("backlight_dir", "")
    return Path(configured_dir) if configured_dir else None
