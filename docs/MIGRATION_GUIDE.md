---
title : LunaWave Migration Guide
last_verified: 2026-07-10
progress: Tahap 0 (belum mulai) → Tahap 12 (selesai)
current_tahap: 0
---

# LunaWave → Kompas: Bridge Migration Guide (Lengkap)

> **Filosofi:** Ini bukan rewrite. Ini serangkaian move kecil yang aman, satu per satu.
> App harus tetap jalan setelah setiap langkah. Tidak ada "big bang refactor."
>
> **Cara pakai dokumen ini:** Kerjakan satu tahap per sprint. Setiap tahap punya
> langkah konkret → verifikasi → baru lanjut ke tahap berikutnya.

---

## Peta Gap Lengkap

| Layer | Sekarang | Impian | Status |
|-------|----------|--------|--------|
| Backend `.py` (kode) | 54 file | ~80 file | Tahap 1–7 |
| Backend `.py` (test) | 0 file | ~65 unit + ~4 integration | Tahap 8 |
| Frontend `.js` | 23 file, 2.813 baris | ~32 file | Tahap 9 |
| Frontend `.css` | 22 file, 3.274 baris | ~24–26 file | Tahap 10 |
| Frontend `.html` | 1 file, 677 baris | 1 file (tidak dipecah) | — |
| Config tooling | 0 file | 3 file | Tahap 11 |
| DevOps CI/CD | CI tidak jujur | CI berfungsi nyata | Tahap 11 |
| ADR | 0 file | 6 file | Tahap 12 |
| Docs baru | 0 | 8 file | Tahap 12 |
| Open source readiness | Partial | Lengkap | Tahap 12 |
| File > 200 baris | ~12 file | ~0 | — |

---

## Aturan Emas (Baca Ini Dulu)

1. **Backward-compat alias wajib ada** — setiap kali file dipindah, file lama diubah jadi satu baris: `from new_location import X`
2. **Test setelah setiap extract** — jalankan app, play satu lagu, pastikan tidak ada `ImportError`
3. **Satu PR per tahap** — jangan campur 2 tahap dalam satu commit
4. **Jangan hapus file lama** sampai semua import sudah diupdate di seluruh codebase
5. **PATCHLOG.md wajib diupdate** setelah setiap tahap selesai
6. **File ✅ jangan disentuh** kecuali ada bug nyata

---

## Peta Risiko (Referensi Cepat)

| Risiko | Yang Termasuk |
|--------|--------------|
| **Nol** | Pindah file tanpa ubah logic: `export_to_sqlite.py`, `schema.sql`, konstanta `CMD_*`, `ConnectionManager` |
| **Rendah** | 1 file dipecah, logic tidak berubah: `websocket.py`, `config.py`, `lyrics.py`, `utils.js`, `audio.js` |
| **Sedang** | Folder baru, banyak import berubah: `adapters/`, `persistence/`, `engine/radio/`, `launcher/gui/` |
| **Tinggi** | Closure kompleks, referensi silang: `playback/controller.py`, `player-events.js` |
| **Opsional** | CSS — hanya kalau cascade bisa dipisah bersih: `player-bar.css`, `cards.css` |

---

## BACKEND PYTHON

---

## Tahap 1 — Setup Pondasi

Tidak mengubah logic apapun. Buat folder + file kosong supaya import path baru sudah bisa ditulis.

### 1.1 Buat folder dan `__init__.py` kosong

```bash
mkdir -p adapters/mpv adapters/ytdlp
mkdir -p engine/radio
mkdir -p persistence
mkdir -p launcher/gui

touch adapters/__init__.py
touch adapters/mpv/__init__.py
touch adapters/ytdlp/__init__.py
touch engine/radio/__init__.py
touch persistence/__init__.py
touch launcher/gui/__init__.py
```

### 1.2 Pisah `core/commands.py`

Ini paling aman — hanya memindahkan konstanta, tidak ada logic.

**Buka `core/command_bus.py`**, cari semua konstanta `CMD_*`, pindahkan ke file baru:

```python
# core/commands.py  — BARU
# Konstanta CMD dipisah dari command_bus.py
# agar bisa diimport tanpa menarik seluruh CommandBus

CMD_PLAY = "play"
CMD_PAUSE = "pause"
CMD_STOP = "stop"
CMD_NEXT = "next"
CMD_PREV = "prev"
CMD_SEEK = "seek"
CMD_SET_VOLUME = "set_volume"
CMD_ADD_TRACK = "add_track"
CMD_REMOVE_TRACK = "remove_track"
CMD_CLEAR_QUEUE = "clear_queue"
CMD_SET_MODE = "set_mode"
CMD_DOWNLOAD = "download"
# Salin semua CMD_* lain yang ada di command_bus.py
```

**Update `core/command_bus.py`** — tambahkan re-export di bagian atas:

```python
# Tambahkan di atas core/command_bus.py:
from core.commands import *  # noqa: F401, F403 — backward compat
```

**Verifikasi:** `python -c "from core.command_bus import CMD_PLAY; print(CMD_PLAY)"` harus print `"play"`.

### 1.3 Pisah `config_security.py`

```python
# config_security.py  — BARU
import secrets
import string
from core.security import hash_password

def generate_admin_password() -> tuple[str, str]:
    """Generate password acak + hash-nya. Return (plain, hashed)."""
    alphabet = string.ascii_letters + string.digits
    plain = ''.join(secrets.choice(alphabet) for _ in range(16))
    hashed = hash_password(plain)
    return plain, hashed
```

Lalu di `config.py`, ganti logika password generation dengan:

```python
# Di config.py — ganti inline password gen dengan:
from config_security import generate_admin_password
# Gunakan generate_admin_password() di tempat yang sebelumnya generate inline
```

**Verifikasi:** `python -c "from config_security import generate_admin_password; p, h = generate_admin_password(); print(len(p), len(h))"` harus print dua angka.

---

## Tahap 2 — Extract `persistence/` dari `cache/db.py`

Ini tahap paling impactful tapi paling hati-hati. `cache/db.py` (388 baris) adalah monolith yang memegang koneksi SQLite + semua repository domain sekaligus.

Strategi: **facade pattern** — `cache/db.py` tetap ada sebagai alias, semua import lama tetap jalan.

### 2.1 Buat `persistence/db.py` (koneksi + init saja)

```python
# persistence/db.py  — BARU
import aiosqlite
import structlog
from pathlib import Path
from config import DB_PATH

logger = structlog.get_logger(__name__)

class DatabaseConnection:
    """Handle koneksi SQLite saja. Tidak tahu domain (track, artist, dll.)."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._conn = None

    @property
    def conn(self):
        return self._conn

    async def init(self, schema_path: Path):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        await self._conn.executescript(schema_sql)

    async def close(self):
        if self._conn:
            await self._conn.close()
```

### 2.2 Buat repo terpisah — satu per satu

Ambil method yang sesuai dari `cache/db.py`, pindahkan ke file repo masing-masing.

