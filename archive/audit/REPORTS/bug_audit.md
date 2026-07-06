# Bug Audit — ytgui (bagas.fm)

Ruang lingkup: seluruh source code non-markdown (Python backend, JS frontend). Direktori `.backup_patchlog/` diabaikan sesuai instruksi (hanya dipakai sebagai referensi historis, bukan target bug).

Ditemukan **10 temuan**, diurutkan dari paling kritis.

---

## BUG-01 — Deadlock: `play_track` bisa mengunci dirinya sendiri saat retry gagal

**Severity:** 🔴 Critical (Lifecycle Bug / Async Bug)

**Lokasi:** `engine/playback/controller.py` — method `play_track()` (blok `except Exception` di dalam `async with self._play_lock:`)

**Deskripsi:**
`play_track()` membungkus seluruh isinya (termasuk logic retry) dengan `async with self._play_lock:`. Ketika `play_track` gagal (exception saat load/play) dan retry count belum mencapai 3, kode melakukan:

```python
if self.state.current_track == track:
    await self._advance_to_next()
```

`_advance_to_next()` memanggil `queue_mode.next(controller)` atau `radio_mode.next(controller)`, yang **keduanya langsung memanggil `controller.play_track(track_berikutnya)` lagi** — padahal `self._play_lock` **masih dipegang oleh call stack yang sama** (`asyncio.Lock` tidak reentrant). Ini menyebabkan `await self._play_lock.acquire()` di pemanggilan `play_track` kedua menunggu selamanya, karena lock hanya bisa dilepas oleh `async with` yang sedang menunggunya sendiri.

**Cara reproduksi:**
1. Jalankan radio/queue mode.
2. Sebabkan `track_loader.load_track()` atau `mpv.play()` gagal (mis. video di-takedown / yt-dlp error / mpv belum connect) pada track pertama.
3. `play_track` masuk except block, retry_count < 3 → memanggil `_advance_to_next()` sambil masih memegang `_play_lock`.
4. `_advance_to_next()` → `queue_mode.next()`/`radio_mode.next()` → `play_track()` lagi → mencoba `async with self._play_lock` → **hang permanen**.
5. Seluruh playback (dan semua command lain yang butuh `_play_lock`, termasuk tombol next/prev pengguna) macet total; task asyncio tersebut tidak akan pernah selesai kecuali proses di-restart.

**Solusi:**
Jangan panggil `_advance_to_next()` dari dalam blok yang masih memegang `self._play_lock`. Lepaskan lock dahulu (keluar dari `async with`) sebelum retry, misalnya dengan menjadwalkan retry sebagai task terpisah, atau memindahkan logic retry ke luar `async with self._play_lock`.

**Kode perbaikan:**
```python
async def play_track(self, track: TrackInfo):
    should_retry = False
    async with self._play_lock:
        if self.state.current_track:
            self.state.history.append(self.state.current_track)

        self.state.current_track = track
        self.state.status = PlayerStatus.LOADING
        self.state.position = 0.0
        self.state.duration = float(track.duration)
        self.state.lyrics_lines = []
        self.state.lyrics_index = 0

        try:
            uri = await self.track_loader.load_track(track)
            await self.mpv.play(uri)

            if getattr(self.state, "audio_output", AudioOutput.DEVICE) == AudioOutput.BROWSER:
                await self.mpv.set_volume(0)
                await self.bus.publish(LogMessageEvent(message="Audio output is browser, mpv silent (volume=0)."))
            else:
                await self.mpv.set_volume(self.state.volume)

            await self.mpv.resume()

            self.state.status = PlayerStatus.PLAYING
            self._retry_count = 0
            _LOG_STATS.is_playing = True
            _LOG_STATS.current_track = track.title[:50] if track and track.title else '—'
            _LOG_STATS.inc('songs_played')
            await self.bus.publish(TrackStartedEvent(track=track))

            if self.state.duration == 0:
                safe_create_task(self._poll_duration(track), name="poll_duration")

        except Exception as e:
            logger.error(f"Failed to play track {track.title}: {e}", exc_info=True)
            self.state.status = PlayerStatus.ERROR
            self.state.error_msg = f"Error: {e}"
            await self.bus.publish(LogMessageEvent(message=f"Gagal memutar lagu: {track.title} | {type(e).__name__}: {str(e)}"))

            self._retry_count += 1
            if self._retry_count >= 3:
                await self.bus.publish(LogMessageEvent(message="Terlalu banyak kegagalan beruntun. Pemutaran dihentikan."))
                self._retry_count = 0
            else:
                should_retry = True  # tandai saja, JANGAN panggil play_track lagi di sini

    # Retry dilakukan SETELAH _play_lock dilepas
    if should_retry:
        backoff = 2 ** self._retry_count
        await asyncio.sleep(backoff)
        if self.state.current_track == track:
            await self._advance_to_next()
```

