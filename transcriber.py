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
    import openai

    client = openai.AsyncOpenAI(api_key=config.OPENAI_API_KEY)
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
