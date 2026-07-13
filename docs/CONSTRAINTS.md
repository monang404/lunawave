---
title: Technical Constraints & Limitations
last_verified: 2026-07-13
owner: Architecture Team
generated: false
---

# Technical Constraints

This document outlines the hard technical constraints and environmental limitations that dictate LunaWave's architecture.

## 1. Environment: Termux (Android)
- **Filesystem**: No standard Linux FHS (`/usr/bin`, `/etc`). Everything is under `/data/data/com.termux/files/usr`.
- **Background Execution**: Requires wakelock to prevent Android from killing the process when the screen is off.
- **Port Binding**: Cannot bind to privileged ports (< 1024).

## 2. Dependencies
- **mpv**: Used for audio playback. Requires `--no-video` and specific IPC configurations for Termux.
- **yt-dlp**: Used for resolving streams. Needs frequent updates to bypass YouTube changes. Rate limiting is a risk.
- **SponsorBlock**: Relies on a community API. Can fail or return malformed data.

## 3. Network & Connectivity
- Mobile networks are inherently unstable. The application must handle disconnects gracefully (hence the Hexagonal Architecture and robust event bus).
- **WebSocket**: Must handle reconnections without losing state (handled via the `AppStore` in the frontend).

## 4. Hardware Limitations
- Devices running Termux may have limited RAM and CPU. The backend Python application must remain lightweight.
- Caching logic must aggressively manage disk space (e.g., limits on `dl_cache/`).

## 5. Security & Isolation
- LunaWave runs locally on the user's device but exposes a web UI.
- The web UI acts as a remote control. Only users with the admin password can issue commands to mpv.