---

## BUG-02 — Race Condition: TOCTOU pada `_download_lock` di `DownloadManager`

**Severity:** 🟠 High (Race Condition)

**Lokasi:** `engine/download_manager.py` — `_on_download()`

**Deskripsi:**
```python
if self._download_lock.locked():
    await self.bus.publish(LogMessageEvent(message="Download sedang berjalan, tunggu selesai."))
    return
safe_create_task(self._do_download(target), name=f"download_{target.video_id}")
```
`self._download_lock.locked()` dicek, tapi lock baru benar-benar di-*acquire* di dalam `_do_download()` yang dijadwalkan lewat `safe_create_task` (event loop belum tentu langsung menjalankannya). Jika `CMD_DOWNLOAD` di-trigger dua kali dengan sangat cepat (mis. double-tap tombol download di UI), kedua panggilan `_on_download` bisa sama-sama melihat `locked() == False` sebelum task pertama sempat jalan, sehingga dua task download dibuat.

**Cara reproduksi:**
1. Klik tombol download dua kali berturut-turut dalam waktu < 1 event-loop-tick.
2. Kedua `_on_download()` call melihat `_download_lock.locked() == False`.
3. Dua `_do_download()` task dijadwalkan; salah satunya baru mengantre di lock setelah task lain jalan duluan — hasil: dua proses `yt-dlp` download berjalan/mengantre untuk track yang sama, boros resource dan progress bar bisa "flicker" karena dua sumber `download_progress` berbeda menimpa satu sama lain.

**Solusi:**
Gunakan flag/set video_id yang sedang didownload, dicek dan di-set secara atomik sebelum menjadwalkan task, bukan hanya `lock.locked()`.

**Kode perbaikan:**
```python
def __init__(self, bus, state, ytdlp):
    self.bus = bus
    self.state = state
    self.ytdlp = ytdlp
    self._download_lock = asyncio.Lock()
    self._downloading_ids: set[str] = set()   # tambahan
    command_bus.register(CMD_DOWNLOAD, self._on_download)

async def _on_download(self, track: TrackInfo | None = None):
    target = track or self.state.current_track
    if not target:
        await self.bus.publish(LogMessageEvent(message="Tidak ada lagu yang dipilih untuk di-download"))
        return
    if target.local_path:
        await self.bus.publish(LogMessageEvent(message="Lagu sudah tersimpan lokal"))
        return
    if target.video_id in self._downloading_ids:
        await self.bus.publish(LogMessageEvent(message="Download sedang berjalan, tunggu selesai."))
        return

    self._downloading_ids.add(target.video_id)  # ditandai SEBELUM menjadwalkan task
    safe_create_task(self._do_download(target), name=f"download_{target.video_id}")

async def _do_download(self, track: TrackInfo):
    async with self._download_lock:
        try:
            ...
        finally:
            self._downloading_ids.discard(track.video_id)
```

---

## BUG-03 — Error Handling: State tidak konsisten jika `mpv.pause()` gagal saat `_on_stop`

**Severity:** 🟠 High (Error Handling / State Bug)

**Lokasi:** `engine/playback/controller.py` — `_on_stop()`

