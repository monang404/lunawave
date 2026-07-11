---
title: LunaWave — Implementation Plan (Bug Batch 2026-07-11)
based_on: BUG_INVENTORY (18 bug unik, dari 13 dokumen PATCH_*.md)
sprint: 3.2 → 3.3
status: READY UNTUK APPLY
---

# IMPLEMENTATION_PLAN.md

> **AI pelaksana: baca ini SAJA sebagai entry point.** Kamu tidak perlu baca
> ulang 13 file `PATCH_*.md` dari awal — dokumen ini sudah merangkum,
> menghapus duplikat, dan menentukan urutan eksekusi. Diff lengkap tetap ada
> di file sumber; kamu cukup buka bagian yang dirujuk saat mengerjakan task
> itu (jangan buka semuanya sekaligus di awal, boros token).

## Sebelum mulai (wajib, sekali saja)

```bash
python scripts/run_all.py --check   # baseline: cuma jalankan checks (verify_docs, architecture_lint, doctor), TANPA generate — belum ada perubahan kode
```

Simpan hasilnya untuk dibandingkan dengan run terakhir di penutup dokumen ini.

Jangan jalankan `find_owner.py` per-task di bawah — semua lokasi file
sudah dipastikan benar di tabel tiap batch. Pakai `find_owner.py <nama>`
hanya kalau ada isi file yang tidak cocok dengan snippet "Cari:" di dokumen
sumber (tanda kode sudah berubah sejak dokumen ditulis).

## Aturan main batch ini

1. **Satu batch = satu file (atau grup file yang wajib diubah bareng).** Buka file itu sekali, terapkan semua task di batch itu sekaligus, baru pindah ke file berikutnya. Ini menghindari kamu bolak-balik ke file yang sama di task terpisah.
2. **Diff persis ada di dokumen sumber yang dirujuk** — kolom "Ambil diff dari" menunjuk ke bagian yang tepat. Salin `Cari:` / `Ganti dengan:` dari sana apa adanya, jangan menulis ulang dari nol.
3. Kalau ada 2 dokumen sumber untuk 1 bug (duplikat), kolom "Ambil diff dari" sudah memilih **satu versi kanonis** — abaikan versi satunya, jangan diterapkan dua kali.
4. Setelah **setiap batch** (bukan setiap task individual): jalankan test batch itu → kalau pass, append **satu** entri `PATCHLOG.md` untuk seluruh batch (bukan per-bug) → lanjut batch berikutnya.
5. Di akhir **semua** batch: `python scripts/doctor.py` lagi, `generate_file_index.py` kalau ada fungsi baru, update `STATUS.md` untuk file yang berubah kondisinya.
6. File `server/handlers/websocket.py` **restricted** (lihat `AI_CONTEXT.md`) — izin eksplisit sudah diberikan user 2026-07-11 (referensi: `PATCH_DISCOVER_PARALLEL_QUERIES.md`, `PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md`). Tetap kerjakan sebagai **satu pass gabungan** (Batch 9) supaya file sensitif ini hanya disentuh sekali.

---

## Ringkasan urutan (12 batch)

| # | Batch | File | Risiko | Prioritas |
|---|-------|------|--------|-----------|
| 1 | yt-dlp client | `engine/ytdlp_client.py` | Rendah | Tinggi |
| 2 | Auth non-blocking | `server/handlers/auth.py` | Rendah | Tinggi |
| 3 | main.py housekeeping | `main.py` | Rendah | Tinggi/Sedang |
| 4 | mpv controller | `engine/mpv_controller.py` | Rendah | Sedang |
| 5 | Lyrics plugin | `plugins/lyrics.py` | Rendah | Sedang |
| 6 | Track loader | `engine/playback/track_loader.py` | Rendah | Tinggi |
| 7 | Event listeners | `server/handlers/event_listeners.py` | Rendah | Sedang |
| 8 | DB index | `cache/schema.sql`, `cache/db.py` | Sangat rendah | Minor |
| 9 | **websocket.py + controller.py (gabungan, restricted)** | `server/handlers/websocket.py`, `engine/playback/controller.py` | Sedang | Tinggi |
| 10 | Serializers lirik (DECISION) | `server/serializers.py`, `broadcast_service.py` | Sedang | Sedang |
| 11 | OTel tracing (DECISION, opsional) | `core/command_bus.py`, `core/observability.py` | Rendah, confidence belum diukur | Sedang/opsional |
| 12 | Startup script cleanup | `start.sh`, `start.bat` | Sangat rendah | Housekeeping |

---

## BATCH 1 — `engine/ytdlp_client.py`

