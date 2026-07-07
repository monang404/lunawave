# Lunawave — Laporan Audit Testing
**Tim Audit:** Senior Software Architect · Principal Backend Engineer · QA Lead · Security Engineer · Performance Engineer  
**Tanggal:** 2026-07-07  
**Scope:** Seluruh project — Python backend, JavaScript frontend, integrasi, coverage, mocking, regression, dan critical flow

---

## Ringkasan Eksekutif

Project Lunawave memiliki **infrastruktur pengujian yang ada tetapi dangkal dan tidak seimbang**. Total ditemukan **24 file test Python** dan **1 file test HTML manual** untuk **~70+ modul sumber**. Test yang ada sebagian besar adalah *structural/source-inspection tests* (menggunakan `inspect.getsource`) bukan behavioral tests. Coverage fungsional nyata sangat rendah, dan seluruh layer frontend JavaScript **tidak memiliki automated testing sama sekali**.

| Kategori | Nilai |
|---|---|
| Estimasi Coverage Keseluruhan | **~22–28%** |
| Coverage Backend (Python) | ~30–38% |
| Coverage Frontend (JavaScript) | **~1%** (manual HTML saja) |
| Test Tipe Unit | Ada, tapi mayoritas struktural |
| Test Tipe Widget | ❌ Tidak ada |
| Test Tipe Integration | Parsial (5 file, banyak yang incomplete) |
| Test Tipe API (HTTP/WS) | Parsial (4 test WS, 1 HTTP) |
| Mock Strategy | Inkonsisten, banyak mock terlalu longgar |
| Regression Suite | ❌ Tidak ada regression suite formal |
| CI/CD Test Gate | ❌ Tidak ada |

---

## 1. Inventaris Test yang Ada

### 1.1 Unit Tests (tests/unit/)

| File Test | Modul yang Diuji | Tipe | Kualitas |
|---|---|---|---|
| `core/test_app_state.py` | `core/state.py` (AppState.duration) | Behavioral | ✅ Baik |
| `core/test_audio_output_enum.py` | `core/state.py` (AudioOutput) | Behavioral | ✅ Baik |
| `core/test_command_bus.py` | `core/command_bus.py` | Behavioral | ✅ Baik |
| `core/test_domain_events.py` | `core/event_bus.py` + `core/events.py` | Behavioral | ✅ Baik |
| `core/test_event_bus_basic.py` | `core/event_bus.py` | Behavioral | ✅ Baik |
| `core/test_tasks.py` | `core/task_utils.py` | Behavioral + Struktural | ✅ Baik |
| `engine/test_queue_locking.py` | `engine/playback/queue_commands.py` | **Struktural saja** | ⚠️ Lemah |
| `engine/test_radio.py` | `engine/radio_engine.py` | **Struktural saja** | ⚠️ Lemah |
| `cache/test_db_upsert.py` | `cache/db.py` (upsert/update/toggle) | Behavioral w/ real DB | ✅ Baik |
| `cache/test_resolver.py` | `cache/resolver.py` + `config.py` | **Struktural saja** | ⚠️ Lemah |
| `server/test_auth.py` | `core/security.py` | Behavioral | ✅ Baik |
| `server/test_security.py` | `server/handlers/http.py` | **Struktural saja** | ⚠️ Lemah |
| `server/test_session.py` | `cache/db.py` (sessions) | Behavioral w/ real DB | ✅ Baik |
| `server/test_ws_broadcast.py` | `server/services/broadcast_service.py` | **Struktural saja** | ⚠️ Lemah |
| `plugins/test_lyrics.py` | `plugins/lyrics.py` | Minimal behavioral | ⚠️ Lemah |
| `plugins/test_lyrics_parser.py` | `plugins/lyrics.py` | Struktural + minimal | ⚠️ Lemah |

### 1.2 Integration Tests (tests/integration/)

| File Test | Scope | Kualitas |
|---|---|---|
| `test_e2e.py` | HTTP health, WS connect/auth/search | ✅ Cukup baik, tapi mock terlalu lebar |
| `test_fase0.py` | TASK-0.1–0.5 quick wins | ⚠️ Campuran behavioral dan struktural |
| `test_fase1.py` | TASK-1.1–1.5 security | ⚠️ `test_metrics_rejects_external_ip` **kosong (pass tanpa assertion)** |

### 1.3 Patch/Regression Test

| File Test | Scope | Kualitas |
|---|---|---|
| `test_patch_0_09_10_11_server_perf.py` | Script defer, Cache-Control, chunk size | Struktural |

### 1.4 Frontend Tests

| File | Scope | Kualitas |
|---|---|---|
| `tests/test_helpers.html` | `utils.js`: `formatTime`, `escapeHtml`, `cleanTrackTitle` | ⚠️ Manual browser, tidak otomatis |

---

## 2. Modul yang TIDAK Memiliki Test

### 2.1 Backend Python — Tidak Diuji Sama Sekali

