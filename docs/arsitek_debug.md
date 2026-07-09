# LunaWave — Laporan Arsitektur & Regression Bug Audit

> **Tanggal Audit:** 2026-07-08  
> **Role:** Senior Software Architect & Debug Engineer  
> **Status:** Tidak ada kode yang diubah. Laporan ini murni analisis.

---

## 1. Entry Point

| File | Keterangan |
|------|-----------|
| `main.py` | Entry point utama via `asyncio.run(main())` |
| `start.py` | GUI launcher (Tkinter) + headless fallback |
| `gui_manager.py` | Window manager Tkinter yang diimport oleh `start.py` |

`main.py` → `core.bootstrap.build_app_context()` → `server.app.create_app()` → `server.app.run_server()`

---

## 2. Arsitektur Aplikasi

```
┌────────────────────────────────────────────────────┐
│                      main.py                       │
│    asyncio.run(main()) → build_app_context()       │
└────────────┬───────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │  core/bootstrap │  Builds AppContext (DI root)
    └────────┬────────┘
             │
   ┌─────────┼─────────────────────────────┐
   ▼         ▼                             ▼
[EventBus] [CommandBus]          [server/app.py → aiohttp]
   │         │                             │
   │    CommandRouter                 Routes:
   │         │                        GET /
   │    PlaybackCommands              GET /ws   ← WebSocket
   │    QueueCommands                 GET /api/stream/{id}
   │    SettingsCommands              GET /health
   │    RadioCommands                 GET /metrics
   │    VolumeService                 GET /static/*
   │
   ├── engine/playback/controller.py  (PlaybackController)
   │       ├── TrackLoader
   │       ├── CacheResolver
   │       ├── QueueMode
   │       └── RadioMode
   │
   ├── engine/mpv_controller.py       (MPV IPC)
   ├── engine/ytdlp_client.py         (yt-dlp thread pool)
   ├── engine/download_manager.py     (async queue workers)
   │
   ├── cache/db.py                    (SQLite connection pool)
   │       ├── TrackRepository
   │       ├── AuthRepository
   │       └── DiscoverRepository
   │
   ├── plugins/lyrics.py              (lrclib + syncedlyrics)
   └── plugins/sponsorblock.py        (SponsorBlock API)
```

### Layer Komunikasi

- **EventBus** (pub/sub, 1-to-many): domain events antar modul
- **CommandBus** (1-to-1): perintah dari WS handler ke engine
- **WebSocket** (`/ws`): komunikasi real-time client ↔ server
- **HTTP REST**: stream proxy, health, metrics

---

## 3. Dependency Graph Antar Module

```
main.py
  └─ config.py
  └─ core/log_config.py
  └─ core/alerting.py
  └─ core/background_tasks.py ──► core/bootstrap.py (AppContext)
  └─ core/bootstrap.py
       ├─ cache/db.py ──────────► cache/repositories/*
       ├─ cache/resolver.py
       ├─ core/state.py ─────────► core/value_objects.py
       │                          ► core/constants.py
       ├─ core/event_bus.py ─────► core/events.py
       ├─ core/command_bus.py ───► core/commands.py
       ├─ engine/mpv_controller.py ► core/exceptions.py
       ├─ engine/ytdlp_client.py
       ├─ engine/playback/controller.py
       │     └─ engine/playback/track_loader.py
       │     └─ engine/queue_manager.py
       │     └─ engine/radio_engine.py
       ├─ engine/playback/playback_commands.py
       ├─ engine/playback/queue_commands.py
       ├─ engine/playback/settings_commands.py
       ├─ engine/playback/radio_commands.py
       ├─ engine/command_router.py
       ├─ engine/download_manager.py
       ├─ engine/volume_service.py
       ├─ plugins/lyrics.py
       ├─ plugins/sponsorblock.py
       ├─ plugins/notifications.py
       ├─ server/app.py
       │     ├─ server/routes.py
       │     ├─ server/middleware.py
       │     ├─ server/handlers/http.py
       │     ├─ server/handlers/websocket.py
       │     │     ├─ server/handlers/auth.py
       │     │     └─ server/handlers/ws/__init__.py
       │     │           ├─ ws/registry.py
       │     │           ├─ ws/playback_handlers.py
       │     │           ├─ ws/queue_handlers.py
       │     │           ├─ ws/settings_handlers.py
       │     │           ├─ ws/radio_handlers.py
       │     │           ├─ ws/download_handlers.py
       │     │           └─ ws/discover_handlers.py
       │     └─ server/handlers/event_listeners.py
       └─ server/services/broadcast_service.py
       └─ server/services/discover_service.py
       └─ server/services/stream_prefetch.py

start.py ──► gui_manager.py ──► start.py (circular import: DependencyChecker, ServerProcessManager)
```

