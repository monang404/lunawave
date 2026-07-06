# Sprint 5 - Architecture Refactoring Changelog

**Status**: ACTIVE (10 tasks done)
**Date**: 2026-07-06

### S05-010 — code_smell_audit.md (CS-11)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring Magic Numbers: WS Payload Defaults)

### S05-009 — code_smell_audit.md (CS-09)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring Primitive Obsession - Value Objects)

### S05-008 — code_smell_audit.md (CS-08)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring Magic Strings: HTTP Routes)

### S05-007 — code_smell_audit.md (CS-07)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring Data Clumps - Serializers)

### S05-006 — code_smell_audit.md (CS-06)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring CommandBus Shotgun Surgery ke Dataclasses)

### S05-005 — code_smell_audit.md (CS-05)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring PlaybackController Long Parameter List)

### S05-004 — code_smell_audit.md (CS-04)
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring PlaybackController God Object)

### S05-003 — code_smell_audit.md (CS-03)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring Large Class websocket.py)

### S05-002 — code_smell_audit.md (CS-02)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring God Function main() di main.py)

### S05-001 — code_smell_audit.md (CS-01)
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactoring God Class ServerManager di start.py)

---

# Sprint 4 - Frontend Experience Changelog

**Status**: ACTIVE (22 tasks done)
**Date**: 2026-07-06

### S04-004 — Sudah diselesaikan secara preventif (Tabler Icons sudah dipin ke v3.2.0 dan Google Fonts sudah self-hosted)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-001 — Menghapus endpoint /admin ganda dan redirect di JS
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-041 — Refactor renderRecentRow menggunakan renderDiscoverList untuk menghindari innerHTML destruction
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-040 — Pindahkan syncBrowserAudio ke dalam blok statusChanged dan debounce syncLocalLyrics
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-039 — Throttle TrackProgressEvent di mpv_controller alih-alih di event_listeners agar menghemat load subscriber
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-038 — Menggunakan broadcast_discover_data dari websocket.py alih-alih duplikasi logika
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-036 — Drop console.log via esbuild --pure:console.log
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-035 — Pindah URL iTunes API ke config.js
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-034 — Migrasi ke ES module system sepenuhnya selesai
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-033 — Dibersihkan 93 typeof guards dari JS
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Done)

### S04-028 — frontend_audit.md W-01
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Pindahkan player-bar keluar dari tab-home ke app shell)

### S04-027 — frontend_audit.md FRONTEND-21
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Fix race condition store.status vs ws update (SB-01))

### S04-010 — deployment_audit.md DEPLOYMENT-66
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Ganti shutil.copy2 dengan SQLite backup API di main.py dan cache/db.py)

### S04-009 — deployment_audit.md DEPLOYMENT-65
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Tambah __version__ di main.py)

### S04-008 — deployment_audit.md DEPLOYMENT-57
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Pin dependensi di pyproject.toml)

### S04-007 — deployment_audit.md DEPLOYMENT-55
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Sudah diperbaiki via pyproject.toml requires-python)

### S04-006 — deployment_audit.md DEPLOYMENT-20
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Minify JS dan CSS menggunakan esbuild)

### S04-005 — deployment_audit.md DEPLOYMENT-18
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Pin versi di requirements.txt dan requirements-dev.txt)

### S04-003 — HTTP vs WS skema error tidak baku
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Buat dan gunakan fungsi serializers.error_payload untuk semua response error di http.py dan websocket.py)

### S04-002 — GET /admin
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Menambahkan header X-Admin-UI-Security pada serve_index)

### S04-025 — Radio randomize bisa spam-klik
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Tambah cooldown 3s + disable button setelah klik)

### S04-026 — Play button aria-label tidak update
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (renderPlayBtn kini update aria-label & title dinamis)

### S04-029 — ::before/::after konflik pada home-art-frame
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Hapus duplicate ::after di cards.css, pertahankan player-bar.css)

### S04-030 — Settings sheet CSS double-defined
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Hapus blok lama di settings-sheet.css, pertahankan versi lengkap)

### S04-031 — favorites.js file kosong
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Tambah stub export agar kompatibel dengan ES module bundler)

### S04-032 — transmit-radio keyframe duplikat
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE (Hapus versi lama di animations.css, versi lengkap di cards.css)

### S04-011 — Frontend global-namespace coupling
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Refactored all JS ke ES modules dengan import/export eksplisit)

### S04-037 — 17 file JS diload terpisah tanpa bundling
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Setup esbuild, entry point main.js, semua dependensi di-resolve lewat imports)

### S04-042 — Bundle JS dengan esbuild
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (bundle.js 103kb dihasilkan, index.html diupdate ke 1 script tag)

