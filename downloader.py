"""
Audio downloader for short-video URLs.

Uses yt-dlp to extract and download audio from YouTube Shorts,
Instagram Reels, and TikTok.
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from functools import partial

import config

logger = logging.getLogger(__name__)

YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }
    ],
}

# Substrings in yt-dlp error messages that indicate private/unavailable content
_PRIVATE_PHRASES = (
    "private video",
    "private",
    "age-restricted",
    "login required",
    "members only",
    "этот контент",
    "this content",
)
_UNAVAILABLE_PHRASES = (
    "video unavailable",
    "not available",
    "has been removed",
    "does not exist",
    "no video formats found",
    "unable to extract",
    "404",
)


@dataclass(frozen=True)
class AudioMeta:
    """Metadata returned by download_audio_with_meta."""
    path: str
    title: str | None = None
    duration: int | None = None


class VideoDownloadError(Exception):
    """Raised when a video cannot be downloaded."""


class VideoUnavailableError(VideoDownloadError):
    """Content is unavailable (removed, geo-blocked, etc.)."""


class VideoPrivateError(VideoDownloadError):
    """Content is private or requires authentication."""


def _classify_ydl_error(message: str) -> VideoDownloadError:
    low = message.lower()
    if any(p in low for p in _PRIVATE_PHRASES):
        return VideoPrivateError(f"Контент приватный или требует авторизации: {message}")
    if any(p in low for p in _UNAVAILABLE_PHRASES):
        return VideoUnavailableError(f"Контент недоступен: {message}")
    return VideoDownloadError(f"Ошибка загрузки: {message}")


def _download_sync(url: str, output_path: str) -> str:
    import yt_dlp
    from yt_dlp.utils import DownloadError, ExtractorError

    opts = {
        **YDL_OPTS,
        "outtmpl": output_path,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except (DownloadError, ExtractorError) as exc:
        raise _classify_ydl_error(str(exc)) from exc

    # yt-dlp appends the extension after post-processing
    final = output_path + ".mp3"
    if not os.path.exists(final):
        raise VideoDownloadError(
            f"Файл не найден после загрузки. Возможно, формат не поддерживается: {url}"
        )
    return final


async def download_audio(url: str) -> str:
    """Download audio from a URL and return the local file path.

    Raises:
        VideoPrivateError: if the content is private or requires login.
        VideoUnavailableError: if the content has been removed or is geo-blocked.
        VideoDownloadError: for any other download failure.
    """
    output_template = os.path.join(config.DOWNLOADS_DIR, str(uuid.uuid4()))
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(_download_sync, url, output_template))


def _download_with_meta_sync(url: str, output_path: str) -> AudioMeta:
    import yt_dlp
    from yt_dlp.utils import DownloadError, ExtractorError

    opts = {
        **YDL_OPTS,
        "outtmpl": output_path,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except (DownloadError, ExtractorError) as exc:
        raise _classify_ydl_error(str(exc)) from exc

    final = output_path + ".mp3"
    if not os.path.exists(final):
        raise VideoDownloadError(
            f"Файл не найден после загрузки. Возможно, формат не поддерживается: {url}"
        )

    title = info.get("title") if info else None
    duration = info.get("duration") if info else None
    if duration is not None:
        duration = int(duration)

    return AudioMeta(path=final, title=title, duration=duration)


async def download_audio_with_meta(url: str) -> AudioMeta:
    """Download audio and return AudioMeta with path, title, and duration.

    Raises:
        VideoPrivateError: if the content is private or requires login.
        VideoUnavailableError: if the content has been removed or is geo-blocked.
        VideoDownloadError: for any other download failure.
    """
    output_template = os.path.join(config.DOWNLOADS_DIR, str(uuid.uuid4()))
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, partial(_download_with_meta_sync, url, output_template)
    )
