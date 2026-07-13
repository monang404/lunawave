---
title: LunaWave File Index
last_verified: 2026-07-13
generated: true
note: Isi file ini di-generate otomatis oleh scripts/generate_file_index.py — JANGAN edit manual.
---

# FILE_INDEX.md — LunaWave File Inventory

> ⚙️ File ini di-generate otomatis oleh `scripts/generate_file_index.py`.
> **Jangan edit manual** — perubahan akan ditimpa saat script dijalankan berikutnya.
> Jalankan `python scripts/generate_file_index.py` setelah ada file/class/fungsi yang berubah.
>
> Format per file: File | Fungsi | Class | Function utama | Digunakan oleh | Menggunakan

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-13 oleh `scripts/generate_file_index.py`
> **Jangan edit blok ini secara manual** — perubahan akan ditimpa saat script dijalankan ulang.


## Root

**File:** `config.py`
**Fungsi:** Load and expose all environment-based runtime configuration constants for LunaWave, including paths, ports, and the admin password.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/connection`, `adapters/ytdlp/downloader`, `adapters/ytdlp/resolver`, `cache/resolver`, `core/log_config`, _9 lainnya_
**Menggunakan:** —


---

**File:** `config_security.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `generate_admin_password()`
**Digunakan oleh:** —
**Menggunakan:** `core/security`


---

**File:** `main.py`
**Fungsi:** Bootstrap all LunaWave subsystems and start the async aiohttp web server.
**Class:** —
**Function utama:** `main()`
**Digunakan oleh:** —
**Menggunakan:** `core/log_config`, `core/state`, `core/event_bus`, `engine/ytdlp_client`, `engine/mpv_controller`, `cache/db`, _7 lainnya_


---

**File:** `start.py`
**Fungsi:** GUI entry point that opens the LunaWave Server Manager desktop window.
**Class:** —
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `launcher/__main__`


---


## core/

**File:** `core/command_bus.py`
**Fungsi:** Implement a single-writer CommandBus that enforces exactly one handler per command name and records Prometheus metrics for every execution.
**Class:** `CommandBus`
**Function utama:** `register()`, `unregister()`
**Digunakan oleh:** `engine/command_router`, `engine/download_manager`, `engine/volume_service`, `plugins/notifications`, `server/handlers/websocket`, _3 lainnya_
**Menggunakan:** `core/observability`, `core/commands`


---

**File:** `core/commands.py`
**Fungsi:** Defines all command constants used by the CommandBus. Separated to allow importing without pulling in the entire CommandBus.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `core/command_bus`
**Menggunakan:** —


---

**File:** `core/event_bus.py`
**Fungsi:** Implement a lightweight async pub/sub EventBus that decouples modules via typed DomainEvents, using weak references for method handlers.
**Class:** `EventBus`
**Function utama:** `subscribe()`, `purge_dead_refs()`, `unsubscribe()`
**Digunakan oleh:** `adapters/mpv/observer`, `engine/download_manager`, `engine/playback/controller`, `engine/volume_service`, `main`, _3 lainnya_
**Menggunakan:** `core/task_utils`, `core/events`, `core/observability`


---

**File:** `core/events.py`
**Fungsi:** Define all typed DomainEvent dataclasses for the LunaWave event bus.
**Class:** `DomainEvent`, `TrackStartedEvent(DomainEvent)`, `TrackEndedEvent(DomainEvent)`, `TrackProgressEvent(DomainEvent)`, `TrackDurationEvent(DomainEvent)`, `QueueUpdatedEvent(DomainEvent)`, `LyricsUpdatedEvent(DomainEvent)`, `DownloadCompleteEvent(DomainEvent)`, `DownloadProgressEvent(DomainEvent)`, `LogMessageEvent(DomainEvent)`, `TrackPauseChangedEvent(DomainEvent)`
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/observer`, `core/event_bus`, `engine/download_manager`, `engine/playback/controller`, `engine/playback/mode_ops`, _10 lainnya_
**Menggunakan:** `core/state`


---

**File:** `core/exceptions.py`
**Fungsi:** Define the custom exception hierarchy for LunaWave error conditions.
**Class:** `YtPlayerError(Exception)`, `MpvConnectionError(YtPlayerError)`, `TrackResolutionError(YtPlayerError)`, `DownloadError(YtPlayerError)`
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/connection`
**Menggunakan:** —