**Deskripsi:**
```python
async def _on_stop(self, _data=None):
    self._retry_count = 0
    await self.mpv.pause()          # <- jika exception di sini...
    self.state.status = PlayerStatus.IDLE
    _LOG_STATS.is_playing = False
    self.state.current_track = None
    self.state.queue.clear()
    self.state.radio_queue.clear()
    ...
```
Tidak ada try/except di sini. `command_bus.execute()` menangkap exception dan me-log-nya, tapi karena exception terjadi di tengah fungsi, **state tidak pernah dibersihkan** — `current_track`, `queue`, dan `status` tetap dalam kondisi sebelumnya meskipun user/sistem sudah menekan "Stop". UI akan menampilkan track/queue yang seharusnya sudah dihentikan.

**Cara reproduksi:**
1. Putuskan koneksi mpv (mis. matikan proses mpv manual atau socket error) tapi `is_connected` masih `True` sesaat.
2. Trigger `CMD_STOP` (tombol Stop di UI).
3. `mpv.pause()` melempar exception (mis. `OSError` dari `_writer.write`) sebelum sempat ditangani internal oleh `_command`/`_send_request` (yang sebenarnya sudah menangkap `OSError`, tapi bug lain di layer bawah tetap bisa lolos, misalnya `AttributeError` bila `_writer` None) → seluruh baris setelah `await self.mpv.pause()` tidak dieksekusi.
4. Status pemutar tetap "PLAYING/ERROR", track & queue tidak ter-clear, padahal user mengira sudah stop.

**Solusi:**
Bungkus efek samping eksternal (`mpv.pause()`) dengan try/except terpisah agar state lokal selalu bersih terlepas dari hasil operasi eksternal.

**Kode perbaikan:**
```python
async def _on_stop(self, _data=None):
    self._retry_count = 0
    try:
        await self.mpv.pause()
    except Exception as e:
        logger.warning(f"mpv.pause() gagal saat stop: {e}")

    self.state.status = PlayerStatus.IDLE
    _LOG_STATS.is_playing = False
    self.state.current_track = None
    self.state.queue.clear()
    self.state.radio_queue.clear()
    self.state.position = 0.0
    self.state.lyrics_lines = []
    self.state.lyrics_index = 0
    await self.bus.publish(LogMessageEvent(message="Pemutaran dihentikan"))
    await self.bus.publish(QueueUpdatedEvent())
```

---

## BUG-04 — Dead Code / Unreachable Except: `except MpvConnectionError: raise` di `_do_connect`

**Severity:** 🟡 Medium (Dead Code / Unreachable Code)

**Lokasi:** `engine/mpv_controller.py` — `_do_connect()`, loop retry koneksi

**Deskripsi:**
```python
for attempt in range(10):
    try:
        ...
        self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)
        ...
        return
    except MpvConnectionError:
        raise
    except (ConnectionError, OSError, FileNotFoundError):
        await asyncio.sleep(0.5)
```
`asyncio.open_unix_connection` / `open_connection` tidak pernah melempar `MpvConnectionError` — exception itu didefinisikan sendiri di codebase dan hanya di-raise secara eksplisit **setelah** loop ini selesai (`raise MpvConnectionError(...)` di baris terakhir fungsi). Blok `except MpvConnectionError: raise` di dalam loop **tidak akan pernah tereksekusi** — ini dead code yang menyesatkan pembaca kode (seolah ada jalur di mana `MpvConnectionError` bisa muncul dari `open_unix_connection`).

**Cara reproduksi:** Statis — baca alur kode: tidak ada baris di dalam `try` yang bisa melempar `MpvConnectionError`, sehingga except clause tersebut secara logis unreachable.

**Solusi:** Hapus except clause yang tidak berguna, atau — jika maksudnya melindungi robustness di masa depan — beri komentar eksplisit. Yang lebih baik: hapus untuk kejelasan kode.

**Kode perbaikan:**
```python
for attempt in range(10):
    try:
        if os.name == 'nt':
            self._reader, self._writer = await asyncio.open_connection('127.0.0.1', int(self.tcp_port))
        else:
            self._reader, self._writer = await asyncio.open_unix_connection(self.socket_path)

        self.is_connected = True
        self._observer_task = safe_create_task(self._observe_events(), name="mpv_observer")
        if os.name != 'nt':
            try:
                import stat
                os.chmod(self.socket_path, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
        logger.info(f"Connected to mpv (attempt {attempt + 1})")
        return
    except (ConnectionError, OSError, FileNotFoundError):
        await asyncio.sleep(0.5)
raise MpvConnectionError(f"Cannot connect to mpv socket after 10 attempts (TCP: {os.environ.get('YT_PLAYER_MPV_PORT', 'N/A')}, Unix: {MPV_SOCKET})")
```

