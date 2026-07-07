---
master_id: M-001
title: AppState adalah mutable shared state global
description: Objek AppState yang termutasi via WebSocket dijalankan dari banyak thread coroutine, namun eksekusi modifikasi data list-nya (queue, lirik) tidak sepenuhnya terkunci dalam _lock. Python GIL tak cukup untuk proteksi tingkat asinkron dan ini memicu kemungkinan korupsi daftar. AppState menyatukan player state, UI state, download state, dan network state menjadi satu struct yang tidak modular. Kelas lain harus memuat keseluruhan state hanya untuk membaca sebagian state spesifik. AppState digunakan sebagai mutable shared state global tanpa mekanisme concurrency protection. Hal ini memungkinkan siapa pun memutasi state secara langsung tanpa lock. Handler mem-bypass event bus mutasi saat mengubah kondisi favorite pada variabel lagu, mencemari status dan menghindari arsitektur asinkron yang telah ada. Variabel AppState dijadikan keranjang sampah raksasa global tempat sembarang modul melempar baca dan tulis modifikasi dari 119 titik lokasi kode yang tak peduli hak milik state tersebut (ownership loss). Memicu malapetaka Race condition.
claimed_location: core/state.py, engine/playback/queue_commands.py, engine/radio_engine.py, engine/playback/controller.py, dkk, server/handlers/ws/discover_handlers.py, core/state.py
claimed_severity: CRITICAL
source_findings: [EXEC-001, ARCH-A07, MAINT-C-01, CS-016, CS-002]

---
master_id: M-002
title: Database.__getattr__ proxy magic
description: Pendefinisian awal parameter instance = None untuk variabel repository saat pemanggilan __init__ di class Database, alih-alih melempar delegasi parameter asli, membuat statis pointer tak bisa dilacak dan terlihat kosong. Penggunaan magic proxy pada Database.__getattr__ membuat API menjadi tidak jelas dan menyulitkan proses mocking saat testing. Pengkabelan virtual instance method lewat getattr ke sub-modul repository membuat trace log samar dan menyebabkan ambigu penimpaan namespace antar file di dalam class Database. Rute jembatan call __getattr__ ke SQLite disematkan celah murni yang gagal menahan call panggilan API (get_track dll) sesaat saat object belum menyelesaikan init-nya, yang menyemburkan rentetan attribute exception kosong yang membingungkan bagi developer lain (traceback buta). Magic attribute proxy __getattr__ merutekan pemanggilan method secara berurutan ke 3 repository berbeda yang jika terjadi kelalaian pemanggilan, AttributeError akan membingungkan developer. Sumber trace jadi buram.
claimed_location: cache/db.py (baris 84), cache/db.py, cache/db.py (__getattr__())
claimed_severity: HIGH
source_findings: [EXEC-002, ARCH-A11, DB-012, CS-020, REP-01]

---
master_id: M-003
title: config.py menjalankan side effects
description: File config.py menjalankan side effects saat proses import (seperti membuat direktori socket dan memvalidasi path), yang mana melanggar prinsip dasar modul Python. File konfigurasi langsung mengeksekusi operasi sistem operasi (mkdir socket dan file I/O). Pemanggilan fungsi ber-side-effect pada modul level top melanggar Clean Architecture dan akan memicu error di saat sistem import daripada saat runtime.
claimed_location: config.py, config.py (baris 10–16)
claimed_severity: HIGH
source_findings: [EXEC-003, ARCH-A09]

---
master_id: M-004
title: Import time di baris terakhir file mpv_controller.py
description: Panggilan library internal "import time" malah tertinggal nyelip berantakan di ujung bawah file (baris 300) gara-gara sisa artefak copy-paste. Keluar dari area top-level class. Pemanggilan modul time.monotonic() dilakukan di dalam method _handle_event namun import time diletakkan di baris paling terakhir dalam file tersebut. Ini memicu NameError jika dieksekusi sebelum modul berhasil diinisialisasi secara utuh. Penulisan modul import time dilempar pada baris paling bawah kode di luar class. Pemanggilan time.monotonic() di dalam fungsi membentur masalah pembacaan (NameError) saat interpreter tidak merunning penuh skripnya (parsial). File mpv_controller.py mengimport modul time di baris paling bawah file, bukan di bagian atas. Ini merupakan bug latent dan code smell yang serius.
claimed_location: mpv_controller.py, engine/mpv_controller.py (baris terakhir), engine/mpv_controller.py baris 300
claimed_severity: CRITICAL
source_findings: [EXEC-004, BUG-B06, BUG-02, MAINT-R-03]

---
master_id: M-005
title: http_session tidak diinjeksikan
description: aiohttp.ClientSession (http_session) dibuat di bootstrap.py namun tidak diinjeksikan ke server/app.py. Akibatnya, stream proxy di http.py akan diam-diam menginisialisasi None fallback.
claimed_location: bootstrap.py, server/app.py, http.py
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-005]

---
master_id: M-006
title: Zero security headers HTTP
description: Tidak terdapat HTTP security headers seperti Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security, atau Referrer-Policy di respons apa pun, membuka celah XSS, clickjacking, dan MIME sniffing.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_findings: [EXEC-006]

---
master_id: M-007
title: CORS wildcard pada endpoint audio
description: Konfigurasi CORS menggunakan wildcard (Access-Control-Allow-Origin: *) pada endpoint /api/stream/{id}, sehingga audio dapat di-embed oleh domain mana saja.
claimed_location: /api/stream/{id}
claimed_severity: Kritis
source_findings: [EXEC-007]

---
master_id: M-008
title: Tidak ada rotasi token session
description: Session token berukuran 16 bytes hex (128-bit) tidak melakukan rotasi pasca-privilege change dan tidak ada mekanisme invalidasi token pada saat logout. Token sesi memakai deret hex generik 16-bit (128 bits entropy) padahal saran standard menuntut sekurang-kurangnya 256 bits, dan token diamankan pada localStorage frontend dengan risiko serangan XSS yang leluasa menyalinnya. Token dilempar cuma-cuma dari endpoint ke layer cache berupa string telanjang. Gagal memvalidasi atau mencegah token yang direkayasa pada sistem.
claimed_location: server/handlers/auth.py (baris 58), web/static/js/ws.js (baris 24), server/handlers/auth.py, cache/repositories/auth_repository.py
claimed_severity: Kritis
source_findings: [EXEC-008, API-03, CS-024]

---
master_id: M-009
title: Logout tidak invalidasi session di server
description: Proses logout melalui JS hanya menghapus token dari localStorage, sedangkan token di database tetap valid hingga waktu kedaluwarsa habis (4 jam).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_findings: [EXEC-009]

---
master_id: M-010
title: X-Forwarded-For rentan di-spoof
description: Header X-Forwarded-For dapat dipalsukan untuk melewati rate limiting karena TRUSTED_PROXY=true dipercaya bulat tanpa memvalidasi jumlah header.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_findings: [EXEC-010]

---
master_id: M-011
title: Binary win32-x64 ter-commit ke repo
description: Folder monster node_modules lupa di-blacklis di gitignore. Menjadikan file sampah dependensi lokal masuk tercommit membebani repository. Hal paling fatal binari node_module milik arsitektur PC developer (e.g win-x64) akan menimpa produksi server linux OS, merusak run runtime app. Binary esbuild untuk Windows (Node modules win32-x64) dikomit ke dalam repository, menimbulkan supply chain risk dan memperbesar ukuran repo tanpa alasan yang perlu.
claimed_location: .gitignore
claimed_severity: Kritis
source_findings: [EXEC-011, DEP-002]

---
master_id: M-012
title: Nilai MAX_VOLUME melebihi batas
description: Handler websocket membatasi maksimal volume_set sebesar 150 sementara class Volume() mem-clamp batas asli secara paksa jadi 100. Hal ini menyebabkan inkonsistensi input. Batasan toleransi maksmimal pengaturan volume audio menabrak bentrokan nilai ganda (100 dan 150) yang tidak bersinergi dengan konstanta MAX_VOLUME di constants.py, menimbulkan bug logika inkonsisten pada interaksi pengaturan level di WS handler dengan VolumeService. Konstanta MAX_VOLUME di-set menjadi 150 di constants.py, nilai yang melebihi 100% ini berpotensi merusak hardware audio. Variabel MAX_VOLUME memiliki batas berlebih 150 sementara casting value strictnya selalu turun (clamp) di batas limit 100. Hal ini menyebabkan error representatif pada AppState.volume atau bahkan bug perulangan render MPV.
claimed_location: constants.py, server/handlers/ws/settings_handlers.py (baris 20), core/constants.py, core/value_objects.py, engine/volume_service.py L23, server/handlers/ws/settings_handlers.py L20, core/constants.py L4
claimed_severity: Kritis
source_findings: [EXEC-012, BUG-B20, CS-025, BL-02]

---
master_id: M-013
title: Memory leak pada _stream_rate_limit
description: Variabel _stream_rate_limit (defaultdict) bertambah tanpa batas karena tidak ada pembersihan (pruning) untuk data usang, menyebabkan memory leak saat traffic tinggi. Perlu ada proses pruning ke dalam _stream_rate_limit agar tidak menyebabkan kebocoran memori (disamakan polanya dengan auth.py). Key IP Address penanda trafik stream dari _stream_rate_limit akan tetap tersimpan meski timestamp-nya sudah dieliminasi, menguras RAM berangsur-angsur apabila pengunjung/konektor berganti IP tanpa batas. Variabel array penyimpan alamat IP pelacak request tidak dilengkapi modul fungsi sampah (garbage collector). Akibatnya dictionary Python level ini menyedot memori ram tak terbatas terus menyimpan IP tanpa pernah meng-clear data IP basi (leak murni).
claimed_location: http.py, server/handlers/http.py, server/handlers/http.py (baris 16–20), server/handlers/http.py (L17, L57-62)
claimed_severity: Blocker / Kritis
source_findings: [EXEC-013, EXEC-039, PERF-P14, EXC-03]

---
master_id: M-014
title: syncBrowserAudio dipanggil setiap tick
description: Fungsi syncBrowserAudio() dijalankan di setiap tick progress (sekitar 333ms) dari handler WS message "progress", membebani evaluasi di browser secara berulang-ulang.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-014]

---
master_id: M-015
title: Fake beat loop berjalan terus menerus
description: Loop efek kelap-kelip cahaya (glow) dieksekusi setTimeout() yang gagal termatikan secara sistem disaat viewport page tertutup, dan mengabaikan mode perlindungan (prefers-reduced-motion) dari penyandang disabilitas syaraf visual. Fake beat loop menggunakan requestAnimationFrame terus berjalan walau tidak ada perubahan visual yang dibutuhkan, membuang sumber daya CPU khususnya di perangkat mobile.
claimed_location: web/static/js/audio.js
claimed_severity: MEDIUM
source_findings: [EXEC-015, FE-018]

---
master_id: M-016
title: Broadcast state penuh setiap event
description: Panggilan penyiaran progress time timer durasi (tick per sekon) memaksa konversi struktur daftar antrean list JSON data-size masif yang membanjiri perlintasan bandwidth, lantaran aplikasi tak mengadopsi mekanisme update bertahap parsial. Sistem mem-broadcast seluruh state aplikasi (antrean, lirik, dll) pada tiap event kecil karena tidak terdapat mekanisme pengiriman data yang hanya berubah (delta/diff). Mengubah status 'favorite' satu trek memaksa router meneruskan status seluruh objek (termasuk queue dan lirik) ke semua klien tersambung. Overhead pengiriman ini dapat menunda koneksi 5-100ms per trigger akibat payload yang tak perlu.
claimed_location: server/handlers/ws/discover_handlers.py (baris 81–88), server/handlers/event_listeners.py, server/services/broadcast_service.py
claimed_severity: CRITICAL
source_findings: [EXEC-016, PERF-P02, SVC-02]

---
master_id: M-017
title: Single-threaded aiohttp tanpa worker pool
description: Aiohttp berjalan single-threaded tanpa worker pool, sehingga request lambat dari yt-dlp dapat menghalangi progress broadcast ke semua client.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-017]

---
master_id: M-018
title: Lyrics sync double requestAnimationFrame
description: Pemanggilan fungsi lirik menjalankan requestAnimationFrame(() => syncLocalLyrics()) pada setiap tik progress, menghasilkan double RAF setiap detiknya.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-018]

---
master_id: M-019
title: Penamaan bilingual tidak konsisten
description: Terdapat penamaan variabel secara bilingual (Indonesia/Inggris) dalam file yang sama (misal nama, judul vs title, artist).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-019]

---
master_id: M-020
title: bundle.js adalah file monolitik
description: Bundle hasil deploy tidak disusutkan, padahal instruksi scriptnya seakan meminta minification. Ini berdampak besar jika cache rusak karena bobot unduh akan melonjak. bundle.js berukuran sangat besar (2.649 baris, 104KB) dan di-generate tanpa source map, sangat menyulitkan debugging di level production.
claimed_location: bundle.js, web/static/js/bundle.js, package.json
claimed_severity: MEDIUM
source_findings: [EXEC-020, PERF-P10]

---
master_id: M-021
title: Log message campur dua bahasa
description: Pesan log tidak konsisten dalam penggunaan bahasa, mencampur pesan bahasa Indonesia ("Memulai download") dengan bahasa Inggris ("Download complete").
claimed_location: TIDAK DISEBUTKAN
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-021]

---
master_id: M-022
title: Tidak ada CHANGELOG.md aktif
description: Tidak ada file CHANGELOG.md di root yang men-tracking version production (hanya tersedia di archive/).
claimed_location: archive/
claimed_severity: TIDAK DISEBUTKAN
source_findings: [EXEC-022]

---
master_id: M-023
title: Konflik versi aiosqlite
description: Terdapat konflik dependensi yang fatal untuk aiosqlite antara requirements.txt dan pyproject.toml yang perlu diselaraskan (gunakan 0.22.1). Indikator versi spesifik aiosqlite tidak nyambung (bentrok) di dua titik (req.txt 0.20 dan pyproject 0.22). Jika developer menggunakan satu dan build docker menggunakan lainnya, bug siluman yang hanya ada di py 0.20 akan menghantui satu sisi environment namun lenyap di sisi satunya. Terdapat version conflict antara pyproject.toml (aiosqlite==0.22.1) dan requirements.txt (aiosqlite==0.20.0), yang bisa memunculkan environment berbeda tergantung dari installer yang dipakai. Modul requirements.txt (aiosqlite==0.20.0) dan pyproject.toml (aiosqlite==0.22.1) tidak berada pada sinkronisasi versi yang sama. Developer yang memakai rujukan beda berisiko men-deploy library out-of-sync dan memicu incompatibility API.
claimed_location: pyproject.toml, requirements.txt, requirements.txt, pyproject.toml, requirements.txt (baris 2), pyproject.toml (baris 8), requirements.txt baris 2, pyproject.toml baris 8
claimed_severity: Blocker / Kritis
source_findings: [EXEC-023, EXEC-038, ARCH-A05, DEP-001]

