from __future__ import annotations
import logging
import re

from aiogram import Router
from aiogram.types import Message

from downloader import VideoPrivateError, VideoUnavailableError, download_audio
from transcriber import transcribe

router = Router()
logger = logging.getLogger(__name__)

# Patterns for supported short-video platforms
URL_PATTERN = re.compile(
    r"https?://"
    r"(?:"
    r"(?:www\.)?youtube\.com/shorts/[^\s]+"
    r"|(?:www\.)?youtu\.be/[^\s]+"
    r"|(?:www\.)?instagram\.com/(?:reel|reels|p)/[^\s]+"
    r"|(?:www\.)?tiktok\.com/@[^\s]+/video/[^\s]+"
    r"|(?:vm|vt)\.tiktok\.com/[^\s]+"
    r")"
)


def _find_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


@router.message(lambda m: m.text and _find_url(m.text or "") is not None)
async def handle_link(message: Message) -> None:
    url = _find_url(message.text)
    status_msg = await message.answer("⏳ Обрабатываю...")
    try:
        audio_path = await download_audio(url)
        text = await transcribe(audio_path)
        import os
        if os.path.exists(audio_path):
            os.remove(audio_path)
        await status_msg.edit_text(f"📝 Расшифровка:\n\n{text}")
    except VideoPrivateError:
        await status_msg.edit_text("🔒 Видео приватное или требует авторизации. Попробуй другую ссылку.")
    except VideoUnavailableError:
        await status_msg.edit_text("❌ Видео недоступно (удалено или заблокировано). Попробуй другую ссылку.")
    except Exception as exc:
        logger.exception("Link transcription error for url=%s", url)
        await status_msg.edit_text(f"❌ Ошибка: {exc}")
