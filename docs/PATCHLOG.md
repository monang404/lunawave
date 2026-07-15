---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-15-042

total_entries: 42

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



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