**`persistence/track_repo.py`:**
```python
# persistence/track_repo.py  — BARU
import structlog
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

class TrackRepository:
    def __init__(self, conn):
        self._conn = conn

    async def get_track(self, video_id: str) -> TrackInfo | None:
        # Pindahkan method get_track dari cache/db.py
        ...

    async def upsert_track(self, track: TrackInfo) -> None:
        # Pindahkan method upsert_track
        ...

    async def set_local_path(self, video_id: str, path: str) -> None:
        ...

    async def increment_play_count(self, video_id: str) -> None:
        ...

    async def evict_stale_tracks(self) -> int:
        ...
```

Buat file yang sama untuk:
- `persistence/session_repo.py` ← method session dari `cache/db.py`
- `persistence/artist_repo.py` ← method artist
- `persistence/genre_repo.py` ← method genre
- `persistence/library_repo.py` ← method get_recent, get_favorites, get_cached

### 2.3 Pindah `schema.sql`

```bash
cp cache/schema.sql persistence/schema.sql
# Biarkan cache/schema.sql tetap ada dulu (hapus nanti di Tahap 8)
```

### 2.4 Update `persistence/__init__.py` — facade backward-compat

```python
# persistence/__init__.py  — UPDATE
from persistence.db import DatabaseConnection
from persistence.track_repo import TrackRepository
from persistence.session_repo import SessionRepository
from persistence.artist_repo import ArtistRepository
from persistence.genre_repo import GenreRepository
from persistence.library_repo import LibraryRepository
from pathlib import Path

class Database:
    """
    Backward-compat wrapper. Semua method delegate ke repo masing-masing.
    Kode lama yang pakai `db.get_track()` tetap jalan tanpa ubah apapun.
    """

    def __init__(self, db_path=None):
        from config import DB_PATH
        self._db = DatabaseConnection(db_path or DB_PATH)
        self._tracks: TrackRepository = None
        self._sessions: SessionRepository = None
        self._artists: ArtistRepository = None
        self._genres: GenreRepository = None
        self._library: LibraryRepository = None

    async def init(self):
        schema_path = Path(__file__).parent / "schema.sql"
        await self._db.init(schema_path)
        # Jalankan migrasi ALTER TABLE (sama seperti cache/db.py lama)
        for sql in [
            "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0",
            "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0",
            "ALTER TABLE genres ADD COLUMN click_count INTEGER DEFAULT 0",
        ]:
            try:
                await self._db.conn.execute(sql)
                await self._db.conn.commit()
            except Exception:
                pass
        self._tracks = TrackRepository(self._db.conn)
        self._sessions = SessionRepository(self._db.conn)
        self._artists = ArtistRepository(self._db.conn)
        self._genres = GenreRepository(self._db.conn)
        self._library = LibraryRepository(self._db.conn)

    # Delegate semua method ke repo yang tepat:
    async def get_track(self, *a, **kw): return await self._tracks.get_track(*a, **kw)
    async def upsert_track(self, *a, **kw): return await self._tracks.upsert_track(*a, **kw)
    async def set_local_path(self, *a, **kw): return await self._tracks.set_local_path(*a, **kw)
    async def increment_play_count(self, *a, **kw): return await self._tracks.increment_play_count(*a, **kw)
    async def evict_stale_tracks(self, *a, **kw): return await self._tracks.evict_stale_tracks(*a, **kw)
    # ... lanjutkan untuk semua method lain (session, artist, genre, library)
```

### 2.5 Update `cache/db.py` — jadikan alias

```python
# cache/db.py  — ganti isi dengan alias
# backward compat — semua import lama tetap jalan
from persistence import Database  # noqa: F401
```

**Verifikasi:** `python -c "from cache.db import Database; print('OK')"` harus print OK. Jalankan app penuh, play satu lagu.

---

## Tahap 3 — Extract `adapters/mpv/`

`engine/mpv_controller.py` (306 baris) mencampur tiga tanggung jawab: koneksi socket, IPC, dan event observer.

### 3.1 `adapters/mpv/connection.py`

Pisahkan logika connect/reconnect/close dari `engine/mpv_controller.py`:

```python
# adapters/mpv/connection.py  — BARU
import asyncio
import structlog
import os
from config import MPV_SOCKET

logger = structlog.get_logger(__name__)

class MpvConnection:
    """Handle buka/tutup/reconnect socket ke MPV. Tidak tahu tentang playback."""

    def __init__(self, socket_path=None, tcp_port=None):
        self.socket_path = socket_path or MPV_SOCKET
        self.tcp_port = tcp_port or os.environ.get("YT_PLAYER_MPV_PORT", "12345")
        self._reader = None
        self._writer = None
        self.is_connected = False
        self._reconnect_lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Connect ke MPV socket. Return True jika sukses."""
        # Pindahkan logika connect dari mpv_controller.py ke sini
        ...

    async def disconnect(self):
        ...

    async def reconnect(self) -> bool:
        async with self._reconnect_lock:
            await self.disconnect()
            return await self.connect()
```

### 3.2 `adapters/mpv/ipc.py`

```python
# adapters/mpv/ipc.py  — BARU
import asyncio
import json
import structlog

logger = structlog.get_logger(__name__)

class MpvIPC:
    """Send/receive JSON IPC ke MPV. Tidak tahu tentang event domain."""

    def __init__(self, connection):
        self._conn = connection
        self._request_id = 0
        self._pending: dict[int, asyncio.Future] = {}
        self._req_lock = asyncio.Lock()

    async def send_command(self, command: list):
        # Pindahkan _send_command + logic pending futures dari mpv_controller.py
        ...

    async def get_property(self, prop: str):
        return await self.send_command(["get_property", prop])

    async def set_property(self, prop: str, value):
        return await self.send_command(["set_property", prop, value])
```

### 3.3 `adapters/mpv/observer.py`

```python
# adapters/mpv/observer.py  — BARU
import asyncio
import structlog
from core.event_bus import EventBus

logger = structlog.get_logger(__name__)

class MpvObserver:
    """Baca event dari MPV socket, publish ke EventBus sebagai DomainEvent."""

    def __init__(self, connection, ipc, event_bus: EventBus, room_id="default"):
        self._conn = connection
        self._ipc = ipc
        self._bus = event_bus
        self._room_id = room_id
        self._task = None

    async def start(self):
        self._task = asyncio.create_task(self._observe_loop(), name="mpv-observer")

    async def stop(self):
        if self._task:
            self._task.cancel()

    async def _observe_loop(self):
        # Pindahkan logika observer loop dari mpv_controller.py
        ...
```

### 3.4 `adapters/mpv/__init__.py` — facade MpvController

