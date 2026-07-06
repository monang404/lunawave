# BACKEND AUDIT — ytgui-main
**Source of Truth:** Active Python files only (`.backup_patchlog` diabaikan)  
**Audit Scope:** Business Logic · Transaction · Exception · Concurrency · Caching · Queue · Retry · Repository · Service · Dependency · Layering  
**Total Files Audited:** ~50 Python modules aktif

---

## 1. ARSITEKTUR & LAYERING

### Struktur Layer (Actual)

```
┌─────────────────────────────────────────────────────────┐
│  ENTRY POINTS                                           │
│  main.py (bootstrap)  ·  start.py (GUI manager)        │
├─────────────────────────────────────────────────────────┤
│  TRANSPORT / PROTOCOL LAYER                             │
│  server/handlers/websocket.py  ·  server/handlers/http.py │
│  server/handlers/auth.py  ·  server/middleware.py       │
├─────────────────────────────────────────────────────────┤
│  APPLICATION / SERVICE LAYER                            │
│  server/services/broadcast_service.py                   │
│  server/services/stream_prefetch.py                     │
│  services/discover_service.py                           │
│  server/handlers/event_listeners.py                     │
├─────────────────────────────────────────────────────────┤
│  DOMAIN / ENGINE LAYER                                  │
│  engine/playback/controller.py  ←  core controller      │
│  engine/queue_manager.py  ·  engine/radio_engine.py     │
│  engine/volume_service.py  ·  engine/download_manager.py│
│  engine/playback/track_loader.py                        │
├─────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                   │
│  engine/mpv_controller.py  (external process: MPV)      │
│  engine/ytdlp_client.py    (external: yt-dlp/YouTube)  │
│  cache/db.py               (SQLite via aiosqlite)       │
│  cache/resolver.py         (URL resolution + TTL)       │
├─────────────────────────────────────────────────────────┤
│  CORE / SHARED KERNEL                                   │
│  core/event_bus.py  ·  core/command_bus.py              │
│  core/state.py  ·  core/ports.py  ·  core/events.py    │
│  core/exceptions.py  ·  core/security.py               │
│  core/observability.py  ·  core/task_utils.py          │
├─────────────────────────────────────────────────────────┤
│  PLUGINS (optional, decoupled)                          │
│  plugins/lyrics.py  ·  plugins/sponsorblock.py         │
│  plugins/notifications.py                               │
└─────────────────────────────────────────────────────────┘
```

### Penilaian Layering

| Aspek | Status | Catatan |
|---|---|---|
| Layer separation | ✅ BAIK | 6 layer jelas, masing-masing tahu tugas sendiri |
| Dependency direction | ✅ BAIK | Selalu ke bawah (transport → domain → infra) |
| Core isolation | ✅ BAIK | `core/` tidak import layer lain |
| Plugin isolation | ✅ BAIK | Plugin inject via constructor, bukan import langsung |
| Cross-layer leak | ⚠️ MINOR | `event_listeners.py` langsung import `DiscoverService` dan buat object inline — ini mestinya diinjek dari `app.py` |
| Service placement | ⚠️ MINOR | `services/discover_service.py` ada di root `/services/`, bukan `/server/services/` — inkonsisten dengan service lain |

---

## 2. BUSINESS LOGIC

### 2.1 Playback Orchestration (`engine/playback/controller.py`)

**Core business rules yang diimplementasikan:**

- **Track history**: Setiap track yang dimainkan di-push ke `state.history` (maxlen=50) sebelum diganti.
- **Status machine**: `IDLE → LOADING → PLAYING ↔ PAUSED → ERROR`. Transisi dikelola ketat di `play_track()` dan event handler.
- **Mode isolation**: Radio Mode dan Queue Mode adalah dua state machine yang _share_ controller tapi punya queue terpisah (`state.queue` vs `state.radio_queue`). Rule eksplisit: Radio **tidak boleh** baca/tulis `state.queue`.
- **Audio output routing**: Saat `audio_output == BROWSER`, MPV di-set volume 0 (silent). Browser stream via `/api/stream/{video_id}`. Logic ini diterapkan di `play_track()` dan `_on_set_output()`.
- **SponsorBlock enforcement**: `sponsorblock.py` subscribe ke setiap `TrackProgressEvent`. Jika position masuk segment → `mpv.seek(end)`.
- **Lyric sync**: `lyrics.py` subscribe ke `TrackProgressEvent`, pakai `bisect_right` untuk cari lyric aktif berdasarkan timestamp — O(log n).

