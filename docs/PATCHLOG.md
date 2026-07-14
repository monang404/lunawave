---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-14-039

total_entries: 39

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



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

**Alasan:** Folder `docs/kompas/` dulunya berfungsi sebagai blueprint "visi" di masa depan. Karena migrasi telah selesai dan arsitektur telah terbukti sesuai aturan blueprint (0 violation via `importlinter`), dokumentasi tersebut resmi menjadi kenyataan dan struktur utama.
**Status:** ✅ SELESAI

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



**Alasan:** Tahap penyelesaian akhir untuk dokumentasi arsitektur dan open source sesuai `MIGRATION_GUIDE.md`.

**Status:** ✅ SELESAI



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



**Alasan:** Memenuhi *checklist* MIGRATION_GUIDE tahap 12b Prioritas 2.

**Status:** ✅ SELESAI



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



**Alasan:** Memenuhi *checklist* MIGRATION_GUIDE tahap 12b Prioritas 1.

**Status:** ✅ SELESAI



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



**Alasan:** Penyelesaian MIGRATION_GUIDE tahap 12a. Sebagian struktur test memang sudah ada dari awal.

**Status:** ✅ SELESAI



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



**Alasan:** Penyelesaian MIGRATION_GUIDE tahap 11.

**Status:** ✅ SELESAI



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



**Alasan:** Penyelesaian MIGRATION_GUIDE tahap 9.

**Status:** ✅ SELESAI



---



## [2026-07-13] Patch — MIGRATION Tahap 8: Pembersihan Sisa



**ID:** `PATCH-2026-07-13-029`

**Tanggal:** 2026-07-13

**Ringkasan:** Merapikan struktur folder sesuai dengan MIGRATION_GUIDE tahap 8.

**File Terdampak:**

- `data/export_to_sqlite.py` -> `scripts/export_to_sqlite.py` [MOVED]

- `cache/schema.sql` [DELETED]

- `plugins/lyrics.py` [MODIFIED]



**Alasan:** Menghapus duplikasi schema sql dan memisahkan komponen lyrics.

**Status:** ✅ SELESAI



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



**Alasan:** Pemisahan sesuai Single Responsibility.

**Status:** ✅ SELESAI



---



## [2026-07-13] Patch — MIGRATION Tahap 6: Extract engine/playback/controller.py



**ID:** `PATCH-2026-07-13-027`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith controller.py dengan memisahkan mutasi antrean dan pengaturan mode.

**File Terdampak:**

- `engine/playback/queue_ops.py` [NEW]

- `engine/playback/mode_ops.py` [NEW]

- `engine/playback/controller.py` [MODIFIED]



**Alasan:** Controller utama kini murni bertugas sebagai orchestrator.

**Status:** ✅ SELESAI



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



**Alasan:** Menjamin tidak ada perubahan perilaku pada fungsi inti.

**Status:** ✅ SELESAI



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

