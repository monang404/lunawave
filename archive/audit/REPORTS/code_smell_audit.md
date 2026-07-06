# Code Smell Audit — ytgui (bagas.fm)

Ruang lingkup: source code non-markdown. `.backup_patchlog/` diabaikan. Verifikasi unused import/variable dijalankan dengan `pyflakes` di seluruh source tree.

---

## CS-01 — God Class: `ServerManager(tk.Tk)`

**Lokasi:** `start.py`, baris 176–825 (~650 baris, 25+ method dalam 1 class)

**Alasan:** Satu class menangani: seluruh UI tkinter (build window, build UI, tombol, link), lifecycle server (`_on_start`, `_on_stop`, `_on_restart`), dependency checking, port conflict resolution (`_on_kill_conflict`), popup dialog kustom (`_show_server_ready_popup`, `_show_new_password_dialog`), dan reset password. Ini adalah definisi tekstual God Class — terlalu banyak alasan berbeda untuk class ini berubah (UI layout, logic proses, business logic password).

**Severity:** 🟠 High

**Cara Refactor:** Pisahkan menjadi beberapa class dengan tanggung jawab tunggal:
- `ServerProcessManager` (sudah ada, terpisah — pertahankan pola ini)
- `ServerManagerWindow` — hanya urus widget/layout (View)
- `ServerManagerController` — orkestrasi antara View dan `ServerProcessManager`/`DependencyChecker`
- `PasswordResetDialog`, `ServerReadyDialog` — extract jadi class dialog terpisah, bukan method di window utama.

---

## CS-02 — God Function / Long Method: `main()` di `main.py`

**Lokasi:** `main.py`, fungsi `main()` — ~180 baris, satu fungsi tunggal

**Alasan:** `main()` melakukan: init DB, init yt-dlp, connect mpv, buat http session, wiring 10+ dependency, start background task (connectivity checker, db cleanup, mpv reconnect checker — masing-masing didefinisikan sebagai nested closure di dalam `main()`), setup web server, cetak banner startup, dan cleanup shutdown. Terlalu banyak tanggung jawab bercampur dalam satu fungsi linear, sulit ditest secara terisolasi (tidak bisa unit-test "bagian wiring" tanpa menjalankan seluruh startup sequence).

**Severity:** 🟡 Medium

**Cara Refactor:** Ekstrak nested function jadi fungsi/class level module terpisah:
```python
# core/background_tasks.py
async def connectivity_checker(state, http_session): ...
async def db_cleanup_task(db): ...
async def mpv_reconnect_checker(mpv, state, resolver): ...

# core/bootstrap.py
async def build_app_context() -> AppContext:
    """Wiring semua dependency, return dataclass AppContext berisi semua komponen."""
    ...

# main.py — jadi tipis:
async def main():
    ctx = await build_app_context()
    tasks = start_background_tasks(ctx)
    try:
        await run_server(ctx.app, ...)
    finally:
        await shutdown(ctx, tasks)
```

---

## CS-03 — Large Class: `server/handlers/websocket.py` (30 fungsi dalam 1 file, ~377 baris)

**Lokasi:** `server/handlers/websocket.py`

**Alasan:** Satu file menampung `ConnectionManager`, `ws_handler`, dan **25 handler action berbeda** (`_handle_search`, `_handle_discover`, `_handle_toggle_favorite`, `_handle_play_track`, dst.) yang masing-masing mewakili fitur berbeda (search, discover, playback, queue, radio, download, settings). File ini akan terus tumbuh setiap kali fitur baru ditambahkan karena semua action WS wajib didaftarkan di sini.

**Severity:** 🟡 Medium