---

**File:** `core/log_config.py`
**Fungsi:** Configure structlog and stdlib logging with an async queue handler, rotating file output, and a compact single-line renderer.
**Class:** —
**Function utama:** `simple_renderer()`, `setup_logging()`
**Digunakan oleh:** `main`
**Menggunakan:** `config`


---

**File:** `core/observability.py`
**Fungsi:** Expose Prometheus metric singletons and an OpenTelemetry tracer for application-wide instrumentation.
**Class:** —
**Function utama:** `get_metrics_content()`
**Digunakan oleh:** `core/command_bus`, `core/event_bus`, `server/connection_manager`, `server/handlers/http`, `server/handlers/websocket`, _1 lainnya_
**Menggunakan:** —


---

**File:** `core/ports.py`
**Fungsi:** Declare Protocol interfaces (ports) for LunaWave's hexagonal architecture.
**Class:** `AudioPlayerPort(Protocol)`, `MediaExtractorPort(Protocol)`, `StreamResolverPort(Protocol)`, `TrackRepositoryPort(Protocol)`, `SessionRepositoryPort(Protocol)`, `DatabasePort(TrackRepositoryPort, SessionRepositoryPort, Protocol)`, `LyricsProvider(Protocol)`, `SponsorBlockProvider(Protocol)`
**Function utama:** `is_connected()`, `cancel_download()`, `db()`
**Digunakan oleh:** `cache/resolver`, `engine/download_manager`, `engine/playback/controller`, `engine/playback/mode_ops`, `engine/playback/track_loader`, _6 lainnya_
**Menggunakan:** `core/state`


---

**File:** `core/security.py`
**Fungsi:** Provide PBKDF2-SHA256 password hashing and constant-time verification.
**Class:** —
**Function utama:** `hash_password()`, `verify_password()`
**Digunakan oleh:** `config_security`, `server/handlers/auth`
**Menggunakan:** —


---

**File:** `core/state.py`
**Fungsi:** Define shared application state dataclasses, enums, and the single mutable AppState object for LunaWave.
**Class:** `PlayerStatus(Enum)`, `AudioOutput(str, Enum)`, `PlaybackMode(Enum)`, `TrackInfo`, `AppState`
**Function utama:** —
**Digunakan oleh:** `adapters/ytdlp/searcher`, `cache/resolver`, `core/events`, `core/ports`, `engine/download_manager`, _25 lainnya_
**Menggunakan:** —


---

**File:** `core/task_utils.py`
**Fungsi:** Wrap asyncio.create_task with centralized exception handling to prevent silent background-task crashes.
**Class:** —
**Function utama:** `safe_create_task()`
**Digunakan oleh:** `adapters/mpv/observer`, `core/event_bus`, `engine/download_manager`, `engine/playback/controller`, `engine/playback/track_loader`, _5 lainnya_
**Menggunakan:** —


---


## adapters/

**File:** `adapters/mpv/__init__.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `MpvController`
**Function utama:** `is_connected()`
**Digunakan oleh:** —
**Menggunakan:** `adapters/mpv/connection`, `adapters/mpv/ipc`, `adapters/mpv/observer`


---

**File:** `adapters/mpv/connection.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `MpvConnection`
**Function utama:** `reader()`, `writer()`
**Digunakan oleh:** `adapters/mpv/__init__`
**Menggunakan:** `core/exceptions`, `config`


---

**File:** `adapters/mpv/ipc.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `MpvIPC`
**Function utama:** `pop_pending()`, `cancel_all_pending()`
**Digunakan oleh:** `adapters/mpv/__init__`
**Menggunakan:** —


---

**File:** `adapters/mpv/observer.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `MpvObserver`
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/__init__`
**Menggunakan:** `core/event_bus`, `core/events`, `core/task_utils`


---

**File:** `adapters/ytdlp/__init__.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `YtDlpClient`
**Function utama:** `cancel_download()`
**Digunakan oleh:** —
**Menggunakan:** `adapters/ytdlp/searcher`, `adapters/ytdlp/resolver`, `adapters/ytdlp/downloader`


