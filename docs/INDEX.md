## Quick Navigation

1. STRUCTURE.md → pahami struktur project
2. FILE_INDEX.md → cari fungsi file
3. PROJECT_STRUCTURE_AUDIT.md -> masiih struktur projek
4. PATCHLOG.md → lihat perubahan terakhir
5. REPORT.md → lihat kondisi project

# AI Rules

Sebelum bekerja:

1. Baca INDEX.md
2. Baca PATCHLOG.md
3. Baca REPORT.md
4. Cari file di FILE_INDEX.md
5. Baru ubah source code

Setelah selesai:

1. Update FILE_INDEX.md jika fungsi file berubah
2. Tambahkan PATCHLOG.md
3. Update REPORT.md




# LunaWave — Project Knowledge Base Index

> **Last Scan:** 2026-07-09
> **Source:** Source code + `PROJECT_STRUCTURE_AUDIT.md` + `docs/LOG/PATCHLOG_REBRANDING.md`
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
├── LOG/
│   └── PATCHLOG_REBRANDING.md   ← Detail patch Sprint 2.1 & 3.2
├── REPORT/
│   ├── REBRANDING_REPORT.md     ← Laporan Sprint 2.1
│   └── REFACTOR_REPORT.md       ← Laporan Sprint 3.2
└── PROJECT_STRUCTURE_AUDIT.md   ← Roadmap refactoring aktif
```
## Current Status

Version : 1.0 (LunaWave)
Sprint : 3.2 (Refactoring Launcher)
Branch : main
Architecture : Hexagonal (Ports & Adapters)
Last Patch : 2026-07-09 (Optimasi Storage Unduhan)


**Alur kerja AI agent:** Baca `INDEX.md` → `STRUCTURE.md` → `FILE_INDEX.md` → cek `PATCHLOG.md` → baru sentuh source code. Setiap perubahan wajib append ke `PATCHLOG.md`.