**Cara Refactor:** Pecah per domain fitur menjadi modul terpisah, didaftarkan lewat registry pattern:
```
server/handlers/ws/
    __init__.py          # import semua modul di bawah agar @register_ws_handler jalan
    playback_handlers.py # _handle_play_track, toggle_pause, next, prev, stop, seek
    queue_handlers.py    # queue_select, queue_add, queue_remove, queue_reorder
    radio_handlers.py    # radio_randomize
    discover_handlers.py # search, discover, toggle_favorite, enqueue_genre_songs
    download_handlers.py # download, delete_download
    settings_handlers.py # set_output, set_sponsorblock, lyrics_offset, volume_*
```

---

## CS-04 — Large Class: `engine/playback/controller.py` (`PlaybackController`, 24 method)

**Lokasi:** `engine/playback/controller.py`

**Alasan:** Sudah dibahas di audit arsitektur sebagai kandidat God Object — menangani play/pause/seek, queue mutation (add/remove/reorder/replace/select), mode switching (queue↔radio), output switching (device↔browser), sponsorblock toggle, dan lyrics offset — 8+ concern berbeda dalam satu class.

**Severity:** 🟠 High

**Cara Refactor:** Pecah menjadi beberapa command handler kecil per grup command (`PlaybackCommands`, `QueueCommands`, `SettingsCommands`), masing-masing menerima `state`+`bus`+`mpv` yang sama via constructor, didaftarkan terpisah ke `CommandRouter`. Lihat detail diagram di laporan arsitektur (`3_architecture.md`, §17).

---

## CS-05 — Long Parameter List: `PlaybackController.__init__` (8 parameter)

**Lokasi:** `engine/playback/controller.py`, baris 29–39

```python
def __init__(
    self, bus: EventBus, state: AppState, mpv: AudioPlayerPort,
    resolver: CacheResolver, sponsorblock: SponsorBlockProvider,
    lyrics_fetcher: LyricsProvider, queue_mode: QueueMode, radio_mode: RadioMode
):
```

**Alasan:** 8 parameter constructor menyulitkan pembuatan instance (di `main.py`) dan menandakan class melakukan terlalu banyak orkestrasi (selaras dengan CS-04). Menambah dependency baru akan terus memperpanjang signature ini.

**Severity:** 🟢 Low

**Cara Refactor:** Kelompokkan dependency terkait ke dalam parameter object / dataclass.
```python
@dataclass
class PlaybackDependencies:
    bus: EventBus
    state: AppState
    mpv: AudioPlayerPort
    resolver: CacheResolver
    sponsorblock: SponsorBlockProvider
    lyrics_fetcher: LyricsProvider
    queue_mode: QueueMode
    radio_mode: RadioMode

class PlaybackController:
    def __init__(self, deps: PlaybackDependencies):
        self.bus = deps.bus
        self.state = deps.state
        ...
```

---

## CS-06 — Duplicate Code: Pola "update duration → upsert DB → publish QueueUpdatedEvent" diulang 3×

**Lokasi:** `engine/playback/controller.py` — `_on_track_duration()` dan 2 blok identik di `_poll_duration()`

**Alasan:**
```python
self.state.duration = event.duration  # / dur
track.duration = int(event.duration)  # / dur
safe_create_task(self.resolver.db.upsert_track(self.state.current_track), name="upsert_track_duration")
await self.bus.publish(QueueUpdatedEvent())
```
Blok logic yang identik (hanya sumber variabel berbeda) muncul 3 kali di file yang sama. Perubahan pada satu blok (mis. tambah validasi) berisiko lupa diterapkan ke 2 blok lainnya.

**Severity:** 🟡 Medium

