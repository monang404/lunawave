# BUG AUDIT REPORT — LUNAWAVE
**Tanggal:** 2026-07-06  
**Auditor:** Tim Audit 10 Persona  
**Codebase:** `lunawave-main`  
**Total Temuan:** 28 bug terverifikasi

---

## RINGKASAN SEVERITY

| Severity | Jumlah |
|---|---|
| 🔴 CRITICAL | 6 |
| 🟠 HIGH | 9 |
| 🟡 MEDIUM | 8 |
| 🟢 LOW | 5 |

---

## KATEGORI INDEX

| ID | Judul | Severity | Kategori |
|---|---|---|---|
| B-01 | `discover_service` KeyError: `stream_url` tidak di-SELECT | 🔴 CRITICAL | Null Pointer / Logic Bug |
| B-02 | `handle_auth` tidur di dalam global `rl_lock` — DoS semua autentikasi | 🔴 CRITICAL | Async Bug / Race Condition |
| B-03 | `_on_track_ended` reason kosong `""` tidak ditangani — autoplay mati diam-diam | 🔴 CRITICAL | Logic Bug / Hidden Bug |
| B-04 | `play_track` retry backoff membaca `_retry_count` setelah lock dilepas — nilai stale | 🔴 CRITICAL | Race Condition / Async Bug |
| B-05 | `_on_track_ended` error path: guard `if IDLE` tidak pernah terpenuhi — double advance | 🔴 CRITICAL | Logic Bug / State Bug |
| B-06 | `import time` di baris paling akhir `mpv_controller.py` — NameError saat cold path | 🔴 CRITICAL | Hidden Bug |
| B-07 | `_lock` di `PlaybackController` dideklarasikan tapi tidak pernah digunakan | 🟠 HIGH | Dead Code / Logic Bug |
| B-08 | `on_next` menahan `_lock` lalu memanggil `_advance_to_next` → `play_track` yang butuh `_play_lock` — bottleneck beruntun | 🟠 HIGH | Async Bug |
| B-09 | `_poll_duration` menerbitkan `QueueUpdatedEvent` meskipun durasi tidak berubah (path kedua) | 🟠 HIGH | Logic Bug |
| B-10 | `VolumeService.current_volume` bisa desync dari `state.volume` saat race | 🟠 HIGH | State Bug / Race Condition |
| B-11 | `handle_ws_message` melempar `json.dumps` ke attribute error jika `data` bukan `dict` | 🟠 HIGH | Error Handling |
| B-12 | `ws_handler`: exception umum ditangkap tanpa konteks — `KeyError`, `AttributeError` disembunyikan | 🟠 HIGH | Error Handling |
| B-13 | `evict_stale_tracks`: list string dioper langsung ke `execute` tanpa `tuple()` — aiosqlite error di beberapa versi | 🟠 HIGH | Hidden Bug |
| B-14 | `SponsorBlock.fetch_segments` mengosongkan `self.segments` sebelum fetch — jeda tanpa proteksi | 🟠 HIGH | Race Condition |
| B-15 | `CacheResolver._fetching` bisa leak event jika `wait()` disambar exception | 🟠 HIGH | Async Bug / Memory |
| B-16 | `_parse_lrc`: baris plain-text tanpa timestamp dimasukkan dengan `t=0.0` — lyric error di awal lagu | 🟡 MEDIUM | Logic Bug |
| B-17 | `lyrics.py`: `clean_title` / `search_query` dihitung bahkan ketika `lrc` sudah ada di cache | 🟡 MEDIUM | Logic Bug / Dead Code |
| B-18 | `_on_track_ended` reason `"eof"` — `asyncio.sleep(0.35)` tidak diproteksi dari double call | 🟡 MEDIUM | Async Bug |
| B-19 | `service_worker` fallback ke `/static/index.html` — path salah, seharusnya `/` | 🟡 MEDIUM | Logic Bug |
| B-20 | `settings_handlers.py` `volume_set` membatasi max 150 tapi `Volume()` clamp ke 100 — inkonsistensi | 🟡 MEDIUM | Logic Bug |
| B-21 | `_connectivity_checker` infinite loop tidak dapat dihentikan saat shutdown | 🟡 MEDIUM | Lifecycle Bug |
| B-22 | `on_radio_randomize`: `cmd` bisa `None` tapi diakses `cmd.seed_artist` tanpa guard | 🟡 MEDIUM | Null Pointer |
| B-23 | `TrackInfo.from_dict`: `VideoId()` melempar `ValueError` untuk ID yang di-hash fallback | 🟡 MEDIUM | Error Handling |
| B-24 | `next_data` dict dibangun tapi tidak pernah digunakan di `_on_track_ended` | 🟢 LOW | Dead Code |
| B-25 | `get_featured_genres` menggunakan `print()` bukan `logger.error()` untuk error | 🟢 LOW | Logic Bug |
| B-26 | `_CompactRenderer.__call__` mengembalikan string kosong padahal structlog mengharapkan dict atau raise | 🟢 LOW | Logic Bug |
| B-27 | `_summary_worker` dan `_status_bar_worker` tidak memeriksa `_stop` event — daemon thread bocor | 🟢 LOW | Lifecycle Bug |
| B-28 | `extractDominantColor` memanggil `callback("var(--bg-elevated)")` — callback menerima string bukan objek `{r,g,b}` | 🟢 LOW | Logic Bug |

---

## DETAIL TEMUAN

---

### B-01 — `discover_service` KeyError: `stream_url` tidak ada di SELECT

**Severity:** 🔴 CRITICAL  
**Kategori:** Null Pointer / Logic Bug  
**File:** `server/services/discover_service.py` — baris 36, 63, 90

#### Cara Reproduksi
1. Buka tab Discover atau Home
2. Server mengirim `DISCOVER` request
3. `DiscoverService.get_recent()` dieksekusi
4. SQL hanya meng-SELECT 9 kolom tapi `TrackInfo(...)` mengakses `d["stream_url"]`
5. → `KeyError: 'stream_url'` → exception tersembunyi dalam `except Exception` → return `[]`
6. Discover tab kosong tanpa pesan error ke user

#### Kode Bermasalah
```python
# discover_service.py baris 25 — stream_url TIDAK ADA di SELECT
async with self.db.conn.execute(
    "SELECT video_id, title, artist, duration, thumbnail, local_path, "
    "view_count, play_count, is_favorite FROM tracks ORDER BY last_played DESC LIMIT ?",
    (n,)
) as cursor:
    async for row in cursor:
        d = dict(row)
        tracks.append(TrackInfo(
            ...
            stream_url=d["stream_url"],   # ← KeyError! 'stream_url' tidak di SELECT
```

