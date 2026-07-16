---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-16-064

total_entries: 64

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



---

## [2026-07-16] Audit launcher/ — Admin Lockout Total & Crash Thread Setelah GUI Ditutup
**ID:** `PATCH-2026-07-16-064`
**Tanggal:** 2026-07-16
**Ringkasan:** Audit mendalam pertama untuk `launcher/` (tkinter GUI server manager, sebelumnya belum pernah diaudit). Dua bug confirmed lewat eksekusi nyata:
(1) **Kontrak file `cache/admin_password.txt` tidak sinkron** — `launcher/gui/auth_panel.py` menulis password yang SUDAH di-hash ke file itu, padahal `config.py` (dan `config_security.generate_admin_password()`) membaca isi file sebagai plaintext mentah lalu meng-hash-nya sendiri di setiap startup server. Akibatnya password yang ditampilkan ke user di dialog first-run/reset TIDAK PERNAH cocok dengan hash yang dipakai server untuk verifikasi login — admin lockout total. Dibuktikan lewat skrip reproduksi yang meniru alur `config.py`: `verify_password(raw_password, ADMIN_PASSWORD)` selalu `False`. Fix: `_reset_password()` sekarang menulis raw password (root cause ada di kontrak antar-modul, bukan di `core.security`).
(2) **Race destroy vs background thread** — semua callback dari background thread (dependency checker, loop refresh status tiap 2 detik, log writer, restart timer, popup server-ready) memanggil `self.after()`/`app.after()` tanpa guard apapun. Begitu window GUI ditutup sementara thread masih berjalan, callback yang telat crash dengan `RuntimeError: main thread is not in main loop`. Direproduksi nyata lewat Xvfb headless + `threading.excepthook`. Fix: tambah flag `ServerManager._closing` (di-set di `destroy()`) dan helper `_safe_after()` yang dipakai di semua titik pemanggilan `.after()` dari thread/loop; loop `_refresh_status()` juga berhenti reschedule begitu closing.
**Catatan tooling:** ditemukan bug tambahan (belum di-fix, di luar scope sesi ini) di `automation/patchlog.py` — `parse_entries()` gagal mem-parse `docs/PATCHLOG.md` yang sudah ada (mengembalikan 0 entri walau ada 63 entri valid), sehingga `patchlog.py add` salah menomori ID baru jadi `-001` dan menimpa `total_entries` jadi `1`. File tidak sengaja sempat tertimpa saat sesi ini dan sudah dipulihkan dari arsip asli sebelum lanjut. **SUSPECTED root cause** (belum diverifikasi lebih lanjut): kemungkinan mismatch regex `ENTRY_RE` terhadap format aktual (spasi/newline ganda) di file nyata — perlu audit terpisah, jangan pakai `patchlog.py add` sampai ini diperbaiki, edit `docs/PATCHLOG.md` manual dulu.
**File Terdampak:**
- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/controller.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app_lifecycle.py`

---

## [2026-07-16] Data Integrity — Kolaborasi/Duet Lagu Hilang di Katalog Multi-Artis
**ID:** `PATCH-2026-07-16-063`
**Tanggal:** 2026-07-16
**Ringkasan:** Konfirmasi eksekusi nyata (bukan asumsi baca kode): `songs.youtube_id` punya constraint `UNIQUE` global, padahal lagu kolaborasi/duet (mis. "Separuh Aku" — Peterpan/NOAH/Ariel NOAH) sah dimiliki lebih dari satu artis. Akibatnya `data/export_to_sqlite.py` (dijalankan nyata terhadap `data/artists_enriched.json`) diam-diam membuang lagu itu dari katalog semua artis kecuali yang pertama ditemukan di JSON — 33 `youtube_id` di data nyata terpengaruh, total lagu ter-export turun dari 1000 jadi 963. Root cause bukan di logic exclusion radio (itu tetap sound, karena sudah keyed di `video_id` langsung, bukan pasangan `(artist_id, video_id)`), murni di schema. Fix: ganti constraint jadi composite `UNIQUE(artist_id, youtube_id)` di `persistence/schema.sql` (skema baru) + migrasi rebuild tabel untuk DB lama yang sudah ada di `persistence/__init__.py` (`_migrate_songs_unique_constraint`), plus scope ulang duplicate-check & duration-backfill di `data/export_to_sqlite.py` ke pasangan `(artist_id, youtube_id)`.
**File Terdampak:**
- `persistence/schema.sql`
- `persistence/__init__.py`
- `data/export_to_sqlite.py`
- `tests/unit/persistence/test_db.py`
- `tests/unit/data/test_export_to_sqlite.py`

---

## [2026-07-16] Race Condition — Pinned TCP Port MPV Diabaikan di Windows
**ID:** `PATCH-2026-07-16-062`
**Tanggal:** 2026-07-16
**Ringkasan:** Baseline test suite menemukan 1 test gagal (`test_mpv_connection_connect_windows`), dikonfirmasi lewat skrip reproduksi: di `adapters/mpv/connection.py`, `_do_connect()` pada path Windows (`os.name == "nt"`) *selalu* menimpa `self.tcp_port` dengan port dinamis hasil bind ke port 0 — bahkan ketika caller (constructor arg atau env var `YT_PLAYER_MPV_PORT`) sudah men-pin port tertentu. Ini merusak deployment yang butuh port tetap (mis. firewall rule spesifik). Root cause: tidak ada pembeda antara "port default fallback" vs "port yang sengaja dipin". Fix: tambah flag `_port_pinned` (True jika `tcp_port` di-pass eksplisit ke constructor ATAU dari env var), auto dynamic-port selection hanya jalan kalau `_port_pinned` False. Sekalian perbaiki pesan error `MpvConnectionError` yang sebelumnya selalu nampilin `os.environ.get('YT_PLAYER_MPV_PORT', 'N/A')` mentah (misleading — tidak reflect port dinamis aktual yang dipakai saat gagal connect), sekarang pakai `self.tcp_port` yang sebenarnya.
**File Terdampak:**
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`