**Cara Refactor:** Ekstrak jadi 1 method privat.
```python
async def _apply_confirmed_duration(self, track: TrackInfo, dur: float):
    self.state.duration = dur
    track.duration = int(dur)
    safe_create_task(self.resolver.db.upsert_track(track), name="upsert_track_duration")
    await self.bus.publish(QueueUpdatedEvent())

async def _on_track_duration(self, event: TrackDurationEvent):
    if event.duration and self.state.duration == 0 and self.state.current_track:
        await self._apply_confirmed_duration(self.state.current_track, event.duration)

async def _poll_duration(self, track: TrackInfo):
    await asyncio.sleep(2)
    if self.state.current_track != track:
        return
    dur = await self.mpv.get_duration()
    if dur > 0:
        await self._apply_confirmed_duration(track, dur)
        return
    await asyncio.sleep(5)
    if self.state.current_track == track:
        dur = await self.mpv.get_duration()
        if dur > 0:
            await self._apply_confirmed_duration(track, dur)
```

---

## CS-07 — Duplicate Code: Pola `async with self._lock: ... publish(QueueUpdatedEvent())` diulang di 6+ handler

**Lokasi:** `engine/playback/controller.py` — `_on_queue_remove`, `_on_queue_add`, `_on_queue_replace`, `_on_queue_reorder`, `_on_stop` (sebagian), `_on_set_sponsorblock`, dll.

**Alasan:** Struktur "acquire lock → mutasi state → publish event" berulang identik di banyak method, hanya isi mutasinya berbeda — boilerplate yang bisa diringkas.

**Severity:** 🟢 Low

**Cara Refactor:** Buat context manager/decorator kecil.
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def _locked_mutation(self):
    async with self._lock:
        yield
    await self.bus.publish(QueueUpdatedEvent())

async def _on_queue_remove(self, index: int):
    async with self._locked_mutation():
        if 0 <= index < len(self.state.queue):
            removed = self.state.queue[index]
            del self.state.queue[index]
            await self.bus.publish(LogMessageEvent(message=f"Dihapus dari antrean: {removed.title}"))
```

---

## CS-08 — Feature Envy: `_on_download_complete` di `event_listeners.py` menembus 3 level ke dalam `playback_controller`

**Lokasi:** `server/handlers/event_listeners.py`, fungsi `_on_download_complete`

```python
safe_create_task(playback_controller.resolver.db.upsert_track(event.track, local_path=event.track.local_path), ...)
from services.discover_service import DiscoverService
ds = DiscoverService(playback_controller.resolver.db)
```

**Alasan:** Fungsi ini lebih "tertarik" pada internal `playback_controller.resolver.db` dibanding pada objeknya sendiri — train-wreck / pelanggaran Law of Demeter klasik. Fungsi ini juga membuat instance `DiscoverService` baru secara ad-hoc di tengah event handler alih-alih menerimanya lewat dependency injection (tidak konsisten dengan `prefetch_service`/`broadcast_service` yang sudah di-inject sebagai parameter).

**Severity:** 🟡 Medium

**Cara Refactor:** Berikan `db` dan `DiscoverService` sebagai dependency eksplisit ke `setup_event_listeners`, dan tambahkan method publik `playback_controller.upsert_current_track_metadata(...)` alih-alih mengakses `resolver.db` langsung dari luar.
```python
def setup_event_listeners(playback_controller, prefetch_service, broadcast_service, discover_service):
    async def _on_download_complete(event: DownloadCompleteEvent):
        await broadcast_service.broadcast_state(playback_controller.state)
        if event.track:
            safe_create_task(
                playback_controller.persist_track_update(event.track),  # method publik baru
                name="upsert_dl_track"
            )
            payload = await discover_service.build_discover_payload()
            await broadcast_service.manager.broadcast(payload)
    ...
```

---

## CS-09 — Primitive Obsession: `video_id`, `duration`, `volume` selalu `str`/`int` polos tanpa Value Object

**Lokasi:** Menyebar di seluruh codebase — `core/state.py` (`TrackInfo.video_id: str`), validasi regex diulang di 2 tempat berbeda (`server/handlers/http.py` dan seharusnya `server/serializers.py`), clamp volume `max(0, min(100, ...))` diulang di `VolumeService` dan `MpvController.set_volume`.

**Alasan:** `video_id` adalah string bebas yang seharusnya punya invariant (`^[a-zA-Z0-9_-]{11}$`) tapi divalidasi tidak konsisten di beberapa tempat (lihat SEC-05 di audit keamanan) karena tidak ada satu Value Object yang memaksakan validitasnya di titik pembuatan. `volume` (int 0–100) dan `Duration` (int detik) juga selalu primitif polos, sehingga logic clamp/validasi diduplikasi di beberapa layer alih-alih terjamin oleh tipe itu sendiri.

**Severity:** 🟡 Medium

**Cara Refactor:**
```python
# core/value_objects.py
import re

