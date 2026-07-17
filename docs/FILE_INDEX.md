---
title: LunaWave File Index
last_verified: 2026-07-17
generated: true
note: Isi file ini di-generate otomatis oleh automation/generate_file_index.py — JANGAN edit manual.
---

# FILE_INDEX.md — LunaWave File Inventory

> ⚙️ File ini di-generate otomatis oleh `automation/generate_file_index.py`.
> **Jangan edit manual** — perubahan akan ditimpa saat script dijalankan berikutnya.
> Jalankan `python automation/generate_file_index.py` setelah ada file/class/fungsi yang berubah.
>
> Format per file: File | Fungsi | Class | Function utama | Digunakan oleh | Menggunakan

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-17 oleh `automation/generate_file_index.py`
> **Jangan edit blok ini secara manual** — perubahan akan ditimpa saat script dijalankan ulang.


## Root

**File:** `config.py`
**Fungsi:** Load and expose all environment-based runtime configuration constants for LunaWave, including paths, ports, and the admin password.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/connection`, `adapters/ytdlp/downloader`, `adapters/ytdlp/resolver`, `cache/resolver`, `core/log_config`, _11 lainnya_
**Menggunakan:** —


---

**File:** `config_security.py`
**Fungsi:** Handles security configurations, including admin password generation and hashing.
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
**Menggunakan:** `cache/db`, `config`, `core/event_bus`, `core/log_config`, `core/state`, `core/task_utils`, _7 lainnya_


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
**Function utama:** `register()`, `unregister()`, `reset()`
**Digunakan oleh:** `engine/command_router`, `engine/download_manager`, `engine/sleep_timer`, `plugins/notifications`, `server/handlers/ws_download`, _2 lainnya_
**Menggunakan:** `core/commands`, `core/observability`


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
**Menggunakan:** `core/events`, `core/observability`, `core/task_utils`


---

**File:** `core/events.py`
**Fungsi:** Define all typed DomainEvent dataclasses for the LunaWave event bus.
**Class:** `DomainEvent`, `TrackStartedEvent(DomainEvent)`, `TrackEndedEvent(DomainEvent)`, `TrackProgressEvent(DomainEvent)`, `TrackDurationEvent(DomainEvent)`, `QueueUpdatedEvent(DomainEvent)`, `LyricsUpdatedEvent(DomainEvent)`, `DownloadCompleteEvent(DomainEvent)`, `DownloadProgressEvent(DomainEvent)`, `LogMessageEvent(DomainEvent)`, `TrackPauseChangedEvent(DomainEvent)`, `MpvReconnectedEvent(DomainEvent)`
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/observer`, `core/event_bus`, `engine/download_manager`, `engine/playback/controller`, `engine/playback/mode_ops`, _11 lainnya_
**Menggunakan:** `core/state`


---

