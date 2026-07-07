# LunaWave - System Mapping & Architecture

Dokumen ini berisi peta komponen dan struktur direktori utama dari **LunaWave**, sebuah aplikasi pemutar musik berbasis YouTube (menggunakan mpv & yt-dlp) dengan arsitektur terspesialisasi.

AI Agent diwajibkan untuk memperbarui dokumen ini apabila menambahkan file utama baru, modul baru, atau jika ada perubahan arsitektur (refactoring besar).

---

## 🏗️ Arsitektur Sistem

LunaWave menggunakan *decoupled architecture* dengan event-driven state management:
- **Backend**: Python dengan `aiohttp` untuk HTTP API & WebSocket, serta SQLite (via `aiosqlite`) untuk penyimpanan sesi dan metadata.
- **Frontend**: Progressive Web App (PWA) menggunakan Vanilla JavaScript (dikompilasi dengan `esbuild`), CSS Tokens, dan Event-driven state management.
- **Playback Engine**: `mpv` untuk pemutaran audio, dan `yt-dlp` untuk ekstraksi stream.
- **Komunikasi Internal**: Menggunakan EventBus dan pola Domain Events untuk menghindari *race conditions* dan menjaga agar state mutations tetap terisolasi.

---

## 📂 Struktur Direktori Utama

```text
/
├── core/                 # Domain logic, constants, state management (AppState), ports
├── engine/               # Playback engine (mpv_controller, download_manager)
├── cache/                # Persistence layer (SQLite db.py, schema, repositories)
├── server/               # API layer (aiohttp app, handlers: http, websocket, auth)
├── web/                  # Frontend PWA (Vanilla JS, CSS, assets, index.html)
├── tests/                # Unit tests dan integration tests
├── scripts/              # Build scripts (e.g., build_js.py)
├── plugins/              # Sistem plugin (jika ada)
├── audit/                # Direktori dokumentasi audit, task, dan log eksekusi AI (berisi file ini)
├── README.md             # Dokumentasi utama proyek
├── package.json          # Node dependencies (untuk tools build JS)
└── pyproject.toml        # Python project metadata & tool configs (Ruff, Mypy)
```

---

## 🧩 Modul & File Kunci (Backend Layering)

| Lapisan | Direktori/File | Fungsi Utama |
| --- | --- | --- |
| **API/Transport** | `server/app.py` | Entry point aiohttp server. |
| **API/Transport** | `server/handlers/*` | HTTP, WebSocket, Auth handlers. (Termasuk rate limiting & stream proxy). |
| **Domain/Core** | `core/state.py` | Menyimpan `AppState` (saat ini *in-memory*). |
| **Domain/Core** | `core/events.py` | EventBus dan definisi domain event. |
| **Domain/Core** | `core/bootstrap.py` | Inisialisasi dependency injection (`PlaybackDependencies`). |
| **Engine** | `engine/mpv_controller.py` | Mengontrol proses mpv player via IPC/socket. |
| **Persistence** | `cache/db.py` | Proxy/koneksi ke SQLite (dengan pola WAL mode). |

---

## 🔗 Dependensi Kunci
- **Python**: `aiohttp`, `aiosqlite`, `yt-dlp`
- **Sistem**: `mpv`, `ffmpeg`
- **Frontend**: Vanilla JS (tanpa framework besar), bundled via `esbuild`.