| Modul | Baris Kode | Fungsi Kritis | Risiko |
|---|---|---|---|
| `engine/mpv_controller.py` | 300 | Koneksi Unix socket, reconnect, event loop | 🔴 KRITIS |
| `engine/playback/controller.py` | 211 | Orchestration play/stop/next/retry | 🔴 KRITIS |
| `engine/playback/track_loader.py` | 34 | Resolusi URL + fallback ke yt-dlp | 🔴 KRITIS |
| `engine/playback/playback_commands.py` | ~150 | on_play, on_stop, on_next, on_prev | 🔴 KRITIS |
| `engine/playback/queue_commands.py` | ~120 | on_queue_add, on_queue_remove, on_queue_select | 🔴 KRITIS |
| `engine/playback/radio_commands.py` | ~80 | on_radio_start, on_radio_next | 🔴 KRITIS |
| `engine/playback/settings_commands.py` | ~60 | Volume, audio output toggle | 🟡 TINGGI |
| `engine/radio_engine.py` | 329 | Seluruh logic radio (hanya structural test) | 🔴 KRITIS |
| `engine/ytdlp_client.py` | 168 | search(), get_stream_url(), download_mp3() | 🔴 KRITIS |
| `engine/download_manager.py` | ~120 | Download flow, lock, duplicate prevention | 🟡 TINGGI |
| `engine/queue_manager.py` | ~80 | Queue add/remove/reorder | 🟡 TINGGI |
| `engine/volume_service.py` | ~60 | Volume persistence | 🟢 SEDANG |
| `cache/resolver.py` | 56 | TTL check, resolve stream URL (hanya struktural) | 🟡 TINGGI |
| `cache/repositories/track_repository.py` | ~80 | CRUD tracks | 🟡 TINGGI |
| `cache/repositories/auth_repository.py` | ~40 | Auth queries | 🟡 TINGGI |
| `cache/repositories/discover_repository.py` | ~60 | Recent/favorites/cached queries | 🟡 TINGGI |
| `server/handlers/http.py` | 207 | Serve stream, static files, login POST | 🔴 KRITIS |
| `server/handlers/auth.py` | 76 | Login flow, session creation | 🔴 KRITIS |
| `server/handlers/websocket.py` | 148 | ConnectionManager, rate limiter, dispatch | 🔴 KRITIS |
| `server/handlers/ws/*.py` | ~400 total | Semua WS command handlers | 🔴 KRITIS |
| `server/handlers/event_listeners.py` | ~80 | Server-side event subscriptions | 🟡 TINGGI |
| `server/services/broadcast_service.py` | 50 | WS broadcast (hanya struktural) | 🟡 TINGGI |
| `server/services/discover_service.py` | ~130 | get_recent, get_favorites, get_featured | 🟡 TINGGI |
| `server/services/stream_prefetch.py` | ~50 | Prefetch stream URL background | 🟡 TINGGI |
| `server/middleware.py` | ~40 | Request middleware | 🟢 SEDANG |
| `plugins/lyrics.py` | 160 | Actual fetch behavior (hanya stub test) | 🟡 TINGGI |
| `plugins/notifications.py` | 168 | Notification render, blocking read loop | 🟡 TINGGI |
| `plugins/sponsorblock.py` | 72 | Segment fetch, skip logic | 🟡 TINGGI |
| `core/observability.py` | ~60 | Prometheus metrics counters | 🟢 SEDANG |
| `core/background_tasks.py` | ~50 | Cleanup tasks scheduler | 🟡 TINGGI |
| `core/value_objects.py` | ~40 | VideoId validator (partial via SSRF test) | 🟡 TINGGI |
| `core/utils.py` | ~30 | Utility functions | 🟢 SEDANG |

### 2.2 Frontend JavaScript — Tidak Diuji Sama Sekali

| Modul | Fungsi Kritis | Risiko |
|---|---|---|
| `ws.js` | WebSocket connect, reconnect, message dispatch | 🔴 KRITIS |
| `store.js` | Global state management, password in-memory | 🔴 KRITIS |
| `audio.js` | Browser audio sync, seek, buffering | 🔴 KRITIS |
| `actions.js` | Semua user action handlers | 🔴 KRITIS |
| `services/auth.js` | Login flow, token storage | 🔴 KRITIS |
| `render/player.js` | Player UI render | 🟡 TINGGI |
| `render/queue.js` | Queue render, drag-drop | 🟡 TINGGI |
| `render/lyrics.js` | Lyrics scroll, sync | 🟡 TINGGI |
| `render/search.js` | Search result render | 🟡 TINGGI |
| `render/discover.js` | Discover panel render | 🟢 SEDANG |
| `render/favorites.js` | Favorites list render | 🟢 SEDANG |
| `events/*.js` | Event handler wiring | 🟡 TINGGI |
| `portal.js` | Modal/portal management | 🟢 SEDANG |
| `dom.js` | DOM element cache | 🟢 SEDANG |
| `platform/*.js` | Touch, keyboard, viewport | 🟢 SEDANG |

---

## 3. Temuan Kritis per Kategori

---

### AUDIT-TEST-001 — Structural Tests Bukan Behavioral Tests
**Severity:** 🔴 KRITIS  
**Kategori:** Test Quality

**Dampak:** 8 dari 16 unit test file hanya memverifikasi bahwa *string tertentu ada dalam source code* (`inspect.getsource`). Ini bukan testing — ini source scanning. Test lulus bahkan jika logika salah, selama kata yang dicari ada di source.

**Lokasi:** `tests/unit/engine/test_queue_locking.py`, `tests/unit/engine/test_radio.py`, `tests/unit/cache/test_resolver.py`, `tests/unit/server/test_security.py`, `tests/unit/server/test_ws_broadcast.py`, `tests/unit/plugins/test_lyrics_parser.py`

**Contoh masalah:**
```python
# tests/unit/engine/test_queue_locking.py
def test_on_queue_remove_uses_lock(self):
    source = inspect.getsource(QueueCommands.on_queue_remove)
    assert "async with self.playback_controller._lock" in source
    # Test ini lulus BAHKAN JIKA lock ada tapi tidak pernah di-acquire
    # karena ada bug logika lain di sekitarnya
```

**Solusi — Ganti dengan behavioral test:**
```python
@pytest.mark.asyncio
async def test_queue_remove_acquires_lock(self):
    """Lock harus di-hold selama operasi remove berlangsung."""
    lock_acquired_during_remove = []
    original_remove = QueueCommands.on_queue_remove

    async def patched_remove(self, cmd):
        # Verifikasi lock sudah di-acquire SEBELUM masuk body
        assert self.playback_controller._lock.locked(), \
            "Lock harus di-acquire saat on_queue_remove berjalan"
        lock_acquired_during_remove.append(True)
        return await original_remove(self, cmd)

    # ... setup dan assert
    assert len(lock_acquired_during_remove) == 1
```

