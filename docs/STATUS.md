---
title : LunaWave Project Status
last_verified: 2026-07-21
sprint: Phase 8 (selesai) + Tier 2 (T10-T16) + Hardening (implementation-plan.md Batch 0-4.2)
---

# STATUS.md — Kondisi File per Sprint

> Tabel ini adalah satu-satunya source of truth untuk "sudah sampai mana?"
> Update setiap sprint selesai.

## Status Fitur (dari `task_breakdown_agent.yaml`)

| Fitur | Status | Waktu Selesai | Ringkasan |
|---|---|---|---|
| Fitur A — `quick_search_discover` | ✅ Done | 17 Jul 2026 | Personalisasi tab Discover (bandit ranking, taste spectrum, filter). Detail: §Discover Tab Personalization di bawah. |
| Fitur B — `login_redesign` | ✅ Done | 19 Jul 2026 | Kredensial admin dipindah ke SQLite. Launcher auth via web. Keputusan lengkap: [ADR-0008](adr/0008-admin-credentials-in-sqlite.md). |
| Fitur C — `radio_toggle_redesign` | ✅ Done | 20 Jul 2026 | UI "Night Dial" (moon-phase, starfield). Animasi rAF terisolasi dengan fallback statis. Sisa *tech debt* dibersihkan. |

Kedua fitur sumber (`meta.source_features` / `meta.completed_features` di
`task_breakdown_agent.yaml`) sekarang sama-sama selesai dan diverifikasi.

**Catatan Khusus Fitur C (Night Dial):**
- **Bug Ditemukan (belum di-fix):** Starfield overflow di viewport 320px/360px & landscape pendek. Keputusan 322px final, tidak dibuka ulang saat ini (perlu task lanjutan terpisah).
- Evaluasi testing lengkap dapat dilihat pada `PATCH-2026-07-20-130` dan pembersihan di `PATCH-2026-07-20-131`.

## Backend Python

