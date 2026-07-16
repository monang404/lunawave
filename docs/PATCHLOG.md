---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-16-068

total_entries: 68

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



---

## [2026-07-16] Migration to Windows Named Pipes IPC & Integration Test Stabilization
**ID:** `PATCH-2026-07-16-068`
**Tanggal:** 2026-07-16
**Ringkasan:**
1. Mengubah mekanisme IPC dari TCP Sockets menjadi Windows Named Pipes (`\\.\pipe\mpv-lunawave`) untuk meningkatkan reliabilitas koneksi dengan proses MPV di OS Windows, menghilangkan limitasi socket exhaustion, dan mengurangi latensi.
2. Memperbaiki *regression* (Zombie non-daemon threads / Timeout) dan *flakiness* di dalam suite tes integrasi akibat perubahan *interface*, serta menyesuaikan timeout ekspektasi dari `yt-dlp`.

- **Fix 1 (Pipes IPC):** `MpvConnection` kini melakukan inisialisasi pada `\\.\pipe\mpv-lunawave` alih-alih port TCP `6666`. `MpvObserver` disesuaikan untuk membaca dari pipe yang sama. Seluruh parameter setup TCP di `run_server()` dihilangkan.
- **Fix 2 (Integration Test Setup):** `tests/integration/conftest.py` ditambahkan command `command_bus._handlers.clear()` untuk menghindari `RuntimeError` duplikasi handler pada tes yang dijalankan secara berurutan.
- **Fix 3 (Test Syncs):** Penyesuaian nama metode (`download_mp3` -> `download_audio`), penambahan field `artist` pada objek `TrackInfo`, perubahan field `file_path` pada `DownloadCompleteEvent` menjadi `track.local_path`, serta update ID video yang *geo-restricted* ke video yang stabil (`jNQXAC9IVRw` - Me at the zoo).

**File Terdampak:**
- `adapters/mpv/connection.py`
- `adapters/mpv/ipc.py`
- `adapters/mpv/observer.py`
- `adapters/ytdlp/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_download_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_websocket_flow.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/adapters/mpv/test_ipc.py`

---

## [2026-07-16] Startup Latency Optimization — 3 Fix: MPV Non-Blocking, Resume Background Task, Windows TCP Polling
**ID:** `PATCH-2026-07-16-067`
**Tanggal:** 2026-07-16
**Ringkasan:** Tiga perbaikan startup latency berurutan berdasarkan analisis mendalam 5-tahap chain dari GUI klik "Start" sampai browser dapat diakses. Total estimasi gain: **1.5–25+ detik** tergantung kondisi.
- **Fix 1 (Dampak terbesar, 1–20+ detik):** "Resume last playback" dipindah dari critical path ke background task (`safe_create_task`). Sebelumnya, kalau stream URL track terakhir sudah expired >6 jam, `main.py` akan melakukan network request ke YouTube via `yt-dlp` (max 25 detik timeout) *sebelum* `run_server()` dipanggil. Sekarang resume berjalan concurrently — browser bisa connect ke UI sementara resume masih diproses di background.
- **Fix 2 (0.3–2 detik):** `mpv.connect()` dipindah dari `asyncio.gather()` blocking ke background task. Web server kini bisa bind port dan menerima koneksi tanpa menunggu MPV spawn + IPC handshake. Koordinasi lewat `asyncio.Event _mpv_ready_event` — resume task menunggu MPV siap (tanpa timeout) sebelum memanggil `play_track()`, tanpa memblok server.
- **Fix 3 (0–1 detik, selalu di Windows):** Ganti `await asyncio.sleep(1.0)` blind wait di Windows dengan polling TCP port aktif (50 iterasi × 100ms = max 5 detik, keluar lebih awal begitu MPV siap). Best-case selesai dalam ~100ms, bukan selalu 1000ms.
- **Tests:** Update 4 test lama di `test_connection.py` (assertion call count disesuaikan dengan polling behavior baru), tambah 2 test baru untuk polling Windows, tambah 1 test baru `test_run_server_not_blocked_by_mpv` dengan event-based coordination. 11/11 test pass.

