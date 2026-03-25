from __future__ import annotations

import hashlib
import logging
import os
import re
from datetime import datetime

from aiogram import F, Router
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from downloader import (
    VideoConnectionError,
    VideoPrivateError,
    VideoUnavailableError,
    download_audio,
    download_audio_with_meta,
)
from transcriber import (
    TranscriptionConnectionError,
    generate_title,
    transcribe,
    transcribe_with_timestamps,
)

router = Router()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL matching
# ---------------------------------------------------------------------------

URL_PATTERN = re.compile(
    r"https?://"
    r"(?:"
    r"(?:www\.)?youtube\.com/shorts/[^\s]+"
    r"|(?:www\.)?youtube\.com/watch\?[^\s]+"
    r"|(?:www\.)?youtu\.be/[^\s]+"
    r"|(?:www\.)?instagram\.com/(?:reel|reels|p)/[^\s]+"
    r"|(?:www\.)?tiktok\.com/@[^\s]+/video/[^\s]+"
    r"|(?:vm|vt)\.tiktok\.com/[^\s]+"
    r")"
)

_SHORTS_PATTERN = re.compile(r"youtube\.com/shorts/")


def _find_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None


def _is_full_youtube(url: str) -> bool:
    """True for full YouTube videos (watch / youtu.be), false for Shorts."""
    if _SHORTS_PATTERN.search(url):
        return False
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return True
    return False


def _label(url: str) -> str:
    if _SHORTS_PATTERN.search(url):
        return "YouTube Shorts"
    if "youtube.com/watch" in url or "youtu.be/" in url:
        return "YouTube"
    if "instagram.com" in url:
        return "Instagram Reel"
    if "tiktok.com" in url:
        return "TikTok"
    return url[:50]


# ---------------------------------------------------------------------------
# Inline keyboard for full YouTube videos
# ---------------------------------------------------------------------------

_CB_PREFIX_TS = "yt_ts:"
_CB_PREFIX_AUDIO = "yt_audio:"

# In-memory URL store keyed by short hash (Telegram callback_data ≤ 64 bytes)
_url_store: dict[str, str] = {}


def _url_key(url: str) -> str:
    """Return a short deterministic key for a URL."""
    key = hashlib.sha256(url.encode()).hexdigest()[:12]
    _url_store[key] = url
    return key


def _url_lookup(key: str) -> str | None:
    return _url_store.get(key)


def _youtube_keyboard(url: str) -> InlineKeyboardMarkup:
    key = _url_key(url)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="\U0001f4dd Текст с тайм-кодами",
                    callback_data=f"{_CB_PREFIX_TS}{key}",
                ),
                InlineKeyboardButton(
                    text="\U0001f3b5 Скачать аудио",
                    callback_data=f"{_CB_PREFIX_AUDIO}{key}",
                ),
            ]
        ]
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_caption(title: str, url: str, date_str: str) -> str:
    short_url = url if len(url) <= 60 else url[:57] + "..."
    return (
        f"\U0001f4c4 *{title}*\n"
        f"\U0001f517 `{short_url}`\n"
        f"\U0001f4c5 {date_str}\n\n"
        "Транскрипция готова."
    )


def _safe_filename(title: str) -> str:
    return title.replace("/", "_").replace("\\", "_").replace(":", "")


# ---------------------------------------------------------------------------
# Message handler — links
# ---------------------------------------------------------------------------

@router.message(lambda m: m.text and _find_url(m.text or "") is not None)
async def handle_link(message: Message) -> None:
    url = _find_url(message.text)

    # Full YouTube video → show action picker
    if _is_full_youtube(url):
        label = _label(url)
        await message.answer(
            f"\U0001f3ac *{label}*\nВыбери действие:",
            parse_mode="Markdown",
            reply_markup=_youtube_keyboard(url),
        )
        return

    # Shorts / Instagram / TikTok → direct transcription
    label = _label(url)
    status_msg = await message.answer(
        f"\u23f3 Транскрибирую: *{label}*...", parse_mode="Markdown"
    )
    audio_path = None
    try:
        audio_path = await download_audio(url)
        text = await transcribe(audio_path)
        title = await generate_title(text)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{_safe_filename(title)}.txt"

        await status_msg.delete()
        buf = BufferedInputFile(text.encode("utf-8"), filename=filename)
        await message.answer_document(
            buf, caption=_make_caption(title, url, date_str), parse_mode="Markdown"
        )
    except VideoPrivateError:
        await status_msg.edit_text(
            "\U0001f512 Видео приватное или требует авторизации. Попробуй другую ссылку."
        )
    except VideoUnavailableError:
        await status_msg.edit_text(
            "\u274c Видео недоступно (удалено или заблокировано). Попробуй другую ссылку."
        )
    except (VideoConnectionError, TranscriptionConnectionError):
        logger.exception("Connection error for url=%s", url)
        await status_msg.edit_text(
            "\u26a0\ufe0f Ошибка соединения — не удалось загрузить или транскрибировать видео. "
            "Попробуй ещё раз через пару минут."
        )
    except Exception as exc:
        logger.exception("Link transcription error for url=%s", url)
        await status_msg.edit_text(
            "\u274c Произошла непредвиденная ошибка. Попробуй ещё раз позже."
        )
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


