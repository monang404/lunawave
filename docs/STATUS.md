---
last_verified: 2026-07-10
sprint: 3.2
---

# STATUS.md — Kondisi File per Sprint

> Tabel ini adalah satu-satunya source of truth untuk "sudah sampai mana?"
> Update setiap sprint selesai.

## Backend Python

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `cache/db.py` | God class 388 baris, 5 domain | Pecah → `persistence/track_repo.py` dll | Sprint 4 | ⏳ Belum |
| `cache/resolver.py` | Di `cache/`, masih aktif | Pindah ke `persistence/resolver.py` | Sprint 5 | ⏳ Belum |
| `engine/mpv_controller.py` | Di `engine/`, adapter eksternal | Pindah ke `adapters/mpv/` | Sprint 4 | ⏳ Belum |
| `engine/ytdlp_client.py` | Di `engine/`, adapter eksternal | Pindah ke `adapters/ytdlp/` | Sprint 4 | ⏳ Belum |
| `server/handlers/websocket.py` | Monolith 317 baris | Pisah `ConnectionManager` ke file sendiri | Sprint 4 | ⏳ Belum |
| `config.py` | Import `core/security` (violation) | Pisah ke `config_security.py` | Sprint 4 | ⏳ Belum |
| `core/command_bus.py` | CMD constants campur logic | Pisah CMD ke `core/commands.py` | Sprint 4 | ⏳ Belum |
| `launcher/` | ✅ Sudah refactor Sprint 3.2 | Sudah sesuai target | — | ✅ Done |
| `start.py` | ✅ Hollow re-export | Sudah sesuai target | — | ✅ Done |

## Frontend JS/CSS

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `web/static/index.html` | SPA monolith 677 baris | Tetap 1 file (tidak dipecah) | — | ✅ Final |
| `web/static/js/` | 21 file, 2813 baris | ~32 file | Sprint 9 | ⏳ Belum |
| `web/static/css/` | 22 file, 3274 baris | ~24-26 file | Sprint 10 | ⏳ Belum |

## Data & Infra

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `data/artists_enriched.json` | 185KB JSON statis | Import ke tabel DB | Sprint 5 | ⏳ Belum |
| `data/export_to_sqlite.py` | Di `data/` | Pindah ke `scripts/` | Sprint 4 | ⏳ Belum |
| `cache/admin_password.txt` | Ada di repo — perlu cek .gitignore | Di .gitignore | ASAP | 🔄 Cek |

## Docs

| Dokumen               | Kondisi Aktual | Tindakan             | Status |
| -----------------------| ----------------| ----------------------| --------|
| `docs/INDEX.md`       | Ada, manual    | Maintain rutin       | ✅　　　|
| `docs/STATUS.md`      | File ini       | Maintain tiap sprint | ✅　　　|
| `docs/AI_CONTEXT.md`  | Sudah ada      | Maintain tiap sprint | ✅　　　|
| `docs/CONSTRAINTS.md` | Belum ada      | Buat Sprint 3.3      | ⏳　　　|
| `docs/kompas/rfc/`    | Folder kosong  | Isi atau hapus       | 🔄　　 |