from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from travel_companion.ask import ask_router
from travel_companion.cards import AnswerCard, Evidence
from travel_companion.config import DEFAULT_CONFIG_PATH, Config, load_config
from travel_companion.database import set_up_database
from travel_companion.model_client import ModelClient
from travel_companion.rate import CurrentRate, current_rate, rate_evidence, rate_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def status_card(config: Config, config_path: Path, rate: CurrentRate) -> AnswerCard:
    allergens = ", ".join(config.active_allergens)
    return AnswerCard(
        kind="status",
        title="Ready",
        body=f"Country pack {config.country}. Watching for {allergens}. Home currency {config.home_currency}.",
        evidence=[
            Evidence(source=str(config_path), text=f"country = {config.country}"),
            Evidence(source=str(config_path), text=f"active_allergens = {allergens}"),
            Evidence(source=str(config_path), text=f"home_currency = {config.home_currency}"),
            rate_evidence(rate),
            Evidence(source=str(config_path), text=f"model.endpoint_url = {config.model_endpoint_url}"),
        ],
    )


def create_app(config_path: Path = DEFAULT_CONFIG_PATH) -> FastAPI:
    config = load_config(config_path)
    database_path = set_up_database(config.data_dir)
    app = FastAPI(title="travel-companion")
    app.state.config = config
    app.state.model_client = ModelClient(config.model_endpoint_url)
    app.include_router(ask_router)

    @app.get("/api/status")
    def get_status() -> AnswerCard:
        return status_card(config, config_path, current_rate(database_path, config.rate, config_path))

    app.include_router(rate_router(database_path, config.rate, config_path))

    @app.get("/")
    def get_ui_shell() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app