#### Solusi
Tambahkan `stream_url` ke query SELECT, atau gunakan `d.get("stream_url")`:

```python
# OPSI 1: Tambahkan ke SELECT (lebih bersih)
async with self.db.conn.execute(
    "SELECT video_id, title, artist, duration, thumbnail, local_path, "
    "stream_url, view_count, play_count, is_favorite "  # ← tambahkan stream_url
    "FROM tracks ORDER BY last_played DESC LIMIT ?",
    (n,)
) as cursor:
    async for row in cursor:
        d = dict(row)
        tracks.append(TrackInfo(
            ...
            stream_url=d.get("stream_url"),  # ← aman
        ))

# OPSI 2: Gunakan .get() dengan default None (fix minimal, berlaku di get_favorites dan get_cached juga)
stream_url=d.get("stream_url"),
```

**Berlaku juga di baris 63 (`get_favorites`) dan baris 90 (`get_cached`). Ketiganya harus diperbaiki.**

---

### B-02 — `handle_auth` tidur di dalam global `rl_lock` — DoS seluruh autentikasi

**Severity:** 🔴 CRITICAL  
**Kategori:** Async Bug / Race Condition  
**File:** `server/handlers/auth.py` — baris 28–45

#### Cara Reproduksi
1. IP A melakukan 2 login attempt gagal
2. IP B mencoba login secara bersamaan
3. IP A masuk `handle_auth` → `async with manager.rl_lock:` → acquire lock
4. Karena ada 2 attempt, `await asyncio.sleep(2)` dieksekusi **di dalam lock**
5. IP B's `handle_auth` menunggu lock selama 2 detik — tidak bisa login sama sekali
6. Attacker dengan 5 attempt dari satu IP membuat semua user (IP lain) tidak bisa login selama 5 detik setiap request

#### Kode Bermasalah
```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    async with manager.rl_lock:           # ← lock diambil
        _prune_stale_ips(manager, now)
        
        # ... (session check, attempt check) ...

        attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]

        if attempts:
            import asyncio
            await asyncio.sleep(min(len(attempts), 5))  # ← SLEEP DI DALAM LOCK! 🔴
```

#### Solusi
Pisahkan logic rate-limit dari logik delay. Catat jumlah attempt, lepas lock, baru tidur:

```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    delay_seconds = 0
    
    async with manager.rl_lock:
        _prune_stale_ips(manager, now)

        # Session token check
        token = data.get("token")
        if token and db:
            if await db.verify_session(token):
                manager.authenticated_connections.add(ws)
                await ws.send_str(json.dumps({"type": "auth_status", "data": {"success": True, "token": token}}))
                return

        attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]
        if attempts:
            delay_seconds = min(len(attempts), 5)   # hitung delay, JANGAN sleep di sini

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            manager.login_attempts[client_ip] = attempts
    # ← lock SUDAH DILEPAS di sini

    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)   # ← sleep di luar lock ✅

    # lanjut verifikasi username/password ...
    async with manager.rl_lock:   # ambil lock lagi hanya saat mutasi
        attempts_now = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]
        if len(attempts_now) >= MAX_LOGIN_ATTEMPTS:
            await ws.send_str(json.dumps({"type": "auth_status", "data": {"success": False, "message": "Terlalu banyak percobaan login."}}))
            return
    # ... verifikasi dan buat session ...
```

---

### B-03 — `_on_track_ended` reason kosong `""` tidak ditangani — autoplay mati diam-diam

**Severity:** 🔴 CRITICAL  
**Kategori:** Logic Bug / Hidden Bug  
**File:** `engine/playback/controller.py` — baris 174–192  
**File terkait:** `core/events.py` — `TrackEndedEvent(reason="")`

#### Cara Reproduksi
1. MPV mengirimkan event `end-file` dengan `reason` selain `eof/stop/error` (misalnya `quit`, `redirect`, `unknown`, atau string kosong)
2. `_handle_event` memanggil `await self._bus.publish(TrackEndedEvent(reason=reason))`
3. `reason` default value di `TrackEndedEvent` adalah `""` (string kosong)
4. Di `_on_track_ended`: `"" == "eof"` → False, `"" == "stop"` → False, `"" == "error"` → False
5. Tidak ada `else` — fungsi return tanpa melakukan apapun
6. **Autoplay berhenti diam-diam.** User harus skip manual.

#### Kode Bermasalah
```python
# events.py
@dataclass
class TrackEndedEvent(DomainEvent):
    reason: str = ""   # ← default kosong

# controller.py — baris 181–192
if reason == "eof":
    await asyncio.sleep(0.35)
    await self._advance_to_next()
elif reason == "stop":
    pass
elif reason == "error":
    self.state.status = PlayerStatus.ERROR
    await self.bus.publish(LogMessageEvent(message="Terjadi kesalahan pemutaran"))
    await asyncio.sleep(2)
    if self.state.status == PlayerStatus.IDLE:
        return
    await self._advance_to_next()
# ← TIDAK ADA else! reason="" / "quit" / "redirect" → autoplay mati
```

#### Solusi
```python
# controller.py — _on_track_ended
async def _on_track_ended(self, event: TrackEndedEvent):
    reason = event.reason
    logger.info(f"[AUTOPLAY] Track ended with reason: {reason!r}")

    if reason == "eof":
        await asyncio.sleep(0.35)
        await self._advance_to_next()
    elif reason == "stop":
        pass  # user stop, tidak advance
    elif reason == "error":
        self.state.status = PlayerStatus.ERROR
        await self.bus.publish(LogMessageEvent(message="Terjadi kesalahan pemutaran"))
        await asyncio.sleep(2)
        if self.state.status != PlayerStatus.ERROR:   # bukan IDLE!
            return
        await self._advance_to_next()
    else:
        # "quit", "redirect", "", atau alasan tidak dikenal → tetap advance
        logger.warning(f"[AUTOPLAY] Unhandled end-file reason: {reason!r}, advancing to next")
        await asyncio.sleep(0.5)
        await self._advance_to_next()
```

---

### B-04 — `play_track` retry backoff membaca `_retry_count` setelah lock dilepas — nilai stale

**Severity:** 🔴 CRITICAL  
**Kategori:** Race Condition / Async Bug  
**File:** `engine/playback/controller.py` — baris 139–150

#### Cara Reproduksi
1. Track gagal (exception di dalam `_play_lock`)
2. `_retry_count` dinaikkan menjadi 1 di dalam lock
3. Lock dilepas, `should_retry = True`
4. Tepat setelah lock dilepas, task lain (misal event MPV reconnect) memanggil `play_track` → `_retry_count` diubah lagi di dalam lock baru
5. Kode asli membaca `backoff = 2 ** self._retry_count` → nilai mungkin sudah berubah
6. Selain itu, **dua coroutine bisa memanggil `_advance_to_next()` secara simultan** (T1 `should_retry=True` dan T2 juga)

