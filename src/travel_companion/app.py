import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from travel_companion.allergen_terms import allergen_terms_router
from travel_companion.ask import ask_router
from travel_companion.brightness import brightness_backend_from_config
from travel_companion.cards import AnswerCard, Evidence
from travel_companion.config import DEFAULT_CONFIG_PATH, Config, load_config
from travel_companion.country_pack import CountryPack, country_pack_evidence, load_country_pack
from travel_companion.database import set_up_database
from travel_companion.dish_lookup import dish_lookup_router
from travel_companion.full_screen import FullScreenView, full_screen_router
from travel_companion.intent_router import intent_router
from travel_companion.model_client import ModelClient
from travel_companion.speech_to_text import Transcriber, speech_router, whisper_transcriber
from travel_companion.ocr import ocr_engine_from_config
from travel_companion.photo_ocr import photo_ocr_router
from travel_companion.rate import CurrentRate, current_rate, rate_evidence, rate_router
from travel_companion.staff_phrase import staff_phrase_router
from travel_companion.vault import Clock, VaultSession, vault_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


def status_card(config: Config, config_path: Path, rate: CurrentRate, country_pack: CountryPack) -> AnswerCard:
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
            *country_pack_evidence(country_pack),
        ],
    )


def create_app(
    config_path: Path = DEFAULT_CONFIG_PATH, clock: Clock = time.monotonic, transcriber: Transcriber | None = None
) -> FastAPI:
    config = load_config(config_path)
    country_pack = load_country_pack(config.packs_dir, config.country, config.active_allergens)
    database_path = set_up_database(config.data_dir)
    app = FastAPI(title="travel-companion")
    app.state.config = config
    app.state.country_pack = country_pack
    app.state.model_client = ModelClient(config.model_endpoint_url)
    app.include_router(ask_router)
    app.include_router(intent_router)
    app.include_router(speech_router(transcriber or whisper_transcriber(config.whisper_cli, config.whisper_model_path)))
    app.include_router(allergen_terms_router)
    app.include_router(dish_lookup_router)
    app.state.ocr_engine = ocr_engine_from_config(config.ocr_engine, config.ocr_language)
    app.include_router(photo_ocr_router)
    app.include_router(staff_phrase_router)

    @app.get("/api/status")
    def get_status() -> AnswerCard:
        return status_card(config, config_path, current_rate(database_path, config.rate, config_path), country_pack)

    app.include_router(rate_router(database_path, config.rate, config_path))

    app.state.vault_session = VaultSession(clock)
    app.include_router(vault_router(database_path, app.state.vault_session))

    app.state.full_screen_view = FullScreenView(brightness_backend_from_config(config.brightness_backend, config.backlight_dir))
    app.include_router(full_screen_router(database_path, app.state.vault_session, app.state.full_screen_view))

    @app.get("/")
    def get_ui_shell() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return app