---

## 4. Flow Aplikasi End-to-End

```
1. User jalankan python main.py
2. setup_logging() + setup_alerting()
3. build_app_context():
   - Buka DB (SQLite WAL, pool 5 conn)
   - Init YtDlpClient (ThreadPoolExecutor 4 workers)
   - Spawn mpv process + connect via Unix socket/TCP
   - Buat aiohttp.ClientSession
   - Buat CacheResolver, SponsorBlockHandler, LyricsFetcher
   - Buat PlaybackController (subscribe ke EventBus)
   - Buat CommandRouter (register semua command ke CommandBus)
   - Buat DownloadManager (3 worker asyncio)
   - create_app() → aiohttp Application + routes
   - setup_event_listeners() → broadcast ke WebSocket

4. start_background_tasks(): connectivity check, DB cleanup/backup

5. run_server(): aiohttp TCPSite listen di host:port

6. Client WS connect → ws_handler():
   - Send initial state
   - Loop terima pesan WS
   - Auth: handle_auth() → manager.authenticated_connections
   - Command: _ws_handlers[action](data, ...) → command_bus.execute()

7. CommandBus → CommandRouter → PlaybackCommands/QueueCommands/etc
   → PlaybackController.play_track()
   → TrackLoader.load_track() → CacheResolver.resolve()
   → mpv.play(uri)
   → EventBus.publish(TrackStartedEvent)
   → BroadcastService.broadcast_state() → ConnectionManager.broadcast() → semua WS client
```

---

## 5. Daftar Lengkap Regression Bug

---

### 🔴 BUG-001 — `AttributeError: 'list' object has no attribute 'popleft'`
**Prioritas:** KRITIS  
**File:** `engine/queue_manager.py:30`, `engine/radio_engine.py:116`  
**Lokasi bug:**
```python
# engine/queue_manager.py:30
track = controller.state.queue.popleft()   # BUG

# engine/radio_engine.py:116
track = self.state.radio_queue.popleft()   # BUG
```
**Penyebab:** Setelah refactor, `state.queue` dan `state.radio_queue` di `core/state.py` diubah dari `deque` menjadi `list` biasa (baris 108–109). Namun `popleft()` hanya ada di `collections.deque`, bukan `list`.  
**Dampak:** **Crash total.** Setiap lagu habis dimainkan → autoplay berikutnya gagal dengan `AttributeError`. Pemutaran Queue dan Radio Mode keduanya mati.  
**Cara perbaiki:** Kembalikan tipe ke `deque` di `core/state.py`:
```python
queue: deque = field(default_factory=deque)
radio_queue: deque = field(default_factory=deque)
```
atau ganti `popleft()` menjadi `pop(0)` di kedua engine.

---

