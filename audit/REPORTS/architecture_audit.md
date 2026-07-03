# Audit Arsitektur — ytgui (bagas.fm)

Referensi utama: source code (`.py`, `.js`, `.sql`, `.css`). Dokumen `.md` dan `.backup_patchlog/` diabaikan.

---

## 1. Folder Structure

```
core/      → domain primitives (state, events, ports, security, utils)
engine/    → business logic / use-cases (playback, queue, radio, download, mpv, ytdlp)
cache/     → persistence (db, resolver)
server/    → delivery layer (HTTP + WebSocket handlers, DI wiring)
services/  → 1 file saja (discover_service.py) — di luar server/services/
plugins/   → optional/pluggable features (lyrics, sponsorblock, notifications)
web/       → frontend statis (vanilla JS + CSS)
tests/     → unit + integration, terpisah rapi
data/      → dataset & script import
```

**Penilaian: 7.5/10.**
Positif: pemisahan `core/engine/cache/server` sudah mencerminkan niat layering yang jelas — jarang ditemukan di proyek solo. `core/ports.py` sebagai lapisan abstraksi eksplisit adalah tanda kedewasaan arsitektur.

Masalah:
- **`services/discover_service.py` inkonsisten** — ada juga `server/services/` (stream_prefetch, broadcast_service). Dua lokasi untuk konsep yang sama ("service") membingungkan; harusnya satu konvensi (`server/services/discover_service.py`).
- `plugins/` isinya lyrics & sponsorblock — ini sebenarnya *domain features*, bukan "plugin" opsional yang bisa dicabut tanpa efek (tightly coupled ke `PlaybackController` via constructor injection). Penamaan menyesatkan.
- Tidak ada folder `interfaces`/`adapters` eksplisit — port (`core/ports.py`) dan implementasi konkretnya (`MpvController`, `YtDlpClient`, `Database`) tersebar di folder berbeda tanpa pengelompokan "adapter layer" yang jelas.

---

## 2. Dependency Direction

**Penilaian: 8/10 — arah dependency secara umum benar (inward), dengan sedikit kebocoran.**

Alur yang diharapkan (Clean Architecture): `server → engine → core ← cache`, tidak ada arah sebaliknya.

Temuan aktual:
- `core/ports.py` mendefinisikan `Protocol` (structural typing) untuk `AudioPlayerPort`, `MediaExtractorPort`, `TrackRepositoryPort`, dll — `engine/playback/controller.py` bergantung ke **abstraksi** ini (`AudioPlayerPort`, bukan `MpvController` langsung), ini textbook **Dependency Inversion** yang benar.
- **Pelanggaran kecil**: `services/discover_service.py` mengakses `self.db._conn` (atribut privat/protected dengan underscore) alih-alih lewat method publik `Database` atau lewat `TrackRepositoryPort`. Ini melompati abstraksi — `DiscoverService` jadi bergantung ke detail implementasi `cache/db.py`, bukan ke port. Kalau `Database` migrasi dari `aiosqlite` ke driver lain, `DiscoverService` ikut rusak.
- `core/event_bus.py` mengimpor `core.task_utils` dan `core.observability` — masih dalam lapisan `core`, aman.
- `main.py` sebagai *composition root* melakukan wiring manual (constructor injection) — ini pola yang benar untuk memastikan dependency mengalir satu arah dari luar ke dalam.

---

## 3. Layering

**Penilaian: 7/10.**

Layer yang teridentifikasi:
1. **Presentation/Delivery** — `server/handlers/*` (HTTP + WS), `web/static/*`
2. **Application/Orchestration** — `engine/playback/controller.py`, `engine/command_router.py`, `core/command_bus.py`, `core/event_bus.py`
3. **Domain** — `core/state.py` (TrackInfo, AppState), `core/events.py`
4. **Infrastructure** — `engine/mpv_controller.py`, `engine/ytdlp_client.py`, `cache/db.py`