### 2.2 Stream URL Resolution (`cache/resolver.py`)

Priority rules:
1. **Local file** → return path langsung (tidak butuh network)
2. **Stream URL fresh** (< `STREAM_URL_TTL_SEC = 21600` = 6 jam) → return dari DB cache
3. **Stale/missing** → `ytdlp.get_stream_url()` → simpan ke DB → return

**Bug ditemukan:**
```python
# resolver.py line ~17
if row and row.local_path:
    path = row.local_path
    import asyncio  # ← import di dalam function (bukan fatal tapi buruk)
    if await asyncio.to_thread(os.path.isfile, path):
```
`os.path.isfile` dijalankan via `asyncio.to_thread` — benar karena I/O blocking — tapi `import asyncio` di dalam loop setiap call adalah style buruk.

### 2.3 Radio Mode (`engine/radio_engine.py`)

Business logic prefetch agresif:
- **Standby buffer 12 lagu**: Disiapkan di background setelah batch pertama dipakai
- **Quick batch 2 artis** → langsung putar → **backfill 2 artis** → **build standby**
- **Prefetch stream URL**: Triggered saat `duration - position <= 30.0` (sisa 30 detik)
- **Exclusion set**: Menghindari lagu yang sedang putar + radio_queue + 20 terakhir dari history

**Masalah:**
```python
# radio_engine.py
async def _backfill_and_standby(self, controller):
    if self._fetch_lock.locked():  # ← race condition: lock bisa diambil setelah check ini
        return
    async with self._fetch_lock:
        ...
```
Ada **TOCTOU race** (Time-of-Check-Time-of-Use): Setelah `if self._fetch_lock.locked()` return False, sebelum `async with self._fetch_lock:` dieksekusi, coroutine lain bisa mengambil lock. Efek: backfill kadang diskip tidak perlu.

---

## 3. TRANSACTION

### 3.1 SQLite Transaction Pattern

Database menggunakan aiosqlite. Pattern:
```python
# Setiap write langsung commit:
await self._conn.execute(query, params)
await self._conn.commit()
```

**Tidak ada explicit transaction grouping.** Setiap operasi di-commit sendiri.

**Masalah kritis — `toggle_favorite()`:**
```python
async def toggle_favorite(self, video_id: str) -> int:
    # SELECT untuk cek keberadaan
    async with self._conn.execute("SELECT 1 FROM tracks WHERE video_id = ?", ...) as cursor:
        if not await cursor.fetchone():
            return 0
    # ← GAP: baris bisa dihapus di sini oleh proses/goroutine lain

    # UPDATE terpisah tanpa lock/transaction
    await self._conn.execute("UPDATE tracks SET is_favorite = 1 - COALESCE(is_favorite, 0) ...", ...)
    await self._conn.commit()

    # SELECT lagi untuk baca nilai baru
    async with self._conn.execute("SELECT is_favorite FROM tracks ...", ...) as cursor:
```

Ini **non-atomic**. Solusinya: pakai `BEGIN ... COMMIT` eksplisit atau satu query `UPDATE ... RETURNING is_favorite`.

**Masalah — `evict_stale_tracks()`:**
```python
await self._conn.execute("DELETE FROM tracks WHERE play_count = 0 AND ...")
await self._conn.commit()
```
DELETE bulk ini tidak dibungkus savepoint. Jika crash setelah DELETE tapi sebelum commit, WAL bisa rollback sendiri — ini sebenarnya aman. Tapi tidak ada error handling di caller (`db_cleanup()` di `main.py`) yang spesifik untuk integrity error.

### 3.2 Schema Migration

Database menggunakan `ALTER TABLE ... ADD COLUMN` yang di-wrap `try/except`:
```python
try:
    await self._conn.execute("ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0")
    await self._conn.commit()
except Exception:  # ← swallow semua exception termasuk non-ColumnExists errors
    pass
```
Ini **anti-pattern**. Exception yang ter-swallow bisa menyembunyikan error lain (disk full, permission, corruption). Sebaiknya: `except aiosqlite.OperationalError as e: if "duplicate column" not in str(e): raise`.

**Tidak ada migration versioning** (schema version table). Schema dikelola via ALTER TABLE ad-hoc — rapuh untuk long-running deployment.

---

## 4. EXCEPTION HANDLING

### 4.1 Exception Hierarchy

```python
# core/exceptions.py
YtPlayerError (base)
├── MpvConnectionError
├── TrackResolutionError  ← TIDAK DIGUNAKAN di active code
└── DownloadError         ← TIDAK DIGUNAKAN di active code
```

