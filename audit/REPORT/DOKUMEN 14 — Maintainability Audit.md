# 🛠️ MAINTAINABILITY AUDIT & REFACTOR ROADMAP — LunaWave
**Audit Tim:** Senior Software Architect · Principal Backend Engineer · Senior Frontend Engineer · DevOps Engineer · QA Lead  
**Tanggal Audit:** 2026-07-07  
**Scope:** Seluruh Python codebase (8.211 baris, 50+ file)  
**Metodologi:** Static analysis, structural review, coupling/cohesion measurement, naming consistency, pattern consistency

---

## SCORECARD MAINTAINABILITY

| Dimensi | Nilai | Grade |
|---|---|---|
| Readability | 6.5 / 10 | B- |
| Naming Consistency | 5.5 / 10 | C+ |
| Architectural Consistency | 6.0 / 10 | B- |
| Modularity | 7.0 / 10 | B |
| Extensibility | 6.5 / 10 | B- |
| Coupling | 5.0 / 10 | C |
| Cohesion | 5.5 / 10 | C+ |
| Technical Debt Load | 4.5 / 10 | D+ |
| **Overall** | **5.8 / 10** | **C+** |

**Verdict:** Arsitektur dasar sudah baik (ports/adapters, event bus, command bus), namun sejumlah pola konsisten yang baik dirusak oleh kebocoran abstraksi, coupling tersembunyi, dan technical debt yang terdokumentasi namun belum diperbaiki.

---

## TEMUAN READABILITY

### R-01 — `log_config.py` adalah God Object yang Melanggar SRP

**Severity:** 🟠 Major  
**File:** `core/log_config.py` (477 baris)

File ini menggabungkan 7 tanggung jawab yang tidak terkait dalam satu modul:

1. ANSI colour constants
2. Global state counter (`_Stats` class)
3. Terminal status bar (threading)
4. Summary printer (threading)
5. Spinner context manager
6. Semantic log rewriter (300+ baris logic)
7. structlog setup

**Masalah konkret:**

```python
# log_config.py baris 226 — import `re as _re` di tengah file, bukan di atas
import re as _re

# log_config.py baris 300 — `import time` di BAWAH class definition
# (bukan di top-level), terjadi dua kali sekaligus
async def _set_property(self, prop: str, value):
    await self._command(["set_property", prop, value])
import time   # ← ini ada di mpv_controller.py tapi symptom dari same pattern
```

Selain itu, `_rewrite_event()` adalah fungsi 150 baris yang melakukan pattern matching dengan 20+ `if/elif` chain untuk semantic rewriting log — logic yang terlalu kompleks untuk sebuah formatter.

**Dampak:** File 477 baris ini adalah yang paling sulit dipahami dalam seluruh codebase. Setiap perubahan pada logging behavior membutuhkan pemahaman seluruh 7 responsibility.

**Solusi — Pecah menjadi modul terpisah:**
```
core/logging/
├── __init__.py          # re-export setup_logging()
├── ansi.py              # ANSI colour constants saja
├── stats.py             # _Stats class saja
├── status_bar.py        # StatusBar thread class
├── renderer.py          # _CompactRenderer + _rewrite_event
└── setup.py             # setup_logging() function
```

---

### R-02 — `start.py` Berisi Dua Program yang Tidak Berhubungan

**Severity:** 🟠 Major  
**File:** `start.py` (866 baris — file terbesar)

`start.py` adalah file terbesar dalam project dan menggabungkan:
- **GUI Tkinter** (ServerManagerApp, dialog windows, widget rendering)
- **Headless CLI launcher** (tanpa GUI)
- **Dependency checker** (DependencyChecker class)
- **Process manager** (ServerProcessManager class)
- **Port scanner** (get_pid_occupying_port — mendukung Win32/Linux/Mac dengan 4 fallback tools)

Selain itu terdapat branding yang tidak konsisten:

```python
# start.py baris 3 — nama lama
"""
bagas.fm — Server Manager
"""

# start.py baris 552 — nama lama masih tersisa
self.title("bagas.fm — Server Manager")

# start.py baris 573
text="bagas.fm",

# Sementara di tempat lain sudah "LunaWave"
text=f"Server LunaWave aktif pada port {port}."
```

**Dampak:** Testing tidak mungkin dilakukan. GUI tidak bisa ditest tanpa display. Logic process management tidak bisa ditest tanpa GUI. Branding lama mengurangi kepercayaan pengguna.

**Solusi:**
```
launcher/
├── gui.py              # ServerManagerApp + semua widget Tkinter
├── cli.py              # headless launch logic  
├── process.py          # ServerProcessManager (testable)
├── checker.py          # DependencyChecker (testable)
└── __init__.py
```

