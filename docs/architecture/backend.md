# Backend Architecture

← [architecture/overview.md](overview.md) | [Blueprint.md](../Blueprint.md)

---

## Peta Modul Python

Setiap modul di bawah memiliki **satu tanggung jawab**. Kolom *Testable* menandai apakah file dapat di-unit-test tanpa mock berat.

---

### `core/` — Pure Domain (tidak ada import eksternal)

| File | Tanggung Jawab | Testable |
|---|---|---|
| `state.py` | Single source of truth state aplikasi | ✅ |
| `event_bus.py` | Pub/sub internal, async event dispatch | ✅ |
| `command_bus.py` | Entry point semua aksi user, dispatch ke handler | ✅ |
| `commands.py` 🆕 | Konstanta `CMD_*` dipisah dari `command_bus` | ✅ |
| `events.py` | Konstanta `EVENT_*` | ✅ |
| `ports.py` | `Protocol` Python untuk semua adapter eksternal | ✅ |
| `security.py` | Token validation, auth helpers | ✅ |
| `task_utils.py` | Asyncio task helper (cancel, create safely) | ✅ |
| `observability.py` | Metrics, tracing stubs | ✅ |
| `exceptions.py` | Hierarki exception domain | ✅ |
| `log_config.py` | Setup logging (structlog / stdlib) | ⚠️ side-effect |
| `latency_window.py` 🆕 | Adaptive prefetch metric window | ✅ |

> `core/` tidak boleh mengimport apapun di luar `core/`.
> Lihat → [architecture/dependency_rules.md](dependency_rules.md)

---

### `adapters/` — Bridge ke Sistem Eksternal

#### `adapters/mpv/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `connection.py` 🆕 | Connect, reconnect, close socket IPC | ✅ (fake socket) |
| `ipc.py` 🆕 | Send command, pending futures, response parsing | ✅ |
| `observer.py` 🆕 | Event loop MPV → publish ke `event_bus` | ✅ |
| `__init__.py` 🆕 | Facade `MpvController` | ✅ |

> Alasan pilih IPC atas subprocess → [ADR-0001](../adr/0001-mpv-ipc-over-subprocess.md)

#### `adapters/ytdlp/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `searcher.py` 🆕 | `search(query) → List[TrackInfo]` | ✅ (fake extractor) |
| `resolver.py` 🆕 | `get_stream_url(video_id) → str` | ✅ |
| `downloader.py` 🆕 | `download_mp3(url) + progress_hook` | ✅ |
| `__init__.py` 🆕 | Facade `YtDlpClient` | ✅ |

---

### `engine/` — Domain Logic (orchestration)

#### `engine/` root

| File | Tanggung Jawab | Testable |
|---|---|---|
| `command_router.py` | Map CMD_* ke handler di engine layer | ✅ |
| `download_manager.py` | Antrian download, progress tracking | ✅ |
| `queue_manager.py` | Manajemen queue track (add, remove, reorder) | ✅ |
| `volume_service.py` | Set/get volume via port | ✅ |

#### `engine/playback/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `controller.py` | Slim orchestrator: play, pause, skip, stop | ✅ |
| `queue_ops.py` 🆕 | Operasi queue saat playback (next, prev) | ✅ |
| `mode_ops.py` 🆕 | Mode switching + set_speed, set_loop, set_crossfade, sleep timer | ✅ |
| `track_loader.py` | Resolve URL dan load ke player | ✅ |
| `crossfade.py` 🆕 | Crossfade fade-in/fade-out via MPV volume ramping | ✅ |

#### `engine/radio/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `engine.py` | Orchestrator radio mode, export `RadioMode` | ✅ |
| `prefetcher.py` | Prefetch track berikutnya di background | ✅ |
| `artist_selector.py` | Pilih artis berdasar queue & riwayat | ✅ |
| `artist_bandit.py` 🆕 | Thompson sampling untuk seleksi artis | ✅ |
| `track_interleaver.py` 🆕 | Interleave hasil pencarian berdasar artis | ✅ |
| `track_filter.py` | Filter track dari hasil pencarian — **akar bug radio mode** | ✅ ⚠️ |

#### `engine/loudness/` 🆕

| File | Tanggung Jawab | Testable |
|---|---|---|
| `analyzer.py` 🆕 | Eksekusi `ffprobe` untuk mengukur EBU R128 | ✅ |
| `gain_calculator.py` 🆕 | Hitung gain (dB) dan filter `af` MPV | ✅ |
| `service.py` 🆕 | Orchestrator pipeline normalisasi kenyaringan | ✅ |

---

### `persistence/` — Data Access

