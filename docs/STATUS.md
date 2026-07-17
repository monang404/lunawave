---
title : LunaWave Project Status
last_verified: 2026-07-16
sprint: Phase 8 (selesai) + Tier 2 (T10-T16) + Hardening (implementation-plan.md Batch 0-4.2)
---

# STATUS.md — Kondisi File per Sprint

> Tabel ini adalah satu-satunya source of truth untuk "sudah sampai mana?"
> Update setiap sprint selesai.

## Backend Python

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `cache/db.py` | ✅ Sudah dipisah ke `persistence/` | Pecah → `persistence/track_repo.py` dll | Sprint 4 | ✅ Done |
| `cache/resolver.py` | Di `cache/`, masih aktif | Pindah ke `persistence/resolver.py` | Sprint 5 | ❄️ Frozen (v1.0.0 Baseline) |
| `engine/mpv_controller.py` | ✅ Sudah dipisah ke `adapters/mpv/` | Pindah ke `adapters/mpv/` | Sprint 4 | ✅ Done |
| `engine/ytdlp_client.py` | ✅ Sudah dipisah ke `adapters/ytdlp/` | Pindah ke `adapters/ytdlp/` | Sprint 4 | ✅ Done |
| `server/handlers/websocket.py` | Monolith **354 baris** (naik dari 317 setelah Batch 9, `PATCH-2026-07-11-018` — parallel broadcast + parallel Discover query, diizinkan eksplisit sbg file *restricted*) | Pisah `ConnectionManager` ke file sendiri | Sprint 4 | ❄️ Frozen (v1.0.0 Baseline) |
| `config.py` | ✅ Sudah dipisah ke `config_security.py` | Pisah ke `config_security.py` | Sprint 4 | ✅ Done |
| `core/command_bus.py` | ✅ Sudah dipisah ke `core/commands.py` | Pisah CMD ke `core/commands.py` | Sprint 4 | ✅ Done |
| `engine/playback/controller.py` | 464 baris, closure kompleks (naik dari 420 setelah `PATCH-2026-07-16-069` — tambah `dispose()` + simpan referensi lambda subscription, diizinkan eksplisit sbg file *restricted*) | Pecah `queue_ops.py` + `mode_ops.py` (lihat MIGRATION_GUIDE Tahap 6) | Sprint 4 | ❄️ Frozen (v1.0.0 Baseline) |
| `launcher/` | ✅ Sudah refactor Sprint 3.2 | Sudah sesuai target | — | ✅ Done |
| `start.py` | ✅ Hollow re-export | Sudah sesuai target | — | ✅ Done |

## Frontend JS/CSS

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `web/static/index.html` | SPA monolith 677 baris | Tetap 1 file (tidak dipecah) | — | ✅ Final |
| `web/static/js/` | **24 file, 3118 baris** (naik dari 21 file/2813 baris) | ~32 file | Sprint 9 | ❄️ Frozen (v1.0.0 Baseline) |
| `web/static/css/` | 22 file, 3274 baris | ~24-26 file | Sprint 10 | ❄️ Frozen (v1.0.0 Baseline) |

## Data & Infra

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `data/artists_enriched.json` | 185KB JSON statis | Import ke tabel DB | Sprint 5 | ❄️ Frozen (v1.0.0 Baseline) |
| `data/export_to_sqlite.py` | Di `data/` | Sudah dipindah ke `data/` | Sprint 3.3 | ✅ Selesai |
| `cache/admin_password.txt` | ✅ Sudah tidak ada di repo, sudah di `.gitignore` (terverifikasi 2026-07-13) | Di .gitignore | — | ✅ Done |

## Docs

| Dokumen               | Kondisi Aktual | Tindakan             | Status |
| -----------------------| ----------------| ----------------------| --------|
| `docs/INDEX.md`       | Ada, manual    | Maintain rutin       | ✅　　　|
| `docs/STATUS.md`      | File ini       | Maintain tiap sprint | ✅　　　|
| `docs/AI_CONTEXT.md`  | Sudah ada      | Maintain tiap sprint | ✅　　　|
| `docs/CONSTRAINTS.md` | Sudah ada      | Maintain rutin      | ✅　　　|
| `docs/rfc/`    | **Sudah tidak ada sama sekali** (bukan lagi "folder kosong") — terverifikasi 2026-07-13 | Tidak ada tindakan lanjutan, sudah terselesaikan dengan sendirinya | ✅　　　|

## Hardening — implementation-plan.md (2026-07-16)

> Ringkasan status per item, lihat `PATCH-2026-07-16-069` di `PATCHLOG.md` untuk detail lengkap.

| Item | Modul | Status |
|------|-------|--------|
| Batch 0 (CI hang) — `pytest-timeout`, await task cancellation | `pytest.ini`, `main.py`, `adapters/mpv/observer.py` | ✅ Done, terverifikasi lewat eksekusi nyata (baseline zombie thread hilang) |
| #1 dedup title radio queue | `engine/radio/track_filter.py` | ✅ Sudah lebih dulu diperbaiki sebelum sesi ini (diverifikasi ulang, ada test) |
| #2 race condition crossfade fade-in | `engine/playback/controller.py`, `crossfade.py` | ✅ Sudah lebih dulu diperbaiki sebelum sesi ini (diverifikasi ulang, ada test) |
| #3 fast-skip `mpv` di integration test | `tests/integration/conftest.py` | ✅ Done + bonus fix: urutan check dipindah sebelum `db.init()` (leak thread ditemukan saat testing) |
| #4 timing side-channel login admin | `server/handlers/auth.py` | ✅ Done + regression test |
| #5 `db.py.close()` join thread asli | `persistence/db.py` | ✅ Done + regression test |
| #6 lifecycle EventBus/CommandBus | `core/command_bus.py`, `engine/playback/controller.py` | ✅ Done — `CommandBus.reset()`, `PlaybackController.dispose()` |
| #7 window deteksi SponsorBlock | `plugins/sponsorblock.py` | ✅ Done + 3 regression test |
| #8 parser LRC multi-timestamp & metadata | `plugins/lyrics_parser.py` | ✅ Done + 2 regression test |
| #9 test coverage modul rawan-timing | `test_crossfade.py`, `test_track_ended_ops.py` | ✅ Done (crossfade sudah ada sebelumnya; track_ended_ops baru ditulis sesi ini) |
| #10 desain tombol "prev" (forward-stack) | `engine/playback/controller.py` | ⏸️ Belum — butuh keputusan produk, belum diajukan |
| #11 dead code | `prefetcher.py`, `middleware.py`, `controller.py` | ✅ Done (2/3 sudah bersih sebelumnya; `_last_position_save` ternyata sudah tersambung, bukan dead code) |
| #12 minor (bare except, token compare) | `main.py`, `http.py` | ✅ Done (`http.py` sudah pakai `secrets.compare_digest` sebelumnya) |
| Bonus: `patchlog.py` catastrophic regex backtracking | `automation/patchlog.py` | ✅ Done, ditemukan saat mencoba log patch ini sendiri |

**Hasil test:** 508 passed, 6 skipped (naik dari baseline 475 passed sebelum sesi ini). `ruff`/`mypy`/`bandit` bersih untuk semua file yang diubah. Coverage total 88%.