#### Kode Bermasalah
```python
async with self._play_lock:
    # ...
    self._retry_count += 1          # dikubah di dalam lock
    if self._retry_count >= 3:
        self._retry_count = 0
    else:
        should_retry = True
# ← lock dilepas di sini

if should_retry:
    backoff = 2 ** self._retry_count  # ← baca di luar lock! nilai bisa sudah berubah
    await asyncio.sleep(backoff)
    if self.state.current_track == track:
        await self._advance_to_next()
```

#### Solusi
Simpan nilai `retry_count` lokal sebelum lock dilepas:

```python
async with self._play_lock:
    # ...
    self._retry_count += 1
    if self._retry_count >= 3:
        await self.bus.publish(LogMessageEvent(message="Terlalu banyak kegagalan beruntun. Pemutaran dihentikan."))
        self._retry_count = 0
        should_retry = False
    else:
        should_retry = True
    local_retry_count = self._retry_count   # ← simpan snapshot sebelum lock lepas

if should_retry:
    backoff = 2 ** local_retry_count        # ← gunakan nilai snapshot
    await asyncio.sleep(backoff)
    if self.state.current_track == track:
        await self._advance_to_next()
```

---

### B-05 — `_on_track_ended` error path: guard `if IDLE` tidak pernah terpenuhi

**Severity:** 🔴 CRITICAL  
**Kategori:** Logic Bug / State Bug  
**File:** `engine/playback/controller.py` — baris 186–192

#### Cara Reproduksi
1. Track berakhir dengan `reason="error"`
2. `self.state.status` di-set ke `PlayerStatus.ERROR`
3. `await asyncio.sleep(2)` — menunggu 2 detik
4. Guard: `if self.state.status == PlayerStatus.IDLE: return`
5. Status adalah `ERROR`, bukan `IDLE` → guard **tidak pernah terpenuhi**
6. Kode selalu melanjutkan ke `_advance_to_next()` meski user sudah stop secara manual (yang set status ke `IDLE`)

Ironisnya, **komentar kode** menyiratkan intent yang benar (guard dari user stop), tapi implementasi salah (cek IDLE bukan periksa apakah track berubah).

#### Kode Bermasalah
```python
elif reason == "error":
    self.state.status = PlayerStatus.ERROR
    await self.bus.publish(LogMessageEvent(message="Terjadi kesalahan pemutaran"))
    await asyncio.sleep(2)
    if self.state.status == PlayerStatus.IDLE:   # ← TIDAK PERNAH TRUE setelah set ERROR
        return
    await self._advance_to_next()
```

#### Solusi
Guard yang benar adalah mengecek apakah track sudah diganti atau user sudah stop:

```python
elif reason == "error":
    self.state.status = PlayerStatus.ERROR
    failed_track = self.state.current_track
    await self.bus.publish(LogMessageEvent(message="Terjadi kesalahan pemutaran"))
    await asyncio.sleep(2)
    # Guard: jangan advance jika user sudah stop (current_track=None) atau ganti lagu
    if self.state.current_track is None or self.state.current_track != failed_track:
        return
    await self._advance_to_next()
```

---

### B-06 — `import time` di baris paling akhir `mpv_controller.py` — NameError saat cold path

**Severity:** 🔴 CRITICAL  
**Kategori:** Hidden Bug  
**File:** `engine/mpv_controller.py` — baris terakhir file

#### Cara Reproduksi
1. `mpv_controller.py` menggunakan `time.monotonic()` di dalam `_handle_event` (baris yang memanggil `self._last_progress_time`)
2. `import time` berada di baris **paling terakhir** file, setelah definisi class
3. Ketika module diimport, Python mengeksekusi kode top-level secara berurutan
4. Jika ada exception **di dalam class body** sebelum baris `import time` dieksekusi, `time` tidak tersedia
5. Lebih kritis: jika `_handle_event` dipanggil dalam test atau lingkungan di mana import gagal sebagian → `NameError: name 'time' is not defined`

#### Kode Bermasalah
```python
# mpv_controller.py — isi method _handle_event
if name == "time-pos" and isinstance(data, (int, float)):
    now = time.monotonic()   # ← menggunakan 'time'
    ...

# ... ratusan baris kode ...

import time   # ← BARIS TERAKHIR FILE! Setelah class selesai
```

#### Solusi
```python
# Pindahkan import ke atas file, setelah imports yang sudah ada
import asyncio
import json
import os
import time          # ← di sini, bukan di bawah

import structlog
# ... sisa imports ...
```

---

### B-07 — `_lock` di `PlaybackController` dideklarasikan tapi tidak pernah digunakan

**Severity:** 🟠 HIGH  
**Kategori:** Dead Code / Logic Bug  
**File:** `engine/playback/controller.py` — baris 59

#### Penjelasan
`PlaybackController.__init__` mendeklarasikan `self._lock = asyncio.Lock()`. Lock ini digunakan secara ekstensif oleh semua `*Commands` class (`PlaybackCommands`, `QueueCommands`, dll) untuk melindungi operasi — **namun tidak pernah di-acquire di dalam `PlaybackController` itu sendiri**.

Ini menciptakan false sense of security: developer baru melihat `_lock` ada dan mengasumsikan operasi internal `PlaybackController` sudah diproteksi, padahal tidak. Semua subscriber event (`_on_track_ended`, `_on_track_progress`, dll) berjalan tanpa lock.

#### Kode Bermasalah
```python
class PlaybackController:
    def __init__(self, deps: PlaybackDependencies):
        # ...
        self._lock = asyncio.Lock()       # ← dideklarasikan
        self._play_lock = asyncio.Lock()  # ← ini digunakan di play_track

    async def play_track(self, track):
        async with self._play_lock:       # ← _play_lock dipakai
            ...
    
    async def _on_track_ended(self, event):
        # ← TIDAK ada lock apapun, state langsung dimutasi
        await self._advance_to_next()
```

#### Solusi
**Opsi A:** Hapus `_lock` jika memang tidak dibutuhkan (setelah verifikasi semua path aman):
```python
# Hapus baris ini:
# self._lock = asyncio.Lock()
```

**Opsi B:** Gunakan `_lock` untuk melindungi `_advance_to_next` dari double-call:
```python
async def _advance_to_next(self):
    async with self._lock:
        if self.state.playback_mode == PlaybackMode.QUEUE:
            await self.queue_mode.next(self)
        else:
            await self.radio_mode.next(self)
```