**File:** `core/exceptions.py`
**Fungsi:** Define the custom exception hierarchy for LunaWave error conditions.
**Class:** `YtPlayerError(Exception)`, `MpvConnectionError(YtPlayerError)`, `TrackResolutionError(YtPlayerError)`, `DownloadError(YtPlayerError)`
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/connection`
**Menggunakan:** —


---

**File:** `core/latency_window.py`
**Fungsi:** Rolling window durasi (detik) untuk menghitung percentile ke-n dari N sample terakhir. Dipakai untuk threshold adaptif yang bereaksi ke kondisi jaringan aktual, bukan angka statis.
**Class:** `LatencyWindow`
**Function utama:** `record()`, `percentile()`, `sample_count()`
**Digunakan oleh:** `cache/resolver`
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
**Digunakan oleh:** `cache/resolver`, `core/command_bus`, `core/event_bus`, `server/connection_manager`, `server/handlers/http`
**Menggunakan:** —


---

**File:** `core/ports.py`
**Fungsi:** Declare Protocol interfaces (ports) for LunaWave's hexagonal architecture.
**Class:** `AudioPlayerPort(Protocol)`, `MediaExtractorPort(Protocol)`, `StreamResolverPort(Protocol)`, `TrackRepositoryPort(Protocol)`, `SessionRepositoryPort(Protocol)`, `ArtistRepositoryPort(Protocol)`, `DatabasePort(TrackRepositoryPort, SessionRepositoryPort, ArtistRepositoryPort, Protocol)`, `LyricsProvider(Protocol)`, `SponsorBlockProvider(Protocol)`
**Function utama:** `is_connected()`, `cancel_download()`, `db()`, `latency_window()`
**Digunakan oleh:** `cache/resolver`, `engine/download_manager`, `engine/loudness/service`, `engine/playback/controller`, `engine/playback/mode_ops`, _7 lainnya_
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
**Class:** `PlayerStatus(Enum)`, `AudioOutput(StrEnum)`, `PlaybackMode(Enum)`, `TrackInfo`, `AppState`
**Function utama:** —
**Digunakan oleh:** `adapters/ytdlp/searcher`, `cache/resolver`, `core/events`, `core/ports`, `engine/download_manager`, _26 lainnya_
**Menggunakan:** —


---

**File:** `core/task_utils.py`
**Fungsi:** Wrap asyncio.create_task with centralized exception handling to prevent silent background-task crashes.
**Class:** —
**Function utama:** `safe_create_task()`
**Digunakan oleh:** `adapters/mpv/observer`, `core/event_bus`, `engine/download_manager`, `engine/playback/controller`, `engine/playback/track_ended_ops`, _4 lainnya_
**Menggunakan:** —


---


## adapters/

**File:** `adapters/mpv/__init__.py`
**Fungsi:** High-level MPV controller combining connection, IPC, and event observation.
**Class:** `MpvController`
**Function utama:** `is_connected()`
**Digunakan oleh:** —
**Menggunakan:** `adapters/mpv/connection`, `adapters/mpv/ipc`, `adapters/mpv/observer`


---

**File:** `adapters/mpv/connection.py`
**Fungsi:** Manages the raw socket connection to the MPV media player.
**Class:** `MpvConnection`
**Function utama:** `reader()`, `writer()`
**Digunakan oleh:** `adapters/mpv/__init__`
**Menggunakan:** `config`, `core/exceptions`


---

**File:** `adapters/mpv/ipc.py`
**Fungsi:** Handles JSON IPC communication and command execution with MPV.
**Class:** `MpvIPC`
**Function utama:** `pop_pending()`, `cancel_all_pending()`
**Digunakan oleh:** `adapters/mpv/__init__`
**Menggunakan:** —


---

**File:** `adapters/mpv/observer.py`
**Fungsi:** Observes and dispatches asynchronous events emitted by the MPV player.
**Class:** `MpvObserver`
**Function utama:** —
**Digunakan oleh:** `adapters/mpv/__init__`
**Menggunakan:** `core/event_bus`, `core/events`, `core/task_utils`


---

**File:** `adapters/ytdlp/__init__.py`
**Fungsi:** Unified client for interacting with yt-dlp for search, extraction, and downloading.
**Class:** `YtDlpClient`
**Function utama:** `cancel_download()`, `close()`
**Digunakan oleh:** —
**Menggunakan:** `adapters/ytdlp/downloader`, `adapters/ytdlp/resolver`, `adapters/ytdlp/searcher`


---

**File:** `adapters/ytdlp/common.py`
**Fungsi:** Shared utilities and constants for yt-dlp integration.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `adapters/ytdlp/downloader`, `adapters/ytdlp/resolver`, `adapters/ytdlp/searcher`
**Menggunakan:** —


---

**File:** `adapters/ytdlp/downloader.py`
**Fungsi:** Handles downloading audio streams using yt-dlp.
**Class:** `YtDlpDownloader`
**Function utama:** `cancel_download()`
**Digunakan oleh:** `adapters/ytdlp/__init__`
**Menggunakan:** `adapters/ytdlp/common`, `config`


---

**File:** `adapters/ytdlp/resolver.py`
**Fungsi:** Resolves direct stream URLs for tracks using yt-dlp.
**Class:** `YtDlpResolver`
**Function utama:** `_extract_sync()`, `_pick_audio_url()`
**Digunakan oleh:** `adapters/ytdlp/__init__`
**Menggunakan:** `adapters/ytdlp/common`, `config`


---

**File:** `adapters/ytdlp/searcher.py`
**Fungsi:** Performs metadata extraction and search operations via yt-dlp.
**Class:** `YtDlpSearcher`
**Function utama:** `_extract_sync()`, `_to_track()`
**Digunakan oleh:** `adapters/ytdlp/__init__`
**Menggunakan:** `adapters/ytdlp/common`, `core/state`


---


## engine/

**File:** `engine/command_router.py`
**Fungsi:** Register all CMD_* CommandBus handlers, routing each command to the appropriate method on PlaybackController or VolumeService.
**Class:** `CommandRouter`
**Function utama:** `_route_sleep()`, `_route()`, `_route_volume()`
**Digunakan oleh:** `main`
**Menggunakan:** `core/command_bus`


---

**File:** `engine/download_manager.py`
**Fungsi:** Handle the CMD_DOWNLOAD command by downloading the current or specified track via yt-dlp and moving it to the downloads/ folder.
**Class:** `DownloadManager`
**Function utama:** `_update_progress()`
**Digunakan oleh:** `main`
**Menggunakan:** `core/command_bus`, `core/event_bus`, `core/events`, `core/ports`, `core/state`, `core/task_utils`


---

**File:** `engine/loudness/analyzer.py`
**Fungsi:** Ukur integrated loudness (LUFS) sebuah track via satu-pass ffmpeg `loudnorm` filter mode measure-only (tidak re-encode, tidak menyimpan file baru).
**Class:** `LoudnessMeasurement(NamedTuple)`, `LoudnessAnalyzer`
**Function utama:** `measure_sync()`
**Digunakan oleh:** `engine/loudness/service`
**Menggunakan:** `config`


---

**File:** `engine/loudness/gain_calculator.py`
**Fungsi:** Hitung gain (dB) yang perlu diterapkan ke sebuah track supaya loudness-nya mendekati target, berdasarkan hasil pengukuran integrated loudness (LUFS) dan true peak (dBTP).
**Class:** —
**Function utama:** `compute_gain_db()`, `build_af_filter()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `engine/loudness/service.py`
**Fungsi:** Orkestrasi analisis loudness: cek apakah track sudah pernah diukur, kalau belum -> ukur via LoudnessAnalyzer lalu simpan ke DB.
**Class:** `LoudnessService`
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `core/ports`, `engine/loudness/analyzer`


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
**Function utama:** `dispose()`
**Digunakan oleh:** `engine/playback/__init__`, `server/app`
**Menggunakan:** `core/event_bus`, `core/events`, `core/ports`, `core/state`, `core/task_utils`, `engine/playback/mode_ops`, _5 lainnya_


