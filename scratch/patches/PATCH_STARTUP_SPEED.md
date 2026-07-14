# PATCH_STARTUP_SPEED.md

**Tujuan:** Startup <5 detik (desktop) / <10 detik (Termux) + pause response instan
**Baca dulu:** `AI_CONTEXT.md`
**Scope:** 4 file dimodifikasi, tidak ada perubahan API/arsitektur

---

## KONTEKS MASALAH

Startup sekarang 22–60+ detik karena 4 bottleneck bersusun:

1. `start.sh/bat` — 7× subprocess Python cold-start untuk dep check + artificial `sleep`
2. `import yt_dlp` di top-level `ytdlp_client.py` — modul besar, lambat di Termux
3. `mpv.connect()` berjalan **setelah** semua import selesai, padahal bisa paralel dengan DB init
4. `main.py` menjalankan `db.init()` → `mpv.connect()` secara **sequential**

Pause delay 1–3 detik karena `toggle_pause()` di-`await` sebelum response WS dikirim, padahal mpv tidak perlu dikonfirmasi dulu untuk update UI.

---

## TASK 1 — `start.sh`: Hapus artificial delays + gabung dep check

**File:** `start.sh`

**Cari dan ganti blok dep check:**

```bash
# SEBELUM (7× subprocess Python):
MISSING_DEPS=0
DEPS="aiohttp aiosqlite yt_dlp syncedlyrics structlog prometheus_client opentelemetry"
for dep in $DEPS; do
    if ! python -c "import $dep" &> /dev/null; then
        echo -e "    ${RED}[-]${RESET} Missing module: $dep"
        MISSING_DEPS=1
    fi
done
```

```bash
# SESUDAH (1× subprocess Python):
MISSING_DEPS=0
if ! python -c "import aiohttp, aiosqlite, yt_dlp, syncedlyrics, structlog, prometheus_client, opentelemetry" &> /dev/null 2>&1; then
    echo -e "    ${RED}[-]${RESET} Ada modul yang belum terinstall."
    echo -e "        Jalankan: ${BOLD}pip install -r requirements.txt${RESET}"
    MISSING_DEPS=1
fi
if [ $MISSING_DEPS -eq 0 ]; then
    echo -e "    ${GREEN}[+]${RESET} All Python dependencies are satisfied."
fi
```

**Cari dan hapus semua artificial delay:**

```bash
# HAPUS baris ini (ada 2 tempat di start.sh):
sleep 0.5

# HAPUS baris ini (sebelum python main.py):
sleep 1
```

**Catatan:** `sleep 2` yang ada di dalam blok `else` (jika deps/mpv missing) boleh dibiarkan — itu intentional untuk user baca pesan error.

---

## TASK 2 — `start.bat`: Hapus artificial delays + gabung dep check

**File:** `start.bat`

**Cari dan ganti blok dep check:**

```bat
REM SEBELUM (7× subprocess Python):
set "DEPS_OK=1"
for %%m in (aiohttp aiosqlite yt_dlp syncedlyrics structlog prometheus_client opentelemetry) do (
    python -c "import %%m" > nul 2>&1
    if errorlevel 1 (
        echo      [-] Missing module: %%m
        set "DEPS_OK=0"
    )
)
```

```bat
REM SESUDAH (1× subprocess Python):
set "DEPS_OK=1"
python -c "import aiohttp, aiosqlite, yt_dlp, syncedlyrics, structlog, prometheus_client, opentelemetry" > nul 2>&1
if errorlevel 1 (
    echo      [-] Ada modul yang belum terinstall.
    echo          Jalankan: pip install -r requirements.txt
    set "DEPS_OK=0"
)
```

**Cari dan hapus semua artificial delay:**

```bat
REM HAPUS baris ini (ada 2 tempat):
ping 127.0.0.1 -n 2 > nul

REM HAPUS baris ini (sebelum python main.py):
ping 127.0.0.1 -n 2 > nul
```

**Catatan:** `ping 127.0.0.1 -n 4 > nul` di dalam blok warning boleh dibiarkan.

---

