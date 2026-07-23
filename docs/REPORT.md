---
title : LunaWave Project Report
last_verified: 2026-07-23
sprint: 3.3
warning: temuan di bawah mungkin sudah berubah, cek kolom STATUS per-item
---

# REPORT.md — LunaWave Analysis Report

> **Tanggal Scan:** 2026-07-23
> **Sumber:** Source code (timpa.rar) + `PROJECT_STRUCTURE_AUDIT.md` + existing docs
> **Sprint aktif saat scan:** Sprint 3.2 (selesai) + Minor UI Patch

---

## Statistik Project

> ⚙️ Blok ini di-generate otomatis oleh `automation/generate_report.py`. **Jangan edit manual.**
> Jalankan `python automation/generate_report.py` untuk memperbarui.

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-23 oleh `automation/generate_report.py`
> **Jangan edit blok ini secara manual.**


| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | 62 |
| Total file `.py` (source, ekskl. `__pycache__`) | 118 |
| Total file `.js` (ekskl. `.min.js`) | 41 |
| Total file `.css` (ekskl. `.min.css`) | 24 |
| Total class (Python) | 98 |
| Total function/method (Python) | 552 |
| Total baris Python | 13,847 |
| Total baris JS (web/) | 5,134 |
| Total baris CSS (web/) | 4,162 |
| Ukuran DB utama (`data/lunawave.db`) | tidak ditemukan |
| Ukuran DB library (`cache/library.db`) | tidak ditemukan |

### File Python Terbesar

| File | Baris |
|------|-------|
| `engine/playback/controller.py` | 461 |
| `persistence/discover_repo.py` | 446 |
| `launcher/gui/ui_builder.py` | 350 |
| `engine/radio/engine.py` | 292 |
| `launcher/gui/app.py` | 290 |
<!-- END:GENERATED -->

---

## Entry Point

| Jalur | Keterangan |
|-------|------------|
| `main.py` | Backend utama — `asyncio.run(main())` |
| `start.py` → `launcher/__main__` | GUI launcher Tkinter (fallback headless ke `main.py`) |
| `start.sh` / `start.bat` | Shell launcher Linux/Termux & Windows |

---
