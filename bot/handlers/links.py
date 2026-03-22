from __future__ import annotations

import logging
import os
import re
from datetime import datetime

from aiogram import Router
from aiogram.types import BufferedInputFile, Message

from downloader import VideoPrivateError, VideoUnavailableError, download_audio
from transcriber import transcribe

router = Router()
logger = logging.getLogger(__name__)

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


def _label(url: str) -> str:
    if "youtube.com/shorts" in url or "youtu.be" in url:
        return "YouTube Shorts"
    if "instagram.com" in url:
        return "Instagram Reel"
    if "tiktok.com" in url:
        return "TikTok"
    return url[:50]


@router.message(lambda m: m.text and _find_url(m.text or "") is not None)
async def handle_link(message: Message) -> None:
    url = _find_url(message.text)
    label = _label(url)
    status_msg = await message.answer(
        f"⏳ Транскрибирую: *{label}*...", parse_mode="Markdown"
    )
    audio_path = None
    try:
        audio_path = await download_audio(url)
        text = await transcribe(audio_path)

        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{label.replace(' ', '_')}.txt"
        short_url = url if len(url) <= 60 else url[:57] + "..."
        caption = (
            f"📄 *{label}*\n"
            f"🔗 `{short_url}`\n"
            f"📅 {date_str}\n\n"
            "Транскрипция готова."
        )

        await status_msg.delete()
        buf = BufferedInputFile(text.encode("utf-8"), filename=filename)
        await message.answer_document(buf, caption=caption, parse_mode="Markdown")
    except VideoPrivateError:
        await status_msg.edit_text(
            "🔒 Видео приватное или требует авторизации. Попробуй другую ссылку."
        )
    except VideoUnavailableError:
        await status_msg.edit_text(
            "❌ Видео недоступно (удалено или заблокировано). Попробуй другую ссылку."
        )
    except Exception as exc:
        logger.exception("Link transcription error for url=%s", url)
        await status_msg.edit_text(f"❌ Ошибка: {exc}")
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
