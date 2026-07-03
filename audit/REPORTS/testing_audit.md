# Audit Testing — ytgui

> Sumber: codebase aktif (bukan backup/docs). Audit dilakukan terhadap 131 test case di 25 file test.

---

## 1. Ringkasan Umum

| Kategori | Jumlah |
|---|---|
| Total test case | 131 |
| File test | 25 |
| Test aktif (tidak di-skip/dead) | ~107 |
| Test struktural (inspect.getsource) | ~31 |
| Test behavioral (eksekusi nyata) | ~76 |
| Coverage estimate (Python) | **~27%** |
| Coverage JS/frontend | **0%** |

CI hanya menjalankan `pytest tests/ -v` tanpa flag `--cov`, sehingga tidak ada laporan coverage aktual yang dihasilkan.

---

## 2. Unit Test

### 2.1 `cache/`

**`test_db_upsert.py`** — 5 test, behavioral ✅
- `update_stream_url_only` preserves metadata (title/artist/duration)
- Timestamp diupdate setelah update URL
- `toggle_favorite` toggles state dengan benar

**`test_resolver.py`** — 4 test, struktural ⚠️
- Hanya mengecek keberadaan konstanta `STREAM_URL_TTL_SEC` dan apakah string tersebut ada di source code
- Tidak ada test terhadap logika `CacheResolver.resolve()` (cache hit, cache miss, TTL expired, fallback ke yt-dlp)

**Coverage `cache/db.py`:** ~30% — method yang tidak tersentuh: `increment_artist_click`, `get_genre_artists`, `get_all_artists`, `get_random_songs`, `get_artist_songs_strict`, `get_genre_songs`, `evict_stale_tracks`, `set_local_path`, `increment_play_count`

---

### 2.2 `core/`

**`test_app_state.py`** — 6 test, behavioral ✅
- Field `duration` di `AppState` dan `state_to_dict()`

**`test_audio_output_enum.py`** — 1 test, behavioral ✅
- `AudioOutput` mewarisi `str`, value konstanta benar

**`test_command_bus.py`** — 3 test, behavioral ✅
- Register dan execute handler
- Single-writer enforcement (duplicate register raises)
- Execute command tanpa handler raises

**`test_domain_events.py`** — 3 test, behavioral ✅
- Subscribe, publish, unsubscribe typed event
- Error boundary: handler crash tidak memblokir handler lain

**`test_event_bus.py`** — 5 test, behavioral ✅
- Concurrent dispatch dengan `asyncio.gather`
- Handler lambat tidak memblokir handler lain
- Mix sync/async handler
- Error isolation antar handler

**`test_event_bus_basic.py`** — 4 test, behavioral ✅
- Subscribe/publish dasar, unsubscribe, error boundary (duplikasi dari test_domain_events)

**`test_tasks.py`** — 9 test, behavioral ✅ + struktural
- `safe_create_task` signature, return type, error logging, callback sync/async, CancelledError handling
- Struktural: scan seluruh codebase untuk `asyncio.create_task()` langsung

**Tidak ada test untuk:** `core/log_config.py`, `core/observability.py`, `core/exceptions.py`, `core/utils.py`

---

### 2.3 `engine/`

**`test_queue_locking.py`** — 3 test, struktural ⚠️
- Hanya mengecek apakah string `async with self._lock` ada di source `_on_queue_remove`, `_on_queue_select`, `_on_next`
- Tidak ada test race condition aktual atau concurrent execution

**`test_radio.py`** — 4 test, struktural ⚠️
- Mengecek apakah kata "timeout" dan "40" ada di source `_fetch_and_play_initial` dan `_prefetch_next`
- Tidak ada test terhadap behavior retry, circuit breaker, atau simulasi timeout

**Tidak ada unit test behavioral untuk:**
- `engine/mpv_controller.py` — **seluruh file, 0%**
- `engine/volume_service.py` — **seluruh file, 0%**
- `engine/queue_manager.py` — **seluruh file, 0%**
- `engine/command_router.py` — **seluruh file, 0%**
- `engine/playback/track_loader.py` — **seluruh file, 0%**
- `engine/playback/controller.py` — ~10% (hanya retry_count reset + structural lock check)
- `engine/ytdlp_client.py` — **seluruh file, 0%**

---

### 2.4 `plugins/`

**`test_lyrics.py`** — 2 test, mixed ⚠️
- Session persistence: behavioral ✅
- `_current_generation` existence: behavioral ✅
- Tidak ada test terhadap fetch flow nyata (sukses, fallback, race condition generation)

**`test_lyrics_parser.py`** — 3 test, struktural ⚠️
- Cek keberadaan field dan string `_current_generation += 1` di source code
- Tidak ada test skenario: dua fetch concurrent, generation mismatch, hasil lama di-discard

