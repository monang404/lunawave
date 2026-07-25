---
title : LunaWave Project Report
last_verified: 2026-07-24
sprint: 3.3
warning: temuan di bawah mungkin sudah berubah, cek kolom STATUS per-item
---

# REPORT.md — LunaWave Analysis Report

> **Tanggal Scan:** 2026-07-24
> **Sumber:** Source code (timpa.rar) + `PROJECT_STRUCTURE_AUDIT.md` + existing docs
> **Sprint aktif saat scan:** Sprint 3.2 (selesai) + Minor UI Patch

---

## Statistik Project

> ⚙️ Blok ini di-generate otomatis oleh `automation/generate_report.py`. **Jangan edit manual.**
> Jalankan `python automation/generate_report.py` untuk memperbarui.

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-24 oleh `automation/generate_report.py`  
> **Jangan edit blok ini secara manual.**


| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | 67 |
| Total file `.py` (source, ekskl. `__pycache__`) | 124 |
| Total file `.js` (ekskl. `.min.js`) | 46 |
| Total file `.css` (ekskl. `.min.css`) | 25 |
| Total class (Python) | 98 |
| Total function/method (Python) | 580 |
| Total baris Python | 14,986 |
| Total baris JS (web/) | 6,466 |
| Total baris CSS (web/) | 4,506 |
| Ukuran DB utama (`data/lunawave.db`) | tidak ditemukan |
| Ukuran DB library (`cache/library.db`) | tidak ditemukan |

### File Python Terbesar

| File | Baris |
|------|-------|
| `engine/playback/controller.py` | 468 |
| `persistence/discover_repo.py` | 446 |
| `launcher/gui/ui_builder.py` | 353 |
| `launcher/gui/app.py` | 297 |
| `engine/radio/engine.py` | 288 |
<!-- END:GENERATED -->

---

## Entry Point

| Jalur | Keterangan |
|-------|------------|
| `main.py` | Backend utama — `asyncio.run(main())` |
| `start.py` → `launcher/__main__` | GUI launcher Tkinter (fallback headless ke `main.py`) |
| `start.sh` / `start.bat` | Shell launcher Linux/Termux & Windows |

---
