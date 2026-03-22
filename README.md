# TSA Bot — Audio Transcription Telegram Bot

Telegram-бот для расшифровки аудио голосовых сообщений и коротких видео в текст с помощью Whisper.

## Возможности

- 🎤 Голосовые сообщения Telegram
- 🎵 Аудиофайлы (ogg, mp3, wav, m4a)
- 🔗 Ссылки на короткие видео:
  - YouTube Shorts
  - Instagram Reels
  - TikTok

## Режимы транскрипции

| Режим | Условие | Описание |
|-------|---------|---------|
| OpenAI Whisper API | `OPENAI_API_KEY` задан | Облачный, высокое качество |
| Локальный faster-whisper | `OPENAI_API_KEY` не задан | Работает офлайн, бесплатно |

## Быстрый старт

### 1. Получить Telegram Bot Token

1. Открой Telegram и найди [@BotFather](https://t.me/BotFather)
2. Отправь команду `/newbot`
3. Задай имя и username бота (например, `MyTranscriberBot`)
4. BotFather выдаст токен вида `123456789:ABCdef...` — скопируй его

### 2. Настройка окружения

```bash
cp .env.example .env
# Открой .env в редакторе и вставь токен:
# TELEGRAM_BOT_TOKEN=123456789:ABCdef...
```

### 3. Запуск через Docker (рекомендуется)

```bash
docker-compose up -d
```

Проверить логи:

```bash
docker-compose logs -f
```

Остановить:

```bash
docker-compose down
```

### 4. Запуск локально (без Docker)

Требования: Python 3.11+, ffmpeg

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Структура проекта

```
tsa-bot/
├── bot/
│   └── handlers/
│       ├── commands.py   # /start
│       ├── audio.py      # голосовые и аудиофайлы
│       └── links.py      # ссылки на видео
├── transcriber.py        # модуль транскрипции (Whisper)
├── downloader.py         # скачивание аудио через yt-dlp
├── config.py             # конфигурация из .env
├── main.py               # точка входа
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Переменные окружения

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Токен бота из @BotFather |
| `OPENAI_API_KEY` | ❌ | — | Ключ OpenAI для Whisper API |
| `WHISPER_MODEL` | ❌ | `base` | Модель faster-whisper (`tiny`/`base`/`small`/`medium`/`large-v3`) |
| `WHISPER_DEVICE` | ❌ | `cpu` | Устройство (`cpu`/`cuda`) |
| `WHISPER_COMPUTE_TYPE` | ❌ | `int8` | Тип вычислений (`int8`/`float16`/`float32`) |
| `DOWNLOADS_DIR` | ❌ | `/tmp/tsa-bot-downloads` | Папка для временных файлов |
| `LOG_LEVEL` | ❌ | `INFO` | Уровень логирования |

## Деплой на VPS

### Требования к серверу

- Ubuntu 22.04 / Debian 12 (или любой дистрибутив с Docker)
- 1+ CPU, 1 GB RAM (2 GB для моделей `medium`/`large-v3`)
- Docker + Docker Compose

### Установка Docker на Ubuntu

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
```

### Деплой

```bash
# Клонировать репозиторий на сервер
git clone <repo-url> tsa-bot
cd tsa-bot

# Настроить окружение
cp .env.example .env
nano .env   # вставить TELEGRAM_BOT_TOKEN

# Запустить
docker-compose up -d

# Убедиться, что бот работает
docker-compose logs -f
```

### Обновление

```bash
git pull
docker-compose up -d --build
```

### Автозапуск (systemd)

Docker с `restart: unless-stopped` автоматически перезапускает контейнер при перезагрузке сервера, если Docker настроен как systemd-сервис (по умолчанию при установке через `get.docker.com`).

## Выбор модели Whisper

| Модель | RAM | Скорость | Точность |
|--------|-----|----------|---------|
| `tiny` | ~1 GB | Очень быстро | Низкая |
| `base` | ~1 GB | Быстро | Приемлемо |
| `small` | ~2 GB | Средне | Хорошо |
| `medium` | ~5 GB | Медленно | Отлично |
| `large-v3` | ~10 GB | Очень медленно | Максимум |

Для домашнего сервера рекомендуется `base` или `small`. Для GPU — `large-v3`.
