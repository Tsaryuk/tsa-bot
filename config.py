import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY") or None
WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
DOWNLOADS_DIR: str = os.getenv("DOWNLOADS_DIR", "/tmp/tsa-bot-downloads")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
