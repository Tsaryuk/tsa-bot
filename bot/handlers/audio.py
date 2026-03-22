import logging
import os
import uuid
from datetime import datetime

from aiogram import Bot, Router
from aiogram.types import BufferedInputFile, Message

import config
from transcriber import transcribe

router = Router()
logger = logging.getLogger(__name__)


def _format_duration(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


async def _download_and_transcribe(
    bot: Bot,
    file_id: str,
    message: Message,
    display_name: str,
    duration: int | None = None,
) -> None:
    status_msg = await message.answer(
        f"⏳ Транскрибирую: *{display_name}*...", parse_mode="Markdown"
    )
    tmp_path = os.path.join(config.DOWNLOADS_DIR, f"{uuid.uuid4()}.ogg")
    try:
        file = await bot.get_file(file_id)
        await bot.download_file(file.file_path, destination=tmp_path)
        text = await transcribe(tmp_path)

        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_name = display_name.replace("/", "_").replace("\\", "_")
        filename = f"{date_str}_{safe_name}.txt"

        caption_lines = [f"📄 *{display_name}*"]
        if duration is not None:
            caption_lines.append(f"⏱ Длительность: {_format_duration(duration)}")
        caption_lines.append(f"📅 {date_str}")
        caption_lines.append("")
        caption_lines.append("Транскрипция готова.")
        caption = "\n".join(caption_lines)

        await status_msg.delete()
        buf = BufferedInputFile(text.encode("utf-8"), filename=filename)
        await message.answer_document(buf, caption=caption, parse_mode="Markdown")
    except Exception as exc:
        logger.exception("Transcription error for file_id=%s", file_id)
        await status_msg.edit_text(f"❌ Ошибка при расшифровке: {exc}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.message(lambda m: m.voice is not None)
async def handle_voice(message: Message, bot: Bot) -> None:
    duration = message.voice.duration
    await _download_and_transcribe(
        bot, message.voice.file_id, message, "Голосовое сообщение", duration
    )


@router.message(lambda m: m.audio is not None)
async def handle_audio(message: Message, bot: Bot) -> None:
    audio = message.audio
    raw_name = audio.file_name or "аудиофайл"
    display_name = os.path.splitext(raw_name)[0]
    await _download_and_transcribe(
        bot, audio.file_id, message, display_name, audio.duration
    )