---

**File:** `engine/playback/crossfade.py`
**Fungsi:** Crossfade helpers untuk transisi halus antar track via MPV volume ramping.
**Class:** —
**Function utama:** `apply_crossfade_in()`, `check_crossfade_out()`
**Digunakan oleh:** —
**Menggunakan:** `core/state`


---

**File:** `engine/playback/mode_ops.py`
**Fungsi:** Handles playback mode switches, such as toggling radio mode or SponsorBlock.
**Class:** `ModeOps`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/ports`, `core/state`, `engine/radio`


---

**File:** `engine/playback/queue_ops.py`
**Fungsi:** Manages queue operations including adding, removing, and reordering tracks.
**Class:** `QueueOps`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/state`


---

**File:** `engine/playback/track_ended_ops.py`
**Fungsi:** Menangani reaksi terhadap TrackEndedEvent (eof/stop/error) dan polling durasi track yang belum diketahui. Diekstrak dari controller.py agar file controller tetap ramping (di bawah LARGE_FILE_THRESHOLD).
**Class:** `TrackEndedOps`
**Function utama:** `poll_duration()`
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/state`, `core/task_utils`


---

**File:** `engine/playback/track_loader.py`
**Fungsi:** Resolve a track URI and trigger background side-effects (sponsorblock, lyrics fetch, play-count increment) before playback begins.
**Class:** `LoadedTrack`, `TrackLoader`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/ports`, `core/state`, `core/task_utils`


---

**File:** `engine/queue_manager.py`
**Fungsi:** Advance playback to the next track in the user queue when called by PlaybackController at track end.
**Class:** `QueueMode`
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `core/events`, `core/state`


---