Masalah:
- `services/discover_service.py` menembus langsung ke infrastruktur (`db._conn`) dari luar `cache/`, melompati layer application/port — pelanggaran layering yang sama seperti di poin Dependency Direction.
- `engine/radio_engine.py` dan `engine/playback/controller.py` sama-sama memanggil `self.db` / `resolver.db` langsung untuk query lagu acak dan `upsert_track` — application layer bicara langsung ke infrastruktur tanpa lapisan Repository/Service perantara yang konsisten (kadang lewat `CacheResolver`, kadang langsung `self.db.xxx`). Ini membuat batas antara "engine" dan "cache" kabur.
- Frontend (`web/static/js/`) tidak punya layering sama sekali — semua fungsi berbagi 1 `window`/global scope tanpa pemisahan presentation vs. state vs. transport (dibahas lebih lanjut di §12 State Management).

---

## 4. SOLID

| Prinsip | Skor | Catatan |
|---|---|---|
| **S**ingle Responsibility | 7/10 | Mayoritas kelas fokus (QueueMode, RadioMode, VolumeService, DownloadManager masing-masing 1 concern). Tapi `PlaybackController` sudah membengkak menjadi god-object: menangani play/pause/seek/queue/radio-mode-switch/output-switch/sponsorblock-toggle/lyrics-offset — 15+ handler dalam 1 kelas. |
| **O**pen/Closed | 6/10 | Menambah command baru butuh edit 3 tempat sekaligus: `core/command_bus.py` (konstanta), `engine/command_router.py` (registrasi), `server/handlers/websocket.py` (`_ws_handlers` dict). Tidak ada mekanisme extend tanpa modifikasi. |
| **L**iskov Substitution | 8/10 | Penggunaan `Protocol` (`AudioPlayerPort`, dll.) memungkinkan substitusi implementasi tanpa merusak kontrak — bagus untuk testability (lihat `tests/unit/engine/test_radio.py` kemungkinan pakai fake/mock yang comply ke Protocol). |
| **I**nterface Segregation | 7/10 | Port-port di `core/ports.py` cukup granular (`LyricsProvider`, `SponsorBlockProvider` terpisah dari `AudioPlayerPort`) — baik. Tapi `DatabasePort` menggabungkan `TrackRepositoryPort` + `SessionRepositoryPort` menjadi satu interface besar yang dipakai di mana-mana walau consumer hanya butuh salah satunya (mis. `auth.py` hanya butuh session, tapi terima `db` bertipe `DatabasePort` penuh). |
| **D**ependency Inversion | 8/10 | Baik di backend (constructor injection + Protocol). Nol di frontend (semua fungsi JS memanggil global `store`, `dom`, `ws` langsung — tidak ada injeksi apapun). |

---

## 5. DRY

**Penilaian: 6.5/10.**

- Pola *"async with self._lock: ... publish QueueUpdatedEvent()"* diulang di hampir setiap handler `PlaybackController` (`_on_queue_remove`, `_on_queue_add`, `_on_queue_replace`, `_on_queue_reorder`, dll.) — bisa diekstrak jadi decorator/helper `@with_lock_and_broadcast`.
- Logic "increment duration lalu upsert ke DB lalu publish QueueUpdatedEvent" muncul identik 3x (`_on_track_duration`, dan 2x di `_poll_duration`) — kandidat kuat untuk diekstrak jadi 1 method `_set_duration(track, dur)`.
- Validasi `video_id` dengan regex `^[a-zA-Z0-9_-]{11}$` hanya ada di `server/handlers/http.py`, tidak direplikasi (malah tidak ada sama sekali) di `server/serializers.py::dict_to_track` — ini kebalikan dari DRY (missing shared validation, bukan duplikasi kode, tapi akar masalahnya sama: tidak ada satu titik validasi terpusat).
- CSS: struktur `web/static/css/` sudah cukup DRY dengan `tokens.css` sebagai sumber design tokens, dan pemisahan `base/`, `components/`, `layout/`, `platform/` — ini justru salah satu bagian ter-DRY di seluruh project.

---

## 6. KISS

**Penilaian: 6/10.**

