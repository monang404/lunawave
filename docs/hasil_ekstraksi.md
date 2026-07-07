# Hasil Ekstraksi Temuan Audit

Total temuan diekstrak dari DOKUMEN 1 — Executive Summary: 43

---
finding_id: EXEC-001
title: AppState adalah mutable shared state global
description: AppState digunakan sebagai mutable shared state global tanpa mekanisme concurrency protection. Hal ini memungkinkan siapa pun memutasi state secara langsung tanpa lock.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.1 Architecture Score: 68/100
raw_quote: "AppState adalah mutable shared state global tanpa mekanisme concurrency protection — siapapun bisa mutasi langsung tanpa lock"

---
finding_id: EXEC-002
title: Database.__getattr__ proxy magic
description: Penggunaan magic proxy pada Database.__getattr__ membuat API menjadi tidak jelas dan menyulitkan proses mocking saat testing.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.1 Architecture Score: 68/100
raw_quote: "Database.__getattr__ proxy magic membuat API tidak jelas dan sulit di-mock dalam testing"

---
finding_id: EXEC-003
title: config.py menjalankan side effects
description: File config.py menjalankan side effects saat proses import (seperti membuat direktori socket dan memvalidasi path), yang mana melanggar prinsip dasar modul Python.
claimed_location: config.py
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.1 Architecture Score: 68/100
raw_quote: "config.py menjalankan side effects saat import (buat direktori socket, validasi path) — melanggar prinsip dasar modul Python"

---
finding_id: EXEC-004
title: Import time di baris terakhir file mpv_controller.py
description: File mpv_controller.py mengimport modul time di baris paling bawah file, bukan di bagian atas. Ini merupakan bug latent dan code smell yang serius.
claimed_location: mpv_controller.py
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.1 Architecture Score: 68/100
raw_quote: "mpv_controller.py mengimport time di baris terakhir file (bukan di atas) — bug latent dan code smell serius"

---
finding_id: EXEC-005
title: http_session tidak diinjeksikan
description: aiohttp.ClientSession (http_session) dibuat di bootstrap.py namun tidak diinjeksikan ke server/app.py. Akibatnya, stream proxy di http.py akan diam-diam menginisialisasi None fallback.
claimed_location: bootstrap.py, server/app.py, http.py
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.1 Architecture Score: 68/100
raw_quote: "http_session (aiohttp.ClientSession) dibuat di bootstrap.py tapi tidak diinjeksikan ke server/app.py"

---
finding_id: EXEC-006
title: Zero security headers HTTP
description: Tidak terdapat HTTP security headers seperti Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security, atau Referrer-Policy di respons apa pun, membuka celah XSS, clickjacking, dan MIME sniffing.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "Zero security headers HTTP — tidak ada Content-Security-Policy, X-Frame-Options... di response manapun."

---
finding_id: EXEC-007
title: CORS wildcard pada endpoint audio
description: Konfigurasi CORS menggunakan wildcard (Access-Control-Allow-Origin: *) pada endpoint /api/stream/{id}, sehingga audio dapat di-embed oleh domain mana saja.
claimed_location: /api/stream/{id}
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "CORS wildcard (Access-Control-Allow-Origin: *) pada /api/stream/{id} — endpoint audio bisa di-embed oleh domain mana pun"

---
finding_id: EXEC-008
title: Tidak ada rotasi token session
description: Session token berukuran 16 bytes hex (128-bit) tidak melakukan rotasi pasca-privilege change dan tidak ada mekanisme invalidasi token pada saat logout.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "Session token 16 bytes hex (128-bit) — aman secara ukuran, namun tidak ada rotasi token pasca-privilege change, tidak ada invalidasi saat logout"

---
finding_id: EXEC-009
title: Logout tidak invalidasi session di server
description: Proses logout melalui JS hanya menghapus token dari localStorage, sedangkan token di database tetap valid hingga waktu kedaluwarsa habis (4 jam).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "Logout tidak invaliadasi session di server — logout() di JS hanya menghapus token dari localStorage"

---
finding_id: EXEC-010
title: X-Forwarded-For rentan di-spoof
description: Header X-Forwarded-For dapat dipalsukan untuk melewati rate limiting karena TRUSTED_PROXY=true dipercaya bulat tanpa memvalidasi jumlah header.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "X-Forwarded-For dapat di-spoof untuk bypass rate limiting — TRUSTED_PROXY=true dipercaya bulat tanpa validasi jumlah header"

---
finding_id: EXEC-011
title: Binary win32-x64 ter-commit ke repo
description: Binary esbuild untuk Windows (Node modules win32-x64) dikomit ke dalam repository, menimbulkan supply chain risk dan memperbesar ukuran repo tanpa alasan yang perlu.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "Node modules win32-x64 ter-commit ke repo (esbuild binary Windows) — supply chain risk dan ukuran repo tidak perlu"

---
finding_id: EXEC-012
title: Nilai MAX_VOLUME melebihi batas
description: Konstanta MAX_VOLUME di-set menjadi 150 di constants.py, nilai yang melebihi 100% ini berpotensi merusak hardware audio.
claimed_location: constants.py
claimed_severity: Kritis
source_section: 3.2 Security Score: 44/100
raw_quote: "MAX_VOLUME = 150 di constants.py — nilai melebihi 100% dapat merusak audio hardware"

---
finding_id: EXEC-013
title: Memory leak pada _stream_rate_limit
description: Variabel _stream_rate_limit (defaultdict) bertambah tanpa batas karena tidak ada pembersihan (pruning) untuk data usang, menyebabkan memory leak saat traffic tinggi.
claimed_location: http.py
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.3 Performance Score: 55/100
raw_quote: "_stream_rate_limit (defaultdict) di http.py tumbuh tanpa batas — tidak ada pruning stale entries; memory leak pada traffic tinggi"

---
finding_id: EXEC-014
title: syncBrowserAudio dipanggil setiap tick
description: Fungsi syncBrowserAudio() dijalankan di setiap tick progress (sekitar 333ms) dari handler WS message "progress", membebani evaluasi di browser secara berulang-ulang.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.3 Performance Score: 55/100
raw_quote: "syncBrowserAudio() dipanggil setiap tick progress (setiap ~333ms) dari handler \"progress\" WS message"

---
finding_id: EXEC-015
title: Fake beat loop berjalan terus menerus
description: Fake beat loop menggunakan requestAnimationFrame terus berjalan walau tidak ada perubahan visual yang dibutuhkan, membuang sumber daya CPU khususnya di perangkat mobile.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.3 Performance Score: 55/100
raw_quote: "Fake beat loop (requestAnimationFrame) tetap berjalan bahkan ketika tidak ada perubahan visual yang diperlukan"

---
finding_id: EXEC-016
title: Broadcast state penuh setiap event
description: Sistem mem-broadcast seluruh state aplikasi (antrean, lirik, dll) pada tiap event kecil karena tidak terdapat mekanisme pengiriman data yang hanya berubah (delta/diff).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.3 Performance Score: 55/100
raw_quote: "Broadcast state penuh (seluruh queue, lyrics, dll) setiap event kecil — tidak ada delta/diff broadcast"

---
finding_id: EXEC-017
title: Single-threaded aiohttp tanpa worker pool
description: Aiohttp berjalan single-threaded tanpa worker pool, sehingga request lambat dari yt-dlp dapat menghalangi progress broadcast ke semua client.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.3 Performance Score: 55/100
raw_quote: "Single-threaded aiohttp tanpa worker pool — satu request yt-dlp yang lambat dapat menunda progress broadcast ke semua client"

---
finding_id: EXEC-018
title: Lyrics sync double requestAnimationFrame
description: Pemanggilan fungsi lirik menjalankan requestAnimationFrame(() => syncLocalLyrics()) pada setiap tik progress, menghasilkan double RAF setiap detiknya.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.3 Performance Score: 55/100
raw_quote: "Lyrics sync memangil requestAnimationFrame(() => syncLocalLyrics()) pada setiap progress tick — double RAF per detik"

---
finding_id: EXEC-019
title: Penamaan bilingual tidak konsisten
description: Terdapat penamaan variabel secara bilingual (Indonesia/Inggris) dalam file yang sama (misal nama, judul vs title, artist).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.4 Maintainability Score: 61/100
raw_quote: "Penamaan bilingual (Indonesia/English) dalam satu file yang sama... bercampur dengan title, artist, duration di Python"

---
finding_id: EXEC-020
title: bundle.js adalah file monolitik
description: bundle.js berukuran sangat besar (2.649 baris, 104KB) dan di-generate tanpa source map, sangat menyulitkan debugging di level production.
claimed_location: bundle.js
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.4 Maintainability Score: 61/100
raw_quote: "bundle.js (2.649 baris, 104KB) adalah satu file monolitik yang di-generate — debug di production sangat sulit tanpa source map"

---
finding_id: EXEC-021
title: Log message campur dua bahasa
description: Pesan log tidak konsisten dalam penggunaan bahasa, mencampur pesan bahasa Indonesia ("Memulai download") dengan bahasa Inggris ("Download complete").
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.4 Maintainability Score: 61/100
raw_quote: "Log message campur dua bahasa: sebagian \"Memulai download\", sebagian \"Download complete\" — tidak konsisten"

---
finding_id: EXEC-022
title: Tidak ada CHANGELOG.md aktif
description: Tidak ada file CHANGELOG.md di root yang men-tracking version production (hanya tersedia di archive/).
claimed_location: archive/
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.4 Maintainability Score: 61/100
raw_quote: "Tidak ada CHANGELOG.md untuk production version tracking (yang ada hanya di archive/)"

---
finding_id: EXEC-023
title: Konflik versi aiosqlite
description: Terdapat version conflict antara pyproject.toml (aiosqlite==0.22.1) dan requirements.txt (aiosqlite==0.20.0), yang bisa memunculkan environment berbeda tergantung dari installer yang dipakai.
claimed_location: pyproject.toml, requirements.txt
claimed_severity: TIDAK DISEBUTKAN
source_section: 3.4 Maintainability Score: 61/100
raw_quote: "pyproject.toml mendefinisikan aiosqlite==0.22.1 tetapi requirements.txt mendefinisikan aiosqlite==0.20.0"

---
finding_id: EXEC-024
title: Sangat sedikit test functions
description: Dari 21 file test, hanya terdapat 17 fungsi test. Banyak file test yang hampir kosong atau memiliki rata-rata di bawah 1 test per file.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Hanya 17 test functions dari 21 file test — rata-rata < 1 test per file; banyak file test yang hampir kosong"

---
finding_id: EXEC-025
title: Coverage threshold sangat rendah
description: CI hanya mematok coverage threshold di angka 40%, jauh dari standar industri untuk rilis produksi (70–80%).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Coverage threshold hanya 40% di CI — standar industri minimum untuk production adalah 70–80%"

---
finding_id: EXEC-026
title: Tidak ada integration test nyata
description: Tidak terdapat test integrasi nyata; test_e2e.py dan test_fase1.py tidak memicu request HTTP/WS secara riil.
claimed_location: test_e2e.py, test_fase1.py
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Tidak ada integration test yang menjalankan stack nyata — test_e2e.py dan test_fase1.py tidak melakukan request HTTP/WS riil"

---
finding_id: EXEC-027
title: Alur kritis tidak di-test
description: Alur sangat penting seperti login/logout, rate limiting, stream proxy, radio mode, download manager, dan event listeners belum mempunyai test sama sekali.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Tidak ada test untuk alur kritis: login/logout, rate limiting, stream proxy, radio mode, download manager, event listeners"

---
finding_id: EXEC-028
title: Konfigurasi Mypy teramat longgar
description: Type checker Mypy dikonfigurasi terlalu bebas (check_untyped_defs = false, disallow_untyped_defs = false), membuatnya hampir dinonaktifkan.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Mypy dikonfigurasi sangat longgar: check_untyped_defs = false, disallow_untyped_defs = false"

---
finding_id: EXEC-029
title: Ruff mengabaikan aturan penting
description: Linter Ruff mengabaikan rule esensial seperti E722 (bare except), F841 (unused variable), dan I001 (import sorting), menjadikan linting tidak efektif.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Ruff mengabaikan banyak rule penting: E722 (bare except), F841 (unused variable), I001 (import sorting)"

---
finding_id: EXEC-030
title: Tidak ada performance/load test
description: Aplikasi belum melalui pengujian performa atau load test.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_section: 3.5 Testability Score: 28/100
raw_quote: "Tidak ada performance test / load test"

---
finding_id: EXEC-031
title: AppState hanya di in-memory
description: Semua state aplikasi di dalam AppState cuma disimpan in-memory; proses restart berarti kehilangan keseluruhan state playback.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_section: 3.6 Scalability Score: 35/100
raw_quote: "Seluruh state aplikasi (AppState) disimpan in-memory — restart = reset state, tidak ada persistence playback state"

---
finding_id: EXEC-032
title: SQLite hanya single instance
description: Aplikasi menggunakan single SQLite instance dengan satu koneksi, yang menghalangi kemampuannya untuk divaluasi secara horizontal (scale out).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_section: 3.6 Scalability Score: 35/100
raw_quote: "Single SQLite instance dengan satu koneksi — tidak dapat di-scale horizontal"

---
finding_id: EXEC-033
title: ConnectionManager berupa list tanpa batas
description: ConnectionManager.active_connections menggunakan list standar tanpa batas, sehingga tak ada perlindungan terhadap serangan connection flood.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_section: 3.6 Scalability Score: 35/100
raw_quote: "ConnectionManager.active_connections adalah plain list tanpa limit — tidak ada proteksi dari connection flood (DoS potensial)"

---
finding_id: EXEC-034
title: Tidak memiliki sistem queue/job
description: Download dijalankan langsung secara paralel di event loop tanpa ada sistem queue atau backpressure untuk membatasinya.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_section: 3.6 Scalability Score: 35/100
raw_quote: "Tidak ada queue/job system — download berjalan langsung di event loop, tidak ada backpressure"

---
finding_id: EXEC-035
title: Tidak ada lapisan cache (Redis/Memcached)
description: Karena hilangnya layer cache, setiap request discover harus selalu membuka sambungan baru ke database SQLite.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_section: 3.6 Scalability Score: 35/100
raw_quote: "Tidak ada cache layer (Redis/Memcached) — setiap discover request membuka koneksi DB"

---
finding_id: EXEC-036
title: Rate limit state tersimpan di in-memory
description: Keamanan dari brute-force rawan di-reset karena state rate limiting tersimpan di memory, yang berarti me-restart server akan menghilangkan semua batas tersebut.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_section: 3.6 Scalability Score: 35/100
raw_quote: "Rate limiting state (login_attempts, command_history) disimpan in-memory — restart server = reset semua brute-force protection"

---
finding_id: EXEC-037
title: File run.py tidak ada (Blocker Deployment)
description: File run.py absen dari kode sumber, mengakibatkan Dockerfile mengalami crash saat mengeksekusi container.
claimed_location: run.py, Dockerfile
claimed_severity: Blocker / Kritis
source_section: 3.7 Release Readiness
raw_quote: "run.py tidak ada — Dockerfile akan crash saat start"

---
finding_id: EXEC-038
title: Sinkronkan versi aiosqlite (Blocker)
description: Terdapat konflik dependensi yang fatal untuk aiosqlite antara requirements.txt dan pyproject.toml yang perlu diselaraskan (gunakan 0.22.1).
claimed_location: requirements.txt, pyproject.toml
claimed_severity: Blocker / Kritis
source_section: 5. PRIORITAS PERBAIKAN (Tier 0)
raw_quote: "Sinkronkan versi aiosqlite antara requirements.txt dan pyproject.toml (gunakan 0.22.1)"

---
finding_id: EXEC-039
title: Pruning memori _stream_rate_limit (Blocker)
description: Perlu ada proses pruning ke dalam _stream_rate_limit agar tidak menyebabkan kebocoran memori (disamakan polanya dengan auth.py).
claimed_location: server/handlers/http.py
claimed_severity: Blocker / Kritis
source_section: 5. PRIORITAS PERBAIKAN (Tier 0)
raw_quote: "Tambah pruning ke _stream_rate_limit (sama dengan pola di server/handlers/auth.py)"

---
finding_id: EXEC-040
title: PWA manifest kurang ikon resolusi tinggi
description: File manifest PWA cuma punya ikon ukuran 1024x1024. Butuh ditambah ukuran 192x192 dan 512x512.
claimed_location: web/static/manifest.json
claimed_severity: Sedang
source_section: 5. PRIORITAS PERBAIKAN (Tier 2)
raw_quote: "PWA manifest: tambah icon 192x192 dan 512x512 (saat ini hanya 1024x1024)"

---
finding_id: EXEC-041
title: Variabel environment jadul di .env.example
description: File .env.example menggunakan variabel berawalan YTGUI_ yang lama, berbenturan dengan kenyataan aktual yang pakai LUNAWAVE_.
claimed_location: .env.example
claimed_severity: Rendah
source_section: 6. INVENTORI TEMUAN LENGKAP
raw_quote: ".env.example menggunakan nama variabel lama (YTGUI_) vs aktual (LUNAWAVE_)"

---
finding_id: EXEC-042
title: File HTML tidak relevan di direktori tests
description: Terdapat file test_helpers.html yang malah menempati folder tes (tests/).
claimed_location: tests/test_helpers.html
claimed_severity: Rendah
source_section: 6. INVENTORI TEMUAN LENGKAP
raw_quote: "tests/test_helpers.html file HTML ada di direktori tests"

---
finding_id: EXEC-043
title: WebSocket di-expose ke global scope window
description: Front end membuka kerentanan atau masalah privasi state dengan mengekspos WebSocket via window.ws = ws ke global scope.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Rendah
source_section: 6. INVENTORI TEMUAN LENGKAP
raw_quote: "window.ws = ws expose WebSocket ke global scope"


Total temuan diekstrak dari DOKUMEN 2 — Bug Audit: 28

---
finding_id: BUG-B01
title: discover_service KeyError: stream_url tidak di-SELECT
description: SQL pada fungsi DiscoverService.get_recent(), get_favorites(), dan get_cached() tidak melakukan query pada kolom stream_url. Hal ini menyebabkan KeyError saat pembacaan dictionary, error tertelan, dan membuat tab Discover tampil kosong tanpa laporan error.
claimed_location: server/services/discover_service.py (baris 36, 63, 90)
claimed_severity: CRITICAL
source_section: B-01 — discover_service KeyError: stream_url tidak ada di SELECT
raw_quote: "SQL hanya meng-SELECT 9 kolom tapi TrackInfo(...) mengakses d[\"stream_url\"]"

---
finding_id: BUG-B02
title: handle_auth tidur di dalam global rl_lock — DoS seluruh autentikasi
description: Delay rate-limiting berupa asyncio.sleep(2) dijalankan di dalam manager.rl_lock. Akibatnya, satu attacker dengan percobaan gagal bisa menahan lock dan memblokir seluruh request autentikasi dari pengguna lain.
claimed_location: server/handlers/auth.py (baris 28–45)
claimed_severity: CRITICAL
source_section: B-02 — handle_auth tidur di dalam global rl_lock — DoS seluruh autentikasi
raw_quote: "Karena ada 2 attempt, await asyncio.sleep(2) dieksekusi di dalam lock... membuat semua user (IP lain) tidak bisa login"

---
finding_id: BUG-B03
title: _on_track_ended reason kosong "" tidak ditangani — autoplay mati
description: Default value string kosong pada TrackEndedEvent.reason tidak ditangani dalam statement kondisional fungsi _on_track_ended(). Jika reason bukan eof/stop/error, fungsi tersebut akan langsung return tanpa melakukan apapun dan autoplay mati diam-diam.
claimed_location: engine/playback/controller.py (baris 174–192), core/events.py
claimed_severity: CRITICAL
source_section: B-03 — _on_track_ended reason kosong "" tidak ditangani — autoplay mati diam-diam
raw_quote: "TIDAK ADA else! reason=\"\" / \"quit\" / \"redirect\" → autoplay mati"

---
finding_id: BUG-B04
title: play_track retry backoff membaca _retry_count stale
description: Variabel self._retry_count dibaca di luar blok _play_lock yang mana nilainya bisa berubah akibat intervensi eksekusi fungsi lain di sela-sela pembebasan lock tersebut, mengakibatkan nilai sleep(backoff) yang tidak terprediksi.
claimed_location: engine/playback/controller.py (baris 139–150)
claimed_severity: CRITICAL
source_section: B-04 — play_track retry backoff membaca _retry_count setelah lock dilepas — nilai stale
raw_quote: "backoff = 2 ** self._retry_count  # ← baca di luar lock! nilai bisa sudah berubah"

---
finding_id: BUG-B05
title: _on_track_ended error path: guard if IDLE tidak pernah terpenuhi
description: Pada kondisi error, state diatur ke PlayerStatus.ERROR sebelum sleep 2 detik. Guard 'if self.state.status == PlayerStatus.IDLE:' tidak akan pernah terpenuhi karena status saat itu adalah ERROR, mengakibatkan perpindahan track tak terhindarkan meski diputus manual oleh user.
claimed_location: engine/playback/controller.py (baris 186–192)
claimed_severity: CRITICAL
source_section: B-05 — _on_track_ended error path: guard if IDLE tidak pernah terpenuhi
raw_quote: "Status adalah ERROR, bukan IDLE → guard tidak pernah terpenuhi"

---
finding_id: BUG-B06
title: import time di baris paling akhir mpv_controller.py
description: Pemanggilan modul time.monotonic() dilakukan di dalam method _handle_event namun import time diletakkan di baris paling terakhir dalam file tersebut. Ini memicu NameError jika dieksekusi sebelum modul berhasil diinisialisasi secara utuh.
claimed_location: engine/mpv_controller.py (baris terakhir)
claimed_severity: CRITICAL
source_section: B-06 — import time di baris paling akhir mpv_controller.py — NameError saat cold path
raw_quote: "import time berada di baris paling terakhir file, setelah definisi class... memicu NameError: name 'time' is not defined"

---
finding_id: BUG-B07
title: _lock di PlaybackController dideklarasikan tapi tidak digunakan
description: PlaybackController memiliki self._lock = asyncio.Lock() namun tidak pernah memanggil lock tersebut pada operasinya secara internal, sehingga subscriber event tetap memutasi state tanpa lock, menimbulkan false sense of security.
claimed_location: engine/playback/controller.py (baris 59)
claimed_severity: HIGH
source_section: B-07 — _lock di PlaybackController dideklarasikan tapi tidak pernah digunakan
raw_quote: "namun tidak pernah di-acquire di dalam PlaybackController itu sendiri... Semua subscriber event berjalan tanpa lock."

---
finding_id: BUG-B08
title: on_next memicu bottleneck beruntun karena hold _lock
description: on_next memegang lock sambil mengeksekusi _advance_to_next() -> play_track(). Hal ini menyebabkab semua operasi I/O dan jaringan panjang terperangkap di dalam satu lock secara sekuensial, menghentikan seluruh antrean operasi lain.
claimed_location: engine/playback/playback_commands.py (baris 29–35)
claimed_severity: HIGH
source_section: B-08 — on_next menahan _lock lalu memanggil _advance_to_next → play_track yang butuh _play_lock — bottleneck beruntun
raw_quote: "semua queue ops lain terblokir selama _advance_to_next berjalan"

---
finding_id: BUG-B09
title: _poll_duration menerbitkan QueueUpdatedEvent meskipun durasi gagal
description: Saat durasi lagu gagal didapatkan (nilai dur masih None) setelah 7 detik, _poll_duration tetap mengirim event QueueUpdatedEvent ke sistem yang akhirnya memicu broadcast menyeluruh tanpa adanya perubahan pada data state durasi.
claimed_location: engine/playback/controller.py (baris 153–170)
claimed_severity: HIGH
source_section: B-09 — _poll_duration menerbitkan QueueUpdatedEvent meskipun durasi tidak berubah
raw_quote: "jika dur masih None setelah 7 detik total, QueueUpdatedEvent tetap diterbitkan. Ini menyebabkan broadcast state ke semua client tanpa perubahan nyata."

---
finding_id: BUG-B10
title: VolumeService.current_volume desync dari state.volume
description: Penggunaan variabel snapshot (self.current_volume) dapat berbeda dengan state yang sesungguhnya apabila state dimutasi secara eksternal. Dua call serentak (race condition) juga dapat membaca dan menambahkan volume yang salah karena duplikasi pengambilan nilai dari variabel independen.
claimed_location: engine/volume_service.py (baris 19–41)
claimed_severity: HIGH
source_section: B-10 — VolumeService.current_volume bisa desync dari state.volume saat race
raw_quote: "jika dua volume command datang bersamaan (async), keduanya membaca state.volume yang sama, menambah +5, dan hasil akhirnya hanya +5 bukan +10"

---
finding_id: BUG-B11
title: handle_ws_message kurang validasi tipe dict untuk 'data'
description: Handler memanggil data = msg.get("data", {}) namun apabila payload menspesifikasikan string untuk 'data', akan terjadi AttributeError di downstream ketika handler lanjutan mencoba untuk mengakses data.get("...").
claimed_location: server/handlers/websocket.py (baris 78–90)
claimed_severity: HIGH
source_section: B-11 — handle_ws_message melempar json.dumps ke attribute error jika data bukan dict
raw_quote: "data = \"malicious_string\" (string, bukan dict)... Handler downstream memanggil data.get(\"position\", 0) → AttributeError"