**File:** `engine/radio/artist_bandit.py`
**Fungsi:** Thompson Sampling (Beta-Bernoulli) untuk memilih artis radio berdasarkan histori selesai/skip, dengan eksplorasi otomatis untuk artis yang datanya masih sedikit.
**Class:** `ArtistStat`
**Function utama:** `sample_artists()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `engine/radio/artist_selector.py`
**Fungsi:** Selects and rotates artists intelligently to maintain variety in radio mode.
**Class:** `ArtistSelector`
**Function utama:** `reset_rotation()`, `build_exclusion_set()`
**Digunakan oleh:** `engine/radio/engine`
**Menggunakan:** `core/state`, `engine/radio/common`, `engine/radio/track_filter`, `engine/radio/track_interleaver`


---

**File:** `engine/radio/common.py`
**Fungsi:** Common utilities and shared logic for the radio engine components.
**Class:** —
**Function utama:** `track_task()`
**Digunakan oleh:** `engine/radio/artist_selector`, `engine/radio/engine`, `engine/radio/prefetcher`
**Menggunakan:** `core/task_utils`


---

**File:** `engine/radio/engine.py`
**Fungsi:** Manages the state and playback progression for the radio mode feature.
**Class:** `RadioMode`
**Function utama:** `check_prefetch()`
**Digunakan oleh:** `engine/radio/__init__`
**Menggunakan:** `core/events`, `core/ports`, `core/state`, `engine/radio/artist_selector`, `engine/radio/common`, `engine/radio/prefetcher`


---

**File:** `engine/radio/prefetcher.py`
**Fungsi:** Pre-fetches tracks asynchronously to ensure seamless transitions in radio mode.
**Class:** `RadioPrefetcher`
**Function utama:** `cancel_tasks()`, `trigger_build_standby()`, `check_prefetch()`
**Digunakan oleh:** `engine/radio/engine`
**Menggunakan:** `config`, `core/state`, `engine/radio/common`


---

**File:** `engine/radio/track_filter.py`
**Fungsi:** Filter candidate tracks for the radio queue to prevent duplicates, skip recently played tracks, and limit artist dominance.
**Class:** `TrackFilter`
**Function utama:** `filter_tracks()`
**Digunakan oleh:** `engine/radio/artist_selector`
**Menggunakan:** `core/state`, `engine/radio/track_interleaver`


---

**File:** `engine/radio/track_interleaver.py`
**Fungsi:** Interleaves tracks from different artists to create a balanced radio queue.
**Class:** —
**Function utama:** `normalize_title()`, `interleave_by_artist()`
**Digunakan oleh:** `engine/radio/artist_selector`, `engine/radio/track_filter`
**Menggunakan:** —


---

**File:** `engine/radio_engine.py`
**Fungsi:** Core logic for the radio mode engine, orchestrating playback when radio is active.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `engine/playback/controller`
**Menggunakan:** `engine/radio`


---

**File:** `engine/sleep_timer.py`
**Fungsi:** Handles setting, tracking, and executing a sleep timer to stop playback after a specified duration.
**Class:** `SleepTimer`
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `core/command_bus`, `core/events`


---

**File:** `engine/volume_service.py`
**Fungsi:** Handle volume-related commands and apply the correct volume to mpv based on the active audio output mode.
**Class:** `VolumeService`
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `core/event_bus`, `core/events`, `core/ports`, `core/state`


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
**Fungsi:** Database facade that aggregates all repositories into a unified data access layer.
**Class:** `Database`
**Function utama:** `conn()`
**Digunakan oleh:** —
**Menggunakan:** `persistence/artist_repo`, `persistence/db`, `persistence/discover_repo`, `persistence/genre_repo`, `persistence/library_repo`, `persistence/session_repo`, _1 lainnya_


---

**File:** `persistence/artist_repo.py`
**Fungsi:** Repository for tracking artist statistics and fetching artist-specific tracks.
**Class:** `ArtistRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---

**File:** `persistence/db.py`
**Fungsi:** Manages the SQLite database connection lifecycle and initialization.
**Class:** `DatabaseConnection`
**Function utama:** `conn()`
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `config`


---