---

### AUDIT-TEST-002 — Integration Test Kosong Tanpa Assertion
**Severity:** 🔴 KRITIS  
**Kategori:** Test Completeness

**Dampak:** `test_metrics_rejects_external_ip` di `test_fase1.py` adalah **test kosong** — hanya berisi `pass`. Test ini lulus selalu, memberikan false confidence bahwa proteksi metrics dari IP eksternal berfungsi, padahal tidak diverifikasi sama sekali.

**Lokasi:** `tests/integration/test_fase1.py`, baris ~54–77

**Kode bermasalah:**
```python
@pytest.mark.asyncio
async def test_metrics_rejects_external_ip(self, aiohttp_client, ...):
    """..."""
    app = create_app(...)
    # ...
    with patch("server.handlers.http.get_metrics_content"):
        with patch("aiohttp.web.BaseRequest.remote", new_callable=pytest.MonkeyPatch):
            pass   # ← TIDAK ADA ASSERTION APAPUN
        pass       # ← TEST SELALU LULUS
```

**Solusi:**
```python
@pytest.mark.asyncio
async def test_metrics_rejects_external_ip(self, aiohttp_client, mock_room_manager, mock_ytdlp, mock_db):
    """Endpoint /metrics harus mengembalikan 403 untuk IP non-localhost."""
    app = create_app(mock_room_manager, mock_ytdlp, mock_db, mock_room_manager)
    app["command_bus"] = AsyncMock()
    app["event_bus"] = AsyncMock()
    client = await aiohttp_client(app)

    # Patch peered_ip agar tampak seperti IP eksternal
    with patch("server.handlers.http._get_client_ip", return_value="203.0.113.5"):
        with patch.dict(os.environ, {}, clear=True):  # Hapus LUNAWAVE_METRICS_TOKEN
            resp = await client.get("/metrics")
            assert resp.status == 403, \
                f"IP eksternal harus mendapat 403, bukan {resp.status}"
```

---

### AUDIT-TEST-003 — Tidak Ada Test untuk Critical Path: MPV Controller
**Severity:** 🔴 KRITIS  
**Kategori:** Coverage Gap

**Dampak:** `engine/mpv_controller.py` adalah **jantung aplikasi** (300 baris, 18 method). Tidak ada satu pun test. Logic berikut sepenuhnya tidak diuji:
- Reconnect loop (`_do_connect` dengan retry exponential backoff)
- Event parsing dari IPC socket (`_observe_events`, `_handle_event`)
- Error handling saat socket putus di tengah playback
- Concurrent `_send_request` race condition

**Lokasi:** `engine/mpv_controller.py`

**Solusi — Gunakan mock IPC socket:**
```python
# tests/unit/engine/test_mpv_controller.py
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from engine.mpv_controller import MPVController

@pytest.fixture
def mock_reader_writer():
    """Fake asyncio StreamReader/StreamWriter pair."""
    reader = AsyncMock()
    writer = AsyncMock()
    writer.is_closing = MagicMock(return_value=False)
    return reader, writer

@pytest.mark.asyncio
async def test_mpv_connect_success(mock_reader_writer):
    reader, writer = mock_reader_writer
    ctrl = MPVController(socket_path="/tmp/fake.sock")

    with patch("asyncio.open_unix_connection", return_value=(reader, writer)):
        await ctrl._do_connect()
        assert ctrl._writer is writer

@pytest.mark.asyncio
async def test_mpv_reconnect_after_disconnect():
    """Harus reconnect otomatis saat koneksi drop."""
    ctrl = MPVController(socket_path="/tmp/fake.sock")
    ctrl._connected = False
    ctrl._reconnect_attempts = 0
    call_count = [0]

    async def fake_connect(path):
        call_count[0] += 1
        if call_count[0] < 3:
            raise ConnectionRefusedError("not ready")
        reader, writer = AsyncMock(), AsyncMock()
        writer.is_closing = MagicMock(return_value=False)
        return reader, writer

    with patch("asyncio.open_unix_connection", side_effect=fake_connect):
        with patch("asyncio.sleep"):  # Skip delay
            await ctrl._do_connect()
    assert call_count[0] == 3  # Harus retry 2x sebelum berhasil

@pytest.mark.asyncio
async def test_handle_event_end_of_file_publishes_event():
    """Event 'end-file' dari MPV harus di-publish ke EventBus."""
    from core.event_bus import EventBus
    from core.events import TrackEndedEvent
    bus = EventBus()
    received = []
    bus.subscribe(TrackEndedEvent, lambda e: received.append(e))

    ctrl = MPVController(socket_path="/tmp/fake.sock", event_bus=bus)
    ctrl._connected = True

    await ctrl._handle_event({"event": "end-file", "reason": "eof"})

    assert len(received) == 1
```

---

### AUDIT-TEST-004 — Tidak Ada Test untuk Auth Handler (Login Flow)
**Severity:** 🔴 KRITIS  
**Kategori:** Security Testing Gap

**Dampak:** `server/handlers/auth.py` (76 baris) menangani login, pembuatan session, dan response cookie — tidak ada satu pun test. Ini adalah attack surface utama.

**Yang belum diuji:**
- Login dengan password benar → 302 redirect + Set-Cookie
- Login dengan password salah → 401
- Login brute force → rate limiting aktif
- Session cookie attributes (HttpOnly, SameSite, Secure)
- Logout → hapus session dari DB

