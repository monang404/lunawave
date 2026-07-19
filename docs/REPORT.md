---
title : LunaWave Project Report
last_verified: 2026-07-19
sprint: 3.3
warning: temuan di bawah mungkin sudah berubah, cek kolom STATUS per-item
---

# REPORT.md — LunaWave Analysis Report

> **Tanggal Scan:** 2026-07-19
> **Sumber:** Source code (timpa.rar) + `PROJECT_STRUCTURE_AUDIT.md` + existing docs
> **Sprint aktif saat scan:** Sprint 3.2 (selesai) + Minor UI Patch

---

## Statistik Project

> ⚙️ Blok ini di-generate otomatis oleh `automation/generate_report.py`. **Jangan edit manual.**
> Jalankan `python automation/generate_report.py` untuk memperbarui.

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-19 oleh `automation/generate_report.py`  
> **Jangan edit blok ini secara manual.**


| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | 55 |
| Total file `.py` (source, ekskl. `__pycache__`) | 111 |
| Total file `.js` (ekskl. `.min.js`) | 38 |
| Total file `.css` (ekskl. `.min.css`) | 23 |
| Total class (Python) | 90 |
| Total function/method (Python) | 495 |
| Total baris Python | 11,534 |
| Total baris JS (web/) | 4,506 |
| Total baris CSS (web/) | 4,039 |
| Ukuran DB utama (`data/lunawave.db`) | 92 KB (+ WAL 24 KB) |
| Ukuran DB library (`cache/library.db`) | tidak ditemukan |

### File Python Terbesar

| File | Baris |
|------|-------|
| `engine/playback/controller.py` | 433 |
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

## Modul Utama

| Layer | Modul Kunci |
|-------|-------------|
| Foundation | `core/state`, `core/event_bus`, `core/command_bus`, `core/events`, `core/ports` |
| Audio Engine | `engine/mpv_controller`, `engine/ytdlp_client`, `engine/playback/controller` |
| Radio/Queue | `engine/radio_engine`, `engine/queue_manager`, `engine/volume_service` |
| Persistence | `cache/db`, `cache/resolver` |
| Web Server | `server/app`, `server/handlers/websocket`, `server/handlers/http` |
| Discovery | `services/discover_service` |
| Plugins | `plugins/lyrics`, `plugins/notifications`, `plugins/sponsorblock` |
| Launcher | `launcher/gui`, `launcher/process` |

---

## Temuan Penting

### ✅ Arsitektur Baik
1. **Hexagonal Architecture terlaksana** — `core/ports.py` mendefinisikan Protocol interfaces; engine/cache/server depend on abstraction.
2. **EventBus + CommandBus** — decoupling pub/sub dan single-writer command pattern sudah berjalan dengan benar.
3. **Plugin system bersih** — `plugins/` hanya berkomunikasi via bus, zero coupling ke engine.
4. **CSS ITCSS** — `tokens.css` + `base/`, `components/`, `layout/`, `platform/` sudah terstruktur.
5. **Sprint 3.2 selesai** — `start.py` → `launcher/` refactor berhasil, validated 8 test case.
6. **Rebranding Sprint 2.1** — YTGUI → LunaWave tuntas, backward-compat shims terpasang.
7. **`data/ytgui.db`** — tidak ditemukan di source (kemungkinan sudah dihapus ✅).



## Dependency Risk

| Hubungan | Status |
|----------|--------|
| `server/services/broadcast_service` → `server/handlers/websocket` (ConnectionManager) | ⚠️ Fragile — potensi circular jika websocket.py butuh broadcast_service |
| `config.py` → `core/security` | ⚠️ Leaf module dengan internal dependency |
| `engine/playback/controller` → `engine/radio_engine` (TYPE_CHECKING guard) | ✅ Aman |
| Semua lainnya | ✅ One-directional |