---

### R-03 — `mpv_controller.py`: `import time` di Akhir File

**Severity:** 🟡 Minor  
**File:** `engine/mpv_controller.py` baris 300

```python
    async def _set_property(self, prop: str, value):
        await self._command(["set_property", prop, value])
import time   # ← BARIS TERAKHIR FILE, di luar semua class
```

`import time` ada di luar semua definisi class/function, di baris terakhir file setelah semua kode. Ini adalah artifact dari copy-paste atau refactor yang tidak selesai. `time` hanya digunakan di `_handle_event` untuk throttling progress event — seharusnya import di bagian atas.

**Solusi:** Pindahkan ke baris 1-10 bersama import lain.

---

## TEMUAN NAMING CONSISTENCY

### N-01 — Penamaan Logger Tidak Konsisten: `logger` vs `_log`

**Severity:** 🟡 Minor  
**File:** 29 file menggunakan `logger`, 1 file menggunakan `_log`

```python
# 29 file menggunakan ini:
logger = structlog.get_logger(__name__)

# engine/radio_engine.py baris 26 — satu-satunya yang pakai _log:
_log = structlog.get_logger(__name__)
```

**Dampak kecil namun nyata:** Ketika developer baru membaca `radio_engine.py` setelah file lain, mereka perlu re-track naming convention yang berbeda. Jika `_log` dimaksudkan sebagai "private" maka inconsistent karena file lain yang sama-sama "private" menggunakan `logger`.

**Solusi:** Standardisasi ke `logger` di seluruh codebase:
```bash
sed -i 's/^_log = structlog/logger = structlog/g' engine/radio_engine.py
sed -i 's/_log\./logger./g' engine/radio_engine.py
```

---

### N-02 — Branding Inkonsisten: `bagas.fm` vs `LunaWave` vs `ytgui`

**Severity:** 🟠 Major  
**File:** `start.py`, `pyproject.toml`, `package-lock.json`, `notifications.py`

Project memiliki setidaknya 3 nama berbeda yang digunakan secara bersamaan:

| Lokasi | Nama yang Digunakan |
|---|---|
| `start.py` docstring (baris 3) | `bagas.fm` |
| `start.py` window title | `bagas.fm — Server Manager` |
| `pyproject.toml` project name | `ytgui` |
| `package-lock.json` | `ytgui-project` |
| `package.json` | `lunawave-project` |
| `plugins/notifications.py` | `NOTIFICATION_ID = "ytgui_nowplaying"` |
| `core/state.py` docstring | `YTGUI V2` |
| README, app UI | `LunaWave` |

**Dampak:** Membingungkan pengguna baru, menyulitkan grepping/searching, menunjukkan proses rename yang tidak tuntas.

**Solusi — rename checklist:**
```bash
# Cari semua occurrence nama lama
grep -rn "bagas\|ytgui\|yt-player\|YT_PLAYER" . --include="*.py" --include="*.toml" --include="*.json"

# File yang perlu diperbaiki:
# start.py: docstring, window title, widget text
# pyproject.toml: project name "ytgui" → "lunawave"  
# notifications.py: NOTIFICATION_ID = "lunawave_nowplaying"
# core/state.py: docstring "YTGUI V2" → "LunaWave"
# env var: YT_PLAYER_BASE → LUNAWAVE_BASE (breaking change, perlu migration)
```

---

### N-03 — Environment Variable Naming Tidak Konsisten

**Severity:** 🟡 Minor  
**File:** `config.py`, `engine/mpv_controller.py`

```python
# config.py — prefix LUNAWAVE_
WEB_HOST = os.environ.get("LUNAWAVE_HOST", "0.0.0.0")
WEB_PORT = int(os.environ.get("LUNAWAVE_PORT", 8765))
ADMIN_USERNAME = os.environ.get("LUNAWAVE_ADMIN_USER", "admin")

# config.py dan mpv_controller.py — prefix YT_PLAYER_ (nama lama)
BASE_DIR = Path(os.environ.get("YT_PLAYER_BASE", ...))
MPV_SOCKET = os.environ.get("YT_PLAYER_SOCKET", ...)

# mpv_controller.py baris 40 — prefix berbeda lagi
self.tcp_port = tcp_port or os.environ.get("YT_PLAYER_MPV_PORT", "12345")
```

Tiga prefix untuk satu aplikasi: `LUNAWAVE_`, `YT_PLAYER_`, dan tanpa prefix.

---

## TEMUAN ARCHITECTURAL CONSISTENCY

### A-01 — Repository Pattern Dilanggar di Tiga Layer Berbeda

