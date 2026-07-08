# Stage 1: Build Frontend Assets
FROM node:18-slim AS frontend
WORKDIR /app
COPY package.json ./
RUN npm install
COPY web/ web/
RUN npm run build

# Stage 2: Runtime
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (mpv for playback, ffmpeg for yt-dlp)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    mpv \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user
RUN useradd -m appuser

WORKDIR /app

# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Copy built frontend assets from stage 1
COPY --from=frontend /app/web/static/js/bundle.js web/static/js/bundle.js
COPY --from=frontend /app/web/static/css/bundle.css web/static/css/bundle.css

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://127.0.0.1:8765/health || exit 1

# Expose HTTP port
EXPOSE 8765

# Command to run the application
CMD ["python", "main.py"]