---

**ID:** `PATCH-2026-07-15-061`
**Tanggal:** 2026-07-15
**Ringkasan:** Audit manual (bukan dari automation/, karena `event_graph.py` cs. hanya cek pub/sub event & arsitektur, bukan kelengkapan WS-action↔frontend-wiring) menemukan 5 fitur backend yang "orphan" (tidak reachable dari client) dan 1 dead code, ditemukan bertahap saat implementasi berjalan.
- **BUG-1 (Kritis, fitur baru sprint 3.3 tidak pernah tersambung):** Loudness Normalization — pipeline lengkap (`LoudnessService`, `gain_calculator.py`, `CMD_SET_LOUDNESS_NORMALIZATION` di `command_router.py`) sudah ada sejak sprint 3.3, tapi action `set_loudness_normalization` tidak pernah didaftarkan di `PLAYBACK_CMDS`/`handle_playback_command`, dan tidak ada UI toggle sama sekali. Fix: tambah action ke WS routing + toggle di Settings sheet (pola sama seperti Crossfade), termasuk sync `data-on` di `renderSettingsSheet()`.
- **BUG-2 (Kritis):** `queue_select` (`CMD_QUEUE_SELECT`) sudah full-implemented & full-tested di backend, tapi `queue-events.js` cuma daftarin click listener untuk `.qi-remove` — klik baris lagu di antrean manual tidak melakukan apapun. Fix: tambah click delegation di `queueList` yang kirim `queue_select` saat item (bukan drag handle/tombol hapus) diklik.
- **BUG-3 (Dead code + fitur mati sejak awal):** Drag-to-reorder queue (`_onDragStart` di `queue-events.js`) butuh elemen `.qi-drag` (CSS-nya sudah ada di `queue.css`), tapi `createQueueItemTemplate()` di `render/queue.js` tidak pernah membuat elemen itu — drag-reorder gak pernah bisa dipakai dari awal. Fix: tambah `<span class="qi-drag">` ke template, disembunyikan untuk current-track item (sama seperti tombol hapus).
- **BUG-4 (Dead code, query DB sia-sia):** `ws_discovery.py` action `discover` mengambil `ds.get_favorites(15)` tapi hasilnya dibuang — tidak dimasukkan ke payload `discover_data`. Kolom `is_favorite` + `toggle_favorite()` di `persistence/track_repo.py` sudah ada tapi datanya tidak pernah sampai ke client. Fix: masukkan `favorites` ke payload (di `ws_discovery.py` dan `ws_download.py` — dua tempat yang broadcast `discover_data`), tambah section "Favorit" di tab Discover (pola sama seperti "Tersimpan Lokal").
  - **Catatan lanjutan (belum dikerjakan, butuh keputusan desain terpisah):** `toggle_favorite()` di persistence masih belum ada command/WS action untuk memicunya (belum ada tombol "like"/heart di UI). Favorit saat ini hanya bisa terisi lewat kolom `play_count`/`is_favorite` yang di-set manual di DB. Fitur "like" penuh (heart button, `CMD_TOGGLE_FAVORITE`) sengaja tidak dibuat di patch ini karena itu fitur baru, bukan bug fix.