```python
# adapters/mpv/__init__.py  — UPDATE
from adapters.mpv.connection import MpvConnection
from adapters.mpv.ipc import MpvIPC
from adapters.mpv.observer import MpvObserver

class MpvController:
    """
    Facade — API publik identik dengan engine/mpv_controller.py lama.
    Tidak ada kode lain yang perlu berubah.
    """

    def __init__(self, socket_path=None, tcp_port=None, event_bus=None, room_id="default"):
        self._conn = MpvConnection(socket_path, tcp_port)
        self._ipc = MpvIPC(self._conn)
        self._observer = MpvObserver(self._conn, self._ipc, event_bus, room_id)
        self._room_id = room_id

    @property
    def is_connected(self):
        return self._conn.is_connected

    async def connect(self): return await self._conn.connect()
    async def play(self, url, **opts): return await self._ipc.send_command(["loadfile", url, "replace"])
    async def pause(self): return await self._ipc.set_property("pause", True)
    async def resume(self): return await self._ipc.set_property("pause", False)
    async def stop(self): return await self._ipc.send_command(["stop"])
    async def seek(self, pos): return await self._ipc.send_command(["seek", pos, "absolute"])
    async def set_volume(self, vol): return await self._ipc.set_property("volume", vol)
    async def get_property(self, prop): return await self._ipc.get_property(prop)
    async def start_observer(self): return await self._observer.start()
    async def stop_observer(self): return await self._observer.stop()
    # ... tambahkan semua method public lain dari mpv_controller.py lama
```

### 3.5 Update `engine/mpv_controller.py` — jadikan alias

```python
# engine/mpv_controller.py  — ganti isi dengan:
from adapters.mpv import MpvController  # noqa: F401 — backward compat
```

**Verifikasi:** Jalankan app, test play/pause/seek. Tidak boleh ada perubahan perilaku.

---

## Tahap 4 — Extract `adapters/ytdlp/`

Pola sama dengan Tahap 3, tapi lebih mudah karena `ytdlp_client.py` sudah lebih clean.

### 4.1 Bagi method dari `engine/ytdlp_client.py`

```python
# adapters/ytdlp/searcher.py  — BARU
class YtDlpSearcher:
    """search(query) → list[TrackInfo]"""
    async def search(self, query: str, max_results: int = 5) -> list:
        # Pindahkan logika search dari ytdlp_client.py
        ...

# adapters/ytdlp/resolver.py  — BARU
class YtDlpResolver:
    """get_stream_url(video_id) → str"""
    async def get_stream_url(self, video_id: str) -> str:
        ...

# adapters/ytdlp/downloader.py  — BARU
class YtDlpDownloader:
    """download_mp3(video_id, path) + progress hook"""
    async def download_mp3(self, video_id: str, output_path, on_progress=None):
        ...
```

### 4.2 `adapters/ytdlp/__init__.py` — facade YtDlpClient

```python
# adapters/ytdlp/__init__.py  — UPDATE
from adapters.ytdlp.searcher import YtDlpSearcher
from adapters.ytdlp.resolver import YtDlpResolver
from adapters.ytdlp.downloader import YtDlpDownloader

class YtDlpClient:
    """Facade — API identik dengan engine/ytdlp_client.py lama."""

    def __init__(self):
        self._searcher = YtDlpSearcher()
        self._resolver = YtDlpResolver()
        self._downloader = YtDlpDownloader()

    async def search(self, *a, **kw): return await self._searcher.search(*a, **kw)
    async def get_stream_url(self, *a, **kw): return await self._resolver.get_stream_url(*a, **kw)
    async def download_mp3(self, *a, **kw): return await self._downloader.download_mp3(*a, **kw)
```

### 4.3 Update `engine/ytdlp_client.py` — jadikan alias

```python
# engine/ytdlp_client.py  — ganti isi dengan:
from adapters.ytdlp import YtDlpClient  # noqa: F401 — backward compat
```

**Verifikasi:** Search lagu, play, download. Semua harus jalan normal.

---

## Tahap 5 — Extract `engine/radio/`

`engine/radio_engine.py` (364 baris) adalah titik bug radio mode. Memecahnya bukan hanya arsitektur — ini isolasi titik masalah.

### 5.1 Identifikasi kelompok method

Buka `radio_engine.py`, kelompokkan method:

| Kelompok | Method (cari di file) | File Tujuan |
|----------|----------------------|-------------|
| Pilih artis & seed | `_select_artist`, `_get_artist_seed`, rotasi | `artist_selector.py` |
| Standby queue & prefetch | `_prefetch_background`, `_build_standby` | `prefetcher.py` |
| Filter & dedup | `_normalize_title`, `_is_noise`, `_is_duplicate`, `_filter_track` | `track_filter.py` |
| Orchestrator | `activate`, `deactivate`, `next_track`, event handlers | `engine.py` |

### 5.2 Pindahkan per kelompok

```python
# engine/radio/artist_selector.py  — BARU
class ArtistSelector:
    """Rotasi artis, seed selection, deduplication pool."""
    def __init__(self, db, state):
        ...
    async def select_next_artist(self) -> str: ...
    def reset_pool(self): ...

# engine/radio/prefetcher.py  — BARU
class RadioPrefetcher:
    """Standby queue, prefetch background task."""
    def __init__(self, ytdlp_client, db, state):
        ...
    async def start(self): ...
    async def stop(self): ...
    async def pop_next(self): ...

# engine/radio/track_filter.py  — BARU
# PERHATIAN: ini akar bug radio mode — test manual sangat dianjurkan setelah extract
class TrackFilter:
    """Filter durasi, noise words, normalisasi judul, deduplication."""
    def is_valid(self, track) -> bool: ...
    def normalize_title(self, title: str) -> str: ...
    def is_duplicate(self, track, history: list) -> bool: ...

# engine/radio/engine.py  — BARU
class RadioMode:
    """Orchestrator radio: activate, deactivate, auto-next."""
    def __init__(self, artist_selector, prefetcher, track_filter, event_bus, command_bus):
        ...
    async def activate(self): ...
    async def deactivate(self): ...
    async def next_track(self): ...
```

### 5.3 `engine/radio/__init__.py`

```python
from engine.radio.engine import RadioMode  # noqa: F401
```

### 5.4 Update `engine/radio_engine.py` — jadikan alias

```python
# engine/radio_engine.py  — ganti isi dengan:
from engine.radio import RadioMode  # noqa: F401 — backward compat
```

**Verifikasi:** Aktifkan radio mode, biarkan berjalan beberapa track. Cek tidak ada auto-next yang stuck.

---

## Tahap 6 — Pecah `engine/playback/controller.py`

`controller.py` (377 baris) mencampur orchestrator + queue ops + mode ops.

### 6.1 Extract `queue_ops.py`

```python
# engine/playback/queue_ops.py  — BARU
class QueueOps:
    """
    Semua operasi queue: select, add, remove, reorder, replace, enqueue artist/genre.
    Dipanggil oleh controller, bukan berdiri sendiri.
    """
    def __init__(self, state, db, event_bus):
        ...
    async def queue_select(self, index: int): ...
    async def add_track(self, track): ...
    async def remove_track(self, index: int): ...
    async def reorder(self, from_idx: int, to_idx: int): ...
    async def replace_queue(self, tracks: list): ...
    async def enqueue_artist(self, artist_name: str): ...
    async def enqueue_genre(self, genre_name: str): ...
```

