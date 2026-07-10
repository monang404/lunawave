---
last_verified: 2026-07-10
sprint: 3.2
status: current
---

## Quick Navigation

1. AI_CONTEXT - untuk ai mehamai progress aplikasi ini
2. STRUCTURE.md → pahami struktur project
3. FILE_INDEX.md → cari fungsi file
4. PROJECT_STRUCTURE_AUDIT.md -> masiih struktur projek
5. PATCHLOG.md → lihat perubahan terakhir
6. REPORT.md → lihat kondisi project
7. MIGRATION_GUIDE.md panduan untuk migrasi ke /kompas
8. /docs/kompas/* Gambaran arsitektur impian dari aplikasi ini
9. STATUS.md → cek kondisi per-file (sudah/belum di-refactor)

# Untuk AI Agent

## Baca urutan ini sebelum kerja:
1. INDEX.md (ini) — orientasi
2. PATCHLOG.md — perubahan terakhir
3. REPORT.md — kondisi & temuan aktif
4. FILE_INDEX.md — cari file spesifik (mungkin stale, verify dulu)
5. Baru sentuh source code

## Setelah selesai kerja:
1. Append PATCHLOG.md (jangan edit entri lama)
2. Update FILE_INDEX.md kalau ada file yang berubah fungsi
3. Update status temuan di REPORT.md kalau ada yang resolved

## ⚠️ Danger Zones — hati-hati ekstra:
| File | Kenapa Berbahaya | Instruksi |
|------|-----------------|-----------|
| `engine/playback/controller.py` | Closure kompleks, referensi silang | Jangan refactor tanpa sprint plan |
| `server/handlers/websocket.py` | Monolith 317 baris, F-01 belum dipecah | Jangan pecah tanpa MIGRATION_GUIDE Tahap 3 |
| `cache/admin_password.txt` | Berisi hash password admin | JANGAN pernah commit file ini |
| `data/artists_enriched.json` | 185KB JSON statis | Jangan modifikasi — jadwalkan migrasi ke DB |
| `cache/db.py` | God class 388 baris | Refactor hanya sesuai MIGRATION_GUIDE Tahap 2 |

## ❌ Yang TIDAK BOLEH dilakukan AI:
- Jangan ganti aiohttp ke framework lain (FastAPI, dll)
- Jangan tambah JS framework apapun di frontend
- Jangan ganti SQLite ke database lain
- Jangan refactor 2 tahap sekaligus dalam 1 commit




# LunaWave — Project Knowledge Base Index

> **Last Scan:** 2026-07-09
> **Source:** Source code + `PROJECT_STRUCTURE_AUDIT.md`
> **Status:** Sprint 3.2 selesai. Sprint berikutnya: refactor `cache/`, `engine/adapters/`, pisah `ConnectionManager`.

---

## Tujuan Project

LunaWave adalah **pemutar musik berbasis YouTube** yang berjalan sebagai server lokal (aiohttp + asyncio), diakses via browser mobile/desktop. Audio diputar oleh MPV melalui IPC socket. Dirancang untuk Termux (Android) sebagai host utama, dengan dukungan Windows. Sebelumnya dikenal sebagai *YT Termux Player / bagas.fm / ytgui*.

Fitur utama: Radio autoplay, Queue mode, SponsorBlock, lirik real-time (LRCLIB), smart caching MP3, portal Admin/Client, multi-room (arsitektur siap, belum fully active).

---

## Entry Point Aplikasi

| Jalur | File | Keterangan |
|-------|------|------------|
| **Backend utama** | `main.py` | `asyncio.run(main())` — inisialisasi semua komponen, lalu menjalankan web server |
| **GUI launcher** | `start.py` → `launcher/__main__.py` | Tkinter wrapper; fallback headless ke `main.py` |
| **Shell (Linux/Termux)** | `start.sh` | Bash launcher dengan env var setup |
| **Shell (Windows)** | `start.bat` | Batch launcher |

---

## Struktur Folder Utama

```
lunawave/
├── main.py            Entry point backend
├── config.py          Konfigurasi global & env vars
├── start.py           Bootstrap launcher GUI
├── core/              Primitives: state, bus, events, ports, security
├── engine/            Domain logic: MPV, yt-dlp, radio, playback, queue
│   └── playback/      Sub-package: controller + track_loader
├── server/            HTTP & WebSocket layer (aiohttp)
│   ├── handlers/      auth, http, websocket, event_listeners
│   └── services/      broadcast, stream_prefetch
├── cache/             Database SQLite + resolver strategy
├── data/              DB aktif, artists JSON, migration script
├── services/          High-level: DiscoverService
├── plugins/           Opsional: lyrics, notifications, sponsorblock
├── launcher/          GUI launcher (Tkinter) — direfactor Sprint 3.2
├── web/               Frontend (vanilla JS + CSS)
│   └── static/
│       ├── index.html SPA monolitik (36 KB)
│       ├── js/        main, audio, ws, store, dom, utils + subdirs
│       └── css/       tokens, components, layout, platform, base
├── scripts/           Dev utilities
├── scratch/           Dev scratch files
└── docs/              Dokumentasi project ini
```

---

## Modul Utama & Fungsi Singkat

| Modul | Fungsi |
|-------|--------|
| `config.py` | Semua konstanta & env vars (`DB_PATH`, `MPV_SOCKET`, `WEB_PORT`, dll.) |
| `core/state.py` | `AppState`, `TrackInfo`, enums `PlayerStatus`, `PlaybackMode`, `AudioOutput` |
| `core/event_bus.py` | Pub/sub `EventBus` singleton (`bus`) |
| `core/command_bus.py` | Single-writer `CommandBus` + konstanta CMD |
| `core/events.py` | 10 `DomainEvent` dataclasses (TrackStarted, TrackEnded, dll.) |
| `core/ports.py` | Protocol interfaces: `AudioPlayerPort`, `MediaExtractorPort`, `DatabasePort`, dll. |
| `engine/mpv_controller.py` | IPC ke MPV (Unix socket / named pipe): play, pause, seek, volume, reconnect |
| `engine/ytdlp_client.py` | Wrapper yt-dlp: search, get_stream_url, download_mp3 |
| `engine/radio_engine.py` | Autonomous radio: artist seed, prefetch, deduplication, standby queue |
| `engine/playback/controller.py` | Orkestrator playback: play, pause, next, prev, seek, mode switch, queue ops |
| `cache/db.py` | SQLite via aiosqlite: tracks, sessions, stream_url, play_count, artists, genres |
| `cache/resolver.py` | Resolve stream URL: local path → cache DB → yt-dlp (waterfall) |
| `server/app.py` | aiohttp app factory + runner |
| `server/handlers/websocket.py` | `ConnectionManager` + WS routing + command dispatch |
| `server/handlers/http.py` | REST: `/`, `/stream`, `/health`, `/metrics` |
| `server/services/broadcast_service.py` | Push state/progress/lyrics ke semua WS clients |
| `services/discover_service.py` | Query recent, favorites, cached, artists, genres dari DB |
| `plugins/lyrics.py` | Fetch + parse LRC dari lrclib.net, sync via TrackProgressEvent |
| `plugins/notifications.py` | Termux MediaStyle notification (no-op di luar Termux) |
| `plugins/sponsorblock.py` | Fetch & skip sponsor segments via SponsorBlock API |
| `launcher/gui.py` | `ServerManager` (Tkinter): start/stop server, log viewer, dependency check |

---

## Statistik Project

| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | ~35 |
| Total file `.py` (ekskl. `__pycache__`) | 54 |
| Total file `.js` | 21 |
| Total file `.css` | 21 |
| Total class (Python) | 49 |
| Total function/method (Python) | 255 |
| Last Sprint | 3.2 — Extract `start.py` → `launcher/` |

---

## Cara Membaca Dokumentasi

```
docs/
├── INDEX.md              ← Mulai di sini: ringkasan & orientasi
├── STRUCTURE.md          ← Detail setiap folder & hubungannya
├── FILE_INDEX.md         ← Inventaris setiap file .py penting
├── PATCHLOG.md           ← Riwayat semua perubahan (append-only)
├── REPORT.md             ← Ringkasan analisis & rekomendasi

```
## Current Status

Version : 1.0 (LunaWave)
Sprint : 3.2 (Refactoring Launcher)
Branch : main
Architecture : Hexagonal (Ports & Adapters)
Last Patch : 2026-07-09 (Optimasi Storage Unduhan)