### 🔴 BUG-002 — `NameError: WSAction.SETTINGS_UPDATE` tidak terdefinisi
**Prioritas:** KRITIS  
**File:** `server/handlers/websocket.py:139`  
**Lokasi bug:**
```python
ADMIN_ONLY_ACTIONS = {WSAction.SET_OUTPUT, WSAction.SET_SPONSORBLOCK,
                      WSAction.DELETE_DOWNLOAD, WSAction.STOP, WSAction.SETTINGS_UPDATE}
```
**Penyebab:** `WSAction.SETTINGS_UPDATE` tidak pernah didefinisikan di `core/ws_actions.py`. Atribut ini tampaknya dihapus saat refactor tapi referensinya tertinggal.  
**Dampak:** `AttributeError` saat modul `websocket.py` diimport. **Server tidak bisa start** karena `ws_handler` tidak bisa di-load.  
**Cara perbaiki:** Tambahkan `SETTINGS_UPDATE = "settings_update"` ke class `WSAction`, atau hapus `WSAction.SETTINGS_UPDATE` dari set `ADMIN_ONLY_ACTIONS`.

---

### 🔴 BUG-003 — `NameError: STATIC_DIR` tidak diimport di `server/handlers/http.py`
**Prioritas:** KRITIS  
**File:** `server/handlers/http.py:21`  
**Lokasi bug:**
```python
async def serve_index(request):
    resp = web.FileResponse(STATIC_DIR / "index.html")  # STATIC_DIR tidak diimport!
```
**Penyebab:** `STATIC_DIR` didefinisikan di `server/routes.py` tapi tidak pernah diimport di `server/handlers/http.py`. Setelah refactor routes dipindah ke file terpisah, import tidak diikutkan.  
**Dampak:** `NameError: name 'STATIC_DIR' is not defined` setiap request ke `GET /`. Halaman utama tidak bisa diakses.  
**Cara perbaiki:** Tambahkan import di `http.py`:
```python
from server.routes import STATIC_DIR
```

---

### 🔴 BUG-004 — `AttributeError: 'Database' object has no attribute 'conn'`
**Prioritas:** KRITIS  
**File:** `engine/radio_engine.py:83`, `engine/radio_engine.py:287`  
**Lokasi bug:**
```python
# radio_engine.py:83
if self.db and self.db.conn:
    self._seed_artists = await self.db.get_all_artists()

# radio_engine.py:287
if self.db and self.db.conn:
    tracks = await self.db.get_random_songs(...)
```
**Penyebab:** `self.db.conn` mengacu ke atribut yang hanya ada di `PoolContext` (inner helper class), bukan di `Database`. Class `Database` mempunyai `self.pool`, `self.tracks`, `self.sessions`, `self.discover` — tidak ada `self.conn`.  
**Dampak:** Ekspresi `self.db.conn` selalu `AttributeError` → exception ditangkap → Radio Mode tidak pernah berhasil fetch lagu. **Radio Mode mati total.**  
**Cara perbaiki:** Ganti guard ke:
```python
if self.db and self.db.pool:
```

---

### 🔴 BUG-005 — `AttributeError`: `db.get_recent_tracks()` dan `db.get_favorites()` tidak ada di `Database`
**Prioritas:** KRITIS  
**File:** `server/handlers/event_listeners.py:62-63`  
**Lokasi bug:**
```python
db = playback_controller.resolver.db
recent = await db.get_recent_tracks(20)   # BUG — method tidak ada
favorites = await db.get_favorites()       # BUG — method tidak ada
```
**Penyebab:** Setelah refactor, class `Database` di `cache/db.py` hanya melakukan forwarding untuk method-method tertentu. Method `get_recent_tracks()` dan `get_favorites()` tidak pernah didelegasikan (tidak ada di `cache/db.py`). Method yang benar adalah `db.tracks.get_recent_tracks()` dan `db.tracks.get_favorite_tracks()`.  
**Dampak:** Setiap download selesai → `_on_download_complete` crash → broadcast discover data gagal → UI discover tidak update setelah download.  
**Cara perbaiki:** Tambahkan forwarding di `cache/db.py`:
```python
async def get_recent_tracks(self, limit: int):
    return await self.tracks.get_recent_tracks(limit)

async def get_favorites(self, limit: int = 50):
    return await self.tracks.get_favorite_tracks(limit)
```