- `engine/radio_engine.py` punya kompleksitas tersembunyi yang cukup tinggi: konsep `_standby`, `_fetch_lock`, `_standby_lock`, quick-batch vs full-batch fetch, backfill — total 9 method saling terkait untuk 1 concern "putar lagu radio berikutnya". Fungsional tapi sulit dipahami pendatang baru tanpa membaca semuanya sekaligus (workable, tapi jauh dari sederhana).
- Sebaliknya, `engine/queue_manager.py` adalah contoh KISS yang baik — 1 class, 1 method, jelas.
- Command dispatch memakai 3 lapis tidak langsung (`command_bus.execute` → `CommandRouter._route` closure → `PlaybackController._on_xxx`) untuk operasi yang sebenarnya bisa dipanggil langsung — menambah indirection yang tidak selalu sepadan dengan manfaatnya untuk aplikasi single-instance seperti ini.

---

## 7. YAGNI

**Penilaian: 6/10 — ada beberapa indikasi over-engineering untuk skala single-user self-hosted app.**

- **OpenTelemetry tracing** (`core/observability.py`, terlihat dari `opentelemetry-api`/`opentelemetry-sdk` di `requirements.txt` dan `tracer.start_as_current_span` di `command_bus.py`) — untuk aplikasi single-process, single-user, self-hosted di Termux, observability distributed-tracing ini kemungkinan besar tidak pernah dikonsumsi (tidak ada Jaeger/Tempo/collector yang disebut dikonfigurasi). Overhead kompleksitas > manfaat pada skala ini.
- **Prometheus metrics endpoint** (`/metrics`, `core/observability.py`) — berguna untuk multi-instance/production monitoring, tapi untuk single-user player, ini kemungkinan besar tidak pernah di-scrape.
- **`SessionRepositoryPort`/multi-session infra** di `core/ports.py` untuk app yang secara desain hanya punya 1 admin user.
- Di sisi lain, **rate-limiting dan session-token architecture** (bukan YAGNI) justru tepat karena app ini expose ke jaringan (Termux/self-hosted diakses dari device lain) — jadi bukan semua kompleksitas berlebihan, hanya observability stack yang terasa besar untuk skalanya.

---

## 8. Clean Architecture

**Penilaian: 7/10 — konsepnya diterapkan, walau tidak 100% murni.**

Yang sudah benar:
- Domain (`core/state.py`, `core/events.py`) tidak bergantung pada framework luar (aiohttp, aiosqlite, yt-dlp tidak diimpor di `core/`).
- Port/Protocol (`core/ports.py`) sebagai boundary — use case (`PlaybackController`) bicara ke abstraksi, bukan implementasi konkret.
- `main.py` sebagai composition root yang mem-wiring semua dependency secara eksplisit di satu tempat.

Yang menyimpang:
- Tidak ada lapisan **Use Case / Application Service** yang benar-benar terpisah dari **Controller** — `PlaybackController` merangkap peran use-case-interactor sekaligus event-handler sekaligus (secara tidak langsung) menjadi tempat business rule bercampur dengan orkestrasi I/O (`await self.mpv.play(uri)` — infrastruktur call — langsung di tengah use-case).
- `DiscoverService` menembus ke `db._conn` (dibahas di §2/§3) — pelanggaran langsung terhadap Dependency Rule Clean Architecture ("source code dependencies can only point inward").

---

## 9. DDD (Domain-Driven Design)

**Penilaian: 5/10 — ada kosakata domain yang konsisten, tapi tidak menerapkan pola DDD taktis secara penuh.**

- **Ubiquitous language cukup konsisten**: `TrackInfo`, `PlaybackMode`, `PlayerStatus`, `QueueMode`, `RadioMode` — nama-nama ini dipakai konsisten dari backend sampai payload WS ke frontend.
- **Tidak ada Aggregate/Entity/Value Object yang jelas dipisahkan** — `TrackInfo` adalah `@dataclass` datar yang berfungsi sekaligus sebagai entity domain, DTO API, dan row database representation (dipakai apa adanya di `serializers.py`, `cache/db.py`, dan `core/state.py`) — anti-pattern "Anemic Domain Model": tidak ada method domain di `TrackInfo` (semua logic ada di service/controller di luar objek).
- **`AppState` adalah 1 aggregate raksasa** yang menggabungkan banyak concern (playback + queue + radio + lyrics + download progress + connectivity) — dalam DDD murni ini idealnya dipecah jadi beberapa aggregate lebih kecil dengan invariant masing-masing (`PlaybackSession`, `QueueAggregate`, `RadioSession`, dsb).
- Tidak ada Domain Events dalam pengertian DDD murni (event di sini lebih ke arah *application/integration events* untuk pub-sub UI sync, bukan representasi perubahan state invariant domain) — meski secara praktis event-driven architecture-nya tetap bermanfaat.

