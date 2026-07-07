# AUDIT ARSITEKTUR — LunaWave
**Tim Audit:** Senior Software Architect · Principal Backend Engineer · Senior Frontend Engineer · DevOps Engineer · QA Lead · Security Engineer · Performance Engineer · Database Architect · UI/UX Expert · Product Engineer

---

## EXECUTIVE SUMMARY

LunaWave memiliki fondasi arsitektur yang **cukup solid** untuk proyek personal/portofolio — Port-based layering, EventBus/CommandBus yang benar, dan Repository Pattern sudah diterapkan. Namun terdapat **19 temuan signifikan** yang akan menjadi bom waktu sebelum production release ke jutaan user: dari bug kritis (KeyError di DiscoverService, `run.py` tidak ada di Dockerfile), hingga architectural debt berat (DiscoverService menduplikasi seluruh query DiscoverRepository, 60+ global variable di frontend, ITUNES_API_URL tidak terdefinisi).

---

## PART 1 — PETA ARSITEKTUR AKTUAL

### 1.1 Folder Structure

```
lunawave-main/
├── config.py               ← Konfigurasi global + side effect (mkdir, file I/O)
├── main.py                 ← Entry point async
├── start.py                ← 31K baris: launcher monolith (platform detection, setup)
├── core/                   ← Domain core (commands, events, state, ports)
├── engine/                 ← Business logic (playback, radio, download, mpv)
│   └── playback/           ← Command handlers dipecah per domain
├── cache/                  ← Persistence layer (DB + repositories)
│   └── repositories/       ← TrackRepo, AuthRepo, DiscoverRepo
├── server/                 ← HTTP/WS layer (aiohttp)
│   ├── handlers/           ← HTTP handlers + WS handlers
│   │   └── ws/             ← WS action handlers per domain
│   └── services/           ← BroadcastService, DiscoverService, PrefetchService
├── plugins/                ← Lyrics, SponsorBlock, Notifications (Termux)
├── data/                   ← Artists JSON + export script
├── web/static/             ← Frontend (vanilla JS, ~60 global vars)
│   ├── js/                 ← Source modules (non-ESM, global namespace)
│   └── css/                ← Terstruktur per komponen/layout/platform
└── tests/                  ← Unit + integration tests
```

**Nilai Positif:**
- Pemisahan `core/`, `engine/`, `cache/`, `server/`, `plugins/` cukup clear
- CSS sudah distrukturisasi per komponen dan platform
- WS handlers dipecah per domain (`playback_handlers`, `queue_handlers`, dll.)

---

## PART 2 — TEMUAN AUDIT

---

### TEMUAN A-01 — CRITICAL BUG
**`KeyError: 'stream_url'` di DiscoverService — Crash pada Runtime**

| | |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | Endpoint `/discover` crash setiap dipanggil → seluruh tab Discover tidak berfungsi |
| **Penyebab** | `DiscoverService` membuat `TrackInfo(stream_url=d["stream_url"], ...)` tapi kolom `stream_url` **tidak di-SELECT** |
| **File** | `server/services/discover_service.py` baris 36, 63, 90 |

```python
# BUGGY — SELECT tidak termasuk stream_url
async with self.db.conn.execute(
    "SELECT video_id, title, artist, duration, thumbnail, local_path, "
    "view_count, play_count, is_favorite FROM tracks ..."
) as cursor:
    async for row in cursor:
        d = dict(row)
        tracks.append(TrackInfo(
            ...
            stream_url=d["stream_url"],  # ← KeyError! Kolom tidak di-SELECT
        ))
```

**Solusi:**
```python
# FIXED — tambahkan stream_url ke SELECT
async with self.db.conn.execute(
    "SELECT video_id, title, artist, duration, thumbnail, local_path, "
    "stream_url, view_count, play_count, is_favorite FROM tracks ..."
) as cursor:
    async for row in cursor:
        d = dict(row)
        tracks.append(TrackInfo(
            ...
            stream_url=d.get("stream_url"),  # ← gunakan .get() untuk safety
        ))
```

---

### TEMUAN A-02 — CRITICAL BUG
**Dockerfile `CMD ["python", "run.py"]` — File Tidak Exist**

| | |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | Container Docker **tidak bisa start sama sekali**. `python run.py` → `FileNotFoundError` |
| **Penyebab** | Entry point yang benar adalah `main.py`, bukan `run.py` |
| **File** | `Dockerfile` baris 28 |