**File:** `persistence/discover_enrich.py`
**Fungsi:** Shared batch-enrichment helper for Discover personalization queries. Given a list of artist rows, attach a cover thumbnail and genre tag list to each one using two queries total for the whole batch (never per-artist), so `discover_repo.py` doesn't run into N+1 query fan-out when enriching a page of results.
**Class:** —
**Function utama:** `enrich_artists()`
**Digunakan oleh:** `persistence/discover_repo`
**Menggunakan:** —


---

**File:** `persistence/discover_repo.py`
**Fungsi:** Repository for Discover-tab personalization queries: bandit-ranked "Untuk Kamu" artists, "Belum Pernah Kamu Dengar" (unheard) artists, genre taste spectrum, genre affinity, and artist detail lookup.
**Class:** `DiscoverRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `persistence/discover_enrich`


---

**File:** `persistence/genre_repo.py`
**Fungsi:** Repository for fetching genre information and tracking genre popularity.
**Class:** `GenreRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---

**File:** `persistence/library_repo.py`
**Fungsi:** Repository for global library operations such as fetching random songs.
**Class:** `LibraryRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---

**File:** `persistence/session_repo.py`
**Fungsi:** Manages authentication session tokens, verifying and cleaning up expired sessions.
**Class:** `SessionRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** —


---

**File:** `persistence/track_repo.py`
**Fungsi:** Repository for track metadata, play counts, favorites, and local file paths.
**Class:** `TrackRepository`
**Function utama:** —
**Digunakan oleh:** `persistence/__init__`
**Menggunakan:** `core/state`


---


## cache/

**File:** `cache/db.py`
**Fungsi:** Provides database caching mechanisms for quick access to frequently used data.
**Class:** —
**Function utama:** —
**Digunakan oleh:** `main`, `scratch/check_db`
**Menggunakan:** `persistence`


---

**File:** `cache/resolver.py`
**Fungsi:** Resolve the playback URI for a track using a priority-based cache strategy: local file > cached stream URL > fresh yt-dlp extraction.
**Class:** `CacheResolver`
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** `config`, `core/latency_window`, `core/observability`, `core/ports`, `core/state`


---


## server/

**File:** `server/app.py`
**Fungsi:** Create and configure the aiohttp web application with all routes, services, and EventBus listeners wired together.
**Class:** —
**Function utama:** `create_app()`, `run_server()`
**Digunakan oleh:** —
**Menggunakan:** `core/ports`, `engine/playback/controller`, `server/connection_manager`, `server/handlers/http`, `server/handlers/websocket`


---

**File:** `server/connection_manager.py`
**Fungsi:** Manages active WebSocket connections and broadcasts events to connected clients.
**Class:** `ConnectionManager`
**Function utama:** `disconnect()`
**Digunakan oleh:** `server/app`, `server/services/broadcast_service`
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
**Menggunakan:** `core/events`, `core/task_utils`, `server/services/broadcast_service`, `server/services/stream_prefetch`


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
**Digunakan oleh:** `server/app`
**Menggunakan:** `server/handlers/auth`, `server/handlers/ws_discovery`, `server/handlers/ws_download`, `server/handlers/ws_playback`, `server/handlers/ws_queue`, `server/middleware`, _1 lainnya_


---

**File:** `server/handlers/ws_cache.py`
**Fungsi:** WebSocket handler for managing cache queries and clearing.
**Class:** —
**Function utama:** `handle_cache_command()`
**Digunakan oleh:** —
**Menggunakan:** `config`


---

**File:** `server/handlers/ws_discovery.py`
**Fungsi:** WebSocket handler for processing discovery and search commands.
**Class:** —
**Function utama:** `handle_discovery_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `server/serializers`, `services/discover_service`


---

**File:** `server/handlers/ws_download.py`
**Fungsi:** WebSocket handler for managing track download requests and status.
**Class:** —
**Function utama:** `handle_download_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/command_bus`, `server/serializers`, `services/discover_service`


---

**File:** `server/handlers/ws_playback.py`
**Fungsi:** WebSocket handler for processing playback control commands.
**Class:** —
**Function utama:** `handle_playback_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/command_bus`, `core/state`, `server/serializers`


---

**File:** `server/handlers/ws_queue.py`
**Fungsi:** WebSocket handler for manipulating the current playback queue.
**Class:** —
**Function utama:** `handle_queue_command()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** `core/command_bus`, `core/state`, `server/serializers`