---
finding_id: BUG-B12
title: ws_handler menangkap semua exception generik tanpa dipisah
description: Handler menganggap semua exception, termasuk disconnect yang wajar (ServerDisconnectedError/CancelledError), sebagai error sistem yang kemudian dicetak ke log, menambah noise dan mempersulit pelacakan error sebenarnya.
claimed_location: server/handlers/websocket.py (baris 65–76)
claimed_severity: HIGH
source_section: B-12 — ws_handler: exception umum ditangkap tanpa konteks — KeyError, AttributeError disembunyikan
raw_quote: "ServerDisconnectedError dan asyncio.CancelledError adalah kondisi normal... Melognya sebagai ERROR menghasilkan noise"

---
finding_id: BUG-B13
title: evict_stale_tracks mengirim list bukan tuple ke fungsi execute
description: Di beberapa versi aiosqlite, argumen list secara kaku tidak diterima pada query IN dengan array tunggal (['abc'] diinterpretasikan sebagai char sekuensial ('a','b','c')), dan list tersebut seharusnya dikoversi terlebih dahulu ke tuple sebelum eksekusi SQL.
claimed_location: cache/repositories/track_repository.py (baris 135–137)
claimed_severity: HIGH
source_section: B-13 — evict_stale_tracks: list string dioper langsung ke execute tanpa tuple()
raw_quote: "SQLite Python adapter... mengharapkan sequence berupa tuple... SQLite dapat menginterpretasi \"abc\" sebagai sequence karakter"

---
finding_id: BUG-B14
title: fetch_segments SponsorBlock mengosongkan list segmen di awal request HTTP
description: Segmen langsung dihapus sebelum menunggu HTTP request SponsorBlock selesai. Ini menyebabkan _on_progress tidak mampu melewatinya meskipun track masih berjalan jika transisi delay atau terjadi error.
claimed_location: plugins/sponsorblock.py (baris 38–53)
claimed_severity: HIGH
source_section: B-14 — SponsorBlock.fetch_segments mengosongkan self.segments sebelum fetch — jeda tanpa proteksi
raw_quote: "self.segments = [] — segments dikosongkan... _on_progress melihat self.segments = [] → tidak ada segment untuk diskip"

---
finding_id: BUG-B15
title: CacheResolver._fetching bisa menunda waiter selamanya (Memory Leak)
description: Jika ytdlp melemparkan exception ketika fetching, Waiter B akan diputus, lalu mengeksekusi fetch ulang seakan tidak pernah ada attempt, yang dapat menyebabkan concurrent parallel call berlebih secara tidak terbatas.
claimed_location: cache/resolver.py (baris 42–56)
claimed_severity: HIGH
source_section: B-15 — CacheResolver._fetching bisa leak event jika wait() disambar exception
raw_quote: "B memanggil await self.resolve(track) rekursif — tapi URL tidak tersimpan ke DB... B melakukan fetch ulang sendiri"

---
finding_id: BUG-B16
title: Baris LRC tanpa timestamp mendapatkan t=0.0
description: Metadata dari LRC file seperti [ti:Title] dimasukkan bersamaan dengan baris plain-text dan dicetak paksa menggunakan timestamp 0.0, yang menyebabkan artefak pada teks berjalan di awal lagu.
claimed_location: plugins/lyrics.py (baris 138–140)
claimed_severity: MEDIUM
source_section: B-16 — _parse_lrc: baris plain-text tanpa timestamp dimasukkan dengan t=0.0 — lyric error di awal lagu
raw_quote: "Baris metadata LRC seperti [ti:Title]... Mereka semua akan muncul sebagai lyric di t=0.0, menghasilkan artifact visual di awal lagu."

---
finding_id: BUG-B17
title: lyrics.py melakukan ekstraksi query pencarian sia-sia
description: Modul pencarian lirik memproses konversi dan sanitasi Regex berat (clean_title dan search_query) meskipun variabel lrc sudah tersedia sukses melalui _cache.
claimed_location: plugins/lyrics.py (baris 57–98)
claimed_severity: MEDIUM
source_section: B-17 — lyrics.py: clean_title / search_query dihitung bahkan ketika lrc sudah ada di cache
raw_quote: "kode tetap melanjutkan menghitung clean_title dan search_query... Ini adalah komputasi yang terbuang setiap kali cache hit."

---
finding_id: BUG-B18
title: _on_track_ended dengan path eof terbuka pada pemanggilan paralel
description: Bug pada engine MPV bisa mengirimkan message end-file (eof) berulang kali berurutan. Tidak ada proteksi guard, yang menyebabkan fungsi _advance_to_next tereksekusi dua kali dan melompati dua trek antrean.
claimed_location: engine/playback/controller.py (baris 181–183)
claimed_severity: MEDIUM
source_section: B-18 — _on_track_ended reason "eof" — asyncio.sleep(0.35) tidak diproteksi dari double call
raw_quote: "MPV terkadang mengirim end-file lebih dari sekali... _advance_to_next() dapat dipanggil dua kali berurutan dalam jeda 0.35 detik"

---
finding_id: BUG-B19
title: service_worker fallback salah path ke /static/index.html
description: Service Worker mencoba mencari dokumen HTML pada cache lewat caches.match('/static/index.html') padahal URL yang di-serve adalah path / (root). Offline fallback menjadi tidak berguna.
claimed_location: web/static/sw.js (baris 77)
claimed_severity: MEDIUM
source_section: B-19 — service_worker fallback ke /static/index.html — path salah, seharusnya /
raw_quote: "caches.match('/static/index.html'); // ← path salah!... Cache lookup ini akan selalu undefined (cache miss) saat offline"

---
finding_id: BUG-B20
title: settings_handlers _handle_volume_set membatasi volume berlebih
description: Handler websocket membatasi maksimal volume_set sebesar 150 sementara class Volume() mem-clamp batas asli secara paksa jadi 100. Hal ini menyebabkan inkonsistensi input.
claimed_location: server/handlers/ws/settings_handlers.py (baris 20)
claimed_severity: MEDIUM
source_section: B-20 — settings_handlers.py volume_set membatasi max 150 tapi Volume() clamp ke 100 — inkonsistensi
raw_quote: "Nilai 150 yang dikirim dari client akan diklem ke 100. Inkonsistensi ini membingungkan dan membuka kemungkinan bug di masa depan"

---
finding_id: BUG-B21
title: _connectivity_checker memiliki infinite loop yang tidak henti saat graceful shutdown
description: asyncio.sleep(60) dapat melemparkan asyncio.CancelledError namun ia diserap ke dalam catch Exception tanpa melemparnya ulang, sehingga daemon task sulit dihentikan secara bersih dari pool saat mematikan aplikasi.
claimed_location: core/background_tasks.py (baris 9–19)
claimed_severity: MEDIUM
source_section: B-21 — _connectivity_checker infinite loop tidak dapat dihentikan saat shutdown
raw_quote: "CancelledError ditangkap oleh except Exception... task ini tidak memeriksa apakah http_session sudah ditutup saat shutdown"

---
finding_id: BUG-B22
title: on_radio_randomize mengambil seed_artist dari cmd tanpa proteksi Null
description: Jika command_router memanggil command via action tanpa argumen (kasus 0 argument signiture), parameter cmd akan menjadi None. Pemanggilan cmd.seed_artist saat itu juga memicu AttributeError.
claimed_location: engine/playback/radio_commands.py (baris 20–22)
claimed_severity: MEDIUM
source_section: B-22 — on_radio_randomize: cmd bisa None tapi diakses cmd.seed_artist tanpa guard
raw_quote: "Jika CommandRouter._route memanggil handler tanpa argument... cmd bisa None. Ini terjadi jika inspect.signature mendeteksi 0 parameter"

---
finding_id: BUG-B23
title: TrackInfo.from_dict mendiamkan ValueError karena video_id hash invalid
description: YtDlpClient menghasilkan fallback hash yang panjangnya melebihi validasi ID (11 huruf), sehingga VideoId() di TrackInfo melempar exception ValueError. Akibatnya object dikonversi jadi None dan request gagal diam-diam.
claimed_location: core/state.py (baris 58–65)
claimed_severity: MEDIUM
source_section: B-23 — TrackInfo.from_dict: VideoId() melempar ValueError untuk ID yang di-hash fallback
raw_quote: "TrackInfo.from_dict(data) akan melempar ValueError di konstruktor VideoId()... Hasilnya: track = None, play request diabaikan diam-diam"

---
finding_id: BUG-B24
title: _on_track_ended mendeklarasikan next_data yang tidak pernah digunakan
description: Di dalam logika perpindahan end-file, variabel next_data dikostruksi, di-assign key dengan nilai video_id, tapi tidak pernah dipakai di kode mana pun setelahnya.
claimed_location: engine/playback/controller.py (baris 177–179)
claimed_severity: LOW
source_section: B-24 — next_data dict dibangun tapi tidak pernah digunakan di _on_track_ended
raw_quote: "next_data = {} // ← dibuat... if reason == \"eof\": // ← next_data TIDAK PERNAH digunakan di bawah ini"

---
finding_id: BUG-B25
title: get_featured_genres menggunakan perintah print() daripada logging
description: Pada tangkapan error koneksi, perintah yang dipakai adalah print standar. Di sisi operasional produksi ini tidak tercatat dalam jurnal logger dengan struktur/tingkatan pesan yang benar.
claimed_location: server/services/discover_service.py (baris 130)
claimed_severity: LOW
source_section: B-25 — get_featured_genres menggunakan print() bukan logger.error() untuk error
raw_quote: "print(f\"Error in get_featured_genres: {e}\")... Error akan muncul di stdout (bukan log file), tidak ter-format"

---
finding_id: BUG-B26
title: _CompactRenderer.__call__ memberikan feedback log berupa empty string
description: Mem-bypass struktur chain logger dengan balasan return "" yang notabene tidak valid terhadap rantai fungsi structlog yang meminta objek dictionary.
claimed_location: core/log_config.py (baris _CompactRenderer.__call__)
claimed_severity: LOW
source_section: B-26 — _CompactRenderer.__call__ mengembalikan string kosong padahal structlog mengharapkan dict atau raise
raw_quote: "_CompactRenderer mengembalikan \"\" (string kosong) yang secara teknis bukan perilaku yang didokumentasikan."

---
finding_id: BUG-B27
title: Daemon _summary_worker dan _status_bar_worker tak punya kondisi henti
description: Membiarkan worker memutar infinite loop dengan while True. Hal ini memaksa thread harus dibunuh oleh interpreter saat aplikasi mati. Akan lebih baik menggunakan event handler .wait() untuk exit condition.
claimed_location: core/log_config.py
claimed_severity: LOW
source_section: B-27 — _summary_worker dan _status_bar_worker tidak memeriksa _stop event — daemon thread bocor
raw_quote: "Karena ini daemon thread... thread tidak bisa di-stop secara bersih (misalnya untuk testing atau graceful shutdown)"

---
finding_id: BUG-B28
title: extractDominantColor merespons balik nilai callback berupa string
description: Pada saat terjadi kegagalan proses ekstraksi warna, callback akan mengembalikan nilai primitif string untuk kode css. Tapi pemanggilnya hanya menyiapkan diri mengolah object {r,g,b}, sehingga berakibat inkonsistensi render halaman.
claimed_location: web/static/js/utils.js
claimed_severity: LOW
source_section: B-28 — extractDominantColor memanggil callback("var(--bg-elevated)") — callback menerima string bukan objek {r,g,b}
raw_quote: "Saat error: color = \"var(--bg-elevated)\", color.r = undefined... guard if (color && color.r !== undefined) gagal"


Total temuan diekstrak dari DOKUMEN 3 — Architecture Audit: 19

---
finding_id: ARCH-A01
title: KeyError: 'stream_url' di DiscoverService — Crash pada Runtime
description: DiscoverService mengambil data dari database namun melupakan field stream_url dari query SELECT. Imbasnya, ketika sistem mencoba membuat instansi TrackInfo, terjadi KeyError yang membuat seluruh tab Discover crash dan tak dapat berfungsi.
claimed_location: server/services/discover_service.py (baris 36, 63, 90)
claimed_severity: CRITICAL
source_section: TEMUAN A-01 — CRITICAL BUG
raw_quote: "DiscoverService membuat TrackInfo(stream_url=d[\"stream_url\"], ...) tapi kolom stream_url tidak di-SELECT"

---
finding_id: ARCH-A02
title: Dockerfile mengeksekusi file yang tidak eksis (run.py)
description: Entry point container Docker diarahkan ke "run.py", sedangkan struktur repository mengharuskan eksekusi pada "main.py". Hal ini membuat Docker tak bisa start karena FileNotFoundError.
claimed_location: Dockerfile (baris 28)
claimed_severity: CRITICAL
source_section: TEMUAN A-02 — CRITICAL BUG
raw_quote: "CMD [\"python\", \"run.py\"] ... Entry point yang benar adalah main.py, bukan run.py"

---
finding_id: ARCH-A03
title: ITUNES_API_URL Tidak Terdefinisi — ReferenceError di Browser
description: File utilitas memanggil constant ITUNES_API_URL untuk keperluan pengambilan metadata cover lagu di iTunes, tapi variabel ini tak terdefinisi di mana pun dalam codebase. Ini memicu ReferenceError pada browser dan menyembunyikan semua artwork UI.
claimed_location: web/static/js/utils.js (baris ~70)
claimed_severity: CRITICAL
source_section: TEMUAN A-03 — CRITICAL BUG
raw_quote: "ITUNES_API_URL sebagai konstanta global tapi tidak pernah didefinisikan di manapun dalam codebase"

---
finding_id: ARCH-A04
title: Penggunaan tag export di dalam file berarsitektur classic script
description: Modul audio.js memakai syntax ESM (export module) tetapi keseluruhan frontend adalah classic script (global namespace tanpa type="module"). Ini memicu SyntaxError fatal di level browser.
claimed_location: web/static/js/audio.js (baris 128)
claimed_severity: CRITICAL
source_section: TEMUAN A-04 — CRITICAL
raw_quote: "export async function _resumeAndPlay(audio) menyebabkan SyntaxError di browser jika dimuat tanpa type=\"module\""

---
finding_id: ARCH-A05
title: Version Mismatch dependensi aiosqlite
description: Modul requirements.txt (aiosqlite==0.20.0) dan pyproject.toml (aiosqlite==0.22.1) tidak berada pada sinkronisasi versi yang sama. Developer yang memakai rujukan beda berisiko men-deploy library out-of-sync dan memicu incompatibility API.
claimed_location: requirements.txt (baris 2), pyproject.toml (baris 8)
claimed_severity: HIGH
source_section: TEMUAN A-05 — HIGH
raw_quote: "requirements.txt dan pyproject.toml tidak sinkron... Developer berbeda mungkin mendapat versi berbeda"

---
finding_id: ARCH-A06
title: DiscoverService Menduplikasi Seluruh Logic DiscoverRepository
description: Logic dari DiscoverService membuat query SQL raw yang duplikat total dengan implementasi di DiscoverRepository (DRY violation ekstrim sebanyak 132 baris). Bug yang diperbaiki satu titik tidak otomatis membetulkan endpoint yang lain.
claimed_location: server/services/discover_service.py, cache/repositories/discover_repository.py
claimed_severity: HIGH
source_section: TEMUAN A-06 — HIGH
raw_quote: "DiscoverService membuka koneksi DB sendiri (self.db.conn.execute(...)) alih-alih mendelegasikan ke Repository"

---
finding_id: ARCH-A07
title: AppState adalah Mutable Shared State Tanpa Lock Penuh — Race Condition
description: Objek AppState yang termutasi via WebSocket dijalankan dari banyak thread coroutine, namun eksekusi modifikasi data list-nya (queue, lirik) tidak sepenuhnya terkunci dalam _lock. Python GIL tak cukup untuk proteksi tingkat asinkron dan ini memicu kemungkinan korupsi daftar.
claimed_location: core/state.py, engine/playback/queue_commands.py
claimed_severity: HIGH
source_section: TEMUAN A-07 — HIGH
raw_quote: "Multiple concurrent WS commands... menulis ke state.queue, state.lyrics_lines, state.position secara bersamaan tanpa synchronization."

---
finding_id: ARCH-A08
title: State lagu yang sedang berputar di-broadcast ke seluruh client anonim
description: manager.broadcast() melampirkan broadcast lagu privat yang sedang diputar ke iterasi "active_connections", termasuk para pengunjung socket yang bahkan belum melakukan login autentikasi. Ini merupakan kebocoran data informasi.
claimed_location: server/handlers/websocket.py (baris 49), server/services/broadcast_service.py
claimed_severity: HIGH
source_section: TEMUAN A-08 — HIGH
raw_quote: "mengirim state (termasuk current_track, queue, lyrics) ke semua WebSocket yang terhubung, termasuk yang belum login."

---
finding_id: ARCH-A09
title: config.py Mengeksekusi Side Effects saat Import
description: File konfigurasi langsung mengeksekusi operasi sistem operasi (mkdir socket dan file I/O). Pemanggilan fungsi ber-side-effect pada modul level top melanggar Clean Architecture dan akan memicu error di saat sistem import daripada saat runtime.
claimed_location: config.py (baris 10–16)
claimed_severity: HIGH
source_section: TEMUAN A-09 — HIGH
raw_quote: "Import config = mkdir, file I/O... melanggar prinsip Clean Architecture — module layer tidak boleh memiliki side effect saat import"

---
finding_id: ARCH-A10
title: Penghapusan item deque menggunakan del memicu kompleksitas O(n)
description: Variabel queue menggunakan struktur deque dari collections yang tak efisien (O(n)) jika dipaksa menghapus data acak di tengah urutan via del self.state.queue[cmd.index]. Jika beroperasi di list 500+ lagu bisa menyumbat I/O jika user sering reorder item.
claimed_location: engine/playback/queue_commands.py (baris 14)
claimed_severity: MEDIUM
source_section: TEMUAN A-10 — MEDIUM
raw_quote: "deque di Python tidak mendukung O(1) random-access delete. del deque[index] = O(n)"

---
finding_id: ARCH-A11
title: Proxy __getattr__ Database mempersulit pelacakan error
description: Magic attribute proxy __getattr__ merutekan pemanggilan method secara berurutan ke 3 repository berbeda yang jika terjadi kelalaian pemanggilan, AttributeError akan membingungkan developer. Sumber trace jadi buram.
claimed_location: cache/db.py (baris 84)
claimed_severity: MEDIUM
source_section: TEMUAN A-11 — MEDIUM
raw_quote: "Magic __getattr__ proxy yang memeriksa 3 repository secara berurutan... Stack trace tidak jelas sumbernya, debugging sulit"

