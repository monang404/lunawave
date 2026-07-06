# Maintainability Audit — ytgui / bagas.fm
> Source of truth: active source code only. Semua markdown/docs diabaikan.
> Tanggal audit: 2026-07-03

---

## Skor Ringkasan

| Dimensi | Skor | Catatan |
|---|---|---|
| Readability | 7/10 | Baik secara lokal, tapi bilingual naming dan inline TODO noise |
| Naming | 6/10 | Inkonsisten: Bahasa Indonesia + Inggris campur di method names |
| Consistency | 6/10 | Pattern deviasi di beberapa modul (import style, error handling) |
| Modularity | 7/10 | Struktur layer bagus, tapi ada God Class (Database) dan misplaced file |
| Extensibility | 7/10 | CommandBus + EventBus membuat fitur baru mudah, tapi websocket handler rigid |
| Coupling | 6/10 | Tiga global singleton, `_conn` exposed, PlaybackController aware terlalu banyak |
| Cohesion | 5/10 | `Database` (388 baris, 5 domain), `log_config.py` (477 baris, 4 class), `discover_data` duplikat |
| Technical Debt | MEDIUM-HIGH | 10 file ber-`PATCHLOG_APPLIED`, `config.py` side effects, 93 typeof guards di JS |
| **Overall** | **6.3/10** | Solid foundation, debt terkumpul di 4–5 file kritis |

---

## 1. READABILITY

### Kekuatan
- Semua file Python punya docstring `Purpose/Subscribes/Publishes` di atas — sangat membantu orientasi.
- `core/events.py`, `core/ports.py`, `core/state.py` bersih dan mudah dibaca.
- `PlaybackController` punya method kecil-kecil yang fokus — mudah di-trace alurnya.
- Komentar inline yang relevan (`# PATCH-RADIO-EMPTY-QUEUE-01:`, `# A-05:`) menjelaskan *why*, bukan hanya *what*.

### Masalah

**`core/log_config.py` — 477 baris, 4 class, mixed concerns**
```
Berisi: status bar terminal, spinner, stats counter, log formatter,
        structlog config, file handler, ANSI color codes.
```
File ini mengerjakan terlalu banyak hal sekaligus. Fungsi `setup_logging()` di baris 416 merupakan output utamanya, tapi pembaca harus melewati 400+ baris infrastruktur terminal untuk mencapainya.

**`start.py` — 834 baris, semua dalam satu file**
```
Berisi: Tkinter GUI, process manager, dependency checker, password dialog,
        first-run setup, port conflict resolver.
```
Tidak ada cara singkat untuk mencari fungsi tertentu tanpa `Ctrl+F`.

**Komentar noise dari patchlog era:**
```python
# PATCHLOG_APPLIED  ← di 10 file, tidak memberikan info baru setelah applied
# CRITICAL-04 fix: ...  ← sudah fix, tapi komentar terus ada
# HIGH-02 fix: ...
```
Ini adalah "archaeological comments" — berguna saat patch diterapkan, tapi sekarang menjadi noise yang memaksa pembaca baru untuk filter mana yang aktual vs historical.

---

## 2. NAMING

### Inkonsistensi Bahasa (Inggris vs Indonesia)

Python source campur dua bahasa dalam naming:

**Indonesia di method names:**
```python
# cache/db.py
async def get_all_artists(self, kategori=...)  # 'kategori' bukan 'category'
async def get_genre_songs(...)  # nama_genre, judul, nama dalam SQL result keys
async def get_random_songs(...)  # judul, nama di TrackInfo mapping

# radio_engine.py
_seed_artists, _artist_rotation  # Inggris
_standby, _standby_lock          # Inggris
nama, judul  # muncul dari DB rows - Indonesia
```

**Log messages dalam Bahasa Indonesia:**
```python
await bus.publish(LogMessageEvent(message="Mengacak ulang stasiun radio..."))
await bus.publish(LogMessageEvent(message="Tidak ada lagu sebelumnya"))
await bus.publish(LogMessageEvent(message="Terlalu banyak kegagalan beruntun."))
```
Log ini dikirim ke client UI (JS) dan ke terminal. Jika project berkembang multi-bahasa, semua string ini perlu diganti — tidak ada i18n layer.