class VideoId(str):
    _RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
    def __new__(cls, value: str):
        if not cls._RE.match(value):
            raise ValueError(f"video_id tidak valid: {value!r}")
        return super().__new__(cls, value)

class Volume(int):
    def __new__(cls, value: int):
        return super().__new__(cls, max(0, min(100, int(value))))
```
`TrackInfo.video_id` bertipe `VideoId`, dan konstruksi `VideoId("...")` otomatis melempar error di titik input (`dict_to_track`) — validasi jadi terpusat di 1 tempat, bukan tersebar.

---

## CS-10 — Magic Number: Timeout literal bertebaran di `radio_engine.py`

**Lokasi:** `engine/radio_engine.py` — `timeout=20.0`, `timeout=30.0` (2×), `timeout=40.0`, `timeout=25.0`, `<= 5`, `> 30`, `<= 30.0`

**Alasan:** File ini sudah punya konstanta bernama di bagian atas (`MAX_TRACK_DURATION`, `TRACKS_PER_ARTIST_TARGET`, `ARTISTS_PER_BATCH`, dst.) — menunjukkan penulis *sadar* akan pentingnya named constant, tapi tidak konsisten menerapkannya untuk angka timeout dan angka ambang batas lain di bagian bawah file yang sama.

**Severity:** 🟢 Low

**Cara Refactor:**
```python
# di bagian konstanta atas file
QUICK_FETCH_TIMEOUT_SEC = 20.0
BACKFILL_TIMEOUT_SEC = 30.0
STANDBY_BUILD_TIMEOUT_SEC = 30.0
RANDOMIZE_TIMEOUT_SEC = 40.0
PREFETCH_TIMEOUT_SEC = 25.0
STANDBY_REFILL_THRESHOLD = 5
RADIO_QUEUE_MAX_SIZE = 30
PREFETCH_TIME_REMAINING_SEC = 30.0
```
Lalu ganti semua literal dengan referensi konstanta ini.

---

## CS-11 — Magic Number: Default value untuk WebSocket payload tersebar tanpa konstanta bersama

**Lokasi:** `server/handlers/websocket.py` — `data.get("volume", 80)`, `data.get("mode", "queue")`, `data.get("output", "device")`, dll.

**Alasan:** Nilai default (`80` untuk volume, `"queue"`/`"device"` sebagai mode/output default) di-hardcode di titik pemakaian, padahal `core/state.py::AppState` sudah mendefinisikan default yang sama (`volume: int = 80`). Dua sumber kebenaran untuk nilai default yang sama berisiko drift jika salah satu diubah tanpa yang lain.

**Severity:** 🟢 Low

**Cara Refactor:** Import default dari `AppState`/`core/constants.py` alih-alih literal ulang.
```python
from core.constants import DEFAULT_VOLUME
...
vol = data.get("volume", DEFAULT_VOLUME)
```

---

## CS-12 — Magic String: Nama action WebSocket (`"play_track"`, `"toggle_pause"`, dst.) hardcoded sebagai string literal di JS dan Python tanpa shared constant

**Lokasi:** `web/static/js/*.js` (pemanggilan `wsSend("play_track", ...)`, `wsSend("toggle_pause")`, dst.) vs `server/handlers/websocket.py` (`@register_ws_handler("play_track")`, dst.)

**Alasan:** String action name diketik ulang secara manual di kedua sisi (client & server) tanpa satu sumber kebenaran. Typo di salah satu sisi (mis. `"toggle_paus"`) tidak akan terdeteksi oleh compiler/linter apapun — hanya diketahui saat runtime lewat `logger.warning(f"Unknown WS action: {action}")`.

**Severity:** 🟡 Medium

**Cara Refactor:** Definisikan konstanta action di 1 file yang bisa dipakai kedua sisi (Python dict + JS object yang di-generate dari sumber sama, atau minimal file `constants.js` yang mirror `command_bus.py`).
```javascript
// web/static/js/actions.js
const WS_ACTIONS = Object.freeze({
    PLAY_TRACK: "play_track",
    TOGGLE_PAUSE: "toggle_pause",
    NEXT: "next",
    // ...
});
```
```python
# server/handlers/ws_actions.py
class WSAction:
    PLAY_TRACK = "play_track"
    TOGGLE_PAUSE = "toggle_pause"
    NEXT = "next"
```

---

## CS-13 — Magic Number: Limit `15`/`100` untuk discover data diulang di 2 tempat

**Lokasi:** `server/handlers/websocket.py::_build_discover_payload` (`ds.get_recent(15)`, `ds.get_favorites(15)`, `ds.get_cached(15)`, `ds.get_featured_artists(100)`, `ds.get_featured_genres(100)`) — dan blok identik terduplikasi persis di `server/handlers/event_listeners.py::_on_download_complete`

**Alasan:** Selain jadi magic number, angka ini **juga duplicate code** (blok query identik disalin utuh ke `event_listeners.py` — lihat juga CS-08). Mengubah limit discover di satu tempat tidak otomatis konsisten di tempat lain.

**Severity:** 🟡 Medium

**Cara Refactor:** Satukan jadi 1 fungsi (`_build_discover_payload` sudah ada — pakai itu di `event_listeners.py` juga, bukan menyalin ulang), dan definisikan limit sebagai konstanta.
```python
# core/constants.py
DISCOVER_RECENT_LIMIT = 15
DISCOVER_FAVORITES_LIMIT = 15
DISCOVER_CACHED_LIMIT = 15
DISCOVER_FEATURED_ARTISTS_LIMIT = 100
DISCOVER_FEATURED_GENRES_LIMIT = 100
```
```python
# event_listeners.py — panggil fungsi yang sudah ada, bukan duplikasi query
from server.handlers.websocket import _build_discover_payload
payload = await _build_discover_payload(playback_controller.resolver.db)
await broadcast_service.manager.broadcast(payload)
```

---

## CS-14 — Unused Import (terverifikasi via `pyflakes`, 25+ kasus)

**Lokasi (contoh signifikan):**
- `main.py`: `logging`, `logging.handlers.RotatingFileHandler` — tidak dipakai
- `server/app.py`: **9 import tak terpakai** — `time`, `TrackStartedEvent`, `TrackProgressEvent`, `QueueUpdatedEvent`, `LyricsUpdatedEvent`, `DownloadCompleteEvent`, `LogMessageEvent`, `TrackPauseChangedEvent`, `safe_create_task`, `state_to_dict`, `CACHE_DIR`, `STREAM_URL_TTL_SEC`
- `server/middleware.py`: `time`, `ACTIVE_WEBSOCKETS`
- `server/handlers/auth.py`: `time`
- `server/handlers/websocket.py`: `re`
- `cache/resolver.py`: `Database` (padahal type hint sudah pakai `TrackRepositoryPort`)
- `services/discover_service.py`: `aiosqlite`
- `engine/radio_engine.py`: `re`, `logging`, `PlaybackMode`
- `engine/mpv_controller.py`: `PlayerStatus`
- `engine/volume_service.py`: `asyncio`, `CommandBus`
- `engine/playback/track_loader.py`: `asyncio`
- `core/ports.py`: `Dict`, `Any`
- `core/observability.py`: `BatchSpanProcessor`, `ConsoleSpanExporter`
- `core/log_config.py`: `Path`
- `core/events.py`: `Any`
- `plugins/sponsorblock.py`: `safe_create_task`
- `data/enrich_duration.py`: `time`

**Alasan:** Import tak terpakai adalah sisa refactor yang tidak dibersihkan — 9 import tak terpakai sekaligus di `server/app.py` (semua `core.events.*`) sangat mencolok, kemungkinan sisa saat event-listener logic dipindah ke `event_listeners.py` tapi importnya lupa dihapus dari `app.py`. Ini menambah noise kognitif dan membuat pembaca salah mengira `app.py` masih menangani event-event tersebut.

**Severity:** 🟢 Low (tidak berdampak fungsional, tapi cepat & murah untuk dibersihkan — cocok untuk quick win)

**Cara Refactor:** Jalankan `pyflakes .` atau `ruff check --select F401` di CI sebagai gate otomatis, lalu hapus seluruh import di atas.
```bash
ruff check --select F401 --fix .
```

---

## CS-15 — Unused Variable (terverifikasi via `pyflakes`)

**Lokasi:**
- `main.py` baris 83–84: `download_manager = DownloadManager(...)` dan `command_router = CommandRouter(...)` — dibuat tapi variabelnya sendiri tidak pernah dibaca lagi (efeknya memang lewat side-effect constructor `command_bus.register(...)`, tapi ini menyamarkan intent — pembaca tidak langsung tahu bahwa "assignment yang tidak dipakai" ini sebenarnya penting untuk side-effect registrasi command)
- `server/handlers/websocket.py` baris 75: `playback_controller = request.app["playback_controller"]` di `ws_handler()` — diambil dari `request.app` tapi tidak pernah dipakai di dalam fungsi itu sendiri (kemungkinan sisa sebelum logic dipindah ke command_bus/event_listeners)
- `core/log_config.py`: variabel `track` (baris 77) dan `exc` (baris 356) di-assign tapi tidak pernah dibaca

**Alasan:** Variabel yang di-assign tapi tak terpakai adalah sinyal dead code atau logic yang lupa dihapus/lupa diselesaikan setelah refactor.

**Severity:** 🟢 Low

**Cara Refactor:**
```python
# main.py — beri underscore prefix untuk menandakan sengaja tak dipakai langsung (side-effect only)
_download_manager = DownloadManager(bus, state, ytdlp)
_command_router = CommandRouter(playback_controller, volume_service)
```
```python
# server/handlers/websocket.py — hapus baris yang benar-benar tidak dipakai
async def ws_handler(request):
    state = request.app["state"]
    manager = request.app["manager"]
    db = request.app["db"]
    ytdlp = request.app["ytdlp"]
    # playback_controller dihapus jika memang tidak dipakai di fungsi ini
```

---

## CS-16 — Dead Code: `except MpvConnectionError: raise` unreachable

**Lokasi:** `engine/mpv_controller.py::_do_connect()`

**Alasan:** Sudah dibahas detail di audit bug (BUG-04) — blok except ini tidak pernah bisa tereksekusi karena `open_unix_connection`/`open_connection` tidak pernah melempar `MpvConnectionError`. Dicantumkan ulang di sini sebagai kategori code smell "Dead Code" murni (di luar konteks bug fungsional).

**Severity:** 🟢 Low

**Cara Refactor:** Hapus except clause tersebut (lihat kode lengkap di `4_security.md`/laporan bug BUG-04).

---

## CS-17 — Duplicate Code (Frontend): Pola render list card (`img.dataset.vid/title/artist/thumb` + lazy-load) diulang identik di 4 tempat

**Lokasi:** `web/static/js/render/discover.js` — blok identik muncul di render "recent" (baris ~65–81), "favorites" (~116–146), "cached" (~182–202), dan lagi di `renderRecentRow` (~369–378)

**Alasan:** Struktur "buat elemen img, set `data-vid`/`data-title`/`data-artist`/`data-thumb`, escape HTML, lazy-load thumbnail" adalah blok ~15 baris yang disalin-tempel 4 kali dengan variasi kecil (nama class CSS berbeda per section).

**Severity:** 🟡 Medium

**Cara Refactor:** Ekstrak jadi 1 factory function.
```javascript
function createTrackCard(track, { cardClass, titleClass, metaClass, metaBuilder }) {
    const el = document.createElement("div");
    el.className = cardClass;
    el.innerHTML = `
        <img class="lazy-cover" data-vid="${escapeHtml(track.video_id || '')}"
             data-title="${escapeHtml(track.title || '')}" data-artist="${escapeHtml(track.artist || '')}"
             data-thumb="${escapeHtml(track.thumbnail || '')}" src="" alt="">
        <div class="${titleClass}"></div>
        <div class="${metaClass}"></div>
    `;
    const title = typeof cleanTrackTitle === "function" ? cleanTrackTitle(track.title) : track.title;
    el.querySelector("." + titleClass).textContent = title;
    el.querySelector("." + metaClass).textContent = metaBuilder(track);
    return el;
}
```

---

## Ringkasan

| # | Smell | Kategori | Severity |
|---|---|---|---|
| CS-01 | `ServerManager` (start.py) | God Class | 🟠 High |
| CS-02 | `main()` di main.py | God Function / Long Method | 🟡 Medium |
| CS-03 | `websocket.py` (30 fungsi) | Large Class | 🟡 Medium |
| CS-04 | `PlaybackController` (24 method) | Large Class / God Object | 🟠 High |
| CS-05 | `PlaybackController.__init__` (8 param) | Long Parameter List | 🟢 Low |
| CS-06 | Duplikasi update-duration 3× | Duplicate Code | 🟡 Medium |
| CS-07 | Duplikasi lock+publish pattern | Duplicate Code | 🟢 Low |
| CS-08 | `_on_download_complete` train-wreck | Feature Envy | 🟡 Medium |
| CS-09 | `video_id`/`volume`/`duration` primitif | Primitive Obsession | 🟡 Medium |
| CS-10 | Timeout literal di radio_engine.py | Magic Number | 🟢 Low |
| CS-11 | Default value WS tanpa konstanta bersama | Magic Number | 🟢 Low |
| CS-12 | Nama action WS hardcoded dupikat client/server | Magic String | 🟡 Medium |
| CS-13 | Limit 15/100 discover diduplikasi | Magic Number + Duplicate Code | 🟡 Medium |
| CS-14 | 25+ unused import (pyflakes-verified) | Unused Import | 🟢 Low |
| CS-15 | Unused variable (main.py, websocket.py, log_config.py) | Unused Variable | 🟢 Low |
| CS-16 | Except clause unreachable di mpv_controller.py | Dead Code | 🟢 Low |
| CS-17 | Template card frontend diulang 4× | Duplicate Code | 🟡 Medium |

**Catatan positif:** Tidak ditemukan "Commented Code" signifikan di Python (hanya 1 komentar penjelas biasa, bukan kode mati) — kebiasaan tidak meninggalkan kode ter-comment cukup baik di seluruh codebase. JS juga bersih dari blok kode ter-comment; hanya 8 pemakaian `console.log`/`console.debug` (di `audio.js`, `main.js`, `utils.js`) yang sebaiknya dihapus/diganti logger terkondisi sebelum rilis produksi.

**Rekomendasi urutan pengerjaan:** Mulai dari **quick win murah** (CS-14, CS-15, CS-16 — bisa diselesaikan dalam <1 jam via `ruff --fix`), lalu **CS-01/CS-04** (God Class terbesar, butuh refactor terencana sebelum menambah fitur besar berikutnya), baru sisanya sesuai prioritas roadmap.
