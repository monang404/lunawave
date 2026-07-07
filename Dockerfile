FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (mpv for playback, ffmpeg for yt-dlp)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    mpv \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose HTTP port
EXPOSE 8765

# Command to run the application
CMD ["python", "main.py"]
