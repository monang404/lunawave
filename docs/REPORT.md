---
title : LunaWave Project Report
last_verified: 2026-07-21
sprint: 3.3
warning: temuan di bawah mungkin sudah berubah, cek kolom STATUS per-item
---

# REPORT.md — LunaWave Analysis Report

> **Tanggal Scan:** 2026-07-21
> **Sumber:** Source code (timpa.rar) + `PROJECT_STRUCTURE_AUDIT.md` + existing docs
> **Sprint aktif saat scan:** Sprint 3.2 (selesai) + Minor UI Patch

---

## Statistik Project

> ⚙️ Blok ini di-generate otomatis oleh `automation/generate_report.py`. **Jangan edit manual.**
> Jalankan `python automation/generate_report.py` untuk memperbarui.

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-21 oleh `automation/generate_report.py`  
> **Jangan edit blok ini secara manual.**


| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | 60 |
| Total file `.py` (source, ekskl. `__pycache__`) | 113 |
| Total file `.js` (ekskl. `.min.js`) | 39 |
| Total file `.css` (ekskl. `.min.css`) | 24 |
| Total class (Python) | 94 |
| Total function/method (Python) | 512 |
| Total baris Python | 12,077 |
| Total baris JS (web/) | 4,828 |
| Total baris CSS (web/) | 4,168 |
| Ukuran DB utama (`data/lunawave.db`) | tidak ditemukan |
| Ukuran DB library (`cache/library.db`) | tidak ditemukan |

### File Python Terbesar

| File | Baris |
|------|-------|
| `engine/playback/controller.py` | 429 |
| `persistence/discover_repo.py` | 419 |
| `launcher/gui/ui_builder.py` | 350 |
| `launcher/gui/app.py` | 292 |
| `bootstrap/services.py` | 247 |
<!-- END:GENERATED -->

---

## Entry Point

| Jalur | Keterangan |
|-------|------------|
| `main.py` | Backend utama — `asyncio.run(main())` |
| `start.py` → `launcher/__main__` | GUI launcher Tkinter (fallback headless ke `main.py`) |
| `start.sh` / `start.bat` | Shell launcher Linux/Termux & Windows |

---