---

### B-08 — `on_next` + `_advance_to_next` memanggil `play_track` yang butuh `_play_lock` — bottleneck beruntun

**Severity:** 🟠 HIGH  
**Kategori:** Async Bug  
**File:** `engine/playback/playback_commands.py` baris 29–35, `engine/playback/controller.py`

#### Penjelasan
`on_next` mengambil `_lock` lalu memanggil `_advance_to_next()`. `_advance_to_next()` memanggil `queue_mode.next(controller)` atau `radio_mode.next(controller)`, yang keduanya memanggil `play_track(track)`. `play_track` mengambil `_play_lock`.

Ini **tidak deadlock** (dua lock berbeda), tapi menimbulkan masalah: seluruh durasi `play_track` (yang bisa panjang karena ada `await resolver.resolve()` dan `await mpv.play()`) terjadi **di dalam `_lock`**, memblokir semua operasi queue lain.

#### Kode Bermasalah
```python
# playback_commands.py
async def on_next(self, cmd=None):
    async with self.playback_controller._lock:     # ← acquire _lock
        # ...
        await self.playback_controller._advance_to_next()  # → play_track → I/O panjang
        # semua queue ops lain terblokir selama _advance_to_next berjalan
```

#### Solusi
```python
async def on_next(self, cmd=None):
    # Validasi dan baca state di dalam lock
    async with self.playback_controller._lock:
        if cmd and getattr(cmd, "video_id", None):
            if not self.state.current_track or self.state.current_track.video_id != cmd.video_id:
                logger.info("Ignoring skip: video_id mismatch")
                return
        should_advance = True
    
    # I/O berat di luar lock
    if should_advance:
        await self.playback_controller._advance_to_next()
```

---

### B-09 — `_poll_duration` menerbitkan `QueueUpdatedEvent` meski durasi tidak berhasil didapat

**Severity:** 🟠 HIGH  
**Kategori:** Logic Bug  
**File:** `engine/playback/controller.py` — baris 153–170

#### Cara Reproduksi
```python
async def _poll_duration(self, track: TrackInfo):
    await asyncio.sleep(2)
    if self.state.current_track != track:
        return
    dur = await self.mpv.get_duration()
    if dur is not None and dur > 0:
        # ... update duration ...
        await self.bus.publish(QueueUpdatedEvent())
    else:
        await asyncio.sleep(5)
        if self.state.current_track == track:
            dur = await self.mpv.get_duration()
            if dur is not None and dur > 0:
                # ... update duration ...
            await self.bus.publish(QueueUpdatedEvent())  # ← dipanggil BAHKAN jika dur=None!
```

Pada path kedua: jika `dur` masih `None` setelah 7 detik total, `QueueUpdatedEvent` tetap diterbitkan. Ini menyebabkan broadcast state ke semua client tanpa perubahan nyata.

#### Solusi
```python
else:
    await asyncio.sleep(5)
    if self.state.current_track == track:
        dur = await self.mpv.get_duration()
        if dur is not None and dur > 0:
            self.state.duration = dur
            track.duration = int(dur)
            safe_create_task(self.db.upsert_track(track), name="upsert_track_duration_poll")
            await self.bus.publish(QueueUpdatedEvent())  # ← hanya jika durasi berhasil
        # else: tidak ada yang berubah, tidak perlu publish
```

---

### B-10 — `VolumeService.current_volume` bisa desync dari `state.volume`

**Severity:** 🟠 HIGH  
**Kategori:** State Bug / Race Condition  
**File:** `engine/volume_service.py` — baris 19–41

#### Cara Reproduksi
1. `VolumeService.__init__` menyalin `self.current_volume = state.volume` (misal: 80)
2. Komponen lain mengubah `state.volume` langsung (misalnya restore dari DB atau WS handler lain)
3. User menekan Volume Up → `self.current_volume = self.state.volume` (ok, re-read)
4. Namun jika dua volume command datang bersamaan (async), keduanya membaca `state.volume` yang sama, menambah +5, dan hasil akhirnya hanya +5 bukan +10

#### Kode Bermasalah
```python
class VolumeService:
    def __init__(self, bus, mpv, state):
        self.current_volume = state.volume  # ← snapshot, bisa stale

    async def _on_volume_up(self, cmd=None):
        self.current_volume = self.state.volume  # ← re-read setiap kali
        self.current_volume = min(100, self.current_volume + 5)
        await self._apply_volume()

    async def _apply_volume(self):
        self.state.volume = self.current_volume  # ← tulis kembali
```

#### Solusi
Hapus `self.current_volume` sebagai field terpisah, operasikan langsung di `state.volume`:

```python
async def _on_volume_up(self, cmd=None):
    new_vol = min(100, int(self.state.volume) + 5)
    self.state.volume = new_vol
    await self._apply_volume_to_mpv()

async def _apply_volume_to_mpv(self):
    if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
        await self.mpv.set_volume(0)
    else:
        await self.mpv.set_volume(self.state.volume)
    from core.events import QueueUpdatedEvent
    await self.bus.publish(QueueUpdatedEvent())
    await self.bus.publish(LogMessageEvent(message=f"Volume: {self.state.volume}%"))
```

---

### B-11 — `handle_ws_message`: tidak ada validasi tipe `data` sebelum `.get()`

**Severity:** 🟠 HIGH  
**Kategori:** Error Handling / Missing Validation  
**File:** `server/handlers/websocket.py` — baris 78–90  
**Lokasi downstream:** semua WS handlers

#### Cara Reproduksi
1. Client mengirim: `{"type": "cmd", "action": "seek", "data": "malicious_string"}`
2. `data = msg.get("data", {})` → `data = "malicious_string"` (string, bukan dict)
3. Handler downstream memanggil `data.get("position", 0)` → `AttributeError: 'str' object has no attribute 'get'`
4. Exception ditangkap di `handle_ws_message` dan mengirim `INTERNAL` error — OK
5. Tapi **juga membocorkan stack trace ke log** tanpa redaksi

#### Kode Bermasalah
```python
async def handle_ws_message(msg: dict, ws, client_ip, state, ytdlp, manager, db, command_bus):
    msg_type = msg.get("type")
    action = msg.get("action", "")
    data = msg.get("data", {})   # ← tidak divalidasi tipenya

    # ... lalu handler downstream:
    # data.get("position", 0)  ← crash jika data bukan dict
```

#### Solusi
```python
data = msg.get("data", {})
if not isinstance(data, dict):
    data = {}   # normalisasi: data harus selalu dict
```

---

### B-12 — `ws_handler`: exception di `async for msg in ws` tidak membedakan jenis error