**Solusi:**
```python
# tests/unit/server/test_auth_handler.py
@pytest.mark.asyncio
async def test_login_correct_password(aiohttp_client, mock_db):
    from core.security import hash_password
    from config import ADMIN_PASSWORD_HASH

    app = create_app(...)
    client = await aiohttp_client(app)

    resp = await client.post("/login", data={
        "password": os.environ.get("LUNAWAVE_ADMIN_PASS", "admin")
    }, allow_redirects=False)

    assert resp.status == 302
    assert "session" in resp.cookies or "Set-Cookie" in resp.headers

@pytest.mark.asyncio
async def test_login_wrong_password(aiohttp_client, mock_db):
    client = await aiohttp_client(create_app(...))
    resp = await client.post("/login", data={"password": "totally_wrong_pw"})
    assert resp.status in (401, 403)

@pytest.mark.asyncio
async def test_login_session_cookie_is_httponly(aiohttp_client, mock_db):
    client = await aiohttp_client(create_app(...))
    resp = await client.post("/login", data={"password": "..."}, allow_redirects=False)
    cookie_header = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in cookie_header, "Session cookie HARUS HttpOnly"
    assert "SameSite" in cookie_header, "Session cookie HARUS SameSite"
```

---

### AUDIT-TEST-005 — Tidak Ada Test untuk YtDlpClient
**Severity:** 🔴 KRITIS  
**Kategori:** Coverage Gap

**Dampak:** `engine/ytdlp_client.py` (168 baris) melakukan network call nyata ke YouTube. Tidak ada test dengan mock yt-dlp, sehingga:
- Bug di `_pick_audio_url` tidak terdeteksi
- `_to_track` tidak diuji dengan format response edge case
- Error handling saat yt-dlp timeout tidak diuji

**Lokasi:** `engine/ytdlp_client.py`

**Solusi — Mock yt-dlp dengan sample_track.json:**
```python
# tests/unit/engine/test_ytdlp_client.py
import pytest
from unittest.mock import patch, MagicMock
from engine.ytdlp_client import YtDlpClient

@pytest.mark.asyncio
async def test_search_returns_track_list(sample_track_json):
    client = YtDlpClient()
    mock_info = {
        "entries": [sample_track_json],
        "_type": "playlist"
    }
    with patch.object(client, "_extract_sync", return_value=mock_info):
        results = await client.search("rick astley")
    assert len(results) == 1
    assert results[0].video_id == "dQw4w9WgXcQ"
    assert results[0].title == "Never Gonna Give You Up"

@pytest.mark.asyncio
async def test_get_stream_url_picks_audio_url(sample_track_json):
    client = YtDlpClient()
    sample_track_json["url"] = "https://manifest.googlevideo.com/audio.webm"
    with patch.object(client, "_extract_sync", return_value=sample_track_json):
        url = await client.get_stream_url("dQw4w9WgXcQ")
    assert "googlevideo.com" in url

@pytest.mark.asyncio
async def test_get_stream_url_raises_on_empty_formats():
    client = YtDlpClient()
    bad_info = {"formats": [], "url": None}
    with patch.object(client, "_extract_sync", return_value=bad_info):
        with pytest.raises(Exception):
            await client.get_stream_url("badid12345a")

def test_to_track_handles_missing_fields():
    client = YtDlpClient()
    minimal_entry = {"id": "abc12345678", "title": "Test"}
    track = client._to_track(minimal_entry)
    assert track.video_id == "abc12345678"
    assert track.artist == ""  # Harus default kosong, bukan crash
    assert track.duration == 0
```

---

### AUDIT-TEST-006 — Tidak Ada Test untuk RadioEngine Logic
**Severity:** 🔴 KRITIS  
**Kategori:** Coverage Gap

**Yang ada:** Hanya 4 structural tests (cek string di source code).  
**Yang tidak ada:** Seluruh behavioral logic berikut tidak diuji:

- `_ensure_artists_loaded` — apakah fallback ke file JSON berfungsi saat DB kosong?
- `_gather_batch` — apakah deduplication video ID berfungsi?
- `_build_exclusion_set` — apakah set exclusion dibuild dengan benar?
- `check_prefetch` — kapan prefetch di-trigger berdasarkan posisi/durasi?
- Artist rotation deck — apakah artist pop dan push kembali dengan benar?

**Solusi:**
```python
# tests/unit/engine/test_radio_behavioral.py
@pytest.mark.asyncio
async def test_ensure_artists_loaded_from_db(tmp_path):
    """Artists harus diload dari DB jika tersedia."""
    from core.state import AppState
    from engine.radio_engine import RadioMode
    from unittest.mock import AsyncMock, MagicMock

    mock_db = MagicMock()
    mock_db.get_all_artists = AsyncMock(return_value=[
        {"name": "Radiohead", "genres": ["alternative"]},
        {"name": "Portishead", "genres": ["trip-hop"]},
    ])
    state = AppState()
    radio = RadioMode(ytdlp=MagicMock(), state=state, db=mock_db)

    await radio._ensure_artists_loaded()

    assert len(radio._artist_pool) == 2
    mock_db.get_all_artists.assert_called_once()

@pytest.mark.asyncio
async def test_build_exclusion_set_includes_current_and_queue():
    """Exclusion set harus termasuk current track dan isi queue."""
    from core.state import AppState, TrackInfo
    from engine.radio_engine import RadioMode

    state = AppState()
    state.current_track = TrackInfo(
        video_id="current111", title="Current", artist="A", duration=200
    )
    state.queue = [
        TrackInfo(video_id="queued1111", title="Q1", artist="B", duration=180),
        TrackInfo(video_id="queued2222", title="Q2", artist="C", duration=200),
    ]
    radio = RadioMode(ytdlp=MagicMock(), state=state)
    exclusion = radio._build_exclusion_set()

    assert "current111" in exclusion
    assert "queued1111" in exclusion
    assert "queued2222" in exclusion

def test_check_prefetch_triggers_at_threshold():
    """Prefetch harus di-trigger saat posisi > (durasi - threshold)."""
    from core.state import AppState
    from engine.radio_engine import RadioMode
    from unittest.mock import MagicMock, patch

    state = AppState()
    radio = RadioMode(ytdlp=MagicMock(), state=state)
    radio._prefetch_triggered = False
    mock_controller = MagicMock()

    with patch.object(radio, "_prefetch_next") as mock_prefetch:
        # Tidak trigger: masih jauh dari akhir
        radio.check_prefetch(mock_controller, position=30.0, duration=200.0)
        mock_prefetch.assert_not_called()

        # Trigger: sudah dekat akhir
        radio.check_prefetch(mock_controller, position=185.0, duration=200.0)
        mock_prefetch.assert_called_once()
```