**`TrackResolutionError` dan `DownloadError` didefinisikan tapi tidak dilempar di manapun.** Seluruh codebase melempar `RuntimeError` generik dari `ytdlp_client.py`. Exception hierarchy ada tapi tidak dipakai secara konsisten.

### 4.2 Pattern per Layer

**Transport (`websocket.py`)** — Baik:
```python
try:
    if action in _ws_handlers:
        await _ws_handlers[action](...)
except Exception as e:
    logger.error(...)
    await ws.send_str(json.dumps({"type": "error", "data": str(e)}))
```

**Engine (`playback/controller.py`)** — Baik dengan retry:
```python
except Exception as e:
    self._retry_count += 1
    if self._retry_count >= 3:
        # stop retry
    else:
        backoff = 2 ** self._retry_count
        await asyncio.sleep(backoff)
        await self._advance_to_next()
```

**Infrastructure (`ytdlp_client.py`)** — Baik:
```python
except asyncio.TimeoutError:
    raise RuntimeError(f"Timeout ({YTDLP_RESOLVE_TIMEOUT_SEC}s) ...")
except RuntimeError:
    raise  # re-raise domain error tanpa wrapping
except Exception as e:
    raise RuntimeError(f"Gagal ...") from e  # chaining OK
```

**Database (`cache/db.py`)** — Campuran:
- Operasi penting (upsert, increment) tidak punya try/except → error akan bubble up ke caller
- Operasi opsional (increment_artist_click) punya try/except → silent degradation
- `except Exception: pass` di skema migration → berbahaya (lihat §3.2)

**EventBus (`core/event_bus.py`)** — Baik:
```python
# Error satu handler tidak memblok handler lain
async def _wrap_handler(h=handler):
    try:
        await h(event)
    except Exception as e:
        logger.error(...)
```

**Masalah — `DiscoverService`:**
```python
async def get_recent(self, n: int) -> list[TrackInfo]:
    try:
        ...
    except Exception:  # ← swallow semua, return []
        pass
    return tracks
```
Semua method di `DiscoverService` swallow exception secara diam-diam. Tidak ada logging, tidak ada metric increment. Kalau DB corrupt atau query salah, UI akan tampil kosong tanpa indikasi.

---

## 5. CONCURRENCY

### 5.1 Lock Inventory

| Lock | Lokasi | Tujuan | Penilaian |
|---|---|---|---|
| `_lock` | `PlaybackController` | Guard semua mutasi state (next/prev/stop/queue ops) | ✅ Konsisten |
| `_play_lock` | `PlaybackController` | Cegah concurrent `play_track()` | ✅ Benar (terpisah dari _lock) |
| `_download_lock` | `DownloadManager` | 1 download pada satu waktu | ✅ Benar |
| `_req_lock` | `MpvController` | Increment `_request_id` safely | ✅ Benar |
| `_reconnect_lock` | `MpvController` | Cegah concurrent reconnect | ✅ Benar |
| `_fetch_lock` | `RadioMode` | Throttle batch fetch | ⚠️ TOCTOU (lihat §2.3) |
| `_standby_lock` | `RadioMode` | Guard `_standby` list | ✅ Benar |
| `rl_lock` | `ConnectionManager` | Rate limit command history | ✅ Benar |

### 5.2 Task Management (`core/task_utils.py`)

`safe_create_task()` adalah wrapper yang:
- Catch `CancelledError` → silent
- Catch `Exception` → log + optional `on_error` callback
- Cegah "Task exception was never retrieved" yang menyebabkan silent crash

Dipakai konsisten di: radio prefetch, lyric fetch, sponsorblock fetch, download, broadcast, dll.

### 5.3 Masalah Concurrency

**1. `_on_next()` dan `_on_track_ended()` bisa konflik:**
```python
async def _on_next(self, data=None):
    async with self._lock:  # acquire _lock
        ...
        await self._advance_to_next()

async def _on_track_ended(self, event):
    if reason == "eof":
        await asyncio.sleep(0.35)  # delay 350ms
        await self._on_next(next_data)  # ini juga acquire _lock
```
Kalau user klik Next dan track berakhir hampir bersamaan, kedua coroutine akan antri di `_lock`. Yang kedua akan skip via:
```python
if not self.state.current_track or self.state.current_track.video_id != data["video_id"]:
    return
```
Ini **benar** — guard ada. Tidak ada bug, hanya perlu diverifikasi edge case track sangat pendek.