- `engine/ytdlp_client.py` — [MO---



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

**Alasan:** Memenuhi Tahap 3 dari MIGRATION_GUIDE, memisahkan concern pada orchestrator mpv.

**Status:** ✅ SELESAI



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

**Alasan:** Memenuhi Tahap 2 dari MIGRATION_GUIDE.

**Status:** ✅ SELESAI



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

**Alasan:** Tahap 1 dari panduan migrasi (Setup Pondasi).

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 12: Startup Script Cleanup



**ID:** `PATCH-2026-07-11-021`

**Tanggal:** 2026-07-11

**Ringkasan:** Gabung 7× subprocess dep-check Python menjadi 1×; hapus `sleep`/`ping` artifisial di `start.sh` dan `start.bat`.

**File Terdampak:**

- `start.sh` — single-import dep check, hapus sleep 0.5 dan sleep 1

- `start.bat` — single-import dep check, hapus ping delays

**Alasan:** Kurangi overhead startup script secara signifikan.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 11: OTel Tracing Dead Weight (Opsi A)



**ID:** `PATCH-2026-07-11-020`

**Tanggal:** 2026-07-11

**Ringkasan:** Hapus OTel span dari `command_bus.py` (tidak ada exporter aktif, 100% sia-sia); hapus setup_tracing dan import OTel dari `observability.py`.

**File Terdampak:**

- `core/command_bus.py` — hapus tracer import dan span context manager

- `core/observability.py` — hapus OTel imports, setup_tracing, tracer

**Alasan:** Zero-benefit CPU work di jalur paling sering dieksekusi; bersihkan dead code.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 10: Serializers Lirik (Variant A)



**ID:** `PATCH-2026-07-11-019`

**Tanggal:** 2026-07-11

**Ringkasan:** Tambah parameter `include_lyrics` di `state_to_dict()` dan `broadcast_state()`; default False untuk broadcast periodik, True untuk initial snapshot.

**File Terdampak:**

- `server/serializers.py` — tambah include_lyrics param

- `server/services/broadcast_service.py` — default include_lyrics=False

**Alasan:** Kurangi payload WS state broadcast yang tidak perlu membawa 200+ baris lirik.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 9: websocket.py + controller.py (Restricted, gabungan)



**ID:** `PATCH-2026-07-11-018`

**Tanggal:** 2026-07-11

**Ringkasan:** `toggle_pause()` fire-and-forget; broadcast paralel ke semua WS client; parallelkan query Discover di action `discover` & `delete_download`.

**File Terdampak:**

- `server/handlers/websocket.py` — asyncio import, parallel broadcast, parallel discover queries, include_lyrics=True initial snapshot

- `engine/playback/controller.py` — safe_create_task mpv_toggle_pause

**Alasan:** Pause instan tanpa jeda; multi-client broadcast simultan; Discover lebih responsif.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 8: DB Index



**ID:** `PATCH-2026-07-11-017`

**Tanggal:** 2026-07-11

**Ringkasan:** Tambah `idx_songs_artist_id` pada tabel `songs` untuk JOIN query di Discover/Radio.

**File Terdampak:**

- `cache/schema.sql` — tambah index idx_songs_artist_id

**Alasan:** Pencegahan full-scan saat data songs bertambah besar.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 7: Event Listeners



**ID:** `PATCH-2026-07-11-016`

**Tanggal:** 2026-07-11

**Ringkasan:** Hapus throttle redundant `_on_track_progress` (sudah ditangani di mpv_controller); parallelkan query Discover di `_on_download_complete`.

**File Terdampak:**

- `server/handlers/event_listeners.py` — hapus throttle, asyncio.gather discover queries

**Alasan:** Kode lebih bersih; discover data refresh lebih efisien.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 6: Track Loader



**ID:** `PATCH-2026-07-11-015`

**Tanggal:** 2026-07-11

**Ringkasan:** `increment_play_count` dijadikan `safe_create_task` (fire-and-forget) agar tidak menunda playback.

**File Terdampak:**

- `engine/playback/track_loader.py` — increment_play_count non-blocking

**Alasan:** Hilangkan 1 DB write round-trip dari jalur kritis ganti lagu.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 5: Lyrics Plugin



**ID:** `PATCH-2026-07-11-014`

**Tanggal:** 2026-07-11

**Ringkasan:** Throttle `LyricsUpdatedEvent` (min 0.5s antar broadcast); lazy import `syncedlyrics`.

**File Terdampak:**

- `plugins/lyrics.py` — throttle LyricsUpdatedEvent, lazy import syncedlyrics

**Alasan:** Kurangi JSON serialize 200+ baris lirik berulang; startup lebih cepat.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 4: mpv Controller



**ID:** `PATCH-2026-07-11-013`

**Tanggal:** 2026-07-11

**Ringkasan:** Throttle publish `TrackProgressEvent` ke 1×/detik; parallelkan 3× `observe_property` saat connect.

**File Terdampak:**

- `engine/mpv_controller.py` — throttle TrackProgressEvent, parallel observe_property

**Alasan:** Kurangi beban event loop dari ~12 Task/detik menjadi ~4 Task/detik; hemat baterai.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 3: main.py Housekeeping



**ID:** `PATCH-2026-07-11-012`

**Tanggal:** 2026-07-11

**Ringkasan:** Parallelkan `db.init()` + `mpv.connect()` via `asyncio.gather`; naikkan interval poller (mpv reconnect 5→30s, connectivity 60→300s); tambah `db_maintenance()` task tiap 6 jam.

**File Terdampak:**

- `main.py` — parallel init, interval poller, db_maintenance task

**Alasan:** Startup lebih cepat; kurangi wake-up loop idle; cegah DB bengkak tanpa batas.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 2: Auth Non-Blocking



**ID:** `PATCH-2026-07-11-011`

**Tanggal:** 2026-07-11

**Ringkasan:** `verify_password()` (PBKDF2 100k iter) dipindah ke `run_in_executor` agar tidak memblokir event loop seluruh client selama proses login.

**File Terdampak:**

- `server/handlers/auth.py` — tambah asyncio import, ganti verify_password ke run_in_executor

**Alasan:** Login blocking ~60-180ms membekukan semua client; sekarang hanya auth yang menunggu.

**Status:** ✅ SELESAI



---



## [2026-07-11] Patch — Batch 1: yt-dlp Client



**ID:** `PATCH-2026-07-11-010`

**Tanggal:** 2026-07-11

**Ringkasan:** Lazy import `yt_dlp` di `_extract_sync` & `_download_sync`; tambah `socket_timeout` dan `extractor_retries` ke `_YDL_OPTS_INFO` untuk mencegah thread zombie saat jaringan buruk.

**File Terdampak:**

- `engine/ytdlp_client.py` — lazy import yt_dlp, socket_timeout=10, extractor_retries=1

**Alasan:** Startup lebih cepat; thread executor tidak habis oleh yt-dlp zombie di jaringan flaky.

**Status:** ✅ SELESAI



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



**Alasan:** `verify_docs.py` 850 baris terlalu besar, duplikasi `CheckResult`/`SKIP_DIRS` di banyak file, logika `replace_marker_block` duplikat di dua generator.

**Status:** ✅ SELESAI — semua script ditest, output/exit code identik dengan sebelum refactor



---



## [2026-07-10] Patch — Pindah .pre-commit-config.yaml ke Root



**ID:** `PATCH-2026-07-10-008`

**Tanggal:** 2026-07-10

**Ringkasan:** `.pre-commit-config.yaml` dipindah dari `scripts/` ke root repo agar pre-commit bisa baca otomatis saat `git commit`.

**File Terdampak:**

- `.pre-commit-config.yaml` — [MOVED] dari `scripts/` ke root

- `docs/PATCHLOG.md` — koreksi entry sebelumnya

- `docs/devops/tooling.md` — update status dari ❌ ke ✅

**Setup:** `pip install pre-commit && pre-commit install`

**Status:** ✅ SELESAI



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

**Kontradiksi yang diselesaikan:**

1. FILE_INDEX.md: warning "manual/stale" bertentangan dengan sistem generated baru

2. REPORT.md: section statistik tidak punya marker → script tidak bisa inject

3. STRUCTURE.md: scripts/ masih describe file lama yang sudah dipindah ke archive/

4. INDEX.md: instruksi "setelah selesai" menyebut run_all.py saja, AI_CONTEXT.md menyebut script satu per satu — tidak konsisten

5. `.pre-commit-config.yaml` dipindah dari `scripts/` ke root repo — sekarang aktif via `pre-commit install`

**Status:** ✅ SELESAI



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

**Alasan:** Aplikasi rusak tanpa internet karena icon hilang. Lagu lokal tidak bisa diputar dengan UX yang baik.

**Status:** ✅ SELESAI



---



## [2026-07-09] Optimasi Storage Unduhan (Single-File)



**ID:** `PATCH-2026-07-09-005`

**Tanggal:** 2026-07-09

**Ringkasan:** Mengubah logika *download* agar memindahkan (*move*) file langsung ke folder `downloads/` tanpa menduplikatnya di `cache/mp3/`.

**File Terdampak:**

- `engine/download_manager.py`

- `server/handlers/websocket.py`



**Alasan:** Menghemat 50% kapasitas penyimpanan saat mengunduh lagu, serta memperbaiki logika `delete_download` agar membersihkan file yang tepat.

**Status:** ✅ SELESAI



---



## [2026-07-09] Bugfix — Radio Cover Image Disappearing



**ID:** `PATCH-2026-07-09-004`

**Tanggal:** 2026-07-09

**Ringkasan:** Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken image karena  class tidak dihapus saat elemen DOM di-_recycle_.

**File Terdampak:**

- `web/static/js/render/queue.js`



**Alasan:** Bugfix untuk memastikan intersection observer memicu ulang lazy-loading gambar.

**Status:** ✅ SELESAI



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



**Alasan:** Tidak ada documentation index sebelumnya (hanya `docs/Index.md` kosong 0 bytes)

**Status:** ✅ SELESAI — dibuat dari scan source code + `PROJECT_STRUCTURE_AUDIT.md`



---



## [2026-07-09] Sprint 3.2 — Extract `start.py` → `launcher/`



**ID:** `PATCH-2026-07-09-002`

**Tanggal:** 2026-07-09

**Ringkasan:** Pecah monolith `start.py` menjadi package `launcher/` dengan separation of concerns.

**File Terdampak:**

- `start.py` (jadi hollow re-export)

- `launcher/` [NEW package — 6 file, lihat "File baru" di bawah]



**Alasan:** Maintainability — UI, process management, network, updater dipisahkan

**Status:** ✅ SELESAI — validasi 8 test case PASS, zero regression



File baru:

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

**File Terdampak:** 33 file total. File signifikan:

- `config.py`

- `main.py`

- `core/observability.py`

- `web/static/js/utils.js`

- `web/static/manifest.json`

- `web/static/sw.js`

- `web/static/index.html`

- `scripts/generate_icons.py` [NEW]



**Alasan:** Rebranding visual & identity

**Status:** ✅ SELESAI — 0 business logic change, semua compat shim terpasang (`YTGUI_*` env vars & localStorage keys masih diterima)



Detail per file:

- `config.py` — env vars primary → `LUNAWAVE_*`, fallback `YTGUI_*`

- `main.py` — log → `lunawave.log`, banner → LunaWave

- `core/observability.py` — metric → `lunawave_events_total`

- `web/static/js/utils.js` — auto-migrate `ytgui_*` → `lunawave_*` localStorage keys

- `web/static/manifest.json`, `sw.js`, `index.html` — PWA identity → LunaWave

- `scripts/generate_icons.py` — [NEW] icon generator PWA



---
