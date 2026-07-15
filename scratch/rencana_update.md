---
title: LunaWave — Rencana Update (Tier 1 & Tier 2)
last_verified: 2026-07-15
sprint: pasca Sprint 3.2 (Batch 8–12) — v1.0.0 Baseline
sumber: docs/OPTIMIZATION_REPORT.md + validasi manual 100-ide-patch v1.x
+ verifikasi ulang line-by-line terhadap source code aktual `lunawave-1.0.1.zip`
  (AI_CONTEXT.md, docs/STATUS.md, docs/PATCHLOG.md, docs/CONSTRAINTS.md,
  docs/testing/*.md, docs/adr/0004, dan file kode terkait) pada 2026-07-15
status: PLANNING — belum ada task yang dieksekusi
---

# rencana_update.md — Breakdown Task Kecil

> Setiap task di bawah didesain **berdiri sendiri** (independen), 1 task = 1
> patch entry di `docs/PATCHLOG.md` (ID mulai `PATCH-2026-07-15-048` — dicek,
> `latest_patch_id` saat ini `PATCH-2026-07-15-047`, jadi 048 benar), sesuai
> batasan `AI_CONTEXT.md`: *"tidak boleh refactor 2 tahap sekaligus dalam 1
> commit"*. Urutan pengerjaan mengikuti urutan task ID (T1 → T16), tapi tiap
> task boleh dikerjakan terpisah di sesi berbeda.

## Cara pakai dokumen ini
- [ ] = belum dikerjakan
- [x] = selesai (checklist manual, bukan auto-generated)
- Kolom **Verifikasi** wajib dijalankan sebelum centang selesai
- Setelah task selesai → prepend entry ke `docs/PATCHLOG.md` + update
  `docs/STATUS.md`## Final Automation & Verification
- [x] Jalankan `python automation/doctor.py` dan pastikan tidak ada `FAIL` baru.
- [x] Jalankan `python generate_file_index.py` (untuk referensi AI di sesi berikutnya).
- [x] Jalankan `python generate_report.py` (update `docs/REPORT.md`).
- [x] Update `docs/PATCHLOG.md` dan `docs/STATUS.md` secara terpusat di akhir.

## Aturan repo tambahan yang wajib diikuti (sering terlupa)

Tiga hal ini ada di `docs/development/coding_standard.md` dan
`docs/testing/testing_strategy.md`, tapi tidak eksplisit disebut di draft
rencana sebelumnya — sekarang ditambahkan ke tiap task yang relevan:

1. **Mirror-path test wajib.** Prinsip #2 repo ini: *"1 file kode (yang
   testable) = 1 file test"*, target coverage **100%** untuk semua file
   testable. Semua file Python yang disentuh Tier 1 & Tier 2 **sudah** punya
   file test mirror (sudah dicek, lihat catatan per task) — artinya edit kode
   tanpa update test yang sesuai akan menurunkan coverage dan melanggar
   prinsip #2. Task frontend (JS) terkecuali untuk file `render/*.js` dan
   `events/*.js` — itu masuk kategori "Manual / e2e smoke" di
   `docs/testing/frontend_testing.md`, jadi verifikasi manual di browser
   sudah cukup, tidak perlu file `*.test.js` baru.
2. **God File Threshold.** File Python >150 baris = "Waspada", >300 baris =
   wajib dipecah (`docs/development/coding_standard.md`). `server/handlers/http.py`
   **sudah 194 baris** — T6, T9, T14 di bawah semua tadinya menumpuk ke file
   ini. T9 sekarang diarahkan ke file baru supaya tidak mendekati ambang 300.
3. **Command baru wajib lewat CommandBus (ADR-0004).** Task yang menambah
   command baru (T10, T11, T13) sebelumnya hanya menyebut `core/commands.py`
   + `engine/command_router.py`-nya kelewat, padahal **wajib** didaftarkan di
   `engine/command_router.py` (consumer tunggal CommandBus) dan dipetakan
   dari WS action masuk di `server/handlers/ws_playback.py` (bukan
   `server/handlers/websocket.py` yang frozen — file ini beda dan **tidak**
   frozen). Tanpa dua langkah ini command tidak akan pernah ke-trigger dari
   frontend. Sudah ditambahkan ke masing-masing task di bawah.

---

## TIER 1 — Backend, zero-risk (kerjakan duluan)

### T1 — Fix bug data-integrity: fallback `video_id` pakai `hash()` random
- [x] **File:** `adapters/ytdlp/searcher.py` (method `_to_track`)
- [x] Tambah `import hashlib` di bagian atas file (sudah ada `import re` di
  baris 25 — taruh di dekatnya)
- [x] Ganti:
  ```python
  video_id = f"vid_{abs(hash(entry.get('title', ''))) % 10**10}"
  ```
  jadi:
  ```python
  video_id = f"vid_{hashlib.sha1(entry.get('title', '').encode()).hexdigest()[:10]}"
  ```
- [x] Terapkan di **kedua** tempat kemunculan — **dikonfirmasi ada persis di
  baris 102 dan 104**, isinya identik
- [x] **Verifikasi:**
  - Jalankan ulang search yang sama 2× (restart proses di antaranya),
    pastikan `video_id` fallback yang dihasilkan **sama persis** kedua kali
  - Update `tests/unit/adapters/ytdlp/test_searcher.py` (file test ini
    **sudah ada** — mirror-path test): tambah/assert bahwa fallback
    `video_id` untuk title yang sama selalu identik antar pemanggilan
    (deterministic), bukan cuma "tidak crash"
- [x] **Risiko:** none — hanya mengubah track yang sebelumnya tidak dapat `id`/`url` valid dari yt-dlp (jarang terjadi)

### T2 — Precompile regex validasi video_id di searcher
- [x] **File:** `adapters/ytdlp/searcher.py`
- [x] Tambah di atas class:
  ```python
  _VALID_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
  ```
- [x] Ganti pemakaian `re.match(r"^[a-zA-Z0-9_\-]{1,64}$", video_id)` (dikonfirmasi persis di baris 101, hanya satu kemunculan) → `_VALID_ID_RE.match(video_id)`
- [x] **Verifikasi:** jalankan `pytest tests/unit/adapters/ytdlp/ -q` (file test sudah ada), atau minimal 1 pencarian manual lewat UI, pastikan hasil search tidak berubah

### T3 — Index `artists.nama`
- [x] **File:** `persistence/schema.sql`
- [x] **Cek dulu tidak ada duplikat** — **dikonfirmasi ulang barusan** via
  query langsung ke `data/lunawave.db`: 100 artis, 0 duplikat `nama`. Tetap
  jalankan ulang di DB produksi kalian sebelum apply (data bisa saja berubah
  sejak commit ini):
  ```sql
  SELECT nama, COUNT(*) c FROM artists GROUP BY nama HAVING c > 1;
  ```
  Kalau hasilnya kosong → lanjut. Kalau ada duplikat → pakai index non-unique
  dulu (`CREATE INDEX` biasa, bukan `UNIQUE`), jangan paksa unique.
- [x] Tambahkan setelah blok `CREATE TABLE artists` (baris 31-38 di schema saat ini):
  ```sql
  CREATE UNIQUE INDEX IF NOT EXISTS idx_artists_nama ON artists(nama);
  ```
- [x] **Verifikasi:** jalankan `python data/export_to_sqlite.py` atau start app sekali agar migrasi `schema.sql` ter-apply (via `Database.init()`), cek index muncul:
  ```sql
  SELECT name FROM sqlite_master WHERE type='index' AND name='idx_artists_nama';
  ```

### T4 — Precompile regex LRC parser
- [x] **File:** `plugins/lyrics_parser.py`
- [x] Pindahkan `pattern = re.compile(...)` (baris 22, di dalam `parse_lrc()`, method ini `@staticmethod`) ke konstanta module-level `_LRC_LINE_RE`
- [x] **Verifikasi:**
  - Putar 1 lagu yang punya lirik synced, pastikan lirik & timing tetap tampil normal
  - Update `tests/unit/plugins/test_lyrics_parser.py` (sudah ada) — pastikan test lama masih hijau setelah pattern dipindah ke module-level

### T5 — Gabung 8× regex noise-keyword jadi 1 pattern
- [x] **File:** `plugins/lyrics_fetcher.py` (saat ini 200 baris — sudah masuk
  zona "Waspada" per `coding_standard.md`, jadi perubahan ini bagus karena
  justru **menyusutkan** baris kode, bukan menambah)
- [x] Ganti loop 8 keyword (`official, music video, lyric, lyrics, audio, video, mv, hq` — dikonfirmasi persis di baris 125-134) dengan 1 konstanta module-level:
  ```python
  _NOISE_RE = re.compile(
      r"\b(?:official|music video|lyrics?|audio|video|mv|hq)s?\b",
      re.IGNORECASE,
  )
  ```
  lalu `clean_title = _NOISE_RE.sub("", clean_title)`
- [x] **Catatan urutan alternation:** urutan `music video` sebelum `video`
  dalam pattern **wajib dipertahankan** persis seperti di atas — regex
  alternation Python mencoba alternatif dari kiri ke kanan di posisi yang
  sama, jadi kalau `video` ditaruh sebelum `music video`, frasa "Official
  Music Video" akan tersisa kata "Music" nyangkut karena "video"-nya kepotong
  duluan. Pattern yang diusulkan sudah benar urutannya (mengikuti urutan loop
  asli), tapi tetap wajib dites, bukan diasumsikan sama.
- [x] **Verifikasi:**
  - Fetch lirik untuk 2-3 track dengan judul kotor (ada "Official Music Video", dsb.) — pastikan hasil `search_query` yang dibersihkan sama seperti sebelum perubahan
  - Update `tests/unit/plugins/test_lyrics_fetcher.py` (sudah ada) dengan
    kasus judul yang mengandung kombinasi 2+ keyword bersebelahan (mis.
    "Official Music Video (Lyrics)") untuk memastikan tidak ada regresi
    urutan alternation

### T6 — Precompile regex validasi video_id di HTTP stream handler
- [x] **File:** `server/handlers/http.py` — **catatan:** file ini saat ini
  194 baris (zona "Waspada", ambang 150). Perubahan T6 sendiri kecil (1 baris
  jadi konstanta), tapi lihat catatan gabungan di T9 di bawah supaya T6+T9+T14
  tidak menumpuk semua ke file yang sama.
- [x] Tambah konstanta module-level `_STREAM_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")`
- [x] Ganti pemakaian di `serve_stream()` (dikonfirmasi persis di baris 64: `re.match(r"^[a-zA-Z0-9_-]{11}$", video_id)`)
- [x] **Verifikasi:**
  - Putar 1 lagu dari awal sampai selesai (memastikan endpoint `/stream/<video_id>` tetap berfungsi), coba juga akses dengan `video_id` invalid (harus tetap dapat `400 Bad Request`)
  - Update `tests/unit/server/handlers/test_http.py` (sudah ada)

### T7 — Rate limiter: `list` → `deque` di command history
- [x] **File:** `server/middleware.py` (dikonfirmasi: `check_rate_limit()` di
  baris 29-41, `manager.command_history` adalah `dict[str, list[float]]`
  yang diinisialisasi `{}` di `server/connection_manager.py` baris 39)
- [x] Ubah struktur nilai `manager.command_history[ip]` dari `list` ke `collections.deque`
- [x] Ganti logic filter:
  ```python
  # sebelum
  cmd_history = [t for t in cmd_history if now - t < 60]
  # sesudah
  while cmd_history and now - cmd_history[0] >= 60:
      cmd_history.popleft()
  ```
- [x] **⚠️ Perbaikan penting yang terlewat di draft sebelumnya:** baris
  `cmd_history = manager.command_history.get(client_ip, [])` defaultnya
  masih `list` kosong (`[]`). Kalau `client_ip` baru (belum ada key),
  `.get()` akan mengembalikan `list`, bukan `deque`, dan `popleft()` di
  baris berikutnya akan **`AttributeError`**. Ganti default jadi:
  ```python
  from collections import deque
  cmd_history = manager.command_history.get(client_ip, deque())
  ```
- [x] **Cek juga `server/handlers/auth.py` (`_prune_stale_ips`, baris 34-55)** — dikonfirmasi logic-nya pakai `any(now - t < WINDOW for t in ts_list)`, ini tetap jalan sama persis di `deque` (iterable apapun kompatibel), tidak perlu diubah
- [x] **Verifikasi:**
  - Kirim >30 command dalam <60 detik dari 1 client, pastikan pesan "rate limit" tetap muncul seperti sebelumnya
  - Update `tests/unit/server/test_middleware.py` (sudah ada) — tambah kasus
    IP baru yang belum pernah muncul di `command_history` untuk menangkap bug
    default-type di atas
  - Test `tests/unit/server/handlers/test_auth.py::test_removes_stale_command_ips` (sudah ada) harus tetap hijau tanpa perubahan

---

**Checkpoint Tier 1:** setelah T1–T7 selesai, jalankan:
```bash
python automation/doctor.py
```
lalu prepend 1 entry gabungan (atau 7 entry terpisah, sesuai preferensi tim)
ke `docs/PATCHLOG.md`.

---

## TIER 2 — Fitur gap nyata (kerjakan bertahap, 2-3 per sesi)

### T8 — Resume posisi playback setelah restart server
- [x] **File baru/edit:** `persistence/schema.sql` (tambah kolom `last_position` di tabel `tracks`, atau tabel `playback_state` terpisah — **pilih salah satu, jangan dua-duanya**). Dikonfirmasi: tabel `tracks` saat ini belum punya kolom serupa, jadi gap ini valid.
- [x] **File:** `engine/playback/controller.py` — simpan `state.position` secara periodik (throttle, misal tiap 10 detik via `_on_track_progress`) — **HATI-HATI:** file ini (398 baris) ada di daftar "tidak boleh disentuh tanpa izin eksplisit" di `AI_CONTEXT.md` **dan** ditandai `❄️ Frozen (v1.0.0 Baseline)` di `docs/STATUS.md`. Minta approval dulu sebelum edit.
- [x] **File:** `main.py` — saat startup, load `last_position` + `current_track` terakhir, seek ke posisi itu sebelum resume
- [x] **Sub-task kecil:**
  - [x] T8a: tambah kolom DB
  - [x] T8b: simpan posisi (write path)
  - [x] T8c: load & seek saat startup (read path)
- [x] **Verifikasi:**
  - Putar lagu, seek ke menit 2, restart server (`Ctrl+C` lalu `python main.py`), pastikan lagu resume dari menit 2 (atau minimal track yang sama ter-load)
  - Kalau approval didapat dan `controller.py` disentuh: update
    `tests/unit/engine/playback/test_controller.py` (sudah ada, 248 baris) —
    jangan tambah test tanpa mengecek dulu apakah perubahan ini bisa
    dipindah keluar dari file frozen (mis. logic throttle-save di helper
    terpisah yang dipanggil dari controller, supaya bagian yang disentuh di
    file frozen seminim mungkin)

### T9 — Cache size indicator + manual clear
    `config.CACHE_DIR` (dikonfirmasi di `config.py`), bukan `cache/` secara umum — `cache/` di root repo juga berisi hal lain (mis. `cache/admin_password.txt`, yang **jangan pernah ikut ditampilkan/di-scan** karena ada di daftar file terlarang commit di `AI_CONTEXT.md`)
  - [x] T9b: backend — command `clear_cache` yang hapus file tapi **jangan hapus track yang `local_path` di-download manual** (bedakan cache MP3 sementara di `cache/mp3/` vs download permanen di folder `downloads/` — pembedaan ini sudah dipakai di `server/handlers/ws_download.py`, ikuti pola yang sama)
  - [x] T9c: frontend — tampilkan ukuran di halaman settings + tombol clear
- [x] **Verifikasi:**
  - Cek ukuran folder `cache/mp3/` via `du -sh` manual, bandingkan dengan angka yang ditampilkan UI — harus cocok
  - Buat `tests/unit/server/handlers/test_ws_cache.py` (file baru — wajib ada
    karena prinsip mirror-path test di repo ini, target 100% coverage)

### T10 — Sleep timer
- [x] **File baru:** `engine/sleep_timer.py` (lebih aman — tidak nyentuh file frozen). **Wajib** pakai format docstring module standar repo ini (`Purpose:`, `Responsibilities:`, `Depends on:`, `Subscribes to:`, `Publishes:`, `Thread Safety:` — dicek, semua modul lain di repo pakai format ini dan `automation/verify_docs.py` memeriksa kelengkapannya)
- [x] **File:** `core/commands.py` — tambah `CMD_SET_SLEEP_TIMER` (constants sudah ada di sini, re-exported lewat `core/command_bus.py` via `from core.commands import *`, jadi import dari `core.command_bus` di handler tetap konsisten dengan command lain)
- [x] **File (ditambahkan — hilang di draft sebelumnya):** `engine/command_router.py` — daftarkan handler baru lewat `command_bus.register(CMD_SET_SLEEP_TIMER, ...)`, ikuti pola command lain di file ini
- [x] **File (ditambahkan — hilang di draft sebelumnya):** `server/handlers/ws_playback.py` — tambah mapping WS action baru → `command_bus.execute(CMD_SET_SLEEP_TIMER, ...)`, ikuti pola `handle_playback_command()` yang sudah ada. Tanpa langkah ini, command tidak akan pernah ke-trigger dari tombol UI.
- [x] **Sub-task kecil:**
  - [x] T10a: command baru `set_sleep_timer(minutes)` — simpan `asyncio` task dengan `call_later`
  - [x] T10b: saat timer habis → panggil `_on_stop` (lewat command bus, bukan akses langsung ke controller internal — sesuai ADR-0004)
  - [x] T10c: frontend — UI pilih durasi (15/30/60 menit) + tampilkan countdown
- [x] **Verifikasi:**
  - Set timer 1 menit (untuk testing), pastikan lagu berhenti otomatis setelah 1 menit
  - Buat `tests/unit/engine/test_sleep_timer.py` (file baru, mirror-path wajib)

### T11 — Playback speed
- [x] **File:** `adapters/mpv/ipc.py` — dikonfirmasi sudah ada `set_property()` (baris 72), tinggal dipanggil dengan `("speed", value)`
- [x] **File:** `core/commands.py` — tambah command baru `CMD_SET_SPEED`
- [x] **File (ditambahkan):** `engine/command_router.py` — daftarkan handler
- [x] **File (ditambahkan):** `server/handlers/ws_playback.py` — mapping WS action baru
- [x] **File:** `engine/playback/controller.py` — perlu approval karena file frozen — **atau** taruh logic di `engine/playback/mode_ops.py` (dikonfirmasi ada, tidak frozen, dan sudah punya akses ke `self.mpv: AudioPlayerPort` di constructor-nya, jadi cocok dipanggil dari sana tanpa perlu edit file frozen)
- [x] **Sub-task kecil:**
  - [x] T11a: backend command + handler
  - [x] T11b: frontend — slider/dropdown speed (0.75x/1x/1.25x/1.5x/2x)
  - [x] T11c: persist pilihan speed per track atau global (putuskan salah satu — sarankan global dulu, lebih simpel)
- [x] **Verifikasi:**
  - Ubah speed ke 1.5x saat lagu main, pastikan pitch tetap wajar (MPV default preserve pitch) dan speed tersimpan setelah ganti lagu (kalau global)
  - Buat/update `tests/unit/engine/playback/test_mode_ops.py` (sudah ada — mirror-path test) untuk logic speed baru

### T12 — Recent search history
- [x] **File:** frontend saja — `web/static/js/events/search-input-events.js` + `web/static/js/utils/toast.js` (dikonfirmasi: `window.safeStorage` sudah didefinisikan di baris 1 file ini dan sudah dipakai di 6+ tempat lain — `services/auth.js`, `ws.js`, `portal.js`, `events/index.js` — jadi aman dipakai ulang, konsisten dengan pola yang ada)
- [x] **Sub-task kecil:**
  - [x] T12a: simpan query ke `safeStorage` (array JSON, max 10 item, dedup)
  - [x] T12b: tampilkan dropdown recent search saat search box difokus & kosong
  - [x] T12c: tombol "Clear search history"
- [x] **Verifikasi:**
  - Cari 3 lagu berbeda, refresh halaman, pastikan history muncul saat search box diklik
  - Sesuai `docs/testing/frontend_testing.md`: file `events/*.js` masuk kategori "Manual / e2e smoke", jadi tidak perlu bikin `*.test.js` Vitest baru — verifikasi manual di atas sudah cukup

### T12b — Support queue track deletion
- [x] **Frontend:** `web/static/js/render/queue.js` (add x button di tiap baris queue)
- [x] **Frontend:** `web/static/js/events/queue-events.js` (event delegation untuk tombol `qi-remove`, kirim wsAction `queue_remove`)
- [x] **Backend:** `server/handlers/ws_playback.py` (tambah command `queue_remove` yang menghapus index dari array queue)
- [x] **Verifikasi:** Tambah 3 lagu ke antrean, hapus lagu ke-2 lewat UI, pastikan lagu ke-3 naik dan pemutaran tidak terganggu

### T13 — A-B repeat / loop mode
- [x] **File:** `core/state.py` — tambah field baru, misal `loop_mode: str = "off"` (`"off" | "track" | "queue"`) (dikonfirmasi belum ada field serupa di state saat ini)
- [x] **File:** `engine/queue_manager.py` (53 baris, tidak frozen, masih jauh dari ambang god-file) — modifikasi `next()` untuk cek `loop_mode` sebelum advance
- [x] **File:** `core/commands.py` + handler — command `CMD_SET_LOOP`
- [x] **File (ditambahkan):** `engine/command_router.py` — daftarkan handler
- [x] **File (ditambahkan):** `server/handlers/ws_playback.py` — mapping WS action baru
- [x] **Sub-task kecil:**
  - [x] T13a: state field + command
  - [x] T13b: logic loop di `queue_manager.py` (radio mode tidak perlu loop, sudah self-sustaining)
  - [x] T13c: frontend toggle button 3-state (off/track/queue)
- [x] **Verifikasi:**
  - Aktifkan "loop track", pastikan lagu yang sama terus berulang; aktifkan "loop queue", pastikan setelah lagu terakhir kembali ke awal antrean
  - Update `tests/unit/engine/test_queue_manager.py` (sudah ada — mirror-path test)

### T14 — Retry stream indicator (expose backend yang sudah ada ke UI)
- [x] **Cek dulu:** backend retry logic sudah ada di `server/handlers/http.py` (`serve_stream`, dikonfirmasi persis: `for attempt in range(2)` di baris 109, cek status `403`/`410` di baris 138). Task ini **hanya** menambah sinyal ke frontend saat retry terjadi.
- [x] **File:** `server/handlers/http.py` — publish event/log message saat retry terjadi (`logger.warning` yang sudah ada bisa dikonversi jadi `LogMessageEvent` juga). **Catatan:** ini file ketiga (setelah T6) yang menyentuh `http.py` di rencana ini — kalau dikerjakan di sesi yang sama dengan T6, cek ulang jumlah baris akhir supaya tidak lewat 250 baris tanpa rencana pemecahan
- [x] **File:** frontend — tampilkan toast singkat "Mencoba ulang koneksi stream..."
- [x] **Verifikasi:**
  - Paling gampang diuji dengan mock/simulate response 403 dari upstream (butuh test manual atau unit test dengan fake response)
  - Update `tests/unit/server/handlers/test_http.py` (sudah ada)

### T15 — Queue duration total
- [x] **File:** frontend saja — `web/static/js/render/queue.js` (dikonfirmasi 149 baris saat ini — pas di batas "Aman/Perhatikan" untuk JS di `coding_standard.md`; penambahan kecil untuk fitur ini kemungkinan besar masih aman, tapi cek ulang jumlah baris akhir)
- [x] Sum `track.duration` dari `store.queue` array
- [x] **⚠️ Koreksi dari draft sebelumnya:** jangan modifikasi `formatTime()` di
  `web/static/js/utils/format.js` untuk menambah dukungan format `HH:MM:SS`
  — fungsi ini dikonfirmasi dipakai di **6 file lain**
  (`discover-tab.js`, `queue.js`, `search.js`, `now-playing.js`,
  `player.js`, `progress-events.js`) untuk durasi per-track yang jarang
  lebih dari 1 jam, jadi mengubahnya berisiko blast-radius luas untuk
  manfaat yang sempit. Sebagai gantinya, tambahkan fungsi baru di file yang
  sama, mis. `formatDurationLong(totalSecs)`, yang mendukung `HH:MM:SS`
  khusus untuk total durasi queue (biasanya bisa >1 jam)
- [x] Tampilkan hasil di header queue panel
- [x] **Verifikasi:**
  - Tambah beberapa lagu ke queue, cek total durasi cocok dengan penjumlahan manual
  - Masuk kategori "Manual / e2e smoke" (`render/*.js`), tidak perlu Vitest baru

### T16 — Crossfade (paling kompleks, taruh terakhir)
- [x] **Riset dulu sebelum implementasi:** cek apakah mau pakai fitur native MPV (`af=afade` dual-instance) atau simulasi manual (fade volume 1 detik sebelum track berakhir lalu load track baru)
- [x] **⚠️ Pertimbangan hardware (dari `docs/CONSTRAINTS.md` §4 — belum
  disebut di draft sebelumnya):** platform utama LunaWave adalah Termux
  (Android) dengan RAM/CPU terbatas. Pendekatan **dual-instance MPV**
  (menjalankan 2 proses/instance MPV bersamaan untuk crossfade) berisiko
  berat di perangkat low-end. **Disarankan pendekatan fade-volume manual
  single-instance sebagai default**, dan riset dual-instance MPV hanya
  sebagai opsi lanjutan kalau device kelas atas.
- [x] **⚠️ Koreksi lokasi file dari draft sebelumnya:** draft lama menyebut
  "taruh logic di `mode_ops.py`/`prefetcher.py`" tanpa path lengkap. Sudah
  dicek: ada **dua** file bernama mirip di repo dengan tanggung jawab
  berbeda —
  - `engine/playback/mode_ops.py` — tidak frozen, sudah pegang referensi
    `self.mpv`, cocok untuk logic fade yang berlaku di **semua** mode
    playback (manual, queue, radio)
  - `engine/radio/prefetcher.py` — **hanya** untuk prefetch track mode
    radio, tidak dipakai mode manual/queue

  Untuk crossfade yang berlaku di semua mode, gunakan
  `engine/playback/mode_ops.py`, **bukan** `engine/radio/prefetcher.py` —
  kalau logic ditaruh di `prefetcher.py`, crossfade hanya akan aktif saat
  radio mode dan tidak berfungsi untuk playback antrean biasa.
- [x] **File:** `engine/playback/controller.py` (frozen — butuh approval) **atau** pendekatan alternatif di `engine/playback/mode_ops.py` tanpa nyentuh file frozen (lihat poin di atas)
- [x] **Sub-task kecil:**
  - [x] T16a: riset pendekatan teknis + tulis ADR singkat kalau approach-nya nyentuh file frozen
  - [x] T16b: implementasi fade-out 1 detik terakhir sebelum EOF
  - [x] T16c: implementasi fade-in 1 detik di awal track baru
  - [x] T16d: toggle on/off di settings (karena ini preferensi subjektif, jangan default ON)
- [x] **Verifikasi:**
  - Dengarkan transisi 2 lagu berturut-turut, pastikan tidak ada "jeda hening" atau "pop" volume tiba-tiba
  - Update `tests/unit/engine/playback/test_mode_ops.py` (sudah ada) kalau logic ditaruh di `mode_ops.py`

---

## Ringkasan Urutan Kerja

| Sesi | Task | Estimasi effort |
|------|------|------------------|
| Sesi 1 | T1 – T7 (semua Tier 1) | Kecil, 1 sesi |
| Sesi 2 | T8 (resume posisi) | Kecil-sedang, butuh approval file frozen |
| Sesi 3 | T9 (cache indicator, file handler baru) + T15 (queue duration) | Kecil, bisa digabung karena independen |
| Sesi 4 | T10 (sleep timer) + T12 (recent search) | Kecil, independen |
| Sesi 5 | T11 (playback speed) | Sedang |
| Sesi 6 | T13 (loop mode) | Sedang |
| Sesi 7 | T14 (retry indicator) | Kecil — cek ulang ukuran `http.py` kalau digabung sesi yang sama dengan T6 |
| Sesi 8 | T16 (crossfade — prioritaskan pendekatan single-instance fade dulu, dual-instance MPV opsional) | Besar — taruh paling akhir |

## Catatan Approval yang Dibutuhkan

Task berikut menyentuh file yang ditandai **"tidak boleh disentuh tanpa izin
eksplisit"** di `AI_CONTEXT.md` (`engine/playback/controller.py` /
`server/handlers/websocket.py`, keduanya dikonfirmasi masih ada di daftar
tersebut) — **wajib minta approval dulu** sebelum eksekusi, atau cari
pendekatan alternatif yang tidak menyentuh file itu:

- T8 (resume posisi) — kemungkinan besar butuh edit `controller.py`
- T11 (playback speed) — bisa dihindari lewat `engine/playback/mode_ops.py`
- T16 (crossfade) — bisa dihindari lewat `engine/playback/mode_ops.py` (lihat catatan lokasi file di T16)

Task lain (T1–T7, T9, T10, T12, T13, T14, T15) **tidak** menyentuh file frozen.