| File | Kondisi Aktual | Kondisi Target | Sprint Target | Status |
|------|---------------|----------------|---------------|--------|
| `cache/db.py` | 🗑️ Dihapus (T2.1, `PATCH-2026-07-18-079`) — semua konsumen sudah pindah ke `persistence` | Pecah → `persistence/track_repo.py` dll | Sprint 4 (T1.2 selesai: `main.py` sudah import langsung dari `persistence`, siap untuk T2.1 hapus alias) | ✅ Done |
| `persistence/stream_cache.py` | ✅ Hasil merge dari `cache/resolver.py` (T2.6, `PATCH-2026-07-18-087`). Folder `cache/` (paket Python) dibubarkan — `cache/pb_html.txt` (template statis, tidak ada referensi aktif) pindah ke `data/pb_html.txt`; `cache/mp3/`, `cache/sockets/`, `cache/admin_password.txt` tetap di tempat karena runtime artifact yang sudah di-gitignore, di luar cakupan T2.6. | Sudah sesuai target | — | ✅ Done |
| `engine/mpv_controller.py` | 🗑️ Dihapus (T2.1, `PATCH-2026-07-18-079`) — semua konsumen sudah pindah ke `adapters.mpv` | Pindah ke `adapters/mpv/` | Sprint 4 (T1.2 selesai: `main.py` sudah import langsung dari `adapters.mpv`, siap untuk T2.1 hapus alias) | ✅ Done |
| `engine/ytdlp_client.py` | 🗑️ Dihapus (T2.1, `PATCH-2026-07-18-079`) — semua konsumen sudah pindah ke `adapters.ytdlp` | Pindah ke `adapters/ytdlp/` | Sprint 4 (T1.2 selesai: `main.py` sudah import langsung dari `adapters.ytdlp`, siap untuk T2.1 hapus alias) | ✅ Done |
| `server/handlers/websocket.py` | Monolith **355 baris** (naik dari 354). Izin eksplisit **diberikan** user pada `PATCH-2026-07-17-071` untuk perubahan 1 baris (`"get_artist_detail"` ditambahkan ke `DISCOVERY_CMDS`) — action itu kini reachable dari client, lihat §Discover Tab Personalization di bawah. | Pisah `ConnectionManager` ke file sendiri | Sprint 4 | ❄️ Frozen (v1.0.0 Baseline) |
| `persistence/discover_repo.py` | **Baru**, `PATCH-2026-07-17-070`. 242 baris — zona Waspada (>150), belum "wajib pecah" (<300). Kalau nanti nambah section baru, pertimbangkan pecah per-jenis query (`bandit.py` / `taste.py`) sebelum lewat 300. | 1 file = query personalisasi Discover | — | 🆕 Baru, siap dipakai backend |
| `persistence/discover_enrich.py` | **Baru**, `PATCH-2026-07-17-070`. 78 baris — aman. | Helper cover+genre batch, dipakai `discover_repo.py` | — | 🆕 Baru, siap dipakai backend |
| `config.py` | ✅ Sudah dipisah ke `config_security.py` | Pisah ke `config_security.py` | Sprint 4 | ✅ Done |
| `core/command_bus.py` | ✅ Sudah dipisah ke `core/commands.py` | Pisah CMD ke `core/commands.py` | Sprint 4 | ✅ Done |
| `bootstrap/` (`services.py`, `startup_tasks.py`, `maintenance.py`) | **Baru**, `PATCH-2026-07-18-086`. `main.py`'s God Function `main()` dipecah jadi 3 stage: `init_core_services()` (DB/MPV/ytdlp/HTTP session + semua domain service), `run_startup_checks()` (connectivity check, MPV initial connect, resume last track), `schedule_db_maintenance()`/`start_mpv_watchdog()` (periodic upkeep). State dibagi lewat `BootstrapContext` singleton di `bootstrap.services.context`. `main.py` sekarang hanya orkestrasi 4 langkah + `run_server()` (create app/banner/serve/shutdown-cleanup, tetap di `main.py` karena memegang lifecycle penuh). | 1 modul = 1 stage bootstrap, `main()` jadi orkestrasi tipis | — | 🆕 Baru, hasil pemecahan main.py |
| `engine/playback/controller.py` | 433 baris (turun dari 464). T2.3 selesai: method `_on_queue_*`/`_advance_to_next` diekstrak ke `queue_controller.py`, method `_on_set_mode`/`_on_set_output`/`_on_set_sponsorblock`/`_on_set_loudness_normalization`/`_on_radio_randomize`/`_on_lyrics_offset` diekstrak ke `settings_controller.py`; `controller.py` sekarang hanya menyimpan method transport (play/pause/next/prev/stop/seek) + delegasi tipis ke kedua sub-controller (`PATCH-2026-07-18-085`) | ✅ Dipecah, lihat PATCH-2026-07-18-085 (`queue_controller.py` + `settings_controller.py`) | Sprint 4 | ✅ Done (izin eksplisit roadmap §2.3, tanda ❄️ Frozen dicabut untuk item ini) |
| `launcher/` | ✅ Sudah refactor Sprint 3.2. ServerLifecycle diekstrak, testable headless, lihat PATCH-2026-07-18-092 | Sudah sesuai target | — | ✅ Done |
| `start.py` | ✅ Hollow re-export | Sudah sesuai target | — | ✅ Done |
| `server/broadcast_service.py` | ✅ Hasil pindah dari `server/services/broadcast_service.py` (T2.7, `PATCH-2026-07-18-090`). **Tetap di `server/`, bukan `services/`** — deviasi sengaja dari rencana awal karena file ini impor `server.connection_manager`/`server.serializers` (web/wire layer), lihat `docs/backend/services.md`. | Sudah sesuai target (deviasi terdokumentasi) | — | ✅ Done |
| `services/stream_prefetch.py` | ✅ Hasil pindah dari `server/services/stream_prefetch.py` (T2.7, `PATCH-2026-07-18-090`). `server/services/` (folder) dihapus. | Sudah sesuai target | — | ✅ Done |
| `.importlinter` | ✅ Bug syntax diperbaiki (T2.7 side-fix, `PATCH-2026-07-18-089`): `forbidden_modules`/`source_modules` koma-satu-baris tidak pernah ter-parse benar oleh import-linter (6 dari 7 kontrak silently no-op sejak dibuat). Sudah diperbaiki jadi format list per-baris; `lint-imports` sekarang benar-benar memverifikasi boundary. | Sudah sesuai target | — | ✅ Done |

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
| `data/artists_enriched.json` | 185KB JSON statis (100 artis) | Import ke tabel DB | Sprint 5 | ❄️ Frozen (v1.0.0 Baseline) |
| `data/artists_enriched1.json` | 1.5MB JSON statis (854 artis) — **BUKAN duplikat** `artists_enriched.json` (dicek T3.5, `diff` menunjukkan `total: 100` vs `total: 854`, konten artis berbeda substantif, bukan cuma reformat). Tidak dihapus. Butuh keputusan pemilik project: apakah ini superset data yang seharusnya menggantikan `artists_enriched.json`, dataset staging terpisah, atau sisa eksperimen yang perlu diberi nama lebih jelas. | Perlu klarifikasi pemilik sebelum diputuskan tetap/hapus/rename | — | ⚠️ Butuh keputusan pemilik (T3.5) |
| `data/export_to_sqlite.py` | Di `data/` (dikonfirmasi ulang T3.5: sempat dipindah ke `scripts/export_to_sqlite.py` di `PATCH-2026-07-13-029`, lalu balik lagi ke `data/` sebelum `PATCH-2026-07-17-072` merename `scripts/`→`automation/`; state fisik repo saat ini sepakat dengan baris ini: tetap di `data/`) | Tetap di `data/` (rencana TASK_BREAKDOWN.md untuk pindah ke `automation/` tidak dieksekusi karena kontradiksi dengan state riil yang sudah ✅ Selesai) | Sprint 3.3 | ✅ Selesai (dipertahankan di `data/`, T3.5) |
| `cache/admin_password.txt` | ✅ Sudah tidak ada di repo, sudah di `.gitignore` (terverifikasi 2026-07-13) | Di .gitignore | — | ✅ Done |
| `launcher/instance/admin_password.txt` (dulu `launcher/cache/admin_password.txt`, TIDAK ter-gitignore) | ✅ Dipindah ke `instance/`, di `.gitignore` (T1.1, PATCH-2026-07-18-077) | Di .gitignore | Fase 1 | ✅ Done |

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
| Facade | `persistence/__init__.py` | ✅ God Facade `Database` **dihapus** (T2.2e, `PATCH-2026-07-18-084`) — diganti `Repositories`, container tipis 1 koneksi + 6 repo domain tanpa method delegasi. Konsumen inject repo yang relevan langsung (`repos.tracks`, `repos.discover`, dst). |
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