**Severity:** 🔴 Critical  
**File:** `server/services/discover_service.py`, `server/handlers/ws/discover_handlers.py`, `server/handlers/http.py`

Project mendefinisikan `TrackRepositoryPort` dan mengimplementasikannya di `cache/repositories/`. Namun beberapa file melewati layer repository dan langsung mengakses `db.conn`:

```python
# server/services/discover_service.py — 5 kali bypass repository
async def get_recent(self, n: int) -> list[TrackInfo]:
    async with self.db.conn.execute(  # type: ignore ← semua pakai type: ignore!
        "SELECT video_id, title, artist, duration, thumbnail, local_path, ..."
    ) as cursor:

# server/handlers/ws/discover_handlers.py baris 67 — WS handler langsung SQL
await db.conn.execute("UPDATE tracks SET is_favorite = ? WHERE video_id = ?", ...)
await db.conn.commit()

# server/handlers/http.py baris 33-35 — health check bypass
if db.conn:
    async with db.conn.execute("SELECT 1") as cursor:
```

**Dampak:** Jika database engine diganti (misal dari SQLite ke PostgreSQL), perubahan harus dilakukan di banyak tempat yang tidak terpusat. SQL duplikat di `discover_service.py` dan `track_repository.py`.

**Solusi — pindahkan query ke DiscoverRepository:**
```python
# cache/repositories/discover_repository.py — tambahkan method:
async def get_recent(self, n: int) -> list[TrackInfo]: ...
async def get_favorites(self, n: int) -> list[TrackInfo]: ...
async def get_cached(self, n: int) -> list[TrackInfo]: ...
async def toggle_favorite(self, video_id: str) -> bool: ...

# server/services/discover_service.py — gunakan repository:
class DiscoverService:
    async def get_recent(self, n: int) -> list[TrackInfo]:
        return await self.db.discover.get_recent(n)  # ← delegasi ke repo
```

---

### A-02 — `STATS` dari `log_config` Dipakai sebagai Shared Mutable State

**Severity:** 🟠 Major  
**File:** `engine/playback/controller.py`, `server/handlers/websocket.py`, `engine/playback/playback_commands.py`, `engine/playback/settings_commands.py`, `server/services/stream_prefetch.py`

`STATS` adalah objek dari layer **logging** yang diimport dan dimutasi dari layer **engine** dan **server**:

```python
# engine/playback/controller.py — business logic menulis ke logging layer
from core.log_config import STATS
STATS.is_playing = True
STATS.current_track = track.title[:50]
STATS.inc('songs_played')

# server/handlers/websocket.py — server layer menulis ke logging layer  
_LOG_STATS.clients = len(self.active_connections)
_LOG_STATS.is_playing = True if _LOG_STATS.current_track != "—" else ...
```

Ini adalah **dependency inversion violation**: modul tingkat rendah (engine) bergantung pada modul presentasi (logging/display). Jika terminal status bar dihapus, engine harus ikut diubah.

**Solusi — gunakan EventBus yang sudah ada:**
```python
# Definisikan event baru
@dataclass
class AppStatsUpdatedEvent(DomainEvent):
    songs_played: int = 0
    clients: int = 0
    is_playing: bool = False
    current_track: str = "—"

# engine/playback/controller.py — publish event, bukan tulis STATS langsung
await self.bus.publish(AppStatsUpdatedEvent(
    is_playing=True,
    current_track=track.title[:50],
))

# log_config.py — subscribe ke event untuk update STATS
# (logging layer mengobservasi business layer, bukan sebaliknya)
```

---

### A-03 — WS Handler Signature Memiliki 7 Parameter Primitif (Primitive Obsession)

**Severity:** 🟠 Major  
**File:** Semua 26 WS handler di `server/handlers/ws/`

Setiap WS handler memiliki signature yang sama persis dengan 7 parameter loose:

```python
# Sama di 26 fungsi:
async def _handle_play_track(data, ws, state, ytdlp, manager, db, command_bus):
async def _handle_toggle_pause(data, ws, state, ytdlp, manager, db, command_bus):
async def _handle_search(data, ws, state, ytdlp, manager, db, command_bus):
# ... 23 handler lainnya identik
```

**Masalah:**
1. Menambahkan dependency baru (misal `event_bus`) membutuhkan perubahan di 26+ tempat
2. Handler yang hanya butuh `command_bus` terpaksa menerima `ytdlp`, `state`, `manager`, `db` yang tidak digunakan
3. Tidak ada type annotation — tidak bisa diverifikasi dengan mypy

