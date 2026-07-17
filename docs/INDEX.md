---
title : LunaWave Documentation Index
last_verified: 2026-07-13
sprint: 3.2
status: current
---

## Quick Navigation

1. `AI_CONTEXT.md` → **baca ini dulu** — constraints, alur kerja AI, automation
2. `STATUS.md` → kondisi per-file & sprint target
3. `PATCHLOG.md` → perubahan terakhir
4. `REPORT.md` → analisis, temuan, statistik (auto-generated)
5. `FILE_INDEX.md` → inventaris file (auto-generated, jangan edit manual)
6. `architecture/folder_structure.md` → detail struktur setiap folder dan penggunaannya
7. `architecture/overview.md` → arsitektur impian, target desain, dan blueprint
8. `adr/` → Architecture Decision Records

# Untuk AI Agent

## Baca urutan ini sebelum kerja:
1. `docs/AI_CONTEXT.md` — **wajib pertama**, berisi constraints, batasan, dan alur kerja lengkap
2. `docs/STATUS.md` — kondisi per-file & sprint target
3. `docs/PATCHLOG.md` — 2-3 entri terakhir
4. Jalankan `python automation/find_owner.py <nama_file_atau_class>` — orientasi modul yang relevan
5. Baru sentuh source code

> ⚙️ `FILE_INDEX.md` dan blok statistik `REPORT.md` adalah **auto-generated** — jangan edit manual.
> Jalankan `python automation/generate_file_index.py` atau `run_all.py` setelah ada perubahan kode.

## Setelah selesai kerja:
1. Jalankan `python automation/architecture_lint.py` — pastikan tidak ada violation baru
2. Jalankan `python automation/generate_file_index.py` — jika ada file/class/fungsi yang berubah
3. Jalankan `python automation/generate_report.py` — jika ada penambahan/penghapusan file
   *(atau `python automation/run_all.py` untuk jalankan semua sekaligus)*
4. Append entry baru ke `docs/PATCHLOG.md` dengan format ID `PATCH-YYYY-MM-DD-NNN`
5. Update `docs/STATUS.md` jika kondisi file berubah

## ⚠️ Danger Zones — hati-hati ekstra:
| File | Kenapa Berbahaya | Instruksi |
|------|-----------------|-----------|
| `engine/playback/controller.py` | Closure kompleks, referensi silang | Jangan refactor tanpa sprint plan |
| `server/handlers/websocket.py` | Monolith 354 baris, restricted file | Jangan pecah tanpa persetujuan eksplisit |
| `cache/admin_password.txt` | Berisi hash password admin | JANGAN pernah commit file ini |
| `data/artists_enriched.json` | 185KB JSON statis | Jangan modifikasi — jadwalkan migrasi ke DB |
| `cache/db.py` | God class, refactor bertahap | Refactor hanya sesuai sprint plan — lihat `docs/STATUS.md` |

## ❌ Yang TIDAK BOLEH dilakukan AI:
- Jangan ganti aiohttp ke framework lain (FastAPI, dll)
- Jangan tambah JS framework apapun di frontend
- Jangan ganti SQLite ke database lain
- Jangan refactor 2 tahap sekaligus dalam 1 commit




# LunaWave — Project Knowledge Base Index

> **Last Scan:** 2026-07-13
> **Source:** Source code + `docs/architecture/folder_structure.md`

---

## Tujuan Project

LunaWave adalah **pemutar musik berbasis YouTube** yang berjalan sebagai server lokal (aiohttp + asyncio), diakses via browser mobile/desktop. Audio diputar oleh MPV melalui IPC socket. Dirancang untuk Termux (Android) sebagai host utama, dengan dukungan Windows. Sebelumnya dikenal sebagai *YT Termux Player / bagas.fm / ytgui*.

Fitur utama: Radio autoplay, Queue mode, SponsorBlock, lirik real-time (LRCLIB), smart caching MP3, portal Admin/Client. Arsitektur EventBus sudah menyiapkan fondasi multi-room untuk pengembangan mendatang (belum aktif — lihat ADR-0005).

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
├── core/              Primitives: state, bus, events, ports, security, commands
├── adapters/          External system adapters (Hexagonal)
│   ├── mpv/           IPC adapter ke MPV player
│   └── ytdlp/         Wrapper yt-dlp client
├── engine/            Domain logic: radio, playback, queue
│   └── playback/      Sub-package: controller + queue_ops + mode_ops
├── persistence/       Data layer: repositories SQLite (track, library, dll.)
├── server/            HTTP & WebSocket layer (aiohttp)
│   ├── handlers/      auth, http, websocket, event_listeners
│   └── services/      broadcast, stream_prefetch
├── cache/             resolver.py (belum direlokasi) — DB lama sudah ke persistence/
├── data/              DB aktif, artists JSON, migration script
├── services/          High-level: DiscoverService
├── plugins/           Opsional: lyrics, notifications, sponsorblock
├── launcher/          GUI launcher (Tkinter)
├── web/               Frontend (vanilla JS + CSS)
│   └── static/
│       ├── index.html SPA monolitik
│       ├── js/        main, audio, ws, store, dom, utils + subdirs
│       └── css/       tokens, components, layout, platform, base
├── automation/           Dev utilities & health checkers
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
| `core/command_bus.py` | Single-writer `CommandBus` + `core/commands.py` |
| `core/events.py` | 10 `DomainEvent` dataclasses (TrackStarted, TrackEnded, dll.) |
| `core/ports.py` | Protocol interfaces: `AudioPlayerPort`, `MediaExtractorPort`, `DatabasePort`, dll. |
| `adapters/mpv/` | IPC ke MPV (Unix socket / named pipe): play, pause, seek, volume, reconnect |
| `adapters/ytdlp/` | Wrapper yt-dlp: search, get_stream_url, download_mp3 |
| `engine/radio_engine.py` | Autonomous radio: artist seed, prefetch, deduplication, standby queue |
| `engine/playback/controller.py` | Orkestrator playback: play, pause, next, prev, seek, mode switch, queue ops |
| `persistence/` | SQLite via aiosqlite: repositories, resolver strategy |
| `cache/resolver.py` | Resolve stream URL: local path → cache DB → yt-dlp (waterfall) — *belum direlokasi* |
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

> Statistik aktual ada di `docs/REPORT.md` §Statistik Project (auto-generated, selalu akurat).
> Angka di bawah ini **tidak diupdate manual** — lihat REPORT.md untuk data terkini.

---

## Cara Membaca Dokumentasi

```
docs/
├── AI_CONTEXT.md         ← Entry point AI — baca ini dulu
├── INDEX.md              ← Orientasi & navigasi (ini)
├── STATUS.md             ← Kondisi per-file & sprint target
├── architecture/folder_structure.md ← Detail struktur setiap folder
├── FILE_INDEX.md         ← Inventaris file (sebagian auto-generated)
├── PATCHLOG.md           ← Riwayat perubahan (append-only)
├── REPORT.md             ← Analisis, temuan, statistik (sebagian auto-generated)
└── adr/                  ← Architecture Decision Records
```