**File Terdampak:**
- `main.py`
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/test_main.py`

---

## [2026-07-16] Full Audit — Frontend (web/static/js/) — Search Mati Total, Volume Slider Dead, Crossfade Dead Code
**ID:** `PATCH-2026-07-16-066`
**Tanggal:** 2026-07-16
**Ringkasan:** Audit menyeluruh pertama kali untuk SELURUH `web/static/js/` (31 file, semua diperiksa baris-per-baris; backend tidak disentuh). 6 bug CONFIRMED (dieksekusi/reproduksi nyata, bukan cuma baca kode) dan beberapa dead-code/minor findings.
- **BUG-1 (Kritis, CONFIRMED):** `#vol-slider` ada di `index.html` tapi tidak pernah dipetakan di `dom.js` (`dom.volSlider` selalu `undefined`). Akibatnya seluruh listener drag volume di `transport-events.js` tidak pernah ter-attach (`if (dom.volSlider)` selalu false) dan render/player.js tidak pernah sinkron nilainya — slider volume 100% non-fungsional dari awal. Fix: tambah `volSlider: $("vol-slider")` ke `dom.js`.
- **BUG-2 (Kritis, CONFIRMED lewat eksekusi nyata):** `window.safeStorage` cuma expose `.get/.set/.remove` (lihat `utils/toast.js`), tapi `search-input-events.js` memanggil `.getItem/.setItem/.removeItem` gaya `localStorage` yang TIDAK ADA di objek itu. `saveSearchHistory()` throw `TypeError` tak tertangkap, dan karena baris ini dipanggil SEBELUM `wsSend("search", ...)` baik di debounce-input maupun handler Enter, exception ini menghentikan seluruh callback → `wsSend("search")` TIDAK PERNAH terpanggil. Direproduksi dengan skrip Node standalone yang meniru pola kode persis — dikonfirmasi search tidak terkirim. **Dampak: fitur SEARCH mati total di seluruh aplikasi**, bukan cuma riwayat pencarian. Fix: ganti ke `.get/.set/.remove`, bungkus `saveSearchHistory` dengan try/catch sebagai defense-in-depth.
- **BUG-3 (Kritis, CONFIRMED):** `render/player.js` (`_renderProgressCore`) memakai `window.audio` untuk logic volume-fade crossfade, tapi `window.audio` TIDAK PERNAH di-assign di manapun (elemen `<audio>` browser diakses lewat `getOrInitAudio()`/`localAudio` di `audio/playback-sync.js`, bukan `window.audio`). Kondisi selalu falsy → seluruh efek fade-out/fade-in volume crossfade untuk output browser adalah dead code, toggle crossfade di Settings tidak berefek pada audio yang sedang main di mode browser. Fix: ganti ke `getOrInitAudio()`.
- **BUG-4 (Sedang, CONFIRMED):** `platform/keyboard.js` memanggil `cmd('play')/cmd('next')/cmd('prev')` — fungsi `cmd` tidak pernah didefinisikan di manapun di codebase (grep kosong). `typeof cmd === 'function'` selalu false → ArrowLeft/ArrowRight/Space di desktop cuma `preventDefault()` tanpa efek (fitur mati sejak awal). Kasus `Space` juga duplicate listener dengan `events/keyboard-shortcut-events.js` (yang sudah admin-gated dan benar-benar jalan). Fix: hapus case Space yang duplikat, sambungkan ArrowLeft/ArrowRight langsung ke `wsSend` dengan guard admin.
- **BUG-5 (XSS, CONFIRMED):** `search-input-events.js` → `renderSearchHistory()` menyisipkan query pencarian (asal input user, disimpan di localStorage) langsung ke `innerHTML` tanpa escape untuk teks yang tampil (`<span>${q}</span>`) — cuma tanda kutip `"` yang di-escape untuk atribut `data-query`. Query berisi markup HTML/script tersimpan lalu dieksekusi ulang tiap kali riwayat pencarian dirender (stored self-XSS). Fix: pakai `escapeHtml()` untuk teks maupun atribut.
- **BUG-6 (Sedang, SUSPECTED — pola dikonfirmasi lewat perbandingan kode, belum direproduksi di device fisik):** `events/progress-events.js` (drag seek bar) tidak punya handler `pointercancel`, tidak seperti drag-reorder queue (`events/queue-events.js`) yang sudah benar menanganinya. Kalau pointer sequence di-cancel OS/browser di tengah drag (gesture back, incoming call, multi-touch) tanpa `pointerup`, `window.isDraggingPb` nyangkut `true` selamanya → progress bar freeze permanen (rAF interpolation loop dan `renderProgress()` sama-sama early-return selama flag itu true), walau playback tetap jalan normal. Fix: tambah handler `pointercancel` yang reset flag + release pointer capture.
- **MINOR-1:** `ws.js` — `store.userRole = "admin"` ter-assign 2x berturut-turut di `auth_status` handler (sisa edit sebelumnya, harmless). Fix: hapus baris duplikat.
- **MINOR-2:** `sw.js` — `PRECACHE_ASSETS` tidak menyertakan `audio/playback-sync.js` dan `audio/visualizer.js` (script inti pemutar audio browser). SW registration saat ini masih dimatikan di `main.js` jadi belum berdampak, tapi akan menyebabkan first-offline-load kehilangan script pemutar audio kalau SW diaktifkan lagi tanpa fix ini. Fix: tambahkan ke daftar precache.
- **DEAD CODE (dilaporkan, TIDAK dihapus — di luar scope "fix bug", risiko regresi kalau dihapus tanpa keputusan desain):**
  - `events/click-delegation-events.js` blok 3 menangani selector `.disc-card, .fav-card, .search-result-item` — tidak ada kode render manapun (discover-tab.js, search.js) yang menghasilkan elemen dengan class ini (semua pakai `.sr-item`). Blok ini 100% unreachable, kemungkinan sisa refactor/rename lama.
  - `audio/visualizer.js`: `startVisualizerLoop()`/`resumeVisualizerLoop()` (visualizer asli berbasis Web Audio API `analyser`/`dataArray`) tidak pernah dipanggil dari manapun, dan `analyser`/`dataArray` (dideklarasikan di `playback-sync.js`) tidak pernah di-assign (tidak ada `createAnalyser()`/`createMediaElementSource()`). `initAudio()` cuma memanggil `startFakeBeatLoop()` (efek beat berbasis timer, bukan analisis audio asli) — implementasi analyser sepenuhnya mati, tergantikan tanpa dibersihkan.
  - `transport-events.js` mereferensikan `dom.btnStop` — tidak ada elemen `#btn-stop` di `index.html` dan tidak dipetakan di `dom.js`; guard `if (dom.btnStop)` membuat ini no-op aman, Stop tetap bisa diakses lewat `ss-stop-btn` di Settings sheet yang sudah benar.