**2. `EventBus.publish()` dan task gathering:**
```python
tasks = [safe_create_task(_wrap_handler()) for ...]
if tasks:
    await asyncio.gather(*tasks, return_exceptions=True)
```
Handler async dijalankan concurrent. Jika dua handler sama-sama mutasi `state`, ada race. Saat ini tidak ada case ini karena handler state hanya ada di `PlaybackController` — tapi ini assumption implicit yang rapuh.

**3. `ConnectionManager.broadcast()` dead connection cleanup:**
```python
results = await asyncio.gather(*(send(ws) for ws in self.active_connections), return_exceptions=True)
dead = [self.active_connections[i] for i, res in enumerate(results) if isinstance(res, Exception)]
for ws in dead:
    self.disconnect(ws)
```
**Bug halus**: Jika `self.active_connections` dimodifikasi oleh coroutine lain saat `gather` berjalan (concurrent connect/disconnect), index `i` akan merujuk ke koneksi yang salah. Solusi: snapshot list dulu: `conns = list(self.active_connections)`.

**4. `MpvController._observe_events()` reconnect:**
Reconnect dalam `_observe_events()` berjalan 3 kali dengan exponential backoff (1s, 2s, 4s). Tapi `main.py` juga punya `mpv_reconnect_checker()` yang cek setiap 5 detik. **Dua mekanisme reconnect berjalan paralel** — bisa menyebabkan double reconnect race. `_reconnect_lock` di `connect()` harusnya menghalau ini tapi `_observe_events()` tidak pakai `connect()` — ia buat koneksi langsung.

---

## 6. CACHING

### 6.1 Stream URL Cache

```
DB.tracks.stream_url + stream_url_ts
TTL: STREAM_URL_TTL_SEC = 21600 (6 jam)
```

**Flow resolver:**
1. Local file check → DB get_track → compare `time.time() - ts < TTL`
2. Kalau fresh → pakai cached URL
3. Kalau stale → `ytdlp.get_stream_url()` → `db.update_stream_url_only()` → return

**Prefetch double-path masalah:**
`StreamPrefetchService.prefetch_stream_url()` dan `CacheResolver.resolve()` keduanya bisa call `ytdlp.get_stream_url()` untuk video_id yang sama secara konkuren (satu dari event listener TrackStarted, satu dari RadioMode prefetch). Karena tidak ada lock per video_id, keduanya akan fetch dan update DB. Hasil: dua fetch beruntun yang tidak perlu. Bukan bug fatal (idempotent), tapi ineffisien — buang network + yt-dlp worker thread.

### 6.2 Local File Cache

```
cache/mp3/{video_id}.mp3  (internal)
downloads/{artist} - {title}.mp3  (user copy)
```

Download manager mengcopy dari internal cache ke user-visible `downloads/`. Internal cache bisa di-evict, user copy tidak.

**Masalah**: `evict_stale_tracks()` hanya delete dari DB, tidak delete file fisik di `cache/mp3/`. File orphan bisa menumpuk tanpa batas.

### 6.3 Lyric Cache

**Tidak ada cache.** Setiap ganti lagu fetch fresh dari lrclib.net / syncedlyrics. Untuk lagu yang sering diputar ini adalah network call berulang yang tidak perlu.

### 6.4 Artist / Seed Cache

```python
# radio_engine.py
async def _ensure_artists_loaded(self):
    if self._seed_artists:  # ← in-memory, persisten selama app hidup
        return
    self._seed_artists = await self.db.get_all_artists()
```

Loaded sekali di memory, tidak di-invalidate. Kalau artis baru diimport ke DB saat app berjalan, Radio tidak akan tahu sampai restart.

---

## 7. QUEUE

### 7.1 Queue Architecture

Dua queue terpisah, keduanya `collections.deque` di `AppState`:

| Field | Pemilik | TTL |
|---|---|---|
| `state.queue` | `QueueMode` | Manual (user tambah/hapus) |
| `state.radio_queue` | `RadioMode` | Auto-managed oleh RadioMode |

**Invariant penting** (dari Radio Constitution): RadioMode **tidak boleh** baca/tulis `state.queue`. Verified — kode saat ini menghormati invariant ini.

### 7.2 Queue Operations

| Operasi | Lock | Atomicity |
|---|---|---|
| `CMD_QUEUE_ADD` | `_lock` | ✅ |
| `CMD_QUEUE_REMOVE` | `_lock` | ✅ |
| `CMD_QUEUE_REPLACE` | `_lock` | ✅ |
| `CMD_QUEUE_REORDER` | `_lock` | ✅ |
| `CMD_QUEUE_SELECT` | `_lock` | ✅ |
| `QueueMode.next()` | via caller `_lock` | ✅ |

