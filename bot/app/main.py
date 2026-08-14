import asyncio
import logging

import httpx
import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()
bot: Bot | None = None


@dp.message(CommandStart())
async def on_start(message: Message) -> None:
    await message.answer("Привет! Опишите свой вопрос — оператор скоро подключится.")


@dp.message()
async def on_user_message(message: Message) -> None:
    await _relay_to_api(message)


async def _relay_to_api(message: Message) -> None:
    if not message.from_user or not message.text:
        return
    payload = {
        "telegram_user_id": message.from_user.id,
        "username": message.from_user.username or "",
        "first_name": message.from_user.first_name or "",
        "text": message.text,
    }
    headers = {"X-Internal-Secret": settings.internal_secret}
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.post(
                f"{settings.api_base_url}/internal/incoming-message", json=payload, headers=headers
            )
            resp.raise_for_status()
    except Exception:
        logger.exception("не удалось передать сообщение в API")


internal_app = FastAPI()


class SendPayload(BaseModel):
    telegram_user_id: int
    text: str


@internal_app.post("/internal/send")
async def internal_send(payload: SendPayload, x_internal_secret: str = Header(default="")):
    if x_internal_secret != settings.internal_secret:
        raise HTTPException(401, "bad internal secret")
    if bot is None:
        raise HTTPException(503, "bot not started")
    await bot.send_message(payload.telegram_user_id, payload.text)
    return {"ok": True}


async def main() -> None:
    global bot
    if not settings.bot_token:
        logger.warning("BOT_TOKEN не задан — заполните bot/.env (см. README, раздел про @BotFather)")
        return
    bot = Bot(token=settings.bot_token)

    config = uvicorn.Config(internal_app, host="0.0.0.0", port=settings.internal_port, log_level="warning")
    server = uvicorn.Server(config)

    logger.info("bot polling + internal server on :%s", settings.internal_port)
    await asyncio.gather(
        dp.start_polling(bot),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