---

## BUG-05 — Missing Validation: `serve_stream` gagal saat spawn mpv, tapi tetap mencoba connect 10x (tanpa exit dini)

**Severity:** 🟡 Medium (Error Handling)

**Lokasi:** `engine/mpv_controller.py` — `_do_connect()`

**Deskripsi:**
```python
try:
    self._mpv_process = await asyncio.create_subprocess_exec(*cmd, ...)
    ...
except OSError as e:
    logger.error(f"Failed to spawn mpv process: {e}")
```
Jika `mpv` binary tidak ditemukan (`FileNotFoundError`, subclass `OSError`), error hanya di-log — kode **lanjut** ke loop percobaan koneksi socket 10x (masing-masing dengan `sleep(0.5)`), padahal socket **tidak mungkin pernah muncul** karena proses mpv tidak pernah start. Ini membuang ~5 detik startup time dan menghasilkan pesan error yang membingungkan (`Cannot connect to mpv socket after 10 attempts`) padahal akar masalahnya "mpv tidak terinstall/tidak ditemukan di PATH".

**Cara reproduksi:**
1. Jalankan aplikasi di environment tanpa `mpv` terinstall / tidak ada di PATH.
2. `_do_connect()` gagal spawn proses, tapi tetap lanjut retry koneksi socket 10x @0.5s (≈5 detik terbuang) sebelum akhirnya raise `MpvConnectionError` dengan pesan yang tidak menyebut akar masalah sebenarnya.

**Solusi:** Return/raise langsung begitu spawn gagal, dengan pesan error yang jelas.

**Kode perbaikan:**
```python
try:
    self._mpv_process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        stdin=asyncio.subprocess.DEVNULL
    )
except OSError as e:
    logger.error(f"Failed to spawn mpv process: {e}")
    raise MpvConnectionError(
        f"Tidak bisa menjalankan mpv (pastikan sudah terinstall dan ada di PATH): {e}"
    ) from e
```

---

## BUG-06 — Missing Validation: `video_id` dari WebSocket `play_track`/`queue_add` tidak divalidasi formatnya

**Severity:** 🟡 Medium (Missing Validation)

**Lokasi:** `server/serializers.py` — `dict_to_track()`, dipakai oleh `server/handlers/websocket.py` (`_handle_play_track`, `_handle_queue_add`, `_handle_download`, dll.)

**Deskripsi:**
`serve_stream` (HTTP handler) memvalidasi `video_id` dengan regex ketat `^[a-zA-Z0-9_-]{11}$`. Namun jalur WebSocket (`dict_to_track`) hanya mengecek `video_id` tidak kosong — tidak ada validasi panjang/format:
```python
def dict_to_track(data: dict) -> Optional[TrackInfo]:
    video_id = data.get("video_id")
    if not video_id:
        return None
    return TrackInfo(video_id=video_id, ...)
```
`video_id` yang sudah lolos autentikasi WS ini akan diteruskan ke `CacheResolver.resolve()` → `YtDlpClient.get_stream_url()` yang membangun URL `https://www.youtube.com/watch?v={video_id}` dan memanggil `yt-dlp`. Domain tetap tetap (bukan celah SSRF langsung), tapi `video_id` sembarangan (string sangat panjang, karakter aneh) tetap diteruskan mentah-mentah ke proses `yt-dlp` (dan dipakai sebagai bagian query string, filename cache lookup di DB), membuka celah DoS ringan (memaksa `yt-dlp` mencoba resolve URL invalid berulang kali dengan timeout 25 detik per percobaan) serta inkonsistensi validasi antar-layer.

**Cara reproduksi:**
1. Login sebagai admin WS.
2. Kirim `{"type":"cmd","action":"play_track","data":{"video_id":"'; DROP TABLE--<script>...(500 karakter)"}}`.
3. Server menerima, membuat `TrackInfo`, memanggil `get_stream_url()` yang menunggu hingga 25 detik (timeout) sebelum gagal — bisa diulang berkali-kali untuk membebani thread pool `yt-dlp` (`ThreadPoolExecutor(max_workers=4)`), menghabiskan slot worker dan menunda request video_id valid lainnya.