---

**File:** `server/middleware.py`
**Fungsi:** Enforce per-IP command rate limiting for WebSocket clients.
**Class:** —
**Function utama:** `check_rate_limit()`
**Digunakan oleh:** `server/handlers/websocket`
**Menggunakan:** —


---

**File:** `server/serializers.py`
**Fungsi:** Convert between AppState/TrackInfo domain objects and JSON-serializable dicts for WebSocket message payloads.
**Class:** —
**Function utama:** `track_to_dict()`, `state_to_dict()`, `dict_to_track()`
**Digunakan oleh:** `server/handlers/websocket`, `server/handlers/ws_discovery`, `server/handlers/ws_download`, `server/handlers/ws_playback`, `server/handlers/ws_queue`, _1 lainnya_
**Menggunakan:** `core/state`


---

**File:** `server/services/broadcast_service.py`
**Fungsi:** Provide typed broadcast helpers that wrap ConnectionManager to push specific message types to all connected WebSocket clients.
**Class:** `BroadcastService`
**Function utama:** —
**Digunakan oleh:** `server/handlers/event_listeners`
**Menggunakan:** `core/state`, `server/connection_manager`, `server/serializers`


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
**Digunakan oleh:** `server/handlers/ws_discovery`, `server/handlers/ws_download`
**Menggunakan:** `core/ports`, `core/state`


---


## plugins/

**File:** `plugins/lyrics.py`
**Fungsi:** Expose lyrics fetching, parsing, and syncing functionality.
**Class:** —
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `plugins/lyrics_fetcher.py`
**Fungsi:** Fetch synchronized lyrics from lrclib.net and syncedlyrics, then update the active lyric index on each playback progress event.
**Class:** `LyricsFetcher`
**Function utama:** `cleanup()`
**Digunakan oleh:** `main`
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`


---

**File:** `plugins/lyrics_parser.py`
**Fungsi:** Parser for extracting timed lyrics from LRC-formatted text.
**Class:** `LyricsParser`
**Function utama:** `parse_lrc()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `plugins/lyrics_sync.py`
**Fungsi:** Synchronizes lyrics display with current track playback progress.
**Class:** `LyricsSync`
**Function utama:** `cleanup()`
**Digunakan oleh:** —
**Menggunakan:** `core/events`


---

**File:** `plugins/notifications.py`
**Fungsi:** Mirror current playback state to an Android MediaStyle notification via termux-notification and relay button presses back via CommandBus.
**Class:** `TermuxNowPlaying`
**Function utama:** `_blocking_read_loop()`
**Digunakan oleh:** `main`
**Menggunakan:** `config`, `core/command_bus`, `core/event_bus`, `core/events`, `core/state`


---

**File:** `plugins/sponsorblock.py`
**Fungsi:** Fetch SponsorBlock skip segments for the current video and auto-seek past them during playback.
**Class:** `SponsorBlockHandler`
**Function utama:** `cleanup()`
**Digunakan oleh:** `main`
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/ports`, `core/state`


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
**Menggunakan:** —


---

**File:** `launcher/gui/app.py`
**Fungsi:** Provide the Tkinter-based ServerManager GUI for starting, stopping, and monitoring the LunaWave backend server.
**Class:** `ServerManager(Tk)`
**Function utama:** `server_port()`, `destroy()`
**Digunakan oleh:** —
**Menggunakan:** `launcher`


---

**File:** `launcher/gui/auth_panel.py`
**Fungsi:** GUI component for user authentication, password reset, and first-run setup.
**Class:** —
**Function utama:** `handle_first_run()`, `on_reset_password()`, `show_new_password_dialog()`
**Digunakan oleh:** `launcher/gui/ui_builder`
**Menggunakan:** —


---

**File:** `launcher/gui/controller.py`
**Fungsi:** Controls the underlying server lifecycle from within the launcher GUI.
**Class:** `ServerController`
**Function utama:** `on_start()`, `wait_for_server_ready()`, `on_stop()`, `wait_stop()`, `on_restart()`, `on_open()`
**Digunakan oleh:** —
**Menggunakan:** `launcher`


---

**File:** `launcher/gui/dep_checker.py`
**Fungsi:** Utility to verify required system dependencies before launching the application.
**Class:** `DependencyChecker`
**Function utama:** `check_dependencies()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `launcher/gui/popups.py`
**Fungsi:** Helper module for displaying generic popup dialogs in the GUI.
**Class:** —
**Function utama:** `show_server_ready_popup()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `launcher/gui/ui_builder.py`
**Fungsi:** Constructs the main user interface layout and elements for the launcher.
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


## data/

**File:** `data/export_to_sqlite.py`
**Fungsi:** Export artist, genre, and song data from a JSON file into a SQLite DB.
**Class:** —
**Function utama:** `create_tables()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---