**Catatan:** DDD taktis penuh kemungkinan besar berlebihan (YAGNI) untuk domain sesederhana music player — skor rendah di sini bukan berarti harus "diperbaiki", tapi mencerminkan bahwa project ini bukan DDD murni meski memakai sebagian kosakatanya.

---

## 10. Feature Modularization

**Penilaian: 6/10 — modularisasi backend cukup baik per-teknis-layer, tapi bukan per-fitur (vertical slice).**

Backend saat ini modular secara **horizontal** (per jenis komponen: semua handler di `server/handlers/`, semua engine di `engine/`), bukan **vertical** (per fitur: semua kode "radio" dalam satu folder `features/radio/{engine,handler,service}.py`). Untuk menambah 1 fitur baru (mis. "playlist"), developer harus menyentuh minimal 5 file berbeda di 5 folder berbeda (`core/command_bus.py`, `engine/command_router.py`, `server/handlers/websocket.py`, `server/serializers.py`, `web/static/js/events/`).

Frontend **sama sekali tidak modular** — 25 file JS berbagi 1 global namespace tanpa module boundary (`export`/`import` tidak dipakai; lihat `<script>` tag di `index.html`, bukan `type="module"`). Menambah fitur di frontend berarti menambah global function baru yang berpotensi collision nama dengan fungsi lain.

---

## 11. Dependency Injection

**Penilaian: 8/10 (backend) / 1/10 (frontend).**

Backend: DI manual (constructor injection) diterapkan konsisten dari `main.py` sampai ke `PlaybackController`, `VolumeService`, `DownloadManager`, `CommandRouter` — semua dependency (bus, state, mpv, resolver, dsb.) di-pass eksplisit lewat constructor, bukan diambil dari global/singleton (kecuali `core.event_bus.bus` dan `core.command_bus.command_bus` yang **memang** module-level singleton — pola ini secara sadar dipilih untuk command/event bus, trade-off yang wajar untuk aplikasi single-process).

Frontend: **tidak ada DI sama sekali** — `store`, `dom`, `ws` semua diakses sebagai variabel global lintas file. Setiap fungsi JS implisit bergantung pada keberadaan global tersebut tanpa deklarasi eksplisit di parameter — sulit untuk unit test terisolasi (dan memang tidak ada test untuk JS sama sekali, konsisten dengan temuan audit kualitas sebelumnya).

---

## 12. Repository Pattern

**Penilaian: 6/10 — setengah diterapkan.**

- `core/ports.py::TrackRepositoryPort` dan `SessionRepositoryPort` mendefinisikan kontrak repository yang jelas.
- `cache/db.py::Database` mengimplementasikan kontrak itu (`upsert_track`, `get_track`, `create_session`, dll.) — cukup dekat dengan pola Repository yang benar.
- **Namun** `Database` juga bocor sebagai *query builder umum* — dipanggil dengan method-method spesifik use-case yang seharusnya milik service/query layer terpisah (`get_genre_artists`, `get_random_songs`, `get_artist_songs_strict`, `increment_artist_click`) — Repository idealnya hanya urus persistence CRUD entity, bukan logic query bisnis seperti "artist rotation exclusion" (`_build_exclusion_set` di `radio_engine.py` memang di luar `Database`, tapi query random-song-nya sendiri sudah mengandung business rule "exclude artist itu" di dalam `Database.get_random_songs`).
- `DiscoverService` melompati Repository sepenuhnya dengan akses `db._conn` langsung — inkonsistensi paling jelas: sebagian kode disiplin pakai Repository, sebagian lain tidak.

---

## 13. Service Layer

**Penilaian: 6.5/10.**