**Solusi:** Terapkan regex validasi yang sama seperti di `serve_stream` pada `dict_to_track`.

**Kode perbaikan:**
```python
import re

_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")

def dict_to_track(data: dict) -> Optional[TrackInfo]:
    video_id = data.get("video_id")
    if not video_id or not _VIDEO_ID_RE.match(video_id):
        return None
    return TrackInfo(
        video_id=video_id,
        title=data.get("title", "Unknown"),
        artist=data.get("artist", "Unknown"),
        duration=int(data.get("duration", 0)),
        thumbnail=data.get("thumbnail"),
        local_path=data.get("local_path"),
        stream_url=data.get("stream_url"),
        view_count=data.get("view_count"),
        is_favorite=int(data.get("is_favorite", False)),
    )
```

---

## BUG-07 — Logic Bug: `get_position()`/`get_duration()` tidak membedakan "nilai 0 valid" vs "gagal ambil property"

**Severity:** 🟢 Low (Logic Bug)

**Lokasi:** `engine/mpv_controller.py` — `get_position()`, `get_duration()`

**Deskripsi:**
```python
async def get_position(self) -> float:
    if not self.is_connected:
        return 0.0
    val = await self._get_property("time-pos")
    return val if val else 0.0
```
`_get_property` bisa mengembalikan `None` (gagal/timeout) **atau** `0.0` (posisi memang di detik ke-0, kondisi normal saat lagu baru mulai). Karena `0.0` falsy di Python, `val if val else 0.0` tidak membedakan dua kasus ini — secara kebetulan hasilnya sama (`0.0`) sehingga tidak menimbulkan bug nyata untuk kasus ini, tapi pola `if val else default` ini rawan menjadi bug nyata bila logic di sekitarnya berubah (mis. suatu saat kode ingin tahu apakah request timeout untuk retry). Termasuk kategori "hidden bug" — secara fungsional tidak error sekarang, tapi merupakan anti-pattern yang menyembunyikan kegagalan request sebagai data valid.

**Cara reproduksi:** Sulit direproduksi sebagai bug nyata saat ini (hasil kebetulan sama), tapi bisa diverifikasi via code review: tambahkan logging pada `_send_request` timeout — akan terlihat bahwa caller tidak pernah tahu apakah `0.0` berarti "posisi 0" atau "request gagal".

**Solusi:** Bedakan eksplisit antara `None` (gagal) dan `0` (valid).

**Kode perbaikan:**
```python
async def get_position(self) -> float:
    if not self.is_connected:
        return 0.0
    val = await self._get_property("time-pos")
    return float(val) if val is not None else 0.0

async def get_duration(self) -> float:
    if not self.is_connected:
        return 0.0
    val = await self._get_property("duration")
    return float(val) if val is not None else 0.0
```

---

## BUG-08 — State Bug: `_on_track_duration` tidak pernah update ulang jika `duration` awalnya salah/0 lalu mpv melaporkan ulang

**Severity:** 🟢 Low (State Bug)

**Lokasi:** `engine/playback/controller.py` — `_on_track_duration()`

**Deskripsi:**
```python
async def _on_track_duration(self, event: TrackDurationEvent):
    if event.duration and self.state.duration == 0:
        self.state.duration = event.duration
        ...
```
Kondisi `self.state.duration == 0` berarti begitu `state.duration` terisi sekali (misal nilai awal salah/sangat kecil karena metadata track tidak akurat, bukan 0 tapi keliru), event `TrackDurationEvent` berikutnya dari mpv (yang biasanya lebih akurat karena berasal dari observe_property langsung) **tidak akan pernah dipakai untuk mengoreksi** durasi yang sudah terlanjur tersimpan salah — karena syarat `== 0` sudah tidak terpenuhi.

