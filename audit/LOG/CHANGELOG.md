# Task Execution Changelog

Dokumen ini adalah rekaman perubahan (log) dari setiap task yang diselesaikan. **AI Agent wajib mengisi log ini SATU PER SATU per task** setiap kali sebuah task telah diimplementasikan, divalidasi dengan sukses, dan sebelum dipindahkan ke folder `DONE`.

---

## 📋 Format Changelog

Gunakan format di bawah ini saat menambahkan *entry* baru ke dalam Changelog (pastikan entry terbaru selalu diletakkan paling atas / format *Reverse Chronological*):

```markdown
### [Task-ID] - YYYY-MM-DD
**Objective:** (Tujuan singkat dari task ini)

- **Deskripsi:** Apa yang dilakukan / diimplementasikan?
- **File Diubah:** 
  - `path/ke/file1.ext` (Modified)
  - `path/ke/file2.ext` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman.
```

---

## 🚀 Log Riwayat Eksekusi

*(Catat perubahan terbaru di atas baris ini)*

### [S02-032] - 2026-07-07
**Objective:** EventBus.subscribe() dengan tipe closure tidak terlindungi garbage collector

- **Deskripsi:** Memperbaiki sistem *event bus* internal (`core/event_bus.py`) agar menautkan fungsi anonim dan *closure* menggunakan referensi lemah (`weakref.ref(handler)`). Perbaikan ini menambal _memory leak_ akibat pendaftaran fungsi-fungsi sesaat sebagai referensi keras (ARCH-A18).
- **File Diubah:** 
  - `core/event_bus.py` (Modified)
  - `tests/unit/core/test_event_bus.py` (New Tests)
- **Status Testing:** ✓ Lulus validasi penyerapan *closure* oleh *garbage collector*.


### [S02-031] - 2026-07-07
**Objective:** ITUNES_API_URL Tidak Terdefinisi — ReferenceError di Browser

- **Deskripsi:** Mendefinisikan konstanta global `ITUNES_API_URL` = `"https://itunes.apple.com/search"` di ranah *browser* yang sebelumnya lupa disisipkan. Hal ini mencegah putusnya rantai pengambilan metadata sampul resolusi tinggi oleh UI via iTunes API (ARCH-A03).
- **File Diubah:** 
  - `web/static/js/utils.js` (Modified)
  - `web/static/js/bundle.js` (Modified)
  - `tests/test_helpers.html` (Test Updated)
- **Status Testing:** ✓ Lulus validasi ketersediaan dan tipe data string `ITUNES_API_URL`.


### [S02-030] - 2026-07-07
**Objective:** extractDominantColor merespons balik nilai callback berupa string

