---
title : LunaWave Project Status
last_verified: 2026-07-17
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
| `server/handlers/websocket.py` | Monolith **355 baris** (naik dari 354). Izin eksplisit **diberikan** user pada `PATCH-2026-07-17-071` untuk perubahan 1 baris (`"get_artist_detail"` ditambahkan ke `DISCOVERY_CMDS`) — action itu kini reachable dari client, lihat §Discover Tab Personalization di bawah. | Pisah `ConnectionManager` ke file sendiri | Sprint 4 | ❄️ Frozen (v1.0.0 Baseline) |
| `persistence/discover_repo.py` | **Baru**, `PATCH-2026-07-17-070`. 242 baris — zona Waspada (>150), belum "wajib pecah" (<300). Kalau nanti nambah section baru, pertimbangkan pecah per-jenis query (`bandit.py` / `taste.py`) sebelum lewat 300. | 1 file = query personalisasi Discover | — | 🆕 Baru, siap dipakai backend |
| `persistence/discover_enrich.py` | **Baru**, `PATCH-2026-07-17-070`. 78 baris — aman. | Helper cover+genre batch, dipakai `discover_repo.py` | — | 🆕 Baru, siap dipakai backend |
| `config.py` | ✅ Sudah dipisah ke `config_security.py` | Pisah ke `config_security.py` | Sprint 4 | ✅ Done |
| `core/command_bus.py` | ✅ Sudah dipisah ke `core/commands.py` | Pisah CMD ke `core/commands.py` | Sprint 4 | ✅ Done |
| `engine/playback/controller.py` | 464 baris, closure kompleks (naik dari 420 setelah `PATCH-2026-07-16-069` — tambah `dispose()` + simpan referensi lambda subscription, diizinkan eksplisit sbg file *restricted*) | Pecah `queue_ops.py` + `mode_ops.py` (lihat MIGRATION_GUIDE Tahap 6) | Sprint 4 | ❄️ Frozen (v1.0.0 Baseline) |
| `launcher/` | ✅ Sudah refactor Sprint 3.2 | Sudah sesuai target | — | ✅ Done |
| `start.py` | ✅ Hollow re-export | Sudah sesuai target | — | ✅ Done |

## Frontend JS/CSS

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `web/static/index.html` | SPA monolith **862 baris** (naik dari 677 — markup taste spectrum/filter bar/3 card-row + artist detail sheet ditambah, `PATCH-2026-07-17-071`) | Tetap 1 file (tidak dipecah) | — | ✅ Final |
| `web/static/js/` | **33 file, 3472 baris** (naik 1 file — `render/discover-personalize.js` baru, 185 baris, `PATCH-2026-07-17-071`). Catatan: angka "24 file" sebelumnya di baris ini sudah stale relatif terhadap isi repo aktual sebelum sesi ini juga; jumlah di atas adalah hasil hitung langsung `find`. | ~32 file | Sprint 9 | ❄️ Frozen (v1.0.0 Baseline) |
| `web/static/css/` | **23 file, 3722 baris** (naik 1 file — `components/discover-cards.css` baru, `PATCH-2026-07-17-071`) | ~24-26 file | Sprint 10 | ❄️ Frozen (v1.0.0 Baseline) |
| `web/static/js/render/discover-tab.js` | Disentuh di `PATCH-2026-07-17-073` untuk mengimplementasi progressive disclosure (jumlah baris sekarang ~286). | Tetap terpisah dari personalisasi | — | ⚠️ Waspada (di atas ambang, namun sudah diperbaiki UI/UX-nya) |

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

## Discover Tab Personalization — Backend + Frontend (2026-07-17)

> Detail lengkap: `PATCH-2026-07-17-070` (backend) dan `PATCH-2026-07-17-071`
> (frontend) di `PATCHLOG.md`. Referensi desain: `discover-tab-redesign.html`.
> Rencana asli: `discover-tab-implementation-plan-v2.md` (v2 dipakai, bukan
> v1 — repo baru `discover_repo.py`, bukan nambah ke
> `artist_repo.py`/`genre_repo.py`, karena God File Threshold).

**Status: selesai end-to-end.** Backend (522 unit test lulus) dan frontend
(§Frontend JS/CSS di atas) sudah terhubung penuh.

| Layer | File | Isi |
|---|---|---|
| Query | `persistence/discover_enrich.py` | `enrich_artists()` — batch cover+genre, no N+1 |
| Query | `persistence/discover_repo.py` | `DiscoverRepository`: `get_bandit_ranked_artists`, `get_unheard_artists`, `get_taste_spectrum`, `get_top_genre`, `get_genre_artists_enriched`, `get_artist_detail` |
| Facade | `persistence/__init__.py` | Delegasi 6 method di atas ke `self._discover` |
| Service | `services/discover_service.py` | Wrapper: `get_for_you`, `get_unheard`, `get_genre_affinity`, `get_taste_spectrum`, `get_artist_detail` |
| WS | `server/handlers/ws_discovery.py` | Action `discover` kirim `for_you`, `unheard`, `genre_affinity_genre`, `genre_affinity_artists`, `taste_spectrum`; action `get_artist_detail` |
| WS router | `server/handlers/websocket.py` | `"get_artist_detail"` ada di `DISCOVERY_CMDS` (izin eksplisit diberikan, `PATCH-2026-07-17-071`) — **blocker lama sudah tidak ada**, action ini reachable end-to-end |
| Store | `web/static/js/store.js` | Default untuk 5 field personalisasi baru |
| WS client | `web/static/js/ws.js` | `discover_data` menyimpan 5 field baru + panggil `renderDiscoverPersonalization()`; `artist_detail` case baru |
| DOM | `web/static/js/dom.js` | Elemen taste bar, filter bar, 3 card-row, artist detail sheet |
| Render | `web/static/js/render/discover-personalize.js` (baru, 185 baris) | Taste bar + fallback, filter kategori/dekade client-side, kartu artis + badge, sheet detail artis, role-gate tombol "Putar Semua" |
| Style | `web/static/css/components/discover-cards.css` (baru) | Semua komponen visual personalisasi + genre palette kurasi |
| Markup | `web/static/index.html` | Section taste spectrum/filter bar/3 card-row + `#artist-detail-sheet` (reuse `.settings-sheet`) |

**Belum ditest manual di browser sungguhan** (lingkungan sesi ini tidak
punya akses jaringan/display) — checklist manual dari
`discover-tab-frontend-handoff.md` §5 masih perlu dijalankan oleh
developer: user baru (histori kosong), bandit belum pernah update, filter
sampai hasil 0, role non-admin, tap kartu → sheet, refresh halaman.