**Solusi — buat Context object:**
```python
# server/handlers/ws/context.py
@dataclass
class WSContext:
    data: dict
    ws: web.WebSocketResponse
    state: AppState
    ytdlp: MediaExtractorPort
    manager: ConnectionManager
    db: DatabasePort
    command_bus: CommandBus

# Signature handler menjadi:
async def _handle_play_track(ctx: WSContext) -> None:
    track = TrackInfo.from_dict(ctx.data)
    if track:
        await ctx.command_bus.execute(PlayTrackCommand(track=track))

# Type-safe, extensible, testable
```

---

### A-04 — `bootstrap.py`: Import di dalam Function Body (Anti-pattern)

**Severity:** 🟡 Minor  
**File:** `core/bootstrap.py`

```python
async def build_app_context() -> AppContext:
    # ...
    from engine.playback.controller import PlaybackDependencies    # ← baris 91
    # ...
    from engine.playback.playback_commands import PlaybackCommands  # ← baris 105
    from engine.playback.queue_commands import QueueCommands        # ← baris 106
    from engine.playback.settings_commands import SettingsCommands  # ← baris 107
    from engine.playback.radio_commands import RadioCommands        # ← baris 108
    # ...
    from config import ADMIN_USERNAME, IS_PASSWORD_AUTO_GENERATED   # ← baris 155
    
async def shutdown_app_context(ctx: AppContext, tasks: list):
    import traceback   # ← baris 182
```

Import di dalam function body menghambat static analysis, menghilangkan IDE autocomplete, dan menyembunyikan circular import yang mungkin ada.

**Solusi:** Pindahkan semua import ke top-level file.

---

## TEMUAN COUPLING

### C-01 — `AppState` Digunakan sebagai Global Mutable Bag (119 akses)

**Severity:** 🔴 Critical  
**File:** `engine/radio_engine.py`, `engine/playback/controller.py`, dan banyak lainnya

`AppState` diakses langsung (`state.xxx = yyy`) dari 119 lokasi di seluruh engine. Ini menciptakan tight coupling di mana setiap modul yang punya referensi ke `state` bisa mengubah apapun kapan saja:

```python
# engine/radio_engine.py — radio langsung menulis ke state
self.state.radio_queue.clear()
self.state.radio_queue.extend(tracks[1:])
self.state.status = PlayerStatus.LOADING

# engine/playback/controller.py — controller juga menulis ke state
self.state.current_track = track
self.state.status = PlayerStatus.LOADING
self.state.position = 0.0
self.state.lyrics_lines = []
```

**Dampak:** Jika dua modul memodifikasi `state` secara bersamaan dari async tasks berbeda, hasilnya adalah race condition yang sulit di-debug. Tidak ada ownership jelas untuk setiap field state.

**Solusi — State Ownership:**
```python
# Bagi AppState menjadi sub-state dengan ownership jelas:
@dataclass
class PlaybackState:      # owned by PlaybackController
    status: PlayerStatus = PlayerStatus.IDLE
    current_track: Optional[TrackInfo] = None
    position: float = 0.0
    duration: float = 0.0

@dataclass 
class QueueState:         # owned by QueueMode
    queue: deque = field(default_factory=deque)
    history: deque = field(default_factory=lambda: deque(maxlen=50))

@dataclass
class RadioState:         # owned by RadioMode
    radio_queue: deque = field(default_factory=deque)

@dataclass
class AppState:           # aggregate, read-only dari luar
    playback: PlaybackState = field(default_factory=PlaybackState)
    queue: QueueState = field(default_factory=QueueState)
    radio: RadioState = field(default_factory=RadioState)
    # ...
```

---

### C-02 — `DiscoverService` Tightly Coupled ke `Database` Concrete Class

**Severity:** 🟡 Minor  
**File:** `server/services/discover_service.py`

```python
class DiscoverService:
    def __init__(self, db: Database):  # ← concrete type, bukan Port
        self.db = db
```

Berbeda dengan `PlaybackController` yang menggunakan `DatabasePort` (Protocol), `DiscoverService` mengimport concrete `Database` class. Testing membutuhkan database nyata.

**Solusi:**
```python
from core.ports import DiscoverRepositoryPort  # tambahkan Port baru

class DiscoverService:
    def __init__(self, db: DiscoverRepositoryPort):  # loose coupling
        self.db = db
```

---

### C-03 — `STATIC_DIR` Didefinisikan Dua Kali dengan Path Berbeda

**Severity:** 🟡 Minor  
**File:** `server/handlers/http.py` baris 15 dan `server/app.py` baris 14

```python
# server/handlers/http.py
STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "static"
#            handler -> handlers -> server -> root -> web/static

# server/app.py  
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
#            app.py -> server -> root -> web/static
```

