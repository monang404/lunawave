---
last_verified: 2026-07-10
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
> **Auto-generated:** 2026-07-10 oleh `scripts/generate_file_index.py`  
> **Jangan edit blok ini secara manual** — perubahan akan ditimpa saat script dijalankan ulang.


## Root

**File:** `config.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** —  
**Digunakan oleh:** `cache/db`, `cache/resolver`, `core/log_config`, `engine/mpv_controller`, `engine/ytdlp_client`, _8 lainnya_  
**Menggunakan:** —


---

**File:** `main.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `main()`  
**Digunakan oleh:** —  
**Menggunakan:** `core/log_config`, `core/state`, `core/event_bus`, `engine/ytdlp_client`, `engine/mpv_controller`, `cache/db`, _7 lainnya_


---

**File:** `start.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** —  
**Digunakan oleh:** —  
**Menggunakan:** `launcher/__main__`


---


## core/

**File:** `core/command_bus.py`  
**Fungsi:** CommandBus untuk single-writer pattern (1-to-1). Berbeda dengan EventBus (pub/sub 1-to-many), CommandBus menjamin hanya ada SATU handler untuk setiap command.  
**Class:** `CommandBus`  
**Function utama:** `register()`, `unregister()`  
**Digunakan oleh:** `engine/command_router`, `engine/download_manager`, `engine/volume_service`, `plugins/notifications`, `server/handlers/websocket`  
**Menggunakan:** `core/observability`


---

**File:** `core/event_bus.py`  
**Fungsi:** EventBus untuk komunikasi antar modul secara decoupled dan asinkron.  
**Class:** `EventBus`  
**Function utama:** `subscribe()`, `purge_dead_refs()`, `unsubscribe()`  
**Digunakan oleh:** `engine/download_manager`, `engine/mpv_controller`, `engine/playback/controller`, `engine/volume_service`, `main`, _3 lainnya_  
**Menggunakan:** `core/task_utils`, `core/events`, `core/observability`


---

**File:** `core/events.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `DomainEvent`, `TrackStartedEvent(DomainEvent)`, `TrackEndedEvent(DomainEvent)`, `TrackProgressEvent(DomainEvent)`, `TrackDurationEvent(DomainEvent)`, `QueueUpdatedEvent(DomainEvent)`, `LyricsUpdatedEvent(DomainEvent)`, `DownloadCompleteEvent(DomainEvent)`, `DownloadProgressEvent(DomainEvent)`, `LogMessageEvent(DomainEvent)`, `TrackPauseChangedEvent(DomainEvent)`  
**Function utama:** —  
**Digunakan oleh:** `core/event_bus`, `engine/download_manager`, `engine/mpv_controller`, `engine/playback/controller`, `engine/queue_manager`, _7 lainnya_  
**Menggunakan:** `core/state`


---

**File:** `core/exceptions.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `YtPlayerError(Exception)`, `MpvConnectionError(YtPlayerError)`, `TrackResolutionError(YtPlayerError)`, `DownloadError(YtPlayerError)`  
**Function utama:** —  
**Digunakan oleh:** `engine/mpv_controller`  
**Menggunakan:** —


---

**File:** `core/log_config.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `simple_renderer()`, `setup_logging()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `config`


---

**File:** `core/observability.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `setup_tracing()`, `get_metrics_content()`  
**Digunakan oleh:** `core/command_bus`, `core/event_bus`, `server/handlers/http`, `server/handlers/websocket`, `server/middleware`  
**Menggunakan:** —


---

**File:** `core/ports.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `AudioPlayerPort(Protocol)`, `MediaExtractorPort(Protocol)`, `TrackRepositoryPort(Protocol)`, `SessionRepositoryPort(Protocol)`, `DatabasePort(TrackRepositoryPort, SessionRepositoryPort, Protocol)`, `LyricsProvider(Protocol)`, `SponsorBlockProvider(Protocol)`  
**Function utama:** `cancel_download()`  
**Digunakan oleh:** `cache/resolver`, `engine/download_manager`, `engine/playback/controller`, `engine/playback/track_loader`, `engine/radio_engine`, _4 lainnya_  
**Menggunakan:** `core/state`


---

**File:** `core/security.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `hash_password()`, `verify_password()`  
**Digunakan oleh:** `server/handlers/auth`  
**Menggunakan:** —