Semua queue ops diproteksi `_lock`. ✅

### 7.3 Radio Queue Capping

```python
# radio_engine.py _backfill_and_standby()
self.state.radio_queue.extend(extra)
while len(self.state.radio_queue) > 30:
    self.state.radio_queue.pop()  # ← hapus dari BELAKANG (LIFO)
```

**Bug logika**: `deque.pop()` hapus dari belakang (elemen terbaru), bukan dari depan. Jadi saat trimming, lagu yang baru saja ditambahkan dari backfill yang dibuang, bukan lagu yang sudah lama antri di belakang. Harusnya `self.state.radio_queue.popleft()` — tapi ini malah lebih buruk karena membuang lagu yang akan segera dimainkan. Solusi terbaik: cap dengan `deque(maxlen=30)` atau jangan pop saat backfill tapi batasi saat extend.

### 7.4 Command Queue (CommandBus)

CommandBus bukan queue — dispatch synchronous/direct via dict lookup. Tidak ada backpressure, tidak ada ordering guarantee. Jika dua `execute()` dipanggil concurrent untuk command sama, mereka bisa overlap (handler dipanggil concurrent). Saat ini tidak masalah karena `_lock` di PlaybackController guard implementasinya.

---

## 8. RETRY

### 8.1 Playback Retry (`engine/playback/controller.py`)

```python
self._retry_count += 1
if self._retry_count >= 3:
    # stop, reset
else:
    backoff = 2 ** self._retry_count  # 2s, 4s, 8s
    await asyncio.sleep(backoff)
    if self.state.current_track == track:
        await self._advance_to_next()
```

- Max 3 kegagalan beruntun sebelum berhenti
- Exponential backoff 2/4/8 detik
- Guard `current_track == track` mencegah retry pada lagu yang sudah diganti

**Masalah**: `self._retry_count` tidak di-reset saat mode ganti (Queue → Radio). Bisa terbawa ke sesi berikutnya. Fixed sebagian di `_on_stop()` dengan explicit `self._retry_count = 0`, tapi tidak di `_on_set_mode()`.

### 8.2 MPV Reconnect Retry (`engine/mpv_controller.py`)

```python
# Di _do_connect(): 10 attempts, 0.5s interval
for attempt in range(10):
    try:
        self._reader, self._writer = await ...open_connection(...)
        ...
        return
    except ...:
        await asyncio.sleep(0.5)
raise MpvConnectionError(...)
```

```python
# Di _observe_events(): 3 attempts, exponential backoff
for attempt in range(3):
    backoff = 2 ** attempt  # 1s, 2s, 4s
    await asyncio.sleep(backoff)
    ...
```

Dua mekanisme reconnect (lihat §5.3) berjalan paralel dengan `main.py`'s `mpv_reconnect_checker()`.

### 8.3 HTTP Retry di `serve_stream()`

```python
for attempt in range(2):
    if not stream_url:
        try:
            stream_url = await ytdlp.get_stream_url(video_id)
        except Exception as e:
            if attempt == 1:
                return web.HTTPInternalServerError(...)
            continue

    try:
        async with http_session.get(stream_url, ...) as upstream:
            if upstream.status in (403, 410) and attempt == 0:
                logger.warning("YouTube stream URL expired, refetching...")
                stream_url = None
                continue
```

Retry logic HTTP proxy: 2 attempt, auto-refetch jika 403/410. ✅ Baik.

### 8.4 yt-dlp Timeout

```python
# ytdlp_client.py
info = await asyncio.wait_for(
    loop.run_in_executor(self._executor, self._extract_sync, url, options),
    timeout=YTDLP_RESOLVE_TIMEOUT_SEC,  # 25s
)
```

Timeout 25 detik untuk resolve. Setelah timeout → `RuntimeError` → bubble ke resolver → bubble ke `play_track()` → trigger retry logic. Chain benar.

**Masalah**: `asyncio.wait_for` timeout **tidak membatalkan thread executor**. Thread yt-dlp tetap berjalan di background meski caller sudah timeout. Ini bisa menghabiskan `ThreadPoolExecutor` slot (max_workers=4). Solusi: `concurrent.futures.Future.cancel()` atau pisahkan timeout jadi 2 lapis.

---

## 9. REPOSITORY PATTERN

### 9.1 Interface Definition (`core/ports.py`)