- **BUG-5 (Dead code sejak awal, ditemukan sampingan):** `dom.discRecent` di `dom.js` menunjuk ke `#discover-recent` yang tidak pernah ada di `index.html` — section "Baru Diputar" di tab Discover selalu `null`/dead. Fix: tambah container `#discover-recent` di `index.html`.
- **DITEMUKAN TAPI BELUM DIPERBAIKI (di luar scope patch ini, butuh konfirmasi):** `pytest` penuh menemukan 2 test gagal yang **tidak berkaitan** dengan perubahan patch ini — `test_app_state_defaults` (`core/state.py`: default `sponsorblock_active` seharusnya `True` tapi aktual `False`) dan `test_sponsorblock_on_progress_seeks_past_segment` (`plugins/sponsorblock.py`: seek tidak terpanggil saat posisi masuk segmen). Kedua file tidak disentuh oleh patch ini — kemungkinan regresi lama yang belum ketahuan. Perlu sesi audit terpisah.
**Verifikasi:** `ruff check` bersih, `mypy` bersih (4 file tersentuh), `pytest` 456 passed/2 failed-pre-existing/4 skipped, `vitest run` 14/14 passed, `automation/doctor.py` skornya identik dengan sebelum patch (tidak ada regresi arsitektur/dokumentasi/keamanan baru).
**File Terdampak:**
- `server/handlers/websocket.py`
- `server/handlers/ws_playback.py`
- `server/handlers/ws_discovery.py`
- `server/handlers/ws_download.py`
- `web/static/index.html`
- `web/static/js/dom.js`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/queue-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/render/discover-tab.js`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `tests/unit/server/handlers/test_ws_download.py`
- `tests/frontend/test_ws-routing.test.js`

---

## [2026-07-15] Test Coverage — Sesi Audit Bug Fix
**ID:** `PATCH-2026-07-15-060`
**Tanggal:** 2026-07-15
**Ringkasan:** Penambahan test yang hilang pasca-implementasi PATCH-058 dan PATCH-059.
- `test_websocket.py`: Tambah `test_new_playback_actions_are_routed` (parametrize 5 action: stop, set_sleep_timer, set_speed, set_loop, set_crossfade), `test_cache_commands_are_routed`, `test_unknown_action_does_not_crash`.
- `test_serializers.py`: Tambah assert untuk 3 field baru di `state_to_dict` (playback_speed, loop_mode, crossfade_enabled) termasuk verifikasi nilai non-default.
**File Terdampak:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_serializers.py`

---


**ID:** `PATCH-2026-07-15-059`
**Tanggal:** 2026-07-15
**Ringkasan:** Audit runtime menemukan 3 bug lanjutan setelah PATCH-058.
- **BUG-A (Kritis):** `server/serializers.py` tidak menyertakan `playback_speed`, `loop_mode`, `crossfade_enabled` di payload state WS. Akibatnya toggle crossfade tidak bisa di-sync dari server, speed tidak persist setelah reconnect, loop mode button tidak reflect state server. Fix: tambahkan 3 field ke `state_to_dict()`.
- **BUG-B (Kritis):** Kecepatan pemutaran hanya dikirim ke MPV (hanya berlaku untuk output Device). Browser audio (`<audio>`) tidak punya hook ke MPV property. Fix: tambahkan `audio.playbackRate = speed` di `settings-events.js` dan `full-state.js`.
- **IMPROVE-C:** Sleep timer tidak punya feedback visual — subtitle hanya menampilkan "15 Menit" statis. Fix: tambahkan countdown timer client-side yang mundur detik per detik dan reset ke "Mati" saat habis.
**File Terdampak:**
- `server/serializers.py`
- `web/static/js/render/full-state.js`
- `web/static/js/events/settings-events.js`

---