Service layer ada tapi tersebar dan namanya tumpang tindih dengan "engine":
- `engine/volume_service.py`, `engine/download_manager.py`, `services/discover_service.py`, `server/services/stream_prefetch.py`, `server/services/broadcast_service.py` — lima "service" di tiga lokasi berbeda dengan tanggung jawab campur antara *application service* (orkestrasi use case) dan *domain service* (pure business logic) tanpa pemisahan eksplisit.
- Tidak ada konvensi penamaan/lokasi yang konsisten untuk "kapan sesuatu jadi `*_service.py` vs `*_manager.py` vs `*_engine.py` vs `*_controller.py`" — empat istilah berbeda dipakai untuk peran yang secara arsitektural mirip (orkestrasi use case), membuat mental model project lebih sulit dipetakan bagi kontributor baru.

---

## 14. State Management

**Penilaian: Backend 8/10, Frontend 4/10.**

**Backend** — `AppState` (single source of truth di server) + `EventBus` (push perubahan ke semua WS client via broadcast) adalah pola state management yang solid untuk real-time multi-client sync: state hidup di server, client hanyalah "view" yang menerima snapshot (`"type":"state"`) dan delta event (`"progress"`, `"favorite_status"`, dll). Konsisten dan predictable.

**Frontend** — `store` adalah objek JS polos (`web/static/js/store.js`) yang **dimutasi langsung dari mana saja** (`Object.assign(store, msg.data)`, `store.position = ...`, `store.lyrics_index = ...`) tanpa reducer/immutability/subscription model. Efeknya:
- Tidak ada cara sistematis untuk tahu "siapa yang mengubah state apa" — setiap file JS bisa menulis ke `store` langsung.
- Re-render dipicu manual (`renderProgress()`, `renderQueue()`, dst dipanggil eksplisit setelah tiap mutasi) — rawan lupa panggil render function tertentu setelah state berubah (sudah terlihat pola `if (typeof renderXxx === "function") renderXxx()` berulang di `ws.js` sebagai workaround, bukan solusi arsitektural).
- Tidak ada single dispatch point (seperti reducer/action) untuk audit atau debugging state changes.

---

## 15. Scalability

**Penilaian: 5.5/10 — didesain untuk single-instance/single-user, bukan horizontal scale.**

- Satu proses `mpv` per aplikasi (`MpvController` singleton via 1 socket) — desain ini secara sadar untuk 1 "ruang dengar" bersama multi-client (semua WS client dengar lagu yang sama), cocok untuk use-case aslinya (personal self-hosted radio), tapi **tidak bisa di-scale ke multi-tenant/multi-room** tanpa refactor besar (perlu 1 `MpvController` + `AppState` per "room").
- State in-memory (`ConnectionManager.login_attempts`, `command_history`, `AppState` itu sendiri) — hilang saat restart, tidak bisa di-share antar >1 instance proses (tidak ada Redis/external state store).
- `aiosqlite` dengan 1 koneksi persisten (`Database._conn`) — cukup untuk single-user load, tapi menjadi bottleneck serialization point kalau load meningkat signifikan.
- **Positif**: pemakaian `asyncio` end-to-end (bukan threading blocking I/O untuk DB/network) sudah tepat untuk vertical scalability (menangani banyak koneksi WS bersamaan pada 1 proses).

---

## 16. Future Maintainability

**Penilaian: 7/10.**

Faktor positif:
- Pola patch bertag (`# PATCHLOG_APPLIED`, `TASK-1.1`, dll.) menunjukkan disiplin tracking perubahan — memudahkan audit historis.
- Protocol-based ports memudahkan penggantian implementasi (mis. ganti `yt-dlp` dengan extractor lain) tanpa menyentuh `PlaybackController`.
- Test suite (131 test) memberi jaring pengaman untuk refactor backend.

Faktor risiko:
- `PlaybackController` yang terus membengkak (God Object) akan makin mahal untuk di-maintain seiring fitur bertambah — perlu dipecah sebelum menambah fitur besar berikutnya.
- Frontend tanpa module system akan makin rapuh — setiap developer baru (termasuk AI agent) berisiko memperkenalkan name collision di global scope karena tidak ada compiler/linter yang mendeteksinya.
- Inkonsistensi nama layer (service/manager/engine/controller) akan makin membingungkan kontributor baru seiring project tumbuh.

---

