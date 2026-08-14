import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:8000")
    internal_port: int = int(os.getenv("BOT_INTERNAL_PORT", "8001"))
    internal_secret: str = os.getenv("BOT_INTERNAL_SECRET", "dev-secret-change-me")


settings = Settings()