---

### AUDIT-TEST-007 — Tidak Ada Test untuk Resolver (Cache TTL Logic)
**Severity:** 🟡 TINGGI  
**Kategori:** Coverage Gap

**Yang ada:** Hanya structural test (cek apakah `STREAM_URL_TTL_SEC` ada di source).  
**Yang tidak ada:** Behavioral test untuk logika TTL itu sendiri.

**Solusi:**
```python
# tests/unit/cache/test_resolver_behavioral.py
@pytest.mark.asyncio
async def test_resolver_returns_cached_url_within_ttl(temp_db):
    """URL dalam TTL harus dikembalikan dari cache, bukan fetch ulang."""
    from cache.resolver import StreamResolver
    from unittest.mock import AsyncMock

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url = AsyncMock(return_value="https://googlevideo.com/new")

    resolver = StreamResolver(db=temp_db, ytdlp=mock_ytdlp)
    track = TrackInfo(video_id="cached00001", title="T", artist="A", duration=200)

    # Simpan URL dengan timestamp baru
    import time
    await temp_db.upsert_track(track, stream_url="https://googlevideo.com/old")
    # Paksa timestamp agar fresh
    await temp_db._conn.execute(
        "UPDATE tracks SET stream_url_ts = ? WHERE video_id = ?",
        (time.time(), "cached00001")
    )
    await temp_db._conn.commit()

    url = await resolver.resolve("cached00001")

    assert url == "https://googlevideo.com/old"  # Harus dari cache
    mock_ytdlp.get_stream_url.assert_not_called()  # Tidak perlu fetch ulang

@pytest.mark.asyncio
async def test_resolver_fetches_new_url_when_expired(temp_db):
    """URL yang expired harus di-fetch ulang."""
    from cache.resolver import StreamResolver
    from unittest.mock import AsyncMock
    import time

    mock_ytdlp = AsyncMock()
    mock_ytdlp.get_stream_url = AsyncMock(return_value="https://googlevideo.com/fresh")
    resolver = StreamResolver(db=temp_db, ytdlp=mock_ytdlp)

    track = TrackInfo(video_id="expired0001", title="T", artist="A", duration=200)
    await temp_db.upsert_track(track, stream_url="https://googlevideo.com/old")
    # Set timestamp di masa lalu (expired)
    await temp_db._conn.execute(
        "UPDATE tracks SET stream_url_ts = ? WHERE video_id = ?",
        (time.time() - 99999, "expired0001")
    )
    await temp_db._conn.commit()

    url = await resolver.resolve("expired0001")

    assert url == "https://googlevideo.com/fresh"
    mock_ytdlp.get_stream_url.assert_called_once_with("expired0001")
```

---

### AUDIT-TEST-008 — Tidak Ada Test untuk WS Command Handlers
**Severity:** 🔴 KRITIS  
**Kategori:** Coverage Gap

**Dampak:** Seluruh `server/handlers/ws/` (~8 file, ~400 baris) tidak diuji. Ini mencakup:
- `_handle_play_track` — apakah track diparsing benar dari data WS?
- `_handle_seek` — apakah value seek divalidasi?
- `_handle_queue_add` — apakah duplikat dicegah?
- `_handle_enqueue_artist_songs` — apakah artist_name divalidasi?

**Solusi:**
```python
# tests/unit/server/ws/test_playback_handlers.py
@pytest.mark.asyncio
async def test_handle_play_track_valid(mock_command_bus):
    from server.handlers.ws.playback_handlers import _handle_play_track
    from unittest.mock import AsyncMock, MagicMock
    from core.state import AppState

    state = AppState()
    ws = AsyncMock()
    manager = MagicMock()
    db = AsyncMock()
    ytdlp = AsyncMock()
    command_bus = AsyncMock()

    data = {"video_id": "dQw4w9WgXcQ", "title": "Test", "artist": "A", "duration": 200}
    await _handle_play_track(data, ws, state, ytdlp, manager, db, command_bus)

    command_bus.execute.assert_called_once()

@pytest.mark.asyncio
async def test_handle_play_track_missing_video_id(mock_command_bus):
    from server.handlers.ws.playback_handlers import _handle_play_track
    from unittest.mock import AsyncMock, MagicMock

    ws = AsyncMock()
    data = {"title": "No ID"}  # video_id hilang
    await _handle_play_track(data, ws, MagicMock(), AsyncMock(), MagicMock(), AsyncMock(), AsyncMock())

    # Harus kirim error, bukan crash
    ws.send_json.assert_called()
    sent = ws.send_json.call_args[0][0]
    assert sent["type"] == "error"
```

---

### AUDIT-TEST-009 — Tidak Ada Test untuk SponsorBlock Plugin
**Severity:** 🟡 TINGGI  
**Kategori:** Coverage Gap

**Yang tidak diuji:**
- `fetch_segments` dengan response JSON valid
- `fetch_segments` saat API tidak tersedia (timeout/error)
- `_on_progress` — apakah seek di-trigger pada waktu yang tepat?
- Apakah tidak ada double-seek saat segment sudah dilewati?

