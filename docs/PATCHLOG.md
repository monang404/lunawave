---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-17-074

total_entries: 74

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



---


## [2026-07-17] merapikan dokumen patchlog

**ID:** `PATCH-2026-07-17-074`

**Tanggal:** 2026-07-17

**Ringkasan:** merapikan dokumen patchlog

**File Terdampak:**

- `PATCHLOG.MD`

---

## [2026-07-17] UI/UX revamp tab discover (progressive disclosure hashtag/list, role-gate access, keyboard accessibility, filter scope)

**ID:** `PATCH-2026-07-17-073`

**Tanggal:** 2026-07-17

**Ringkasan:** UI/UX revamp tab discover (progressive disclosure hashtag/list, role-gate access, keyboard accessibility, filter scope)

**File Terdampak:**

- `server/handlers/ws_discovery.py`
- `web/static/js/render/discover-tab.js`
- `web/static/js/events/click-delegation-events.js`
- `web/static/index.html`
- `web/static/css/components/discover-cards.css`
- `web/static/js/render/discover-personalize.js`

---

## [2026-07-17] Patch — Sinkronisasi Referensi automation/

**ID:** `PATCH-2026-07-17-072`

**Tanggal:** 2026-07-17

**Ringkasan:** Menyelaraskan nama direktori dan modul internal dari `scripts/` menjadi `automation/` di seluruh dokumentasi dan docstring file Python. Juga menghapus blok instruksi peringatan migrasi di `AI_CONTEXT.md` sesuai dengan instruksi yang tertera di sana.

**File Terdampak:**

- `AI_CONTEXT.md` — [MODIFIED] hapus catatan migrasi.
- `automation/**/*.py` — [MODIFIED] update docstring Module dari `scripts.` menjadi `automation.`.
- `automation/shared/skip_dirs.py` — [MODIFIED] update skip dirs `"scripts"` menjadi `"automation"`.
- `automation/shared/arch_rules.py` — [MODIFIED] update arch rules.
- `automation/find_owner.py` — [MODIFIED] update pemetaan folder.
- `docs/*.md` — [MODIFIED] referensi `scripts/` di-update ke `automation/` (non-historical file).

---

## [2026-07-17] Discover Tab revamp — frontend wiring (taste spectrum, filter bar, 3 card-row, artist detail sheet)

**ID:** `PATCH-2026-07-17-071`

**Tanggal:** 2026-07-17

**Ringkasan:** Melanjutkan `PATCH-2026-07-17-070` (backend-only) sesuai `discover-tab-frontend-handoff.md`. Semua data personalisasi yang sudah dikirim backend kini benar-benar sampai ke UI dan bisa dipakai user. 1. **`server/handlers/websocket.py`** — izin eksplisit diberikan user (file ini *restricted* per `AI_CONTEXT.md`). Ditambah 1 baris: `"get_artist_detail"` ke `DISCOVERY_CMDS`, sehingga action yang sudah diimplementasi di `ws_discovery.py` sejak PATCH-070 kini benar-benar reachable dari client. 2. **`web/static/js/store.js`** — tambah default `discover_for_you`, `discover_unheard`, `discover_genre_affinity_genre`, `discover_genre_affinity_artists`, `discover_taste_spectrum`. 3. **`web/static/js/ws.js`** — `case "discover_data"` sekarang menyimpan 5 field baru dari payload + memanggil `renderDiscoverPersonalization()`. Tambah `case "artist_detail"` baru (sebelumnya di-drop diam-diam karena tidak ada `default:` case). 4. **`web/static/js/dom.js`** — register elemen baru: taste bar/legend, filter bar (segmented + chip row), 3 card-row (`rowForYou`, `rowGenreAffinity`, `rowUnheard`), sheet `artistDetailSheet` + cover/nama/tag/track-list/tombol di dalamnya. 5. **`web/static/js/render/discover-personalize.js` (baru, 185 baris).** Semua logic render + interaksi personalisasi: taste bar dari `discover_taste_spectrum` (dengan fallback "Dengarkan beberapa lagu dulu..." kalau kosong), kartu artis generik (cover + nama + genre tag, badge `match_pct` untuk "Untuk Kamu", badge "Baru" + varian `.undiscovered` untuk "Belum Pernah Kamu Dengar"), filter kategori + dekade client-side (dekade dibangun dari nilai `tahun_aktif` aktual yang ada di data, bukan hard-coded), handler tap kartu → `wsSend('get_artist_detail', ...)` → isi & buka sheet saat `handleArtistDetail()` dipanggil dari `ws.js`, tombol "Putar Semua" → reuse `enqueue_artist_songs` dengan role-gate (`store.userRole !== 'admin'` → toast) konsisten dengan pola Discover lain. `discover-tab.js` (sudah lewat ambang 200 baris) **tidak disentuh sama sekali** — tetap fokus ke recent/favorites/cached/hashtag-cloud. 6. **`web/static/css/components/discover-cards.css` (baru).** `.taste-bar`/ `.taste-legend`, `.filter-bar`/`.segmented`/`.chip`, `.artist-card` (+ varian `.undiscovered`), styling konten `.ads-*` untuk artist detail sheet. Genre tag pakai palet kecil kurasi (`--g-pop`, `--g-rock`, dst, didefinisikan lokal di file ini) bukan `hsl(random)`. Tidak ada CSS baru untuk shell sheet — reuse `.settings-sheet` yang sudah ada. 7. **`web/static/index.html`** — markup taste spectrum + filter bar + 3 card-row disisipkan di bawah header Discover, sebelum "Jelajahi Artis"/"Jelajahi Genre" yang sudah ada. Sheet baru `<div class="settings-sheet" id="artist-detail-sheet">` (reuse pola `#action-sheet`/`#help-sheet` + `#main-overlay`). Ditambah 1 link CSS (`discover-cards.css`) dan 1 script tag (`render/discover-personalize.js`). 8. **`web/static/js/events/settings-events.js`** — `closeMainOverlay()` ditambah 1 baris supaya `artistDetailSheet` ikut ketutup saat backdrop di-tap, konsisten dengan sheet lain. 9. **`web/static/js/events/index.js`** — daftarkan `initDiscoverFilterEvents()` di urutan init yang sama dengan `initSettingsEvents()` dkk. **Verifikasi otomatis:** `automation/doctor.py`, `generate_file_index.py`, `generate_report.py` dijalankan bersih untuk file yang disentuh sesi ini (2 FAIL yang tersisa — `engine/playback/controller.py` 464 baris & `.gitignore` hilang — sudah ada sebelum sesi ini, tidak disentuh/diperparah oleh patch ini).

**File Terdampak:**

- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/dom.js`
- `web/static/js/render/discover-personalize.js` (baru)
- `web/static/css/components/discover-cards.css` (baru)
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/index.js`

---

## [2026-07-17] Discover Tab revamp — backend saja (personalisasi: bandit ranking, unheard artists, taste spectrum, genre affinity, artist detail)

**ID:** `PATCH-2026-07-17-070`

**Tanggal:** 2026-07-17

