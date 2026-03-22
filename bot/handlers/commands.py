from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()

WELCOME_TEXT = """
👋 Привет! Я бот для расшифровки аудио.

Что я умею:
• 🎤 Расшифровывать голосовые сообщения
• 🎵 Расшифровывать аудиофайлы (ogg, mp3, wav, m4a)
• 🔗 Скачивать и расшифровывать аудио из ссылок:
  — YouTube Shorts
  — Instagram Reels
  — TikTok

Просто отправь мне голосовое сообщение, аудиофайл или ссылку — и я верну тебе текст!

📋 /limits — ограничения и подробности
""".strip()

LIMITS_TEXT = """
📋 Ограничения и детали

📁 Размер файла: до 20 МБ (лимит Telegram)
⏱ Длительность: до ~30 минут (рекомендуется до 10 мин для скорости)
🌍 Языки: автоопределение (русский, английский и другие)

Поддерживаемые форматы:
• Голосовые сообщения Telegram (ogg)
• Аудиофайлы: mp3, wav, m4a, ogg, flac
• Видеосообщения (кружочки)
• Ссылки: YouTube Shorts, TikTok, Instagram Reels

⚡ Скорость транскрипции:
• OpenAI API — ~10–30 сек на любой файл
• Локальная модель (base) — ~1–2x длительности файла

⚠️ Ограничения по ссылкам:
• Instagram Reels могут быть недоступны без авторизации
• Только публичные видео
""".strip()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(WELCOME_TEXT)


@router.message(Command("limits"))
async def cmd_limits(message: Message) -> None:
    await message.answer(LIMITS_TEXT)