---

**File:** `core/state.py`  
**Fungsi:** Menyimpan state aplikasi LunaWave, termasuk status pemutar, mode pemutaran, lagu saat ini, antrean, riwayat, status download, lirik, dan tab aktif.  
**Class:** `PlayerStatus(Enum)`, `AudioOutput(str, Enum)`, `PlaybackMode(Enum)`, `TrackInfo`, `AppState`  
**Function utama:** —  
**Digunakan oleh:** `cache/db`, `cache/resolver`, `core/events`, `core/ports`, `engine/download_manager`, _16 lainnya_  
**Menggunakan:** —


---

**File:** `core/task_utils.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `safe_create_task()`  
**Digunakan oleh:** `core/event_bus`, `engine/download_manager`, `engine/mpv_controller`, `engine/playback/controller`, `engine/playback/track_loader`, _5 lainnya_  
**Menggunakan:** —


---


## engine/

**File:** `engine/command_router.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `CommandRouter`  
**Function utama:** `_route()`, `_route_volume()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `core/command_bus`


---

**File:** `engine/download_manager.py`  
**Fungsi:** Mengelola download lagu dari YouTube.  
**Class:** `DownloadManager`  
**Function utama:** `_update_progress()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/state`, `core/ports`, `core/task_utils`


---

**File:** `engine/mpv_controller.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `MpvController`  
**Function utama:** —  
**Digunakan oleh:** `main`  
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`, `core/task_utils`, `core/exceptions`


---

**File:** `engine/playback/controller.py`  
**Fungsi:** Central controller for playback orchestration.  
**Class:** `PlaybackController`  
**Function utama:** —  
**Digunakan oleh:** `engine/playback/__init__`, `server/app`  
**Menggunakan:** `core/event_bus`, `core/events`, `core/state`, `core/ports`, `cache/resolver`, `engine/queue_manager`, _3 lainnya_


---

**File:** `engine/playback/track_loader.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `TrackLoader`  
**Function utama:** —  
**Digunakan oleh:** `engine/playback/controller`  
**Menggunakan:** `core/state`, `core/ports`, `cache/resolver`, `core/task_utils`


---

**File:** `engine/queue_manager.py`  
**Fungsi:** Mengelola playback dari user queue.  
**Class:** `QueueMode`  
**Function utama:** —  
**Digunakan oleh:** `engine/playback/controller`  
**Menggunakan:** `core/events`, `core/state`


---

**File:** `engine/radio_engine.py`  
**Fungsi:** Mengelola pemutaran lagu secara otomatis dan berkelanjutan (Radio Mode). Radio Mode adalah fitur independen: ia memiliki list lagu sendiri (state.radio_queue) dan TIDAK PERNAH membaca atau menulis state.queue (milik Queue Mode). Lihat Constitution: "Radio must work independently from queue" dan "Radio must NEVER depend on Queue Empty events."  
**Class:** `RadioMode`  
**Function utama:** `check_prefetch()`  
**Digunakan oleh:** `engine/playback/controller`  
**Menggunakan:** `core/events`, `core/state`, `core/ports`, `core/task_utils`


---

**File:** `engine/volume_service.py`  
**Fungsi:** Mengelola kontrol volume MPV.  
**Class:** `VolumeService`  
**Function utama:** —  
**Digunakan oleh:** —  
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/ports`, `core/state`


---

**File:** `engine/ytdlp_client.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `YtDlpClient`  
**Function utama:** `cancel_download()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `core/state`, `config`


---


## cache/

**File:** `cache/db.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `Database`  
**Function utama:** `conn()`  
**Digunakan oleh:** `cache/resolver`, `main`, `scratch/check_db`, `services/discover_service`  
**Menggunakan:** `core/state`, `config`


---

**File:** `cache/resolver.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `CacheResolver`  
**Function utama:** —  
**Digunakan oleh:** `engine/playback/controller`, `engine/playback/track_loader`  
**Menggunakan:** `cache/db`, `config`, `core/state`, `core/ports`


---


## server/

**File:** `server/app.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `create_app()`, `run_server()`  
**Digunakan oleh:** —  
**Menggunakan:** `core/events`, `core/task_utils`, `server/serializers`, `server/handlers/http`, `server/handlers/websocket`, `config`, _2 lainnya_


