# Data Flow Audit — LunaWave

Scope: object lifecycle, state, cache, session, repository, service, DTO, mapper, serializer/deserializer.
Tidak membahas UI/frontend. Fokus murni pada aliran data antar layer.

---

## 🔴 #1 — `state.queue` / `state.radio_queue` di-refactor dari `deque` → `list`, tapi consumer masih panggil `.popleft()`

**File:** `engine/queue_manager.py:30` (`QueueMode.next`), `engine/radio_engine.py:116` (`RadioMode.next`)

```python
# engine/queue_manager.py
track = controller.state.queue.popleft()

# engine/radio_engine.py
track = self.state.radio_queue.popleft()
```

**Root cause:** Di `core/state.py`, field `AppState.queue` dan `AppState.radio_queue` didefinisikan sebagai `list` biasa (`field(default_factory=list)`), bukan `collections.deque`. Ini konsisten dipakai sebagai `list` di tempat lain:

- `engine/playback/queue_commands.py` → `.pop(0)`, `.append()`, `.clear()`, `.extend()`, `del q[i]`, `.insert()`
- `engine/playback/playback_commands.py` → `.clear()`

Tapi **hanya** `QueueMode.next()` dan `RadioMode.next()` yang masih memanggil `.popleft()` — method milik `deque`, tidak ada di `list`.

**Dampak (parah):** `list` tidak punya method `.popleft()` → `AttributeError` setiap kali:
- Lagu di QUEUE mode selesai diputar (auto-advance lewat `_on_track_ended` → `_advance_to_next()` → `QueueMode.next()`)
- Tombol "Next" ditekan manual saat mode QUEUE
- Sama persis untuk RADIO mode (`RadioMode.next()`)

Karena `_on_track_ended` dipanggil dari `EventBus.publish()` yang membungkus setiap subscriber dengan `try/except` (lihat `core/event_bus.py`), exception ini **tidak** meng-crash seluruh server — tapi **silently swallowed** setelah di-log. Efek yang terlihat user: lagu berhenti begitu saja setelah track pertama selesai, tanpa error yang jelas ke client (auto-advance mati total di kedua mode).

Untuk trigger manual via tombol "Next" (WS command → `command_bus.execute` → `CommandRouter._route`), exception ini justru di-raise ulang oleh `CommandBus.execute` dan ditangkap generic exception handler di `handle_ws_message`, dikembalikan ke client sebagai `{"code": "INTERNAL", ...}`.

**Verifikasi:** dikonfirmasi langsung: `list().popleft()` → `AttributeError: 'list' object has no attribute 'popleft'`.

**Fix:** Ganti `.popleft()` menjadi `.pop(0)` di kedua tempat (konsisten dengan pola yang sudah dipakai di `queue_commands.py`), ATAU ubah `queue`/`radio_queue` kembali menjadi `deque` di `core/state.py` dan pastikan seluruh consumer (`queue_commands.py`, `playback_commands.py`) disesuaikan (`del q[i]`, `.insert()` tidak didukung deque tanpa index-based cost, jadi `.pop(0)` di sisi consumer adalah fix yang lebih murah/aman).

---

## 🔴 #2 — Facade `Database` kehilangan beberapa method forwarding ke repository → `AttributeError` di alur discover & post-download

**File:** `cache/db.py` (bagian "Explicit Forwarding") vs pemanggil di `server/handlers/event_listeners.py` dan `server/handlers/ws/discover_handlers.py`

`Database` di-refactor menjadi facade yang forward ke sub-repository (`self.tracks = TrackRepository(...)`, `self.discover = DiscoverRepository(...)`, `self.sessions = AuthRepository(...)`). Forwarding eksplisit yang ada di `cache/db.py`:

```
get_track, upsert_track, update_stream_url_only, set_local_path,
increment_play_count, toggle_favorite, evict_stale_tracks,
increment_artist_click, increment_genre_click, get_genre_artists,
get_all_artists, get_random_songs, get_artist_songs_strict,
get_genre_songs, create_session, verify_session, delete_session,
cleanup_sessions
```

