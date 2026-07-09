# PROJECT STRUCTURE AUDIT — LunaWave
> **Tujuan:** Roadmap refactoring berbasis analisis struktur aktual.
> **Tanggal Audit:** 2026-07-09 (Diperbarui setelah Sprint 3.2)
> **Aturan:** Dokumen ini berisi observasi dan panduan refactoring.

---

## 1. Struktur Folder Saat Ini

```
lunawave/                          ← Root proyek
│
├── main.py                        ← Entry point utama (asyncio runner)
├── config.py                      ← Konfigurasi global & env vars
├── start.py                       ← Bootstrap launcher (memanggil launcher/)
├── launcher/                      ← Modul internal GUI launcher
│   ├── __main__.py                ← Coordinator startup
│   ├── __init__.py
│   ├── gui.py                     ← Tkinter UI
│   ├── process.py                 ← Manajemen subprocess & log
│   ├── network.py                 ← Deteksi port & konektivitas
│   └── updater.py                 ← Cek versi & update (stub)
├── start.bat / start.sh           ← Shell launcher (Windows & Linux/Termux)
├── requirements.txt               ← Python dependencies
├── lunawave.log                   ← Log file runtime
│
├── core/                          ← Lapisan fondasi — shared primitives
│   ├── __init__.py
│   ├── state.py                   ← AppState, TrackInfo, enums
│   ├── event_bus.py               ← Pub/sub EventBus
│   ├── command_bus.py             ← Single-writer CommandBus + CMD constants
│   ├── events.py                  ← DomainEvent dataclasses
│   ├── ports.py                   ← Protocol interfaces (ports/adapters)
│   ├── exceptions.py              ← Custom exceptions
│   ├── log_config.py              ← Logging setup (structlog)
│   ├── observability.py           ← Prometheus metrics & OpenTelemetry tracer
│   ├── security.py                ← Password hashing
│   ├── task_utils.py              ← safe_create_task() helper
│   └── __pycache__/
│
├── engine/                        ← Domain logic — audio & playback
│   ├── __init__.py
│   ├── mpv_controller.py          ← IPC ke MPV via socket/named pipe (307 baris)
│   ├── ytdlp_client.py            ← Wrapper yt-dlp (171 baris)
│   ├── radio_engine.py            ← Radio Mode — autonomous playback (365 baris)
│   ├── command_router.py          ← CommandBus → PlaybackController dispatcher
│   ├── download_manager.py        ← Manajemen download MP3
│   ├── queue_manager.py           ← Queue Mode state (sangat kecil, 1006 bytes)
│   ├── volume_service.py          ← Volume control service
│   └── playback/
│       ├── __init__.py
│       ├── controller.py          ← PlaybackController utama (351 baris)
│       └── track_loader.py        ← Track loading & plugin injection (kecil)
│
├── server/                        ← HTTP & WebSocket layer
│   ├── __init__.py
│   ├── app.py                     ← aiohttp app factory & runner
│   ├── middleware.py              ← Rate limiting
│   ├── serializers.py             ← State → JSON & JSON → Track
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── auth.py                ← Session auth handlers
│   │   ├── event_listeners.py     ← EventBus → broadcast bridge
│   │   ├── http.py                ← REST routes (stream, health, metrics)
│   │   └── websocket.py           ← WS handler & ConnectionManager (317 baris)
│   └── services/
│       ├── broadcast_service.py   ← Push events ke semua WS clients
│       └── stream_prefetch.py     ← Pre-fetch stream URL untuk lagu berikutnya
│
├── cache/                         ← Persistence & resolusi stream URL
│   ├── __init__.py
│   ├── db.py                      ← SQLite database via aiosqlite (389 baris)
│   ├── resolver.py                ← Strategi resolve: local → cache → yt-dlp
│   ├── schema.sql                 ← DDL schema database
│   ├── inject_svgs.py             ← Utilitas inject SVG (tersesat di sini?)
│   ├── admin_password.txt         ← ⚠️ Kredensial tersimpan di sini
│   ├── library.db                 ← SQLite library (69 KB)
│   ├── library.db-shm/wal         ← SQLite WAL files
│   └── mp3/                       ← MP3 download cache (runtime-generated)
│
├── data/                          ← Data semi-permanen proyek
│   ├── lunawave.db                ← SQLite DB utama (135 KB)
│   ├── lunawave.db-shm/wal        ← SQLite WAL files
│   ├── artists_enriched.json      ← ⚠️ 185 KB — data artis enrichment
│   ├── ytgui.db                   ← ⚠️ DB warisan (212 KB) — masih ada?
│   └── export_to_sqlite.py        ← Script migrasi data
│
├── services/                      ← High-level application services
│   └── discover_service.py        ← Recent & Favorites query ke DB
│
├── plugins/                       ← Fitur opsional/platform-specific
│   ├── __init__.py
│   ├── lyrics.py                  ← LyricsFetcher via lrclib.net (179 baris)
│   ├── notifications.py           ← Termux MediaStyle notifications (171 baris)
│   └── sponsorblock.py            ← SponsorBlock segment skipping (3 KB)
│
├── web/                           ← Frontend aset
│   ├── asset/
│   │   └── logos/
│   └── static/
│       ├── index.html             ← ⚠️ SPA HTML monolitik (36 KB!)
│       ├── manifest.json          ← PWA manifest
│       ├── sw.js                  ← Service Worker
│       ├── css/
│       │   ├── tokens.css         ← Design tokens (variabel CSS)
│       │   ├── portal.css         ← Styles khusus admin portal
│       │   ├── base/              ← reset, animations, typography
│       │   ├── components/        ← cards, player-bar, queue, dll (8 file)
│       │   ├── layout/            ← app-shell, grid, nav
│       │   └── platform/          ← desktop, tablet, mobile, landscape
│       └── js/
│           ├── main.js            ← Bootstrap & inisialisasi
│           ├── audio.js           ← Browser Audio Engine (13 KB)
│           ├── ws.js              ← WebSocket client (9 KB)
│           ├── utils.js           ← Utility functions (7 KB)
│           ├── dom.js             ← DOM helpers
│           ├── store.js           ← State store sederhana
│           ├── config.js          ← Config (sangat kecil, 55 bytes)
│           ├── portal.js          ← Admin portal entry
│           ├── events/            ← Event handlers (player, queue, lyrics, dll)
│           ├── render/            ← View renderers (discover, queue, search, dll)
│           ├── platform/          ← Keyboard, touch, viewport handlers
│           └── services/          ← auth.js (hanya 1 file)
│
├── docs/                          ← Dokumentasi
├── scripts/                       ← Utility scripts
│   ├── generate_icons.py
│   └── shortcuts/
├── scratch/                       ← Scratch files (runtime/dev)
├── .github/                       ← CI/CD workflows
└── .git/
```