# ---------------------------------------------------------------------------
# Callback handlers — YouTube actions
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith(_CB_PREFIX_TS))
async def cb_youtube_timestamps(callback: CallbackQuery) -> None:
    key = callback.data[len(_CB_PREFIX_TS):]
    url = _url_lookup(key)
    if not url:
        await callback.answer("Ссылка устарела, отправь ещё раз.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "\u23f3 Транскрибирую с тайм-кодами...", reply_markup=None
    )
    audio_path = None
    try:
        audio_path = await download_audio(url)
        text = await transcribe_with_timestamps(audio_path)
        title = await generate_title(text)
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"{date_str}_{_safe_filename(title)}.txt"
        caption = _make_caption(title, url, date_str)

        await callback.message.delete()
        buf = BufferedInputFile(text.encode("utf-8"), filename=filename)
        await callback.message.answer_document(
            buf, caption=caption, parse_mode="Markdown"
        )
    except VideoPrivateError:
        await callback.message.edit_text(
            "\U0001f512 Видео приватное или требует авторизации."
        )
    except VideoUnavailableError:
        await callback.message.edit_text(
            "\u274c Видео недоступно (удалено или заблокировано)."
        )
    except (VideoConnectionError, TranscriptionConnectionError):
        logger.exception("Connection error for url=%s", url)
        await callback.message.edit_text(
            "\u26a0\ufe0f Ошибка соединения — не удалось загрузить или транскрибировать видео. "
            "Попробуй ещё раз через пару минут."
        )
    except Exception as exc:
        logger.exception("Timestamp transcription error for url=%s", url)
        await callback.message.edit_text(
            "\u274c Произошла непредвиденная ошибка. Попробуй ещё раз позже."
        )
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)


@router.callback_query(F.data.startswith(_CB_PREFIX_AUDIO))
async def cb_youtube_download(callback: CallbackQuery) -> None:
    key = callback.data[len(_CB_PREFIX_AUDIO):]
    url = _url_lookup(key)
    if not url:
        await callback.answer("Ссылка устарела, отправь ещё раз.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(
        "\u23f3 Скачиваю аудио...", reply_markup=None
    )
    audio_path = None
    try:
        meta = await download_audio_with_meta(url)
        audio_path = meta.path
        date_str = datetime.now().strftime("%Y-%m-%d")
        short_url = url if len(url) <= 60 else url[:57] + "..."
        title_line = f"\U0001f3b5 *{meta.title}*\n" if meta.title else "\U0001f3b5 *Аудио из YouTube*\n"
        caption = (
            f"{title_line}"
            f"\U0001f517 `{short_url}`\n"
            f"\U0001f4c5 {date_str}"
        )

        await callback.message.delete()
        audio_file = FSInputFile(audio_path)
        audio_kwargs: dict = {
            "caption": caption,
            "parse_mode": "Markdown",
        }
        if meta.title:
            audio_kwargs["title"] = meta.title
        if meta.duration:
            audio_kwargs["duration"] = meta.duration
        await callback.message.answer_audio(audio_file, **audio_kwargs)
    except VideoPrivateError:
        await callback.message.edit_text(
            "\U0001f512 Видео приватное или требует авторизации."
        )
    except VideoUnavailableError:
        await callback.message.edit_text(
            "\u274c Видео недоступно (удалено или заблокировано)."
        )
    except VideoConnectionError:
        logger.exception("Connection error during audio download for url=%s", url)
        await callback.message.edit_text(
            "\u26a0\ufe0f Ошибка соединения — не удалось скачать аудио. "
            "Попробуй ещё раз через пару минут."
        )
    except Exception as exc:
        logger.exception("Audio download error for url=%s", url)
        await callback.message.edit_text(
            "\u274c Произошла непредвиденная ошибка. Попробуй ещё раз позже."
        )
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