## Baseline Fase 0 (2026-07-18)

Dijalankan di branch `refactor/roadmap` (dibuat dari `develop`) sebagai titik
acuan sebelum roadmap refactor T1–T4 dimulai. Setiap task refactor berikutnya
wajib mempertahankan angka `passed` ini atau lebih tinggi, dan wajib menjaga
`0 broken` pada import-linter.

- **T0.1 — Branch dasar:** `refactor/roadmap` dibuat dari `develop`.
  Catatan lingkungan: zip export yang digunakan tidak menyertakan histori
  git (`.git` tidak ada), sehingga repo di-`git init` ulang dengan commit
  awal tunggal di `develop` sebelum branch ini dibuat. Perintah
  `git log --all --full-history` untuk file apapun (termasuk
  `launcher/cache/admin_password.txt` di T1.1) tidak akan menunjukkan
  histori asli proyek — jalankan T1.1 di clone lokal yang punya history
  sungguhan, bukan hasil zip ini.
- **T0.2 — Baseline test:** `pytest -q` → **558 passed, 1 failed, 6 skipped**
  (35.04s). Kegagalan pre-existing (bukan disebabkan Fase 0):
  `tests/unit/server/handlers/test_ws_playback.py::test_handle_playback_command_other_commands`
  — assertion mock `execute('cmd.prev')` vs actual `execute('cmd.prev', {})`.
  Catatan lingkungan: `tkinter` tidak terpasang secara default di sandbox ini
  dan sempat menyebabkan 3 error collection pada
  `tests/unit/launcher/gui/*`; sudah diperbaiki dengan `apt-get install
  python3-tk` sebelum baseline final di atas diambil.
- **T0.3 — Baseline dependency:** `lint-imports --config .importlinter` →
  **7 kept, 0 broken** (menganalisis 131 file, 371 dependency).
- **T0.4 — Freeze file berisiko:** dicatat, tidak ada perubahan kode. File
  yang di-freeze selama roadmap: `main.py`, `persistence/__init__.py`,
  `engine/playback/controller.py`, `launcher/gui/app.py`.

## T2.2 — Hapus facade `Database` (2026-07-18, selesai)

Dikerjakan sebagai 5 sub-task berurutan (a→b→c→d→e), masing-masing bisa
di-revert independen sampai T2.2e menghapus facade-nya. `persistence/__init__.py`
dan `main.py` disentuh dengan izin eksplisit roadmap ini (keduanya di-freeze
di T0.4 untuk perubahan *lain*, bukan untuk task T2.2 sendiri).

- **T2.2a-d:** ekstraksi `persistence/db.py` (`DatabaseConnection`) +
  migrasi konsumen session/artist/genre/library/discover ke repo masing-masing
  langsung. Lihat `PATCH-2026-07-18-079` s.d. `-083` di `PATCHLOG.md`.
- **T2.2e — Hapus facade `Database`:** `PATCH-2026-07-18-084`. `persistence/__init__.py`
  kini cuma berisi `Repositories` (container 1 koneksi + 6 repo, tanpa method
  delegasi). `main.py` wiring ulang: setiap service dapat repo yang relevan
  langsung, bukan seluruh objek DB. `resolver.db` (dipakai lintas domain oleh
  `PlaybackController`/`TrackLoader`/`track_ended_ops`/`event_listeners`) tetap
  jalan lewat `ResolverDbCompat` (adapter tipis, bukan facade baru — cuma
  menggabungkan `TrackRepository`+`ArtistRepository`+`DiscoverRepository` untuk
  method yang benar-benar dipanggil lewat `resolver.db`).
  - **Hasil test:** 558 passed (sama persis dgn baseline T0.2), 1 failed
    pre-existing (`test_ws_playback`, tidak terkait perubahan ini).
  - **import-linter:** 7 kept, 0 broken (tidak berubah dari baseline).
  - **Baris `persistence/__init__.py`:** 213→109 baris (God Facade
    dengan puluhan method delegasi sudah tidak ada).