---
master_id: M-024
title: Sangat sedikit test functions
description: Kumpulan unit test inspeksi mem-parsing isi raw source code fungsi melacak kata string (inspect.getsource) alih-alih me-run fungsinya. Menjadikan file pengujian buta terhadap kebenaran logika berjalan, dan cuma mendeteksi keberadaan kode saja. Dari 21 file test, hanya terdapat 17 fungsi test. Banyak file test yang hampir kosong atau memiliki rata-rata di bawah 1 test per file.
claimed_location: tests/unit/engine/test_queue_locking.py, tests/unit/engine/test_radio.py, tests/unit/cache/test_resolver.py, tests/unit/server/test_security.py, tests/unit/server/test_ws_broadcast.py, tests/unit/plugins/test_lyrics_parser.py
claimed_severity: Kritis
source_findings: [EXEC-024, AUDIT-TEST-001]

---
master_id: M-025
title: Coverage threshold sangat rendah
description: CI hanya mematok coverage threshold di angka 40%, jauh dari standar industri untuk rilis produksi (70–80%).
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_findings: [EXEC-025]

---
master_id: M-026
title: Tidak ada integration test nyata
description: Test module case integrasi perlindungan keamanan IP ditulis melompong nihil tanpa diakhiri satupun baris asserstion, menghasilkan pass-lulus otomatis bodoh selamanya untuk kondisi test cacat. Tidak terdapat test integrasi nyata; test_e2e.py dan test_fase1.py tidak memicu request HTTP/WS secara riil.
claimed_location: test_e2e.py, test_fase1.py, tests/integration/test_fase1.py, baris ~54–77
claimed_severity: Kritis
source_findings: [EXEC-026, AUDIT-TEST-002]

---
master_id: M-027
title: Alur kritis tidak di-test
description: Ribuan baris kode rute masuk lalu-lintas event websocket (antre, set volume, play dll) belum dibuat mock case simulasi satupun. Menimbulkan kecacatan sinkronisasi state dari command UI klien luput tidak dihandle. Otak inti penggerak dan controller engine audio (MPV) sama sekali hampa tidak pernah dimasukkan ke satupun skema tes skenario berjalan. Kondisi rawannya logika IPC loop, reconnect, atau play-stop menjadi buta. Rute masuk dan keluar klien pada server otentikasi kunci utama sistem password login tidak diproteksi uji tes case apapun. Menutupi potensi eksploit brutal token (brute force) atau cookie hijacking. Interval limit batas kedaluwarsa waktu string tautan media media belum ditelusuri logic timing test-nya, sebatas parsing konstanta hardcode file, menutupi celah link basi (expired ttl timeout limit). Alur sangat penting seperti login/logout, rate limiting, stream proxy, radio mode, download manager, dan event listeners belum mempunyai test sama sekali. Blok pemotong iklan (SponsorBlock) yang menyerap segmen array timestamp tidak disandingkan test verifikator pemanggilan skip pada posisi sekon time video. Beresiko loop skip memutar terus atau gagal skip. Modul jembatan pembentuk perintah call ke library yt-dlp pencari video sama sekali tidak di-stub/di-mock via unit testing, meloloskan handling error fatal jaringan atau manipulasi data API mentah tak diketahui sistem. Konsep perputaran antrean pintar mesin radio seperti fetch track acak, exclude, rotate array tidak tersentuh testing behavioral, hanya mengandalkan inspeksi parse source code yang tak berguna memverifikasi fungsinya.
claimed_location: engine/mpv_controller.py, server/handlers/auth.py, engine/ytdlp_client.py, engine/radio_engine.py, cache/resolver.py, server/handlers/ws/, plugins/sponsorblock.py
claimed_severity: Kritis
source_findings: [EXEC-027, AUDIT-TEST-003, AUDIT-TEST-004, AUDIT-TEST-005, AUDIT-TEST-006, AUDIT-TEST-007, AUDIT-TEST-008, AUDIT-TEST-009]

---
master_id: M-028
title: Konfigurasi Mypy teramat longgar
description: Type checker Mypy dikonfigurasi terlalu bebas (check_untyped_defs = false, disallow_untyped_defs = false), membuatnya hampir dinonaktifkan. Pemindai kejelasan tipe (Mypy type check) dimatikan total semua fungsinya (ignoring, disallow=false, check_untyped=false). Alat mypy jadi formalitas buta ompong tak mendeteksi satupun anomali code (Type check useless).
claimed_location: pyproject.toml seksi [tool.mypy]
claimed_severity: Kritis
source_findings: [EXEC-028, DEP-010]

---
master_id: M-029
title: Ruff mengabaikan aturan penting
description: Linter Ruff mengabaikan rule esensial seperti E722 (bare except), F841 (unused variable), dan I001 (import sorting), menjadikan linting tidak efektif. Pemindai gaya program (Linter Ruff) dikebiri habis-habisan memblok / mute paksa eror bahaya (bare except E722, unused var F841). Sehingga bug krusial yang harusnya di report malah dimatikan rules ignore-nya.
claimed_location: pyproject.toml seksi [tool.ruff.lint]
claimed_severity: Kritis
source_findings: [EXEC-029, DEP-009]

---
master_id: M-030
title: Tidak ada performance/load test
description: Aplikasi belum melalui pengujian performa atau load test.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Kritis
source_findings: [EXEC-030]

---
master_id: M-031
title: AppState hanya di in-memory
description: Semua state aplikasi di dalam AppState cuma disimpan in-memory; proses restart berarti kehilangan keseluruhan state playback. Rangkaian data playlist dimemori cuma di injeksi menumpang di variable instance objek lokal. Mengakibatkan pengguna LunaWave nangis gigit jari daftar 50 lagu impiannya menghilang ketiup angin saat program Python ini terpaksa direstart / server shut-down.
claimed_location: core/state.py
claimed_severity: Fundamental
source_findings: [EXEC-031, QUE-03]

---
master_id: M-032
title: SQLite hanya single instance
description: Aplikasi menggunakan single SQLite instance dengan satu koneksi, yang menghalangi kemampuannya untuk divaluasi secara horizontal (scale out). Seluruh aktivitas database (read dan write) dibebankan pada satu pool aiosqlite, menyebabkan seluruh eksekusi coroutine harus antre sekuensial. Saat workload tinggi, bisa mengunci seluruh jalannya aplikasi secara paralel.
claimed_location: cache/db.py
claimed_severity: CRITICAL
source_findings: [EXEC-032, DB-001]

---
master_id: M-033
title: ConnectionManager berupa list tanpa batas
description: Penyimpanan client id pada dictionary array dikerjakan sekenanya, di mana pembagian pengulangan list disaat event disconnect beririsan bisa menimbulkan array size change error karena iterator membaca (snapshot) isi yang sama sewaktu iterasi async loop. ConnectionManager.active_connections menggunakan list standar tanpa batas, sehingga tak ada perlindungan terhadap serangan connection flood. Struktur data tracking konektor terpusat disimpan pada native List object di Python sehingga pencabutan dan scan entitas client membutuhkan komputasi linear. Rentan menyebabkan overhead O(n).
claimed_location: server/handlers/websocket.py (baris 25, 40–41), server/handlers/websocket.py (ConnectionManager)
claimed_severity: Fundamental
source_findings: [EXEC-033, PERF-P07, CC-02]

---
master_id: M-034
title: Tidak memiliki sistem queue/job
description: Download dijalankan langsung secara paralel di event loop tanpa ada sistem queue atau backpressure untuk membatasinya.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_findings: [EXEC-034]

---
master_id: M-035
title: Tidak ada lapisan cache (Redis/Memcached)
description: Karena hilangnya layer cache, setiap request discover harus selalu membuka sambungan baru ke database SQLite.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_findings: [EXEC-035]

---
master_id: M-036
title: Rate limit state tersimpan di in-memory
description: Keamanan dari brute-force rawan di-reset karena state rate limiting tersimpan di memory, yang berarti me-restart server akan menghilangkan semua batas tersebut.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: Fundamental
source_findings: [EXEC-036]

---
master_id: M-037
title: File run.py tidak ada (Blocker Deployment)
description: Entry point container Docker diarahkan ke "run.py", sedangkan struktur repository mengharuskan eksekusi pada "main.py". Hal ini membuat Docker tak bisa start karena FileNotFoundError. File run.py absen dari kode sumber, mengakibatkan Dockerfile mengalami crash saat mengeksekusi container. Entry point container Docker di setting asal (run.py) padahal file run script aslinya gak pernah ada (harusnya main.py/start.py). Akibatnya image docker walau di build lolos "ijo", saat start langsung meledak ModuleNotFound.
claimed_location: run.py, Dockerfile, Dockerfile (baris 28), Dockerfile baris 24
claimed_severity: Blocker / Kritis
source_findings: [EXEC-037, ARCH-A02, DEP-006]

---
master_id: M-038
title: PWA manifest kurang ikon resolusi tinggi
description: File manifest PWA cuma punya ikon ukuran 1024x1024. Butuh ditambah ukuran 192x192 dan 512x512. Register konfigurasi pembentuk format aplikasi web (manifest.json) melompong dari penyertaan parameter varian resolusi. Hal ini me-nonaktifkan pengerjaan masking ukuran ikon yang dibutuhkan Chrome/iOS saat menyimpan ke beranda gawai.
claimed_location: web/static/manifest.json
claimed_severity: Sedang
source_findings: [EXEC-040, FE-019]

---
master_id: M-039
title: Variabel environment jadul di .env.example
description: File .env.example menggunakan variabel berawalan YTGUI_ yang lama, berbenturan dengan kenyataan aktual yang pakai LUNAWAVE_. Penamaan project aplikasi pecah terbelah identitasnya bercampur aduk antara sebutan lama (bagas.fm dan ytgui) dan sebutan resmi baru (LunaWave). Membingungkan buat pengguna UI baru dan pencarian regex string developer. Variabel pada frontend masih menyimpan legacy label "ytgui" berupa magic string, yang jika akan migrasi atau dihapus akan memakan refactor berat ke depan. Prefix prefiks nama variabel rute environment tak senada, berhamburan 3 gaya format pemanggilan variabel dalam satu atap server: LUNAWAVE_ vs YT_PLAYER_ vs non-prefix. Memusingkan operator deployment setup.
claimed_location: .env.example, web/static/js/ws.js, web/static/js/services/auth.js, start.py, pyproject.toml, package-lock.json, notifications.py, config.py, engine/mpv_controller.py
claimed_severity: MAJOR
source_findings: [EXEC-041, CS-011, MAINT-N-02, MAINT-N-03]

---
master_id: M-040
title: File HTML tidak relevan di direktori tests
description: Terdapat file test_helpers.html yang malah menempati folder tes (tests/).
claimed_location: tests/test_helpers.html
claimed_severity: Rendah
source_findings: [EXEC-042]