---

### 🔴 BUG-006 — `gui_manager.py` menggunakan env var yang salah (`LunaWave_PORT` vs `LUNAWAVE_PORT`)
**Prioritas:** TINGGI  
**File:** `gui_manager.py:16`, `gui_manager.py:259-260`  
**Lokasi bug:**
```python
# gui_manager.py:16
SERVER_PORT = int(os.environ.get("LunaWave_PORT", 8765))  # BUG: case salah

# gui_manager.py:259-260
env["LunaWave_HOST"] = "0.0.0.0"   # BUG
env["LunaWave_PORT"] = str(port)    # BUG
```
**Penyebab:** Setelah refactor env var distandarisasi ke `LUNAWAVE_PORT` / `LUNAWAVE_HOST` (lihat `config.py:30-31`), tapi `gui_manager.py` masih menggunakan nama lama `LunaWave_PORT` dan `LunaWave_HOST`.  
**Dampak:** Server yang di-spawn oleh GUI tidak menerima konfigurasi port/host yang benar dari GUI. Server selalu start di port default (8765), dan perubahan port di GUI field tidak berpengaruh. Port conflict detection juga berpotensi salah.  
**Cara perbaiki:** Update semua referensi di `gui_manager.py` ke `LUNAWAVE_PORT` dan `LUNAWAVE_HOST`.

---

### 🔴 BUG-007 — `gui_manager.check_first_run()` menulis password ke path lama (`cache/`)
**Prioritas:** TINGGI  
**File:** `gui_manager.py:185-196`  
**Lokasi bug:**
```python
# gui_manager.py:185
password_file = BASE_DIR / "cache" / "admin_password.txt"  # BUG: path lama
```
**Penyebab:** Setelah refactor, password file dipindah ke `data/admin_password.txt` (lihat `config.py` dan prosedur migrasi di `config.get_admin_password()`). Namun `check_first_run()` di GUI masih menulis ke path lama.  
**Dampak:** GUI membuat password baru di `cache/admin_password.txt`, tapi `config.py` membaca dari `data/admin_password.txt`. Pada first run via GUI, password yang dibuat GUI tidak akan dibaca oleh server → server auto-generate password baru yang berbeda → login menggunakan password dari GUI **gagal**.  
**Cara perbaiki:** Update `check_first_run()` di `gui_manager.py`:
```python
password_file = BASE_DIR / "data" / "admin_password.txt"
```

---

### 🟠 BUG-008 — Broken WS Handler: `set_mode`, `set_output`, `volume_set` menggunakan string literal, bukan `WSAction`
**Prioritas:** SEDANG  
**File:** `server/handlers/ws/settings_handlers.py:21`, `:27`, `:33`  
**Lokasi bug:**
```python
@register_ws_handler("volume_set")   # Bukan WSAction.VOLUME_SET
@register_ws_handler("set_mode")     # Bukan WSAction.SET_MODE
@register_ws_handler("set_output")   # Bukan WSAction.SET_OUTPUT
```
**Penyebab:** Tiga handler settings di-register menggunakan string hardcoded alih-alih konstanta `WSAction`. Ini mungkin warisan sebelum refactor WSAction constants.  
**Dampak:** Secara fungsional masih bekerja karena nilai string-nya sama dengan nilai di `WSAction`. Tapi ini **dead code smell** dan rentan regression jika nilai `WSAction` diubah — tidak akan ada error saat registrasi, handler diam-diam tidak terpanggil.  
**Cara perbaiki:** Konsistensi dengan handler lain:
```python
@register_ws_handler(WSAction.VOLUME_SET)
@register_ws_handler(WSAction.SET_MODE)
@register_ws_handler(WSAction.SET_OUTPUT)
```

---