| Task | Ambil diff dari | Isi singkat |
|---|---|---|
| Lazy import `yt_dlp` | `PATCH_STARTUP_SPEED.md` § TASK 3 | Pindah `import yt_dlp` top-level → lazy import di `_extract_sync` & `_download_sync` |
| `socket_timeout` + `extractor_retries` | `PATCH_YTDLP_THREAD_STARVATION.md` § Diff yang Direncanakan | Tambah `"socket_timeout": 10, "extractor_retries": 1` ke `_YDL_OPTS_INFO` |

**Test:** `pytest tests/ -x -q`. Manual: search/play tetap jalan (boleh ~1 detik lebih lambat di request pertama). Throttle jaringan lambat → request gagal ≤20 detik, bukan menggantung lama.

---

## BATCH 2 — `server/handlers/auth.py`

| Task | Ambil diff dari |
|---|---|
| `verify_password()` jangan blokir event loop (PBKDF2 100k iter → `run_in_executor`) | `PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md` § TASK 2 |

**Test:** login benar/salah normal, rate-limit tetap di percobaan ke-6. Manual dampak nyata: play musik di 1 client, login (boleh salah) di client lain → progress bar client pertama tidak boleh stutter.

Ini fix **confidence tinggi** (sudah dibenchmark ~58ms di dokumen sumber) — prioritaskan, jangan gabung dengan Batch 11 (OTel) yang confidence-nya belum terukur.

---

## BATCH 3 — `main.py`

Tiga task di file yang sama — kerjakan sekali jalan:

| Task | Ambil diff dari |
|---|---|
| Interval poller: `mpv_reconnect_checker` 5s→30s, `check_connectivity` 60s→300s | `PATCH_BATTERY_DRAIN.md` § TASK 4 |
| Jadwalkan `db_maintenance()` (evict_stale_tracks + cleanup_sessions, tiap 6 jam) | `PATCH_DB_MAINTENANCE_SCHEDULER.md` § Diff yang Direncanakan |
| Paralelkan `db.init()` + `mpv.connect()` via `asyncio.gather` | `PATCH_STARTUP_SPEED.md` § TASK 4 |

⚠️ **Cek dulu sebelum apply task `db_maintenance`:** buka `cache/db.py`, cari `evict_stale_tracks()` — pastikan query-nya **tidak** lagi mereferensikan kolom `is_favorite` (fitur favorit sudah dihapus dari project). Kalau kolom itu masih dipakai di `WHERE`, hapus klausanya dulu sebelum menjadwalkan task ini, atau query akan error saat runtime. (Sumber catatan: `PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md`)

Gabungkan ketiga perubahan jadi satu blok inisialisasi yang konsisten (jangan biarkan urutan `db.init()` berubah jadi setelah service lain yang butuh `db`).

**Test:** `time python main.py` → startup <5s desktop / <10s Termux. `pytest tests/ -x -q`. Manual: biarkan app jalan >6 jam sekali (atau panggil `db_maintenance()` manual) → cek `sessions`/`tracks` stale terhapus.

---

## BATCH 4 — `engine/mpv_controller.py`

| Task | Ambil diff dari |
|---|---|
| Throttle publish `TrackProgressEvent` ke 1×/detik | `PATCH_BATTERY_DRAIN.md` § TASK 1 |
| Paralelkan 3× `observe_property` saat connect | `PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md` § TASK 4 |

**Test:** `pytest`. Manual: play lagu, lirik tetap sync (delay ≤1 detik, tidak terasa), progress bar UI update ~1×/detik. Connect mpv → progress/pause-state/duration semua tetap masuk normal.

---

## BATCH 5 — `plugins/lyrics.py`

| Task | Ambil diff dari |
|---|---|
| Throttle `LyricsUpdatedEvent` (min 0.5 detik antar broadcast) | `PATCH_BATTERY_DRAIN.md` § TASK 3 |
| Lazy import `syncedlyrics` | `PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md` § TASK 2 |

**Test:** `pytest`. Manual: paksa lrclib gagal → fallback syncedlyrics tetap jalan.

---

## BATCH 6 — `engine/playback/track_loader.py`

| Task | Ambil diff dari |
|---|---|
| `increment_play_count` jadi `safe_create_task` (non-blocking) | `PATCH_PLAYCOUNT_NONBLOCKING.md` § Diff yang Direncanakan |

**Test:** `pytest`. Manual: ganti lagu cepat berkali-kali → play_count tetap bertambah benar (cek via Discover), tidak ada jeda tambahan saat mulai putar.

---

## BATCH 7 — `server/handlers/event_listeners.py`

| Task | Ambil diff dari |
|---|---|
| Hapus throttle redundant di `_on_track_progress` (sudah ditangani di Batch 4) | `PATCH_BATTERY_DRAIN.md` § TASK 2 |
| Paralelkan query Discover di `_on_download_complete` | `PATCH_DISCOVER_PARALLEL_QUERIES.md` § `event_listeners.py`, ATAU `PATCH_PLAYCOUNT_LAZYIMPORT_DISCOVER.md` § TASK 3a (isi identik, pakai salah satu saja) |