**Yang hilang dari daftar forwarding**, padahal ada di `TrackRepository` dan dipanggil lewat objek `Database`:
- `get_recent_tracks` — ada di `TrackRepository`, **tidak** di-forward di `Database`
- `get_favorite_tracks` — ada di `TrackRepository`, **tidak** di-forward
- `get_cached_tracks` — ada di `TrackRepository`, **tidak** di-forward
- `set_favorite` — ada di `TrackRepository`, **tidak** di-forward

**Titik gagal konkret:**

1. `server/handlers/event_listeners.py` → `_on_download_complete`:
   ```python
   db = playback_controller.resolver.db     # ini objek Database, bukan TrackRepository
   recent = await db.get_recent_tracks(20)  # AttributeError: 'Database' object has no attribute 'get_recent_tracks'
   favorites = await db.get_favorites()     # juga tidak ada — nama pun berbeda (get_favorites vs get_favorite_tracks)
   ```
   Exception ini terjadi **setelah** `broadcast_state` dan `upsert_track` berhasil, sehingga tertangkap oleh error-boundary `EventBus.publish` dan cuma di-log. **Efek nyata:** setiap kali sebuah download selesai, notifikasi `discover_data` (refresh daftar recent/favorites di client) **tidak pernah terkirim** — client tidak tahu track yang baru saja selesai di-download sudah tersedia offline sampai mereka manual trigger `discover` action lagi.

2. `server/handlers/ws/discover_handlers.py` → `_handle_toggle_favorite`, jalur `set_favorite is not None`:
   ```python
   await db.set_favorite(video_id, target)   # AttributeError: 'Database' object has no attribute 'set_favorite'
   ```
   Ini di luar try/except lokal, jadi ter-catch oleh exception handler generic di `handle_ws_message` → client menerima error `INTERNAL`. **Efek:** fitur "set favorite ke status tertentu" (bukan sekadar toggle) rusak total; hanya jalur `toggle_favorite` (tanpa `set_favorite` eksplisit) yang masih berfungsi karena `toggle_favorite` kebetulan ada di daftar forwarding.

**Fix:** Tambahkan forwarding yang hilang di `cache/db.py`:
```python
async def get_recent_tracks(self, limit): return await self.tracks.get_recent_tracks(limit)
async def get_favorite_tracks(self, limit): return await self.tracks.get_favorite_tracks(limit)
async def get_cached_tracks(self, limit): return await self.tracks.get_cached_tracks(limit)
async def set_favorite(self, video_id, is_favorite): return await self.tracks.set_favorite(video_id, is_favorite)
```
Juga perbaiki pemanggilan `db.get_favorites()` di `event_listeners.py` menjadi `db.get_favorite_tracks(...)` agar nama method konsisten dengan repository.

---

## 🟠 #3 — Skema payload `discover_data` tidak konsisten antar dua producer

**File:** `server/handlers/ws/discover_handlers.py` (`_build_discover_payload`) vs `server/handlers/event_listeners.py` (`_on_download_complete`)

Payload `discover_data` yang dikirim dari alur normal (`WSAction.DISCOVER` / initial load) punya 5 field:
```json
{"recent": [...], "favorites": [...], "cached_tracks": [...], "featured_artists": [...], "featured_genres": [...]}
```

Tapi payload `discover_data` yang dikirim `_on_download_complete` (setelah download selesai) hanya berisi 2 field:
```json
{"recent": [...], "favorites": [...]}
```

