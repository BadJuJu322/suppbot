import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _split_ids(raw: str) -> set:
    return {int(x) for x in raw.split(",") if x.strip()}


def _split_origins(raw: str) -> list:
    return [x.strip() for x in raw.split(",") if x.strip()]


@dataclass
class Settings:
    dev_mode: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    bot_internal_url: str = os.getenv("BOT_INTERNAL_URL", "http://localhost:8001")
    bot_internal_secret: str = os.getenv("BOT_INTERNAL_SECRET", "dev-secret-change-me")
    allowed_operator_ids: set = field(
        default_factory=lambda: _split_ids(os.getenv("ALLOWED_OPERATOR_IDS", ""))
    )
    cors_origins: list = field(
        default_factory=lambda: _split_origins(os.getenv("CORS_ORIGINS", "http://localhost:5173"))
    )


settings = Settings()