---

## 2. Folder yang Terlalu Besar

| Folder | Masalah |
|--------|---------|
| `web/static/` | Berisi 30+ file JS/CSS tersebar di 7 subdirektori tanpa build system. Semua dimuat manual via `index.html`. Tidak ada bundling/minification. |
| `data/` | Mix antara DB aktif, DB warisan (`ytgui.db`), data JSON besar (`artists_enriched.json`), dan script migrasi — semua campur dalam satu folder. |
| `cache/` | Campur antara runtime code (`db.py`, `resolver.py`, `schema.sql`), file persisten (`library.db`), kredensial (`admin_password.txt`), dan utilitas tersesat (`inject_svgs.py`). |
| `engine/` | Satu folder menampung hal yang berbeda: controller, client, service, dan mode engine. Bisa lebih terstruktur. |

---

## 3. File yang Terlalu Besar

| File | Ukuran | Masalah |
|------|--------|---------|
| `web/static/index.html` | ~36 KB | SPA HTML monolitik. Semua komponen (player, queue, settings, modal, dll.) dalam 1 file HTML tanpa templating. |
| `engine/radio_engine.py` | 365 baris / 16 KB | Algoritma radio yang kompleks — bisa dipecah ke sub-modul (search strategy, queue builder, deduplication). |
| `engine/playback/controller.py` | 351 baris / 16 KB | PlaybackController yang menggabungkan track loading, event handling, mode switching, dan error recovery. |
| `cache/db.py` | 389 baris / 15 KB | Satu class `Database` menangani semua query: tracks, sessions, play_count, stream_url — belum dipecah per concern. |
| `server/handlers/websocket.py` | 317 baris / 12 KB | `ConnectionManager` + WS routing + auth check + rate limiting + command dispatch semuanya dalam satu file. |
| `engine/mpv_controller.py` | 307 baris / 12 KB | MPV IPC + reconnection + volume + events dalam satu class. |
| `data/artists_enriched.json` | 185 KB | File JSON besar yang mestinya di database, bukan di-commit ke repo sebagai file statis. |
| `data/ytgui.db` | 212 KB | Database warisan yang tampaknya tidak digunakan lagi (nama dari proyek sebelum rebranding). |

---

## 4. Dependency Antar Modul

Berikut adalah peta ketergantungan antar modul (panah = "mengimport"):

