---
title : LunaWave Project Report
last_verified: 2026-07-13
sprint: 3.2
warning: temuan di bawah mungkin sudah berubah, cek kolom STATUS per-item
---

# REPORT.md — LunaWave Analysis Report

> **Tanggal Scan:** 2026-07-13
> **Sumber:** Source code (timpa.rar) + `PROJECT_STRUCTURE_AUDIT.md` + existing docs
> **Sprint aktif saat scan:** Sprint 3.2 (selesai) + Minor UI Patch

---

## Statistik Project

> ⚙️ Blok ini di-generate otomatis oleh `scripts/generate_report.py`. **Jangan edit manual.**
> Jalankan `python scripts/generate_report.py` untuk memperbarui.

<!-- BEGIN:GENERATED -->
> **Auto-generated:** 2026-07-13 oleh `scripts/generate_report.py`
> **Jangan edit blok ini secara manual.**


| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | 57 |
| Total file `.py` (source, ekskl. `__pycache__`) | 96 |
| Total file `.js` (ekskl. `.min.js`) | 34 |
| Total file `.css` (ekskl. `.min.css`) | 21 |
| Total class (Python) | 72 |
| Total function/method (Python) | 374 |
| Total baris Python | 7,354 |
| Total baris JS (web/) | 3,075 |
| Total baris CSS (web/) | 3,277 |
| Ukuran DB utama (`data/lunawave.db`) | 524 KB (+ WAL 161 KB) |
| Ukuran DB library (`cache/library.db`) | 68 KB (+ WAL 0 KB) |

### File Python Terbesar

| File | Baris |
|------|-------|
| `engine/playback/controller.py` | 346 ⚠️ |
| `main.py` | 266 |
| `launcher/gui/ui_builder.py` | 266 |
| `launcher/gui/app.py` | 255 |
| `engine/radio/engine.py` | 195 |
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

### ⚠️ Temuan Masalah (dari `PROJECT_STRUCTURE_AUDIT.md`)

| ID | Severity | Masalah | Lokasi | Status |
|----|----------|---------|--------|--------|
| F-01 | 🔴 Tinggi | `ConnectionManager` tercampur dalam `websocket.py` bersama routing & auth | `server/handlers/websocket.py` (317 baris) | ⏳ Backlog — target Sprint 4 (lihat `STATUS.md`) |
| F-02 | 🟡 Menengah | `mpv_controller.py` & `ytdlp_client.py` sebaiknya di `adapters/`, bukan `engine/` | `engine/` | ⏳ Backlog — target Sprint 4 |
| F-03 | 🟡 Menengah | `cache/db.py` God Class — 5 domain query dalam 1 class (389 baris) | `cache/db.py` | ⏳ Backlog — target Sprint 4 |
| F-04 | 🟡 Menengah | `cache/` campur: runtime code + DB files + credentials + misplaced util | `cache/` | 🔄 Sebagian — F-09 (misplaced util) sudah beres, F-10 (credentials) sedang dicek, split ke `persistence/` masih Sprint 5 |
| F-05 | 🟡 Menengah | `data/artists_enriched.json` 185 KB sebaiknya di-import ke DB | `data/` | ⏳ Backlog — target Sprint 5 |
| F-06 | 🟡 Menengah | `config.py` mengimport `core/security` (leaf module tidak seharusnya punya dep internal) | `config.py:L47,L64` | ⏳ Backlog — target Sprint 4 |
| F-07 | 🟡 Menengah | `web/static/index.html` SPA monolitik 36 KB | `web/static/index.html` | ✅ Ditutup — keputusan final: **tidak dipecah** (lihat `AI_CONTEXT.md` & `STATUS.md`). ⚠️ Temuan ini kontradiktif dengan keputusan tsb; dibiarkan di sini sebagai riwayat analisis, jangan dieksekusi ulang. |
| F-08 | 🟢 Rendah | `data/export_to_sqlite.py` seharusnya di `scripts/` | `data/` | ⏳ Backlog — target Sprint 4 |
| F-09 | 🟢 Rendah | `cache/inject_svgs.py` tersesat — sudah ada di `scripts/inject_svgs.py` | `cache/` (tidak ditemukan di RAR → sudah pindah ✅) | ✅ Resolved |
| F-10 | 🔴 Penting | `cache/admin_password.txt` harus dipastikan ada di `.gitignore` | `cache/admin_password.txt` | 🔄 In-progress — cek `.gitignore` (lihat `STATUS.md`, prioritas ASAP) |

---

## Rekomendasi (Prioritas)

### 🔴 Segera
1. **Pisah `ConnectionManager`** dari `server/handlers/websocket.py` → `server/connection_manager.py` untuk mencegah potensi circular dependency dan meningkatkan testability.
2. **Pastikan `cache/admin_password.txt` ada di `.gitignore`** — file ini berisi hash password admin.

### 🟡 Sprint Berikutnya
3. **Buat `adapters/`** — pindah `engine/mpv_controller.py` dan `engine/ytdlp_client.py` agar `engine/` menjadi pure domain logic.
4. **Pecah `cache/db.py`** menjadi repositories per concern: `TrackRepository`, `SessionRepository`, `ArtistRepository`, `GenreRepository`.
5. **Pisah `cache/`** menjadi `persistence/` (db.py, schema.sql) + `cache/` slim (resolver.py, mp3/).
6. **Migrasi `data/artists_enriched.json`** ke tabel DB `artists` — 185 KB JSON statis tidak efisien.

### 🟢 Backlog
7. **Pindah `data/export_to_sqlite.py`** → `scripts/`.
8. **Extract `<template>` komponen** dari `web/static/index.html` 36 KB.
9. **Pertimbangkan build tooling** (Vite/esbuild) untuk frontend JS/CSS.
10. **Implementasi `launcher/updater.py`** yang masih stub.

---

## Dependency Risk

| Hubungan | Status |
|----------|--------|
| `server/services/broadcast_service` → `server/handlers/websocket` (ConnectionManager) | ⚠️ Fragile — potensi circular jika websocket.py butuh broadcast_service |
| `config.py` → `core/security` | ⚠️ Leaf module dengan internal dependency |
| `engine/playback/controller` → `engine/radio_engine` (TYPE_CHECKING guard) | ✅ Aman |
| Semua lainnya | ✅ One-directional |