```dockerfile
# BUGGY
CMD ["python", "run.py"]
```

**Solusi:**
```dockerfile
# FIXED
CMD ["python", "main.py"]
```

---

### TEMUAN A-03 — CRITICAL BUG
**`ITUNES_API_URL` Tidak Terdefinisi — ReferenceError di Browser**

| | |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | Seluruh fungsi `getCoverArt()` crash → tidak ada artwork yang tampil di UI. Console error pada setiap track |
| **Penyebab** | `utils.js` menggunakan `ITUNES_API_URL` sebagai konstanta global tapi **tidak pernah didefinisikan** di manapun dalam codebase (tidak di `index.html`, tidak di `config.js`) |
| **File** | `web/static/js/utils.js` baris ~70 |

```javascript
// BUGGY — ITUNES_API_URL undefined, ReferenceError
const response = await fetch(`${ITUNES_API_URL}?term=${query}&media=music&limit=1`);
```

**Solusi:**
```javascript
// FIXED — tambahkan di config.js atau index.html sebelum bundle.js
// config.js:
const TABS = ["home", "search", "radio", "discover"];
const ITUNES_API_URL = "https://itunes.apple.com/search"; // ← tambahkan ini
```

---

### TEMUAN A-04 — CRITICAL
**`audio.js` menggunakan `export` tapi file dimuat sebagai classic script**

| | |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | `export async function _resumeAndPlay(audio)` menyebabkan SyntaxError di browser jika dimuat tanpa `type="module"`. File lain yang memanggil `_resumeAndPlay()` dari global scope tidak bisa mengaksesnya |
| **Penyebab** | `audio.js` menggunakan ES Module `export` syntax tapi seluruh arsitektur frontend adalah classic script (global namespace) |
| **File** | `web/static/js/audio.js` baris 128 |

```javascript
// BUGGY — ES module export di non-module context
export async function _resumeAndPlay(audio) {
```

**Solusi:**
```javascript
// FIXED — hapus export, jadikan global (konsisten dengan arsitektur saat ini)
async function _resumeAndPlay(audio) {
```

---

### TEMUAN A-05 — HIGH
**Dependency Version Mismatch: `aiosqlite`**

| | |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Instalasi dari `requirements.txt` menggunakan `0.20.0`, dari `pyproject.toml` menggunakan `0.22.1`. Developer berbeda mungkin mendapat versi berbeda, menyebabkan API incompatibility |
| **Penyebab** | `requirements.txt` dan `pyproject.toml` tidak sinkron |
| **File** | `requirements.txt` baris 2, `pyproject.toml` baris 8 |

```
# requirements.txt
aiosqlite==0.20.0   ← LAMA

# pyproject.toml
"aiosqlite==0.22.1" ← BARU
```

**Solusi:** Gunakan **satu sumber kebenaran**. Hapus `requirements.txt` dan generate dari pyproject:
```bash
pip-compile pyproject.toml -o requirements.txt
# atau sync manual:
# requirements.txt → aiosqlite==0.22.1
```

---

### TEMUAN A-06 — HIGH
**`DiscoverService` Menduplikasi Seluruh Logic `DiscoverRepository` — 132 Baris Dead Code**

| | |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | DRY violation berat. Bug fix di satu tempat tidak otomatis fix di tempat lain. `DiscoverService.get_recent()` dan `DiscoverRepository.get_recent()` (via `TrackRepository`) overlap total |
| **Penyebab** | `DiscoverService` membuka koneksi DB sendiri (`self.db.conn.execute(...)`) alih-alih mendelegasikan ke Repository |
| **File** | `server/services/discover_service.py` (132 baris), `cache/repositories/discover_repository.py` |

```python
# BUGGY — DiscoverService punya SQL query sendiri yang sama dengan Repository
class DiscoverService:
    async def get_recent(self, n: int) -> list[TrackInfo]:
        async with self.db.conn.execute(  # Langsung ke DB, bypass Repository
            "SELECT ... FROM tracks ORDER BY last_played DESC LIMIT ?"
        ) ...

# DiscoverRepository JUGA punya get_recent() via Database proxy
# Dua tempat, query identik, tapi DiscoverService tidak pernah pakai Repository!
```