**Inkonsistensi di DB schema:**
- Tabel `tracks`: kolom `title`, `artist`, `duration` → Inggris
- Tabel `songs`: kolom `judul`, `nama` (via JOIN dengan `artists`) → Indonesia
- Ini menyebabkan mapping yang awkward di `get_random_songs()`:
  ```python
  title=row["judul"],   # bukan row["title"]
  artist=row["nama"],   # bukan row["artist"]
  ```

**Naming `_LOG_STATS` sebagai module-level alias:**
```python
# engine/playback/controller.py
from core.log_config import STATS as _LOG_STATS
```
`_LOG_STATS` adalah alias dengan underscore prefix (konvensi private) tapi diakses di beberapa tempat. Nama lebih baik: import langsung `STATS` atau `stats_counter`.

### Kekuatan naming
- Command constants konsisten: `CMD_PLAY_TRACK`, `CMD_TOGGLE_PAUSE`, `CMD_NEXT` — uniform prefix `CMD_`.
- Event classes konsisten: `TrackStartedEvent`, `TrackEndedEvent`, `QueueUpdatedEvent` — uniform suffix `Event`.
- Ports: `AudioPlayerPort`, `MediaExtractorPort`, `DatabasePort` — uniform suffix `Port`.

---

## 3. CONSISTENCY

### Python: Import Style Tidak Konsisten

**Deferred/inline imports di dalam fungsi:**
```python
# server/handlers/websocket.py baris 33, 56
async def broadcast(self, message: dict):
    import asyncio  # ← sudah ada di module level di file lain

# server/handlers/websocket.py baris 243
async def _handle_delete_download(...):
    import os  # ← seharusnya top-level

# engine/playback/controller.py baris 251
async def _on_radio_randomize(self, data=None):
    from core.task_utils import safe_create_task  # ← sudah diimport di atas!
```
`safe_create_task` sudah diimport di baris 21 file yang sama, tapi di-import lagi di dalam method. Ini inconsistency, bukan circular import prevention.

**Import `asyncio` inline di `ConnectionManager.__init__`:**
```python
class ConnectionManager:
    def __init__(self):
        ...
        import asyncio
        self.rl_lock = asyncio.Lock()
```
`asyncio` jelas tersedia di module level (dipakai di atas), tidak ada alasan defer.

### Python: Error Handling Pattern Berbeda-beda

**Pattern 1 — guard + return:**
```python
async def increment_artist_click(self, artist_name: str):
    if not self._conn: return  # satu baris, tanpa log
```

**Pattern 2 — try/except dengan log:**
```python
async def increment_artist_click(self, artist_name: str):
    try: ...
    except Exception as e:
        logger.error(f"Error incrementing artist click: {e}")
```

**Pattern 3 — silent except pass:**
```python
try:
    await self._conn.execute("ALTER TABLE tracks ADD COLUMN is_favorite ...")
    await self._conn.commit()
except Exception:
    pass  # intentional: kolom sudah ada
```
Pattern 3 di `Database.init()` ada 4x untuk schema migration. Ini acceptable, tapi tanpa komentar akan terlihat seperti lazy error suppression.

### JS: `typeof` Guard Pattern — 93 Occurrences

```javascript
if (typeof renderPlayBtn === "function") renderPlayBtn();
if (typeof renderNowPlaying === "function") renderNowPlaying();
if (typeof syncBrowserAudio === "function") syncBrowserAudio(wantsPlay);
```
Ada 93 guard `typeof ... === "function"` tersebar di JS files. Ini adalah pola defensive programming karena JS tidak menggunakan module system (semua file di-concatenate implicitly via `<script>` tags di HTML). Konsekuensinya: developer selalu harus defensive guard saat memanggil fungsi lintas file. Ini membuat code verbose dan menyulitkan refactor.

---

## 4. MODULARITY

### Kekuatan
- Pemisahan `core/`, `engine/`, `server/`, `plugins/`, `cache/` jelas dan meaningful.
- `PlaybackController` berhasil di-split dari satu God file ke:
  - `controller.py` (orchestration)
  - `track_loader.py` (loading concern)
  - `queue_manager.py` (queue logic)
  - `radio_engine.py` (radio logic)