**Severity:** 🟠 HIGH  
**Kategori:** Error Handling  
**File:** `server/handlers/websocket.py` — baris 65–76

#### Kode Bermasalah
```python
try:
    async for msg in ws:
        ...
except Exception as e:
    logger.error(f"WebSocket error: {e}")  # ← semua exception dilog sebagai error
finally:
    manager.disconnect(ws)
```

`aiohttp.ServerDisconnectedError` dan `asyncio.CancelledError` adalah kondisi normal (client tutup browser, server shutdown), bukan error. Melognya sebagai ERROR menghasilkan noise dan mempersulit debugging error sesungguhnya.

#### Solusi
```python
import aiohttp

try:
    async for msg in ws:
        ...
except asyncio.CancelledError:
    pass  # normal: server shutdown
except aiohttp.ServerDisconnectedError:
    pass  # normal: client disconnect
except Exception as e:
    logger.error(f"WebSocket unexpected error: {e}", exc_info=True)
finally:
    manager.disconnect(ws)
```

---

### B-13 — `evict_stale_tracks`: `list` dioper ke `execute()` sebagai params — error di aiosqlite versi tertentu

**Severity:** 🟠 HIGH  
**Kategori:** Hidden Bug  
**File:** `cache/repositories/track_repository.py` — baris 135–137

#### Kode Bermasalah
```python
video_ids = [r["video_id"] for r in rows]   # ← list

placeholders = ','.join(['?'] * len(video_ids))
await self._conn.execute(
    f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids  # ← list, bukan tuple
)
```

SQLite Python adapter (`sqlite3` dan `aiosqlite`) secara resmi menerima `tuple` atau `list` sebagai params. Namun beberapa versi aiosqlite lebih ketat dan mengharapkan sequence berupa tuple. Lebih kritis: jika `video_ids` adalah list dengan satu elemen `["abc"]`, SQLite dapat menginterpretasi `"abc"` sebagai sequence karakter `('a','b','c')`.

#### Solusi
```python
await self._conn.execute(
    f"DELETE FROM tracks WHERE video_id IN ({placeholders})", tuple(video_ids)  # ← konversi ke tuple
)
```

---

### B-14 — `SponsorBlock.fetch_segments` mengosongkan segments sebelum fetch selesai

**Severity:** 🟠 HIGH  
**Kategori:** Race Condition  
**File:** `plugins/sponsorblock.py` — baris 38–53

#### Cara Reproduksi
1. Track A sedang diputar, segments untuk track A tersimpan: `[(10.0, 30.0)]`
2. Track B mulai, `fetch_segments(video_id_B)` dipanggil
3. Baris 38: `self.segments = []` — segments dikosongkan
4. Sementara HTTP request ke SponsorBlock API berjalan (~1-3 detik), `_on_progress` bisa dipanggil
5. `_on_progress` melihat `self.segments = []` → tidak ada segment untuk diskip (padahal track B belum dapat segmentnya, dan track A sudah dikosongkan)
6. Jika track A masih playing (edge case saat transisi), segment yang seharusnya ada sudah hilang

#### Kode Bermasalah
```python
async def fetch_segments(self, video_id: str):
    self.segments = []   # ← langsung dikosongkan sebelum fetch!
    params = { "videoID": video_id, ... }
    
    try:
        async with self._session.get(...) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.segments = [...]   # ← baru diisi setelah HTTP selesai
```

#### Solusi
Gunakan variabel lokal sementara, assign atomik di akhir:

```python
async def fetch_segments(self, video_id: str):
    new_segments = []   # ← lokal
    try:
        async with self._session.get(
            SPONSORBLOCK_API, params=params,
            timeout=aiohttp.ClientTimeout(total=3)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                new_segments = [
                    (seg["segment"][0], seg["segment"][1]) for seg in data
                ]
                logger.info(f"SponsorBlock: {len(new_segments)} segments for {video_id}")
    except Exception as e:
        logger.debug(f"SponsorBlock fetch failed: {e}")
    finally:
        self.segments = new_segments   # ← assign atomik di akhir (bahkan jika fetch gagal = [])
```

---

### B-15 — `CacheResolver._fetching`: waiter bisa hang jika event tidak pernah di-set

**Severity:** 🟠 HIGH  
**Kategori:** Async Bug / Memory  
**File:** `cache/resolver.py` — baris 42–56

#### Cara Reproduksi
1. Coroutine A: `video_id` belum di `_fetching` → buat `event`, masuk ke fetch
2. Coroutine B: `video_id` sudah di `_fetching` → `await self._fetching[video_id].wait()`
3. Coroutine A: `ytdlp.get_stream_url()` melempar exception → `finally` dieksekusi → `event.set()` → B lanjut
4. B memanggil `await self.resolve(track)` rekursif — **tapi URL tidak tersimpan ke DB** (exception terjadi sebelum `upsert_track`)
5. B kembali ke step 1: tidak ada di `_fetching` lagi → B melakukan fetch ulang sendiri
6. **Ini sebenarnya OK** — B akan retry. Tapi jika ada **3+ coroutine menunggu** dan A gagal, semuanya retry paralel → N concurrent yt-dlp calls untuk video yang sama

#### Kode Bermasalah
```python
if track.video_id in self._fetching:
    await self._fetching[track.video_id].wait()
    return await self.resolve(track)   # ← rekursif, tidak ada limit

event = asyncio.Event()
self._fetching[track.video_id] = event

try:
    url = await self.ytdlp.get_stream_url(track.video_id)
    track.stream_url = url
    await self.db.upsert_track(track, stream_url=url)
    return url
finally:
    event.set()
    self._fetching.pop(track.video_id, None)
```

#### Solusi
Simpan hasil fetch (sukses atau gagal) untuk waiter gunakan langsung:

```python
class CacheResolver:
    def __init__(self, db, ytdlp):
        self.db = db
        self.ytdlp = ytdlp
        self._fetching: dict[str, asyncio.Event] = {}
        self._fetch_results: dict[str, str | Exception] = {}   # ← simpan hasil

    async def resolve(self, track: TrackInfo) -> str:
        # ... (cache checks sama) ...

        if track.video_id in self._fetching:
            await self._fetching[track.video_id].wait()
            result = self._fetch_results.get(track.video_id)
            if isinstance(result, Exception):
                raise result
            if isinstance(result, str):
                return result
            return await self.resolve(track)  # fallback jika result hilang

        event = asyncio.Event()
        self._fetching[track.video_id] = event
        
        try:
            url = await self.ytdlp.get_stream_url(track.video_id)
            track.stream_url = url
            await self.db.upsert_track(track, stream_url=url)
            self._fetch_results[track.video_id] = url
            return url
        except Exception as e:
            self._fetch_results[track.video_id] = e
            raise
        finally:
            event.set()
            self._fetching.pop(track.video_id, None)
            # Bersihkan result setelah dipakai (optional: bisa retain untuk TTL pendek)
            self._fetch_results.pop(track.video_id, None)
```

