---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-15-047

total_entries: 47

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



---

## [2026-07-15] CI Hang Diagnosis & Documentation Update
**ID:** `PATCH-2026-07-15-047`
**Tanggal:** 2026-07-15
**Ringkasan:** Mendiagnosa dan menemukan akar masalah "hang 1 jam 54 menit" pada CI pytest. Hang terbukti disebabkan oleh *zombie process* `yt-dlp` pada integration test (`test_download_flow.py`) yang gagal *timeout* akibat pemblokiran IP oleh YouTube di server GitHub Actions, dan tidak di-kill saat *teardown*. Memperbarui panduan integration testing dengan instruksi untuk memastikan `yt-dlp` dibunuh secara eksplisit di *teardown*. Seluruh 435 unit tests (P0-P4) terbukti *green* dan tidak bermasalah.
**File Terdampak:**
- `docs/testing/integration_testing.md`
- `log.md` (Catatan Mentah / Laporan Investigasi)

---

## [2026-07-15] Test Coverage P3 & P4 - WS & Radio Engine
**ID:** `PATCH-2026-07-15-046`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk error handling dan WS routing di `server/handlers/websocket.py` & `ws_playback.py` (P3) serta fallback prefetch dan radio_next di `engine/radio/engine.py` & `prefetcher.py` (P4) sesuai dengan `PATCH_TEST_COVERAGE.md`.
**File Terdampak:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_artist_selector.py`

---

## [2026-07-15] Test Coverage P2 - observer.py
**ID:** `PATCH-2026-07-15-045`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk loop event async di `adapters/mpv/observer.py` sesuai dengan P2 di `PATCH_TEST_COVERAGE.md` (unknown property change, cleanup path, socket reconnect loop). Coverage keseluruhan naik dari 77.48% menjadi 78.43%.
**File Terdampak:**
- `tests/unit/adapters/mpv/test_observer.py`

---

## [2026-07-15] Test Coverage P1 - controller.py
**ID:** `PATCH-2026-07-15-044`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk state machine di `engine/playback/controller.py` sesuai dengan P1 di `PATCH_TEST_COVERAGE.md` (race condition, error state, empty queue, rollback). Coverage keseluruhan naik dari 77.10% menjadi 77.48%.
**File Terdampak:**
- `tests/unit/engine/playback/test_controller.py`

---

## [2026-07-15] Test Coverage P0 - serve_stream
**ID:** `PATCH-2026-07-15-043`
**Tanggal:** 2026-07-15
**Ringkasan:** Menambahkan unit test untuk fungsi `serve_stream()` di `server/handlers/http.py` sesuai dengan P0 di `PATCH_TEST_COVERAGE.md`. Coverage keseluruhan naik dari 75.10% menjadi 77.10%.
**File Terdampak:**
- `tests/unit/server/handlers/test_http.py`

---

## [2026-07-15] Quality of Life (QoL) Enhancements: Bandit, Loudness, Adaptive Prefetch
**ID:** `PATCH-2026-07-15-042`
**Tanggal:** 2026-07-15
**Ringkasan:** Eksekusi integrasi 3 fitur besar secara serentak untuk mematuhi larangan two-stage refactoring:
1. Thompson Sampling Bandit untuk Artist Radio.
2. EBU R128 Loudness Normalization.
3. Adaptive Network Prefetch (Latency Window).
Fitur dipisah ke service/kelas baru dan controller dimodifikasi untuk injeksi ketergantungan.
**File Terdampak:**
- `persistence/schema.sql` & `__init__.py`
- `core/state.py`, `core/commands.py`, `core/ports.py`
- `persistence/artist_repo.py`, `persistence/track_repo.py`, `persistence/library_repo.py`
- `core/latency_window.py`
- `config.py` & `core/observability.py`
- `cache/resolver.py`
- `engine/radio/prefetcher.py`, `engine/radio/artist_bandit.py`, `engine/radio/artist_selector.py`
- `engine/loudness/gain_calculator.py`, `engine/loudness/analyzer.py`, `engine/loudness/service.py`
- `engine/playback/track_loader.py`, `engine/playback/mode_ops.py`, `engine/playback/controller.py`
- `adapters/mpv/__init__.py`
- `engine/command_router.py`
- `server/serializers.py`
- `main.py`

---



## [2026-07-14] Stable Release Hardening & Bug Fixes

**ID:** `PATCH-2026-07-14-041`
**Tanggal:** 2026-07-14
**Ringkasan:** Eksekusi P0-P2 dari IMPLEMENTATION_PLAN.md untuk persiapan Stable Release v1.0.0. Termasuk perbaikan banner password, path downloads, DB migration logging, `shell=False` di network probing, pemblokiran CI gate, metadata `pyproject.toml`, update package metadata, dan setup wheel build di CI.
**File Terdampak:**
- `main.py`
- `config.py`
- `README.md`
- `docs/INDEX.md`
- `engine/download_manager.py`
- `server/handlers/ws_download.py`
- `persistence/__init__.py`
- `launcher/network.py`
- `package.json`
- `.importlinter`
- `.github/workflows/ci.yml`
- `pyproject.toml`

---