## automation/

**File:** `automation/architecture_lint.py`
**Fungsi:** Validate inter-layer import boundaries against the architecture rules defined in docs/architecture/dependency_rules.md.
**Class:** —
**Function utama:** `path_to_layer()`, `module_to_layer()`, `check_file()`, `scan_project()`, `collect_results()`, `render_text()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/call_graph.py`
**Fungsi:** Cari caller & callee dari 1 nama fungsi, scan AST on-demand (bukan disimpan di repo_index — call-graph lengkap semua-fungsi terlalu besar).
**Class:** —
**Function utama:** `find_callers()`, `find_callees()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/context_pack.py`
**Fungsi:** Satu panggilan yang menggabungkan semua tool automation/ jadi 1 JSON — endpoint utama untuk AI agent supaya tidak perlu 5 panggilan terpisah.
**Class:** —
**Function utama:** `build_context_pack()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/doctor.py`
**Fungsi:** Orchestrate all registered health checkers and display a consolidated project health dashboard with aggregate scores.
**Class:** —
**Function utama:** `section()`, `run_checker_json()`, `run_all_checkers()`, `render_checker()`, `print_summary()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/event_graph.py`
**Fungsi:** Menganalisis dan memvalidasi event pub/sub. Memastikan tidak ada publisher tanpa subscriber (dead event) dan tidak ada subscriber tanpa publisher (ghost event).
**Class:** —
**Function utama:** `build_event_map()`, `check_events()`, `get_json_data()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/find_owner.py`
**Fungsi:** Display ownership, dependencies, and impact radius of a given module, class, or function name.
**Class:** —
**Function utama:** `collect_py_files()`, `extract_info()`, `find_all_classes_and_functions()`, `build_reverse_index()`, `read_status_for_file()`, `resolve_target()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/generate_file_index.py`
**Fungsi:** Generate and inject an auto-produced file index section into docs/FILE_INDEX.md based on AST analysis of all Python source files.
**Class:** —
**Function utama:** `extract_purpose()`, `extract_module_info()`, `collect_py_files()`, `build_reverse_index()`, `format_file_entry()`, `build_generated_block()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/generate_report.py`
**Fungsi:** Generate and inject project statistics into the <!-- BEGIN:GENERATED --> block of docs/REPORT.md.
**Class:** —
**Function utama:** `count_files_by_ext()`, `count_py_files()`, `count_folders()`, `count_classes_and_functions()`, `count_lines()`, `count_js_files()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/hotspot.py`
**Fungsi:** Ranking file paling berisiko: skor = churn (jumlah kemunculan di PATCHLOG.md) x sentralitas (reverse-dep 1-hop dari repo_index).
**Class:** —
**Function utama:** `compute_hotspots()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/impact.py`
**Fungsi:** Blast radius sebelum refactor/hapus: reverse-dep transitif (import graph) DIGABUNG reverse-dep via event bus (subscriber dari event yang dipublish file target) — sisi event wajib, bukan opsional (lihat rationale di atas).
**Class:** —
**Function utama:** `transitive_reverse_deps()`, `event_impacted()`, `compute_impact()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/patchlog.py`
**Fungsi:** Baca/tulis docs/PATCHLOG.md terstruktur. ID PATCH-YYYY-MM-DD-NNN, NNN = total entries berjalan (bukan reset per hari).
**Class:** —
**Function utama:** `parse_entries()`, `add_entry()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/run_all.py`
**Fungsi:** Run all documentation generators and the project health check in a single command.
**Class:** —
**Function utama:** `run()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/shared/arch_rules.py`
**Fungsi:** Auto-generated module docstring.
**Class:** `Violation`
**Function utama:** `to_dict()`, `is_known()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/shared/check_result.py`
**Fungsi:** Define the CheckResult dataclass and generic weighted-scoring helpers shared by all LunaWave health checker scripts.
**Class:** `CheckResult`
**Function utama:** `count()`, `percentage()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/shared/constants.py`
**Fungsi:** Konstanta bersama antar checker automation/, misalnya ambang batas "file besar" yang dipakai automation/verify_structure.py.
**Class:** —
**Function utama:** —
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/shared/generated_block.py`
**Fungsi:** Provide replace_marker_block() to update <!-- BEGIN/END:GENERATED --> sections in Markdown files.
**Class:** —
**Function utama:** `replace_marker_block()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/shared/repo_index.py`
**Fungsi:** Index AST satu kali untuk seluruh repo (classes, functions, imports, layer, event publish/subscribe, reverse-deps), dengan cache ber-invalidasi mtime.
**Class:** —
**Function utama:** `build_index()`, `load_index()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/shared/skip_dirs.py`
**Fungsi:** Define SKIP_DIRS and walk_py_files() used by all scanner scripts to exclude non-source directories from file system traversal.
**Class:** —
**Function utama:** `walk_py_files()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/test_locator.py`
**Fungsi:** Petakan source <-> test dua arah via konvensi path-mirroring tests/unit/<subpath>/test_<nama>.py <-> <subpath>/<nama>.py.
**Class:** —
**Function utama:** `find_test_for()`, `find_orphans()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_docs.py`
**Fungsi:** Orchestrate all documentation health checks and report results as a human-readable summary or a structured JSON payload.
**Class:** —
**Function utama:** `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_docs/checks_coverage.py`
**Fungsi:** Implement FILE_INDEX sync, REPORT validation, module docstring coverage, and overall documentation coverage checks for verify_docs.
**Class:** —
**Function utama:** `check_file_index()`, `check_report()`, `check_module_docstrings()`, `check_documentation_coverage()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_docs/checks_docs.py`
**Fungsi:** Implement documentation structure, PATCHLOG integrity, frontmatter validity, and generated-marker pair checks for verify_docs.
**Class:** —
**Function utama:** `check_docs_structure()`, `check_patchlog()`, `check_frontmatter()`, `check_generated_blocks()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_docs/checks_files.py`
**Fungsi:** Implement large-file and empty-package checks for verify_docs.
**Class:** —
**Function utama:** `check_large_files()`, `check_empty_packages()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_docs/helpers.py`
**Fungsi:** Provide shared constants, regex patterns, and I/O/filesystem utilities for all verify_docs sub-modules.
**Class:** —
**Function utama:** `read_text()`, `parse_frontmatter()`, `collect_py_files()`, `count_lines()`, `get_module_docstring()`, `fmt_items()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_docs/render.py`
**Fungsi:** Render verify_docs check results as a human-readable terminal summary or a structured JSON report matching the checker contract.
**Class:** —
**Function utama:** `render_summary()`, `render_json()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_security.py`
**Fungsi:** Verify that sensitive files are listed in .gitignore to prevent accidental credential or database commits.
**Class:** —
**Function utama:** `check_credential_ignore()`, `check_db_files_ignore()`, `render_summary()`, `render_json()`, `main()`
**Digunakan oleh:** —
**Menggunakan:** —


---

**File:** `automation/verify_structure.py`
**Fungsi:** Validate project structure health: oversized Python files and unimplemented stub items tracked in STATUS.md.
**Class:** —
**Function utama:** `check_big_files()`, `check_pending_items()`, `render_summary()`, `render_json()`, `main()`
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


## ⚠️ File Besar (>400 baris)


| File | Baris | Catatan |
|---|---|---|

| `engine/playback/controller.py` | 464 | Perlu dipecah |


## 📋 Checklist Dokumentasi Docstring

**119/119** file `.py` sudah punya docstring modul terstruktur (`Purpose:` / `Subscribes to:` / `Publishes:`). Berikut yang belum:


_(semua file sudah terdokumentasi 🎉)_

<!-- END:GENERATED -->