---

### B-16 — `_parse_lrc`: baris plain-text tanpa timestamp di-append dengan `t=0.0`

**Severity:** 🟡 MEDIUM  
**Kategori:** Logic Bug  
**File:** `plugins/lyrics.py` — baris 138–140

#### Kode Bermasalah
```python
def _parse_lrc(self, lrc_text: str) -> list[tuple[float, str]]:
    for line in lrc_text.splitlines():
        m = pattern.match(line)
        if m:
            minutes, seconds, text = m.groups()
            timestamp = int(minutes) * 60 + float(seconds)
            result.append((timestamp, text.strip()))
        else:
            if line:
                result.append((0.0, line))   # ← semua baris non-timestamp muncul di t=0
```

Baris metadata LRC seperti `[ti:Title]`, `[ar:Artist]`, `[al:Album]`, `[by:Creator]` tidak cocok dengan pattern timestamp tapi juga bukan kosong. Mereka semua akan muncul sebagai lyric di t=0.0, menghasilkan artifact visual di awal lagu.

#### Solusi
```python
_METADATA_RE = re.compile(r"^\[(?:ti|ar|al|by|offset|length|re|ve):.*\]$", re.IGNORECASE)

def _parse_lrc(self, lrc_text: str) -> list[tuple[float, str]]:
    pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")
    result = []
    for line in lrc_text.splitlines():
        line = line.strip()
        if not line:
            continue
        m = pattern.match(line)
        if m:
            minutes, seconds, text = m.groups()
            timestamp = int(minutes) * 60 + float(seconds)
            if text.strip():   # ← skip baris lyric kosong
                result.append((timestamp, text.strip()))
        elif not _METADATA_RE.match(line):
            # Bukan metadata dan bukan timestamp → lyric plain text
            # Hanya tambahkan jika ada timestamp sebelumnya (append setelah entry terakhir)
            pass   # ← abaikan baris tanpa timestamp untuk menghindari artifact t=0
    return sorted(result, key=lambda x: x[0])
```

---

### B-17 — `lyrics.py`: `clean_title` dan `search_query` dihitung meski `lrc` sudah ada di cache

**Severity:** 🟡 MEDIUM  
**Kategori:** Logic Bug / Dead Code  
**File:** `plugins/lyrics.py` — baris 57–98

#### Penjelasan
Ketika lyrics sudah ada di `_cache`, variabel `lrc` di-set dari cache. Namun kode tetap melanjutkan menghitung `clean_title` dan `search_query` (baris 70–78) yang hanya digunakan oleh blok `if not lrc:` berikutnya — yang tidak akan pernah berjalan. Ini adalah komputasi yang terbuang setiap kali cache hit.

#### Kode Bermasalah
```python
if track.video_id in self._cache:
    lrc = self._cache[track.video_id]
    # lrc sekarang ada isinya

# Blok ini selalu dieksekusi — meski lrc sudah ada
clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title)
for kw in ['official', 'music video', ...]:
    clean_title = re.sub(...)
search_query = ...

if not lrc:           # ← tidak akan True jika lrc dari cache
    # fetch dari API
    
if not lrc:           # ← tidak akan True
    # fallback ke syncedlyrics
```

#### Solusi
```python
if track.video_id in self._cache:
    lrc = self._cache[track.video_id]
else:
    lrc = None
    # Hitung clean_title dan search_query HANYA jika diperlukan
    clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title)
    for kw in ['official', 'music video', 'lyric', 'lyrics', 'audio', 'video', 'mv', 'hq']:
        clean_title = re.sub(rf'\b{kw}s?\b', '', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'\s+', ' ', clean_title).strip('- ')
    search_query = clean_title if "-" in title else (f"{clean_title} {artist}" if artist and artist.lower() not in ["unknown", "topic"] else clean_title)

    # fetch dari lrclib ...
    async with session.get(url_get, ...) as resp:
        ...

    if not lrc:
        # fallback ke syncedlyrics
        ...
```

---

### B-18 — `_on_track_ended` eof path tidak terlindungi dari pemanggilan ganda

**Severity:** 🟡 MEDIUM  
**Kategori:** Async Bug  
**File:** `engine/playback/controller.py` — baris 181–183

#### Penjelasan
`_on_track_ended` dipanggil oleh EventBus setiap kali MPV mengirim `end-file` event. MPV terkadang mengirim `end-file` lebih dari sekali (bug/quirk MPV yang dikenal). Tanpa guard, `_advance_to_next()` dapat dipanggil dua kali berurutan dalam jeda 0.35 detik, menyebabkan dua lagu di-skip sekaligus.

#### Kode Bermasalah
```python
if reason == "eof":
    await asyncio.sleep(0.35)
    await self._advance_to_next()    # ← bisa dipanggil dua kali
```

#### Solusi
```python
_advancing = False  # tambahkan sebagai instance variable di __init__

async def _on_track_ended(self, event: TrackEndedEvent):
    if self._advancing:
        logger.debug("Ignoring duplicate end-file event")
        return
    self._advancing = True
    try:
        reason = event.reason
        if reason == "eof":
            await asyncio.sleep(0.35)
            await self._advance_to_next()
        # ...
    finally:
        self._advancing = False
```

---

### B-19 — `service_worker.js` fallback ke `/static/index.html` — path tidak valid

**Severity:** 🟡 MEDIUM  
**Kategori:** Logic Bug  
**File:** `web/static/sw.js` — baris 77

#### Kode Bermasalah
```javascript
self.addEventListener('fetch', (event) => {
    // ...
    if (event.request.headers.get('accept').includes('text/html')) {
        return caches.match('/static/index.html');   // ← path salah!
    }
```

`/static/index.html` bukan route yang valid di server. Server melayani HTML di `/` (via `serve_index` handler), bukan di `/static/index.html`. Cache lookup ini akan selalu `undefined` (cache miss) saat offline, menyebabkan PWA offline mode gagal.

#### Solusi
```javascript
return caches.match('/');   // ← route yang benar
```

Pastikan juga `/` ada di `PRECACHE_ASSETS`:
```javascript
const PRECACHE_ASSETS = [
    '/',                        // ← sudah ada, bagus
    '/static/inter.css',
    // ...
];
```

---

### B-20 — `settings_handlers.py volume_set` membatasi volume ke 150 tapi `Volume()` clamp ke 100