**Cara reproduksi:**
1. Track punya metadata `duration` yang salah dari yt-dlp (mis. 1 detik, bukan 0).
2. `play_track()` set `self.state.duration = float(track.duration)` → `1.0` (bukan 0, sehingga cek berikutnya `== 0` gagal).
3. mpv mengirim event `duration` sebenarnya (mis. 240 detik) via `_on_track_duration` — diabaikan karena `state.duration` sudah `1.0`, bukan `0`.
4. UI menampilkan progress bar/durasi salah selama seluruh playback track tersebut.

**Solusi:** Gunakan flag eksplisit "durasi sudah dikonfirmasi dari mpv" alih-alih mengandalkan nilai `0` sebagai sentinel.

**Kode perbaikan:**
```python
# di play_track(): tambahkan flag
self.state.duration = float(track.duration)
self._duration_confirmed = False   # baru

async def _on_track_duration(self, event: TrackDurationEvent):
    if event.duration and not getattr(self, "_duration_confirmed", False):
        self.state.duration = event.duration
        self._duration_confirmed = True
        if self.state.current_track:
            self.state.current_track.duration = int(event.duration)
            safe_create_task(self.resolver.db.upsert_track(self.state.current_track), name="upsert_track_duration")
        await self.bus.publish(QueueUpdatedEvent())
```

---

## BUG-09 — Race Condition ringan: rate-limit list di-mutasi tanpa lock penuh saat `_prune_stale_ips` berjalan bersamaan permintaan lain

**Severity:** 🟢 Low (Race Condition)

**Lokasi:** `server/handlers/auth.py` — `handle_auth()` vs `server/middleware.py` — `check_rate_limit()`

**Deskripsi:**
Keduanya menggunakan `manager.rl_lock` untuk melindungi `manager.login_attempts` dan `manager.command_history` — ini sudah benar untuk operasi read-modify-write di masing-masing fungsi. Namun `handle_auth()` melakukan pola berikut **di luar transaksi atomik yang konsisten**:
```python
attempts = manager.login_attempts.get(client_ip, [])
attempts = [t for t in attempts if now - t < 300]
if not attempts:
    manager.login_attempts.pop(client_ip, None)
else:
    manager.login_attempts[client_ip] = attempts
...
# di jalur gagal login:
attempts.append(now)
manager.login_attempts[client_ip] = attempts
```
Ini sebenarnya masih di dalam `async with manager.rl_lock:` yang sama (lock dipegang dari awal `handle_auth`), jadi aman dari race antar-koneksi WS lain yang memanggil `handle_auth`/`check_rate_limit` — **tapi** karena `_prune_stale_ips` dan variabel `attempts` lokal dihitung ulang secara terpisah dua kali (sekali untuk cek limit, sekali untuk append), ada potensi duplikasi logic yang membuat penghapusan key (`pop`) lalu penambahan ulang (`[client_ip] = attempts`) pada dict yang sama dalam satu fungsi — tidak menyebabkan crash, tapi rawan salah kalau salah satu bagian diedit di masa depan tanpa memperhitungkan bagian lain (silent logic drift). Dikategorikan sebagai **hidden bug / code smell berisiko race di masa depan** bila refactor menghapus lock tanpa disadari dependensinya.

**Cara reproduksi:** Tidak menghasilkan bug fungsional saat ini (lock melindungi keseluruhan fungsi), tapi review kode menunjukkan duplikasi filter list yang seharusnya disatukan agar tidak "kelihatan" seperti unprotected race saat dibaca sekilas — risiko human error tinggi saat refactor.

**Solusi:** Sederhanakan agar hanya satu sumber kebenaran untuk `attempts` per request, jelas terlihat berada dalam satu critical section.