```python
class TrackRepositoryPort(Protocol):
    async def upsert_track(self, track, stream_url=None, local_path=None): ...
    async def update_stream_url_only(self, video_id, stream_url): ...
    async def get_track(self, video_id): ...
    async def increment_play_count(self, video_id): ...

class SessionRepositoryPort(Protocol):
    async def create_session(self, token, expires_at): ...
    async def verify_session(self, token): ...
    async def delete_session(self, token): ...
    async def cleanup_sessions(self): ...

class DatabasePort(TrackRepositoryPort, SessionRepositoryPort, Protocol):
    async def init(self): ...
    async def close(self): ...
```

Protocol-based interface — ✅ testable tanpa concrete DB.

### 9.2 Implementation (`cache/db.py`)

**Satu kelas `Database` mengimplementasikan semua: TrackRepo + SessionRepo + Radio queries + Discover queries.**

**Masalah desain**: `Database` terlalu besar (God Object). Terdapat metode yang tidak ada di interface:
- `get_all_artists()` — Radio seeding
- `get_random_songs()` — Radio query
- `get_artist_songs_strict()` — Discover/Queue
- `get_genre_songs()` — Genre enqueue
- `get_genre_artists()` — Genre discovery
- `toggle_favorite()` — User interaction
- `evict_stale_tracks()` — Maintenance
- `increment_artist_click()` / `increment_genre_click()` — Analytics

Method-method ini tidak ada di `DatabasePort` protocol. Artinya caller yang butuh method ini (RadioMode, DiscoverService, WebSocket handlers) harus type-cast ke concrete `Database` — menghancurkan abstraksi.

### 9.3 Direct DB Access Anti-pattern

```python
# discover_service.py
class DiscoverService:
    def __init__(self, db: Database):  # ← concrete type, bukan Port
        self.db = db

    async def get_recent(self, n):
        # Langsung akses self.db._conn:
        async with self.db._conn.execute("SELECT ...", ...) as cursor:
```

`DiscoverService` mengakses `self.db._conn` (private field) secara langsung, bypass semua metode public DB. Ini **hard coupling** ke implementasi internal aiosqlite — menyulitkan testing dan refactoring.

---

## 10. SERVICE LAYER

### 10.1 Service Inventory

| Service | Lokasi | Tanggung Jawab | Penilaian |
|---|---|---|---|
| `PlaybackController` | engine/playback/ | Orkestrasi playback utama | ✅ SRP OK |
| `QueueMode` | engine/queue_manager.py | Lanjutkan ke lagu berikutnya di queue | ✅ Lean, SRP |
| `RadioMode` | engine/radio_engine.py | Auto-fill radio queue, prefetch | ✅ Kompleks tapi terfokus |
| `VolumeService` | engine/volume_service.py | Volume up/down/set + routing | ✅ Lean |
| `DownloadManager` | engine/download_manager.py | Download MP3 + progress | ✅ OK |
| `TrackLoader` | engine/playback/track_loader.py | Resolve URI + trigger side tasks | ✅ Extracted dengan benar |
| `CacheResolver` | cache/resolver.py | URL resolution dengan TTL cache | ✅ SRP OK |
| `BroadcastService` | server/services/ | Broadcast ke WebSocket clients | ✅ Lean |
| `StreamPrefetchService` | server/services/ | Background prefetch stream URL | ✅ Lean |
| `DiscoverService` | services/ | Aggregasi data untuk tab Discover | ⚠️ Coupling masalah (lihat §9.3) |
| `LyricsFetcher` | plugins/lyrics.py | Fetch + parse + sync lirik | ✅ Isolated |
| `SponsorBlockHandler` | plugins/sponsorblock.py | Fetch segments + skip | ✅ Isolated |
| `TermuxNowPlaying` | plugins/notifications.py | Notification Android | ✅ Isolated |

### 10.2 Masalah Service

**1. `event_listeners.py` bukan service — ini controller side effect:**
```python
# event_listeners.py
async def _on_download_complete(event: DownloadCompleteEvent):
    # Langsung buat DiscoverService inline:
    ds = DiscoverService(playback_controller.resolver.db)
    recent = await ds.get_recent(15)
    ...
    # Langsung broadcast manual:
    await broadcast_service.manager.broadcast({...})
```
Event listener membuat service object setiap event dan melakukan orchestration yang seharusnya ada di BroadcastService atau DiscoverService.

