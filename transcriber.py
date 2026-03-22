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

async def _transcribe_openai(audio_path: str) -> str:
    import httpx
    import openai

    http_client = (
        httpx.AsyncClient(proxy=config.OPENAI_PROXY) if config.OPENAI_PROXY else None
    )
    client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY, http_client=http_client)
    with open(audio_path, "rb") as f:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    return response.text


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


async def _transcribe_local(audio_path: str) -> str:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _transcribe_local_sync, audio_path)


# ---------------------------------------------------------------------------
# Title generation
# ---------------------------------------------------------------------------

def _title_from_text(text: str) -> str:
    """Fallback: use first 6 words of transcription as title."""
    words = text.split()[:6]
    title = " ".join(words)
    return title.rstrip(".,!?;:") if title else "Запись"


async def _generate_title_openai(text: str) -> str:
    import httpx
    import openai

    http_client = (
        httpx.AsyncClient(proxy=config.OPENAI_PROXY) if config.OPENAI_PROXY else None
    )
    client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY, http_client=http_client)
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