**Solusi:**
```python
# tests/unit/plugins/test_sponsorblock.py
@pytest.mark.asyncio
async def test_fetch_segments_parses_response():
    from plugins.sponsorblock import SponsorBlock
    from unittest.mock import AsyncMock, MagicMock, patch
    from core.state import AppState

    mock_mpv = AsyncMock()
    state = AppState()
    sb = SponsorBlock(mpv=mock_mpv, state=state)

    fake_response = [
        {"segment": [10.0, 25.0], "category": "sponsor"},
        {"segment": [90.0, 95.0], "category": "intro"},
    ]
    mock_session = AsyncMock()
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=fake_response)
    mock_session.get = AsyncMock(return_value=__aenter_ctx(mock_resp))

    sb._session = mock_session
    await sb.fetch_segments("dQw4w9WgXcQ")

    assert len(sb._segments) == 2
    assert sb._segments[0] == (10.0, 25.0)

@pytest.mark.asyncio
async def test_on_progress_seeks_past_segment():
    """Saat posisi masuk segment sponsor, seek ke akhir segment."""
    from plugins.sponsorblock import SponsorBlock
    from core.state import AppState
    from core.events import TrackProgressEvent

    mock_mpv = AsyncMock()
    state = AppState()
    sb = SponsorBlock(mpv=mock_mpv, state=state)
    sb._segments = [(10.0, 25.0)]  # Satu segment sponsor

    event = TrackProgressEvent(position=12.0, duration=200.0)
    await sb._on_progress(event)

    mock_mpv.seek.assert_called_once_with(25.0)
```

---

### AUDIT-TEST-010 — Frontend: Tidak Ada Test Runner Otomatis
**Severity:** 🔴 KRITIS  
**Kategori:** Frontend Testing Infrastructure

**Dampak:** `package.json` memiliki `"test": "echo \"Error: no test specified\" && exit 1"`. Seluruh 25 modul JavaScript tidak memiliki automated test. `test_helpers.html` adalah manual browser test yang tidak bisa di-run di CI.

**Yang perlu diuji tetapi tidak ada infrastrukturnya:**
- `ws.js`: reconnect logic, message parsing, heartbeat
- `store.js`: state mutation, subscriber notification
- `audio.js`: sync drift correction menggunakan `server_ts`
- `actions.js`: command dispatch ke WS
- `services/auth.js`: token storage, session check

**Solusi — Setup Vitest:**
```json
// package.json (tambahkan)
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  },
  "devDependencies": {
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0",
    "jsdom": "^24.0.0",
    "happy-dom": "^13.0.0"
  }
}
```

```javascript
// tests/js/utils.test.js
import { describe, it, expect } from 'vitest'
import { formatTime, escapeHtml, cleanTrackTitle } from '../../web/static/js/utils.js'

describe('formatTime', () => {
  it('formats zero as 00:00', () => expect(formatTime(0)).toBe('00:00'))
  it('formats 65s as 01:05', () => expect(formatTime(65)).toBe('01:05'))
  it('handles negative values', () => expect(formatTime(-10)).toBe('00:00'))
  it('formats one hour as 60:00', () => expect(formatTime(3600)).toBe('60:00'))
})

describe('escapeHtml', () => {
  it('escapes script tags', () =>
    expect(escapeHtml('<script>alert("xss")</script>')).not.toContain('<script>'))
  it('escapes ampersand', () =>
    expect(escapeHtml('a&b')).toBe('a&amp;b'))
})
```

```javascript
// tests/js/store.test.js
import { describe, it, expect, vi } from 'vitest'

describe('store', () => {
  it('notifies subscribers on state change', () => {
    const callback = vi.fn()
    store.subscribe('status', callback)
    store.setState({ status: 'playing' })
    expect(callback).toHaveBeenCalledWith('playing')
  })
})
```

---

### AUDIT-TEST-011 — Mock Strategy Terlalu Longgar di E2E Tests
**Severity:** 🟡 TINGGI  
**Kategori:** Mock Quality

**Dampak:** Di `test_e2e.py`, `mock_db.verify_session` di-mock return `True` secara default. Ini membuat test autentikasi tidak realistis — semua token diterima, termasuk token kosong atau invalid.

**Kode bermasalah:**
```python
# tests/integration/test_e2e.py
@pytest.fixture
def mock_db():
    db = MagicMock(spec=DatabasePort)
    db.verify_session = AsyncMock(return_value=True)  # ← Selalu True! Tidak realistis
```

**Dampak konkret:** `test_e2e_websocket_auth_with_token` lulus bahkan dengan token `"test-token"` karena mock selalu menerima. Bug real (token tidak disimpan ke DB) tidak akan terdeteksi.

**Solusi — Mock berbasis state:**
```python
@pytest.fixture
def mock_db():
    valid_tokens = set()
    db = MagicMock(spec=DatabasePort)

    async def verify_session(token):
        return token in valid_tokens

    async def create_session(token, expires_at):
        valid_tokens.add(token)

    db.verify_session = AsyncMock(side_effect=verify_session)
    db.create_session = AsyncMock(side_effect=create_session)
    return db
```

---

### AUDIT-TEST-012 — Tidak Ada Test untuk Concurrency / Race Condition
**Severity:** 🔴 KRITIS  
**Kategori:** Concurrency Testing

**Dampak:** Aplikasi ini heavily concurrent (asyncio, multiple WS clients, background tasks). Tidak ada satu pun test yang mensimulasikan concurrent access. Race conditions yang diketahui ada (nested lock, competing reconnect) tidak diverifikasi dengan test.

**Solusi:**
```python
# tests/unit/engine/test_concurrency.py
@pytest.mark.asyncio
async def test_queue_concurrent_add_remove_no_deadlock():
    """Concurrent add dan remove tidak boleh deadlock."""
    from engine.queue_manager import QueueManager
    from core.state import AppState, TrackInfo

    state = AppState()
    qm = QueueManager(state=state)

    tracks = [TrackInfo(video_id=f"track{i:05d}", title=f"T{i}", artist="A", duration=200)
              for i in range(20)]

    async def add_tracks():
        for t in tracks[:10]:
            await qm.add(t)

    async def remove_tracks():
        for _ in range(5):
            await qm.remove_at(0)
            await asyncio.sleep(0)

    # Jalankan concurrent, harus selesai dalam 5 detik tanpa deadlock
    await asyncio.wait_for(
        asyncio.gather(add_tracks(), remove_tracks()),
        timeout=5.0
    )

@pytest.mark.asyncio
async def test_multiple_ws_clients_receive_broadcast():
    """Semua WS client yang konek harus menerima broadcast yang sama."""
    # ... test dengan multiple concurrent WS connections
```

