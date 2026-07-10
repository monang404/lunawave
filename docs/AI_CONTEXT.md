---
last_verified: 2026-07-10
sprint: 3.2
---

# AI_CONTEXT.md — Baca ini sebelum menyentuh kode apapun

## Ringkasan Project
LunaWave adalah music player berbasis YouTube yang jalan sebagai server lokal
(aiohttp + asyncio), diakses via browser. Audio diputar oleh MPV via IPC socket.
Platform utama: Termux (Android) + Windows.
Arsitektur: Hexagonal (Ports & Adapters). Frontend: Vanilla JS, no framework.

## Sprint Aktif: 3.2 (selesai) → 3.3 (berikutnya)
- Sprint 3.2 selesai: refactor `start.py` → `launcher/` ✅
- Sprint 3.3 target: lihat `docs/STATUS.md` untuk daftar lengkap

## File yang TIDAK BOLEH disentuh tanpa izin eksplisit
- `engine/playback/controller.py` — risiko tinggi, closure kompleks
- `server/handlers/websocket.py` — jangan pecah dulu, ikuti MIGRATION_GUIDE Tahap 3
- `cache/admin_password.txt` — JANGAN commit
- `web/static/index.html` — tidak dipecah, ini keputusan final

## Batasan teknis yang tidak boleh dilanggar
- Tidak boleh ganti aiohttp ke framework lain
- Tidak boleh tambah JS framework (React, Vue, dll)
- Tidak boleh ganti SQLite ke DB lain
- Tidak boleh refactor 2 tahap sekaligus dalam 1 commit
- Setiap file yang dipindah WAJIB ada backward-compat alias

## Alur kerja AI yang benar
1. Baca file ini
2. Baca `docs/STATUS.md` — cek kondisi file yang akan disentuh
3. Baca `docs/PATCHLOG.md` — 2-3 entri terakhir
4. Baru kerjakan task
5. Setelah selesai: append PATCHLOG, update STATUS.md jika ada yang berubah

## Pointer ke detail
| Butuh info tentang | Baca |
|--------------------|------|
| Semua file & fungsinya | `docs/FILE_INDEX.md` (verify dulu, mungkin stale) |
| Struktur folder | `docs/STRUCTURE.md` |
| Roadmap refactoring | `docs/MIGRATION_GUIDE.md` |
| Arsitektur ideal | `docs/kompas/Blueprint.md` |
| Keputusan arsitektur | `docs/kompas/adr/` |
| Temuan & status bug | `docs/REPORT.md` |
| Kondisi per-file | `docs/STATUS.md` |