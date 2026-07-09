# STRUCTURE.md — LunaWave Folder Reference

> **Last Updated:** 2026-07-09 | Sprint 3.2

---

## Root

**Folder:** `/` (root)
**Fungsi:** Entry points, konfigurasi global, launcher scripts
**Isi:** `main.py`, `config.py`, `start.py`, `start.sh`, `start.bat`, `requirements.txt`, `README.md`, `lunawave.log`
**Digunakan oleh:** Semua modul mengimport `config.py`; `main.py` adalah orkestrasi startup penuh

---

## core/

**Folder:** `core/`
**Fungsi:** Lapisan fondasi — shared primitives, tidak boleh mengimport dari layer lain
**Isi:**
- `state.py` — `AppState`, `TrackInfo`, enums (`PlayerStatus`, `PlaybackMode`, `AudioOutput`)
- `event_bus.py` — `EventBus` singleton pub/sub (`bus`)
- `command_bus.py` — `CommandBus` single-writer + konstanta `CMD.*`
- `events.py` — 10 `DomainEvent` dataclasses (immutable)
- `ports.py` — Protocol interfaces: `AudioPlayerPort`, `MediaExtractorPort`, `DatabasePort`, `LyricsProvider`, `SponsorBlockProvider`
- `security.py` — `hash_password()`, `verify_password()` (PBKDF2)
- `task_utils.py` — `safe_create_task()` wrapper asyncio
- `observability.py` — Prometheus counter (`lunawave_events_total`), OpenTelemetry tracer stub
- `log_config.py` — Setup structlog JSON logging
- `exceptions.py` — `YtPlayerError`, `MpvConnectionError`, `TrackResolutionError`, `DownloadError`

**Digunakan oleh:** `engine/`, `cache/`, `server/`, `plugins/`, `services/`, `main.py`

---

## engine/

**Folder:** `engine/`
**Fungsi:** Domain logic audio & playback — mencakup adapter external (MPV, yt-dlp) dan mode engine
**Isi:**
- `mpv_controller.py` — `MpvController`: IPC ke MPV via Unix socket/named pipe (play, pause, seek, volume, reconnect, event observe)
- `ytdlp_client.py` — `YtDlpClient`: search YouTube, get stream URL, download MP3; timeout via `YTDLP_RESOLVE_TIMEOUT_SEC`
- `radio_engine.py` — `RadioMode`: autonomous playback dari artist seed, standby queue, prefetch, deduplication
- `command_router.py` — `CommandRouter`: dispatch CommandBus action → `PlaybackController` / `VolumeService`
- `download_manager.py` — `DownloadManager`: orkestrasi download MP3 + progress event
- `queue_manager.py` — `QueueMode`: advance ke track berikutnya di queue (minimal, 1 KB)
- `volume_service.py` — `VolumeService`: handler volume_up/down/set via EventBus

**Isi sub-folder `engine/playback/`:**
- `controller.py` — `PlaybackController`: orkestrator utama play/pause/next/prev/seek/queue ops
- `track_loader.py` — `TrackLoader`: resolve + inject plugin (SponsorBlock, Lyrics) sebelum play

**Digunakan oleh:** `main.py`, `server/app.py`, `server/handlers/websocket.py`
**⚠️ Catatan audit:** `mpv_controller.py` dan `ytdlp_client.py` sebaiknya dipindah ke `adapters/` (lihat `PROJECT_STRUCTURE_AUDIT.md` §6B)

---

## cache/

**Folder:** `cache/`
**Fungsi:** Persistence layer SQLite + strategi resolve stream URL
**Isi:**
- `db.py` — `Database`: semua query SQLite (tracks, sessions, play_count, stream_url, artists, genres, library)
- `resolver.py` — `CacheResolver`: waterfall resolve → local path → DB cache → yt-dlp live
- `schema.sql` — DDL schema database
- `library.db` — SQLite library cache (69 KB)
- `admin_password.txt` — ⚠️ hash password admin (auto-generated, di luar `.gitignore` harap diverifikasi)
- `mp3/` — direktori MP3 download cache (runtime-generated)

**Digunakan oleh:** `main.py`, `engine/playback/controller.py`, `server/`, `services/`
**⚠️ Catatan audit:** `cache/` terlalu campur — sebaiknya pisah `persistence/` (db.py, schema.sql) dari `cache/` (resolver.py, mp3/)

---

## data/

**Folder:** `data/`
**Fungsi:** Data semi-permanen project
**Isi:**
- `lunawave.db` — SQLite DB utama aktif (180 KB + WAL 160 KB)
- `lunawave.db-shm`, `lunawave.db-wal` — SQLite WAL files
- `artists_enriched.json` — ⚠️ 185 KB data artis (sebaiknya di-import ke DB sebagai tabel)
- `export_to_sqlite.py` — ⚠️ One-time migration script (sebaiknya dipindah ke `scripts/`)

**Digunakan oleh:** `config.py` (DB_PATH), `cache/db.py`, `engine/radio_engine.py`
**⚠️ Catatan:** `data/ytgui.db` (warisan, 212 KB) tidak terdeteksi di RAR ini — kemungkinan sudah dihapus ✅

---

## server/

**Folder:** `server/`
**Fungsi:** HTTP & WebSocket layer — aiohttp app factory, routing, middleware
**Isi:**
- `app.py` — `create_app()`, `run_server()`: factory aiohttp application
- `middleware.py` — rate limiting middleware
- `serializers.py` — `state_to_dict()`, `track_to_dict()`, `dict_to_track()`