### S04-021 — Skeleton CSS var undefined
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Fixed variables in animations.css)

### S04-022 — #discover-favorites / #discover-recent null di DOM
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Added missing containers to index.html and discover.js)

### S04-023 — Admin role dari localStorage tanpa server validation
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Updated initPortal to wait for auth_status from server)

### S04-024 — Lyrics disembunyikan total di mobile
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Tampilkan compact version instead of display none)

### S04-014 — Loading Issue Summary
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-015 — Animation Issue Summary
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-016 — UI Consistency Summary
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-017 — UX Issue Summary
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-018 — Dark Mode Summary
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-019 — Form Validation Summary
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-012 — Responsive Issue Summary
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-013 — Accessibility Summary
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE (Summary row closed)

### S04-020 — Focus trap missing di bottom sheet
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE (Implemented focus trap in settings, lyrics, help, and action sheets)

---

# Sprint 3 - Data & API Reliability Changelog

**Status**: COMPLETED (47 tasks done)
**Date**: 2026-07-03

### S03-001 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-002 — `GET /health`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-003 — Fix issue in api_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-004 — Fix issue in api_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-005 — `GET /api/stream/{video_id}`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-006 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-007 — WS `search` (`ytdlp.search(query, max_results=10)`)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-008 — `GET /api/stream/{video_id}` (cache-hit lokal)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-009 — `GET /` (`serve_index`)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-010 — Static assets (`/static`)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-011 — `stream_url` cache di DB (`STREAM_URL_TTL_SEC = 21600`)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-012 — `GET /api/stream/{video_id}`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-013 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-014 — `dict_to_track` (`server/serializers.py`)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-015 — Exception generik di `handle_ws_message`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-016 — Semua endpoint HTTP & protokol WS
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-017 — `GET /api/stream/{video_id}`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-018 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-019 — WS commands (`play_track`, `download`, dll.)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-020 — Fix issue in api_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-021 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-022 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-023 — `cache/db.py:toggle_favorite()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-024 — `cache/db.py:__init__()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-025 — `engine/radio_engine.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-026 — `services/discover_service.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-027 — `cache/db.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-028 — `cache/db.py:evict_stale_tracks()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-029 — Tidak ada
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-030 — `engine/radio_engine.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-031 — database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-032 — database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-033 — database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-034 — `cache/db.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-035 — `server/handlers/event_listeners.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-036 — Fix issue in database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-037 — `cache/db.py` (get_random_songs, get_genre_songs, dll)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-038 — `cache/schema.sql`, `cache/db.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-039 — `cache/schema.sql`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-040 — `cache/schema.sql`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-041 — `cache/db.py`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-042 — `scratch/check_db.py`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-043 — deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-044 — Backup
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-045 — Rollback
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-046 — Monitoring
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-047 — Repo hygiene
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

---

# Sprint 2 - Security Hardening Changelog

**Status**: COMPLETED (15 tasks done)
**Date**: 2026-07-03