```
config.py
  ↑
  ├── core/state.py
  ├── core/security.py
  │
  └── [semua modul mengimport config secara langsung]

core/  (lapisan fondasi — tidak boleh import selain dari dirinya sendiri)
  ├── state.py         ← diimport oleh: engine, cache, plugins, server
  ├── event_bus.py     ← diimport oleh: engine, server, plugins
  ├── command_bus.py   ← diimport oleh: engine, server, plugins
  ├── events.py        ← diimport oleh: engine, server, plugins
  ├── ports.py         ← diimport oleh: engine, cache, server
  ├── observability.py ← diimport oleh: core/event_bus, core/command_bus, server/handlers
  ├── task_utils.py    ← diimport oleh: engine, server
  └── security.py      ← diimport oleh: config, server/handlers/auth

cache/
  ├── db.py            → core/state, config
  └── resolver.py      → cache/db, config, core/state, core/ports

engine/
  ├── ytdlp_client.py         → core/state, config
  ├── mpv_controller.py       → config, core/event_bus, core/events, core/state, core/task_utils, core/exceptions
  ├── radio_engine.py         → core/events, core/state, core/ports, core/task_utils
  ├── download_manager.py     → core/*, config
  ├── volume_service.py       → core/*
  ├── command_router.py       → core/command_bus
  ├── queue_manager.py        → (minimal)
  └── playback/
      ├── controller.py       → core/*, cache/resolver, engine/queue_manager, engine/radio_engine
      └── track_loader.py     → cache/resolver, core/ports

services/
  └── discover_service.py     → cache/db, core/state

plugins/
  ├── lyrics.py               → config, core/event_bus, core/events, core/state
  ├── notifications.py        → core/event_bus, core/events, core/command_bus, core/state
  └── sponsorblock.py         → core/*

server/
  ├── app.py                  → core/events, core/task_utils, server/serializers, server/handlers/*, config, core/ports, engine/playback/controller
  ├── serializers.py          → core/state
  ├── middleware.py           → (minimal)
  ├── handlers/
  │   ├── auth.py             → core/security
  │   ├── event_listeners.py  → core/events, core/task_utils, server/services/*
  │   ├── http.py             → config, core/observability
  │   └── websocket.py        → core/observability, core/command_bus, core/state, server/serializers, server/middleware, server/handlers/auth, services/discover_service
  └── services/
      ├── broadcast_service.py → server/handlers/websocket (ConnectionManager)
      └── stream_prefetch.py   → cache/db, config, core/ports, engine/ytdlp_client

main.py  → semua modul di atas
```

---

## 5. Circular Dependency

### ⚠️ Risiko Circular — Terdeteksi

| Hubungan | Status | Penjelasan |
|----------|--------|------------|
| `server/services/broadcast_service.py` → `server/handlers/websocket.py` (ConnectionManager) | **⚠️ Berisiko** | `broadcast_service` mengimport `ConnectionManager` dari `websocket.py`, sementara `websocket.py` bisa saja membutuhkan `broadcast_service` di masa depan. Saat ini belum circular, tapi desainnya fragile. |
| `engine/playback/controller.py` → `engine/radio_engine.py` | **✅ Aman saat ini** | `controller.py` mengimport `RadioMode` secara langsung (bukan via TYPE_CHECKING). `radio_engine.py` menggunakan `TYPE_CHECKING` untuk import `PlaybackController`, sehingga circular runtime dihindari. |
| `config.py` → `core/security.py` | **⚠️ Berisiko** | `config.py` mengimport `core/security.hash_password` saat runtime (saat generate password). Ini membuat `config.py` tergantung pada `core/`, padahal seharusnya `config.py` adalah leaf module yang tidak punya dependency internal. |
| `services/discover_service.py` → `cache/db.py` | **✅ Aman** | Satu arah, tidak ada balik. |
| `server/app.py` → `engine/playback/controller.py` | **✅ Aman** | Dependency injection melalui parameter, tidak hardcoded. |

### ✅ Desain yang Sudah Benar (Menghindari Circular)
- `core/event_bus.py` dan `core/command_bus.py` menggunakan typed events sebagai payload — modul tidak saling import satu sama lain, hanya share events.
- `engine/radio_engine.py` menggunakan `TYPE_CHECKING` guard untuk menghindari circular import dengan `engine/playback/`.
- `core/ports.py` mendefinisikan `Protocol` interfaces — modul lain depend on abstraction, bukan concrete class.

---

## 6. Folder yang Bisa Dipisah

### A. `cache/` → Pecah Menjadi `persistence/` + `cache/`
**Masalah saat ini:** `cache/` campur antara database layer (`db.py`, `schema.sql`, `library.db`) dengan caching strategy (`resolver.py`) dan file runtime lainnya (`admin_password.txt`, `inject_svgs.py`).

**Rekomendasi:**
```
persistence/          ← NEW: lapisan database murni
  ├── db.py           ← dipindah dari cache/
  ├── schema.sql
  └── library.db

cache/                ← SLIM: hanya resolver + file cache
  ├── resolver.py
  └── mp3/            ← downloaded audio files
```

---