- Port/Protocol pattern di `core/ports.py` memungkinkan substitusi implementasi.

### Masalah

**`services/discover_service.py` — File di lokasi salah**
```
/services/discover_service.py  ← di root level, bukan di /server/services/
```
Ini adalah satu-satunya file di direktori `services/` root. Semua services lain ada di `server/services/`. Ini bukan keputusan arsitektur — ini inkonsistensi yang membingungkan.

**`Database` class (388 baris) — God Class dengan 5 domain berbeda**
```
Satu class mengelola:
  1. Track cache (upsert_track, get_track, update_stream_url_only, set_local_path)
  2. Session auth (create_session, verify_session, delete_session, cleanup_sessions)
  3. Artist catalog (get_all_artists, get_artist_songs_strict, increment_artist_click)
  4. Genre catalog (get_genre_songs, get_genre_artists, increment_genre_click)
  5. Lifecycle (init, close, evict_stale_tracks)
```
`DatabasePort` di `core/ports.py` sudah memisahkan `TrackRepositoryPort` dan `SessionRepositoryPort` — tapi implementasinya masih satu class. Artist dan genre belum punya port sama sekali.

**`core/log_config.py` (477 baris) — Mixed concerns**
```
1. _Stats counter class (state)
2. Status bar terminal renderer (thread, ANSI, psutil)
3. Spinner animation class
4. Summary worker (background thread)
5. structlog processor/renderer
6. File handler setup
7. setup_logging() (entry point)
```
Minimal 3 file terpisah: `stats.py`, `terminal_ui.py`, `log_setup.py`.

---

## 5. EXTENSIBILITY

### Kekuatan
- **CommandBus** dengan `register()/unregister()` memudahkan penambahan command baru — cukup register handler, tidak perlu ubah dispatcher.
- **EventBus** dengan typed events memungkinkan subscriber baru tanpa mengubah publisher.
- **WebSocket handler registry** (`_ws_handlers` dict + `@register_ws_handler` decorator) clean untuk menambah action baru.
- **Port Protocol** memungkinkan swap implementasi (misal: ganti mpv dengan vlc cukup implementasi `AudioPlayerPort`).

### Masalah

**`DiscoverService` dibuat ulang setiap request (tidak injectable)**
```python
# server/handlers/websocket.py
async def _build_discover_payload(db):
    ds = DiscoverService(db)  # ← new instance every call

# server/handlers/event_listeners.py
async def _on_download_complete(event):
    ds = DiscoverService(playback_controller.resolver.db)  # ← another new instance
```
`DiscoverService` punya constructor ringan, tapi pola ini tidak extensible. Kalau `DiscoverService` perlu state atau caching, semua call-site harus diubah.

**`_on_download_complete` di `event_listeners.py` — Inline discover payload build**
```python
# Inline duplicate dari _build_discover_payload() di websocket.py:
recent = await ds.get_recent(15)
favorites = await ds.get_favorites(15)
cached = await ds.get_cached(15)
...
await broadcast_service.manager.broadcast({
    "type": "discover_data",
    "data": { "recent": ..., "favorites": ..., ... }
})
```
Ini duplikasi persis dari `_build_discover_payload()` dan `broadcast_discover_data()` di `websocket.py`. Dua tempat harus diupdate kalau struktur `discover_data` berubah.

**`ws_handler` function signature tidak extensible**
```python
async def _handle_search(data, ws, client_ip, state, ytdlp, manager, db):
```
Setiap handler menerima 7 parameter posisional. Menambah dependency (misal: `discover_service`) berarti mengubah signature semua ~25 handler sekaligus. Lebih baik: inject sebagai context object atau gunakan request-local context.

---

## 6. COUPLING

### Kekuatan
- `PlaybackController` tidak langsung import dari `server/` — komunikasi melalui EventBus.
- `MpvController` menerima `EventBus` via DI (dengan fallback ke global `bus`).
- `RadioMode` menggunakan `TYPE_CHECKING` untuk menghindari circular import dengan `PlaybackController`.

### Masalah

