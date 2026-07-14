---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-14-038

total_entries: 38

---



# PATCHLOG.md — LunaWave



> **Format:** Append-only. Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



---







## [2026-07-09] Replace semua identitas legacy (YTGUI, ytgui, bagas.fm, YT Termux Player) dengan LunaWave. Zero regresi pada business logic.

**ID:** `PATCH-2026-07-09-001`

**Tanggal:** 2026-07-09

**Ringkasan:** Replace semua identitas legacy (YTGUI, ytgui, bagas.fm, YT Termux Player) dengan LunaWave. Zero regresi pada business logic.

**File Terdampak:**

- `config.py`
- `main.py`
- `core/observability.py`
- `web/static/js/utils.js`
- `web/static/manifest.json`
- `web/static/sw.js`
- `web/static/index.html`
- `scripts/generate_icons.py`
- `config.py`
- `main.py`
- `core/observability.py`
- `web/static/js/utils.js`
- `web/static/manifest.json`
- `scripts/generate_icons.py`
- `start.py`
- `launcher/`
- `launcher/__init__.py`
- `launcher/gui.py`
- `launcher/process.py`
- `launcher/network.py`
- `launcher/updater.py`
- `docs/INDEX.md`
- `docs/STRUCTURE.md`
- `docs/FILE_INDEX.md`
- `docs/PATCHLOG.md`
- `docs/REPORT.md`
- `web/static/js/render/queue.js`
- `engine/download_manager.py`
- `server/handlers/websocket.py`
- `web/static/index.html`
- `web/static/css/tokens.css`
- `web/static/css/vendor/tabler-icons.min.css`
- `web/static/css/vendor/fonts/*`
- `web/static/sw.js`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`
- `docs/STRUCTURE.md`
- `docs/INDEX.md`
- `.pre-commit-config.yaml`
- `.pre-commit-config.yaml`
- `docs/PATCHLOG.md`
- `docs/devops/tooling.md`
- `scripts/shared/`
- `scripts/verify_docs/`
- `scripts/verify_docs.py`
- `scripts/verify_security.py`
- `scripts/verify_structure.py`
- `scripts/architecture_lint.py`
- `scripts/generate_report.py`
- `scripts/generate_file_index.py`
- `docs/STRUCTURE.md`
- `docs/architecture/folder_structure.md`
- `AI_CONTEXT.md`
- `docs/AI_CONTEXT.md`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`
- `engine/ytdlp_client.py`
- `server/handlers/auth.py`
- `main.py`
- `engine/mpv_controller.py`
- `plugins/lyrics.py`
- `engine/playback/track_loader.py`
- `server/handlers/event_listeners.py`
- `cache/schema.sql`
- `server/handlers/websocket.py`
- `engine/playback/controller.py`
- `server/serializers.py`
- `server/services/broadcast_service.py`
- `core/command_bus.py`
- `core/observability.py`
- `start.sh`
- `start.bat`
- `adapters/__init__.py`
- `engine/radio/__init__.py`
- `persistence/__init__.py`
- `launcher/__init__.py`
- `core/command_bus.py`
- `core/commands.py`
- `config.py`
- `config_security.py`
- `persistence/db.py`
- `persistence/track_repo.py`
- `persistence/session_repo.py`
- `persistence/artist_repo.py`
- `persistence/genre_repo.py`
- `persistence/library_repo.py`
- `persistence/__init__.py`
- `cache/db.py`
- `persistence/schema.sql`
- `scripts/architecture_lint.py`
- `adapters/mpv/connection.py`
- `adapters/mpv/ipc.py`
- `adapters/mpv/observer.py`
- `adapters/mpv/__init__.py`
- `engine/mpv_controller.py`
- `adapters/ytdlp/common.py`
- `adapters/ytdlp/searcher.py`
- `adapters/ytdlp/resolver.py`
- `adapters/ytdlp/downloader.py`
- `adapters/ytdlp/__init__.py`
- `engine/ytdlp_client.py`
- `engine/radio_engine.py`
- `engine/radio/artist_selector.py`
- `engine/radio/track_interleaver.py`
- `engine/radio/prefetcher.py`
- `engine/radio/engine.py`
- `engine/radio/__init__.py`
- `engine/playback/queue_ops.py`
- `engine/playback/mode_ops.py`
- `engine/playback/controller.py`
- `server/handlers/websocket.py`
- `server/connection_manager.py`
- `server/handlers/ws_*.py`
- `launcher/gui.py`
- `launcher/gui/app.py`
- `data/export_to_sqlite.py`
- `cache/schema.sql`
- `plugins/lyrics.py`
- `web/static/js/events/*`
- `web/static/js/audio/*`
- `web/static/js/utils/*`
- `web/static/js/render/*`
- `web/static/js/ws.js`
- `web/static/index.html`
- `scripts/verify_docs/checks_docs.py`
- `scripts/architecture_lint.py`
- `scripts/generate_file_index.py`
- `docs/CONSTRAINTS.md`
- `docs/rfc/.keep`
- `pyproject.toml`
- `.importlinter`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `tests/unit/adapters/mpv/`
- `tests/unit/engine/radio/`
- `tests/unit/engine/playback/`
- `tests/unit/server/handlers/`
- `tests/unit/server/services/`
- `tests/unit/plugins/`
- `tests/unit/launcher/gui/`
- `tests/integration/`
- `tests/frontend/utils/`
- `tests/fakes/fake_lyrics_provider.py`
- `tests/fakes/fake_sponsorblock_provider.py`
- `tests/conftest.py`
- `tests/unit/persistence/test_library_repo.py`
- `tests/unit/engine/radio/test_track_interleaver.py`
- `tests/unit/engine/playback/test_queue_ops.py`
- `tests/unit/engine/playback/test_mode_ops.py`
- `tests/unit/launcher/gui/test_dep_checker.py`
- `tests/unit/server/test_connection_manager.py`
- `tests/unit/server/test_middleware.py`
- `tests/unit/server/test_serializers.py`
- `tests/unit/engine/radio/test_artist_selector.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_sync.py`
- `services/__init__.py`
- `.importlinter`
- `requirements-dev.txt`
- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.editorconfig`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`
- `docs/kompas/*`
- `docs/Blueprint.md`
- `AI_CONTEXT.md`
- `CONTRIBUTING.md`
- `docs/MIGRATION_GUIDE.md`
- `docs/PATCHLOG.md`
- `docs/STATUS.md`
- `docs/FILE_INDEX.md`
- `scripts/architecture_lint.py`
- `scripts/find_owner.py`
- `scripts/verify_structure.py`
- `tests/conftest.py`
- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_websocket_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_download_flow.py`
- `scripts/generate_file_index.py`
- `scripts/generate_report.py`
- `scripts/run_all.py`

---
