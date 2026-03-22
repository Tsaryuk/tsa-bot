import logging
import os
import uuid

from aiogram import Bot, Router
from aiogram.types import Message

import config
from transcriber import transcribe

router = Router()
logger = logging.getLogger(__name__)


async def _download_and_transcribe(bot: Bot, file_id: str, message: Message) -> None:
    status_msg = await message.answer("⏳ Обрабатываю...")
    tmp_path = os.path.join(config.DOWNLOADS_DIR, f"{uuid.uuid4()}.ogg")
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=tmp_path)
        text = await transcribe(tmp_path)
        await status_msg.edit_text(f"📝 Расшифровка:\n\n{text}")
    except Exception as exc:
        logger.exception("Transcription error for file_id=%s", file_id)
        await status_msg.edit_text(f"❌ Ошибка при расшифровке: {exc}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message, bot: Bot) -> None:
    await _download_and_transcribe(bot, message.voice.file_id, message)


@router.message(lambda m: m.audio is not None)
async def handle_audio(message: Message, bot: Bot) -> None:
    await _download_and_transcribe(bot, message.audio.file_id, message)