---
finding_id: ARCH-A12
title: Frontend mempunyai 60+ variabel global (Zero Module)
description: File javascript dimuat ke dalam global name space HTML satu demi satu (classic scripts). Semua objek (store, ws, localAudio) dilempar bertumpuk menaikkan peluang collision, tak punya encapsulation, dan tak bisa dilakukan unit test.
claimed_location: web/static/js/*.js
claimed_severity: MEDIUM
source_section: TEMUAN A-12 — MEDIUM
raw_quote: "Tidak ada encapsulation. Setiap file bisa membaca/menulis store, ws, localAudio, dll. Naming collision tidak terdeteksi sampai runtime."

---
finding_id: ARCH-A13
title: DiscoverService.get_featured_genres() menggunakan statment print standar
description: Alih-alih memakai sistem logger bawaan (logger.error()), fungsi menangkap galat dengan sekadar di-print biasa. Alhasil monitoring metrics tidak pernah menyimpan event error tersebut dalam logs/app.log produksi.
claimed_location: server/services/discover_service.py (baris 121)
claimed_severity: MEDIUM
source_section: TEMUAN A-13 — MEDIUM
raw_quote: "Error di produksi tidak masuk ke log file (logs/app.log), tidak masuk ke monitoring Prometheus. Silent failure"

---
finding_id: ARCH-A14
title: CacheResolver._fetching tidak dilengkapi pengaman lock atomic asyncio
description: Dictionary _fetching rentan race condition dalam blok asyncio karena dua coroutine bisa melewati pengecekan variabel sebelum sempat mengunci, yang pada akhirnya malah menciptakan overhead query yt-dlp ganda untuk video yang sama.
claimed_location: cache/resolver.py (baris 32–38)
claimed_severity: MEDIUM
source_section: TEMUAN A-14 — MEDIUM
raw_quote: "race window antara check dan set... Check dan set pada _fetching dict tidak atomic dalam asyncio"

---
finding_id: ARCH-A15
title: start.py merupakan monolith launcher berisi 31.000 baris kode
description: File launcher sangat raksasa sampai 31K baris karena ia menggabungkan deteksi cross-platform ke satu lokasi sentral tanpa modularitas. File jadi tak bisa diuji secara terpisah dan membuang performa.
claimed_location: start.py
claimed_severity: MEDIUM
source_section: TEMUAN A-15 — MEDIUM
raw_quote: "File 31K baris sulit di-review, sulit di-test, sulit di-maintain. Bertentangan dengan SRP"

---
finding_id: ARCH-A16
title: Listener Event plugin mengkonsumsi performa linear berulang (O(n))
description: SponsorBlockHandler dan LyricsFetcher mendaftar diri pada frekuensi TrackProgressEvent (setiap ~330ms) lalu menjalankan scan sekuensial linear (for loop) di dalam list array yang panjang, memberatkan kinerja I/O player seiring waktu berjalan.
claimed_location: plugins/sponsorblock.py (baris 19), plugins/lyrics.py (baris 22)
claimed_severity: MEDIUM
source_section: TEMUAN A-16 — MEDIUM
raw_quote: "Setiap progress tick... memanggil _on_progress di dua plugin. Jika ada banyak segment SponsorBlock, inner loop bisa berat"

---
finding_id: ARCH-A17
title: Tipe data field is_favorite bercampur inkonsisten
description: Field is_favorite di-anotasikan sebagai tipe integer Optional[int], tetapi pada saat casting serialisasi JSON (to_dict) dipaksa dilempar jadi boolean. Ini menyebabkan ambiguitas yang tak terjelaskan saat dioper ke state lain.
claimed_location: core/state.py (baris 35, 52)
claimed_severity: LOW
source_section: TEMUAN A-17 — LOW
raw_quote: "is_favorite kadang int (0/1), kadang bool. to_dict() menggunakan bool(self.is_favorite) tapi field adalah Optional[int]"

---
finding_id: ARCH-A18
title: EventBus.subscribe() dengan tipe closure tidak terlindungi garbage collector
description: Lambda atau fungsi nested tak berstatus unbound method yang didaftarkan pada event_bus diikat secara statis (strong reference), tidak terserap oleh clean up weakref, sehingga menimbulkan akumulasi memory leak.
claimed_location: core/event_bus.py (baris 17–20)
claimed_severity: LOW
source_section: TEMUAN A-18 — LOW
raw_quote: "Jika handler adalah lambda atau nested function... weakref tidak digunakan. Lambda/closure yang tidak di-reference di luar akan ter-GC"

---
finding_id: ARCH-A19
title: Handler EnqueueGenreSongs menyebabkan eksekusi CommandBus Race 
description: Fungsi mengeksekusi urutan modifikasi mode secara serial (SetModeCommand lalu QueueReplaceCommand lalu QueueSelectCommand). Hal ini membuat celah terbuka pada selipan event websocket lain, memungkinkan korupsi urutan antrian queue jika terjadi secara paralel.
claimed_location: server/handlers/ws/queue_handlers.py (baris 54–59)
claimed_severity: MEDIUM
source_section: TEMUAN A-19 — ARCHITECTURAL
raw_quote: "3 command_bus.execute() berurutan tanpa lock. Jika WS command lain masuk di antara perintah kedua dan ketiga, state queue bisa corrupt"


Total temuan diekstrak dari DOKUMEN 4 — Code Smell Audit: 25

---
finding_id: CS-001
title: God Class pada ServerManagerWindow
description: ServerManagerWindow bertindak sebagai God Class dengan menangani event, dependency, proses, password, dan dialog (866 baris) dalam satu file. Tidak ada pemisahan Single Responsibility Principle.
claimed_location: start.py (baris 1–866)
claimed_severity: HIGH
source_section: CS-001 — God Class: ServerManagerWindow
raw_quote: "Ini adalah God Class murni — satu kelas yang tahu dan melakukan segalanya."

---
finding_id: CS-002
title: AppState menderita Primitive Obsession dan Large Class
description: AppState menyatukan player state, UI state, download state, dan network state menjadi satu struct yang tidak modular. Kelas lain harus memuat keseluruhan state hanya untuk membaca sebagian state spesifik.
claimed_location: core/state.py
claimed_severity: MEDIUM
source_section: CS-002 — God Class: AppState (Primitive Obsession + Large Class)
raw_quote: "Ini campuran domain berbeda tanpa pemisahan... setiap modul yang ingin mengakses satu aspek harus import seluruh AppState."

---
finding_id: CS-003
title: serve_stream bertindak sebagai God Function
description: Satu fungsi sepanjang ~130 baris meng-handle banyak lapisan secara manual meliputi validasi ID, rate limit, proxying, Etag, path check, dsb.
claimed_location: server/handlers/http.py (baris serve_stream)
claimed_severity: HIGH
source_section: CS-003 — God Function: serve_stream
raw_quote: "Ini adalah God Function — terlalu banyak tanggung jawab."

---
finding_id: CS-004
title: Method handle_auth memiliki siklus proses berlapis (Long Method)
description: Logika handle_auth sangat panjang karena memuat session checking, sleep penalty, validasi credensial, pruning, dan response generation sekaligus.
claimed_location: server/handlers/auth.py
claimed_severity: MEDIUM
source_section: CS-004 — Long Method: handle_auth
raw_quote: "Terlalu banyak tahap dalam satu alur."

---
finding_id: CS-005
title: Handlers websocket melempar Long Parameter List secara terpusat
description: Setiap WS handler diinisialisasi dengan tujuh parameter serupa yang tidak semuanya digunakan, memaksakan interface pattern secara artifisial.
claimed_location: server/handlers/ws/
claimed_severity: HIGH
source_section: CS-005 — Long Parameter List (Systemic): WS Handlers
raw_quote: "Setiap WS handler memiliki signature identik dengan 7 parameter... Ini adalah code smell sistemik"

---
finding_id: CS-006
title: _build_ui membangun semua interface dalam satu method
description: Method perenderan antarmuka utama menangani semuanya tanpa didelegasikan sehingga modifikasi di satu lokasi sangat rapuh terhadap blok sekitar.
claimed_location: start.py (method _build_ui)
claimed_severity: MEDIUM
source_section: CS-006 — Long Method: _build_ui di ServerManagerWindow
raw_quote: "Satu method membangun seluruh UI dari header sampai log panel. Tidak ada pemisahan per seksi UI."

---
finding_id: CS-007
title: Validasi regex video_id diulang (Duplicate Code)
description: Format validasi (seperti ^[a-zA-Z0-9_-]{11}$) tersebar di berbagai layer dengan penyesuaian kecil berbeda (contohnya range limit 1-64 vs 11).
claimed_location: core/value_objects.py, server/handlers/ws/discover_handlers.py, engine/ytdlp_client.py
claimed_severity: MEDIUM
source_section: CS-007 — Duplicate Code: Validasi video_id Regex
raw_quote: "Jika format berubah (misal 12 karakter), harus diubah di semua tempat — risiko inkonsistensi."

---
finding_id: CS-008
title: Penulisan file password administrator direplikasi berkali-kali
description: Fungsi write untuk meng-generate dan me-render admin_password.txt dijalankan lewat implementasi file I/O repetitif (3 lokasi).
claimed_location: config.py, start.py
claimed_severity: MEDIUM
source_section: CS-008 — Duplicate Code: Password File Logic
raw_quote: "Logic untuk generate, hash, dan simpan password admin... ditulis 3 kali"

---
finding_id: CS-009
title: Dua implementasi mekanik rate limit yang berbeda secara fungsional
description: Sistem memisahkan filter rate limit dengan collections.defaultdict(list) secara global di satu modul dan dengan dict command_history di ConnectionManager di file berbeda, yang bisa inkonsisten.
claimed_location: server/handlers/http.py, server/middleware.py
claimed_severity: MEDIUM
source_section: CS-009 — Duplicate Code: defaultdict Rate Limit — 2 Implementasi Berbeda
raw_quote: "Rate limiting diimplementasikan dua kali dengan mekanisme berbeda... Keduanya beroperasi dengan sliding window 60 detik"

---
finding_id: CS-010
title: is_favorite terjebak sebagai integer alih-alih boolean (Primitive Obsession)
description: Konversi tak berujung antara integer(0,1) dan boolean terus terjadi pada track item di berbagai layer akibat deklarasi is_favorite menggunakan Optional[int].
claimed_location: core/state.py, cache/db.py, cache/repositories/
claimed_severity: MEDIUM
source_section: CS-010 — Primitive Obsession: is_favorite sebagai int bukan bool
raw_quote: "Field is_favorite didefinisikan sebagai Optional[int] di TrackInfo padahal semantiknya boolean."

---
finding_id: CS-011
title: Variabel environment memakai legacy brand string literal (ytgui_*)
description: Variabel pada frontend masih menyimpan legacy label "ytgui" berupa magic string, yang jika akan migrasi atau dihapus akan memakan refactor berat ke depan.
claimed_location: web/static/js/ws.js, web/static/js/services/auth.js
claimed_severity: MEDIUM
source_section: CS-011 — Primitive Obsession: Magic String "ytgui_*" di Frontend
raw_quote: "Kunci localStorage menggunakan string literal tersebar... berasal dari nama lama sistem"

---
finding_id: CS-012
title: Parameter temporal angka dibiarkan sebagai Magic Number di hardcode
description: Timeout, limits, TTL tidak memiliki constanta berpusat (seperti 300, 14400, dll), menyulitkan pengaturan operasional dan skalabilitas server.
claimed_location: Tersebar di seluruh codebase
claimed_severity: MEDIUM
source_section: CS-012 — Magic Number: Timeout/Delay Hardcoded
raw_quote: "Banyak angka timeout, delay, dan limit ditulis langsung tanpa nama konstanta."

---
finding_id: CS-013
title: String type event dipatok literal pada switch frontend (Magic String)
description: Identifier tipe di WebSocket handler menggunakan label text mati ("progress", "lyrics"). Sedikit saja typo atau update API, frontend akan silent error.
claimed_location: web/static/js/ws.js
claimed_severity: MEDIUM
source_section: CS-013 — Magic String: Status dan Event Type sebagai Literal
raw_quote: "Message type dari server... ditulis sebagai string literal di switch-case."

---
finding_id: CS-014
title: Feature envy koneksi db pada discover_handlers
description: Kode WS handler tiba-tiba memotong lapisan interaksi dan langsung merengkuh akses await db.conn.execute(...) di dalamnya, memblokir fleksibilitas modular.
claimed_location: server/handlers/ws/discover_handlers.py
claimed_severity: MEDIUM
source_section: CS-014 — Feature Envy: discover_handlers.py Akses Langsung ke db.conn
raw_quote: "Handler mengakses db.conn... secara langsung, melewati abstraksi repository."

---
finding_id: CS-015
title: Import sqlite langsung di dalam controller UI
description: Metode pada tampilan antar-muka mengambil library sqlite3 secara sporadis untuk memanipulasi direktori tanpa melalui business engine.
claimed_location: start.py (ServerManagerController.on_reset_password)
claimed_severity: MEDIUM
source_section: CS-015 — Feature Envy: on_reset_password Akses Langsung Database SQLite
raw_quote: "GUI controller mengimport dan menggunakan sqlite3 secara langsung untuk menghapus sessions."

---
finding_id: CS-016
title: Track pada AppState diset paksa oleh Websocket
description: Handler mem-bypass event bus mutasi saat mengubah kondisi favorite pada variabel lagu, mencemari status dan menghindari arsitektur asinkron yang telah ada.
claimed_location: server/handlers/ws/discover_handlers.py
claimed_severity: MEDIUM
source_section: CS-016 — Feature Envy: AppState di Tulis Langsung dari Handler
raw_quote: "Handler WebSocket memutasi state.current_track secara langsung dari luar domain engine."

---
finding_id: CS-017
title: resumeVisualizerLoop tak difungsikan (Dead Code)
description: Subrutin untuk mengekstrak atau kembali ke pemutar gelombang mati di kode statis front-end tanpa pemanggilan dari handler mana pun.
claimed_location: web/static/js/audio.js
claimed_severity: LOW
source_section: CS-017 — Dead Code: resumeVisualizerLoop Tidak Dipanggil
raw_quote: "Fungsi resumeVisualizerLoop terdefinisi namun tidak dipanggil dari mana pun"

---
finding_id: CS-018
title: unlockBrowserAudio nganggur (Dead Code)
description: Prosedur tersebut disetel sebagai variabel global browser JS dan tak pernah dideklarasikan interaksinya dengan DOM atau listener.
claimed_location: web/static/js/audio.js
claimed_severity: LOW
source_section: CS-018 — Dead Code: unlockBrowserAudio Terdefinisi tapi Tidak Dipakai
raw_quote: "unlockBrowserAudio(forcePlay) tidak muncul sebagai pemanggil di file JS manapun"

---
finding_id: CS-019
title: _last_stdout_line memonitor log tak terpakai (Dead Code)
description: Variabel pada instance server UI hanya mendata line out tanpa sempat memanipulasinya atau membacanya sebelum loop berikutnya.
claimed_location: start.py (ServerManagerController)
claimed_severity: LOW
source_section: CS-019 — Dead Code: _last_stdout_line di ServerManagerController
raw_quote: "Field self._last_stdout_line di-assign... tapi tidak pernah dibaca atau digunakan"

---
finding_id: CS-020
title: Deklarasi sub-modul repository dini yang menyesatkan
description: Pendefinisian awal parameter instance = None untuk variabel repository saat pemanggilan __init__ di class Database, alih-alih melempar delegasi parameter asli, membuat statis pointer tak bisa dilacak dan terlihat kosong.
claimed_location: cache/db.py
claimed_severity: LOW
source_section: CS-020 — Dead Code: self.tracks, self.sessions, self.discover di Database
raw_quote: "Atribut None awal ini menyesatkan... akses ke method-method repository dilakukan via __getattr__ proxy"

---
finding_id: CS-021
title: Inline import module asyncio
description: Fungsi memuat module asyncio di tengah scope definisi, menghasilkan inefisiensi pengerjaan cache library.
claimed_location: server/handlers/auth.py (baris 43), engine/download_manager.py
claimed_severity: LOW
source_section: CS-021 — Unused Import: import asyncio di dalam Method Body
raw_quote: "asyncio diimport di dalam body fungsi... setiap call ke fungsi ini memuat (atau lookup) modul"

---
finding_id: CS-022
title: Unused root module aiohttp import
description: Library ditarik keseluruhan walaupun tak dipakai secara namespace, memboroskan tree-shaking virtual machine python.
claimed_location: server/handlers/websocket.py (baris 5)
claimed_severity: LOW
source_section: CS-022 — Unused Variable: aiohttp Import di server/handlers/websocket.py
raw_quote: "import aiohttp dilakukan di top-level... aiohttp namespace tidak diakses langsung"

---
finding_id: CS-023
title: Komentar tambal sulam ditinggalkan menumpuk (Commented Code)
description: Informasi historikal patch masa lampau disembunyikan dalam code, bukan dititipkan sebagai dokumentasi git/CHANGELOG resmi.
claimed_location: server/handlers/http.py, web/static/js/ws.js, engine/mpv_controller.py
claimed_severity: LOW
source_section: CS-023 — Commented Code: Sisa Komentar PATCH
raw_quote: "Banyak komentar # PATCH-* yang menjelaskan \"dulu ada bug, sekarang sudah fix\"... seharusnya berada di git commit message"

---
finding_id: CS-024
title: Session tidak divalidasi dan berbentuk primitive string
description: Token dilempar cuma-cuma dari endpoint ke layer cache berupa string telanjang. Gagal memvalidasi atau mencegah token yang direkayasa pada sistem.
claimed_location: server/handlers/auth.py, cache/repositories/auth_repository.py
claimed_severity: LOW
source_section: CS-024 — Primitive Obsession: Session Token sebagai Raw String
raw_quote: "Session token dihandle sebagai str biasa... Tidak ada validasi format, panjang minimum, atau type"

---
finding_id: CS-025
title: Limit hardware suara tak berkoordinasi (MAX_VOLUME inkonsisten)
description: Variabel MAX_VOLUME memiliki batas berlebih 150 sementara casting value strictnya selalu turun (clamp) di batas limit 100. Hal ini menyebabkan error representatif pada AppState.volume atau bahkan bug perulangan render MPV.
claimed_location: core/constants.py, core/value_objects.py
claimed_severity: HIGH
source_section: CS-025 — Magic Number: MAX_VOLUME = 150 Inkonsisten dengan Volume(int) max 100
raw_quote: "MAX_VOLUME = 150 di constants.py berbeda dengan Volume(int) yang clamp ke max(0, min(100, int(value)))... Ini adalah BUG"


Total temuan diekstrak dari DOKUMEN 6 — Performance Audit: 18

---
finding_id: PERF-P01
title: Discover Queries Dieksekusi Secara Serial (N+1 Berganda)
description: Query discover ke SQLite (get_recent, get_favorites, dsb) dipanggil dengan eksekusi await berurutan, menimbulkan latensi hingga +80-200ms per panggilan karena penumpukan di environment single-connection.
claimed_location: server/handlers/ws/discover_handlers.py (baris 17–31)
claimed_severity: CRITICAL
source_section: P-01 — CRITICAL: Discover Queries Dieksekusi Secara Serial (N+1 Berganda)
raw_quote: "Setiap request DISCOVER dari klien menjalankan 5 query SQLite secara berurutan... masing-masing query menunggu yang sebelumnya selesai."

---
finding_id: PERF-P02
title: Full State Broadcast Setiap Toggle Favorite
description: Mengubah status 'favorite' satu trek memaksa router meneruskan status seluruh objek (termasuk queue dan lirik) ke semua klien tersambung. Overhead pengiriman ini dapat menunda koneksi 5-100ms per trigger akibat payload yang tak perlu.
claimed_location: server/handlers/ws/discover_handlers.py (baris 81–88)
claimed_severity: CRITICAL
source_section: P-02 — CRITICAL: Full State Broadcast Setiap Toggle Favorite
raw_quote: "sistem melakukan broadcast_state(state) ke semua klien aktif... payload bisa 5–50KB."

---
finding_id: PERF-P03
title: Seeding Database 1000 Songs dengan Serial INSERT (Startup Lambat)
description: Pemasukan bibit awal database tidak dioptimasi secara batch; fungsi berjalan repetitif per objek. Di kondisi I/O buruk, blokase load startup ini akan menjeda kesiapan server sampai sekitar semenit.
claimed_location: cache/db.py (baris 71–107)
claimed_severity: HIGH
source_section: P-03 — HIGH: Seeding Database 1000 Songs dengan Serial INSERT (Startup Lambat)
raw_quote: "menginsert 100 artists + ~1000 songs satu per satu... Ini berarti 1100+ round-trip ke SQLite engine."

---
finding_id: PERF-P04
title: 100 Artist + 100 Genre Dikirim ke Klien Setiap Discover
description: Pengiriman daftar discover tidak disaring. Penarikan langsung 100 items akan me-render terlalu banyak DOM Node hashtag-pill yang malah akan mencekik thread visual browser pada layar sempit.
claimed_location: core/constants.py (baris 13–14)
claimed_severity: HIGH
source_section: P-04 — HIGH: 100 Artist + 100 Genre Dikirim ke Klien Setiap Discover
raw_quote: "setiap request DISCOVER mengirim 200 objek dalam payload JSON... Ini juga di-render semuanya ke DOM sekaligus"

---
finding_id: PERF-P05
title: renderFullState() Merender Semua Komponen Tanpa Dirty Check
description: Tidak ada delta diff state (dirty tracking) saat menerima update, memaksa aplikasi javascript menjalankan siklus perenderan ke seluruh sub-layout, menyita frametime dan menimbulkan tampilan janky.
claimed_location: web/static/js/ws.js (baris 95–97 dan 147–157)
claimed_severity: HIGH
source_section: P-05 — HIGH: renderFullState() Merender Semua Komponen Tanpa Dirty Check
raw_quote: "Setiap state message... memicu renderFullState() yang memanggil 8 fungsi render sekaligus... menyebabkan layout thrashing"

---
finding_id: PERF-P06
title: JSON.stringify(track) di Setiap Render Item (Expensive per Frame)
description: Saat membangun antrean layout lagu (discover/recent), metadata direkam ke attribut JSON-text via stringify per baris objek secara simultan. Sangat mendegradasi resource memory-thread browser pada iterasi data berjumlah banyak.
claimed_location: web/static/js/render/discover.js (baris 126, 192, 412)
claimed_severity: HIGH
source_section: P-06 — HIGH: JSON.stringify(track) di Setiap Render Item (Expensive per Frame)
raw_quote: "Fungsi renderDiscoverTab()... memanggil JSON.stringify(track) untuk setiap item di setiap render cycle... operasi yang cukup mahal di main thread"

---
finding_id: PERF-P07
title: active_connections Adalah List, Bukan Set (O(n) Remove)
description: Struktur data tracking konektor terpusat disimpan pada native List object di Python sehingga pencabutan dan scan entitas client membutuhkan komputasi linear. Rentan menyebabkan overhead O(n).
claimed_location: server/handlers/websocket.py (baris 25, 40–41)
claimed_severity: HIGH
source_section: P-07 — HIGH: active_connections Adalah List, Bukan Set (O(n) Remove)
raw_quote: "Saat klien disconnect, list.remove(ws) melakukan linear scan O(n) untuk menemukan elemen."

---
finding_id: PERF-P08
title: extractDominantColor() Membuat Canvas 50x50 di Main Thread per Track Change
description: Pembacaan warna latar memblok render visual utama karena instruksi get_image_data tak memakai pekerja paralel offscreen, melainkan berjalan secara sekuensial. Jeda terasa berat untuk UI animasi transisi sampul.
claimed_location: web/static/js/utils.js (fungsi extractDominantColor)
claimed_severity: MEDIUM
source_section: P-08 — MEDIUM: extractDominantColor() Membuat Canvas 50×50 di Main Thread per Track Change
raw_quote: "menggunakan synchronous canvas pixel read getImageData() di main thread... memblok main thread dan menginvalidate GPU compositing"

---
finding_id: PERF-P09
title: loadLazyCovers() Dipanggil Berulang Kali per Render Cycle
description: Inisiasi ulang image lazy_load melanda seluruh Node Document secara konstan setiap saat (Full DOM Scan), karena ia diletakkan tepat pada akhir dua prosedur render tab yang berbeda tapi eksekusinya tumpang tindih dalam satu event loop frame.
claimed_location: web/static/js/render/discover.js (baris 218, 242)
claimed_severity: MEDIUM
source_section: P-09 — MEDIUM: loadLazyCovers() Dipanggil Berulang Kali per Render Cycle
raw_quote: "melakukan document.querySelectorAll... DAN dipanggil di akhir renderDiscoverTab() DAN renderRecentRow()."

---
finding_id: PERF-P10
title: Bundle JS Tidak di-Minify dalam Development Build (105KB Unminified)
description: Bundle hasil deploy tidak disusutkan, padahal instruksi scriptnya seakan meminta minification. Ini berdampak besar jika cache rusak karena bobot unduh akan melonjak.
claimed_location: web/static/js/bundle.js, package.json
claimed_severity: MEDIUM
source_section: P-10 — MEDIUM: Bundle JS Tidak di-Minify dalam Development Build (105KB Unminified)
raw_quote: "File bundle.js saat ini 105,303 bytes (105KB) tidak terkompresi dan berisi komentar, whitespace, dan nama variabel panjang."

---
finding_id: PERF-P11
title: switchTab('discover') Memicu DISCOVER Request Setiap Kali Tab Diklik
description: Transisi antar-menu pada aplikasi tidak dicadangkan pada cache memory atau memiliki throttle window, menembakkan request data dan memboros kinerja jaringan client dan server terus-menerus.
claimed_location: web/static/js/main.js (baris 53–56)
claimed_severity: MEDIUM
source_section: P-11 — MEDIUM: switchTab('discover') Memicu DISCOVER Request Setiap Kali Tab Diklik
raw_quote: "Setiap kali user switch ke tab home atau discover, wsSend(WS_ACTIONS.DISCOVER) langsung dieksekusi... Tidak ada cooldown atau check apakah data sudah fresh."

---
finding_id: PERF-P12
title: Missing Index untuk Favorites Query
description: Tabel lagu SQL tidak dioptimasi menggunakan partial index komposit pada pola filter 'is_favorite = 1'. Server terpaksa membaca seluruh database (full scan), memunculkan hambatan pada jumlah entri masif.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_section: P-12 — MEDIUM: Missing Index untuk Favorites Query
raw_quote: "Kolom is_favorite tidak memiliki index spesifik untuk nilai = 1. SQLite harus full-scan tabel tracks untuk setiap favorites request."

---
finding_id: PERF-P13
title: Service Worker Precache 20+ File CSS Terpisah (Tidak Perlu)
description: Precache array module mengundang banyak sekali HTTP Request karena file sumber (tokens, base) dipaksa di-precache meskipun kesemuanya sebenarnya sudah terserap ke dalam bundle.css.
claimed_location: web/static/sw.js (baris 4–29)
claimed_severity: MEDIUM
source_section: P-13 — MEDIUM: Service Worker Precache 20+ File CSS Terpisah (Tidak Perlu)
raw_quote: "Service Worker di sw.js me-precache 20+ file CSS individual... Padahal semua CSS sudah di-bundle ke bundle.css."

---
finding_id: PERF-P14
title: _stream_rate_limit Dictionary Tidak Di-cleanup (Memory Leak Bertahap)
description: Key IP Address penanda trafik stream dari _stream_rate_limit akan tetap tersimpan meski timestamp-nya sudah dieliminasi, menguras RAM berangsur-angsur apabila pengunjung/konektor berganti IP tanpa batas.
claimed_location: server/handlers/http.py (baris 16–20)
claimed_severity: MEDIUM
source_section: P-14 — MEDIUM: _stream_rate_limit Dictionary Tidak Di-cleanup (Memory Leak Bertahap)
raw_quote: "Cleanup hanya memfilter timestamps dalam list, bukan menghapus entries dengan empty list... kunci IP-nya tidak pernah dihapus"

---
finding_id: PERF-P15
title: _pending Dict di MpvController Tidak Dibersihkan Saat Timeout
description: Block future asinkron _pending berpotensi menggantung tak terhapus jika terinterupsi intervensi diluar jangkauan TimeOut (misal dari CancelledError yang membunuh proses secara mutlak), berujung memori membengkak.
claimed_location: engine/mpv_controller.py (baris 198–209)
claimed_severity: MEDIUM
source_section: P-15 — MEDIUM: _pending Dict di MpvController Tidak Dibersihkan Saat Timeout
raw_quote: "jika _send_request di-cancel dari luar... finally block tidak menjamin cleanup... _pending bisa accumulate stale futures"

---
finding_id: PERF-P16
title: DiscoverService Di-instantiasi Ulang di Setiap Request
description: Module fungsional DiscoverService yang seharusnya cuma sebagai service stateless instansi Singleton, justru di-build berulang setiap kali masuknya request. Ini membuang waktu eksekusi VM internal (meski relatif kecil).
claimed_location: server/handlers/ws/discover_handlers.py (baris 17)
claimed_severity: LOW
source_section: P-16 — LOW: DiscoverService Di-instantiasi Ulang di Setiap Request
raw_quote: "_build_discover_payload(db) membuat objek DiscoverService(db) baru setiap kali dipanggil."

---
finding_id: PERF-P17
title: Bundle CSS 55KB — Tidak Perlu Critical CSS Split
description: Sistem memuat semua aturan UI desktop & tablet menjadi satu kesatuan di mobile tanpa media selector split query. Peniadaan pemisahan gaya per-platform murni memperberat blok render tag Head di browser low-end.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: LOW
source_section: P-17 — LOW: Bundle CSS 55KB — Tidak Perlu Critical CSS Split
raw_quote: "bundle.css sebesar 55KB... di-load secara blocking di <head>. Platform-specific CSS... di-load semua"

---
finding_id: PERF-P18
title: getHashtagColor() Warna Acak Tidak Konsisten Antar Session
description: Warna penanda chip genre dirender dengan Math.random() in-memory alih-alih di-hash statis dari title-nya, mengakibatkan pergeseran tone warna kapan pun DOM berubah atau browser me-load halaman.
claimed_location: web/static/js/render/discover.js (baris 1–7)
claimed_severity: LOW
source_section: P-18 — LOW: getHashtagColor() Warna Acak Tidak Konsisten Antar Session
raw_quote: "Setiap page refresh, warna berubah — tidak konsisten secara visual... karena random, bukan deterministik hash"


Total temuan diekstrak dari DOKUMEN 7 — Database Audit: 17

---
finding_id: DB-001
title: Single Persistent Connection: Write Bottleneck & Deadlock Risk
description: Seluruh aktivitas database (read dan write) dibebankan pada satu pool aiosqlite, menyebabkan seluruh eksekusi coroutine harus antre sekuensial. Saat workload tinggi, bisa mengunci seluruh jalannya aplikasi secara paralel.
claimed_location: cache/db.py
claimed_severity: CRITICAL
source_section: DB-001 — Single Persistent Connection: Write Bottleneck & Deadlock Risk
raw_quote: "Semua operasi database (read dan write) berbagi satu aiosqlite connection... satu connection tunggal berarti semua coroutine antre secara serial."

---
finding_id: DB-002
title: Tidak Ada busy_timeout PRAGMA
description: Konfigurasi SQLite belum mensetting delay limit pada concurrent writes, yang menyebabkan sistem merespons error SQLITE_BUSY secara langsung saat menimpa data, berpotensi pada kehilangan data dan crash sepihak.
claimed_location: cache/db.py — fungsi init()
claimed_severity: HIGH
source_section: DB-002 — Tidak Ada busy_timeout PRAGMA
raw_quote: "Tanpa PRAGMA busy_timeout, jika ada dua proses/thread mencoba write... SQLite langsung return SQLITE_BUSY (error) alih-alih menunggu."

---
finding_id: DB-003
title: Tidak Ada Migration System
description: Pembaharuan struktur kolom berjalan mandiri dan tidak sinkron karena tak ada versioning. Manipulasi ALTER TABLE langsung menumpuk dengan schema.sql mengakibatkan error pada eksekusi deploy antar pengguna lama/baru.
claimed_location: cache/db.py
claimed_severity: CRITICAL
source_section: DB-003 — Tidak Ada Migration System
raw_quote: "Tidak ada versioning, tidak ada rollback, tidak ada tracking versi schema... Jika kolom yang sama ditambahkan dua kali... dapat terjadi error"

---
finding_id: DB-004
title: Schema Drift: schema.sql vs export_to_sqlite.py
description: Definisi pembuatan tabel database terbelah ke dalam dua file berbeda dengan properti index dan constraint FK yang kontradiktif, memicu duplikasi sekaligus risiko korupsi pada data saat seed manual di ekspor.
claimed_location: data/export_to_sqlite.py, cache/schema.sql
claimed_severity: HIGH
source_section: DB-004 — Schema Drift: schema.sql vs export_to_sqlite.py
raw_quote: "Dua file mendefinisikan schema tabel yang sama... secara terpisah. Keduanya tidak sinkron"

---
finding_id: DB-005
title: INSERT OR REPLACE pada Tabel artists: Data Loss Risk
description: Mekanisme override data artis menghapus baris lama secara total dan membuat entri kosong baru. Variabel seperti statistik click_count akan terhapus tak bersisa di setiap perulangan seed.
claimed_location: cache/db.py — _seed_initial_data()
claimed_severity: HIGH
source_section: DB-005 — INSERT OR REPLACE pada Tabel artists: Data Loss Risk
raw_quote: "OR REPLACE di SQLite bekerja dengan cara DELETE + INSERT — ini berarti click_count... akan direset ke NULL setiap kali re-seed"

---
finding_id: DB-006
title: Race Condition: evict_stale_tracks() SELECT + DELETE Non-Atomic
description: Proses pencarian entri yang kedaluwarsa lalu penghapusannya dijalankan dalam dua query terpisah tanpa isolasi lock, memberi celah file termodifikasi di antaranya untuk terhapus tanpa ampun.
claimed_location: cache/repositories/track_repository.py
claimed_severity: HIGH
source_section: DB-006 — Race Condition: evict_stale_tracks() SELECT + DELETE Non-Atomic
raw_quote: "Antara SELECT dan DELETE, track yang baru saja mulai diplay... bisa ikut terhapus karena data masih stale"

---
finding_id: DB-007
title: toggle_favorite() Tidak Menggunakan Transaksi Eksplisit
description: Eksekusi tombol favorite tidak memakai batasan urutan (BEGIN EXCLUSIVE/IMMEDIATE). Double tap berurutan akan membaca cache yang sama dari state terdahulu tanpa mengunci nilainya, menggagalkan togle ganda.
claimed_location: cache/repositories/track_repository.py
claimed_severity: MEDIUM
source_section: DB-007 — toggle_favorite() Tidak Menggunakan Transaksi Eksplisit
raw_quote: "Dua request toggle_favorite yang datang hampir bersamaan... keduanya membaca is_favorite yang sama dan menghasilkan hasil yang salah"

---
finding_id: DB-008
title: sessions Table: Tidak Ada Index pada expires_at
description: Pembersihan sesi timeout berpatokan pada kalkulasi data kolom expires_at yang tidak diindeks, memaksa pindaian basis data menyeluruh terhadap tiap sesi aktif saat cleanup berjalan.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_section: DB-008 — sessions Table: Tidak Ada Index pada expires_at
raw_quote: "Tanpa index pada expires_at, ini adalah full table scan setiap kali cleanup berjalan."

---
finding_id: DB-009
title: Missing Index: tracks.is_favorite untuk Query Favorites
description: Parameter penanda favorite pada daftar lagu tidak ditopang tabel indeks sama sekali. Daftar lagu terfavorit hanya dapat disajikan dengan full table scan, yang melambat linear seiring data.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_section: DB-009 — Missing Index: tracks.is_favorite untuk Query Favorites
raw_quote: "Tidak ada index pada kolom is_favorite. Setiap query yang memfilter favorite tracks... harus full table scan."

---
finding_id: DB-010
title: upsert_track() Selalu Update last_played
description: Rekaman waktu putar dimanipulasi asal ketika metadata disentuh dari upsert_track(), meski lagu hanya sekadar diresolve tanpa benar-benar diputar, merusak integritas algoritma riwayat play_count dan cache cleanup.
claimed_location: cache/repositories/track_repository.py
claimed_severity: MEDIUM
source_section: DB-010 — upsert_track() Selalu Update last_played
raw_quote: "Ini menyebabkan track yang hanya di-resolve URL-nya... memiliki last_played yang ter-update, mengacaukan sorting"

---
finding_id: DB-011
title: artists.id bukan AUTOINCREMENT: Risk pada Re-seed
description: Kolom ID artis digantungkan manual pada parameter string JSON yang tidak di-generate dinamis secara inkremental, rentan menubruk foreign key dan menimbulkan invalid references bila json dirubah/digabung.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_section: DB-011 — artists.id bukan AUTOINCREMENT: Risk pada Re-seed
raw_quote: "id didefinisikan sebagai INTEGER PRIMARY KEY (tanpa AUTOINCREMENT)... bisa terjadi ID conflict atau orphaned foreign key references."

---
finding_id: DB-012
title: __getattr__ Proxy di Database: Anti-Pattern Berbahaya
description: Pengkabelan virtual instance method lewat getattr ke sub-modul repository membuat trace log samar dan menyebabkan ambigu penimpaan namespace antar file di dalam class Database.
claimed_location: cache/db.py
claimed_severity: MEDIUM
source_section: DB-012 — __getattr__ Proxy di Database: Anti-Pattern Berbahaya
raw_quote: "Ini menyembunyikan dependency graph, membuat stack trace sulit dibaca, dan dapat menyebabkan metode yang salah terpanggil"

---
finding_id: DB-013
title: verify_session(): Side Effect Write dalam Read Operation
description: Pembacaan sesi via metode token murni menyertakan fungsi write database DELETE sepihak tanpa disangka. Menyalahi pedoman prinsip pemisahan baca-tulis serta memboros request tak terpakai.
claimed_location: cache/repositories/auth_repository.py
claimed_severity: MEDIUM
source_section: DB-013 — verify_session(): Side Effect Write dalam Read Operation
raw_quote: "verify_session() melakukan DELETE... sebagai side effect dari operasi baca. Ini melanggar prinsip Command-Query Separation."

---
finding_id: DB-014
title: get_random_songs(): CTE dengan RANDOM() Tidak Deterministik & Slow
description: Komputasi fungsi RANDOM di query SQLite dipaksa pada level setiap objek lagu saat menyusun radio otomatis, menyedot performa komputasi linear penuh pada semua tracks di dataset dan murni tidak skalabel.
claimed_location: cache/repositories/discover_repository.py
claimed_severity: MEDIUM
source_section: DB-014 — get_random_songs(): CTE dengan RANDOM() Tidak Deterministik & Slow
raw_quote: "RANDOM() dievaluasi per-row untuk setiap partition, yang menyebabkan full table scan pada songs... ini menjadi O(N) operation"

---
finding_id: DB-015
title: evict_stale_tracks(): File Delete Sebelum DB Commit
description: Urutan logika hapus track membuang file lokal sebelum komitmen DB terkunci sukses. Sebuah crash tak terduga pasca unlink file tapi pra-commit sql akan memunculkan file hantu di DB yang mustahil diakses.
claimed_location: cache/repositories/track_repository.py
claimed_severity: MEDIUM
source_section: DB-015 — evict_stale_tracks(): File Delete Sebelum DB Commit
raw_quote: "Jika aplikasi crash setelah file dihapus tapi sebelum DB commit... menyebabkan inconsistency antara DB dan filesystem."

---
finding_id: DB-016
title: Tidak Ada Normalisasi: TrackInfo.artist Duplikat Data
description: Rekaman identitas nama artis di tabel track disimpan ke dalam kolom string sembarang dibanding memanfaatkan parameter id Foreign Key, menimbulkan ambiguitas statisik dan huruf (case-sensitive) yang tak terkumpul.
claimed_location: cache/schema.sql
claimed_severity: LOW
source_section: DB-016 — Tidak Ada Normalisasi: TrackInfo.artist Duplikat Data
raw_quote: "kolom artist disimpan sebagai TEXT bebas (tidak ada FK ke tabel artists)... Nama artis bisa tidak konsisten"

---
finding_id: DB-017
title: CacheResolver._fetching: Memory Leak jika Exception
description: Event asinkron fetch URL dapat menimbulkan siklus tak berujung (infinite recursion) dari resolusi gagal ganda, mengekskalasi kebocoran request di memori dan menguasai queue proses thread lokal.
claimed_location: cache/resolver.py
claimed_severity: MEDIUM
source_section: DB-017 — CacheResolver._fetching: Memory Leak jika Exception
raw_quote: "Jika resolve yang pertama gagal tapi event di-set, resolve kedua (recursive) akan mencoba fetch lagi... tidak ada proteksi terhadap infinite recursion"


Total temuan diekstrak dari DOKUMEN 8 — API Audit: 18

---
finding_id: API-01
title: TrackInfo.from_dict() Menerima stream_url dari Client (Injection Risk)
description: Metode pembacaan state mengizinkan input "stream_url" maupun "local_path" tak tersaring diserap langsung dari perintah yang dikirim klien (client controlled), membuka manipulasi state maupun file system jika tersimpan via database upsert.
claimed_location: core/state.py (baris 58-76), server/handlers/ws/playback_handlers.py, dll
claimed_severity: CRITICAL
source_section: API-01 — CRITICAL: TrackInfo.from_dict() Menerima stream_url dari Client (Injection Risk)
raw_quote: "field stream_url dan local_path dari klien bisa memengaruhi log, state, dan edge-case alur resolver yang belum ter-audit penuh"

---
finding_id: API-02
title: /api/stream/{video_id} Tidak Memerlukan Autentikasi
description: Titik henti stream bersifat terbuka lebar ke publik. Semua yang memiliki kode identifikasi Youtube acak dapat memerintahkan server menarik data url di latar belakang, menguras sumber daya secara ilegal serta melanggar term of service YouTube tanpa jejak token.
claimed_location: server/handlers/http.py (serve_stream baris 50-190), server/app.py (baris 38)
claimed_severity: CRITICAL
source_section: API-02 — CRITICAL: /api/stream/{video_id} Tidak Memerlukan Autentikasi
raw_quote: "Endpoint /api/stream/{video_id} bersifat public tanpa autentikasi. Siapa saja... dapat langsung mengakses stream audio — termasuk memicu yt-dlp"

---
finding_id: API-03
title: Session Token Hanya 16 Bytes Hex (32 Karakter) — Terlalu Pendek
description: Token sesi memakai deret hex generik 16-bit (128 bits entropy) padahal saran standard menuntut sekurang-kurangnya 256 bits, dan token diamankan pada localStorage frontend dengan risiko serangan XSS yang leluasa menyalinnya.
claimed_location: server/handlers/auth.py (baris 58), web/static/js/ws.js (baris 24)
claimed_severity: HIGH
source_section: API-03 — HIGH: Session Token Hanya 16 Bytes Hex (32 Karakter) — Terlalu Pendek
raw_quote: "token disimpan di localStorage/sessionStorage... tanpa flags HttpOnly atau Secure, membuat token rentan terhadap XSS."

---
finding_id: API-04
title: Tidak Ada API Versioning
description: Tidak dijumpai pengenal awalan versi baik di API routing HTTP (e.g., /v1/) dan payload soket websocket. Saat interface bermutasi, server tak bisa memberikan penanganan berjenjang kepada klien aplikasi lawas.
claimed_location: server/routes.py, core/ws_actions.py
claimed_severity: HIGH
source_section: API-04 — HIGH: Tidak Ada API Versioning
raw_quote: "Saat breaking change terjadi... semua klien lama akan rusak sekaligus tanpa fallback path."

---
finding_id: API-05
title: Error Response Format Tidak Konsisten
description: Sistem penanganan balasan kesalahan bercabang ke dalam tiga gaya yang sangat berbeda di backend (sebagai JSON error di HTTP, pesan error spesifik WS, atau pesan log pasif). Menjadikan client sulit memetakannya.
claimed_location: server/handlers/ws/utils.py, server/handlers/websocket.py (baris 123-130), server/handlers/event_listeners.py
claimed_severity: HIGH
source_section: API-05 — HIGH: Error Response Format Tidak Konsisten
raw_quote: "Terdapat 3 format error berbeda yang digunakan secara tidak konsisten... Klien harus menangani 3 pola berbeda."

---
finding_id: API-06
title: Rate Limiting WS dan HTTP Berbeda Implementasi, Tidak Sinkron
description: Proteksi traffic beroperasi ganda dengan standar yang tak sinkron (30 requests/60 detik untuk WS, 20 requests/60 detik untuk HTTP stream) di layer mandiri, sementara endpoints vital /health maupun /metrics dilepas tanpa pengawasan pembatasan trafik sama sekali.
claimed_location: server/middleware.py, server/handlers/http.py, core/constants.py
claimed_severity: HIGH
source_section: API-06 — HIGH: Rate Limiting WS dan HTTP Berbeda Implementasi, Tidak Sinkron
raw_quote: "Terdapat dua sistem rate limit independen yang tidak berbagi state... Tidak ada rate limit untuk endpoint /health dan /metrics"

---
finding_id: API-07
title: Tidak Ada HTTP Request Timeout untuk Proxy Stream
description: Sambungan eksternal get-request ke server stream Youtube tidak mencantumkan parameter timeout sama sekali. Apabila target mengalami hang atau menunda respons, request akan nyangkut menyedot ketersediaan proses worker backend selamanya.
claimed_location: server/handlers/http.py (baris 151-189)
claimed_severity: HIGH
source_section: API-07 — HIGH: Tidak Ada HTTP Request Timeout untuk Proxy Stream
raw_quote: "async with http_session.get(stream_url, headers=headers) as upstream... tanpa timeout eksplisit. Jika YouTube lambat merespons... request handler akan tergantung selamanya"

---
finding_id: API-08
title: WebSocket Auth Bypass via Role client — Tidak Konsisten
description: Tampilan web mengenalkan 3 tipe akses role ("portal", "admin", "client") tapi di dalam kerangka pengaman backend fungsi require_auth menganggap valid semuanya yang berada di himpunan authenticated_connections, sehingga level otorisasi non-admin ("client") sejatinya ilusi yang diblokir sebagai unauthenticated.
claimed_location: server/handlers/auth.py, server/handlers/websocket.py (baris 121)
claimed_severity: HIGH
source_section: API-08 — HIGH: WebSocket Auth Bypass via Role client — Tidak Konsisten
raw_quote: "backend tidak mengenal role ini sama sekali. Semua non-admin yang terhubung akan selalu mendapat AUTH_REQUIRED error untuk setiap command."

---
finding_id: API-09
title: Tidak Ada Pagination untuk Search Results
description: Payload kembalian pada titik temu fitur pencarian dan rekomendasi dikunci paksa pada hard-limit 50 data, tak melempar format paginasi, indikator page-next, kursor, total data, yang menyebabkan hasil tak akan dapat diekspansi user.
claimed_location: server/handlers/ws/discover_handlers.py (baris 39-52), core/constants.py
claimed_severity: HIGH
source_section: API-09 — HIGH: Tidak Ada Pagination untuk Search Results
raw_quote: "Search handler menerima max_results... maksimal 50 hasil. Tidak ada cursor-based pagination, tidak ada total_count, tidak ada has_more flag."

---
finding_id: API-10
title: /health Tidak Mengembalikan Informasi yang Cukup untuk Load Balancer
description: Respon HTTP ping berstatus OK 200 sekalipun komponen playback mpv down. Desain ini membingungkan reverse proxy/loadbalancer pada skala produksi (health liveness berbeda dari readiness).
claimed_location: server/handlers/http.py (health_check baris 27-44)
claimed_severity: MEDIUM
source_section: API-10 — MEDIUM: /health Tidak Mengembalikan Informasi yang Cukup untuk Load Balancer
raw_quote: "mengembalikan {'status': 'ok'...} dengan status 200 bahkan ketika MPV tidak terkoneksi... Load balancer tidak bisa membedakan server yang benar-benar ready"

---
finding_id: API-11
title: Caching Response Header Tidak Konsisten di Stream Endpoint
description: Layanan mengirim perintah simpan cache browser ("Cache-Control: private, max-age=3600") meskipun stream di-direct langsung dari URL Youtube yang miliki sistem validasi per 6-jam.
claimed_location: server/handlers/http.py (baris 83-90 dan 158-164)
claimed_severity: MEDIUM
source_section: API-11 — MEDIUM: Caching Response Header Tidak Konsisten di Stream Endpoint
raw_quote: "header Cache-Control yang sama di-set tanpa mempertimbangkan bahwa URL YouTube sudah expired setiap 6 jam... Browser bisa men-cache URL yang sudah expired"

---
finding_id: API-12
title: HTTP 302 Digunakan untuk Redirect Stream (Seharusnya 307)
description: Transisi rute cadangan memancarkan code response 302 (Found) sementara standard resmi HTTP Stream harusnya menuntut lemparan kode redirect statis 307 (Temporary Redirect) sehingga client takkan mengkonversi operasi awal dari pola asalnya.
claimed_location: server/handlers/http.py (baris 118)
claimed_severity: MEDIUM
source_section: API-12 — MEDIUM: HTTP 302 Digunakan untuk Redirect Stream (Seharusnya 307)
raw_quote: "mengembalikan 302 Found. Menurut RFC 7231, 302 memperbolehkan browser mengubah POST menjadi GET... seharusnya digunakan 307 Temporary Redirect"

---
finding_id: API-13
title: Tidak Ada Input Validation untuk Artist Name dan Genre Name
description: Handler khusus antrean genre/artis tidak menerapkan pengereman batasan nilai panjang karakter yang lolos, mempersilakan client mengekstrak pencarian query dengan ukuran teks super raksasa.
claimed_location: server/handlers/ws/queue_handlers.py (baris 33-43)
claimed_severity: MEDIUM
source_section: API-13 — MEDIUM: Tidak Ada Input Validation untuk Artist Name dan Genre Name
raw_quote: "Tidak ada validasi panjang, karakter, atau keberadaan data. String panjang 10.000 karakter bisa dikirim... Tidak ada response error jika artist tidak ditemukan."

---
finding_id: API-14
title: WebSocket Actions Menggunakan String Literal, Bukan Enum (Inkonsistensi Naming)
description: Penamaan routing dan fungsi WebSocket dipecah-pecah ke hardcode value teks mentah, alih-alih me-mappingnya pada satu pusat StrEnum WSAction yang telah tersedia di core module, berisiko tinggi saat penggantian sintaks global.
claimed_location: server/handlers/ws/settings_handlers.py (baris 21, 26, 31)
claimed_severity: MEDIUM
source_section: API-14 — MEDIUM: WebSocket Actions Menggunakan String Literal, Bukan Enum (Inkonsistensi Naming)
raw_quote: "Beberapa handler tidak menggunakan konstanta WSAction tapi langsung menggunakan string literal... Inkonsistensi ini rawan typo dan membuat refactoring berbahaya."

---
finding_id: API-15
title: Retry Logic Tidak Idempotent untuk PLAY_TRACK
description: Penayangan trek lagu menenggak perintah ganda berulang-ulang tanpa saringan ID. Jaringan yang terputus sejenak dari klien bisa mengirim ulang perintah ini dan mengeksekusinya ke engine tanpa peringatan duplikasi.
claimed_location: server/handlers/ws/playback_handlers.py (baris 8-11), web/static/js/ws.js
claimed_severity: MEDIUM
source_section: API-15 — MEDIUM: Retry Logic Tidak Idempotent untuk PLAY_TRACK
raw_quote: "jika klien mengirim perintah yang sama dua kali... lagu akan di-play dua kali... Tidak ada deduplication berdasarkan video_id atau timestamp."

---
finding_id: API-16
title: /metrics Menggunakan Custom Header X-Metrics-Token (Non-Standard)
description: Rute layanan prometheus mendadak menggunakan X-Metrics-Token custom pada pengamanan rahasianya, yang secara inheren ditolak berbagai engine analitik lain yang biasanya menggunakan skema Bearer Auth konvensional.
claimed_location: server/handlers/http.py (serve_metrics baris 198-210)
claimed_severity: MEDIUM
source_section: API-16 — MEDIUM: /metrics Menggunakan Custom Header X-Metrics-Token (Non-Standard)
raw_quote: "menggunakan header custom X-Metrics-Token untuk autentikasi, alih-alih standard Authorization: Bearer <token>. Hal ini tidak kompatibel dengan sebagian besar monitoring stack"

---
finding_id: API-17
title: DELETE_DOWNLOAD Tidak Mengembalikan Status Sukses/Gagal Terstruktur
description: Kesimpulan penyelesaian penarikan/unduh dihapus dikirim kembali sekadar sebagai pesan logs biasa ke client, meluputkan penanda statis JSON object gagal/sukses secara programatik untuk ditangani tampilan frontend.
claimed_location: server/handlers/ws/download_handlers.py (baris 19-49)
claimed_severity: MEDIUM
source_section: API-17 — MEDIUM: DELETE_DOWNLOAD Tidak Mengembalikan Status Sukses/Gagal Terstruktur
raw_quote: "mengirim hasil operasi sebagai log message (string), bukan pesan terstruktur. Klien tidak dapat membedakan... secara programatik."

---
finding_id: API-18
title: .env.example Menggunakan Nama Variable yang Berbeda dari config.py
description: Label konstanta pengaturan awal yang tercatat di kerangka .env referensi memakai kata dasar YTGUI_*, berlawanan mutlak dari penulisan di dalam skrip config.py yang justru menggunakan kata kunci LUNAWAVE_*.
claimed_location: .env.example, config.py (baris 24-29)
claimed_severity: LOW
source_section: API-18 — LOW: .env.example Menggunakan Nama Variable yang Berbeda dari config.py
raw_quote: ".env.example mendefinisikan YTGUI_HOST... namun config.py membaca LUNAWAVE_HOST... Nama variable di .env.example tidak cocok"


Total temuan diekstrak dari DOKUMEN 9 — Frontend Audit: 24


---
finding_id: FE-001
title: ITUNES_API_URL Tidak Pernah Didefinisikan: Runtime ReferenceError
description: Script pemanggil cover artwork mereferensikan variabel ITUNES_API_URL yang kosong secara absolut pada semua file konfigurasi. Ketiadaan variabel ini meruntuhkan (crash) pemanggilan gambar thumbnail asli dan mengembalikan default youtube yang buram.
claimed_location: web/static/js/utils.js, web/static/js/config.js
claimed_severity: CRITICAL
source_section: FE-001 — ITUNES_API_URL Tidak Pernah Didefinisikan: Runtime ReferenceError
raw_quote: "menggunakan konstanta ITUNES_API_URL yang tidak pernah didefinisikan di mana pun... browser akan melempar ReferenceError: ITUNES_API_URL is not defined"

---
finding_id: FE-002
title: Service Worker Cache Stale: Deployment Bypass
description: String pemanggilan resource bundle.js pada script worker tidak menggunakan kunci versi identik yang sama dengan yang dikaitkan di HTML, mengakibatkan pengguna selalu disodori versi cache lawas meskipun backend telah terbaharui dari ujung server.
claimed_location: web/static/sw.js, web/static/index.html
claimed_severity: CRITICAL
source_section: FE-002 — Service Worker Cache Stale: Deployment Bypass
raw_quote: "SW lama akan terus menyajikan versi bundle.js lama dari cache, karena cache key tidak cocok dengan URL baru yang ada query param-nya."

---
finding_id: FE-003
title: Duplicate Event Listener pada Lyric Offset Controls
description: Interaksi fungsi sinkronisasi (sync) waktu lirik ditumpuk pengaitannya dua kali ke satu tag button secara repetitif, mengakibatkan variabel perubahan offset terpanggil berlipat (-0.5 jadi -1.0) memicu kacau waktu tanpa ada warning.
claimed_location: web/static/js/events/lyrics-events.js (baris 34-45 dan 59-70)
claimed_severity: CRITICAL
source_section: FE-003 — Duplicate Event Listener pada Lyric Offset Controls
raw_quote: "dom.lyricOffsetMinus dan btnSyncMinus merujuk pada elemen yang sama... Akibatnya setiap klik pada tombol offset akan mengubah lyrics_offset dua kali"

---
finding_id: FE-004
title: renderSheetLyrics() Menambah Scroll Listener Tanpa Batas
description: Mekanisme pendeteksian wheel mouse dan usap lirik menempelkan event touchmove tanpa diset ulang tiap kali innerHTML div parent lirik dihapus bangun. Karena pendeteksian _scrollBound memakai atribut element dom yang terganti, event lama terus tergenang menjejali memory (leak).
claimed_location: web/static/js/render/lyrics.js
claimed_severity: HIGH
source_section: FE-004 — renderSheetLyrics() Menambah Scroll Listener Tanpa Batas
raw_quote: "Setiap kali innerHTML di-set ulang, elemen lama dihapus... tapi _scrollBound masih true di referensi dom.lyricsContent... listener lama akan leak."

---
finding_id: FE-005
title: Tidak Ada Focus Trap pada Modal/Bottom Sheet
description: Menu jendela mengambang pada aplikasi (settings, lyrics, action) dibiarkan mengalirkan fokus navigasi ke objek belakang background sheet. Membuat pengguna keyboard memicu komponen asing melampaui aturan keamanan (WCAG) aksesabilitas antarmuka.
claimed_location: web/static/index.html (.settings-sheet), web/static/js/events/settings-events.js
claimed_severity: HIGH
source_section: FE-005 — Tidak Ada Focus Trap pada Modal/Bottom Sheet
raw_quote: "Saat sheet terbuka, pengguna keyboard dapat berpindah focus ke elemen di belakang overlay... melanggar WCAG 2.1.2 dan merupakan masalah serius"

---
finding_id: FE-006
title: Login Form: Tidak Ada <label> pada Input Fields
description: Field masukkan login tidak dirangkai menggunakan korelasi tag pelabelan. Mengandalkan placeholder sebagai identitas semata menyingkirkan kemampuan alat screen reader disabilitas memahami fungsi kotak isian.
claimed_location: web/static/index.html
claimed_severity: HIGH
source_section: FE-006 — Login Form: Tidak Ada <label> pada Input Fields
raw_quote: "Kedua field login... tidak memiliki elemen <label> yang terasosiasi. Screen reader tidak bisa mengidentifikasi tujuan field-field ini."

---
finding_id: FE-007
title: Volume Slider Tidak Ada aria-label dan aria-valuenow
description: Parameter nilai (aria) aksesibilitas dasar (aria-label, valuenow) luput pada bar kontrol volume, membungkam petunjuk status dan perubahan persentase ukuran audio secara absolut pada asisten mesin pencerna layar.
claimed_location: web/static/index.html
claimed_severity: HIGH
source_section: FE-007 — Volume Slider Tidak Ada aria-label dan aria-valuenow
raw_quote: "Input range untuk volume tidak memiliki aria-label, aria-valuemin, aria-valuemax, dan aria-valuenow... Screen reader hanya membaca '80' tanpa konteks"

---
finding_id: FE-008
title: Dark Mode: Aplikasi Hanya Mendukung Dark, Tidak Ada Light Mode Support
description: Palet warna tema hanya menginjeksi token variabel css gelap sepenuhnya menolak preferensi device pengguna (light/dark os). Ketidakadaan color-scheme turut menyebabkan kontras fatal silau dari sisa komponen input putih standar browser.
claimed_location: web/static/css/tokens.css
claimed_severity: HIGH
source_section: FE-008 — Dark Mode: Aplikasi Hanya Mendukung Dark, Tidak Ada Light Mode Support
raw_quote: "Tidak ada @media (prefers-color-scheme: light) di mana pun... absennya color-scheme deklarasi menyebabkan browser scrollbar, input fields... tetap menggunakan OS default (putih)"

---
finding_id: FE-009
title: Responsive: Lirik Dipotong Paksa di Mobile (Max-Height 40px)
description: Styling lirik seluler menetapkan max-height: 40px serta memotong baris lewat text-overflow-ellipsis, murni menumpulkan fungsinya saat teks lirik aktual berisi deretan barisan super panjang pada piranti sempit (terpenggal total).
claimed_location: web/static/css/platform/mobile.css
claimed_severity: HIGH
source_section: FE-009 — Responsive: Lirik Dipotong Paksa di Mobile (Max-Height 40px)
raw_quote: "lyrics-wrap dibatasi max-height: 40px... teks lirik terpotong... ukuran font 14px dipaksa text-overflow: ellipsis. Ini menyebabkan lirik panjang tidak terbaca"

---
finding_id: FE-010
title: Responsive: Desktop Player Bar Menggunakan !important Berlebihan (CSS Specificity War)
description: Penataan desktop.css menembak atribut baris kontrol memakai !important di belasan definisi. Kode styling meng-overwritte dirinya terus, menggagalkan ekstensi komponen dan menyebabkan duplikasi kotor saat mendesain layout horizontal/landscape.
claimed_location: web/static/css/platform/desktop.css, landscape.css
claimed_severity: MEDIUM
source_section: FE-010 — Responsive: Desktop Player Bar Menggunakan !important Berlebihan (CSS Specificity War)
raw_quote: "menggunakan 30+ deklarasi !important untuk meng-override player bar layout... specificity war... Setiap perubahan di base CSS membutuhkan tambahan !important baru"

---
finding_id: FE-011
title: UX: Swipe Gesture Hanya Tersedia untuk Admin
description: Usapan kontrol geser track memblokir intervensi non-admin dengan sengaja memunculkan balok toast error tiap di swipe, memberi ketidaknyamanan navigasi karena fitur tak dinonaktifkan sunyi secara visual.
claimed_location: web/static/js/platform/touch.js
claimed_severity: MEDIUM
source_section: FE-011 — UX: Swipe Gesture Hanya Tersedia untuk Admin
raw_quote: "Client mode user yang hanya mendengarkan tidak mendapatkan feedback apa pun untuk swipe yang tidak tersedia... toast pesan 'Hanya admin...' muncul"

---
finding_id: FE-012
title: UX: Login Error State Tidak Di-Clear Saat Re-attempt
description: Papan penanda keliru input hanya membersihkan label bila eksekusi socket terklik terkirim (auth ok). Jika pengguna menghapus teks ketikan saat panel ber-error, pesan error mematung tersangkut meski ketikan baru di-reset ke string sah.
claimed_location: web/static/js/services/auth.js, web/static/js/events/index.js
claimed_severity: MEDIUM
source_section: FE-012 — UX: Login Error State Tidak Di-Clear Saat Re-attempt
raw_quote: "Jika user mengetik ulang tapi belum klik submit, error lama masih tampil, memberikan false negative impression... error tidak hilang saat user mulai mengetik"

---
finding_id: FE-013
title: Form Validation: Login Submit dengan Enter Hanya dari Password Field
description: Input eksekusi cepat menggunakan Enter Button tak diregister ke kolom masukan pengguna, mengakibatkan tekan sentak enter cuma berfungsi dari kolom kata sandi. Pengguna harus berpindah kolom jika tekan enter ditengah-tengah isi nama.
claimed_location: web/static/js/events/index.js
claimed_severity: MEDIUM
source_section: FE-013 — Form Validation: Login Submit dengan Enter Hanya dari Password Field
raw_quote: "Shortcut Enter untuk submit hanya terdaftar di admin-password. Jika user mengetik username lalu langsung Enter... tidak ada yang terjadi."

---
finding_id: FE-014
title: State Bug: store.status Di-set Optimistik Sebelum Server Konfirmasi
description: Pemencetan kontrol jeda dimanipulasi dengan langsung menimpa status "PLAYING" dalam klien secara seketika. Apabila internet terputus, atau request hilang, state server akan tertinggal dan frontend secara permanen terjebak out-of-sync.
claimed_location: web/static/js/events/player-events.js
claimed_severity: MEDIUM
source_section: FE-014 — State Bug: store.status Di-set Optimistik Sebelum Server Konfirmasi
raw_quote: "store.status langsung diubah di frontend sebelum server merespons... menimbulkan window di mana state bisa tidak sinkron permanen jika WebSocket drop"

---
finding_id: FE-015
title: Navigation: aria-selected Tidak Update Saat Tab Berubah via Swipe
description: Tindakan merubah menu lewat geser touch tidak memperbaharui nilai atribut seleksi (aria-selected) elemen DOM-nya, ditambah hilangnya penomoran role="tabpanel" pemisah antar layer konten yang mematikan kapabilitas screen navigation.
claimed_location: web/static/index.html, web/static/js/main.js
claimed_severity: MEDIUM
source_section: FE-015 — Navigation: aria-selected Tidak Update Saat Tab Berubah via Swipe
raw_quote: "swipe gesture... tidak mengubah tab aktif. Ini... menyebabkan aria-selected tidak sync. Yang lebih kritis: Navigasi tab... tidak ada role='tabpanel'"

---
finding_id: FE-016
title: UI Consistency: Inline Style vs CSS Class (Anti-Pattern)
description: Halaman skeleton di-hardcode memakai beruntun penempelan elemen tag "style=.." secara brutal (inline styling). Menciderai kemudahan re-factoring layout, menyusahkan tracking properti UI dan membuat penggelapan dark-mode menyulit.
claimed_location: web/static/index.html
claimed_severity: MEDIUM
source_section: FE-016 — UI Consistency: Inline Style vs CSS Class (Anti-Pattern)
raw_quote: "Terdapat banyak inline style langsung di HTML... Ada 15+ elemen dengan inline style... menyulitkan theming, dark/light mode toggle"

---
finding_id: FE-017
title: Loading State: Tidak Ada Skeleton Screen untuk Queue dan Radio
description: Container ruang blok barisan antrean lagu murni tidak membekali fitur state loading apapun selama WS tengah memuat respon awal, menelantarkan blok komponen jadi kanvas putih kosong membingungkan dalam beberapa sekon.
claimed_location: web/static/js/render/queue.js, web/static/index.html
claimed_severity: MEDIUM
source_section: FE-017 — Loading State: Tidak Ada Skeleton Screen untuk Queue dan Radio
raw_quote: "queue list... dan radio queue... tidak memiliki loading state sama sekali. Saat aplikasi pertama kali load... kedua container ini kosong tanpa indikasi apapun"

---
finding_id: FE-018
title: Animation: Fake Beat Loop Berjalan Saat Tab Tidak Aktif
description: Loop efek kelap-kelip cahaya (glow) dieksekusi setTimeout() yang gagal termatikan secara sistem disaat viewport page tertutup, dan mengabaikan mode perlindungan (prefers-reduced-motion) dari penyandang disabilitas syaraf visual.
claimed_location: web/static/js/audio.js
claimed_severity: MEDIUM
source_section: FE-018 — Animation: Fake Beat Loop Berjalan Saat Tab Tidak Aktif
raw_quote: "tidak ada pause saat browser tab tidak aktif atau saat user pindah ke tab lain... berjalan setiap 500ms tanpa mempertimbangkan prefers-reduced-motion"

---
finding_id: FE-019
title: PWA: Manifest Hanya Satu Icon (1024x1024)
description: Register konfigurasi pembentuk format aplikasi web (manifest.json) melompong dari penyertaan parameter varian resolusi. Hal ini me-nonaktifkan pengerjaan masking ukuran ikon yang dibutuhkan Chrome/iOS saat menyimpan ke beranda gawai.
claimed_location: web/static/manifest.json
claimed_severity: MEDIUM
source_section: FE-019 — PWA: Manifest Hanya Satu Icon (1024x1024)
raw_quote: "hanya mendefinisikan satu icon dalam satu ukuran... Android Chrome tidak punya icon yang tepat... iOS tidak punya apple-touch-icon"

---
finding_id: FE-020
title: Widget Tree: favorites.js adalah File Kosong
description: Modul file penulisan skrip daftar favorit tersaji nir-kode sama sekali (0 bytes). Algoritma pembentuknya nyatanya tertindih di luar berkas (discover.js), menumbuhkan utang teknis penumpukan bundel statis percuma tak bertuan.
claimed_location: web/static/js/render/favorites.js
claimed_severity: MEDIUM
source_section: FE-020 — Widget Tree: favorites.js adalah File Kosong
raw_quote: "File... ada di direktori render namun isinya kosong. Logika render favorites justru ada di render/discover.js."

---
finding_id: FE-021
title: Rebuild: Hashtag Color Menggunakan Math.random() — Warna Berubah Setiap Render
description: Variabel hash-color di injeksi menggunakan fungsi Math.random bawaan yang bersifat temporal dan menumpang memori lokal, akibatnya rentetan tag artis yang sama akan meleset gradasinya secara random setiap kali web client refresh halaman.
claimed_location: web/static/js/render/discover.js
claimed_severity: MEDIUM
source_section: FE-021 — Rebuild: Hashtag Color Menggunakan Math.random() — Warna Berubah Setiap Render
raw_quote: "menggunakan Math.random() untuk generate warna... Setiap kali halaman di-refresh... warna artis/genre akan berubah secara random."

---
finding_id: FE-022
title: UX: Artist Name Truncated di 25 Karakter dengan Nilai Hardcoded
description: Pemangkasan nama title di Javascript dipancangkan limit kasar (hardcode) pada titik absolut karakter ke-25 tanpa memperhitungkan lebar dinamis screen (responsif flex CSS), menuntun ke kondisi jelek pada viewport raksasa dan gawai.
claimed_location: web/static/js/render/search.js, web/static/js/render/discover.js
claimed_severity: LOW
source_section: FE-022 — UX: Artist Name Truncated di 25 Karakter dengan Nilai Hardcoded
raw_quote: "nama artis di-truncate di 25 karakter dengan logika manual yang di-hardcode... truncation via JS tidak responsif"

---
finding_id: FE-023
title: Console.log Masih Ada di Production Code
description: Baris rekam debugging developer berserakan belum tersapu ke luar build produksi, yang dengan konyol merilis info parameter sensitif dan nilai-nilai tersembunyi ke publik mana saja yang iseng mampir.
claimed_location: web/static/js/audio.js, web/static/js/utils.js
claimed_severity: LOW
source_section: FE-023 — Console.log Masih Ada di Production Code
raw_quote: "console.log debug masih ada di production code... mengekspos informasi internal yang tidak perlu ke user mana pun"

---
finding_id: FE-024
title: UX: Tidak Ada Konfirmasi Saat Hapus Unduhan
description: Pemencetan kontrol hapus memicu pengiriman event tak termaafkan (destruktif deletion) ke socket tanpa filter persetujuan terlebih dahulu. Salah sentuh akan menggagalkan file hasil susah payah didownload sebelumnya, tak dapat dikembalikan.
claimed_location: web/static/js/events/player-events.js
claimed_severity: LOW
source_section: FE-024 — UX: Tidak Ada Konfirmasi Saat Hapus Unduhan
raw_quote: "Action 'Hapus Unduhan' di action sheet langsung mengirim DELETE_DOWNLOAD ke server tanpa konfirmasi. Ini adalah destructive action"


Total temuan diekstrak dari DOKUMEN 10 — Backend Audit: 42


---
finding_id: BUG-01
title: DiscoverService KeyError: stream_url Not in SELECT
description: Kueri SQL tidak meminta kolom stream_url pada pemilihan data track, namun kode mengasumsikan keberadaannya pada variabel dictionary yang dilempar, memicu KeyError fatal yang mencrash fungsi tab Discover secara keseluruhan.
claimed_location: server/services/discover_service.py (get_recent() L36, get_favorites() L63, get_cached() L90)
claimed_severity: CRITICAL
source_section: BUG-01 — DiscoverService KeyError: stream_url Not in SELECT
raw_quote: "SQL query memilih kolom tanpa stream_url, tapi kode langsung mengaksesnya... KeyError: 'stream_url' tidak ada di dict!"

---
finding_id: BUG-02
title: import time di Bawah Class — Hoisting Mismatch
description: Penulisan modul import time dilempar pada baris paling bawah kode di luar class. Pemanggilan time.monotonic() di dalam fungsi membentur masalah pembacaan (NameError) saat interpreter tidak merunning penuh skripnya (parsial).
claimed_location: engine/mpv_controller.py (baris terakhir)
claimed_severity: CRITICAL
source_section: BUG-02 — import time di Bawah Class — Hoisting Mismatch
raw_quote: "import time ditempatkan di baris terakhir file... Ini bekerja di CPython... tapi ini adalah anti-pattern yang rentan, menyesatkan"

---
finding_id: BUG-03
title: RadioRandomizeCommand Hanya Berjalan di RADIO Mode
description: Parameter mode pemutaran radio diproteksi if statement ketat yang mensyaratkan status radio sedang aktif untuk fungsi pengacakan seed artist. Alhasil, klik acak dari antrean biasa diblok mentah dengan notifikasi log saja (harus 2 klik baru jalan).
claimed_location: engine/playback/radio_commands.py (on_radio_randomize())
claimed_severity: CRITICAL
source_section: BUG-03 — RadioRandomizeCommand Hanya Berjalan di RADIO Mode
raw_quote: "Guard if self.state.playback_mode == PlaybackMode.RADIO memblokir fetch jika belum di mode RADIO... user mendapat 'Radio tidak aktif'"

---
finding_id: BUG-04
title: Admin Password Tidak Tercetak di Non-TTY Environment
description: Pencetakan password rahasia admin untuk sesi awal dikunci validasi output isatty() yang selalu salah (false) di lingkungan background (docker, daemon systemd), menyembunyikan selamanya password masuk yang ter-generate.
claimed_location: config.py (get_admin_password())
claimed_severity: CRITICAL
source_section: BUG-04 — Admin Password Tidak Tercetak di Non-TTY Environment
raw_quote: "sys.stderr.isatty() check memblokir output di non-interactive terminal... jika bukan TTY, password tercetak ke file tapi tidak ada notifikasi!"

---
finding_id: BL-01
title: on_queue_select() Membuang Track Sebelum Index Tanpa Update History
description: Pemilihan acak nomor baris antrean lagu langsung mem-pop list index-index lawas membuangnya begitu saja tanpa mendaftarkannya terlebih dahulu ke memori log history pemutaran.
claimed_location: engine/playback/queue_commands.py (on_queue_select())
claimed_severity: HIGH
source_section: BL-01 — on_queue_select() Membuang Track Sebelum Index Tanpa Update History
raw_quote: "Loop for _ in range(cmd.index + 1): self.state.queue.popleft() membuang semua track sebelum index... Track-track ini hilang selamanya dari sesi pemutaran."

---
finding_id: BL-02
title: Volume Cap Tidak Konsisten: 100 vs 150
description: Batasan toleransi maksmimal pengaturan volume audio menabrak bentrokan nilai ganda (100 dan 150) yang tidak bersinergi dengan konstanta MAX_VOLUME di constants.py, menimbulkan bug logika inkonsisten pada interaksi pengaturan level di WS handler dengan VolumeService.
claimed_location: engine/volume_service.py L23, server/handlers/ws/settings_handlers.py L20, core/constants.py L4
claimed_severity: HIGH
source_section: BL-02 — Volume Cap Tidak Konsisten: 100 vs 150
raw_quote: "VolumeService membatasi volume ke 100, tapi settings_handlers.py mengirim volume_set hingga 150. MAX_VOLUME = 150 di constants tidak digunakan"

---
finding_id: BL-03
title: _gather_batch() dengan prioritized_artist Tidak Menjamin Artist Muncul
description: Algoritma order fallback radio tidak menjaring kriteria ketat WHERE untuk artist prioritas melainkan murni mengacak CASE THEN secara raw, menyebabkan seed awal artis bisa tak diikutsertakan sedikitpun kalau slot limit baris kuota data sudah penuh duluan oleh record artis lain.
claimed_location: cache/repositories/discover_repository.py (get_random_songs())
claimed_severity: MEDIUM
source_section: BL-03 — _gather_batch() dengan prioritized_artist Tidak Menjamin Artist Muncul
raw_quote: "SQL menggunakan ORDER BY CASE WHEN nama = ? THEN 0 ELSE 1 END, RANDOM() — ini hanya memprioritas, tidak memfilter... Jika limit sudah tercapai... artist seed tidak muncul"

---
finding_id: BL-04
title: _backfill_and_standby() Race Condition pada Queue Length Check
description: Pemeriksaan kapasitas queue pemutaran (15 slot) dijalankan setelah fungsi di kunci (locked) oleh lock async yang mana queue length bisa saja sudah dieksekusi dan berubah panjang aslinya, memicu double fetch ganda data pemutaran (terlalu banyak dimuat).
claimed_location: engine/radio_engine.py (_backfill_and_standby())
claimed_severity: MEDIUM
source_section: BL-04 — _backfill_and_standby() Race Condition pada Queue Length Check
raw_quote: "Cek len(self.state.radio_queue) >= 15 dilakukan setelah acquire _fetch_lock, tapi queue bisa berubah saat menunggu lock. Double fetch bisa terjadi"

---
finding_id: TXN-01
title: Setiap DB Operation Commit Terpisah — N+1 Commit Anti-Pattern
description: Operasi insert dan update (upsert dll) melontarkan signal commit() tiap putaran baris di transaksi seeding awal tanpa di-wrap bundle commit, sangat merugikan performa menulis (ratusan penulisan ke disk lambat memakan waktu).
claimed_location: cache/repositories/track_repository.py, cache/repositories/auth_repository.py, cache/repositories/discover_repository.py
claimed_severity: HIGH
source_section: TXN-01 — Setiap DB Operation Commit Terpisah — N+1 Commit Anti-Pattern
raw_quote: "Setiap upsert_track, increment_play_count, create_session melakukan commit() individual... ini bisa ratusan commits → sangat lambat."

---
finding_id: TXN-02
title: _seed_initial_data() Tanpa Error Recovery — Partial State
description: Skrip muat awalan (seeding) pangkalan data berjalan telanjang menabrak apa saja tanpa pengamanan blok tangkap try-except, mengakibatkan DB dibiarkan kotor patah-patah isinya tanpa sempat merollback kalau ditengah muat paksa terjadi interupsi OS.
claimed_location: cache/db.py (_seed_initial_data())
claimed_severity: HIGH
source_section: TXN-02 — _seed_initial_data() Tanpa Error Recovery — Partial State
raw_quote: "Jika seeding terinterupsi (misalnya power loss), DB bisa dalam keadaan parsial. Tidak ada transaksi atomik yang membungkus"

---
finding_id: TXN-03
title: toggle_favorite Menggunakan RETURNING — SQLite 3.35+ Only
description: Modul database handler membungkus perintah UPDATE menyisipkan keyword RETURNING yang absolut tak direkognisi engine SQLite kernel versi lawas (di bawah 3.35). Menyebabkan mogok crash jika perangkat yang dipasang belum update SQLite (seperti shell android lama).
claimed_location: cache/repositories/track_repository.py (toggle_favorite())
claimed_severity: MEDIUM
source_section: TXN-03 — toggle_favorite Menggunakan RETURNING — SQLite 3.35+ Only
raw_quote: "Di SQLite < 3.35 (misalnya di Android Termux lama), RETURNING tidak didukung → crash saat user toggle favorit"

---
finding_id: TXN-04
title: upsert_track Selalu Update last_played — Polusi Data Recent
description: Rekaman fungsi meremajakan track (upsert) gegabah memperbaharui properti last_played (di set = time saat ini) tanpa melihat bahwa hal tersebut bukan dari diputar-player, merepresentasikan seakan track sering dimainkan dan mengotor-kacaukan data Recently Played list murni.
claimed_location: cache/repositories/track_repository.py (upsert_track())
claimed_severity: MEDIUM
source_section: TXN-04 — upsert_track Selalu Update last_played — Polusi Data Recent
raw_quote: "Memanggil upsert_track saat update stream URL atau duration juga memperbarui last_played, sehingga track yang tidak diputar muncul di daftar 'Recently Played'"

---
finding_id: EXC-01
title: CacheResolver.resolve() Thundering Herd Setelah Error
description: Apabila utilitas pemanggil link URL yt-dlp mati gagal mengembalikan URL, pelepasan status _fetching justru men-trigger loop ulang secara rentetan paralel kepada semua klien tunggu (waiters) untuk me-resolve sendiri barengan hingga mengebom layanan yt-dlp secara gila-gilaan (thundering herd).
claimed_location: cache/resolver.py (resolve())
claimed_severity: HIGH
source_section: EXC-01 — CacheResolver.resolve() Thundering Herd Setelah Error
raw_quote: "semua waiter di-release melalui event.set(), lalu masing-masing memanggil resolve() lagi secara rekursif... semua waiter akan mencoba fetch ulang secara paralel"

---
finding_id: EXC-02
title: _fetching.wait() Tanpa Timeout — Deadlock Potensial
description: Event listener yang menahan task async untuk antrean stream resolving tak mengeset parameter batasan waktu (timeout) apapun, mengakibatkan thread melayang mati (hang deadlock loading spinner di frontend) apabila task yang ditunggu kebetulan tertutup tiba-tiba (crash) sebelum melaporkan sinyal kelar.
claimed_location: cache/resolver.py L43, server/services/stream_prefetch.py L22
claimed_severity: HIGH
source_section: EXC-02 — _fetching.wait() Tanpa Timeout — Deadlock Potensial
raw_quote: "Jika task yang sedang fetch crash sebelum memanggil event.set(), semua waiter hang selamanya... await self._fetching[track.video_id].wait() tidak ada timeout"

---
finding_id: EXC-03
title: _stream_rate_limit dict Tidak Pernah Dibersihkan — Memory Leak
description: Variabel array penyimpan alamat IP pelacak request tidak dilengkapi modul fungsi sampah (garbage collector). Akibatnya dictionary Python level ini menyedot memori ram tak terbatas terus menyimpan IP tanpa pernah meng-clear data IP basi (leak murni).
claimed_location: server/handlers/http.py (L17, L57-62)
claimed_severity: HIGH
source_section: EXC-03 — _stream_rate_limit dict Tidak Pernah Dibersihkan — Memory Leak
raw_quote: "Tidak ada cleanup expired entries → dict tumbuh seiring waktu dan tidak pernah dikurangi... IP yang tidak pernah request lagi tidak pernah dihapus"

---
finding_id: EXC-04
title: Double TrackEndedEvent Race di _on_track_ended
description: Penanganan trigger waktu jeda EOF mpv sebesar (0.35s) tak diproteksi flag blokade boolean, membuat kiriman koneksi end-file redundan (misal 2 sinyal double karena lag internet) mengeksekusi track lompat 2x maju melompat secara brutal (skip song).
claimed_location: engine/playback/controller.py (_on_track_ended())
claimed_severity: HIGH
source_section: EXC-04 — Double TrackEndedEvent Race di _on_track_ended
raw_quote: "Jika dalam 0.35s ada event end-file kedua... dua coroutine autoplay jalan paralel → dua lagu diputar sekaligus atau lagu dilewati"

---
finding_id: EXC-05
title: bare except di _handle_delete_download
description: Logika penghapusan file lagu memakai metode blok exception-kosong (bare except:) yang menyapu buta-buta semua pesan komplain error tingkat dasar Python (keyboard-interrupt dll). Kesalahan penghapusan dari folder lokal juga menjadi gaib ditelan bumi.
claimed_location: server/handlers/ws/download_handlers.py (_handle_delete_download())
claimed_severity: MEDIUM
source_section: EXC-05 — bare except di _handle_delete_download
raw_quote: "except: tanpa type swallows semua exceptions... Kegagalan menghapus file user tidak dilaporkan ke client"

---
finding_id: CC-01
title: STATS.is_playing Diset Tanpa Lock dari Async Context
description: Pencatatan status putar lagu (is_playing) pada status bar thread memodifikasi property objek core logging secara harfiah begitu saja tanpa memanfaatkan thread-lock async yang tesedia, yang rawan menodai pembacaan (torn read) di chip bertipe ARM.
claimed_location: engine/playback/controller.py L127, engine/playback/playback_commands.py L54, core/log_config.py
claimed_severity: HIGH
source_section: CC-01 — STATS.is_playing Diset Tanpa Lock dari Async Context
raw_quote: "STATS.is_playing = True di controller.py... diset langsung tanpa lock → potensial torn read di ARM... dibaca dengan lock, tapi written tanpa lock"

---
finding_id: CC-02
title: ConnectionManager.active_connections List Tanpa Lock
description: Penyimpanan client id pada dictionary array dikerjakan sekenanya, di mana pembagian pengulangan list disaat event disconnect beririsan bisa menimbulkan array size change error karena iterator membaca (snapshot) isi yang sama sewaktu iterasi async loop.
claimed_location: server/handlers/websocket.py (ConnectionManager)
claimed_severity: MEDIUM
source_section: CC-02 — ConnectionManager.active_connections List Tanpa Lock
raw_quote: "broadcast() iterates list(self.active_connections) yang merupakan snapshot — disconnect saat broadcast tidak segera efektif... tanpa explicit lock"

---
finding_id: CC-03
title: play_track() Retry di Luar Lock — Stale State Access
description: Formula hitung limit hitback retry dijalankan dari titik poin blok setelah proses di luar lock mutex terputus-sambung dengan coroutine lain, mengijinkan pembacaan iterasi (retry count) menyadur nilai kusam (stale) dan men-trigger skip lompat error.
claimed_location: engine/playback/controller.py (play_track() L146-150)
claimed_severity: MEDIUM
source_section: CC-03 — play_track() Retry di Luar Lock — Stale State Access
raw_quote: "backoff = 2 ** self._retry_count dibaca setelah async with self._play_lock keluar. Antara keluar lock dan baca _retry_count, nilai bisa berubah"

---
finding_id: CC-04
title: DownloadManager._download_lock Memblokir Task Kedua Selamanya
description: Lock antrean handler mendownload tak mengikat klausul tenggang wait_for() sama sekali. Kalau antrean task ke-1 memakan waktu super lama/nge-hang dari internet lemot, maka task pen-download file track kedua terparkir pasif mematung (starvation limit) tanpa konfirmasi reject ke UI klien.
claimed_location: engine/download_manager.py (_do_download())
claimed_severity: MEDIUM
source_section: CC-04 — DownloadManager._download_lock Memblokir Task Kedua Selamanya
raw_quote: "Task kedua menunggu _download_lock yang dipegang task pertama. Tidak ada timeout — task kedua bisa menunggu selama download pertama berlangsung"

---
finding_id: CAC-01
title: Lyrics Cache FIFO Bukan LRU — Hotspot Eviction
description: Kamus penampung string lirik dalam memori dibatasi di angka 50 dengan cara me-remove item data terdepan (index awalan / FIFO), ironisnya track yang tersering di mainkan juga ikut tertendang dihapus dan harus fetch ulang, bukannya menghapus lagu asing (least used data / LRU).
claimed_location: plugins/lyrics.py (fetch())
claimed_severity: MEDIUM
source_section: CAC-01 — Lyrics Cache FIFO Bukan LRU — Hotspot Eviction
raw_quote: "Cache lirik 50 item menggunakan FIFO eviction. Lagu yang paling sering diputar (hotspot) bisa di-evict... bukan least-recently-used"

---
finding_id: CAC-02
title: Stream URL TTL di Batas Bawah Kedaluwarsa YouTube
description: Interval wajar ketahanan string referensi yt-dlp URL disetel ngawur 6 jam mutlak (21600), padahal youtube dapat memutuskan URL kurang dari range wajar ini sedikit, memicu link expired dipanggil sebagai link wajar (403 terlarang).
claimed_location: config.py
claimed_severity: MEDIUM
source_section: CAC-02 — Stream URL TTL di Batas Bawah Kedaluwarsa YouTube
raw_quote: "STREAM_URL_TTL_SEC = 21600 (6 jam)... URL yang di-cache tepat di batas TTL mungkin sudah tidak valid saat diputar → error 403 dari YouTube"

---
finding_id: CAC-03
title: StreamPrefetchService._fetching Bisa Bocor Saat Exception
description: Skema coroutine background pemanggil URL di belakang layar memuat wait limit exception rentan. Jika asyncio dilempar status CancelledError sewaktu lock (walau langka), key data tracking URL terkait tidak tuntas dikuras, menimbulkan penumpukan flag (bocor memori task).
claimed_location: server/services/stream_prefetch.py
claimed_severity: MEDIUM
source_section: CAC-03 — StreamPrefetchService._fetching Bisa Bocor Saat Exception
raw_quote: "Jika get_stream_url() raise exception... async.CancelledError terjadi di event.set() sendiri (sangat jarang), entry bisa tertinggal."

---
finding_id: QUE-01
title: deque Delete by Index adalah O(n) — Performance Bottleneck
description: List penyimpanan alur main dikonstruksi secara paksa dengan metode objek python (deque). Saat list ditarik reorder (pengubahan urutan list 1 ke urut 5) maka array list ditarik manual dipaksa bergeser dan me-loop 1 by 1 O(n) murni menumpulkan efisiensi saat list berukuran fantastis (1000 item ++).
claimed_location: engine/playback/queue_commands.py (on_queue_remove(), on_queue_reorder())
claimed_severity: MEDIUM
source_section: QUE-01 — deque Delete by Index adalah O(n) — Performance Bottleneck
raw_quote: "collections.deque tidak efisien untuk random-access modification... del self.state.queue[cmd.index] di on_queue_remove() adalah O(n)"

---
finding_id: QUE-02
title: ENQUEUE_GENRE_SONGS Tidak Langsung Putar — User Harus Klik Lagi
description: Pemencetan kartu blok tab 'Mix' langsung me-replika lagu ke daftar pemutaran tanpa mengeksekusinya di saat lock sama yang dikembalikan UI. Beresiko me-race parameter lock queue_select dengan parameter lain, menyebabkan gagal playback instan.
claimed_location: server/handlers/ws/queue_handlers.py (_handle_enqueue_genre_songs())
claimed_severity: MEDIUM
source_section: QUE-02 — ENQUEUE_GENRE_SONGS Tidak Langsung Putar — User Harus Klik Lagi
raw_quote: "tiga command terpisah, tidak atomik... Jika race terjadi antara dua execute(), queue bisa berubah."

---
finding_id: QUE-03
title: Queue Tidak Persisten — Hilang Saat Restart
description: Rangkaian data playlist dimemori cuma di injeksi menumpang di variable instance objek lokal. Mengakibatkan pengguna LunaWave nangis gigit jari daftar 50 lagu impiannya menghilang ketiup angin saat program Python ini terpaksa direstart / server shut-down.
claimed_location: core/state.py
claimed_severity: MEDIUM
source_section: QUE-03 — Queue Tidak Persisten — Hilang Saat Restart
raw_quote: "Queue pengguna hilang setiap restart... Queue hanya disimpan di memori (AppState.queue)... UX yang buruk."

---
finding_id: RTY-01
title: CacheResolver.resolve() Tidak Ada Retry untuk Fetch Gagal
description: Interaksi lempar balik fetch request API string youtube langsung error dan tamat memutus loop tanpa adanya peredam logic (mekanik retrying / backoff) memicu satu network drop murni melumpuhkan 1 putaran request lagu begitu saja.
claimed_location: cache/resolver.py (resolve())
claimed_severity: HIGH
source_section: RTY-01 — CacheResolver.resolve() Tidak Ada Retry untuk Fetch Gagal
raw_quote: "Satu kegagalan transien dari yt-dlp (network blip) langsung gagalkan pemutaran. Tidak ada retry atau backoff."

---
finding_id: RTY-02
title: MPV Reconnect Tidak Restore Queue State
description: Skema perbaikan MPV crash sukses membangkitkan instance video ke menit pemutaran namun acuh tidak memanggil re-restore list array (Queue dan state Radio), menumbangkan alur otomatis berurut setelah engine hidup kembali (lagu terputus tidak maju track berikutnya).
claimed_location: engine/playback/controller.py (_on_mpv_reconnected())
claimed_severity: MEDIUM
source_section: RTY-02 — MPV Reconnect Tidak Restore Queue State
raw_quote: "me-restore posisi playback... tapi tidak restore queue atau mode. Jika MPV disconnect saat radio mode, setelah reconnect radio tidak aktif lagi."

---
finding_id: RTY-03
title: _observe_events() Kill + Terminate Tanpa Check Exit Status
description: Engine MPV yang macet dibuang kasar (terminate) ditindih tembakan pamungkas (kill process id) di nol sekon beruntun secara langsung, memantik lemparan error tingkat shell os level (OSError) jika PID id yang dituju sudah terlebih lunas mati.
claimed_location: engine/mpv_controller.py (_observe_events() finally)
claimed_severity: MEDIUM
source_section: RTY-03 — _observe_events() Kill + Terminate Tanpa Check Exit Status
raw_quote: "terminate() lalu self._mpv_process.kill() tanpa delay → kill dikirim mungkin sebelum terminate sempat berjalan... OSError"

---
finding_id: REP-01
title: Database.__getattr__ Proxy Tidak Aman Sebelum init()
description: Rute jembatan call __getattr__ ke SQLite disematkan celah murni yang gagal menahan call panggilan API (get_track dll) sesaat saat object belum menyelesaikan init-nya, yang menyemburkan rentetan attribute exception kosong yang membingungkan bagi developer lain (traceback buta).
claimed_location: cache/db.py (__getattr__())
claimed_severity: HIGH
source_section: REP-01 — Database.__getattr__ Proxy Tidak Aman Sebelum init()
raw_quote: "Jika ada kode yang memanggil db.get_track() sebelum await db.init() selesai... __getattr__ tidak ada guard untuk state 'belum diinisialisasi'"

---
finding_id: REP-02
title: evict_stale_tracks() Load All IDs ke Memory
description: Mekanik pembersihan tembolok kotor database menelan mentah-mentah jutaan dataset dari fetchall() dan mem-pushnya membengkak menjadi variable object python (list buffer) alih-alih me-limit parameter batching SQL. Menurunkan IO ram di skenario ukuran db tinggi.
claimed_location: cache/repositories/track_repository.py (evict_stale_tracks())
claimed_severity: MEDIUM
source_section: REP-02 — evict_stale_tracks() Load All IDs ke Memory
raw_quote: "seluruh video_id di-load ke Python list sebelum delete... fetchall() tanpa batching"

---
finding_id: REP-03
title: discover_handlers.py Bypass Repository Layer — Direct DB Access
description: Endpoint server murni menerobos partisi abstrak level repository dan menendang command pemanggilan baris query sintak execute DB SQLite mentahan via logic websocket tanpa mengindahkn alur port fungsi dan membocorkan arsitektur (coupling brutal).
claimed_location: server/handlers/ws/discover_handlers.py (_handle_toggle_favorite())
claimed_severity: MEDIUM
source_section: REP-03 — discover_handlers.py Bypass Repository Layer — Direct DB Access
raw_quote: "Handler langsung memanggil db.conn.execute()... bypass repository, mengakibatkan duplikasi logic dan tidak ada validasi"

---
finding_id: REP-04
title: SQL WITH RankedSongs Window Function — SQLite Compatibility Risk
description: Sintak mutakhir ROW_NUMBER (window ops) sengaja di lempar keras-keras dari repo discover ke compiler DB. Dimana SQLite usang versi lawas (< 3.25 / tahun 2018) menolak membacanya dan mogok kerja (Crash) — problem termux/docker base android tua.
claimed_location: cache/repositories/discover_repository.py (get_random_songs(), get_genre_songs())
claimed_severity: MEDIUM
source_section: REP-04 — SQL WITH RankedSongs Window Function — SQLite Compatibility Risk
raw_quote: "ROW_NUMBER() OVER (PARTITION BY ...) memerlukan SQLite 3.25+... Termux di Android lama bisa menggunakan versi lebih tua"

---
finding_id: SVC-01
title: DiscoverService Diinstansiasi per Request — Overhead Tidak Perlu
description: Objek servis penyedia lagu campuran difabrikasi ulang berulang menjadi var/objek python memori baru (diinstansiasi gres) terus menerus per panggilan hit websocket, yang menambah cycle beban CPU ringan dan mem-bypass teknik efisiensi cache memori singel.
claimed_location: server/handlers/ws/discover_handlers.py (_build_discover_payload())
claimed_severity: MEDIUM
source_section: SVC-01 — DiscoverService Diinstansiasi per Request — Overhead Tidak Perlu
raw_quote: "Setiap request DISCOVER WebSocket membuat instance DiscoverService baru... pola ini tidak scalable dan mencegah caching tingkat service."

---
finding_id: SVC-02
title: BroadcastService.broadcast_state() Serialisasi Full State per Setiap Progress Event
description: Panggilan penyiaran progress time timer durasi (tick per sekon) memaksa konversi struktur daftar antrean list JSON data-size masif yang membanjiri perlintasan bandwidth, lantaran aplikasi tak mengadopsi mekanisme update bertahap parsial.
claimed_location: server/handlers/event_listeners.py, server/services/broadcast_service.py
claimed_severity: MEDIUM
source_section: SVC-02 — BroadcastService.broadcast_state() Serialisasi Full State per Setiap Progress Event
raw_quote: "_on_queue_updated memanggil broadcast_state() yang serialisasi full state termasuk seluruh queue... ratusan KB per update... Tidak ada differential/incremental state update"

---
finding_id: SVC-03
title: VolumeService Tidak Sync dengan State saat Init
description: Layanan objek class in-memori status volume mengambil nilainya sendiri saja saat boot tanpa mengorelasikan sinkronisasinya ke player daemon mpv asli, sehingga slider volume tidak terpantul-balas (out of sync) nilai benarnya bila mpv diboot berbekal state lawas.
claimed_location: engine/volume_service.py (__init__())
claimed_severity: MEDIUM
source_section: SVC-03 — VolumeService Tidak Sync dengan State saat Init
raw_quote: "current_volume diinisialisasi dari state.volume di constructor, tapi jika MPV sudah berjalan dengan volume berbeda, nilai tidak sync"

---
finding_id: DEP-01
title: Domain Layer Import dari Logging Infrastructure
description: Penataan skrip ranah (domain layer controller) membocorkan privasi levelnya dengan meng-import core log (log_config.py / infrastruktur utilitas) yang merusak batasan bersih pemisahan layer pada arsitektur serta memukul tingkat kesulitan uji unittest mock.
claimed_location: engine/playback/controller.py L17, engine/playback/playback_commands.py L4
claimed_severity: HIGH
source_section: DEP-01 — Domain Layer Import dari Logging Infrastructure
raw_quote: "Domain logic (playback) seharusnya tidak bergantung pada logging infrastructure. Ini menciptakan coupling yang tidak perlu"

---
finding_id: DEP-02
title: track_loader.py Akses DB Langsung via resolver.db
description: Pemanggilan fungsi utilitas loader nekat melompati hierarki interface dengan me-reach (mengambil) instance internal modul database resolver `self.resolver.db`, menimbulkan pengkaitan erat tersembunyi berisiko hancur ketika logic parent resolver disentuh/diganti.
claimed_location: engine/playback/track_loader.py L27
claimed_severity: MEDIUM
source_section: DEP-02 — track_loader.py Akses DB Langsung via resolver.db
raw_quote: "akses database melalui resolver.db — ini mengekspos internal CacheResolver dan menciptakan coupling tidak langsung ke DB."

---
finding_id: DEP-03
title: event_listeners.py Import dari discover_handlers.py — Circular-Risk
description: Script wadah muat listener mereferensikan library file rute web service socket sejawatnya ke ruang filenya, menghasilkan potensi lilitan-keliling lingkaran (circular dependency) dan membobol aturan batas antar-handler.
claimed_location: server/handlers/event_listeners.py L57-58
claimed_severity: MEDIUM
source_section: DEP-03 — event_listeners.py Import dari discover_handlers.py — Circular-Risk
raw_quote: "satu handler mengimport dari handler lain di layer yang sama — antar-handler dependency yang tidak sehat... Tidak ada shared service"

---
finding_id: DEP-04
title: PlaybackController Akses resolver.db Langsung
description: Kode mesin pemutar melantur dengan menancapkan perintah pembaharuan (upsert DB) memakai path variabel `self.resolver.db`, yang padahal ia memiliki instance var pasangannya sendiri `self.db`, menghasilkan var ganda tumpuk saling membingungkan pemanggilan API SQLite nya.
claimed_location: engine/playback/controller.py L89, L105
claimed_severity: MEDIUM
source_section: DEP-04 — PlaybackController Akses resolver.db Langsung
raw_quote: "akses DB melalui dua layer (resolver → db) dari domain controller... kadang pakai self.db, kadang self.resolver.db"

---
finding_id: DEP-05
title: config.py Diimport dari Hampir Semua Layer
description: Semua direktori fungsionalitas murni secara bar-bar meng-import config.py absolut langsung ke berkasnya. Mengakibatkan hard-coupling global yang melumpuhkan kemampuan Dependency Injection (DI) yang baik pada lingkungan deployment berlapis dan pen-tes-an.
claimed_location: Multiple
claimed_severity: MEDIUM
source_section: DEP-05 — config.py Diimport dari Hampir Semua Layer
raw_quote: "config.py diimport dari core/, engine/, cache/, server/, plugins/ — semua layer bergantung pada satu file... Tidak ada dependency injection"


Total temuan diekstrak dari DOKUMEN 11 — Testing Audit: 15


---
finding_id: AUDIT-TEST-001
title: Structural Tests Bukan Behavioral Tests
description: Kumpulan unit test inspeksi mem-parsing isi raw source code fungsi melacak kata string (inspect.getsource) alih-alih me-run fungsinya. Menjadikan file pengujian buta terhadap kebenaran logika berjalan, dan cuma mendeteksi keberadaan kode saja.
claimed_location: tests/unit/engine/test_queue_locking.py, tests/unit/engine/test_radio.py, tests/unit/cache/test_resolver.py, tests/unit/server/test_security.py, tests/unit/server/test_ws_broadcast.py, tests/unit/plugins/test_lyrics_parser.py
claimed_severity: CRITICAL
source_section: AUDIT-TEST-001 — Structural Tests Bukan Behavioral Tests
raw_quote: "hanya memverifikasi bahwa string tertentu ada dalam source code (inspect.getsource)... Test lulus bahkan jika logika salah"

---
finding_id: AUDIT-TEST-002
title: Integration Test Kosong Tanpa Assertion
description: Test module case integrasi perlindungan keamanan IP ditulis melompong nihil tanpa diakhiri satupun baris asserstion, menghasilkan pass-lulus otomatis bodoh selamanya untuk kondisi test cacat.
claimed_location: tests/integration/test_fase1.py, baris ~54–77
claimed_severity: CRITICAL
source_section: AUDIT-TEST-002 — Integration Test Kosong Tanpa Assertion
raw_quote: "adalah test kosong — hanya berisi pass. Test ini lulus selalu... padahal tidak diverifikasi sama sekali."

---
finding_id: AUDIT-TEST-003
title: Tidak Ada Test untuk Critical Path: MPV Controller
description: Otak inti penggerak dan controller engine audio (MPV) sama sekali hampa tidak pernah dimasukkan ke satupun skema tes skenario berjalan. Kondisi rawannya logika IPC loop, reconnect, atau play-stop menjadi buta.
claimed_location: engine/mpv_controller.py
claimed_severity: CRITICAL
source_section: AUDIT-TEST-003 — Tidak Ada Test untuk Critical Path: MPV Controller
raw_quote: "jantung aplikasi (300 baris, 18 method). Tidak ada satu pun test... logic berikut sepenuhnya tidak diuji"

---
finding_id: AUDIT-TEST-004
title: Tidak Ada Test untuk Auth Handler (Login Flow)
description: Rute masuk dan keluar klien pada server otentikasi kunci utama sistem password login tidak diproteksi uji tes case apapun. Menutupi potensi eksploit brutal token (brute force) atau cookie hijacking.
claimed_location: server/handlers/auth.py
claimed_severity: CRITICAL
source_section: AUDIT-TEST-004 — Tidak Ada Test untuk Auth Handler (Login Flow)
raw_quote: "menangani login, pembuatan session, dan response cookie — tidak ada satu pun test. Ini adalah attack surface utama."

---
finding_id: AUDIT-TEST-005
title: Tidak Ada Test untuk YtDlpClient
description: Modul jembatan pembentuk perintah call ke library yt-dlp pencari video sama sekali tidak di-stub/di-mock via unit testing, meloloskan handling error fatal jaringan atau manipulasi data API mentah tak diketahui sistem.
claimed_location: engine/ytdlp_client.py
claimed_severity: CRITICAL
source_section: AUDIT-TEST-005 — Tidak Ada Test untuk YtDlpClient
raw_quote: "melakukan network call nyata ke YouTube. Tidak ada test dengan mock yt-dlp... Bug di _pick_audio_url tidak terdeteksi"

---
finding_id: AUDIT-TEST-006
title: Tidak Ada Test untuk RadioEngine Logic
description: Konsep perputaran antrean pintar mesin radio seperti fetch track acak, exclude, rotate array tidak tersentuh testing behavioral, hanya mengandalkan inspeksi parse source code yang tak berguna memverifikasi fungsinya.
claimed_location: engine/radio_engine.py
claimed_severity: CRITICAL
source_section: AUDIT-TEST-006 — Tidak Ada Test untuk RadioEngine Logic
raw_quote: "Seluruh behavioral logic berikut tidak diuji... fallback ke file JSON... prefetch di-trigger... artist pop dan push kembali"

---
finding_id: AUDIT-TEST-007
title: Tidak Ada Test untuk Resolver (Cache TTL Logic)
description: Interval limit batas kedaluwarsa waktu string tautan media media belum ditelusuri logic timing test-nya, sebatas parsing konstanta hardcode file, menutupi celah link basi (expired ttl timeout limit).
claimed_location: cache/resolver.py
claimed_severity: HIGH
source_section: AUDIT-TEST-007 — Tidak Ada Test untuk Resolver (Cache TTL Logic)
raw_quote: "Hanya structural test... Behavioral test untuk logika TTL itu sendiri... Yang tidak ada"

---
finding_id: AUDIT-TEST-008
title: Tidak Ada Test untuk WS Command Handlers
description: Ribuan baris kode rute masuk lalu-lintas event websocket (antre, set volume, play dll) belum dibuat mock case simulasi satupun. Menimbulkan kecacatan sinkronisasi state dari command UI klien luput tidak dihandle.
claimed_location: server/handlers/ws/
claimed_severity: CRITICAL
source_section: AUDIT-TEST-008 — Tidak Ada Test untuk WS Command Handlers
raw_quote: "Seluruh server/handlers/ws/ (~8 file, ~400 baris) tidak diuji. Ini mencakup: _handle_play_track... _handle_seek"

---
finding_id: AUDIT-TEST-009
title: Tidak Ada Test untuk SponsorBlock Plugin
description: Blok pemotong iklan (SponsorBlock) yang menyerap segmen array timestamp tidak disandingkan test verifikator pemanggilan skip pada posisi sekon time video. Beresiko loop skip memutar terus atau gagal skip.
claimed_location: plugins/sponsorblock.py
claimed_severity: HIGH
source_section: AUDIT-TEST-009 — Tidak Ada Test untuk SponsorBlock Plugin
raw_quote: "Yang tidak diuji: fetch_segments dengan response JSON valid... _on_progress — apakah seek di-trigger pada waktu yang tepat?"

---
finding_id: AUDIT-TEST-010
title: Frontend: Tidak Ada Test Runner Otomatis
description: Lapis antarmuka javascript dibiarkan berjalan hampa telanjang tak punya pengujian unit runner tool apapun (seperti jest/vitest), cuma bersandar pada 1 page testing visual manual konvensional yang tak berimbas.
claimed_location: Seluruh web/static/js/
claimed_severity: CRITICAL
source_section: AUDIT-TEST-010 — Frontend: Tidak Ada Test Runner Otomatis
raw_quote: "Seluruh 25 modul JavaScript tidak memiliki automated test... hanya manual browser test yang tidak bisa di-run di CI"

---
finding_id: AUDIT-TEST-011
title: Mock Strategy Terlalu Longgar di E2E Tests
description: Modul fungsi mock penguji koneksi integrasi akhir memancangkan default check token-pass-berhasil (return true all) pada verifikator session token secara sewenang-wenang membabi buta, yang berakibat otentikasi login apa saja akan lewat lulus walau salah.
claimed_location: tests/integration/test_e2e.py
claimed_severity: HIGH
source_section: AUDIT-TEST-011 — Mock Strategy Terlalu Longgar di E2E Tests
raw_quote: "mock_db.verify_session di-mock return True secara default... semua token diterima, termasuk token kosong atau invalid."

---
finding_id: AUDIT-TEST-012
title: Tidak Ada Test untuk Concurrency / Race Condition
description: Mekanik asinkron lalu lintas ganda interupsi (konkurensi thread) sepi total dari beban pengujian (stress collision task test). Aplikasi buta akan penanganan lock-queue race jika di spam WS berentet oleh admin.
claimed_location: test suites (global)
claimed_severity: CRITICAL
source_section: AUDIT-TEST-012 — Tidak Ada Test untuk Concurrency / Race Condition
raw_quote: "Aplikasi ini heavily concurrent... Tidak ada satu pun test yang mensimulasikan concurrent access. Race conditions... tidak diverifikasi"

---
finding_id: AUDIT-TEST-013
title: Tidak Ada Test untuk Notifications Plugin
description: Sinyal pemanggilan loop event OS di backend notif diparkir mandiri tanpa uji thread cleanup maupun uji lemparan string broadcast title. Logika ini akan beresiko freeze thead bila dibiarkan menggantung.
claimed_location: plugins/notifications.py
claimed_severity: HIGH
source_section: AUDIT-TEST-013 — Tidak Ada Test untuk Notifications Plugin
raw_quote: "memiliki blocking thread (_blocking_read_loop)... Tidak ada test untuk: Thread cleanup... Event TrackStartedEvent memicu notifikasi"

---
finding_id: AUDIT-TEST-014
title: Tidak Ada Performance / Load Test
description: Kekokohan infrastruktur jaringan real-time streaming tak dibackup oleh profil beban (benchmark perf) pengujian jumlah maksimal bandwidth / koneksi klien (load test) membahayakan kapabilitas server crash bila dihantam banyak user.
claimed_location: test suites (global)
claimed_severity: HIGH
source_section: AUDIT-TEST-014 — Tidak Ada Performance / Load Test
raw_quote: "Tidak ada benchmark atau load test untuk: Berapa banyak concurrent WS connection... broadcast ke N client... Memory usage"

---
finding_id: AUDIT-TEST-015
title: Fixture Tunggal sample_track.json Tidak Cukup
description: Pangkalan sumber data bohongan pengetesan hanya disuntik 1 file model yang kelewat standar murni bersih lurus, melupakan file uji batas anomali cacat karakter khusus atau array cacat, menimbulkan false pass.
claimed_location: tests/fixtures/sample_track.json
claimed_severity: MEDIUM
source_section: AUDIT-TEST-015 — Fixture Tunggal sample_track.json Tidak Cukup
raw_quote: "Hanya ada satu fixture file JSON. Tidak ada fixture untuk: Track dengan thumbnail Null... judul mengandung karakter Unicode... response cacat"


Total temuan diekstrak dari DOKUMEN 12 — DevOps Audit: 35


---
finding_id: DEVOPS-001
title: Dockerfile Mereferensikan run.py yang Tidak Ada
description: Titik eksekusi container (CMD) pada Dockerfile dengan ceroboh di-set untuk memanggil "run.py", yang mana sama sekali tak ada dalam direktori aplikasi (hanya ada main.py). Membuat deployment otomatis langsung crash seketika (fatal).
claimed_location: Dockerfile, baris 28
claimed_severity: CRITICAL
source_section: DEVOPS-001 — Dockerfile Mereferensikan run.py yang Tidak Ada
raw_quote: "CMD [\"python\", \"run.py\"] ... run.py TIDAK ADA ... container langsung crash saat start"

---
finding_id: DEVOPS-002
title: Container Berjalan Sebagai Root
description: File racikan Docker melalaikan deklarasi pembuatan ruang profil pengguna (USER), menjadikan hak akses aplikasi berjalan sebagai raja (root) di dalam container, sangat rentan di-infiltrasi hingga menembus host OS jika aplikasi bobol.
claimed_location: Dockerfile (keseluruhan)
claimed_severity: CRITICAL
source_section: DEVOPS-002 — Container Berjalan Sebagai Root
raw_quote: "Tidak ada direktif USER di Dockerfile. Container berjalan sebagai root (UID 0)... Ini adalah pelanggaran prinsip least-privilege"

---
finding_id: DEVOPS-003
title: Tidak Ada HEALTHCHECK di Dockerfile
description: Parameter ping status (Healthcheck) dilupakan di script docker. Saat aplikasi python macet melayang (hang), instansi manajer docker tidak dapat mendeteksi kondisi mati rasa aplikasi untuk me-restartnya secara otomatis (Up terus padahal modar).
claimed_location: Dockerfile
claimed_severity: HIGH
source_section: DEVOPS-003 — Tidak Ada HEALTHCHECK di Dockerfile
raw_quote: "Docker tidak bisa mendeteksi apakah container dalam keadaan sehat atau stuck... docker ps akan menampilkan Up meskipun server sudah crash"

---
finding_id: DEVOPS-004
title: Volume Docker Hanya Mount /app/data, Cache dan Logs Hilang Saat Restart
description: Konfigurasi Compose me-mount 1 direktori belaka (/app/data), sementara tumpukan berharga cache download, catatan history log, serta pendaftaran pasword admin (/app/cache) akan tersapu rata dan musnah tak berbekas begitu container direstart.
claimed_location: docker-compose.yml
claimed_severity: CRITICAL
source_section: DEVOPS-004 — Volume Docker Hanya Mount /app/data, Cache dan Logs Hilang Saat Restart
raw_quote: "hanya mount ./data:/app/data. Direktori berikut tidak di-persist dan hilang setiap container restart... cache/mp3/ ... logs/"

---
finding_id: DEVOPS-005
title: Port Binding ke 0.0.0.0 Tanpa Firewall Layer
description: Ekstraksi map binding port pada konfigurasi docker (0.0.0.0:8765) dengan ceroboh mengekspos rute langsung aplikasi mentah ke ranah internet publik bila perangkat punya public IP. Beresiko ditembus penyusup tanpa pelindung firewall reverse proxy tambahan (seperti nginx).
claimed_location: docker-compose.yml, baris ports
claimed_severity: HIGH
source_section: DEVOPS-005 — Port Binding ke 0.0.0.0 Tanpa Firewall Layer
raw_quote: "Port 8765 di-bind ke semua interface (0.0.0.0:8765:8765)... terbuka ke internet. Untuk aplikasi yang didesain sebagai personal server, ini berisiko."

---
finding_id: DEVOPS-006
title: Layer Caching Dockerfile Tidak Optimal
description: Tata perancangan layer script docker kurang cermat menaruh aksi transfer source code (COPY . .) di atas lintasan install dependensi NPM. Mengakibatkan setiap perubahaan Python sedetik pun juga harus membuild ulang module bundle npm yang berat memperlambat siklus iterasi (cache bust sia-sia).
claimed_location: Dockerfile
claimed_severity: MEDIUM
source_section: DEVOPS-006 — Layer Caching Dockerfile Tidak Optimal
raw_quote: "COPY . . dilakukan sebelum npm build. Setiap perubahan source code... akan invalida seluruh layer termasuk npm install. Build lambat."

---
finding_id: DEVOPS-007
title: Tidak Ada Continuous Deployment (CD)
description: Alur roda pipa perakitan otomatis (CI pipeline) terputus di tengah (hanya testing), absennya step pengantaran build rilis ke ekosistem production berujung pada pen-deployan kuli manual yang rentan kecelakaan/human-error.
claimed_location: .github/workflows/ci.yml
claimed_severity: HIGH
source_section: DEVOPS-007 — Tidak Ada Continuous Deployment (CD)
raw_quote: "CI pipeline hanya melakukan test dan lint. Tidak ada otomasi deployment... manual yang tidak terdokumentasi, berisiko human error."

---
finding_id: DEVOPS-008
title: Windows CI Job Tidak Menjalankan Tests
description: Pengecekan otomatis server CI yang spesifik untuk ekosistem (OS) windows hanya main pura-pura uji parse (cek sintak cmd doang) dan melewatkan tes unit pytest core, membiarkan bug patal versi rute backslash windows tembus (silent bug).
claimed_location: .github/workflows/ci.yml
claimed_severity: HIGH
source_section: DEVOPS-008 — Windows CI Job Tidak Menjalankan Tests
raw_quote: "Job test-windows di CI hanya mengecek apakah start.bat bisa diparsing... TIDAK ADA pytest di sini!"

---
finding_id: DEVOPS-009
title: CI Coverage Threshold Terlalu Rendah (40%)
description: Syarat indikator lolos kualitas hijau dari porsentase uji test unit dipatok amat teramat miskin cuma 40 persen (--cov-fail-under=40), menumbuhkan penipuan (false sense) keamanan code yang meloloskan > separuh kode tak teruji ke produksi.
claimed_location: .github/workflows/ci.yml, baris 41
claimed_severity: MEDIUM
source_section: DEVOPS-009 — CI Coverage Threshold Terlalu Rendah (40%)
raw_quote: "threshold yang sangat rendah... memberikan false sense of security — CI hijau meskipun 60% kode tidak diuji."

---
finding_id: DEVOPS-010
title: Tidak Ada CI Job untuk Frontend JavaScript
description: Jaring pengecekan rilis membiarkan folder web interface Javascript buta-buta telanjang menembus release karena "npm test" tidak di definisikan runnernya (echo error di package.json). Bug fatal client frontend tidak bisa terdeteksi CI.
claimed_location: .github/workflows/ci.yml, package.json
claimed_severity: HIGH
source_section: DEVOPS-010 — Tidak Ada CI Job untuk Frontend JavaScript
raw_quote: "package.json mendefinisikan \"test\": \"echo \\\"Error: no test specified\\\" && exit 1\"... Bug JavaScript tidak akan terdeteksi di CI."

---
finding_id: DEVOPS-011
title: Tidak Ada Artifact Pinning / Reproducible Build
description: Rantai pipa server github-actions menarik paket dependensi luar tanpa dipatok kode rilis hash absolut (contoh action checkout). Rentan sekali jikalau aksi library luar terinfiltrasi malware otomatis merembet pada aplikasi proyek (supply chain attack risk).
claimed_location: .github/workflows/ci.yml
claimed_severity: MEDIUM
source_section: DEVOPS-011 — Tidak Ada Artifact Pinning / Reproducible Build
raw_quote: "CI menggunakan actions/checkout@v4 tanpa SHA pinning. Jika action di-hijack (supply chain attack), CI bisa disusupi."

---
finding_id: DEVOPS-012
title: Inkonsistensi Prefix Environment Variable (3 Skema Berbeda)
description: Nama penanda environment server tumpang-tindih bercampur 3 ragam prefix aneh sekaligus secara berantakan (YTGUI_, LUNAWAVE_, YT_PLAYER_, LunaWave_PORT). Saat admin mengisi dari .env.example (YTGUI_), sistem diam-diam membaca yang lain, sehingga gagal mem-passing admin_password tanpa pesan (silent fail).
claimed_location: config.py, .env.example, start.sh, start.py
claimed_severity: CRITICAL
source_section: DEVOPS-012 — Inkonsistensi Prefix Environment Variable (3 Skema Berbeda)
raw_quote: "tiga prefix berbeda secara bersamaan untuk env var yang saling terkait... config.py membaca LUNAWAVE_ADMIN_PASS (TIDAK TERBACA!)"

---
finding_id: DEVOPS-013
title: admin_password.txt Disimpan dalam Plaintext Hash Tanpa Enkripsi Tambahan
description: Dokumen pengingat simpanan kata sandi administrator tercetak polos ke file plaintext hash secara kasar di wilayah direktori bebas yang berdampingan di area "cache" lagu MP3, membuatnya gampang dicolong diekstrak paksa peretas jikalau server terpapar bocor exploit transversal zip.
claimed_location: config.py, baris 66–69
claimed_severity: HIGH
source_section: DEVOPS-013 — admin_password.txt Disimpan dalam Plaintext Hash Tanpa Enkripsi Tambahan
raw_quote: "menyimpan PBKDF2 hash... di dalam cache/ yang bersebelahan dengan MP3 files... mereka bisa melakukan offline dictionary attack"

---
finding_id: DEVOPS-014
title: docker-compose.yml Tidak Meneruskan Secrets dari Environment
description: Struktur pembungkus compose environment abai tidak mendistribusikan turunan secret-token maupun pasword rahasia server (seperti LUNAWAVE_ADMIN_PASS). Membuat setting manual env luar tertelan dan wadah terpaksa meng-generate kunci random terus.
claimed_location: docker-compose.yml
claimed_severity: HIGH
source_section: DEVOPS-014 — docker-compose.yml Tidak Meneruskan Secrets dari Environment
raw_quote: "hanya meneruskan PYTHONUNBUFFERED=1... LUNAWAVE_ADMIN_PASS tidak ada... Container akan selalu menggunakan auto-generated password"

---
finding_id: DEVOPS-015
title: Password Admin Tercetak ke stderr di TTY
description: Password login murni tak ter-hash yang di-generate perdana tercetak ke wadah shell console log sys.stderr, di mana oleh script eksekutor termux (android) dipaksa dilempar terekam utuh ke dalam log file plaintext (>> startup.log 2>&1). Menghamparkan pundi password bagi sesiapa yang nimbrung.
claimed_location: config.py, baris 76–79
claimed_severity: HIGH
source_section: DEVOPS-015 — Password Admin Tercetak ke stderr di TTY
raw_quote: "password raw (sebelum di-hash) ditulis ke sys.stderr... termux_boot.sh melakukan 2>&1... password plaintext masuk ke log file."

---
finding_id: DEVOPS-016
title: JS Bundle Tidak Di-build dalam Docker Image
description: Pembungkus perakitan kontainer abai me-running script penjahit (npm run build) halaman. Jika repo bersih tak punya file bundle.js (karena ter-gitignore dari host), maka aplikasi Docker yang dionline-kan buta 100% tanpa skrip interaksi frontend satupun (lumpuh putih UI).
claimed_location: Dockerfile
claimed_severity: CRITICAL
source_section: DEVOPS-016 — JS Bundle Tidak Di-build dalam Docker Image
raw_quote: "Dockerfile tidak menjalankan npm run build... container akan serve halaman tanpa JavaScript yang ter-bundle. App tidak akan berfungsi."

---
finding_id: DEVOPS-017
title: requirements.txt dan pyproject.toml Tidak Sinkron
description: Pengaturan paket library aplikasi tercerai belai menyamping pada 2 file rujukan independen (req.txt dan toml) tanpa pengunci sinkronisasi korelasi satu-kebenaran (sync single truth). Berakibat error inkonsisten di staging-dev versus saat di run via build Docker.
claimed_location: requirements.txt, pyproject.toml
claimed_severity: HIGH
source_section: DEVOPS-017 — requirements.txt dan pyproject.toml Tidak Sinkron
raw_quote: "Tidak ada mekanisme untuk memastikan keduanya sinkron... menyebabkan environment yang inconsistent antara pip install -r dan pip install -e"

---
finding_id: DEVOPS-018
title: make_dist.sh Menggunakan git archive Tanpa Verifikasi Integritas
description: Proses pengepakan arsip zip rilis program manual cuma mem-pump `git archive` mentahan, telanjang tak disertai stempel tanda periksa keamanan file SHA-checksum, gagal melakukan verifikasi tag versi dan juga lupa menginklusikan compile-an frontend bundle.js yang diperlukan.
claimed_location: scripts/make_dist.sh
claimed_severity: MEDIUM
source_section: DEVOPS-018 — make_dist.sh Menggunakan git archive Tanpa Verifikasi Integritas
raw_quote: "Tidak ada: Checksum (SHA256)... Version tagging otomatis... Verifikasi bahwa bundle.js sudah ter-build"

---
finding_id: DEVOPS-019
title: Tidak Ada Proses Release Formal
description: Pola rilis berantakan tanpa wadah track log perubahan terpusat, pengingat rilis di kode (main.py) mematok angka ngawur (1.0.0) yang mengacuhkan versi project paten aslinya yang sedang di 0.1.0 di file pyproject.
claimed_location: main.py baris 1, pyproject.toml
claimed_severity: HIGH
source_section: DEVOPS-019 — Tidak Ada Proses Release Formal
raw_quote: "main.py adalah hardcoded __version__ = \"1.0.0\" dan tidak terhubung ke pyproject.toml yang memiliki version = \"0.1.0\" (inkonsisten!)."

---
finding_id: DEVOPS-020
title: Rollback via git checkout Berbahaya di Environment Produksi
description: Skrip pembantu darurat untuk mengembalikan patch lawas menggunakan teknik paksa brutal reset git checkout ke id mundur, memblok mundur file sistem mentah tanpa meng-stop daemon running Python, menjebol koneksi DB berakibat cacat parah file lokal korup.
claimed_location: scripts/rollback.sh
claimed_severity: CRITICAL
source_section: DEVOPS-020 — Rollback via git checkout Berbahaya di Environment Produksi
raw_quote: "menggunakan git checkout <target> untuk rollback. Ini sangat berbahaya... Tidak ada stop server sebelum rollback — database bisa corrupt"

---
finding_id: DEVOPS-021
title: Tidak Ada Database Migration Framework
description: Struktur desain tabel sqlite di-inject asal sabet menumpang numpuk baris (add column) sekenanya per boot program. Saat sistem harus di rollback turun versi karena bug server, tabel akan menabrak hancur lantaran hilangnya riwayat manajemen transisi kolom database (migration file/alembic).
claimed_location: cache/db.py (init)
claimed_severity: HIGH
source_section: DEVOPS-021 — Tidak Ada Database Migration Framework
raw_quote: "Skema DB diubah dengan ALTER TABLE di db.init() secara ad-hoc. Tidak ada versioning migrasi... Rollback ke versi lama bisa menyebabkan skema tidak kompatibel"

---
finding_id: DEVOPS-022
title: Prometheus Metrics Ada Tapi Tidak Terhubung ke Sistem Monitoring
description: Dekorasi penyetelan export data grafik kinerja (Metrics) yang tertanam di server hanya menjadi hiasan statis, lantaran hilangnya rantai kaitan ke sistem ekosistem pembaca penangkap log utamanya (Prometheus / Grafana). Metric dibuat untuk dicuekin (Theater monitoring semata).
claimed_location: docker-compose.yml, core/observability.py
claimed_severity: HIGH
source_section: DEVOPS-022 — Prometheus Metrics Ada Tapi Tidak Terhubung ke Sistem Monitoring
raw_quote: "Endpoint /metrics tersedia. Namun tidak ada prometheus.yml, tidak ada Grafana... Metrics ada tapi tidak ada yang membacanya — monitoring theater."

---
finding_id: DEVOPS-023
title: Metrics yang Terdefinisi Tidak Mencukupi untuk Production Monitoring
description: Ekstraksi catatan data (Gauge) sangat minim dan dangkal, meloloskan buta parameter kritis yang penting seperti statistik jumlah download fail, rute kueri server database mandek, hingga status mati-tidak MPV (Cuma ada 4 item unfaedah).
claimed_location: core/observability.py
claimed_severity: MEDIUM
source_section: DEVOPS-023 — Metrics yang Terdefinisi Tidak Mencukupi untuk Production Monitoring
raw_quote: "Hanya ada 4 metric... Tidak ada metric untuk: Error rate... DB query latency... YtDlp resolve latency... Radio mode health"

---
finding_id: DEVOPS-024
title: Log Hanya ke File Lokal, Tidak Ada Centralized Logging
description: Sistem pen-catatan event error aplikasi memendam file tulisannya khusus pada /logs lokal saja per 5MB putaran. Bencana kehilangan file saat sistem Docker hang membuat error lenyap, karna output print tidak dilempar standar keluar (stdout) di mode container.
claimed_location: core/log_config.py
claimed_severity: HIGH
source_section: DEVOPS-024 — Log Hanya ke File Lokal, Tidak Ada Centralized Logging
raw_quote: "Log ditulis ke logs/app.log dengan RotatingFileHandler... Log hilang saat container restart... Tidak ada structured log shipping"

---
finding_id: DEVOPS-025
title: Log File Tidak Di-mount di Docker Container
description: Sambungan dari temuan direktori kontainer (004). Volume pembuat logs tidak dipetakan ke host lokal, menyebabkan seluruh catatan sakti saat proses crash langsung terkubur wafat sesaat setelah container ditendang restart ulang, debug tak mungkin dilakukan (mustahil dicari lognya).
claimed_location: docker-compose.yml
claimed_severity: HIGH
source_section: DEVOPS-025 — Log File Tidak Di-mount di Docker Container
raw_quote: "logs/ tidak di-mount sebagai volume. Saat container restart, seluruh riwayat log hilang. Tidak bisa melakukan post-mortem analysis"

---
finding_id: DEVOPS-026
title: Structlog Tidak Menyertakan Correlation ID / Request ID
description: Perekam barisan pesan log buta-buta membom penulisan pesan tanpa dibekali token id berantai (Req ID). Begitu server padat dipakai paralel, admin akan mual muntah mengurai membedakan baris log mana yang milik rute user 1 dibanding rute event user 2 (pencampuran baris pusing).
claimed_location: server/middleware.py, core/log_config.py
claimed_severity: MEDIUM
source_section: DEVOPS-026 — Structlog Tidak Menyertakan Correlation ID / Request ID
raw_quote: "Log tidak memiliki correlation ID... tidak bisa trace log dari satu request/WebSocket session ke seluruh pipeline... Debugging sangat sulit."

---
finding_id: DEVOPS-027
title: Tidak Ada Sistem Alerting Sama Sekali
description: Ketiadaan notifikator (alarm sirine system warning) bagi operasi server. Bilamana mesin lumpuh ditengah jalan atau RAM kepenuhan pada pukul 3 subuh, admin baru ngeh keesokan hari secara manual, karena script pemberi tanda SOS sama sekali belum dirancang satupun.
claimed_location: test suites (global)
claimed_severity: CRITICAL
source_section: DEVOPS-027 — Tidak Ada Sistem Alerting Sama Sekali
raw_quote: "Jika server crash, MPV disconnect, DB korup... tidak ada notifikasi. Operator hanya bisa tahu dari monitor_health.sh yang harus dijalankan secara manual"

---
finding_id: DEVOPS-028
title: monitor_health.sh Tidak Memeriksa MPV Status
description: Skrip bash pengecek kesehatan mesin ngawur mentah-mentah melihat label string "ok" walau isi perut report menyebutkan mpv (engine suara inti) dalam status modar/mati (not_started). Cek up ini menyesatkan admin, server dilaporin oke walau engine jebol.
claimed_location: scripts/monitor_health.sh
claimed_severity: HIGH
source_section: DEVOPS-028 — monitor_health.sh Tidak Memeriksa MPV Status
raw_quote: "STATUS != \"ok\"... Namun /health mengembalikan \"ok\" bahkan jika MPV disconnect... Kondisi degraded... tidak terdeteksi."

---
finding_id: DEVOPS-029
title: Backup Database Hanya Satu File .bak (Overwrite Setiap 24 Jam)
description: Roda rutinitas salin db 24 jam dengan kejam selalu menimpa file duplikat yang itu-itu lagi (.bak) selamanya tanpa sistem antrean berurut (rotasi array max). Kalau database asli error busuk pas ter-copas jam tersebut, admin ga akan punya mundur sisa versi cadangan satupun lagi (kedua file sama-sama busuk).
claimed_location: core/background_tasks.py, baris 32
claimed_severity: CRITICAL
source_section: DEVOPS-029 — Backup Database Hanya Satu File .bak (Overwrite Setiap 24 Jam)
raw_quote: "Selalu overwrite file yang sama! ... Jika corruption terjadi tepat sebelum backup run berikutnya, backup .bak sudah corrupt juga"

---
finding_id: DEVOPS-030
title: Tidak Ada Backup untuk File MP3 Download
description: Ratusan berkas lagu mentah cache-offline kesayangan yang telah capek-capek dimuat tak diamankan dalam backup rotasi database (hanya file data .db nya). Hancurnya disk atau error hapus kontainer berarti reset 0 dari ulang pemanggilan download API yt dari awal lagi semua lagunya.
claimed_location: test suites (global)
claimed_severity: HIGH
source_section: DEVOPS-030 — Tidak Ada Backup untuk File MP3 Download
raw_quote: "File MP3 yang sudah di-download ke cache/mp3/ tidak di-backup. Jika disk failure... semua MP3... hilang. Re-download... memerlukan waktu"

---
finding_id: DEVOPS-031
title: Backup Tidak Diverifikasi Setelah Dibuat
description: Mekanik panggil api salin copy database langsung melepasnya begitu script copy kelar dan diam bertawakal buta berasumsi filenya sempurna berjalan tanpa melakukan re-verify integrity_check memastikan integritas. Jika ada corrupt IO, backup akan sukses semu padahal rusak.
claimed_location: core/background_tasks.py
claimed_severity: HIGH
source_section: DEVOPS-031 — Backup Tidak Diverifikasi Setelah Dibuat
raw_quote: "tidak ada verifikasi bahwa backup file valid dan tidak corrupt setelah dibuat."

---
finding_id: DEVOPS-032
title: Tidak Ada Rencana Disaster Recovery
description: Nihilnya pakem buku panduan prosedur penangan cacat parah atau crash total. Operator bakal kebingungan mati lemes kalau misal server kena sabotase, tidak tahu urutan RPO maupun letak langkah recovery db manual pas kondisi hidup dan mati karena no-playbook document.
claimed_location: test suites (global)
claimed_severity: CRITICAL
source_section: DEVOPS-032 — Tidak Ada Rencana Disaster Recovery
raw_quote: "Tidak ada dokumentasi tentang: RTO... RPO... Prosedur recovery saat disk failure... saat database corrupt... saat server di-compromise"

---
finding_id: DEVOPS-033
title: Termux Boot Script Tidak Menangani Kegagalan Startup
description: Script startup daemon auto-load linux termux android mengeksekusi jalan paksa background terminal server dengan mengabaikan sinyal kelar. Jadi misal script macet di detik 1 gagal build dependensi, bash akan menipu menelurkan log berhasil (exit 0) padahal proses crash.
claimed_location: scripts/termux_boot.sh
claimed_severity: HIGH
source_section: DEVOPS-033 — Termux Boot Script Tidak Menangani Kegagalan Startup
raw_quote: "menjalankan ./start.sh >> logs/startup.log 2>&1 & tanpa memeriksa apakah startup berhasil. Jika server gagal start... script tetap exit 0"

---
finding_id: DEVOPS-034
title: opentelemetry Disebut di Dependency Check Tapi Tidak di requirements.txt
description: Teks parameter string pada skrip bash pemeriksa run-time dependencies error nyebut library (opentelemetry) yang sama sekali melompong tak ada hubungannya dengan pip list requirement rilis file. Menelurkan false negative (minta di-install padahal ga dipake sama sekali).
claimed_location: start.sh, requirements.txt
claimed_severity: HIGH
source_section: DEVOPS-034 — opentelemetry Disebut di Dependency Check Tapi Tidak di requirements.txt
raw_quote: "start.sh dan start.bat memeriksa import opentelemetry... tapi requirements.txt dan pyproject.toml tidak mencantumkannya... false negative"

---
finding_id: DEVOPS-035
title: /tmp Socket Path di .env.example Berbahaya di Shared Environment
description: Panduan penulisan rute soket komunikasi MPV pada templat lingkungan dev keliru merekomendasikan penanaman pipa socket di direktori publik global sistem operasi yang absolut tidak aman (/tmp). Membahayakan pintu intersep socket diretas penyusup (bisa lempar fake command player dari app tetangga).
claimed_location: .env.example, baris 11
claimed_severity: MEDIUM
source_section: DEVOPS-035 — /tmp Socket Path di .env.example Berbahaya di Shared Environment
raw_quote: "menganjurkan YT_PLAYER_SOCKET=/tmp/mpv-ytgui.sock. Pada sistem multi-user... file di /tmp bisa diakses user lain. Socket MPV yang terbuka bisa dieksploitasi"


Total temuan diekstrak dari DOKUMEN 13 — Dependency Audit: 14


---
finding_id: DEP-001
title: VERSION CONFLICT aiosqlite Berbeda di Dua File
description: Indikator versi spesifik aiosqlite tidak nyambung (bentrok) di dua titik (req.txt 0.20 dan pyproject 0.22). Jika developer menggunakan satu dan build docker menggunakan lainnya, bug siluman yang hanya ada di py 0.20 akan menghantui satu sisi environment namun lenyap di sisi satunya.
claimed_location: requirements.txt baris 2, pyproject.toml baris 8
claimed_severity: CRITICAL
source_section: TEMUAN #1 — VERSION CONFLICT: aiosqlite Berbeda di Dua File
raw_quote: "requirements.txt aiosqlite==0.20.0 ... pyproject.toml \"aiosqlite==0.22.1\" ... Bug ini bisa muncul di production namun tidak terreproduksi di development"

---
finding_id: DEP-002
title: node_modules Tidak Ada di .gitignore
description: Folder monster node_modules lupa di-blacklis di gitignore. Menjadikan file sampah dependensi lokal masuk tercommit membebani repository. Hal paling fatal binari node_module milik arsitektur PC developer (e.g win-x64) akan menimpa produksi server linux OS, merusak run runtime app.
claimed_location: .gitignore
claimed_severity: CRITICAL
source_section: TEMUAN #2 — CRITICAL: node_modules Tidak Ada di .gitignore
raw_quote: ".gitignore tidak menyertakan node_modules/ sama sekali... Binary platform yang salah masuk ke production (zip berisi @esbuild/win32-x64 binary, bukan Linux)"

---
finding_id: DEP-003
title: CDN External tanpa Subresource Integrity (SRI)
description: Link tembakan resource desain Font (Tabler icons) diarahkan dari jsdelivr eksternal murni tanpa filter pencocokan validitas hash-checksum (SRI). Bila cdn dibajak hacker dan link diisi malware js injeksi, seluruh user LunaWave seketika tertular otomatis (Supply Chain Attack vector).
claimed_location: web/static/index.html baris 17-18
claimed_severity: CRITICAL
source_section: TEMUAN #3 — CRITICAL: CDN External tanpa Subresource Integrity (SRI)
raw_quote: "CDN External tanpa Subresource Integrity (SRI)... Jika CDN dicompromise... attacker bisa menyuntikkan JavaScript arbitrer ke semua user"

---
finding_id: DEP-004
title: Package Name Mismatch antara package.json dan package-lock.json
description: File peniti kunci paket (package-lock) tidak pernah di perbaharui secara pas dengan package asalnya saat project berubah nama. Lock name ngotot pake nama lama ytgui-project sedang json barunya lunawave. Berpotensi CI pipe eror jika melakukan validasi ketat nama paket.
claimed_location: package.json baris 2, package-lock.json baris 2
claimed_severity: MAJOR
source_section: TEMUAN #4 — MAJOR: Package Name Mismatch antara package.json dan package-lock.json
raw_quote: "package.json punya nama \"lunawave-project\" namun package-lock.json masih menggunakan nama lama \"ytgui-project\". Ini menandakan lock file tidak pernah di-regenerate"

---
finding_id: DEP-005
title: Python Version Inconsistency di Tiga Tempat
description: Tembakan minimal os python beda-beda belangsak pada 3 setting file. Pyproject bilang >=3.10, CI di 3.11, Docker di 3.12. Membuat kelolosan error ga singkron (test lolos di versi 3.11 tapi jebol deprecated library pas di-docker pake versi 3.12).
claimed_location: pyproject.toml, .github/workflows/ci.yml, Dockerfile
claimed_severity: MAJOR
source_section: TEMUAN #5 — MAJOR: Python Version Inconsistency di Tiga Tempat
raw_quote: "Tiga lokasi berbeda mendefinisikan versi Python berbeda, menyebabkan behavior berbeda antara development, CI, dan production Docker"

---
finding_id: DEP-006
title: Dockerfile Merujuk File yang Tidak Ada (run.py)
description: Entry point container Docker di setting asal (run.py) padahal file run script aslinya gak pernah ada (harusnya main.py/start.py). Akibatnya image docker walau di build lolos "ijo", saat start langsung meledak ModuleNotFound.
claimed_location: Dockerfile baris 24
claimed_severity: MAJOR
source_section: TEMUAN #6 — MAJOR: Dockerfile Merujuk File yang Tidak Ada (run.py)
raw_quote: "Dockerfile baris terakhir menjalankan CMD [\"python\", \"run.py\"] namun file run.py tidak ada... crash langsung saat container distart"

---
finding_id: DEP-007
title: Dev Dependencies Sangat Jauh dari Latest (Outdated)
description: Deretan modul library penunjang environment (pytest, ruff, mypy, bandit) membusuk usang tertinggal sangat jauh (contoh mypy telat rilis 1 major version, ruff telat 14 patch minor) membuat testing berisiko tersandung bug-bug di versi lama tsb.
claimed_location: requirements-dev.txt
claimed_severity: MAJOR
source_section: TEMUAN #7 — MAJOR: Dev Dependencies Sangat Jauh dari Latest (Outdated)
raw_quote: "Semua dev dependencies dalam requirements-dev.txt sudah sangat tertinggal dari versi terbaru, beberapa dengan breaking changes di intermediate versions"

---
finding_id: DEP-008
title: Production Dependencies Tertinggal dari Latest
description: Modul utama tulang punggung aplikasi (yt-dlp, structlog, prometheus) dibiarkan usang. Terutama bahaya buat yt-dlp yang kalau telat patch Youtube API sebentar, akan fail fungsi utamanya gak mau muter/download musik youtube.
claimed_location: requirements.txt
claimed_severity: MAJOR
source_section: TEMUAN #8 — MAJOR: Production Dependencies Tertinggal dari Latest
raw_quote: "yt-dlp khusus: Ini adalah library yang paling sering butuh update. YouTube secara aktif memperbarui... kemungkinan besar ada format yang sudah tidak bisa diextract"

---
finding_id: DEP-009
title: Ruff Configuration Terlalu Banyak Rules yang Di-ignore
description: Pemindai gaya program (Linter Ruff) dikebiri habis-habisan memblok / mute paksa eror bahaya (bare except E722, unused var F841). Sehingga bug krusial yang harusnya di report malah dimatikan rules ignore-nya.
claimed_location: pyproject.toml seksi [tool.ruff.lint]
claimed_severity: MAJOR
source_section: TEMUAN #9 — MAJOR: Ruff Configuration — Terlalu Banyak Rules yang Di-ignore
raw_quote: "mengignore 9 Ruff rules penting... E722 (bare except)... F841 (unused variable)... menyembunyikan error, anti-pattern yang serius"

---
finding_id: DEP-010
title: Mypy Dikonfigurasi Terlalu Permissif
description: Pemindai kejelasan tipe (Mypy type check) dimatikan total semua fungsinya (ignoring, disallow=false, check_untyped=false). Alat mypy jadi formalitas buta ompong tak mendeteksi satupun anomali code (Type check useless).
claimed_location: pyproject.toml seksi [tool.mypy]
claimed_severity: MAJOR
source_section: TEMUAN #10 — MAJOR: Mypy Dikonfigurasi Terlalu Permissif
raw_quote: "Konfigurasi mypy hampir non-functional. Dengan semua option dimatikan... Type checking tidak memberikan nilai proteksi yang berarti"

---
finding_id: DEP-011
title: esbuild Hanya di devDependencies tapi Dibutuhkan untuk Build
description: Library pembuat bundel JS (esbuild) ditaruh di kategori "Dev-Only", namun script build produksi wajib membutuhkannya. Saat production rilis menarik paket dependensi non-dev, esbuild tidak ikut masuk, build UI js production dipastikan lumpuh.
claimed_location: package.json
claimed_severity: MINOR
source_section: TEMUAN #11 — MINOR: esbuild Hanya di devDependencies tapi Dibutuhkan untuk Build
raw_quote: "esbuild ada di devDependencies... npm run build adalah bagian dari deployment pipeline. Jika ada sistem yang menginstall hanya --production... build akan gagal."

---
finding_id: DEP-012
title: syncedlyrics 1.0.1 Potensi Breaking API
description: Plugin pemetik lirik nyangkut di 1.0.1. Modul ini ngandelin scraping web ketiga. Kalau web ketiga (e.g musixmatch) ngubah api nya seiprit, scraper lirik bakalan mati senyap karena tak punya status fallback fail yang terekam monitoring.
claimed_location: requirements.txt, plugins/lyrics.py
claimed_severity: MINOR
source_section: TEMUAN #12 — MINOR: syncedlyrics 1.0.1 — Potensi Breaking API
raw_quote: "Provider-provider ini sering mengubah API mereka... jika gagal, lyrics tidak tersedia — namun saat ini tidak ada monitoring untuk kasus ini."

---
finding_id: DEP-013
title: Bandit Mengskip Rules Keamanan Penting
description: Security linter Bandit dimatikan pemindai /tmp (B108). Membiasakan taruh folder temp ke hardcode absolut (/tmp) di os linux rawan serangan racun symlink jika sistem berjenis multi-user, karena hacker user sebelah dapat menumpuk folder palsu pakai nama yg sama.
claimed_location: pyproject.toml
claimed_severity: MINOR
source_section: TEMUAN #13 — MINOR: Bandit Mengskip Rules Keamanan Penting
raw_quote: "Bandit dikonfigurasi untuk skip 3 rules... B108 (hardcoded /tmp path): Path /tmp rentan terhadap symlink attacks dan race conditions di multi-user environment"

---
finding_id: DEP-014
title: CI Pipeline Menginstall requirements.txt di Ubuntu tapi Tidak di Windows
description: CI build runner untuk test_windows tidak mengeksekusi pytest usai menginstall requirement. CI hanya melakukan test command gampang cmd.exe /c start.bat doang. Membiarkan segala bug konektor windows aiohttp lolos ga ada yang ngetes.
claimed_location: .github/workflows/ci.yml
claimed_severity: MINOR
source_section: TEMUAN #14 — MINOR: CI Pipeline Menginstall requirements.txt di Ubuntu tapi Tidak di Windows
raw_quote: "CI job test-windows menginstall dependencies... namun tidak menjalankan test suite, hanya mengtest start.bat syntax... Bug spesifik Windows... tidak akan terdeteksi."


Total temuan diekstrak dari DOKUMEN 14 — Maintainability Audit: 19


---
finding_id: MAINT-R-01
title: log_config.py adalah God Object yang Melanggar SRP
description: File konfigurator log menggendong 7 tanggung jawab raksasa yang tidak nyambung sekaligus (ANSI colour, global state, CLI status bar, Spinner context, semantic log rewriter). File ini sangat padat, ruwet (477 baris), dan susah untuk dibaca ataupun diubah fungsinya (God Object).
claimed_location: core/log_config.py
claimed_severity: MAJOR
source_section: R-01 — log_config.py adalah God Object yang Melanggar SRP
raw_quote: "File ini menggabungkan 7 tanggung jawab yang tidak terkait dalam satu modul... File 477 baris ini adalah yang paling sulit dipahami"

---
finding_id: MAINT-R-02
title: start.py Berisi Dua Program yang Tidak Berhubungan
description: Script startup (start.py) adalah tong sampah raksasa menjejalkan GUI Manager Tkinter + Headless CLI + Port Scanner secara tumpang-tindih di file 866 baris, membuatnya sama sekali tak bisa dites otomatis unit test.
claimed_location: start.py
claimed_severity: MAJOR
source_section: R-02 — start.py Berisi Dua Program yang Tidak Berhubungan
raw_quote: "start.py adalah file terbesar dalam project dan menggabungkan: GUI Tkinter... Headless CLI... Dependency checker... Process manager..."

---
finding_id: MAINT-R-03
title: mpv_controller.py import time di Akhir File
description: Panggilan library internal "import time" malah tertinggal nyelip berantakan di ujung bawah file (baris 300) gara-gara sisa artefak copy-paste. Keluar dari area top-level class.
claimed_location: engine/mpv_controller.py baris 300
claimed_severity: MINOR
source_section: R-03 — mpv_controller.py: import time di Akhir File
raw_quote: "import time   # ← BARIS TERAKHIR FILE, di luar semua class... Ini adalah artifact dari copy-paste atau refactor yang tidak selesai."

---
finding_id: MAINT-N-01
title: Penamaan Logger Tidak Konsisten logger vs _log
description: Standar konvensi variabel pemanggil logger secara global menggunakan nama "logger" (di 29 file), tiba-tiba terpelanting jadi nama aneh "_log" secara khusus di file radio_engine.py doang. Membingungkan jika ini private atau public convention.
claimed_location: engine/radio_engine.py
claimed_severity: MINOR
source_section: N-01 — Penamaan Logger Tidak Konsisten: logger vs _log
raw_quote: "29 file menggunakan ini: logger = ... satu-satunya yang pakai _log: _log = ... Jika _log dimaksudkan sebagai \"private\" maka inconsistent"

---
finding_id: MAINT-N-02
title: Branding Inkonsisten bagas.fm vs LunaWave vs ytgui
description: Penamaan project aplikasi pecah terbelah identitasnya bercampur aduk antara sebutan lama (bagas.fm dan ytgui) dan sebutan resmi baru (LunaWave). Membingungkan buat pengguna UI baru dan pencarian regex string developer.
claimed_location: start.py, pyproject.toml, package-lock.json, notifications.py
claimed_severity: MAJOR
source_section: N-02 — Branding Inkonsisten: bagas.fm vs LunaWave vs ytgui
raw_quote: "Project memiliki setidaknya 3 nama berbeda yang digunakan secara bersamaan... start.py docstring: bagas.fm ... pyproject.toml: ytgui"

---
finding_id: MAINT-N-03
title: Environment Variable Naming Tidak Konsisten
description: Prefix prefiks nama variabel rute environment tak senada, berhamburan 3 gaya format pemanggilan variabel dalam satu atap server: LUNAWAVE_ vs YT_PLAYER_ vs non-prefix. Memusingkan operator deployment setup.
claimed_location: config.py, engine/mpv_controller.py
claimed_severity: MINOR
source_section: N-03 — Environment Variable Naming Tidak Konsisten
raw_quote: "Tiga prefix untuk satu aplikasi: LUNAWAVE_, YT_PLAYER_, dan tanpa prefix."

---
finding_id: MAINT-A-01
title: Repository Pattern Dilanggar di Tiga Layer Berbeda
description: Konsep abstraksi database (Ports/Repository) dilangkahi secara kasar. Jalur service seperti discover_service bypass layer menembus keras langsung menulis syntax SQL query pakai raw db.conn. Jika db diganti/dirubah tabelnya, developer perlu membongkar seluruh sistem.
claimed_location: server/services/discover_service.py, server/handlers/ws/discover_handlers.py, server/handlers/http.py
claimed_severity: CRITICAL
source_section: A-01 — Repository Pattern Dilanggar di Tiga Layer Berbeda
raw_quote: "melewati layer repository dan langsung mengakses db.conn... WS handler langsung SQL... Jika database engine diganti... perubahan harus dilakukan di banyak tempat"

---
finding_id: MAINT-A-02
title: STATS dari log_config Dipakai sebagai Shared Mutable State
description: Parameter state perhitungan metrik stat logger diculik dan dijadikan state wadah mutasi berbagi (shared object) secara langsung oleh modul engine playback di backend. Mengakibatkan pelanggaran dependency inversion berat (logic merubah UI presentasi).
claimed_location: engine/playback/controller.py, server/handlers/websocket.py, dkk
claimed_severity: MAJOR
source_section: A-02 — STATS dari log_config Dipakai sebagai Shared Mutable State
raw_quote: "STATS adalah objek dari layer logging yang diimport dan dimutasi dari layer engine dan server... Ini adalah dependency inversion violation"

---
finding_id: MAINT-A-03
title: WS Handler Signature Memiliki 7 Parameter Primitif (Primitive Obsession)
description: Tiap bongkahan 26 fungsi Websocket terjangkit penyakit duplikasi primitive parameter. Meng-copy paste urutan argumen parameter 7 fungsi bawaan kemana-mana. Repot manakala jika satu butuh module tambahan event_bus, seluruh 26 file harus diotak-atik semua.
claimed_location: Semua 26 WS handler di server/handlers/ws/
claimed_severity: MAJOR
source_section: A-03 — WS Handler Signature Memiliki 7 Parameter Primitif (Primitive Obsession)
raw_quote: "Setiap WS handler memiliki signature yang sama persis dengan 7 parameter loose... Handler yang hanya butuh command_bus terpaksa menerima ytdlp, state, manager, db yang tidak digunakan"

---
finding_id: MAINT-A-04
title: bootstrap.py Import di dalam Function Body (Anti-pattern)
description: Tata letak pengimporan modul memanggil dari perut di dalam fungsi, bukan dideklarasi top-level. Mematikan static analizer pembaca autocomplete dan menyamarkan penyakit circular loop error tersembunyi.
claimed_location: core/bootstrap.py
claimed_severity: MINOR
source_section: A-04 — bootstrap.py: Import di dalam Function Body (Anti-pattern)
raw_quote: "Import di dalam function body menghambat static analysis, menghilangkan IDE autocomplete, dan menyembunyikan circular import"

---
finding_id: MAINT-C-01
title: AppState Digunakan sebagai Global Mutable Bag (119 akses)
description: Variabel AppState dijadikan keranjang sampah raksasa global tempat sembarang modul melempar baca dan tulis modifikasi dari 119 titik lokasi kode yang tak peduli hak milik state tersebut (ownership loss). Memicu malapetaka Race condition.
claimed_location: engine/radio_engine.py, engine/playback/controller.py, dkk
claimed_severity: CRITICAL
source_section: C-01 — AppState Digunakan sebagai Global Mutable Bag (119 akses)
raw_quote: "diakses langsung (state.xxx = yyy) dari 119 lokasi di seluruh engine. Ini menciptakan tight coupling di mana setiap modul... bisa mengubah apapun kapan saja"

---
finding_id: MAINT-C-02
title: DiscoverService Tightly Coupled ke Database Concrete Class
description: Servis discover mengikat kelas objek konkret database secara keras/solid (tight-coupled). Memutus fleksibilitas antarmuka (Port) dan memaksa pengujian module ini butuh running real file database utuh (susah untuk unit test mocking).
claimed_location: server/services/discover_service.py
claimed_severity: MINOR
source_section: C-02 — DiscoverService Tightly Coupled ke Database Concrete Class
raw_quote: "mengimport concrete Database class. Testing membutuhkan database nyata."

---
finding_id: MAINT-C-03
title: STATIC_DIR Didefinisikan Dua Kali dengan Path Berbeda
description: Penentuan penunjuk jalan letak folder halaman html (/web/static) dideklarasikan dobel di dua file lewat jalur turunan kalkulasi string parent yang beda. Rapuh banget, geser letak file 1x maka akan macet 404 pathing web-nya (path rusak).
claimed_location: server/handlers/http.py baris 15, server/app.py baris 14
claimed_severity: MINOR
source_section: C-03 — STATIC_DIR Didefinisikan Dua Kali dengan Path Berbeda
raw_quote: "Kedua path menghasilkan direktori yang sama secara hasil, tetapi cara penghitungannya berbeda... Ini rapuh: jika salah satu file dipindah, satu path akan rusak."

---
finding_id: MAINT-C-04
title: build_app_context() Memiliki 28 Import dan Membangun Semua Dependency Secara Manual
description: Script inisiator peluncur awal app memikul fungsi Manual Dependency Injection, memaksa pemanggilan 28 jenis import class yang panjang tak terawat di satu function build_app_context(). (sangat fragile untuk maintain modul).
claimed_location: core/bootstrap.py
claimed_severity: MAJOR
source_section: C-04 — build_app_context() Memiliki 28 Import dan Membangun Semua Dependency Secara Manual
raw_quote: "bootstrap.py import dari 28 modul dan secara manual merangkai semua dependency. Ini adalah manual DI container yang fragile"

---
finding_id: MAINT-CO-01
title: discover_service.py Mengandung SQL Duplikat dengan track_repository.py
description: Duplikasi query SQL telanjang bergelimpangan ngawur ngulangi tugas yang persis dengan yang ada pada penampung modul repository track (SELECT video_id, title... FROM tracks). Kalau tabel berubah harus dirubah sinkron di banyak tempat atau program fail.
claimed_location: server/services/discover_service.py vs cache/repositories/track_repository.py
claimed_severity: MAJOR
source_section: CO-01 — discover_service.py Mengandung SQL Duplikat dengan track_repository.py
raw_quote: "DiscoverService memiliki 5 SQL query yang hampir identik dengan yang ada di TrackRepository... Jika kolom tracks ditambahkan, harus update di dua tempat."

---
finding_id: MAINT-CO-02
title: DependencyChecker di start.py Mengecek opentelemetry yang Tidak Ada di Requirements
description: Skrip check di launcher keliru memancing pendeteksian nama modul "opentelemetry" yang sama sekali tak terinstal via requirements dan tak pernah dipakai, melahirkan validasi palsu false negative eror (bilang dependensi lu kurang terus/hilang).
claimed_location: start.py baris 51
claimed_severity: MAJOR
source_section: CO-02 — DependencyChecker di start.py Mengecek opentelemetry yang Tidak Ada di Requirements
raw_quote: "opentelemetry tidak terdaftar di requirements.txt... Checker akan selalu melaporkan dependency ini sebagai \"missing\""

---
finding_id: MAINT-TD-01
title: 12 PATCH Comment Terdokumentasi Belum Direfactor
description: Meninggalkan artefak barisan riwayat perbaikan debug sprint lawas berupa komen (contoh: # CRITICAL-03, # PATCH-YTDLP) di kode produksi berjalan (production code). Menjadikan dokumen source script tidak rapi berbalut sampah dokumentasi historis internal.
claimed_location: config.py, engine/mpv_controller.py, engine/radio_engine.py
claimed_severity: MAJOR
source_section: TD-01 — 12 PATCH Comment Terdokumentasi Belum Direfactor
raw_quote: "komentar audit internal yang masih ada di production code, menandai fix yang sudah diterapkan namun belum di-refactor dengan benar... memberi kesan kode belum siap."

---
finding_id: MAINT-TD-02
title: 16 type ignore Menandai Masalah Typing yang Belum Diselesaikan
description: Penambal bypass tutup mata terhadap warning hint tipe (type: ignore) berhamburan hingga 16 baris akibat akses nakal yang melangkahi parameter abstract port class, menandakan sistem tipe arsitektur port tidak beres (Type Check Mypy error suppressed).
claimed_location: discover_service.py, mpv_controller.py
claimed_severity: MINOR
source_section: TD-02 — 16 # type: ignore Menandai Masalah Typing yang Belum Diselesaikan
raw_quote: "type: ignore pada db.conn access terjadi karena akses langsung ke concrete attribute yang tidak ada di Port interface"

---
finding_id: MAINT-TD-03
title: asyncio Diimport Dua Kali di websocket.py
description: Kelalaian sepele menyisakan panggilan sisa dobel library asyncio masuk 2x (satu di atas top, satu nyelip di method bawah). Sisaan hasil kegagalan bersih-bersih refactoring.
claimed_location: server/handlers/websocket.py
claimed_severity: MINOR
source_section: TD-03 — asyncio Diimport Dua Kali di websocket.py
raw_quote: "import asyncio   # baris 52 — DUPLIKAT di dalam method!... Import duplikat di dalam method adalah artifact dari refactor yang tidak bersih."



---

Total Seluruh Temuan dari Semua Dokumen: 317