---

**File:** `adapters/ytdlp/common.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `adapters/ytdlp/downloader`, `adapters/ytdlp/resolver`, `adapters/ytdlp/searcher`
**Menggunakan:** —


---

**File:** `adapters/ytdlp/downloader.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `YtDlpDownloader`
**Function utama:** `cancel_download()`
**Digunakan oleh:** `adapters/ytdlp/__init__`
**Menggunakan:** `config`, `adapters/ytdlp/common`


---

**File:** `adapters/ytdlp/resolver.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `YtDlpResolver`
**Function utama:** `_extract_sync()`, `_pick_audio_url()`
**Digunakan oleh:** `adapters/ytdlp/__init__`
**Menggunakan:** `config`, `adapters/ytdlp/common`


---

**File:** `adapters/ytdlp/searcher.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `YtDlpSearcher`
**Function utama:** `_extract_sync()`, `_to_track()`
**Digunakan oleh:** `adapters/ytdlp/__init__`
**Menggunakan:** `core/state`, `adapters/ytdlp/common`


---


## engine/

**File:** `engine/command_router.py`
**Fungsi:** Register all CMD_* CommandBus handlers, routing each command to the appropriate method on PlaybackController or VolumeService.
**Class:** `CommandRouter`
**Function utama:** `_route()`, `_route_volume()`
**Digunakan oleh:** `main`
**Menggunakan:** `core/command_bus`


---

**File:** `engine/download_manager.py`
**Fungsi:** Handle the CMD_DOWNLOAD command by downloading the current or specified track via yt-dlp and moving it to the downloads/ folder.
**Class:** `DownloadManager`
**Function utama:** `_update_progress()`
**Digunakan oleh:** `main`
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/state`, `core/ports`, `core/task_utils`


---

**File:** `engine/mpv_controller.py`
**Fungsi:** Auto-generated purpose.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `main`
**Menggunakan:** `adapters/mpv`


---

**File:** `engine/playback/controller.py`
**Fungsi:** Orchestrate all playback logic: track loading, queue/radio advancement, pause/seek, and mode switching via CommandBus commands.
**Class:** `PlaybackController`
**Function utama:** —
**Digunakan oleh:** `engine/playback/__init__`, `server/app`
**Menggunakan:** `core/event_bus`, `core/events`, `core/state`, `core/ports`, `engine/queue_manager`, `engine/radio_engine`, _4 lainnya_


---

**File:** `engine/playback/mode_ops.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `ModeOps`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/state`, `core/ports`, `engine/radio`


---

**File:** `engine/playback/queue_ops.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `QueueOps`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/state`


---

**File:** `engine/playback/track_loader.py`
**Fungsi:** Resolve a track URI and trigger background side-effects (sponsorblock, lyrics fetch, play-count increment) before playback begins.
**Class:** `TrackLoader`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/state`, `core/ports`, `core/task_utils`


---

**File:** `engine/queue_manager.py`
**Fungsi:** Advance playback to the next track in the user queue when called by PlaybackController at track end.
**Class:** `QueueMode`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/state`


---

**File:** `engine/radio/artist_selector.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `ArtistSelector`
**Function utama:** `reset_rotation()`, `build_exclusion_set()`
**Digunakan oleh:** `engine/radio/engine`
**Menggunakan:** `core/state`, `engine/radio/common`, `engine/radio/track_interleaver`, `engine/radio/track_filter`


---

**File:** `engine/radio/common.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `track_task()`
**Digunakan oleh:** `engine/radio/artist_selector`, `engine/radio/engine`, `engine/radio/prefetcher`
**Menggunakan:** `core/task_utils`


---

**File:** `engine/radio/engine.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `RadioMode`
**Function utama:** `check_prefetch()`
**Digunakan oleh:** `engine/radio/__init__`
**Menggunakan:** `core/events`, `core/state`, `core/ports`, `engine/radio/common`, `engine/radio/artist_selector`, `engine/radio/prefetcher`


