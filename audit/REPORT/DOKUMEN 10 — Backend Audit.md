# 🔍 BACKEND AUDIT REPORT — LunaWave
**Scope:** Business Logic · Transaction · Exception · Concurrency · Caching · Queue · Retry · Repository · Service · Dependency · Layering  
**Audit Team:** Senior Software Architect, Principal Backend Engineer, DevOps Engineer, QA Lead, Security Engineer, Database Architect  
**Standard:** Production-grade, scale-ready assessment  
**Date:** 2026-07-07

---

## TABLE OF CONTENTS

1. [Critical Bugs (P0)](#critical-bugs-p0)
2. [Business Logic Issues](#business-logic-issues)
3. [Transaction & Database Issues](#transaction--database-issues)
4. [Exception Handling Issues](#exception-handling-issues)
5. [Concurrency & Race Conditions](#concurrency--race-conditions)
6. [Caching Issues](#caching-issues)
7. [Queue Issues](#queue-issues)
8. [Retry & Resilience Issues](#retry--resilience-issues)
9. [Repository Issues](#repository-issues)
10. [Service Layer Issues](#service-layer-issues)
11. [Dependency & Layering Violations](#dependency--layering-violations)
12. [Summary Table](#summary-table)

---

## CRITICAL BUGS (P0)

---

### BUG-01 — `DiscoverService` KeyError: `stream_url` Not in SELECT

| Field | Detail |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | Setiap request ke tab Discover → crash KeyError, seluruh feature Discover mati |
| **Penyebab** | SQL query memilih kolom tanpa `stream_url`, tapi kode langsung mengaksesnya |
| **Lokasi** | `server/services/discover_service.py` · `get_recent()` L36, `get_favorites()` L63, `get_cached()` L90 |

**Kode Bermasalah:**
```python
# SQL hanya memilih: video_id, title, artist, duration, thumbnail, local_path, view_count, play_count, is_favorite
async with self.db.conn.execute(
    "SELECT video_id, title, artist, duration, thumbnail, local_path, view_count, play_count, is_favorite "
    "FROM tracks ORDER BY last_played DESC LIMIT ?", (n,)
) as cursor:
    async for row in cursor:
        d = dict(row)
        tracks.append(TrackInfo(
            ...
            stream_url=d["stream_url"],   # ← KeyError: 'stream_url' tidak ada di dict!
```

**Solusi:**
```python
# Opsi 1: Tambahkan stream_url ke SELECT
async with self.db.conn.execute(
    "SELECT video_id, title, artist, duration, thumbnail, local_path, "
    "stream_url, stream_url_ts, view_count, play_count, is_favorite "
    "FROM tracks ORDER BY last_played DESC LIMIT ?", (n,)
) as cursor:

# Opsi 2: Gunakan .get() dengan fallback
stream_url=d.get("stream_url"),
```
Terapkan fix yang sama di `get_recent()`, `get_favorites()`, dan `get_cached()`.

---

### BUG-02 — `import time` di Bawah Class — Hoisting Mismatch

| Field | Detail |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | `_handle_event()` menggunakan `time.monotonic()` yang tidak tersedia sampai akhir file — jika Python memuat file secara parsial, NameError |
| **Penyebab** | `import time` ditempatkan di baris terakhir file, di luar class |
| **Lokasi** | `engine/mpv_controller.py` · baris terakhir |

**Kode Bermasalah:**
```python
    async def _set_property(self, prop: str, value):
        await self._command(["set_property", prop, value])
import time   # ← import di sini, setelah class definition selesai!
```

Fungsi `_handle_event()` di dalam class memanggil `time.monotonic()`, bergantung pada `import time` ini. Ini bekerja di CPython karena seluruh file diparse dulu, tapi ini adalah anti-pattern yang rentan, menyesatkan, dan akan rusak di beberapa tools analisis statis.

**Solusi:**
```python
# Pindahkan ke baris 1-10, bersama import lainnya
import time

class MpvController:
    ...
```

---

### BUG-03 — `RadioRandomizeCommand` Hanya Berjalan di RADIO Mode

| Field | Detail |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | Klik tombol "Acak" saat mode QUEUE → radio tidak aktif, tidak ada feedback yang jelas, user bingung |
| **Penyebab** | Guard `if self.state.playback_mode == PlaybackMode.RADIO` memblokir fetch jika belum di mode RADIO |
| **Lokasi** | `engine/playback/radio_commands.py` · `on_radio_randomize()` |

**Kode Bermasalah:**
```python
async def on_radio_randomize(self, cmd):
    seed = None
    should_fetch = False
    async with self.playback_controller._lock:
        if self.state.playback_mode == PlaybackMode.RADIO:
            # hanya masuk sini jika SUDAH di RADIO mode
            seed = cmd.seed_artist if cmd else None
            ...
            should_fetch = True
        else:
            await self.bus.publish(LogMessageEvent(message="Radio tidak aktif"))
            # user mendapat "Radio tidak aktif" dan harus klik dua kali
```

**Solusi:**
```python
async def on_radio_randomize(self, cmd):
    seed = getattr(cmd, "seed_artist", None)
    async with self.playback_controller._lock:
        if self.state.playback_mode != PlaybackMode.RADIO:
            # Otomatis switch ke RADIO mode
            self.state.playback_mode = PlaybackMode.RADIO
            self.state.status = PlayerStatus.LOADING
            self.playback_controller._retry_count = 0
        self.state.radio_queue.clear()
        await self.mpv.pause()
        self.state.current_track = None
        self.state.position = 0.0
        self.radio_mode._artist_rotation = []
        await self.bus.publish(QueueUpdatedEvent())
        await self.bus.publish(LogMessageEvent(message="Mengacak ulang stasiun radio..."))

    safe_create_task(
        self.radio_mode._fetch_and_play_initial(self.playback_controller, seed_artist=seed),
        name="radio_randomize_fetch"
    )
```

---

### BUG-04 — Admin Password Tidak Tercetak di Non-TTY Environment

| Field | Detail |
|---|---|
| **Severity** | 🔴 CRITICAL |
| **Dampak** | Di Docker, systemd, atau background process, password auto-generated tidak pernah terlihat oleh admin → aplikasi tidak bisa diakses |
| **Penyebab** | `sys.stderr.isatty()` check memblokir output di non-interactive terminal |
| **Lokasi** | `config.py` · `get_admin_password()` |

**Kode Bermasalah:**
```python
if sys.stderr.isatty():
    sys.stderr.write(f"PASSWORD ADMIN GENERATED: {raw_password}\n")
    # jika bukan TTY, password tercetak ke file tapi tidak ada notifikasi!
```

**Solusi:**
```python
# Selalu cetak ke stderr, lepas dari TTY — tapi tambahkan penanda agar mudah di-grep
sys.stderr.write("=" * 50 + "\n")
sys.stderr.write(f"[LUNAWAVE] AUTO-GENERATED ADMIN PASSWORD: {raw_password}\n")
sys.stderr.write(f"[LUNAWAVE] Simpan password ini! (juga di cache/admin_password.txt)\n")
sys.stderr.write("=" * 50 + "\n")
sys.stderr.flush()

# Juga kirim ke logger terstruktur sehingga masuk ke app.log
import structlog
structlog.get_logger(__name__).warning("Admin password auto-generated", hint="Check cache/admin_password.txt")
```

---

## BUSINESS LOGIC ISSUES

---

### BL-01 — `on_queue_select()` Membuang Track Sebelum Index Tanpa Update History

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Memilih track index-5 dari queue akan membuang track 0–4 dari queue tanpa memasukkannya ke history. Track-track ini hilang selamanya dari sesi pemutaran. |
| **Penyebab** | Loop `for _ in range(cmd.index + 1): self.state.queue.popleft()` membuang semua track sebelum index |
| **Lokasi** | `engine/playback/queue_commands.py` · `on_queue_select()` |

**Kode Bermasalah:**
```python
async def on_queue_select(self, cmd):
    async with self.playback_controller._lock:
        if 0 <= cmd.index < len(self.state.queue):
            track = self.state.queue[cmd.index]
            for _ in range(cmd.index + 1):
                self.state.queue.popleft()   # ← track index 0..index-1 dibuang!
            await self.playback_controller.play_track(track)
```

**Solusi:**
```python
async def on_queue_select(self, cmd):
    async with self.playback_controller._lock:
        if 0 <= cmd.index < len(self.state.queue):
            track = self.state.queue[cmd.index]
            # Simpan track yang diskip ke history
            for _ in range(cmd.index):
                skipped = self.state.queue.popleft()
                self.playback_controller.state.history.append(skipped)
            self.state.queue.popleft()  # pop track yang dipilih
            await self.playback_controller.play_track(track)
```

---

### BL-02 — Volume Cap Tidak Konsisten: `100` vs `150`

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | `VolumeService` membatasi volume ke 100, tapi `settings_handlers.py` mengirim `volume_set` hingga 150. `MAX_VOLUME = 150` di constants tidak digunakan di `VolumeService`. User yang kirim nilai 120 via `volume_set` akan mendapat 120, tapi user yang klik +5 tidak bisa melewati 100. |
| **Penyebab** | Inkonsistensi antara tiga definisi batas volume |
| **Lokasi** | `engine/volume_service.py` L23, `server/handlers/ws/settings_handlers.py` L20, `core/constants.py` L4 |

**Kode Bermasalah:**
```python
# volume_service.py
self.current_volume = min(100, self.current_volume + 5)   # cap 100

# settings_handlers.py
vol = max(0, min(150, int(data.get("volume", DEFAULT_VOLUME))))   # cap 150

# constants.py
MAX_VOLUME = 150   # tidak dipakai di VolumeService!
```

**Solusi:**
```python
# volume_service.py — gunakan MAX_VOLUME dari constants
from core.constants import MAX_VOLUME

async def _on_volume_up(self, cmd=None):
    self.current_volume = self.state.volume
    self.current_volume = min(MAX_VOLUME, self.current_volume + 5)
    await self._apply_volume()

async def _on_volume_down(self, cmd=None):
    self.current_volume = self.state.volume
    self.current_volume = max(0, self.current_volume - 5)
    await self._apply_volume()
```

---

### BL-03 — `_gather_batch()` dengan `prioritized_artist` Tidak Menjamin Artist Muncul

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | User memilih seed artist tertentu, tapi radio bisa saja tidak memainkan lagu dari artist tersebut sama sekali jika DB tidak punya cukup lagu yang tersedia |
| **Penyebab** | SQL menggunakan `ORDER BY CASE WHEN nama = ? THEN 0 ELSE 1 END, RANDOM()` — ini hanya memprioritas, tidak memfilter |
| **Lokasi** | `cache/repositories/discover_repository.py` · `get_random_songs()` |

**Kode Bermasalah:**
```python
if artist:
    query += " ORDER BY CASE WHEN nama = ? THEN 0 ELSE 1 END, RANDOM() LIMIT ?"
    params.extend([artist, limit])
# Jika limit sudah tercapai oleh non-artist-seed, artist seed tidak muncul
```

**Solusi:**
```python
# Fetch artist seed songs terlebih dahulu, lalu isi sisanya
async def get_random_songs_with_seed(self, limit, exclude_ids, artist=None, max_per_artist=3):
    result = []
    if artist:
        seed_songs = await self.get_artist_songs_strict(artist, limit=TRACKS_PER_ARTIST_TARGET)
        seed_songs = [s for s in seed_songs if s.video_id not in exclude_ids]
        result.extend(seed_songs)
        exclude_ids = exclude_ids | {s.video_id for s in result}
    
    remaining = limit - len(result)
    if remaining > 0:
        filler = await self.get_random_songs(remaining, exclude_ids, max_per_artist=max_per_artist)
        result.extend(filler)
    
    random.shuffle(result)
    return result
```

---

### BL-04 — `_backfill_and_standby()` Race Condition pada Queue Length Check

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Cek `len(self.state.radio_queue) >= 15` dilakukan setelah acquire `_fetch_lock`, tapi queue bisa berubah saat menunggu lock. Double fetch bisa terjadi |
| **Penyebab** | Queue check tidak atomik dengan lock acquisition |
| **Lokasi** | `engine/radio_engine.py` · `_backfill_and_standby()` |

**Kode Bermasalah:**
```python
async with self._fetch_lock:
    if len(self.state.radio_queue) >= 15:
        return   # ← queue sudah diisi oleh task lain saat kita nunggu lock
    # tapi bisa juga sebaliknya: queue sudah dikonsumsi dan kosong
```

**Solusi:** Pindahkan cek sebelum lock untuk fast-exit:
```python
async def _backfill_and_standby(self, controller):
    if len(self.state.radio_queue) >= 15:
        return  # fast-exit tanpa tunggu lock
    if self._fetch_lock.locked():
        return
    async with self._fetch_lock:
        # re-check setelah acquire
        if len(self.state.radio_queue) >= 15:
            return
        ...
```

---

## TRANSACTION & DATABASE ISSUES

---

### TXN-01 — Setiap DB Operation Commit Terpisah — N+1 Commit Anti-Pattern

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Setiap `upsert_track`, `increment_play_count`, `create_session` melakukan `commit()` individual. Untuk seeding 2500 artis + lagu, ini bisa ratusan commits → sangat lambat. |
| **Penyebab** | Tidak ada batch transaction atau unit-of-work pattern |
| **Lokasi** | `cache/repositories/track_repository.py`, `cache/repositories/auth_repository.py`, `cache/repositories/discover_repository.py` |

**Kode Bermasalah:**
```python
# track_repository.py
async def upsert_track(self, track, stream_url=None, local_path=None):
    await self._conn.execute(query, (...))
    await self._conn.commit()   # commit per operasi

async def increment_play_count(self, video_id):
    await self._conn.execute("UPDATE tracks SET ...")
    await self._conn.commit()   # commit terpisah lagi
```

**Solusi — Async Context Manager untuk Batch:**
```python
# cache/db.py
from contextlib import asynccontextmanager

@asynccontextmanager
async def transaction(self):
    """Context manager untuk batch operations."""
    try:
        yield self._conn
        await self._conn.commit()
    except Exception:
        await self._conn.rollback()
        raise

# Gunakan di _seed_initial_data:
async with self.transaction():
    for artist in data.get('artists', []):
        await self._conn.execute("INSERT OR REPLACE INTO artists ...", ...)
        for lagu in artist.get('lagu_populer', []):
            await self._conn.execute("INSERT OR IGNORE INTO songs ...", ...)
# commit sekali di akhir, bukan per baris
```

---

### TXN-02 — `_seed_initial_data()` Tanpa Error Recovery — Partial State

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Jika seeding terinterupsi (misalnya power loss), DB bisa dalam keadaan parsial. Tidak ada transaksi atomik yang membungkus seluruh proses seeding. |
| **Penyebab** | Tidak ada `try/except/rollback` di level seeding keseluruhan |
| **Lokasi** | `cache/db.py` · `_seed_initial_data()` |

**Kode Bermasalah:**
```python
async def _seed_initial_data(self):
    for artist in data.get('artists', []):
        await self._conn.execute('INSERT OR REPLACE INTO artists ...', ...)
        for genre_name in artist.get('genre', []):
            await self._conn.execute('INSERT OR IGNORE INTO genres ...', ...)
        for lagu in artist.get('lagu_populer', []):
            await self._conn.execute('INSERT OR IGNORE INTO songs ...', ...)
    await self._conn.commit()  # commit di akhir, tapi tidak ada rollback jika crash di tengah
```

**Solusi:**
```python
async def _seed_initial_data(self):
    try:
        async with self._conn.execute("BEGIN"):
            pass  # explicit BEGIN
        for artist in data.get('artists', []):
            await self._conn.execute(...)
            ...
        await self._conn.commit()
        logger.info("Database auto-seeded successfully.")
    except Exception as e:
        await self._conn.rollback()
        logger.error(f"Seeding gagal, rollback: {e}")
        raise
```

---

### TXN-03 — `toggle_favorite` Menggunakan `RETURNING` — SQLite 3.35+ Only

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Di SQLite < 3.35 (misalnya di Android Termux lama), `RETURNING` tidak didukung → crash saat user toggle favorit |
| **Penyebab** | `RETURNING` clause hanya tersedia sejak SQLite 3.35.0 (March 2021) |
| **Lokasi** | `cache/repositories/track_repository.py` · `toggle_favorite()` |

**Kode Bermasalah:**
```python
async with self._conn.execute(
    """UPDATE tracks SET is_favorite = 1 - COALESCE(is_favorite, 0)
       WHERE video_id = ? RETURNING is_favorite""",
    (video_id,)
) as cursor:
    row = await cursor.fetchone()
```

**Solusi — Kompatibel Semua Versi SQLite:**
```python
async def toggle_favorite(self, video_id: str) -> int:
    if not self._conn: return 0
    await self._conn.execute(
        "UPDATE tracks SET is_favorite = 1 - COALESCE(is_favorite, 0) WHERE video_id = ?",
        (video_id,)
    )
    await self._conn.commit()
    async with self._conn.execute(
        "SELECT is_favorite FROM tracks WHERE video_id = ?", (video_id,)
    ) as cursor:
        row = await cursor.fetchone()
    return row["is_favorite"] if row else 0
```

---

### TXN-04 — `upsert_track` Selalu Update `last_played` — Polusi Data Recent

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Memanggil `upsert_track` saat update stream URL atau duration juga memperbarui `last_played`, sehingga track yang tidak diputar muncul di daftar "Recently Played" |
| **Penyebab** | Field `last_played` diset ke `ts` di setiap upsert tanpa kondisi |
| **Lokasi** | `cache/repositories/track_repository.py` · `upsert_track()` |

**Kode Bermasalah:**
```python
# Dipanggil juga dari _on_track_duration, prefetch, dll.
await self._conn.execute(query, (
    track.video_id, ..., ts  # last_played = ts selalu!
))
```

**Solusi:**
```python
# Pisahkan: hanya update last_played saat track benar-benar diputar
# Gunakan parameter explicit

async def upsert_track(self, track, stream_url=None, local_path=None, update_played=False):
    ts = int(time.time())
    last_played_val = ts if update_played else None
    query = """
        INSERT INTO tracks (video_id, title, ..., last_played)
        VALUES (?, ..., ?)
        ON CONFLICT(video_id) DO UPDATE SET
            ...
            last_played = CASE WHEN ? THEN excluded.last_played ELSE tracks.last_played END
    """
    await self._conn.execute(query, (..., last_played_val, update_played))
    await self._conn.commit()

# Panggil dengan update_played=True hanya dari track_loader / increment_play_count
```

---

## EXCEPTION HANDLING ISSUES

---

### EXC-01 — `CacheResolver.resolve()` Thundering Herd Setelah Error

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Jika `get_stream_url()` gagal, semua waiter di-release melalui `event.set()`, lalu masing-masing memanggil `resolve()` lagi secara rekursif. `_fetching` sudah di-pop, sehingga semua waiter akan mencoba fetch ulang secara paralel → thundering herd ke yt-dlp |
| **Penyebab** | Tidak ada mekanisme untuk menyimpan error state saat fetch gagal |
| **Lokasi** | `cache/resolver.py` · `resolve()` |

**Kode Bermasalah:**
```python
try:
    url = await self.ytdlp.get_stream_url(track.video_id)
    ...
    return url
finally:
    event.set()
    self._fetching.pop(track.video_id, None)
    # waiter terbangun, _fetching kosong → semua fetch ulang sendiri!
```

**Solusi — Error Caching:**
```python
_error_cache: dict[str, tuple[float, Exception]] = {}  # video_id → (ts, error)
ERROR_CACHE_TTL = 30  # detik

async def resolve(self, track: TrackInfo) -> str:
    vid = track.video_id
    
    # Check error cache
    if vid in self._error_cache:
        ts, err = self._error_cache[vid]
        if time.time() - ts < self.ERROR_CACHE_TTL:
            raise err
        del self._error_cache[vid]
    
    # ... existing logic ...
    
    error_to_cache = None
    try:
        url = await self.ytdlp.get_stream_url(vid)
        track.stream_url = url
        await self.db.upsert_track(track, stream_url=url)
        return url
    except Exception as e:
        error_to_cache = e
        raise
    finally:
        if error_to_cache:
            self._error_cache[vid] = (time.time(), error_to_cache)
        event.set()
        self._fetching.pop(vid, None)
```

---

### EXC-02 — `_fetching.wait()` Tanpa Timeout — Deadlock Potensial

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Jika task yang sedang fetch crash sebelum memanggil `event.set()`, semua waiter hang selamanya. Playback stuck di LOADING state tanpa batas waktu. |
| **Penyebab** | `await self._fetching[track.video_id].wait()` tidak ada timeout |
| **Lokasi** | `cache/resolver.py` L43, `server/services/stream_prefetch.py` L22 |

**Kode Bermasalah:**
```python
if track.video_id in self._fetching:
    await self._fetching[track.video_id].wait()   # ← bisa hang selamanya
    return await self.resolve(track)
```

**Solusi:**
```python
if track.video_id in self._fetching:
    try:
        await asyncio.wait_for(
            self._fetching[track.video_id].wait(),
            timeout=YTDLP_RESOLVE_TIMEOUT_SEC + 5
        )
    except asyncio.TimeoutError:
        self._fetching.pop(track.video_id, None)
        raise RuntimeError(f"Timeout menunggu resolve untuk {track.video_id}")
    return await self.resolve(track)
```

---

### EXC-03 — `_stream_rate_limit` dict Tidak Pernah Dibersihkan — Memory Leak

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | `_stream_rate_limit` adalah modul-level dict yang menyimpan history request per IP. Tidak ada cleanup expired entries → dict tumbuh seiring waktu dan tidak pernah dikurangi. Pada production dengan banyak IP, ini menjadi memory leak. |
| **Penyebab** | Entries lama difilter per request untuk IP yang sama, tapi IP yang tidak pernah request lagi tidak pernah dihapus dari dict |
| **Lokasi** | `server/handlers/http.py` · L17, L57-62 |

**Kode Bermasalah:**
```python
_stream_rate_limit = collections.defaultdict(list)   # ← tidak pernah dibersihkan

async def serve_stream(request):
    history = _stream_rate_limit[client_ip]
    history = [t for t in history if now - t < 60]   # filter per-IP tapi IP lama tidak dihapus
    _stream_rate_limit[client_ip] = history   # IP yang tidak request lagi tetap di dict!
```

**Solusi:**
```python
async def serve_stream(request):
    now = time.monotonic()
    history = _stream_rate_limit.get(client_ip, [])
    history = [t for t in history if now - t < 60]
    if len(history) >= STREAM_RATE_LIMIT_MAX:
        return web.json_response(error_payload("HTTP_ERROR", "Rate limit exceeded"), status=429)
    history.append(now)
    if history:
        _stream_rate_limit[client_ip] = history
    else:
        _stream_rate_limit.pop(client_ip, None)  # hapus entry kosong
```

---

### EXC-04 — Double `TrackEndedEvent` Race di `_on_track_ended`

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | `reason="eof"` → `await asyncio.sleep(0.35)` lalu `_advance_to_next()`. Jika dalam 0.35s ada event `end-file` kedua (misalnya karena MPV reconnect), dua coroutine autoplay jalan paralel → dua lagu diputar sekaligus atau lagu dilewati |
| **Penyebab** | Tidak ada guard untuk memastikan hanya satu autoplay chain berjalan |
| **Lokasi** | `engine/playback/controller.py` · `_on_track_ended()` |

**Kode Bermasalah:**
```python
async def _on_track_ended(self, event: TrackEndedEvent):
    if reason == "eof":
        await asyncio.sleep(0.35)
        await self._advance_to_next()   # ← tidak ada proteksi double-fire
```

**Solusi:**
```python
def __init__(self, ...):
    ...
    self._advancing = False   # flag guard

async def _on_track_ended(self, event: TrackEndedEvent):
    reason = event.reason
    if reason == "eof":
        if self._advancing:
            return  # abaikan event duplikat
        self._advancing = True
        try:
            await asyncio.sleep(0.35)
            await self._advance_to_next()
        finally:
            self._advancing = False
    elif reason == "error":
        ...
```

---

### EXC-05 — `bare except` di `_handle_delete_download`

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Kegagalan menghapus file user tidak dilaporkan ke client |
| **Penyebab** | `except:` tanpa type swallows semua exceptions termasuk `SystemExit` dan `KeyboardInterrupt` |
| **Lokasi** | `server/handlers/ws/download_handlers.py` · `_handle_delete_download()` |

**Kode Bermasalah:**
```python
try:
    os.remove(str(user_path))
except:   # ← bare except!
    pass
```

**Solusi:**
```python
try:
    os.remove(str(user_path))
except OSError as e:
    logger.warning(f"Gagal hapus user download {user_path}: {e}")
```

---

## CONCURRENCY & RACE CONDITIONS

---

### CC-01 — `STATS.is_playing` Diset Tanpa Lock dari Async Context

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | `_status_bar_worker` adalah daemon thread yang membaca `STATS` dengan lock. Tapi `STATS.is_playing = True` di `controller.py` dan `playback_commands.py` diset langsung tanpa lock → potensial torn read di ARM (non-x86) |
| **Penyebab** | `STATS._Stats.inc()` menggunakan lock tapi direct attribute assignment tidak |
| **Lokasi** | `engine/playback/controller.py` L127, `engine/playback/playback_commands.py` L54, `core/log_config.py` |

**Kode Bermasalah:**
```python
# controller.py
STATS.is_playing = True    # ← tanpa lock!
STATS.current_track = track.title[:50]

# log_config.py _status_bar_worker:
with STATS.lock:
    is_playing = STATS.is_playing   # ← dibaca dengan lock, tapi written tanpa lock
```

**Solusi:**
```python
# Tambahkan helper method ke _Stats
def set(self, field, value):
    with self.lock:
        setattr(self, field, value)

# Gunakan di semua tempat:
STATS.set('is_playing', True)
STATS.set('current_track', track.title[:50])
```

---

### CC-02 — `ConnectionManager.active_connections` List Tanpa Lock

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `connect()` append, `disconnect()` remove, `broadcast()` iterates — semua asyncio (single-thread), aman. Tapi jika ada bug atau future threading, ini akan race. Selain itu, `broadcast()` iterates `list(self.active_connections)` yang merupakan snapshot — disconnect saat broadcast tidak segera efektif. |
| **Penyebab** | Desain async-only tanpa explicit lock |
| **Lokasi** | `server/handlers/websocket.py` · `ConnectionManager` |

**Solusi:**
```python
# Ganti list dengan set untuk O(1) lookup/remove
# Dan tambahkan asyncio.Lock untuk keamanan

class ConnectionManager:
    def __init__(self):
        self._connections: set = set()
        self._conn_lock = asyncio.Lock()
    
    async def connect(self, ws):
        async with self._conn_lock:
            self._connections.add(ws)
        ACTIVE_WEBSOCKETS.inc()
    
    def disconnect(self, ws):
        self._connections.discard(ws)   # O(1), tidak raise jika tidak ada
        ACTIVE_WEBSOCKETS.dec()
    
    async def broadcast(self, message):
        async with self._conn_lock:
            targets = set(self._connections)
        ...
```

---

### CC-03 — `play_track()` Retry di Luar Lock — Stale State Access

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `backoff = 2 ** self._retry_count` dibaca setelah `async with self._play_lock` keluar. Antara keluar lock dan baca `_retry_count`, nilai bisa berubah dari coroutine lain yang menang lock. |
| **Penyebab** | Retry logic split antara dalam dan luar lock |
| **Lokasi** | `engine/playback/controller.py` · `play_track()` L146-150 |

**Kode Bermasalah:**
```python
async with self._play_lock:
    ...
    self._retry_count += 1
    if self._retry_count >= 3:
        self._retry_count = 0
    else:
        should_retry = True

if should_retry:
    backoff = 2 ** self._retry_count   # ← _retry_count bisa berubah!
    await asyncio.sleep(backoff)
    if self.state.current_track == track:
        await self._advance_to_next()
```

**Solusi:**
```python
retry_count_snapshot = 0
async with self._play_lock:
    ...
    self._retry_count += 1
    retry_count_snapshot = self._retry_count
    if self._retry_count >= 3:
        self._retry_count = 0
    else:
        should_retry = True

if should_retry:
    backoff = 2 ** retry_count_snapshot   # ← gunakan snapshot
    await asyncio.sleep(backoff)
    if self.state.current_track == track:
        await self._advance_to_next()
```

---

### CC-04 — `DownloadManager._download_lock` Memblokir Task Kedua Selamanya

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Dua request download yang berbeda berjalan melalui `_do_download()`. Task kedua menunggu `_download_lock` yang dipegang task pertama. Tidak ada timeout — task kedua bisa menunggu selama download pertama berlangsung (bisa 10+ menit). |
| **Penyebab** | `asyncio.Lock` tanpa timeout untuk operasi long-running |
| **Lokasi** | `engine/download_manager.py` · `_do_download()` |

**Solusi:**
```python
try:
    await asyncio.wait_for(self._download_lock.acquire(), timeout=5.0)
except asyncio.TimeoutError:
    await self.bus.publish(LogMessageEvent(message="Download sedang berjalan. Tunggu selesai dulu."))
    return
try:
    # ... download logic ...
finally:
    self._download_lock.release()
    self._downloading_ids.discard(track.video_id)
```

---

## CACHING ISSUES

---

### CAC-01 — Lyrics Cache FIFO Bukan LRU — Hotspot Eviction

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Cache lirik 50 item menggunakan FIFO eviction. Lagu yang paling sering diputar (hotspot) bisa di-evict sementara lagu yang hanya diputar sekali tetap ada di cache. |
| **Penyebab** | `self._cache.pop(next(iter(self._cache)))` — evict item pertama (tertua), bukan least-recently-used |
| **Lokasi** | `plugins/lyrics.py` · `fetch()` |

**Kode Bermasalah:**
```python
if len(self._cache) > 50:
    self._cache.pop(next(iter(self._cache)))   # FIFO, bukan LRU
```

**Solusi — Gunakan OrderedDict sebagai LRU:**
```python
from collections import OrderedDict

def __init__(self, ...):
    self._cache: OrderedDict[str, str] = OrderedDict()
    self._cache_max = 50

# Saat get:
def _cache_get(self, key):
    if key in self._cache:
        self._cache.move_to_end(key)  # tandai sebagai recently used
        return self._cache[key]
    return None

# Saat set:
def _cache_set(self, key, value):
    if key in self._cache:
        self._cache.move_to_end(key)
    self._cache[key] = value
    if len(self._cache) > self._cache_max:
        self._cache.popitem(last=False)  # evict LRU (oldest)
```

---

### CAC-02 — Stream URL TTL di Batas Bawah Kedaluwarsa YouTube

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `STREAM_URL_TTL_SEC = 21600` (6 jam). YouTube stream URL biasanya expire dalam 6 jam. URL yang di-cache tepat di batas TTL mungkin sudah tidak valid saat diputar → error 403 dari YouTube |
| **Penyebab** | TTL terlalu optimistik — tidak ada safety margin |
| **Lokasi** | `config.py` |

**Solusi:**
```python
# Kurangi TTL dengan safety margin 1 jam
STREAM_URL_TTL_SEC = 18000  # 5 jam (bukan 6 jam)

# Atau tambahkan jitter untuk menghindari mass-expiry
import random
effective_ttl = STREAM_URL_TTL_SEC - random.randint(0, 3600)
```

---

### CAC-03 — `StreamPrefetchService._fetching` Bisa Bocor Saat Exception

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Jika `get_stream_url()` raise exception sebelum `finally` — wait, `finally` selalu dijalankan. Tapi jika `asyncio.CancelledError` terjadi di `event.set()` sendiri (sangat jarang), entry bisa tertinggal. Lebih penting: tidak ada timeout pada `wait()` |
| **Lokasi** | `server/services/stream_prefetch.py` |

Lihat juga **EXC-02** untuk solusi timeout.

---

## QUEUE ISSUES

---

### QUE-01 — `deque` Delete by Index adalah O(n) — Performance Bottleneck

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Untuk queue 1000 lagu, `del self.state.queue[cmd.index]` di `on_queue_remove()` adalah O(n) karena deque harus dikonversi ke list. Untuk `on_queue_reorder()`, `del q[cmd.from_index]` dan `q.insert(cmd.to_index, item)` masing-masing O(n). |
| **Penyebab** | `collections.deque` tidak efisien untuk random-access modification |
| **Lokasi** | `engine/playback/queue_commands.py` · `on_queue_remove()`, `on_queue_reorder()` |

**Solusi:** Ganti `deque` dengan `list` untuk `state.queue` (list lebih efisien untuk random access). Pertahankan `deque` hanya untuk `history` yang operasinya adalah append/popleft:
```python
# core/state.py
@dataclass
class AppState:
    queue: list = field(default_factory=list)   # list untuk O(1) random access
    radio_queue: list = field(default_factory=list)
    history: deque = field(default_factory=lambda: deque(maxlen=50))  # tetap deque
```

---

### QUE-02 — `ENQUEUE_GENRE_SONGS` Tidak Langsung Putar — User Harus Klik Lagi

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `_handle_enqueue_genre_songs()` memanggil `QueueSelectCommand(index=0)` setelah `QueueReplaceCommand`. Tapi `QueueSelectCommand` hanya memilih dari queue jika `0 <= index < len(queue)` — ini berfungsi, tapi melewati `_play_lock` dua kali. Jika race terjadi antara dua execute(), queue bisa berubah. |
| **Lokasi** | `server/handlers/ws/queue_handlers.py` · `_handle_enqueue_genre_songs()` |

**Kode Bermasalah:**
```python
await command_bus.execute(SetModeCommand(mode=PlaybackMode.QUEUE))
await command_bus.execute(QueueReplaceCommand(tracks=songs))
await command_bus.execute(QueueSelectCommand(index=0))
# tiga command terpisah, tidak atomik
```

**Solusi:** Buat command atomik `PlayQueueCommand` atau handle di satu handler:
```python
if songs:
    first_track, rest = songs[0], songs[1:]
    await command_bus.execute(SetModeCommand(mode=PlaybackMode.QUEUE))
    await command_bus.execute(QueueReplaceCommand(tracks=rest))
    await command_bus.execute(PlayTrackCommand(track=first_track))
```

---

### QUE-03 — Queue Tidak Persisten — Hilang Saat Restart

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Queue pengguna hilang setiap restart. Untuk produksi, ini adalah UX yang buruk. |
| **Penyebab** | Queue hanya disimpan di memori (`AppState.queue`) |
| **Solusi** | Simpan queue ke SQLite saat berubah, restore saat startup |

```python
# cache/schema.sql — tambahkan tabel
CREATE TABLE IF NOT EXISTS queue_state (
    position INTEGER PRIMARY KEY,
    video_id TEXT NOT NULL,
    title TEXT,
    artist TEXT,
    duration INTEGER,
    thumbnail TEXT
);

# core/bootstrap.py — restore queue saat startup
async def _restore_queue(state: AppState, db: Database):
    rows = await db.conn.execute(
        "SELECT * FROM queue_state ORDER BY position"
    )
    for row in await rows.fetchall():
        track = TrackInfo(video_id=row["video_id"], ...)
        state.queue.append(track)
```

---

## RETRY & RESILIENCE ISSUES

---

### RTY-01 — `CacheResolver.resolve()` Tidak Ada Retry untuk Fetch Gagal

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Satu kegagalan transien dari yt-dlp (network blip) langsung gagalkan pemutaran. Tidak ada retry atau backoff. |
| **Penyebab** | `get_stream_url()` di-await sekali, exception langsung di-raise ke caller |
| **Lokasi** | `cache/resolver.py` · `resolve()` |

**Solusi:**
```python
async def resolve(self, track: TrackInfo) -> str:
    ...
    MAX_RETRIES = 2
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            url = await self.ytdlp.get_stream_url(track.video_id)
            if url:
                track.stream_url = url
                await self.db.upsert_track(track, stream_url=url)
                return url
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Resolve attempt {attempt+1} gagal, retry...")
                await asyncio.sleep(1.5 ** attempt)
    raise RuntimeError(f"Gagal resolve setelah {MAX_RETRIES} percobaan: {last_error}") from last_error
```

---

### RTY-02 — MPV Reconnect Tidak Restore Queue State

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `_on_mpv_reconnected()` me-restore posisi playback track saat ini, tapi tidak restore queue atau mode. Jika MPV disconnect saat radio mode, setelah reconnect radio tidak aktif lagi. |
| **Penyebab** | `_on_mpv_reconnected()` hanya restore `current_track` dan `position` |
| **Lokasi** | `engine/playback/controller.py` · `_on_mpv_reconnected()` |

**Solusi:**
```python
async def _on_mpv_reconnected(self, event: MpvReconnectedEvent):
    if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED) and self.state.current_track:
        try:
            uri = await self.resolver.resolve(self.state.current_track)
            await self.mpv.play(uri)
            await self.mpv.seek(self.state.position)
            await self.mpv.set_volume(
                0 if self.state.audio_output == AudioOutput.BROWSER else self.state.volume
            )
            if self.state.status == PlayerStatus.PLAYING:
                await self.mpv.resume()
            else:
                await self.mpv.pause()
            # Broadcast state untuk sync semua client
            await self.bus.publish(QueueUpdatedEvent())
        except Exception as e:
            logger.error(f"Failed to restore playback: {e}")
```

---

### RTY-03 — `_observe_events()` Kill + Terminate Tanpa Check Exit Status

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `self._mpv_process.terminate()` lalu `self._mpv_process.kill()` tanpa delay → kill dikirim mungkin sebelum terminate sempat berjalan, atau proses sudah mati → OSError |
| **Penyebab** | Tidak ada `wait_for` antara terminate dan kill |
| **Lokasi** | `engine/mpv_controller.py` · `_observe_events()` finally |

**Kode Bermasalah:**
```python
if self._mpv_process:
    try:
        self._mpv_process.terminate()
        self._mpv_process.kill()   # ← langsung kill tanpa tunggu
    except OSError:
        pass
```

**Solusi:**
```python
if self._mpv_process:
    try:
        self._mpv_process.terminate()
        try:
            await asyncio.wait_for(self._mpv_process.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            self._mpv_process.kill()
    except OSError:
        pass
    finally:
        self._mpv_process = None
```

---

## REPOSITORY ISSUES

---

### REP-01 — `Database.__getattr__` Proxy Tidak Aman Sebelum `init()`

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | Jika ada kode yang memanggil `db.get_track()` sebelum `await db.init()` selesai, `self.tracks` adalah `None`, `__getattr__` tidak akan menemukan method, dan akan raise `AttributeError` dengan pesan yang membingungkan |
| **Penyebab** | `__getattr__` tidak ada guard untuk state "belum diinisialisasi" |
| **Lokasi** | `cache/db.py` · `__getattr__()` |

**Kode Bermasalah:**
```python
def __getattr__(self, name):
    if self.tracks and hasattr(self.tracks, name):
        return getattr(self.tracks, name)
    # jika self.tracks = None → tidak masuk sini → raise AttributeError
    raise AttributeError(f"'Database' object has no attribute '{name}'")
```

**Solusi:**
```python
def __getattr__(self, name):
    if self._conn is None:
        raise RuntimeError(
            f"Database belum diinisialisasi. Panggil 'await db.init()' terlebih dahulu. "
            f"Attribute yang dicoba: '{name}'"
        )
    for repo in (self.tracks, self.sessions, self.discover):
        if repo is not None and hasattr(repo, name):
            return getattr(repo, name)
    raise AttributeError(f"'Database' object has no attribute '{name}'")
```

---

### REP-02 — `evict_stale_tracks()` Load All IDs ke Memory

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Jika ada 100.000 stale tracks, seluruh video_id di-load ke Python list sebelum delete. Untuk skala besar ini bermasalah. |
| **Penyebab** | `fetchall()` tanpa batching |
| **Lokasi** | `cache/repositories/track_repository.py` · `evict_stale_tracks()` |

**Solusi — Batch Delete:**
```python
async def evict_stale_tracks(self, batch_size=500) -> int:
    if not self._conn: return 0
    total_deleted = 0
    while True:
        cursor = await self._conn.execute(
            """SELECT video_id FROM tracks
               WHERE play_count = 0 AND local_path IS NULL
               AND (is_favorite = 0 OR is_favorite IS NULL)
               AND (stream_url_ts IS NULL OR stream_url_ts < ?)
               LIMIT ?""",
            (int(time.time()) - 30*24*3600, batch_size)
        )
        rows = await cursor.fetchall()
        if not rows:
            break
        
        video_ids = [r["video_id"] for r in rows]
        # delete files + DB records (batch)
        placeholders = ','.join(['?'] * len(video_ids))
        await self._conn.execute(
            f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids
        )
        await self._conn.commit()
        total_deleted += len(video_ids)
        
        if len(rows) < batch_size:
            break
    
    return total_deleted
```

---

### REP-03 — `discover_handlers.py` Bypass Repository Layer — Direct DB Access

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Handler langsung memanggil `db.conn.execute()` dan `db.conn.commit()` — bypass repository, mengakibatkan duplikasi logic dan tidak ada validasi |
| **Penyebab** | `toggle_favorite` dengan `set_favorite` parameter tidak ada di repository |
| **Lokasi** | `server/handlers/ws/discover_handlers.py` · `_handle_toggle_favorite()` |

**Kode Bermasalah:**
```python
if set_favorite is not None:
    target = 1 if set_favorite else 0
    await db.conn.execute(
        "UPDATE tracks SET is_favorite = ? WHERE video_id = ?", (target, video_id)
    )
    await db.conn.commit()   # ← direct DB access dari handler!
```

**Solusi — Tambahkan method ke repository:**
```python
# track_repository.py
async def set_favorite(self, video_id: str, is_favorite: bool) -> int:
    if not self._conn: return 0
    val = 1 if is_favorite else 0
    await self._conn.execute(
        "UPDATE tracks SET is_favorite = ? WHERE video_id = ?", (val, video_id)
    )
    await self._conn.commit()
    return val

# discover_handlers.py
if set_favorite is not None:
    is_fav = await db.set_favorite(video_id, bool(set_favorite))
else:
    is_fav = await db.toggle_favorite(video_id)
```

---

### REP-04 — SQL `WITH RankedSongs` Window Function — SQLite Compatibility Risk

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `ROW_NUMBER() OVER (PARTITION BY ...)` memerlukan SQLite 3.25+ (2018). Termux di Android lama bisa menggunakan versi lebih tua |
| **Penyebab** | Window functions adalah fitur SQLite yang relatif baru |
| **Lokasi** | `cache/repositories/discover_repository.py` · `get_random_songs()`, `get_genre_songs()` |

**Solusi — Verifikasi versi saat startup:**
```python
# cache/db.py di init()
async with self._conn.execute("SELECT sqlite_version()") as cursor:
    row = await cursor.fetchone()
    version_str = row[0]
    major, minor, *_ = [int(x) for x in version_str.split('.')]
    if (major, minor) < (3, 25):
        logger.warning(
            f"SQLite {version_str} tidak mendukung window functions. "
            "Radio mode mungkin tidak bekerja dengan benar."
        )
```

---

## SERVICE LAYER ISSUES

---

### SVC-01 — `DiscoverService` Diinstansiasi per Request — Overhead Tidak Perlu

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | Setiap request DISCOVER WebSocket membuat instance `DiscoverService` baru. Objek ringan tapi pola ini tidak scalable dan mencegah caching tingkat service. |
| **Penyebab** | Tidak ada singleton atau DI container |
| **Lokasi** | `server/handlers/ws/discover_handlers.py` · `_build_discover_payload()` |

**Kode Bermasalah:**
```python
async def _build_discover_payload(db):
    ds = DiscoverService(db)   # ← new instance per request
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)
    ...
```

**Solusi — Singleton DiscoverService:**
```python
# server/app.py
discover_service = DiscoverService(db)
app["discover_service"] = discover_service

# discover_handlers.py
async def _build_discover_payload(db, discover_service=None):
    ds = discover_service or DiscoverService(db)
    ...
```

---

### SVC-02 — `BroadcastService.broadcast_state()` Serialisasi Full State per Setiap Progress Event

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `TrackProgressEvent` dikirim setiap 0.33 detik → `broadcast_progress()` dipanggil (difilter 0.5s). Tapi `_on_queue_updated` memanggil `broadcast_state()` yang serialisasi full state termasuk seluruh queue. Untuk queue 200 lagu, ini bisa ratusan KB per update. |
| **Penyebab** | Tidak ada differential/incremental state update |
| **Lokasi** | `server/handlers/event_listeners.py`, `server/services/broadcast_service.py` |

**Solusi — Partial State Updates:**
```python
# broadcast_service.py
async def broadcast_queue_only(self, state: AppState):
    """Broadcast hanya queue, tanpa lyrics dan progress."""
    await self.manager.broadcast({
        "type": "queue_update",
        "data": {
            "queue": [t.to_dict() for t in state.queue],
            "radio_queue": [t.to_dict() for t in state.radio_queue],
            "current_track": state.current_track.to_dict() if state.current_track else None,
            "status": state.status.name,
            "playback_mode": state.playback_mode.name,
        }
    })

# event_listeners.py
async def _on_queue_updated(event: QueueUpdatedEvent):
    await broadcast_service.broadcast_queue_only(playback_controller.state)
```

---

### SVC-03 — `VolumeService` Tidak Sync dengan State saat Init

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `VolumeService.current_volume` diinisialisasi dari `state.volume` di constructor, tapi jika MPV sudah berjalan dengan volume berbeda, nilai tidak sync |
| **Penyebab** | Tidak ada sync dengan MPV saat init |
| **Lokasi** | `engine/volume_service.py` · `__init__()` |

**Solusi:**
```python
async def sync_with_mpv(self):
    """Sync volume state dengan MPV yang berjalan."""
    if self.mpv.is_connected:
        try:
            current = await self.mpv._get_property("volume")
            if current is not None:
                self.current_volume = Volume(int(current))
                self.state.volume = self.current_volume
        except Exception:
            pass  # fallback ke state.volume

# Panggil dari bootstrap setelah connect:
await volume_service.sync_with_mpv()
```

---

## DEPENDENCY & LAYERING VIOLATIONS

---

### DEP-01 — Domain Layer Import dari Logging Infrastructure

| Field | Detail |
|---|---|
| **Severity** | 🟠 HIGH |
| **Dampak** | `engine/playback/controller.py` mengimport `STATS` dari `core/log_config.py`. Domain logic (playback) seharusnya tidak bergantung pada logging infrastructure. Ini menciptakan coupling yang tidak perlu dan membuat unit testing domain logic lebih sulit. |
| **Penyebab** | `STATS` objek digunakan sebagai side-channel untuk status bar |
| **Lokasi** | `engine/playback/controller.py` L17, `engine/playback/playback_commands.py` L4 |

**Kode Bermasalah:**
```python
# engine/playback/controller.py — domain layer
from core.log_config import STATS   # ← import dari infrastructure!

class PlaybackController:
    async def play_track(self, track):
        ...
        STATS.is_playing = True   # ← domain mengubah logging state!
```

**Solusi — Gunakan Event:**
```python
# Tambahkan domain event
@dataclass
class PlaybackStatusChangedEvent(DomainEvent):
    is_playing: bool
    current_track_title: str = ""
    songs_played_delta: int = 0

# Di controller, publish event alih-alih langsung ubah STATS
await self.bus.publish(PlaybackStatusChangedEvent(
    is_playing=True,
    current_track_title=track.title[:50],
    songs_played_delta=1
))

# Di log_config atau event_listener, subscribe ke event:
def _on_playback_status_changed(event: PlaybackStatusChangedEvent):
    with STATS.lock:
        STATS.is_playing = event.is_playing
        STATS.current_track = event.current_track_title
        if event.songs_played_delta:
            STATS.songs_played += event.songs_played_delta
```

---

### DEP-02 — `track_loader.py` Akses DB Langsung via `resolver.db`

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `TrackLoader` akses database melalui `resolver.db` — ini mengekspos internal CacheResolver dan menciptakan coupling tidak langsung ke DB. Jika resolver diubah, TrackLoader bisa broken. |
| **Penyebab** | Tidak ada port/interface yang tepat untuk `increment_play_count` di level TrackLoader |
| **Lokasi** | `engine/playback/track_loader.py` L27 |

**Kode Bermasalah:**
```python
async def load_track(self, track: TrackInfo) -> str:
    uri = await self.resolver.resolve(track)
    await self.resolver.db.increment_play_count(track.video_id)  # ← akses DB via resolver!
```

**Solusi:**
```python
# Inject db port secara eksplisit ke TrackLoader
class TrackLoader:
    def __init__(self, resolver, sponsorblock, lyrics_fetcher, db: TrackRepositoryPort):
        self.db = db
        ...
    
    async def load_track(self, track):
        uri = await self.resolver.resolve(track)
        await self.db.increment_play_count(track.video_id)
        ...
```

---

### DEP-03 — `event_listeners.py` Import dari `discover_handlers.py` — Circular-Risk

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `server/handlers/event_listeners.py` mengimport `broadcast_discover_data` dari `server/handlers/ws/discover_handlers.py`. Ini berarti satu handler mengimport dari handler lain di layer yang sama — antar-handler dependency yang tidak sehat. |
| **Penyebab** | Tidak ada shared service untuk discover broadcast |
| **Lokasi** | `server/handlers/event_listeners.py` L57-58 |

**Kode Bermasalah:**
```python
# event_listeners.py
from server.handlers.ws.discover_handlers import broadcast_discover_data   # ← antar-handler import
...
await broadcast_discover_data(broadcast_service.manager, playback_controller.resolver.db)
```

**Solusi — Pindahkan ke BroadcastService:**
```python
# broadcast_service.py
async def broadcast_discover(self, db):
    from server.services.discover_service import DiscoverService
    ds = DiscoverService(db)
    payload = {
        "type": "discover_data",
        "data": {
            "recent": [t.to_dict() for t in await ds.get_recent(15)],
            ...
        }
    }
    await self.manager.broadcast(payload)

# event_listeners.py
async def _on_download_complete(event: DownloadCompleteEvent):
    await broadcast_service.broadcast_state(playback_controller.state)
    if event.track:
        await playback_controller.resolver.db.upsert_track(event.track, local_path=event.track.local_path)
        await broadcast_service.broadcast_discover(playback_controller.resolver.db)
```

---

### DEP-04 — `PlaybackController` Akses `resolver.db` Langsung

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `engine/playback/controller.py` memanggil `self.resolver.db.upsert_track()` di beberapa tempat — akses DB melalui dua layer (resolver → db) dari domain controller |
| **Lokasi** | `engine/playback/controller.py` L89, L105 |

**Kode Bermasalah:**
```python
safe_create_task(self.resolver.db.upsert_track(self.state.current_track), ...)
safe_create_task(self.db.upsert_track(track), ...)   # kadang pakai self.db, kadang self.resolver.db
```

Ini juga menunjukkan inkonsistensi: `PlaybackController` memiliki `self.db` (dari `PlaybackDependencies`) tapi kadang menggunakan `self.resolver.db` — dua referensi ke objek yang sama tapi diakses melalui path berbeda.

**Solusi:** Selalu gunakan `self.db` dan hapus akses via `self.resolver.db`:
```python
# Konsisten gunakan self.db
safe_create_task(self.db.upsert_track(self.state.current_track), name="upsert_track_duration")
```

---

### DEP-05 — `config.py` Diimport dari Hampir Semua Layer

| Field | Detail |
|---|---|
| **Severity** | 🟡 MEDIUM |
| **Dampak** | `config.py` diimport dari `core/`, `engine/`, `cache/`, `server/`, `plugins/` — semua layer bergantung pada satu file konfigurasi global. Testing individual modul memerlukan patching config values. |
| **Penyebab** | Tidak ada dependency injection untuk config |

**Solusi — Config Dataclass dengan DI:**
```python
# core/config_port.py
from dataclasses import dataclass

@dataclass
class AppConfig:
    db_path: str
    cache_dir: str
    mpv_socket: str
    default_volume: int = 80
    stream_url_ttl_sec: int = 18000
    ytdlp_resolve_timeout_sec: int = 25
    web_host: str = "0.0.0.0"
    web_port: int = 8765
    lyrics_api_base: str = "https://lrclib.net/api"

# Injeksikan ke semua komponen yang membutuhkan, bukan import langsung
```

---

## SUMMARY TABLE

| ID | Kategori | Severity | File | Deskripsi |
|---|---|---|---|---|
| BUG-01 | Business Logic | 🔴 CRITICAL | `discover_service.py` | KeyError `stream_url` — Discover tab crash |
| BUG-02 | Code Quality | 🔴 CRITICAL | `mpv_controller.py` | `import time` di bawah class |
| BUG-03 | Business Logic | 🔴 CRITICAL | `radio_commands.py` | RadioRandomize hanya jalan di RADIO mode |
| BUG-04 | Security | 🔴 CRITICAL | `config.py` | Admin password tidak muncul di non-TTY |
| BL-01 | Business Logic | 🟠 HIGH | `queue_commands.py` | Queue select membuang track tanpa update history |
| BL-02 | Business Logic | 🟠 HIGH | Multiple | Volume cap 100 vs 150 inkonsisten |
| BL-03 | Business Logic | 🟡 MEDIUM | `discover_repository.py` | Seed artist tidak dijamin muncul |
| BL-04 | Concurrency | 🟡 MEDIUM | `radio_engine.py` | Race pada queue length check |
| TXN-01 | Transaction | 🟠 HIGH | Repositories | N+1 commit anti-pattern |
| TXN-02 | Transaction | 🟠 HIGH | `db.py` | Seeding tanpa atomic transaction |
| TXN-03 | Transaction | 🟡 MEDIUM | `track_repository.py` | `RETURNING` SQLite 3.35+ only |
| TXN-04 | Transaction | 🟡 MEDIUM | `track_repository.py` | `last_played` terpolusi saat non-play upsert |
| EXC-01 | Exception | 🟠 HIGH | `resolver.py` | Thundering herd setelah fetch error |
| EXC-02 | Exception | 🟠 HIGH | `resolver.py`, `stream_prefetch.py` | `wait()` tanpa timeout — deadlock potensial |
| EXC-03 | Exception | 🟠 HIGH | `http.py` | `_stream_rate_limit` memory leak |
| EXC-04 | Exception | 🟠 HIGH | `controller.py` | Double TrackEndedEvent race |
| EXC-05 | Exception | 🟡 MEDIUM | `download_handlers.py` | Bare `except:` |
| CC-01 | Concurrency | 🟠 HIGH | `controller.py`, `log_config.py` | `STATS` ditulis tanpa lock dari async |
| CC-02 | Concurrency | 🟡 MEDIUM | `websocket.py` | `active_connections` list tanpa lock |
| CC-03 | Concurrency | 🟡 MEDIUM | `controller.py` | Retry logic baca stale `_retry_count` |
| CC-04 | Concurrency | 🟡 MEDIUM | `download_manager.py` | Lock tanpa timeout untuk long operation |
| CAC-01 | Caching | 🟡 MEDIUM | `lyrics.py` | Cache FIFO bukan LRU |
| CAC-02 | Caching | 🟡 MEDIUM | `config.py` | Stream URL TTL di batas kedaluwarsa YouTube |
| CAC-03 | Caching | 🟡 MEDIUM | `stream_prefetch.py` | `_fetching` tanpa timeout |
| QUE-01 | Queue | 🟡 MEDIUM | `queue_commands.py` | `deque` delete O(n) |
| QUE-02 | Queue | 🟡 MEDIUM | `queue_handlers.py` | Genre enqueue tidak atomik |
| QUE-03 | Queue | 🟡 MEDIUM | `state.py` | Queue tidak persisten |
| RTY-01 | Retry | 🟠 HIGH | `resolver.py` | Tidak ada retry untuk URL fetch gagal |
| RTY-02 | Retry | 🟡 MEDIUM | `controller.py` | MPV reconnect tidak restore queue state |
| RTY-03 | Retry | 🟡 MEDIUM | `mpv_controller.py` | Kill tanpa wait setelah terminate |
| REP-01 | Repository | 🟠 HIGH | `db.py` | `__getattr__` proxy tidak safe sebelum init |
| REP-02 | Repository | 🟡 MEDIUM | `track_repository.py` | `evict_stale_tracks` load semua ke memory |
| REP-03 | Repository | 🟡 MEDIUM | `discover_handlers.py` | Direct DB access bypass repository |
| REP-04 | Repository | 🟡 MEDIUM | `discover_repository.py` | Window functions SQLite 3.25+ only |
| SVC-01 | Service | 🟡 MEDIUM | `discover_handlers.py` | `DiscoverService` diinstansiasi per request |
| SVC-02 | Service | 🟡 MEDIUM | `event_listeners.py` | Full state serialisasi tiap progress event |
| SVC-03 | Service | 🟡 MEDIUM | `volume_service.py` | Volume tidak sync dengan MPV saat init |
| DEP-01 | Dependency | 🟠 HIGH | `controller.py` | Domain import logging infrastructure |
| DEP-02 | Dependency | 🟡 MEDIUM | `track_loader.py` | DB diakses via `resolver.db` |
| DEP-03 | Dependency | 🟡 MEDIUM | `event_listeners.py` | Import antar-handler |
| DEP-04 | Dependency | 🟡 MEDIUM | `controller.py` | Inkonsistensi `self.db` vs `self.resolver.db` |
| DEP-05 | Dependency | 🟡 MEDIUM | Multiple | `config.py` diimport semua layer |

---

## PRIORITY ACTION PLAN

### Sprint 0 — Fix Sekarang (Blocker Production)
1. **BUG-01** — Fix `stream_url` KeyError di `DiscoverService` (5 menit, 3 baris)
2. **BUG-02** — Pindahkan `import time` ke atas `mpv_controller.py` (1 menit)
3. **BUG-03** — Fix `on_radio_randomize` agar auto-switch ke RADIO mode
4. **BUG-04** — Hapus `isatty()` check untuk password output

### Sprint 1 — High Priority (Week 1)
- TXN-01, TXN-02 — Batch transaction + atomic seeding
- EXC-01, EXC-02 — Error caching + wait timeout di resolver
- EXC-03 — Cleanup `_stream_rate_limit` memory leak
- EXC-04 — Guard double TrackEndedEvent
- RTY-01 — Tambah retry di `CacheResolver.resolve()`
- REP-01 — `__getattr__` proxy safety check

### Sprint 2 — Medium Priority (Week 2-3)
- CC-01 — STATS thread-safety
- DEP-01 — Pisahkan domain dari logging infra
- BL-01, BL-02 — Queue select history + volume consistency
- TXN-03, TXN-04 — SQLite compat + last_played fix
- REP-03 — Remove direct DB access dari handler

### Sprint 3 — Technical Debt (Month 2)
- QUE-01 — Ganti deque dengan list untuk queue
- QUE-03 — Queue persistence
- CAC-01 — LRU untuk lyrics cache
- SVC-02 — Partial state updates
- DEP-05 — Config injection

---

*Laporan ini dihasilkan dari audit menyeluruh terhadap seluruh kode backend LunaWave. Setiap temuan disertai lokasi eksak, kode bermasalah, dan solusi implementasi yang siap diterapkan.*
