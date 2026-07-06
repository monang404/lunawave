# 🌙 LunaWave

> **Midnight Audio Experience.**  
> A premium, lightweight, and modern YouTube music player designed for Termux and low-resource environments.

LunaWave (formerly known as Bagas.FM / YTGUI) is a fully-featured personal music streaming server and PWA client. It allows you to search, queue, and play audio seamlessly from YouTube with a beautiful dark-mode interface, synchronized lyrics, and offline caching capabilities.

## ✨ Features

- **Progressive Web App (PWA)**: Installable on mobile and desktop with a native app feel.
- **Background Playback**: Keeps playing your music even when the screen is locked or the app is minimized (via Service Worker & MediaSession API).
- **Synchronized Lyrics**: Real-time lyrics display for an immersive karaoke experience.
- **Zero-Latency UI**: Bundled assets and aggressive caching for instant load times.
- **Radio Mode**: Endless music discovery based on your current track.
- **Docker Ready**: Deploy anywhere with a single `docker compose up -d` command.

## 🚀 Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone https://github.com/monang404/ytgui.git lunawave
   cd lunawave
   ```
2. Start the server:
   ```bash
   docker compose up -d
   ```
3. Open `http://localhost:8765` in your browser. The default admin username is `admin`. The password will be generated and printed to the console on first run, or you can set `LUNAWAVE_ADMIN_PASS` in your environment.

### Manual Installation (Termux / Local)

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   python start.py
   ```

## 🛠️ Configuration

You can configure LunaWave using the following Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LUNAWAVE_HOST` | Host to bind the server | `0.0.0.0` |
| `LUNAWAVE_PORT` | Port to run the web interface | `8765` |
| `LUNAWAVE_ADMIN_USER` | Admin username for login | `admin` |
| `LUNAWAVE_ADMIN_PASS` | Admin password (hashed or plain) | *Auto-generated* |

## 📦 Architecture

LunaWave operates on a modern, decoupled architecture:
- **Backend**: Python `aiohttp` for asynchronous HTTP and WebSocket connections, coupled with SQLite for robust session and metadata storage.
- **Frontend**: Vanilla JavaScript (bundled), CSS Tokens, and Event-driven state management for maximum performance without the overhead of heavy frameworks.
- **Audio Engine**: `yt-dlp` and `FFmpeg` for reliable stream extraction and playback.

---
*LunaWave is an open-source project. Contributions and feedback are welcome!*