**Solusi — Hapus `DiscoverService`, routing langsung ke Repository:**
```python
# discover_handlers.py — gunakan db langsung via proxy
async def _build_discover_payload(db):
    recent   = await db.get_recent(DISCOVER_RECENT_LIMIT)        # db.discover.get_recent()
    favorites= await db.get_favorites(DISCOVER_FAVORITES_LIMIT)  # via __getattr__ proxy
    cached   = await db.get_cached(DISCOVER_CACHED_LIMIT)
    featured_artists = await db.get_featured_artists(DISCOVER_FEATURED_ARTISTS_LIMIT)
    featured_genres  = await db.get_featured_genres(DISCOVER_FEATURED_GENRES_LIMIT)
    # DiscoverService tidak perlu ada sama sekali
```

Perlu menambahkan `get_recent()`, `get_favorites()`, `get_cached()` ke `DiscoverRepository` (sudah ada sebagian), lalu expose via `Database.__getattr__` proxy.

---

### TEMUAN A-07 — HIGH
**`AppState` adalah Mutable Shared State Tanpa Lock — Race Condition**

| | |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Multiple concurrent WS commands (dari multi-client) menulis ke `state.queue`, `state.lyrics_lines`, `state.position` secara bersamaan tanpa synchronization. Potensi list corruption |
| **Penyebab** | `AppState` adalah `@dataclass` biasa diakses dari multiple coroutines. Python's GIL melindungi di level bytecode, tapi operasi `deque.append()` + `deque.popleft()` yang berurutan dari coroutine berbeda masih bisa interleave |
| **File** | `core/state.py`, `engine/playback/queue_commands.py` |

```python
# BUGGY — dua WS command concurrent menulis queue tanpa full protection
async def on_queue_add(self, cmd):
    async with self.playback_controller._lock:  # Hanya _lock
        self.state.queue.append(cmd.track)      # Tapi EventBus publish dari luar lock
        await self.bus.publish(QueueUpdatedEvent())
        # Event handler bisa memicu state mutation lagi sebelum lock release
```

**Solusi:** Pastikan semua mutasi `AppState` dilakukan di dalam `_lock` yang sama, termasuk event publish yang bisa memicu write-back ke state.

---

### TEMUAN A-08 — HIGH
**Broadcast State ke Semua Client Termasuk yang Tidak Terautentikasi**

| | |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | `manager.broadcast()` mengirim `state` (termasuk `current_track`, `queue`, `lyrics`) ke **semua WebSocket** yang terhubung, termasuk yang belum login. Informasi tentang lagu yang sedang diputar bocor ke pengunjung anonim |
| **Penyebab** | `ConnectionManager.broadcast()` mengiterasi `active_connections` (semua koneksi), bukan `authenticated_connections` |
| **File** | `server/handlers/websocket.py` baris 49, `server/services/broadcast_service.py` |

```python
# BUGGY — broadcast ke semua, termasuk unauthenticated
async def broadcast(self, message: dict):
    targets = list(self.active_connections)  # SEMUA koneksi!
    results = await asyncio.gather(*(send(ws) for ws in targets))
```

**Solusi — pisahkan state broadcast:**
```python
# FIXED — broadcast hanya ke authenticated, atau buat tier broadcast
async def broadcast_to_authenticated(self, message: dict):
    data = json.dumps(message, ensure_ascii=False)
    targets = list(self.authenticated_connections)
    ...

async def broadcast_to_all(self, message: dict):
    # Hanya untuk pesan public seperti 'now_playing_title'
    data = json.dumps(message, ensure_ascii=False)
    targets = list(self.active_connections)
    ...
```

---

### TEMUAN A-09 — HIGH
**`config.py` Mengeksekusi Side Effects saat Import**

| | |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Import `config` = `mkdir`, file I/O, hash password, write file. Ini melanggar prinsip Clean Architecture — module layer tidak boleh memiliki side effect saat import. Testing menjadi sulit, dan error konfigurasi terjadi di waktu import bukan runtime |
| **Penyebab** | `socket_dir.mkdir(parents=True, exist_ok=True)` dieksekusi di module level |
| **File** | `config.py` baris 10–16 |

```python
# BUGGY — side effect di module level
socket_dir = BASE_DIR / "cache" / "sockets"
socket_dir.mkdir(parents=True, exist_ok=True)  # ← Ini jalan saat `import config`
```

**Solusi:**
```python
# FIXED — pindahkan ke fungsi inisialisasi
def get_socket_path() -> str:
    socket_dir = BASE_DIR / "cache" / "sockets"
    socket_dir.mkdir(parents=True, exist_ok=True)
    ...
    return str(_socket_path)

MPV_SOCKET = None  # Lazy initialization
```