### 🟠 BUG-009 — `RadioMode._ensure_artists_loaded()` akses `db.conn` yang tidak ada
**Prioritas:** SEDANG (turunan dari BUG-004, detil berbeda)  
**File:** `engine/radio_engine.py:83`  
**Lokasi bug:**
```python
async def _ensure_artists_loaded(self) -> None:
    if self._seed_artists:
        return
    try:
        if self.db and self.db.conn:   # BUG: db.conn tidak ada di Database
            self._seed_artists = await self.db.get_all_artists()
    except Exception as e:
        logger.warning(...)

    if not self._seed_artists:
        raise RuntimeError("Tabel artists kosong...")
```
**Penyebab:** Kondisi `self.db.conn` selalu raise `AttributeError` (yang kemudian ditangkap oleh `except Exception`), menyebabkan `_seed_artists` tetap kosong, lalu `RuntimeError` selalu dilempar.  
**Dampak:** Radio Mode selalu menampilkan error "Tabel artists kosong" meski database terisi penuh.

---

### 🟠 BUG-010 — `LyricsPlugin`: `search_query` potensial `NameError` pada edge case lrclib
**Prioritas:** SEDANG  
**File:** `plugins/lyrics.py:94-99`  
**Lokasi bug:**
```python
# Outer block (lines 71-91) HANYA dijalankan kalau lrc masih None/empty
# Tapi search_query HANYA di-set di dalam outer block

if not lrc:  # Second check — syncedlyrics fallback
    logger.info(f"syncedlyrics query: {search_query}")   # BUG: jika lrc dari cache
```
**Penyebab:** Jika `track.video_id` ada di `_cache` (baris ~55) dan lrc langsung di-set dari cache, outer `if not lrc` block (baris 71) dilewati sehingga `search_query` tidak pernah di-assign. Jika kemudian lrc dari cache bernilai `None` atau empty string (corrupted cache entry), blok kedua `if not lrc` di baris 94 terpicu dan `search_query` tidak terdefinisi → `NameError`.  
**Dampak:** Edge case: crash saat fetch lyrics untuk lagu dengan corrupted cache entry.  
**Cara perbaiki:** Inisialisasi `search_query = ""` di awal fungsi sebelum blok bersyarat.

---

### 🟠 BUG-011 — `DiscoverService` memanggil method yang tidak ada di `TrackRepository`
**Prioritas:** SEDANG  
**File:** `server/services/discover_service.py:40`, `:50`  
**Lokasi bug:**
```python
# discover_service.py:40
data = await self.track_repo.get_recent_tracks(n)     # OK — ada di TrackRepository

# discover_service.py:50
data = await self.track_repo.get_favorite_tracks(n)   # OK — ada di TrackRepository
```
*Catatan: ini sebenarnya BENAR di `DiscoverService` sendiri. Bug terjadi di BUG-005 (event_listeners) yang memanggil `db.get_favorites()` tanpa forwarding.*

---

### 🟠 BUG-012 — `engine/radio_engine.py` menggunakan `state.radio_queue` sebagai `deque` tapi ini `list`
**Prioritas:** TINGGI (turunan BUG-001, different context)  
**File:** `engine/radio_engine.py:116`, `engine/radio_engine.py:119`  
**Lokasi bug:**
```python
track = self.state.radio_queue.popleft()   # AttributeError: list has no popleft
if len(self.state.radio_queue) <= 5:
    ...
```
**Dampak:** Sama dengan BUG-001 — identik untuk Radio Mode.

---

### 🟡 BUG-013 — `gui_manager.py` circular import dengan `start.py`
**Prioritas:** RENDAH-SEDANG  
**File:** `gui_manager.py:9-10`  
**Lokasi bug:**
```python
from start import DependencyChecker, ServerProcessManager
```
**Penyebab:** `gui_manager.py` mengimport dari `start.py`, dan `start.py` mengimport dari `gui_manager.py` (`from gui_manager import ServerManagerWindow`). Ini circular import.  
**Dampak:** Tidak crash dalam kondisi normal karena `start.py` hanya mengimport `gui_manager` di dalam blok `if __name__ == "__main__"` (runtime, bukan top-level). Namun jika ada test atau tooling yang mengimport keduanya, `ImportError` bisa terjadi.  
**Cara perbaiki:** Ekstrak `DependencyChecker` dan `ServerProcessManager` ke file terpisah (`core/server_utils.py` atau serupa).