---

### AUDIT-TEST-013 — Tidak Ada Test untuk Notifications Plugin
**Severity:** 🟡 TINGGI  
**Kategori:** Coverage Gap

**Dampak:** `plugins/notifications.py` memiliki blocking thread (`_blocking_read_loop`) yang berjalan di thread pool. Tidak ada test untuk:
- Thread cleanup saat `cleanup()` dipanggil
- Event `TrackStartedEvent` memicu notifikasi
- Behavior saat notification daemon tidak tersedia

---

### AUDIT-TEST-014 — Tidak Ada Performance / Load Test
**Severity:** 🟡 TINGGI  
**Kategori:** Performance Testing

**Dampak:** Tidak ada benchmark atau load test untuk:
- Berapa banyak concurrent WS connection yang bisa ditangani?
- Apakah broadcast ke N client menyebabkan latency?
- Memory usage saat radio mode berjalan 24 jam?

**Solusi — Benchmark minimal dengan pytest-benchmark:**
```python
# tests/performance/test_broadcast_perf.py
def test_broadcast_100_clients_latency(benchmark):
    """Broadcast ke 100 client harus selesai dalam < 50ms."""
    async def run():
        manager = ConnectionManager()
        # Simulasi 100 WS client
        clients = [AsyncMock() for _ in range(100)]
        for c in clients:
            manager.connections["room1"].add(c)

        await manager.broadcast("room1", {"type": "state", "data": {}})

    result = benchmark(asyncio.run, run())
    # pytest-benchmark otomatis report timing
```

---

### AUDIT-TEST-015 — Fixture Tunggal `sample_track.json` Tidak Cukup
**Severity:** 🟢 SEDANG  
**Kategori:** Test Data

**Dampak:** Hanya ada satu fixture file JSON. Tidak ada fixture untuk:
- Track dengan thumbnail `None`
- Track dengan judul mengandung karakter Unicode
- Track dengan durasi sangat panjang (> 1 jam)
- Response yt-dlp dengan format DASH vs non-DASH
- Response yt-dlp yang cacat/partial (error case)

**Solusi:**
```json
// tests/fixtures/track_no_thumbnail.json
{
    "id": "nullthumb001",
    "title": "Track Without Thumbnail 𝄞",
    "uploader": "Artist Üñíçödé",
    "duration": 4321,
    "thumbnail": null,
    "formats": [...]
}

// tests/fixtures/track_live.json — track live stream
// tests/fixtures/track_yt_error.json — simulasi error response
```

---

## 4. Coverage Estimate per Modul

| Modul | Estimated Coverage | Keterangan |
|---|---|---|
| `core/event_bus.py` | 80% | Test baik, tapi async callback belum diuji |
| `core/command_bus.py` | 85% | Baik |
| `core/state.py` | 60% | AppState dan AudioOutput diuji, PlayerStatus belum |
| `core/task_utils.py` | 90% | Sangat baik |
| `core/security.py` | 95% | Sangat baik |
| `core/value_objects.py` | 30% | Hanya diuji via structural test |
| `cache/db.py` | 55% | upsert/session diuji, backup/get_all/etc belum |
| `cache/resolver.py` | 10% | Hanya structural |
| `cache/repositories/*.py` | 0% | Tidak ada test |
| `engine/mpv_controller.py` | **0%** | Tidak ada test |
| `engine/radio_engine.py` | **8%** | 4 structural test saja |
| `engine/ytdlp_client.py` | **0%** | Tidak ada test |
| `engine/playback/controller.py` | **0%** | Tidak ada test |
| `engine/playback/playback_commands.py` | 15% | Hanya on_stop via fase0 |
| `engine/playback/queue_commands.py` | 5% | Hanya structural |
| `engine/playback/track_loader.py` | **0%** | Tidak ada test |
| `engine/playback/radio_commands.py` | **0%** | Tidak ada test |
| `engine/download_manager.py` | 20% | Partial via fase0 |
| `server/handlers/auth.py` | **0%** | Tidak ada test |
| `server/handlers/http.py` | 15% | Partial structural + 1 e2e |
| `server/handlers/websocket.py` | 20% | Partial via e2e |
| `server/handlers/ws/*.py` | **0%** | Tidak ada test |
| `server/services/broadcast_service.py` | 5% | Structural saja |
| `server/services/discover_service.py` | **0%** | Tidak ada test |
| `plugins/lyrics.py` | 10% | Init saja, behavior tidak diuji |
| `plugins/notifications.py` | **0%** | Tidak ada test |
| `plugins/sponsorblock.py` | **0%** | Tidak ada test |
| **JavaScript (semua)** | **~2%** | Hanya utils.js manual |
| **TOTAL ESTIMASI** | **~22–28%** | |

---

## 5. Critical Flow yang Belum Diuji

Berikut adalah **flow pengguna kritis** yang sama sekali tidak memiliki test end-to-end:

| ID | Flow Kritis | Risiko Jika Bug |
|---|---|---|
| CF-01 | User login → session dibuat → WS auth dengan token → command diterima | Data loss, unauthorized access |
| CF-02 | Play track → yt-dlp resolve URL → MPV play → progress events → track ended | App hang, silent failure |
| CF-03 | Track ended → auto-next (queue mode) → load track berikutnya | Playback berhenti, queue rusak |
| CF-04 | Track ended → auto-next (radio mode) → prefetch → play | Radio berhenti setelah 1 lagu |
| CF-05 | Stream URL expired (> 6 jam) → re-resolve → seamless playback lanjut | Playback error di tengah lagu |
| CF-06 | User disconnect WS → reconnect → state sync dengan server | State out-of-sync di client |
| CF-07 | Concurrent play dari 2 WS client admin → hanya 1 yang berhasil | Race condition, app crash |
| CF-08 | Download track → file tersimpan → serve via `/stream/local/` | Download tidak bisa diputar |
| CF-09 | Rate limit login (5 attempts) → block IP → tunggu → bisa login lagi | Security bypass |
| CF-10 | SponsorBlock segment fetch → posisi masuk segment → seek otomatis | Sponsor segment tidak dilewati |

---

## 6. Prioritas Implementasi Test

### Prioritas 1 — Segera (Sprint Berikutnya)

| # | Test yang Perlu Dibuat | Effort | Impact |
|---|---|---|---|
| P1-01 | `test_mpv_controller.py` — connect, reconnect, event handling | 3 hari | 🔴 Sangat Tinggi |
| P1-02 | `test_ytdlp_client.py` — search, get_stream_url dengan mock | 1 hari | 🔴 Sangat Tinggi |
| P1-03 | `test_auth_handler.py` — login, logout, brute force | 1 hari | 🔴 Sangat Tinggi |
| P1-04 | `test_resolver_behavioral.py` — TTL hit/miss | 1 hari | 🔴 Tinggi |
| P1-05 | Perbaiki `test_metrics_rejects_external_ip` (saat ini kosong) | 2 jam | 🔴 Tinggi |
| P1-06 | `test_radio_behavioral.py` — artist pool, exclusion set, prefetch trigger | 2 hari | 🔴 Tinggi |

### Prioritas 2 — Sprint +1

| # | Test yang Perlu Dibuat | Effort | Impact |
|---|---|---|---|
| P2-01 | `test_playback_commands.py` — on_play, on_next, on_prev, on_stop | 2 hari | 🟡 Tinggi |
| P2-02 | `test_ws_handlers.py` — semua WS command dengan mock command_bus | 2 hari | 🟡 Tinggi |
| P2-03 | `test_sponsorblock.py` — segment parse, skip logic | 1 hari | 🟡 Tinggi |
| P2-04 | `test_broadcast_service.py` — broadcast behavior (bukan structural) | 1 hari | 🟡 Tinggi |
| P2-05 | Setup Vitest + `utils.test.js`, `store.test.js`, `audio.test.js` | 2 hari | 🟡 Tinggi |
| P2-06 | `test_concurrency.py` — concurrent queue, multi-client broadcast | 2 hari | 🟡 Tinggi |

### Prioritas 3 — Sprint +2

| # | Test yang Perlu Dibuat | Effort | Impact |
|---|---|---|---|
| P3-01 | `test_discover_service.py` — recent, favorites, featured | 1 hari | 🟢 Sedang |
| P3-02 | `test_notifications.py` — event subscribe, thread cleanup | 1 hari | 🟢 Sedang |
| P3-03 | `test_track_loader.py` — load track, URL resolution | 1 hari | 🟢 Sedang |
| P3-04 | Critical flow E2E: CF-02, CF-03, CF-04 (play→ended→autonext) | 3 hari | 🟢 Sedang |
| P3-05 | Performance benchmark: broadcast latency, queue throughput | 1 hari | 🟢 Sedang |
| P3-06 | Tambah fixtures: track_no_thumbnail, track_unicode, track_error | 4 jam | 🟢 Sedang |

---

## 7. Rekomendasi Infrastruktur Testing

### 7.1 Tambahkan pytest-cov untuk coverage tracking

```bash
pip install pytest-cov
```

```ini
# pyproject.toml — tambahkan
[tool.pytest.ini_options]
addopts = "--cov=core --cov=engine --cov=cache --cov=server --cov=plugins --cov-report=term-missing --cov-fail-under=60"
```

### 7.2 Tambahkan GitHub Actions CI

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest --cov --cov-fail-under=60
      - run: npm ci && npm test
```

### 7.3 Pisahkan Slow Tests dengan Markers

```python
# Tambahkan ke test yang butuh network/external
@pytest.mark.slow
@pytest.mark.asyncio
async def test_real_ytdlp_search():  # Opsional, skip di CI cepat
    ...
```

```ini
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "slow: tests that require network or external processes",
    "integration: integration tests requiring full app stack",
]
```

### 7.4 Target Coverage Realistis

| Sprint | Target Coverage | Focus |
|---|---|---|
| Sekarang | 22–28% (baseline) | — |
| +1 | 45% | MPV, ytdlp, auth, resolver |
| +2 | 60% | Playback commands, WS handlers, radio |
| +3 | 75% | Frontend JS, concurrency, E2E critical flows |
| Production-ready | **80%+** | Semua modul, regression suite lengkap |

---

## 8. Quick Wins (Bisa Dikerjakan < 1 Hari)

1. **Fix test kosong** `test_metrics_rejects_external_ip` — 2 jam
2. **Ganti 8 structural tests** dengan behavioral tests menggunakan AsyncMock — 4 jam
3. **Tambah 5 fixture JSON** (edge cases) ke `tests/fixtures/` — 2 jam  
4. **Setup pytest-cov** di `pyproject.toml` — 30 menit
5. **Tambah `npm test` via Vitest** ke `package.json` — 2 jam
6. **Perbaiki mock_db** di `test_e2e.py` agar stateful — 1 jam

---

*Laporan ini dihasilkan dari analisis statis seluruh source code dan test suite. Estimasi coverage bersifat konservatif berdasarkan line counting dan path analysis tanpa menjalankan coverage tool (karena environment tidak memiliki MPV/ytdlp). Untuk angka akurat, jalankan: `pytest --cov --cov-report=html`.*