---

**File:** `server/handlers/auth.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `handle_auth()`, `require_auth()`  
**Digunakan oleh:** `server/handlers/websocket`  
**Menggunakan:** `config`, `core/security`


---

**File:** `server/handlers/event_listeners.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `setup_event_listeners()`  
**Digunakan oleh:** —  
**Menggunakan:** `core/events`, `core/task_utils`, `server/services/stream_prefetch`, `server/services/broadcast_service`


---

**File:** `server/handlers/http.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `serve_index()`, `health_check()`, `serve_stream()`, `serve_metrics()`  
**Digunakan oleh:** `server/app`  
**Menggunakan:** `config`, `core/observability`


---

**File:** `server/handlers/websocket.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `ConnectionManager`  
**Function utama:** `disconnect()`, `ws_handler()`, `handle_ws_message()`  
**Digunakan oleh:** `server/app`, `server/services/broadcast_service`  
**Menggunakan:** `core/observability`, `core/command_bus`, `core/state`, `server/serializers`, `server/middleware`, `server/handlers/auth`, _1 lainnya_


---

**File:** `server/middleware.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `check_rate_limit_sync()`, `check_rate_limit()`  
**Digunakan oleh:** `server/handlers/websocket`  
**Menggunakan:** `core/observability`


---

**File:** `server/serializers.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `track_to_dict()`, `state_to_dict()`, `dict_to_track()`  
**Digunakan oleh:** `server/app`, `server/handlers/websocket`, `server/services/broadcast_service`  
**Menggunakan:** `core/state`


---

**File:** `server/services/broadcast_service.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `BroadcastService`  
**Function utama:** —  
**Digunakan oleh:** `server/handlers/event_listeners`  
**Menggunakan:** `server/serializers`, `server/handlers/websocket`, `core/state`


---

**File:** `server/services/stream_prefetch.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `StreamPrefetchService`  
**Function utama:** —  
**Digunakan oleh:** `server/handlers/event_listeners`  
**Menggunakan:** `config`, `core/ports`


---


## services/

**File:** `services/discover_service.py`  
**Fungsi:** Menyediakan data discover (recent dan favorites).  
**Class:** `DiscoverService`  
**Function utama:** —  
**Digunakan oleh:** `server/handlers/websocket`  
**Menggunakan:** `core/state`, `cache/db`


---


## plugins/

**File:** `plugins/lyrics.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `LyricsFetcher`  
**Function utama:** `cleanup()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`


---

**File:** `plugins/notifications.py`  
**Fungsi:** Mirrors current playback state to an Android notification via termux-notification (MediaStyle), and relays button presses back into the EventBus through a FIFO. No-op automatically on any platform where the termux-notification binary is not present.  
**Class:** `TermuxNowPlaying`  
**Function utama:** `_blocking_read_loop()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `core/event_bus`, `core/events`, `core/command_bus`, `core/state`, `config`


---

**File:** `plugins/sponsorblock.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `SponsorBlockHandler`  
**Function utama:** `cleanup()`  
**Digunakan oleh:** `main`  
**Menggunakan:** `config`, `core/event_bus`, `core/events`, `core/state`, `core/ports`, `core/task_utils`


---


## launcher/

**File:** `launcher/__main__.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `main()`  
**Digunakan oleh:** `start`  
**Menggunakan:** —


---

**File:** `launcher/gui.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `ServerManager(Tk)`  
**Function utama:** `server_port()`, `destroy()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `launcher/network.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `check_port_in_use()`, `get_pid_occupying_port()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `launcher/process.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `ServerProcess`  
**Function utama:** `kill_process_tree()`, `kill_mpv()`, `start()`, `is_running()`, `stop()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `launcher/updater.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `check_for_updates()`, `get_release_info()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---


## data/

**File:** `data/export_to_sqlite.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `create_tables()`, `main()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---


## scripts/

