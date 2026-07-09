# PATCHLOG.md — LunaWave

> **Format:** Append-only. Jangan hapus entri sebelumnya.
> **Detail lengkap per sprint:** lihat `docs/LOG/`

---

## [2026-07-09] Sprint 2.1 — LunaWave Rebranding

**Tanggal:** 2026-07-09
**Ringkasan:** Replace semua identitas legacy (YTGUI, ytgui, bagas.fm, YT Termux Player) dengan LunaWave. Zero regresi pada business logic.
**File berubah:** 33 file (detail di `docs/LOG/PATCHLOG_REBRANDING.md`)
**Alasan:** Rebranding visual & identity
**Status:** ✅ SELESAI — 0 business logic change, semua compat shim terpasang (`YTGUI_*` env vars & localStorage keys masih diterima)

Patch highlights:
- `config.py` — env vars primary → `LUNAWAVE_*`, fallback `YTGUI_*`
- `main.py` — log → `lunawave.log`, banner → LunaWave
- `core/observability.py` — metric → `lunawave_events_total`
- `web/static/js/utils.js` — auto-migrate `ytgui_*` → `lunawave_*` localStorage keys
- `web/static/manifest.json`, `sw.js`, `index.html` — PWA identity → LunaWave
- `scripts/generate_icons.py` — [NEW] icon generator PWA

---

## [2026-07-09] Sprint 3.2 — Extract `start.py` → `launcher/`

**Tanggal:** 2026-07-09
**Ringkasan:** Pecah monolith `start.py` menjadi package `launcher/` dengan separation of concerns.
**File berubah:** `start.py` (hollow), `launcher/` [NEW package — 6 files]
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

**Tanggal:** 2026-07-09
**Ringkasan:** Pembuatan awal dokumentasi knowledge base dari source code scan.
**File berubah:** `docs/INDEX.md` [NEW], `docs/STRUCTURE.md` [NEW], `docs/FILE_INDEX.md` [NEW], `docs/PATCHLOG.md` [NEW], `docs/REPORT.md` [NEW]
**Alasan:** Tidak ada documentation index sebelumnya (hanya `docs/Index.md` kosong 0 bytes)
**Status:** ✅ SELESAI — dibuat dari scan source code + `PROJECT_STRUCTURE_AUDIT.md`

---

## [2026-07-09] Bugfix — Radio Cover Image Disappearing

**Tanggal:** 2026-07-09
**Ringkasan:** Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken image karena `.observed` class tidak dihapus saat elemen DOM di-_recycle_.
**File berubah:** `web/static/js/render/queue.js`
**Alasan:** Bugfix untuk memastikan intersection observer memicu ulang lazy-loading gambar.
**Status:** ✅ SELESAI

---

## [2026-07-09] Optimasi Storage Unduhan (Single-File)

**Tanggal:** 2026-07-09
**Ringkasan:** Mengubah logika *download* agar memindahkan (*move*) file langsung ke folder `downloads/` tanpa menduplikatnya di `cache/mp3/`.
**File berubah:** `engine/download_manager.py`, `server/handlers/websocket.py`
**Alasan:** Menghemat 50% kapasitas penyimpanan saat mengunduh lagu, serta memperbaiki logika `delete_download` agar membersihkan file yang tepat.
**Status:** ✅ SELESAI
---

## [2026-07-09] Patch � Offline CDN Fix

**Tanggal:** 2026-07-09
**Ringkasan:** Self-host Tabler Icons & hapus Google Fonts CDN. UI kini berfungsi penuh tanpa internet.
**File berubah:**
- `web/static/index.html` � hapus 4 baris Google Fonts, ganti 1 baris Tabler CDN ? lokal
- `web/static/css/tokens.css` � pastikan font fallback stack
- `web/static/css/vendor/tabler-icons.min.css` � [NEW] self-hosted
- `web/static/css/vendor/fonts/*` � [NEW] font files
- `web/static/sw.js` � bump CACHE_VERSION, tambah vendor ke PRECACHE_ASSETS
**Alasan:** Aplikasi rusak tanpa internet karena icon hilang. Lagu lokal tidak bisa diputar dengan UX yang baik.
**Status:** ? SELESAI