**Catatan realistis dari dokumen sumber:** `cache/db.py` pakai satu koneksi `aiosqlite` (satu worker thread) — jadi `asyncio.gather` di sini **tidak mempercepat eksekusi query di level DB**, cuma mengurangi overhead scheduling event-loop antar-`await` (sub-milidetik). Tetap aman diterapkan (low-risk, no downside), tapi jangan ekspektasi ini terasa signifikan.

**Test:** `pytest`. Manual: selesai download → data Discover tetap lengkap dan benar.

---

## BATCH 8 — `cache/schema.sql` + `cache/db.py`

| Task | Ambil diff dari |
|---|---|
| Index `idx_songs_artist_id` | `PATCH_SONGS_ARTIST_ID_INDEX.md` § Rencana Fix |

**Catatan realistis:** pada ukuran data saat ini (963 baris `songs`) dampaknya <1ms — murni pencegahan untuk pertumbuhan data ke depan. Boleh dikerjakan kapan saja, tidak mendesak.

**Test:** tidak ada test fungsional wajib — index bersifat additive, tidak mengubah behavior.

---

## BATCH 9 — `server/handlers/websocket.py` + `engine/playback/controller.py` (RESTRICTED, satu pass gabungan)

File `websocket.py` ditandai restricted di `AI_CONTEXT.md`. Karena **3 task berbeda** sama-sama butuh menyentuhnya, kerjakan sekaligus dalam satu review — jangan buka/edit file ini 3× terpisah.

| Task | File | Ambil diff dari |
|---|---|---|
| `toggle_pause()` jadi fire-and-forget (`safe_create_task`, bukan `await`) | `engine/playback/controller.py` | `PATCH_PAUSE_DELAY.md` § FILE 1 (atau `PATCH_STARTUP_SPEED.md` § TASK 5, isi identik — pakai salah satu) |
| `ConnectionManager.broadcast()` paralel ke semua WS client | `server/handlers/websocket.py` | `PATCH_PAUSE_DELAY.md` § FILE 2 (atau `PATCH_STARTUP_SPEED.md` § TASK 6, isi identik — pakai salah satu) |
| Paralelkan query Discover di action `discover` & `delete_download` | `server/handlers/websocket.py` | `PATCH_DISCOVER_PARALLEL_QUERIES.md` § `websocket.py` (dua blok diff-nya) |

Pastikan `import asyncio` ada di module level `websocket.py` (dipakai oleh 2 dari 3 task di atas) — cek sekali di awal batch ini, jangan cek berulang per task.

**Test:** `pytest`. Manual: play → pause → UI update instan tanpa jeda. Buka 2+ koneksi WS (HP+PC) → broadcast tetap sampai semua client. Buka tab Discover → data tetap lengkap, terasa tidak lebih lambat.

---

## BATCH 10 — Payload lirik dobel di `state` broadcast (DECISION WAJIB SEBELUM CODING)

Dua dokumen sumber punya bug yang sama tapi **solusi berbeda** — pilih **Variant A**:

- **Variant A (dipilih — lebih rendah risiko regresi):** `PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md` § TASK 2. Tambah parameter `include_lyrics: bool` di `state_to_dict()` (default `True`) dan `broadcast_state()` (default `False`). Initial snapshot di `websocket.py` tetap pakai `include_lyrics=True` — tidak butuh perubahan tambahan di alur connect.
- ~~Variant B~~ (`PATCH_STATE_LYRICS_DEDUP.md`) — **jangan dipakai**: menghapus field lirik total dari `state_to_dict()` lebih hemat payload tapi butuh mitigasi tambahan (kirim message `"lyrics"` terpisah setelah initial snapshot) supaya tidak ada jeda lirik kosong saat client baru connect — mitigasi ini di luar scope minimal dan menambah 1 titik perubahan lagi di `websocket.py` yang sudah cukup ramai di Batch 9.

| File | Ambil diff dari |
|---|---|
| `server/serializers.py` | `PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md` § 2a |
| `server/services/broadcast_service.py` | `PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md` § 2b |
| `server/handlers/websocket.py` (initial snapshot, `include_lyrics=True`) | `PATCH_DB_MAINTENANCE_LYRICS_PAYLOAD.md` § 2c |

⚠️ Baris terakhir menyentuh `websocket.py` lagi — kalau memungkinkan, gabungkan pengerjaan ini ke **Batch 9** sekalian (masih file restricted yang sama) supaya file itu betul-betul cuma dibuka sekali di seluruh sesi. Urutan di sini (Batch 10 terpisah) hanya karena butuh keputusan Variant A/B dulu.