**Isi sub-folder `server/handlers/`:**
- `auth.py` — Session auth: `handle_auth()`, `require_auth()`, IP rate limit prune
- `http.py` — REST handlers: `serve_index`, `health_check`, `serve_stream`, `serve_metrics`
- `websocket.py` — `ConnectionManager` + `ws_handler()` + `handle_ws_message()` (⚠️ God handler — 317 baris)
- `event_listeners.py` — `setup_event_listeners()`: bridge EventBus → broadcast ke WS clients

**Isi sub-folder `server/services/`:**
- `broadcast_service.py` — `BroadcastService`: push state/progress/lyrics/log/download ke WS clients
- `stream_prefetch.py` — `StreamPrefetchService`: pre-fetch stream URL untuk lagu berikutnya

**Digunakan oleh:** `main.py`
**Menggunakan:** `core/*`, `engine/playback/controller.py`, `cache/db.py`, `services/discover_service.py`

---

## services/

**Folder:** `services/`
**Fungsi:** High-level application services (query layer di atas cache/db)
**Isi:**
- `discover_service.py` — `DiscoverService`: `get_recent()`, `get_favorites()`, `get_cached()`, `get_featured_artists()`, `get_featured_genres()`

**Digunakan oleh:** `server/handlers/websocket.py`
**Menggunakan:** `cache/db.py`, `core/state.py`

---

## plugins/

**Folder:** `plugins/`
**Fungsi:** Fitur opsional/platform-specific — berkomunikasi hanya via EventBus & CommandBus
**Isi:**
- `lyrics.py` — `LyricsFetcher`: fetch LRC dari lrclib.net, sync posisi via `TrackProgressEvent`
- `notifications.py` — `TermuxNowPlaying`: MediaStyle notification Termux; no-op di luar Termux
- `sponsorblock.py` — `SponsorBlockHandler`: fetch & auto-skip sponsor segments

**Digunakan oleh:** `main.py` (inject ke `PlaybackController`)
**Menggunakan:** `core/event_bus.py`, `core/events.py`, `core/command_bus.py`

---

## launcher/

**Folder:** `launcher/`
**Fungsi:** GUI launcher Tkinter — dipecah dari `start.py` pada Sprint 3.2
**Isi:**
- `gui.py` — `ServerManager(tk.Tk)`: UI start/stop server, log viewer, dependency check, port management
- `process.py` — `ServerProcess`: subprocess lifecycle, stdout pipe, kill process tree, kill mpv
- `network.py` — `check_port_in_use()`, `get_pid_occupying_port()`
- `updater.py` — `check_for_updates()`, `get_release_info()` (stub, belum implementasi)
- `__main__.py` — Coordinator startup; fallback headless jika Tkinter tidak tersedia

**Digunakan oleh:** `start.py`
**Menggunakan:** `subprocess`, `tkinter`, `socket`

---

## web/

**Folder:** `web/`
**Fungsi:** Seluruh frontend aset (vanilla JS + CSS, tanpa build system)
**Isi:**

`web/static/index.html` — ⚠️ SPA HTML monolitik 36 KB (semua panel, modal, player dalam 1 file)
`web/static/manifest.json` — PWA manifest
`web/static/sw.js` — Service Worker (`lunawave-v1` cache)

**`web/static/js/` (entry & core):**
- `main.js` — Bootstrap & inisialisasi semua modul
- `audio.js` — Browser Audio Engine (13 KB): sync browser audio dengan MPV
- `ws.js` — WebSocket client (9 KB): connect, reconnect, message dispatch
- `store.js` — State store in-memory sederhana
- `utils.js` — `safeStorage` (dengan legacy key migration `ytgui_*`→`lunawave_*`), helper umum
- `dom.js` — DOM helper functions
- `config.js` — Config minimal (55 bytes)
- `portal.js` — Admin portal entry

**`web/static/js/events/`:** handler player, queue, lyrics, settings
**`web/static/js/render/`:** view renderers: discover, queue, search, now-playing, player, lyrics
**`web/static/js/platform/`:** keyboard, touch, viewport handlers
**`web/static/js/services/`:** `auth.js` — session management

**`web/static/css/`:**
- `tokens.css` — Design tokens (CSS variables)
- `base/` — reset, animations, typography
- `components/` — cards, player-bar, queue, search, lyrics, toasts, dll. (8 file)
- `layout/` — app-shell, grid, nav
- `platform/` — desktop, tablet, mobile, landscape, safe-area
- `portal.css` — Admin portal styles

**Digunakan oleh:** Browser client; di-serve oleh `server/handlers/http.py`

---

## scripts/ & scratch/

**Folder:** `scripts/`
**Fungsi:** Utility scripts developer
**Isi:** `generate_icons.py` (PWA icons), `inject_svgs.py`, `shortcuts/` (play_pause, next_track, volume_up shell scripts)

**Folder:** `scratch/`
**Fungsi:** File debug/dev sementara
**Isi:** `check_db.py` — query DB untuk debugging

---

## docs/

**Folder:** `docs/`
**Fungsi:** Knowledge base project — acuan utama sebelum AI melakukan perubahan
**Isi:** `INDEX.md`, `STRUCTURE.md`, `FILE_INDEX.md`, `PATCHLOG.md`, `REPORT.md`, `PROJECT_STRUCTURE_AUDIT.md`, `LOG/`, `REPORT/`