Kedua path menghasilkan direktori yang sama secara hasil, tetapi cara penghitungannya berbeda — satu menggunakan `.parent.parent.parent` dan satu menggunakan `.parent.parent`. Ini rapuh: jika salah satu file dipindah, satu path akan rusak.

**Solusi — definisikan sekali di `config.py`:**
```python
# config.py
STATIC_DIR = BASE_DIR / "web" / "static"

# Semua modul yang butuh:
from config import STATIC_DIR
```

---

### C-04 — `build_app_context()` Memiliki 28 Import dan Membangun Semua Dependency Secara Manual

**Severity:** 🟠 Major  
**File:** `core/bootstrap.py`

`bootstrap.py` import dari 28 modul dan secara manual merangkai semua dependency. Ini adalah **manual DI container** yang fragile:

```python
# bootstrap.py — 28 baris import
from cache.db import Database
from config import WEB_HOST, WEB_PORT
from core.state import AppState, PlayerStatus
from engine.mpv_controller import MpvController
from engine.ytdlp_client import YtDlpClient
from plugins.notifications import TermuxNowPlaying
from plugins.lyrics import LyricsFetcher
# ... 21 import lagi
```

Menambahkan satu service baru membutuhkan: (1) tambah import di bootstrap, (2) tambah ke `AppContext` dataclass, (3) pass ke setiap function yang butuh, (4) tambah ke `shutdown_app_context`.

**Solusi jangka pendek:** Pecah `build_app_context` menjadi factory functions yang lebih kecil:
```python
async def _build_storage(config) -> tuple[Database, ...]: ...
async def _build_engine(storage, config) -> tuple[MpvController, ...]: ...
async def _build_plugins(engine, storage) -> tuple[...]: ...
async def _build_server(engine, plugins) -> web.Application: ...
```

---

## TEMUAN COHESION

### CO-01 — `discover_service.py` Mengandung SQL Duplikat dengan `track_repository.py`

**Severity:** 🟠 Major  
**File:** `server/services/discover_service.py` vs `cache/repositories/track_repository.py`

`DiscoverService` memiliki 5 SQL query yang hampir identik dengan yang ada di `TrackRepository`, khususnya SELECT dari tabel `tracks`:

```python
# discover_service.py — query manual dengan field eksplisit (3 kali)
"SELECT video_id, title, artist, duration, thumbnail, local_path, 
 view_count, play_count, is_favorite FROM tracks ORDER BY last_played DESC LIMIT ?"

# track_repository.py — query dengan SELECT *
"SELECT * FROM tracks WHERE video_id = ?"
```

Jika kolom `tracks` ditambahkan, harus update di dua tempat. Jika column name diubah, `discover_service.py` tidak akan error compile-time.

**Solusi:** Pindahkan semua SQL ke `DiscoverRepository` dan gunakan melalui `DiscoverService`.

---

### CO-02 — `DependencyChecker` di `start.py` Mengecek `opentelemetry` yang Tidak Ada di Requirements

**Severity:** 🟠 Major  
**File:** `start.py` baris 51

```python
deps = {
    "yt-dlp": "yt_dlp",
    "aiosqlite": "aiosqlite",
    "aiohttp": "aiohttp",
    "syncedlyrics": "syncedlyrics",
    "structlog": "structlog",
    "prometheus_client": "prometheus_client",
    "opentelemetry": "opentelemetry"    # ← TIDAK ADA di requirements.txt!
}
```

`opentelemetry` tidak terdaftar di `requirements.txt` maupun `pyproject.toml`. Checker akan selalu melaporkan dependency ini sebagai "missing" meski aplikasi berjalan normal — atau jika terinstall secara manual, checker tidak akan mendeteksi keberadaannya secara benar karena nama package-nya bukan `opentelemetry` tapi `opentelemetry-api`.

---

## TEMUAN TECHNICAL DEBT

### TD-01 — 12 PATCH Comment Terdokumentasi Belum Direfactor

**Severity:** 🟠 Major

Codebase mengandung komentar audit internal yang masih ada di production code, menandai fix yang sudah diterapkan namun belum di-refactor dengan benar:

```python
# config.py
# PATCH-YTDLP-RESOLVE-TIMEOUT-01: yt-dlp.get_stream_url() sebelumnya tidak punya batas waktu

# engine/mpv_controller.py docstring
# CRITICAL-03 fix: On Windows, falls back to TCP socket
# CRITICAL-06 fix: _set_property is now properly defined.
# MED-11: Basic reconnection support via is_connected flag.

# engine/radio_engine.py baris 121
# PATCH-RADIO-EMPTY-QUEUE-01: Queue habis — _start() jalan di background (bisa
```