---

**File:** `engine/radio/prefetcher.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `RadioPrefetcher`
**Function utama:** `cancel_tasks()`, `clear_standby()`, `trigger_build_standby()`, `check_prefetch()`
**Digunakan oleh:** `engine/radio/engine`
**Menggunakan:** `core/state`, `engine/radio/common`


---

**File:** `engine/radio/track_filter.py`
**Fungsi:** Filter candidate tracks for the radio queue to prevent duplicates, skip recently played tracks, and limit artist dominance.
**Class:** `TrackFilter`
**Function utama:** `filter_tracks()`
**Digunakan oleh:** `engine/radio/artist_selector`
**Menggunakan:** `core/state`


---

**File:** `engine/radio/track_interleaver.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `interleave_by_artist()`
**Digunakan oleh:** `engine/radio/artist_selector`
**Menggunakan:** —


---

**File:** `engine/radio_engine.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `engine/radio`


---

**File:** `engine/volume_service.py`
**Fungsi:** Handle volume-related commands and apply the correct volume to mpv based on the active audio output mode.
**Class:** `VolumeService`
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/ports`, `core/state`


---

**File:** `engine/ytdlp_client.py`
**Fungsi:** Auto-generated purpose.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `main`
**Menggunakan:** `adapters/ytdlp`


---


## persistence/

**File:** `persistence/__init__.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `Database`
**Function utama:** `conn()`
**Digunakan oleh:** —
**Menggunakan:** `persistence/db`, `persistence/track_repo`, `persistence/session_repo`, `persistence/artist_repo`, `persistence/genre_repo`, `persistence/library_repo`


---

**File:** `persistence/artist_repo.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `ArtistRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---

**File:** `persistence/db.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `DatabaseConnection`
**Function utama:** `conn()`
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `config`


---

**File:** `persistence/genre_repo.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `GenreRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---

**File:** `persistence/library_repo.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `LibraryRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---

**File:** `persistence/session_repo.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `SessionRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** —


---

**File:** `persistence/track_repo.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `TrackRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---


## cache/

**File:** `cache/db.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `cache/resolver`, `main`, `scratch/check_db`
**Menggunakan:** `persistence`


---

**File:** `cache/resolver.py`
**Fungsi:** Resolve the playback URI for a track using a priority-based cache strategy: local file > cached stream URL > fresh yt-dlp extraction.
**Class:** `CacheResolver`
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `cache/db`, `config`, `core/state`, `core/ports`


---


## server/

**File:** `server/app.py`
**Fungsi:** Create and configure the aiohttp web application with all routes, services, and EventBus listeners wired together.
**Class:** —
**Function utama:** `create_app()`, `run_server()`
**Digunakan oleh:** —
**Menggunakan:** `core/events`, `core/task_utils`, `server/serializers`, `server/handlers/http`, `server/handlers/websocket`, `config`, _2 lainnya_


---

**File:** `server/connection_manager.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `ConnectionManager`
**Function utama:** `disconnect()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/observability`


---

**File:** `server/handlers/auth.py`
**Fungsi:** Handle WebSocket authentication, session token verification, and per-IP login rate limiting.
**Class:** —
**Function utama:** `handle_auth()`, `require_auth()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `config`, `core/security`


---

**File:** `server/handlers/event_listeners.py`
**Fungsi:** Subscribe to domain events from the EventBus and forward them as WebSocket broadcasts via BroadcastService.
**Class:** —
**Function utama:** `setup_event_listeners()`
**Digunakan oleh:** —
**Menggunakan:** `core/events`, `core/task_utils`, `server/services/stream_prefetch`, `server/services/broadcast_service`


---

**File:** `server/handlers/http.py`
**Fungsi:** Serve the SPA index, audio stream proxy, health check, and Prometheus metrics endpoints over HTTP.
**Class:** —
**Function utama:** `serve_index()`, `health_check()`, `serve_stream()`, `serve_metrics()`
**Digunakan oleh:** `server/app`
**Menggunakan:** `config`, `core/observability`


---

**File:** `server/handlers/websocket.py`
**Fungsi:** Handle WebSocket connections, authenticate clients, and dispatch incoming commands to the CommandBus after rate-limit enforcement.
**Class:** —
**Function utama:** `ws_handler()`, `handle_ws_message()`
**Digunakan oleh:** `server/app`, `server/services/broadcast_service`
**Menggunakan:** `core/observability`, `core/command_bus`, `core/state`, `server/serializers`, `server/middleware`, `server/handlers/auth`, _6 lainnya_


---

**File:** `server/handlers/ws_discovery.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `handle_discovery_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `services/discover_service`, `server/serializers`


---

**File:** `server/handlers/ws_download.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `handle_download_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/command_bus`, `server/serializers`, `services/discover_service`