---

### TEMUAN A-10 — MEDIUM
**`del self.state.queue[cmd.index]` — O(n) pada Deque**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Queue 500+ lagu: hapus item di tengah = O(n) operasi. Dengan banyak user concurrent yang sering reorder/remove, bisa jadi bottleneck |
| **Penyebab** | `deque` di Python tidak mendukung O(1) random-access delete. `del deque[index]` = O(n) |
| **File** | `engine/playback/queue_commands.py` baris 14 |

```python
# BUGGY — O(n) delete dari deque
del self.state.queue[cmd.index]
```

**Solusi:** Gunakan `list` untuk queue jika operasi random-access sering, atau implementasikan soft-delete dengan tombstone:
```python
# FIXED — konversi ke list untuk operasi random access
queue_as_list = list(self.state.queue)
queue_as_list.pop(cmd.index)
self.state.queue = deque(queue_as_list)
```

---

### TEMUAN A-11 — MEDIUM
**`Database.__getattr__` Proxy — Silent Failure & Debugging Nightmare**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `db.nonexistent_method()` akan mencoba `db.tracks.nonexistent_method`, lalu `db.sessions.nonexistent_method`, lalu raise `AttributeError`. Stack trace tidak jelas sumbernya, debugging sulit |
| **Penyebab** | Magic `__getattr__` proxy yang memeriksa 3 repository secara berurutan |
| **File** | `cache/db.py` baris 84 |

```python
# PROBLEMATIC — silent chain lookup
def __getattr__(self, name):
    if self.tracks and hasattr(self.tracks, name):
        return getattr(self.tracks, name)
    if self.sessions and hasattr(self.sessions, name):
        return getattr(self.sessions, name)
    if self.discover and hasattr(self.discover, name):
        return getattr(self.discover, name)
    raise AttributeError(...)
```

**Solusi:** Expose metode secara eksplisit, bukan via `__getattr__`:
```python
class Database:
    # Explicit delegation — clear, type-safe, debuggable
    async def get_track(self, video_id: str):
        return await self.tracks.get_track(video_id)
    
    async def create_session(self, token: str, expires_at: int):
        return await self.sessions.create_session(token, expires_at)
    
    async def get_random_songs(self, **kwargs):
        return await self.discover.get_random_songs(**kwargs)
    # dst...
```

---

### TEMUAN A-12 — MEDIUM
**Frontend: 60+ Global Variables — Zero Module System**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Tidak ada encapsulation. Setiap file bisa membaca/menulis `store`, `ws`, `localAudio`, dll. Naming collision tidak terdeteksi sampai runtime. Testing unit tidak bisa dilakukan |
| **Penyebab** | Semua JS dimuat sebagai classic `<script>` tags ke `window` namespace global |
| **File** | `web/static/js/*.js` — 60 identifier global |

```
# Global namespace (partial):
store, ws, wsReconnectTimer, dom, WS_ACTIONS, localAudio, 
audioUnlocked, _unlocking, _lastLoadedVideoId, audioCtx, 
logToastTimer, renderFullStateTimeout, _lazyCoverObserver...
```

**Solusi Bertahap (tanpa breaking change):**
```javascript
// Step 1: Wrap ke IIFE namespace
const LunaWave = (function() {
    const _store = { status: "IDLE", ... };
    const _audio = { instance: null, unlocked: false };
    
    return {
        store: _store,
        audio: _audio,
        wsSend: function(action, data) { ... }
    };
})();

// Step 2: Migrasi ke ESM dengan bundler (esbuild sudah ada di package.json)
// build_js.py sudah ada — extend untuk ESM output
```

---

### TEMUAN A-13 — MEDIUM
**`DiscoverService.get_featured_genres()` Menggunakan `print()` bukan Logger**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Error di produksi tidak masuk ke log file (`logs/app.log`), tidak masuk ke monitoring Prometheus. Silent failure |
| **Penyebab** | `print(f"Error in get_featured_genres: {e}")` alih-alih `logger.error(...)` |
| **File** | `server/services/discover_service.py` baris 121 |

```python
# BUGGY
except Exception as e:
    print(f"Error in get_featured_genres: {e}")  # ← print bukan logger!

# FIXED
except Exception as e:
    logger.error(f"Error in get_featured_genres: {e}", exc_info=True)
```

---