Komentar `CRITICAL-XX`, `MED-XX`, `HIGH-XX`, `PATCH-XX` adalah artefak dari sprint review session yang seharusnya dihapus atau dikonversi ke proper docstring setelah fix dianggap stabil. Di production code, komentar seperti ini mengurangi readability dan memberi kesan kode belum siap.

**Solusi:** Buat tiket di issue tracker untuk setiap PATCH, lalu hapus semua inline patch comments. Informasi ini seharusnya ada di git commit message, bukan di kode.

---

### TD-02 — 16 `# type: ignore` Menandai Masalah Typing yang Belum Diselesaikan

**Severity:** 🟡 Minor

```python
# discover_service.py — 5x type: ignore pada db.conn access
async with self.db.conn.execute(  # type: ignore

# mpv_controller.py
async def get_position(self) -> float | None:
    val = await self._get_property("time-pos")
    return float(val) if val is not None else None
```

`# type: ignore` pada `db.conn` terjadi karena akses langsung ke concrete attribute yang tidak ada di Port interface — ini adalah symptom dari masalah A-01 (repository bypass).

---

### TD-03 — `asyncio` Diimport Dua Kali di `websocket.py`

**Severity:** 🟡 Minor  
**File:** `server/handlers/websocket.py`

```python
import asyncio   # baris 1 — top-level import

# ...

async def broadcast(self, message: dict):
    # ...
    import asyncio   # baris 52 — DUPLIKAT di dalam method!
    async def send(ws):
```

Import duplikat di dalam method adalah artifact dari refactor yang tidak bersih.

---

## RINGKASAN TECHNICAL DEBT TOTAL

| Kategori | Jumlah | Estimasi Effort |
|---|---|---|
| God Object / SRP violation | 2 (log_config, start.py) | 3-5 hari |
| Repository pattern bypass | 3 lokasi | 1-2 hari |
| Primitive obsession (7-arg handlers) | 26 handler | 2-3 hari |
| Naming inconsistency | 4 jenis | 1 hari |
| Coupling (STATS, AppState) | 2 pattern | 3-4 hari |
| Dead code / duplicate definitions | 5 instance | 0.5 hari |
| PATCH comments cleanup | 12 komentar | 0.5 hari |
| type: ignore cleanup | 16 instance | 1-2 hari |
| **Total estimasi** | | **~12-18 hari dev** |

---

## 🗺️ ROADMAP REFACTOR

### FASE 0 — Quick Wins (Estimasi: 2-3 hari, tanpa breaking change)
*Lakukan dulu sebelum sprint lain — risiko rendah, dampak tinggi.*

| ID | Task | File | Effort |
|---|---|---|---|
| F0-01 | Fix branding: ganti `bagas.fm` → `LunaWave` di start.py | `start.py` | 1 jam |
| F0-02 | Rename `_log` → `logger` di radio_engine.py | `engine/radio_engine.py` | 15 menit |
| F0-03 | Pindah `import time` ke top-level mpv_controller.py | `engine/mpv_controller.py` | 5 menit |
| F0-04 | Hapus `import asyncio` duplikat di websocket.py | `server/handlers/websocket.py` | 5 menit |
| F0-05 | Pindah semua deferred imports ke top-level bootstrap.py | `core/bootstrap.py` | 30 menit |
| F0-06 | Hapus `opentelemetry` dari DependencyChecker | `start.py` | 5 menit |
| F0-07 | Definisikan `STATIC_DIR` sekali di `config.py` | `config.py`, `server/app.py`, `server/handlers/http.py` | 15 menit |
| F0-08 | Hapus 12 PATCH/CRITICAL/MED inline comments dari production code | Multiple files | 1 jam |
| F0-09 | Update pyproject.toml project name `ytgui` → `lunawave` | `pyproject.toml` | 5 menit |
| F0-10 | Fix NOTIFICATION_ID `ytgui_nowplaying` → `lunawave_nowplaying` | `plugins/notifications.py` | 5 menit |

**Acceptance criteria Fase 0:** Tidak ada nama `bagas.fm`, `ytgui`, `_log` di production code. `import` semua di top-level.

---

### FASE 1 — Repository Pattern Enforcement (Estimasi: 3-4 hari)
*Selesaikan sebelum menambahkan fitur database baru.*

