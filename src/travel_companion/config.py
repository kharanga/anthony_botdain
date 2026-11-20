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
    packs_dir: Path = Path("packs")
    brightness_backend: str = "recording"
    backlight_dir: Path | None = None
    whisper_cli: str = "whisper-cli"
    whisper_model_path: Path = Path("models/ggml-base.en.bin")
    ocr_engine: str = "tesseract"
    ocr_language: str = "spa"
    ocr_low_confidence_threshold: float = 70.0


def load_config(config_path: Path) -> Config:
    raw = tomllib.loads(Path(config_path).read_text())
    return Config(
        country=raw["country"],
        active_allergens=tuple(raw["active_allergens"]),
        home_currency=raw["home_currency"],
        rate=float(raw["rate"]),
        data_dir=Path(raw["data_dir"]),
        model_endpoint_url=raw["model"]["endpoint_url"],
        packs_dir=Path(raw.get("packs_dir", "packs")),
        brightness_backend=raw.get("display", {}).get("brightness_backend", "recording"),
        backlight_dir=backlight_dir_from(raw.get("display", {})),
        whisper_cli=raw.get("speech", {}).get("whisper_cli", "whisper-cli"),
        whisper_model_path=Path(raw.get("speech", {}).get("whisper_model_path", "models/ggml-base.en.bin")),
        ocr_engine=raw.get("ocr", {}).get("engine", "tesseract"),
        ocr_language=raw.get("ocr", {}).get("language", "spa"),
        ocr_low_confidence_threshold=float(raw.get("ocr", {}).get("low_confidence_threshold", 70.0)),
    )


def backlight_dir_from(display_section: dict) -> Path | None:
    configured_dir = display_section.get("backlight_dir", "")
    return Path(configured_dir) if configured_dir else None
