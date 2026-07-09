# Laporan Audit Async — LunaWave

Metode: menelusuri seluruh call chain pembuatan task (`asyncio.create_task`/`safe_create_task`/`loop.create_task`), pemakaian lock (`asyncio.Lock`), subprocess async, dan siklus shutdown; dikonfirmasi dengan menjalankan test suite (muncul warning nyata `Task was destroyed but it is pending!` untuk `persist_state_loop`).

---

## BUG #1 (KRITIS) — Task bocor: `persist_state_loop` tidak pernah disimpan/dibatalkan

**Lokasi**
`engine/playback/controller.py:71` (dibuat) & `core/bootstrap.py:186-197` / `main.py:38-43` (shutdown)
```python
# controller.py __init__
safe_create_task(self._persist_state_loop(), name="persist_state_loop")
```
```python
# main.py
tasks = start_background_tasks(ctx)   # hanya berisi connectivity_task & db_cleanup_task
...
finally:
    await shutdown_app_context(ctx, tasks)   # hanya cancel task di 'tasks'
```

**Penyebab**
`safe_create_task()` mengembalikan objek `asyncio.Task`, tapi nilai kembaliannya **dibuang** (tidak disimpan ke `self._persist_state_task` atau semacamnya). Karena `PlaybackController` tidak menyimpan referensi kuat ke task ini, dan task ini juga tidak dimasukkan ke list `tasks` yang dikembalikan `start_background_tasks()`, maka:
1. Tidak ada referensi eksternal apapun yang menahan task ini tetap hidup — berisiko dihancurkan prematur oleh garbage collector di tengah eksekusi (event loop hanya menyimpan *weak reference*). Ini **terbukti nyata** — muncul warning saat test run:
   ```
   Task was destroyed but it is pending!
   task: <Task pending name='persist_state_loop' ...>
   ```
2. `shutdown_app_context()` tidak pernah bisa memanggil `.cancel()` pada loop `while True` ini karena tidak punya akses ke referensinya.

**Impact**
- Loop persist-state (`while True: sleep(5) → save_to_disk`) berpotensi berhenti diam-diam kapan saja akibat GC, sehingga state berhenti tersimpan ke disk tanpa ada log error yang jelas ke user.
- Saat aplikasi shutdown, task ini tidak dibatalkan secara graceful → proses exit tidak bersih (task masih pending saat event loop ditutup).

**Solusi minimal**
Simpan referensi task ke `self`, dan kembalikan/daftarkan agar ikut di-cancel saat shutdown:
```python
self._persist_state_task = safe_create_task(self._persist_state_loop(), name="persist_state_loop")
```
lalu sertakan `self._persist_state_task` ke list `tasks` yang diteruskan ke `shutdown_app_context` (mis. lewat `ctx.playback_controller._persist_state_task`).

---

## BUG #2 (KRITIS) — Task bocor: `DownloadManager._workers` tidak pernah di-cancel saat shutdown

**Lokasi**
`engine/download_manager.py:33-35` (dibuat), tidak direferensikan di `core/bootstrap.py::shutdown_app_context`
```python
self._workers = []
for i in range(3):
    self._workers.append(safe_create_task(self._worker_loop(), name=f"dl_worker_{i}"))
```

**Penyebab**
Berbeda dari Bug #1, referensi task di sini memang disimpan (`self._workers`), jadi tidak berisiko di-GC prematur. Namun `self._workers` **tidak pernah dibaca oleh kode manapun** — tidak ada method `close()`/`stop()` di `DownloadManager`, dan `shutdown_app_context()` hanya membatalkan `tasks` (list dari `start_background_tasks`), yang tidak memuat worker download ini sama sekali.