**2. VolumeService state tidak sinkron:**
```python
class VolumeService:
    def __init__(self, bus, mpv, state):
        self.current_volume = state.volume  # ← snapshot saat init
```
`self.current_volume` diinisialisasi dari `state.volume` sekali saja. Jika volume diubah dari luar VolumeService (misalnya di `_on_set_output()` di PlaybackController), `self.current_volume` tidak ter-update. Ini bisa menyebabkan volume "loncat" kembali ke nilai lama saat `volume_up/down` dipanggil setelah `set_output`.

---

## 11. DEPENDENCY INJECTION

### 11.1 Pola yang Dipakai

Dependency Injection dilakukan via **constructor injection** di `main.py`:

```python
# main.py — Manual DI Container
db = Database()
ytdlp = YtDlpClient()
mpv = MpvController()
resolver = CacheResolver(db, ytdlp)
sponsorblock = SponsorBlockHandler(mpv, state, session, bus)
lyrics_fetcher = LyricsFetcher(state, session, bus)
queue_mode = QueueMode()
radio_mode = RadioMode(ytdlp, state, db)
volume_service = VolumeService(bus, mpv, state)
playback_controller = PlaybackController(bus, state, mpv, resolver, sponsorblock, lyrics_fetcher, queue_mode, radio_mode)
download_manager = DownloadManager(bus, state, ytdlp)
command_router = CommandRouter(playback_controller, volume_service)
```

**Tidak ada DI framework** — pure manual wiring. ✅ Cukup untuk skala ini.

### 11.2 Masalah DI

**1. Global fallback di dalam service:**
```python
# mpv_controller.py, lyrics.py, sponsorblock.py
if event_bus is None:
    from core.event_bus import bus as _global_bus
    event_bus = _global_bus
```
Pattern ini ada di 3 tempat. Saat production, bus selalu diinjek. Tapi fallback ke global `bus` ini menyembunyikan missing dependency — sebaiknya fail-fast dengan `assert event_bus is not None`.

**2. `CommandBus` sebagai implicit global:**
```python
# core/command_bus.py
command_bus = CommandBus()  # ← module-level singleton

# Dipakai langsung di handler:
from core.command_bus import command_bus, CMD_...
await command_bus.execute(CMD_PLAY_TRACK, track)
```
`command_bus` adalah global singleton yang di-import langsung, bukan diinjek. Ini membuat testing sulit karena semua test yang memanggil handler perlu patch global. `EventBus` (`bus`) punya masalah yang sama.

**3. `app.py` membuat object service tanpa injeksi:**
```python
# server/app.py
prefetch_service = StreamPrefetchService(db, ytdlp)  # ← dibuat di sini
broadcast_service = BroadcastService(manager)
setup_event_listeners(playback_controller, prefetch_service, broadcast_service)
```
Ini seharusnya dibuat di `main.py` dan diinjek ke `create_app()`. Sekarang `create_app()` adalah implicit factory sekaligus komposer — mixing responsibility.

**4. `DiscoverService` dibuat ad-hoc berulang:**
```python
# websocket.py
ds = DiscoverService(db)
# Di event_listeners.py juga:
ds = DiscoverService(playback_controller.resolver.db)
```
DiscoverService dibuat di minimal 3 tempat yang berbeda (websocket handler `_build_discover_payload`, `handle_toggle_favorite`, `event_listeners._on_download_complete`). Seharusnya singleton yang diinjek.

---

## 12. RINGKASAN TEMUAN & PRIORITAS

### CRITICAL (Harus Fix)

| # | Lokasi | Masalah |
|---|---|---|
| C-01 | `cache/db.py:toggle_favorite()` | Non-atomic: SELECT → UPDATE → SELECT terpisah tanpa transaction |
| C-02 | `engine/mpv_controller.py` | Dua mekanisme reconnect paralel (observer + main.py checker) bisa race |
| C-03 | `server/handlers/websocket.py:broadcast()` | Index-based dead connection cleanup unsafe saat concurrent modify |
| C-04 | `engine/ytdlp_client.py` | `asyncio.wait_for` timeout tidak cancel thread executor — thread leak |

### HIGH (Harus Fix Segera)

| # | Lokasi | Masalah |
|---|---|---|
| H-01 | `cache/db.py:__init__()` | `except Exception: pass` di schema migration menyembunyikan error |
| H-02 | `engine/radio_engine.py` | TOCTOU race di `_backfill_and_standby()` |
| H-03 | `engine/radio_engine.py` | `deque.pop()` (LIFO) saat trimming radio_queue harusnya tidak pop dari belakang |
| H-04 | `engine/volume_service.py` | `self.current_volume` snapshot stale — volume bisa "loncat" |
| H-05 | `core/exceptions.py` | `TrackResolutionError` dan `DownloadError` didefinisikan tapi tidak dipakai |