**3 Global Singleton — Testing nightmare**
```python
# core/event_bus.py
bus = EventBus()

# core/command_bus.py
command_bus = CommandBus()

# core/log_config.py
STATS = _Stats()
```
Ketiga singleton ini diimport langsung dari banyak file. Dalam test, harus di-patch secara eksplisit. `bus` dan `command_bus` diimport global ke `MpvController`, `SponsorBlockHandler`, `LyricsFetcher`, `DownloadManager`, `CommandRouter`, `websocket.py` — total 15+ import sites.

**`config.py` punya side effects saat import**
```python
# Dieksekusi saat `import config`:
socket_dir.mkdir(parents=True, exist_ok=True)  # filesystem write
with open(_password_file, "r") as f:           # file read
    ADMIN_PASSWORD = f.read().strip()
print(f"PASSWORD ADMIN GENERATED: {raw_password}")  # stdout
```
Setiap module yang melakukan `from config import DB_PATH` berpotensi memicu side effects ini. Ini membuat unit testing menjadi sulit — file system dan stdout bisa terpengaruh hanya karena melakukan import.

**`PlaybackController` terikat ke `CacheResolver` (bukan port)**
```python
class PlaybackController:
    def __init__(self, ..., resolver: CacheResolver, ...):
```
`resolver` adalah concrete class, bukan Protocol. Ini berbeda dari pattern yang digunakan untuk `mpv` (melalui `AudioPlayerPort`) dan `db` (melalui `DatabasePort`). Akibatnya:
```python
# Di engine/playback/controller.py:
safe_create_task(self.resolver.db.upsert_track(track), ...)
```
Controller langsung akses `resolver.db` — menembus abstraksi dua level.

**`DiscoverService` import `aiosqlite` langsung (tidak butuh)**
```python
# services/discover_service.py
import aiosqlite  # ← tidak digunakan! hanya Database yang digunakan
from cache.db import Database
```
`aiosqlite` tidak dipanggil di `discover_service.py` — semua akses DB melalui `Database` yang di-inject. Ini adalah unused import yang juga menambah coupling.

---

## 7. COHESION

### `Database` class — Low cohesion, 5 domain dalam 1 class

Seperti disebutkan di Modularity: satu class melayani track cache, session auth, artist catalog, genre catalog, dan lifecycle. Cohesion rendah karena method-method ini tidak saling berkaitan secara logis — mereka hanya kebetulan mengakses database yang sama.

**Dampak konkret**: `core/ports.py` sudah mendefinisikan `TrackRepositoryPort` dan `SessionRepositoryPort` sebagai protocol terpisah, tapi implementasinya masih satu class. Artist dan Genre tidak punya port sama sekali — mereka "invisible" dari sudut pandang dependency contract.

### `event_listeners.py` — Ambiguous ownership

```python
async def _on_download_complete(event: DownloadCompleteEvent):
    await broadcast_service.broadcast_state(playback_controller.state)
    # DB upsert (state mutation)
    safe_create_task(playback_controller.resolver.db.upsert_track(...), ...)
    # Discover broadcast (duplicate logic)
    ds = DiscoverService(playback_controller.resolver.db)
    ...
    await broadcast_service.manager.broadcast({...})  # bypass BroadcastService interface
```
Satu event listener melakukan 3 hal berbeda: broadcast state, mutate DB, dan broadcast discover data (dengan bypass `BroadcastService` interface untuk memanggil `manager.broadcast` langsung). Ini menunjukkan cohesion yang rendah dalam satu fungsi.

### `log_config.py` — Multiple unrelated concerns (lihat Modularity)

### JS `audio.js` (293 baris) — High cohesion ✓
File ini fokus: semua tentang browser audio element management. Ini contoh cohesion yang baik di JS layer.

### JS `events/player-events.js` (425 baris) — Low cohesion

Satu file menangani: playback controls, progress bar, mode switching, output switching, search header collapse, action modal, radio controls. Ini adalah UI event handler yang tidak fokus.

---

## 8. TECHNICAL DEBT

### Debt Kategori A — Structural (sulit refactor nanti)