### S02-001 — `GET /api/stream/{video_id}`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-002 — WS command gagal (`handle_ws_message` catch-all)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-003 — Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-004 — `GET /metrics`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-005 — Login admin (`handle_auth`)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-006 — Semua action WS setelah login
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-007 — `GET /api/stream/{video_id}`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-008 — `GET /health`, `GET /metrics`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-009 — dependency_audit.md
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-010 — Secrets
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-011 — Secrets
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-012 — `server/middleware.py`, `handlers/auth.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-013 — `server/handlers/http.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-014 — `config.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-015 — frontend_audit.md
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

---

﻿# Sprint 3 - Data & API Reliability Changelog

**Status**: COMPLETED (47 tasks done)
**Date**: 2026-07-03

### S03-001 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-002 â€” `GET /health`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-003 â€” Fix issue in api_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-004 â€” Fix issue in api_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-005 â€” `GET /api/stream/{video_id}`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-006 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-007 â€” WS `search` (`ytdlp.search(query, max_results=10)`)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-008 â€” `GET /api/stream/{video_id}` (cache-hit lokal)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-009 â€” `GET /` (`serve_index`)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-010 â€” Static assets (`/static`)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-011 â€” `stream_url` cache di DB (`STREAM_URL_TTL_SEC = 21600`)
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-012 â€” `GET /api/stream/{video_id}`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-013 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-014 â€” `dict_to_track` (`server/serializers.py`)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-015 â€” Exception generik di `handle_ws_message`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-016 â€” Semua endpoint HTTP & protokol WS
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-017 â€” `GET /api/stream/{video_id}`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-018 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-019 â€” WS commands (`play_track`, `download`, dll.)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-020 â€” Fix issue in api_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-021 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-022 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-023 â€” `cache/db.py:toggle_favorite()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-024 â€” `cache/db.py:__init__()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-025 â€” `engine/radio_engine.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-026 â€” `services/discover_service.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-027 â€” `cache/db.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-028 â€” `cache/db.py:evict_stale_tracks()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-029 â€” Tidak ada
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-030 â€” `engine/radio_engine.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-031 â€” database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-032 â€” database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-033 â€” database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-034 â€” `cache/db.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-035 â€” `server/handlers/event_listeners.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-036 â€” Fix issue in database_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-037 â€” `cache/db.py` (get_random_songs, get_genre_songs, dll)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-038 â€” `cache/schema.sql`, `cache/db.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-039 â€” `cache/schema.sql`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-040 â€” `cache/schema.sql`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-041 â€” `cache/db.py`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-042 â€” `scratch/check_db.py`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-043 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-044 â€” Backup
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-045 â€” Rollback
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-046 â€” Monitoring
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S03-047 â€” Repo hygiene
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

---\n\n# Sprint 2 - Frontend & Core Player Changelog

**Status**: COMPLETED (15 tasks done)
**Date**: 2026-07-03

### S02-001 â€” `GET /api/stream/{video_id}`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-002 â€” WS command gagal (`handle_ws_message` catch-all)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-003 â€” Fix issue in api_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-004 â€” `GET /metrics`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-005 â€” Login admin (`handle_auth`)
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-006 â€” Semua action WS setelah login
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-007 â€” `GET /api/stream/{video_id}`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-008 â€” `GET /health`, `GET /metrics`
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-009 â€” dependency_audit.md
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-010 â€” Secrets
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-011 â€” Secrets
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-012 â€” `server/middleware.py`, `handlers/auth.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-013 â€” `server/handlers/http.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-014 â€” `config.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S02-015 â€” frontend_audit.md
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

---\n\n# Sprint 1 - Core Bug Fixes & Stability Changelog

**Status**: COMPLETED (66 tasks done)
**Date**: 2026-07-03

### S01-001 â€” `engine/mpv_controller.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-002 â€” `server/handlers/websocket.py:broadcast()`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-003 â€” `engine/radio_engine.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-004 â€” `engine/volume_service.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-005 â€” `core/exceptions.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-006 â€” `core/command_bus.py` + `core/event_bus.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-007 â€” `engine/playback/controller.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-008 â€” `server/handlers/event_listeners.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-009 â€” Seluruh codebase
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-010 â€” `services/discover_service.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-011 â€” Semua plugin
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-012 â€” `cache/resolver.py` + `StreamPrefetchService`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-013 â€” `server/app.py`
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-014 â€” bug_audit.md
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-015 â€” bug_audit.md
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-016 â€” bug_audit.md
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-017 â€” bug_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-018 â€” bug_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-019 â€” bug_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-020 â€” bug_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-021 â€” bug_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-022 â€” bug_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-023 â€” bug_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-024 â€” dependency_audit.md
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-025 â€” dependency_audit.md
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-026 â€” dependency_audit.md
- **Priority**: P1 | **Type**: DECISION-NEEDED
- **Status**: DONE

### S01-027 â€” dependency_audit.md
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-028 â€” dependency_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-029 â€” dependency_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-030 â€” dependency_audit.md
- **Priority**: P2 | **Type**: DECISION-NEEDED
- **Status**: DONE

### S01-031 â€” dependency_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-032 â€” dependency_audit.md
- **Priority**: P3 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-033 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-034 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-035 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-036 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-037 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-038 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-039 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-040 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-041 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-042 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-043 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-044 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-045 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-046 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-047 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-048 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-049 â€” deployment_audit.md
- **Priority**: P0 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-050 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-051 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-052 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-053 â€” deployment_audit.md
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-054 â€” Disaster Recovery
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-055 â€” Secrets
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-056 â€” Monitoring
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-057 â€” Logging
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-058 â€” Logging
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-059 â€” Monitoring
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-060 â€” Release
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-061 â€” Release
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-062 â€” Docker
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-063 â€” Alerting
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-064 â€” Logging
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-065 â€” root repo
- **Priority**: P2 | **Type**: IMPLEMENTATION
- **Status**: DONE

### S01-066 â€” `engine/mpv_controller.py`
- **Priority**: P1 | **Type**: IMPLEMENTATION
- **Status**: DONE



### S05-011 - Refactoring Magic Strings: WS Action Names
- **Priority**: P2 | **Type**: REFACTOR
- **Status**: DONE
- **Description**: Diganti magic strings pada actions WebSocket backend dan JS (wsSend) dengan referensi konstanta dari WSAction/WS_ACTIONS.