### TEMUAN A-14 — MEDIUM
**`CacheResolver._fetching` Dictionary Tidak Thread-Safe untuk Concurrent Resolve**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Race condition: dua coroutine bisa lolos dari `if track.video_id in self._fetching:` check sebelum salah satunya menulis ke dict, menyebabkan double fetch |
| **Penyebab** | Check dan set pada `_fetching` dict tidak atomic dalam asyncio |
| **File** | `cache/resolver.py` baris 32–38 |

```python
# BUGGY — race window antara check dan set
if track.video_id in self._fetching:
    await self._fetching[track.video_id].wait()
    return await self.resolve(track)
# ← Dua coroutine bisa KEDUANYA lolos dari sini

event = asyncio.Event()
self._fetching[track.video_id] = event  # Satu akan overwrite yang lain
```

**Solusi:**
```python
# FIXED — gunakan asyncio.Lock per video_id dengan defaultdict
from collections import defaultdict

class CacheResolver:
    def __init__(self, db, ytdlp):
        ...
        self._fetch_lock = asyncio.Lock()
        self._fetching: dict[str, asyncio.Event] = {}
    
    async def resolve(self, track: TrackInfo) -> str:
        ...
        async with self._fetch_lock:
            if track.video_id in self._fetching:
                event = self._fetching[track.video_id]
            else:
                event = asyncio.Event()
                self._fetching[track.video_id] = event
                event = None  # flag: we are the fetcher
        
        if event is not None:
            await event.wait()
            return await self.resolve(track)
        # kita yang fetch...
```

---

### TEMUAN A-15 — MEDIUM
**`start.py` adalah Monolith 31K Baris — Maintenance Nightmare**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | File 31K baris sulit di-review, sulit di-test, sulit di-maintain. Bertentangan dengan SRP |
| **Penyebab** | Platform-specific setup code (Windows, Linux, Termux, Docker) digabung dalam satu file |
| **File** | `start.py` |

**Solusi:** Pecah ke `scripts/setup/`:
```
scripts/
├── setup/
│   ├── __init__.py
│   ├── windows.py      # Windows-specific setup
│   ├── termux.py       # Termux/Android setup
│   └── linux.py        # Linux setup
└── start.py            # Thin launcher: detects platform, delegates
```

---

### TEMUAN A-16 — MEDIUM
**`SponsorBlockHandler` dan `LyricsFetcher` Subscribe ke `TrackProgressEvent` — O(n) per Frame**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Setiap progress tick (setiap ~330ms dari MPV) memanggil `_on_progress` di dua plugin. Jika ada banyak segment SponsorBlock, inner loop bisa berat |
| **Penyebab** | Plugin langsung subscribe ke event progress yang high-frequency |
| **File** | `plugins/sponsorblock.py` baris 19, `plugins/lyrics.py` baris 22 |

```python
# Setiap 330ms, dua handler ini dipanggil:
async def _on_progress(self, event: TrackProgressEvent):
    for start, end in self.segments:  # O(n) loop di setiap tick!
        if start <= current_pos < end:
            await self.mpv.seek(end)
```

**Solusi:** Sort segments dan gunakan binary search, atau pre-compute next_segment saat fetch:
```python
import bisect

async def _on_progress(self, event: TrackProgressEvent):
    pos = event.position
    # Binary search, O(log n) bukan O(n)
    i = bisect.bisect_right(self._segment_starts, pos) - 1
    if i >= 0 and pos < self._segment_ends[i]:
        await self.mpv.seek(self._segment_ends[i])
```

---

### TEMUAN A-17 — LOW
**`TrackInfo` di `state.py` Memiliki `is_favorite: Optional[int] = 0` — Tipe Inconsistent**

| | |
|---|---|
| **Severity** | 🟢 LOW |
| **Dampak** | `is_favorite` kadang `int` (0/1), kadang `bool`. `to_dict()` menggunakan `bool(self.is_favorite)` tapi field adalah `Optional[int]`. Inconsistency menyebabkan bug subtle saat serialisasi |
| **File** | `core/state.py` baris 35, 52 |

```python
# INCONSISTENT
is_favorite: Optional[int] = 0   # field adalah int
"is_favorite": bool(getattr(self, "is_favorite", 0))  # to_dict() konversi ke bool
```

**Solusi:** Pilih satu tipe dan konsisten:
```python
is_favorite: bool = False  # Gunakan bool, konsisten dengan to_dict()
```

---

### TEMUAN A-18 — LOW
**`EventBus.subscribe()` Menggunakan `weakref` untuk Method tapi Tidak untuk Lambda/Closure**