**Tidak ada test untuk:**
- `plugins/sponsorblock.py` — **0%**
- `plugins/notifications.py` — **0%**

---

### 2.5 `server/`

**`test_auth.py`** — 12 test, behavioral ✅
- `hash_password` / `verify_password` lengkap: plaintext ditolak, salt unik, unicode, edge case kosong
- Ini salah satu test suite paling solid di seluruh codebase

**`test_http_handlers.py`** — 3 test, sebagian **dead code** 🔴
- `test_index_html_has_defer_script`: behavioral ✅
- `test_stream_proxy_cache_control`: **dead** — badan test diawali `return` sebelum assertion
- `test_chunk_size_is_16kb`: **dead** — badan test diawali `return` sebelum assertion

**`test_middleware.py`** — 6 test, sebagian **dead code** 🔴
- `test_command_history_has_cleanup`: behavioral ✅
- `test_login_attempts_has_cleanup`: **dead** — diawali `return`
- `test_command_history_initialized_as_dict`: behavioral ✅
- `test_login_attempts_initialized_as_dict`: behavioral ✅
- `test_rate_limit_threshold`: behavioral ✅
- `test_login_rate_limit_threshold`: **dead** — diawali `return`

**`test_security.py`** — 6 test, struktural ⚠️
- Semua mengecek keberadaan string (`urlparse`, `googlevideo.com`, `is_relative_to`) di source
- Tidak ada test serangan nyata: URL dengan scheme `file://`, path traversal `../../etc/passwd`, domain `evil.googlevideo.com.attacker.com`

**`test_session.py`** — 9 test, behavioral ✅
- Schema tabel, create/verify/delete/cleanup session
- Expired token ditolak, nonexistent token ditolak

**`test_ws_broadcast.py`** — 3 test, struktural ⚠️
- Mengecek keberadaan string `server_ts`, `time.time()`, `"position"` di source broadcast_service
- Tidak ada test terhadap payload aktual yang dikirim ke client

---

## 3. Integration Test

**`test_e2e.py`** — 6 test, behavioral ✅ (terbaik)
- `/health` endpoint: status + db connected
- `/metrics` endpoint: format Prometheus
- WebSocket connect: menerima initial state
- WS auth dengan token: `auth_status.success = true`
- WS search command: hasil dikembalikan dengan benar
- WS command tanpa auth: ditolak dengan pesan error

Menggunakan `aiohttp_client` + mock DB/ytdlp yang solid (spec-based).

**`test_fase0.py`** — 22 test, mixed
- `_TITLE_NOISE_WORDS` frozenset: behavioral ✅
- Retry count reset di `_on_stop`: behavioral ✅
- Background task cancel saat `on_deactivated`: behavioral ✅ (dengan mock task)
- Download manager signature: behavioral ✅
- Rate limit key eviction: sebagian **behavioral logic di test sendiri**, bukan di SUT

**`test_fase1.py`** — 9 test, mixed
- Password security: behavioral ✅
- Config ENV hashing: behavioral ✅ (reload module)
- Metrics protection: partially behavioral (beberapa assertion di-pass/skip)
- Next bypass removal: struktural (string search)

**`test_patch_0_09_10_11_server_perf.py`** — 3 test (duplikat dari `test_http_handlers.py`, path berbeda)

---

## 4. API Test

Tidak ada test yang menguji `YtDlpClient` secara langsung. Dependency yt-dlp selalu di-mock di integration test. Tidak ada contract test atau VCR cassette untuk respons yt-dlp/SponsorBlock/lyrics.

---

## 5. Widget / Frontend Test

**Tidak ada.** Direktori `web/static/js/` mengandung ~15 file JS dengan logika signifikan:

- `ws.js` — WebSocket reconnect, message dispatch, queue sync
- `audio.js` — Browser audio playback, MediaSession API
- `events/player-events.js` — State rendering dari WS events
- `render/discover.js` — Artist/genre grid rendering
- `services/auth.js` — Token management

Tidak ada test runner (Jest, Vitest, Playwright) yang dikonfigurasi.

---

## 6. Mock Quality

| Lokasi | Kualitas | Catatan |
|---|---|---|
| `test_e2e.py` | ✅ Baik | `AsyncMock` + `spec=DatabasePort` + `spec=PlaybackController` |
| `test_fase0.py` | ✅ Baik | PlaybackController di-construct manual, dependensi di-mock |
| `test_fase1.py` | ⚠️ Partial | Beberapa test assertion di-`pass` tanpa validasi |
| Unit engine tests | 🔴 Lemah | Mayoritas struktural, tidak ada mock runtime behavior |
| Unit plugin tests | 🔴 Lemah | Tidak ada mock `aiohttp.ClientSession` untuk lyrics/sponsorblock |