### B. `engine/` → Pecah Menjadi `engine/` + `adapters/`
**Masalah saat ini:** `engine/` menampung domain logic (radio, playback, queue) bercampur dengan adapter/client external (`mpv_controller.py`, `ytdlp_client.py`).

**Rekomendasi:**
```
adapters/             ← NEW: concrete implementations dari core/ports.py
  ├── mpv_controller.py   ← AudioPlayerPort implementation
  └── ytdlp_client.py     ← MediaExtractorPort implementation

engine/               ← PURE: hanya domain logic
  ├── radio_engine.py
  ├── queue_manager.py
  ├── download_manager.py
  ├── volume_service.py
  ├── command_router.py
  └── playback/
      ├── controller.py
      └── track_loader.py
```

---

### C. `start.py` → Pecah Menjadi Package `launcher/` (✅ SELESAI)
**Status:** Diselesaikan pada Sprint 3.2.
`start.py` kini hanya menjadi *bootstrap file* yang memanggil package `launcher/`, di mana kode dibagi menjadi file-file kecil yang fokus (`gui.py`, `process.py`, `network.py`, `updater.py`).

---

### D. `server/handlers/websocket.py` → Pisahkan `ConnectionManager`
**Masalah:** `websocket.py` menampung `ConnectionManager` (koneksi state), routing command, dan auth check sekaligus.

**Rekomendasi:**
```
server/
  ├── connection_manager.py  ← BARU: ConnectionManager dipindah ke sini
  └── handlers/
      ├── websocket.py       ← SLIM: hanya routing & dispatch
      ├── auth.py
      ├── http.py
      └── event_listeners.py
```

---

### E. `data/` → Bersihkan Artefak Warisan
**Masalah:** Folder `data/` berisi `ytgui.db` (212 KB) sisa dari era sebelum rebranding LunaWave, dan `export_to_sqlite.py` yang merupakan one-time migration script.

**Rekomendasi:**
- Archive atau hapus `data/ytgui.db` setelah verifikasi tidak ada data yang belum dimigrasikan.
- Pindahkan `data/export_to_sqlite.py` ke `scripts/` (itu script, bukan data).
- Pertimbangkan migrasi `artists_enriched.json` ke database sebagai tabel `artists`, bukan file JSON statis 185 KB.

---

### F. `web/static/index.html` → Komponen HTML Terpisah
**Masalah:** 36 KB HTML monolitik — semua modal, panel, player bar dalam satu file.

**Rekomendasi jangka panjang:**
- Minimal: extract ke `<template>` tag per komponen, load via JS.
- Optimal: adopsi build tooling (Vite/esbuild) — ini perubahan besar yang membutuhkan sprint tersendiri.

---

## 7. Folder yang Sudah Bagus ✅

### `core/` — Excellent
- Tidak ada dependency ke modul lain di luar `core/` (hampir sepenuhnya).
- `ports.py` mendefinisikan abstraction interface dengan baik menggunakan `Protocol`.
- `event_bus.py` + `command_bus.py` memisahkan pub/sub dari single-writer command pattern dengan benar.
- `state.py` bersih — hanya dataclass dan enum, tidak ada business logic.
- `events.py` mendefinisikan domain events sebagai immutable dataclass.
- `task_utils.py` adalah utility murni tanpa side-effect.

### `web/static/css/` — Arsitektur Sudah Terstruktur
- Pemisahan folder `base/`, `components/`, `layout/`, `platform/` sudah mengikuti metodologi ITCSS.
- `tokens.css` sebagai design token sudah dipisah dengan benar.
- Masing-masing file CSS fokus pada satu concern (e.g., `player-bar.css`, `queue.css`).

### `plugins/` — Desain Plugin Clean
- Setiap plugin (`lyrics`, `sponsorblock`, `notifications`) adalah modul independen.
- Semua hanya berkomunikasi via `EventBus` dan `CommandBus` — tidak ada direct coupling ke engine.
- Mudah ditambah atau dinonaktifkan tanpa efek samping ke core.

### `server/services/` — Slim & Focused
- `broadcast_service.py` (1.6 KB) dan `stream_prefetch.py` (835 bytes) adalah contoh single-responsibility yang baik.
- Masing-masing melakukan satu hal dan melakukannya dengan baik.

### `web/static/js/events/` & `web/static/js/render/` — Pemisahan Concerns
- `events/` hanya berisi event handler (tidak ada rendering).
- `render/` hanya berisi view logic (tidak ada business logic).
- Pemisahan ini sudah mengikuti prinsip separation of concerns dengan baik untuk vanilla JS tanpa framework.

### `engine/playback/` — Sub-package yang Tepat
- Pemecahan `controller.py` + `track_loader.py` ke sub-package `playback/` adalah keputusan arsitektur yang bagus — menunjukkan kesiapan untuk dipecah lebih lanjut.

---


