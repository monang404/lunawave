# REPORT.md — LunaWave Analysis Report

> **Tanggal Scan:** 2026-07-09
> **Sumber:** Source code (timpa.rar) + `PROJECT_STRUCTURE_AUDIT.md` + existing docs
> **Sprint aktif saat scan:** Sprint 3.2 (selesai) + Minor UI Patch

---

## Statistik Project

| Metrik | Nilai |
|--------|-------|
| Total folder (ekskl. `__pycache__`, `.git`) | ~35 |
| Total file `.py` (source, ekskl. `__pycache__`) | 54 |
| Total file `.js` | 21 |
| Total file `.css` | 21 |
| Total class (Python) | 49 |
| Total function/method (Python) | 255 |
| Ukuran DB utama (`data/lunawave.db`) | 180 KB (+ WAL 160 KB) |
| Ukuran DB library (`cache/library.db`) | 69 KB |

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

| ID | Severity | Masalah | Lokasi |
|----|----------|---------|--------|
| F-01 | 🔴 Tinggi | `ConnectionManager` tercampur dalam `websocket.py` bersama routing & auth | `server/handlers/websocket.py` (317 baris) |
| F-02 | 🟡 Menengah | `mpv_controller.py` & `ytdlp_client.py` sebaiknya di `adapters/`, bukan `engine/` | `engine/` |
| F-03 | 🟡 Menengah | `cache/db.py` God Class — 5 domain query dalam 1 class (389 baris) | `cache/db.py` |
| F-04 | 🟡 Menengah | `cache/` campur: runtime code + DB files + credentials + misplaced util | `cache/` |
| F-05 | 🟡 Menengah | `data/artists_enriched.json` 185 KB sebaiknya di-import ke DB | `data/` |
| F-06 | 🟡 Menengah | `config.py` mengimport `core/security` (leaf module tidak seharusnya punya dep internal) | `config.py:L47,L64` |
| F-07 | 🟡 Menengah | `web/static/index.html` SPA monolitik 36 KB | `web/static/index.html` |
| F-08 | 🟢 Rendah | `data/export_to_sqlite.py` seharusnya di `scripts/` | `data/` |
| F-09 | 🟢 Rendah | `cache/inject_svgs.py` tersesat — sudah ada di `scripts/inject_svgs.py` | `cache/` (tidak ditemukan di RAR → sudah pindah ✅) |
| F-10 | 🔴 Penting | `cache/admin_password.txt` harus dipastikan ada di `.gitignore` | `cache/admin_password.txt` |

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