**ID:** `PATCH-2026-07-15-058`
**Tanggal:** 2026-07-15
**Ringkasan:** Audit pasca-implementasi T1–T16 menemukan 4 bug kritis dan 2 bug minor yang menyebabkan beberapa fitur baru tidak berfungsi dari frontend.
- **BUG-1 (Kritis):** `PLAYBACK_CMDS` di `server/handlers/websocket.py` tidak mencakup 5 action baru (`stop`, `set_sleep_timer`, `set_speed`, `set_loop`, `set_crossfade`). WebSocket menerima pesan tapi diam-diam mengabaikannya. Fix: tambahkan 5 action ke set.
- **BUG-2 (Kritis):** `store.js` tidak punya field `crossfade_enabled`. Fix: tambahkan `crossfade_enabled: false` ke `createStore()`.
- **BUG-3 (Kritis):** `transport-events.js` membaca `store.loopMode` (camelCase) padahal store memakai `store.loop_mode` (snake_case). Tombol Repeat selalu cycle ke "track". Fix: rename ke `loop_mode`.
- **BUG-4 (Kritis):** `queue_manager.py` punya dead code `pass` di blok `loop_mode == "queue"` saat queue kosong. Fix: hapus blok if/pass yang tidak berguna.
- **MINOR-1:** `core/state.py` mendefinisikan `playback_speed` dan `loop_mode` dua kali di dataclass. Fix: hapus duplikat.
- **MINOR-2:** `settings-events.js` mendaftarkan listener `sbToggle.click` dua kali, yang kedua mengirim action `toggle_sponsorblock` yang tidak ada handler-nya. Fix: hapus listener duplikat.
**File Terdampak:**
- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/events/transport-events.js`
- `engine/queue_manager.py`
- `core/state.py`
- `web/static/js/events/settings-events.js`

---


**ID:** `PATCH-2026-07-15-057`
**Tanggal:** 2026-07-15
**Ringkasan:** T16: Implementasi efek crossfade eksperimental. Menambah `crossfade_enabled` di state, command `CMD_SET_CROSSFADE`, pengaturan UI di Settings, fade-out manual 2 detik di `controller.py`, fade-in di `controller.py` saat putar track baru untuk DEVICE output, dan JS client-side volume fade untuk BROWSER output. Refactoring crossfade dilakukan dengan memisahkan logika ke `crossfade.py` untuk menjaga ukuran file `controller.py` di bawah batas.
**File Terdampak:**
- `core/state.py`
- `core/commands.py`
- `engine/command_router.py`
- `engine/playback/mode_ops.py`
- `engine/playback/controller.py`
- `engine/playback/crossfade.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `web/static/js/dom.js`
- `docs/ADR/003-Crossfade.md`

---

## [2026-07-15] Queue Duration UI (Tier 2 - T15)
**ID:** `PATCH-2026-07-15-056`
**Tanggal:** 2026-07-15
**Ringkasan:** T15: Penambahan informasi jumlah lagu dan total durasi estimasi secara real-time pada footer panel "Antrean Putar".
**File Terdampak:**
- `web/static/js/render/queue.js`

---

## [2026-07-15] Retry Stream Indicator (Tier 2 - T14)
**ID:** `PATCH-2026-07-15-055`
**Tanggal:** 2026-07-15
**Ringkasan:** T14: Menambahkan log publish (berupa `LogMessageEvent`) yang diekspos ke UI apabila endpoint `/stream/<video_id>` menerima respons 403 atau 410 dari upstream.
**File Terdampak:**
- `server/handlers/http.py`

---

## [2026-07-15] Loop Mode (Tier 2 - T13)
**ID:** `PATCH-2026-07-15-054`
**Tanggal:** 2026-07-15
**Ringkasan:** T13: Menambahkan fitur Loop Mode (off/track/queue). Menambah flag di AppState, logic `next()` pada `queue_manager.py`, command WS baru, serta toggle UI button yang disinkronisasi dengan state.
**File Terdampak:**
- `core/state.py`
- `core/commands.py`
- `engine/queue_manager.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/dom.js`
- `web/static/js/render/player.js`
- `web/static/js/events/transport-events.js`
- `web/static/css/components/player-bar.css`
- `tests/unit/engine/test_queue_manager.py`

---