| Item | Lokasi | Dampak |
|---|---|---|
| `config.py` side effects saat import | `config.py` baris 13, 54-73 | Unit test semua module yang import config menjadi unpredictable |
| `Database` God Class | `cache/db.py` | Setiap tambahan domain baru makin membesar; tidak ada batas alami |
| Global singleton tanpa DI | `core/event_bus.py`, `core/command_bus.py` | Mock di test harus patch global; integration test tidak bisa isolate |
| `CacheResolver` exposed via `resolver.db` | `engine/playback/controller.py:60` | 2-level abstraction breach |
| `services/` di root (misplace) | `services/discover_service.py` | Bingung saat navigasi direktori |

### Debt Kategori B — Code Quality (lebih mudah fix)

| Item | Lokasi | Dampak |
|---|---|---|
| "Archaeological comments" `PATCHLOG_APPLIED` | 10 file | Noise untuk pembaca baru |
| Bilingual naming (ID + EN) | `cache/db.py`, `radio_engine.py`, log messages | Konsistensi komunikasi, i18n |
| Inline `asyncio` import di `ConnectionManager.__init__` | `server/handlers/websocket.py:33` | Minor inconsistency |
| `discover_data` logic duplikat | `websocket.py` + `event_listeners.py` | Bug harus difix di dua tempat |
| `import aiosqlite` unused di `discover_service.py` | `services/discover_service.py:7` | Dead import |
| `safe_create_task` re-import di method | `engine/playback/controller.py:251` | Duplicate import |
| `_LOG_STATS` as private alias | `engine/playback/controller.py:24` | Confusing name convention |

### Debt Kategori C — JS Layer

| Item | Lokasi | Dampak |
|---|---|---|
| 93 `typeof` guards | JS semua files | Symptom dari tidak ada module system |
| 68 inline `style=` di `index.html` | `web/static/index.html` | Style harus dikelola di dua tempat |
| No JS module system (`import`/`require`) | Semua JS | Scale bottleneck; naming collision risk |
| Hardcoded iTunes API URL | `web/static/js/utils.js:92` | Config harusnya di satu tempat |
| 21 `console.log` di production JS | Semua JS files | Log noise di browser devtools |

---

## 9. REFACTORING PRIORITY

### TIER 1 — Impact Tinggi, Risiko Rendah (lakukan sekarang)

**R-01: Pindahkan `discover_service.py` ke `server/services/`**
- Perubahan: satu `mv` + update 2 import sites
- Risiko: sangat rendah
- Gain: struktur direktori konsisten

**R-02: Deduplikasi `discover_data` broadcast**
- Buat satu fungsi `build_and_broadcast_discover(manager, db)` di `broadcast_service.py`
- Hapus duplicate logic di `event_listeners.py` dan `websocket.py`
- Risiko: rendah
- Gain: bug fix di satu tempat, bukan dua

**R-03: Hapus dead import dan PATCHLOG noise**
- Hapus `import aiosqlite` dari `discover_service.py`
- Hapus `# PATCHLOG_APPLIED` dari 10 file (sudah irrelevant)
- Ubah archaeological comments menjadi komentar ringkas (atau hapus)
- Risiko: nol
- Gain: readability langsung lebih bersih

**R-04: Pindahkan inline imports ke top-level**
- `import asyncio` di `ConnectionManager.__init__` dan `broadcast()`
- `import os` di `_handle_delete_download`
- `from core.task_utils import safe_create_task` di `_on_radio_randomize` (sudah ada di atas!)
- Risiko: nol
- Gain: consistency

### TIER 2 — Impact Tinggi, Risiko Medium (rencanakan dengan test)

**R-05: Split `core/log_config.py` menjadi 3 file**
```
core/log_config.py      → hanya setup_logging() + _CompactRenderer + _FileFormatter
core/stats.py           → _Stats class + STATS singleton
core/terminal_ui.py     → _status_bar_worker, start_status_bar, Spinner, _summary_worker
```
- Risiko: medium (ada import `STATS` dari log_config di beberapa file)
- Gain: log_config.py jadi 80 baris, mudah dibaca

