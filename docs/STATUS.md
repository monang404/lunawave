---
title : LunaWave Project Status
last_verified: 2026-07-13
sprint: 3.2 (selesai) + Batch 8–12 pasca-sprint (belum diberi nomor resmi)
---

# STATUS.md — Kondisi File per Sprint

> Tabel ini adalah satu-satunya source of truth untuk "sudah sampai mana?"
> Update setiap sprint selesai.

## Backend Python

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `cache/db.py` | ✅ Sudah dipisah ke `persistence/` | Pecah → `persistence/track_repo.py` dll | Sprint 4 | ✅ Done |
| `cache/resolver.py` | Di `cache/`, masih aktif | Pindah ke `persistence/resolver.py` | Sprint 5 | ⏳ Belum |
| `engine/mpv_controller.py` | ✅ Sudah dipisah ke `adapters/mpv/` | Pindah ke `adapters/mpv/` | Sprint 4 | ✅ Done |
| `engine/ytdlp_client.py` | ✅ Sudah dipisah ke `adapters/ytdlp/` | Pindah ke `adapters/ytdlp/` | Sprint 4 | ✅ Done |
| `server/handlers/websocket.py` | Monolith **354 baris** (naik dari 317 setelah Batch 9, `PATCH-2026-07-11-018` — parallel broadcast + parallel Discover query, diizinkan eksplisit sbg file *restricted*) | Pisah `ConnectionManager` ke file sendiri | Sprint 4 | ⏳ Belum |
| `config.py` | ✅ Sudah dipisah ke `config_security.py` | Pisah ke `config_security.py` | Sprint 4 | ✅ Done |
| `core/command_bus.py` | ✅ Sudah dipisah ke `core/commands.py` | Pisah CMD ke `core/commands.py` | Sprint 4 | ✅ Done |
| `engine/playback/controller.py` | 420 baris, closure kompleks (naik setelah Batch 9, `PATCH-2026-07-11-018` — `safe_create_task` untuk `mpv_toggle_pause`, diizinkan eksplisit sbg file *restricted*) | Pecah `queue_ops.py` + `mode_ops.py` (lihat MIGRATION_GUIDE Tahap 6) | Sprint 4 | ⏳ Belum |
| `launcher/` | ✅ Sudah refactor Sprint 3.2 | Sudah sesuai target | — | ✅ Done |
| `start.py` | ✅ Hollow re-export | Sudah sesuai target | — | ✅ Done |

## Frontend JS/CSS

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `web/static/index.html` | SPA monolith 677 baris | Tetap 1 file (tidak dipecah) | — | ✅ Final |
| `web/static/js/` | **24 file, 3118 baris** (naik dari 21 file/2813 baris) | ~32 file | Sprint 9 | ⏳ Belum |
| `web/static/css/` | 22 file, 3274 baris | ~24-26 file | Sprint 10 | ⏳ Belum |

## Data & Infra

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `data/artists_enriched.json` | 185KB JSON statis | Import ke tabel DB | Sprint 5 | ⏳ Belum |
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
