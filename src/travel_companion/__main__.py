import os
from pathlib import Path

import uvicorn

from travel_companion.app import create_app
from travel_companion.config import DEFAULT_CONFIG_PATH


def config_path_from_env() -> Path:
    return Path(os.environ.get("TRAVEL_COMPANION_CONFIG", DEFAULT_CONFIG_PATH))


def serve() -> None:
    host = os.environ.get("TRAVEL_COMPANION_HOST", "127.0.0.1")
    port = int(os.environ.get("TRAVEL_COMPANION_PORT", "8765"))
    uvicorn.run(create_app(config_path_from_env()), host=host, port=port)


if __name__ == "__main__":
    serve()