## [2026-07-15] Recent Search History (Tier 2 - T12)
**ID:** `PATCH-2026-07-15-053`
**Tanggal:** 2026-07-15
**Ringkasan:** T12: Riwayat pencarian terkini menggunakan safeStorage di sisi client beserta dukungan penghapusan manual. Juga memperbaiki fitur penghapusan item individual di daftar antrean.
**File Terdampak:**
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/events/queue-events.js`
- `server/handlers/ws_playback.py`

---

## [2026-07-15] Playback Speed Control (Tier 2 - T11)
**ID:** `PATCH-2026-07-15-052`
**Tanggal:** 2026-07-15
**Ringkasan:** T11: Fitur kontrol kecepatan pemutaran. Menambahkan dropdown kecepatan di Setting, menghubungkannya melalui event WebSocket, serta pengaturan real-time menggunakan `mpv.set_property("speed", value)`.
**File Terdampak:**
- `core/state.py`
- `core/commands.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/render/player.js`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`

---

## [2026-07-15] Sleep Timer (Tier 2 - T10)
**ID:** `PATCH-2026-07-15-051`
**Tanggal:** 2026-07-15
**Ringkasan:** T10: Implementasi mode Sleep Timer. Mengatur waktu tidur dengan opsi countdown, mengintegrasikannya dengan command bus agar memicu auto-stop playback setelah waktu terlampaui, dan menambah test.
**File Terdampak:**
- `core/commands.py`
- `engine/sleep_timer.py`
- `engine/command_router.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `tests/unit/engine/test_sleep_timer.py`

---

## [2026-07-15] Cache Size Indicator & Clear (Tier 2 - T9)
**ID:** `PATCH-2026-07-15-050`
**Tanggal:** 2026-07-15
**Ringkasan:** T9: Penambahan handler `ws_cache.py` untuk mengukur direktori cache MP3 (`config.CACHE_DIR`) dan menghapusnya tanpa menyentuh file statis atau unduhan manual, disertai unit test. Di UI ditambahkan tampilan ukuran disk pada tab Settings.
**File Terdampak:**
- `server/handlers/ws_cache.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `tests/unit/server/handlers/test_ws_cache.py`

---

## [2026-07-15] Playback Resume Functionality (Tier 2 - T8)
**ID:** `PATCH-2026-07-15-049`
**Tanggal:** 2026-07-15
**Ringkasan:** Implementasi Task T8: Resume posisi playback setelah restart server. Modifikasi meliputi penambahan kolom `last_position` di tabel `tracks`, method di repositori untuk write/read posisi, `_on_track_progress` di controller untuk menyimpan secara periodik (setiap 10 detik), dan script `main.py` untuk load last state saat startup. Unit test untuk start_paused pada controller telah ditambahkan. Panjang file `controller.py` telah dikompres kembali sehingga lolos pengecekan `<400 baris` doctor.
**File Terdampak:**
- `core/state.py`
- `persistence/schema.sql`
- `persistence/track_repo.py`
- `persistence/__init__.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `main.py`

---

## [2026-07-15] Fixes and Optimizations Tier 1
**ID:** `PATCH-2026-07-15-048`
**Tanggal:** 2026-07-15
**Ringkasan:** Implementasi Task T1-T7 Tier 1: Perbaikan bug data integrity hash fallback, precompile regex di searcher, lrc parser, HTTP handler, optimasi regex noise-keyword lirik, dan penggantian list ke deque pada rate limiter. Menambahkan unique index pada `artists.nama` di schema DB.
**File Terdampak:**
- `adapters/ytdlp/searcher.py`
- `tests/unit/adapters/ytdlp/test_searcher.py`
- `persistence/schema.sql`
- `plugins/lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `plugins/lyrics_fetcher.py`
- `tests/unit/plugins/test_lyrics_fetcher.py`
- `server/handlers/http.py`
- `tests/unit/server/handlers/test_http.py`
- `server/middleware.py`
- `tests/unit/server/test_middleware.py`

---

## [2026-07-15] CI Hang Diagnosis & Documentation Update
**ID:** `PATCH-2026-07-15-047`
**Tanggal:** 2026-07-15
**Ringkasan:** Mendiagnosa dan menemukan akar masalah "hang 1 jam 54 menit" pada CI pytest. Hang terbukti disebabkan oleh *zombie process* `yt-dlp` pada integration test (`test_download_flow.py`) yang gagal *timeout* akibat pemblokiran IP oleh YouTube di server GitHub Actions, dan tidak di-kill saat *teardown*. Memperbarui panduan integration testing dengan instruksi untuk memastikan `yt-dlp` dibunuh secara eksplisit di *teardown*. Seluruh 435 unit tests (P0-P4) terbukti *green* dan tidak bermasalah.
**File Terdampak:**
- `docs/testing/integration_testing.md`
- `log.md` (Catatan Mentah / Laporan Investigasi)