## 17. Diagram Arsitektur Ideal (Target Clean Architecture + DI penuh)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            PRESENTATION LAYER                             │
│  ┌────────────────────────┐        ┌───────────────────────────────────┐ │
│  │  Frontend (ES Modules)  │        │   server/handlers/ (HTTP + WS)    │ │
│  │  ─────────────────────  │◄──WS──►│  ws_handler, http handlers        │ │
│  │  store/ (state module)  │  JSON  │  → hanya parsing + validasi I/O   │ │
│  │  render/ (view modules) │        │  → delegasikan ke Application     │ │
│  │  services/ (ws client)  │        └───────────────────┬───────────────┘ │
│  └────────────────────────┘                             │                 │
└───────────────────────────────────────────────────────────┼──────────────┘
                                                              │ calls
                                                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         APPLICATION LAYER (Use Cases)                     │
│  features/                                                                │
│   ├── playback/                                                           │
│   │    ├── application/  PlayTrackUseCase, StopUseCase, SeekUseCase      │
│   │    │                 (masing-masing kecil, single-responsibility)     │
│   │    └── ...                                                            │
│   ├── queue/       application/  AddToQueueUseCase, ReorderUseCase        │
│   ├── radio/        application/  RadioNextUseCase, RandomizeUseCase      │
│   ├── download/     application/  DownloadTrackUseCase                    │
│   └── discover/     application/  GetDiscoverDataUseCase                  │
│                                                                             │
│  Semua use case HANYA bergantung ke port (interface), di-inject via DI   │
│  container di composition root (main.py).                                 │
└───────────────────────────────┬────────────────────────────────────────┘
                                  │ depends on (interface only)
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                              DOMAIN LAYER (core/)                         │
│  core/domain/                                                             │
│    Entities:      Track (dengan behavior, bukan anemic dataclass)         │
│    Value Objects:  Duration, VideoId (validasi format built-in)           │
│    Aggregates:     PlaybackSession, QueueAggregate, RadioSession          │
│    Domain Events:  TrackStarted, TrackEnded, QueueChanged                 │
│    Ports:          AudioPlayerPort, MediaExtractorPort,                   │
│                     TrackRepositoryPort, SessionRepositoryPort            │
│                                                                             │
│  ZERO dependency ke framework luar (aiohttp/aiosqlite/yt-dlp dilarang     │
│  diimpor di sini).                                                        │
└───────────────────────────────▲────────────────────────────────────────┘
                                  │ implements (dependency inversion)
                                  │
┌──────────────────────────────────────────────────────────────────────────┐
│                          INFRASTRUCTURE LAYER (adapters/)                 │
│  adapters/                                                                 │
│   ├── mpv/           MpvController implements AudioPlayerPort            │
│   ├── ytdlp/          YtDlpClient implements MediaExtractorPort           │
│   ├── persistence/    SqliteTrackRepository implements TrackRepositoryPort│
│   │                   SqliteSessionRepository implements SessionRepo...   │
│   └── notifications/  TermuxNowPlaying (optional adapter)                 │
└──────────────────────────────────────────────────────────────────────────┘

              ▲                                              ▲
              │                                              │
              └──────────────── composition root ────────────┘
                       main.py: wiring semua adapter ke use case
                       via constructor injection (DI container ringan)

Dependency Rule:  Presentation → Application → Domain ← Infrastructure
                  (Infrastructure implement port yang didefinisikan Domain,
                   BUKAN Domain memanggil Infrastructure langsung)
```

**Perbedaan kunci dari struktur saat ini:**
1. **Vertical slice per fitur** (`features/playback`, `features/radio`, dst.) menggantikan horizontal split saat ini (`engine/`, `server/`) — menambah fitur baru cukup 1 folder baru, bukan menyentuh 5 file tersebar.
2. **`PlaybackController` dipecah** jadi use-case kecil per-command (`PlayTrackUseCase`, `SeekUseCase`, dll.) — masing-masing testable independen, menghilangkan God Object.
3. **Repository konsisten** — `DiscoverService`/query khusus lainnya wajib lewat `TrackRepositoryPort`, tidak ada akses `db._conn` langsung dari luar `adapters/persistence/`.
4. **Frontend jadi ES modules** dengan store sebagai 1 modul state-management eksplisit (bisa custom pub-sub kecil, tidak perlu framework besar) — `render/`, `services/` (WS client), dan `store/` punya boundary import yang jelas via `export`/`import`, menghilangkan ketergantungan `window.*` global.
