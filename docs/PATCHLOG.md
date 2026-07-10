---
title: LunaWave Patch Log
last_verified: 2026-07-10
latest_patch_id: PATCH-2026-07-10-008
total_entries: 6
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