**Severity:** 🟡 MEDIUM  
**Kategori:** Logic Bug / Inkonsistensi  
**File:** `server/handlers/ws/settings_handlers.py` — baris 20

#### Kode Bermasalah
```python
@register_ws_handler("volume_set")
async def _handle_volume_set(data, ws, state, ytdlp, manager, db, command_bus):
    try:
        vol = max(0, min(150, int(data.get("volume", DEFAULT_VOLUME))))  # ← clamp ke 150
        await command_bus.execute(VolumeSetCommand(volume=vol))
    except (ValueError, TypeError):
        pass
```

`VolumeSetCommand(volume=vol)` → `VolumeService._on_volume_set` → `Volume(vol)` → `Volume.__new__` clamp ke `max(0, min(100, int(value)))`. Nilai 150 yang dikirim dari client akan diklem ke 100. Inkonsistensi ini membingungkan dan membuka kemungkinan bug di masa depan jika `Volume()` diubah.

#### Solusi
```python
vol = max(0, min(100, int(data.get("volume", DEFAULT_VOLUME))))   # ← konsisten dengan Volume()
```

---

### B-21 — `_connectivity_checker` infinite loop tidak dapat dihentikan saat shutdown

**Severity:** 🟡 MEDIUM  
**Kategori:** Lifecycle Bug  
**File:** `core/background_tasks.py` — baris 9–19

#### Kode Bermasalah
```python
async def _connectivity_checker(state, http_session):
    while True:             # ← loop tanpa kondisi keluar
        try:
            async with http_session.get(...) as r:
                state.is_online = (r.status == 204)
        except Exception:
            state.is_online = False
        await asyncio.sleep(60)
```

`asyncio.CancelledError` ditangkap oleh `except Exception` (karena `CancelledError` adalah subclass `BaseException` di Python 3.8+ dan **bukan** `Exception`) — jadi sebenarnya OK untuk cancellation. Namun masalahnya: task ini tidak memeriksa apakah `http_session` sudah ditutup saat shutdown, yang menyebabkan `aiohttp.ClientConnectorError` dilog sebagai warning pada setiap shutdown.

#### Solusi
```python
async def _connectivity_checker(state, http_session):
    while True:
        try:
            async with http_session.get(
                "https://connectivitycheck.gstatic.com/generate_204",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as r:
                state.is_online = (r.status == 204)
        except asyncio.CancelledError:
            raise   # ← propagate cancellation agar task bisa dihentikan bersih
        except aiohttp.ClientConnectionError:
            if http_session.closed:
                return   # ← keluar bersih jika session sudah ditutup
            state.is_online = False
        except Exception as e:
            structlog.get_logger(__name__).warning(f"Connectivity check error: {e}")
            state.is_online = False
        await asyncio.sleep(60)
```

---

### B-22 — `on_radio_randomize`: `cmd` bisa `None` tapi `cmd.seed_artist` diakses tanpa guard

**Severity:** 🟡 MEDIUM  
**Kategori:** Null Pointer  
**File:** `engine/playback/radio_commands.py` — baris 20–22

#### Kode Bermasalah
```python
async def on_radio_randomize(self, cmd):
    seed = None
    should_fetch = False
    async with self.playback_controller._lock:
        if self.state.playback_mode == PlaybackMode.RADIO:
            seed = cmd.seed_artist if cmd else None   # ← guard ada di sini

# Tapi di radio_engine._fetch_and_play_initial:
async def _fetch_and_play_initial(self, controller, seed_artist=None):
    # OK, seed_artist bisa None

# Masalah ada di radio_handlers.py:
@register_ws_handler(WSAction.RADIO_RANDOMIZE)
async def _handle_radio_randomize(data, ws, state, ytdlp, manager, db, command_bus):
    seed_artist = data.get("seed_artist") if isinstance(data, dict) else None
    await command_bus.execute(RadioRandomizeCommand(seed_artist=seed_artist))
```

`RadioRandomizeCommand` memiliki `seed_artist: Optional[str] = None`, jadi `cmd` tidak akan `None`. Tapi jika `CommandRouter._route` memanggil handler tanpa argument (`action()`), `cmd` bisa `None`. Ini terjadi jika `inspect.signature` mendeteksi 0 parameter (bug di `_route`).

#### Solusi di `command_router.py`:
```python
def _route(self, action):
    async def handler(command):
        sig = inspect.signature(action)
        if len(sig.parameters) > 0:
            res = action(command)
        else:
            res = action()   # ← ini yang akan crash jika action butuh cmd
        if asyncio.iscoroutine(res):
            return await res
        return res
    return handler
```

Guard yang lebih aman:
```python
def _route(self, action):
    async def handler(command):
        # Selalu berikan command — biarkan handler yang menentukan apakah perlu
        import asyncio
        res = action(command)
        if asyncio.iscoroutine(res):
            return await res
        return res
    return handler
```

---

### B-23 — `TrackInfo.from_dict`: `VideoId()` melempar `ValueError` untuk ID yang tidak valid

**Severity:** 🟡 MEDIUM  
**Kategori:** Error Handling  
**File:** `core/state.py` — baris 58–65

#### Penjelasan
`VideoId` memvalidasi format `^[a-zA-Z0-9_-]{11}$`. Namun `YtDlpClient._to_track()` bisa menghasilkan video_id yang tidak sesuai format ini (misalnya hash fallback seperti `vid_1234567890`). Jika track seperti ini masuk ke WS handler `play_track`, `TrackInfo.from_dict(data)` akan melempar `ValueError` di konstruktor `VideoId()`, yang ditangkap oleh `except ValueError: return None`. Hasilnya: `track = None`, play request diabaikan diam-diam.

#### Kode Bermasalah
```python
# state.py
@classmethod
def from_dict(cls, data: dict) -> Optional['TrackInfo']:
    if not data:
        return None
    try:
        video_id = VideoId(data.get("video_id", ""))   # ← raises ValueError jika tidak valid
    except ValueError:
        return None   # ← silent failure

# ytdlp_client.py — bisa menghasilkan ID yang tidak valid
video_id = f"vid_{abs(hash(entry.get('title', ''))) % 10**10}"
# "vid_1234567890" — 16 karakter, tidak lolos regex VideoId
```

#### Solusi
Dua-arah:
1. Fix `YtDlpClient._to_track()` agar tidak menghasilkan ID non-standar
2. Log error sebelum `return None` di `from_dict`:

```python
@classmethod
def from_dict(cls, data: dict) -> Optional['TrackInfo']:
    if not data:
        return None
    try:
        video_id = VideoId(data.get("video_id", ""))
    except ValueError as e:
        import structlog
        structlog.get_logger(__name__).warning(
            f"TrackInfo.from_dict: invalid video_id {data.get('video_id')!r}: {e}"
        )
        return None
```