### MEDIUM (Tech Debt)

| # | Lokasi | Masalah |
|---|---|---|
| M-01 | `services/discover_service.py` | Akses `self.db._conn` langsung (bypass abstraksi) + `except Exception: pass` silent |
| M-02 | `cache/resolver.py` | `import asyncio` di dalam loop function |
| M-03 | `cache/db.py` | God Object — terlalu banyak method di luar interface Port |
| M-04 | `core/command_bus.py` + `core/event_bus.py` | Global singleton sulit di-test |
| M-05 | `engine/playback/controller.py` | `_retry_count` tidak reset saat mode switch |
| M-06 | `server/handlers/event_listeners.py` | Buat `DiscoverService` inline setiap event |
| M-07 | Seluruh codebase | Tidak ada lyric cache — fetch ulang setiap track |
| M-08 | `cache/db.py:evict_stale_tracks()` | Tidak hapus file fisik di `cache/mp3/` — orphan file |
| M-09 | Tidak ada | Tidak ada DB schema versioning/migration system |
| M-10 | `services/discover_service.py` | Lokasi tidak konsisten (`/services/` bukan `/server/services/`) |

### LOW (Improvement)

| # | Lokasi | Masalah |
|---|---|---|
| L-01 | `engine/playback/controller.py:EventBus.publish()` | Implicit assumption: tidak ada dua handler yang mutasi state |
| L-02 | Semua plugin | Global bus fallback menyembunyikan missing dependency |
| L-03 | `cache/resolver.py` + `StreamPrefetchService` | Double fetch untuk video_id yang sama (no per-key lock) |
| L-04 | `engine/radio_engine.py` | Seed artists tidak di-invalidate kalau DB diupdate saat runtime |
| L-05 | `server/app.py` | `create_app()` jadi factory + composer — mixing responsibility |

---

## 13. QUICK FIX PATCHES

### Fix C-01: Atomic toggle_favorite
```python
# cache/db.py
async def toggle_favorite(self, video_id: str) -> int:
    async with self._conn.execute("BEGIN"): pass
    try:
        cursor = await self._conn.execute(
            """UPDATE tracks
               SET is_favorite = 1 - COALESCE(is_favorite, 0)
               WHERE video_id = ?
               RETURNING is_favorite""",
            (video_id,)
        )
        row = await cursor.fetchone()
        await self._conn.commit()
        return int(row["is_favorite"]) if row else 0
    except Exception:
        await self._conn.execute("ROLLBACK")
        raise
```

### Fix C-03: Broadcast snapshot
```python
# server/handlers/websocket.py
async def broadcast(self, message: dict):
    conns = list(self.active_connections)  # ← snapshot!
    data = json.dumps(message, ensure_ascii=False)
    results = await asyncio.gather(*(send(ws) for ws in conns), return_exceptions=True)
    for ws, res in zip(conns, results):
        if isinstance(res, Exception):
            self.disconnect(ws)
```

### Fix H-01: Schema migration error handling
```python
# cache/db.py
import aiosqlite
try:
    await self._conn.execute("ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0")
    await self._conn.commit()
except aiosqlite.OperationalError as e:
    if "duplicate column" not in str(e).lower():
        raise  # re-raise non-expected errors
```

### Fix H-03: Radio queue trim
```python
# engine/radio_engine.py  
if extra:
    self.state.radio_queue.extend(extra)
    # Trim dari belakang dengan benar:
    while len(self.state.radio_queue) > 30:
        self.state.radio_queue.pop()  # Ini sudah LIFO — hapus lagu paling baru
    # Atau lebih baik: batasi saat extend:
    # tracks_to_add = extra[:max(0, 30 - len(self.state.radio_queue))]
    # self.state.radio_queue.extend(tracks_to_add)
```

### Fix H-04: VolumeService sync
```python
# engine/volume_service.py
async def _apply_volume(self):
    self.state.volume = self.current_volume  # ← sync state dulu
    if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
        await self.mpv.set_volume(0)
    else:
        await self.mpv.set_volume(self.current_volume)
    await self.bus.publish(...)

async def _on_volume_up(self, _data=None):
    # Sync dari state dulu untuk avoid stale snapshot:
    self.current_volume = self.state.volume
    self.current_volume = min(100, self.current_volume + 5)
    await self._apply_volume()
```