| File | Tanggung Jawab | Testable |
|---|---|---|
| `db.py` | Inisialisasi SQLite, connection pool | ✅ (in-memory) |
| `track_repo.py` | CRUD track | ✅ |
| `session_repo.py` | CRUD session playback | ✅ |
| `artist_repo.py` | CRUD artis | ✅ |
| `genre_repo.py` | CRUD genre | ✅ |
| `library_repo.py` | Query library (filter, sort, search) | ✅ |
| `schema.sql` | DDL SQLite, dipindah dari `cache/schema.sql` | — |
| `__init__.py` | Facade `Database`, backward-compat | ✅ |

> Alasan SQLite atas JSON cache → [ADR-0002](../adr/0002-sqlite-over-json-cache.md)
> Detail skema & query → [backend/persistence.md](../backend/persistence.md)

---

### `cache/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `resolver.py` | Cache URL stream, TTL, invalidasi | ✅ |
| `mp3/` | Folder penyimpanan file MP3 yang diunduh | — |

Detail → [backend/caching.md](../backend/caching.md)

---

### `server/` — API Layer

#### `server/` root

| File | Tanggung Jawab | Testable |
|---|---|---|
| `app.py` | FastAPI app factory, lifespan, router mount | ✅ |
| `middleware.py` | Auth middleware, CORS, rate limit | ✅ |
| `serializers.py` | Pydantic models / dict serialization | ✅ |
| `connection_manager.py` 🆕 | Registry koneksi WS aktif (cut dari websocket.py) | ✅ |

#### `server/handlers/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `auth.py` | Login endpoint, token issue | ✅ |
| `http.py` | HTTP endpoints (serve static, status) | ✅ |
| `event_listeners.py` | Subscribe event bus → trigger broadcast | ✅ |
| `websocket.py` | Slim: lifecycle WS + routing ke sub-handler | ✅ |
| `ws_playback.py` 🆕 | Handle cmd play/pause/skip/seek/volume/speed/loop/crossfade/sleep | ✅ |
| `ws_queue.py` 🆕 | Handle cmd queue add/remove/reorder | ✅ |
| `ws_discovery.py` 🆕 | Handle cmd search/discover | ✅ |
| `ws_download.py` 🆕 | Handle cmd download/cancel | ✅ |
| `ws_cache.py` 🆕 | Handle cmd get_cache_size / clear_cache | ✅ |

#### `server/services/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `broadcast_service.py` | Kirim state ke semua koneksi WS aktif | ✅ |
| `stream_prefetch.py` | Prefetch URL stream sebelum dibutuhkan | ✅ |

---

### `services/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `discover_service.py` | Logic discover (mix artis, trending) | ✅ |

---

### `plugins/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `lyrics_fetcher.py` 🆕 | Fetch lirik dari provider | ✅ (fake provider) |
| `lyrics_parser.py` 🆕 | Parse format LRC / SRT | ✅ |
| `lyrics_sync.py` 🆕 | Sinkronisasi lirik dengan posisi playback | ✅ |
| `notifications.py` | Desktop notification via port | ✅ |
| `sponsorblock.py` | Skip sponsor segment via SponsorBlock API | ✅ |

---

### `launcher/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `process.py` | Start/stop server process | ✅ |
| `network.py` | Cek port tersedia, resolve host | ✅ |
| `updater.py` | Update checker (stub) | ✅ |

#### `launcher/gui/`

| File | Tanggung Jawab | Testable |
|---|---|---|
| `app.py` 🆕 | Tkinter app, event loop | Manual QA |
| `ui_builder.py` 🆕 | Widget builder | Manual QA |
| `status_panel.py` 🆕 | Panel status server | ✅ (logic) |
| `log_panel.py` 🆕 | Panel log output | ✅ (logic) |
| `dep_checker.py` 🆕 | Cek dependensi saat startup | ✅ |
| `__init__.py` 🆕 | Facade | — |

---

### `scripts/`

| File | Tanggung Jawab |
|---|---|
| `export_to_sqlite.py` | Migrasi data JSON → SQLite |
| `generate_icons.py` | Generate icon set dari SVG |
| `inject_svgs.py` | Inject SVG inline ke HTML |
| `shortcuts/` | Shortcut script untuk OS |

---

## Dokumen Terkait

- [architecture/dependency_rules.md](dependency_rules.md) — Aturan arah import
- [backend/services.md](../backend/services.md) — Detail engine & services
- [backend/persistence.md](../backend/persistence.md) — Detail SQLite & repositories
- [backend/api.md](../backend/api.md) — HTTP & WebSocket API endpoints
- [backend/caching.md](../backend/caching.md) — Cache resolver
- [testing/unit_testing.md](../testing/unit_testing.md) — Tabel unit test per modul
