FROM python:3.11-slim

# System deps: ffmpeg for audio processing, yt-dlp needs it
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create downloads directory
RUN mkdir -p /tmp/tsa-bot-downloads

# Run the bot
CMD ["python", "main.py"]
