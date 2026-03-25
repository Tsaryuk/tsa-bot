"""
Transcription module.

Supports two modes:
1. OpenAI Whisper API  — when OPENAI_API_KEY is set
2. Local faster-whisper — fallback (no API key required)

Input:  path to an audio file (ogg, mp3, wav, m4a)
Output: transcribed text string
"""

import asyncio
import logging
from functools import lru_cache

import config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OpenAI Whisper API backend
# ---------------------------------------------------------------------------

def _format_ts(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _openai_client():
    import httpx
    import openai

    http_client = (
        httpx.AsyncClient(proxy=config.OPENAI_PROXY) if config.OPENAI_PROXY else None
    )
    return openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY, http_client=http_client)


async def _transcribe_openai(audio_path: str) -> str:
    client = _openai_client()
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    return response.text


async def _transcribe_openai_timestamps(audio_path: str) -> str:
    client = _openai_client()
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    lines = []
    for seg in response.segments or []:
        ts = _format_ts(seg["start"])
        lines.append(f"[{ts}] {seg['text'].strip()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Local faster-whisper backend
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_local_model():
    from faster_whisper import WhisperModel

    logger.info(
        "Loading local Whisper model=%s device=%s compute_type=%s",
        config.WHISPER_MODEL,
        config.WHISPER_DEVICE,
        config.WHISPER_COMPUTE_TYPE,
    )
    return WhisperModel(
        config.WHISPER_MODEL,
        device=config.WHISPER_DEVICE,
        compute_type=config.WHISPER_COMPUTE_TYPE,
    )


def _transcribe_local_sync(audio_path: str) -> str:
    model = _get_local_model()
    segments, _info = model.transcribe(audio_path)
    return " ".join(seg.text.strip() for seg in segments)


def _transcribe_local_timestamps_sync(audio_path: str) -> str:
    model = _get_local_model()
    segments, _info = model.transcribe(audio_path)
    lines = []
    for seg in segments:
        ts = _format_ts(seg.start)
        lines.append(f"[{ts}] {seg.text.strip()}")
    return "\n".join(lines)


async def _transcribe_local(audio_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _transcribe_local_sync, audio_path)


async def _transcribe_local_timestamps(audio_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _transcribe_local_timestamps_sync, audio_path)


# ---------------------------------------------------------------------------
# Title generation
# ---------------------------------------------------------------------------

def _title_from_text(text: str) -> str:
    """Fallback: use first 6 words of transcription as title."""
    words = text.split()[:6]
    title = " ".join(words)
    return title.rstrip(".,!?;:") if title else "Запись"


async def _generate_title_openai(text: str) -> str:
    client = _openai_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Придумай короткое название (3–6 слов) для записи по её тексту. "
                    "Только название, без кавычек и пояснений. На том же языке, что и текст."
                ),
            },
            {"role": "user", "content": text[:1000]},
        ],
        max_tokens=20,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip().rstrip(".,!?;:")


async def generate_title(text: str) -> str:
    """Generate a short meaningful title for the transcription."""
    if config.OPENAI_API_KEY:
        try:
            return await _generate_title_openai(text)
        except Exception:
            logger.warning("Title generation failed, falling back to first words")
    return _title_from_text(text)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def transcribe(audio_path: str) -> str:
    """Transcribe an audio file and return the text."""
    if config.OPENAI_API_KEY:
        logger.debug("Using OpenAI Whisper API for %s", audio_path)
        return await _transcribe_openai(audio_path)
    else:
        logger.debug("Using local faster-whisper for %s", audio_path)
        return await _transcribe_local(audio_path)


async def transcribe_with_timestamps(audio_path: str) -> str:
    """Transcribe an audio file and return text with [MM:SS] timestamps."""
    if config.OPENAI_API_KEY:
        logger.debug("Using OpenAI Whisper API (timestamps) for %s", audio_path)
        return await _transcribe_openai_timestamps(audio_path)
    else:
        logger.debug("Using local faster-whisper (timestamps) for %s", audio_path)
        return await _transcribe_local_timestamps(audio_path)