**Kode perbaikan:**
```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    async with manager.rl_lock:
        _prune_stale_ips(manager, now)

        token = data.get("token")
        if token and db and await db.verify_session(token):
            manager.authenticated_connections.add(ws)
            await ws.send_str(json.dumps({
                "type": "auth_status",
                "data": {"success": True, "token": token}
            }))
            return

        attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]

        if len(attempts) >= MAX_LOGIN_ATTEMPTS:
            manager.login_attempts[client_ip] = attempts
            await ws.send_str(json.dumps({
                "type": "auth_status",
                "data": {"success": False, "message": "Terlalu banyak percobaan login. Coba lagi dalam 5 menit."}
            }))
            return

        username = data.get("username", "")
        password = data.get("password", "")
        if secrets.compare_digest(username, ADMIN_USERNAME) and verify_password(password, ADMIN_PASSWORD):
            new_token = secrets.token_hex(16)
            if db:
                await db.create_session(new_token, int(now) + 86400)
            manager.authenticated_connections.add(ws)
            manager.login_attempts.pop(client_ip, None)
            await ws.send_str(json.dumps({
                "type": "auth_status",
                "data": {"success": True, "token": new_token}
            }))
        else:
            attempts.append(now)
            manager.login_attempts[client_ip] = attempts
            await ws.send_str(json.dumps({
                "type": "auth_status",
                "data": {"success": False, "message": "Username atau Password salah!"}
            }))
```

---

## BUG-10 — Dead Code: parameter `client_ip` tidak dipakai di banyak `_ws_handlers`

**Severity:** ⚪ Info (Dead Code)

**Lokasi:** `server/handlers/websocket.py` — hampir seluruh fungsi `@register_ws_handler(...)` (mis. `_handle_search`, `_handle_toggle_favorite`, `_handle_next`, dll.)

**Deskripsi:** Semua handler menerima parameter `client_ip` di signature-nya (`async def _handle_xxx(data, ws, client_ip, state, ytdlp, manager, db)`), tapi mayoritas tidak pernah menggunakannya sama sekali. Ini bukan bug fungsional, tapi indikasi dead parameter yang membingungkan pembaca kode dan berpotensi menyembunyikan kebutuhan rate-limit/audit-log per-IP yang sebenarnya seharusnya diterapkan di level handler individual (mis. untuk aksi sensitif seperti `download`, `delete_download`), bukan hanya rate-limit generik di `check_rate_limit`.

**Cara reproduksi:** Review statis — cukup `grep client_ip` di dalam body tiap handler untuk melihat mayoritas tidak memakainya.

**Solusi:** Jika memang tidak diperlukan, gunakan `_data=None`-style konvensi atau `**_` untuk parameter tak terpakai agar eksplisit; atau — lebih baik — manfaatkan `client_ip` untuk audit log pada aksi sensitif (download/delete_download).

**Kode perbaikan (contoh audit log pada aksi sensitif):**
```python
@register_ws_handler("download")
async def _handle_download(data, ws, client_ip, state, ytdlp, manager, db):
    track = dict_to_track(data) if data else None
    logger.info(f"Download diminta oleh {client_ip} untuk video_id={getattr(track, 'video_id', None)}")
    await command_bus.execute(CMD_DOWNLOAD, track)
```

---

## Ringkasan Prioritas Perbaikan

| # | Bug | Severity | Kategori |
|---|---|---|---|
| BUG-01 | Deadlock `play_track` saat retry gagal | 🔴 Critical | Lifecycle/Async |
| BUG-02 | TOCTOU race di `_download_lock` | 🟠 High | Race Condition |
| BUG-03 | State tidak konsisten jika `mpv.pause()` gagal di `_on_stop` | 🟠 High | Error Handling/State |
| BUG-04 | Except clause unreachable di `_do_connect` | 🟡 Medium | Dead Code |
| BUG-05 | Tidak exit dini saat spawn mpv gagal | 🟡 Medium | Error Handling |
| BUG-06 | `video_id` WS tidak divalidasi format | 🟡 Medium | Missing Validation |
| BUG-07 | `0` vs `None` ambigu di `get_position`/`get_duration` | 🟢 Low | Logic Bug |
| BUG-08 | Durasi track tidak bisa dikoreksi ulang | 🟢 Low | State Bug |
| BUG-09 | Duplikasi logic filter `attempts` rawan human-error | 🟢 Low | Race Condition (laten) |
| BUG-10 | Parameter `client_ip` dead di banyak handler | ⚪ Info | Dead Code |

**Rekomendasi urutan pengerjaan:** BUG-01 (deadlock, harus segera — ini bisa membekukan seluruh player) → BUG-03 → BUG-02 → BUG-05/BUG-06 → sisanya bersifat perbaikan kualitas kode.