| ID | Task | File | Effort |
|---|---|---|---|
| F1-01 | Tambah method `get_recent()`, `get_favorites()`, `get_cached()`, `toggle_favorite()` ke `DiscoverRepository` | `cache/repositories/discover_repository.py` | 2 jam |
| F1-02 | Refactor `DiscoverService` untuk menggunakan `DiscoverRepository` (hapus raw SQL) | `server/services/discover_service.py` | 2 jam |
| F1-03 | Pindah `UPDATE tracks SET is_favorite` dari ws handler ke repository | `server/handlers/ws/discover_handlers.py` | 1 jam |
| F1-04 | Ganti raw `db.conn` di `DiscoverService` dengan `db.discover.*` | `server/services/discover_service.py` | 1 jam |
| F1-05 | Tambahkan `DiscoverRepositoryPort` ke `core/ports.py` | `core/ports.py` | 30 menit |
| F1-06 | Update `DiscoverService.__init__` untuk terima Port, bukan concrete | `server/services/discover_service.py` | 30 menit |
| F1-07 | Buat unit test untuk `DiscoverRepository` | `tests/unit/cache/` | 3 jam |

**Acceptance criteria Fase 1:** Zero raw SQL di luar `cache/repositories/`. `DiscoverService` dapat ditest tanpa database nyata.

---

### FASE 2 — WS Handler Context Object (Estimasi: 2-3 hari)
*Lakukan setelah Fase 1 selesai.*

| ID | Task | File | Effort |
|---|---|---|---|
| F2-01 | Buat `WSContext` dataclass | `server/handlers/ws/context.py` | 30 menit |
| F2-02 | Refactor semua 26 WS handler ke `WSContext` | `server/handlers/ws/*.py` | 3 jam |
| F2-03 | Update `handle_ws_message()` untuk build dan pass `WSContext` | `server/handlers/websocket.py` | 1 jam |
| F2-04 | Tambah type annotation ke semua handler | `server/handlers/ws/*.py` | 1 jam |
| F2-05 | Buat unit test untuk sample WS handlers dengan mock `WSContext` | `tests/unit/server/` | 2 jam |

**Acceptance criteria Fase 2:** Menambahkan dependency baru ke WS handlers hanya membutuhkan satu perubahan di `WSContext`, bukan 26 perubahan.

---

### FASE 3 — STATS Coupling Elimination (Estimasi: 3-4 hari)
*Lakukan setelah Fase 2 — membutuhkan EventBus yang stabil.*

| ID | Task | File | Effort |
|---|---|---|---|
| F3-01 | Definisikan `AppStatsUpdatedEvent` di `core/events.py` | `core/events.py` | 30 menit |
| F3-02 | Ganti direct `STATS.xxx =` di `controller.py` dengan event publish | `engine/playback/controller.py` | 1 jam |
| F3-03 | Ganti direct `_LOG_STATS.xxx =` di `websocket.py` dengan event | `server/handlers/websocket.py` | 1 jam |
| F3-04 | Ganti semua `STATS`/`_LOG_STATS` writes di semua engine files | `engine/playback/*.py`, `server/services/*.py` | 2 jam |
| F3-05 | `log_config.py` subscribe ke `AppStatsUpdatedEvent` untuk update internal `_Stats` | `core/log_config.py` | 1 jam |
| F3-06 | Hapus `from core.log_config import STATS` dari semua non-logging modules | Multiple | 30 menit |

**Acceptance criteria Fase 3:** Module `engine/` tidak boleh import dari `core/log_config`. Semua stats update via EventBus.

---

### FASE 4 — log_config.py Decomposition (Estimasi: 3-5 hari)
*Sprint tersendiri — risiko tertinggi karena menyentuh logging.*

| ID | Task | File | Effort |
|---|---|---|---|
| F4-01 | Ekstrak ANSI constants ke `core/logging/ansi.py` | Baru | 30 menit |
| F4-02 | Ekstrak `_Stats` class ke `core/logging/stats.py` | Baru | 1 jam |
| F4-03 | Ekstrak `StatusBar` thread ke `core/logging/status_bar.py` | Baru | 1 jam |
| F4-04 | Ekstrak `Spinner` ke `core/logging/spinner.py` | Baru | 30 menit |
| F4-05 | Ekstrak `_CompactRenderer` + `_rewrite_event` ke `core/logging/renderer.py` | Baru | 2 jam |
| F4-06 | Sederhanakan `_rewrite_event` dengan strategy pattern atau dict dispatch | `core/logging/renderer.py` | 3 jam |
| F4-07 | Buat `core/logging/__init__.py` yang re-export `setup_logging` | Baru | 15 menit |
| F4-08 | Update semua import `from core.log_config import ...` | Multiple | 1 jam |

**Acceptance criteria Fase 4:** `core/log_config.py` tidak ada lagi. Semua logging komponen < 100 baris per file. `_rewrite_event` memiliki unit test.

---

### FASE 5 — AppState Ownership (Estimasi: 5-7 hari)
*Sprint terbesar — lakukan di sprint terpisah dengan feature freeze.*

