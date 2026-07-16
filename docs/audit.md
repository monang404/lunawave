---
title: LunaWave Full Codebase Audit
last_verified: 2026-07-16
---

# LunaWave — Full Codebase Audit
**Tanggal:** 2026-07-16
**Baseline sebelum audit:** 467 test passed, doctor.py 100/100 (5 checker), ruff bersih.
**Hasil akhir setelah fix:** 472 test passed, doctor.py 100/100, ruff bersih.

---

## 1. Temuan berdasarkan severity

| # | Severity | File:Line | Bug | Status | Fix |
|---|---|---|---|---|---|
| 1 | **Critical** | `server/connection_manager.py` `broadcast()` | `results` dari `gather()` dipasangkan (`zip`) dengan `list(self.active_connections)` yang di-fetch **ulang** setelah `await` — kalau ada connect/disconnect konkuren di tengah broadcast, index bisa mismatch → send result salah dipasangkan ke ws lain → **client sehat ikut ke-disconnect**. | **CONFIRMED** (repro manual + test, gagal 3/3 di kode lama) | Pin satu snapshot list, dipakai ulang untuk `gather()` & `zip()` |
| 2 | **Critical** | `launcher/gui/auth_panel.py` | Kontrak file `cache/admin_password.txt` tidak sinkron dengan `config.py`: launcher nulis password yang **sudah di-hash**, `config.py` baca isi file sebagai plaintext lalu hash sendiri → password yang ditampilkan ke user tidak pernah valid → admin lockout total. | **CONFIRMED** (repro eksekusi: `verify_password()` selalu `False`) | Tulis raw password ke file |
| 3 | **Medium** | `launcher/gui/app.py`, `controller.py` | Semua callback background-thread (dep checker, refresh loop 2s, log writer, restart timer, popup ready) pakai `self.after()` tanpa guard → crash `RuntimeError: main thread is not in main loop` kalau window sudah ditutup. | **CONFIRMED** (repro via Xvfb headless + `threading.excepthook`) | Flag `_closing` + helper `_safe_after()` |
| 4 | **Medium** | `automation/patchlog.py` `parse_entries()` | Regex gagal mem-parse `docs/PATCHLOG.md` yang sudah ada (0 dari 63+ entri terbaca) → `patchlog.py add` salah nomor ID jadi `-001` dan menimpa `total_entries`. File sempat tertimpa saat sesi audit sebelumnya, sudah dipulihkan dari arsip asli. | **SUSPECTED** (root cause regex belum ditelusuri detail) | **Belum di-fix** — jangan pakai `patchlog.py add`, edit manual |
| 5 | **Low** | `launcher/gui/controller.py` `on_kill_conflict` | Baca `self._conflict_pid` dari `ServerController`, padahal di-set di `ServerManager` → selalu `None`, fallback re-fetch PID (dead code, bukan bug fungsional nyata). | **CONFIRMED** (dead code, dampak fungsional nihil) | Belum di-fix (prioritas rendah) |
| 6 | **Low/Note** | Banyak titik (`controller.py`, `track_loader.py`, `download_manager.py`, `event_listeners.py`, dll.) | Return value `safe_create_task()` sering dibuang (fire-and-forget) — pola yang secara umum dianggap berisiko GC dini di dokumentasi asyncio. | **SUSPECTED** (tidak berhasil direproduksi — CPython menahan referensi task via event loop internal + `add_done_callback`, jadi task tidak hilang dalam praktiknya) | Tidak di-fix, dicatat sebagai architecture smell saja |

---

## 2. Module yang berhasil diaudit (breadth scan + deep-dive, tidak berhenti di bug pertama)
`core/event_bus.py`, `core/task_utils.py`, `core/command_bus.py` (via test suite), `persistence/db.py`, `persistence/track_repo.py` (commit pattern), `engine/sleep_timer.py`, `engine/radio/prefetcher.py` (lock ordering standby_lock/fetch_lock — tidak ada ABBA deadlock), `engine/loudness/analyzer.py` (subprocess, shell=False, aman), `adapters/ytdlp/downloader.py` (path traversal via video_id — sudah disanitasi aman), `server/handlers/websocket.py`, `server/handlers/http.py` (path traversal + SSRF di `serve_stream` — sudah aman), `server/connection_manager.py` (bug #1 di atas), `server/handlers/auth.py` (rate-limit, PBKDF2 di executor — sekilas aman, lihat scope belum tuntas di bawah), seluruh `launcher/` (bug #2, #3, #5 di atas). Scan menyeluruh (grep) untuk pola: SQL string-interpolation (nihil — semua parameterized), `eval`/`exec`/`pickle`/`os.system` (nihil), bare `except:` (2 titik, keduanya benign/teardown), `asyncio.create_task` fire-and-forget (lihat #6).

## 3. Module yang belum sempat diaudit mendalam
- `web/static/js/**` (frontend) — hanya diverifikasi lewat catatan sesi lalu (duplicate listener sudah di-fix), tidak di-scan ulang baris-per-baris sesi ini
- `plugins/lyrics_fetcher.py`, `plugins/notifications.py` — hanya spot-check konvensi, tidak deep-dive ulang
- `engine/mpv_controller.py`, `adapters/mpv/observer.py`, `adapters/mpv/ipc.py`, `adapters/mpv/connection.py` — hanya dicek untuk pola lock, belum full state-machine review
- `data/export_to_sqlite.py`, `persistence/artist_repo.py`, `persistence/library_repo.py` — belum di-review sesi ini
- `automation/*.py` lainnya (`architecture_lint.py`, `event_graph.py`, `hotspot.py`, `impact.py`, `call_graph.py`, `test_locator.py`, `context_pack.py`) — belum diaudit, hanya `patchlog.py` yang ketahuan bermasalah (temuan #4)
- Security audit mendalam (session/cookie flags, CSRF, dependency CVE scan via `pip-audit`/`bandit` yang sudah ada di `requirements-dev.txt` tapi belum dijalankan sesi ini)

## 4. Area yang butuh audit lanjutan (prioritas)
1. Root-cause `automation/patchlog.py` (temuan #4) — risiko data-loss di tooling sendiri
2. `adapters/mpv/*` — state machine reconnect & observer loop, belum direview detail sesi ini
3. Jalankan `bandit` dan `pip-audit` (sudah ada di dev deps, belum pernah dieksekusi menurut riwayat yang bisa diverifikasi)
4. Frontend `web/static/js/**` — re-audit menyeluruh (bukan cuma percaya catatan sesi lalu)
5. `persistence/artist_repo.py`, `library_repo.py`, `data/export_to_sqlite.py`

## 5. Estimasi keyakinan codebase "bersih"
**Sedang (bukan tinggi).** Test suite + doctor + ruff hijau, dan bug tersembunyi paling berbahaya sesi ini (race condition broadcast) sudah confirmed & fixed dengan reproduksi nyata — itu alasan naik dari "rendah". Tapi scope yang di-cover sesi ini adalah breadth scan + deep-dive pada area berisiko tinggi yang bisa dijangkau dalam satu sesi, **bukan** audit baris-per-baris untuk 30 kategori bug × seluruh 136 file source. Area di §3 dan §4 (terutama adapters/mpv/*, frontend JS, dan automation/*.py lain) belum dapat perlakuan yang sama tingkat kedalamannya, jadi klaim "bersih total" belum bisa dibuat jujur.