---
master_id: M-041
title: WebSocket di-expose ke global scope window
description: Front end membuka kerentanan atau masalah privasi state dengan mengekspos WebSocket via window.ws = ws ke global scope. File javascript dimuat ke dalam global name space HTML satu demi satu (classic scripts). Semua objek (store, ws, localAudio) dilempar bertumpuk menaikkan peluang collision, tak punya encapsulation, dan tak bisa dilakukan unit test.
claimed_location: web/static/js/*.js
claimed_severity: MEDIUM
source_findings: [EXEC-043, ARCH-A12]

---
master_id: M-042
title: discover_service KeyError: stream_url tidak di-SELECT
description: DiscoverService mengambil data dari database namun melupakan field stream_url dari query SELECT. Imbasnya, ketika sistem mencoba membuat instansi TrackInfo, terjadi KeyError yang membuat seluruh tab Discover crash dan tak dapat berfungsi. Kueri SQL tidak meminta kolom stream_url pada pemilihan data track, namun kode mengasumsikan keberadaannya pada variabel dictionary yang dilempar, memicu KeyError fatal yang mencrash fungsi tab Discover secara keseluruhan. SQL pada fungsi DiscoverService.get_recent(), get_favorites(), dan get_cached() tidak melakukan query pada kolom stream_url. Hal ini menyebabkan KeyError saat pembacaan dictionary, error tertelan, dan membuat tab Discover tampil kosong tanpa laporan error.
claimed_location: server/services/discover_service.py (baris 36, 63, 90), server/services/discover_service.py (get_recent() L36, get_favorites() L63, get_cached() L90)
claimed_severity: CRITICAL
source_findings: [BUG-B01, ARCH-A01, BUG-01]

---
master_id: M-043
title: handle_auth tidur di dalam global rl_lock — DoS seluruh autentikasi
description: Delay rate-limiting berupa asyncio.sleep(2) dijalankan di dalam manager.rl_lock. Akibatnya, satu attacker dengan percobaan gagal bisa menahan lock dan memblokir seluruh request autentikasi dari pengguna lain.
claimed_location: server/handlers/auth.py (baris 28–45)
claimed_severity: CRITICAL
source_findings: [BUG-B02]

---
master_id: M-044
title: _on_track_ended reason kosong "" tidak ditangani — autoplay mati
description: Default value string kosong pada TrackEndedEvent.reason tidak ditangani dalam statement kondisional fungsi _on_track_ended(). Jika reason bukan eof/stop/error, fungsi tersebut akan langsung return tanpa melakukan apapun dan autoplay mati diam-diam.
claimed_location: engine/playback/controller.py (baris 174–192), core/events.py
claimed_severity: CRITICAL
source_findings: [BUG-B03]

---
master_id: M-045
title: play_track retry backoff membaca _retry_count stale
description: Variabel self._retry_count dibaca di luar blok _play_lock yang mana nilainya bisa berubah akibat intervensi eksekusi fungsi lain di sela-sela pembebasan lock tersebut, mengakibatkan nilai sleep(backoff) yang tidak terprediksi. Formula hitung limit hitback retry dijalankan dari titik poin blok setelah proses di luar lock mutex terputus-sambung dengan coroutine lain, mengijinkan pembacaan iterasi (retry count) menyadur nilai kusam (stale) dan men-trigger skip lompat error.
claimed_location: engine/playback/controller.py (baris 139–150), engine/playback/controller.py (play_track() L146-150)
claimed_severity: CRITICAL
source_findings: [BUG-B04, CC-03]

---
master_id: M-046
title: _on_track_ended error path: guard if IDLE tidak pernah terpenuhi
description: Pada kondisi error, state diatur ke PlayerStatus.ERROR sebelum sleep 2 detik. Guard 'if self.state.status == PlayerStatus.IDLE:' tidak akan pernah terpenuhi karena status saat itu adalah ERROR, mengakibatkan perpindahan track tak terhindarkan meski diputus manual oleh user.
claimed_location: engine/playback/controller.py (baris 186–192)
claimed_severity: CRITICAL
source_findings: [BUG-B05]

---
master_id: M-047
title: _lock di PlaybackController dideklarasikan tapi tidak digunakan
description: PlaybackController memiliki self._lock = asyncio.Lock() namun tidak pernah memanggil lock tersebut pada operasinya secara internal, sehingga subscriber event tetap memutasi state tanpa lock, menimbulkan false sense of security.
claimed_location: engine/playback/controller.py (baris 59)
claimed_severity: HIGH
source_findings: [BUG-B07]

---
master_id: M-048
title: on_next memicu bottleneck beruntun karena hold _lock
description: on_next memegang lock sambil mengeksekusi _advance_to_next() -> play_track(). Hal ini menyebabkab semua operasi I/O dan jaringan panjang terperangkap di dalam satu lock secara sekuensial, menghentikan seluruh antrean operasi lain.
claimed_location: engine/playback/playback_commands.py (baris 29–35)
claimed_severity: HIGH
source_findings: [BUG-B08]

---
master_id: M-049
title: _poll_duration menerbitkan QueueUpdatedEvent meskipun durasi gagal
description: Saat durasi lagu gagal didapatkan (nilai dur masih None) setelah 7 detik, _poll_duration tetap mengirim event QueueUpdatedEvent ke sistem yang akhirnya memicu broadcast menyeluruh tanpa adanya perubahan pada data state durasi.
claimed_location: engine/playback/controller.py (baris 153–170)
claimed_severity: HIGH
source_findings: [BUG-B09]

---
master_id: M-050
title: VolumeService.current_volume desync dari state.volume
description: Layanan objek class in-memori status volume mengambil nilainya sendiri saja saat boot tanpa mengorelasikan sinkronisasinya ke player daemon mpv asli, sehingga slider volume tidak terpantul-balas (out of sync) nilai benarnya bila mpv diboot berbekal state lawas. Penggunaan variabel snapshot (self.current_volume) dapat berbeda dengan state yang sesungguhnya apabila state dimutasi secara eksternal. Dua call serentak (race condition) juga dapat membaca dan menambahkan volume yang salah karena duplikasi pengambilan nilai dari variabel independen.
claimed_location: engine/volume_service.py (baris 19–41), engine/volume_service.py (__init__())
claimed_severity: HIGH
source_findings: [BUG-B10, SVC-03]

---
master_id: M-051
title: handle_ws_message kurang validasi tipe dict untuk 'data'
description: Handler memanggil data = msg.get("data", {}) namun apabila payload menspesifikasikan string untuk 'data', akan terjadi AttributeError di downstream ketika handler lanjutan mencoba untuk mengakses data.get("...").
claimed_location: server/handlers/websocket.py (baris 78–90)
claimed_severity: HIGH
source_findings: [BUG-B11]

---
master_id: M-052
title: ws_handler menangkap semua exception generik tanpa dipisah
description: Handler menganggap semua exception, termasuk disconnect yang wajar (ServerDisconnectedError/CancelledError), sebagai error sistem yang kemudian dicetak ke log, menambah noise dan mempersulit pelacakan error sebenarnya.
claimed_location: server/handlers/websocket.py (baris 65–76)
claimed_severity: HIGH
source_findings: [BUG-B12]

---
master_id: M-053
title: evict_stale_tracks mengirim list bukan tuple ke fungsi execute
description: Di beberapa versi aiosqlite, argumen list secara kaku tidak diterima pada query IN dengan array tunggal (['abc'] diinterpretasikan sebagai char sekuensial ('a','b','c')), dan list tersebut seharusnya dikoversi terlebih dahulu ke tuple sebelum eksekusi SQL.
claimed_location: cache/repositories/track_repository.py (baris 135–137)
claimed_severity: HIGH
source_findings: [BUG-B13]

---
master_id: M-054
title: fetch_segments SponsorBlock mengosongkan list segmen di awal request HTTP
description: Segmen langsung dihapus sebelum menunggu HTTP request SponsorBlock selesai. Ini menyebabkan _on_progress tidak mampu melewatinya meskipun track masih berjalan jika transisi delay atau terjadi error.
claimed_location: plugins/sponsorblock.py (baris 38–53)
claimed_severity: HIGH
source_findings: [BUG-B14]

---
master_id: M-055
title: CacheResolver._fetching bisa menunda waiter selamanya (Memory Leak)
description: Event listener yang menahan task async untuk antrean stream resolving tak mengeset parameter batasan waktu (timeout) apapun, mengakibatkan thread melayang mati (hang deadlock loading spinner di frontend) apabila task yang ditunggu kebetulan tertutup tiba-tiba (crash) sebelum melaporkan sinyal kelar. Jika ytdlp melemparkan exception ketika fetching, Waiter B akan diputus, lalu mengeksekusi fetch ulang seakan tidak pernah ada attempt, yang dapat menyebabkan concurrent parallel call berlebih secara tidak terbatas. Interaksi lempar balik fetch request API string youtube langsung error dan tamat memutus loop tanpa adanya peredam logic (mekanik retrying / backoff) memicu satu network drop murni melumpuhkan 1 putaran request lagu begitu saja. Apabila utilitas pemanggil link URL yt-dlp mati gagal mengembalikan URL, pelepasan status _fetching justru men-trigger loop ulang secara rentetan paralel kepada semua klien tunggu (waiters) untuk me-resolve sendiri barengan hingga mengebom layanan yt-dlp secara gila-gilaan (thundering herd). Event asinkron fetch URL dapat menimbulkan siklus tak berujung (infinite recursion) dari resolusi gagal ganda, mengekskalasi kebocoran request di memori dan menguasai queue proses thread lokal. Skema coroutine background pemanggil URL di belakang layar memuat wait limit exception rentan. Jika asyncio dilempar status CancelledError sewaktu lock (walau langka), key data tracking URL terkait tidak tuntas dikuras, menimbulkan penumpukan flag (bocor memori task).
claimed_location: cache/resolver.py (baris 42–56), cache/resolver.py, cache/resolver.py (resolve()), cache/resolver.py L43, server/services/stream_prefetch.py L22, server/services/stream_prefetch.py
claimed_severity: HIGH
source_findings: [BUG-B15, DB-017, EXC-01, EXC-02, RTY-01, CAC-03]

---
master_id: M-056
title: Baris LRC tanpa timestamp mendapatkan t=0.0
description: Metadata dari LRC file seperti [ti:Title] dimasukkan bersamaan dengan baris plain-text dan dicetak paksa menggunakan timestamp 0.0, yang menyebabkan artefak pada teks berjalan di awal lagu.
claimed_location: plugins/lyrics.py (baris 138–140)
claimed_severity: MEDIUM
source_findings: [BUG-B16]

---
master_id: M-057
title: lyrics.py melakukan ekstraksi query pencarian sia-sia
description: Modul pencarian lirik memproses konversi dan sanitasi Regex berat (clean_title dan search_query) meskipun variabel lrc sudah tersedia sukses melalui _cache.
claimed_location: plugins/lyrics.py (baris 57–98)
claimed_severity: MEDIUM
source_findings: [BUG-B17]

---
master_id: M-058
title: _on_track_ended dengan path eof terbuka pada pemanggilan paralel
description: Bug pada engine MPV bisa mengirimkan message end-file (eof) berulang kali berurutan. Tidak ada proteksi guard, yang menyebabkan fungsi _advance_to_next tereksekusi dua kali dan melompati dua trek antrean. Penanganan trigger waktu jeda EOF mpv sebesar (0.35s) tak diproteksi flag blokade boolean, membuat kiriman koneksi end-file redundan (misal 2 sinyal double karena lag internet) mengeksekusi track lompat 2x maju melompat secara brutal (skip song).
claimed_location: engine/playback/controller.py (baris 181–183), engine/playback/controller.py (_on_track_ended())
claimed_severity: HIGH
source_findings: [BUG-B18, EXC-04]

---
master_id: M-059
title: service_worker fallback salah path ke /static/index.html
description: Service Worker mencoba mencari dokumen HTML pada cache lewat caches.match('/static/index.html') padahal URL yang di-serve adalah path / (root). Offline fallback menjadi tidak berguna.
claimed_location: web/static/sw.js (baris 77)
claimed_severity: MEDIUM
source_findings: [BUG-B19]

---
master_id: M-060
title: _connectivity_checker memiliki infinite loop yang tidak henti saat graceful shutdown
description: asyncio.sleep(60) dapat melemparkan asyncio.CancelledError namun ia diserap ke dalam catch Exception tanpa melemparnya ulang, sehingga daemon task sulit dihentikan secara bersih dari pool saat mematikan aplikasi.
claimed_location: core/background_tasks.py (baris 9–19)
claimed_severity: MEDIUM
source_findings: [BUG-B21]

---
master_id: M-061
title: on_radio_randomize mengambil seed_artist dari cmd tanpa proteksi Null
description: Jika command_router memanggil command via action tanpa argumen (kasus 0 argument signiture), parameter cmd akan menjadi None. Pemanggilan cmd.seed_artist saat itu juga memicu AttributeError.
claimed_location: engine/playback/radio_commands.py (baris 20–22)
claimed_severity: MEDIUM
source_findings: [BUG-B22]

---
master_id: M-062
title: TrackInfo.from_dict mendiamkan ValueError karena video_id hash invalid
description: YtDlpClient menghasilkan fallback hash yang panjangnya melebihi validasi ID (11 huruf), sehingga VideoId() di TrackInfo melempar exception ValueError. Akibatnya object dikonversi jadi None dan request gagal diam-diam.
claimed_location: core/state.py (baris 58–65)
claimed_severity: MEDIUM
source_findings: [BUG-B23]

---
master_id: M-063
title: _on_track_ended mendeklarasikan next_data yang tidak pernah digunakan
description: Di dalam logika perpindahan end-file, variabel next_data dikostruksi, di-assign key dengan nilai video_id, tapi tidak pernah dipakai di kode mana pun setelahnya.
claimed_location: engine/playback/controller.py (baris 177–179)
claimed_severity: LOW
source_findings: [BUG-B24]

---
master_id: M-064
title: get_featured_genres menggunakan perintah print() daripada logging
description: Pada tangkapan error koneksi, perintah yang dipakai adalah print standar. Di sisi operasional produksi ini tidak tercatat dalam jurnal logger dengan struktur/tingkatan pesan yang benar. Alih-alih memakai sistem logger bawaan (logger.error()), fungsi menangkap galat dengan sekadar di-print biasa. Alhasil monitoring metrics tidak pernah menyimpan event error tersebut dalam logs/app.log produksi.
claimed_location: server/services/discover_service.py (baris 130), server/services/discover_service.py (baris 121)
claimed_severity: MEDIUM
source_findings: [BUG-B25, ARCH-A13]

---
master_id: M-065
title: _CompactRenderer.__call__ memberikan feedback log berupa empty string
description: Mem-bypass struktur chain logger dengan balasan return "" yang notabene tidak valid terhadap rantai fungsi structlog yang meminta objek dictionary.
claimed_location: core/log_config.py (baris _CompactRenderer.__call__)
claimed_severity: LOW
source_findings: [BUG-B26]

---
master_id: M-066
title: Daemon _summary_worker dan _status_bar_worker tak punya kondisi henti
description: Membiarkan worker memutar infinite loop dengan while True. Hal ini memaksa thread harus dibunuh oleh interpreter saat aplikasi mati. Akan lebih baik menggunakan event handler .wait() untuk exit condition.
claimed_location: core/log_config.py
claimed_severity: LOW
source_findings: [BUG-B27]

---
master_id: M-067
title: extractDominantColor merespons balik nilai callback berupa string
description: Pada saat terjadi kegagalan proses ekstraksi warna, callback akan mengembalikan nilai primitif string untuk kode css. Tapi pemanggilnya hanya menyiapkan diri mengolah object {r,g,b}, sehingga berakibat inkonsistensi render halaman.
claimed_location: web/static/js/utils.js
claimed_severity: LOW
source_findings: [BUG-B28]

---
master_id: M-068
title: ITUNES_API_URL Tidak Terdefinisi — ReferenceError di Browser
description: File utilitas memanggil constant ITUNES_API_URL untuk keperluan pengambilan metadata cover lagu di iTunes, tapi variabel ini tak terdefinisi di mana pun dalam codebase. Ini memicu ReferenceError pada browser dan menyembunyikan semua artwork UI.
claimed_location: web/static/js/utils.js (baris ~70)
claimed_severity: CRITICAL
source_findings: [ARCH-A03]

---
master_id: M-069
title: Penggunaan tag export di dalam file berarsitektur classic script
description: Modul audio.js memakai syntax ESM (export module) tetapi keseluruhan frontend adalah classic script (global namespace tanpa type="module"). Ini memicu SyntaxError fatal di level browser.
claimed_location: web/static/js/audio.js (baris 128)
claimed_severity: CRITICAL
source_findings: [ARCH-A04]

---
master_id: M-070
title: DiscoverService Menduplikasi Seluruh Logic DiscoverRepository
description: Duplikasi query SQL telanjang bergelimpangan ngawur ngulangi tugas yang persis dengan yang ada pada penampung modul repository track (SELECT video_id, title... FROM tracks). Kalau tabel berubah harus dirubah sinkron di banyak tempat atau program fail. Logic dari DiscoverService membuat query SQL raw yang duplikat total dengan implementasi di DiscoverRepository (DRY violation ekstrim sebanyak 132 baris). Bug yang diperbaiki satu titik tidak otomatis membetulkan endpoint yang lain.
claimed_location: server/services/discover_service.py, cache/repositories/discover_repository.py, server/services/discover_service.py vs cache/repositories/track_repository.py
claimed_severity: MAJOR
source_findings: [ARCH-A06, MAINT-CO-01]

---
master_id: M-071
title: State lagu yang sedang berputar di-broadcast ke seluruh client anonim
description: manager.broadcast() melampirkan broadcast lagu privat yang sedang diputar ke iterasi "active_connections", termasuk para pengunjung socket yang bahkan belum melakukan login autentikasi. Ini merupakan kebocoran data informasi.
claimed_location: server/handlers/websocket.py (baris 49), server/services/broadcast_service.py
claimed_severity: HIGH
source_findings: [ARCH-A08]

---
master_id: M-072
title: Penghapusan item deque menggunakan del memicu kompleksitas O(n)
description: Variabel queue menggunakan struktur deque dari collections yang tak efisien (O(n)) jika dipaksa menghapus data acak di tengah urutan via del self.state.queue[cmd.index]. Jika beroperasi di list 500+ lagu bisa menyumbat I/O jika user sering reorder item. List penyimpanan alur main dikonstruksi secara paksa dengan metode objek python (deque). Saat list ditarik reorder (pengubahan urutan list 1 ke urut 5) maka array list ditarik manual dipaksa bergeser dan me-loop 1 by 1 O(n) murni menumpulkan efisiensi saat list berukuran fantastis (1000 item ++).
claimed_location: engine/playback/queue_commands.py (baris 14), engine/playback/queue_commands.py (on_queue_remove(), on_queue_reorder())
claimed_severity: MEDIUM
source_findings: [ARCH-A10, QUE-01]

---
master_id: M-073
title: Tipe data field is_favorite bercampur inkonsisten
description: Konversi tak berujung antara integer(0,1) dan boolean terus terjadi pada track item di berbagai layer akibat deklarasi is_favorite menggunakan Optional[int]. Field is_favorite di-anotasikan sebagai tipe integer Optional[int], tetapi pada saat casting serialisasi JSON (to_dict) dipaksa dilempar jadi boolean. Ini menyebabkan ambiguitas yang tak terjelaskan saat dioper ke state lain.
claimed_location: core/state.py (baris 35, 52), core/state.py, cache/db.py, cache/repositories/
claimed_severity: MEDIUM
source_findings: [ARCH-A17, CS-010]

---
master_id: M-074
title: EventBus.subscribe() dengan tipe closure tidak terlindungi garbage collector
description: Lambda atau fungsi nested tak berstatus unbound method yang didaftarkan pada event_bus diikat secara statis (strong reference), tidak terserap oleh clean up weakref, sehingga menimbulkan akumulasi memory leak.
claimed_location: core/event_bus.py (baris 17–20)
claimed_severity: LOW
source_findings: [ARCH-A18]

---
master_id: M-075
title: Handler EnqueueGenreSongs menyebabkan eksekusi CommandBus Race
description: Fungsi mengeksekusi urutan modifikasi mode secara serial (SetModeCommand lalu QueueReplaceCommand lalu QueueSelectCommand). Hal ini membuat celah terbuka pada selipan event websocket lain, memungkinkan korupsi urutan antrian queue jika terjadi secara paralel. Pemencetan kartu blok tab 'Mix' langsung me-replika lagu ke daftar pemutaran tanpa mengeksekusinya di saat lock sama yang dikembalikan UI. Beresiko me-race parameter lock queue_select dengan parameter lain, menyebabkan gagal playback instan.
claimed_location: server/handlers/ws/queue_handlers.py (baris 54–59), server/handlers/ws/queue_handlers.py (_handle_enqueue_genre_songs())
claimed_severity: MEDIUM
source_findings: [ARCH-A19, QUE-02]

---
master_id: M-076
title: God Class pada ServerManagerWindow
description: ServerManagerWindow bertindak sebagai God Class dengan menangani event, dependency, proses, password, dan dialog (866 baris) dalam satu file. Tidak ada pemisahan Single Responsibility Principle. Metode pada tampilan antar-muka mengambil library sqlite3 secara sporadis untuk memanipulasi direktori tanpa melalui business engine. Script startup (start.py) adalah tong sampah raksasa menjejalkan GUI Manager Tkinter + Headless CLI + Port Scanner secara tumpang-tindih di file 866 baris, membuatnya sama sekali tak bisa dites otomatis unit test. Method perenderan antarmuka utama menangani semuanya tanpa didelegasikan sehingga modifikasi di satu lokasi sangat rapuh terhadap blok sekitar. Fungsi write untuk meng-generate dan me-render admin_password.txt dijalankan lewat implementasi file I/O repetitif (3 lokasi).
claimed_location: start.py (baris 1–866), start.py, start.py (method _build_ui), config.py, start.py, start.py (ServerManagerController.on_reset_password)
claimed_severity: MAJOR
source_findings: [CS-001, MAINT-R-02, CS-006, CS-008, CS-015]

---
master_id: M-077
title: serve_stream bertindak sebagai God Function
description: Satu fungsi sepanjang ~130 baris meng-handle banyak lapisan secara manual meliputi validasi ID, rate limit, proxying, Etag, path check, dsb.
claimed_location: server/handlers/http.py (baris serve_stream)
claimed_severity: HIGH
source_findings: [CS-003]

---
master_id: M-078
title: Method handle_auth memiliki siklus proses berlapis (Long Method)
description: Logika handle_auth sangat panjang karena memuat session checking, sleep penalty, validasi credensial, pruning, dan response generation sekaligus.
claimed_location: server/handlers/auth.py
claimed_severity: MEDIUM
source_findings: [CS-004]

---
master_id: M-079
title: Handlers websocket melempar Long Parameter List secara terpusat
description: Tiap bongkahan 26 fungsi Websocket terjangkit penyakit duplikasi primitive parameter. Meng-copy paste urutan argumen parameter 7 fungsi bawaan kemana-mana. Repot manakala jika satu butuh module tambahan event_bus, seluruh 26 file harus diotak-atik semua. Setiap WS handler diinisialisasi dengan tujuh parameter serupa yang tidak semuanya digunakan, memaksakan interface pattern secara artifisial.
claimed_location: server/handlers/ws/, Semua 26 WS handler di server/handlers/ws/
claimed_severity: MAJOR
source_findings: [CS-005, MAINT-A-03]

---
master_id: M-080
title: Validasi regex video_id diulang (Duplicate Code)
description: Format validasi (seperti ^[a-zA-Z0-9_-]{11}$) tersebar di berbagai layer dengan penyesuaian kecil berbeda (contohnya range limit 1-64 vs 11).
claimed_location: core/value_objects.py, server/handlers/ws/discover_handlers.py, engine/ytdlp_client.py
claimed_severity: MEDIUM
source_findings: [CS-007]

---
master_id: M-081
title: Dua implementasi mekanik rate limit yang berbeda secara fungsional
description: Sistem memisahkan filter rate limit dengan collections.defaultdict(list) secara global di satu modul dan dengan dict command_history di ConnectionManager di file berbeda, yang bisa inkonsisten. Proteksi traffic beroperasi ganda dengan standar yang tak sinkron (30 requests/60 detik untuk WS, 20 requests/60 detik untuk HTTP stream) di layer mandiri, sementara endpoints vital /health maupun /metrics dilepas tanpa pengawasan pembatasan trafik sama sekali.
claimed_location: server/handlers/http.py, server/middleware.py, server/middleware.py, server/handlers/http.py, core/constants.py
claimed_severity: HIGH
source_findings: [CS-009, API-06]

---
master_id: M-082
title: Parameter temporal angka dibiarkan sebagai Magic Number di hardcode
description: Timeout, limits, TTL tidak memiliki constanta berpusat (seperti 300, 14400, dll), menyulitkan pengaturan operasional dan skalabilitas server.
claimed_location: Tersebar di seluruh codebase
claimed_severity: MEDIUM
source_findings: [CS-012]

---
master_id: M-083
title: String type event dipatok literal pada switch frontend (Magic String)
description: Identifier tipe di WebSocket handler menggunakan label text mati ("progress", "lyrics"). Sedikit saja typo atau update API, frontend akan silent error. Penamaan routing dan fungsi WebSocket dipecah-pecah ke hardcode value teks mentah, alih-alih me-mappingnya pada satu pusat StrEnum WSAction yang telah tersedia di core module, berisiko tinggi saat penggantian sintaks global.
claimed_location: web/static/js/ws.js, server/handlers/ws/settings_handlers.py (baris 21, 26, 31)
claimed_severity: MEDIUM
source_findings: [CS-013, API-14]

---
master_id: M-084
title: Feature envy koneksi db pada discover_handlers
description: Endpoint server murni menerobos partisi abstrak level repository dan menendang command pemanggilan baris query sintak execute DB SQLite mentahan via logic websocket tanpa mengindahkn alur port fungsi dan membocorkan arsitektur (coupling brutal). Kode WS handler tiba-tiba memotong lapisan interaksi dan langsung merengkuh akses await db.conn.execute(...) di dalamnya, memblokir fleksibilitas modular. Konsep abstraksi database (Ports/Repository) dilangkahi secara kasar. Jalur service seperti discover_service bypass layer menembus keras langsung menulis syntax SQL query pakai raw db.conn. Jika db diganti/dirubah tabelnya, developer perlu membongkar seluruh sistem.
claimed_location: server/handlers/ws/discover_handlers.py, server/services/discover_service.py, server/handlers/ws/discover_handlers.py, server/handlers/http.py, server/handlers/ws/discover_handlers.py (_handle_toggle_favorite())
claimed_severity: CRITICAL
source_findings: [CS-014, MAINT-A-01, REP-03]

---
master_id: M-085
title: resumeVisualizerLoop tak difungsikan (Dead Code)
description: Subrutin untuk mengekstrak atau kembali ke pemutar gelombang mati di kode statis front-end tanpa pemanggilan dari handler mana pun.
claimed_location: web/static/js/audio.js
claimed_severity: LOW
source_findings: [CS-017]

---
master_id: M-086
title: unlockBrowserAudio nganggur (Dead Code)
description: Prosedur tersebut disetel sebagai variabel global browser JS dan tak pernah dideklarasikan interaksinya dengan DOM atau listener.
claimed_location: web/static/js/audio.js
claimed_severity: LOW
source_findings: [CS-018]

---
master_id: M-087
title: _last_stdout_line memonitor log tak terpakai (Dead Code)
description: Variabel pada instance server UI hanya mendata line out tanpa sempat memanipulasinya atau membacanya sebelum loop berikutnya.
claimed_location: start.py (ServerManagerController)
claimed_severity: LOW
source_findings: [CS-019]

---
master_id: M-088
title: Inline import module asyncio
description: Kelalaian sepele menyisakan panggilan sisa dobel library asyncio masuk 2x (satu di atas top, satu nyelip di method bawah). Sisaan hasil kegagalan bersih-bersih refactoring. Fungsi memuat module asyncio di tengah scope definisi, menghasilkan inefisiensi pengerjaan cache library.
claimed_location: server/handlers/auth.py (baris 43), engine/download_manager.py, server/handlers/websocket.py
claimed_severity: LOW
source_findings: [CS-021, MAINT-TD-03]

---
master_id: M-089
title: Unused root module aiohttp import
description: Library ditarik keseluruhan walaupun tak dipakai secara namespace, memboroskan tree-shaking virtual machine python.
claimed_location: server/handlers/websocket.py (baris 5)
claimed_severity: LOW
source_findings: [CS-022]

---
master_id: M-090
title: Komentar tambal sulam ditinggalkan menumpuk (Commented Code)
description: Informasi historikal patch masa lampau disembunyikan dalam code, bukan dititipkan sebagai dokumentasi git/CHANGELOG resmi. Meninggalkan artefak barisan riwayat perbaikan debug sprint lawas berupa komen (contoh: # CRITICAL-03, # PATCH-YTDLP) di kode produksi berjalan (production code). Menjadikan dokumen source script tidak rapi berbalut sampah dokumentasi historis internal.
claimed_location: server/handlers/http.py, web/static/js/ws.js, engine/mpv_controller.py, config.py, engine/mpv_controller.py, engine/radio_engine.py
claimed_severity: MAJOR
source_findings: [CS-023, MAINT-TD-01]

---
master_id: M-091
title: Discover Queries Dieksekusi Secara Serial (N+1 Berganda)
description: Query discover ke SQLite (get_recent, get_favorites, dsb) dipanggil dengan eksekusi await berurutan, menimbulkan latensi hingga +80-200ms per panggilan karena penumpukan di environment single-connection.
claimed_location: server/handlers/ws/discover_handlers.py (baris 17–31)
claimed_severity: CRITICAL
source_findings: [PERF-P01]

---
master_id: M-092
title: Seeding Database 1000 Songs dengan Serial INSERT (Startup Lambat)
description: Operasi insert dan update (upsert dll) melontarkan signal commit() tiap putaran baris di transaksi seeding awal tanpa di-wrap bundle commit, sangat merugikan performa menulis (ratusan penulisan ke disk lambat memakan waktu). Pemasukan bibit awal database tidak dioptimasi secara batch; fungsi berjalan repetitif per objek. Di kondisi I/O buruk, blokase load startup ini akan menjeda kesiapan server sampai sekitar semenit.
claimed_location: cache/db.py (baris 71–107), cache/repositories/track_repository.py, cache/repositories/auth_repository.py, cache/repositories/discover_repository.py
claimed_severity: HIGH
source_findings: [PERF-P03, TXN-01]

---
master_id: M-093
title: 100 Artist + 100 Genre Dikirim ke Klien Setiap Discover
description: Pengiriman daftar discover tidak disaring. Penarikan langsung 100 items akan me-render terlalu banyak DOM Node hashtag-pill yang malah akan mencekik thread visual browser pada layar sempit.
claimed_location: core/constants.py (baris 13–14)
claimed_severity: HIGH
source_findings: [PERF-P04]

---
master_id: M-094
title: renderFullState() Merender Semua Komponen Tanpa Dirty Check
description: Tidak ada delta diff state (dirty tracking) saat menerima update, memaksa aplikasi javascript menjalankan siklus perenderan ke seluruh sub-layout, menyita frametime dan menimbulkan tampilan janky.
claimed_location: web/static/js/ws.js (baris 95–97 dan 147–157)
claimed_severity: HIGH
source_findings: [PERF-P05]

---
master_id: M-095
title: JSON.stringify(track) di Setiap Render Item (Expensive per Frame)
description: Saat membangun antrean layout lagu (discover/recent), metadata direkam ke attribut JSON-text via stringify per baris objek secara simultan. Sangat mendegradasi resource memory-thread browser pada iterasi data berjumlah banyak.
claimed_location: web/static/js/render/discover.js (baris 126, 192, 412)
claimed_severity: HIGH
source_findings: [PERF-P06]

---
master_id: M-096
title: extractDominantColor() Membuat Canvas 50x50 di Main Thread per Track Change
description: Pembacaan warna latar memblok render visual utama karena instruksi get_image_data tak memakai pekerja paralel offscreen, melainkan berjalan secara sekuensial. Jeda terasa berat untuk UI animasi transisi sampul.
claimed_location: web/static/js/utils.js (fungsi extractDominantColor)
claimed_severity: MEDIUM
source_findings: [PERF-P08]

---
master_id: M-097
title: loadLazyCovers() Dipanggil Berulang Kali per Render Cycle
description: Inisiasi ulang image lazy_load melanda seluruh Node Document secara konstan setiap saat (Full DOM Scan), karena ia diletakkan tepat pada akhir dua prosedur render tab yang berbeda tapi eksekusinya tumpang tindih dalam satu event loop frame.
claimed_location: web/static/js/render/discover.js (baris 218, 242)
claimed_severity: MEDIUM
source_findings: [PERF-P09]

---
master_id: M-098
title: switchTab('discover') Memicu DISCOVER Request Setiap Kali Tab Diklik
description: Transisi antar-menu pada aplikasi tidak dicadangkan pada cache memory atau memiliki throttle window, menembakkan request data dan memboros kinerja jaringan client dan server terus-menerus.
claimed_location: web/static/js/main.js (baris 53–56)
claimed_severity: MEDIUM
source_findings: [PERF-P11]

---
master_id: M-099
title: Missing Index untuk Favorites Query
description: Parameter penanda favorite pada daftar lagu tidak ditopang tabel indeks sama sekali. Daftar lagu terfavorit hanya dapat disajikan dengan full table scan, yang melambat linear seiring data. Tabel lagu SQL tidak dioptimasi menggunakan partial index komposit pada pola filter 'is_favorite = 1'. Server terpaksa membaca seluruh database (full scan), memunculkan hambatan pada jumlah entri masif.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_findings: [PERF-P12, DB-009]

---
master_id: M-100
title: Service Worker Precache 20+ File CSS Terpisah (Tidak Perlu)
description: Precache array module mengundang banyak sekali HTTP Request karena file sumber (tokens, base) dipaksa di-precache meskipun kesemuanya sebenarnya sudah terserap ke dalam bundle.css.
claimed_location: web/static/sw.js (baris 4–29)
claimed_severity: MEDIUM
source_findings: [PERF-P13]

---
master_id: M-101
title: _pending Dict di MpvController Tidak Dibersihkan Saat Timeout
description: Block future asinkron _pending berpotensi menggantung tak terhapus jika terinterupsi intervensi diluar jangkauan TimeOut (misal dari CancelledError yang membunuh proses secara mutlak), berujung memori membengkak.
claimed_location: engine/mpv_controller.py (baris 198–209)
claimed_severity: MEDIUM
source_findings: [PERF-P15]

---
master_id: M-102
title: DiscoverService Di-instantiasi Ulang di Setiap Request
description: Objek servis penyedia lagu campuran difabrikasi ulang berulang menjadi var/objek python memori baru (diinstansiasi gres) terus menerus per panggilan hit websocket, yang menambah cycle beban CPU ringan dan mem-bypass teknik efisiensi cache memori singel. Module fungsional DiscoverService yang seharusnya cuma sebagai service stateless instansi Singleton, justru di-build berulang setiap kali masuknya request. Ini membuang waktu eksekusi VM internal (meski relatif kecil).
claimed_location: server/handlers/ws/discover_handlers.py (baris 17), server/handlers/ws/discover_handlers.py (_build_discover_payload())
claimed_severity: MEDIUM
source_findings: [PERF-P16, SVC-01]

---
master_id: M-103
title: Bundle CSS 55KB — Tidak Perlu Critical CSS Split
description: Sistem memuat semua aturan UI desktop & tablet menjadi satu kesatuan di mobile tanpa media selector split query. Peniadaan pemisahan gaya per-platform murni memperberat blok render tag Head di browser low-end.
claimed_location: TIDAK DISEBUTKAN
claimed_severity: LOW
source_findings: [PERF-P17]

---
master_id: M-104
title: getHashtagColor() Warna Acak Tidak Konsisten Antar Session
description: Variabel hash-color di injeksi menggunakan fungsi Math.random bawaan yang bersifat temporal dan menumpang memori lokal, akibatnya rentetan tag artis yang sama akan meleset gradasinya secara random setiap kali web client refresh halaman. Warna penanda chip genre dirender dengan Math.random() in-memory alih-alih di-hash statis dari title-nya, mengakibatkan pergeseran tone warna kapan pun DOM berubah atau browser me-load halaman.
claimed_location: web/static/js/render/discover.js (baris 1–7), web/static/js/render/discover.js
claimed_severity: MEDIUM
source_findings: [PERF-P18, FE-021]

---
master_id: M-105
title: Tidak Ada busy_timeout PRAGMA
description: Konfigurasi SQLite belum mensetting delay limit pada concurrent writes, yang menyebabkan sistem merespons error SQLITE_BUSY secara langsung saat menimpa data, berpotensi pada kehilangan data dan crash sepihak.
claimed_location: cache/db.py — fungsi init()
claimed_severity: HIGH
source_findings: [DB-002]

---
master_id: M-106
title: Tidak Ada Migration System
description: Definisi pembuatan tabel database terbelah ke dalam dua file berbeda dengan properti index dan constraint FK yang kontradiktif, memicu duplikasi sekaligus risiko korupsi pada data saat seed manual di ekspor. Struktur desain tabel sqlite di-inject asal sabet menumpang numpuk baris (add column) sekenanya per boot program. Saat sistem harus di rollback turun versi karena bug server, tabel akan menabrak hancur lantaran hilangnya riwayat manajemen transisi kolom database (migration file/alembic). Pembaharuan struktur kolom berjalan mandiri dan tidak sinkron karena tak ada versioning. Manipulasi ALTER TABLE langsung menumpuk dengan schema.sql mengakibatkan error pada eksekusi deploy antar pengguna lama/baru.
claimed_location: cache/db.py, data/export_to_sqlite.py, cache/schema.sql, cache/db.py (init)
claimed_severity: CRITICAL
source_findings: [DB-003, DB-004, DEVOPS-021]

---
master_id: M-107
title: INSERT OR REPLACE pada Tabel artists: Data Loss Risk
description: Mekanisme override data artis menghapus baris lama secara total dan membuat entri kosong baru. Variabel seperti statistik click_count akan terhapus tak bersisa di setiap perulangan seed.
claimed_location: cache/db.py — _seed_initial_data()
claimed_severity: HIGH
source_findings: [DB-005]

---
master_id: M-108
title: Race Condition: evict_stale_tracks() SELECT + DELETE Non-Atomic
description: Proses pencarian entri yang kedaluwarsa lalu penghapusannya dijalankan dalam dua query terpisah tanpa isolasi lock, memberi celah file termodifikasi di antaranya untuk terhapus tanpa ampun. Mekanik pembersihan tembolok kotor database menelan mentah-mentah jutaan dataset dari fetchall() dan mem-pushnya membengkak menjadi variable object python (list buffer) alih-alih me-limit parameter batching SQL. Menurunkan IO ram di skenario ukuran db tinggi. Urutan logika hapus track membuang file lokal sebelum komitmen DB terkunci sukses. Sebuah crash tak terduga pasca unlink file tapi pra-commit sql akan memunculkan file hantu di DB yang mustahil diakses.
claimed_location: cache/repositories/track_repository.py, cache/repositories/track_repository.py (evict_stale_tracks())
claimed_severity: HIGH
source_findings: [DB-006, DB-015, REP-02]

---
master_id: M-109
title: toggle_favorite() Tidak Menggunakan Transaksi Eksplisit
description: Modul database handler membungkus perintah UPDATE menyisipkan keyword RETURNING yang absolut tak direkognisi engine SQLite kernel versi lawas (di bawah 3.35). Menyebabkan mogok crash jika perangkat yang dipasang belum update SQLite (seperti shell android lama). Eksekusi tombol favorite tidak memakai batasan urutan (BEGIN EXCLUSIVE/IMMEDIATE). Double tap berurutan akan membaca cache yang sama dari state terdahulu tanpa mengunci nilainya, menggagalkan togle ganda.
claimed_location: cache/repositories/track_repository.py, cache/repositories/track_repository.py (toggle_favorite())
claimed_severity: MEDIUM
source_findings: [DB-007, TXN-03]

---
master_id: M-110
title: sessions Table: Tidak Ada Index pada expires_at
description: Pembersihan sesi timeout berpatokan pada kalkulasi data kolom expires_at yang tidak diindeks, memaksa pindaian basis data menyeluruh terhadap tiap sesi aktif saat cleanup berjalan.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_findings: [DB-008]

---
master_id: M-111
title: upsert_track() Selalu Update last_played
description: Rekaman fungsi meremajakan track (upsert) gegabah memperbaharui properti last_played (di set = time saat ini) tanpa melihat bahwa hal tersebut bukan dari diputar-player, merepresentasikan seakan track sering dimainkan dan mengotor-kacaukan data Recently Played list murni. Rekaman waktu putar dimanipulasi asal ketika metadata disentuh dari upsert_track(), meski lagu hanya sekadar diresolve tanpa benar-benar diputar, merusak integritas algoritma riwayat play_count dan cache cleanup.
claimed_location: cache/repositories/track_repository.py, cache/repositories/track_repository.py (upsert_track())
claimed_severity: MEDIUM
source_findings: [DB-010, TXN-04]

---
master_id: M-112
title: artists.id bukan AUTOINCREMENT: Risk pada Re-seed
description: Kolom ID artis digantungkan manual pada parameter string JSON yang tidak di-generate dinamis secara inkremental, rentan menubruk foreign key dan menimbulkan invalid references bila json dirubah/digabung.
claimed_location: cache/schema.sql
claimed_severity: MEDIUM
source_findings: [DB-011]

---
master_id: M-113
title: verify_session(): Side Effect Write dalam Read Operation
description: Pembacaan sesi via metode token murni menyertakan fungsi write database DELETE sepihak tanpa disangka. Menyalahi pedoman prinsip pemisahan baca-tulis serta memboros request tak terpakai.
claimed_location: cache/repositories/auth_repository.py
claimed_severity: MEDIUM
source_findings: [DB-013]

---
master_id: M-114
title: get_random_songs(): CTE dengan RANDOM() Tidak Deterministik & Slow
description: Algoritma order fallback radio tidak menjaring kriteria ketat WHERE untuk artist prioritas melainkan murni mengacak CASE THEN secara raw, menyebabkan seed awal artis bisa tak diikutsertakan sedikitpun kalau slot limit baris kuota data sudah penuh duluan oleh record artis lain. Sintak mutakhir ROW_NUMBER (window ops) sengaja di lempar keras-keras dari repo discover ke compiler DB. Dimana SQLite usang versi lawas (< 3.25 / tahun 2018) menolak membacanya dan mogok kerja (Crash) — problem termux/docker base android tua. Komputasi fungsi RANDOM di query SQLite dipaksa pada level setiap objek lagu saat menyusun radio otomatis, menyedot performa komputasi linear penuh pada semua tracks di dataset dan murni tidak skalabel.
claimed_location: cache/repositories/discover_repository.py, cache/repositories/discover_repository.py (get_random_songs(), get_genre_songs()), cache/repositories/discover_repository.py (get_random_songs())
claimed_severity: MEDIUM
source_findings: [DB-014, REP-04, BL-03]

---
master_id: M-115
title: Tidak Ada Normalisasi: TrackInfo.artist Duplikat Data
description: Rekaman identitas nama artis di tabel track disimpan ke dalam kolom string sembarang dibanding memanfaatkan parameter id Foreign Key, menimbulkan ambiguitas statisik dan huruf (case-sensitive) yang tak terkumpul.
claimed_location: cache/schema.sql
claimed_severity: LOW
source_findings: [DB-016]

---
master_id: M-116
title: TrackInfo.from_dict() Menerima stream_url dari Client (Injection Risk)
description: Metode pembacaan state mengizinkan input "stream_url" maupun "local_path" tak tersaring diserap langsung dari perintah yang dikirim klien (client controlled), membuka manipulasi state maupun file system jika tersimpan via database upsert.
claimed_location: core/state.py (baris 58-76), server/handlers/ws/playback_handlers.py, dll
claimed_severity: CRITICAL
source_findings: [API-01]

---
master_id: M-117
title: /api/stream/{video_id} Tidak Memerlukan Autentikasi
description: Titik henti stream bersifat terbuka lebar ke publik. Semua yang memiliki kode identifikasi Youtube acak dapat memerintahkan server menarik data url di latar belakang, menguras sumber daya secara ilegal serta melanggar term of service YouTube tanpa jejak token.
claimed_location: server/handlers/http.py (serve_stream baris 50-190), server/app.py (baris 38)
claimed_severity: CRITICAL
source_findings: [API-02]

---
master_id: M-118
title: Tidak Ada API Versioning
description: Tidak dijumpai pengenal awalan versi baik di API routing HTTP (e.g., /v1/) dan payload soket websocket. Saat interface bermutasi, server tak bisa memberikan penanganan berjenjang kepada klien aplikasi lawas.
claimed_location: server/routes.py, core/ws_actions.py
claimed_severity: HIGH
source_findings: [API-04]

---
master_id: M-119
title: Error Response Format Tidak Konsisten
description: Sistem penanganan balasan kesalahan bercabang ke dalam tiga gaya yang sangat berbeda di backend (sebagai JSON error di HTTP, pesan error spesifik WS, atau pesan log pasif). Menjadikan client sulit memetakannya.
claimed_location: server/handlers/ws/utils.py, server/handlers/websocket.py (baris 123-130), server/handlers/event_listeners.py
claimed_severity: HIGH
source_findings: [API-05]

---
master_id: M-120
title: Tidak Ada HTTP Request Timeout untuk Proxy Stream
description: Sambungan eksternal get-request ke server stream Youtube tidak mencantumkan parameter timeout sama sekali. Apabila target mengalami hang atau menunda respons, request akan nyangkut menyedot ketersediaan proses worker backend selamanya.
claimed_location: server/handlers/http.py (baris 151-189)
claimed_severity: HIGH
source_findings: [API-07]

---
master_id: M-121
title: WebSocket Auth Bypass via Role client — Tidak Konsisten
description: Tampilan web mengenalkan 3 tipe akses role ("portal", "admin", "client") tapi di dalam kerangka pengaman backend fungsi require_auth menganggap valid semuanya yang berada di himpunan authenticated_connections, sehingga level otorisasi non-admin ("client") sejatinya ilusi yang diblokir sebagai unauthenticated.
claimed_location: server/handlers/auth.py, server/handlers/websocket.py (baris 121)
claimed_severity: HIGH
source_findings: [API-08]

---
master_id: M-122
title: Tidak Ada Pagination untuk Search Results
description: Payload kembalian pada titik temu fitur pencarian dan rekomendasi dikunci paksa pada hard-limit 50 data, tak melempar format paginasi, indikator page-next, kursor, total data, yang menyebabkan hasil tak akan dapat diekspansi user.
claimed_location: server/handlers/ws/discover_handlers.py (baris 39-52), core/constants.py
claimed_severity: HIGH
source_findings: [API-09]

---
master_id: M-123
title: /health Tidak Mengembalikan Informasi yang Cukup untuk Load Balancer
description: Respon HTTP ping berstatus OK 200 sekalipun komponen playback mpv down. Desain ini membingungkan reverse proxy/loadbalancer pada skala produksi (health liveness berbeda dari readiness). Skrip bash pengecek kesehatan mesin ngawur mentah-mentah melihat label string "ok" walau isi perut report menyebutkan mpv (engine suara inti) dalam status modar/mati (not_started). Cek up ini menyesatkan admin, server dilaporin oke walau engine jebol.
claimed_location: server/handlers/http.py (health_check baris 27-44), scripts/monitor_health.sh
claimed_severity: HIGH
source_findings: [API-10, DEVOPS-028]

---
master_id: M-124
title: Caching Response Header Tidak Konsisten di Stream Endpoint
description: Layanan mengirim perintah simpan cache browser ("Cache-Control: private, max-age=3600") meskipun stream di-direct langsung dari URL Youtube yang miliki sistem validasi per 6-jam.
claimed_location: server/handlers/http.py (baris 83-90 dan 158-164)
claimed_severity: MEDIUM
source_findings: [API-11]

---
master_id: M-125
title: HTTP 302 Digunakan untuk Redirect Stream (Seharusnya 307)
description: Transisi rute cadangan memancarkan code response 302 (Found) sementara standard resmi HTTP Stream harusnya menuntut lemparan kode redirect statis 307 (Temporary Redirect) sehingga client takkan mengkonversi operasi awal dari pola asalnya.
claimed_location: server/handlers/http.py (baris 118)
claimed_severity: MEDIUM
source_findings: [API-12]

---
master_id: M-126
title: Tidak Ada Input Validation untuk Artist Name dan Genre Name
description: Handler khusus antrean genre/artis tidak menerapkan pengereman batasan nilai panjang karakter yang lolos, mempersilakan client mengekstrak pencarian query dengan ukuran teks super raksasa.
claimed_location: server/handlers/ws/queue_handlers.py (baris 33-43)
claimed_severity: MEDIUM
source_findings: [API-13]

---
master_id: M-127
title: Dark Mode: Aplikasi Hanya Mendukung Dark, Tidak Ada Light Mode Support
description: Palet warna tema hanya menginjeksi token variabel css gelap sepenuhnya menolak preferensi device pengguna (light/dark os). Ketidakadaan color-scheme turut menyebabkan kontras fatal silau dari sisa komponen input putih standar browser.
claimed_location: web/static/css/tokens.css
claimed_severity: HIGH
source_findings: [FE-008]

---
master_id: M-128
title: Responsive: Lirik Dipotong Paksa di Mobile (Max-Height 40px)
description: Styling lirik seluler menetapkan max-height: 40px serta memotong baris lewat text-overflow-ellipsis, murni menumpulkan fungsinya saat teks lirik aktual berisi deretan barisan super panjang pada piranti sempit (terpenggal total).
claimed_location: web/static/css/platform/mobile.css
claimed_severity: HIGH
source_findings: [FE-009]

---
master_id: M-129
title: Responsive: Desktop Player Bar Menggunakan !important Berlebihan (CSS Specificity War)
description: Penataan desktop.css menembak atribut baris kontrol memakai !important di belasan definisi. Kode styling meng-overwritte dirinya terus, menggagalkan ekstensi komponen dan menyebabkan duplikasi kotor saat mendesain layout horizontal/landscape.
claimed_location: web/static/css/platform/desktop.css, landscape.css
claimed_severity: MEDIUM
source_findings: [FE-010]

---
master_id: M-130
title: UX: Swipe Gesture Hanya Tersedia untuk Admin
description: Usapan kontrol geser track memblokir intervensi non-admin dengan sengaja memunculkan balok toast error tiap di swipe, memberi ketidaknyamanan navigasi karena fitur tak dinonaktifkan sunyi secara visual.
claimed_location: web/static/js/platform/touch.js
claimed_severity: MEDIUM
source_findings: [FE-011]

---
master_id: M-131
title: UX: Login Error State Tidak Di-Clear Saat Re-attempt
description: Papan penanda keliru input hanya membersihkan label bila eksekusi socket terklik terkirim (auth ok). Jika pengguna menghapus teks ketikan saat panel ber-error, pesan error mematung tersangkut meski ketikan baru di-reset ke string sah.
claimed_location: web/static/js/services/auth.js, web/static/js/events/index.js
claimed_severity: MEDIUM
source_findings: [FE-012]

---
master_id: M-132
title: Form Validation: Login Submit dengan Enter Hanya dari Password Field
description: Input eksekusi cepat menggunakan Enter Button tak diregister ke kolom masukan pengguna, mengakibatkan tekan sentak enter cuma berfungsi dari kolom kata sandi. Pengguna harus berpindah kolom jika tekan enter ditengah-tengah isi nama.
claimed_location: web/static/js/events/index.js
claimed_severity: MEDIUM
source_findings: [FE-013]

---
master_id: M-133
title: State Bug: store.status Di-set Optimistik Sebelum Server Konfirmasi
description: Pemencetan kontrol jeda dimanipulasi dengan langsung menimpa status "PLAYING" dalam klien secara seketika. Apabila internet terputus, atau request hilang, state server akan tertinggal dan frontend secara permanen terjebak out-of-sync.
claimed_location: web/static/js/events/player-events.js
claimed_severity: MEDIUM
source_findings: [FE-014]

---
master_id: M-134
title: Navigation: aria-selected Tidak Update Saat Tab Berubah via Swipe
description: Tindakan merubah menu lewat geser touch tidak memperbaharui nilai atribut seleksi (aria-selected) elemen DOM-nya, ditambah hilangnya penomoran role="tabpanel" pemisah antar layer konten yang mematikan kapabilitas screen navigation.
claimed_location: web/static/index.html, web/static/js/main.js
claimed_severity: MEDIUM
source_findings: [FE-015]

---
master_id: M-135
title: UI Consistency: Inline Style vs CSS Class (Anti-Pattern)
description: Halaman skeleton di-hardcode memakai beruntun penempelan elemen tag "style=.." secara brutal (inline styling). Menciderai kemudahan re-factoring layout, menyusahkan tracking properti UI dan membuat penggelapan dark-mode menyulit.
claimed_location: web/static/index.html
claimed_severity: MEDIUM
source_findings: [FE-016]

---
master_id: M-136
title: Loading State: Tidak Ada Skeleton Screen untuk Queue dan Radio
description: Container ruang blok barisan antrean lagu murni tidak membekali fitur state loading apapun selama WS tengah memuat respon awal, menelantarkan blok komponen jadi kanvas putih kosong membingungkan dalam beberapa sekon.
claimed_location: web/static/js/render/queue.js, web/static/index.html
claimed_severity: MEDIUM
source_findings: [FE-017]

---
master_id: M-137
title: Widget Tree: favorites.js adalah File Kosong
description: Modul file penulisan skrip daftar favorit tersaji nir-kode sama sekali (0 bytes). Algoritma pembentuknya nyatanya tertindih di luar berkas (discover.js), menumbuhkan utang teknis penumpukan bundel statis percuma tak bertuan.
claimed_location: web/static/js/render/favorites.js
claimed_severity: MEDIUM
source_findings: [FE-020]

---
master_id: M-138
title: UX: Artist Name Truncated di 25 Karakter dengan Nilai Hardcoded
description: Pemangkasan nama title di Javascript dipancangkan limit kasar (hardcode) pada titik absolut karakter ke-25 tanpa memperhitungkan lebar dinamis screen (responsif flex CSS), menuntun ke kondisi jelek pada viewport raksasa dan gawai.
claimed_location: web/static/js/render/search.js, web/static/js/render/discover.js
claimed_severity: LOW
source_findings: [FE-022]

---
master_id: M-139
title: Console.log Masih Ada di Production Code
description: Baris rekam debugging developer berserakan belum tersapu ke luar build produksi, yang dengan konyol merilis info parameter sensitif dan nilai-nilai tersembunyi ke publik mana saja yang iseng mampir.
claimed_location: web/static/js/audio.js, web/static/js/utils.js
claimed_severity: LOW
source_findings: [FE-023]

---
master_id: M-140
title: UX: Tidak Ada Konfirmasi Saat Hapus Unduhan
description: Pemencetan kontrol hapus memicu pengiriman event tak termaafkan (destruktif deletion) ke socket tanpa filter persetujuan terlebih dahulu. Salah sentuh akan menggagalkan file hasil susah payah didownload sebelumnya, tak dapat dikembalikan.
claimed_location: web/static/js/events/player-events.js
claimed_severity: LOW
source_findings: [FE-024]

---
master_id: M-141
title: RadioRandomizeCommand Hanya Berjalan di RADIO Mode
description: Parameter mode pemutaran radio diproteksi if statement ketat yang mensyaratkan status radio sedang aktif untuk fungsi pengacakan seed artist. Alhasil, klik acak dari antrean biasa diblok mentah dengan notifikasi log saja (harus 2 klik baru jalan).
claimed_location: engine/playback/radio_commands.py (on_radio_randomize())
claimed_severity: CRITICAL
source_findings: [BUG-03]

---
master_id: M-142
title: Admin Password Tidak Tercetak di Non-TTY Environment
description: Password login murni tak ter-hash yang di-generate perdana tercetak ke wadah shell console log sys.stderr, di mana oleh script eksekutor termux (android) dipaksa dilempar terekam utuh ke dalam log file plaintext (>> startup.log 2>&1). Menghamparkan pundi password bagi sesiapa yang nimbrung. Pencetakan password rahasia admin untuk sesi awal dikunci validasi output isatty() yang selalu salah (false) di lingkungan background (docker, daemon systemd), menyembunyikan selamanya password masuk yang ter-generate.
claimed_location: config.py (get_admin_password()), config.py, baris 76–79
claimed_severity: CRITICAL
source_findings: [BUG-04, DEVOPS-015]

---
master_id: M-143
title: on_queue_select() Membuang Track Sebelum Index Tanpa Update History
description: Pemilihan acak nomor baris antrean lagu langsung mem-pop list index-index lawas membuangnya begitu saja tanpa mendaftarkannya terlebih dahulu ke memori log history pemutaran.
claimed_location: engine/playback/queue_commands.py (on_queue_select())
claimed_severity: HIGH
source_findings: [BL-01]

---
master_id: M-144
title: _backfill_and_standby() Race Condition pada Queue Length Check
description: Pemeriksaan kapasitas queue pemutaran (15 slot) dijalankan setelah fungsi di kunci (locked) oleh lock async yang mana queue length bisa saja sudah dieksekusi dan berubah panjang aslinya, memicu double fetch ganda data pemutaran (terlalu banyak dimuat).
claimed_location: engine/radio_engine.py (_backfill_and_standby())
claimed_severity: MEDIUM
source_findings: [BL-04]

---
master_id: M-145
title: _seed_initial_data() Tanpa Error Recovery — Partial State
description: Skrip muat awalan (seeding) pangkalan data berjalan telanjang menabrak apa saja tanpa pengamanan blok tangkap try-except, mengakibatkan DB dibiarkan kotor patah-patah isinya tanpa sempat merollback kalau ditengah muat paksa terjadi interupsi OS.
claimed_location: cache/db.py (_seed_initial_data())
claimed_severity: HIGH
source_findings: [TXN-02]

---
master_id: M-146
title: bare except di _handle_delete_download
description: Logika penghapusan file lagu memakai metode blok exception-kosong (bare except:) yang menyapu buta-buta semua pesan komplain error tingkat dasar Python (keyboard-interrupt dll). Kesalahan penghapusan dari folder lokal juga menjadi gaib ditelan bumi.
claimed_location: server/handlers/ws/download_handlers.py (_handle_delete_download())
claimed_severity: MEDIUM
source_findings: [EXC-05]

---
master_id: M-147
title: STATS.is_playing Diset Tanpa Lock dari Async Context
description: Parameter state perhitungan metrik stat logger diculik dan dijadikan state wadah mutasi berbagi (shared object) secara langsung oleh modul engine playback di backend. Mengakibatkan pelanggaran dependency inversion berat (logic merubah UI presentasi). Pencatatan status putar lagu (is_playing) pada status bar thread memodifikasi property objek core logging secara harfiah begitu saja tanpa memanfaatkan thread-lock async yang tesedia, yang rawan menodai pembacaan (torn read) di chip bertipe ARM.
claimed_location: engine/playback/controller.py L127, engine/playback/playback_commands.py L54, core/log_config.py, engine/playback/controller.py, server/handlers/websocket.py, dkk
claimed_severity: MAJOR
source_findings: [CC-01, MAINT-A-02]

---
master_id: M-148
title: DownloadManager._download_lock Memblokir Task Kedua Selamanya
description: Lock antrean handler mendownload tak mengikat klausul tenggang wait_for() sama sekali. Kalau antrean task ke-1 memakan waktu super lama/nge-hang dari internet lemot, maka task pen-download file track kedua terparkir pasif mematung (starvation limit) tanpa konfirmasi reject ke UI klien.
claimed_location: engine/download_manager.py (_do_download())
claimed_severity: MEDIUM
source_findings: [CC-04]

---
master_id: M-149
title: Lyrics Cache FIFO Bukan LRU — Hotspot Eviction
description: Kamus penampung string lirik dalam memori dibatasi di angka 50 dengan cara me-remove item data terdepan (index awalan / FIFO), ironisnya track yang tersering di mainkan juga ikut tertendang dihapus dan harus fetch ulang, bukannya menghapus lagu asing (least used data / LRU).
claimed_location: plugins/lyrics.py (fetch())
claimed_severity: MEDIUM
source_findings: [CAC-01]

---
master_id: M-150
title: Stream URL TTL di Batas Bawah Kedaluwarsa YouTube
description: Interval wajar ketahanan string referensi yt-dlp URL disetel ngawur 6 jam mutlak (21600), padahal youtube dapat memutuskan URL kurang dari range wajar ini sedikit, memicu link expired dipanggil sebagai link wajar (403 terlarang).
claimed_location: config.py
claimed_severity: MEDIUM
source_findings: [CAC-02]

---
master_id: M-151
title: MPV Reconnect Tidak Restore Queue State
description: Skema perbaikan MPV crash sukses membangkitkan instance video ke menit pemutaran namun acuh tidak memanggil re-restore list array (Queue dan state Radio), menumbangkan alur otomatis berurut setelah engine hidup kembali (lagu terputus tidak maju track berikutnya).
claimed_location: engine/playback/controller.py (_on_mpv_reconnected())
claimed_severity: MEDIUM
source_findings: [RTY-02]

---
master_id: M-152
title: _observe_events() Kill + Terminate Tanpa Check Exit Status
description: Engine MPV yang macet dibuang kasar (terminate) ditindih tembakan pamungkas (kill process id) di nol sekon beruntun secara langsung, memantik lemparan error tingkat shell os level (OSError) jika PID id yang dituju sudah terlebih lunas mati.
claimed_location: engine/mpv_controller.py (_observe_events() finally)
claimed_severity: MEDIUM
source_findings: [RTY-03]

---
master_id: M-153
title: Domain Layer Import dari Logging Infrastructure
description: Penataan skrip ranah (domain layer controller) membocorkan privasi levelnya dengan meng-import core log (log_config.py / infrastruktur utilitas) yang merusak batasan bersih pemisahan layer pada arsitektur serta memukul tingkat kesulitan uji unittest mock.
claimed_location: engine/playback/controller.py L17, engine/playback/playback_commands.py L4
claimed_severity: HIGH
source_findings: [DEP-01]

---
master_id: M-154
title: track_loader.py Akses DB Langsung via resolver.db
description: Kode mesin pemutar melantur dengan menancapkan perintah pembaharuan (upsert DB) memakai path variabel `self.resolver.db`, yang padahal ia memiliki instance var pasangannya sendiri `self.db`, menghasilkan var ganda tumpuk saling membingungkan pemanggilan API SQLite nya. Pemanggilan fungsi utilitas loader nekat melompati hierarki interface dengan me-reach (mengambil) instance internal modul database resolver `self.resolver.db`, menimbulkan pengkaitan erat tersembunyi berisiko hancur ketika logic parent resolver disentuh/diganti.
claimed_location: engine/playback/track_loader.py L27, engine/playback/controller.py L89, L105
claimed_severity: MEDIUM
source_findings: [DEP-02, DEP-04]

---
master_id: M-155
title: event_listeners.py Import dari discover_handlers.py — Circular-Risk
description: Script wadah muat listener mereferensikan library file rute web service socket sejawatnya ke ruang filenya, menghasilkan potensi lilitan-keliling lingkaran (circular dependency) dan membobol aturan batas antar-handler.
claimed_location: server/handlers/event_listeners.py L57-58
claimed_severity: MEDIUM
source_findings: [DEP-03]

---
master_id: M-156
title: config.py Diimport dari Hampir Semua Layer
description: Semua direktori fungsionalitas murni secara bar-bar meng-import config.py absolut langsung ke berkasnya. Mengakibatkan hard-coupling global yang melumpuhkan kemampuan Dependency Injection (DI) yang baik pada lingkungan deployment berlapis dan pen-tes-an.
claimed_location: Multiple
claimed_severity: MEDIUM
source_findings: [DEP-05]

---
master_id: M-157
title: docker-compose.yml Tidak Meneruskan Secrets dari Environment
description: Struktur pembungkus compose environment abai tidak mendistribusikan turunan secret-token maupun pasword rahasia server (seperti LUNAWAVE_ADMIN_PASS). Membuat setting manual env luar tertelan dan wadah terpaksa meng-generate kunci random terus.
claimed_location: docker-compose.yml
claimed_severity: HIGH
source_findings: [DEVOPS-014]

---
master_id: M-158
title: JS Bundle Tidak Di-build dalam Docker Image
description: Pembungkus perakitan kontainer abai me-running script penjahit (npm run build) halaman. Jika repo bersih tak punya file bundle.js (karena ter-gitignore dari host), maka aplikasi Docker yang dionline-kan buta 100% tanpa skrip interaksi frontend satupun (lumpuh putih UI).
claimed_location: Dockerfile
claimed_severity: CRITICAL
source_findings: [DEVOPS-016]

---
master_id: M-159
title: make_dist.sh Menggunakan git archive Tanpa Verifikasi Integritas
description: Proses pengepakan arsip zip rilis program manual cuma mem-pump `git archive` mentahan, telanjang tak disertai stempel tanda periksa keamanan file SHA-checksum, gagal melakukan verifikasi tag versi dan juga lupa menginklusikan compile-an frontend bundle.js yang diperlukan.
claimed_location: scripts/make_dist.sh
claimed_severity: MEDIUM
source_findings: [DEVOPS-018]

---
master_id: M-160
title: Tidak Ada Proses Release Formal
description: Pola rilis berantakan tanpa wadah track log perubahan terpusat, pengingat rilis di kode (main.py) mematok angka ngawur (1.0.0) yang mengacuhkan versi project paten aslinya yang sedang di 0.1.0 di file pyproject.
claimed_location: main.py baris 1, pyproject.toml
claimed_severity: HIGH
source_findings: [DEVOPS-019]

---
master_id: M-161
title: Rollback via git checkout Berbahaya di Environment Produksi
description: Skrip pembantu darurat untuk mengembalikan patch lawas menggunakan teknik paksa brutal reset git checkout ke id mundur, memblok mundur file sistem mentah tanpa meng-stop daemon running Python, menjebol koneksi DB berakibat cacat parah file lokal korup.
claimed_location: scripts/rollback.sh
claimed_severity: CRITICAL
source_findings: [DEVOPS-020]

---
master_id: M-162
title: Prometheus Metrics Ada Tapi Tidak Terhubung ke Sistem Monitoring
description: Ekstraksi catatan data (Gauge) sangat minim dan dangkal, meloloskan buta parameter kritis yang penting seperti statistik jumlah download fail, rute kueri server database mandek, hingga status mati-tidak MPV (Cuma ada 4 item unfaedah). Dekorasi penyetelan export data grafik kinerja (Metrics) yang tertanam di server hanya menjadi hiasan statis, lantaran hilangnya rantai kaitan ke sistem ekosistem pembaca penangkap log utamanya (Prometheus / Grafana). Metric dibuat untuk dicuekin (Theater monitoring semata).
claimed_location: docker-compose.yml, core/observability.py, core/observability.py
claimed_severity: HIGH
source_findings: [DEVOPS-022, DEVOPS-023]

---
master_id: M-163
title: Log Hanya ke File Lokal, Tidak Ada Centralized Logging
description: Sambungan dari temuan direktori kontainer (004). Volume pembuat logs tidak dipetakan ke host lokal, menyebabkan seluruh catatan sakti saat proses crash langsung terkubur wafat sesaat setelah container ditendang restart ulang, debug tak mungkin dilakukan (mustahil dicari lognya). Sistem pen-catatan event error aplikasi memendam file tulisannya khusus pada /logs lokal saja per 5MB putaran. Bencana kehilangan file saat sistem Docker hang membuat error lenyap, karna output print tidak dilempar standar keluar (stdout) di mode container.
claimed_location: core/log_config.py, docker-compose.yml
claimed_severity: HIGH
source_findings: [DEVOPS-024, DEVOPS-025]

---
master_id: M-164
title: Structlog Tidak Menyertakan Correlation ID / Request ID
description: Perekam barisan pesan log buta-buta membom penulisan pesan tanpa dibekali token id berantai (Req ID). Begitu server padat dipakai paralel, admin akan mual muntah mengurai membedakan baris log mana yang milik rute user 1 dibanding rute event user 2 (pencampuran baris pusing).
claimed_location: server/middleware.py, core/log_config.py
claimed_severity: MEDIUM
source_findings: [DEVOPS-026]

---
master_id: M-165
title: Tidak Ada Sistem Alerting Sama Sekali
description: Ketiadaan notifikator (alarm sirine system warning) bagi operasi server. Bilamana mesin lumpuh ditengah jalan atau RAM kepenuhan pada pukul 3 subuh, admin baru ngeh keesokan hari secara manual, karena script pemberi tanda SOS sama sekali belum dirancang satupun.
claimed_location: test suites (global)
claimed_severity: CRITICAL
source_findings: [DEVOPS-027]

---
master_id: M-166
title: Backup Database Hanya Satu File .bak (Overwrite Setiap 24 Jam)
description: Ratusan berkas lagu mentah cache-offline kesayangan yang telah capek-capek dimuat tak diamankan dalam backup rotasi database (hanya file data .db nya). Hancurnya disk atau error hapus kontainer berarti reset 0 dari ulang pemanggilan download API yt dari awal lagi semua lagunya. Roda rutinitas salin db 24 jam dengan kejam selalu menimpa file duplikat yang itu-itu lagi (.bak) selamanya tanpa sistem antrean berurut (rotasi array max). Kalau database asli error busuk pas ter-copas jam tersebut, admin ga akan punya mundur sisa versi cadangan satupun lagi (kedua file sama-sama busuk). Mekanik panggil api salin copy database langsung melepasnya begitu script copy kelar dan diam bertawakal buta berasumsi filenya sempurna berjalan tanpa melakukan re-verify integrity_check memastikan integritas. Jika ada corrupt IO, backup akan sukses semu padahal rusak.
claimed_location: core/background_tasks.py, baris 32, test suites (global), core/background_tasks.py
claimed_severity: CRITICAL
source_findings: [DEVOPS-029, DEVOPS-030, DEVOPS-031]

---
master_id: M-167
title: Tidak Ada Rencana Disaster Recovery
description: Nihilnya pakem buku panduan prosedur penangan cacat parah atau crash total. Operator bakal kebingungan mati lemes kalau misal server kena sabotase, tidak tahu urutan RPO maupun letak langkah recovery db manual pas kondisi hidup dan mati karena no-playbook document.
claimed_location: test suites (global)
claimed_severity: CRITICAL
source_findings: [DEVOPS-032]

---
master_id: M-168
title: Termux Boot Script Tidak Menangani Kegagalan Startup
description: Script startup daemon auto-load linux termux android mengeksekusi jalan paksa background terminal server dengan mengabaikan sinyal kelar. Jadi misal script macet di detik 1 gagal build dependensi, bash akan menipu menelurkan log berhasil (exit 0) padahal proses crash.
claimed_location: scripts/termux_boot.sh
claimed_severity: HIGH
source_findings: [DEVOPS-033]

---
master_id: M-169
title: opentelemetry Disebut di Dependency Check Tapi Tidak di requirements.txt
description: Skrip check di launcher keliru memancing pendeteksian nama modul "opentelemetry" yang sama sekali tak terinstal via requirements dan tak pernah dipakai, melahirkan validasi palsu false negative eror (bilang dependensi lu kurang terus/hilang). Teks parameter string pada skrip bash pemeriksa run-time dependencies error nyebut library (opentelemetry) yang sama sekali melompong tak ada hubungannya dengan pip list requirement rilis file. Menelurkan false negative (minta di-install padahal ga dipake sama sekali).
claimed_location: start.sh, requirements.txt, start.py baris 51
claimed_severity: MAJOR
source_findings: [DEVOPS-034, MAINT-CO-02]

---
master_id: M-170
title: /tmp Socket Path di .env.example Berbahaya di Shared Environment
description: Panduan penulisan rute soket komunikasi MPV pada templat lingkungan dev keliru merekomendasikan penanaman pipa socket di direktori publik global sistem operasi yang absolut tidak aman (/tmp). Membahayakan pintu intersep socket diretas penyusup (bisa lempar fake command player dari app tetangga).
claimed_location: .env.example, baris 11
claimed_severity: MEDIUM
source_findings: [DEVOPS-035]

---
master_id: M-171
title: CDN External tanpa Subresource Integrity (SRI)
description: Link tembakan resource desain Font (Tabler icons) diarahkan dari jsdelivr eksternal murni tanpa filter pencocokan validitas hash-checksum (SRI). Bila cdn dibajak hacker dan link diisi malware js injeksi, seluruh user LunaWave seketika tertular otomatis (Supply Chain Attack vector).
claimed_location: web/static/index.html baris 17-18
claimed_severity: CRITICAL
source_findings: [DEP-003]

---
master_id: M-172
title: Package Name Mismatch antara package.json dan package-lock.json
description: File peniti kunci paket (package-lock) tidak pernah di perbaharui secara pas dengan package asalnya saat project berubah nama. Lock name ngotot pake nama lama ytgui-project sedang json barunya lunawave. Berpotensi CI pipe eror jika melakukan validasi ketat nama paket.
claimed_location: package.json baris 2, package-lock.json baris 2
claimed_severity: MAJOR
source_findings: [DEP-004]

---
master_id: M-173
title: Python Version Inconsistency di Tiga Tempat
description: Tembakan minimal os python beda-beda belangsak pada 3 setting file. Pyproject bilang >=3.10, CI di 3.11, Docker di 3.12. Membuat kelolosan error ga singkron (test lolos di versi 3.11 tapi jebol deprecated library pas di-docker pake versi 3.12).
claimed_location: pyproject.toml, .github/workflows/ci.yml, Dockerfile
claimed_severity: MAJOR
source_findings: [DEP-005]

---
master_id: M-174
title: Dev Dependencies Sangat Jauh dari Latest (Outdated)
description: Deretan modul library penunjang environment (pytest, ruff, mypy, bandit) membusuk usang tertinggal sangat jauh (contoh mypy telat rilis 1 major version, ruff telat 14 patch minor) membuat testing berisiko tersandung bug-bug di versi lama tsb.
claimed_location: requirements-dev.txt
claimed_severity: MAJOR
source_findings: [DEP-007]

---
master_id: M-175
title: Production Dependencies Tertinggal dari Latest
description: Modul utama tulang punggung aplikasi (yt-dlp, structlog, prometheus) dibiarkan usang. Terutama bahaya buat yt-dlp yang kalau telat patch Youtube API sebentar, akan fail fungsi utamanya gak mau muter/download musik youtube.
claimed_location: requirements.txt
claimed_severity: MAJOR
source_findings: [DEP-008]

---
master_id: M-176
title: esbuild Hanya di devDependencies tapi Dibutuhkan untuk Build
description: Library pembuat bundel JS (esbuild) ditaruh di kategori "Dev-Only", namun script build produksi wajib membutuhkannya. Saat production rilis menarik paket dependensi non-dev, esbuild tidak ikut masuk, build UI js production dipastikan lumpuh.
claimed_location: package.json
claimed_severity: MINOR
source_findings: [DEP-011]

---
master_id: M-177
title: syncedlyrics 1.0.1 Potensi Breaking API
description: Plugin pemetik lirik nyangkut di 1.0.1. Modul ini ngandelin scraping web ketiga. Kalau web ketiga (e.g musixmatch) ngubah api nya seiprit, scraper lirik bakalan mati senyap karena tak punya status fallback fail yang terekam monitoring.
claimed_location: requirements.txt, plugins/lyrics.py
claimed_severity: MINOR
source_findings: [DEP-012]

---
master_id: M-178
title: Bandit Mengskip Rules Keamanan Penting
description: Security linter Bandit dimatikan pemindai /tmp (B108). Membiasakan taruh folder temp ke hardcode absolut (/tmp) di os linux rawan serangan racun symlink jika sistem berjenis multi-user, karena hacker user sebelah dapat menumpuk folder palsu pakai nama yg sama.
claimed_location: pyproject.toml
claimed_severity: MINOR
source_findings: [DEP-013]

---
master_id: M-179
title: CI Pipeline Menginstall requirements.txt di Ubuntu tapi Tidak di Windows
description: CI build runner untuk test_windows tidak mengeksekusi pytest usai menginstall requirement. CI hanya melakukan test command gampang cmd.exe /c start.bat doang. Membiarkan segala bug konektor windows aiohttp lolos ga ada yang ngetes.
claimed_location: .github/workflows/ci.yml
claimed_severity: MINOR
source_findings: [DEP-014]

---
master_id: M-180
title: log_config.py adalah God Object yang Melanggar SRP
description: File konfigurator log menggendong 7 tanggung jawab raksasa yang tidak nyambung sekaligus (ANSI colour, global state, CLI status bar, Spinner context, semantic log rewriter). File ini sangat padat, ruwet (477 baris), dan susah untuk dibaca ataupun diubah fungsinya (God Object).
claimed_location: core/log_config.py
claimed_severity: MAJOR
source_findings: [MAINT-R-01]

---
master_id: M-181
title: Penamaan Logger Tidak Konsisten logger vs _log
description: Standar konvensi variabel pemanggil logger secara global menggunakan nama "logger" (di 29 file), tiba-tiba terpelanting jadi nama aneh "_log" secara khusus di file radio_engine.py doang. Membingungkan jika ini private atau public convention.
claimed_location: engine/radio_engine.py
claimed_severity: MINOR
source_findings: [MAINT-N-01]

---
master_id: M-182
title: bootstrap.py Import di dalam Function Body (Anti-pattern)
description: Tata letak pengimporan modul memanggil dari perut di dalam fungsi, bukan dideklarasi top-level. Mematikan static analizer pembaca autocomplete dan menyamarkan penyakit circular loop error tersembunyi. Script inisiator peluncur awal app memikul fungsi Manual Dependency Injection, memaksa pemanggilan 28 jenis import class yang panjang tak terawat di satu function build_app_context(). (sangat fragile untuk maintain modul).
claimed_location: core/bootstrap.py
claimed_severity: MAJOR
source_findings: [MAINT-A-04, MAINT-C-04]

---
master_id: M-183
title: DiscoverService Tightly Coupled ke Database Concrete Class
description: Servis discover mengikat kelas objek konkret database secara keras/solid (tight-coupled). Memutus fleksibilitas antarmuka (Port) dan memaksa pengujian module ini butuh running real file database utuh (susah untuk unit test mocking).
claimed_location: server/services/discover_service.py
claimed_severity: MINOR
source_findings: [MAINT-C-02]

---
master_id: M-184
title: STATIC_DIR Didefinisikan Dua Kali dengan Path Berbeda
description: Penentuan penunjuk jalan letak folder halaman html (/web/static) dideklarasikan dobel di dua file lewat jalur turunan kalkulasi string parent yang beda. Rapuh banget, geser letak file 1x maka akan macet 404 pathing web-nya (path rusak).
claimed_location: server/handlers/http.py baris 15, server/app.py baris 14
claimed_severity: MINOR
source_findings: [MAINT-C-03]

---
master_id: M-185
title: 16 type ignore Menandai Masalah Typing yang Belum Diselesaikan
description: Penambal bypass tutup mata terhadap warning hint tipe (type: ignore) berhamburan hingga 16 baris akibat akses nakal yang melangkahi parameter abstract port class, menandakan sistem tipe arsitektur port tidak beres (Type Check Mypy error suppressed).
claimed_location: discover_service.py, mpv_controller.py
claimed_severity: MINOR
source_findings: [MAINT-TD-02]

---
master_id: M-186
title: CacheResolver._fetching tidak dilengkapi pengaman lock atomic asyncio
description: Dictionary _fetching rentan race condition dalam blok asyncio karena dua coroutine bisa melewati pengecekan variabel sebelum sempat mengunci, yang pada akhirnya malah menciptakan overhead query yt-dlp ganda untuk video yang sama.
claimed_location: cache/resolver.py (baris 32–38)
claimed_severity: MEDIUM
source_findings: [ARCH-A14]

---
master_id: M-187
title: start.py merupakan monolith launcher berisi 31.000 baris kode
description: File launcher sangat raksasa sampai 31K baris karena ia menggabungkan deteksi cross-platform ke satu lokasi sentral tanpa modularitas. File jadi tak bisa diuji secara terpisah dan membuang performa.
claimed_location: start.py
claimed_severity: MEDIUM
source_findings: [ARCH-A15]

---
master_id: M-188
title: Listener Event plugin mengkonsumsi performa linear berulang (O(n))
description: SponsorBlockHandler dan LyricsFetcher mendaftar diri pada frekuensi TrackProgressEvent (setiap ~330ms) lalu menjalankan scan sekuensial linear (for loop) di dalam list array yang panjang, memberatkan kinerja I/O player seiring waktu berjalan.
claimed_location: plugins/sponsorblock.py (baris 19), plugins/lyrics.py (baris 22)
claimed_severity: MEDIUM
source_findings: [ARCH-A16]

---
master_id: M-189
title: Retry Logic Tidak Idempotent untuk PLAY_TRACK
description: Penayangan trek lagu menenggak perintah ganda berulang-ulang tanpa saringan ID. Jaringan yang terputus sejenak dari klien bisa mengirim ulang perintah ini dan mengeksekusinya ke engine tanpa peringatan duplikasi.
claimed_location: server/handlers/ws/playback_handlers.py (baris 8-11), web/static/js/ws.js
claimed_severity: MEDIUM
source_findings: [API-15]

---
master_id: M-190
title: /metrics Menggunakan Custom Header X-Metrics-Token (Non-Standard)
description: Rute layanan prometheus mendadak menggunakan X-Metrics-Token custom pada pengamanan rahasianya, yang secara inheren ditolak berbagai engine analitik lain yang biasanya menggunakan skema Bearer Auth konvensional.
claimed_location: server/handlers/http.py (serve_metrics baris 198-210)
claimed_severity: MEDIUM
source_findings: [API-16]

---
master_id: M-191
title: DELETE_DOWNLOAD Tidak Mengembalikan Status Sukses/Gagal Terstruktur
description: Kesimpulan penyelesaian penarikan/unduh dihapus dikirim kembali sekadar sebagai pesan logs biasa ke client, meluputkan penanda statis JSON object gagal/sukses secara programatik untuk ditangani tampilan frontend.
claimed_location: server/handlers/ws/download_handlers.py (baris 19-49)
claimed_severity: MEDIUM
source_findings: [API-17]

---
master_id: M-192
title: .env.example Menggunakan Nama Variable yang Berbeda dari config.py
description: Label konstanta pengaturan awal yang tercatat di kerangka .env referensi memakai kata dasar YTGUI_*, berlawanan mutlak dari penulisan di dalam skrip config.py yang justru menggunakan kata kunci LUNAWAVE_*.
claimed_location: .env.example, config.py (baris 24-29)
claimed_severity: LOW
source_findings: [API-18]

---
master_id: M-193
title: ITUNES_API_URL Tidak Pernah Didefinisikan: Runtime ReferenceError
description: Script pemanggil cover artwork mereferensikan variabel ITUNES_API_URL yang kosong secara absolut pada semua file konfigurasi. Ketiadaan variabel ini meruntuhkan (crash) pemanggilan gambar thumbnail asli dan mengembalikan default youtube yang buram.
claimed_location: web/static/js/utils.js, web/static/js/config.js
claimed_severity: CRITICAL
source_findings: [FE-001]

---
master_id: M-194
title: Service Worker Cache Stale: Deployment Bypass
description: String pemanggilan resource bundle.js pada script worker tidak menggunakan kunci versi identik yang sama dengan yang dikaitkan di HTML, mengakibatkan pengguna selalu disodori versi cache lawas meskipun backend telah terbaharui dari ujung server.
claimed_location: web/static/sw.js, web/static/index.html
claimed_severity: CRITICAL
source_findings: [FE-002]

---
master_id: M-195
title: Duplicate Event Listener pada Lyric Offset Controls
description: Interaksi fungsi sinkronisasi (sync) waktu lirik ditumpuk pengaitannya dua kali ke satu tag button secara repetitif, mengakibatkan variabel perubahan offset terpanggil berlipat (-0.5 jadi -1.0) memicu kacau waktu tanpa ada warning.
claimed_location: web/static/js/events/lyrics-events.js (baris 34-45 dan 59-70)
claimed_severity: CRITICAL
source_findings: [FE-003]

---
master_id: M-196
title: renderSheetLyrics() Menambah Scroll Listener Tanpa Batas
description: Mekanisme pendeteksian wheel mouse dan usap lirik menempelkan event touchmove tanpa diset ulang tiap kali innerHTML div parent lirik dihapus bangun. Karena pendeteksian _scrollBound memakai atribut element dom yang terganti, event lama terus tergenang menjejali memory (leak).
claimed_location: web/static/js/render/lyrics.js
claimed_severity: HIGH
source_findings: [FE-004]

---
master_id: M-197
title: Tidak Ada Focus Trap pada Modal/Bottom Sheet
description: Menu jendela mengambang pada aplikasi (settings, lyrics, action) dibiarkan mengalirkan fokus navigasi ke objek belakang background sheet. Membuat pengguna keyboard memicu komponen asing melampaui aturan keamanan (WCAG) aksesabilitas antarmuka.
claimed_location: web/static/index.html (.settings-sheet), web/static/js/events/settings-events.js
claimed_severity: HIGH
source_findings: [FE-005]

---
master_id: M-198
title: Login Form: Tidak Ada <label> pada Input Fields
description: Field masukkan login tidak dirangkai menggunakan korelasi tag pelabelan. Mengandalkan placeholder sebagai identitas semata menyingkirkan kemampuan alat screen reader disabilitas memahami fungsi kotak isian.
claimed_location: web/static/index.html
claimed_severity: HIGH
source_findings: [FE-006]

---
master_id: M-199
title: Volume Slider Tidak Ada aria-label dan aria-valuenow
description: Parameter nilai (aria) aksesibilitas dasar (aria-label, valuenow) luput pada bar kontrol volume, membungkam petunjuk status dan perubahan persentase ukuran audio secara absolut pada asisten mesin pencerna layar.
claimed_location: web/static/index.html
claimed_severity: HIGH
source_findings: [FE-007]

---
master_id: M-200
title: Frontend: Tidak Ada Test Runner Otomatis
description: Lapis antarmuka javascript dibiarkan berjalan hampa telanjang tak punya pengujian unit runner tool apapun (seperti jest/vitest), cuma bersandar pada 1 page testing visual manual konvensional yang tak berimbas.
claimed_location: Seluruh web/static/js/
claimed_severity: CRITICAL
source_findings: [AUDIT-TEST-010]

---
master_id: M-201
title: Mock Strategy Terlalu Longgar di E2E Tests
description: Modul fungsi mock penguji koneksi integrasi akhir memancangkan default check token-pass-berhasil (return true all) pada verifikator session token secara sewenang-wenang membabi buta, yang berakibat otentikasi login apa saja akan lewat lulus walau salah.
claimed_location: tests/integration/test_e2e.py
claimed_severity: HIGH
source_findings: [AUDIT-TEST-011]

---
master_id: M-202
title: Tidak Ada Test untuk Concurrency / Race Condition
description: Mekanik asinkron lalu lintas ganda interupsi (konkurensi thread) sepi total dari beban pengujian (stress collision task test). Aplikasi buta akan penanganan lock-queue race jika di spam WS berentet oleh admin.
claimed_location: test suites (global)
claimed_severity: CRITICAL
source_findings: [AUDIT-TEST-012]

---
master_id: M-203
title: Tidak Ada Test untuk Notifications Plugin
description: Sinyal pemanggilan loop event OS di backend notif diparkir mandiri tanpa uji thread cleanup maupun uji lemparan string broadcast title. Logika ini akan beresiko freeze thead bila dibiarkan menggantung.
claimed_location: plugins/notifications.py
claimed_severity: HIGH
source_findings: [AUDIT-TEST-013]

---
master_id: M-204
title: Tidak Ada Performance / Load Test
description: Kekokohan infrastruktur jaringan real-time streaming tak dibackup oleh profil beban (benchmark perf) pengujian jumlah maksimal bandwidth / koneksi klien (load test) membahayakan kapabilitas server crash bila dihantam banyak user.
claimed_location: test suites (global)
claimed_severity: HIGH
source_findings: [AUDIT-TEST-014]

---
master_id: M-205
title: Fixture Tunggal sample_track.json Tidak Cukup
description: Pangkalan sumber data bohongan pengetesan hanya disuntik 1 file model yang kelewat standar murni bersih lurus, melupakan file uji batas anomali cacat karakter khusus atau array cacat, menimbulkan false pass.
claimed_location: tests/fixtures/sample_track.json
claimed_severity: MEDIUM
source_findings: [AUDIT-TEST-015]

---
master_id: M-206
title: Dockerfile Mereferensikan run.py yang Tidak Ada
description: Titik eksekusi container (CMD) pada Dockerfile dengan ceroboh di-set untuk memanggil "run.py", yang mana sama sekali tak ada dalam direktori aplikasi (hanya ada main.py). Membuat deployment otomatis langsung crash seketika (fatal).
claimed_location: Dockerfile, baris 28
claimed_severity: CRITICAL
source_findings: [DEVOPS-001]

---
master_id: M-207
title: Container Berjalan Sebagai Root
description: File racikan Docker melalaikan deklarasi pembuatan ruang profil pengguna (USER), menjadikan hak akses aplikasi berjalan sebagai raja (root) di dalam container, sangat rentan di-infiltrasi hingga menembus host OS jika aplikasi bobol.
claimed_location: Dockerfile (keseluruhan)
claimed_severity: CRITICAL
source_findings: [DEVOPS-002]

---
master_id: M-208
title: Tidak Ada HEALTHCHECK di Dockerfile
description: Parameter ping status (Healthcheck) dilupakan di script docker. Saat aplikasi python macet melayang (hang), instansi manajer docker tidak dapat mendeteksi kondisi mati rasa aplikasi untuk me-restartnya secara otomatis (Up terus padahal modar).
claimed_location: Dockerfile
claimed_severity: HIGH
source_findings: [DEVOPS-003]

---
master_id: M-209
title: Volume Docker Hanya Mount /app/data, Cache dan Logs Hilang Saat Restart
description: Konfigurasi Compose me-mount 1 direktori belaka (/app/data), sementara tumpukan berharga cache download, catatan history log, serta pendaftaran pasword admin (/app/cache) akan tersapu rata dan musnah tak berbekas begitu container direstart.
claimed_location: docker-compose.yml
claimed_severity: CRITICAL
source_findings: [DEVOPS-004]

---
master_id: M-210
title: Port Binding ke 0.0.0.0 Tanpa Firewall Layer
description: Ekstraksi map binding port pada konfigurasi docker (0.0.0.0:8765) dengan ceroboh mengekspos rute langsung aplikasi mentah ke ranah internet publik bila perangkat punya public IP. Beresiko ditembus penyusup tanpa pelindung firewall reverse proxy tambahan (seperti nginx).
claimed_location: docker-compose.yml, baris ports
claimed_severity: HIGH
source_findings: [DEVOPS-005]

---
master_id: M-211
title: Layer Caching Dockerfile Tidak Optimal
description: Tata perancangan layer script docker kurang cermat menaruh aksi transfer source code (COPY . .) di atas lintasan install dependensi NPM. Mengakibatkan setiap perubahaan Python sedetik pun juga harus membuild ulang module bundle npm yang berat memperlambat siklus iterasi (cache bust sia-sia).
claimed_location: Dockerfile
claimed_severity: MEDIUM
source_findings: [DEVOPS-006]

---
master_id: M-212
title: Tidak Ada Continuous Deployment (CD)
description: Alur roda pipa perakitan otomatis (CI pipeline) terputus di tengah (hanya testing), absennya step pengantaran build rilis ke ekosistem production berujung pada pen-deployan kuli manual yang rentan kecelakaan/human-error.
claimed_location: .github/workflows/ci.yml
claimed_severity: HIGH
source_findings: [DEVOPS-007]

---
master_id: M-213
title: Windows CI Job Tidak Menjalankan Tests
description: Pengecekan otomatis server CI yang spesifik untuk ekosistem (OS) windows hanya main pura-pura uji parse (cek sintak cmd doang) dan melewatkan tes unit pytest core, membiarkan bug patal versi rute backslash windows tembus (silent bug).
claimed_location: .github/workflows/ci.yml
claimed_severity: HIGH
source_findings: [DEVOPS-008]

---
master_id: M-214
title: CI Coverage Threshold Terlalu Rendah (40%)
description: Syarat indikator lolos kualitas hijau dari porsentase uji test unit dipatok amat teramat miskin cuma 40 persen (--cov-fail-under=40), menumbuhkan penipuan (false sense) keamanan code yang meloloskan > separuh kode tak teruji ke produksi.
claimed_location: .github/workflows/ci.yml, baris 41
claimed_severity: MEDIUM
source_findings: [DEVOPS-009]

---
master_id: M-215
title: Tidak Ada CI Job untuk Frontend JavaScript
description: Jaring pengecekan rilis membiarkan folder web interface Javascript buta-buta telanjang menembus release karena "npm test" tidak di definisikan runnernya (echo error di package.json). Bug fatal client frontend tidak bisa terdeteksi CI.
claimed_location: .github/workflows/ci.yml, package.json
claimed_severity: HIGH
source_findings: [DEVOPS-010]

---
master_id: M-216
title: Tidak Ada Artifact Pinning / Reproducible Build
description: Rantai pipa server github-actions menarik paket dependensi luar tanpa dipatok kode rilis hash absolut (contoh action checkout). Rentan sekali jikalau aksi library luar terinfiltrasi malware otomatis merembet pada aplikasi proyek (supply chain attack risk).
claimed_location: .github/workflows/ci.yml
claimed_severity: MEDIUM
source_findings: [DEVOPS-011]

---
master_id: M-217
title: Inkonsistensi Prefix Environment Variable (3 Skema Berbeda)
description: Nama penanda environment server tumpang-tindih bercampur 3 ragam prefix aneh sekaligus secara berantakan (YTGUI_, LUNAWAVE_, YT_PLAYER_, LunaWave_PORT). Saat admin mengisi dari .env.example (YTGUI_), sistem diam-diam membaca yang lain, sehingga gagal mem-passing admin_password tanpa pesan (silent fail).
claimed_location: config.py, .env.example, start.sh, start.py
claimed_severity: CRITICAL
source_findings: [DEVOPS-012]

---
master_id: M-218
title: admin_password.txt Disimpan dalam Plaintext Hash Tanpa Enkripsi Tambahan
description: Dokumen pengingat simpanan kata sandi administrator tercetak polos ke file plaintext hash secara kasar di wilayah direktori bebas yang berdampingan di area "cache" lagu MP3, membuatnya gampang dicolong diekstrak paksa peretas jikalau server terpapar bocor exploit transversal zip.
claimed_location: config.py, baris 66–69
claimed_severity: HIGH
source_findings: [DEVOPS-013]

---
master_id: M-219
title: requirements.txt dan pyproject.toml Tidak Sinkron
description: Pengaturan paket library aplikasi tercerai belai menyamping pada 2 file rujukan independen (req.txt dan toml) tanpa pengunci sinkronisasi korelasi satu-kebenaran (sync single truth). Berakibat error inkonsisten di staging-dev versus saat di run via build Docker.
claimed_location: requirements.txt, pyproject.toml
claimed_severity: HIGH
source_findings: [DEVOPS-017]


Total temuan mentah (sebelum dedup): 317
Total setelah dedup: 219
Jumlah yang tergabung (bukan unik): 59