
text = r'''
---
master_id: M-076
verification_status: VALID
verified_location: start.py:1-867
code_evidence: 
```python
class ServerManagerController:
...
class ServerManagerWindow(tk.Tk):
...
class PasswordResetDialog(tk.Toplevel):
```
verification_note: File `start.py` (867 baris) mengemas logika GUI (Tkinter), headless management, koneksi socket/port checker, dan dependensi (DependencyChecker) menjadi satu (God Class / God File) tanpa pemisahan `Single Responsibility Principle`.
---

---
master_id: M-077
verification_status: VALID
verified_location: server/handlers/http.py:48-189
code_evidence: 
```python
async def serve_stream(request):
    video_id_str = request.match_info.get("video_id")
    ...
```
verification_note: Fungsi `serve_stream` sepanjang ~140 baris menangani validasi request, rate limiting custom, cross-origin check, cache reading, fallback yt-dlp URL generation, HTTP proxy streaming chunk, dan exception handling sekaligus (God Function).
---

---
master_id: M-078
verification_status: VALID
verified_location: server/handlers/auth.py:27-74
code_evidence: 
```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    async with manager.rl_lock:
        _prune_stale_ips(manager, now)
```
verification_note: Logika `handle_auth` memiliki layer-layer logika panjang seperti sinkronisasi lock rate limit, token verification fallback session db, sleep penalty array mutasi, dan pembentukan respons otentikasi.
---

---
master_id: M-079
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:39, server/handlers/ws/settings_handlers.py:9
code_evidence: 
```python
async def _handle_search(data, ws, state, ytdlp, manager, db, command_bus):
...
async def _handle_volume_up(data, ws, state, ytdlp, manager, db, command_bus):
```
verification_note: Seluruh WS handlers terikat oleh parameter boilerplate 7 argumen yang redundan `(data, ws, state, ytdlp, manager, db, command_bus)`, terlepas dari dipakai atau tidaknya argumen tersebut.
---

---
master_id: M-080
verification_status: VALID
verified_location: core/value_objects.py:4, server/handlers/ws/discover_handlers.py:7, engine/ytdlp_client.py:156
code_evidence: 
```python
_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")  # core/value_objects.py
...
VIDEO_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{11}$") # discover_handlers.py
...
re.match(r'^[a-zA-Z0-9_\-]{1,64}$', video_id) # ytdlp_client.py
```
verification_note: Logika regex memvalidasi `video_id` YouTube ditulis berulang di berbagai file dengan format berlainan tanpa standarisasi tunggal (Duplicate Code).
---

---
master_id: M-081
verification_status: VALID
verified_location: server/handlers/http.py:17, server/middleware.py:6
code_evidence: 
```python
_stream_rate_limit = collections.defaultdict(list)
STREAM_RATE_LIMIT_MAX = 20 # http.py
...
cmd_history = manager.command_history.get(client_ip, []) # middleware.py
if len(cmd_history) >= MAX_RATE_LIMIT: # (30 dari constants.py)
```
verification_note: Implementasi rate limit dipecah fungsionalitasnya menjadi dua tracker mandiri (`manager.command_history` untuk WS vs `_stream_rate_limit` untuk HTTP) dengan limit kuota yang tidak sinkron (30 vs 20) dan endpoints seperti `/health` tidak tercover sama sekali.
---

---
master_id: M-082
verification_status: VALID
verified_location: server/handlers/auth.py:41, server/handlers/http.py:98
code_evidence: 
```python
attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]
...
if time.time() - row.stream_url_ts < STREAM_URL_TTL_SEC:
```
verification_note: Ditemukan berbagai literal konstanta magic numbers seperti waktu `300` detik di hardcode di kode.
---

---
master_id: M-083
verification_status: VALID
verified_location: web/static/js/ws.js:71, server/handlers/ws/settings_handlers.py:17
code_evidence: 
```javascript
    switch (msg.type) {
        case "auth_status":
...
@register_ws_handler("volume_set")
```
verification_note: Routing handler maupun penanganan event di client-side menggunakan label string literal (Magic String) rentan patah / typo (misalnya: `@register_ws_handler("volume_set")` tidak merujuk pada class `WSAction`).
---

---
master_id: M-084
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:67
code_evidence: 
```python
            await db.conn.execute("UPDATE tracks SET is_favorite = ? WHERE video_id = ?", (target, video_id))
```
verification_note: Handler WebSocket (`_handle_toggle_favorite`) membypass lapisan abstraksi / Repository dan secara brutal menembak database dengan me-mutate via perintah mentah `db.conn.execute`. (Feature Envy).
---

---
master_id: M-085
verification_status: VALID
verified_location: web/static/js/audio.js:102, web/static/js/bundle.js:2162
code_evidence: 
```javascript
function resumeVisualizerLoop() {
    if (animationId) return;
    if (Date.now() - lastVisualizerUpdate < 50) return;
    drawVisualizer();
}
```
verification_note: Prosedur `resumeVisualizerLoop()` hanya dideklarasikan di file, tetapi tidak ada instruksi panggilan (invoke) darimana pun di codebase (Dead Code).
---

---
master_id: M-086
verification_status: SUDAH_BENAR
verified_location: web/static/js/audio.js:291, web/static/js/events/player-events.js:20
code_evidence: 
```javascript
    document.addEventListener("click", unlockBrowserAudio);
```
verification_note: Berbeda dengan temuan yang menyebut `unlockBrowserAudio` nganggur (Dead Code), fungsi ini secara eksplisit dipanggil dari event listener click browser, serta pada saat tombol settings output ditekan, untuk inisialisasi awal AudioContext.
---

---
master_id: M-087
verification_status: VALID
verified_location: start.py:419, start.py:431
code_evidence: 
```python
            def on_log(line, tag):
                self._last_stdout_line = line
...
    def _wait_for_server_ready(self, port: int):
...
        self._last_stdout_line = ""
```
verification_note: Properti `self._last_stdout_line` ditulis secara konstan dari output sub-process tetapi nilainya tak pernah benar-benar dibaca atau divisualisasikan oleh UI. (Dead Variable).
---

---
master_id: M-088
verification_status: VALID
verified_location: server/handlers/auth.py:44, engine/download_manager.py:33, engine/download_manager.py:77
code_evidence: 
```python
        if attempts:
            import asyncio
            await asyncio.sleep(min(len(attempts), 5))
```
verification_note: Import module inline seperti `import asyncio` atau `import shutil` menumpuk nyelip di tengah fungsi eksekusi (seperti `handle_auth`, `_do_download`), menyebabkan inefisiensi namespace dan scope per-panggilan.
---

---
master_id: M-089
verification_status: VALID
verified_location: server/handlers/websocket.py:5
code_evidence: 
```python
import aiohttp
import structlog
from aiohttp import web
```
verification_note: `import aiohttp` diekspor di level modul namun sama sekali tidak pernah di-invoke (UNUSED), karena seluruh request aiohttp di-pass via namespace spesifik `from aiohttp import web`.
---

---
master_id: M-090
verification_status: VALID
verified_location: web/static/js/ws.js:127, web/static/js/ws.js:137, web/static/js/audio.js:174, dll
code_evidence: 
```javascript
                    // PATCH-ANDROID-AUDIO-01: kalau sebelumnya sudah ketauan diblock browser,
...
            // PATCH-ANDROID-AUDIO-01: dipanggil tiap tick (bukan cuma saat statusChanged)
```
verification_note: Artefak revisi lama masa lalu (seperti `PATCH-ANDROID-AUDIO-01`, `PATCH-AUDIO-UNLOCK-RACE-01`) dibiarkan menggunung di kode JS dan tests, mengotori codebase dengan barisan dokumentasi histori internal perbaikan patch.
---

Batch ini: 14 valid, 0 tidak ditemukan, 1 sudah benar, 0 perlu konfirmasi.

'''

with open('docs/verifikasi_ekstraksi.md', 'a', encoding='utf-8') as f:
    f.write(text)