- **Deskripsi:** Menstandarkan balasan rutin *error fallback* pada `extractDominantColor` (`web/static/js/utils.js`). Awalnya mengembalikan literal CSS string yang tidak dapat diekstraksi properti komponen RGB-nya oleh pemanggil dan menyebabkan *undefined behaviour*. Kini fungsi telah diamankan untuk mengirim objek balasan berstruktur sama `{r: 28, g: 28, b: 34}` (menyerupai *dark mode fallback* \#1C1C22) saat penangkapan elemen *canvas* bermasalah (BUG-B28).
- **File Diubah:** 
  - `web/static/js/utils.js` (Modified)
  - `tests/test_helpers.html` (Test Updated)
- **Status Testing:** ✓ Lulus uji injeksi elemen kanvas tak-valid yang memicu pengembalian mode *fallback* bentuk objek.


### [S02-029] - 2026-07-07
**Objective:** Daemon _summary_worker dan _status_bar_worker tak punya kondisi henti

- **Deskripsi:** Menambahkan sinkronisasi penyetopan menggunakan _event handler_ (`threading.Event().wait()`) untuk *worker* terminal `_summary_worker` dan `_status_bar_worker`. Hal ini mencegah *thread* tertahan _sleep_ paksa hingga sepuluh menit tatkala aplikasi meminta terminasi (_graceful shutdown_) (BUG-B27).
- **File Diubah:** 
  - `core/log_config.py` (Modified)
  - `tests/unit/core/test_log_config.py` (New Tests)
- **Status Testing:** ✓ Lulus uji percepatan terminasi dan pembebasan eksekusi blokir (*unblock*) utas saat _shutdown_ dipanggil.


### [S02-028] - 2026-07-07
**Objective:** _CompactRenderer.__call__ memberikan feedback log berupa empty string

- **Deskripsi:** Memperbaiki malpraktik pada prosesor `_CompactRenderer` di log config yang meretur nilai string kosong alih-alih mempertahankan rantai `event_dict`. Log `noise` yang tidak krusial kini dicegat menggunakan pelemparan eksepsi `structlog.DropEvent` standar, memastikan data tak sekadar dibuang ke terminal namun menjaga integritas sirkulasi rantai data sampai ujung penangkap pesan (BUG-B26).
- **File Diubah:** 
  - `core/log_config.py` (Modified)
  - `tests/unit/core/test_log_config.py` (New Test)
- **Status Testing:** ✓ Lulus validasi penangkapan eksepsi pembuangan pesan (_DropEvent_) dan kembalian kamus data log asli tanpa kecelakaan di level *renderer*.


### [S02-027] - 2026-07-07
**Objective:** get_featured_genres menggunakan perintah print() daripada logging

- **Deskripsi:** Memastikan standarisasi pencatatan galat (error logging) pada `DiscoverService.get_featured_genres` telah menggunakan eksekutor terstruktur `logger.error` daripada metode konsol (`print`) untuk penangkapan eksepsi persisten, sehingga jejak error operasional terekam secara aman pada subsistem log (BUG-B25, ARCH-A13).
- **File Diubah:** 
  - `tests/unit/server/test_discover_service.py` (New Test)
- **Status Testing:** ✓ Lulus validasi simulasi pelemparan galat (`sqlite3.Error`) yang sukses ditangkap dan dicatat (log error).


### [S02-026] - 2026-07-07
**Objective:** _on_track_ended mendeklarasikan next_data yang tidak pernah digunakan

- **Deskripsi:** Menyingkirkan entitas `dead code` dari logika transit memori `PlaybackController._on_track_ended` yang sekadar menyimpan atribut `video_id` ke variabel lokal `next_data` namun tidak dioperasikan sama sekali (BUG-B24).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
- **Status Testing:** ✓ Lulus tanpa regresi perilaku modul kontrol pemutar.


### [S02-025] - 2026-07-07
**Objective:** TrackInfo.from_dict mendiamkan ValueError karena video_id hash invalid

- **Deskripsi:** Memperbaiki penanganan kegagalan (*exception handling*) di `TrackInfo.from_dict` agar tidak mendiamkan error ketika menemui ID video yang melanggar ketentuan panjang (bukan 11 karakter). Kesalahan akan dicatat (melalui `structlog`) secara eksplisit alih-alih ditelan mentah-mentah lalu mengembalikan `None`, memudahkan pelacakan jika *client* `yt-dlp` mengeluarkan respons abnormal (BUG-B23).
- **File Diubah:** 
  - `core/state.py` (Modified)
  - `tests/unit/core/test_app_state.py` (New Test)
- **Status Testing:** ✓ Lulus uji penangkapan dan verifikasi pemanggilan pencatatan log *error* saat validasi *hash* meleset.


### [S02-024] - 2026-07-07
**Objective:** service_worker fallback salah path ke /static/index.html

- **Deskripsi:** Memperbaiki resolusi rujukan berkas saat kondisi internet mati (_offline fallback_) pada *Service Worker*. URL *fallback* HTML yang sebelumnya mengarah secara invalid ke `/static/index.html` dialihkan kembali ke rute sejati `/` (root), memastikan ketersediaan moda operasional PWA (Progressive Web App) tatkala *offline* (BUG-B19).
- **File Diubah:** 
  - `web/static/sw.js` (Modified)
  - `tests/unit/web/test_sw_fallback.py` (New Test)
- **Status Testing:** ✓ Lulus validasi ketersediaan lintasan _cache fallback_ yang benar dengan memindai *syntax file sw.js*.


### [S02-023] - 2026-07-07
**Objective:** _on_track_ended dengan path eof terbuka pada pemanggilan paralel

- **Deskripsi:** Mengamankan transisi perpindahan lagu (*EOF*) pada modul `PlaybackController._on_track_ended` dari pemicuan ganda akibat sinyal redundan *engine MPV* di saat *lag*. Pengaman `_eof_advancing` mencegah fungsi lompat 2 trek secara destruktif tanpa menginterupsi *sleep timer* peredam jeda standar 0.35 detik (BUG-B18, EXC-04).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
  - `tests/unit/engine/test_playback_controller_eof_parallel.py` (New Test)
- **Status Testing:** ✓ Lulus uji penahanan transmisi ganda (*concurrent event drops*) melalui sinkronisasi *asyncio.gather*.


### [S02-022] - 2026-07-07
**Objective:** lyrics.py melakukan ekstraksi query pencarian sia-sia

- **Deskripsi:** Memindahkan rantai komputasi pembersihan RegEx untuk _clean_title_ dan perakitan kueri pencarian (_search_query_) ke dalam percabangan asinkron `if not lrc:`. Langkah protektif ini meredam siklus CPU intensif tanpa guna saat status *cache* berujung *hit*, memastikan *runtime* sinkronisasi lirik berjalan optimal sesuai prinsip penghematan beban performa (BUG-B17).
- **File Diubah:** 
  - `plugins/lyrics.py` (Modified)
  - `tests/unit/plugins/test_lyrics.py` (New Test)
- **Status Testing:** ✓ Lulus validasi peniadaan *RegEx parsing* untuk skenario persediaan lirik di dalam struktur data termemori (*cache*).


### [S02-021] - 2026-07-07
**Objective:** Baris LRC tanpa timestamp mendapatkan t=0.0

- **Deskripsi:** Menghapus blok pengecualian (*fallback*) pada fungsi `_parse_lrc` di modul Lirik yang secara keliru menempelkan *timestamp* `0.0` untuk metatag (misal `[ti:Title]`) maupun baris telanjang tanpa penanda waktu format `.lrc`. Perbaikan ini memastikan tidak ada baris artefak menumpuk pada detik permulaan trek. (BUG-B16).
- **File Diubah:** 
  - `plugins/lyrics.py` (Modified)
  - `tests/unit/plugins/test_lyrics_parser.py` (New Test)
- **Status Testing:** ✓ Lulus validasi penjatuhan (*drop*) paksa terhadap *string* bukan lirik tanpa memecah integritas *parsing*.


### [S02-020] - 2026-07-07
**Objective:** CacheResolver._fetching bisa menunda waiter selamanya (Memory Leak)

- **Deskripsi:** Merombak implementasi antrean tunggu resolusi *stream* (CacheResolver._fetching) dari berbasis _asyncio.Event_ menjadi pemanfaatan fitur modern _asyncio.Future_ berbalut `asyncio.Lock`. Perubahan arsitektur ini membekali _fetcher_ dengan batas penantian (timeout 30 detik) serta mewariskan status eksepsi secara simultan ke seluruh *waiter*. Hal ini menyudahi malfungsi siklus kegagalan rekursif tak terhingga bila yt-dlp secara terduga gulung tikar (BUG-B15).
- **File Diubah:** 
  - `cache/resolver.py` (Modified)
  - `tests/unit/cache/test_resolver_concurrency.py` (New Test)
- **Status Testing:** ✓ Lulus validasi simulasi konkurensi dengan rintangan asinkron.


### [S02-019] - 2026-07-07
**Objective:** fetch_segments SponsorBlock mengosongkan list segmen di awal request HTTP

- **Deskripsi:** Melindungi *array* dari penghapusan prematur tatkala request _SponsorBlock_ masih diproses. Sinkronisasi akses _self.segments_ dengan mekanisme *asyncio.Lock* memastikan perpindahan interval/transisi lagu tidak menginterupsi filter iklan trek berjalan saat _network fetch_ mengalami jeda respon (BUG-B14).
- **File Diubah:** 
  - `plugins/sponsorblock.py` (Modified)
  - `tests/unit/plugins/test_sponsorblock.py` (New Test)
- **Status Testing:** ✓ Lulus uji konkurensi (mock _delayed network fetch_) dan validasi persistensi segmen masa lampau.


### [S02-018] - 2026-07-07
**Objective:** evict_stale_tracks mengirim list bukan tuple ke fungsi execute

- **Deskripsi:** Menuntaskan cacat penolakan bacaan array oleh `aiosqlite` ketika operasi penghapusan massal dilakukan. Koleksi `video_ids` yang memuat sederet entitas *stale* secara dinamis dikonversi ke dalam wujud literal `tuple` sebelum ter-bind ke kueri eksekusi SQL berbasis klausa `IN` (BUG-B13).
- **File Diubah:** 
  - `cache/repositories/track_repository.py` (Modified)
  - `tests/unit/cache/test_track_eviction.py` (New Test)
- **Status Testing:** ✓ Lulus uji identifikasi parameter iteratif berbasis _tuple_.


### [S02-017] - 2026-07-07
**Objective:** ws_handler menangkap semua exception generik tanpa dipisah

- **Deskripsi:** Menurunkan derajat kesalahan pencatatan (*error logging*) atas putusnya koneksi *websocket* secara alamiah. Tangkapan _Exception_ generik kini dipecah: _asyncio.CancelledError_ diarahkan ke `logger.debug` dan _ConnectionError_ ke `logger.info`, sehingga tidak mengotori _log_ utama dengan jejak galat semu yang membingungkan pelacakan bug (BUG-B12).
- **File Diubah:** 
  - `server/handlers/websocket.py` (Modified)
  - `tests/unit/server/test_ws_exceptions.py` (New Test)
- **Status Testing:** ✓ Lulus verifikasi penanganan pengecualian pada unit _mock websocket iteration_.


### [S02-016] - 2026-07-07
**Objective:** handle_ws_message kurang validasi tipe dict untuk 'data'

- **Deskripsi:** Melindungi *downstream handler* websoket dari *AttributeError* apabila klien mengirimi parameter `data` berformat non-dictionary. Implementasi perlindungan tambahan pada *router* utama pesan websoket mensyaratkan `isinstance(data, dict)`; jika bukan, payload otomatis diganti ke dictionary kosong `{}` sembari memunculkan peringatan (BUG-B11).
- **File Diubah:** 
  - `server/handlers/websocket.py` (Modified)
  - `tests/unit/server/test_ws_data_type.py` (New Test)
- **Status Testing:** ✓ Lulus validasi ketahanan *handler* terhadap muatan *payload data* berupa string.


### [S02-015] - 2026-07-07
**Objective:** VolumeService.current_volume desync dari state.volume

- **Deskripsi:** Menghilangkan redundansi dan *race condition* pada pengaturan volume. Variabel bayangan `self.current_volume` yang rawan usang pada `VolumeService` telah dihapus. Seluruh operasi manipulasi/penyesuaian volume (`_on_volume_up`, `_on_volume_down`, dan `_on_volume_set`) sekarang langsung beroperasi di atas mutasi nilai otoritatif `self.state.volume` dengan proteksi serial `asyncio.Lock` guna melindunginya dari modifikasi serentak ganda (BUG-B10).
- **File Diubah:** 
  - `engine/volume_service.py` (Modified)
  - `tests/unit/engine/test_volume_service.py` (New Test)
- **Status Testing:** ✓ Lulus validasi penangkalan korupsi data *race condition* atas bombardir *event trigger* bersamaan.


### [S02-014] - 2026-07-07
**Objective:** _poll_duration menerbitkan QueueUpdatedEvent meskipun durasi gagal

- **Deskripsi:** Mencegah penerbitan _event_ `QueueUpdatedEvent` secara mubazir manakala kegagalan pengambilan durasi (*poll_duration* bernilai `None`) terjadi secara beruntun pada blok _fallback_. Notifikasi ke sistem kini diwajibkan hanya tereksekusi bila `dur is not None and dur > 0` terpenuhi sepenuhnya di dalam *retry delay* (BUG-B09).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
  - `tests/unit/engine/test_poll_duration.py` (New Test)
- **Status Testing:** ✓ Lulus validasi ketiadaan pemanggilan propagasi event `bus.publish` saat hasil resolusi durasi MPV terdeteksi nihil/gagal.


### [S02-013] - 2026-07-07
**Objective:** on_next memicu bottleneck beruntun karena hold _lock

- **Deskripsi:** Mencegah *bottleneck* I/O pada antrean _event handling_ akibat penguncian yang terlalu lama. Pemanggilan rute asinkron berdurasi panjang `_advance_to_next` dan `play_track` kini ditarik ke luar cakupan pelindung `async with self.playback_controller._lock:` pada modul `PlaybackCommands` agar tidak memblokir lajur instruksi jaringan dan _command handling_ paralel lainnya (BUG-B08).
- **File Diubah:** 
  - `engine/playback/playback_commands.py` (Modified)
  - `tests/unit/engine/test_playback_commands_lock.py` (New Test)
- **Status Testing:** ✓ Lulus validasi ketiadaan akuisisi *lock* pada rute fungsi I/O _play/advance_.


### [S02-012] - 2026-07-07
**Objective:** _lock di PlaybackController dideklarasikan tapi tidak digunakan

- **Deskripsi:** Mengimplementasikan pemakaian mutex `self._lock` di `PlaybackController` untuk memproteksi segala rute modifikasi `self.state` pada saat _event handling_. Blok mutasi state pada fungsi `_on_track_duration`, `_poll_duration`, `_on_track_ended` (rute error), `_on_track_progress`, dan `_on_pause_changed` kini dibungkus dengan klausul `async with self._lock:` untuk mencegah fenomena persaingan data (data race) dan mutasi status serentak (BUG-B07).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
  - `tests/unit/engine/test_playback_controller_lock.py` (New Test)
- **Status Testing:** ✓ Lulus uji verifikasi pemakaian (akuisi) objek Lock.


### [S02-011] - 2026-07-07
**Objective:** _on_track_ended error path: guard if IDLE tidak pernah terpenuhi

- **Deskripsi:** Mengkoreksi logika _guard checking_ pasca-jeda error agar perpindahan antrean otomatis batal jika _state_ dimanipulasi manual. Pengecekan status pada rute `reason == "error"` di `_on_track_ended` direvisi menjadi `if self.state.status != PlayerStatus.ERROR:` agar dapat menangkal intervensi _stop_ (`IDLE`) maupun _next/prev_ (`LOADING`) ganda yang luput dari filter sebelumnya (BUG-B05).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
  - `tests/unit/engine/test_playback_controller_error_guard.py` (New Test)
- **Status Testing:** ✓ Lulus validasi pembatalan _advance_to_next_ manakala mutasi _state_ mendistraksi jeda _sleep_.


### [S02-010] - 2026-07-07
**Objective:** play_track retry backoff membaca _retry_count stale

- **Deskripsi:** Mencegah efek *stale read* dan inkonsistensi durasi pemulihan otomatis (retry backoff delay) pada modul pengendali pemutaran akibat modifikasi eksternal saat status pelepasan *lock*. Variabel statis hitungan retri `_retry_count` kini ditangkap lalu disalin ke variabel lokal `current_retry_count` sesaat sebelum melepas (exit) pelindung mutasi `async with self._play_lock` di rutinitas `play_track` (BUG-B04).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
  - `tests/unit/engine/test_playback_controller_retry.py` (New Test)
- **Status Testing:** ✓ Lulus validasi simulasi modifikasi *data race* sewaktu iterasi sleep (backoff) menggunakan mock.


### [S02-009] - 2026-07-07
**Objective:** _on_track_ended reason kosong "" tidak ditangani — autoplay mati

- **Deskripsi:** Menangani parameter *reason* kosong `""` pada `TrackEndedEvent` agar siklus pemutaran otomatis (autoplay) tidak terhenti di tengah jalan. Menambahkan _fall-through_ yang menangkap variasi *reason* kosong `""` agar disejajarkan dengan `eof`, memastikan MPV senantiasa maju (advance) ke lagu berikutnya pasca-pengakhiran pemutaran. Ditambahkan pula log warning dan fallback `advance` untuk event tak terduga (BUG-B03).
- **File Diubah:** 
  - `engine/playback/controller.py` (Modified)
  - `tests/unit/engine/test_playback_controller_track_ended.py` (New Test)
- **Status Testing:** ✓ Lulus validasi fungsi `advance_to_next` pada kasus `reason` bernilai *empty string* atau parameter tak dikenali.


### [S02-008] - 2026-07-07
**Objective:** handle_auth tidur di dalam global rl_lock — DoS seluruh autentikasi

- **Deskripsi:** Mencegah pemblokiran parsial layanan (DoS) akibat siklus interupsi _blocking_ (tidur) di dalam blok kuncian variabel sinkron. Menyelamatkan eksekusi *asynchronous sleep* (waktu tunda) yang semula terkurung dalam `async with manager.rl_lock:` pada modul otentikasi `server/handlers/auth.py`. Kode telah diekstraksi ke luar cakupan *lock*. Modifikasi ini membuat koneksi yang terkena *delay* rate-limit tidak akan menyeret atau memacetkan *request login* _client_ lain (BUG-B02).
- **File Diubah:** 
  - `server/handlers/auth.py` (Modified)
- **Status Testing:** ✓ Lulus uji _concurrency_ _non-blocking_ auth handler di pytest.


### [S02-007] - 2026-07-07
**Objective:** discover_service KeyError: stream_url tidak di-SELECT

- **Deskripsi:** Memperbaiki insiden hancurnya fitur *Discover* (KeyError) saat mencoba memuat *stream_url*. Modifikasi mencakup injeksi kolom `stream_url` pada skrip sintaks `SELECT` database internal serta pemakaian abstraksi proteksi *fallback* `.get()` pada perakitan kelas model `TrackInfo`. Pembenahan blok *bare exception* turut disertakan dengan membidik galat yang lebih spesifik demi menunjang stabilitas (BUG-B01).
- **File Diubah:** 
  - `server/services/discover_service.py` (Modified)
  - `tests/unit/server/test_discover_service.py` (New Test)
- **Status Testing:** ✓ Lulus pengujian *parsing dict row* via Mock unit test.


### [S02-006] - 2026-07-07
**Objective:** Broadcast state penuh setiap event

- **Deskripsi:** Merombak *handler* untuk _toggle favorite_ yang berlebihan akibat menyiarkan `state.to_dict()` secara global. Skrip diganti menggunakan `manager.broadcast()` yang sekadar meneruskan paket notifikasi parsial tipe `"favorite_status"`. Refaktor ini menyiasati perlintasan beban besar dan menghemat utilisasi *bandwidth* WebSocket tiap kali ada penyematan label favorit (EXEC-016).
- **File Diubah:** 
  - `server/handlers/ws/discover_handlers.py` (Modified)
  - `tests/unit/server/test_ws_discover_broadcast.py` (New Test)
- **Status Testing:** ✓ Lulus validasi simulasi payload via Mock broadcast.


### [S02-005] - 2026-07-07
**Objective:** Memory leak pada _stream_rate_limit

- **Deskripsi:** Menghilangkan batasan panjang ukuran *dictionary rate limit* dan menggantinya dengan iterasi reguler pendeteksi IP kadaluwarsa (berusia lebih dari 60 detik) di rutinitas fungsi `_enforce_rate_limit` (di `server/handlers/http.py`). Hal ini memastikan setiap entri lawas tereliminasi seketika, selaras dengan metode pembersihan yang telah sukses diterapkan pada otentikasi login, sehingga celah kebocoran memori (_memory leak_) akibat penumpukan sampah array historis tertanggulangi (EXEC-013).
- **File Diubah:** 
  - `server/handlers/http.py` (Modified)
  - `tests/unit/server/test_http_rate_limit_prune.py` (New Test)
- **Status Testing:** ✓ Lulus uji _garbage collection rate limiter_ dengan _mock_ aliran waktu di pytest.


### [S02-004] - 2026-07-07
**Objective:** Nilai MAX_VOLUME melebihi batas

- **Deskripsi:** Menstandarkan fungsi *clamping* pada class `Volume` di `core/value_objects.py`. Angka `100` yang _hardcoded_ telah diubah menjadi import langsung dari `MAX_VOLUME` (`core.constants.py`). Solusi ini menyamakan toleransi maksimum untuk menghindari _bug_ input saat slider *volume* klien diset mencapai 150 (EXEC-012).
- **File Diubah:** 
  - `core/value_objects.py` (Modified)
  - `tests/unit/core/test_value_objects.py` (New Test)
- **Status Testing:** ✓ Lulus uji testing unit batas parameter value object.


### [S02-003] - 2026-07-07
**Objective:** http_session tidak diinjeksikan

- **Deskripsi:** Menambahkan pengiriman (passing) instansi *object* `http_session` dari saat deklarasi di `bootstrap.py` menjadi _keyword argument_ menuju `create_app` di modul `server/app.py`. Integrasi ini menghentikan instansiasi fallback `None` pada rute proxy sehingga lalu lintas stream media _client-side_ termanajemen dengan benar oleh satu *http session pool* tunggal terpusat (EXEC-005).
- **File Diubah:** 
  - `server/app.py` (Modified)
  - `core/bootstrap.py` (Modified)
  - `tests/unit/server/test_app_http_session.py` (New Test)
- **Status Testing:** ✓ Lulus uji _key injection_ ke internal `web.Application`.


### [S02-002] - 2026-07-07
**Objective:** Import time di baris terakhir file mpv_controller.py

- **Deskripsi:** Memindahkan baris `import time` yang sebelumnya terlempar di baris paling bawah kode `mpv_controller.py` menuju ke blok *top-level import* di awal file. Perbaikan ini mengikuti standar PEP-8 sekaligus menghilangkan celah *NameError* yang bisa muncul bila instance class memanggil `time` sebelum interpretasi baris akhir dieksekusi (EXEC-004).
- **File Diubah:** 
  - `engine/mpv_controller.py` (Modified)
  - `tests/unit/test_mpv_controller_init.py` (New Test)
- **Status Testing:** ✓ Lulus uji inisialisasi class via pytest.


### [S02-001] - 2026-07-07
**Objective:** AppState adalah mutable shared state global

- **Deskripsi:** Menambahkan penguncian state bawaan pada dataclass `AppState` (`asyncio.Lock`) di `core/state.py`. Hal ini memungkinkan akses thread-safe pada _coroutine handler_ WebSocket seperti `discover_handlers.py` saat hendak memodifikasi parameter mutasi state global (seperti `current_track.is_favorite`) demi menangkal _race condition_ (EXEC-001).
- **File Diubah:** 
  - `core/state.py` (Modified)
  - `server/handlers/ws/discover_handlers.py` (Modified)
  - `tests/unit/core/test_state_lock.py` (New Test)
- **Status Testing:** ✓ Teruji unit test eksistensi objek Lock pada _instance_ class.


### [S01-021] - 2026-07-07
**Objective:** admin_password.txt Disimpan dalam Plaintext Hash Tanpa Enkripsi Tambahan

- **Deskripsi:** Memitigasi risiko keamanan eksposur *file directory* (seperti *zip traversal*) dengan memindahkan file kredensial persisten `admin_password.txt` (termasuk *initial password* sementara) di `config.py` dari `/cache` ke folder operasi terlindungi `/data`. Skrip akan secara otomatis memigrasikan fail lama saat server direstart jika sebelumnya pernah tersimpan di cache (DEVOPS-013).
- **File Diubah:** 
  - `config.py` (Modified)
  - `tests/unit/test_config_password.py` (Modified)
- **Status Testing:** ✓ Teruji via pytest (mengonfirmasi pembuatan file berlangsung di struktur tree /data).


### [S01-020] - 2026-07-07
**Objective:** Volume Docker Hanya Mount /app/data, Cache dan Logs Hilang Saat Restart

- **Deskripsi:** Memperbaiki konfigurasi `docker-compose.yml` yang abai me-mount direktori penting `/app/cache`. Direktori ini krusial untuk menyimpan token password awal, daftar putar sisa, serta file log. Modifikasi memastikan _bind mount_ untuk cache terpetakan sempurna (DEVOPS-004).
- **File Diubah:** 
  - `docker-compose.yml` (Modified)
  - `tests/unit/test_docker_compose.py` (New Test)
- **Status Testing:** ✓ Teruji via unit test struktural memastikan /app/cache di-binding.


### [S01-019] - 2026-07-07
**Objective:** Mock Strategy Terlalu Longgar di E2E Tests

- **Deskripsi:** Melakukan eskalasi rigoritas pengujian mock autentikasi di `test_e2e.py`. Penggunaan return absolute `True` pada `verify_session` diganti dengan side effect realistis yang secara spesifik mensyaratkan token `'valid-token'`. Integrasi pengujian juga di-refaktor untuk mengakomodasi penambahan skenario test token _invalid_ guna menjamin _rejection_ saat ada upaya intrusi token palsu (AUDIT-TEST-011).
- **File Diubah:** 
  - `tests/integration/test_e2e.py` (Modified)
- **Status Testing:** ✓ Teruji via pytest (seluruh 7 test E2E lulus secara fungsional).


### [S01-018] - 2026-07-07
**Objective:** Login Form: Tidak Ada <label> pada Input Fields

- **Deskripsi:** Menambahkan elemen pelabelan `<label for="...">` pada input otentikasi di file UI `index.html`. Modifikasi ini disandingkan dengan *class* CSS khusus `.visually-hidden` di `portal.css` sehingga teks peruntukan kotak (seperti "Username" / "Password") tak mengubah *layout* fisik, tapi terbaca utuh oleh aplikasi *screen reader* (aksesibilitas disabilitas) (FE-006).
- **File Diubah:** 
  - `web/static/index.html` (Modified)
  - `web/static/css/portal.css` (Modified)
  - `tests/unit/test_html_labels.py` (New Test)
- **Status Testing:** ✓ Teruji via unit test (memastikan tag label for="admin-*" exist).


### [S01-017] - 2026-07-07
**Objective:** /metrics Menggunakan Custom Header X-Metrics-Token (Non-Standard)

- **Deskripsi:** Refaktor rute API Prometheus `/metrics` di `server/handlers/http.py`. Skema eksklusif `X-Metrics-Token` dirombak dan disejajarkan dengan standar autentikasi HTTP lazim `Authorization: Bearer <token>` guna memastikan kompatibilitas penuh dengan sistem pengeruk eksternal. (API-16).
- **File Diubah:** 
  - `server/handlers/http.py` (Modified)
  - `tests/unit/server/test_metrics_auth.py` (New Test)
- **Status Testing:** ✓ Unit test berhasil. Memverifikasi jika Bearer token kosong, atau token tidak match, server merespons HTTP 403 Forbidden.


### [S01-016] - 2026-07-07
**Objective:** Admin Password Tidak Tercetak di Non-TTY Environment

- **Deskripsi:** Mengganti mekanisme pencetakan password inisial di `config.py` dari `sys.stderr` ke file temporary. Hal ini menyelesaikan dua *issue* sekaligus: mencegah password plaintext terekam di file log (seperti `startup.log` di Termux), dan memastikan admin tetap bisa mengakses password baru saat di-deploy di dalam lingkungan Docker atau SystemD (*non-TTY*) via berkas `cache/admin_initial_password.txt`. Pesan pemberitahuan lokasi file tetap diprint dengan aman.
- **File Diubah:** 
  - `config.py` (Modified)
  - `tests/unit/test_config_password.py` (New Test)
- **Status Testing:** ✓ Teruji secara unit test (pytest) untuk membuktikan file initial password ter-generate dan dapat diakses.


### [S01-015] - 2026-07-07
**Objective:** Form Validation: Login Submit dengan Enter Hanya dari Password Field

- **Deskripsi:** Menambahkan fungsionalitas penekanan tombol *Enter* (submit action) pada bidang input *Username*. Kode `addEventListener("keypress", ...)` baru dilekatkan pada `dom.adminUsername` di dalam `web/static/js/events/index.js` guna menyamakan *behavior* dengan field *Password* (FE-013).
- **File Diubah:** 
  - `web/static/js/events/index.js` (Modified)
  - `web/static/js/bundle.js` (Compiled)
  - `tests/unit/test_js_login_enter.py` (New Test)
- **Status Testing:** ✓ Teruji secara statis memastikan event keypress Enter divalidasi ke elemen input adminUsername.


### [S01-014] - 2026-07-07
**Objective:** Dark Mode: Aplikasi Hanya Mendukung Dark, Tidak Ada Light Mode Support

- **Deskripsi:** Menambahkan kompatibilitas preferensi tema (Light/Dark mode). Menulis variabel override skema warna CSS yang mengikuti mode cerah sistem lewat media query `@media (prefers-color-scheme: light)` pada `web/static/css/tokens.css`. Atribut `color-scheme` juga disematkan agar browser menangani fallback UI standar dengan tepat (FE-008).
- **File Diubah:** 
  - `web/static/css/tokens.css` (Modified)
  - `tests/unit/test_css_light_mode.py` (New Test)
- **Status Testing:** ✓ Lulus validasi struktural (statis test Python memverifikasi eksistensi kueri media dan preferensi *color-scheme*).


### [S01-013] - 2026-07-07
**Objective:** Tidak Ada Pagination untuk Search Results

- **Deskripsi:** Melakukan *refactor* pada data kembalian hasil pencarian di `server/handlers/ws/discover_handlers.py`. Yang sebelumnya mereturn *Array list tunggal* kini beralih menjadi format *object* terstruktur yang menyimpan metadata `items`, `next_page_token`, dan `total_count`. Perbaikan *frontend* dilakukan di `renderSearchResults` secara *backward-compatible* sehingga sanggup mem-parsing baik bentuk *object* baru maupun balasan lama.
- **File Diubah:** 
  - `server/handlers/ws/discover_handlers.py` (Modified)
  - `web/static/js/render/search.js` (Modified)
  - `web/static/js/bundle.js` (Compiled)
  - `tests/unit/server/test_search_pagination.py` (New Test)
- **Status Testing:** ✓ Teruji via unit test (simulasi JSON payload WebSocket search). Fungsi `search.js` telah teruji *backward-compatible*.


### [S01-012] - 2026-07-07
**Objective:** /api/stream/{video_id} Tidak Memerlukan Autentikasi

- **Deskripsi:** Menambahkan pengamanan autentikasi pada rute publik `/api/stream/{video_id}`. Rute ini sekarang mewajibkan penyertaan *query parameter* `?token=` yang divalidasi keaktifannya melalui database. Akses dari IP eksternal (bukan localhost) tanpa token akan ditolak dengan respons HTTP 401 Unauthorized, mengatasi kerentanan *HTTP Stream Hijacking* (API-02).
- **File Diubah:** 
  - `server/handlers/http.py` (Modified)
  - `web/static/js/audio.js` (Modified)
  - `web/static/js/bundle.js` (Modified)
  - `tests/unit/server/test_stream_auth.py` (New Test)
  - `tests/unit/test_http_cors.py` (Updated Test)
- **Status Testing:** ✓ Teruji via unit test dengan skenario IP eksternal (401 Unauthorized), Token Valid (200 OK), dan Localhost fallback (200 OK).


### [S01-011] - 2026-07-07
**Objective:** verify_session(): Side Effect Write dalam Read Operation

- **Deskripsi:** Menghapus *side-effect* operasi penghapusan sesi (delete) di dalam fungsi *query* `verify_session()` di `cache/repositories/auth_repository.py`. Sebelumnya, fungsi tersebut menghapus sesi secara sembunyi-sembunyi saat memvalidasi sesi kedaluwarsa. Perbaikan ini menegakkan asas CQRS (*Command-Query Responsibility Segregation*), memisahkan tugas bersih-bersih murni ke `cleanup_sessions()`. (DB-013).
- **File Diubah:** 
  - `cache/repositories/auth_repository.py` (Modified)
- **Status Testing:** ✓ Teruji via unit testing penuh. 86 tests lolos tanpa ada disrupsi fungsional.


### [S01-010] - 2026-07-07
**Objective:** sessions Table: Tidak Ada Index pada expires_at

- **Deskripsi:** Menambahkan B-Tree Index `idx_sessions_expires_at` pada kolom `expires_at` tabel `sessions` di `cache/schema.sql`. Hal ini mencegah lambatnya query database (*Full Table Scan*) ketika script membersihkan session login admin yang kadaluarsa (DB-008).
- **File Diubah:** 
  - `cache/schema.sql` (Modified)
  - `tests/unit/test_schema_indexes.py` (New)
- **Status Testing:** ✓ Teruji secara statis memastikan schema.sql memiliki perintah `CREATE INDEX IF NOT EXISTS`.


### [S01-009] - 2026-07-07
**Objective:** Service Worker Precache 20+ File CSS Terpisah (Tidak Perlu)

- **Deskripsi:** Memperbaiki file `web/static/sw.js` dengan memangkas daftar panjang aset CSS dari *array* `PRECACHE_ASSETS`. Karena CSS yang ditarget akan dilayani secara dinamis oleh dynamic caching, mem-precache mereka satu-satu di awal akan mengirimkan puluhan HTTP request secara masif. Kini, *array* hanya berisi berkas esensial, memperbaiki isu pemborosan *bandwidth* (PERF-P13).
- **File Diubah:** 
  - `web/static/sw.js` (Modified)
  - `tests/unit/test_sw.py` (New)
- **Status Testing:** ✓ Telah diuji dengan script parsing AST sederhana yang memastikan panjang array `PRECACHE_ASSETS` kurang dari atau sama dengan 5. Test berhasil dijalankan.


### [S01-008] - 2026-07-07
**Objective:** Method handle_auth memiliki siklus proses berlapis (Long Method)

- **Deskripsi:** Melakukan ekstraksi (*Extract Method*) pada metode `handle_auth` di `server/handlers/auth.py`. Fungsi yang memuat banyak proses berlapis (verifikasi sesi, rate-limit, validasi kredensial, DB ops) ini dipecah menjadi tiga fungsi helper independen: `_verify_token`, `_check_rate_limit`, dan `_process_credentials`. Struktur kode kini lebih kohesif, mengurangi kompleksitas *cyclomatic*, dan memperjelas pembacaan logika tanpa memodifikasi kapabilitas intinya.
- **File Diubah:** 
  - `server/handlers/auth.py` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, 84 unit test berhasil berjalan tanpa regresi sama sekali.


### [S01-007] - 2026-07-07
**Objective:** serve_stream bertindak sebagai God Function

- **Deskripsi:** Melakukan refactor pada _God Function_ `serve_stream` di `server/handlers/http.py`. Fungsi tunggal yang membengkak sepanjang ~150 baris kini telah dipecah menjadi beberapa fungsi bantuan spesifik: `_enforce_rate_limit`, `_validate_origin`, `_get_cors_origin`, `_try_serve_cache`, `_validate_stream_url`, dan `_proxy_stream`. Modifikasi ini mengisolasi logika HTTP routing dan membuat proxy stream lebih mudah dipelihara (maintainability meningkat).
- **File Diubah:** 
  - `server/handlers/http.py` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, unit test `tests/unit/test_http_cors.py` dan `tests/unit/test_http_rate_limit.py` berhasil pass tanpa regresi.


### [S01-006] - 2026-07-07
**Objective:** Penggunaan tag export di dalam file berarsitektur classic script

- **Deskripsi:** Menghapus keyword `export` pada fungsi `_resumeAndPlay` di `audio.js` karena frontend ini berjalan sebagai classic script, bukan ESM (module). Hal ini mengatasi `SyntaxError: Unexpected token 'export'` yang terjadi ketika script dijalankan secara langsung.
- **File Diubah:** 
  - `web/static/js/audio.js` (Modified)
  - `web/static/js/bundle.js` (Modified)
  - `tests/test_audio.html` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, test berhasil memverifikasi fungsi termuat tanpa `SyntaxError`.


### [S01-005] - 2026-07-07
**Objective:** WebSocket di-expose ke global scope window

- **Deskripsi:** Melakukan refactor pada `ws.js` dengan membungkus logika WebSocket di dalam closure (IIFE) dan menghapus `window.ws = ws`. Hal ini mencegah objek WebSocket mentah terekspos ke scope `window` global, menutup kerentanan XSS dan manipulasi state. Dibuat test `test_ws.html` untuk memverifikasi enkapsulasi ini.
- **File Diubah:** 
  - `web/static/js/ws.js` (Modified)
  - `web/static/js/bundle.js` (Modified)
  - `tests/test_ws.html` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, test berhasil memverifikasi enkapsulasi WebSocket.


### [S01-004] - 2026-07-07
**Objective:** X-Forwarded-For rentan di-spoof

- **Deskripsi:** Memperbaiki penguraian _header_ `X-Forwarded-For` ketika `TRUSTED_PROXY=true` untuk selalu mengambil IP terakhir (`split(",")[-1]`) yang di-_append_ oleh _proxy_ tepercaya di hadapan aplikasi, alih-alih mengambil IP yang paling kiri (`split(",")[0]`) yang dapat dikontrol sesuka hati oleh penyerang (IP spoofing bypass rate-limit).
- **File Diubah:** 
  - `server/handlers/websocket.py` (Modified)
  - `tests/unit/test_websocket_xff.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, `[-1]` dieksekusi benar.


### [S01-003] - 2026-07-07
**Objective:** Logout tidak invalidasi session di server

- **Deskripsi:** Task ini telah diselesaikan berbarengan dengan pengerjaan task **S01-002**. Invalidasi sesi di database melalui WS command `LOGOUT` sudah diimplementasikan (memanggil `await db.delete_session(token)`).
- **File Diubah:** 
  - *Tergabung dalam S01-002*
- **Status Testing:** ✓ Sudah di-test dan selesai bersamaan dengan S01-002.


### [S01-002] - 2026-07-07
**Objective:** Tidak ada rotasi token session & invalidasi pada saat logout

- **Deskripsi:** Menambahkan ukuran enkripsi token autentikasi dari `16 bytes hex` (128-bit) menjadi `32 bytes hex` (256-bit) di `secrets.token_hex(32)`. Serta mengimplementasikan WS action handler baru `WSAction.LOGOUT` yang membersihkan `ytgui_session_token` dari database secara *server-side* pada saat user logout dari frontend.
- **File Diubah:** 
  - `core/ws_actions.py` (Modified)
  - `server/handlers/auth.py` (Modified)
  - `server/handlers/websocket.py` (Modified)
  - `web/static/js/services/auth.js` (Modified)
  - `tests/unit/test_auth_rotation.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, `handle_logout` di-cover oleh test, `32 bytes` (panjang 64 char) terverifikasi.


### [S01-001] - 2026-07-07
**Objective:** CORS wildcard pada endpoint audio

- **Deskripsi:** Menghilangkan `Access-Control-Allow-Origin: *` pada endpoint audio streaming (`serve_stream`) dan menggantinya dengan origin/skema spesifik yang memanggilnya, selaras dengan validasi origin yang sudah ada sebelumnya. Hal ini mencegah audio diekstrak atau di-embed oleh sembarang domain yang tidak sah (mencegah pencurian bandwidth).
- **File Diubah:** 
  - `server/handlers/http.py` (Modified)
  - `tests/unit/test_http_cors.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, `Access-Control-Allow-Origin` terverifikasi dinamis.


### [S00-005] - 2026-07-07
**Objective:** Tidak Ada Sistem Alerting Sama Sekali

- **Deskripsi:** Mengimplementasikan modul `core/alerting.py` untuk menangkap _unhandled exception_ secara global (melalui `sys.excepthook`) dan event loop errors di asyncio, kemudian mengirimkan notifikasi SOS darurat via HTTP POST ke webhook URL Discord/Slack (environment `LUNAWAVE_ALERT_WEBHOOK`) apabila terjadi server crash, menghapus kebutaan operasional saat server down tiba-tiba.
- **File Diubah:** 
  - `core/alerting.py` (Added)
  - `main.py` (Modified)
  - `tests/unit/test_alerting.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, unit test berhasil mensimulasikan panggilan webhook dan fungsi penangkapan error.


### [S00-004] - 2026-07-07
**Objective:** Tidak Ada Proses Release Formal (Single Source of Truth)

- **Deskripsi:** Menghapus hardcode versi `1.0.0` pada `main.py` dan menggantinya dengan logika pembacaan file `pyproject.toml` menggunakan library bawaan python 3.11+ `tomllib`. Versi project kini tersinkronisasi dan diatur sepenuhnya via `pyproject.toml` sebagai _single source of truth_.
- **File Diubah:** 
  - `main.py` (Modified)
  - `tests/unit/test_version.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, test berhasil membaca string `0.1.0`.


### [S00-001] - 2026-07-07
**Objective:** Sangat sedikit test functions (test_queue_locking)

- **Deskripsi:** Melakukan refactor pada file `tests/unit/engine/test_queue_locking.py` yang sebelumnya hanya mem-parsing source code (`inspect.getsource`) menjadi unit test sungguhan dengan menggunakan object `AsyncMock` dan instansiasi `QueueCommands` serta `PlaybackCommands` agar memverifikasi logika runtime lock `async with self.playback_controller._lock` berjalan semestinya.
- **File Diubah:** 
  - `tests/unit/engine/test_queue_locking.py` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, 3 fungsi test berhasil lewat.


### [S00-003] - 2026-07-07
**Objective:** Missing Index untuk Favorites Query

- **Deskripsi:** Menambahkan partial index SQL `idx_is_favorite` (`WHERE is_favorite = 1`) pada tabel `tracks` di `cache/schema.sql` dan `cache/db.py` untuk menghilangkan kendala full-table scan pada query pengambilan daftar lagu favorit, sehingga pencarian ratusan item lebih cepat dan aman secara performa.
- **File Diubah:** 
  - `cache/schema.sql` (Modified)
  - `cache/db.py` (Modified)
  - `tests/unit/cache/test_db_index.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, test berhasil.


### [S00-002] - 2026-07-07
**Objective:** Rate limit state tersimpan di in-memory (Memory Leak)

- **Deskripsi:** Menambahkan mekanisme garbage collection untuk dictionary `_stream_rate_limit` pada route `serve_stream`. Dict akan di-prune dari IP usang (usia data > 60 detik) saat entri melampaui 1000 items, dan akan di-clear paksa bila melebihi 5000 items untuk mencegah memory leak yang berkepanjangan pada long-running server.
- **File Diubah:** 
  - `server/handlers/http.py` (Modified)
  - `tests/unit/test_http_rate_limit.py` (Added)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman, test berhasil.


### [S00-007] - 2026-07-07
**Objective:** Python Version Inconsistency di Tiga Tempat

- **Deskripsi:** Menyeragamkan target Python Version menjadi 3.12 di pyproject.toml, .github/workflows/ci.yml, dan memastikan selaras dengan Dockerfile yang sudah menggunakan 3.12.
- **File Diubah:** 
  - `pyproject.toml` (Modified)
  - `.github/workflows/ci.yml` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman.


### [S00-008] - 2026-07-07
**Objective:** syncedlyrics 1.0.1 Potensi Breaking API

- **Deskripsi:** Mengganti blok 'bare except' / Exception generik dengan penangkapan tipe error spesifik (ValueError, KeyError, TypeError, dll.) untuk mengantisipasi kegagalan parsing lirik apabila API third-party web berubah, serta meningkatkan level logging (dari sekadar print/debug menjadi warning/error dengan exc_info).
- **File Diubah:** 
  - `plugins/lyrics.py` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman.


### [S00-010] - 2026-07-07
**Objective:** Inkonsistensi Prefix Environment Variable (3 Skema Berbeda)

- **Deskripsi:** Menyeragamkan seluruh awalan Environment Variable menjadi `LUNAWAVE_*` di seluruh konfigurasi, script bash/batch, dan documentasi environment (.env.example) guna menghindari kebingungan konfigurasi.
- **File Diubah:** 
  - `config.py` (Modified)
  - `start.sh` (Modified)
  - `start.bat` (Modified)
  - `.env.example` (Modified)
  - `engine/mpv_controller.py` (Modified)
  - `scripts/monitor_health.sh` (Modified)
  - `scripts/monitor_health.ps1` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman.


### [S00-006] - 2026-07-07
**Objective:** CDN External tanpa Subresource Integrity (SRI)

- **Deskripsi:** Menambahkan atribut integrity (SRI hash) dan crossorigin="anonymous" pada link eksternal jsdelivr di index.html untuk font tabler-icons guna mencegah supply chain attack.
- **File Diubah:** 
  - `web/static/index.html` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman.


### [S00-009] - 2026-07-07
**Objective:** Dockerfile Mereferensikan run.py yang Tidak Ada

- **Deskripsi:** Mengubah referensi run.py menjadi main.py pada CMD eksekusi Dockerfile.
- **File Diubah:** 
  - `Dockerfile` (Modified)
- **Status Testing:** ✓ Sudah di-test, lolos validasi, build aman.


### [Contoh-S00-001] - 2024-01-01
**Objective:** Contoh penulisan changelog.

- **Deskripsi:** Menambahkan format kerangka dasar untuk CHANGELOG.md.
- **File Diubah:** 
  - `audit/LOG/CHANGELOG.md` (Modified)
- **Status Testing:** ✓ Sudah di-test dan selesai tanpa kendala.