---

### 🟡 BUG-014 — `core/background_tasks.py` mengimport `AppContext` dari `core/bootstrap.py` (potential circular import)
**Prioritas:** RENDAH-SEDANG  
**File:** `core/background_tasks.py:7`  
**Lokasi bug:**
```python
from core.bootstrap import AppContext
```
**Penyebab:** `core/bootstrap.py` mengimport banyak modul engine dan server. `core/background_tasks.py` diimport dari `core/bootstrap.py` via `start_background_tasks()`. Selama Python belum mengeksekusi semua import di `bootstrap.py` saat `background_tasks.py` di-load, ini bisa menyebabkan circular import.  
**Dampak:** Tidak crash di runtime normal karena import dilakukan secara bertahap. Tapi rentan jika urutan import berubah.

---

### 🟡 BUG-015 — `serve_metrics` menggunakan `content_type` dengan cara yang salah
**Prioritas:** RENDAH  
**File:** `server/handlers/http.py`  
**Lokasi bug:**
```python
content, content_type = get_metrics_content()
ct = content_type.split(";")[0].strip()
return web.Response(body=content, content_type=ct)
```
**Penyebab:** `generate_latest()` dari `prometheus_client` mengembalikan bytes. `web.Response(body=content, content_type=ct)` di aiohttp: jika `body` adalah bytes dan `content_type` sudah terstripped, parameter `charset` hilang dan bisa menyebabkan response tanpa charset untuk format text-based Prometheus.  
**Dampak:** Minor — Prometheus scraper mungkin masih parse dengan benar karena format valid, tapi bisa menyebabkan warning/issue pada beberapa scraper yang strict.

---

### 🟡 BUG-016 — `RadioMode._gather_batch()` akses `db.conn` yang tidak ada (lagi)
**Prioritas:** TINGGI (turunan BUG-004)  
**File:** `engine/radio_engine.py:287`  
**Lokasi bug:**
```python
async def _gather_batch(self, ...) -> list:
    ...
    if self.db and self.db.conn:   # BUG
        try:
            tracks = await self.db.get_random_songs(...)
```
**Dampak:** Identik BUG-004 — batch gathering untuk Radio Mode selalu gagal dengan silent exception.

---

### 🟡 BUG-017 — Dead Code: `WSAction.SETTINGS_UPDATE` direferensikan tapi tidak pernah ada handler-nya
**Prioritas:** RENDAH  
**File:** `server/handlers/websocket.py:139`, `core/ws_actions.py`  
**Dampak:** Kalau `SETTINGS_UPDATE` ditambahkan ke `WSAction`, tidak ada WS handler yang terdaftar untuk action tersebut. Client yang mengirim `settings_update` akan mendapat warning "Unknown WS action". Dead code.

---

### 🟡 BUG-018 — `VolumeService._on_volume_up/down` membatasi volume hingga 100, padahal `MAX_VOLUME = 150`
**Prioritas:** RENDAH  
**File:** `engine/volume_service.py:17`, `:22`  
**Lokasi bug:**
```python
async def _on_volume_up(self, cmd=None):
    async with self._lock:
        new_vol = min(100, self.state.volume + 5)   # BUG: hardcoded 100, bukan MAX_VOLUME

async def _on_volume_down(self, cmd=None):
    async with self._lock:
        new_vol = max(0, self.state.volume - 5)    # OK
```
**Penyebab:** `MAX_VOLUME` di `core/constants.py` adalah 150, tapi `volume_up` hardcode batas atas ke 100. Ini berbeda dengan `VolumeSetCommand` yang menggunakan range 0-150.  
**Dampak:** User tidak bisa naik volume di atas 100% lewat tombol volume up, meski slider bisa ke 150%.

