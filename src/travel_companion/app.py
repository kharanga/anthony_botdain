from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from travel_companion.cards import AnswerCard, Evidence
from travel_companion.config import DEFAULT_CONFIG_PATH, Config, load_config

STATIC_DIR = Path(__file__).resolve().parent / "static"


def status_card(config: Config, config_path: Path) -> AnswerCard:
    allergens = ", ".join(config.active_allergens)
    return AnswerCard(
        kind="status",
        title="Ready",
        body=f"Country pack {config.country}. Watching for {allergens}. Home currency {config.home_currency}.",
        evidence=[
            Evidence(source=str(config_path), text=f"country = {config.country}"),
            Evidence(source=str(config_path), text=f"active_allergens = {allergens}"),
            Evidence(source=str(config_path), text=f"home_currency = {config.home_currency}"),
            Evidence(source=str(config_path), text=f"rate = {config.rate:g} CRC per USD"),
            Evidence(source=str(config_path), text=f"model.endpoint_url = {config.model_endpoint_url}"),
        ],
    )


def create_app(config_path: Path = DEFAULT_CONFIG_PATH) -> FastAPI:
    config = load_config(config_path)
    config.data_dir.mkdir(parents=True, exist_ok=True)
    app = FastAPI(title="travel-companion")
    app.state.config = config

    @app.get("/api/status")
    def get_status() -> AnswerCard:
        return status_card(config, config_path)

    @app.get("/")
    def get_ui_shell() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app