| | |
|---|---|
| **Severity** | 🟢 LOW |
| **Dampak** | Jika handler adalah lambda atau nested function (bukan bound method), `weakref` tidak digunakan. Lambda/closure yang tidak di-reference di luar akan ter-GC, menyebabkan silent unsubscribe |
| **File** | `core/event_bus.py` baris 17–20 |

```python
def subscribe(self, event_type, handler):
    if inspect.ismethod(handler):
        ref = weakref.WeakMethod(handler)  # OK untuk bound method
    else:
        ref = handler  # Lambda/closure: strong reference, tidak akan GC
        # Tapi juga tidak di-cleanup otomatis jika handler scope berakhir
```

---

### TEMUAN A-19 — ARCHITECTURAL
**`EnqueueGenreSongs` Command Handler: Sequential `SetMode` → `QueueReplace` → `QueueSelect` Berpotensi Race**

| | |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Handler memanggil 3 `command_bus.execute()` berurutan tanpa lock. Jika WS command lain masuk di antara perintah kedua dan ketiga, state queue bisa corrupt |
| **File** | `server/handlers/ws/queue_handlers.py` baris 54–59 |

```python
# BERPOTENSI RACE — 3 command sequential tanpa atomic group
await command_bus.execute(SetModeCommand(mode=PlaybackMode.QUEUE))
await command_bus.execute(QueueReplaceCommand(tracks=songs))  # ← gap di sini
await command_bus.execute(QueueSelectCommand(index=0))        # command lain bisa masuk
```

**Solusi:** Buat composite command `EnqueueAndPlayCommand` atau wrap dalam lock di handler level.

---

## PART 3 — EVALUASI PRINSIP ARSITEKTUR

### 3.1 Dependency Direction
| Status | Keterangan |
|--------|-----------|
| ✅ BAIK | `core/` tidak mengimport dari `engine/`, `server/`, `cache/` |
| ✅ BAIK | `engine/` mengimport `core/` tapi tidak `server/` |
| ⚠️ PARTIAL | `engine/playback/controller.py` mengimport `cache/resolver.py` secara langsung (harusnya via port) |
| ⚠️ PARTIAL | `server/handlers/event_listeners.py` import `discover_handlers` secara langsung — coupling antar handlers |

### 3.2 SOLID

| Prinsip | Status | Catatan |
|---------|--------|---------|
| **S** SRP | ⚠️ | `config.py` punya side effect + konfigurasi. `start.py` 31K baris |
| **O** OCP | ✅ | Plugin system (lyrics, sponsorblock) extensible tanpa modifikasi core |
| **L** LSP | ✅ | Repository implementations mengikuti Port protocols |
| **I** ISP | ✅ | Port/Protocol dipecah (`AudioPlayerPort`, `MediaExtractorPort`, dll.) |
| **D** DIP | ✅ | DI via constructor injection di semua komponen penting |

### 3.3 Clean Architecture

| Layer | Status | Catatan |
|-------|--------|---------|
| Domain (`core/`) | ✅ | Commands, Events, Ports tidak punya framework dependency |
| Application (`engine/`) | ✅ | Business logic bebas dari HTTP/DB detail |
| Infrastructure (`cache/`, `server/`) | ⚠️ | `DiscoverService` bypass repository, `Database.__getattr__` proxy fragile |
| Presentation (`web/`) | ❌ | No module system, 60+ globals, `export` di non-ESM context |

### 3.4 DRY

| Area | Status | Catatan |
|------|--------|---------|
| `DiscoverService` vs `DiscoverRepository` | ❌ | 132 baris duplikat query SQL |
| `WS_ACTIONS` di JS vs `WSAction` di Python | ⚠️ | Manual sync, potensi drift |
| `to_dict()` / `from_dict()` | ✅ | Terpusat di `TrackInfo` |

### 3.5 Repository Pattern
| Status | Catatan |
|--------|---------|
| ✅ GOOD | `TrackRepository`, `AuthRepository`, `DiscoverRepository` ada dan terpisah |
| ⚠️ ISSUE | `DiscoverService` bypass semua repository, akses DB langsung via `self.db.conn` |
| ⚠️ ISSUE | `discover_handlers.py` juga akses `db.conn.execute()` langsung untuk toggle favorite |

### 3.6 State Management
| Status | Catatan |
|--------|---------|
| ✅ GOOD | Single `AppState` sebagai source of truth |
| ✅ GOOD | CommandBus memastikan single handler per command |
| ⚠️ ISSUE | Mutable shared state tanpa full lock strategy |
| ❌ ISSUE | Frontend store adalah mutable plain object, tidak ada immutability guarantee |