## TASK 3 — `engine/ytdlp_client.py`: Lazy import `yt_dlp`

**File:** `engine/ytdlp_client.py`

**Cari:**
```python
import asyncio
import yt_dlp
import re
from concurrent.futures import ThreadPoolExecutor
```

**Ganti dengan:**
```python
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor
```

**Lalu cari method `_extract_sync`:**
```python
def _extract_sync(self, url, opts):
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
```

**Ganti dengan:**
```python
def _extract_sync(self, url, opts):
    import yt_dlp  # lazy import — hanya saat dibutuhkan, bukan saat startup
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)
```

**Lalu cari method `_download_sync`:**
```python
def _download_sync(self, video_id, opts):
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
```

**Ganti dengan:**
```python
def _download_sync(self, video_id, opts):
    import yt_dlp  # lazy import
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
```

**Alasan:** `yt_dlp` adalah modul yang sangat besar. Import di top-level berarti dipanggil saat `main.py` melakukan `from engine.ytdlp_client import YtDlpClient` — sebelum asyncio bahkan dimulai. Lazy import memindahkan biaya ini ke request pertama user (search/play), bukan startup.

---

## TASK 4 — `main.py`: Parallelkan DB init + MPV connect

**File:** `main.py`

**Cari blok inisialisasi sequential ini:**
```python
    # 1. Initialize DB
    print("  [1/5] Membuka database perpustakaan...")
    db = Database()
    await db.init()

    # 2. Initialize Core Engine
    print("  [2/5] Menginisialisasi YT-DLP Engine...")
    ytdlp = YtDlpClient()

    print("  [3/5] Menghubungkan ke audio player (MPV)...")
    mpv = MpvController()
    try:
        await mpv.connect()
        mpv.is_available = True
    except Exception as e:
        structlog.get_logger(__name__).error(f"mpv not available: {e}")
        state.error_msg = (
            "MPV tidak ditemukan. Jalankan: pkg install mpv (Termux) "
            "atau install MPV dan tambahkan ke PATH (Windows/Linux)."
        )
        state.status = PlayerStatus.ERROR
        mpv.is_available = False
```

**Ganti dengan:**
```python
    # 1. Inisialisasi DB dan MPV secara paralel untuk mempersingkat startup
    print("  [1/5] Membuka database + menghubungkan audio player (paralel)...")
    db = Database()
    mpv = MpvController()

    async def _init_mpv():
        try:
            await mpv.connect()
            mpv.is_available = True
        except Exception as e:
            structlog.get_logger(__name__).error(f"mpv not available: {e}")
            state.error_msg = (
                "MPV tidak ditemukan. Jalankan: pkg install mpv (Termux) "
                "atau install MPV dan tambahkan ke PATH (Windows/Linux)."
            )
            state.status = PlayerStatus.ERROR
            mpv.is_available = False

    await asyncio.gather(db.init(), _init_mpv())

    # 2. Initialize Core Engine (YtDlpClient ringan — hanya buat ThreadPoolExecutor)
    print("  [2/5] Menginisialisasi YT-DLP Engine...")
    ytdlp = YtDlpClient()

    print("  [3/5] Menyiapkan layanan playback...")
```

**Alasan:** `db.init()` (buka SQLite + execute schema) dan `mpv.connect()` (spawn proses + poll socket) sama-sama I/O bound dan independen satu sama lain. Dengan `asyncio.gather`, keduanya berjalan bersamaan — total waktu = `max(db_time, mpv_time)` bukan `db_time + mpv_time`.

---

## TASK 5 — `engine/playback/controller.py`: Fix pause delay

**File:** `engine/playback/controller.py`

**Cari method `_on_cmd_toggle_pause`:**
```python
    async def _on_cmd_toggle_pause(self, _data=None):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            new_status = PlayerStatus.PAUSED if self.state.status == PlayerStatus.PLAYING else PlayerStatus.PLAYING
            self.state.status = new_status
            await self.bus.publish(TrackPauseChangedEvent(is_paused=(new_status == PlayerStatus.PAUSED)))
            await self.mpv.toggle_pause()
```