---

### 🟡 BUG-019 — `gui_manager.ServerManagerController.check_first_run()` memvalidasi path lama
**Prioritas:** SEDANG (turunan BUG-007, kasus berbeda)  
**Penjelasan:** Pada `on_reset_password()` (baris 357), path sudah benar ke `data/`. Tapi pada `check_first_run()` (baris 185), path masih ke `cache/`. Inkonsistensi ini bisa menyebabkan dua file password berbeda existsimultan.

---

### 🟡 BUG-020 — `core/cli_ui.start_ui_threads()` tidak pernah dipanggil dari `main.py`
**Prioritas:** RENDAH  
**File:** `core/cli_ui.py`, `main.py`  
**Penyebab:** `start_ui_threads()` didefinisikan di `core/cli_ui.py` namun tidak ada pemanggilan di `main.py` atau `core/bootstrap.py`.  
**Dampak:** Status bar CLI dan summary thread tidak pernah berjalan. `STATS` object di `cli_ui.py` tetap di-update (dari tempat lain seperti `websocket.py`), tapi UI bar tidak tampil.

---

### 🟡 BUG-021 — `mpv_controller._observe_events()` memanggil `_mpv_process.wait(timeout=1)` secara sinkron
**Prioritas:** SEDANG  
**File:** `engine/mpv_controller.py` (dalam `_observe_events`)  
**Lokasi bug:**
```python
try:
    self._mpv_process.wait(timeout=1)   # BUG: blocking call di async context
except Exception:
    pass
```
**Penyebab:** `subprocess.Popen.wait(timeout=1)` adalah blocking call. Ini dipanggil dari dalam coroutine async sehingga **mem-block event loop** selama 1 detik saat reconnect.  
**Dampak:** Lag/freeze semua WebSocket connection selama 1 detik pada setiap reconnect MPV.  
**Cara perbaiki:** Gunakan `await asyncio.wait_for(self._mpv_process.wait(), timeout=1.0)` (async subprocess wait).

---

### 🟡 BUG-022 — `DiscoverService.__init__` menggunakan class-level import yang tidak valid
**Prioritas:** RENDAH  
**File:** `server/services/discover_service.py:24`  
**Lokasi bug:**
```python
class DiscoverService:
    from core.ports import DatabasePort   # Class-level import — unusual pattern
    def __init__(self, track_repo: DatabasePort, discover_repo: DatabasePort):
```
**Penyebab:** Import di level class body berfungsi tapi menempatkan `DatabasePort` sebagai class attribute, bukan module-level import. Tidak crash, tapi tidak idiomatik dan confusing bagi tooling (linter, type checker).

---

### 🟡 BUG-023 — `_discover_service_instance` global di `discover_handlers.py` tidak thread-safe
**Prioritas:** RENDAH  
**File:** `server/handlers/ws/discover_handlers.py`  
**Lokasi bug:**
```python
_discover_service_instance = None

async def _build_discover_payload(db):
    global _discover_service_instance
    if _discover_service_instance is None:
        ...
        _discover_service_instance = DiscoverService(track_repo, discover_repo)
```
**Penyebab:** Race condition: dua concurrent WS calls ke `DISCOVER` action bisa sama-sama melihat `_discover_service_instance = None` dan membuat dua instance berbeda. Dalam asyncio single-thread ini aman selama tidak ada `await` antara check dan assignment — dan memang tidak ada. Namun pola ini tetap fragile.

---

### 🟡 BUG-024 — `server/handlers/http.py` menggunakan `collections` yang diimport tapi tidak dipakai
**Prioritas:** RENDAH (dead import)  
**File:** `server/handlers/http.py:4`  
**Lokasi bug:**
```python
import collections   # Tidak dipakai sama sekali
```
**Dampak:** Dead import. Tidak fungsional, tapi menandakan refactor yang tidak bersih.