---

## PART 4 — DIAGRAM ARSITEKTUR IDEAL

### 4.1 Arsitektur Aktual (As-Is)

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENT (Browser)                          │
│  Global Namespace: store, ws, dom, 60+ vars, Classic Scripts    │
│  ├── ws.js (WebSocket client)                                   │
│  ├── audio.js (Browser Audio, export bug)                       │
│  ├── render/*.js (DOM rendering)                                │
│  └── utils.js (ITUNES_API_URL undefined)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket /ws + HTTP /api
┌──────────────────────────▼──────────────────────────────────────┐
│                     SERVER LAYER (aiohttp)                      │
│  ├── ws_handler → _ws_handlers{} registry                      │
│  ├── http.py (stream proxy, health, metrics)                    │
│  ├── BroadcastService → broadcasts to ALL connections ⚠️        │
│  └── DiscoverService ← DUPLICATE of DiscoverRepository ❌        │
└──────────────────────────┬──────────────────────────────────────┘
                           │ CommandBus / EventBus
┌──────────────────────────▼──────────────────────────────────────┐
│                    ENGINE LAYER                                  │
│  ├── PlaybackController (subscribe TrackEnded, Progress, etc.)  │
│  ├── RadioMode (standby prefetch, rotation)                     │
│  ├── QueueMode, VolumeService, DownloadManager                  │
│  └── MpvController (JSON IPC over socket)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                   CACHE/PERSISTENCE                              │
│  ├── Database (aiosqlite, single connection WAL)                │
│  │   ├── TrackRepository                                        │
│  │   ├── AuthRepository                                         │
│  │   └── DiscoverRepository                                     │
│  └── CacheResolver (local file → stream URL → yt-dlp)          │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Arsitektur Ideal (To-Be)

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND (ESM Modules)                      │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  store.js   │  │  ws.js       │  │  render/              │  │
│  │  (reactive  │  │  (ESM export)│  │  (pure functions)     │  │
│  │  state)     │  │              │  │                       │  │
│  └──────┬──────┘  └──────┬───────┘  └───────────────────────┘  │
│         │                │                                      │
│  ┌──────▼────────────────▼───────────────────────────────────┐  │
│  │              main.js (App controller)                     │  │
│  │  import { store } from './store.js'                       │  │
│  │  import { wsSend } from './ws.js'                         │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ WebSocket + HTTP
┌──────────────────────────▼──────────────────────────────────────┐
│                  PRESENTATION LAYER (aiohttp)                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           ConnectionManager (Auth-aware)                │    │
│  │   broadcast_to_authenticated() / broadcast_to_all()     │    │
│  └────────────────────────┬────────────────────────────────┘    │
│                           │                                     │
│  ┌────────────┐  ┌────────┴───────┐  ┌─────────────────────┐   │
│  │ HTTP       │  │ WS Handlers    │  │ BroadcastService    │   │
│  │ serve_index│  │ (per domain)   │  │ (event → WS push)   │   │
│  │ serve_stream│ │ playback/      │  └─────────────────────┘   │
│  │ /metrics   │  │ queue/         │                            │
│  └────────────┘  │ discover/      │                            │
│                  └────────┬───────┘                            │
└───────────────────────────┼────────────────────────────────────┘
                            │ CommandBus
┌───────────────────────────▼────────────────────────────────────┐
│                  APPLICATION LAYER (engine/)                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              CommandBus (1-to-1 routing)                 │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────┐  ┌────────┴───────┐  ┌───────────────────────┐ │
│  │PlaybackCtrl│  │ RadioMode      │  │ DownloadManager       │ │
│  │(orchestrator│ │ (standby queue)│  │ VolumeService         │ │
│  └──────┬─────┘  └────────────────┘  └───────────────────────┘ │
│         │ EventBus (pub/sub)                                    │
│  ┌──────▼────────────────────────────────────────────────────┐  │
│  │        EventBus subscribers: Lyrics, SponsorBlock,        │  │
│  │        BroadcastService, PrefetchService                  │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬────────────────────────────────────┘
                            │ Ports (interfaces)
┌───────────────────────────▼────────────────────────────────────┐
│                   DOMAIN CORE (core/)                           │
│  Commands · Events · Ports · AppState · ValueObjects           │
│  [Zero external dependencies — pure Python]                    │
└───────────────────────────┬────────────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────────────┐
│               INFRASTRUCTURE LAYER (cache/)                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │   Database (aiosqlite, WAL, single connection)          │   │
│  │   ├── TrackRepository    (CRUD tracks)                  │   │
│  │   ├── AuthRepository     (session management)           │   │
│   │   └── DiscoverRepository (recent, favorites, artists)  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────┐    ┌──────────────────────────────────┐  │
│  │   CacheResolver   │    │   YtDlpClient (ThreadExecutor)   │  │
│  │ local→stream→fetch│    │   MpvController (JSON IPC)       │  │
│  └───────────────────┘    └──────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 Dependency Flow Rules (Ideal)

```
Frontend (ESM)
    ↕ WS/HTTP
Presentation (server/)
    ↕ CommandBus / EventBus
Application (engine/)
    ↕ Ports (interfaces)
Domain Core (core/)        ← Zero outward dependency
    ↑ implements
Infrastructure (cache/)
```

**Golden Rule:** Dependency arrows hanya boleh mengarah **ke dalam** (menuju Domain Core). Tidak ada `core/` yang import `engine/`, tidak ada `engine/` yang import `server/`.

---

## PART 5 — RINGKASAN PRIORITAS PERBAIKAN

| Prioritas | ID | Temuan | Effort |
|-----------|-----|--------|--------|
| 🔴 P0 | A-01 | KeyError `stream_url` DiscoverService | 5 menit |
| 🔴 P0 | A-02 | Dockerfile CMD `run.py` tidak ada | 1 menit |
| 🔴 P0 | A-03 | `ITUNES_API_URL` undefined | 5 menit |
| 🔴 P0 | A-04 | `export` di non-ESM `audio.js` | 2 menit |
| 🟠 P1 | A-05 | aiosqlite version mismatch | 10 menit |
| 🟠 P1 | A-06 | DiscoverService duplikasi Repository | 2 jam |
| 🟠 P1 | A-07 | AppState mutable tanpa lock | 4 jam |
| 🟠 P1 | A-08 | Broadcast ke unauthenticated clients | 1 jam |
| 🟠 P1 | A-09 | config.py side effect saat import | 2 jam |
| 🟡 P2 | A-10 | O(n) delete deque | 30 menit |
| 🟡 P2 | A-11 | `__getattr__` proxy fragile | 3 jam |
| 🟡 P2 | A-12 | 60+ global JS vars | 8 jam |
| 🟡 P2 | A-13 | `print()` bukan logger | 5 menit |
| 🟡 P2 | A-14 | CacheResolver race condition | 1 jam |
| 🟡 P2 | A-15 | `start.py` 31K baris monolith | 4 jam |
| 🟡 P2 | A-16 | O(n) SponsorBlock per frame | 1 jam |
| 🟢 P3 | A-17 | `is_favorite` type inconsistency | 30 menit |
| 🟢 P3 | A-18 | weakref handler edge case | 1 jam |
| 🟡 P2 | A-19 | EnqueueGenre sequential command race | 2 jam |

---

## PART 6 — PENILAIAN KESELURUHAN

| Dimensi | Skor | Keterangan |
|---------|------|-----------|
| **Layering / Separation of Concerns** | 7/10 | Baik, tapi DiscoverService bypass layer |
| **Dependency Direction** | 8/10 | Core bebas, tapi engine→cache direct |
| **SOLID** | 7/10 | DIP dan ISP bagus, SRP lemah di config.py |
| **DRY** | 5/10 | DiscoverService adalah DRY violation besar |
| **Repository Pattern** | 7/10 | Ada tapi di-bypass di beberapa tempat |
| **State Management** | 6/10 | Satu AppState bagus, tapi tanpa locking strategy |
| **Frontend Architecture** | 3/10 | Global namespace, tidak ada module system |
| **Security Architecture** | 7/10 | Auth ada, tapi broadcast bocor ke unauthenticated |
| **Scalability** | 5/10 | Single-process, single DB, akan bottleneck di multi-user |
| **Testability** | 5/10 | Backend testable, frontend tidak bisa unit test |

**Skor Keseluruhan: 6.0/10** — Fondasi solid untuk proyek personal, perlu 4–8 critical fix sebelum production.

---

*Laporan ini dihasilkan oleh Tim Audit Software LunaWave — 2026.*
*Audit berikutnya: Backend Bugs & Security Deep-Dive*
