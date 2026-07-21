---
title : LunaWave Project Status
last_verified: 2026-07-21
sprint:
---

# STATUS.md — Kondisi File per Sprint

> Tabel ini adalah satu-satunya source of truth untuk "sudah sampai mana?"
> Update setiap sprint selesai.

## perf_background_battery_survival (2026-07-21)

Battery/background-survival fixes (server mati & baterai boros saat layar
mati) — PERF-1..4, 6, 7 dari temuan.md. PERF-5 (broadcast progress
per-visibility) **deferred — future work, butuh sign-off terpisah** (lihat
`docs/rfc/performa/task_breakdown_perf.yaml` blok `future_work` / F1.1).

| File | Perubahan |
|---|---|
| `plugins/notifications.py` | `--ongoing` + `--priority high` di notifikasi now-playing (PERF-1) |
| `persistence/db.py` | `PRAGMA synchronous=NORMAL` setelah `journal_mode=WAL` (PERF-7) |
| `bootstrap/power.py` (baru) | `acquire_wake_lock()` fail-safe (PERF-2) |
| `bootstrap/startup_tasks.py` | wiring `acquire_wake_lock()` sebagai background task |
| `web/static/js/audio/playback-sync.js` | titik kontrol tunggal visibilitychange (PERF-3) |
| `web/static/js/audio/visualizer.js` | guard `document.hidden` self-terminating (PERF-3) |
| `web/static/js/render/radio-hero-moon.js` | guard `document.hidden` di stepCycle/stepTween (PERF-3) |
| `web/static/js/ws.js` | exponential backoff reconnect + listener visibility terpisah (PERF-4) |
| `engine/loudness/analyzer.py` | wrapper `nice`/`ionice` untuk ffmpeg (PERF-6) |
| `engine/loudness/service.py` | charging-gate untuk analisis loudness (PERF-6) |
| `adapters/ytdlp/__init__.py` | `os.setpriority` low-priority worker thread (PERF-6) |
| `docs/CONSTRAINTS.md` | dokumentasi setup manual HyperOS/MIUI (PERF-2) |
