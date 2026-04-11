import asyncio
import logging
import socket

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiohttp import TCPConnector

import config
from bot.handlers import register_all_handlers

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    connector = TCPConnector(family=socket.AF_INET)
    session = AiohttpSession(connector=connector)
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN, session=session)
    dp = Dispatcher()
    register_all_handlers(dp)

    logger.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