**File:** `scripts/architecture_lint.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** `Violation`  
**Function utama:** `path_to_layer()`, `module_to_layer()`, `check_file()`, `scan_project()`, `is_known()`, `main()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `scripts/doctor.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `section()`, `run_script()`, `check_docs()`, `check_architecture()`, `check_big_files()`, `check_pending_docs()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `scripts/find_owner.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `collect_py_files()`, `extract_info()`, `find_all_classes_and_functions()`, `build_reverse_index()`, `read_status_for_file()`, `resolve_target()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `scripts/generate_file_index.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `extract_purpose()`, `extract_module_info()`, `collect_py_files()`, `build_reverse_index()`, `format_file_entry()`, `build_generated_block()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `scripts/generate_report.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `count_files_by_ext()`, `count_py_files()`, `count_folders()`, `count_classes_and_functions()`, `count_lines()`, `count_js_files()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `scripts/run_all.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `run()`, `main()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---

**File:** `scripts/verify_docs.py`  
**Fungsi:** ⚠️ _Belum ada docstring modul terstruktur (Purpose/Subscribes to/Publishes)_  
**Class:** —  
**Function utama:** `read_text()`, `parse_frontmatter()`, `looks_like_path()`, `check_patchlog()`, `check_frontmatter_freshness()`, `build_basename_index()`  
**Digunakan oleh:** —  
**Menggunakan:** —


---


## ⚠️ File Besar (>200 baris)


| File | Baris | Catatan |
|---|---|---|

| `launcher/gui.py` | 756 | Perlu dipecah |

| `scripts/verify_docs.py` | 422 | Perlu dipecah |

| `scripts/generate_file_index.py` | 391 | Perlu dipecah |

| `cache/db.py` | 388 | Perlu dipecah |

| `engine/playback/controller.py` | 377 | Perlu dipecah |

| `engine/radio_engine.py` | 365 | Perlu dipecah |

| `server/handlers/websocket.py` | 316 | Perhatikan |

| `engine/mpv_controller.py` | 306 | Perhatikan |

| `scripts/generate_report.py` | 277 | Perhatikan |

| `scripts/find_owner.py` | 272 | Perhatikan |

| `scripts/architecture_lint.py` | 251 | Perhatikan |

| `scripts/doctor.py` | 249 | Perhatikan |

| `main.py` | 208 | Perhatikan |


## 📋 Checklist Dokumentasi Docstring

**10/53** file `.py` sudah punya docstring modul terstruktur (`Purpose:` / `Subscribes to:` / `Publishes:`). Berikut yang belum:


- [ ] `cache/db.py`

- [ ] `cache/resolver.py`

- [ ] `config.py`

- [ ] `core/events.py`

- [ ] `core/exceptions.py`

- [ ] `core/log_config.py`

- [ ] `core/observability.py`

- [ ] `core/ports.py`

- [ ] `core/security.py`

- [ ] `core/task_utils.py`

- [ ] `data/export_to_sqlite.py`

- [ ] `engine/command_router.py`

- [ ] `engine/mpv_controller.py`

- [ ] `engine/playback/track_loader.py`

- [ ] `engine/ytdlp_client.py`

- [ ] `launcher/__main__.py`

- [ ] `launcher/gui.py`

- [ ] `launcher/network.py`

- [ ] `launcher/process.py`

- [ ] `launcher/updater.py`

- [ ] `main.py`

- [ ] `plugins/lyrics.py`

- [ ] `plugins/sponsorblock.py`

- [ ] `scratch/check_db.py`

- [ ] `scripts/architecture_lint.py`

- [ ] `scripts/archive/generate_icons.py`

- [ ] `scripts/archive/inject_svgs.py`

- [ ] `scripts/doctor.py`

- [ ] `scripts/find_owner.py`

- [ ] `scripts/generate_file_index.py`

- [ ] `scripts/generate_report.py`

- [ ] `scripts/run_all.py`

- [ ] `scripts/verify_docs.py`

- [ ] `server/app.py`

- [ ] `server/handlers/auth.py`

- [ ] `server/handlers/event_listeners.py`

- [ ] `server/handlers/http.py`

- [ ] `server/handlers/websocket.py`

- [ ] `server/middleware.py`

- [ ] `server/serializers.py`

- [ ] `server/services/broadcast_service.py`

- [ ] `server/services/stream_prefetch.py`

- [ ] `start.py`

<!-- END:GENERATED -->