### 6.2 Extract `mode_ops.py`

```python
# engine/playback/mode_ops.py  — BARU
class ModeOps:
    """Set mode, audio output, sponsorblock, radio randomize."""
    def __init__(self, state, command_bus, event_bus):
        ...
    async def set_mode(self, mode): ...
    async def set_output(self, output): ...
    async def toggle_sponsorblock(self): ...
    async def randomize(self): ...
```

### 6.3 Update `controller.py` — slim down

```python
# engine/playback/controller.py  — UPDATE (bukan ganti, tapi slim down)
from engine.playback.queue_ops import QueueOps
from engine.playback.mode_ops import ModeOps

class PlaybackController:
    def __init__(self, ...):
        ...
        self._queue_ops = QueueOps(self._state, self._db, self._bus)
        self._mode_ops = ModeOps(self._state, self._command_bus, self._bus)

    # Delegate ke sub-modul:
    async def queue_select(self, *a, **kw): return await self._queue_ops.queue_select(*a, **kw)
    async def set_mode(self, *a, **kw): return await self._mode_ops.set_mode(*a, **kw)
    # ... play, pause, next, prev, seek tetap di controller (orchestrator)
```

**Verifikasi:** Test play/pause/next/prev, ganti mode, tambah ke queue, remove dari queue.

---

## Tahap 7 — Extract `server/` WebSocket + `launcher/gui/`

### 7.1 Extract `server/connection_manager.py`

Pisahkan `ConnectionManager` dari `server/handlers/websocket.py`:

```python
# server/connection_manager.py  — BARU
import asyncio
from aiohttp import web
import structlog

logger = structlog.get_logger(__name__)

class ConnectionManager:
    """Track semua WS connections. Tidak tahu tentang domain/command."""

    def __init__(self):
        self._connections: dict[str, web.WebSocketResponse] = {}
        self._lock = asyncio.Lock()

    async def add(self, ws_id: str, ws: web.WebSocketResponse):
        async with self._lock:
            self._connections[ws_id] = ws

    async def remove(self, ws_id: str):
        async with self._lock:
            self._connections.pop(ws_id, None)

    async def broadcast(self, message: dict):
        import json
        text = json.dumps(message)
        dead = []
        for ws_id, ws in list(self._connections.items()):
            try:
                await ws.send_str(text)
            except Exception:
                dead.append(ws_id)
        for ws_id in dead:
            await self.remove(ws_id)

    async def send_to(self, ws_id: str, message: dict):
        import json
        ws = self._connections.get(ws_id)
        if ws:
            await ws.send_str(json.dumps(message))

    @property
    def count(self) -> int:
        return len(self._connections)
```

### 7.2 Extract WS handler per domain

Ambil dari `server/handlers/websocket.py`:

```python
# server/handlers/ws_playback.py  — BARU
# Handler untuk: play, pause, next, prev, seek, set_mode, set_output, lyrics_offset
async def handle_playback_command(cmd: str, data: dict, controller, ws_id: str):
    ...

# server/handlers/ws_queue.py  — BARU
# Handler untuk: queue_select, add_track, remove_track, reorder, enqueue_artist/genre
async def handle_queue_command(cmd: str, data: dict, controller, ws_id: str):
    ...

# server/handlers/ws_discovery.py  — BARU
# Handler untuk: search, discover (recent, favorites, cached, artists, genres)
async def handle_discovery_command(cmd: str, data: dict, discover_service, ws_id: str):
    ...

# server/handlers/ws_download.py  — BARU
# Handler untuk: download, delete_download
async def handle_download_command(cmd: str, data: dict, download_manager, ws_id: str):
    ...
```

Slim down `server/handlers/websocket.py` — tinggal lifecycle + routing:

```python
# server/handlers/websocket.py  — setelah dipecah, tinggal ~80 baris
from server.connection_manager import ConnectionManager
from server.handlers.ws_playback import handle_playback_command
from server.handlers.ws_queue import handle_queue_command
from server.handlers.ws_discovery import handle_discovery_command
from server.handlers.ws_download import handle_download_command

PLAYBACK_CMDS = {"play", "pause", "next", "prev", "seek", "set_mode", "set_output", "lyrics_offset"}
QUEUE_CMDS = {"queue_select", "add_track", "remove_track", "reorder", "enqueue_artist", "enqueue_genre"}
DISCOVERY_CMDS = {"search", "discover"}
DOWNLOAD_CMDS = {"download", "delete_download"}

async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    ws_id = str(id(ws))
    await connection_manager.add(ws_id, ws)
    try:
        async for msg in ws:
            data = json.loads(msg.data)
            cmd = data.get("cmd")
            if cmd in PLAYBACK_CMDS:
                await handle_playback_command(cmd, data, controller, ws_id)
            elif cmd in QUEUE_CMDS:
                await handle_queue_command(cmd, data, controller, ws_id)
            elif cmd in DISCOVERY_CMDS:
                await handle_discovery_command(cmd, data, discover_service, ws_id)
            elif cmd in DOWNLOAD_CMDS:
                await handle_download_command(cmd, data, download_manager, ws_id)
    finally:
        await connection_manager.remove(ws_id)
    return ws
```

**Verifikasi:** Test setiap jenis command dari UI browser.

### 7.3 Extract `launcher/gui/`

`launcher/gui.py` (756 baris!) dipecah:

```python
# launcher/gui/dep_checker.py  — BARU, MULAI DARI SINI (paling independen)
import shutil

class DependencyChecker:
    """Cek ketersediaan mpv, yt-dlp, python version."""
    REQUIRED = {"mpv": "mpv", "yt-dlp": "yt-dlp"}

    def check_all(self) -> dict[str, bool]:
        return {name: bool(shutil.which(cmd)) for name, cmd in self.REQUIRED.items()}

    def all_ok(self) -> bool:
        return all(self.check_all().values())

# launcher/gui/log_panel.py  — BARU
import tkinter as tk
from tkinter import scrolledtext

class LogPanel:
    """ScrolledText log viewer + auto-scroll + level filter."""
    def __init__(self, parent):
        self._widget = scrolledtext.ScrolledText(parent, state="disabled", height=15)
    def append(self, text: str): ...
    def clear(self): ...
    def widget(self): return self._widget

# launcher/gui/status_panel.py  — BARU
class StatusPanel:
    """Tampilkan status server: port, PID, uptime, connection count."""
    def __init__(self, parent):
        ...
    def update(self, status: dict): ...

# launcher/gui/ui_builder.py  — BARU
import tkinter as tk
class UIBuilder:
    """Build semua widget Tkinter. Tidak ada business logic di sini."""
    def build(self, root: tk.Tk, callbacks: dict) -> dict:
        """Return dict of widget references."""
        ...

# launcher/gui/app.py  — BARU
from launcher.gui.ui_builder import UIBuilder
from launcher.gui.log_panel import LogPanel
from launcher.gui.status_panel import StatusPanel
from launcher.gui.dep_checker import DependencyChecker

class ServerManager:
    """Main window + server lifecycle."""
    def __init__(self):
        self._dep_checker = DependencyChecker()
        self._log_panel = None
        self._status_panel = None
    def run(self): ...
    def start_server(self): ...
    def stop_server(self): ...
```