---

## 7. Regression Risk

Test yang bersifat struktural (`inspect.getsource`) akan **false-positive** jika:
- Kode direfactor tanpa mengubah perilaku (rename variabel, restrukturisasi if/else)
- String yang dicari ada di komentar atau dead code

File dengan test dead (early `return`):
- `tests/unit/server/test_http_handlers.py` — 2 test mati
- `tests/unit/server/test_middleware.py` — 2 test mati

---

## 8. Coverage Estimate per Modul

| Modul | Est. Coverage | Jenis Test |
|---|---|---|
| `core/command_bus.py` | ~85% | Behavioral |
| `core/event_bus.py` | ~80% | Behavioral |
| `core/task_utils.py` | ~85% | Behavioral |
| `core/security.py` | ~90% | Behavioral |
| `core/state.py` | ~65% | Behavioral |
| `cache/db.py` | ~30% | Behavioral (subset method) |
| `cache/resolver.py` | ~5% | Struktural saja |
| `server/handlers/auth.py` | ~40% | Via integration |
| `server/handlers/http.py` | ~25% | Struktural + 2 test mati |
| `server/handlers/websocket.py` | ~20% | Struktural + integration |
| `server/middleware.py` | ~25% | Struktural + 2 test mati |
| `server/serializers.py` | ~35% | Via test_app_state |
| `server/services/broadcast_service.py` | ~10% | Struktural saja |
| `engine/playback/controller.py` | ~12% | Behavioral partial |
| `engine/radio_engine.py` | ~15% | Mix struktural/behavioral |
| `engine/download_manager.py` | ~25% | Signature + callable |
| `plugins/lyrics.py` | ~15% | Struktural |
| `engine/mpv_controller.py` | **0%** | Tidak ada test |
| `engine/volume_service.py` | **0%** | Tidak ada test |
| `engine/queue_manager.py` | **0%** | Tidak ada test |
| `engine/command_router.py` | **0%** | Tidak ada test |
| `engine/playback/track_loader.py` | **0%** | Tidak ada test |
| `engine/ytdlp_client.py` | **0%** | Tidak ada test |
| `plugins/sponsorblock.py` | **0%** | Tidak ada test |
| `plugins/notifications.py` | **0%** | Tidak ada test |
| `services/discover_service.py` | **0%** | Tidak ada test |
| `web/static/js/*` | **0%** | Tidak ada test runner |

**Estimasi keseluruhan (Python): ~27%**

---

## 9. Yang Belum Diuji

### Critical (penggunaan runtime utama, tidak ada test sama sekali)

1. **`PlaybackController.play_track()`** — Flow lengkap: resolve URI, `mpv.play()`, volume branching DEVICE vs BROWSER, `TrackStartedEvent`, retry pada error, backoff
2. **`PlaybackController._on_track_ended()`** — Transisi QUEUE → next, RADIO → next, retry count increments, state reset
3. **`CacheResolver.resolve()`** — Cache hit, cache miss (resolve via yt-dlp), TTL expired (refresh), race condition
4. **`MpvController`** — Semua method: connect, play, pause, resume, seek, `_handle_event` (property-change, end-file), reconnect logic
5. **`VolumeService._apply_volume()`** — Branching DEVICE (set mpv volume) vs BROWSER (set 0), clamping 0–100
6. **`QueueMode.next()`** — Queue kosong (IDLE), queue tidak kosong (play next)

### High (fitur penting, zero behavioral coverage)

7. **`SponsorBlockHandler._on_progress()`** — Segment skip saat posisi masuk range, state `sponsorblock_active = False` (no-op)
8. **`SponsorBlockHandler.fetch_segments()`** — HTTP 200 (parse segments), HTTP 404 (kosong), network error (graceful)
9. **`LyricsFetcher.fetch()`** — Fetch berhasil, generation mismatch (hasil lama dibuang), concurrent fetch cancel
10. **`PlaybackController._on_queue_*`** — add, remove, replace, reorder, select by index
11. **`DiscoverService`** — `get_recent`, `get_favorites`, `get_cached`, `get_featured_artists/genres` (DB integration)
12. **`PlaybackController._on_prev()`** — History non-empty, history kosong

### Medium (fitur sekunder atau platform-spesifik)