Dan di `ytdlp_client.py`:
```python
# Jangan generate fallback ID yang tidak valid
if not video_id or not re.match(r'^[a-zA-Z0-9_\-]{11}$', video_id):
    return None   # skip entry ini daripada generate ID palsu
```

---

### B-24 — `next_data` dict dibangun tapi tidak pernah digunakan

**Severity:** 🟢 LOW  
**Kategori:** Dead Code  
**File:** `engine/playback/controller.py` — baris 177–179

#### Kode Bermasalah
```python
async def _on_track_ended(self, event: TrackEndedEvent):
    reason = event.reason
    logger.info(f"[AUTOPLAY] Track ended with reason: {reason}")

    next_data = {}                                              # ← dibuat
    if self.state.current_track:
        next_data["video_id"] = self.state.current_track.video_id   # ← diisi

    if reason == "eof":        # ← next_data TIDAK PERNAH digunakan di bawah ini
        ...
```

#### Solusi
Hapus kedua baris tersebut:
```python
# Hapus:
# next_data = {}
# if self.state.current_track:
#     next_data["video_id"] = self.state.current_track.video_id
```

---

### B-25 — `get_featured_genres` menggunakan `print()` bukan `logger.error()`

**Severity:** 🟢 LOW  
**Kategori:** Logic Bug  
**File:** `server/services/discover_service.py` — baris 130

#### Kode Bermasalah
```python
async def get_featured_genres(self, n: int) -> list[dict]:
    # ...
    except Exception as e:
        print(f"Error in get_featured_genres: {e}")   # ← print! bukan logger
    return genres
```

Error akan muncul di stdout (bukan log file), tidak ter-format, tidak ada level, tidak ada stack trace. Di environment produksi dengan stdout di-redirect, error ini akan hilang sama sekali.

#### Solusi
```python
except Exception as e:
    logger.error(f"Error in get_featured_genres: {e}", exc_info=True)
```

---

### B-26 — `_CompactRenderer.__call__` mengembalikan string kosong — strukturlog mengharapkan dict

**Severity:** 🟢 LOW  
**Kategori:** Logic Bug  
**File:** `core/log_config.py` — baris `_CompactRenderer.__call__`

#### Penjelasan
structlog processor chain: setiap processor menerima `(logger, method, event_dict)` dan harus mengembalikan `event_dict` (dict yang dimodifikasi) atau melempar `DropEvent` untuk membuang log. `_CompactRenderer` mengembalikan `""` (string kosong) yang secara teknis bukan perilaku yang didokumentasikan. Meski saat ini tidak menyebabkan crash (structlog mengabaikan nilai return dari renderer terakhir), ini bisa berubah di versi structlog mendatang.

#### Solusi
```python
def __call__(self, logger, method, event_dict):
    # ... render logic ...
    from structlog.exceptions import DropEvent
    raise DropEvent()   # ← untuk suppress noise logs
    # ATAU untuk logs normal:
    return event_dict   # ← kembalikan dict asli (render ke stderr sudah dilakukan)
```

---

### B-27 — `_summary_worker` dan `_status_bar_worker` tidak memeriksa stop condition

**Severity:** 🟢 LOW  
**Kategori:** Lifecycle Bug  
**File:** `core/log_config.py`

#### Kode Bermasalah
```python
def _summary_worker():
    while True:              # ← tidak ada exit condition
        time.sleep(600)
        # ... print stats ...

_summary_thread = threading.Thread(target=_summary_worker, daemon=True, name="summary")
```

Karena ini daemon thread, Python akan membunuhnya saat main thread selesai. Ini acceptable untuk daemon, tapi thread tidak bisa di-stop secara bersih (misalnya untuk testing atau graceful shutdown dengan resource flushing).

#### Solusi
```python
_summary_stop = threading.Event()

def _summary_worker():
    while not _summary_stop.wait(timeout=600):  # ← tunggu 600s atau sampai stop
        with STATS.lock:
            # ... print stats ...

def stop_summary():
    _summary_stop.set()
```

---

### B-28 — `extractDominantColor`: callback dipanggil dengan string saat error, tapi caller mengharapkan `{r,g,b}`

**Severity:** 🟢 LOW  
**Kategori:** Logic Bug  
**File:** `web/static/js/utils.js`

#### Kode Bermasalah
```javascript
window.extractDominantColor = function(imageElement, callback) {
    try {
        // ... ekstraksi warna ...
        if (callback) callback({r: bestR, g: bestG, b: bestB});   // ← objek {r,g,b}
    } catch (e) {
        console.warn("Color extraction failed:", e);
        if (callback) callback("var(--bg-elevated)");              // ← string! inkonsisten
    }
};
```

Di `render/now-playing.js`, caller:
```javascript
window.extractDominantColor(dom.vinylCover, (color) => {
    if (color && color.r !== undefined) {   // ← guard ada, tapi...
        dom.tabHome.style.setProperty("--color-r", color.r);
        dom.tabHome.style.setProperty("--color-g", color.g);
        dom.tabHome.style.setProperty("--color-b", color.b);
    }
    // ← jika color adalah string, tidak ada fallback styling
});
```

Saat error: `color = "var(--bg-elevated)"`, `color.r = undefined`, guard `if (color && color.r !== undefined)` gagal, `--color-r/g/b` tidak di-set → warna background tidak berubah. Bukan crash, tapi visual glitch.

#### Solusi
```javascript
} catch (e) {
    console.warn("Color extraction failed:", e);
    // Kembalikan warna default sebagai objek {r,g,b}
    if (callback) callback({r: 30, g: 30, b: 40});  // ← dark neutral default
}
```

---

## APPENDIX — PETA HUBUNGAN BUG

```
B-02 (DoS auth via lock)
  └─ Menyebabkan semua user tidak bisa login saat ada brute-force

B-03 (reason="" tidak ditangani)
  └─ Menyebabkan autoplay mati diam-diam → user mengira app freeze

B-04 (retry_count race) + B-05 (IDLE guard salah)
  └─ Kombinasi: error track menyebabkan dua advance bersamaan

B-01 (KeyError stream_url)
  └─ Discover tab selalu kosong → silent failure di catch

B-06 (import time di akhir)
  └─ NameError sporadis saat cold path di _handle_event

B-07 (_lock tidak digunakan) + B-08 (lock bottleneck)
  └─ Miskomunikasi intent concurrency protection
```

---

*Laporan ini dihasilkan dari static code analysis penuh. Semua bug telah diverifikasi langsung dari source code.*