---

**File:** `server/handlers/ws_playback.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `handle_playback_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/command_bus`, `core/state`, `server/serializers`


---

**File:** `server/handlers/ws_queue.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `handle_queue_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/command_bus`, `core/state`, `server/serializers`


---

**File:** `server/middleware.py`
**Fungsi:** Enforce per-IP command rate limiting for WebSocket clients.
**Class:** —
**Function utama:** `check_rate_limit_sync()`, `check_rate_limit()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/observability`


---

**File:** `server/serializers.py`
**Fungsi:** Convert between AppState/TrackInfo domain objects and JSON-serializable dicts for WebSocket message payloads.
**Class:** —
**Function utama:** `track_to_dict()`, `state_to_dict()`, `dict_to_track()`
**Digunakan oleh:** `server/app`, `server/handlers/websocket`, `server/handlers/ws_discovery`, `server/handlers/ws_download`, `server/handlers/ws_playback`, _2 lainnya_
**Menggunakan:** `core/state`


---

**File:** `server/services/broadcast_service.py`
**Fungsi:** Provide typed broadcast helpers that wrap ConnectionManager to push specific message types to all connected WebSocket clients.
**Class:** `BroadcastService`
**Function utama:** —
**Digunakan oleh:** `server/handlers/event_listeners`
**Menggunakan:** `server/serializers`, `server/handlers/websocket`, `core/state`


---

**File:** `server/services/stream_prefetch.py`
**Fungsi:** Pre-fetch and cache the stream URL for the next track in the background to reduce playback latency at track transitions.
**Class:** `StreamPrefetchService`
**Function utama:** —
**Digunakan oleh:** `server/handlers/event_listeners`
**Menggunakan:** `config`, `core/ports`


---


## services/

**File:** `services/discover_service.py`
**Fungsi:** Query the SQLite database to provide discover-page data: recently played tracks, favorites, cached tracks, and featured artists/genres.
**Class:** `DiscoverService`
**Function utama:** —
**Digunakan oleh:** `server/handlers/websocket`, `server/handlers/ws_discovery`, `server/handlers/ws_download`
**Menggunakan:** `core/state`, `core/ports`


---


## plugins/

**File:** `plugins/lyrics.py`
**Fungsi:** Expose lyrics fetching, parsing, and syncing functionality.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `main`
**Menggunakan:** `plugins/lyrics_fetcher`, `plugins/lyrics_parser`, `plugins/lyrics_sync`


---

**File:** `plugins/lyrics_fetcher.py`
**Fungsi:** Fetch synchronized lyrics from lrclib.net and syncedlyrics, then update the active lyric index on each playback progress event.
**Class:** `LyricsFetcher`
**Function utama:** `cleanup()`
**Digunakan oleh:** `plugins/lyrics`
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`


---

**File:** `plugins/lyrics_parser.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `LyricsParser`
**Function utama:** `parse_lrc()`
**Digunakan oleh:** `plugins/lyrics`
**Menggunakan:** —


---