**Ganti dengan:**
```python
    async def _on_cmd_toggle_pause(self, _data=None):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED):
            new_status = PlayerStatus.PAUSED if self.state.status == PlayerStatus.PLAYING else PlayerStatus.PLAYING
            self.state.status = new_status
            # Publish event dulu (update UI segera), lalu kirim ke mpv secara fire-and-forget.
            # Tidak perlu await mpv.toggle_pause() — mpv tidak perlu dikonfirmasi
            # untuk update state UI. Ini menghilangkan jeda 1–3 detik saat pause.
            await self.bus.publish(TrackPauseChangedEvent(is_paused=(new_status == PlayerStatus.PAUSED)))
            safe_create_task(self.mpv.toggle_pause(), name="mpv_toggle_pause")
```

**Alasan:** `mpv.toggle_pause()` hanya write ke socket (`writer.write` + `drain`) — tidak ada response yang perlu di-await dari mpv untuk keperluan UI. State sudah diupdate sebelumnya. Menggunakan `safe_create_task` memastikan error tetap ter-log jika mpv disconnect.

---

## TASK 6 — `server/handlers/websocket.py`: Parallelkan broadcast

**File:** `server/handlers/websocket.py`

**Cari method `broadcast` di class `ConnectionManager`:**
```python
    async def broadcast(self, message: dict):
        data = json.dumps(message, ensure_ascii=False)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_str(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)
```

**Ganti dengan:**
```python
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        results = await asyncio.gather(
            *[ws.send_str(data) for ws in list(self.active_connections)],
            return_exceptions=True
        )
        # Bersihkan koneksi yang error (dead)
        dead = [
            ws for ws, result in zip(list(self.active_connections), results)
            if isinstance(result, Exception)
        ]
        for ws in dead:
            self.disconnect(ws)
```

**Tambahkan import `asyncio` di bagian atas file jika belum ada** (sudah ada via `import asyncio` di `__init__` ConnectionManager, tapi pastikan ada di module level):

Cari:
```python
import json
import time
import structlog
import re
from aiohttp import web
import aiohttp
```

Ganti dengan:
```python
import asyncio
import json
import time
import structlog
import re
from aiohttp import web
import aiohttp
```

**Alasan:** Dengan 1 koneksi WS ini tidak signifikan, tapi dengan 2+ koneksi (misal buka di HP + PC sekaligus), broadcast sequential membuat setiap klien menunggu klien sebelumnya selesai. Dengan `asyncio.gather`, semua WS dikirim bersamaan.

---

## VERIFIKASI

Setelah semua patch diterapkan, jalankan:

```bash
# Test startup time
time python main.py &
# Tunggu sampai muncul "Web server running", lalu Ctrl+C
# Target: <5 detik di desktop, <10 detik di Termux

# Test fungsionalitas
python -m pytest tests/ -x -q
# Harus: semua pass, tidak ada regression
```

Indikator sukses startup cepat di log:
```
[1/5] Membuka database + menghubungkan audio player (paralel)...
[2/5] Menginisialisasi YT-DLP Engine...
[3/5] Menyiapkan layanan playback...
...
Web server running on http://0.0.0.0:8765   ← harus muncul <5 detik dari start
```

---

## CATATAN PENTING

- **Task 3 (lazy yt_dlp):** First search/play request pertama setelah startup akan sedikit lebih lambat (~1 detik) karena yt_dlp baru di-import saat itu. Ini trade-off yang acceptable — startup cepat lebih penting dari latency first-request.
- **Task 4 (parallel init):** Jika mpv tidak terinstall, error masih ter-handle dengan benar karena `_init_mpv()` memiliki try/except yang sama seperti sebelumnya.
- **Task 5 (pause fix):** Jika mpv disconnect saat toggle_pause dipanggil, `safe_create_task` akan log error tapi tidak crash. State UI tetap terupdate — sinkronisasi terjadi saat mpv reconnect.
- **Jangan ubah urutan** `asyncio.gather(db.init(), _init_mpv())` — DB harus ready sebelum services di bawahnya dibuat, dan MPV connect tidak bergantung pada DB.
