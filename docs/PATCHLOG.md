---
title: LunaWave Patch Log
last_verified: 2026-07-11
latest_patch_id: PATCH-2026-07-11-009
total_entries: 7
---

# PATCHLOG.md — LunaWave

> **Format:** Append-only. Jangan hapus entri sebelumnya.
> **Detail lengkap per sprint:**
> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).
> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".

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

## [2026-07-09] Bugfix — Radio Cover Image Disappearing

**ID:** `PATCH-2026-07-09-004`
**Tanggal:** 2026-07-09
**Ringkasan:** Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken image karena  class tidak dihapus saat elemen DOM di-_recycle_.
**File Terdampak:**
- `web/static/js/render/queue.js`

**Alasan:** Bugfix untuk memastikan intersection observer memicu ulang lazy-loading gambar.
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

## [2026-07-10] Patch — Pindah .pre-commit-config.yaml ke Root

**ID:** `PATCH-2026-07-10-008`
**Tanggal:** 2026-07-10
**Ringkasan:** `.pre-commit-config.yaml` dipindah dari `scripts/` ke root repo agar pre-commit bisa baca otomatis saat `git commit`.
**File Terdampak:**
- `.pre-commit-config.yaml` — [MOVED] dari `scripts/` ke root
- `docs/PATCHLOG.md` — koreksi entry sebelumnya
- `docs/kompas/devops/tooling.md` — update status dari ❌ ke ✅
**Setup:** `pip install pre-commit && pre-commit install`
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
- `docs/kompas/architecture/folder_structure.md` — update tree `scripts/`
- `AI_CONTEXT.md` — tambah seksi "Struktur internal scripts/"
- `docs/AI_CONTEXT.md` — idem
- `docs/FILE_INDEX.md` — regenerate (file baru masuk index)
- `docs/REPORT.md` — regenerate (statistik file .py bertambah)

**Alasan:** `verify_docs.py` 850 baris terlalu besar, duplikasi `CheckResult`/`SKIP_DIRS` di banyak file, logika `replace_marker_block` duplikat di dua generator.
**Status:** ✅ SELESAI — semua script ditest, output/exit code identik dengan sebelum refactor

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

## [2026-07-11] Patch — Batch 2: Auth Non-Blocking

**ID:** `PATCH-2026-07-11-011`
**Tanggal:** 2026-07-11
**Ringkasan:** `verify_password()` (PBKDF2 100k iter) dipindah ke `run_in_executor` agar tidak memblokir event loop seluruh client selama proses login.
**File Terdampak:**
- `server/handlers/auth.py` — tambah asyncio import, ganti verify_password ke run_in_executor
**Alasan:** Login blocking ~60-180ms membekukan semua client; sekarang hanya auth yang menunggu.
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

## [2026-07-11] Patch — Batch 4: mpv Controller

**ID:** `PATCH-2026-07-11-013`
**Tanggal:** 2026-07-11
**Ringkasan:** Throttle publish `TrackProgressEvent` ke 1×/detik; parallelkan 3× `observe_property` saat connect.
**File Terdampak:**
- `engine/mpv_controller.py` — throttle TrackProgressEvent, parallel observe_property
**Alasan:** Kurangi beban event loop dari ~12 Task/detik menjadi ~4 Task/detik; hemat baterai.
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

## [2026-07-11] Patch — Batch 6: Track Loader

**ID:** `PATCH-2026-07-11-015`
**Tanggal:** 2026-07-11
**Ringkasan:** `increment_play_count` dijadikan `safe_create_task` (fire-and-forget) agar tidak menunda playback.
**File Terdampak:**
- `engine/playback/track_loader.py` — increment_play_count non-blocking
**Alasan:** Hilangkan 1 DB write round-trip dari jalur kritis ganti lagu.
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

## [2026-07-11] Patch — Batch 8: DB Index

**ID:** `PATCH-2026-07-11-017`
**Tanggal:** 2026-07-11
**Ringkasan:** Tambah `idx_songs_artist_id` pada tabel `songs` untuk JOIN query di Discover/Radio.
**File Terdampak:**
- `cache/schema.sql` — tambah index idx_songs_artist_id
**Alasan:** Pencegahan full-scan saat data songs bertambah besar.
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

## [2026-07-11] Patch — Batch 12: Startup Script Cleanup

**ID:** `PATCH-2026-07-11-021`
**Tanggal:** 2026-07-11
**Ringkasan:** Gabung 7× subprocess dep-check Python menjadi 1×; hapus `sleep`/`ping` artifisial di `start.sh` dan `start.bat`.
**File Terdampak:**
- `start.sh` — single-import dep check, hapus sleep 0.5 dan sleep 1
- `start.bat` — single-import dep check, hapus ping delays
**Alasan:** Kurangi overhead startup script secara signifikan.
**Status:** ✅ SELESAI