**Ringkasan:** Eksekusi bagian backend dari `discover-tab-implementation-plan-v2.md` (v2 dipakai, bukan v1 — lihat alasan di bawah). **Frontend sengaja belum disentuh sama sekali** — task ini eksplisit diminta backend-only, siap dilanjutkan sesi lain oleh frontend designer/programmer. Lihat `docs/STATUS.md` §"Discover Tab Personalization — Backend" untuk ringkasan siap-pakai yang ditujukan buat sesi lanjutan itu. 1. **`persistence/discover_enrich.py` (baru, 78 baris).** `enrich_artists(conn, rows)` — helper bersama: attach `cover` (thumbnail YouTube dari lagu pertama artis, `MIN(id)` bukan `RANDOM()` supaya deterministic/tidak flicker) + `genres` (list tag) ke sekumpulan artist row sekaligus. 2 query total untuk berapa pun jumlah artis (hindari N+1). 2. **`persistence/discover_repo.py` (baru, 242 baris).** `class DiscoverRepository` — **keputusan v2, bukan v1**: v1 rencananya nambah method ini ke `artist_repo.py`/`genre_repo.py` (116/97 baris saat itu), tapi itu akan mendorong keduanya ke zona Waspada (>150 baris) padahal tanggung jawab aslinya cuma click/reward tracking, bukan personalisasi. Jadi repo terpisah, sejajar `LibraryRepository`. Method: `get_bandit_ranked_artists(limit)` ("Untuk Kamu", ranking posterior mean `alpha/(alpha+beta)`, exclude artis yang belum tersentuh bandit sama sekali), `get_unheard_artists(limit)` ("Belum Pernah Kamu Dengar", filter `alpha=beta=1 AND click_count=0`), `get_taste_spectrum(limit=6)` (agregasi genre dari `tracks.play_count + is_favorite*3`, dinormalisasi ke persentase + bucket "Lainnya" untuk sisa genre di luar top-N; `[]` kalau histori kosong), `get_top_genre()` (elemen pertama taste spectrum atau `None`), `get_genre_artists_enriched(genre, limit)`, `get_artist_detail(nama)` (info + genre + hingga 10 lagu, urut by id bukan random, untuk detail sheet yang stabil antar-buka). File ini masuk zona **Waspada** (242 baris, ambang 150-300) — bukan pelanggaran, tapi kalau nanti ada section Discover baru lagi, pertimbangkan pecah per jenis query dulu sebelum tembus 300. 3. **`persistence/__init__.py`:** import + instansiasi `DiscoverRepository` (`self._discover`), delegasi 6 method baru di atas — pola sama persis dengan repo lain yang sudah ada. 4. **`services/discover_service.py`** (161 → 208 baris, tetap zona Waspada tapi belum "wajib pecah"): 5 wrapper method baru — `get_for_you`, `get_unheard`, `get_genre_affinity` (return `{genre, artists}`, `genre=None` kalau histori kosong), `get_taste_spectrum`, `get_artist_detail` — semua delegasi ke facade `Database` seperti method lain di file ini, guard `getattr(self.db, "conn", None)` konsisten dengan pola existing. 5. **`server/handlers/ws_discovery.py`:** action `discover` — `asyncio.gather` diperluas dari 5 jadi 9 query paralel, payload `discover_data` nambah 5 field (`for_you`, `unheard`, `genre_affinity_genre`, `genre_affinity_artists`, `taste_spectrum`). Action baru `get_artist_detail` diimplementasikan lengkap (terima `{artist: nama}`, balas `{type: "artist_detail", data: {...} | null}`). 6. **`server/handlers/websocket.py` — SENGAJA TIDAK DISENTUH.** File ini *restricted* di `AI_CONTEXT.md` ("tidak boleh disentuh tanpa izin eksplisit"). Perubahan yang dibutuhkan cuma 1 baris (tambah `"get_artist_detail"` ke `DISCOVERY_CMDS`), tapi izin eksplisit belum diminta/didapat di sesi ini — jadi **action `get_artist_detail` sudah diimplementasikan di `ws_discovery.py` tapi belum bisa dipanggil sama sekali** lewat WS asli sampai baris itu ditambah. Action `discover` yang sudah diperluas TIDAK terpengaruh blocker ini (sudah ada di `DISCOVERY_CMDS` sebelumnya). 7. **Test (mirror per Prinsip #2):** `tests/unit/persistence/test_discover_repo.py` (baru, 14 test, mencakup semua method + edge case histori kosong/artist tidak ditemukan/cap 10 lagu). `test_discover_service.py` (+12 test untuk 5 wrapper baru). `test_ws_discovery.py` (+4 test: payload personalisasi lengkap, `get_artist_detail` sukses, `get_artist_detail` dengan nama kosong tidak memanggil service — plus 1 test lama diupdate supaya tidak break setelah `gather` diperluas dari 5→9 query). 8. **Automation:** `generate_file_index.py` + `generate_report.py` dijalankan ulang (file baru: `discover_repo.py`, `discover_enrich.py`, `test_discover_repo.py`). `doctor.py` bersih untuk semua yang diubah di patch ini — satu-satunya FAIL yang tersisa (`engine/playback/controller.py` 464 baris) adalah temuan pre-existing dari sesi sebelumnya, tidak disentuh atau diperparah oleh patch ini. **Hasil test:** 522 unit test lulus (naik dari 508 baseline), 0 gagal. `tests/unit/launcher/gui/*` tidak ikut collect di environment eksekusi ini (`ModuleNotFoundError: tkinter`, pre-existing keterbatasan environment, bukan regresi dari patch ini).

**File Terdampak:**

- `persistence/discover_enrich.py` (baru)
- `persistence/discover_repo.py` (baru)
- `persistence/__init__.py`
- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/persistence/test_discover_repo.py` (baru)
- `tests/unit/services/test_discover_service.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `docs/STATUS.md`
- `docs/discover-tab-frontend-handoff.md` (baru — laporan handoff detail utk sesi frontend berikutnya: kontrak payload, gap ws.js/store.js yang tidak disebut di implementation-plan-v2.md, urutan pengerjaan, checklist)
- `docs/FILE_INDEX.md` (auto-generated)
- `docs/REPORT.md` (auto-generated)
- `server/handlers/websocket.py` (butuh izin eksplisit, 1 baris)
- `web/static/js/dom.js`, `web/static/index.html`,

---

## [2026-07-16] Eksekusi implementation-plan.md (Batch 0–4.2): CI hang, timing side-channel, race condition crossfade, SponsorBlock window, parser LRC, lifecycle EventBus/CommandBus

**ID:** `PATCH-2026-07-16-069`

**Tanggal:** 2026-07-16

**Ringkasan:** Eksekusi penuh `implementation-plan.md` (hasil verifikasi `summary-1.md`, 16 Juli 2026), batch demi batch. Beberapa item (#1 dedup title radio, #2 race crossfade, #4 metrics token compare, #11 sebagian dead code) ternyata **sudah** diperbaiki sebelumnya di codebase (kemungkinan patch manual terpisah) — diverifikasi ulang, tidak diubah lagi. Item yang benar-benar dieksekusi di sesi ini: 1. **Batch 0 (CI hang):** Tambah `pytest-timeout` (jaring pengaman, 60s/thread) di `pytest.ini` + `requirements-dev.txt`. `main.py` shutdown: `task.cancel()` sekarang diikuti `await asyncio.gather(*tasks, return_exceptions=True)`. `adapters/mpv/observer.py.stop()`: await task sampai tuntas setelah cancel. **Terverifikasi lewat eksekusi nyata** (bukan cuma analisis): baseline suite sebelumnya meninggalkan zombie non-daemon thread (`conftest.py` sampai perlu `os._exit()` paksa); setelah fix, suite exit bersih tanpa paksaan. 2. **Batch 1:** (#3) fast-skip `shutil.which("mpv")` dipindah SEBELUM `db.init()` di `tests/integration/conftest.py` — ditemukan lewat testing bahwa urutan lama (db.init() sebelum skip check) bikin fixture generator skip sebelum `yield`, jadi teardown `db.close()` tidak pernah jalan -> connection thread leak (root cause zombie thread kedua, di luar dugaan awal plan). (#5) `persistence/db.py.close()`: ganti `asyncio.sleep(0.01)` dengan `asyncio.to_thread(worker_thread.join, timeout=1.0)` -- join asli, bukan tebak-tebakan delay. (#4) `server/handlers/auth.py`: hilangkan short-circuit `and` yang skip `verify_password` kalau username salah (celah timing side-channel enumerasi username) — sekarang `verify_password` selalu jalan. (#11) hapus `clear_standby()` (stub `pass`, tak terpakai) di `engine/radio/prefetcher.py`; `check_rate_limit_sync()` & `secrets.compare_digest()` di `http.py` ternyata sudah dibersihkan sebelumnya. `controller.py._last_position_save` ternyata sudah tersambung benar (bukan dead code seperti dugaan plan, tidak diubah). (#12) `main.py:339` bare `except:` -> `except Exception:`. 3. **Batch 2.3 (#7):** `plugins/sponsorblock.py` — ganti window deteksi sempit (`start <= pos <= start+0.6`) yang bisa terlewat kalau progress event melompat, dengan one-directional check (`start <= pos < end`) + flag `_skipped_segments` per-track (direset tiap `fetch_segments`). Perbaiki docstring throttle interval yang salah ("~0.5s" -> "~1.0s"). 4. **Batch 3:** Test baru `tests/unit/engine/playback/test_track_ended_ops.py` (modul sebelumnya nol coverage) — grace-window `_handle_stop()`, dispatch eof/stop/error, `poll_duration`. 5. **Batch 4.1 (#8):** `plugins/lyrics_parser.py` — parser LRC diganti total: dukung multi-timestamp per baris (chorus berulang), skip tag metadata (`[ar:...]`, `[ti:...]`) alih-alih dianggap teks lirik biasa. 6. **Batch 4.2 (#6):** `core/command_bus.py` tambah `reset()` resmi (ganti akses langsung `_handlers.clear()` di `tests/integration/conftest.py`). `engine/playback/controller.py` tambah `dispose()` — unsubscribe 5 handler (termasuk 3 lambda closure yang referensinya kini disimpan sebagai atribut instance agar bisa di-unsubscribe balik), cancel `_fade_task` pending. Didokumentasikan eksplisit kenapa 3 lambda itu sengaja strong-ref (bukan bug WeakMethod). 7. **Bonus (ditemukan saat eksekusi, di luar 12 temuan awal):** `automation/patchlog.py.parse_entries()` — regex tunggal dengan beberapa `.*?` + `re.DOTALL` di-scan ke seluruh file (35KB, 28 entry berulang) menyebabkan catastrophic backtracking, hang tak terhingga (dikonfirmasi lewat eksekusi langsung dengan timeout). Diganti dengan split per-entry (separator `\n\n---\n\n`) dulu, baru regex sederhana per-chunk. 8. **Tidak dieksekusi (sesuai arahan plan sendiri):** #10 (tombol "prev" / forward-stack) — butuh keputusan produk dulu, belum diajukan ke user di sesi ini. `test_radio_flow.py` mock network (0.4, opsional/prioritas rendah) — tidak disentuh. **Hasil akhir:** 508 passed, 6 skipped (naik dari baseline 475 passed, 6 skipped) — unit + integration (integration tetap skip karena `mpv`/`yt-dlp` tidak terpasang di sandbox). `ruff check` bersih, `mypy` bersih (10 file diubah), `bandit` tanpa temuan baru, coverage total 88%.

**File Terdampak:**

- `pytest.ini`
- `requirements-dev.txt`
- `main.py`
- `adapters/mpv/observer.py`
- `tests/integration/conftest.py`
- `persistence/db.py`
- `tests/unit/persistence/test_db.py`
- `server/handlers/auth.py`
- `tests/unit/server/handlers/test_auth.py`
- `engine/radio/prefetcher.py`
- `plugins/sponsorblock.py`
- `tests/unit/plugins/test_sponsorblock.py`
- `plugins/lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `core/command_bus.py`
- `tests/unit/core/test_command_bus.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/engine/playback/test_track_ended_ops.py`
- `automation/patchlog.py`
- `docs/PATCHLOG.md`

---

## [2026-07-16] Migration to Windows Named Pipes IPC & Integration Test Stabilization

**ID:** `PATCH-2026-07-16-068`

**Tanggal:** 2026-07-16

**Ringkasan:** 1. Mengubah mekanisme IPC dari TCP Sockets menjadi Windows Named Pipes (`\\.\pipe\mpv-lunawave`) untuk meningkatkan reliabilitas koneksi dengan proses MPV di OS Windows, menghilangkan limitasi socket exhaustion, dan mengurangi latensi. 2. Memperbaiki *regression* (Zombie non-daemon threads / Timeout) dan *flakiness* di dalam suite tes integrasi akibat perubahan *interface*, serta menyesuaikan timeout ekspektasi dari `yt-dlp`. - **Fix 1 (Pipes IPC):** `MpvConnection` kini melakukan inisialisasi pada `\\.\pipe\mpv-lunawave` alih-alih port TCP `6666`. `MpvObserver` disesuaikan untuk membaca dari pipe yang sama. Seluruh parameter setup TCP di `run_server()` dihilangkan. - **Fix 2 (Integration Test Setup):** `tests/integration/conftest.py` ditambahkan command `command_bus._handlers.clear()` untuk menghindari `RuntimeError` duplikasi handler pada tes yang dijalankan secara berurutan. - **Fix 3 (Test Syncs):** Penyesuaian nama metode (`download_mp3` -> `download_audio`), penambahan field `artist` pada objek `TrackInfo`, perubahan field `file_path` pada `DownloadCompleteEvent` menjadi `track.local_path`, serta update ID video yang *geo-restricted* ke video yang stabil (`jNQXAC9IVRw` - Me at the zoo).

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

**Ringkasan:** Tiga perbaikan startup latency berurutan berdasarkan analisis mendalam 5-tahap chain dari GUI klik "Start" sampai browser dapat diakses. Total estimasi gain: **1.5–25+ detik** tergantung kondisi. - **Fix 1 (Dampak terbesar, 1–20+ detik):** "Resume last playback" dipindah dari critical path ke background task (`safe_create_task`). Sebelumnya, kalau stream URL track terakhir sudah expired >6 jam, `main.py` akan melakukan network request ke YouTube via `yt-dlp` (max 25 detik timeout) *sebelum* `run_server()` dipanggil. Sekarang resume berjalan concurrently — browser bisa connect ke UI sementara resume masih diproses di background. - **Fix 2 (0.3–2 detik):** `mpv.connect()` dipindah dari `asyncio.gather()` blocking ke background task. Web server kini bisa bind port dan menerima koneksi tanpa menunggu MPV spawn + IPC handshake. Koordinasi lewat `asyncio.Event _mpv_ready_event` — resume task menunggu MPV siap (tanpa timeout) sebelum memanggil `play_track()`, tanpa memblok server. - **Fix 3 (0–1 detik, selalu di Windows):** Ganti `await asyncio.sleep(1.0)` blind wait di Windows dengan polling TCP port aktif (50 iterasi × 100ms = max 5 detik, keluar lebih awal begitu MPV siap). Best-case selesai dalam ~100ms, bukan selalu 1000ms. - **Tests:** Update 4 test lama di `test_connection.py` (assertion call count disesuaikan dengan polling behavior baru), tambah 2 test baru untuk polling Windows, tambah 1 test baru `test_run_server_not_blocked_by_mpv` dengan event-based coordination. 11/11 test pass.

**File Terdampak:**

- `main.py`
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/test_main.py`

---

## [2026-07-16] Full Audit — Frontend (web/static/js/) — Search Mati Total, Volume Slider Dead, Crossfade Dead Code

**ID:** `PATCH-2026-07-16-066`

**Tanggal:** 2026-07-16

**Ringkasan:** Audit menyeluruh pertama kali untuk SELURUH `web/static/js/` (31 file, semua diperiksa baris-per-baris; backend tidak disentuh). 6 bug CONFIRMED (dieksekusi/reproduksi nyata, bukan cuma baca kode) dan beberapa dead-code/minor findings. - **BUG-1 (Kritis, CONFIRMED):** `#vol-slider` ada di `index.html` tapi tidak pernah dipetakan di `dom.js` (`dom.volSlider` selalu `undefined`). Akibatnya seluruh listener drag volume di `transport-events.js` tidak pernah ter-attach (`if (dom.volSlider)` selalu false) dan render/player.js tidak pernah sinkron nilainya — slider volume 100% non-fungsional dari awal. Fix: tambah `volSlider: $("vol-slider")` ke `dom.js`. - **BUG-2 (Kritis, CONFIRMED lewat eksekusi nyata):** `window.safeStorage` cuma expose `.get/.set/.remove` (lihat `utils/toast.js`), tapi `search-input-events.js` memanggil `.getItem/.setItem/.removeItem` gaya `localStorage` yang TIDAK ADA di objek itu. `saveSearchHistory()` throw `TypeError` tak tertangkap, dan karena baris ini dipanggil SEBELUM `wsSend("search", ...)` baik di debounce-input maupun handler Enter, exception ini menghentikan seluruh callback → `wsSend("search")` TIDAK PERNAH terpanggil. Direproduksi dengan skrip Node standalone yang meniru pola kode persis — dikonfirmasi search tidak terkirim. **Dampak: fitur SEARCH mati total di seluruh aplikasi**, bukan cuma riwayat pencarian. Fix: ganti ke `.get/.set/.remove`, bungkus `saveSearchHistory` dengan try/catch sebagai defense-in-depth. - **BUG-3 (Kritis, CONFIRMED):** `render/player.js` (`_renderProgressCore`) memakai `window.audio` untuk logic volume-fade crossfade, tapi `window.audio` TIDAK PERNAH di-assign di manapun (elemen `<audio>` browser diakses lewat `getOrInitAudio()`/`localAudio` di `audio/playback-sync.js`, bukan `window.audio`). Kondisi selalu falsy → seluruh efek fade-out/fade-in volume crossfade untuk output browser adalah dead code, toggle crossfade di Settings tidak berefek pada audio yang sedang main di mode browser. Fix: ganti ke `getOrInitAudio()`. - **BUG-4 (Sedang, CONFIRMED):** `platform/keyboard.js` memanggil `cmd('play')/cmd('next')/cmd('prev')` — fungsi `cmd` tidak pernah didefinisikan di manapun di codebase (grep kosong). `typeof cmd === 'function'` selalu false → ArrowLeft/ArrowRight/Space di desktop cuma `preventDefault()` tanpa efek (fitur mati sejak awal). Kasus `Space` juga duplicate listener dengan `events/keyboard-shortcut-events.js` (yang sudah admin-gated dan benar-benar jalan). Fix: hapus case Space yang duplikat, sambungkan ArrowLeft/ArrowRight langsung ke `wsSend` dengan guard admin. - **BUG-5 (XSS, CONFIRMED):** `search-input-events.js` → `renderSearchHistory()` menyisipkan query pencarian (asal input user, disimpan di localStorage) langsung ke `innerHTML` tanpa escape untuk teks yang tampil (`<span>${q}</span>`) — cuma tanda kutip `"` yang di-escape untuk atribut `data-query`. Query berisi markup HTML/script tersimpan lalu dieksekusi ulang tiap kali riwayat pencarian dirender (stored self-XSS). Fix: pakai `escapeHtml()` untuk teks maupun atribut. - **BUG-6 (Sedang, SUSPECTED — pola dikonfirmasi lewat perbandingan kode, belum direproduksi di device fisik):** `events/progress-events.js` (drag seek bar) tidak punya handler `pointercancel`, tidak seperti drag-reorder queue (`events/queue-events.js`) yang sudah benar menanganinya. Kalau pointer sequence di-cancel OS/browser di tengah drag (gesture back, incoming call, multi-touch) tanpa `pointerup`, `window.isDraggingPb` nyangkut `true` selamanya → progress bar freeze permanen (rAF interpolation loop dan `renderProgress()` sama-sama early-return selama flag itu true), walau playback tetap jalan normal. Fix: tambah handler `pointercancel` yang reset flag + release pointer capture. - **MINOR-1:** `ws.js` — `store.userRole = "admin"` ter-assign 2x berturut-turut di `auth_status` handler (sisa edit sebelumnya, harmless). Fix: hapus baris duplikat. - **MINOR-2:** `sw.js` — `PRECACHE_ASSETS` tidak menyertakan `audio/playback-sync.js` dan `audio/visualizer.js` (script inti pemutar audio browser). SW registration saat ini masih dimatikan di `main.js` jadi belum berdampak, tapi akan menyebabkan first-offline-load kehilangan script pemutar audio kalau SW diaktifkan lagi tanpa fix ini. Fix: tambahkan ke daftar precache. - **DEAD CODE (dilaporkan, TIDAK dihapus — di luar scope "fix bug", risiko regresi kalau dihapus tanpa keputusan desain):** - `events/click-delegation-events.js` blok 3 menangani selector `.disc-card, .fav-card, .search-result-item` — tidak ada kode render manapun (discover-tab.js, search.js) yang menghasilkan elemen dengan class ini (semua pakai `.sr-item`). Blok ini 100% unreachable, kemungkinan sisa refactor/rename lama. - `audio/visualizer.js`: `startVisualizerLoop()`/`resumeVisualizerLoop()` (visualizer asli berbasis Web Audio API `analyser`/`dataArray`) tidak pernah dipanggil dari manapun, dan `analyser`/`dataArray` (dideklarasikan di `playback-sync.js`) tidak pernah di-assign (tidak ada `createAnalyser()`/`createMediaElementSource()`). `initAudio()` cuma memanggil `startFakeBeatLoop()` (efek beat berbasis timer, bukan analisis audio asli) — implementasi analyser sepenuhnya mati, tergantikan tanpa dibersihkan. - `transport-events.js` mereferensikan `dom.btnStop` — tidak ada elemen `#btn-stop` di `index.html` dan tidak dipetakan di `dom.js`; guard `if (dom.btnStop)` membuat ini no-op aman, Stop tetap bisa diakses lewat `ss-stop-btn` di Settings sheet yang sudah benar. **Verifikasi:** `vitest run` 14/14 tetap passed (3 file test, tidak ada regresi), `node --check` bersih untuk semua 7 file yang diedit, reproduksi manual (skrip Node standalone) mengkonfirmasi BUG-2 sebelum & sesudah fix.

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

**Ringkasan:** Audit mendalam pertama untuk `launcher/` (tkinter GUI server manager, sebelumnya belum pernah diaudit). Dua bug confirmed lewat eksekusi nyata: (1) **Kontrak file `cache/admin_password.txt` tidak sinkron** — `launcher/gui/auth_panel.py` menulis password yang SUDAH di-hash ke file itu, padahal `config.py` (dan `config_security.generate_admin_password()`) membaca isi file sebagai plaintext mentah lalu meng-hash-nya sendiri di setiap startup server. Akibatnya password yang ditampilkan ke user di dialog first-run/reset TIDAK PERNAH cocok dengan hash yang dipakai server untuk verifikasi login — admin lockout total. Dibuktikan lewat skrip reproduksi yang meniru alur `config.py`: `verify_password(raw_password, ADMIN_PASSWORD)` selalu `False`. Fix: `_reset_password()` sekarang menulis raw password (root cause ada di kontrak antar-modul, bukan di `core.security`). (2) **Race destroy vs background thread** — semua callback dari background thread (dependency checker, loop refresh status tiap 2 detik, log writer, restart timer, popup server-ready) memanggil `self.after()`/`app.after()` tanpa guard apapun. Begitu window GUI ditutup sementara thread masih berjalan, callback yang telat crash dengan `RuntimeError: main thread is not in main loop`. Direproduksi nyata lewat Xvfb headless + `threading.excepthook`. Fix: tambah flag `ServerManager._closing` (di-set di `destroy()`) dan helper `_safe_after()` yang dipakai di semua titik pemanggilan `.after()` dari thread/loop; loop `_refresh_status()` juga berhenti reschedule begitu closing. **Catatan tooling:** ditemukan bug tambahan (belum di-fix, di luar scope sesi ini) di `automation/patchlog.py` — `parse_entries()` gagal mem-parse `docs/PATCHLOG.md` yang sudah ada (mengembalikan 0 entri walau ada 63 entri valid), sehingga `patchlog.py add` salah menomori ID baru jadi `-001` dan menimpa `total_entries` jadi `1`. File tidak sengaja sempat tertimpa saat sesi ini dan sudah dipulihkan dari arsip asli sebelum lanjut. **SUSPECTED root cause** (belum diverifikasi lebih lanjut): kemungkinan mismatch regex `ENTRY_RE` terhadap format aktual (spasi/newline ganda) di file nyata — perlu audit terpisah, jangan pakai `patchlog.py add` sampai ini diperbaiki, edit `docs/PATCHLOG.md` manual dulu.

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

## [2026-07-16] Race Condition — Pinned TCP Port MPV Diabaikan di Windows

**ID:** `PATCH-2026-07-15-061`

**Tanggal:** 2026-07-15

**Ringkasan:** Audit manual (bukan dari automation/, karena `event_graph.py` cs. hanya cek pub/sub event & arsitektur, bukan kelengkapan WS-action↔frontend-wiring) menemukan 5 fitur backend yang "orphan" (tidak reachable dari client) dan 1 dead code, ditemukan bertahap saat implementasi berjalan. - **BUG-1 (Kritis, fitur baru sprint 3.3 tidak pernah tersambung):** Loudness Normalization — pipeline lengkap (`LoudnessService`, `gain_calculator.py`, `CMD_SET_LOUDNESS_NORMALIZATION` di `command_router.py`) sudah ada sejak sprint 3.3, tapi action `set_loudness_normalization` tidak pernah didaftarkan di `PLAYBACK_CMDS`/`handle_playback_command`, dan tidak ada UI toggle sama sekali. Fix: tambah action ke WS routing + toggle di Settings sheet (pola sama seperti Crossfade), termasuk sync `data-on` di `renderSettingsSheet()`. - **BUG-2 (Kritis):** `queue_select` (`CMD_QUEUE_SELECT`) sudah full-implemented & full-tested di backend, tapi `queue-events.js` cuma daftarin click listener untuk `.qi-remove` — klik baris lagu di antrean manual tidak melakukan apapun. Fix: tambah click delegation di `queueList` yang kirim `queue_select` saat item (bukan drag handle/tombol hapus) diklik. - **BUG-3 (Dead code + fitur mati sejak awal):** Drag-to-reorder queue (`_onDragStart` di `queue-events.js`) butuh elemen `.qi-drag` (CSS-nya sudah ada di `queue.css`), tapi `createQueueItemTemplate()` di `render/queue.js` tidak pernah membuat elemen itu — drag-reorder gak pernah bisa dipakai dari awal. Fix: tambah `<span class="qi-drag">` ke template, disembunyikan untuk current-track item (sama seperti tombol hapus). - **BUG-4 (Dead code, query DB sia-sia):** `ws_discovery.py` action `discover` mengambil `ds.get_favorites(15)` tapi hasilnya dibuang — tidak dimasukkan ke payload `discover_data`. Kolom `is_favorite` + `toggle_favorite()` di `persistence/track_repo.py` sudah ada tapi datanya tidak pernah sampai ke client. Fix: masukkan `favorites` ke payload (di `ws_discovery.py` dan `ws_download.py` — dua tempat yang broadcast `discover_data`), tambah section "Favorit" di tab Discover (pola sama seperti "Tersimpan Lokal"). - **Catatan lanjutan (belum dikerjakan, butuh keputusan desain terpisah):** `toggle_favorite()` di persistence masih belum ada command/WS action untuk memicunya (belum ada tombol "like"/heart di UI). Favorit saat ini hanya bisa terisi lewat kolom `play_count`/`is_favorite` yang di-set manual di DB. Fitur "like" penuh (heart button, `CMD_TOGGLE_FAVORITE`) sengaja tidak dibuat di patch ini karena itu fitur baru, bukan bug fix. - **BUG-5 (Dead code sejak awal, ditemukan sampingan):** `dom.discRecent` di `dom.js` menunjuk ke `#discover-recent` yang tidak pernah ada di `index.html` — section "Baru Diputar" di tab Discover selalu `null`/dead. Fix: tambah container `#discover-recent` di `index.html`. - **DITEMUKAN TAPI BELUM DIPERBAIKI (di luar scope patch ini, butuh konfirmasi):** `pytest` penuh menemukan 2 test gagal yang **tidak berkaitan** dengan perubahan patch ini — `test_app_state_defaults` (`core/state.py`: default `sponsorblock_active` seharusnya `True` tapi aktual `False`) dan `test_sponsorblock_on_progress_seeks_past_segment` (`plugins/sponsorblock.py`: seek tidak terpanggil saat posisi masuk segmen). Kedua file tidak disentuh oleh patch ini — kemungkinan regresi lama yang belum ketahuan. Perlu sesi audit terpisah. **Verifikasi:** `ruff check` bersih, `mypy` bersih (4 file tersentuh), `pytest` 456 passed/2 failed-pre-existing/4 skipped, `vitest run` 14/14 passed, `automation/doctor.py` skornya identik dengan sebelum patch (tidak ada regresi arsitektur/dokumentasi/keamanan baru).

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

**Ringkasan:** Penambahan test yang hilang pasca-implementasi PATCH-058 dan PATCH-059. - `test_websocket.py`: Tambah `test_new_playback_actions_are_routed` (parametrize 5 action: stop, set_sleep_timer, set_speed, set_loop, set_crossfade), `test_cache_commands_are_routed`, `test_unknown_action_does_not_crash`. - `test_serializers.py`: Tambah assert untuk 3 field baru di `state_to_dict` (playback_speed, loop_mode, crossfade_enabled) termasuk verifikasi nilai non-default.

**File Terdampak:**

- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_serializers.py`

---

## [2026-07-15] Test Coverage — Sesi Audit Bug Fix

**ID:** `PATCH-2026-07-15-059`

**Tanggal:** 2026-07-15

**Ringkasan:** Audit runtime menemukan 3 bug lanjutan setelah PATCH-058. - **BUG-A (Kritis):** `server/serializers.py` tidak menyertakan `playback_speed`, `loop_mode`, `crossfade_enabled` di payload state WS. Akibatnya toggle crossfade tidak bisa di-sync dari server, speed tidak persist setelah reconnect, loop mode button tidak reflect state server. Fix: tambahkan 3 field ke `state_to_dict()`. - **BUG-B (Kritis):** Kecepatan pemutaran hanya dikirim ke MPV (hanya berlaku untuk output Device). Browser audio (`<audio>`) tidak punya hook ke MPV property. Fix: tambahkan `audio.playbackRate = speed` di `settings-events.js` dan `full-state.js`. - **IMPROVE-C:** Sleep timer tidak punya feedback visual — subtitle hanya menampilkan "15 Menit" statis. Fix: tambahkan countdown timer client-side yang mundur detik per detik dan reset ke "Mati" saat habis.

**File Terdampak:**

- `server/serializers.py`
- `web/static/js/render/full-state.js`
- `web/static/js/events/settings-events.js`

---

## [2026-07-15] Audit Pasca-Implementasi T1–T16 — 4 Bug Kritis & 2 Bug Minor

**ID:** `PATCH-2026-07-15-058`

**Tanggal:** 2026-07-15

**Ringkasan:** Audit pasca-implementasi T1–T16 menemukan 4 bug kritis dan 2 bug minor yang menyebabkan beberapa fitur baru tidak berfungsi dari frontend. - **BUG-1 (Kritis):** `PLAYBACK_CMDS` di `server/handlers/websocket.py` tidak mencakup 5 action baru (`stop`, `set_sleep_timer`, `set_speed`, `set_loop`, `set_crossfade`). WebSocket menerima pesan tapi diam-diam mengabaikannya. Fix: tambahkan 5 action ke set. - **BUG-2 (Kritis):** `store.js` tidak punya field `crossfade_enabled`. Fix: tambahkan `crossfade_enabled: false` ke `createStore()`. - **BUG-3 (Kritis):** `transport-events.js` membaca `store.loopMode` (camelCase) padahal store memakai `store.loop_mode` (snake_case). Tombol Repeat selalu cycle ke "track". Fix: rename ke `loop_mode`. - **BUG-4 (Kritis):** `queue_manager.py` punya dead code `pass` di blok `loop_mode == "queue"` saat queue kosong. Fix: hapus blok if/pass yang tidak berguna. - **MINOR-1:** `core/state.py` mendefinisikan `playback_speed` dan `loop_mode` dua kali di dataclass. Fix: hapus duplikat. - **MINOR-2:** `settings-events.js` mendaftarkan listener `sbToggle.click` dua kali, yang kedua mengirim action `toggle_sponsorblock` yang tidak ada handler-nya. Fix: hapus listener duplikat.

**File Terdampak:**

- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/events/transport-events.js`
- `engine/queue_manager.py`
- `core/state.py`
- `web/static/js/events/settings-events.js`

---

## [2026-07-15] T16: Implementasi Crossfade Eksperimental

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

**Ringkasan:** Eksekusi integrasi 3 fitur besar secara serentak untuk mematuhi larangan two-stage refactoring: 1. Thompson Sampling Bandit untuk Artist Radio. 2. EBU R128 Loudness Normalization. 3. Adaptive Network Prefetch (Latency Window). Fitur dipisah ke service/kelas baru dan controller dimodifikasi untuk injeksi ketergantungan.

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

## [2026-07-14] Baseline Stable v1.0.0 Release

**ID:** `PATCH-2026-07-14-040`

**Tanggal:** 2026-07-14

**Ringkasan:** Finalisasi "stable baseline version" v1.0.0. Mengubah status item tertunda menjadi ❄️ Frozen (v1.0.0 Baseline) di `STATUS.md`, menambahkan `CHANGELOG.md`, `CONTRIBUTING.md`, dan `SECURITY.md` (Open Source Readiness), dan melakukan tag v1.0.0 pada repositori.

**File Terdampak:**

- `docs/STATUS.md`
- `CHANGELOG.md` [NEW]
- `CONTRIBUTING.md` [NEW]
- `SECURITY.md` [NEW]

---

## [2026-07-14] Standardize Docstrings Format

**ID:** `PATCH-2026-07-14-039`

**Tanggal:** 2026-07-14

**Ringkasan:** Menyeragamkan format docstring pada 145 file menggunakan analisis AST dinamis untuk memastikan kelengkapan field sesuai standar.

**File Terdampak:**

- All python files (145 files across the codebase)

---

## [2026-07-14] automation - all tests and linters passing

**ID:** `PATCH-2026-07-14-038`

**Tanggal:** 2026-07-14

**Ringkasan:** automation - all tests and linters passing

**File Terdampak:**

- `docs/PATCHLOG.md`

---

## [2026-07-13] Skenario Integration Test & Generator Script Fix

**ID:** `PATCH-2026-07-13-037`

**Tanggal:** 2026-07-13

**Ringkasan:** Membangun `tests/integration/conftest.py` dengan komponen asli (EventBus, DB, yt-dlp) untuk integration testing. Menambahkan 4 end-to-end flow test (IT-01 sampai IT-04) untuk memastikan fungsionalitas WebSocket, Playback, Radio, dan Download berjalan dengan baik. Selain itu, generator script `generate_file_index.py` direfactor supaya dapat mendeteksi file dan folder secara dinamis tanpa hardcode. Crash encoding cp1252 pada output di terminal Windows juga telah diatasi.

**File Terdampak:**

- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_websocket_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_download_flow.py`
- `scripts/generate_file_index.py`
- `scripts/generate_report.py`
- `scripts/run_all.py`

---

## [2026-07-13] Patch — Reorganisasi Dokumentasi (docs/kompas/ → docs/)

**ID:** `PATCH-2026-07-13-036`

**Tanggal:** 2026-07-13

**Ringkasan:** Memindahkan seluruh file dan folder implementasi arsitektur dari `docs/kompas/` ke root dokumentasi `docs/`. Menghapus folder `docs/kompas/` yang sudah kosong dan memperbarui referensi di seluruh proyek (`AI_CONTEXT.md`, `.py` scripts, `.md` docs). Dokumentasi ini kini menjadi referensi utama karena migrasi telah dinyatakan terealisasi 100%.

**File Terdampak:**

- `docs/kompas/*` ➔ `docs/*` [MOVED]
- `docs/Blueprint.md`, `docs/architecture/`, `docs/adr/`, `docs/backend/`, `docs/frontend/`, `docs/testing/`, `docs/devops/`, `docs/development/`, `docs/security/`, `docs/opensource/` [NEW PATHS]
- `AI_CONTEXT.md` [MODIFIED]
- `CONTRIBUTING.md` [MODIFIED]
- `docs/MIGRATION_GUIDE.md` [MODIFIED]
- `docs/PATCHLOG.md` [MODIFIED]
- `docs/STATUS.md` [MODIFIED]
- `docs/FILE_INDEX.md` [MODIFIED]
- `scripts/architecture_lint.py` [MODIFIED]
- `scripts/find_owner.py` [MODIFIED]
- `scripts/verify_structure.py` [MODIFIED]
- `tests/conftest.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 13: Evaluasi Arsitektur & Open Source Readiness

**ID:** `PATCH-2026-07-13-035`

**Tanggal:** 2026-07-13

**Ringkasan:** Menyelesaikan checklist Tahap 13. Melakukan evaluasi arsitektur berdasarkan `docs/blueprint.md` menggunakan `import-linter`. Hasilnya: 0 pelanggaran (semua dependency contract terpenuhi). Selain itu, semua file standar open source readiness telah ditambahkan.

**File Terdampak:**

- `.importlinter` [MODIFIED] — menambahkan `include_external_packages = True` dan multiline root_packages
- `requirements-dev.txt` [MODIFIED] — ditambahkan secara otomatis pada environment lokal
- `LICENSE` [NEW] — MIT License
- `CHANGELOG.md` [NEW] — Changelog file
- `CONTRIBUTING.md` [NEW] — Panduan kontribusi
- `SECURITY.md` [NEW] — Kebijakan keamanan
- `.editorconfig` [NEW] — Editor config
- `.github/PULL_REQUEST_TEMPLATE.md` [NEW]
- `.github/ISSUE_TEMPLATE/bug_report.md` [NEW]
- `.github/ISSUE_TEMPLATE/feature_request.md` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 12b: Prioritas Test per Layer (Adapter/Plugin/Server)

**ID:** `PATCH-2026-07-13-034`

**Tanggal:** 2026-07-13

**Ringkasan:** Melengkapi unit tests Prioritas 2 (Adapter/Plugin/Server logic) menggunakan mocks dan fakes. Menambahkan `services/__init__.py` yang hilang agar test coverage penuh dapat dieksekusi. Total test suite kini berjumlah 295 test case yang lulus penuh.

**File Terdampak:**

- `tests/unit/launcher/gui/test_dep_checker.py` [NEW]
- `tests/unit/server/test_connection_manager.py` [NEW]
- `tests/unit/server/test_middleware.py` [NEW]
- `tests/unit/server/test_serializers.py` [NEW]
- `tests/unit/engine/radio/test_artist_selector.py` [NEW]
- `tests/unit/engine/radio/test_prefetcher.py` [NEW]
- `tests/unit/engine/radio/test_engine.py` [NEW]
- `tests/unit/plugins/test_lyrics_parser.py` [NEW]
- `tests/unit/plugins/test_lyrics_sync.py` [NEW]
- `services/__init__.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 12b: Prioritas Test per Layer (Pure Logic)

**ID:** `PATCH-2026-07-13-033`

**Tanggal:** 2026-07-13

**Ringkasan:** Melengkapi unit tests Prioritas 1 (Pure Logic / Zero I/O) yang sebelumnya masih *missing* pada fase 12b. Total 16 test cases ditambahkan dan seluruhnya lulus (`16 passed`).

**File Terdampak:**

- `tests/unit/persistence/test_library_repo.py` [NEW]
- `tests/unit/engine/radio/test_track_interleaver.py` [NEW]
- `tests/unit/engine/playback/test_queue_ops.py` [NEW]
- `tests/unit/engine/playback/test_mode_ops.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 12a: Setup Testing Infrastructure

**ID:** `PATCH-2026-07-13-032`

**Tanggal:** 2026-07-13

**Ringkasan:** Setup folder struktur testing, pembuatan *fakes* (LyricsProvider, SponsorBlockProvider), dan modifikasi *fixture* `memory_db` di `conftest.py` sesuai panduan MIGRATION_GUIDE Tahap 12a.

**File Terdampak:**

- `tests/unit/adapters/mpv/` [NEW DIR]
- `tests/unit/engine/radio/` [NEW DIR]
- `tests/unit/engine/playback/` [NEW DIR]
- `tests/unit/server/handlers/` [NEW DIR]
- `tests/unit/server/services/` [NEW DIR]
- `tests/unit/plugins/` [NEW DIR]
- `tests/unit/launcher/gui/` [NEW DIR]
- `tests/integration/` [NEW DIR]
- `tests/frontend/utils/` [NEW DIR]
- `tests/fakes/fake_lyrics_provider.py` [NEW]
- `tests/fakes/fake_sponsorblock_provider.py` [NEW]
- `tests/conftest.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 11: Config, Tooling, CI

**ID:** `PATCH-2026-07-13-031`

**Tanggal:** 2026-07-13

**Ringkasan:** Setup file konfigurasi DevOps/Tooling sesuai MIGRATION_GUIDE tahap 11.

**File Terdampak:**

- `pyproject.toml` [MODIFIED]
- `.importlinter` [NEW]
- `.pre-commit-config.yaml` [MODIFIED]
- `.github/workflows/ci.yml` [MODIFIED]
- `.github/workflows/release.yml` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 9: Ekstraksi Frontend & Fix Doctor

**ID:** `PATCH-2026-07-13-030`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith frontend (player-events, audio, utils, discover) sesuai tahap 9, dan membereskan peringatan `doctor.py`.

**File Terdampak:**

- `web/static/js/events/*` [NEW]
- `web/static/js/audio/*` [NEW]
- `web/static/js/utils/*` [NEW]
- `web/static/js/render/*` [NEW]
- `web/static/js/ws.js` [MODIFIED]
- `web/static/index.html` [MODIFIED]
- `scripts/verify_docs/checks_docs.py` [MODIFIED]
- `scripts/architecture_lint.py` [MODIFIED]
- `scripts/generate_file_index.py` [MODIFIED]
- `docs/CONSTRAINTS.md` [NEW]
- `docs/rfc/.keep` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 8: Pembersihan Sisa

**ID:** `PATCH-2026-07-13-029`

**Tanggal:** 2026-07-13

**Ringkasan:** Merapikan struktur folder sesuai dengan MIGRATION_GUIDE tahap 8.

**File Terdampak:**

- `data/export_to_sqlite.py` -> `scripts/export_to_sqlite.py` [MOVED]
- `cache/schema.sql` [DELETED]
- `plugins/lyrics.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 7: Extract server/ WebSocket + launcher/gui/

**ID:** `PATCH-2026-07-13-028`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith websocket handler dan launcher GUI menjadi komponen diskrit yang sesuai dengan prinsip Single Responsibility.

**File Terdampak:**

- `server/handlers/websocket.py` [MODIFIED]
- `server/connection_manager.py` [NEW]
- `server/handlers/ws_*.py` [NEW]
- `launcher/gui.py` [MODIFIED]
- `launcher/gui/app.py`, `ui_builder.py`, `popups.py`,  `auth_panel.py`, `dep_checker.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 6: Extract engine/playback/controller.py

**ID:** `PATCH-2026-07-13-027`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith controller.py dengan memisahkan mutasi antrean dan pengaturan mode.

**File Terdampak:**

- `engine/playback/queue_ops.py` [NEW]
- `engine/playback/mode_ops.py` [NEW]
- `engine/playback/controller.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 5: Extract engine/radio/

**ID:** `PATCH-2026-07-13-026`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith engine/radio_engine.py berukuran 440 baris menjadi modul terpisah untuk isolasi bug radio mode.

**File Terdampak:**

- `engine/radio_engine.py` (menjadi alias)
- `engine/radio/artist_selector.py` [NEW]
- `engine/radio/track_interleaver.py` [NEW]
- `engine/radio/prefetcher.py` [NEW]
- `engine/radio/engine.py` [NEW]
- `engine/radio/__init__.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 4: Extract adapters/ytdlp/

**ID:** `PATCH-2026-07-13-025`

**Tanggal:** 2026-07-13

**Ringkasan:** Extract logika integrasi yt-dlp dari `engine/ytdlp_client.py` menjadi modul-modul independen di `adapters/ytdlp/`. Implementasi ini juga menyertakan `ThreadPoolExecutor` yang dibagikan antar komponen dari `YtDlpClient` Facade.

**File Terdampak:**

- `adapters/ytdlp/common.py` [NEW] — `YDL_OPTS_INFO`
- `adapters/ytdlp/searcher.py` [NEW] — `YtDlpSearcher`
- `adapters/ytdlp/resolver.py` [NEW] — `YtDlpResolver`
- `adapters/ytdlp/downloader.py` [NEW] — `YtDlpDownloader`
- `adapters/ytdlp/__init__.py` [NEW] — `YtDlpClient` Facade
- `engine/ytdlp_client.py` — [MODIFIED] re-export alias untuk backward compatibility

---

## [2026-07-13] Patch — MIGRATION Tahap 3: Extract adapters/mpv/

**ID:** `PATCH-2026-07-13-024`

**Tanggal:** 2026-07-13

**Ringkasan:** Extract logika koneksi, IPC, dan event loop observasi dari `engine/mpv_controller.py` menjadi modul-modul independen di `adapters/mpv/`. Menambahkan pola Facade di `adapters/mpv/__init__.py`. `engine/mpv_controller.py` kini hanya berfungsi sebagai re-export alias untuk backward compatibility.

**File Terdampak:**

- `adapters/mpv/connection.py` [NEW] — `MpvConnection`
- `adapters/mpv/ipc.py` [NEW] — `MpvIPC`
- `adapters/mpv/observer.py` [NEW] — `MpvObserver`
- `adapters/mpv/__init__.py` [NEW] — `MpvController` Facade
- `engine/mpv_controller.py` — [MODIFIED] acts as alias

---

## [2026-07-13] Patch — MIGRATION Tahap 2: Extract persistence/

**ID:** `PATCH-2026-07-13-023`

**Tanggal:** 2026-07-13

**Ringkasan:** Extract god-class `cache/db.py` (388 baris) menjadi repository terpisah di layer `persistence/` (`track_repo`, `artist_repo`, `session_repo`, `genre_repo`, `library_repo`). Mengimplementasikan Facade pattern untuk `Database` di `persistence/__init__.py`. `cache/db.py` diubah menjadi alias re-export agar backward compatible.

**File Terdampak:**

- `persistence/db.py` [NEW] — SQLite connection logic
- `persistence/track_repo.py` [NEW] — Track metadata & url caching
- `persistence/session_repo.py` [NEW] — Web sessions
- `persistence/artist_repo.py` [NEW] — Artist data
- `persistence/genre_repo.py` [NEW] — Genre data
- `persistence/library_repo.py` [NEW] — Cross-domain/random queries
- `persistence/__init__.py` — [MODIFIED] Facade pattern
- `cache/db.py` — [MODIFIED] acts as alias
- `persistence/schema.sql` — [NEW] copy dari cache/
- `scripts/architecture_lint.py` — [MODIFIED] izinkan `cache` import `persistence`

---

## [2026-07-13] Patch — MIGRATION Tahap 1: Setup Pondasi

**ID:** `PATCH-2026-07-13-022`

**Tanggal:** 2026-07-13

**Ringkasan:** Setup struktur folder target migrasi (`adapters/`, `engine/radio/`, `persistence/`, `launcher/gui/`), extract constants `CMD_*` dari `core/command_bus.py` ke `core/commands.py`, dan memisahkan fungsi admin password generation dari `config.py` ke `config_security.py`.

**File Terdampak:**

- `adapters/__init__.py`, `adapters/mpv/__init__.py`, `adapters/ytdlp/__init__.py` [NEW]
- `engine/radio/__init__.py` [NEW]
- `persistence/__init__.py` [NEW]
- `launcher/__init__.py`, `launcher/gui/__init__.py` [NEW]
- `core/command_bus.py` — pindah CMD_* ke core.commands
- `core/commands.py` — [NEW] menampung CMD_*
- `config.py` — pakai fungsi generate_admin_password
- `config_security.py` — [NEW] fungsi generate_admin_password

---

## [2026-07-11] Patch — Batch 12: Startup Script Cleanup

**ID:** `PATCH-2026-07-11-021`

**Tanggal:** 2026-07-11

**Ringkasan:** Gabung 7× subprocess dep-check Python menjadi 1×; hapus `sleep`/`ping` artifisial di `start.sh` dan `start.bat`.

**File Terdampak:**

- `start.sh` — single-import dep check, hapus sleep 0.5 dan sleep 1
- `start.bat` — single-import dep check, hapus ping delays

---

## [2026-07-11] Patch — Batch 11: OTel Tracing Dead Weight (Opsi A)

**ID:** `PATCH-2026-07-11-020`

**Tanggal:** 2026-07-11

**Ringkasan:** Hapus OTel span dari `command_bus.py` (tidak ada exporter aktif, 100% sia-sia); hapus setup_tracing dan import OTel dari `observability.py`.

**File Terdampak:**

- `core/command_bus.py` — hapus tracer import dan span context manager
- `core/observability.py` — hapus OTel imports, setup_tracing, tracer

---

## [2026-07-11] Patch — Batch 10: Serializers Lirik (Variant A)

**ID:** `PATCH-2026-07-11-019`

**Tanggal:** 2026-07-11

**Ringkasan:** Tambah parameter `include_lyrics` di `state_to_dict()` dan `broadcast_state()`; default False untuk broadcast periodik, True untuk initial snapshot.

**File Terdampak:**

- `server/serializers.py` — tambah include_lyrics param
- `server/services/broadcast_service.py` — default include_lyrics=False

---

## [2026-07-11] Patch — Batch 9: websocket.py + controller.py (Restricted, gabungan)

**ID:** `PATCH-2026-07-11-018`

**Tanggal:** 2026-07-11

**Ringkasan:** `toggle_pause()` fire-and-forget; broadcast paralel ke semua WS client; parallelkan query Discover di action `discover` & `delete_download`.

**File Terdampak:**

- `server/handlers/websocket.py` — asyncio import, parallel broadcast, parallel discover queries, include_lyrics=True initial snapshot
- `engine/playback/controller.py` — safe_create_task mpv_toggle_pause

---

## [2026-07-11] Patch — Batch 8: DB Index

**ID:** `PATCH-2026-07-11-017`

**Tanggal:** 2026-07-11

**Ringkasan:** Tambah `idx_songs_artist_id` pada tabel `songs` untuk JOIN query di Discover/Radio.

**File Terdampak:**

- `cache/schema.sql` — tambah index idx_songs_artist_id

---

## [2026-07-11] Patch — Batch 7: Event Listeners

**ID:** `PATCH-2026-07-11-016`

**Tanggal:** 2026-07-11

**Ringkasan:** Hapus throttle redundant `_on_track_progress` (sudah ditangani di mpv_controller); parallelkan query Discover di `_on_download_complete`.

**File Terdampak:**

- `server/handlers/event_listeners.py` — hapus throttle, asyncio.gather discover queries

---

## [2026-07-11] Patch — Batch 6: Track Loader

**ID:** `PATCH-2026-07-11-015`

**Tanggal:** 2026-07-11

**Ringkasan:** `increment_play_count` dijadikan `safe_create_task` (fire-and-forget) agar tidak menunda playback.

**File Terdampak:**

- `engine/playback/track_loader.py` — increment_play_count non-blocking

---

## [2026-07-11] Patch — Batch 5: Lyrics Plugin

**ID:** `PATCH-2026-07-11-014`

**Tanggal:** 2026-07-11

**Ringkasan:** Throttle `LyricsUpdatedEvent` (min 0.5s antar broadcast); lazy import `syncedlyrics`.

**File Terdampak:**

- `plugins/lyrics.py` — throttle LyricsUpdatedEvent, lazy import syncedlyrics

---

## [2026-07-11] Patch — Batch 4: mpv Controller

**ID:** `PATCH-2026-07-11-013`

**Tanggal:** 2026-07-11

**Ringkasan:** Throttle publish `TrackProgressEvent` ke 1×/detik; parallelkan 3× `observe_property` saat connect.

**File Terdampak:**

- `engine/mpv_controller.py` — throttle TrackProgressEvent, parallel observe_property

---

## [2026-07-11] Patch — Batch 3: main.py Housekeeping

**ID:** `PATCH-2026-07-11-012`

**Tanggal:** 2026-07-11

**Ringkasan:** Parallelkan `db.init()` + `mpv.connect()` via `asyncio.gather`; naikkan interval poller (mpv reconnect 5→30s, connectivity 60→300s); tambah `db_maintenance()` task tiap 6 jam.

**File Terdampak:**

- `main.py` — parallel init, interval poller, db_maintenance task

---

## [2026-07-11] Patch — Batch 2: Auth Non-Blocking

**ID:** `PATCH-2026-07-11-011`

**Tanggal:** 2026-07-11

**Ringkasan:** `verify_password()` (PBKDF2 100k iter) dipindah ke `run_in_executor` agar tidak memblokir event loop seluruh client selama proses login.

**File Terdampak:**

- `server/handlers/auth.py` — tambah asyncio import, ganti verify_password ke run_in_executor

---

## [2026-07-11] Patch — Batch 1: yt-dlp Client

**ID:** `PATCH-2026-07-11-010`

**Tanggal:** 2026-07-11

**Ringkasan:** Lazy import `yt_dlp` di `_extract_sync` & `_download_sync`; tambah `socket_timeout` dan `extractor_retries` ke `_YDL_OPTS_INFO` untuk mencegah thread zombie saat jaringan buruk.

**File Terdampak:**

- `engine/ytdlp_client.py` — lazy import yt_dlp, socket_timeout=10, extractor_retries=1

---

## [2026-07-11] Patch — Refactor scripts/ → shared/ + verify_docs/

**ID:** `PATCH-2026-07-11-009`

**Tanggal:** 2026-07-11

**Ringkasan:** Pecah `verify_docs.py` (850 baris) menjadi package `verify_docs/`, ekstrak utilitas bersama ke package `shared/`. CLI semua script identik — tidak ada breaking change.

**File Terdampak:**

- `scripts/shared/` — [NEW package] `__init__.py`, `check_result.py`, `skip_dirs.py`, `generated_block.py`
- `scripts/verify_docs/` — [NEW package] `__init__.py`, `helpers.py`, `checks_docs.py`, `checks_coverage.py`, `checks_files.py`, `render.py`
- `scripts/verify_docs.py` — refactor jadi thin CLI (~60 baris)
- `scripts/verify_security.py` — hapus local `CheckResult`, pakai `shared.check_result`
- `scripts/verify_structure.py` — hapus local `CheckResult`, pakai `shared.check_result`; pakai `shared.skip_dirs`
- `scripts/architecture_lint.py` — pakai `shared.skip_dirs`; bungkus hasil sebagai `shared.CheckResult`
- `scripts/generate_report.py` — pakai `shared.skip_dirs`, `shared.generated_block`
- `scripts/generate_file_index.py` — pakai `shared.skip_dirs`, `shared.generated_block`
- `docs/STRUCTURE.md` — update deskripsi `scripts/`
- `docs/architecture/folder_structure.md` — update tree `scripts/`
- `AI_CONTEXT.md` — tambah seksi "Struktur internal scripts/"
- `docs/AI_CONTEXT.md` — idem
- `docs/FILE_INDEX.md` — regenerate (file baru masuk index)
- `docs/REPORT.md` — regenerate (statistik file .py bertambah)

---

## [2026-07-10] Patch — Pindah .pre-commit-config.yaml ke Root

**ID:** `PATCH-2026-07-10-008`

**Tanggal:** 2026-07-10

**Ringkasan:** `.pre-commit-config.yaml` dipindah dari `scripts/` ke root repo agar pre-commit bisa baca otomatis saat `git commit`.

**File Terdampak:**

- `.pre-commit-config.yaml` — [MOVED] dari `scripts/` ke root
- `docs/PATCHLOG.md` — koreksi entry sebelumnya
- `docs/devops/tooling.md` — update status dari ❌ ke ✅

---

## [2026-07-10] Patch — Fix Kontradiksi Dokumentasi & Scripts

**ID:** `PATCH-2026-07-10-007`

**Tanggal:** 2026-07-10

**Ringkasan:** Sinkronisasi 5 kontradiksi antara docs dan scripts yang dibuat di sesi sebelumnya.

**File Terdampak:**

- `docs/FILE_INDEX.md` — hapus warning "mungkin stale", tambah marker `BEGIN/END:GENERATED`, update frontmatter ke `generated: true`
- `docs/REPORT.md` — tambah marker `BEGIN/END:GENERATED` di section Statistik Project
- `docs/STRUCTURE.md` — update deskripsi `scripts/` dari isi lama (generate_icons, inject_svgs) ke isi aktual (6 dev tooling scripts)
- `docs/INDEX.md` — selaraskan instruksi "setelah selesai kerja" dengan AI_CONTEXT.md (langkah per-script + run_all), hapus warning "mungkin stale" yang kontradiktif
- `.pre-commit-config.yaml` — dipindah dari `scripts/` ke root repo (opsi A); install dengan `pip install pre-commit && pre-commit install`

---

## [2026-07-09] Patch — Offline CDN Fix

**ID:** `PATCH-2026-07-09-006`

**Tanggal:** 2026-07-09

**Ringkasan:** Self-host Tabler Icons & hapus Google Fonts CDN. UI kini berfungsi penuh tanpa internet.

**File Terdampak:**

- `web/static/index.html` — hapus 4 baris Google Fonts, ganti 1 baris Tabler CDN → lokal
- `web/static/css/tokens.css` — pastikan font fallback stack
- `web/static/css/vendor/tabler-icons.min.css` — [NEW] self-hosted
- `web/static/css/vendor/fonts/*` — [NEW] font files
- `web/static/sw.js` — bump CACHE_VERSION, tambah vendor ke PRECACHE_ASSETS

---

## [2026-07-09] Optimasi Storage Unduhan (Single-File)

**ID:** `PATCH-2026-07-09-005`

**Tanggal:** 2026-07-09

**Ringkasan:** Mengubah logika *download* agar memindahkan (*move*) file langsung ke folder `downloads/` tanpa menduplikatnya di `cache/mp3/`.

**File Terdampak:**

- `engine/download_manager.py`
- `server/handlers/websocket.py`

---

## [2026-07-09] Bugfix — Radio Cover Image Disappearing

**ID:** `PATCH-2026-07-09-004`

**Tanggal:** 2026-07-09

**Ringkasan:** Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken image karena  class tidak dihapus saat elemen DOM di-_recycle_.

**File Terdampak:**

- `web/static/js/render/queue.js`

---

## [2026-07-09] Knowledge Base — Initial Documentation

**ID:** `PATCH-2026-07-09-003`

**Tanggal:** 2026-07-09

**Ringkasan:** Pembuatan awal dokumentasi knowledge base dari source code scan.

**File Terdampak:**

- `docs/INDEX.md` [NEW]
- `docs/STRUCTURE.md` [NEW]
- `docs/FILE_INDEX.md` [NEW]
- `docs/PATCHLOG.md` [NEW]
- `docs/REPORT.md` [NEW]

---

## [2026-07-09] Sprint 3.2 — Extract `start.py` → `launcher/`

**ID:** `PATCH-2026-07-09-002`

**Tanggal:** 2026-07-09

**Ringkasan:** Pecah monolith `start.py` menjadi package `launcher/` dengan separation of concerns.

**File Terdampak:**

- `start.py` (jadi hollow re-export)
- `launcher/` [NEW package — 6 file, lihat "File baru" di bawah]
- `launcher/__init__.py`, `launcher/__main__.py` — coordinator
- `launcher/gui.py` — `ServerManager` Tkinter UI
- `launcher/process.py` — `ServerProcess`, `kill_process_tree()`, `kill_mpv()`
- `launcher/network.py` — `check_port_in_use()`, `get_pid_occupying_port()`
- `launcher/updater.py` — stub OTA updater

---

## [2026-07-09] Sprint 2.1 — LunaWave Rebranding

**ID:** `PATCH-2026-07-09-001`

**Tanggal:** 2026-07-09

**Ringkasan:** Replace semua identitas legacy (YTGUI, ytgui, bagas.fm, YT Termux Player) dengan LunaWave. Zero regresi pada business logic.

**File Terdampak:**

- `config.py`
- `main.py`
- `core/observability.py`
- `web/static/js/utils.js`
- `web/static/manifest.json`
- `web/static/sw.js`
- `web/static/index.html`
- `scripts/generate_icons.py` [NEW]
- `config.py` — env vars primary → `LUNAWAVE_*`, fallback `YTGUI_*`
- `main.py` — log → `lunawave.log`, banner → LunaWave
- `core/observability.py` — metric → `lunawave_events_total`
- `web/static/js/utils.js` — auto-migrate `ytgui_*` → `lunawave_*` localStorage keys
- `web/static/manifest.json`, `sw.js`, `index.html` — PWA identity → LunaWave
- `scripts/generate_icons.py` — [NEW] icon generator PWA

---