13. **`TrackLoader.load_track()`** — resolve + background tasks (sponsorblock + lyrics) diluncurkan
14. **`CommandRouter`** — Route CMD_* ke PlaybackController/VolumeService yang benar
15. **`PlaybackController._on_set_output()`** — Transisi DEVICE → BROWSER (mpv volume 0), BROWSER → DEVICE (restore)
16. **`PlaybackController._on_seek()`** — Forward mpv.seek, state.position diupdate
17. **`Database.increment_play_count()`**, `evict_stale_tracks()`, `get_random_songs()`, `get_artist_songs_strict()`
18. **`TermuxNowPlaying`** — Platform guard (no-op jika `termux-notification` tidak ada), FIFO reader thread

### Low / Infrastruktur

19. **`YtDlpClient.search()`** — Mock yt-dlp response, parse entry fields, duration fallback
20. **`YtDlpClient.get_stream_url()`** — Cache file check, yt-dlp extraction, timeout
21. **`server/handlers/http.py`** — Actual request/response: SSRF rejection, path traversal rejection, chunk streaming
22. **JS Frontend** — WebSocket reconnect, audio buffer switching, MediaSession API, lyrics sync rendering

---

## 10. Prioritas Test

### P0 — Tulis sekarang (critical path, zero coverage)

```
tests/unit/engine/test_playback_controller.py
  - test_play_track_success()             # mock mpv + resolver, cek TrackStartedEvent
  - test_play_track_error_retries()       # resolver raises, cek retry + backoff
  - test_on_track_ended_queue_mode()      # next dari queue
  - test_on_track_ended_radio_mode()      # next dari radio
  - test_on_stop_resets_state()           # (sudah ada, tapi perlu behavioral)
  - test_advance_to_next_empty_queue()    # idle saat queue kosong

tests/unit/cache/test_resolver.py  [extend]
  - test_resolve_cache_hit()
  - test_resolve_cache_miss_fetches_ytdlp()
  - test_resolve_expired_ttl_refreshes()

tests/unit/engine/test_volume_service.py
  - test_volume_up_clamps_at_100()
  - test_volume_down_clamps_at_0()
  - test_apply_volume_browser_output_sets_mpv_to_0()
  - test_apply_volume_device_output_uses_current_volume()
```

### P1 — Sprint berikutnya (high impact, mock-friendly)

```
tests/unit/engine/test_queue_manager.py
  - test_next_empty_queue_sets_idle()
  - test_next_pops_and_plays()

tests/unit/plugins/test_sponsorblock.py
  - test_fetch_segments_200()
  - test_fetch_segments_404_empty()
  - test_on_progress_skips_segment()
  - test_on_progress_noop_when_disabled()

tests/unit/engine/test_track_loader.py
  - test_load_track_launches_bg_tasks()
  - test_load_track_returns_uri()

tests/unit/plugins/test_lyrics_behavior.py
  - test_fetch_discards_stale_generation()
  - test_concurrent_fetch_only_last_wins()

tests/unit/server/test_http_handlers_behavior.py
  - test_ssrf_rejects_file_scheme()
  - test_ssrf_rejects_evil_domain()
  - test_path_traversal_rejected()
  - test_chunk_size_16kb_streaming()   # fix dari dead test
```

### P2 — Backlog (coverage completion)

```
tests/unit/services/test_discover_service.py
  - test_get_recent_returns_ordered_by_last_played()
  - test_get_favorites_returns_favorited_first()
  - test_get_recent_with_empty_db()

tests/unit/engine/test_command_router.py
  - test_volume_up_routes_to_volume_service()
  - test_play_track_routes_to_playback_controller()

tests/unit/cache/test_db_extra.py
  - test_increment_play_count()
  - test_evict_stale_tracks()
  - test_get_random_songs()

tests/unit/engine/test_mpv_controller.py
  - test_handle_event_time_pos_publishes_progress()
  - test_handle_event_end_file_eof()
  - test_play_when_disconnected_noop()
```

### P3 — Jangka panjang

- Setup Jest/Vitest untuk `web/static/js/` (ws.js, audio.js, player-events.js)
- Playwright E2E test untuk alur login → search → play
- Aktifkan `pytest --cov` di CI dengan threshold 60%
- Perbaiki 4 test yang dead (early `return`) di `test_middleware.py` dan `test_http_handlers.py`

---

## 11. Catatan Khusus

**Test struktural perlu diganti behavioral.** Sekitar 31 test menggunakan `inspect.getsource()` untuk mengecek apakah string tertentu ada di source code. Ini rapuh: akan false-positive jika string ada di komentar, dead code, atau refactoring mengubah nama tanpa mengubah perilaku. Prioritaskan penggantian dengan test yang benar-benar mengeksekusi kode.

**Konfigurasikan coverage di CI.** Tambahkan ke `ci.yml`:
```yaml
- name: Run tests with coverage
  run: pytest tests/ -v --cov=. --cov-report=term-missing --cov-fail-under=40
```

**Tambahkan `pytest-cov` ke `requirements-dev.txt`.**