**Impact**
Saat aplikasi dimatikan, 3 worker loop (`while True: await self._download_queue.get()`) tetap berstatus *pending* selamanya. `asyncio.run(main())` di `main.py` akan menutup event loop dengan task-task ini masih berjalan, menyebabkan proses shutdown tidak bersih (kemungkinan warning "Task was destroyed but it is pending!" identik dengan Bug #1, atau proses mpv/ytdlp anak yang sedang didownload terhenti paksa tanpa pembatalan yang tertib).

**Solusi minimal**
Tambahkan pembatalan eksplisit di `shutdown_app_context`, misalnya:
```python
for t in ctx.download_manager._workers:
    t.cancel()
```
(dengan syarat `download_manager` diekspos lewat `AppContext`, tanpa mengubah struktur lain).

---

## BUG #3 (KRITIS) — Async/Sync API tertukar pada `asyncio.subprocess.Process` (await hilang + API salah)

**Lokasi**
`engine/mpv_controller.py:219-224`, dalam blok `finally` di `_observe_events()`
```python
self._mpv_process.terminate()
try:
    self._mpv_process.wait(timeout=1)      # <- BUG
except Exception:
    pass
if self._mpv_process.poll() is None:       # <- BUG
    self._mpv_process.kill()
```

**Penyebab**
`self._mpv_process` dibuat lewat `asyncio.create_subprocess_exec(...)`, sehingga bertipe `asyncio.subprocess.Process` — bukan `subprocess.Popen`. Pada `asyncio.subprocess.Process`:
- `.wait()` adalah **coroutine** tanpa parameter `timeout`, harus dipanggil dengan `await`. Di sini dipanggil **tanpa `await`** dan dengan kwarg `timeout=1` yang tidak dikenali API-nya → langsung melempar `TypeError` saat baris itu dieksekusi.
- `.poll()` **tidak ada** pada `asyncio.subprocess.Process` (method itu milik `subprocess.Popen`) → akan melempar `AttributeError`.

Kedua exception ini **langsung ditelan** oleh `except Exception: pass` yang membungkusnya, sehingga bug ini gagal sunyi (silent failure) — tidak pernah terlihat di log.

Bandingkan dengan pola yang benar yang sudah ada di method `close()` pada file yang sama:
```python
self._mpv_process.terminate()
try:
    await asyncio.wait_for(self._mpv_process.wait(), timeout=1.0)
except asyncio.TimeoutError:
    self._mpv_process.kill()
```

**Impact**
Saat koneksi ke mpv terputus dan proses lama perlu dihentikan sebelum restart (`_observe_events` reconnect path), logika "tunggu 1 detik lalu paksa kill jika belum berhenti" **tidak pernah benar-benar berjalan** — exception langsung terjadi di baris pertama dan ditelan diam-diam, lalu kode lompat ke `.poll()` yang juga error dan tertelan. Proses mpv lama berpotensi menjadi proses zombie/tidak pernah benar-benar diberi kill signal melalui jalur ini, dan graceful-termination yang dimaksud desainer kode tidak pernah tercapai.

**Solusi minimal**
Samakan dengan pola yang sudah benar di `close()`:
```python
self._mpv_process.terminate()
try:
    await asyncio.wait_for(self._mpv_process.wait(), timeout=1.0)
except asyncio.TimeoutError:
    self._mpv_process.kill()
```
(mengganti `wait(timeout=1)` + `poll()` dengan `await asyncio.wait_for(self._mpv_process.wait(), timeout=1.0)`).

---

## BUG #4 (SEDANG) — Lock dipegang terlalu lama, menghambat operasi async lain (blocking)

**Lokasi**
`engine/playback/queue_commands.py::on_queue_select`
```python
async def on_queue_select(self, cmd):
    async with self.playback_controller._lock:
        if 0 <= cmd.index < len(self.state.queue):
            track = self.state.queue[cmd.index]
            for _ in range(cmd.index):
                skipped = self.state.queue.pop(0)
                self.state.history.append(skipped)
            self.state.queue.pop(0)
            await self.playback_controller.play_track(track)   # <- I/O panjang, masih di dalam lock
```

**Penyebab**
`self.playback_controller._lock` diambil untuk melindungi mutasi `state.queue`/`state.history` (operasi cepat, murni in-memory). Namun `await self.playback_controller.play_track(track)` — yang melakukan resolve URL (jaringan), `mpv.play()`, dan publish event — **tetap dieksekusi di dalam blok `async with self._lock`**, sehingga lock ini dipegang selama seluruh proses loading track (bisa berdetik-detik karena I/O jaringan/mpv).

Selama lock ini dipegang, semua handler lain yang juga butuh `self._lock` — `_on_track_progress`, `_on_pause_changed`, `_on_track_duration`, serta `on_queue_remove`/`on_queue_add`/`on_queue_replace`/`on_queue_reorder` — akan **tertahan (blocked)** menunggu giliran, walaupun operasi-operasi tersebut secara logis tidak berkaitan dengan proses loading track yang sedang berjalan.

**Impact**
- Update posisi playback (`_on_track_progress`) dan status pause/resume (`_on_pause_changed`) akan macet/tertunda selama track baru sedang di-load — dari sisi user terasa seperti UI "freeze" sesaat.
- Command antrean lain (tambah/hapus/reorder lagu) yang dikirim bersamaan akan tertahan sampai `play_track` selesai, padahal `play_track` sendiri sudah punya proteksi race-condition-nya sendiri lewat `self._play_lock` (lock terpisah, komentar "A-05: cegah concurrent play_track race").
- Risiko laten: jika di masa depan ada event yang dipublish di dalam call-chain `play_track` (mis. dari `track_loader`/`mpv`) yang handler-nya juga butuh `self._lock`, akan terjadi deadlock nyata karena `asyncio.Lock` tidak reentrant (task yang sama menunggu lock yang sudah dipegangnya sendiri).

**Solusi minimal**
Lepaskan `self._lock` sebelum memanggil `play_track` — pindahkan pemanggilan `play_track` keluar dari blok `async with`:
```python
async def on_queue_select(self, cmd):
    track = None
    async with self.playback_controller._lock:
        if 0 <= cmd.index < len(self.state.queue):
            track = self.state.queue[cmd.index]
            for _ in range(cmd.index):
                skipped = self.state.queue.pop(0)
                self.state.history.append(skipped)
            self.state.queue.pop(0)
    if track is not None:
        await self.playback_controller.play_track(track)
```

---

## Ringkasan
| # | Severity | Jenis | Lokasi utama |
|---|----------|-------|---------------|
| 1 | Kritis | Task bocor (referensi tidak disimpan + tidak di-cancel) | `engine/playback/controller.py` |
| 2 | Kritis | Task bocor (tidak di-cancel saat shutdown) | `engine/download_manager.py` |
| 3 | Kritis | Await hilang + API async/sync tertukar, ditelan silent except | `engine/mpv_controller.py` |
| 4 | Sedang | Lock dipegang selama I/O panjang → blocking / risiko deadlock laten | `engine/playback/queue_commands.py` |

Tidak ada perbaikan di luar isu asynchronous yang disertakan.
