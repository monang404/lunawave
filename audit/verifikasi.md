Berikut adalah hasil verifikasi terhadap batch temuan audit:

---
master_id: M-001
source_findings: [EXEC-001, ARCH-A07, MAINT-C-01, CS-016, CS-002]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:81-86
code_evidence: 
```python
        if state.current_track and state.current_track.video_id == video_id:
            state.current_track.is_favorite = is_fav
            await manager.broadcast({
                "type": "state",
                "data": state.to_dict()
            })
```
verification_note: `AppState` yang didefinisikan di `core/state.py` merupakan sekadar dataclass, sementara kode handler seperti contoh di atas langsung memodifikasi atribut (`state.current_track.is_favorite`) dari coroutine berbeda secara _bypassing_ tanpa kunci (lock) maupun event bus.
---
master_id: M-002
source_findings: [EXEC-002, ARCH-A11, DB-012, CS-020, REP-01]
verification_status: VALID
verified_location: cache/db.py:140-148
code_evidence: 
```python
    def __getattr__(self, name):
        """Proxy missing methods to the repositories to maintain backward compatibility."""
        if self.tracks and hasattr(self.tracks, name):
            return getattr(self.tracks, name)
        if self.sessions and hasattr(self.sessions, name):
            return getattr(self.sessions, name)
        if self.discover and hasattr(self.discover, name):
            return getattr(self.discover, name)
        raise AttributeError(f"'Database' object has no attribute '{name}'")
```
verification_note: Sesuai dengan klaim, object `Database` memilki magic proxy `__getattr__` yang merutekan _method calls_ ke sub-modul (_repositories_), yang mana bernilai `None` sebelum `init()` selesai.
---
master_id: M-003
source_findings: [EXEC-003, ARCH-A09]
verification_status: VALID
verified_location: config.py:12-14
code_evidence: 
```python
    socket_dir = BASE_DIR / "cache" / "sockets"
    socket_dir.mkdir(parents=True, exist_ok=True)
    _raw_socket = os.environ.get("YT_PLAYER_SOCKET", str(socket_dir / "mpv-yt-player.sock"))
```
verification_note: Eksekusi _side-effect_ dengan membuat folder (operasi IO) dieksekusi secara top-level persis di saat proses _import_ module `config`.
---
master_id: M-004
source_findings: [EXEC-004, BUG-B06, BUG-02, MAINT-R-03]
verification_status: VALID
verified_location: engine/mpv_controller.py:298-301
code_evidence: 
```python
    async def _set_property(self, prop: str, value):
        await self._command(["set_property", prop, value])
import time

```
verification_note: Import time benar-benar tergeletak begitu saja di baris terbawah (di luar _scope_ class dan top file), yang berisiko memicu NameError bila modul `time` dipanggil dari dalam eksekusi _method_ sebelum baris terakhir selesai terbaca.
---
master_id: M-005
source_findings: [EXEC-005]
verification_status: VALID
verified_location: server/app.py:16-17
code_evidence: 
```python
def create_app(playback_controller: PlaybackController, ytdlp: MediaExtractorPort, db: DatabasePort, manager: ConnectionManager, command_bus=None, event_bus=None) -> web.Application:
    try:
```
verification_note: `http_session` diinisialisasi di `core/bootstrap.py` tapi tidak pernah diloloskan menjadi argumen di fungsi `create_app` untuk _state_ aplikasi. Akibatnya ketika dipanggil dari `server/handlers/http.py`, `app.get("http_session")` bernilai None.
---
master_id: M-006
source_findings: [EXEC-006]
verification_status: VALID
verified_location: server/app.py:35-41
code_evidence: 
```python
    from server.routes import ROUTE_INDEX, ROUTE_WS, ROUTE_STREAM, ROUTE_HEALTH, ROUTE_METRICS, ROUTE_STATIC
    app.router.add_get(ROUTE_INDEX, serve_index)
    app.router.add_get(ROUTE_WS, ws_handler)
    app.router.add_get(ROUTE_STREAM, serve_stream)
    app.router.add_get(ROUTE_HEALTH, health_check)
    app.router.add_get(ROUTE_METRICS, serve_metrics)
    app.router.add_static(ROUTE_STATIC, STATIC_DIR, name="static", append_version=True)
```
verification_note: Tidak ada satupun _middleware_ atau injeksi yang mengatur konfigurasi dan _header_ keamanan HTTP disematkan pada respons aplikasi webnya di _entrypoint_ inisialisasi server.
---
master_id: M-007
source_findings: [EXEC-007]
verification_status: VALID
verified_location: server/handlers/http.py:157-164
code_evidence: 
```python
                response = web.StreamResponse(
                    status=upstream.status,
                    headers={
                        "Content-Type": upstream.headers.get("Content-Type", "audio/mpeg"),
                        "Accept-Ranges": "bytes",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "private, max-age=3600",
                    }
                )
```
verification_note: Endpoint stream `serve_stream` secara vulgar mengatur _hardcode_ `Access-Control-Allow-Origin` menjadi `*` (wildcard) yang memungkinkan sembarang asal domain membaca audio ini.
---
master_id: M-008
source_findings: [EXEC-008, API-03, CS-024]
verification_status: VALID
verified_location: server/handlers/auth.py:57-61
code_evidence: 
```python
        if secrets.compare_digest(username, ADMIN_USERNAME) and verify_password(password, get_admin_password()):
            new_token = secrets.token_hex(16)
            if db:
                await db.create_session(new_token, int(now) + 14400)
            manager.authenticated_connections.add(ws)
```
verification_note: Token generasi sesi hanya menggunakan `secrets.token_hex(16)` dan tidak ada mekanisme lain yang menukar (_rotate_) token selama siklus hidup sesi berjalan.
---
master_id: M-009
source_findings: [EXEC-009]
verification_status: VALID
verified_location: web/static/js/services/auth.js:79-84
code_evidence: 
```javascript
    store.userRole = "portal";
    store.adminUsername = "";
    safeStorage.remove("ytgui_user_role");
    safeStorage.remove("ytgui_admin_username");
    safeStorage.remove("ytgui_session_token");

    closeSettings();
```
verification_note: Proses `logout` murni terjadi di _client-side_ untuk menghapus cache localStorage, tetapi sama sekali tidak diiringi dengan _call_ ke API server untuk _revoke_ atau invalidasi token di _database_, menjadikannya aktif hingga `expiration_time` berakhir.
---
master_id: M-010
source_findings: [EXEC-010]
verification_status: VALID
verified_location: server/handlers/websocket.py:96-97
code_evidence: 
```python
                if TRUSTED_PROXY and "X-Forwarded-For" in request.headers:
                    client_ip = request.headers.get("X-Forwarded-For").split(",")[0].strip()
```
verification_note: Saat _fallback_ proxy terpercaya menyala, variabel `X-Forwarded-For` dicacah dan bagian paling awal (`[0]`) di-set buta sebagai IP klien tanpa memvalidasi _depth/hop_ asal IP pengirim (_spoofable_).
---
master_id: M-011
source_findings: [EXEC-011, DEP-002]
verification_status: VALID
verified_location: .gitignore:1-15
code_evidence: 
```text
# Virtual environments and secrets
.env
*.env
.venv
env/
venv/
ENV/
```
verification_note: `node_modules` atau folder dependensi lokal sama sekali tidak dimasukkan ke dalam daftar blacklist `.gitignore`.
---
master_id: M-012
source_findings: [EXEC-012, BUG-B20, CS-025, BL-02]
verification_status: VALID
verified_location: core/constants.py:4
code_evidence: 
```python
MAX_VOLUME = 150
```
verification_note: `MAX_VOLUME` di-set menjadi 150 pada `core/constants.py`, tetapi pada `core/value_objects.py` line 13 kelas `Volume` memaksa pemotongan nilai (clamp) maksimum menjadi 100, sehingga terjadi inkonsistensi.
---
master_id: M-013
source_findings: [EXEC-013, EXEC-039, PERF-P14, EXC-03]
verification_status: VALID
verified_location: server/handlers/http.py:17
code_evidence: 
```python
_stream_rate_limit = collections.defaultdict(list)
```
verification_note: Variabel `_stream_rate_limit` hanya menambah riwayat (history) pada line 62 tanpa pernah menghapus record/IP yang sudah usang jika user tidak mengakses lagi, memicu memory leak murni.
---
master_id: M-014
source_findings: [EXEC-014]
verification_status: SUDAH_BENAR
verified_location: web/static/js/ws.js:139-147
code_evidence: 
```javascript
            if (statusChanged) {
                renderNowPlaying();
                renderQueue();
                renderRadio();
                updateSearchPlayingState();
                updateDiscoverPlayingState();
                if (store.audio_output === 'browser') {
                    syncBrowserAudio();
                }
            }
```
verification_note: Pemanggilan `syncBrowserAudio()` pada WS handler `progress` sudah dibungkus di dalam kondisi `if (statusChanged)`. Jadi TIDAK dipanggil pada setiap tick time update (333ms), melainkan hanya saat state lagu benar-benar berubah.
---
master_id: M-015
source_findings: [EXEC-015, FE-018]
verification_status: VALID
verified_location: web/static/js/audio.js:73-75
code_evidence: 
```javascript
        }, 150);
    }
    _fakeBeatRaf = requestAnimationFrame(tick);
```
verification_note: `startFakeBeatLoop` dieksekusi menggunakan loop `requestAnimationFrame` dan `setTimeout` secara terus-menerus tanpa memberhentikan event ketika page ter-hide.
---
master_id: M-016
source_findings: [EXEC-016, PERF-P02, SVC-02]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:81-86
code_evidence: 
```python
        if state.current_track and state.current_track.video_id == video_id:
            state.current_track.is_favorite = is_fav
            await manager.broadcast({
                "type": "state",
                "data": state.to_dict()
            })
```
verification_note: Sama halnya temuan M-001, ketika nilai 'favorite' pada track berubah, handler mengirim fungsi `state.to_dict()` secara vulgar yang mem-broadcast ulang KESELURUHAN antrian ke seluruh klien.
---
master_id: M-017
source_findings: [EXEC-017]
verification_status: VALID
verified_location: server/app.py:48-51
code_evidence: 
```python
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
```
verification_note: Server aiohttp dieksekusi tunggal via `web.AppRunner(app)` pada root asyncio loop tanpa worker pool sama sekali (misal gunicorn).
---
master_id: M-018
source_findings: [EXEC-018]
verification_status: VALID
verified_location: web/static/js/ws.js:149-151
code_evidence: 
```javascript
            if (store.lyrics_lines && store.lyrics_lines.length > 0) {
                requestAnimationFrame(() => syncLocalLyrics());
            }
```
verification_note: Kode memicu fungsi `requestAnimationFrame` di handler "progress" yang ditembak berulang-ulang saat koneksi WS aktif tiap detiknya untuk sinkronisasi lirik.
---
master_id: M-019
source_findings: [EXEC-019]
verification_status: PERLU_KONFIRMASI
verified_location: -
code_evidence: -
verification_note: Temuan "Penamaan bilingual tidak konsisten" sifatnya tersebar secara abstrak dalam file, sehingga tidak bisa diarahkan pada line/blok spesifik dan membutuhkan pencarian lebih luas.
---
master_id: M-020
source_findings: [EXEC-020, PERF-P10]
verification_status: VALID
verified_location: web/static/js/bundle.js:1-5
code_evidence: 
```javascript
// --- config.js ---
const TABS = ["home", "search", "radio", "discover"];

// --- store.js ---
const store = {
```
verification_note: File `bundle.js` adalah hasil kompilasi skrip vanilla concat biasa berjumlah sangat masif tanpa melalui proses minification atau source maps removal.
---
master_id: M-021
source_findings: [EXEC-021]
verification_status: TIDAK_DITEMUKAN
verified_location: engine/download_manager.py:86
code_evidence: 
```python
                await self.bus.publish(LogMessageEvent(message=f"Download sukses: {track.title} (Tersimpan di folder 'downloads')"))
```
verification_note: Teks bahasa Inggris "Download complete" tidak dapat ditemukan sama sekali pada log di dalam codebase, melainkan "Download sukses:".
---
master_id: M-022
source_findings: [EXEC-022]
verification_status: VALID
verified_location: -
code_evidence: 
```text
file tidak ada di path tersebut
```
verification_note: Direktori root tidak memiliki file `CHANGELOG.md` sama sekali (hanya ada versi obsolete di archive jika ada).
---
master_id: M-023
source_findings: [EXEC-023, EXEC-038, ARCH-A05, DEP-001]
verification_status: VALID
verified_location: pyproject.toml:13
code_evidence: 
```toml
    "aiosqlite==0.22.1",
```
verification_note: Terdapat perbedaan fatal pendefinisian dependensi di mana `pyproject.toml` menggunakan `0.22.1`, sementara di `requirements.txt` baris 2 memaksa `0.20.0`.
---
master_id: M-024
source_findings: [EXEC-024, AUDIT-TEST-001]
verification_status: VALID
verified_location: tests/unit/engine/test_queue_locking.py:18-20
code_evidence: 
```python
    def test_on_queue_remove_uses_lock(self):
        """on_queue_remove HARUS menggunakan 'async with self.playback_controller._lock'."""
        source = inspect.getsource(QueueCommands.on_queue_remove)
```
verification_note: Kode pada unit tests melakukan pengecekan inspeksi regex literal baris source code (inspect.getsource) bukan run asserstion pada logika runtime itu sendiri.
---
master_id: M-025
source_findings: [EXEC-025]
verification_status: VALID
verified_location: .github/workflows/ci.yml:40-41
code_evidence: 
```yaml
    - name: Run tests with coverage
      run: pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=40
```
verification_note: Nilai rasio keberhasilan coverage test CI dibatasi sangat rendah `--cov-fail-under=40` (40%).
---
master_id: M-026
source_findings: [EXEC-026, AUDIT-TEST-002]
verification_status: VALID
verified_location: tests/integration/test_fase1.py:92-99
code_evidence: 
```python
        with patch("server.handlers.http.get_metrics_content"):
            with patch("aiohttp.web.BaseRequest.remote", new_callable=pytest.MonkeyPatch):
                # Karena tidak mudah patch readonly property, kita patch dictionary
                pass

            # Mari gunakan patch untuk _localhost_ips yang digunakan di dalam fungsi
            # Namun karena itu didefinisikan lokal di dalam fungsi, kita tidak bisa patch.
            pass
```
verification_note: Blok pengujian integrasi perlindungan IP pada `test_fase1.py` dibiarkan kosong melompong (hanya berisi `pass`) tanpa adanya satupun eksekusi request dan asersi, sehingga status lulus tes bersifat palsu.
---
master_id: M-027
source_findings: [EXEC-027, AUDIT-TEST-003, AUDIT-TEST-004, AUDIT-TEST-005, AUDIT-TEST-006, AUDIT-TEST-007, AUDIT-TEST-008, AUDIT-TEST-009]
verification_status: VALID
verified_location: -
code_evidence: 
```text
Tidak ada integrasi tes atau mock pada alur fungsional kritis
```
verification_note: Sesuai klaim audit, setelah menelusuri folder `tests/`, tidak ditemukan berkas pengujian apa pun untuk fungsionalitas inti aplikasi, logika MPV, atau simulasi WS event handler.
---
master_id: M-028
source_findings: [EXEC-028, DEP-010]
verification_status: VALID
verified_location: pyproject.toml:46-47
code_evidence: 
```toml
check_untyped_defs = false
disallow_untyped_defs = false
```
verification_note: Konfigurasi alat Mypy diatur terlampau permisif, dengan tipe cek untuk def tak bertipe dimatikan secara total.
---
master_id: M-029
source_findings: [EXEC-029, DEP-009]
verification_status: VALID
verified_location: pyproject.toml:40
code_evidence: 
```toml
ignore = ["E501", "E722", "E731", "E402", "F841", "E712", "E741", "E701", "E702", "I001"]
```
verification_note: Ruff secara gamblang mematikan aturan (ignore) esensial seperti `E722` (bare except) dan `F841` (unused variable).
---
master_id: M-030
source_findings: [EXEC-030]
verification_status: VALID
verified_location: -
code_evidence: 
```text
Tidak ditemukan modul k6, locust, atau stress tester lainnya
```
verification_note: Tidak ada satupun alat untuk uji beban/performa dan load testing di repositori ini.
---
master_id: M-031
source_findings: [EXEC-031, QUE-03]
verification_status: VALID
verified_location: core/state.py:93-94
code_evidence: 
```python
    queue:           deque = field(default_factory=deque)
    radio_queue:     deque = field(default_factory=deque)
```
verification_note: Antrean queue hanya menggunakan native `deque` in-memory. Jika instance aplikasi python restart, antrean akan menguap.
---
master_id: M-032
source_findings: [EXEC-032, DB-001]
verification_status: VALID
verified_location: cache/db.py:33
code_evidence: 
```python
        self._conn = await aiosqlite.connect(self.db_path)
```
verification_note: Aplikasi murni menggunakan 1 (satu) koneksi tunggal SQLite `_conn` yang dipakai bergantian, sama sekali tidak menggunakan connection pooler.
---
master_id: M-033
source_findings: [EXEC-033, PERF-P07, CC-02]
verification_status: VALID
verified_location: server/handlers/websocket.py:25
code_evidence: 
```python
        self.active_connections = []
```
verification_note: Variabel `active_connections` sekadar native list python tanpa memiliki pembatasan panjang maksimum (max length).
---
master_id: M-034
source_findings: [EXEC-034]
verification_status: VALID
verified_location: engine/download_manager.py:55
code_evidence: 
```python
        safe_create_task(self._do_download(target), name=f"download_{target.video_id}")
```
verification_note: Proses download ditembak langsung menggunakan `safe_create_task` di event loop tanpa ada penahan batas concurrency queue (sistem queue/job).
---
master_id: M-035
source_findings: [EXEC-035]
verification_status: VALID
verified_location: -
code_evidence: 
```text
Tidak ditemukan cache Redis/Memcached pada file server.
```
verification_note: Semua proses discover menembak mentah-mentah via SQLite karena tidak ada lapisan cache eksternal sama sekali.
---
master_id: M-036
source_findings: [EXEC-036]
verification_status: VALID
verified_location: server/handlers/http.py:17
code_evidence: 
```python
_stream_rate_limit = collections.defaultdict(list)
```
verification_note: Keamanan pencatatan rate limit disimpan pada variabel RAM lokal `_stream_rate_limit`. Restart server otomatis me-reset memori serangan brute-force.
---
master_id: M-037
source_findings: [EXEC-037, ARCH-A02, DEP-006]
verification_status: VALID
verified_location: Dockerfile:28
code_evidence: 
```dockerfile
CMD ["python", "run.py"]
```
verification_note: Dockerfile secara keliru menunjuk ke entrypoint eksekusi `run.py` padahal file penjalannya seharusnya adalah `main.py`. 
---
master_id: M-038
source_findings: [EXEC-040, FE-019]
verification_status: VALID
verified_location: web/static/manifest.json:11-15
code_evidence: 
```json
    {
      "src": "/static/lunawave_logo.png",
      "sizes": "1024x1024",
      "type": "image/png"
    }
```
verification_note: Hanya ada satu ukuran ikon (1024x1024) yang didaftarkan dalam `manifest.json`.
---
master_id: M-039
source_findings: [EXEC-041, CS-011, MAINT-N-02, MAINT-N-03]
verification_status: VALID
verified_location: .env.example:1-21
code_evidence: 
```env
YTGUI_HOST=0.0.0.0
...
YT_PLAYER_SOCKET=/tmp/mpv-ytgui.sock
...
TRUSTED_PROXY=127.0.0.1
```
verification_note: Prefix variabel environemnt di `.env.example` masih campur aduk menggunakan `YTGUI_`, `YT_PLAYER_`, dan non-prefix yang membingungkan.
---
master_id: M-040
source_findings: [EXEC-042]
verification_status: VALID
verified_location: tests/test_helpers.html:1-4
code_evidence: 
```html
<!DOCTYPE html>
<html>
<head>
    <title>JS Helpers Test</title>
```
verification_note: File berekstensi HTML ini nyasar diletakkan pada folder direktori `tests/` milik backend pengujian python.
---
master_id: M-041
source_findings: [EXEC-043, ARCH-A12]
verification_status: VALID
verified_location: web/static/js/ws.js:18
code_evidence: 
```javascript
    window.ws = ws;
```
verification_note: Objek koneksi websocket mentah diekspos secara vulgar ke scope `window` global pada browser klien, memungkinkan campur tangan atau intrusi skrip luar (XSS).
---
master_id: M-042
source_findings: [BUG-B01, ARCH-A01, BUG-01]
verification_status: VALID
verified_location: server/services/discover_service.py:36
code_evidence: 
```python
                        stream_url=d["stream_url"],
```
verification_note: Kode pada blok kueri SQLite sama sekali tidak men-SELECT kolom `stream_url`, namun pada inisialisasi TrackInfo, kunci map dict `d["stream_url"]` diakses secara mutlak yang memicu KeyError fatal.
---
master_id: M-043
source_findings: [BUG-B02]
verification_status: VALID
verified_location: server/handlers/auth.py:28-45
code_evidence: 
```python
    async with manager.rl_lock:
        ...
        if attempts:
            import asyncio
            await asyncio.sleep(min(len(attempts), 5))
```
verification_note: Eksekusi penundaan rate limit `asyncio.sleep` diletakkan di dalam lock mutex `rl_lock` global, berpotensi mengunci seluruh sistem autentikasi dari client lain (Denial of Service).
---
master_id: M-044
source_findings: [BUG-B03]
verification_status: VALID
verified_location: engine/playback/controller.py:173-192
code_evidence: 
```python
        if reason == "eof":
            await asyncio.sleep(0.35)
            await self._advance_to_next()
        elif reason == "stop":
            pass
        elif reason == "error":
```
verification_note: Parameter logis untuk string `reason` bernilai kosong (seperti "") yang terlewat dari kondisi "eof", "stop", maupun "error" akan diabaikan total, membuat lagu berikutnya gagal diputar (autoplay mati).
---
master_id: M-045
source_findings: [BUG-B04, CC-03]
verification_status: VALID
verified_location: engine/playback/controller.py:146-150
code_evidence: 
```python
        if should_retry:
            backoff = 2 ** self._retry_count
            await asyncio.sleep(backoff)
```
verification_note: Pembacaan variabel statis `self._retry_count` terjadi di luar jangkauan blok mutex pelindung `async with self._play_lock`, rentan mengalami data race saat diakses paralel.
---
master_id: M-046
source_findings: [BUG-B05]
verification_status: VALID
verified_location: engine/playback/controller.py:186-192
code_evidence: 
```python
        elif reason == "error":
            self.state.status = PlayerStatus.ERROR
            ...
            await asyncio.sleep(2)
            if self.state.status == PlayerStatus.IDLE:
                return
```
verification_note: Kondisi guard IDLE tidak akan pernah terpenuhi karena nilai statusnya sudah ditetapkan keras ke ERROR sesaat sebelum jeda asinkron `sleep`.
---
master_id: M-047
source_findings: [BUG-B07]
verification_status: VALID
verified_location: engine/playback/controller.py:59
code_evidence: 
```python
        self._lock = asyncio.Lock()
```
verification_note: Objek mutex `self._lock` dideklarasikan namun tidak pernah sekalipun dipanggil pada scope internal kelas `PlaybackController` tersebut.
---
master_id: M-048
source_findings: [BUG-B08]
verification_status: VALID
verified_location: engine/playback/playback_commands.py:29-35
code_evidence: 
```python
    async def on_next(self, cmd=None):
        async with self.playback_controller._lock:
            ...
            await self.playback_controller._advance_to_next()
```
verification_note: Handler `on_next` menahan lock terpusat `_lock` di saat yang sama memanggil `_advance_to_next` (yang mengurus I/O panjang), mengakibatkan bottleneck parah di seluruh command lainnya.
---
master_id: M-049
source_findings: [BUG-B09]
verification_status: VALID
verified_location: engine/playback/controller.py:163-171
code_evidence: 
```python
                if dur is not None and dur > 0:
                    ...
                await self.bus.publish(QueueUpdatedEvent())
```
verification_note: Baris propagasi event antrean terpasang di bawah scope luar tanpa mengecek jika `dur` berhasil didapat. Hal ini memicu trigger sia-sia bila `dur` bernilai None.
---
master_id: M-050
source_findings: [BUG-B10, SVC-03]
verification_status: VALID
verified_location: engine/volume_service.py:19
code_evidence: 
```python
        self.current_volume = state.volume
```
verification_note: Servis volume hanya memegang cerminan status awal memori volume saat inisialisasi tanpa secara asinkron memantau status get_volume mutakhir pada layer daemon OS Mpv.
---
master_id: M-051
source_findings: [BUG-B11]
verification_status: VALID
verified_location: server/handlers/websocket.py:111-112
code_evidence: 
```python
    data = msg.get("data", {})
```
verification_note: Tidak ada jaminan validasi tipe objek dictionary dict pada `data`. Jika `data` dikirim client berwujud literal string, handler lanjutan yang mengeksekusi `get()` akan lumpuh.
---
master_id: M-052
source_findings: [BUG-B12]
verification_status: VALID
verified_location: server/handlers/websocket.py:101-102
code_evidence: 
```python
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
```
verification_note: Scope Except menangkap liar kelas dasar Exception dan mencetak sebagai log ERROR meski yang tertangkap adalah pemutusan koneksi wajar seperti CancelledError.
---
master_id: M-053
source_findings: [BUG-B13]
verification_status: VALID
verified_location: cache/repositories/track_repository.py:136-137
code_evidence: 
```python
        await self._conn.execute(
            f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids
        )
```
verification_note: Kumpulan identifier langsung dioper bertipe data iteratif array `list` ketimbang diserialisasi sebagai `tuple` parameter bind SQLite murni.
---
master_id: M-054
source_findings: [BUG-B14]
verification_status: VALID
verified_location: plugins/sponsorblock.py:38
code_evidence: 
```python
        self.segments = []
```
verification_note: Memori blok segmen langsung dikosongkan sebelum request jaringan (yang rawan delayed HTTP call) dimulai, membekukan fitur proteksi SponsorBlock di saat transisi awal video diputar.
---
master_id: M-055
source_findings: [BUG-B15, DB-017, EXC-01, EXC-02, RTY-01, CAC-03]
verification_status: VALID
verified_location: cache/resolver.py:42-44
code_evidence: 
```python
        if track.video_id in self._fetching:
            await self._fetching[track.video_id].wait()
            return await self.resolve(track)
```
verification_note: Siklus loop rekursi tanpa batas jika task fetch yt-dlp melempar exception: waiter dibangunkan lalu memanggil get `resolve()` lagi, yang men-trigger gagal tak terbatas (Thundering herd/Memory Leak).
---
master_id: M-056
source_findings: [BUG-B16]
verification_status: VALID
verified_location: plugins/lyrics.py:138-141
code_evidence: 
```python
            else:
                if line:
                    result.append((0.0, line))
```
verification_note: Sesuai temuan, jika parser gagal mencocokkan pattern (contohnya baris metadata seperti `[ti:Title]`), teks tersebut dimasukkan dengan timestamp `0.0`.
---
master_id: M-057
source_findings: [BUG-B17]
verification_status: VALID
verified_location: plugins/lyrics.py:57-80
code_evidence: 
```python
            if track.video_id in self._cache:
                lrc = self._cache[track.video_id]
...
            clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title)
...
            if not lrc:
```
verification_note: Variabel `clean_title` dan eksekusi RegEx `re.sub` diproses secara berat tanpa menghiraukan apakah nilai `lrc` sebenarnya sudah didapatkan sukses dari _cache_.
---
master_id: M-058
source_findings: [BUG-B18, EXC-04]
verification_status: VALID
verified_location: engine/playback/controller.py:181-183
code_evidence: 
```python
        if reason == "eof":
            await asyncio.sleep(0.35)
            await self._advance_to_next()
```
verification_note: Tidak terdapat mekanisme penguncian/flag boolean pelindung terhadap trigger paralel. Jika mesin mpv mengirim lebih dari satu notifikasi `eof` saat lag/masalah jaringan, maka trek bisa terlewati dua kali.
---
master_id: M-059
source_findings: [BUG-B19]
verification_status: VALID
verified_location: web/static/sw.js:76-79
code_evidence: 
```javascript
            }).catch(() => {
                if (event.request.headers.get('accept').includes('text/html')) {
                    return caches.match('/static/index.html');
                }
            })
```
verification_note: `Service Worker` mencoba memuat _fallback offline_ `/static/index.html`, namun karena file rute index utamanya disajikan dari root `/`, file di path tersebut tidak akan ada dan PWA offline mode gagal beroperasi.
---
master_id: M-060
source_findings: [BUG-B21]
verification_status: SUDAH_BENAR
verified_location: core/background_tasks.py:23
code_evidence: 
```python
        except Exception as e:
            structlog.get_logger(__name__).warning(f"Connectivity check unexpected error: {e}")
            state.is_online = False

        await asyncio.sleep(60)
```
verification_note: Klaim audit salah. Pemanggilan `await asyncio.sleep(60)` berlokasi **di luar** cakupan blok `try...except`. Jadi ketika asyncio melontarkan `CancelledError` pada siklus _graceful shutdown_, task ini akan sukses terhenti (tidak tertelan oleh `except Exception as e`).
---
master_id: M-061
source_findings: [BUG-B22]
verification_status: SUDAH_BENAR
verified_location: engine/playback/radio_commands.py:21
code_evidence: 
```python
            if self.state.playback_mode == PlaybackMode.RADIO:
                seed = cmd.seed_artist if cmd else None
```
verification_note: Kode pada baris 21 nyatanya telah mengimplementasikan pengecekan Null dengan ternary operator `if cmd else None`, menepis klaim audit bahwa `cmd.seed_artist` dieksekusi buta dan memicu `AttributeError`.
---
master_id: M-062
source_findings: [BUG-B23]
verification_status: VALID
verified_location: core/state.py:62-64
code_evidence: 
```python
        try:
            video_id = VideoId(data.get("video_id", ""))
        except ValueError:
            return None
```
verification_note: Objek TrackInfo diam-diam menelan eksepsi `ValueError` jika hash ID tidak valid dan langsung membalikkan balasan kosong `None` tanpa meninggalkan jejak log error.
---
master_id: M-063
source_findings: [BUG-B24]
verification_status: VALID
verified_location: engine/playback/controller.py:177-179
code_evidence: 
```python
        next_data = {}
        if self.state.current_track:
            next_data["video_id"] = self.state.current_track.video_id
```
verification_note: Variabel tipe dictionary `next_data` dideklarasikan, disematkan value video_id ke dalamnya, tetapi variabel ini tidak pernah digunakan lagi seiring berjalannya keseluruhan alur perpindahan.
---
master_id: M-064
source_findings: [BUG-B25, ARCH-A13]
verification_status: VALID
verified_location: server/services/discover_service.py:131-132
code_evidence: 
```python
        except Exception as e:
            print(f"Error in get_featured_genres: {e}")
```
verification_note: Tangkapan galat yang tereksekusi pada fungsi `get_featured_genres` menggunakan utilitas primitif `print()` bukannya log dari object logger yang telah ditentukan.
---
master_id: M-065
source_findings: [BUG-B26]
verification_status: VALID
verified_location: core/log_config.py:403-404
code_evidence: 
```python
        sys.stderr.flush()
        return ""  # prevent default handler from double-printing
```
verification_note: structlog `_CompactRenderer` mengirim balik tipe primitive string kosong `""` ke struktur chain yang mengharapkan object dictionary. Ini merupakan arsitektur kustom logger yang berisiko.
---
master_id: M-066
source_findings: [BUG-B27]
verification_status: VALID
verified_location: core/log_config.py:119-122
code_evidence: 
```python
def _summary_worker():
    while True:
        time.sleep(600)  # every 10 minutes
        with STATS.lock:
```
verification_note: Memang benar bahwa daemon thread `_summary_worker` dirancang mengeksekusi iterasi loop `while True` tanpa event `.wait()` maupun parameter exit flag. (Catatan: `_status_bar_worker` sudah memiliki `_status_bar_active`).
---
master_id: M-067
source_findings: [BUG-B28]
verification_status: VALID
verified_location: web/static/js/utils.js:194-196
code_evidence: 
```javascript
    } catch (e) {
        console.warn("Color extraction failed:", e);
        if (callback) callback("var(--bg-elevated)");
    }
```
verification_note: Fungsi pemanggil ekstraksi warna `extractDominantColor` memberikan String CSS `"var(--bg-elevated)"` saat catch error, sedangkan ekspektasi balasan di mana-mana seharusnya berupa Object `{r,g,b}`.
---
master_id: M-068
source_findings: [ARCH-A03]
verification_status: VALID
verified_location: web/static/js/utils.js:91-92
code_evidence: 
```javascript
        const cleanTitle = window.cleanTrackTitle(track.title);
        const query = encodeURIComponent(track.artist + " " + cleanTitle);
        const response = await fetch(`${ITUNES_API_URL}?term=${query}&media=music&limit=1`);
```
verification_note: `ITUNES_API_URL` tidak didefinisikan sama sekali di dalam kode scope `utils.js` maupun global `bundle.js`, sehingga dapat memicu `ReferenceError` pada _browser_ saat fetch iTunes.
---
master_id: M-069
source_findings: [ARCH-A04]
verification_status: VALID
verified_location: web/static/js/audio.js:141-142
code_evidence: 
```javascript
export async function _resumeAndPlay(audio) {
    if (audioCtx && audioCtx.state === 'suspended') {
```
verification_note: Modul di `audio.js` membenturkan sintaks JS ESM `export async function` namun pada HTML tidak diikat bersama format type="module", memicu `SyntaxError: Unexpected token 'export'` pada klien.
---
master_id: M-070
source_findings: [ARCH-A06, MAINT-CO-01]
verification_status: VALID
verified_location: server/services/discover_service.py:17-42
code_evidence: 
```python
    async def get_recent(self, n: int) -> list[TrackInfo]:
        ...
            async with self.db.conn.execute(  # type: ignore
                "SELECT video_id, title, artist, duration, thumbnail, local_path, view_count, play_count, is_favorite FROM tracks ORDER BY last_played DESC LIMIT ?", (n,)
            ) as cursor:
```
verification_note: Fungsi layer _service_ `DiscoverService` langsung menebak dan menembak raw SQL query ke dalam layer DB secara sporadis. Logika query ini seharusnya ditempatkan secara _Dry_ pada kelas _repository_ yang bersangkutan (`TrackRepository` / `DiscoverRepository`).
---
master_id: M-071
source_findings: [ARCH-A08]
verification_status: VALID
verified_location: server/handlers/websocket.py:48-60
code_evidence: 
```python
    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
...
        targets = list(self.active_connections)
```
verification_note: Data status player (termasuk lagu yang diputar) dibroadcast ke koleksi `self.active_connections` yang memuat seluruh socket klien, bahkan yang belum terautentikasi dan berada di pool IP terblokir.
---
master_id: M-072
source_findings: [ARCH-A10, QUE-01]
verification_status: VALID
verified_location: engine/playback/queue_commands.py:23-24
code_evidence: 
```python
            if 0 <= cmd.index < len(self.state.queue):
                removed = self.state.queue[cmd.index]
                del self.state.queue[cmd.index]
```
verification_note: List queue menggunakan struktur data `deque` standar dari modul python collections. Operator `del` terhadap elemen spesifik deque memiliki kompleksitas operasi $O(N)$ di mana seluruh blok rotasi elemen akan digeser linear.
---
master_id: M-073
source_findings: [ARCH-A17, CS-010]
verification_status: VALID
verified_location: core/state.py:43, 54, 77
code_evidence: 
```python
    is_favorite: Optional[int] = 0
...
            "is_favorite": bool(getattr(self, "is_favorite", 0)),
...
            is_favorite=int(data.get("is_favorite", False)),
```
verification_note: Penamaan anotasi tipe variabelnya adalah `Optional[int] = 0`, akan tetapi ketika diekspor diubah menjadi Boolean via object mapping, lalu ketika diserialisasi kembali lewat `from_dict` dikonversi ke Integer boolean base. Terdapat duplikasi standar boolean.
---
master_id: M-074
source_findings: [ARCH-A18]
verification_status: VALID
verified_location: core/event_bus.py:33-37
code_evidence: 
```python
    def subscribe(self, event_type: Type[E], handler: Callable[[E], Any]):
        if inspect.ismethod(handler):
            ref = weakref.WeakMethod(handler)
        else:
            ref = handler  # type: ignore
        self._subscribers[event_type].append(ref)
```
verification_note: Fungsi lambda atau handler nested dicatat menggunakan _strong reference_ alias disalin paksa ke array, yang akan mencegah garbage collector membersihkan variabel objek tersebut secara permanen sehingga rawan menjadi _memory leak_.
---
master_id: M-075
source_findings: [ARCH-A19, QUE-02]
verification_status: VALID
verified_location: server/handlers/ws/queue_handlers.py:57-59
code_evidence: 
```python
            await command_bus.execute(SetModeCommand(mode=PlaybackMode.QUEUE))
            await command_bus.execute(QueueReplaceCommand(tracks=songs))
            await command_bus.execute(QueueSelectCommand(index=0))
```
verification_note: Handler ini menumpuk tiga fungsi _command bus dispatching_ asinkron sekaligus tanpa penguncian _lock_. Terbuka sangat lebar celah _Race condition_ apabila state diganggu _concurrent socket clients_ di antara pengiriman await tersebut.
---
master_id: M-076
source_findings: [CS-001, MAINT-R-02, CS-006, CS-008, CS-015]
verification_status: VALID
verified_location: start.py:539-800
code_evidence: 
```python
class ServerManagerWindow(tk.Tk):
    def __init__(self):
        super().__init__()
...
        self.controller.run_dependency_check()
...
```
verification_note: Modul GUI `start.py` menggabungkan keseluruhan utilitas backend Tkinter (Port Scanner, Subprocess Executor, UI Layout DOM, SQL Connector, Thread Waiter, File System chmod) ke dalam 1 struktur _God Class_ lebih dari 800 baris kotor, melanggar pola *Single Responsibility*.
---
master_id: M-077
source_findings: [CS-003]
verification_status: VALID
verified_location: server/handlers/http.py:48-189
code_evidence: 
```python
async def serve_stream(request):
    video_id_str = request.match_info.get("video_id")
...
```
verification_note: Tanggung jawab yang seharusnya dienkapsulasi (ID Validator, DB Querying, CORS Auth Origin Checker, Rate Limiting, Proxy Resolver, ETag caching rules, HTTP streaming chunks) ditulis berderet vertikal sepanjang ~140 baris kodingan dalam satu _God Function_ yang membengkak.
---
master_id: M-078
source_findings: [CS-004]
verification_status: VALID
verified_location: server/handlers/auth.py:27-74
code_evidence: 
```python
async def handle_auth(ws, data, manager, client_ip, db, now):
    async with manager.rl_lock:
        _prune_stale_ips(manager, now)
```
verification_note: Metode `handle_auth` memiliki beban kontrol berlebih. Dalam 1 blok try-catch, memvalidasi _stale IPs_, melakukan rate-limit wait punishment, _password hashing checking_, manipulasi token DB, hingga manipulasi Websocket socket-send ke klien.
---
master_id: M-079
source_findings: [CS-005, MAINT-A-03]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:40
code_evidence: 
```python
@register_ws_handler(WSAction.SEARCH)
async def _handle_search(data, ws, state, ytdlp, manager, db, command_bus):
```
verification_note: Semua fungsi socket (contoh: Search, QueueSelect, Volume) memiliki pemaksaan tipe injeksi long-list dependency parameter yang selalu kembar-7 (data, ws, state, ytdlp, manager, db, command_bus) yang padahal tidak semua argumen dipakai. Modifikasi satu _signature_ parameter memaksa perubahan di 26 handler file WS.
---
master_id: M-080
source_findings: [CS-007]
verification_status: VALID
verified_location: core/value_objects.py:4, server/handlers/ws/discover_handlers.py:7, engine/ytdlp_client.py:156
code_evidence: 
```python
    _RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
```
verification_note: Ekspresi *Regular Expression* dari validasi hash video YouTube ditulis redundan setidaknya di 3 tempat berbeda tanpa pemanggilan sentral. Di dalam WS handler `discover` tertera `^[A-Za-z0-9_-]{11}$`, sementara di value-object `^[a-zA-Z0-9_-]{11}$` dan di engine ada regex custom string lain.
---
master_id: M-081
source_findings: [CS-009, API-06]
verification_status: VALID
verified_location: server/handlers/http.py:17, server/middleware.py:4-16
code_evidence: 
```python
_stream_rate_limit = collections.defaultdict(list)
STREAM_RATE_LIMIT_MAX = 20
```
verification_note: Modul filter *Rate limiter* di-copy paste di 2 lingkungan terpisah dengan nama yang berbeda. `middleware.py` untuk WS berbasis `command_history`, dan `http.py` mendirikan variabel lokal `_stream_rate_limit` manual berbasis array defaultdict tanpa sinkronisasi global limit API.
---
master_id: M-082
source_findings: [CS-012]
verification_status: VALID
verified_location: server/handlers/auth.py:13-14
code_evidence: 
```python
    WINDOW_AUTH = 300
    WINDOW_CMD  = 60
```
verification_note: Terlalu banyak angka temporal *Magic Number* (seperti `300`, `60`, `14400`, `16384`) dibiarkan mengapung di kode yang tersebar alih-alih ditaruh rapi di `core.constants`.
---
master_id: M-083
source_findings: [CS-013, API-14]
verification_status: VALID
verified_location: web/static/js/ws.js:99
code_evidence: 
```javascript
function handleServerMessage(msg) {
    switch (msg.type) {
        case "auth_status":
...
        case "state":
```
verification_note: JavaScript meng-hardcode string literal (`"auth_status"`, `"state"`, `"progress"`) alih-alih mem-parsing _type definition enum_ lintas backend/frontend. Pada WS di backend pun, `"volume_set"` didaftarkan menggunakan string mentahan alih-alih mengambil variabel terpusat `WSAction.VOLUME_SET`.
---
master_id: M-084
source_findings: [CS-014, MAINT-A-01, REP-03]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:67
code_evidence: 
```python
            await db.conn.execute("UPDATE tracks SET is_favorite = ? WHERE video_id = ?", (target, video_id))
            await db.conn.commit()
```
verification_note: Bukti tak terbantahkan bahwa _Coupling Abstraction Layer_ dibobol brutal. Logic socket (_interface layer_) menerobos _service class_ dan meraba parameter _connection sql_ langsung memodifikasi query SQLite tanpa lewat `Repository`.
---
master_id: M-085
source_findings: [CS-017]
verification_status: VALID
verified_location: web/static/js/audio.js:102-104
code_evidence: 
```javascript
function resumeVisualizerLoop() {
    if (!_vizRafId && analyser) startVisualizerLoop();
}
```
verification_note: Fungsi Javascript `resumeVisualizerLoop` dideklarasikan tapi status modulnya tak ter-export alias tidak di-_invoke_ pada proses DOM atau Event handler dari luar kode _scope_-nya (*Dead Code*).
---
master_id: M-086
source_findings: [CS-018]
verification_status: SUDAH_BENAR
verified_location: web/static/js/audio.js:290-292, web/static/js/main.js:21
code_evidence: 
```javascript
function initAudio() {
    document.addEventListener("click", unlockBrowserAudio);
}
```
verification_note: Klaim audit salah. Prosedur `unlockBrowserAudio` secara aktif di-_binding_ oleh event listener klik dokumen di dalam `initAudio()`, dan inisiator tersebut telah dipanggil langsung oleh eksekutor startup UI utama (`main.js`). Oleh karena itu fungsi tersebut sama sekali bukan dead code.
---
master_id: M-087
source_findings: [CS-019]
verification_status: VALID
verified_location: start.py:419, 431
code_evidence: 
```python
            def on_log(line, tag):
                self._last_stdout_line = line
...
        self._last_stdout_line = ""
```
verification_note: Variabel properti `self._last_stdout_line` ditulis secara aktif setiap iterasi _stream stdout_ tetapi tak pernah ada satu fungsipun yang membacanya. Ini menjadi sampah memori.
---
master_id: M-088
source_findings: [CS-021, MAINT-TD-03]
verification_status: VALID
verified_location: engine/download_manager.py:33-35, server/handlers/auth.py:44
code_evidence: 
```python
        async def handler(command):
            import asyncio
            res = action(command.track)
```
verification_note: `import asyncio` dipanggil tepat di dalam *scope* (di tengah-tengah fungsi _async def_), menyebabkan instruksi resolusi *module* tertumpuk secara berulang-ulang tiap *handler* terpanggil, sebuah inefisiensi yang kentara.
---
master_id: M-089
source_findings: [CS-022]
verification_status: SUDAH_BENAR
verified_location: server/handlers/websocket.py:90, 99
code_evidence: 
```python
            if msg.type == aiohttp.WSMsgType.TEXT:
...
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
```
verification_note: Audit keliru. Modul inti `aiohttp` (bukan sekadar `aiohttp.web`) tetap digunakan namespace-nya untuk memanggil konstanta enum dari jenis _WS message type_ secara eksplisit.
---
master_id: M-090
source_findings: [CS-023, MAINT-TD-01]
verification_status: VALID
verified_location: config.py:29, engine/mpv_controller.py:21-23, engine/radio_engine.py:121
code_evidence: 
```python
# PATCH-YTDLP-RESOLVE-TIMEOUT-01: yt-dlp.get_stream_url() sebelumnya tidak punya batas waktu
...
    # CRITICAL-03 fix: On Windows, falls back to TCP socket (localhost:port)
...
            # PATCH-RADIO-EMPTY-QUEUE-01: Queue habis — _start() jalan di background
```
verification_note: Jejak revisi perbaikan *issue* tertinggal di berbagai sudut kode produksi (menandakan *tech debt*) tanpa dibersihkan dengan layak usai *merge* dilakukan.
---
master_id: M-091
source_findings: [PERF-P01]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:19-23
code_evidence: 
```python
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)
    favorites = await ds.get_favorites(DISCOVER_FAVORITES_LIMIT)
    cached = await ds.get_cached(DISCOVER_CACHED_LIMIT)
    featured_artists = await ds.get_featured_artists(DISCOVER_FEATURED_ARTISTS_LIMIT)
    featured_genres = await ds.get_featured_genres(DISCOVER_FEATURED_GENRES_LIMIT)
```
verification_note: Kelima tabel / sumber agregasi _discover_ dieksekusi menunggu berantai (_serial_). Jika 1 baris memakan waktu 15ms, maka klien harus menunggu 75ms hanya untuk mengekstrak struktur query yang padahal bisa ditembakkan independen dengan `asyncio.gather`.
---
master_id: M-092
source_findings: [PERF-P03, TXN-01]
verification_status: VALID
verified_location: cache/db.py:93-121
code_evidence: 
```python
        for artist in data.get('artists', []):
...
            for lagu in artist.get('lagu_populer', []):
...
                    await self._conn.execute('''
                        INSERT OR IGNORE INTO songs (artist_id, judul, youtube_id, duration)
```
verification_note: Mekanisme penanaman _seed database_ tidak disatukan dalam perintah `executemany` secara *batching*. Menembakkan lebih dari ratusan query raw SQL *execute* per perulangan For Loop.
---
master_id: M-093
source_findings: [PERF-P04]
verification_status: VALID
verified_location: core/constants.py:13-14
code_evidence: 
```python
DISCOVER_FEATURED_ARTISTS_LIMIT = 100
DISCOVER_FEATURED_GENRES_LIMIT = 100
```
verification_note: Terdapat dua konstanta batas limit 100 data entri yang memicu pengiriman payload WebSocket raksasa di halaman pencarian kategori ke seluruh klien pada fase awal halaman *discover*.
---
master_id: M-094
source_findings: [PERF-P05]
verification_status: VALID
verified_location: web/static/js/ws.js:226-238
code_evidence: 
```javascript
function renderFullState() {
    renderHeader();
    renderNowPlaying();
...
    renderLyrics();
    renderSettingsSheet();
...
```
verification_note: Sebuah mutasi kedudukan waktu pemutaran (contohnya pergeseran 1 detik track audio) memicu _Redraw_ / perenderan buta ke seluruh seksi aplikasi, karena tidak ada *Dirty Check* (_Diffing_) State per komponen layaknya kerangka JS modern.
---
master_id: M-095
source_findings: [PERF-P06]
verification_status: VALID
verified_location: web/static/js/render/discover.js:126, 192, 412
code_evidence: 
```javascript
                el.dataset.trackStr = JSON.stringify(track).replace(/'/g, "&apos;");
...
            el.dataset.track = JSON.stringify(track);
```
verification_note: Operasi mahal serialisasi obyek metadata (`JSON.stringify`) diulang tanpa belas kasihan di dalam iterasi per-item list hasil *Discover* dan *Recent*, yang bisa berpotensi menghabiskan daya *scripting* Frame secara instan.
---
master_id: M-096
source_findings: [PERF-P08]
verification_status: VALID
verified_location: web/static/js/utils.js:152-156
code_evidence: 
```javascript
        const canvas = document.createElement('canvas');
        const canvasContext = canvas.getContext('2d', { willReadFrequently: true });
...
        const data = canvasContext.getImageData(0, 0, 50, 50).data;
```
verification_note: Pengambilan bit sampel gambar dieksekusi sinkron pada lapisan Main-Thread DOM (bukan pada Worker), memaksa UI mengalami kondisi _freeze/jank_ mikrosekon sejenak tiap cover musik diganti.
---
master_id: M-097
source_findings: [PERF-P09]
verification_status: VALID
verified_location: web/static/js/render/discover.js:291, 432
code_evidence: 
```javascript
    window.loadLazyCovers();
```
verification_note: `window.loadLazyCovers()` dipanggil di akhir iterasi kedua fungsi `renderRecentRow` maupun `renderDiscoverTab`. Karena penempatannya, fungsi yang mengaktifkan peramban `IntersectionObserver` ini menghajar tag secara dobel pada iterasi satu siklus *Event Loop*.
---
master_id: M-098
source_findings: [PERF-P11]
verification_status: VALID
verified_location: web/static/js/main.js:57-59
code_evidence: 
```javascript
        if (tab === "discover" || tab === "home") {
            wsSend(WS_ACTIONS.DISCOVER);
        }
```
verification_note: Klien yang dengan santai klik bolak-balik pergantian menu (misalnya Discover - Search - Discover) akan selalu menghantam WebSocket Server dengan instruksi pengiriman ulang query Database *Discover* (tanpa blok *caching* / jeda *Throttle*).
---
master_id: M-099
source_findings: [PERF-P12, DB-009]
verification_status: VALID
verified_location: cache/schema.sql:19-22
code_evidence: 
```sql
CREATE INDEX IF NOT EXISTS idx_local_path ON tracks(local_path) WHERE local_path IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_last_played ON tracks(last_played DESC);
CREATE INDEX IF NOT EXISTS idx_play_count ON tracks(play_count DESC) WHERE play_count > 0;
CREATE INDEX IF NOT EXISTS idx_stream_url_ts ON tracks(stream_url_ts);
```
verification_note: Sama sekali tak terdapat formasi blok index semisal `CREATE INDEX idx_is_favorite ON tracks(is_favorite)` guna mempercepat query perburuan daftar lagu-lagu favorit pada dataset ratusan item lagu.
---
master_id: M-100
source_findings: [PERF-P13]
verification_status: VALID
verified_location: web/static/sw.js:5-30
code_evidence: 
```javascript
const PRECACHE_ASSETS = [
...
    '/static/css/tokens.css',
    '/static/css/base/reset.css',
...
```
verification_note: Strategi Service Worker PWA melakukan beban *Precache* belasan CSS statis mentahan yang padahal sudah dienkapsulasi dengan perintah `@import` di `inter.css` atau yang dimuat seutuhnya ke bundle bundler, sehingga mubazir bandwith.
---
master_id: M-101
source_findings: [PERF-P15]
verification_status: VALID
verified_location: engine/mpv_controller.py:284-290
code_evidence: 
```python
        try:
            self._writer.write(payload.encode())
            await self._writer.drain()
            return await asyncio.wait_for(future, timeout=2.0)
        except (OSError, asyncio.TimeoutError):
            self._pending.pop(request_id, None)
            return None
```
verification_note: Blok eksekusi `await asyncio.wait_for` hanya menangkap `OSError` dan `TimeoutError`. Jika task induk di-cancel (melempar `asyncio.CancelledError`), future di dalam dict `_pending` tidak akan pernah di-pop dan menggantung abadi di memori, berpotensi memory leak.
---
master_id: M-102
source_findings: [PERF-P16, SVC-01]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:17-33
code_evidence: 
```python
async def _build_discover_payload(db):
    ds = DiscoverService(db)
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)
    favorites = await ds.get_favorites(DISCOVER_FAVORITES_LIMIT)
...
    return {
        "type": "discover_data",
        "data": {
            "recent": [t.to_dict() for t in recent],
```
verification_note: Pembentukan muatan data discover memanggil database dengan batas statis (`DISCOVER_RECENT_LIMIT`, dll) namun sama sekali tidak menyediakan kontrol parameter asupan seperti `offset` maupun `page`, sehingga mustahil melakukan infinite-scroll bagi antarmuka klien.
---
master_id: M-103
source_findings: [PERF-P17]
verification_status: VALID
verified_location: (Global CSS Bundle)
code_evidence: 
(Semua aturan CSS disatukan di main.css yang dibundle via esbuild di package.json)
verification_note: Tidak ada mekanisme _Critical CSS_ atau pemecahan chunk asset spesifik mobile. Semua aset gaya diunduh dan diproses penuh meski perangkat pengguna tidak mengakses _layout_ desktop.
---
master_id: M-104
source_findings: [PERF-P18, FE-021]
verification_status: VALID
verified_location: web/static/js/render/discover.js:1-9
code_evidence: 
```javascript
const _hashtagColors = {};
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag];
    const hue = Math.floor(Math.random() * 360);
...
    const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    _hashtagColors[hashtag] = color;
    return color;
}
```
verification_note: Pewarnaan elemen UI hash tag/genre sepenuhnya diundi dengan algoritma `Math.random()`. Walaupun menggunakan dictionary memory sementara, warna akan hilang/berubah drastis ketika page _refresh_.
---
master_id: M-105
source_findings: [DB-002]
verification_status: VALID
verified_location: cache/db.py:30-36
code_evidence: 
```python
    async def init(self):
...
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
```
verification_note: Pada saat inisialisasi basis data SQLite, parameter konfigurasi mendasar `PRAGMA busy_timeout = 5000` dihilangkan, berpotensi menghasilkan `SQLITE_BUSY` saat terjadi balapan data simpan antar handler (konkurensi).
---
master_id: M-106
source_findings: [DB-003, DB-004, DEVOPS-021]
verification_status: VALID
verified_location: cache/db.py:42-47, cache/schema.sql
code_evidence: 
```python
        async def add_column_if_not_exists(table, column, definition):
...
            if column not in columns:
                await self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
```
verification_note: Perubahan arsitektur kolom sepenuhnya bergantung injeksi raw skrip ad-hoc saat runtime alih-alih memakai sistem migrasi sah semacam _Alembic_. Menyebabkan jejak evolusi data kacau, susah mundur versi, dan rentan patah.
---
master_id: M-107
source_findings: [DB-005]
verification_status: VALID
verified_location: cache/db.py:95-98
code_evidence: 
```python
            await self._conn.execute('''
                INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif)
                VALUES (?, ?, ?, ?)
            ''', (artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))
```
verification_note: Karena `INSERT OR REPLACE` di SQLite bermakna "hapus baris lama dan buat baris baru", parameter metrik seperti `click_count` di tabel artis akan dibunuh kembali menjadi default (Nol) jika sinkronisasi re-seed terjadi.
---
master_id: M-108
source_findings: [DB-006, DB-015, REP-02]
verification_status: VALID
verified_location: cache/repositories/track_repository.py:108-138
code_evidence: 
```python
        cursor = await self._conn.execute(
            """SELECT video_id FROM tracks ..."""
        )
        rows = await cursor.fetchall()
...
        for vid in video_ids:
            p = CACHE_DIR / f"{vid}.mp3"
            if p.exists():
                try: p.unlink()
...
        await self._conn.execute(
            f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids
        )
```
verification_note: Urutan skenario mengambil array id, lalu unlink file IO disusul instruksi DELETE sql sangat rawan bentrok _race condition_. Seandainya server lumpuh sebelum perulangan SQL tereksekusi, maka MP3-nya menguap tapi logik rekam di basis datanya gentayangan tak tersentuh.
---
master_id: M-109
source_findings: [DB-007, TXN-03]
verification_status: VALID
verified_location: cache/repositories/track_repository.py:93-97
code_evidence: 
```python
            """UPDATE tracks
               SET is_favorite = 1 - COALESCE(is_favorite, 0)
               WHERE video_id = ?
               RETURNING is_favorite""",
```
verification_note: _Clause_ istimewa `RETURNING` hanya kompatibel di instrumen SQLite v3.35 ke atas. Pemasangan baris ini seketika menumbangkan fungsionalitas tombol favorite bagi pengguna ponsel tua karena dilempar _Syntax Error_.
---
master_id: M-110
source_findings: [DB-008]
verification_status: VALID
verified_location: cache/schema.sql:24-27
code_evidence: 
```sql
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL
);
```
verification_note: Tabel penyimpan kunci otentikasi login admin tidak mengaplikasikan _B-Tree Index_ pada kolom penyortir waktu `expires_at`, melambatkan operasi pembersihan (cleanup) seiring menumpuknya session kadaluarsa.
---
master_id: M-111
source_findings: [DB-010, TXN-04]
verification_status: VALID
verified_location: cache/repositories/track_repository.py:44-55
code_evidence: 
```python
            INSERT INTO tracks (
...             local_path, last_played
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
...
                last_played=excluded.last_played
```
verification_note: Operasi menimpa/memperbaharui record _track_ mengikutsertakan parameter _last_played_ ke titik waktu saat ini (sekarang), meskipun fungsi _upsert_ juga dapat dipanggil dari interaksi ringan seperti caching tanpa pemutaran player sungguhan, merusak validitas daftar _Recently Played_.
---
master_id: M-112
source_findings: [DB-011]
verification_status: VALID
verified_location: cache/db.py:93-98, cache/schema.sql:30-31
code_evidence: 
```sql
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY,
    nama TEXT NOT NULL,
```
verification_note: Desain `artists.id` dicabut status `AUTOINCREMENT`-nya, lalu memaksakan suplai ID mutlak dari berkas JSON di dalam kode Python. Praktek ini amat rapuh merusak konsistensi _foreign keys_ manakala urutan array ID JSON tergusur.
---
master_id: M-113
source_findings: [DB-013]
verification_status: VALID
verified_location: cache/repositories/auth_repository.py:28-29
code_evidence: 
```python
            if row:
                await self.delete_session(token)
            return False
```
verification_note: Terjadi penyimpangan side-effect tak terduga; Fungsi yang namanya `verify_session` (yang sejatinya merupakan _Query/Read_) diimbuhi logika perintah menghancurkan sesi (`delete_session`).
---
master_id: M-114
source_findings: [DB-014, REP-04, BL-03]
verification_status: VALID
verified_location: cache/repositories/discover_repository.py:76-77
code_evidence: 
```sql
                SELECT s.youtube_id, s.judul, s.duration, a.nama,
                       ROW_NUMBER() OVER (PARTITION BY s.artist_id ORDER BY RANDOM()) as rn
```
verification_note: Query kalkulasi radio memanfaatkan fungsi rumit SQL Window `ROW_NUMBER()`, yang tidak diakui oleh piranti lama (SQLite rilis di bawah v3.25), memancing sistem menjadi lumpuh saat dibangkitkan pada lingkungan Android/Debian tua. 
---
master_id: M-115
source_findings: [DB-016]
verification_status: VALID
verified_location: cache/schema.sql:3-17
code_evidence: 
```sql
CREATE TABLE IF NOT EXISTS tracks (
    video_id     TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    artist       TEXT,
```
verification_note: Tabel primer `tracks` mengandalkan nama artis dalam format baris _string_ harfiah ketimbang merelasikan _foreign key_ `artist_id` ke dalam tabel `artists`. Menodai esensi normalisasi data (duplikat teks).
---
master_id: M-116
source_findings: [API-01]
verification_status: VALID
verified_location: core/state.py:58-76
code_evidence: 
```python
    @classmethod
    def from_dict(cls, data: dict) -> Optional['TrackInfo']:
...
            local_path=data.get("local_path"),
            stream_url=data.get("stream_url"),
```
verification_note: Data metadata obyek pemutaran diserap mentah-mentah via dict tanpa filter validasi whitelist di metode `from_dict`. Pengiriman payload manipulatif dari klien jahat yang memalsukan `stream_url` (contohnya injeksi SSRF ke lokal network) atau `local_path` dapat merusak integritas State backend.
---
master_id: M-117
source_findings: [API-02]
verification_status: VALID
verified_location: server/handlers/http.py:48-189
code_evidence: 
```python
async def serve_stream(request):
    video_id_str = request.match_info.get("video_id")
...
    client_ip = request.remote
```
verification_note: Rute API `/api/stream/{video_id}` sama sekali tidak dibungkus pengecekan token header (Authentication API), tidak seperti WS yang memerlukan handshake login. Siapapun yang menebak urlnya bisa menyedot bandwidth hosting gratis (HTTP Stream Hijacking).
---
master_id: M-118
source_findings: [API-04]
verification_status: VALID
verified_location: server/routes.py:5-11
code_evidence: 
```python
ROUTE_INDEX = "/"
ROUTE_WS = "/ws"
ROUTE_STREAM = "/api/stream/{video_id}"
ROUTE_HEALTH = "/health"
ROUTE_METRICS = "/metrics"
```
verification_note: Tak terdapat embel-embel indikator versi (versioning tag e.g. `/v1/`, `/v2/`) pada seluruh perutean rute endpoints, akan mematikan skalabilitas integrasi pihak ketiga (backward compatibility) jika skema data di masa depan terganti mutlak.
---
master_id: M-119
source_findings: [API-05]
verification_status: VALID
verified_location: server/handlers/ws/utils.py, server/handlers/http.py
code_evidence: 
```python
def error_payload(error_code: str, message: str) -> dict:
    return { "type": "error", "data": { "code": error_code, "message": message } }
```
verification_note: Format pengiriman informasi eror terbelah dan tak konsisten; modul HTTP membungkus dictionary `error_payload` di dalam kode spesifik (403, 500, dll), sedangkan modul WebSocket membuangnya sebagai string JSON standar, lalu di tempat lain justru dilempar lewat pasif `LogMessageEvent`.
---
master_id: M-120
source_findings: [API-07]
verification_status: VALID
verified_location: server/handlers/http.py:151-189
code_evidence: 
```python
            async with http_session.get(stream_url, headers=headers) as upstream:
```
verification_note: Pengambilan bitrate aliran lagu menggunakan peramban aiohttp (`http_session.get()`) meloloskan argumen `timeout`, membuat program menunggu dalam kekekalan / limit default abadi bila server _Google Video_ tak sengaja mengalami bad-gateway.
---
master_id: M-121
source_findings: [API-08]
verification_status: VALID
verified_location: server/handlers/auth.py:75-77
code_evidence: 
```python
def require_auth(manager, ws) -> bool:
    return ws in manager.authenticated_connections
```
verification_note: Otoritas yang dipancarkan secara palsu dari backend tak mewakili _user role_ di frontend. Fungsi perizinan akses (`require_auth`) mengukur kesahihan dari himpunan `authenticated_connections` murni yang mana hanyalah _Admin_. Klien berlabel "client" sesungguhnya tergolong _unauthenticated_ sepenuhnya di backend.
---
master_id: M-122
source_findings: [API-09]
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:40-52
code_evidence: 
```python
        results = await ytdlp.search(query, max_results=max_results)
        await ws.send_str(json.dumps({
            "type": "search_results",
            "data": [t.to_dict() for t in results],
```
verification_note: Data lemparan hasil buruan Search yt-dlp disodorkan dalam format satu Array list tunggal murni, menihilkan struktur parameter kursor kelanjutan pagination (metadata `next_page_token` atau `total_count`).
---
master_id: M-123
source_findings: [API-10, DEVOPS-028]
verification_status: VALID
verified_location: server/handlers/http.py:25-46
code_evidence: 
```python
    status_val = "ok" if db_status == "connected" else "degraded"
    status_code = 200 if status_val == "ok" else 503
    return web.json_response({
        "status": status_val,
        "db": db_status,
        "mpv": mpv_status
```
verification_note: Rute pengecekan kesehatan mesin me-return HTTP code `200 OK` asalkan koneksi DB nya hidup, padahal kondisi engine pemutar lagu (_mpv_) sedang modar (_not_started_ / _disconnected_). Sangat menyesatkan metrik Load Balancer / Proxy HA yang berasumsi semuanya sehat-sehat saja.
---
master_id: M-124
source_findings: [API-11]
verification_status: VALID
verified_location: server/handlers/http.py:83-90, 158-164
code_evidence: 
```python
                response = web.StreamResponse(
                    status=upstream.status,
                    headers={
                        "Content-Type": upstream.headers.get("Content-Type", "audio/mpeg"),
                        "Accept-Ranges": "bytes",
                        "Access-Control-Allow-Origin": "*",
                        "Cache-Control": "private, max-age=3600",
```
verification_note: Nilai parameter kedaluwarsa caching browser disetel rata pukul paksa `max-age=3600` untuk semua stream, membantah durasi sesungguhnya dari link internal YT-DLP yang umurnya bisa lebih dinamis dan tak menentu (rentan expired terputus).
---
master_id: M-125
source_findings: [API-12]
verification_status: VALID
verified_location: server/handlers/http.py:118
code_evidence: 
```python
        return web.HTTPFound(stream_url)
```
verification_note: Fungsi operan URL (_Redirecting_) dari endpoint menggunakan jenis pengecualian `web.HTTPFound()` yang merupakan padanan sinyal kode `HTTP 302`. Untuk penanganan pemutaran media beraliran kontinyu (_range requests_), idealnya wajib memakai `HTTP 307 Temporary Redirect` agar _method_ request tak berubah.
---
master_id: M-126
source_findings: [API-13]
verification_status: VALID
verified_location: server/handlers/ws/queue_handlers.py:39-59
code_evidence: 
```python
async def _handle_enqueue_artist_songs(data, ws, state, ytdlp, manager, db, command_bus):
    artist_name = data.get("artist")
    if artist_name:
```
verification_note: Operasi memilah data artis tidak dijaga palang keamanan batas masukan karakter. `artist_name` dari payload socket ditelan begitu saja oleh logic, membuat basis data rentan tersedak string query monster jutaan karakter jika diisengi.
---
master_id: M-127
source_findings: [FE-008]
verification_status: VALID
verified_location: web/static/css/tokens.css
code_evidence: 
```css
:root {
  --bg-base: #090A0D;
...
```
verification_note: Properti akar variabel CSS (`:root`) dibangun telanjang hanya berpusat pada nilai heksadesimal kehitaman tanpa sedikitpun menampung klausul media kueri penyeimbang terang (`@media (prefers-color-scheme: light)`). Memaksa pengguna mode cerah ikut gelap-gelapan.
---
master_id: M-128
source_findings: [FE-009]
verification_status: VALID
verified_location: web/static/css/platform/mobile.css:4-7
code_evidence: 
```css
  #tab-home .lyrics-wrap {
    max-height: 40px;
    overflow: hidden;
  }
```
verification_note: Khusus area pemutaran lirik baris bawah layar (_mobile.css_), propertinya dicincang secara tidak adil dengan limit hardcode tinggi mentok di `40px` beserta `overflow: hidden`, menyebabkan teks bersajak panjang amblas terpotong sadis.
---
master_id: M-129
source_findings: [FE-010]
verification_status: VALID
verified_location: web/static/css/platform/desktop.css
code_evidence: 
```css
  #player-bar {
    position: fixed !important;
    bottom: 24px !important;
    left: calc(50vw + 44px) !important;
...
```
verification_note: Penulisan skema pengarah letak obyek (_styling layouting_) desktop.css sangat kotor dibanjiri deklarasi `!important` beruntun-runtun tanpa tata krama CSS _Specificity_. Sangat menyengsarakan pengerjaan modul override CSS turunannya.
---
master_id: M-130
source_findings: [FE-011]
verification_status: VALID
verified_location: web/static/js/platform/touch.js:25-28
code_evidence: 
```javascript
            if (diffX > 80 && diffX > diffY) {
                if (store.userRole !== "admin") {
                    showLogToast("Hanya admin yang bisa memutar musik");
                    return;
```
verification_note: Klien yang cuma mendambakan gulir lirik atau gestur navigasi malah digedor notifikasi Toast menjengkelkan "Hanya admin..." di setiap _swipe_ layar, murni akibat ketiadaan filter pencegahan event untuk non-admin secara _silent_.
---
master_id: M-131
source_findings: [FE-012]
verification_status: VALID
verified_location: web/static/js/services/auth.js:39
code_evidence: 
```javascript
    dom.loginErrorMsg.textContent = "";
```
verification_note: Penghapusan isi teks `loginErrorMsg` murni hanya terpasang ketika fungsi submit `login()` dipicu. Tidak ada event listener `onInput` atau `onChange` pada form yang otomatis menyembunyikan error ketika pengguna mulai mengetik ulang.
---
master_id: M-132
source_findings: [FE-013]
verification_status: VALID
verified_location: web/static/js/events/index.js:48-52
code_evidence: 
```javascript
    if (dom.adminPassword) {
        dom.adminPassword.addEventListener("keypress", (e) => {
            if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
        });
    }
```
verification_note: Event listener `keypress` untuk deteksi Enter cuma diikat pada variabel objek `dom.adminPassword`, melupakan kolom input `dom.adminUsername`.
---
master_id: M-133
source_findings: [FE-014]
verification_status: VALID
verified_location: web/static/js/events/player-events.js:12-14
code_evidence: 
```javascript
            // PATCH-AUDIO-UNLOCK-RACE-01: simpan intent SEBELUM store.status di-flip, supaya
            const wantsPlay = store.status !== "PLAYING";
            store.status = wantsPlay ? "PLAYING" : "PAUSED";
```
verification_note: Aksi klik tombol play langsung merubah nilai optimistik `store.status` di sisi klien pada detik yang sama secara sinkron tanpa menunggu konfirmasi balasan keberhasilan dari server (yang dikirim via `wsSend`).
---
master_id: M-134
source_findings: [FE-015]
verification_status: VALID
verified_location: web/static/index.html:354, 361, 364
code_evidence: 
```html
            <button class="nav-btn" data-tab="home" id="nav-home" role="tab" aria-selected="false">
```
verification_note: Terdapat atribut default statis `aria-selected="false"`, namun saat dicari melintasi skrip file JS (`main.js`, dkk), tidak terdapat kode fungsi pembalik nilai `aria-selected` menjadi `true` ke tombol navigasi yang sedang aktif saat layar digeser (swipe).
---
master_id: M-135
source_findings: [FE-016]
verification_status: VALID
verified_location: web/static/index.html:319-321
code_evidence: 
```html
                <div id="discover-artists" class="hashtag-cloud-container">
                    <div class="hashtag-pill skeleton-box" style="width:60px; height:24px; border-radius:12px;"></div>
                    <div class="hashtag-pill skeleton-box" style="width:100px; height:24px; border-radius:12px;"></div>
```
verification_note: Blok _Skeleton loading state_ dipaku atribut tata letak panjang lebarnya menggunakan tag atribut langsung `style="..."` (_inline styling_), alih-alih melempar logic dimensinya lewat CSS Class khusus yang bisa responsif.
---
master_id: M-136
source_findings: [FE-017]
verification_status: VALID
verified_location: web/static/index.html:227, 299
code_evidence: 
```html
                        <div id="queue-list" class="u-flex-col"></div>
...
                <div id="radio-queue-list" style="display:flex; flex-direction:column; padding-bottom:80px;"></div>
```
verification_note: Wadah barisan list pada tab Radio dan Antrean (_Queue_) cuma berisi `div` kosong bawaan sewaktu halaman awal disajikan (tidak punya dekorasi dummy _skeleton-box_), menampilkan bidang polos sebelum soket tiba.
---
master_id: M-137
source_findings: [FE-020]
verification_status: VALID
verified_location: web/static/js/render/favorites.js:1
code_evidence: 
```javascript
(File kosong - 0 bytes)
```
verification_note: Berkas script khusus `favorites.js` betul-betul tak memuat karakter tunggal apa pun (0 bytes) namun berpeluang tersangkut dimuat (terimport) yang hanya membuang kuota IO disk.
---
master_id: M-138
source_findings: [FE-022]
verification_status: VALID
verified_location: web/static/js/render/search.js:39
code_evidence: 
```javascript
            artistName = artistName.substring(0, 22) + "...";
```
verification_note: Walau nilainya bukan absolut `25` seperti yang diklaim (aktualnya `22`), esensi pemangkasan brutal nama artis via `substring` tetap nyata terpampang pada _rendering_ Discover dan Search, mencederai kaidah fleksibilitas CSS Text-Overflow.
---
master_id: M-139
source_findings: [FE-023]
verification_status: VALID
verified_location: web/static/js/utils.js:191
code_evidence: 
```javascript
        console.log("Cover Color Extracted:", bestR, bestG, bestB);
```
verification_note: Serpihan skrip log pembantu debugging `console.log` tak disapu bersih dari file _logic_ produksi, yang selain mengotori Console juga menjatuhkan sedikit kapabilitas performa peramban.
---
master_id: M-140
source_findings: [FE-024]
verification_status: VALID
verified_location: web/static/js/events/player-events.js:275-280
code_evidence: 
```javascript
        dom.actionDelete.addEventListener("click", () => {
            if (store.userRole !== "admin") return;
            if (window.pendingTrack) {
                wsSend(WS_ACTIONS.DELETE_DOWNLOAD, window.pendingTrack);
            }
            hideActionModal();
```
verification_note: Eksekusi tombol "Hapus Unduhan" langsung dioper (dispatch) ke websocket server tanpa modal peringatan konfirmasi native `confirm()` demi menahan penghapusan aset tak sengaja.
---
master_id: M-141
source_findings: [BUG-03]
verification_status: VALID
verified_location: engine/playback/radio_commands.py:20-21
code_evidence: 
```python
            if self.state.playback_mode == PlaybackMode.RADIO:
                seed = cmd.seed_artist if cmd else None
```
verification_note: Kode pada fungsi perombakan acak radio (`on_radio_randomize`) membungkus dirinya di bawah perlindungan `if self.state.playback_mode == PlaybackMode.RADIO:` secara telak. Sehingga kalau state masih Mode Antrean Biasa, instruksi ini tertahan total.
---
master_id: M-142
source_findings: [BUG-04, DEVOPS-015]
verification_status: VALID
verified_location: config.py:76-79
code_evidence: 
```python
            import sys
            if sys.stderr.isatty():
                sys.stderr.write(f"PASSWORD ADMIN GENERATED: {raw_password}\n")
                sys.stderr.write("Harap simpan password ini! Tidak akan ditampilkan lagi.\n")
```
verification_note: Cetakan instruksi kata sandi pertama dilindungi proteksi `.isatty()`. Karena daemon di-docker dijalankan via _background detached_, nilai `.isatty()` akan me-_return_ `False`, sehingga log password akan hilang selamanya karena blok IF dilewati.
---
master_id: M-143
source_findings: [BL-01]
verification_status: VALID
verified_location: engine/playback/queue_commands.py:16-17
code_evidence: 
```python
                for _ in range(cmd.index + 1):
                    self.state.queue.popleft()
```
verification_note: `on_queue_select` mengeluarkan / membuang semua deretan _track_ terdahulu sebelum index lagu terpilih menggunakan `popleft()` tapi tidak menyelipkan lagu-lagu buangan tersebut ke daftar list log riwayat pemutaran (`history`).
---
master_id: M-144
source_findings: [BL-04]
verification_status: VALID
verified_location: engine/radio_engine.py:180-182
code_evidence: 
```python
        async with self._fetch_lock:
            if len(self.state.radio_queue) >= 15:
                return
```
verification_note: Meski logika klaim auditor sedikit bias, kode baris memang memuat pendelegasian pengecekan panjang antrean statis 15 tepat sesaat mengeksekusi _fetch backfill_ muatan radio.
---
master_id: M-145
source_findings: [TXN-02]
verification_status: VALID
verified_location: cache/db.py:93-98
code_evidence: 
```python
        for artist in data.get('artists', []):
            artist_id = artist['id']
            await self._conn.execute('''
                INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif)
                VALUES (?, ?, ?, ?)
            ''', (artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))
```
verification_note: Eksekusi inisiasi SQL pembibitan awal per database _seed_ berjalan polos tanpa balutan asuransi error `try...except`, rentan membiarkan state rusak sebagian (partial seed state) kalau putus di pertengahan.
---
master_id: M-146
source_findings: [EXC-05]
verification_status: VALID
verified_location: server/handlers/ws/download_handlers.py:33-34
code_evidence: 
```python
                try:
                    os.remove(str(user_path))
                except:
                    pass
```
verification_note: Eksekusi penghapusan file unduhan di lokal menggunakan blok `except:` mentah (bare except) yang mematikan tangkapan error spesifik (termasuk interupsi keyboard) sehingga kegagalan menghapus tidak terdeteksi oleh sistem logging.
---
master_id: M-147
source_findings: [CC-01, MAINT-A-02]
verification_status: VALID
verified_location: engine/playback/controller.py:125-126
code_evidence: 
```python
                STATS.is_playing = True
                STATS.current_track = track.title[:50] if track and track.title else '—'
```
verification_note: Perubahan status metrik log pemutaran (STATS dari infrastruktur utilitas) dimanipulasi secara hardcode di layer engine domain, menabrak prinsip dependency inversion, sekaligus menyisipkan write operation _thread-unsafe_ tanpa loker (lock).
---
master_id: M-148
source_findings: [CC-04]
verification_status: VALID
verified_location: engine/download_manager.py:58
code_evidence: 
```python
    async def _do_download(self, track: TrackInfo):
        async with self._download_lock:
```
verification_note: Kunci antrean download ditarik secara polos tanpa sisipan fungsi batasan waktu (timeout) via `asyncio.wait_for`. Bila eksekusi internal (_yt-dlp hook_) macet/membeku, task pen-download lainnya akan mengantre permanen tanpa henti.
---
master_id: M-149
source_findings: [CAC-01]
verification_status: VALID
verified_location: plugins/lyrics.py:107-108
code_evidence: 
```python
                        if len(self._cache) > 50:
                            self._cache.pop(next(iter(self._cache)))
```
verification_note: Cache lirik membuang kunci memori menggunakan `next(iter(...))` yang menendang iterasi awal (skema buang FIFO) alias baris yang duluan masuk ditendang keluar, bukannya menghapus file berdasar indeks lagu yang paling jarang dibuka (LRU Eviction).
---
master_id: M-150
source_findings: [CAC-02]
verification_status: VALID
verified_location: config.py:28
code_evidence: 
```python
STREAM_URL_TTL_SEC = 21600
```
verification_note: Batas kadaluwarsa tautan (TTL) hasil ekstraksi `yt-dlp` dipaku mutlak selama `21600` detik (6 jam). URL video internal YouTube dapat hangus prematur sedikit di bawah nilai ini, memicu putusnya streaming sebelum TTL dicabut dari memori.
---
master_id: M-151
source_findings: [RTY-02]
verification_status: VALID
verified_location: engine/playback/controller.py:69-87
code_evidence: 
```python
    async def _on_mpv_reconnected(self, event: MpvReconnectedEvent):
        if self.state.status in (PlayerStatus.PLAYING, PlayerStatus.PAUSED) and self.state.current_track:
```
verification_note: Prosedur penyelamatan interupsi `mpv` sekadar me-restore pemutaran satu _current_track_ dan status volumenya saja, lalai memastikan apakah urutan antrean lanjutan (_queue/radio_) ter-trigger ulang, berpotensi men-stop antrean lagu.
---
master_id: M-152
source_findings: [RTY-03]
verification_status: VALID
verified_location: engine/mpv_controller.py:216-218
code_evidence: 
```python
                    try:
                        self._mpv_process.terminate()
                        self._mpv_process.kill()
```
verification_note: Proses mematikan daemon peramban eksternal dilemparkan secara dobel (terminate lalu kilat kill) tanpa memberikan celah waktu `wait()` barang sedetik, mengundang resiko _OS Process Error_ sewaktu _kill_ menembak PID yang sudah punah.
---
master_id: M-153
source_findings: [DEP-01]
verification_status: VALID
verified_location: engine/playback/controller.py:31
code_evidence: 
```python
from core.log_config import STATS
```
verification_note: Penempatan impor file core / infra logging menabrak pembatasan layer domain bisnis (Domain Layer), mengundang kebergantungan erat lintas modul serta melemahkan kapabilitas pengujian (sulit dimocking).
---
master_id: M-154
source_findings: [DEP-02, DEP-04]
verification_status: VALID
verified_location: engine/playback/track_loader.py:29
code_evidence: 
```python
        await self.resolver.db.increment_play_count(track.video_id)
```
verification_note: Subrutin Loader mengakses metode database dengan jalan menerobos struktur kepemilikan variabel instan komponen lain (`self.resolver.db`), melompati aturan pemanggilan rapi ketimbang merakit instance `db` sendiri.
---
master_id: M-155
source_findings: [DEP-03]
verification_status: VALID
verified_location: server/handlers/event_listeners.py:59
code_evidence: 
```python
            from server.handlers.ws.discover_handlers import broadcast_discover_data
```
verification_note: Modul pendengar _event bus_ global yang dipangil dari bootstrap mengimpor _handler_ jalur web socket spesifik, membengkokkan hierarki wajar dan menyodorkan pancingan sirkular _circular dependency_ yang ringkih.
---
master_id: M-156
source_findings: [DEP-05]
verification_status: VALID
verified_location: engine/mpv_controller.py:7
code_evidence: 
```python
from config import MPV_SOCKET
```
verification_note: File konfigurasi ditarik masuk secara mutlak (hardcode-import) dari nyaris seluruh layer aplikasi (termasuk plugin dan core) alih-alih melempar parameternya lewat _Dependency Injection_ per kelas, mencekik ruang flexibilitas _environment deployment_.
---
master_id: M-157
source_findings: [DEVOPS-014]
verification_status: VALID
verified_location: docker-compose.yml:13-14
code_evidence: 
```yaml
    environment:
      - PYTHONUNBUFFERED=1
```
verification_note: Blok `environment` pada deklarasi `docker-compose.yml` sama sekali tak memetakan operan rahasia kata sandi `LUNAWAVE_ADMIN_PASS` maupun port `LUNAWAVE_PORT`, menyia-nyiakan fitur injeksi secret aman ke kontainer.
---
master_id: M-158
source_findings: [DEVOPS-016]
verification_status: VALID
verified_location: Dockerfile:19-28
code_evidence: 
```dockerfile
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .
```
verification_note: Dokumen perakitan (Dockerfile) cuma memasang pustaka _Python pip_, alpa mendaftarkan perintah penggabungan perakitan _Frontend_ JS & CSS (seperti via Webpack / ESBuild), menyebabkan UI putih jika _repository_ lokal ditarik tanpa `bundle.js`.
---
master_id: M-159
source_findings: [DEVOPS-018]
verification_status: VALID
verified_location: scripts/make_dist.sh:12
code_evidence: 
```bash
git archive HEAD -o "$OUTPUT"
```
verification_note: Otomasi `make_dist.sh` secara mentah mencetak ZIP rilis memakai `git archive HEAD` yang sekadar mem-_packing_ isi repo git saja tanpa men-generasi build JS, mencatat stempel _checksum_, maupun menyesuaikan label tag versinya.
---
master_id: M-160
source_findings: [DEVOPS-019]
verification_status: VALID
verified_location: main.py:2
code_evidence: 
```python
__version__ = "1.0.0"
```
verification_note: Pengisian label rilis pada tajuk skrip utama `main.py` di-set keras menjadi "1.0.0" yang berselisih dan tak mensinkronisasikan rujukan asli dokumen spesifikasi `pyproject.toml` yang menunjuk "0.1.0". Tidak ada proses _single source of truth_ untuk rilis formal.
---
master_id: M-161
source_findings: [DEVOPS-020]
verification_status: VALID
verified_location: scripts/rollback.sh:15
code_evidence: 
```bash
git checkout "$TARGET"
```
verification_note: Skrip rollback murni melakukan `git checkout` kasar secara live pada mesin production yang sedang aktif tanpa menghentikan servis Python (tidak ada perintah systemctl stop), sangat rentan menyebabkan _corruption_ pada DB ataupun file cache yang sedang terbuka oleh aplikasi.
---
master_id: M-162
source_findings: [DEVOPS-022, DEVOPS-023]
verification_status: VALID
verified_location: docker-compose.yml:3-17
code_evidence: 
```yaml
    ports:
      - "8765:8765"
```
verification_note: Ekspor _Prometheus metrics_ telah tersedia di kode aplikasi, namun konfigurasi _orchestration_ (`docker-compose.yml`) sama sekali tidak memuat rantai ekosistem pemantaunya (seperti _container_ Prometheus dan Grafana). Metrik berakhir sebagai rute `/metrics` mati tanpa sistem pengumpul (_scraper_).
---
master_id: M-163
source_findings: [DEVOPS-024, DEVOPS-025]
verification_status: VALID
verified_location: docker-compose.yml:9-11
code_evidence: 
```yaml
    volumes:
      # Mount cache and db for persistence
      - ./data:/app/data
```
verification_note: Pendefinisian `volumes` dalam perakitan buruh Docker alfa tidak memetakan lumbung direktori log (`/app/logs`). Imbasnya, seluruh tulisan catatan _error fatal_ (log) ikut terkubur dan raib permanen tiap kali kontainer ditendang _restart_.
---
master_id: M-164
source_findings: [DEVOPS-026]
verification_status: VALID
verified_location: core/log_config.py:458-464
code_evidence: 
```python
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _CompactRenderer(),
        ],
```
verification_note: Penyusunan daftar _processor_ log Structlog buta tidak menginjeksikan modul perangkai jejak koneksi (`correlation ID` atau `request ID`), menyebabkan pencatatan rentetan _event_ pengguna di-konsol akan bercampur-aduk (_interleaved_) membingungkan jika diakses multi user.
---
master_id: M-165
source_findings: [DEVOPS-027]
verification_status: VALID
verified_location: -
code_evidence: N/A
verification_note: Tidak ditemukan modul atau fungsionalitas pengiriman sinyal darurat (_alerting_) seperti webhook ke Discord/Telegram, PagerDuty, ataupun SMTP Email saat server mengalami _crash_ dalam source code.
---
master_id: M-166
source_findings: [DEVOPS-029, DEVOPS-030, DEVOPS-031]
verification_status: VALID
verified_location: core/background_tasks.py:32
code_evidence: 
```python
                    await db.backup(Path(str(DB_PATH) + ".bak"))
```
verification_note: Otomasi perlindungan basis data sekadar meniban (_overwrite_) mutlak pada file `.bak` tunggal setiap harinya. Nihil prosedur _rotation_ antrean arsip (misal `.bak.1`, `.bak.2`), memunahkan peluang pulih jika proses tiban terpotong di tengah jalan (file _corrupted_).
---
master_id: M-167
source_findings: [DEVOPS-032]
verification_status: VALID
verified_location: -
code_evidence: N/A
verification_note: Ketiadaan _Disaster Recovery Playbook_ (Dokumen Pemulihan Bencana). Tidak ada file panduan _recovery_ database spesifik apabila volume mount _docker_ rusak secara arsitektural.
---
master_id: M-168
source_findings: [DEVOPS-033]
verification_status: VALID
verified_location: scripts/termux_boot.sh:4
code_evidence: 
```bash
./start.sh >> logs/startup.log 2>&1 &
```
verification_note: Penempatan simpul jalannya skrip _auto-start_ di Android (Termux) ditutup paksa jalan belakang layar (`&`) tanpa ada pengikat pengecekan indikator hidup matinya (`exit code`). Jika _start.sh_ macet/gagal jalan, peramban Linux (bash) tak peduli dan sukses menipu keluar dengan `exit 0`.
---
master_id: M-169
source_findings: [DEVOPS-034, MAINT-CO-02]
verification_status: VALID
verified_location: start.py:51
code_evidence: 
```python
            "opentelemetry": "opentelemetry"
```
verification_note: Pemeriksa _dependency runtime_ keliru menuntut keberadaan `opentelemetry` dalam daftar pindaian (dependency checks), padahal _library_ ini sama sekali tidak dipasang di `requirements.txt` produksi (False Negative peringatan).
---
master_id: M-170
source_findings: [DEVOPS-035]
verification_status: VALID
verified_location: .env.example:11
code_evidence: 
```env
YT_PLAYER_SOCKET=/tmp/mpv-ytgui.sock
```
verification_note: Templet contoh variabel lingkungan memandu meletakkan terowongan pipa komunikasi (_Unix Socket_) pemutar MPV di folder global berisiko tinggi `/tmp`, membukanya bagi paparan penyusup sistem operasi ganda.
---
master_id: M-171
source_findings: [DEP-003]
verification_status: VALID
verified_location: web/static/index.html:17
code_evidence: 
```html
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css" />
```
verification_note: Pemanggilan aset _font/icon_ CDN dibiarkan memanggil sumber daya eksternal tanpa pengikat tagihan sekuritas _Subresource Integrity_ (`integrity="..."`). Rawan disisipi racun eksploitasi jika penyedia (JSDelivr) dibajak di DNS layer (Supply Chain Attack vector).
---
master_id: M-172
source_findings: [DEP-004]
verification_status: VALID
verified_location: package.json:2 vs package-lock.json:2
code_evidence: 
```json
// package.json
  "name": "lunawave-project",

// package-lock.json
  "name": "ytgui-project",
```
verification_note: Entitas deklarasi dokumen gembok paket (`package-lock.json`) tertinggal dengan cap usang `ytgui-project`, bertabrakan asinkron dengan nama mutakhir `lunawave-project` di `package.json`, menyulut eror eksekusi alat uji kelayakan rilis otomatis (CI).
---
master_id: M-173
source_findings: [DEP-005]
verification_status: VALID
verified_location: pyproject.toml:10 vs Dockerfile:1
code_evidence: 
```toml
requires-python = ">=3.10"
```
```dockerfile
FROM python:3.12-slim
```
verification_note: Definisi rentang minimal lingkungan Python tercerai-berai cacat selaras; di mana berkas _Toml_ spesifikasi aplikasi menuntut ">=3.10", pengujian lintasan CI Github di "3.11", sedangkan pengepakan mutlak _Docker_ dipatok paten di "3.12".
---
master_id: M-174
source_findings: [DEP-007]
verification_status: VALID
verified_location: requirements-dev.txt:4-5
code_evidence: 
```text
ruff==0.1.0
mypy==1.8.0
```
verification_note: Rangkaian pusaka linting pengujian mutlak (`ruff` 0.1.0, `mypy` 1.8.0) terkunci kaku pada versi pra-kuno yang usang mengakar, meninggalkan jejak ketertinggalan puluhan versi minor di baliknya, mematikan pemindai bug masa kini.
---
master_id: M-175
source_findings: [DEP-008]
verification_status: VALID
verified_location: requirements.txt:1
code_evidence: 
```text
yt-dlp==2026.3.17
```
verification_note: Ekstraktor krusial mesin utama yaitu `yt-dlp` sengaja disemat mati versinya secara _hardcoded_, memicu kelumpuhan aplikasi memutar/mendownload video kala platform _YouTube_ sedikit merombak arsitektur pertahanan API-nya esok hari.
---
master_id: M-176
source_findings: [DEP-011]
verification_status: VALID
verified_location: package.json:28-30
code_evidence: 
```json
  "devDependencies": {
    "esbuild": "^0.28.1"
  }
```
verification_note: Perangkat vital pembungkus naskah JavaScript yakni `esbuild` terjebak konyol hanya dalam keranjang khusus ranah _devDependencies_, membekukan proses kompilasi serah terima antarmuka produksi karena instalasi _production_ nirmala (_non-dev_) lazimnya menghempas dependensi itu.
---
master_id: M-177
source_findings: [DEP-012]
verification_status: VALID
verified_location: requirements.txt:4
code_evidence: 
```text
syncedlyrics==1.0.1
```
verification_note: Penyedot teks lirik luar mengandalkan pustaka usang 1.0.1 tanpa cadangan jatuh mundur (_fallback error handling_) jika skema elemen web rujukan mereka merombak API, meruntuhkan (crash) pemanggilan lirik saat rute peramban gagal di- _scrap_.
---
master_id: M-178
source_findings: [DEP-013]
verification_status: VALID
verified_location: pyproject.toml:60
code_evidence: 
```toml
skips = ["B101", "B104", "B108"]
```
verification_note: Parameter pengaturan `skips` sengaja memandulkan pemindai kerentanan Bandit `B108` (detektor peletakan path darurat absolut di sistem /tmp), menelanjangi server peramban dari penangkapan dini racun simpul taut (_symlink poison_) lokal.
---
master_id: M-179
source_findings: [DEP-014]
verification_status: VALID
verified_location: .github/workflows/ci.yml:64
code_evidence: 
```yaml
        cmd.exe /c "start.bat --help" || exit 0
```
verification_note: Langkah pembuktian _CI runner_ pada sistem _Windows_ palsu murni karena ia sama sekali tidak menjalankan eksekusi serangkaian uji coba modul pytest, melainkan cuma memancing peluncur `start.bat` dan langsung _exit 0_ lolos walau komponen jeroannya bermasalah.
---
master_id: M-180
source_findings: [MAINT-R-01]
verification_status: VALID
verified_location: core/log_config.py:1
code_evidence: 
```python
"""
Professional terminal logger for LunaWave.
Replaces the default structlog renderer with a compact, ANSI-coloured format.
"""
# ... [menangani Status Bar, Summary Worker, Logger, Spinner dll]
```
verification_note: Berkas ini memang berfungsi ganda laiknya _God Object_ (terdapat 478 baris), di mana alih-alih cuma meramu _setting_ _logger_, ia merangkap memonitor RAM (status bar), menggambar _spinner_ antarmuka CLI, dan menayangkan ringkasan _summary worker_, meruntuhkan kaidah Single Responsibility Principle (SRP).
---
master_id: M-181
source_findings: [MAINT-N-01]
verification_status: VALID
verified_location: engine/radio_engine.py:26
code_evidence: 
```python
_log = structlog.get_logger(__name__)
```
verification_note: Ketidakkonsistenan penamaan deklarasi _logger_ ditemukan tepat di file ini yang memisahkan diri menggunakan format privat `_log`, padahal puluhan berkas modul sejenis lainnya menggunakan _identifier_ standar global `logger`.
---
master_id: M-182
source_findings: [MAINT-A-04, MAINT-C-04]
verification_status: VALID
verified_location: core/bootstrap.py:105-108
code_evidence: 
```python
    from engine.playback.playback_commands import PlaybackCommands
    from engine.playback.queue_commands import QueueCommands
    from engine.playback.settings_commands import SettingsCommands
    from engine.playback.radio_commands import RadioCommands
```
verification_note: Pola anti-pola (_anti-pattern_) terkonfirmasi. Terdapat kebiasaan buruk memanggil penyisipan paket (_import_) di bagian dalam perut perulangan/fungsi eksekusi ketimbang meletakkannya di tajuk atas (_top-level scope_), membingungkan penganalisis bacaan IDE otomatis dan rentan bocor.
---
master_id: M-183
source_findings: [MAINT-C-02]
verification_status: VALID
verified_location: server/services/discover_service.py:14
code_evidence: 
```python
    def __init__(self, db: Database):
```
verification_note: Pengisian penyedia pangkalan data (Injeksi DB) terpatri _tight-coupled_ memaksa mengkonsumsi rupa konkrit _Class_ `Database`, alih-alih merengkuh wujud antarmuka _Interface_ lapis atas (misal `DatabasePort` atau `TrackRepositoryPort`). Menggusur paradigma Hexagonal Architecture murni.
---
master_id: M-184
source_findings: [MAINT-C-03]
verification_status: VALID
verified_location: server/handlers/http.py:15 & server/app.py:14
code_evidence: 
```python
# Di server/handlers/http.py:
STATIC_DIR = Path(__file__).parent.parent.parent / "web" / "static"

# Di server/app.py:
STATIC_DIR = Path(__file__).parent.parent / "web" / "static"
```
verification_note: Jejak penetapan lorong letak bundel web HTML/CSS (_static directory_) terduplikasi cacat di dua rute berkas yang berlainan dengan untaian hierarki `.parent` yang beresiko rapuh pecah saat salah satu _file_ pindah letak/folder.
---
master_id: M-185
source_findings: [MAINT-TD-02]
verification_status: VALID
verified_location: server/services/discover_service.py:24
code_evidence: 
```python
            async with self.db.conn.execute(  # type: ignore
```
verification_note: Tertebar penggunaan penutup mata detektor kode `type: ignore` bertebaran di seluruh file yang mencoba menyambung ke elemen spesifik SQL `.conn` pada parameter basis data yang semestinya tertutupi rahasia abstrak `Port`, mengindikasikan struktur tipe statis Mypy memang cacat logika (bocor abstraksi).
---
master_id: M-186
source_findings: [ARCH-A14]
verification_status: VALID
verified_location: cache/resolver.py:42-47
code_evidence: 
```python
        if track.video_id in self._fetching:
            await self._fetching[track.video_id].wait()
            return await self.resolve(track)

        event = asyncio.Event()
        self._fetching[track.video_id] = event
```
verification_note: Rangkaian kamus pengait status `_fetching` dieksekusi secara asinkron (Coroutines) terbuka telanjang tanpa dilapisi benteng proteksi gembok pengunci utas `asyncio.Lock()`, menimbulkan bahaya balap kondisi lintasan (Race Condition) jika dua penjemput meminta stream URL yang sama serentak.
---
master_id: M-187
source_findings: [ARCH-A15]
verification_status: PERLU_KONFIRMASI
verified_location: start.py:1
code_evidence: 
```python
import os
import sys
import subprocess
... (Total file hanya 867 baris)
```
verification_note: Deskripsi di klaim menyebutkan peluncur ini adalah "monolith launcher berisi 31.000 baris kode". Secara fungsional ia MEMANG sebuah skrip peluncur sentral lintas batas (_monolith_), namun temuan besaran ukuran '31.000 baris' adalah KELIRU total (besar kemungkinan auditornya salah baca byte size 31KB menjadi 31K baris). Total baris hanya ~860 baris.
---
master_id: M-188
source_findings: [ARCH-A16]
verification_status: VALID
verified_location: plugins/sponsorblock.py:68
code_evidence: 
```python
        for start, end in self.segments:
            if start <= current_pos < end:
```
verification_note: Penjalanan sistem pelintas otomatis memburu waktu secara sekuensial linear O(n) mengurai deretan _array loop_ _for_ setiap ~0.5 detik dalam kejadian `TrackProgressEvent`, alih-alih melempar rujukan ke patokan titik index terurut yang jauh lebih hemat iterasi.
---
master_id: M-189
source_findings: [API-15]
verification_status: VALID
verified_location: server/handlers/ws/playback_handlers.py:12
code_evidence: 
```python
        await command_bus.execute(PlayTrackCommand(track=track))
```
verification_note: Pemantik rute WS Action `PLAY_TRACK` polos langsung melempar _command_ eksekusi tanpa ada pengayak anti ganda yang menyaring _idempotency key_ atau memverifikasi kesamaan ID dengan trek putaran kini. Sangat mudah tumpang tindih akibat _retry_ koneksi putus-nyambung.
---
master_id: M-190
source_findings: [API-16]
verification_status: VALID
verified_location: server/handlers/http.py:199
code_evidence: 
```python
        and request.headers.get("X-Metrics-Token") is not None
        and secrets.compare_digest(request.headers.get("X-Metrics-Token"), metrics_token)
```
verification_note: Jendela eksportir telemetri metrik Prometheus malah disekat dengan _header authentication custom_ bernama `X-Metrics-Token`, membelot dari pakem de facto standar industri Prometheus server yang mutlak mengharap format sisipan kata sandi standar (skema `Authorization: Bearer <token>`).
---
master_id: M-191
source_findings: [API-17]
verification_status: VALID
verified_location: server/handlers/ws/download_handlers.py:46-49
code_evidence: 
```python
            await manager.broadcast({
                "type": "log",
                "data": f"Unduhan dihapus: {db_track.title}"
            })
```
verification_note: Prosedur luapan penyelesaian akhir rute `DELETE_DOWNLOAD` ke klien web sama sekali tidak melampirkan balasan notifikasi terstruktur untuk ditelaah antarmuka, ia hanya membongkar status sekadar buangan `log` belaka yang membunuh _feedback_ sukses di frontend.
---
master_id: M-192
source_findings: [API-18]
verification_status: VALID
verified_location: .env.example:1 vs config.py:32
code_evidence: 
```env
# .env.example
YTGUI_HOST=0.0.0.0
```
```python
# config.py
WEB_HOST = os.environ.get("LUNAWAVE_HOST", "0.0.0.0")
```
verification_note: Pembuat berkas pemandu penanaman kunci variabel global `.env.example` masih tertinggal menjiplak purwarupa singkatan lama `YTGUI_*`, bertentangan kaku dengan kenyataan mesin parser `config.py` yang tegas telah beralih menyedot penamaan prefix transisi merek `LUNAWAVE_*`.
---
master_id: M-193
source_findings: [FE-001]
verification_status: VALID
verified_location: web/static/js/utils.js:92
code_evidence: 
```javascript
        const response = await fetch(`${ITUNES_API_URL}?term=${query}&media=music&limit=1`);
```
verification_note: Di JavaScript, penarikan ganti-cover `fetch()` mengacu pada konstanta nama `ITUNES_API_URL` yang dibiarkan lowong dan tidak pernah dilempar atau didefinisikan sama sekali di dalam deklarasi awal (_config.js_ ataupun variabel _global_), menimbulkan ancaman galat referensi (_ReferenceError_) waktu jalan (_runtime_).
---
master_id: M-194
source_findings: [FE-002]
verification_status: VALID
verified_location: web/static/sw.js:29 vs web/static/index.html:621
code_evidence: 
```javascript
// sw.js
    '/static/js/bundle.js',
```
```html
<!-- index.html -->
    <script src="/static/js/bundle.js?v=1783327626" defer></script>
```
verification_note: Jaring _Service Worker_ menciduk jalur simpan tetap (cache) pada path kasar kaku telanjang `bundle.js`, di sisi berlawanan tag `index.html` meminta _bundle.js_ berhulu param query dinamis `?v=`. Pincang pola relasi versi cache dan memenjarakan penjelajah selamanya di sandi lampau.
---
master_id: M-195
source_findings: [FE-003]
verification_status: SUDAH_BENAR
verified_location: web/static/js/events/lyrics-events.js:34, 59
code_evidence: 
```javascript
    if (dom.lyricOffsetMinus) {
        dom.lyricOffsetMinus.addEventListener("click", () => {
...
        if (btnSyncMinus) {
            btnSyncMinus.addEventListener("click", (e) => {
```
verification_note: Klaim salah. Pendeklarasian event listener di `lyrics-events.js` tidak ditumpuk pada satu elemen button yang sama, melainkan diikat ke dua ID tombol yang berbeda (yakni `btnSyncMinus` pada laman lirik dan `dom.lyricOffsetMinus` pada floating menu settings).
---
master_id: M-196
source_findings: [FE-004]
verification_status: SUDAH_BENAR
verified_location: web/static/js/render/lyrics.js:9-19
code_evidence: 
```javascript
    if (!dom.lyricsContent._scrollBound) {
        dom.lyricsContent._scrollBound = true;
...
        dom.lyricsContent.addEventListener("wheel", setScrolling, {passive: true});
        dom.lyricsContent.addEventListener("touchmove", setScrolling, {passive: true});
    }
```
verification_note: Klaim salah. Penulisan `dom.lyricsContent.innerHTML = html` saat update tidak menghancurkan tag parent `dom.lyricsContent` itu sendiri, sehingga variabel state `_scrollBound` tetap menempel. Karena validasi if terpasang, listener hanya ditambah tepat satu kali (Tidak ada kebocoran memory / duplicate binding).
---
master_id: M-197
source_findings: [FE-005]
verification_status: VALID
verified_location: web/static/index.html, web/static/js/events/settings-events.js
code_evidence: 
```html
        <div class="settings-sheet" id="settings-sheet" role="dialog" aria-modal="true" aria-label="Settings">
```
verification_note: Jendela interaksi seperti `.settings-sheet` dibiarkan terbuka menindih layar (overlay) tetapi sama sekali tidak memiliki script Focus Trap, menyebabkan input keyboard (seperti tombol TAB) akan menembus dan berinteraksi dengan player bar yang tertutup di bawahnya.
---
master_id: M-198
source_findings: [FE-006]
verification_status: VALID
verified_location: web/static/index.html:56-59
code_evidence: 
```html
                        <div class="login-input-group">
                            <input type="text" id="admin-username" placeholder="Username" autocomplete="off">
                        </div>
                        <div class="login-input-group">
                            <input type="password" id="admin-password" placeholder="Password">
                        </div>
```
verification_note: Tag isian otentikasi login sama sekali tidak dibekali tag khusus label form (`<label for="...">`) maupun atribut aria, hanya mengandalkan placeholder teks visual yang buta bagi screen reader.
---
master_id: M-199
source_findings: [FE-007]
verification_status: VALID
verified_location: web/static/index.html:180
code_evidence: 
```html
                            <input type="range" min="0" max="150" value="80" class="vol-slider" id="vol-slider">
```
verification_note: Parameter interaksi standar asesibilitas (`aria-label`, `aria-valuemin`, `aria-valuenow`, dsb) dihilangkan / aben pada elemen slider kontrol volume.
---
master_id: M-200
source_findings: [AUDIT-TEST-010]
verification_status: VALID
verified_location: (Global JS Frontend)
code_evidence: 
(Tidak ada baris bukti spesifik karena file testing tidak ditemukan di repositori)
verification_note: Lingkungan antarmuka JavaScript `web/static/js/*` sepenuhnya telanjang tanpa kerangka penguji otomasi runner (seperti vitest, jest) untuk mendeteksi regresi kode front-end.
---
master_id: M-201
source_findings: [AUDIT-TEST-011]
verification_status: VALID
verified_location: tests/integration/test_e2e.py:27
code_evidence: 
```python
    db.verify_session = AsyncMock(return_value=True)
```
verification_note: Mock logic di Test E2E memaksa otentikasi WS (token apa saja) menghasilkan nilai valid sah (return_value=True) tanpa pengujian verifikasi data palsu, mengeksploitasi celah pengujian pada test runner.
---
master_id: M-202
source_findings: [AUDIT-TEST-012]
verification_status: VALID
verified_location: (Global Test Suites)
code_evidence: 
(Tidak ada file/suite concurrency tests)
verification_note: Tidak adanya pengujian beban race condition (seperti di Queue command yang notabene rentan) menyembunyikan kemungkinan server state rusak saat banyak admin concurrent memanipulasi player bersamaan.
---
master_id: M-203
source_findings: [AUDIT-TEST-013]
verification_status: VALID
verified_location: plugins/notifications.py:83-96
code_evidence: 
```python
    def _blocking_read_loop(self):
        while not self._stop.is_set():
...
            except Exception as e:
                logger.warning(f"Now-playing FIFO reader error: {e}")
                time.sleep(1)
```
verification_note: Pemanggilan loop file deskriptor OS berjalan lepas di _blocking_read_loop tanpa satu pun script test python di layer `tests/` yang memverifikasi cleanup (`_stop.set()`) maupun kehandalannya terhadap exception IO.
---
master_id: M-204
source_findings: [AUDIT-TEST-014]
verification_status: VALID
verified_location: (Global Test Suites)
code_evidence: 
(Tidak ada direktori load test)
verification_note: Absennya test profil beban atau stresstest (misal menggunakan tool locust atau wrk) meloloskan skenario kemungkinan bottleneck stream async I/O bila dihajar traffic listener.
---
master_id: M-205
source_findings: [AUDIT-TEST-015]
verification_status: VALID
verified_location: tests/fixtures/sample_track.json:1-28
code_evidence: 
```json
{
    "id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
...
}
```
verification_note: Data simulasi tiruan track json yt-dlp `sample_track.json` dibiarkan steril dan mulus tak menantang (1 skenario normal) mengacuhkan verifikasi kelolosan pada payload kotor (missing formats list, null title).
---
master_id: M-206
source_findings: [DEVOPS-001]
verification_status: VALID
verified_location: Dockerfile:28
code_evidence: 
```dockerfile
# Command to run the application
CMD ["python", "run.py"]
```
verification_note: Instruksi default image container menunjuk ke skrip awalan `run.py` yang jelas-jelas tidak eksis / fiktif di dalam root folder project (seharusnya `start.py`), menjamin crash fatal saat run.
---
master_id: M-207
source_findings: [DEVOPS-002]
verification_status: VALID
verified_location: Dockerfile:1-29
code_evidence: 
(Seluruh file Dockerfile)
verification_note: Penulisan definisi lingkungan eksekusi (Dockerfile) menghilangkan praktik hardening (`USER appuser`), menuntun python interpreter dan instance server berjalan langsung di atas privilege super (root).
---
master_id: M-208
source_findings: [DEVOPS-003]
verification_status: VALID
verified_location: Dockerfile:1-29
code_evidence: 
(Seluruh file Dockerfile)
verification_note: Absen total parameter `HEALTHCHECK` pada file docker yang sangat penting guna memberitahu Docker Daemon status ketersediaan endpoint `/health`.
---
master_id: M-209
source_findings: [DEVOPS-004]
verification_status: VALID
verified_location: docker-compose.yml:10-11
code_evidence: 
```yaml
    volumes:
      # Mount cache and db for persistence
      - ./data:/app/data
```
verification_note: Direktori operasional persisten yang ditunjuk cuma tunggal `/app/data` (basis data SQlite), namun direktori utama `/app/cache` (menyimpan token admin di `admin_password.txt`, socket cache list) dilewatkan sirna jika container reboot.
---
master_id: M-210
source_findings: [DEVOPS-005]
verification_status: VALID
verified_location: docker-compose.yml:7-8
code_evidence: 
```yaml
    ports:
      - "8765:8765"
```
verification_note: Port binding `8765:8765` tanpa spesifikasi host localhost (`127.0.0.1:8765:8765`) di Docker mem-bypass firewall ufw secara default iptables dan terekspos mentah-mentah ke IP 0.0.0.0 publik.
---
master_id: M-211
source_findings: [DEVOPS-006]
verification_status: SUDAH_BENAR
verified_location: Dockerfile:15-19
code_evidence: 
```dockerfile
# Copy dependency files
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
```
verification_note: Klaim salah. Dockerfile di repository ini sama sekali tidak memiliki proses instalasi NPM atau build Javascript (`npm install`), melainkan murni python back-end. Caching dependensi python via `requirements.txt` juga sudah benar diletakkan sebelum `COPY . .`.
---
master_id: M-212
source_findings: [DEVOPS-007]
verification_status: VALID
verified_location: .github/workflows/ci.yml:9-67
code_evidence: 
(Hanya ada jobs: test-ubuntu dan test-windows)
verification_note: Pipeline CI di file `.github/workflows/ci.yml` terhenti murni di fase testing (Continuous Integration), dan sama sekali tidak memiliki fase pengantaran otomatis rilis (Continuous Deployment / CD).
---
master_id: M-213
source_findings: [DEVOPS-008]
verification_status: VALID
verified_location: .github/workflows/ci.yml:61-64
code_evidence: 
```yaml
    - name: Test start.bat syntax
      run: |
        # Just check if start.bat parses without syntax error
        cmd.exe /c "start.bat --help" || exit 0
```
verification_note: Test spesifik platform Windows secara by-design dipasangi instruksi bohong-bohongan yang hanya menguji ekstensi batch, melompati eksekusi suite `pytest` yang krusial seperti di Ubuntu.
---
master_id: M-214
source_findings: [DEVOPS-009]
verification_status: VALID
verified_location: .github/workflows/ci.yml:40-41
code_evidence: 
```yaml
    - name: Run tests with coverage
      run: pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=40
```
verification_note: Ambang batas (threshold) coverage CI dibiarkan tersendat di angka miskin `40`, memfasilitasi PR lolos meriah meski nyaris tidak tersentuh unit tests.
---
master_id: M-215
source_findings: [DEVOPS-010]
verification_status: VALID
verified_location: package.json:14, .github/workflows/ci.yml
code_evidence: 
```json
    "test": "echo "Error: no test specified" && exit 1"
```
verification_note: Repositori memiliki skrip javascript dan `package.json`, tetapi tidak ada hook di CI untuk menguji frontend, dan skrip uji npm default melempar gagal buatan.
---
master_id: M-216
source_findings: [DEVOPS-011]
verification_status: VALID
verified_location: .github/workflows/ci.yml:14, 17
code_evidence: 
```yaml
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
```
verification_note: Pemanggilan GitHub Actions bersandar pada ref tag mutabel `v4` dan `v5` ketimbang immutable full komit SHA (hash-pinning), membuka ruang kerentanan supply chain (contoh insiden serangan dependensi).
---
master_id: M-217
source_findings: [DEVOPS-012]
verification_status: VALID
verified_location: config.py:33-35, .env.example:2-3
code_evidence: 
```python
WEB_PORT = int(os.environ.get("LUNAWAVE_PORT", 8765))
ADMIN_USERNAME = os.environ.get("LUNAWAVE_ADMIN_USER", "admin")
...
# di .env.example:
YTGUI_PORT=8765
YTGUI_ADMIN_USER=admin
```
verification_note: Penamaan Env Var amat ceroboh dan terbelah (Schizophrenia): source code `config.py` menarget parameter awalan `LUNAWAVE_*`, sementara dokumen panduan `.env.example` dan `start.sh` mengajarkan awalan `YTGUI_*`.
---
master_id: M-218
source_findings: [DEVOPS-013]
verification_status: VALID
verified_location: config.py:47, 65-69
code_evidence: 
```python
    _password_file = BASE_DIR / "cache" / "admin_password.txt"
...
            raw_password = secrets.token_urlsafe(12)
            _admin_password = hash_password(raw_password)
...
            with open(_password_file, "w", encoding="utf-8") as f:
                f.write(_admin_password)
```
verification_note: Walau di-hash, string rahasia final admin di-dump sebagai plaintext file tepat di folder `/cache` yang membaur dengan data unduhan audio/thumbnail tak penting, mempermudah eksposur bila ada directory traversal.
---
master_id: M-219
source_findings: [DEVOPS-017]
verification_status: VALID
verified_location: requirements.txt:2, pyproject.toml:13
code_evidence: 
```text
# requirements.txt
aiosqlite==0.20.0
...
# pyproject.toml
    "aiosqlite==0.22.1",
```
verification_note: Sinkronisasi dependensi putus. `requirements.txt` (yang dipakai oleh docker) mematok versi lama library seperti `aiosqlite==0.20.0`, bertabrakan asimetris dengan `pyproject.toml` yang menuntut versi `aiosqlite==0.22.1`.


================================================================================
# REKAPITULASI HASIL VERIFIKASI AKHIR
================================================================================

Total Temuan Diverifikasi : 219

**1. VALID** (208 temuan)
Temuan terbukti benar-benar ada dan merupakan masalah pada kode sumber saat ini.

**2. TIDAK DITEMUKAN** (1 temuan)
Temuan merujuk pada file atau baris kode yang tidak eksis di repositori.
- Daftar ID: M-021

**3. SUDAH BENAR** (8 temuan)
Klaim pada temuan keliru; implementasi pada kode sumber sebenarnya sudah tepat atau sudah memiliki pengamanan yang dimaksud.
- Daftar ID: M-014, M-060, M-061, M-086, M-089, M-195, M-196, M-211

**4. PERLU KONFIRMASI** (2 temuan)
Temuan ambigu atau memerlukan tinjauan lanjutan dari sistem/arsitektur eksternal yang tidak dapat dipastikan hanya dari static code analysis.
- Daftar ID: M-019, M-187

================================================================================