Sebelum apply: `grep -rn "state_to_dict(\|broadcast_state(" --include="*.py" .` — pastikan tidak ada pemanggil lain yang butuh `include_lyrics=True` selain initial snapshot.

**Test:** refresh browser mid-lagu (lirik aktif) → lirik tetap langsung muncul dari initial snapshot. Update queue/selesai download → payload WS `"state"` (cek DevTools Network) tidak lagi bawa `lyrics_lines`/`lyrics_timestamps`.

---

## BATCH 11 — OTel span overhead (DECISION, opsional/lower confidence)

Dokumen sumber sendiri (`PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md` § TASK 1) eksplisit bilang magnitude dampaknya **belum diukur** di device asli (beda dari Batch 2/Auth yang sudah dibenchmark). Pilih salah satu:

- **Opsi A — hapus span sepenuhnya** dari `core/command_bus.py` (rekomendasi untuk fase stabilisasi ini). Diff: `PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md` § OPSI A.
- **Opsi B — future-proof via env var** `LUNAWAVE_ENABLE_TRACING` (`NoOpTracer` default). `core/command_bus.py` tidak perlu disentuh. Diff: `PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md` § OPSI B.

Sebelum apply Opsi A: `grep -rn "tracer\|opentelemetry" .` (termasuk `docs/`) — sesuaikan referensi lain kalau ada.

**Boleh di-skip / ditunda** batch ini kalau prioritas token/waktu terbatas — bukan bug fungsional, murni dead-weight cleanup.

**Test:** `pytest`. Manual: semua command dasar (play/pause/next/prev/seek/volume/queue) tetap jalan tanpa `AttributeError`. `/metrics` (Prometheus) tetap muncul & increment normal.

---

## BATCH 12 — `start.sh` + `start.bat` (housekeeping, boleh dikerjakan kapan saja)

| Task | Ambil diff dari |
|---|---|
| Gabung 7× subprocess dep-check jadi 1×, hapus `sleep`/`ping` artifisial | `PATCH_STARTUP_SPEED.md` § TASK 1 (`start.sh`) & § TASK 2 (`start.bat`) |

Tidak menyentuh kode Python — risiko sangat rendah, tidak butuh `pytest`. Test: jalankan `start.sh`/`start.bat` manual, pastikan pesan dep-check & startup normal.

---

## Setelah SEMUA batch selesai

```bash
python scripts/run_all.py           # generate_file_index + generate_report + doctor, satu command
```

Ini otomatis meng-update `FILE_INDEX.md` (kalau ada fungsi/class baru, mis. `db_maintenance`, `_init_mpv`) dan statistik `REPORT.md`, lalu jalankan health check penuh. Bandingkan output `doctor` di dalamnya dengan baseline `run_all.py --check` di awal — harus sama atau lebih baik, tidak ada FAIL baru. Kalau tidak ada file baru/dihapus dan tidak ada fungsi baru, generator tetap aman dijalankan (idempotent, cuma nulis ulang blok `BEGIN:GENERATED`).

Lalu update `docs/STATUS.md` untuk baris `engine/mpv_controller.py` dan `server/handlers/websocket.py` kalau kondisinya berubah signifikan (keduanya sudah tercatat "Sprint 4 — Belum" untuk refactor lain; batch ini tidak mengubah rencana refactor itu, cuma bugfix, jadi kemungkinan STATUS.md tidak perlu diubah — cek isinya dulu sebelum menyimpulkan tidak perlu).

Append **satu entri PATCHLOG per batch** (bukan per bug), format:

```markdown
## [YYYY-MM-DD] Patch — <Nama Batch>

**ID:** `PATCH-YYYY-MM-DD-0NN`
**Tanggal:** YYYY-MM-DD
**Ringkasan:** <1-2 kalimat>
**File Terdampak:**
- `path/file.py` — <ringkas perubahan>
**Alasan:** <kenapa>
**Status:** ✅ SELESAI
```

Lanjutkan nomor `NNN` dari `latest_patch_id` di frontmatter `PATCHLOG.md` (saat ini `PATCH-2026-07-11-009` → batch pertama yang di-apply jadi `-010`, dst — urut sesuai urutan batch yang benar-benar dikerjakan, bukan nomor batch di dokumen ini).

## Yang SENGAJA tidak dimasukkan ke plan ini

- Task 4 di `PATCH_STARTUP_SPEED.md` (paralel observe_property) — sudah masuk Batch 4 dari sumber lain, jangan diterapkan dua kali.
- `BUG_LEDGER.md` yang direferensikan di akhir `PATCH_TRACING_OVERHEAD_AUTH_BLOCKING.md` — file ini **tidak ada** di repo saat ini (dicek langsung), kemungkinan rencana dokumen yang belum direalisasikan. Jangan buat file baru untuk ini kecuali diminta eksplisit — di luar scope batch bugfix ini.