**R-06: Inject `DiscoverService` sebagai dependency**
```python
# server/app.py
discover_service = DiscoverService(db)
app["discover_service"] = discover_service

# handler terima via request.app["discover_service"]
```
- Risiko: medium (perlu update semua handler signature atau pakai context object)
- Gain: testable, no duplicate instantiation

**R-07: Pisahkan `Database` God Class menjadi 3**
```
cache/track_repository.py     → TrackRepository (track cache methods)
cache/session_repository.py   → SessionRepository (auth sessions)
cache/catalog_repository.py   → CatalogRepository (artists, songs, genres)
cache/db.py                   → Database = komposisi ketiga di atas + lifecycle
```
- Risiko: medium-high (banyak import site yang bergantung `from cache.db import Database`)
- Gain: setiap repository punya cohesion tinggi, mudah test, sesuai ports yang sudah ada

**R-08: Eliminasi side effects di `config.py`**
```python
# config.py: hanya define konstanta dan env reads
DB_PATH = BASE_DIR / "data" / "ytgui.db"
MPV_SOCKET = _compute_socket_path()  # pure function

# Pindahkan password setup ke: core/startup.py
async def ensure_admin_password() -> str:
    ...  # file I/O, print, dll — dijalankan di main.py, bukan saat import
```
- Risiko: medium (perlu ubah `main.py` dan `start.py`)
- Gain: `import config` jadi safe untuk test; semua side effects explicit

### TIER 3 — Impact Jangka Panjang, Risiko Tinggi (sprint tersendiri)

**R-09: JS Module System**
- Tambahkan `type="module"` ke script tags, atau gunakan bundler (esbuild/vite)
- Hilangkan 93 `typeof` guards
- Risiko: tinggi (breaking change pada load order; perlu test semua browser target termasuk mobile)
- Gain: refactor JS jadi jauh lebih mudah; eliminasi naming collision risk

**R-10: Extract `CacheResolverPort` Protocol**
```python
# core/ports.py
class CacheResolverPort(Protocol):
    async def resolve(self, track: TrackInfo) -> str: ...

# PlaybackController menerima CacheResolverPort, bukan CacheResolver concrete
```
- Hilangkan `resolver.db` access dari `PlaybackController`
- Risiko: medium (perlu refactor controller + test)
- Gain: sesuai port pattern yang sudah konsisten di modul lain

---

## 10. ROADMAP REFACTOR

```
Sprint 0 — Cleanup (no risk, 1-2 jam)
├── R-01  mv discover_service.py → server/services/
├── R-03  Hapus dead imports + PATCHLOG comments
└── R-04  Pindahkan inline imports ke top-level

Sprint 1 — Deduplikasi & Cohesion (3-5 jam)
├── R-02  Sentralisasi discover_data broadcast di BroadcastService
└── R-05  Split log_config.py → log_config + stats + terminal_ui

Sprint 2 — Dependency & Coupling (1 hari, butuh test coverage)
├── R-06  Inject DiscoverService via app context
├── R-07  Split Database → TrackRepository + SessionRepository + CatalogRepository
└── R-08  Pindahkan config.py side effects ke main.py startup

Sprint 3 — Architecture (1-2 hari, risiko tinggi)
├── R-09  JS module system atau bundler
└── R-10  CacheResolverPort protocol + isolasi PlaybackController dari DB

Prioritas absolut jika hanya bisa pilih satu:
→ R-07 (split Database) + R-02 (discover dedup) memberi return terbesar
   terhadap maintainability harian karena keduanya adalah titik terpanas
   yang paling sering diubah.
```

---

## Lampiran: File Hotspot (Paling Sering Perlu Diubah)

| File | Baris | Alasan Hotspot |
|---|---|---|
| `cache/db.py` | 388 | Setiap domain baru tambah method di sini |
| `server/handlers/websocket.py` | 377 | Setiap action WS baru masuk ke sini |
| `core/log_config.py` | 477 | Perubahan UI terminal harus edit file besar |
| `engine/playback/controller.py` | 337 | Core orchestration, sering perlu tambah handler |
| `server/handlers/event_listeners.py` | 91 | Setiap event baru butuh subscriber baru di sini |
| `start.py` | 834 | GUI manager, sulit ditest, monolitik |