`launcher/gui/__init__.py`:
```python
from launcher.gui.app import ServerManager  # noqa: F401
```

`launcher/gui.py` — jadikan alias:
```python
from launcher.gui import ServerManager  # noqa: F401 — backward compat
```

**Verifikasi:** Jalankan `python start.py`, GUI harus muncul dan bisa start/stop server.

---

## Tahap 8 — Bersihkan Sisa

### 8.1 Pindah `data/export_to_sqlite.py` ke `scripts/`

```bash
mv data/export_to_sqlite.py scripts/export_to_sqlite.py
```

Update semua referensi (kemungkinan hanya di README).

### 8.2 Hapus duplikasi `schema.sql`

Setelah memastikan `persistence/schema.sql` sudah dipakai di mana-mana:

```bash
# Cek dulu tidak ada yang masih import dari cache/schema.sql
grep -r "cache/schema" . --include="*.py"
# Kalau kosong:
rm cache/schema.sql
```

### 8.3 Opsional — pisah `plugins/lyrics.py`

Kalau `lyrics.py` sudah > 200 baris:

```python
# plugins/lyrics_fetcher.py   ← HTTP request ke lrclib.net
# plugins/lyrics_parser.py    ← parse format LRC → [(timestamp, line)]
# plugins/lyrics_sync.py      ← sync posisi via TrackProgressEvent
```

`plugins/lyrics.py` → jadikan alias:
```python
from plugins.lyrics_fetcher import LyricsFetcher
from plugins.lyrics_parser import LyricsParser
from plugins.lyrics_sync import LyricsSync
```

---

## FRONTEND JAVASCRIPT

---

## Tahap 9 — Pecah File JS Besar

**Catatan penting sebelum mulai:** Frontend pakai vanilla JS tanpa module bundler. Setiap file baru harus ditambahkan ke `index.html` via `<script>` tag, **dalam urutan yang benar** (dependencies harus dimuat sebelum file yang menggunakannya).

### 9.1 Pecah `events/player-events.js` (425 baris → 6 file)

Ini file paling besar dan paling berisiko. Banyak variabel closure yang dibagi antar fungsi.

**Langkah aman:** Baca dulu seluruh file, catat semua variabel yang dibagi (`searchTimer`, `lastSearchQuery`, `isDragging`, dll.) — variabel ini harus tetap di scope yang benar.

```
events/player-events.js (425 baris)
├── events/transport-events.js     ~90 baris  ← play/pause/next/prev/radio-toggle
├── events/progress-events.js      ~50 baris  ← pointer down/move/up drag-seek
├── events/search-input-events.js  ~70 baris  ← input, clear button, header collapse
├── events/action-modal-events.js  ~40 baris  ← play now / enqueue / cancel / delete
├── events/click-delegation-events.js ~90 baris ← global click delegation
└── events/keyboard-shortcut-events.js ~30 baris ← global keydown shortcuts
```

Setelah extract, update `index.html`:
```html
<!-- Ganti satu <script src="js/events/player-events.js"> dengan: -->
<script src="js/events/transport-events.js"></script>
<script src="js/events/progress-events.js"></script>
<script src="js/events/search-input-events.js"></script>
<script src="js/events/action-modal-events.js"></script>
<script src="js/events/click-delegation-events.js"></script>
<script src="js/events/keyboard-shortcut-events.js"></script>
```

**Verifikasi:** Test setiap tombol satu per satu — play, pause, next, prev, drag progress bar, search, click queue item, keyboard shortcut.

### 9.2 Pecah `audio.js` (336 baris → 2 file)

```javascript
// audio/playback-sync.js  — BARU (~230 baris)
// getOrInitAudio, unlockBrowserAudio, syncBrowserAudio, tap-to-play logic

// audio/visualizer.js  — BARU (~100 baris)
// initVisualizer, startFakeBeatLoop, canvas animation loop
```

Update `index.html`:
```html
<!-- Ganti <script src="js/audio.js"> dengan: -->
<script src="js/audio/playback-sync.js"></script>
<script src="js/audio/visualizer.js"></script>
```

**Verifikasi:** Audio sinkronisasi saat play/pause. Visualizer animasi muncul.

### 9.3 Pecah `utils.js` (212 baris → 2 file)

```javascript
// utils/format.js  — BARU (~40 baris)
// formatTime(seconds), escapeHtml(str)

// utils/toast.js  — BARU (~170 baris)
// showConnectionToast, hideConnectionToast, showLogToast
```

**Perhatian:** Cek dulu berapa file yang `import` atau panggil fungsi dari `utils.js`:
```bash
grep -r "formatTime\|escapeHtml\|showConnectionToast\|showLogToast" web/static/js/ --include="*.js" -l
```
Semua file yang ditemukan harus tetap bisa akses fungsi-fungsi itu. Karena vanilla JS pakai global scope, cukup pastikan `utils/format.js` dan `utils/toast.js` dimuat **sebelum** file yang memakainya di `index.html`.

Update `index.html`:
```html
<!-- Ganti <script src="js/utils.js"> dengan: -->
<script src="js/utils/format.js"></script>
<script src="js/utils/toast.js"></script>
```

**Verifikasi:** Waktu di player-bar format dengan benar. Toast connection muncul saat disconnect.

### 9.4 Pecah `render/discover.js` (281 baris → 2 file)

```javascript
// render/discover-tab.js  — BARU (~180 baris)
// renderDiscoverTab, getHashtagColor, updateDiscoverPlayingState

// render/radio-tab.js  — BARU (~100 baris)
// renderRadio, renderRecentRow
```

Update `index.html`:
```html
<!-- Ganti <script src="js/render/discover.js"> dengan: -->
<script src="js/render/discover-tab.js"></script>
<script src="js/render/radio-tab.js"></script>
```

**Verifikasi:** Tab Discover tampil dengan benar. Tab Radio tampil dengan benar.

### 9.5 Slim `ws.js` (248 baris) — pindahkan render logic

`ws.js` berisi `renderFullState` dan `renderHeader` yang seharusnya ada di `render/`.

```javascript
// render/full-state.js  — BARU
// renderFullState(state), renderHeader(state), syncLocalLyrics(state)
```

`ws.js` setelah di-slim (~190 baris): hanya berisi WebSocket setup, reconnect logic, dan message routing ke fungsi render.

Update `index.html`:
```html
<!-- Tambahkan SEBELUM ws.js: -->
<script src="js/render/full-state.js"></script>
<script src="js/ws.js"></script>  <!-- tetap ada, tapi lebih slim -->
```

