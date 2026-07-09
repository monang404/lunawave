# FILE_INDEX.md — LunaWave File Inventory

> **Last Updated:** 2026-07-09 | Sprint 3.2
> Format per file: File | Fungsi | Class | Function utama | Digunakan oleh | Menggunakan

---

## Root

**File:** `main.py`
**Fungsi:** Entry point utama — inisialisasi semua komponen, jalankan web server
**Class:** —
**Function utama:** `main()` (async), `check_connectivity()`, `mpv_reconnect_checker()`
**Digunakan oleh:** `asyncio.run()` langsung
**Menggunakan:** Semua modul (`config`, `core/*`, `engine/*`, `cache/*`, `server/*`, `plugins/*`)

---

**File:** `config.py`
**Fungsi:** Konfigurasi global: path, env vars, konstanta playback, auth
**Class:** —
**Function utama:** — (module-level constants: `BASE_DIR`, `DB_PATH`, `MPV_SOCKET`, `WEB_HOST`, `WEB_PORT`, `ADMIN_PASSWORD`)
**Digunakan oleh:** Semua modul
**Menggunakan:** `core/security.py` (hash_password saat generate password)

---

**File:** `start.py`
**Fungsi:** Bootstrap launcher — memanggil `launcher.__main__.main()`
**Class:** —
**Function utama:** — (3 baris: import + `main()`)
**Digunakan oleh:** User langsung (`python start.py`)
**Menggunakan:** `launcher/__main__.py`

---

## core/

**File:** `core/state.py`
**Fungsi:** Data model & enums global aplikasi
**Class:** `PlayerStatus(Enum)`, `AudioOutput(Enum)`, `PlaybackMode(Enum)`, `TrackInfo`, `AppState`
**Function utama:** — (dataclass fields saja)
**Digunakan oleh:** Hampir semua modul
**Menggunakan:** —

---

**File:** `core/event_bus.py`
**Fungsi:** Pub/sub EventBus — satu arah, type-safe, singleton `bus`
**Class:** `EventBus`
**Function utama:** `subscribe()`, `publish()`, `unsubscribe()`
**Digunakan oleh:** `engine/*`, `server/*`, `plugins/*`, `main.py`
**Menggunakan:** `core/observability.py`

---

**File:** `core/command_bus.py`
**Fungsi:** Single-writer CommandBus + konstanta `CMD.*`
**Class:** `CommandBus`
**Function utama:** `register()`, `dispatch()`, `CMD.*` constants
**Digunakan oleh:** `engine/command_router.py`, `server/handlers/websocket.py`, `plugins/*`
**Menggunakan:** `core/observability.py`

---

**File:** `core/events.py`
**Fungsi:** Domain event dataclasses (immutable payloads)
**Class:** `DomainEvent`, `TrackStartedEvent`, `TrackEndedEvent`, `TrackProgressEvent`, `TrackDurationEvent`, `QueueUpdatedEvent`, `LyricsUpdatedEvent`, `DownloadCompleteEvent`, `DownloadProgressEvent`, `LogMessageEvent`, `TrackPauseChangedEvent`
**Function utama:** —
**Digunakan oleh:** `engine/*`, `server/handlers/*`, `plugins/*`
**Menggunakan:** `core/state.py`

---

**File:** `core/ports.py`
**Fungsi:** Protocol interfaces (Ports & Adapters pattern)
**Class:** `AudioPlayerPort`, `MediaExtractorPort`, `TrackRepositoryPort`, `SessionRepositoryPort`, `DatabasePort`, `LyricsProvider`, `SponsorBlockProvider`
**Function utama:** — (Protocol method signatures)
**Digunakan oleh:** `engine/*`, `cache/*`, `server/*`
**Menggunakan:** `core/state.py`

---

**File:** `core/security.py`
**Fungsi:** Password hashing & verification (PBKDF2-SHA256)
**Class:** —
**Function utama:** `hash_password(password)`, `verify_password(password, hashed)`
**Digunakan oleh:** `config.py`, `server/handlers/auth.py`
**Menggunakan:** `werkzeug.security` atau `hashlib`

---

**File:** `core/task_utils.py`
**Fungsi:** Safe asyncio task wrapper dengan error logging
**Class:** —
**Function utama:** `safe_create_task(coro, name, on_error)`
**Digunakan oleh:** `engine/*`, `server/*`, `main.py`
**Menggunakan:** `asyncio`, `structlog`

