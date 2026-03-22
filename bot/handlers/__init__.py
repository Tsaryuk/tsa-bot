from aiogram import Dispatcher

from .commands import router as commands_router
from .audio import router as audio_router
from .links import router as links_router


def register_all_handlers(dp: Dispatcher) -> None:
    dp.include_router(commands_router)
    dp.include_router(audio_router)
    dp.include_router(links_router)