**Dampak:** Kedua broadcast memakai `"type": "discover_data"` yang sama, tapi bentuk `data` berbeda. Consumer (client) yang mengharapkan `cached_tracks`/`featured_artists`/`featured_genres` selalu ada di setiap event `discover_data` akan menerima payload parsial setiap kali ada broadcast dari jalur download — berpotensi menimpa/mengosongkan state client untuk field yang tidak dikirim tergantung cara client melakukan merge. (Catatan: ini juga tidak akan pernah terkirim akibat bug #2, tapi skema tetap perlu disamakan begitu bug #2 diperbaiki.)

**Fix:** Gunakan satu fungsi builder yang sama (`_build_discover_payload` dari `discover_handlers.py`) di kedua tempat, alih-alih membangun payload manual dan parsial di `event_listeners.py`.

---

## 🟠 #4 — `CacheResolver.resolve()`: hasil fetch tidak diteruskan ke object `TrackInfo` milik pemanggil yang menunggu (race condition)

**File:** `cache/resolver.py`, method `resolve()`

```python
if needs_fetch:
    url = await asyncio.wait_for(self.ytdlp.get_stream_url(track.video_id), timeout=30.0)
    track.stream_url = url          # <-- hanya caller PERTAMA yang set atribut ini
    await self.db.upsert_track(track, stream_url=url)
    ...
    return url
else:
    return await asyncio.wait_for(fut, timeout=35.0)   # <-- caller lain dapat return value URL,
                                                        #     TAPI track (miliknya sendiri) TIDAK di-update
```

**Dampak:** Ketika dua pemanggilan `resolve()` untuk `video_id` yang sama terjadi bersamaan (mis. saat prefetch radio & saat user memilih lagu yang sama), hanya caller yang menjadi "leader fetch" yang objek `TrackInfo`-nya mendapatkan `stream_url` ter-update. Caller kedua (follower) menerima nilai balik (`url`) yang benar sebagai return value fungsi, tapi **atribut `track.stream_url` miliknya sendiri tetap `None`**.

Ini nyata berdampak di `engine/radio_engine.py` → `_do_prefetch`:
```python
next_track = self.state.radio_queue[0]
if next_track.stream_url:      # cek berdasarkan atribut object
    return
await controller.track_loader.resolver.resolve(next_track)
```
Jika `next_track` kebetulan sedang di-resolve bersamaan oleh proses lain (mis. dipanggil juga lewat `load_track` saat lagu benar-benar mulai diputar), pengecekan `if next_track.stream_url` di pemanggilan berikutnya tetap `False` meski URL sudah berhasil diambil dan tersimpan di DB — menyebabkan `_do_prefetch` mengulang proses resolve yang sebenarnya tidak perlu (inefisiensi, bukan crash), dan setiap kode lain yang mengandalkan `track.stream_url` (bukan return value fungsi) untuk assumsi "sudah di-resolve" bisa salah baca state track sebagai "belum di-resolve".

**Fix:** Di cabang `else` (`needs_fetch=False`), tetap set `track.stream_url = url` sebelum return, agar object pemanggil manapun konsisten mendapat data yang sama seperti return value-nya.

---

## 🟡 #5 — `state.json` kehilangan `local_path` setiap kali server restart (serializer dipakai untuk dua tujuan berbeda)

**File:** `core/state.py` — `TrackInfo.to_dict()` (dipakai baik untuk **broadcast ke client** maupun untuk **`to_persistent_dict()`/simpan ke disk**) dan `TrackInfo.from_dict()` (dipakai baik untuk **parsing payload client** maupun **load dari `state.json`**)

```python
def to_dict(self) -> dict:
    return {
        ...,
        "is_cached": bool(self.local_path),   # local_path asli TIDAK pernah diserialisasi
        ...
    }

@classmethod
def from_dict(cls, data: dict) -> Optional['TrackInfo']:
    ...
    # stream_url dan local_path TIDAK diambil dari client payload (S02-040)
    # untuk mencegah SSRF/injection.
    local_path=None,
    stream_url=None,
    ...
```

`AppState.to_persistent_dict()` (dipanggil oleh `save_to_disk`, dijalankan tiap 5 detik oleh `_persist_state_loop` di `PlaybackController`) memanggil `t.to_dict()` untuk setiap track di `queue`, `radio_queue`, `history`, dan `current_track`. Karena `to_dict()` hanya menyimpan boolean `is_cached`, bukan path aslinya, dan `from_dict()` selalu memaksa `local_path=None` (aturan keamanan yang sebenarnya ditujukan untuk payload dari **client via WebSocket**, bukan untuk file state milik server sendiri) —

**Dampak:** Setiap kali server di-restart, seluruh track yang ada di `queue`, `radio_queue`, `history`, dan `current_track` yang sebelumnya sudah ter-download (`local_path` terisi) akan **kehilangan referensi lokal-nya** begitu di-load ulang dari `state.json`, walau file MP3 fisiknya masih ada di cache. Track tersebut akan dianggap "belum di-cache" sampai di-resolve ulang lewat `CacheResolver` (yang untungnya query ulang ke DB dan bisa menemukan `local_path` yang benar — lihat `resolve()` cek `db.get_track` duluan). Jadi dampaknya bukan playback rusak total, tapi **state in-memory langsung setelah restart untuk semua track di queue/history sempat salah** (tidak "is_cached") sampai masing-masing di-resolve ulang satu per satu, dan field `is_cached` yang dikirim ke client (misalnya untuk item-item di riwayat/antrean sebelum sempat diputar ulang) akan salah tampil sebagai "belum tersedia offline" walau sebenarnya sudah.

**Fix:** Pisahkan dua serializer: satu untuk output client (`to_dict`, tetap strip raw path demi keamanan, cukup `is_cached`), satu lagi untuk persistensi disk (misal `to_disk_dict`/`from_disk_dict`) yang menyimpan & memuat `local_path` & `stream_url` apa adanya karena sumber datanya terpercaya (server sendiri, bukan client).

---

## 🟡 #6 — `app["command_bus"]` diisi kondisional tapi diakses tanpa pengaman (dependency wiring rapuh)

**File:** `server/app.py` (`create_app`) vs `server/handlers/websocket.py` (`ws_handler`)

```python
# server/app.py
if command_bus:
    app["command_bus"] = command_bus   # key hanya diset jika command_bus truthy

# server/handlers/websocket.py
command_bus = request.app["command_bus"]   # direct index access, bukan .get()
```

**Dampak:** Jika `create_app()` dipanggil tanpa `command_bus` (parameter default `None` — persis seperti yang dilakukan hampir semua test integrasi: `create_app(mock_playback_controller, mock_ytdlp, mock_db, ConnectionManager())`), maka `app["command_bus"]` tidak pernah di-set, dan **koneksi WebSocket apapun akan langsung `KeyError: 'command_bus'`** begitu `ws_handler` dipanggil. Di production ini "aman" karena `core/bootstrap.py` selalu mengoper `command_bus` non-None, tapi ini adalah wiring dependency yang rapuh — bukan startup config yang gagal fail-fast, melainkan silent trap yang baru meledak saat request WS pertama masuk.

**Fix:** Gunakan `app["command_bus"] = command_bus` tanpa kondisional (biarkan `None` eksplisit jika memang tidak ada), dan di `ws_handler` gunakan `request.app.get("command_bus")` dengan guard/pesan error yang jelas jika `None`.

---

## Ringkasan

| # | Severity | Lokasi | Data yang hilang/rusak |
|---|----------|--------|--------------------------|
| 1 | Critical | `engine/queue_manager.py`, `engine/radio_engine.py` | Auto-advance ke track berikutnya crash (list vs deque) |
| 2 | Critical | `cache/db.py` (facade forwarding) | `discover_data` post-download & `set_favorite` gagal total (AttributeError) |
| 3 | Moderate | `event_listeners.py` vs `discover_handlers.py` | Skema `discover_data` tidak konsisten (field hilang) |
| 4 | Moderate | `cache/resolver.py` | `track.stream_url` tidak ter-update untuk pemanggil concurrent (return value vs object state) |
| 5 | Moderate | `core/state.py` (`to_dict`/`from_dict`) | `local_path` hilang dari semua track di state setelah restart |
| 6 | Minor | `server/app.py` / `websocket.py` | `command_bus` wiring rapuh, `KeyError` jika tidak dioper |