**Verifikasi:** Refresh halaman, state awal render dengan benar. Semua update real-time dari WS masih jalan.

---

## FRONTEND CSS

---

## Tahap 10 — CSS (Konservatif)

CSS diperlakukan berbeda dari JS/Python. **Cascade dan specificity gampang rusak** kalau dipecah asal-asalan.

**Aturan sebelum pecah CSS:** Buka DevTools, cek apakah selector di file yang akan dipecah saling referensi (nested selector, `:has()`, combinators). Kalau iya, pertimbangkan biarkan 1 file.

### Yang perlu diaudit (bukan dipecah dulu)

| File | Ukuran | Keputusan |
|------|--------|-----------|
| `components/player-bar.css` | 579 baris | **Audit dulu** — kalau layout/progress/controls bisa dipisah bersih, pecah |
| `components/cards.css` | 491 baris | **Prioritas rendah** — pecah ke `discover-cards.css` + `search-cards.css` hanya kalau memang dipakai secara terpisah |
| `platform/desktop.css` | 389 baris | **Biarkan** — "semua override desktop" sudah tepat sebagai 1 file |
| `components/settings-sheet.css` | 311 baris | **Biarkan** — pecah kalau opsi terus bertambah |

### Cara audit `player-bar.css` sebelum dipecah

```bash
# Lihat semua selector unik di file
grep -E "^\." web/static/css/components/player-bar.css | sort | head -30

# Cari selector yang mungkin lintas-concern
grep -E "\.(progress|controls|layout)" web/static/css/components/player-bar.css
```

Kalau banyak `.player-bar .controls .progress` (deeply nested, semua bergantung pada parent selector), **lebih aman biarkan 1 file**.

### Kalau memutuskan untuk pecah `player-bar.css`

```
components/player-bar.css (579 baris)
├── components/player-bar/layout.css     ← posisi, flex, grid player-bar
├── components/player-bar/progress.css   ← progress bar, drag handle, timestamp
└── components/player-bar/controls.css   ← tombol play/pause/next/prev, icon size
```

Update `index.html`:
```html
<!-- Ganti <link href="css/components/player-bar.css"> dengan: -->
<link rel="stylesheet" href="css/components/player-bar/layout.css">
<link rel="stylesheet" href="css/components/player-bar/progress.css">
<link rel="stylesheet" href="css/components/player-bar/controls.css">
```

**Verifikasi:** Buka di mobile, tablet, desktop. Cek di semua breakpoint. Cek dark/light mode kalau ada.

---

## TOOLING & DEVOPS

---

## Tahap 11 — Config, Tooling, CI

### 11.1 `requirements-dev.txt`

```
pytest>=8.0
pytest-asyncio>=0.23
pytest-cov>=5.0
ruff>=0.4
mypy>=1.10
bandit>=1.7
pip-audit>=2.7
import-linter>=2.0
```

### 11.2 `pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
select = ["E", "F", "I", "UP", "B"]
ignore = ["E501"]  # longline — handled by formatter

[tool.ruff.format]
quote-style = "double"

[tool.mypy]
python_version = "3.13"
ignore_missing_imports = true
# Mulai dari strict = false, naikkan bertahap:
# Aktifkan per-modul setelah modul itu punya coverage cukup:
# [[tool.mypy.overrides]]
# module = "core.*"
# strict = true

[tool.bandit]
exclude_dirs = ["tests", "scratch", "scripts"]

[tool.coverage.run]
source = ["core", "engine", "server", "persistence", "adapters", "services", "plugins"]
omit = [
    "launcher/gui/app.py",        # Manual QA
    "launcher/gui/ui_builder.py", # Manual QA
    "start.py",
    "*/scratch/*",
]

[tool.coverage.report]
# fail_under = 100  # Aktifkan ini setelah test suite cukup lengkap
show_missing = true
```

### 11.3 `.importlinter`

```ini
[importlinter]
root_packages = core,adapters,engine,persistence,server,services,plugins,launcher

[importlinter:contract:core-is-isolated]
name = core tidak boleh import lapisan lain
type = forbidden
source_modules = core
forbidden_modules = adapters, engine, server, persistence, services, plugins, launcher

[importlinter:contract:adapters-only-import-core]
name = adapters hanya boleh import core
type = forbidden
source_modules = adapters
forbidden_modules = engine, server, persistence, services

[importlinter:contract:persistence-only-import-core]
name = persistence hanya boleh import core
type = forbidden
source_modules = persistence
forbidden_modules = adapters, engine, server, services

[importlinter:contract:plugins-only-import-core]
name = plugins hanya boleh import core
type = forbidden
source_modules = plugins
forbidden_modules = server, launcher
```

### 11.4 `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-merge-conflict

  - repo: local
    hooks:
      - id: import-linter
        name: import-linter
        entry: lint-imports
        language: python
        pass_filenames: false
```

### 11.5 Fix CI — jadikan jujur

**Masalah saat ini:** `ci.yml` mereferensikan `requirements-dev.txt`, `tests/`, dan `pyproject.toml` yang tidak ada, jadi CI pasti gagal di step pertama.

**Opsi jujur sementara (sebelum test suite ada):**

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: pip install ruff bandit
      - run: ruff check .
      - run: bandit -r . -c pyproject.toml

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.13" }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v --cov
        # Hapus step ini sampai tests/ punya isi yang cukup
        # continue-on-error: true  # sementara kalau belum siap
```

### 11.6 `release.yml` — auto-release on tag

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ["v*.*.*"]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          generate_release_notes: true
          files: |
            requirements.txt
            requirements-dev.txt
```

---

## TESTING

---

## Tahap 12a — Setup Testing Infrastructure

### Setup awal

```bash
mkdir -p tests/unit/core tests/unit/adapters/mpv tests/unit/adapters/ytdlp
mkdir -p tests/unit/engine/radio tests/unit/engine/playback
mkdir -p tests/unit/persistence tests/unit/cache
mkdir -p tests/unit/server/handlers tests/unit/server/services
mkdir -p tests/unit/services tests/unit/plugins
mkdir -p tests/unit/launcher/gui
mkdir -p tests/integration
mkdir -p tests/fakes
mkdir -p tests/frontend/utils

touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
```

### `tests/conftest.py`

```python
import pytest
import asyncio
import aiosqlite
from pathlib import Path

@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def memory_db():
    """SQLite in-memory — murah, cepat, tidak meninggalkan file."""
    conn = await aiosqlite.connect(":memory:")
    conn.row_factory = aiosqlite.Row
    schema = (Path(__file__).parent.parent / "persistence" / "schema.sql").read_text()
    await conn.executescript(schema)
    yield conn
    await conn.close()
```

### `tests/fakes/` — implementasi Port untuk test

```python
# tests/fakes/fake_audio_player.py
from core.ports import AudioPlayerPort

