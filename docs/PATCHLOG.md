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