---

## [2026-07-15] Test Coverage P3 & P4 - WS & Radio Engine
**ID:** `PATCH-2026-07-15-046`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk error handling dan WS routing di `server/handlers/websocket.py` & `ws_playback.py` (P3) serta fallback prefetch dan radio_next di `engine/radio/engine.py` & `prefetcher.py` (P4) sesuai dengan `PATCH_TEST_COVERAGE.md`.
**File Terdampak:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_artist_selector.py`

---

## [2026-07-15] Test Coverage P2 - observer.py
**ID:** `PATCH-2026-07-15-045`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk loop event async di `adapters/mpv/observer.py` sesuai dengan P2 di `PATCH_TEST_COVERAGE.md` (unknown property change, cleanup path, socket reconnect loop). Coverage keseluruhan naik dari 77.48% menjadi 78.43%.
**File Terdampak:**
- `tests/unit/adapters/mpv/test_observer.py`

---

## [2026-07-15] Test Coverage P1 - controller.py
**ID:** `PATCH-2026-07-15-044`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk state machine di `engine/playback/controller.py` sesuai dengan P1 di `PATCH_TEST_COVERAGE.md` (race condition, error state, empty queue, rollback). Coverage keseluruhan naik dari 77.10% menjadi 77.48%.
**File Terdampak:**
- `tests/unit/engine/playback/test_controller.py`

---

## [2026-07-15] Test Coverage P0 - serve_stream
**ID:** `PATCH-2026-07-15-043`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk fungsi `serve_stream()` di `server/handlers/http.py` sesuai dengan P0 di `PATCH_TEST_COVERAGE.md`. Coverage keseluruhan naik dari 75.10% menjadi 77.10%.
**File Terdampak:**
- `tests/unit/server/handlers/test_http.py`

---

## [2026-07-15] Quality of Life (QoL) Enhancements: Bandit, Loudness, Adaptive Prefetch
**ID:** `PATCH-2026-07-15-042`
**Tanggal:** 2026-07-15
**Ringkasan:** Eksekusi integrasi 3 fitur besar secara serentak untuk mematuhi larangan two-stage refactoring:
1. Thompson Sampling Bandit untuk Artist Radio.
2. EBU R128 Loudness Normalization.
3. Adaptive Network Prefetch (Latency Window).
Fitur dipisah ke service/kelas baru dan controller dimodifikasi untuk injeksi ketergantungan.
**File Terdampak:**
- `persistence/schema.sql` & `__init__.py`
- `core/state.py`, `core/commands.py`, `core/ports.py`
- `persistence/artist_repo.py`, `persistence/track_repo.py`, `persistence/library_repo.py`
- `core/latency_window.py`
- `config.py` & `core/observability.py`
- `cache/resolver.py`
- `engine/radio/prefetcher.py`, `engine/radio/artist_bandit.py`, `engine/radio/artist_selector.py`
- `engine/loudness/gain_calculator.py`, `engine/loudness/analyzer.py`, `engine/loudness/service.py`
- `engine/playback/track_loader.py`, `engine/playback/mode_ops.py`, `engine/playback/controller.py`
- `adapters/mpv/__init__.py`
- `engine/command_router.py`
- `server/serializers.py`
- `main.py`

---



## [2026-07-14] Stable Release Hardening & Bug Fixes

**ID:** `PATCH-2026-07-14-041`
**Tanggal:** 2026-07-14
**Ringkasan:** Eksekusi P0-P2 dari IMPLEMENTATION_PLAN.md untuk persiapan Stable Release v1.0.0. Termasuk perbaikan banner password, path downloads, DB migration logging, `shell=False` di network probing, pemblokiran CI gate, metadata `pyproject.toml`, update package metadata, dan setup wheel build di CI.
**File Terdampak:**
- `main.py`
- `config.py`
- `README.md`
- `docs/INDEX.md`
- `engine/download_manager.py`
- `server/handlers/ws_download.py`
- `persistence/__init__.py`
- `launcher/network.py`
- `package.json`
- `.importlinter`
- `.github/workflows/ci.yml`
- `pyproject.toml`

---