class FakeAudioPlayer(AudioPlayerPort):
    """Implementasi AudioPlayerPort yang tidak pegang proses apapun."""
    def __init__(self):
        self.is_connected = True
        self.current_url = None
        self.is_paused = False
        self.volume = 80
        self.calls = []

    async def play(self, url, **opts):
        self.current_url = url
        self.is_paused = False
        self.calls.append(("play", url))

    async def pause(self):
        self.is_paused = True
        self.calls.append(("pause",))

    async def resume(self):
        self.is_paused = False
        self.calls.append(("resume",))

    async def stop(self):
        self.current_url = None
        self.calls.append(("stop",))

    async def seek(self, position: float):
        self.calls.append(("seek", position))

    async def set_volume(self, level: int):
        self.volume = level
        self.calls.append(("set_volume", level))

    async def get_property(self, prop: str):
        return None

# tests/fakes/fake_media_extractor.py
from core.ports import MediaExtractorPort
from core.state import TrackInfo

class FakeMediaExtractor(MediaExtractorPort):
    """Simulasi yt-dlp tanpa network."""
    def __init__(self, search_results=None, stream_url="http://fake-stream.mp3"):
        self._search_results = search_results or []
        self._stream_url = stream_url

    async def search(self, query: str, max_results: int = 5) -> list[TrackInfo]:
        return self._search_results[:max_results]

    async def get_stream_url(self, video_id: str) -> str:
        return f"{self._stream_url}?id={video_id}"

    async def download_mp3(self, video_id: str, output_path, on_progress=None):
        if on_progress:
            on_progress({"percent": 100, "speed": "N/A"})
        return str(output_path)

# tests/fakes/fake_lyrics_provider.py
from core.ports import LyricsProvider

class FakeLyricsProvider(LyricsProvider):
    def __init__(self, lyrics=None):
        self._lyrics = lyrics or []

    async def get_lyrics(self, title: str, artist: str) -> list:
        return self._lyrics

# tests/fakes/fake_sponsorblock_provider.py
from core.ports import SponsorBlockProvider

class FakeSponsorBlockProvider(SponsorBlockProvider):
    def __init__(self, segments=None):
        self._segments = segments or []

    async def get_segments(self, video_id: str) -> list:
        return self._segments
```

---

## Tahap 12b — Prioritas Test per Layer

Kerjakan dalam urutan ini — dari yang paling bernilai/murah ke yang paling mahal.

### Prioritas 1: `core/` dan `persistence/` — pure logic, zero I/O

```python
# tests/unit/core/test_event_bus.py — contoh
import pytest
from core.event_bus import EventBus
from core.events import TrackStartedEvent
from core.state import TrackInfo

@pytest.mark.asyncio
async def test_subscribe_and_publish():
    bus = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    bus.subscribe(TrackStartedEvent, handler)
    track = TrackInfo(video_id="abc123", title="Test", artist="Artist", duration=180)
    await bus.publish(TrackStartedEvent(track=track, room_id="default"))

    assert len(received) == 1
    assert received[0].track.video_id == "abc123"

# tests/unit/core/test_security.py
from core.security import hash_password, verify_password

def test_hash_and_verify():
    plain = "secret123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong", hashed) is False
    assert hashed != plain

# tests/unit/persistence/test_track_repo.py
import pytest
from persistence.track_repo import TrackRepository
from core.state import TrackInfo

@pytest.mark.asyncio
async def test_upsert_and_get(memory_db):
    repo = TrackRepository(memory_db)
    track = TrackInfo(video_id="xyz", title="Song", artist="Artist", duration=200)
    await repo.upsert_track(track)
    result = await repo.get_track("xyz")
    assert result is not None
    assert result.title == "Song"

@pytest.mark.asyncio
async def test_get_nonexistent(memory_db):
    repo = TrackRepository(memory_db)
    result = await repo.get_track("notexists")
    assert result is None

@pytest.mark.asyncio
async def test_increment_play_count(memory_db):
    repo = TrackRepository(memory_db)
    track = TrackInfo(video_id="abc", title="T", artist="A", duration=100)
    await repo.upsert_track(track)
    await repo.increment_play_count("abc")
    result = await repo.get_track("abc")
    assert result.play_count == 1
```

### Prioritas 2: `engine/` — domain logic dengan fakes

```python
# tests/unit/engine/radio/test_track_filter.py
# PRIORITAS TERTINGGI — akar bug radio mode
from engine.radio.track_filter import TrackFilter
from core.state import TrackInfo

def make_track(title, duration=200):
    return TrackInfo(video_id="x", title=title, artist="A", duration=duration)

def test_filter_short_track():
    f = TrackFilter()
    assert f.is_valid(make_track("Song", duration=29)) is False  # terlalu pendek

def test_filter_noise_title():
    f = TrackFilter()
    assert f.is_valid(make_track("(Official Video)")) is False

def test_normalize_removes_brackets():
    f = TrackFilter()
    assert f.normalize_title("Song Name (Official Video) [HD]") == "song name"

def test_duplicate_detection():
    f = TrackFilter()
    t1 = make_track("Song Name")
    t2 = make_track("Song Name (Remastered)")
    history = [t1]
    assert f.is_duplicate(t2, history) is True

# tests/unit/engine/test_queue_manager.py
import pytest
from engine.queue_manager import QueueManager
from core.state import TrackInfo, AppState
from tests.fakes.fake_audio_player import FakeAudioPlayer

@pytest.mark.asyncio
async def test_add_and_get():
    state = AppState()
    qm = QueueManager(state)
    track = TrackInfo(video_id="1", title="T", artist="A", duration=100)
    await qm.add_track(track)
    assert len(state.queue) == 1

@pytest.mark.asyncio
async def test_remove_track():
    state = AppState()
    qm = QueueManager(state)
    t1 = TrackInfo(video_id="1", title="T1", artist="A", duration=100)
    t2 = TrackInfo(video_id="2", title="T2", artist="A", duration=100)
    await qm.add_track(t1)
    await qm.add_track(t2)
    await qm.remove_track(0)
    assert state.queue[0].video_id == "2"
```

### Prioritas 3: Integration tests

```python
# tests/integration/test_playback_flow.py
import pytest
from core.command_bus import CommandBus
from core.event_bus import EventBus
from core.state import AppState
from core.events import TrackStartedEvent
from tests.fakes.fake_audio_player import FakeAudioPlayer
from tests.fakes.fake_media_extractor import FakeMediaExtractor

@pytest.mark.asyncio
async def test_play_command_triggers_track_started():
    bus = EventBus()
    cmd_bus = CommandBus()
    state = AppState()
    player = FakeAudioPlayer()
    extractor = FakeMediaExtractor(stream_url="http://fake.mp3")

    # Wiring minimal
    received_events = []
    bus.subscribe(TrackStartedEvent, lambda e: received_events.append(e))

    # ... setup controller dengan fake deps ...
    # await controller.play(video_id="testid")

    # assert player.current_url is not None
    # assert len(received_events) == 1
    pass  # Isi sesuai wiring controller aktual