| ID | Task | File | Effort |
|---|---|---|---|
| F5-01 | Design sub-state ownership model (PlaybackState, QueueState, RadioState) | Architecture | 1 hari |
| F5-02 | Buat dataclass terpisah untuk setiap sub-state | `core/state.py` | 2 jam |
| F5-03 | Refactor `PlaybackController` untuk hanya mutasi `PlaybackState` | `engine/playback/controller.py` | 3 jam |
| F5-04 | Refactor `QueueMode` untuk hanya mutasi `QueueState` | `engine/queue_manager.py` | 2 jam |
| F5-05 | Refactor `RadioMode` untuk hanya mutasi `RadioState` | `engine/radio_engine.py` | 3 jam |
| F5-06 | Update `AppState.to_dict()` untuk flatten sub-states | `core/state.py` | 1 jam |
| F5-07 | Update semua WS handlers yang membaca state | `server/handlers/ws/*.py` | 2 jam |
| F5-08 | Regression test untuk seluruh playback flow | `tests/integration/` | 4 jam |

**Acceptance criteria Fase 5:** Tidak ada modul yang menulis ke state milik modul lain. Setiap state field memiliki satu owner yang jelas.

---

### FASE 6 — start.py Decomposition (Estimasi: 2-3 hari)
*Dapat dilakukan paralel dengan Fase 3-5.*

| ID | Task | File | Effort |
|---|---|---|---|
| F6-01 | Ekstrak `ServerProcessManager` ke `launcher/process.py` | Baru | 1 jam |
| F6-02 | Ekstrak `DependencyChecker` ke `launcher/checker.py` | Baru | 30 menit |
| F6-03 | Ekstrak semua Tkinter GUI ke `launcher/gui.py` | Baru | 2 jam |
| F6-04 | Ekstrak headless CLI launcher ke `launcher/cli.py` | Baru | 1 jam |
| F6-05 | `start.py` menjadi entrypoint tipis yang detect GUI/headless | `start.py` | 30 menit |
| F6-06 | Buat unit test untuk `DependencyChecker` dan `ServerProcessManager` | `tests/unit/launcher/` | 2 jam |

**Acceptance criteria Fase 6:** `start.py` < 50 baris. `ServerProcessManager` dapat ditest tanpa Tkinter.

---

## TIMELINE IMPLEMENTASI

```
Week 1-2:    FASE 0 (Quick Wins)
             ↓
Week 3-4:    FASE 1 (Repository Pattern)
             ↓
Week 5-6:    FASE 2 (WS Context Object) + FASE 6 paralel (start.py)
             ↓
Week 7-8:    FASE 3 (STATS Coupling)
             ↓
Week 9-11:   FASE 4 (log_config Decomposition)
             ↓
Week 12-16:  FASE 5 (AppState Ownership) — feature freeze sprint
```

**Total estimasi:** 12-18 hari dev (4-6 minggu dengan 2-3 developer)

---

## ATURAN REFACTORING

Selama refactoring, tim harus mematuhi:

1. **Refactor = test dulu.** Sebelum memindah kode, pastikan ada test yang cover behavior tersebut. Jika tidak ada, tulis dulu testnya.
2. **Satu Fase = satu PR per task (F1-01, F1-02, dst).** Jangan gabungkan Fase yang berbeda dalam satu PR.
3. **Green setelah setiap commit.** CI harus pass sebelum PR di-merge.
4. **No breaking change di public API** (WS message format, HTTP endpoints) kecuali di Fase 5 yang sudah dijadwalkan.
5. **Hapus komentar `PATCH-XX` hanya setelah** test untuk behavior tersebut sudah ditulis.

---

## QUICK REFERENCE: FILE PRIORITY

| File | Masalah Utama | Priority |
|---|---|---|
| `core/log_config.py` | God Object, 477 baris, 7 tanggung jawab | 🔴 High |
| `start.py` | 866 baris, 2 program, branding lama | 🔴 High |
| `core/bootstrap.py` | 28 imports, deferred imports, too many deps | 🟠 Medium |
| `server/services/discover_service.py` | Bypass repository, SQL duplikat | 🟠 Medium |
| `server/handlers/ws/*.py` | 7-arg primitive obsession | 🟠 Medium |
| `engine/playback/controller.py` | STATS coupling | 🟠 Medium |
| `engine/mpv_controller.py` | `import time` di akhir file | 🟡 Low |
| `server/handlers/websocket.py` | `import asyncio` duplikat | 🟡 Low |

---

*Laporan ini dihasilkan oleh tim audit software LunaWave. Seluruh temuan diverifikasi manual terhadap source code aktual.*