---

**File:** `core/observability.py`
**Fungsi:** Prometheus metrics + OpenTelemetry tracer setup
**Class:** —
**Function utama:** `setup_tracing()`, `get_metrics_content()`
**Digunakan oleh:** `core/event_bus.py`, `core/command_bus.py`, `server/handlers/http.py`
**Menggunakan:** `prometheus_client`, `opentelemetry`

---

**File:** `core/exceptions.py`
**Fungsi:** Custom exception hierarchy
**Class:** `YtPlayerError`, `MpvConnectionError`, `TrackResolutionError`, `DownloadError`
**Function utama:** —
**Digunakan oleh:** `engine/mpv_controller.py`, `cache/resolver.py`
**Menggunakan:** —

---

## engine/

**File:** `engine/mpv_controller.py`
**Fungsi:** IPC ke MPV via Unix socket / Windows named pipe
**Class:** `MpvController`
**Function utama:** `connect()`, `play(url)`, `pause()`, `resume()`, `seek(s)`, `set_volume(v)`, `close()`, `_observe_events()`
**Digunakan oleh:** `main.py`, `engine/playback/controller.py`
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`, `core/task_utils`, `core/exceptions`

---

**File:** `engine/ytdlp_client.py`
**Fungsi:** Wrapper yt-dlp: search, stream URL resolve, MP3 download
**Class:** `YtDlpClient`
**Function utama:** `search(query, max_results)`, `get_stream_url(video_id)`, `download_mp3(video_id)`, `cancel_download()`
**Digunakan oleh:** `main.py`, `engine/radio_engine.py`, `cache/resolver.py`, `server/services/stream_prefetch.py`
**Menggunakan:** `yt_dlp`, `core/state`, `config`

---

**File:** `engine/radio_engine.py`
**Fungsi:** Radio Mode — autonomous playback dari artist seed dengan prefetch & deduplication (365 baris)
**Class:** `RadioMode`
**Function utama:** `on_activated()`, `on_deactivated()`, `next()`, `_build_standby()`, `_prefetch_next()`, `check_prefetch()`
**Digunakan oleh:** `main.py`, `engine/playback/controller.py`
**Menggunakan:** `core/events`, `core/state`, `core/ports`, `core/task_utils`, `cache/db` (via db param)

---

**File:** `engine/playback/controller.py`
**Fungsi:** Orkestrator utama playback — semua command play/pause/next/prev/seek/queue (351 baris)
**Class:** `PlaybackController`
**Function utama:** `play_track(track)`, `_on_cmd_toggle_pause()`, `_on_next()`, `_on_stop()`, `_on_seek()`, `_on_set_mode()`, semua queue ops
**Digunakan oleh:** `main.py`, `server/app.py`, `server/handlers/websocket.py`
**Menggunakan:** `core/*`, `cache/resolver`, `engine/queue_manager`, `engine/radio_engine`, `engine/playback/track_loader`

---

**File:** `engine/playback/track_loader.py`
**Fungsi:** Resolve stream URL + inject plugin (SponsorBlock, Lyrics) sebelum play
**Class:** `TrackLoader`
**Function utama:** `load_track(track) → str`
**Digunakan oleh:** `engine/playback/controller.py`
**Menggunakan:** `cache/resolver`, `core/ports`

---

**File:** `engine/command_router.py`
**Fungsi:** Dispatch CommandBus action → PlaybackController atau VolumeService
**Class:** `CommandRouter`
**Function utama:** `_route(action)`, `_route_volume(action)`
**Digunakan oleh:** `main.py`
**Menggunakan:** `core/command_bus`

---

**File:** `engine/download_manager.py`
**Fungsi:** Orkestrasi download MP3 + emit progress events
**Class:** `DownloadManager`
**Function utama:** `_on_download(track)`, `_do_download(track)`, `_update_progress(pct)`
**Digunakan oleh:** `main.py`
**Menggunakan:** `core/event_bus`, `core/state`, `engine/ytdlp_client`

---

**File:** `engine/queue_manager.py`
**Fungsi:** Queue Mode — advance ke track berikutnya (1 KB, minimal)
**Class:** `QueueMode`
**Function utama:** `next(controller)`
**Digunakan oleh:** `engine/playback/controller.py`
**Menggunakan:** —

---

**File:** `engine/volume_service.py`
**Fungsi:** Handle volume_up / volume_down / volume_set via EventBus
**Class:** `VolumeService`
**Function utama:** `_on_volume_up()`, `_on_volume_down()`, `_on_volume_set()`, `_apply_volume()`
**Digunakan oleh:** `main.py`
**Menggunakan:** `core/event_bus`, `core/state`, `engine/mpv_controller`

---

## cache/

**File:** `cache/db.py`
**Fungsi:** SQLite database layer via aiosqlite — semua query (389 baris, God Class)
**Class:** `Database`
**Function utama:** `init()`, `get_track()`, `upsert_track()`, `increment_play_count()`, `create_session()`, `get_recent_tracks()`, `get_favorites()`, `get_genre_artists()`, `increment_artist_click()`
**Digunakan oleh:** `main.py`, `services/discover_service.py`, `server/handlers/*`, `cache/resolver.py`
**Menggunakan:** `aiosqlite`, `core/state`, `config`

---

**File:** `cache/resolver.py`
**Fungsi:** Waterfall resolve stream URL: local path → DB cache → yt-dlp live
**Class:** `CacheResolver`
**Function utama:** `resolve(track) → str`
**Digunakan oleh:** `engine/playback/controller.py`, `engine/playback/track_loader.py`
**Menggunakan:** `cache/db`, `engine/ytdlp_client`, `core/ports`, `config`

---

## server/

**File:** `server/app.py`
**Fungsi:** aiohttp app factory + runner
**Class:** —
**Function utama:** `create_app(playback_controller, ytdlp, db)`, `run_server(app, host, port)`
**Digunakan oleh:** `main.py`
**Menggunakan:** `core/*`, `server/handlers/*`, `server/services/*`, `engine/playback/controller`

---

**File:** `server/handlers/websocket.py`
**Fungsi:** ConnectionManager + WS routing + command dispatch (317 baris)
**Class:** `ConnectionManager`
**Function utama:** `connect(ws)`, `disconnect(ws)`, `broadcast(msg)`, `ws_handler(request)`, `handle_ws_message()`
**Digunakan oleh:** `server/app.py`, `server/services/broadcast_service.py`
**Menggunakan:** `core/command_bus`, `core/state`, `server/serializers`, `server/middleware`, `server/handlers/auth`, `services/discover_service`

---

**File:** `server/handlers/http.py`
**Fungsi:** REST handlers: index SPA, health, stream proxy, metrics
**Class:** —
**Function utama:** `serve_index()`, `health_check()`, `serve_stream()`, `serve_metrics()`
**Digunakan oleh:** `server/app.py`
**Menggunakan:** `config`, `core/observability`

---

**File:** `server/handlers/auth.py`
**Fungsi:** Session auth via WebSocket — login, token validation, rate limit
**Class:** —
**Function utama:** `handle_auth(ws, data, manager, client_ip, db, now)`, `require_auth(manager, ws)`, `_prune_stale_ips()`
**Digunakan oleh:** `server/handlers/websocket.py`
**Menggunakan:** `core/security`

---

**File:** `server/handlers/event_listeners.py`
**Fungsi:** Bridge EventBus → broadcast ke semua WS clients
**Class:** —
**Function utama:** `setup_event_listeners(state, manager, broadcast_service, stream_prefetch)`
**Digunakan oleh:** `server/app.py`
**Menggunakan:** `core/events`, `core/task_utils`, `server/services/*`

---

**File:** `server/services/broadcast_service.py`
**Fungsi:** Push state, progress, lyrics, log, download progress ke WS clients
**Class:** `BroadcastService`
**Function utama:** `broadcast_state()`, `broadcast_progress()`, `broadcast_lyrics()`, `broadcast_log()`, `broadcast_download_progress()`
**Digunakan oleh:** `server/handlers/event_listeners.py`
**Menggunakan:** `server/handlers/websocket.py` (ConnectionManager), `server/serializers`

---

**File:** `server/services/stream_prefetch.py`
**Fungsi:** Pre-fetch & cache stream URL untuk lagu berikutnya
**Class:** `StreamPrefetchService`
**Function utama:** `prefetch_stream_url(video_id)`
**Digunakan oleh:** `server/handlers/event_listeners.py`
**Menggunakan:** `cache/db`, `engine/ytdlp_client`, `core/ports`, `config`

---

**File:** `server/middleware.py`
**Fungsi:** Rate limiting middleware (IP-based)
**Class:** —
**Function utama:** `check_rate_limit(manager, client_ip, now)`, `check_rate_limit_sync()`
**Digunakan oleh:** `server/handlers/websocket.py`
**Menggunakan:** —

---

**File:** `server/serializers.py`
**Fungsi:** Konversi AppState ↔ JSON dict
**Class:** —
**Function utama:** `state_to_dict(state)`, `track_to_dict(track)`, `dict_to_track(data)`
**Digunakan oleh:** `server/handlers/websocket.py`, `server/services/broadcast_service.py`
**Menggunakan:** `core/state`

---

## services/

**File:** `services/discover_service.py`
**Fungsi:** Query layer discovery: recent, favorites, cached, artists, genres
**Class:** `DiscoverService`
**Function utama:** `get_recent(n)`, `get_favorites(n)`, `get_cached(n)`, `get_featured_artists(n)`, `get_featured_genres(n)`
**Digunakan oleh:** `server/handlers/websocket.py`
**Menggunakan:** `cache/db`, `core/state`

---

## plugins/

**File:** `plugins/lyrics.py`
**Fungsi:** Fetch LRC dari lrclib.net, sync posisi lirik via progress event
**Class:** `LyricsFetcher`
**Function utama:** `fetch(track)`, `_parse_lrc(lrc_text)`, `_on_progress(event)`, `cleanup()`
**Digunakan oleh:** `main.py` (inject ke PlaybackController)
**Menggunakan:** `core/event_bus`, `core/events`, `core/state`, `config`, `aiohttp`

---

**File:** `plugins/notifications.py`
**Fungsi:** Termux MediaStyle notification + media button listener (no-op di non-Termux)
**Class:** `TermuxNowPlaying`
**Function utama:** `start()`, `cleanup()`, `_on_track_started()`, `_on_pause_changed()`, `_render()`
**Digunakan oleh:** `main.py`
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/state`

---

**File:** `plugins/sponsorblock.py`
**Fungsi:** Fetch & auto-skip sponsor segments via SponsorBlock API
**Class:** `SponsorBlockHandler`
**Function utama:** `fetch_segments(video_id)`, `_on_progress(event)`, `cleanup()`
**Digunakan oleh:** `main.py` (inject ke PlaybackController)
**Menggunakan:** `core/event_bus`, `core/events`, `core/state`, `config`, `aiohttp`

---

## launcher/

**File:** `launcher/gui.py`
**Fungsi:** `ServerManager` Tkinter UI — start/stop server, log viewer, dependency check (29 KB)
**Class:** `ServerManager(tk.Tk)`
**Function utama:** `_check_dependencies()`, `_is_running()`, `_refresh_status()`, `_build_ui()`, `server_port`
**Digunakan oleh:** `launcher/__main__.py`
**Menggunakan:** `launcher/network`, `launcher/process`, `launcher/updater`, `tkinter`

---

**File:** `launcher/process.py`
**Fungsi:** Subprocess lifecycle: start/stop server, pipe stdout, kill process tree
**Class:** `ServerProcess`
**Function utama:** `start()`, `stop()`, `is_running()`, `kill_process_tree(pid)`, `kill_mpv()`
**Digunakan oleh:** `launcher/gui.py`
**Menggunakan:** `subprocess`, `psutil` (opsional), `signal`

---

**File:** `launcher/network.py`
**Fungsi:** Deteksi port availability dan PID yang mengokupasi port
**Class:** —
**Function utama:** `check_port_in_use(port)`, `get_pid_occupying_port(port)`
**Digunakan oleh:** `launcher/gui.py`
**Menggunakan:** `socket`, `psutil`

---

**File:** `launcher/updater.py`
**Fungsi:** Cek versi & update OTA (stub — belum diimplementasi)
**Class:** —
**Function utama:** `check_for_updates()`, `get_release_info()`
**Digunakan oleh:** `launcher/gui.py`
**Menggunakan:** —

---

## data/ (scripts)

**File:** `data/export_to_sqlite.py`
**Fungsi:** One-time migration script — import data ke `lunawave.db`
**Class:** —
**Function utama:** (migration logic)
**Digunakan oleh:** Developer manual saja
**Menggunakan:** `sqlite3`
**⚠️ Seharusnya dipindah ke `scripts/`**
