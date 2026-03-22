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

## Публикация на GitHub

### Шаг 1 — Создать репозиторий на GitHub

1. Зайди на [github.com](https://github.com) и войди в аккаунт
2. Нажми **"+"** → **"New repository"**
3. Название: `tsa-bot`
4. Видимость: **Private** (рекомендуется — токен бота нельзя публиковать)
5. **Не ставь** галочки "Add README", ".gitignore", "license" — репо уже инициализировано локально
6. Нажми **"Create repository"**

### Шаг 2 — Привязать и запушить

После создания GitHub покажет инструкции. Выполни в папке `tsa-bot/`:

```bash
git remote add origin https://github.com/ВАШ_USERNAME/tsa-bot.git
git branch -M main
git push -u origin main
```

Замени `ВАШ_USERNAME` на свой GitHub логин.

> **Важно:** `.env` файл с токенами **не попадёт** в репо — он уже исключён в `.gitignore`.

## Деплой на VPS (пошагово)

### Шаг 1 — Арендовать сервер

**Hetzner Cloud (рекомендуется, дешевле):**
1. Зайди на [hetzner.com/cloud](https://www.hetzner.com/cloud)
2. Создай аккаунт, привяжи карту
3. Нажми **"Create Server"**
4. Выбери: Location **Nuremberg** или **Helsinki**, Image **Ubuntu 22.04**, Type **CX21** (2 vCPU, 4 GB RAM, ~€4/мес)
5. В разделе **SSH Keys** добавь свой публичный ключ (если нет — можно пропустить, пароль придёт на email)
6. Нажми **"Create & Buy"**

**DigitalOcean (альтернатива):**
1. Зайди на [digitalocean.com](https://digitalocean.com)
2. **Create** → **Droplets**
3. Image: **Ubuntu 22.04**, Size: **Basic → Regular → $6/мес** (1 vCPU, 1 GB RAM — минимум)
4. Добавь SSH Key или пароль

### Шаг 2 — Подключиться к серверу

```bash
ssh root@IP_АДРЕС_СЕРВЕРА
```

Если использовал пароль — введи его при запросе.

### Шаг 3 — Установить Docker

```bash
# Одна команда устанавливает Docker и Docker Compose
curl -fsSL https://get.docker.com | sh

# Разрешить запуск без sudo (необязательно для root)
sudo usermod -aG docker $USER
newgrp docker

# Проверить установку
docker --version
docker compose version
```

### Шаг 4 — Клонировать репозиторий

```bash
# Установить git (если нет)
apt install -y git

# Клонировать репо (замени URL на свой GitHub репозиторий)
git clone https://github.com/ВАШ_USERNAME/tsa-bot.git
cd tsa-bot
```

### Шаг 5 — Создать .env с токеном

```bash
cp .env.example .env
nano .env
```

В редакторе вставь свой токен:

```
TELEGRAM_BOT_TOKEN=123456789:ABCdef...
```

Сохранить: `Ctrl+O`, `Enter`, выйти: `Ctrl+X`

### Шаг 6 — Запустить бота

```bash
docker compose up -d --build
```

Это скачает образ, соберёт контейнер и запустит его в фоне.

Проверить что работает:

```bash
docker compose logs -f
```

Должен появиться лог вида `Bot started`. Выйти из логов: `Ctrl+C`

### Автозапуск после перезагрузки сервера

В `docker-compose.yml` уже настроено `restart: unless-stopped` — контейнер автоматически стартует при перезагрузке сервера (пока Docker сам запускается через systemd, что является стандартным поведением при установке через `get.docker.com`).

Проверить:

```bash
sudo reboot
# подождать 30 секунд, подключиться снова
ssh root@IP_АДРЕС_СЕРВЕРА
docker ps   # контейнер должен быть в статусе "Up"
```

### Обновление бота

```bash
cd tsa-bot
git pull
docker compose up -d --build
```

## Выбор модели Whisper

| Модель | RAM | Скорость | Точность |
|--------|-----|----------|---------|
| `tiny` | ~1 GB | Очень быстро | Низкая |
| `base` | ~1 GB | Быстро | Приемлемо |
| `small` | ~2 GB | Средне | Хорошо |
| `medium` | ~5 GB | Медленно | Отлично |
| `large-v3` | ~10 GB | Очень медленно | Максимум |

Для домашнего сервера рекомендуется `base` или `small`. Для GPU — `large-v3`.