**File:** `plugins/lyrics_sync.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `LyricsSync`
**Function utama:** `cleanup()`
**Digunakan oleh:** `plugins/lyrics`
**Menggunakan:** `core/events`


---

**File:** `plugins/notifications.py`
**Fungsi:** Mirror current playback state to an Android MediaStyle notification via termux-notification and relay button presses back via CommandBus.
**Class:** `TermuxNowPlaying`
**Function utama:** `_blocking_read_loop()`
**Digunakan oleh:** `main`
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/state`, `config`


---

**File:** `plugins/sponsorblock.py`
**Fungsi:** Fetch SponsorBlock skip segments for the current video and auto-seek past them during playback.
**Class:** `SponsorBlockHandler`
**Function utama:** `cleanup()`
**Digunakan oleh:** `main`
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`, `core/ports`, `core/task_utils`


---


## launcher/

**File:** `launcher/__main__.py`
**Fungsi:** Entry point for the LunaWave launcher when executed as a package.
**Class:** —
**Function utama:** `main()`
**Digunakan oleh:** `start`
**Menggunakan:** —


---

**File:** `launcher/gui.py`
**Fungsi:** Auto-generated purpose.
**Class:** —
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `launcher/gui/app`


---

**File:** `launcher/gui/app.py`
**Fungsi:** Provide the Tkinter-based ServerManager GUI for starting, stopping, and monitoring the LunaWave backend server.
**Class:** `ServerManager(Tk)`
**Function utama:** `server_port()`, `destroy()`
**Digunakan oleh:** `launcher/gui`
**Menggunakan:** `launcher`


---

**File:** `launcher/gui/auth_panel.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `handle_first_run()`, `on_reset_password()`, `show_new_password_dialog()`
**Digunakan oleh:** `launcher/gui/ui_builder`
**Menggunakan:** —


---

**File:** `launcher/gui/controller.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `ServerController`
**Function utama:** `on_start()`, `wait_for_server_ready()`, `on_stop()`, `wait_stop()`, `on_restart()`, `on_open()`
**Digunakan oleh:** —
**Menggunakan:** `launcher`


---

**File:** `launcher/gui/dep_checker.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `DependencyChecker`
**Function utama:** `check_dependencies()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `launcher/gui/popups.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `show_server_ready_popup()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `launcher/gui/ui_builder.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `UIBuilder`
**Function utama:** `build_ui()`
**Digunakan oleh:** —
**Menggunakan:** `launcher/gui/auth_panel`


---

**File:** `launcher/network.py`
**Fungsi:** Provide cross-platform utilities to detect TCP port availability and identify the PID currently occupying a port.
**Class:** —
**Function utama:** `check_port_in_use()`, `get_pid_occupying_port()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `launcher/process.py`
**Fungsi:** Manage OS-level lifecycle for the LunaWave server and mpv processes from the desktop launcher.
**Class:** `ServerProcess`
**Function utama:** `kill_process_tree()`, `kill_mpv()`, `start()`, `is_running()`, `stop()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `launcher/updater.py`
**Fungsi:** Stub module reserved for future OTA update checking and release info retrieval in the LunaWave launcher.
**Class:** —
**Function utama:** `check_for_updates()`, `get_release_info()`
**Digunakan oleh:** —
**Menggunakan:** —


---


## scratch/

**File:** `scratch/check_db.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `main()`
**Digunakan oleh:** —
**Menggunakan:** `cache/db`, `core/state`


---

**File:** `scratch/fix_docstrings.py`
**Fungsi:** Auto-generated module docstring.
**Class:** —
**Function utama:** `inject_docstring()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---


## ⚠️ File Besar (>200 baris)


| File | Baris | Catatan |
|---|---|---|

| `engine/playback/controller.py` | 346 | Perhatikan |

| `launcher/gui/ui_builder.py` | 266 | Perhatikan |

| `main.py` | 266 | Perhatikan |

| `launcher/gui/app.py` | 255 | Perhatikan |


## 📋 Checklist Dokumentasi Docstring

**81/81** file `.py` sudah punya docstring modul terstruktur (`Purpose:` / `Subscribes to:` / `Publishes:`). Berikut yang belum:


_(semua file sudah terdokumentasi 🎉)_

<!-- END:GENERATED -->