**Verifikasi:** `vitest run` 14/14 tetap passed (3 file test, tidak ada regresi), `node --check` bersih untuk semua 7 file yang diedit, reproduksi manual (skrip Node standalone) mengkonfirmasi BUG-2 sebelum & sesudah fix.
**File Terdampak:**
- `web/static/js/dom.js`
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/player.js`
- `web/static/js/platform/keyboard.js`
- `web/static/js/events/progress-events.js`
- `web/static/js/ws.js`
- `web/static/sw.js`

---

## [2026-07-16] Full Audit — Race Condition di ConnectionManager.broadcast()
**ID:** `PATCH-2026-07-16-065`
**Tanggal:** 2026-07-16
**Ringkasan:** Full-codebase audit (breadth scan seluruh package + deep-dive area berisiko tinggi: core/event_bus.py, persistence/db.py, engine/sleep_timer.py, server/handlers/websocket.py, engine/radio/prefetcher.py lock ordering, server/connection_manager.py). Ditemukan CONFIRMED race condition di `ConnectionManager.broadcast()`: `results` dari `asyncio.gather()` dipasangkan (`zip()`) dengan `list(self.active_connections)` yang di-fetch ULANG setelah await, bukan snapshot yang sama dipakai untuk gather(). Kalau ada connect/disconnect konkuren selagi broadcast() masih await (mis. client baru connect, atau client lain di-disconnect independen oleh handler-nya sendiri), index/urutan list itu bisa berubah -> hasil send_str() salah dipasangkan ke ws yang salah -> client SEHAT bisa ikut ke-disconnect secara keliru. Direproduksi nyata (script manual + test suite, gagal 3/3 run di kode lama). Fix: pin SATU snapshot list, dipakai ulang untuk gather() maupun zip(), sehingga urutan selalu align terlepas dari mutasi konkuren pada active_connections.
**File Terdampak:**
- `server/connection_manager.py`
- `tests/unit/server/test_connection_manager.py`

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
