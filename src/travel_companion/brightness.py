from pathlib import Path
from typing import Protocol

RECORDING_STARTING_LEVEL = 128
RECORDING_MAX_LEVEL = 255
SYSFS_BACKLIGHT_ROOT = Path("/sys/class/backlight")


class BrightnessBackend(Protocol):
    def level(self) -> int: ...

    def max_level(self) -> int: ...

    def set_level(self, level: int) -> None: ...

    def description(self) -> str: ...


class RecordingBrightness:
    def __init__(self, starting_level: int = RECORDING_STARTING_LEVEL, max_level: int = RECORDING_MAX_LEVEL) -> None:
        self._level = starting_level
        self._max_level = max_level
        self.levels_set: list[int] = []

    def level(self) -> int:
        return self._level

    def max_level(self) -> int:
        return self._max_level

    def set_level(self, level: int) -> None:
        self._level = level
        self.levels_set.append(level)

    def description(self) -> str:
        return "recording brightness backend (no backlight on this machine)"


class SysfsBrightness:
    def __init__(self, device_dir: Path) -> None:
        self._device_dir = device_dir

    def _read_number(self, file_name: str) -> int:
        return int((self._device_dir / file_name).read_text().strip())

    def level(self) -> int:
        return self._read_number("brightness")

    def max_level(self) -> int:
        return self._read_number("max_brightness")

    def set_level(self, level: int) -> None:
        (self._device_dir / "brightness").write_text(f"{level}\n")

    def description(self) -> str:
        return str(self._device_dir)


def first_backlight_device(backlight_root: Path) -> Path:
    devices = sorted(path for path in backlight_root.iterdir() if (path / "max_brightness").exists())
    if not devices:
        raise FileNotFoundError(f"No backlight device under {backlight_root}")
    return devices[0]


def brightness_backend_from_config(backend_name: str, backlight_dir: Path | None) -> BrightnessBackend:
    if backend_name == "recording":
        return RecordingBrightness()
    if backend_name == "sysfs":
        return SysfsBrightness(backlight_dir or first_backlight_device(SYSFS_BACKLIGHT_ROOT))
    raise ValueError(f"Unknown brightness backend {backend_name!r}; use 'recording' or 'sysfs'.")