---

## 6. Ringkasan Prioritas

| ID | Prioritas | Komponen | Dampak |
|----|-----------|----------|--------|
| BUG-001 | 🔴 KRITIS | `engine/queue_manager.py`, `radio_engine.py` | Autoplay mati, crash setiap track selesai |
| BUG-002 | 🔴 KRITIS | `server/handlers/websocket.py` | Server tidak bisa start |
| BUG-003 | 🔴 KRITIS | `server/handlers/http.py` | Halaman utama (`/`) error 500 |
| BUG-004 | 🔴 KRITIS | `engine/radio_engine.py` | Radio Mode mati total |
| BUG-005 | 🔴 KRITIS | `server/handlers/event_listeners.py` | Crash setelah download, discover tidak update |
| BUG-006 | 🟠 TINGGI | `gui_manager.py` | Port config dari GUI tidak berlaku ke server |
| BUG-007 | 🟠 TINGGI | `gui_manager.py` | First-run password GUI tidak cocok dengan server |
| BUG-008 | 🟠 SEDANG | `ws/settings_handlers.py` | Tidak crash tapi rentan jika WSAction berubah |
| BUG-009 | 🟠 SEDANG | `engine/radio_engine.py` | Radio gagal load artists (turunan BUG-004) |
| BUG-010 | 🟠 SEDANG | `plugins/lyrics.py` | NameError pada edge case corrupted lyrics cache |
| BUG-012 | 🟠 TINGGI | `engine/radio_engine.py` | Sama dengan BUG-001 di konteks radio |
| BUG-016 | 🟠 TINGGI | `engine/radio_engine.py` | Sama dengan BUG-004 di _gather_batch |
| BUG-021 | 🟡 SEDANG | `engine/mpv_controller.py` | Blocking event loop 1 detik saat reconnect |
| BUG-018 | 🟡 RENDAH | `engine/volume_service.py` | Volume up batas 100 bukan 150 |
| BUG-013 | 🟡 RENDAH | `gui_manager.py` / `start.py` | Circular import (latent) |
| BUG-019 | 🟡 SEDANG | `gui_manager.py` | Dua password file bisa konflik |
| BUG-020 | 🟡 RENDAH | `core/cli_ui.py` | Status bar CLI tidak jalan |
| BUG-022 | 🟡 RENDAH | `server/services/discover_service.py` | Class-level import unusual |
| BUG-023 | 🟡 RENDAH | `server/handlers/ws/discover_handlers.py` | Global state fragile |
| BUG-024 | 🟡 RENDAH | `server/handlers/http.py` | Dead import |

---

## 7. Urutan Perbaikan yang Disarankan

1. **BUG-002** — Fix dulu `WSAction.SETTINGS_UPDATE`, karena kalau server tidak bisa start, bug lain tidak bisa ditest.
2. **BUG-003** — Fix `STATIC_DIR` import di `http.py` agar halaman utama bisa diakses.
3. **BUG-001 + BUG-012** — Fix `list` → `deque` atau ganti `popleft()` agar autoplay bekerja.
4. **BUG-004 + BUG-009 + BUG-016** — Fix `db.conn` → `db.pool` agar Radio Mode berfungsi.
5. **BUG-005** — Tambah forwarding method `get_recent_tracks` dan `get_favorites` di `Database`.
6. **BUG-006 + BUG-007 + BUG-019** — Fix GUI env var naming dan path password.
7. **BUG-008** — Konsistensi `WSAction` di settings handlers.
8. **BUG-010** — Init `search_query = ""` di lyrics plugin.
9. **BUG-021** — Fix blocking `wait()` di mpv reconnect.
10. Sisanya: code quality issues (BUG-013, 018, 020, 022, 023, 024).

---

*Laporan ini dihasilkan dari analisis statis 100% tanpa menjalankan kode dan tanpa mengubah satu baris pun.*