```

### Checklist File Test (urutan prioritas)

#### Langsung mulai (pure logic):
- [ ] `tests/unit/core/test_event_bus.py`
- [ ] `tests/unit/core/test_command_bus.py`
- [ ] `tests/unit/core/test_state.py`
- [ ] `tests/unit/core/test_security.py`
- [ ] `tests/unit/core/test_events.py`
- [ ] `tests/unit/core/test_exceptions.py`
- [ ] `tests/unit/persistence/test_track_repo.py`
- [ ] `tests/unit/persistence/test_artist_repo.py`
- [ ] `tests/unit/persistence/test_genre_repo.py`
- [ ] `tests/unit/persistence/test_session_repo.py`
- [ ] `tests/unit/persistence/test_library_repo.py`
- [ ] `tests/unit/engine/radio/test_track_filter.py` ← **akar bug radio**
- [ ] `tests/unit/engine/test_queue_manager.py`
- [ ] `tests/unit/engine/playback/test_queue_ops.py`
- [ ] `tests/unit/engine/playback/test_mode_ops.py`

#### Setelah fakes tersedia (butuh mock):
- [ ] `tests/unit/engine/radio/test_artist_selector.py`
- [ ] `tests/unit/engine/radio/test_prefetcher.py`
- [ ] `tests/unit/engine/radio/test_engine.py`
- [ ] `tests/unit/engine/playback/test_controller.py`
- [ ] `tests/unit/services/test_discover_service.py`
- [ ] `tests/unit/server/test_serializers.py`
- [ ] `tests/unit/server/test_middleware.py`
- [ ] `tests/unit/server/test_connection_manager.py`
- [ ] `tests/unit/plugins/test_lyrics_parser.py`
- [ ] `tests/unit/plugins/test_lyrics_sync.py`
- [ ] `tests/unit/launcher/gui/test_dep_checker.py`

#### Integration (setelah unit tests cukup):
- [ ] `tests/integration/test_playback_flow.py`
- [ ] `tests/integration/test_websocket_flow.py`
- [ ] `tests/integration/test_radio_flow.py`
- [ ] `tests/integration/test_download_flow.py`

#### Frontend (opsional, gunakan Vitest):
- [ ] `tests/frontend/utils/format.test.js`
- [ ] `tests/frontend/test_store.test.js`

---

## DOKUMENTASI & OPEN SOURCE

---

## Tahap 13 — Docs Baru + Open Source Readiness

### 13.1 File yang perlu dibuat

| File | Isi Minimum |
|------|------------|
| `LICENSE` | MIT License — 1 file, ganti `[year]` dan `[name]` |
| `CHANGELOG.md` | Format: `## [1.0.0] — 2026-07-10` lalu bullet per perubahan |
| `CONTRIBUTING.md` | Cara fork, branch naming, commit convention, PR checklist |
| `SECURITY.md` | Cara report vulnerability, expected response time |
| `docs/ARCHITECTURE.md` | Layer diagram + dependency direction + keputusan utama |
| `docs/DEVELOPMENT.md` | Clone → install → jalankan (harus bisa diikuti dari nol) |
| `docs/TESTING.md` | Cara run test, cara tambah test, cara tambah fake |
| `docs/TROUBLESHOOTING.md` | Error umum + solusi: MPV tidak connect, yt-dlp gagal, radio stuck |
| `.editorconfig` | indent_style, charset, end_of_line |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Template laporan bug |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Template permintaan fitur |
| `.github/PULL_REQUEST_TEMPLATE.md` | Checklist PR: test, docs, linting |

### 13.2 Template `LICENSE` (MIT)

```
MIT License

Copyright (c) 2026 [Nama kamu]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 13.3 ADR — 6 file yang perlu dibuat

Format tiap ADR: **Konteks → Keputusan → Konsekuensi** (masing-masing 2–4 kalimat).

```markdown
# ADR 0001 — MPV via IPC Socket, bukan Subprocess

## Konteks
LunaWave perlu mengontrol playback audio secara real-time (seek, volume, pause)
dan menerima event (end-of-file, time-pos) tanpa polling.

## Keputusan
Gunakan MPV dengan flag `--input-ipc-server` dan kontrol via JSON IPC socket.

## Konsekuensi
+ Komunikasi dua arah tanpa polling, latensi rendah
+ MPV process terpisah dari Python — crash MPV tidak crash server
- Perlu handling reconnect kalau socket putus
- Di Windows butuh named pipe, tidak bisa Unix socket langsung
```

Buat hal yang sama untuk `0002` s.d. `0006` sesuai topik di §10.3 blueprint.

### 13.4 Open Source Checklist

- [ ] `LICENSE` — MIT, tambahkan sekarang
- [ ] `README.md` — verifikasi instruksi run-from-zero bisa diikuti dari nol (`git clone` → `cd` → ikuti README → jalan)
- [ ] `CONTRIBUTING.md` — tambahkan
- [ ] `SECURITY.md` — tambahkan
- [ ] `CHANGELOG.md` — tambahkan
- [ ] `.editorconfig` — tambahkan
- [ ] `.github/ISSUE_TEMPLATE/` — tambahkan
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` — tambahkan
- [ ] `data/lunawave.db` di `.gitignore` — verifikasi (file DB runtime tidak boleh di-commit)
- [ ] `cache/mp3/` di `.gitignore` — verifikasi
- [ ] `cache/admin_password.txt` di `.gitignore` — **tambahkan segera**, file ini ada di repo saat ini

---

## Checklist Per Tahap (Master)

Tandai ✅ setelah tahap selesai dan app masih jalan.

**Backend Python:**
- [ ] **Tahap 1** — Folder baru + `core/commands.py` + `config_security.py`
- [ ] **Tahap 2** — Extract `persistence/` dari `cache/db.py`
- [ ] **Tahap 3** — Extract `adapters/mpv/`
- [ ] **Tahap 4** — Extract `adapters/ytdlp/`
- [ ] **Tahap 5** — Extract `engine/radio/`
- [ ] **Tahap 6** — Pecah `engine/playback/controller.py`
- [ ] **Tahap 7** — Extract WS handlers + `launcher/gui/`
- [ ] **Tahap 8** — Bersihkan sisa + opsional `plugins/lyrics/`

**Frontend:**
- [ ] **Tahap 9** — Pecah 5 file JS besar
- [ ] **Tahap 10** — Audit CSS, pecah kalau aman

**Tooling:**
- [ ] **Tahap 11** — `requirements-dev.txt`, `pyproject.toml`, `.importlinter`, fix CI

**Testing:**
- [ ] **Tahap 12a** — Setup folder + fakes + conftest
- [ ] **Tahap 12b** — Isi test, mulai dari `core/` dan `persistence/`

**Docs:**
- [ ] **Tahap 13** — `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, 6 ADR, 4 docs baru

---

*Dibuat berdasarkan source code `lunawave/` aktual + `bridge_to_kompas_v2.md`*
*Terakhir diupdate: 2026-07-10*
