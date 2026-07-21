---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-20-135

total_entries: 135

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Versi format:** v2 (field-based) — bermigrasi dari v1 (prosa bebas) pada 2026-07-20. Entry hasil migrasi bertanda `Status: Unclassified` dan menyimpan isi Ringkasan v1 apa adanya, utuh, di field `Notes` -- tidak ada fakta teknis yang hilang atau diringkas saat migrasi.

> **ID:** setiap entri wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit), sekarang jadi heading `## PATCH-...` -- satu-satunya sumber judul per entry.

> **Field:** Tanggal, Timestamp, Git Branch, Git Commit, Type, Area, Priority, Title, Reason, Root Cause, Solution, Changed Files, Changed Symbols, Tests, Breaking Change, Regression Risk, Related Patch, Status, Notes -- urutan selalu sama di semua entry. Lihat `automation/patchlog.py` untuk definisi & CLI lengkap.

---

## PATCH-2026-07-20-135

**Tanggal:** 2026-07-20
**Timestamp:** 22:54
**Git Branch:** -
**Git Commit:** -
**Type:** Refactor
**Area:** Tooling
**Priority:** High
**Title:** Migrasi PATCHLOG.md ke format v2 field-based + refactor patchlog.py

**Reason:** Format v1 (prosa bebas per-entry) sulit di-grep presisi, duplikasi heading vs Ringkasan, tidak ada field terstruktur (Type/Area/Priority/Changed Symbols/dst.) -- lihat evaluasi di PATCHLOG_REDESIGN.md.

**Root Cause:**
Format v1 menjejalkan seluruh alasan/root-cause/proses investigasi/fix/hasil-test/edge-case ke dalam satu field Ringkasan prosa bebas, sekaligus diulang di heading -- rata-rata 684 karakter per entry, ~45% dari total isi file, tidak bisa di-query per kategori (mis. grep root cause tanpa noise), dan tidak ada field terstruktur (Type/Area/Priority/Changed Symbols/Breaking Change/Regression Risk/Status/Related Patch) walau info itu kadang disebut naratif.

**Solution:**
Ganti ke format v2: heading per-ID (## PATCH-...) sebagai satu-satunya sumber judul, diikuti field eksplisit (Tanggal/Timestamp/Git Branch/Git Commit -- auto; Type/Area/Priority -- semi-otomatis; Title/Reason/Root Cause/Solution/Changed Symbols/Tests/Breaking Change/Regression Risk/Related Patch/Status/Notes -- manual). Migrasi 134 entry v1 dikerjakan mekanis lewat automation/migrate_patchlog_v2.py (skrip sekali-jalan, dibuang setelah dipakai): Title = kalimat pertama Ringkasan lama (potong di '.'/'—' pertama, <=100 char), seluruh Ringkasan lama dipindah verbatim ke Notes (tidak dipecah otomatis ke Root Cause/Solution -- itu butuh pemahaman makna, berisiko salah kalau dikerjakan mesin), Type/Area/Priority/Status/Breaking Change/Regression Risk diisi 'Unclassified' (jujur menandakan belum diklasifikasi, bukan ditebak). Diverifikasi 0 mismatch antara 134 entry v1 vs v2 (ID/tanggal/files/isi Ringkasan-ke-Notes identik). patchlog.py direfactor: parsing regex generik FIELD_RE (satu pola untuk semua field, bukan regex per-field), _split_into_chunks() dipertahankan apa adanya (sudah teruji), CLI add baru dengan flag lengkap + fallback $EDITOR untuk field panjang, subcommand symbol baru untuk query Changed Symbols, verify() ditambah pengecekan enum. doc_parsing_utils.PATCH_ID_RE & checks_docs.py diupdate mengikuti heading baru.

**Changed Files:**
- `docs/PATCHLOG.md`
- `automation/patchlog.py`
- `automation/verify_docs/doc_parsing_utils.py`
- `automation/verify_docs/checks_docs.py`
- `tests/unit/automation/test_patchlog.py`
- `tests/unit/automation/test_find_owner_and_context_pack.py`

**Changed Symbols:**
- `parse_entry_fields()`
- `ENTRY_HEADING_RE`
- `FIELD_RE`
- `ENUM_FIELDS`
- `render_entry()`
- `suggest_area()`
- `PATCH_ID_RE`

**Tests:** pytest tests/unit/automation (33/33), python automation/doctor.py --strict (5/5 PASS 100), python automation/patchlog.py verify (134/134 parsed, 0 invalid enum)

**Breaking Change:** No

**Regression Risk:** Low

**Related Patch:** -

**Status:** Merged

**Notes:**
hotspot.py dan context_pack.py (consumer parse_entries()) tidak diubah -- kontrak id+files dipertahankan. Test fixture di test_find_owner_and_context_pack.py diupdate ke format v2. Field Git Branch/Git Commit/Timestamp untuk 134 entry migrasi diisi '-' (tidak tersedia untuk histori lama, bukan ditebak).

---

## PATCH-2026-07-20-134

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** pause_race_condition_fix

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/events/transport-events.js`
- `web/static/js/audio/playback-sync.js`
- `tests/frontend/pause-race.test.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
pause_race_condition_fix — FIX-PAUSE-RACE-01: pause auto-play lagi sendiri di jaringan jelek (dilaporkan user, dikonfirmasi lewat eksekusi kode asli sebelum patch). Root cause: optimistic UI update (klik pause -> store.status="PAUSED" instan) dilindungi grace-window waktu TETAP (window.lastToggleTime, 1200ms di ws.js utk progress message, 1500ms terpisah di playback-sync.js utk native pause/play event) yang tujuannya nolak update status server yang datang sebelum server sempat memproses toggle kita. Di jaringan flaky, RTT sering > grace-window itu, jadi progress broadcast BASI (msg.data.status masih status lama, dari sebelum server proses toggle) lolos dan menimpa balik store.status yang baru saja di-set user -> cabang FIX-RADIO-08 di ws.js (awalnya utk recover autoplay-block radio) melihat "status PLAYING tapi audio.paused" -> panggil _resumeAndPlay(audio) tanpa gesture user -> audio kedengaran lanjut main sendiri sebentar sampai broadcast progress yang valid tiba dan mengoreksi lagi. Dikonfirmasi lewat harness Node (vm) yang me-load ws.js + playback-sync.js ASLI (bukan tulis ulang) dan mensimulasikan klik-pause lalu progress basi tiba di t=2000ms: store.status berbalik ke PLAYING dan audio.play() benar-benar terpanggil. Klaim awal soal "ping-pong wsSend ke server" DICABUT setelah diuji — tidak terjadi, karena guard di listener native play sudah anggap store.status === "PLAYING" (sudah kadung ketimpa) jadi tidak resend. Fix: ganti grace-window berbasis WAKTU dengan pending-target tracking (markPendingToggle(target) + isPendingToggleActive(matchStatus) di store.js) — client melacak status APA yang sedang ditunggu konfirmasinya, dan menolak update dari server yang KONTRADIKTIF dengan target itu selama masih menunggu (bukan cuma "belum lewat sekian ms"), dengan safety-valve PENDING_TOGGLE_TIMEOUT_MS=8 detik supaya tidak macet permanen kalau command toggle kita sendiri hilang di jalan. 4 titik yang tadinya manual set window.lastToggleTime (klik tombol pause di transport-events.js; native pause listener, native play listener, dan Media Session _optimisticToggle di playback-sync.js) disatukan lewat helper markPendingToggle() yang sama, menutup inkonsistensi 1200ms vs 1500ms sekaligus. Verifikasi: regression test baru tests/frontend/pause-race.test.js (3 test) jalan terhadap modul ASLI (store.js + ws.js, bukan simulasi) — dibuktikan dua arah: gagal saat logika lama dipasang balik sementara (bug beneran kedeteksi), lulus dengan patch terpasang. Suite lengkap: 19/19 test lulus (ws-routing, store, format, pause-race), tidak ada regresi. Ditemukan juga edge case pas review lanjutan: kalau user pause lalu SEBELUM konfirmasi server datang langsung klik next/prev/pilih track lain, pendingToggleTarget="PAUSED" yang basi ikut nyangkut dan bikin progress message track BARU (LOADING -> PLAYING) salah dianggap kontradiktif -> status macet di LOADING sampai safety-valve 8 detik habis. Fix: wsSend() di ws.js (satu-satunya jalur semua command ke server) clear pendingToggleTarget kalau action-nya next/prev/play_track -- otomatis berlaku ke semua caller (tombol transport, keyboard shortcut, klik track di search/queue, Media Session). Dikonfirmasi reproduksi bug dulu (status stuck di LOADING) dan fix-nya (status lanjut ke PLAYING) lewat harness Node terpisah sebelum ditambahkan sbg test ke-4 di pause-race.test.js. Suite lengkap sekarang 20/20 lulus.

---

## PATCH-2026-07-20-133

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** starfield_and_discover_scrollbar: tambah ambient starfield pure-CSS site-wide + theming scrollbar D…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/css/layout/app-shell.css`
- `web/static/css/components/discover-cards.css`
- `web/static/css/platform/desktop.css`
- `web/static/css/platform/landscape.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
starfield_and_discover_scrollbar: tambah ambient starfield pure-CSS site-wide + theming scrollbar Discover tab. (1) #content-area (app-shell.css) dikasih background-image 8x radial-gradient kecil (warna rgba(154,160,170,x) sama kaya .radio-hero .star, opacity 0.2-0.35), di-tile 220px x 220px, statis tanpa animasi -- muncul di belakang semua tab (Home/Search/Radio/Discover) tanpa markup baru, index.html tidak disentuh sama sekali (masih locked). Sesi sebelumnya sempat merencanakan pendekatan ini tapi editnya tidak pernah benar-benar tersimpan ke file -- diverifikasi ulang dari awal sebelum implementasi. (2) Scrollbar #tab-discover (discover-cards.css): ditambah ::-webkit-scrollbar (thumb 8px rounded var(--border-3), hover var(--text-3)) + scrollbar-width:thin/scrollbar-color untuk Firefox, gantiin scrollbar default browser yang tidak sesuai tema gelap. (3) Fix 'kurang mentok kanan': #tab-discover scroll sendiri terpisah dari #content-area, tapi ikut aturan .tab-panel (max-width:1200px/1000px + margin auto + padding 40px/32px) sehingga scrollbar jatuh ~79px dari tepi browser asli. Di desktop.css (min-width:1024px) dan landscape.css (tablet landscape), constraint itu dilepas khusus dari #tab-discover sendiri (max-width:none, margin:0, padding hanya bottom 120px untuk player-bar clearance) dan dipindah ke #tab-discover > * (max-width 1200px/1000px + margin auto), memanfaatkan pola existing yang sudah ada di codebase dimana semua direct children #tab-discover (discover-header, taste-block, filter-bar, card-row, section-label-row, sr-item, dst) sudah punya padding horizontal var(--s5)=20px sendiri -- diverifikasi satu-satu lewat grep sebelum implementasi, jadi #discover-cached (satu-satunya child tanpa padding sendiri) tetap aman karena children di dalamnya (.sr-item) juga sudah self-inset. Hasil: scrollbar sekarang flush ke tepi browser, layout visual anak-anaknya tidak berubah. Verifikasi: review manual cascade CSS baris-per-baris (spesifisitas ID vs class + !important); percobaan live-render via Playwright headless gagal karena sandbox network memblokir koneksi localhost (bukan masalah CSS), jadi tidak ada screenshot before/after -- disarankan dicek ulang di browser nyata.

---

## PATCH-2026-07-20-132

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/css/components/radio-hero.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — HOTFIX (real-device report, screenshot bug): .radio-hero collapse ke sliver ~50px saat Radio ON dengan daftar 'All Stations' terisi. Root cause BUKAN RFC lama (§2, min-height vs teks 2 baris) -- ini bug flexbox terpisah: .radio-hero adalah flex item di dalam .tab-panel (nav.css: display:flex; flex-direction:column; height:100%), sementara yang scroll adalah #content-area (app-shell.css: flex:1; overflow-y:scroll), bukan .tab-panel itu sendiri. Begitu 'All Stations' terisi (radio ON) dan total tinggi children .tab-panel (hero + list) melebihi height:100% tsb, flexbox mengecilkan children sesuai flex-shrink (default:1) SEBELUM #content-area sempat scroll -- height:322px fixed saja tidak melindungi karena flex-basis tetap boleh diperas oleh algoritma shrink tanpa flex-shrink:0. Fix: tambah flex-shrink:0 + min-height:322px (backstop) ke .radio-hero di radio-hero.css, comment R2.1 diupdate menjelaskan root cause baru. Diverifikasi via Playwright headless (chromium) mereproduksi struktur nyata index.html + CSS asli, viewport mobile 400x700 dan desktop 1366x660, radio-queue-list diisi item .radio-queue-item sungguhan (bukan simulasi div kosong): SEBELUM fix tinggi .radio-hero jatuh 322px->50px persis begitu daftar terisi (match screenshot 'Radio On' user); SESUDAH fix tetap 322px konsisten di kedua viewport, baik state off/on x kosong/terisi (4 kombinasi diuji eksplisit), dan #content-area tetap scrollable normal (scrollHeight bertambah sesuai jumlah station, tidak clipped). python automation/doctor.py --strict --json -> PASS/100 (tidak ada regresi baru).

---

## PATCH-2026-07-20-131

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/css/components/cards.css`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 7 (PENUTUP, R7.1..R7.3): hapus 233 baris CSS lama `.radio-featured`/`.centerpiece-*`/`.radio-live-badge` + keyframes terkait dari `cards.css` setelah grep-ulang dependency (kosong, kecuali 1 keyframe unrelated di file lain, di luar scope, dicatat terpisah); regenerasi `FILE_INDEX.md`/`REPORT.md`; `doctor.py --strict` PASS/100. Menutup seluruh fitur "Night Dial" (Sesi 1-7) -- ringkasan referensi: font self-host (S1), `radio-hero.css` height-fixed (S2), `radio-hero-moon.js` terisolasi (S3), gate `index.html` (S4), wiring (S5), QA + 1 fix reduced-motion (S6), cleanup (S7, entry ini).

---

## PATCH-2026-07-20-130

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/render/radio-hero-moon.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 6 (R6.1..R6.6, QA via headless browser): tinggi kartu 322px identik off/on terkonfirmasi (R6.1); klik/keyboard/swipe/guard-role berfungsi benar (R6.3, R6.4); rAF isolation stress-test 60x spam toggle bersih tanpa leak (R6.5, proxy -- playback nyata tidak bisa diuji di sandbox); BUG DITEMUKAN+FIX di radio-hero-moon.js -- rAF loop sebelumnya tidak berhenti saat prefers-reduced-motion aktif, sekarang fallback render statis tanpa rAF sama sekali (R6.6). BUG DITEMUKAN, BELUM DIFIX (dicatat terpisah sesuai DoD R6.2) -- starfield overflow di viewport 320/360px dan landscape pendek. doctor.py tetap PASS/100.

---

## PATCH-2026-07-20-129

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/render/radio-tab.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 5 (R5.1): hook setRadioHeroAnimState(isRadio) dari renderRadio() + sinkronisasi aria-pressed, satu baris tambahan masing-masing, radio-tab.js tetap satu-satunya pemilik state on/off. Menutup Sesi 1-5 fitur "Night Dial" (font, CSS, modul JS animasi, markup index.html, wiring) -- Sesi 6 (QA) & Sesi 7 (cleanup CSS lama) masih pending.

---

## PATCH-2026-07-20-128

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 4 (R4.1, gate governance-locked, dieksekusi setelah konfirmasi eksplisit user): satu-satunya sentuhan ke index.html untuk seluruh fitur -- markup #radio-toggle-btn diganti total ke desain "Night Dial" (id/data-on/rt-sub dipertahankan), tambah <link> radio-hero.css dan <script> radio-hero-moon.js. doctor.py & architecture_lint.py tetap PASS 100.

---

## PATCH-2026-07-20-127

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/render/radio-hero-moon.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 3 (R3.1..R3.4): modul baru radio-hero-moon.js (astronomi fase bulan, state machine rAF cycling/tweening, API publik setRadioHeroAnimState(isOn)) -- self-contained, module-scoped, self-audit isolasi RFC §5.4 penuh lolos (tidak ada state global bocor, tidak ada coupling ke playback-sync.js/player.js, klik & subtitle tetap 100% milik file lain sesuai RFC §5.3). Belum reachable dari UI -- lanjutan di sesi 4 (gate index.html, wajib konfirmasi eksplisit user).

---

## PATCH-2026-07-20-126

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/css/components/radio-hero.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 2 (R2.1..R2.4): isi penuh radio-hero.css (container height:322px fixed, starfield, moon SVG + tuner ticks, badge status 2-state selalu-visible sesuai R-D2, hero-name/hero-sub) dibangun bertahap dalam 1 sesi dedicated. Semua animasi transform/opacity/filter/stroke/fill only (tidak ada reflow di keyframes). Belum reachable dari UI -- lanjutan di sesi 3 (modul JS animasi).

---

## PATCH-2026-07-20-125

**Tanggal:** 2026-07-20
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** radio_toggle_redesign

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/fonts/fraunces/fraunces-latin-500-italic.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-400-normal.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-500-normal.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-600-normal.woff2`
- `web/static/fonts/LICENSE.md`
- `web/static/css/components/radio-hero.css`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
radio_toggle_redesign — Sesi 1 (R1.1..R1.2): fondasi font self-host (Fraunces italic 500, Space Grotesk 400/500/600 via Fontsource/npm, bukan CDN Google Fonts) + skeleton radio-hero.css (baru) dengan @font-face dan variable scoped ke .radio-hero (tidak duplikasi tokens.css). Belum reachable dari UI manapun -- lanjutan di sesi 2 (CSS komponen penuh).

---

## PATCH-2026-07-19-124

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Doc cleanup (di luar task_breakdown_agent

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/backend/persistence.md`
- `docs/backend/services.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Doc cleanup (di luar task_breakdown_agent.yaml, atas permintaan user): perbaiki drift dokumentasi vs kode aktual di docs/backend/persistence.md dan docs/backend/services.md, ditemukan saat audit pasca T-B19. persistence.md: skema tracks/sessions/artists/genres di dokumen sebelumnya tidak cocok dengan persistence/schema.sql aktual (mis. sessions didoc sebagai id/started_at/ended_at/track_count/mode, padahal aktual token/expires_at) -- diganti skema akurat untuk 7 tabel (tracks, sessions, admin_account, artists, genres, artist_genres, songs), tambah tabel artist_genres & songs yang sebelumnya tidak terdokumentasi sama sekali; Repository API diperbaiki total (TrackRepository/ArtistRepository/GenreRepository/LibraryRepository method-nya sebelumnya fiksi/tidak cocok nama method aktual); section Inisialisasi Database diganti dari class Database (sudah dihapus PATCH-2026-07-18-084) ke DatabaseConnection+Repositories aktual; tambah section Cache Resolver (link ke caching.md, hindari duplikasi); Migrasi Skema diperbaiki jadi 2 jalur nyata (loop ALTER TABLE di Repositories.init() + _migrate_songs_unique_constraint di db.py); contoh Testing diganti pakai API upsert_track/get_track yang benar. services.md: command_router.py -- HANDLERS dict fiktif diganti pola CommandRouter.register() aktual dgn CMD_PLAY_TRACK dst; playback/controller.py -- tabel sub-modul diupdate lengkap (queue_controller.py, settings_controller.py, crossfade.py, track_ended_ops.py sebelumnya tidak disebut); radio/engine.py -- alur radio fiktif (artist_selector.select_next -> ytdlp_adapter.search -> track_filter.filter -> queue_manager.enqueue) diganti alur nyata RadioMode (on_activated/_start dengan standby prefetch, next() dengan radio_queue popleft, _backfill_and_standby); queue_manager.py -- method add/remove/reorder/clear fiktif dihapus, diganti catatan bahwa operasi queue nyata ada di engine/playback/queue_ops.py (QueueOps) + queue_controller.py, queue_manager.py sendiri cuma QueueMode.next(); volume_service.py -- contoh kode function bebas diganti method class VolumeService aktual (_on_volume_up/_on_volume_set/_apply_volume, range 0-150 bukan 0-100); discover_service.py -- deskripsi 'rule-based, belum ada ML' diganti (sekarang wrapper DiscoverRepository dengan bandit ranking). Semua path test yang direferensikan diverifikasi ada di disk. doctor.py --strict tetap PASS 100 setelah perubahan (checker tidak menangkap drift semantik ini -- hanya cek struktur/frontmatter/docstring coverage, bukan kecocokan konten kode vs prosa).

---

## PATCH-2026-07-19-123

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B19 (lanjutan): finalisasi entry CHANGELOG

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `CHANGELOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B19 (lanjutan): finalisasi entry CHANGELOG.md untuk login_redesign. Entry [Unreleased] sebelumnya ditulis sebagai draft 'dalam progres' merujuk task_breakdown_agent.yaml -- sekarang Fitur B sudah selesai (T-B1..T-B19), entry difinalisasi: hapus framing draft, tambahkan poin launcher tanpa mekanisme auth sendiri (K5) dan env var override (K4) yang sebelumnya tidak disebut, section Dampak Upgrade (K3) link ke ADR-0008 yang sudah terbit (gantikan link langsung ke threat_model.md#anchor).

---

## PATCH-2026-07-19-122

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B19: dokumentasi akhir Fitur B (login_redesign) & regenerasi index

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/backend/api.md`
- `docs/backend/persistence.md`
- `docs/STATUS.md`
- `README.md`
- `docs/PATCHLOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B19: dokumentasi akhir Fitur B (login_redesign) & regenerasi index. docs/backend/api.md: ganti bagian auth HTTP basi (POST /auth/login, /portal, query-param token di koneksi WS) dengan alur nyata Fitur B -- section baru Autentikasi & Setup mendokumentasikan action WS setup_admin/auth (payload, response setup_status/auth_status), GET /api/setup-required, dan gate require_auth() per-action (bukan lagi gate di level koneksi); tabel Kode Error WebSocket dikoreksi (4001/4002 lama tidak lagi relevan, kegagalan auth sekarang dikirim sebagai pesan bukan close code); route table disamakan dengan server/app.py aktual (/, /admin, /api/stream/{video_id}, /api/setup-required, /health, /metrics). docs/backend/persistence.md: tambah skema admin_account dan AdminAccountRepository (create_admin_account, get_admin_account, admin_account_exists), link ke ADR-0008. docs/security/threat_model.md: sudah diupdate di T-B18 (link ke ADR-0008 terbit). docs/STATUS.md: section baru Status Fitur menyatakan Fitur A (quick_search_discover, done sesi sebelumnya) dan Fitur B (login_redesign, done sesi ini T-B1..T-B19) sama-sama selesai. README.md: bagian Mengakses Antarmuka Web diperbaiki (password admin tidak lagi auto-generate, sekarang lewat Initial Setup) plus catatan upgrade eksplisit (dari T-B6): kredensial lama tidak dimigrasikan otomatis, upgrade = logout paksa + wajib re-setup, link ke ADR-0008. run_all.py + generate_file_index.py + generate_report.py dijalankan ulang; doctor.py --strict PASS penuh; patchlog.py verify tanpa entry rusak.

---

## PATCH-2026-07-19-121

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B18: ADR-0008

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/adr/0008-admin-credentials-in-sqlite.md`
- `docs/security/threat_model.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B18: ADR-0008 — kredensial admin di SQLite, tanpa migrasi otomatis. Menyatukan keputusan K3 (tidak ada migrasi otomatis dari cache/admin_password.txt maupun instance/admin_password.txt, instalasi lama & baru diarahkan ke Initial Setup identik), K4 (env var override LUNAWAVE_ADMIN_PASS/YTGUI_ADMIN_PASS dipertahankan sebagai jalur non-default untuk provisioning non-interaktif, dikonsumsi satu-satunya kali oleh bootstrap.services._seed_admin_account_from_env saat admin_account masih kosong, tidak pernah overwrite akun existing), dan K5 (launcher tanpa mekanisme auth sendiri, tombol Reset Password di launcher/gui/auth_panel.py redirect ke web via webbrowser.open) menjadi satu ADR mengikuti pola 0002-sqlite-over-json-cache.md. Mencatat alternatif yang dipertimbangkan (migrasi otomatis, hapus env var override, launcher pertahankan mekanisme sendiri) beserta alasan penolakan masing-masing, dan konsekuensi eksplisit: user existing wajib re-setup (logout paksa) saat upgrade. docs/security/threat_model.md diupdate agar catatan K3 menunjuk ke ADR-0008 yang sudah terbit, bukan lagi forward-reference.

---

## PATCH-2026-07-19-120

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B16

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `launcher/auth_service.py`
- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/ui_builder.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B16.1..T-B17: Sesi 10 — launcher tanpa mekanisme auth sendiri, tombol Reset Password redirect ke web (K5), review .gitignore/verify_security.py. T-B16.1 hapus launcher/auth_service.py (satu-satunya konsumen: launcher/gui/auth_panel.py; find_owner.py mengonfirmasi file sudah tidak ada). T-B16.2 tulis ulang auth_panel.py: on_reset_password() sekarang cuma buka http://localhost:{server_port} di browser (webbrowser.open), tidak ada lagi generate/simpan password lokal; konsekuensi wajib di luar files resmi task tapi diperlukan agar import tidak patah -- app.py: hapus panggilan handle_first_run (fungsi ini juga sudah tidak ada, launcher tidak lagi punya alur first-run sendiri, web sendiri yang cek /api/setup-required); ui_builder.py: panggilan on_reset_password disederhanakan jadi satu argumen (app). Test disesuaikan: tests/unit/launcher/gui/test_auth_panel.py ditulis ulang total (assert webbrowser.open dipanggil ke URL yang benar, assert tidak ada file instance/ ditulis); tests/unit/launcher/gui/test_app.py -- helper _make_app() berhenti monkeypatch handle_first_run yang sudah dihapus. T-B16.3 manual QA end-to-end dengan server nyata (bukan mock), BASE_DIR sementara, tanpa mpv (tidak tersedia di sandbox, di luar scope jalur auth): (1) boot instalasi baru -> GET /api/setup-required -> {"setup_required": true}, direktori instance/ tidak pernah dibuat; (2) via WS nyata: action setup_admin (username admin) -> {"success": true}, lalu action auth dengan password yang sama -> {"success": true, token diterbitkan}; (3) GET /api/setup-required setelah itu -> {"setup_required": false}; instance/ tetap tidak pernah ada di seluruh skenario -- mengonfirmasi dod T-B16.3 (start server dari launcher -> browser -> setup/login berhasil, tanpa instance/admin_password.txt terlibat). T-B17 review: .gitignore TIDAK diubah (pola cache/admin_password.txt & instance/ sengaja dipertahankan selama masa transisi, sesuai instruksi task); verify_security.py --json -> PASS 100/100 (Credential Ignore PASS, DB Files Ignore PASS). Regresi penuh: 667 passed, 6 skipped (skip krn tkinter tidak ada display di sandbox verifikasi -- python3-tk sendiri terpasang & bisa diimport, cuma tidak ada X server, di luar scope T-B16).

---

## PATCH-2026-07-19-119

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B15

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `config_security.py`
- `tests/unit/test_config_security.py`
- `docs/FILE_INDEX.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B15.1..T-B15.3: bersih-bersih pasca cut-over kredensial. T-B15.1 find_owner.py config_security.py -> satu-satunya konsumen adalah tests/unit/test_config_security.py (tidak ada konsumen produksi lain; config.py sudah lepas dependency di T-B14.1). T-B15.2 hapus config_security.py & tests/unit/test_config_security.py; print banner PASSWORD ADMIN GENERATED sudah tidak ada sejak T-B14.1 (tidak ada sisa di main.py). docs/FILE_INDEX.md di-regenerate (entry config_security.py basi dihapus otomatis) -- doctor.py --strict sempat FAIL karena ini, sekarang PASS 100 setelah regenerate. T-B15.3 regression: full suite 665 passed/4 skipped (unit+integration, di luar tkinter GUI yang tidak tersedia di sandbox verifikasi); 3 skenario e2e boot manual dengan SQLite nyata (bukan mock) -- (A) instalasi baru tanpa override: admin_account kosong, tidak ada file password ditulis; (B) instalasi lama dengan artifact cache/admin_password.txt sisa pra-redesign tanpa override: perilaku identik skenario A (K3, tidak ada migrasi otomatis, file lama diabaikan bukan dihapus paksa); (C) provisioning non-interaktif via LUNAWAVE_ADMIN_PASS (K4): admin_account ter-seed dengan hash PBKDF2 valid (diverifikasi cocok/tidak-cocok via verify_password), reboot kedua dengan env var berbeda tidak overwrite akun existing (K3). impact.py tetap gagal karena bug lama ImportError collect_py_files di find_owner.py (pre-existing, sudah dicatat sejak T-B14, di luar scope perbaikan sesi ini).

---

## PATCH-2026-07-19-118

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B14

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `config.py`
- `bootstrap/services.py`
- `main.py`
- `tests/unit/test_config.py`
- `tests/unit/bootstrap/test_services.py`
- `tests/conftest.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B14.1..T-B14.2: hapus mekanisme legacy auto-generated admin password di config.py (IS_PASSWORD_AUTO_GENERATED, cache/admin_password.txt, chmod, banner). admin_account (SQLite) tetap satu-satunya source of truth untuk login (T-B13.1). Env var override LUNAWAVE_ADMIN_PASS/YTGUI_ADMIN_PASS dipertahankan (K4) lewat symbol baru config.ADMIN_PASSWORD_OVERRIDE, dikonsumsi satu-satunya oleh bootstrap.services._seed_admin_account_from_env() yang seed admin_account sekali saat tabel masih kosong dan tidak pernah overwrite akun existing (K3). main.py: hapus blok banner kredensial yang bergantung ke IS_PASSWORD_AUTO_GENERATED (konsekuensi wajib dari penghapusan simbol tsb, di luar files config.py tapi diperlukan agar import tidak patah). Test suite disesuaikan: tests/unit/test_config.py, tests/unit/bootstrap/test_services.py (3 test baru untuk _seed_admin_account_from_env), tests/conftest.py (hapus workaround LUNAWAVE_ADMIN_PASS default yang sudah tidak relevan). Verifikasi: 666 passed, 4 skipped (skip krn tkinter tidak ada di sandbox verifikasi, di luar scope); doctor.py --strict PASS; impact.py config.py gagal karena bug lama ImportError collect_py_files di find_owner.py (pre-existing, di luar scope T-B14).

---

## PATCH-2026-07-19-117

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-B13

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/auth.py`
- `server/handlers/websocket.py`
- `tests/unit/server/handlers/test_auth.py`
- `tests/unit/server/handlers/test_websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-B13.1..T-B13.2: cut-over sumber kredensial login dari config.ADMIN_USERNAME/ADMIN_PASSWORD ke admin_account_repo (SQLite). handle_auth sekarang menerima repos penuh (bukan hanya repos.sessions) untuk akses repos.admin_account. Mitigasi timing side-channel PATCH-2026-07-16-001 dipertahankan via dummy PBKDF2 hash saat admin_account belum ada (instalasi baru). Perubahan izin gate BARU (terpisah dari T-B8) di server/handlers/websocket.py: satu baris pemanggilan handle_auth diteruskan repos, bukan repos.sessions. Regresi T-B13.2: skenario instalasi baru dan instalasi lama kini identik (K3, wajib Initial Setup ulang, tidak ada migrasi otomatis).

---

## PATCH-2026-07-19-116

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fitur B (login_redesign)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/css/portal.css`
- `web/static/js/portal.js`
- `web/static/js/main.js`
- `web/static/js/dom.js`
- `web/static/js/events/index.js`
- `web/static/js/services/auth.js`
- `web/static/js/ws.js`
- `tests/frontend/ws-routing.test.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fitur B (login_redesign) — Sesi 6, T-B10..T-B12.2: CSS #setup-screen + wiring JS + validasi client (parallel_ok, tidak locked, tidak butuh izin tambahan). T-B10: web/static/css/portal.css -- rule #setup-screen (mirror persis #portal-screen: fixed/flex/hidden, toggle lewat class portal-active) dan #setup-submit-btn (mirror #admin-submit-btn, plus state :disabled) ditambahkan; field Confirm Password otomatis konsisten di 3 breakpoint karena reuse .login-input-group/.login-error dan portal.css sendiri tidak punya override per-breakpoint (tidak ada selector 'portal' di platform/*.css). T-B11.1/T-B11.2: web/static/js/portal.js -- fungsi baru initSetupCheck() (async) memanggil GET /api/setup-required SEBELUM memutuskan tampilkan #setup-screen atau #portal-screen, sengaja tidak ditebak murni dari localStorage (kontrak K3: upgrade instalasi lama tanpa migrasi otomatis bisa saja localStorage masih simpan role lama padahal admin_account kosong); fetch gagal (network/non-200) fail-open ke alur login normal (initPortal() tetap dipanggil) supaya user existing tidak pernah terkunci gara-gara check ini sendiri gagal. web/static/js/main.js: init() manggil initSetupCheck() menggantikan initPortal() langsung. web/static/js/dom.js: 8 elemen #setup-screen baru didaftarkan (setupScreen, setupForm, setupUsername, setupPassword, setupConfirmPassword, setupConfirmErrorMsg, setupSubmitBtn, setupErrorMsg). T-B12.1: web/static/js/events/index.js -- fungsi updateSetupSubmitState() disable submit selama password!=confirm (dicek live tiap input, bukan cuma saat submit), listener input pada setup-password & setup-confirm-password, Enter key pada confirm-password men-trigger klik submit kalau tidak disabled. T-B12.2: web/static/js/services/auth.js -- fungsi baru submitSetup(user, pass, confirmPass): validasi ulang match sebagai jaring pengaman (submit seharusnya sudah disabled duluan), lalu wsSend('setup_admin', {username, password}) -- confirmPass TIDAK PERNAH masuk payload, sesuai kontrak T-B5.1 (_validate_setup_input di server/handlers/setup.py memang tidak pernah menerima field ini). web/static/js/ws.js: case baru 'setup_status' di handleServerMessage -- sukses: re-enable submit button, toast, toggle #setup-screen -> #portal-screen (TIDAK auto-login sebagai admin, user login manual pakai kredensial yang baru dibuat); gagal: re-enable submit button, tampilkan msg.data.message di #setup-error-msg, tetap di #setup-screen. Test baru: tests/frontend/ws-routing.test.js -- 2 skenario setup_status (success toggle screen + reset field, failure tetap di setup-screen dengan pesan server) ditambah ke mock dom yang sudah ada; total 16 test frontend (vitest), semua hijau (naik dari 14). Checkpoint end-to-end manual (folder data kosong -> Initial Setup -> submit -> redirect Login -> login berhasil) TIDAK bisa dijalankan sungguhan di browser -- sandbox ini tanpa network/display DAN tanpa mpv/yt-dlp (bahkan fixture app_client integration test butuh keduanya, lihat tests/integration/conftest.py), sama seperti precedent semua sesi sebelumnya (T-B8: 'belum ditest manual di browser sungguhan'). Sebagai gantinya, alur penuh sudah ditelusuri baris-per-baris end-to-end (GET /api/setup-required -> setup_required true -> #setup-screen tampil -> isi form -> validasi match client -> submit -> wsSend('setup_admin') tanpa confirm -> server handle_setup_admin (T-B5, sudah 11+3 skenario unit test hijau) -> setup_status success -> toggle ke #portal-screen -> login manual via action 'auth' existing yang sudah reachable sejak T-B8) dan didukung unit test di kedua sisi (backend: test_setup.py 14 skenario + test_websocket.py; frontend: ws-routing.test.js 16 skenario). Regresi penuh: 663 passed, 6 skipped (skip count sama seperti sesi 5, murni sandbox tanpa mpv/X display, tidak terkait Fitur B). doctor.py --strict PASS 100 semua checker. vitest: 16/16 passed (naik dari 14 baseline sesi 5).

---

## PATCH-2026-07-19-115

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fitur B (login_redesign)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fitur B (login_redesign) — Sesi 5, T-B9.1..T-B9.2: gate index.html #2 (izin eksplisit user diberikan PERSIS sebelum T-B9.1, terpisah dari izin T-B8 meski satu fitur). Menambahkan #setup-screen ke web/static/index.html, reuse struktur .portal-card/.portal-title/.portal-subtitle/.portal-options/.portal-admin-wrapper/.portal-login-form/.login-input-group/.login-error dari #portal-screen existing (T-B9.1), lalu field Confirm Password + area pesan validasi tersendiri (T-B9.2). Elemen baru: #setup-screen, #setup-form, #setup-username, #setup-password, #setup-confirm-password, #setup-confirm-error-msg, #setup-submit-btn, #setup-error-msg -- semua id baru, tidak ada id/class #portal-screen existing yang diubah (portal-screen, portal-login-form, admin-username, admin-password, admin-submit-btn, login-error-msg persis sama seperti sebelumnya). Field Confirm Password sengaja diberi area pesan validasi terpisah (#setup-confirm-error-msg) dari error server (#setup-error-msg) karena kontrak T-B5: confirm password tidak pernah dikirim ke server, jadi pesan mismatch-nya murni client-side (akan divalidasi di T-B12.1/T-B12.2). Markup belum berfungsi -- belum ada CSS untuk #setup-screen (display:none/flex, styling Confirm Password) dan belum ada wiring JS (cek /api/setup-required, toggle vs #portal-screen, validasi submit) -- itu T-B10..T-B12.2 di sesi 6. Setup-screen saat ini tidak memiliki class display CSS sendiri sehingga akan tampak tanpa styling/positioning jika dirender langsung sebelum T-B10 -- ini disengaja, konsisten dengan pola inkremental fitur ini (mis. setup_admin action T-B5 belum reachable sampai T-B8). post_commands verify_structure.py --verbose --json: flag --verbose tidak dikenali script actual (error argparse) -- bug pre-existing tidak terkait perubahan sesi ini (mirip catatan impact.py di PATCH-2026-07-19-113), dijalankan tanpa --verbose sebagai gantinya, PASS 100 (Big Files, Pending Items) baik setelah T-B9.1 maupun setelah T-B9.2. Regresi penuh: 663 passed, 6 skipped (naik 4 dari 2 baseline tercatat sesi 4 -- 4 skip tambahan murni environment sandbox ini, integration test butuh mpv tidak ada + GUI test butuh X display tidak ada, tidak terkait Fitur B, tidak ada test baru gagal/berkurang). doctor.py --strict PASS 100 semua checker (verify_docs, architecture_lint, verify_structure, verify_security, event_graph).

---

## PATCH-2026-07-19-114

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fitur B (login_redesign)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`
- `server/app.py`
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fitur B (login_redesign) — Sesi 4, T-B8: routing setup_admin ke whitelist (GATE, izin eksplisit user diberikan PERSIS sebelum task ini, terpisah dari izin manapun sebelumnya di file yang sama). server/handlers/websocket.py: action 'setup_admin' di-special-case di handle_ws_message() SEBELUM require_auth() -- mirror persis pola action 'auth', karena saat Initial Setup belum ada admin_account sama sekali sehingga tidak ada cara 'sudah login' pada titik itu. Memanggil handle_setup_admin() dari server/handlers/setup.py (T-B5/T-B7). Command lama (auth, playback, queue, discovery, download, cache) tidak diubah/disentuh sama sekali. server/app.py (TIDAK locked): endpoint GET /api/setup-required didaftarkan via app.router.add_get(), memanggil setup_required() dari setup.py -- akan dipanggil client saat load, SEBELUM koneksi WS dibuka (T-B11.1). Unit test baru: test_handle_ws_message_setup_admin (dispatch benar, args match) + test_handle_ws_message_setup_admin_bypasses_require_auth (regresi guard -- setup_admin TIDAK PERNAH memanggil require_auth(), krusial karena kalau ini regresi instalasi baru tidak akan pernah bisa menyelesaikan Initial Setup) di tests/unit/server/handlers/test_websocket.py. tests/unit/server/test_app.py: assertion route '/api/setup-required' ditambah ke test_create_app_registers_routes_and_services. Regresi WS lengkap: 663 passed, 2 skipped (naik 2 dari 661 baseline sesi 3), tidak ada command lama yang regresi. doctor.py --strict PASS 100 semua checker (architecture_lint, verify_docs, verify_structure, verify_security, event_graph). setup_admin & GET /api/setup-required kini reachable end-to-end dari WS/HTTP client (belum ditest manual di browser sungguhan -- sandbox tanpa network/display, sama seperti precedent Fitur A). Belum ada markup UI (#setup-screen) di index.html -- itu T-B9 (gate index.html, sesi 5, izin terpisah lagi).

---

## PATCH-2026-07-19-113

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fitur B (login_redesign)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/security/threat_model.md`
- `CHANGELOG.md`
- `server/handlers/setup.py`
- `tests/unit/server/handlers/test_setup.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fitur B (login_redesign) — Sesi 3, T-B6..T-B7: dokumentasi K3 (tanpa migrasi otomatis) + fallback kegagalan setup. T-B6: tambah section 'Catatan Desain: Kredensial Admin Tidak Dimigrasikan Otomatis (K3)' di docs/security/threat_model.md -- rasional (dua file password lama tidak sinkron di lapangan, risiko salah pilih sumber > biaya re-setup), konsekuensi (upgrade = wajib Initial Setup lagi), pointer ke ADR resmi yang akan ditulis di T-B18 setelah cut-over selesai. DoD terpenuhi by construction: TIDAK ADA kode migrasi ditulis sama sekali (tidak ada baca cache/admin_password.txt atau instance/admin_password.txt di manapun) sehingga instalasi baru & lama otomatis berperilaku identik terhadap admin_account -- keduanya kosong sampai lewat Initial Setup. Draft catatan upgrade ditambah ke CHANGELOG.md (## [Unreleased], ditandai draft/dalam-progres, akan difinalisasi T-B19). T-B7: fallback kegagalan di server/handlers/setup.py -- 3 titik try/except baru (admin_account_exists() awal, create_admin_account() non-IntegrityError, setup_required() HTTP endpoint): kegagalan DB corrupt/disk penuh/OSError ditangkap eksplisit, di-log via structlog (detail lengkap TIDAK dikirim ke client, cuma pesan generik 'Gagal menyimpan akun admin...'), handler TIDAK melempar exception ke luar (server tetap start & jalan untuk client lain), dan karena create_admin_account adalah single atomic INSERT, kegagalan tidak pernah menyisakan row admin_account setengah-jadi/kosong yang bisa login tanpa password. setup_required() HTTP mengembalikan 503 + pesan generik alih-alih 500 stack-trace bocor. Unit test baru (3 skenario fallback ditambah ke tests/unit/server/handlers/test_setup.py, total 14 skenario di file itu): create gagal (OSError, pesan tidak bocor), exists-check gagal (OperationalError, insert TIDAK dipanggil), endpoint setup_required gagal (503, pesan tidak bocor) -- semua hijau. Regresi penuh: 661 passed, 2 skipped (naik 3 dari 658 baseline sesi 2). verify_security.py PASS 100. doctor.py --strict PASS 100 semua checker. Catatan insidental: automation/impact.py punya bug pre-existing tidak terkait Fitur B (ImportError: cannot import name 'collect_py_files' from find_owner -- terjadi di SEMUA target file, bukan spesifik ke perubahan sesi ini), post_command T-B6 yang memanggilnya dilewati, dicatat di sini untuk visibilitas, tidak diperbaiki (di luar scope Fitur B). Belum reachable dari client -- handler setup_admin masih menunggu whitelist websocket.py (T-B8).

---

## PATCH-2026-07-19-112

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fitur B (login_redesign)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/setup.py`
- `server/connection_manager.py`
- `tests/unit/server/handlers/test_setup.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fitur B (login_redesign) — Sesi 2, T-B5.1..T-B5.6: handler setup_admin lengkap. File baru server/handlers/setup.py: handle_setup_admin(ws, data, manager, client_ip, repos, now) -- validasi username wajib + password minimal 8 karakter (field confirm password TIDAK pernah dikirim/divalidasi di server, kontrak dengan T-B12.2), hashing via core.security.hash_password (existing, tidak reimplement), simpan via repos.admin_account.create_admin_account(). Race condition submit ganda ditangani 2 lapis: cek admin_account_exists() dulu (fast-path, bukan pertahanan utama), lalu tangkap sqlite3.IntegrityError dari UNIQUE constraint (T-B1) sebagai pertahanan sesungguhnya utk kasus TOCTOU -- keduanya kirim pesan 'Akun admin sudah pernah dibuat', tidak pernah overwrite diam-diam. Rate limit 5x/5menit per IP: state baru manager.setup_attempts (terpisah dari login_attempts, ditambah di server/connection_manager.py, tidak locked), pola prune+lock identik handle_auth di auth.py. Fungsi setup_required(request) -- calon handler GET /api/setup-required, cek admin_account_exists() -> {setup_required: bool}; belum didaftarkan ke router (menunggu gate T-B8, websocket.py/app.py locked). Unit test baru tests/unit/server/handlers/test_setup.py: 11 skenario (validasi kosong/pendek, sukses hash+save, username di-strip, submit-ganda via exists()=True, submit-ganda via IntegrityError race, rate limit ke-6 ditolak, stale attempts di-prune, input invalid tetap kena hitungan rate limit, endpoint setup_required true/false) -- semua hijau. Regresi penuh: 658 passed, 2 skipped (tidak ada regresi). Environment fix insidental: apt-get install python3-tk (dependency test launcher/gui yang sebelumnya ModuleNotFoundError di sandbox ini, dicatat STATUS.md T0.2 sebelumnya). generate_file_index.py & generate_report.py dijalankan. doctor.py --strict PASS 100 semua checker. Belum reachable dari client sama sekali -- action setup_admin belum ada di whitelist websocket.py, endpoint HTTP belum terdaftar di app.py.

---

## PATCH-2026-07-19-111

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fitur B (login_redesign)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/schema.sql`
- `persistence/admin_account_repo.py`
- `persistence/__init__.py`
- `tests/unit/persistence/test_admin_account_repo.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fitur B (login_redesign) — Sesi 1, T-B1..T-B4: infrastruktur admin_account. Tabel admin_account (username UNIQUE, password_hash, created_at) ditambah ke persistence/schema.sql via CREATE TABLE IF NOT EXISTS -- otomatis terbuat di DB lama maupun baru karena executescript() jalan tiap startup (persistence/db.py), tidak perlu ALTER TABLE migration terpisah. Repository baru persistence/admin_account_repo.py (AdminAccountRepository) mirror pola session_repo.py: create_admin_account(username, password_hash) -- TANPA logika hashing di layer ini, hashing dilakukan di caller (T-B5); get_admin_account() -> None saat kosong; admin_account_exists() konsisten dengan get_admin_account(). Didaftarkan ke persistence/__init__.py (repos.admin_account), mengikuti pola facade tipis repos.discover -- tidak ada method delegasi tambahan di Repositories. Unit test baru tests/unit/persistence/test_admin_account_repo.py: create/get/exists lifecycle (4 skenario) + UNIQUE constraint pada percobaan create kedua dengan username sama (sqlite3.IntegrityError, baris pertama tidak ter-overwrite) -- kontrak dasar untuk race condition submit ganda yang akan diimplementasikan penuh di T-B5.3. Belum reachable dari client (belum ada handler/route) -- infrastruktur murni, menunggu T-B5 (handler setup_admin). generate_file_index.py & generate_report.py dijalankan (file baru terindeks). doctor.py --strict PASS 100 (architecture_lint, verify_docs, verify_structure, verify_security, event_graph semua PASS).

---

## PATCH-2026-07-19-110

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-A9: registrasi elemen DOM baru Quick Search Discover ke dom

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/dom.js`
- `web/static/js/events/discover-search-events.js`
- `web/static/js/render/discover-search.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-A9: registrasi elemen DOM baru Quick Search Discover ke dom.js (10 elemen via $() + filterScopeHint/rowUnheardLabel yang di-resolve di dalam dom.js). discover-search-events.js (T-A7) & render/discover-search.js (T-A8) diupdate pakai dom.* alih-alih document.getElementById langsung. main.js tidak berubah (urutan initDOM()/initEvents() sudah benar). doctor.py --strict PASS 100.

---

## PATCH-2026-07-19-109

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-A8: file baru web/static/js/render/discover-search

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/render/discover-search.js`
- `web/static/index.html`
- `web/static/js/ws.js`
- `web/static/js/events/discover-search-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-A8: file baru web/static/js/render/discover-search.js -- render hasil pencarian Quick Search Discover, mirror ringan render/search.js, reuse .sr-item. 5 state (Initial/Loading/Empty/No result/Error) lengkap dengan toggle blok personalisasi & guard request basi. Perlu 2 baris container + 1 baris <script> di index.html (izin eksplisit user) dan wiring kecil di ws.js (tidak locked) + discover-search-events.js (tidak locked). doctor.py --strict PASS 100.

---

## PATCH-2026-07-19-108

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-A7: file baru web/static/js/events/discover-search-events

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/events/discover-search-events.js`
- `web/static/js/events/index.js`
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-A7: file baru web/static/js/events/discover-search-events.js -- event handling + debounce 500ms untuk Quick Search Discover, mirror pola search-input-events.js. wsSend('discover_search', {query, kategori, decade}) terpicu setelah 500ms idle (atau Enter langsung). Tombol clear reset input, filter row, kategori/decade ke default TANPA round-trip ke server saat query kosong. Opsi dekade diturunkan dari data personalisasi yang sudah dimuat, tanpa query/kolom skema baru. Didaftarkan ke initEvents() via events/index.js. Ditambahkan 1 baris <script> di index.html (izin eksplisit user) -- reachable end-to-end. doctor.py --strict PASS 100.

---

## PATCH-2026-07-19-107

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-A6: CSS baru web/static/css/components/discover-search

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/css/components/discover-search.css`
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-A6: CSS baru web/static/css/components/discover-search.css untuk Quick Search Discover (search bar + filter row), pakai token spacing --s* project-wide, tanpa breakpoint baru. .filter-bar/.segmented/.custom-dropdown di-reuse apa adanya (tidak ada rule baru untuk itu). Perlu 1 baris tambahan <link rel=stylesheet> di web/static/index.html (izin eksplisit user, di luar cakupan file asli T-A6) supaya CSS ini benar-benar termuat. verify_structure.py & doctor.py --strict PASS 100.

---

## PATCH-2026-07-19-106

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-A5: markup Quick Search Discover di web/static/index

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/index.html`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-A5: markup Quick Search Discover di web/static/index.html (izin eksplisit user) -- search bar (.discover-search-wrap) + filter row (reuse .segmented kategori K1 + .custom-dropdown dekade K2, progressive disclosure via display:none) disisipkan sebelum .taste-block di #tab-discover. Terisolasi via id/class baru, tidak ada duplicate id, elemen Discover existing (taste-block, kategori-toggle, decade-dropdown-container) tidak berubah. Belum ada JS wiring (menunggu T-A7/T-A8).

---

## PATCH-2026-07-19-105

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T-A4: tambah 'discover_search' ke DISCOVERY_CMDS di server/handlers/websocket

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T-A4: tambah 'discover_search' ke DISCOVERY_CMDS di server/handlers/websocket.py (izin eksplisit user, perubahan 1 baris) -- action discover_search kini reachable dari client. Command lama (search, discover, get_artist_detail) diverifikasi tetap jalan. doctor.py --strict PASS 100, identik baseline T0.1. Belum ditest manual di browser sungguhan (sandbox tanpa network/display), sama seperti catatan get_artist_detail sebelumnya.

---

## PATCH-2026-07-19-104

**Tanggal:** 2026-07-19
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Quick Search Discover (T-A1

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/discover_repo.py`
- `tests/unit/persistence/test_discover_repo_search.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/server/handlers/test_ws_discovery.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Quick Search Discover (T-A1..T-A3): search_tracks() di discover_repo.py (LIKE title/artist, filter kategori Solo/Band K1 & dekade K2 via subquery tanpa JOIN artists/artist_genres, tanpa logika skor/ranking), unit test baru, branch discover_search di ws_discovery.py. Belum reachable dari client -- menunggu izin eksplisit T-A4 (DISCOVERY_CMDS di server/handlers/websocket.py, file governance-locked).

---

## PATCH-2026-07-18-103

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Rename nama generik: adapters/ytdlp/common

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/ytdlp/ydl_options.py`
- `adapters/ytdlp/searcher.py`
- `adapters/ytdlp/resolver.py`
- `adapters/ytdlp/downloader.py`
- `engine/radio/radio_config.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`
- `engine/radio/prefetcher.py`
- `automation/verify_docs/doc_parsing_utils.py`
- `automation/verify_docs/render.py`
- `automation/verify_docs/checks_files.py`
- `automation/verify_docs/checks_coverage.py`
- `automation/verify_docs/checks_docs.py`
- `automation/verify_docs.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Rename nama generik: adapters/ytdlp/common.py -> ydl_options.py, engine/radio/common.py -> radio_config.py, automation/verify_docs/helpers.py -> doc_parsing_utils.py; sekalian perbaiki docstring 'Depends on' yang masih menyebut scripts.verify_docs.helpers (sisa lupa update dari PATCH-2026-07-17-072)

---

## PATCH-2026-07-18-102

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Rename file test yang menyimpang konvensi penamaan (tests/frontend/test_store

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/frontend/store.test.js`
- `tests/frontend/ws-routing.test.js`
- `tests/unit/launcher/gui/test_app.py`
- `tests/unit/adapters/ytdlp/test_ytdlp.py`
- `docs/testing/README.md`
- `docs/testing/frontend_testing.md`
- `docs/architecture/folder_structure.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Rename file test yang menyimpang konvensi penamaan (tests/frontend/test_store.test.js -> store.test.js, test_ws-routing.test.js -> ws-routing.test.js, tests/unit/launcher/gui/test_app_lifecycle.py -> test_app.py); konsolidasi test_ytdlp.py + test_ytdlp_client.py jadi satu file test_ytdlp.py (kelas facade disuffix ViaYtDlpClient agar tidak bentrok nama, semua 42 assertion/test case dipertahankan, verified: 620 passed tetap sama)

---

## PATCH-2026-07-18-101

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Rename ADR 003-Crossfade

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/adr/0007-crossfade.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Rename ADR 003-Crossfade.md ke konvensi 0007-crossfade.md, samakan judul internal jadi ADR-0007 (tidak ada referensi lain yang perlu diupdate selain entri historis di PATCHLOG.md yang sengaja dibiarkan sebagai catatan riwayat)

---

## PATCH-2026-07-18-100

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Perluas

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `.importlinter`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Perluas .importlinter: kontrak automation dan data sebagai root package terisolasi (automation tidak boleh diimpor, data hanya boleh diimpor automation); dikonfirmasi cache/ sudah bukan python package sejak T2.6 sehingga tidak perlu entri forbidden_modules tambahan

---

## PATCH-2026-07-18-099

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Tambahkan accessor get_*() bertipe di server/handlers/__init__

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/__init__.py`
- `server/handlers/http.py`
- `server/handlers/websocket.py`
- `server/handlers/audio_stream_handler.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Tambahkan accessor get_*() bertipe di server/handlers/__init__.py untuk semua key request.app[...] (repos, tracks, conn, state, manager, ytdlp, playback_controller) - rencana asli get_db() untuk request.app['db'] sudah tidak relevan sejak Database God Facade dipecah T2.2, diganti akses per-repo

---

## PATCH-2026-07-18-098

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Tambahkan type hint DatabasePort ke constructor engine/ yang menerima db tanpa tipe

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/ports.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Tambahkan type hint DatabasePort ke constructor engine/ yang menerima db tanpa tipe

---

## PATCH-2026-07-18-097

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Audit data/: artists_enriched1

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/STATUS.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Audit data/: artists_enriched1.json TERNYATA BUKAN duplikat (854 vs 100 artis, beda substantif) - tidak dihapus, didokumentasikan di STATUS.md, butuh keputusan pemilik project. export_to_sqlite.py dikonfirmasi tetap di data/ (kontradiksi dengan rencana pindah ke automation/ di TASK_BREAKDOWN.md dibatalkan karena state riil sudah selesai)

---

## PATCH-2026-07-18-096

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pisah serve_stream (range-request) ke audio_stream_handler

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/audio_stream_handler.py`
- `server/handlers/http.py`
- `server/app.py`
- `tests/unit/server/handlers/test_audio_stream_handler.py`
- `tests/unit/server/handlers/test_http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pisah serve_stream (range-request) ke audio_stream_handler.py

---

## PATCH-2026-07-18-095

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pisah skor rekomendasi (compute_match_pct, taste spectrum) ke services/discover_ranking

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `services/discover_ranking.py`
- `persistence/discover_repo.py`
- `services/discover_service.py`
- `tests/unit/services/test_discover_ranking.py`
- `tests/unit/persistence/test_discover_repo.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pisah skor rekomendasi (compute_match_pct, taste spectrum) ke services/discover_ranking.py, fungsi murni tanpa DB

---

## PATCH-2026-07-18-094

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Ekstrak auth_service

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `launcher/auth_service.py`
- `launcher/gui/auth_panel.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Ekstrak auth_service.py dari auth_panel.py, pisah logic dari UI

---

## PATCH-2026-07-18-093

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pecah build_ui() jadi 4 method privat di ui_builder

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `launcher/gui/ui_builder.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pecah build_ui() jadi 4 method privat di ui_builder.py

---

## PATCH-2026-07-18-092

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Ekstrak ServerLifecycle (tanpa dependency Tkinter) dari ServerManager di launcher/gui/app

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `launcher/gui/app.py`
- `launcher/server_lifecycle.py`
- `launcher/gui/log_view.py`
- `tests/unit/launcher/test_server_lifecycle.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Ekstrak ServerLifecycle (tanpa dependency Tkinter) dari ServerManager di launcher/gui/app.py

---

## PATCH-2026-07-18-091

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Perbaiki typo/leftover text di docs/STATUS

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/STATUS.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Perbaiki typo/leftover text di docs/STATUS.md pada baris services/stream_prefetch.py (sisa draf tidak sengaja ke-commit).

---

## PATCH-2026-07-18-090

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `services/stream_prefetch.py`
- `server/broadcast_service.py`
- `server/handlers/event_listeners.py`
- `server/app.py`
- `tests/unit/services/test_stream_prefetch.py`
- `tests/unit/server/test_broadcast_service.py`
- `docs/backend/services.md`
- `docs/backend/background_jobs.md`
- `docs/testing/unit_testing.md`
- `docs/INDEX.md`
- `docs/architecture/backend.md`
- `docs/architecture/data_flow.md`
- `docs/adr/0005-websocket-single-channel.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T2.7: Satukan services/ (root) dan server/services/. stream_prefetch.py pindah ke services/stream_prefetch.py sesuai rencana (hanya impor config+core). broadcast_service.py TIDAK dipindah ke root services/ (deviasi dari rencana) melainkan ke server/broadcast_service.py, karena mengimpor server.connection_manager dan server.serializers (konstruksi web/wire layer) -- begitu bug .importlinter (PATCH-2026-07-18-089) diperbaiki, memindahkannya ke services/ akan melanggar kontrak 'services hanya boleh import core dan persistence'. Folder server/services/ dihapus. Update importer: server/handlers/event_listeners.py, server/app.py. Test dipindah: tests/unit/services/test_stream_prefetch.py, tests/unit/server/test_broadcast_service.py. Dokumentasi diupdate: docs/backend/services.md (keputusan+konvensi suffix), docs/backend/background_jobs.md, docs/testing/unit_testing.md, docs/INDEX.md, docs/architecture/backend.md, docs/architecture/data_flow.md, docs/adr/0005-websocket-single-channel.md. Verifikasi: pytest 594 passed 0 failed, lint-imports 7 kept 0 broken (verified real, bukan false positive), architecture_lint PASS, doctor PASS, wiring server/app.py dicek manual.

---

## PATCH-2026-07-18-089

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Perbaiki bug syntax

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `.importlinter`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Perbaiki bug syntax .importlinter: forbidden_modules/source_modules pakai koma-satu-baris yang TIDAK di-parse import-linter (SetField hanya split per-baris, bukan per-koma) — 6 dari 7 kontrak selama ini silently no-op (selalu KEPT tanpa benar-benar cek apa pun). Diverifikasi langsung ke source import-linter (grimp.find_shortest_chains + ForbiddenContract.check). Diperbaiki jadi format list per-baris (sama seperti root_packages yang sudah benar). Baseline lint-imports pasca-perbaikan: 7 kept, 0 broken (genuinely verified, bukan false positive).

---

## PATCH-2026-07-18-088

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Perbaiki assertion salah di test_handle_playback_command_other_commands: CMD_PREV memang dikirim be…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/server/handlers/test_ws_playback.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Perbaiki assertion salah di test_handle_playback_command_other_commands: CMD_PREV memang dikirim beserta data (simetris dengan CMD_NEXT, mendukung guard video_id opsional di _on_prev), bukan tanpa argumen. Baseline test suite sekarang 594 passed, 0 failed.

---

## PATCH-2026-07-18-087

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Gabungkan cache/resolver

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/stream_cache.py`
- `data/pb_html.txt`
- `bootstrap/services.py`
- `tests/integration/conftest.py`
- `tests/unit/test_main.py`
- `tests/unit/persistence/test_stream_cache.py`
- `tests/unit/engine/playback/test_track_loader.py`
- `tests/unit/engine/conftest.py`
- `tests/unit/bootstrap/test_services.py`
- `server/handlers/ws_cache.py`
- `docs/backend/caching.md`
- `cache/resolver.py`
- `cache/__init__.py`
- `cache/pb_html.txt`
- `tests/unit/cache/test_resolver.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Gabungkan cache/resolver.py ke persistence/stream_cache.py, hapus folder cache/ (pb_html.txt statis dipindah ke data/, ws_cache.py tidak di-rename karena tidak terkait stream cache)

---

## PATCH-2026-07-18-086

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pecah main

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `main.py`
- `bootstrap/__init__.py`
- `bootstrap/services.py`
- `bootstrap/startup_tasks.py`
- `bootstrap/maintenance.py`
- `tests/unit/test_main.py`
- `tests/unit/bootstrap/__init__.py`
- `tests/unit/bootstrap/test_services.py`
- `tests/unit/bootstrap/test_startup_tasks.py`
- `tests/unit/bootstrap/test_maintenance.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pecah main.py jadi bootstrap/ (services, startup_tasks, maintenance), main() jadi orkestrasi 4 langkah

---

## PATCH-2026-07-18-085

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pecah PlaybackController: ekstrak QueueController dan SettingsController, wiring delegasi via comma…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/playback/controller.py`
- `engine/playback/queue_controller.py`
- `engine/playback/settings_controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/engine/playback/test_queue_controller.py`
- `tests/unit/engine/playback/test_settings_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pecah PlaybackController: ekstrak QueueController dan SettingsController, wiring delegasi via command_router

---

## PATCH-2026-07-18-084

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/__init__.py`
- `main.py`
- `cache/resolver.py`
- `server/app.py`
- `server/handlers/http.py`
- `server/handlers/websocket.py`
- `server/handlers/ws_download.py`
- `scratch/check_db.py`
- `tests/conftest.py`
- `tests/integration/conftest.py`
- `tests/unit/core/test_ports.py`
- `tests/unit/persistence/test_db.py`
- `tests/unit/persistence/test_track_repo.py`
- `tests/unit/persistence/test_session_repo.py`
- `tests/unit/persistence/test_artist_repo.py`
- `tests/unit/persistence/test_genre_repo.py`
- `tests/unit/persistence/test_discover_repo.py`
- `tests/unit/services/test_discover_service.py`
- `tests/unit/test_main.py`
- `tests/unit/server/test_app.py`
- `tests/unit/server/handlers/test_http.py`
- `tests/unit/server/handlers/test_ws_download.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T2.2e: hapus facade Database (God Facade) dari persistence/__init__.py. Diganti Repositories: container tipis 1 koneksi + 6 repo domain (tracks/sessions/artists/genres/library/discover) tanpa method delegasi. main.py wiring ulang: CacheResolver dapat ResolverDbCompat (gabungan TrackRepository+ArtistRepository+DiscoverRepository, cuma utk resolver.db yg dipakai lintas domain oleh controller/track_loader/track_ended_ops/event_listeners -- BUKAN facade baru, tidak ada logic sendiri), LoudnessService dapat repos.tracks langsung, RadioMode dapat repos.artists+repos.library. server/app.py: create_app terima Repositories, app dict simpan 'repos'+'conn'+'tracks' (bukan 'db' facade penuh). http.py health_check pakai app['conn']. websocket.py: db->repos, handle_download_command sekarang terima tracks+discover terpisah (bukan db penuh) - ws_download.py diperbaiki mengikuti. scratch/check_db.py diperbaiki (Database sudah tidak ada). Enam file test yang pakai db fixture dgn flat facade call (test_track_repo, test_session_repo, test_artist_repo, test_genre_repo, test_discover_repo, test_discover_service) di-sed ke db.<repo>.<method>. test_ports.py ditulis ulang per-repo (bukan cek 1 Database god object). test_db.py ditulis ulang menguji persistence.db.DatabaseConnection langsung (bukan lewat facade). test_main.py, test_app.py, test_http.py, test_ws_download.py disesuaikan ke wiring baru. Hasil: 558 passed (baseline T0.2 sama persis), 1 failed pre-existing (test_ws_playback, tidak terkait), import-linter 7 kept/0 broken.

---

## PATCH-2026-07-18-083

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Migrasi discover_service dan ws_discovery ke DiscoverRepository langsung (T2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `server/handlers/websocket.py`
- `server/handlers/event_listeners.py`
- `server/handlers/ws_download.py`
- `persistence/discover_repo.py`
- `core/ports.py`
- `tests/unit/services/test_discover_service.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Migrasi discover_service dan ws_discovery ke DiscoverRepository langsung (T2.2d). DiscoverService kini menerima DiscoverRepository (bukan facade Database) via param 'discover'; tambah DiscoverRepositoryPort di core/ports.py dan property conn publik di DiscoverRepository (pola sama dgn artist_repo.py/library_repo.py T2.2c). handle_discovery_command di ws_discovery.py menerima discover_repo langsung. server/handlers/websocket.py disentuh 1 baris untuk wiring db.discover (melanjutkan izin eksplisit yg sama dgn T2.2c). Konsumen lain DiscoverService yang tadinya pass facade penuh (event_listeners.py, ws_download.py) ikut diperbaiki ke db.discover supaya tidak pecah runtime, walau di luar SOP-A target eksplisit task ini.

---

## PATCH-2026-07-18-082

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/__init__.py`
- `persistence/artist_repo.py`
- `persistence/library_repo.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`
- `server/handlers/auth.py`
- `server/handlers/ws_queue.py`
- `server/handlers/websocket.py`
- `main.py`
- `tests/integration/conftest.py`
- `tests/unit/engine/radio/test_artist_selector.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/server/handlers/test_ws_queue.py`
- `tests/unit/server/handlers/test_websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T2.2c: migrasi konsumen domain session/artist/genre/library ke repository masing-masing langsung (session/artist/genre/library repo properties baru di facade Database: sessions, artists, genres, library). auth.py->SessionRepository, ws_queue.py->ArtistRepository+GenreRepository (mixed 2 domain dalam 1 file), artist_selector.py/RadioMode->ArtistRepository+LibraryRepository (mixed 2 domain). Tambah properti conn publik di ArtistRepository & LibraryRepository utk liveness-check yang sudah ada sebelumnya. websocket.py (sebelumnya frozen) diedit di call-site dispatch (izin eksplisit user, bukan spontan) utk narrow db->db.sessions / db.artists,db.genres. Discovery/download/cache command tetap pakai db penuh (butuh T2.2d).

---

## PATCH-2026-07-18-081

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/__init__.py`
- `server/services/stream_prefetch.py`
- `server/app.py`
- `server/handlers/http.py`
- `tests/unit/server/handlers/test_http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T2.2b: migrasi konsumen domain track yang aman (StreamPrefetchService, serve_stream di http.py) ke TrackRepository langsung via db.tracks property baru di facade Database. resolver.py/event_listeners.py/ws_download.py/track_loader.py/track_ended_ops.py TIDAK dinarrow di task ini — resolver.db dipakai lintas-domain (StreamResolverPort.db bertipe DatabasePort penuh, dipakai controller.py utk record_completion/record_skip [artis] dan event_listeners.py/ws_download.py utk instansiasi DiscoverService inline [discover]); narrow resolver.py baru aman setelah T2.2c (artist) dan T2.2d (discover) beres, dan controller.py sendiri frozen (butuh T2.3 utk disentuh).

---

## PATCH-2026-07-18-080

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/db.py`
- `persistence/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T2.2a: Ekstrak lifecycle koneksi Database ke persistence/db.py (DatabaseConnection sudah ada sejak sebelumnya; pindahkan _migrate_songs_unique_constraint ke sana juga), Database jadi facade tipis

---

## PATCH-2026-07-18-079

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Hapus 6 file alias backward-compat setelah semua konsumen dipindah ke sumber asli

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `scratch/check_db.py`
- `tests/conftest.py`
- `tests/integration/conftest.py`
- `tests/unit/core/test_ports.py`
- `tests/unit/test_main.py`
- `engine/radio_engine.py`
- `engine/mpv_controller.py`
- `engine/ytdlp_client.py`
- `cache/db.py`
- `plugins/lyrics.py`
- `launcher/gui.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Hapus 6 file alias backward-compat setelah semua konsumen dipindah ke sumber asli

---

## PATCH-2026-07-18-078

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Luruskan import di main

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `main.py`
- `engine/playback/controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Luruskan import di main.py dan controller.py ke sumber asli (persistence, adapters.mpv, adapters.ytdlp, engine.radio), file alias masih ada sebagai fallback

---

## PATCH-2026-07-18-077

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pindahkan admin_password

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `.gitignore`
- `launcher/gui/auth_panel.py`
- `tests/unit/launcher/gui/test_auth_panel.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pindahkan admin_password.txt ke instance/ (di luar tracking git) dan perluas .gitignore

---

## PATCH-2026-07-18-076

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Fase 0 selesai: buat branch refactor/roadmap, catat baseline pytest (558 passed, 1 pre-existing fai…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/STATUS.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Fase 0 selesai: buat branch refactor/roadmap, catat baseline pytest (558 passed, 1 pre-existing failed, 6 skipped) dan baseline lint-imports (7 kept, 0 broken) di docs/STATUS.md

---

## PATCH-2026-07-18-075

**Tanggal:** 2026-07-18
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** fix bug tools patchloh yang gagal mengurutkan patch dan membuat patch tidak increment jadi jadi 001…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `patchlog.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
fix bug tools patchloh yang gagal mengurutkan patch dan membuat patch tidak increment jadi jadi 001 bukan meneruskan id yang ada

---

## PATCH-2026-07-17-074

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** merapikan dokumen patchlog

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `PATCHLOG.MD`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
merapikan dokumen patchlog

---

## PATCH-2026-07-17-073

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** UI/UX revamp tab discover (progressive disclosure hashtag/list, role-gate access, keyboard accessib…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/ws_discovery.py`
- `web/static/js/render/discover-tab.js`
- `web/static/js/events/click-delegation-events.js`
- `web/static/index.html`
- `web/static/css/components/discover-cards.css`
- `web/static/js/render/discover-personalize.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
UI/UX revamp tab discover (progressive disclosure hashtag/list, role-gate access, keyboard accessibility, filter scope)

---

## PATCH-2026-07-17-072

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menyelaraskan nama direktori dan modul internal dari `scripts/` menjadi `automation/` di seluruh do…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `AI_CONTEXT.md`
- `automation/**/*.py`
- `automation/shared/skip_dirs.py`
- `automation/shared/arch_rules.py`
- `automation/find_owner.py`
- `docs/*.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menyelaraskan nama direktori dan modul internal dari `scripts/` menjadi `automation/` di seluruh dokumentasi dan docstring file Python. Juga menghapus blok instruksi peringatan migrasi di `AI_CONTEXT.md` sesuai dengan instruksi yang tertera di sana.

---

## PATCH-2026-07-17-071

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Melanjutkan `PATCH-2026-07-17-070` (backend-only) sesuai `discover-tab-frontend-handoff

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/dom.js`
- `web/static/js/render/discover-personalize.js`
- `web/static/css/components/discover-cards.css`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/index.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Melanjutkan `PATCH-2026-07-17-070` (backend-only) sesuai `discover-tab-frontend-handoff.md`. Semua data personalisasi yang sudah dikirim backend kini benar-benar sampai ke UI dan bisa dipakai user. 1. **`server/handlers/websocket.py`** — izin eksplisit diberikan user (file ini *restricted* per `AI_CONTEXT.md`). Ditambah 1 baris: `"get_artist_detail"` ke `DISCOVERY_CMDS`, sehingga action yang sudah diimplementasi di `ws_discovery.py` sejak PATCH-070 kini benar-benar reachable dari client. 2. **`web/static/js/store.js`** — tambah default `discover_for_you`, `discover_unheard`, `discover_genre_affinity_genre`, `discover_genre_affinity_artists`, `discover_taste_spectrum`. 3. **`web/static/js/ws.js`** — `case "discover_data"` sekarang menyimpan 5 field baru dari payload + memanggil `renderDiscoverPersonalization()`. Tambah `case "artist_detail"` baru (sebelumnya di-drop diam-diam karena tidak ada `default:` case). 4. **`web/static/js/dom.js`** — register elemen baru: taste bar/legend, filter bar (segmented + chip row), 3 card-row (`rowForYou`, `rowGenreAffinity`, `rowUnheard`), sheet `artistDetailSheet` + cover/nama/tag/track-list/tombol di dalamnya. 5. **`web/static/js/render/discover-personalize.js` (baru, 185 baris).** Semua logic render + interaksi personalisasi: taste bar dari `discover_taste_spectrum` (dengan fallback "Dengarkan beberapa lagu dulu..." kalau kosong), kartu artis generik (cover + nama + genre tag, badge `match_pct` untuk "Untuk Kamu", badge "Baru" + varian `.undiscovered` untuk "Belum Pernah Kamu Dengar"), filter kategori + dekade client-side (dekade dibangun dari nilai `tahun_aktif` aktual yang ada di data, bukan hard-coded), handler tap kartu → `wsSend('get_artist_detail', ...)` → isi & buka sheet saat `handleArtistDetail()` dipanggil dari `ws.js`, tombol "Putar Semua" → reuse `enqueue_artist_songs` dengan role-gate (`store.userRole !== 'admin'` → toast) konsisten dengan pola Discover lain. `discover-tab.js` (sudah lewat ambang 200 baris) **tidak disentuh sama sekali** — tetap fokus ke recent/favorites/cached/hashtag-cloud. 6. **`web/static/css/components/discover-cards.css` (baru).** `.taste-bar`/ `.taste-legend`, `.filter-bar`/`.segmented`/`.chip`, `.artist-card` (+ varian `.undiscovered`), styling konten `.ads-*` untuk artist detail sheet. Genre tag pakai palet kecil kurasi (`--g-pop`, `--g-rock`, dst, didefinisikan lokal di file ini) bukan `hsl(random)`. Tidak ada CSS baru untuk shell sheet — reuse `.settings-sheet` yang sudah ada. 7. **`web/static/index.html`** — markup taste spectrum + filter bar + 3 card-row disisipkan di bawah header Discover, sebelum "Jelajahi Artis"/"Jelajahi Genre" yang sudah ada. Sheet baru `<div class="settings-sheet" id="artist-detail-sheet">` (reuse pola `#action-sheet`/`#help-sheet` + `#main-overlay`). Ditambah 1 link CSS (`discover-cards.css`) dan 1 script tag (`render/discover-personalize.js`). 8. **`web/static/js/events/settings-events.js`** — `closeMainOverlay()` ditambah 1 baris supaya `artistDetailSheet` ikut ketutup saat backdrop di-tap, konsisten dengan sheet lain. 9. **`web/static/js/events/index.js`** — daftarkan `initDiscoverFilterEvents()` di urutan init yang sama dengan `initSettingsEvents()` dkk. **Verifikasi otomatis:** `automation/doctor.py`, `generate_file_index.py`, `generate_report.py` dijalankan bersih untuk file yang disentuh sesi ini (2 FAIL yang tersisa — `engine/playback/controller.py` 464 baris & `.gitignore` hilang — sudah ada sebelum sesi ini, tidak disentuh/diperparah oleh patch ini).

---

## PATCH-2026-07-17-070

**Tanggal:** 2026-07-17
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Eksekusi bagian backend dari `discover-tab-implementation-plan-v2

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/discover_enrich.py`
- `persistence/discover_repo.py`
- `persistence/__init__.py`
- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/persistence/test_discover_repo.py`
- `tests/unit/services/test_discover_service.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `docs/STATUS.md`
- `docs/discover-tab-frontend-handoff.md`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`
- `server/handlers/websocket.py`
- `web/static/js/dom.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Eksekusi bagian backend dari `discover-tab-implementation-plan-v2.md` (v2 dipakai, bukan v1 — lihat alasan di bawah). **Frontend sengaja belum disentuh sama sekali** — task ini eksplisit diminta backend-only, siap dilanjutkan sesi lain oleh frontend designer/programmer. Lihat `docs/STATUS.md` §"Discover Tab Personalization — Backend" untuk ringkasan siap-pakai yang ditujukan buat sesi lanjutan itu. 1. **`persistence/discover_enrich.py` (baru, 78 baris).** `enrich_artists(conn, rows)` — helper bersama: attach `cover` (thumbnail YouTube dari lagu pertama artis, `MIN(id)` bukan `RANDOM()` supaya deterministic/tidak flicker) + `genres` (list tag) ke sekumpulan artist row sekaligus. 2 query total untuk berapa pun jumlah artis (hindari N+1). 2. **`persistence/discover_repo.py` (baru, 242 baris).** `class DiscoverRepository` — **keputusan v2, bukan v1**: v1 rencananya nambah method ini ke `artist_repo.py`/`genre_repo.py` (116/97 baris saat itu), tapi itu akan mendorong keduanya ke zona Waspada (>150 baris) padahal tanggung jawab aslinya cuma click/reward tracking, bukan personalisasi. Jadi repo terpisah, sejajar `LibraryRepository`. Method: `get_bandit_ranked_artists(limit)` ("Untuk Kamu", ranking posterior mean `alpha/(alpha+beta)`, exclude artis yang belum tersentuh bandit sama sekali), `get_unheard_artists(limit)` ("Belum Pernah Kamu Dengar", filter `alpha=beta=1 AND click_count=0`), `get_taste_spectrum(limit=6)` (agregasi genre dari `tracks.play_count + is_favorite*3`, dinormalisasi ke persentase + bucket "Lainnya" untuk sisa genre di luar top-N; `[]` kalau histori kosong), `get_top_genre()` (elemen pertama taste spectrum atau `None`), `get_genre_artists_enriched(genre, limit)`, `get_artist_detail(nama)` (info + genre + hingga 10 lagu, urut by id bukan random, untuk detail sheet yang stabil antar-buka). File ini masuk zona **Waspada** (242 baris, ambang 150-300) — bukan pelanggaran, tapi kalau nanti ada section Discover baru lagi, pertimbangkan pecah per jenis query dulu sebelum tembus 300. 3. **`persistence/__init__.py`:** import + instansiasi `DiscoverRepository` (`self._discover`), delegasi 6 method baru di atas — pola sama persis dengan repo lain yang sudah ada. 4. **`services/discover_service.py`** (161 → 208 baris, tetap zona Waspada tapi belum "wajib pecah"): 5 wrapper method baru — `get_for_you`, `get_unheard`, `get_genre_affinity` (return `{genre, artists}`, `genre=None` kalau histori kosong), `get_taste_spectrum`, `get_artist_detail` — semua delegasi ke facade `Database` seperti method lain di file ini, guard `getattr(self.db, "conn", None)` konsisten dengan pola existing. 5. **`server/handlers/ws_discovery.py`:** action `discover` — `asyncio.gather` diperluas dari 5 jadi 9 query paralel, payload `discover_data` nambah 5 field (`for_you`, `unheard`, `genre_affinity_genre`, `genre_affinity_artists`, `taste_spectrum`). Action baru `get_artist_detail` diimplementasikan lengkap (terima `{artist: nama}`, balas `{type: "artist_detail", data: {...} | null}`). 6. **`server/handlers/websocket.py` — SENGAJA TIDAK DISENTUH.** File ini *restricted* di `AI_CONTEXT.md` ("tidak boleh disentuh tanpa izin eksplisit"). Perubahan yang dibutuhkan cuma 1 baris (tambah `"get_artist_detail"` ke `DISCOVERY_CMDS`), tapi izin eksplisit belum diminta/didapat di sesi ini — jadi **action `get_artist_detail` sudah diimplementasikan di `ws_discovery.py` tapi belum bisa dipanggil sama sekali** lewat WS asli sampai baris itu ditambah. Action `discover` yang sudah diperluas TIDAK terpengaruh blocker ini (sudah ada di `DISCOVERY_CMDS` sebelumnya). 7. **Test (mirror per Prinsip #2):** `tests/unit/persistence/test_discover_repo.py` (baru, 14 test, mencakup semua method + edge case histori kosong/artist tidak ditemukan/cap 10 lagu). `test_discover_service.py` (+12 test untuk 5 wrapper baru). `test_ws_discovery.py` (+4 test: payload personalisasi lengkap, `get_artist_detail` sukses, `get_artist_detail` dengan nama kosong tidak memanggil service — plus 1 test lama diupdate supaya tidak break setelah `gather` diperluas dari 5→9 query). 8. **Automation:** `generate_file_index.py` + `generate_report.py` dijalankan ulang (file baru: `discover_repo.py`, `discover_enrich.py`, `test_discover_repo.py`). `doctor.py` bersih untuk semua yang diubah di patch ini — satu-satunya FAIL yang tersisa (`engine/playback/controller.py` 464 baris) adalah temuan pre-existing dari sesi sebelumnya, tidak disentuh atau diperparah oleh patch ini. **Hasil test:** 522 unit test lulus (naik dari 508 baseline), 0 gagal. `tests/unit/launcher/gui/*` tidak ikut collect di environment eksekusi ini (`ModuleNotFoundError: tkinter`, pre-existing keterbatasan environment, bukan regresi dari patch ini).

---

## PATCH-2026-07-16-069

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Eksekusi penuh `implementation-plan

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `pytest.ini`
- `requirements-dev.txt`
- `main.py`
- `adapters/mpv/observer.py`
- `tests/integration/conftest.py`
- `persistence/db.py`
- `tests/unit/persistence/test_db.py`
- `server/handlers/auth.py`
- `tests/unit/server/handlers/test_auth.py`
- `engine/radio/prefetcher.py`
- `plugins/sponsorblock.py`
- `tests/unit/plugins/test_sponsorblock.py`
- `plugins/lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `core/command_bus.py`
- `tests/unit/core/test_command_bus.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/engine/playback/test_track_ended_ops.py`
- `automation/patchlog.py`
- `docs/PATCHLOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Eksekusi penuh `implementation-plan.md` (hasil verifikasi `summary-1.md`, 16 Juli 2026), batch demi batch. Beberapa item (#1 dedup title radio, #2 race crossfade, #4 metrics token compare, #11 sebagian dead code) ternyata **sudah** diperbaiki sebelumnya di codebase (kemungkinan patch manual terpisah) — diverifikasi ulang, tidak diubah lagi. Item yang benar-benar dieksekusi di sesi ini: 1. **Batch 0 (CI hang):** Tambah `pytest-timeout` (jaring pengaman, 60s/thread) di `pytest.ini` + `requirements-dev.txt`. `main.py` shutdown: `task.cancel()` sekarang diikuti `await asyncio.gather(*tasks, return_exceptions=True)`. `adapters/mpv/observer.py.stop()`: await task sampai tuntas setelah cancel. **Terverifikasi lewat eksekusi nyata** (bukan cuma analisis): baseline suite sebelumnya meninggalkan zombie non-daemon thread (`conftest.py` sampai perlu `os._exit()` paksa); setelah fix, suite exit bersih tanpa paksaan. 2. **Batch 1:** (#3) fast-skip `shutil.which("mpv")` dipindah SEBELUM `db.init()` di `tests/integration/conftest.py` — ditemukan lewat testing bahwa urutan lama (db.init() sebelum skip check) bikin fixture generator skip sebelum `yield`, jadi teardown `db.close()` tidak pernah jalan -> connection thread leak (root cause zombie thread kedua, di luar dugaan awal plan). (#5) `persistence/db.py.close()`: ganti `asyncio.sleep(0.01)` dengan `asyncio.to_thread(worker_thread.join, timeout=1.0)` -- join asli, bukan tebak-tebakan delay. (#4) `server/handlers/auth.py`: hilangkan short-circuit `and` yang skip `verify_password` kalau username salah (celah timing side-channel enumerasi username) — sekarang `verify_password` selalu jalan. (#11) hapus `clear_standby()` (stub `pass`, tak terpakai) di `engine/radio/prefetcher.py`; `check_rate_limit_sync()` & `secrets.compare_digest()` di `http.py` ternyata sudah dibersihkan sebelumnya. `controller.py._last_position_save` ternyata sudah tersambung benar (bukan dead code seperti dugaan plan, tidak diubah). (#12) `main.py:339` bare `except:` -> `except Exception:`. 3. **Batch 2.3 (#7):** `plugins/sponsorblock.py` — ganti window deteksi sempit (`start <= pos <= start+0.6`) yang bisa terlewat kalau progress event melompat, dengan one-directional check (`start <= pos < end`) + flag `_skipped_segments` per-track (direset tiap `fetch_segments`). Perbaiki docstring throttle interval yang salah ("~0.5s" -> "~1.0s"). 4. **Batch 3:** Test baru `tests/unit/engine/playback/test_track_ended_ops.py` (modul sebelumnya nol coverage) — grace-window `_handle_stop()`, dispatch eof/stop/error, `poll_duration`. 5. **Batch 4.1 (#8):** `plugins/lyrics_parser.py` — parser LRC diganti total: dukung multi-timestamp per baris (chorus berulang), skip tag metadata (`[ar:...]`, `[ti:...]`) alih-alih dianggap teks lirik biasa. 6. **Batch 4.2 (#6):** `core/command_bus.py` tambah `reset()` resmi (ganti akses langsung `_handlers.clear()` di `tests/integration/conftest.py`). `engine/playback/controller.py` tambah `dispose()` — unsubscribe 5 handler (termasuk 3 lambda closure yang referensinya kini disimpan sebagai atribut instance agar bisa di-unsubscribe balik), cancel `_fade_task` pending. Didokumentasikan eksplisit kenapa 3 lambda itu sengaja strong-ref (bukan bug WeakMethod). 7. **Bonus (ditemukan saat eksekusi, di luar 12 temuan awal):** `automation/patchlog.py.parse_entries()` — regex tunggal dengan beberapa `.*?` + `re.DOTALL` di-scan ke seluruh file (35KB, 28 entry berulang) menyebabkan catastrophic backtracking, hang tak terhingga (dikonfirmasi lewat eksekusi langsung dengan timeout). Diganti dengan split per-entry (separator `\n\n---\n\n`) dulu, baru regex sederhana per-chunk. 8. **Tidak dieksekusi (sesuai arahan plan sendiri):** #10 (tombol "prev" / forward-stack) — butuh keputusan produk dulu, belum diajukan ke user di sesi ini. `test_radio_flow.py` mock network (0.4, opsional/prioritas rendah) — tidak disentuh. **Hasil akhir:** 508 passed, 6 skipped (naik dari baseline 475 passed, 6 skipped) — unit + integration (integration tetap skip karena `mpv`/`yt-dlp` tidak terpasang di sandbox). `ruff check` bersih, `mypy` bersih (10 file diubah), `bandit` tanpa temuan baru, coverage total 88%.

---

## PATCH-2026-07-16-068

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** 1

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/mpv/connection.py`
- `adapters/mpv/ipc.py`
- `adapters/mpv/observer.py`
- `adapters/ytdlp/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_download_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_websocket_flow.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/adapters/mpv/test_ipc.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
1. Mengubah mekanisme IPC dari TCP Sockets menjadi Windows Named Pipes (`\\.\pipe\mpv-lunawave`) untuk meningkatkan reliabilitas koneksi dengan proses MPV di OS Windows, menghilangkan limitasi socket exhaustion, dan mengurangi latensi. 2. Memperbaiki *regression* (Zombie non-daemon threads / Timeout) dan *flakiness* di dalam suite tes integrasi akibat perubahan *interface*, serta menyesuaikan timeout ekspektasi dari `yt-dlp`. - **Fix 1 (Pipes IPC):** `MpvConnection` kini melakukan inisialisasi pada `\\.\pipe\mpv-lunawave` alih-alih port TCP `6666`. `MpvObserver` disesuaikan untuk membaca dari pipe yang sama. Seluruh parameter setup TCP di `run_server()` dihilangkan. - **Fix 2 (Integration Test Setup):** `tests/integration/conftest.py` ditambahkan command `command_bus._handlers.clear()` untuk menghindari `RuntimeError` duplikasi handler pada tes yang dijalankan secara berurutan. - **Fix 3 (Test Syncs):** Penyesuaian nama metode (`download_mp3` -> `download_audio`), penambahan field `artist` pada objek `TrackInfo`, perubahan field `file_path` pada `DownloadCompleteEvent` menjadi `track.local_path`, serta update ID video yang *geo-restricted* ke video yang stabil (`jNQXAC9IVRw` - Me at the zoo).

---

## PATCH-2026-07-16-067

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Tiga perbaikan startup latency berurutan berdasarkan analisis mendalam 5-tahap chain dari GUI klik…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `main.py`
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/test_main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Tiga perbaikan startup latency berurutan berdasarkan analisis mendalam 5-tahap chain dari GUI klik "Start" sampai browser dapat diakses. Total estimasi gain: **1.5–25+ detik** tergantung kondisi. - **Fix 1 (Dampak terbesar, 1–20+ detik):** "Resume last playback" dipindah dari critical path ke background task (`safe_create_task`). Sebelumnya, kalau stream URL track terakhir sudah expired >6 jam, `main.py` akan melakukan network request ke YouTube via `yt-dlp` (max 25 detik timeout) *sebelum* `run_server()` dipanggil. Sekarang resume berjalan concurrently — browser bisa connect ke UI sementara resume masih diproses di background. - **Fix 2 (0.3–2 detik):** `mpv.connect()` dipindah dari `asyncio.gather()` blocking ke background task. Web server kini bisa bind port dan menerima koneksi tanpa menunggu MPV spawn + IPC handshake. Koordinasi lewat `asyncio.Event _mpv_ready_event` — resume task menunggu MPV siap (tanpa timeout) sebelum memanggil `play_track()`, tanpa memblok server. - **Fix 3 (0–1 detik, selalu di Windows):** Ganti `await asyncio.sleep(1.0)` blind wait di Windows dengan polling TCP port aktif (50 iterasi × 100ms = max 5 detik, keluar lebih awal begitu MPV siap). Best-case selesai dalam ~100ms, bukan selalu 1000ms. - **Tests:** Update 4 test lama di `test_connection.py` (assertion call count disesuaikan dengan polling behavior baru), tambah 2 test baru untuk polling Windows, tambah 1 test baru `test_run_server_not_blocked_by_mpv` dengan event-based coordination. 11/11 test pass.

---

## PATCH-2026-07-16-066

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Audit menyeluruh pertama kali untuk SELURUH `web/static/js/` (31 file, semua diperiksa baris-per-ba…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/dom.js`
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/player.js`
- `web/static/js/platform/keyboard.js`
- `web/static/js/events/progress-events.js`
- `web/static/js/ws.js`
- `web/static/sw.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Audit menyeluruh pertama kali untuk SELURUH `web/static/js/` (31 file, semua diperiksa baris-per-baris; backend tidak disentuh). 6 bug CONFIRMED (dieksekusi/reproduksi nyata, bukan cuma baca kode) dan beberapa dead-code/minor findings. - **BUG-1 (Kritis, CONFIRMED):** `#vol-slider` ada di `index.html` tapi tidak pernah dipetakan di `dom.js` (`dom.volSlider` selalu `undefined`). Akibatnya seluruh listener drag volume di `transport-events.js` tidak pernah ter-attach (`if (dom.volSlider)` selalu false) dan render/player.js tidak pernah sinkron nilainya — slider volume 100% non-fungsional dari awal. Fix: tambah `volSlider: $("vol-slider")` ke `dom.js`. - **BUG-2 (Kritis, CONFIRMED lewat eksekusi nyata):** `window.safeStorage` cuma expose `.get/.set/.remove` (lihat `utils/toast.js`), tapi `search-input-events.js` memanggil `.getItem/.setItem/.removeItem` gaya `localStorage` yang TIDAK ADA di objek itu. `saveSearchHistory()` throw `TypeError` tak tertangkap, dan karena baris ini dipanggil SEBELUM `wsSend("search", ...)` baik di debounce-input maupun handler Enter, exception ini menghentikan seluruh callback → `wsSend("search")` TIDAK PERNAH terpanggil. Direproduksi dengan skrip Node standalone yang meniru pola kode persis — dikonfirmasi search tidak terkirim. **Dampak: fitur SEARCH mati total di seluruh aplikasi**, bukan cuma riwayat pencarian. Fix: ganti ke `.get/.set/.remove`, bungkus `saveSearchHistory` dengan try/catch sebagai defense-in-depth. - **BUG-3 (Kritis, CONFIRMED):** `render/player.js` (`_renderProgressCore`) memakai `window.audio` untuk logic volume-fade crossfade, tapi `window.audio` TIDAK PERNAH di-assign di manapun (elemen `<audio>` browser diakses lewat `getOrInitAudio()`/`localAudio` di `audio/playback-sync.js`, bukan `window.audio`). Kondisi selalu falsy → seluruh efek fade-out/fade-in volume crossfade untuk output browser adalah dead code, toggle crossfade di Settings tidak berefek pada audio yang sedang main di mode browser. Fix: ganti ke `getOrInitAudio()`. - **BUG-4 (Sedang, CONFIRMED):** `platform/keyboard.js` memanggil `cmd('play')/cmd('next')/cmd('prev')` — fungsi `cmd` tidak pernah didefinisikan di manapun di codebase (grep kosong). `typeof cmd === 'function'` selalu false → ArrowLeft/ArrowRight/Space di desktop cuma `preventDefault()` tanpa efek (fitur mati sejak awal). Kasus `Space` juga duplicate listener dengan `events/keyboard-shortcut-events.js` (yang sudah admin-gated dan benar-benar jalan). Fix: hapus case Space yang duplikat, sambungkan ArrowLeft/ArrowRight langsung ke `wsSend` dengan guard admin. - **BUG-5 (XSS, CONFIRMED):** `search-input-events.js` → `renderSearchHistory()` menyisipkan query pencarian (asal input user, disimpan di localStorage) langsung ke `innerHTML` tanpa escape untuk teks yang tampil (`<span>${q}</span>`) — cuma tanda kutip `"` yang di-escape untuk atribut `data-query`. Query berisi markup HTML/script tersimpan lalu dieksekusi ulang tiap kali riwayat pencarian dirender (stored self-XSS). Fix: pakai `escapeHtml()` untuk teks maupun atribut. - **BUG-6 (Sedang, SUSPECTED — pola dikonfirmasi lewat perbandingan kode, belum direproduksi di device fisik):** `events/progress-events.js` (drag seek bar) tidak punya handler `pointercancel`, tidak seperti drag-reorder queue (`events/queue-events.js`) yang sudah benar menanganinya. Kalau pointer sequence di-cancel OS/browser di tengah drag (gesture back, incoming call, multi-touch) tanpa `pointerup`, `window.isDraggingPb` nyangkut `true` selamanya → progress bar freeze permanen (rAF interpolation loop dan `renderProgress()` sama-sama early-return selama flag itu true), walau playback tetap jalan normal. Fix: tambah handler `pointercancel` yang reset flag + release pointer capture. - **MINOR-1:** `ws.js` — `store.userRole = "admin"` ter-assign 2x berturut-turut di `auth_status` handler (sisa edit sebelumnya, harmless). Fix: hapus baris duplikat. - **MINOR-2:** `sw.js` — `PRECACHE_ASSETS` tidak menyertakan `audio/playback-sync.js` dan `audio/visualizer.js` (script inti pemutar audio browser). SW registration saat ini masih dimatikan di `main.js` jadi belum berdampak, tapi akan menyebabkan first-offline-load kehilangan script pemutar audio kalau SW diaktifkan lagi tanpa fix ini. Fix: tambahkan ke daftar precache. - **DEAD CODE (dilaporkan, TIDAK dihapus — di luar scope "fix bug", risiko regresi kalau dihapus tanpa keputusan desain):** - `events/click-delegation-events.js` blok 3 menangani selector `.disc-card, .fav-card, .search-result-item` — tidak ada kode render manapun (discover-tab.js, search.js) yang menghasilkan elemen dengan class ini (semua pakai `.sr-item`). Blok ini 100% unreachable, kemungkinan sisa refactor/rename lama. - `audio/visualizer.js`: `startVisualizerLoop()`/`resumeVisualizerLoop()` (visualizer asli berbasis Web Audio API `analyser`/`dataArray`) tidak pernah dipanggil dari manapun, dan `analyser`/`dataArray` (dideklarasikan di `playback-sync.js`) tidak pernah di-assign (tidak ada `createAnalyser()`/`createMediaElementSource()`). `initAudio()` cuma memanggil `startFakeBeatLoop()` (efek beat berbasis timer, bukan analisis audio asli) — implementasi analyser sepenuhnya mati, tergantikan tanpa dibersihkan. - `transport-events.js` mereferensikan `dom.btnStop` — tidak ada elemen `#btn-stop` di `index.html` dan tidak dipetakan di `dom.js`; guard `if (dom.btnStop)` membuat ini no-op aman, Stop tetap bisa diakses lewat `ss-stop-btn` di Settings sheet yang sudah benar. **Verifikasi:** `vitest run` 14/14 tetap passed (3 file test, tidak ada regresi), `node --check` bersih untuk semua 7 file yang diedit, reproduksi manual (skrip Node standalone) mengkonfirmasi BUG-2 sebelum & sesudah fix.

---

## PATCH-2026-07-16-065

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Full-codebase audit (breadth scan seluruh package + deep-dive area berisiko tinggi: core/event_bus

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/connection_manager.py`
- `tests/unit/server/test_connection_manager.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Full-codebase audit (breadth scan seluruh package + deep-dive area berisiko tinggi: core/event_bus.py, persistence/db.py, engine/sleep_timer.py, server/handlers/websocket.py, engine/radio/prefetcher.py lock ordering, server/connection_manager.py). Ditemukan CONFIRMED race condition di `ConnectionManager.broadcast()`: `results` dari `asyncio.gather()` dipasangkan (`zip()`) dengan `list(self.active_connections)` yang di-fetch ULANG setelah await, bukan snapshot yang sama dipakai untuk gather(). Kalau ada connect/disconnect konkuren selagi broadcast() masih await (mis. client baru connect, atau client lain di-disconnect independen oleh handler-nya sendiri), index/urutan list itu bisa berubah -> hasil send_str() salah dipasangkan ke ws yang salah -> client SEHAT bisa ikut ke-disconnect secara keliru. Direproduksi nyata (script manual + test suite, gagal 3/3 run di kode lama). Fix: pin SATU snapshot list, dipakai ulang untuk gather() maupun zip(), sehingga urutan selalu align terlepas dari mutasi konkuren pada active_connections.

---

## PATCH-2026-07-16-064

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Audit mendalam pertama untuk `launcher/` (tkinter GUI server manager, sebelumnya belum pernah diaud…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/controller.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app_lifecycle.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Audit mendalam pertama untuk `launcher/` (tkinter GUI server manager, sebelumnya belum pernah diaudit). Dua bug confirmed lewat eksekusi nyata: (1) **Kontrak file `cache/admin_password.txt` tidak sinkron** — `launcher/gui/auth_panel.py` menulis password yang SUDAH di-hash ke file itu, padahal `config.py` (dan `config_security.generate_admin_password()`) membaca isi file sebagai plaintext mentah lalu meng-hash-nya sendiri di setiap startup server. Akibatnya password yang ditampilkan ke user di dialog first-run/reset TIDAK PERNAH cocok dengan hash yang dipakai server untuk verifikasi login — admin lockout total. Dibuktikan lewat skrip reproduksi yang meniru alur `config.py`: `verify_password(raw_password, ADMIN_PASSWORD)` selalu `False`. Fix: `_reset_password()` sekarang menulis raw password (root cause ada di kontrak antar-modul, bukan di `core.security`). (2) **Race destroy vs background thread** — semua callback dari background thread (dependency checker, loop refresh status tiap 2 detik, log writer, restart timer, popup server-ready) memanggil `self.after()`/`app.after()` tanpa guard apapun. Begitu window GUI ditutup sementara thread masih berjalan, callback yang telat crash dengan `RuntimeError: main thread is not in main loop`. Direproduksi nyata lewat Xvfb headless + `threading.excepthook`. Fix: tambah flag `ServerManager._closing` (di-set di `destroy()`) dan helper `_safe_after()` yang dipakai di semua titik pemanggilan `.after()` dari thread/loop; loop `_refresh_status()` juga berhenti reschedule begitu closing. **Catatan tooling:** ditemukan bug tambahan (belum di-fix, di luar scope sesi ini) di `automation/patchlog.py` — `parse_entries()` gagal mem-parse `docs/PATCHLOG.md` yang sudah ada (mengembalikan 0 entri walau ada 63 entri valid), sehingga `patchlog.py add` salah menomori ID baru jadi `-001` dan menimpa `total_entries` jadi `1`. File tidak sengaja sempat tertimpa saat sesi ini dan sudah dipulihkan dari arsip asli sebelum lanjut. **SUSPECTED root cause** (belum diverifikasi lebih lanjut): kemungkinan mismatch regex `ENTRY_RE` terhadap format aktual (spasi/newline ganda) di file nyata — perlu audit terpisah, jangan pakai `patchlog.py add` sampai ini diperbaiki, edit `docs/PATCHLOG.md` manual dulu.

---

## PATCH-2026-07-16-063

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Konfirmasi eksekusi nyata (bukan asumsi baca kode): `songs

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/schema.sql`
- `persistence/__init__.py`
- `data/export_to_sqlite.py`
- `tests/unit/persistence/test_db.py`
- `tests/unit/data/test_export_to_sqlite.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Konfirmasi eksekusi nyata (bukan asumsi baca kode): `songs.youtube_id` punya constraint `UNIQUE` global, padahal lagu kolaborasi/duet (mis. "Separuh Aku" — Peterpan/NOAH/Ariel NOAH) sah dimiliki lebih dari satu artis. Akibatnya `data/export_to_sqlite.py` (dijalankan nyata terhadap `data/artists_enriched.json`) diam-diam membuang lagu itu dari katalog semua artis kecuali yang pertama ditemukan di JSON — 33 `youtube_id` di data nyata terpengaruh, total lagu ter-export turun dari 1000 jadi 963. Root cause bukan di logic exclusion radio (itu tetap sound, karena sudah keyed di `video_id` langsung, bukan pasangan `(artist_id, video_id)`), murni di schema. Fix: ganti constraint jadi composite `UNIQUE(artist_id, youtube_id)` di `persistence/schema.sql` (skema baru) + migrasi rebuild tabel untuk DB lama yang sudah ada di `persistence/__init__.py` (`_migrate_songs_unique_constraint`), plus scope ulang duplicate-check & duration-backfill di `data/export_to_sqlite.py` ke pasangan `(artist_id, youtube_id)`.

---

## PATCH-2026-07-16-062

**Tanggal:** 2026-07-16
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Baseline test suite menemukan 1 test gagal (`test_mpv_connection_connect_windows`), dikonfirmasi le…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Baseline test suite menemukan 1 test gagal (`test_mpv_connection_connect_windows`), dikonfirmasi lewat skrip reproduksi: di `adapters/mpv/connection.py`, `_do_connect()` pada path Windows (`os.name == "nt"`) *selalu* menimpa `self.tcp_port` dengan port dinamis hasil bind ke port 0 — bahkan ketika caller (constructor arg atau env var `YT_PLAYER_MPV_PORT`) sudah men-pin port tertentu. Ini merusak deployment yang butuh port tetap (mis. firewall rule spesifik). Root cause: tidak ada pembeda antara "port default fallback" vs "port yang sengaja dipin". Fix: tambah flag `_port_pinned` (True jika `tcp_port` di-pass eksplisit ke constructor ATAU dari env var), auto dynamic-port selection hanya jalan kalau `_port_pinned` False. Sekalian perbaiki pesan error `MpvConnectionError` yang sebelumnya selalu nampilin `os.environ.get('YT_PLAYER_MPV_PORT', 'N/A')` mentah (misleading — tidak reflect port dinamis aktual yang dipakai saat gagal connect), sekarang pakai `self.tcp_port` yang sebenarnya.

---

## PATCH-2026-07-15-061

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Audit manual (bukan dari automation/, karena `event_graph

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`
- `server/handlers/ws_playback.py`
- `server/handlers/ws_discovery.py`
- `server/handlers/ws_download.py`
- `web/static/index.html`
- `web/static/js/dom.js`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/queue-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/render/discover-tab.js`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `tests/unit/server/handlers/test_ws_download.py`
- `tests/frontend/test_ws-routing.test.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Audit manual (bukan dari automation/, karena `event_graph.py` cs. hanya cek pub/sub event & arsitektur, bukan kelengkapan WS-action↔frontend-wiring) menemukan 5 fitur backend yang "orphan" (tidak reachable dari client) dan 1 dead code, ditemukan bertahap saat implementasi berjalan. - **BUG-1 (Kritis, fitur baru sprint 3.3 tidak pernah tersambung):** Loudness Normalization — pipeline lengkap (`LoudnessService`, `gain_calculator.py`, `CMD_SET_LOUDNESS_NORMALIZATION` di `command_router.py`) sudah ada sejak sprint 3.3, tapi action `set_loudness_normalization` tidak pernah didaftarkan di `PLAYBACK_CMDS`/`handle_playback_command`, dan tidak ada UI toggle sama sekali. Fix: tambah action ke WS routing + toggle di Settings sheet (pola sama seperti Crossfade), termasuk sync `data-on` di `renderSettingsSheet()`. - **BUG-2 (Kritis):** `queue_select` (`CMD_QUEUE_SELECT`) sudah full-implemented & full-tested di backend, tapi `queue-events.js` cuma daftarin click listener untuk `.qi-remove` — klik baris lagu di antrean manual tidak melakukan apapun. Fix: tambah click delegation di `queueList` yang kirim `queue_select` saat item (bukan drag handle/tombol hapus) diklik. - **BUG-3 (Dead code + fitur mati sejak awal):** Drag-to-reorder queue (`_onDragStart` di `queue-events.js`) butuh elemen `.qi-drag` (CSS-nya sudah ada di `queue.css`), tapi `createQueueItemTemplate()` di `render/queue.js` tidak pernah membuat elemen itu — drag-reorder gak pernah bisa dipakai dari awal. Fix: tambah `<span class="qi-drag">` ke template, disembunyikan untuk current-track item (sama seperti tombol hapus). - **BUG-4 (Dead code, query DB sia-sia):** `ws_discovery.py` action `discover` mengambil `ds.get_favorites(15)` tapi hasilnya dibuang — tidak dimasukkan ke payload `discover_data`. Kolom `is_favorite` + `toggle_favorite()` di `persistence/track_repo.py` sudah ada tapi datanya tidak pernah sampai ke client. Fix: masukkan `favorites` ke payload (di `ws_discovery.py` dan `ws_download.py` — dua tempat yang broadcast `discover_data`), tambah section "Favorit" di tab Discover (pola sama seperti "Tersimpan Lokal"). - **Catatan lanjutan (belum dikerjakan, butuh keputusan desain terpisah):** `toggle_favorite()` di persistence masih belum ada command/WS action untuk memicunya (belum ada tombol "like"/heart di UI). Favorit saat ini hanya bisa terisi lewat kolom `play_count`/`is_favorite` yang di-set manual di DB. Fitur "like" penuh (heart button, `CMD_TOGGLE_FAVORITE`) sengaja tidak dibuat di patch ini karena itu fitur baru, bukan bug fix. - **BUG-5 (Dead code sejak awal, ditemukan sampingan):** `dom.discRecent` di `dom.js` menunjuk ke `#discover-recent` yang tidak pernah ada di `index.html` — section "Baru Diputar" di tab Discover selalu `null`/dead. Fix: tambah container `#discover-recent` di `index.html`. - **DITEMUKAN TAPI BELUM DIPERBAIKI (di luar scope patch ini, butuh konfirmasi):** `pytest` penuh menemukan 2 test gagal yang **tidak berkaitan** dengan perubahan patch ini — `test_app_state_defaults` (`core/state.py`: default `sponsorblock_active` seharusnya `True` tapi aktual `False`) dan `test_sponsorblock_on_progress_seeks_past_segment` (`plugins/sponsorblock.py`: seek tidak terpanggil saat posisi masuk segmen). Kedua file tidak disentuh oleh patch ini — kemungkinan regresi lama yang belum ketahuan. Perlu sesi audit terpisah. **Verifikasi:** `ruff check` bersih, `mypy` bersih (4 file tersentuh), `pytest` 456 passed/2 failed-pre-existing/4 skipped, `vitest run` 14/14 passed, `automation/doctor.py` skornya identik dengan sebelum patch (tidak ada regresi arsitektur/dokumentasi/keamanan baru).

---

## PATCH-2026-07-15-060

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Penambahan test yang hilang pasca-implementasi PATCH-058 dan PATCH-059

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_serializers.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Penambahan test yang hilang pasca-implementasi PATCH-058 dan PATCH-059. - `test_websocket.py`: Tambah `test_new_playback_actions_are_routed` (parametrize 5 action: stop, set_sleep_timer, set_speed, set_loop, set_crossfade), `test_cache_commands_are_routed`, `test_unknown_action_does_not_crash`. - `test_serializers.py`: Tambah assert untuk 3 field baru di `state_to_dict` (playback_speed, loop_mode, crossfade_enabled) termasuk verifikasi nilai non-default.

---

## PATCH-2026-07-15-059

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Audit runtime menemukan 3 bug lanjutan setelah PATCH-058

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/serializers.py`
- `web/static/js/render/full-state.js`
- `web/static/js/events/settings-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Audit runtime menemukan 3 bug lanjutan setelah PATCH-058. - **BUG-A (Kritis):** `server/serializers.py` tidak menyertakan `playback_speed`, `loop_mode`, `crossfade_enabled` di payload state WS. Akibatnya toggle crossfade tidak bisa di-sync dari server, speed tidak persist setelah reconnect, loop mode button tidak reflect state server. Fix: tambahkan 3 field ke `state_to_dict()`. - **BUG-B (Kritis):** Kecepatan pemutaran hanya dikirim ke MPV (hanya berlaku untuk output Device). Browser audio (`<audio>`) tidak punya hook ke MPV property. Fix: tambahkan `audio.playbackRate = speed` di `settings-events.js` dan `full-state.js`. - **IMPROVE-C:** Sleep timer tidak punya feedback visual — subtitle hanya menampilkan "15 Menit" statis. Fix: tambahkan countdown timer client-side yang mundur detik per detik dan reset ke "Mati" saat habis.

---

## PATCH-2026-07-15-058

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Audit pasca-implementasi T1–T16 menemukan 4 bug kritis dan 2 bug minor yang menyebabkan beberapa fi…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/events/transport-events.js`
- `engine/queue_manager.py`
- `core/state.py`
- `web/static/js/events/settings-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Audit pasca-implementasi T1–T16 menemukan 4 bug kritis dan 2 bug minor yang menyebabkan beberapa fitur baru tidak berfungsi dari frontend. - **BUG-1 (Kritis):** `PLAYBACK_CMDS` di `server/handlers/websocket.py` tidak mencakup 5 action baru (`stop`, `set_sleep_timer`, `set_speed`, `set_loop`, `set_crossfade`). WebSocket menerima pesan tapi diam-diam mengabaikannya. Fix: tambahkan 5 action ke set. - **BUG-2 (Kritis):** `store.js` tidak punya field `crossfade_enabled`. Fix: tambahkan `crossfade_enabled: false` ke `createStore()`. - **BUG-3 (Kritis):** `transport-events.js` membaca `store.loopMode` (camelCase) padahal store memakai `store.loop_mode` (snake_case). Tombol Repeat selalu cycle ke "track". Fix: rename ke `loop_mode`. - **BUG-4 (Kritis):** `queue_manager.py` punya dead code `pass` di blok `loop_mode == "queue"` saat queue kosong. Fix: hapus blok if/pass yang tidak berguna. - **MINOR-1:** `core/state.py` mendefinisikan `playback_speed` dan `loop_mode` dua kali di dataclass. Fix: hapus duplikat. - **MINOR-2:** `settings-events.js` mendaftarkan listener `sbToggle.click` dua kali, yang kedua mengirim action `toggle_sponsorblock` yang tidak ada handler-nya. Fix: hapus listener duplikat.

---

## PATCH-2026-07-15-057

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T16: Implementasi efek crossfade eksperimental

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/state.py`
- `core/commands.py`
- `engine/command_router.py`
- `engine/playback/mode_ops.py`
- `engine/playback/controller.py`
- `engine/playback/crossfade.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `web/static/js/dom.js`
- `docs/ADR/003-Crossfade.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T16: Implementasi efek crossfade eksperimental. Menambah `crossfade_enabled` di state, command `CMD_SET_CROSSFADE`, pengaturan UI di Settings, fade-out manual 2 detik di `controller.py`, fade-in di `controller.py` saat putar track baru untuk DEVICE output, dan JS client-side volume fade untuk BROWSER output. Refactoring crossfade dilakukan dengan memisahkan logika ke `crossfade.py` untuk menjaga ukuran file `controller.py` di bawah batas.

---

## PATCH-2026-07-15-056

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T15: Penambahan informasi jumlah lagu dan total durasi estimasi secara real-time pada footer panel…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/render/queue.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T15: Penambahan informasi jumlah lagu dan total durasi estimasi secara real-time pada footer panel "Antrean Putar".

---

## PATCH-2026-07-15-055

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T14: Menambahkan log publish (berupa `LogMessageEvent`) yang diekspos ke UI apabila endpoint `/stre…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T14: Menambahkan log publish (berupa `LogMessageEvent`) yang diekspos ke UI apabila endpoint `/stream/<video_id>` menerima respons 403 atau 410 dari upstream.

---

## PATCH-2026-07-15-054

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T13: Menambahkan fitur Loop Mode (off/track/queue)

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/state.py`
- `core/commands.py`
- `engine/queue_manager.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/dom.js`
- `web/static/js/render/player.js`
- `web/static/js/events/transport-events.js`
- `web/static/css/components/player-bar.css`
- `tests/unit/engine/test_queue_manager.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T13: Menambahkan fitur Loop Mode (off/track/queue). Menambah flag di AppState, logic `next()` pada `queue_manager.py`, command WS baru, serta toggle UI button yang disinkronisasi dengan state.

---

## PATCH-2026-07-15-053

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T12: Riwayat pencarian terkini menggunakan safeStorage di sisi client beserta dukungan penghapusan…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/events/queue-events.js`
- `server/handlers/ws_playback.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T12: Riwayat pencarian terkini menggunakan safeStorage di sisi client beserta dukungan penghapusan manual. Juga memperbaiki fitur penghapusan item individual di daftar antrean.

---

## PATCH-2026-07-15-052

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T11: Fitur kontrol kecepatan pemutaran

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/state.py`
- `core/commands.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/render/player.js`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T11: Fitur kontrol kecepatan pemutaran. Menambahkan dropdown kecepatan di Setting, menghubungkannya melalui event WebSocket, serta pengaturan real-time menggunakan `mpv.set_property("speed", value)`.

---

## PATCH-2026-07-15-051

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T10: Implementasi mode Sleep Timer

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/commands.py`
- `engine/sleep_timer.py`
- `engine/command_router.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `tests/unit/engine/test_sleep_timer.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T10: Implementasi mode Sleep Timer. Mengatur waktu tidur dengan opsi countdown, mengintegrasikannya dengan command bus agar memicu auto-stop playback setelah waktu terlampaui, dan menambah test.

---

## PATCH-2026-07-15-050

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** T9: Penambahan handler `ws_cache

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/ws_cache.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `tests/unit/server/handlers/test_ws_cache.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
T9: Penambahan handler `ws_cache.py` untuk mengukur direktori cache MP3 (`config.CACHE_DIR`) dan menghapusnya tanpa menyentuh file statis atau unduhan manual, disertai unit test. Di UI ditambahkan tampilan ukuran disk pada tab Settings.

---

## PATCH-2026-07-15-049

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Implementasi Task T8: Resume posisi playback setelah restart server

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/state.py`
- `persistence/schema.sql`
- `persistence/track_repo.py`
- `persistence/__init__.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Implementasi Task T8: Resume posisi playback setelah restart server. Modifikasi meliputi penambahan kolom `last_position` di tabel `tracks`, method di repositori untuk write/read posisi, `_on_track_progress` di controller untuk menyimpan secara periodik (setiap 10 detik), dan script `main.py` untuk load last state saat startup. Unit test untuk start_paused pada controller telah ditambahkan. Panjang file `controller.py` telah dikompres kembali sehingga lolos pengecekan `<400 baris` doctor.

---

## PATCH-2026-07-15-048

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Implementasi Task T1-T7 Tier 1: Perbaikan bug data integrity hash fallback, precompile regex di sea…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/ytdlp/searcher.py`
- `tests/unit/adapters/ytdlp/test_searcher.py`
- `persistence/schema.sql`
- `plugins/lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `plugins/lyrics_fetcher.py`
- `tests/unit/plugins/test_lyrics_fetcher.py`
- `server/handlers/http.py`
- `tests/unit/server/handlers/test_http.py`
- `server/middleware.py`
- `tests/unit/server/test_middleware.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Implementasi Task T1-T7 Tier 1: Perbaikan bug data integrity hash fallback, precompile regex di searcher, lrc parser, HTTP handler, optimasi regex noise-keyword lirik, dan penggantian list ke deque pada rate limiter. Menambahkan unique index pada `artists.nama` di schema DB.

---

## PATCH-2026-07-15-047

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Mendiagnosa dan menemukan akar masalah "hang 1 jam 54 menit" pada CI pytest

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/testing/integration_testing.md`
- `log.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Mendiagnosa dan menemukan akar masalah "hang 1 jam 54 menit" pada CI pytest. Hang terbukti disebabkan oleh *zombie process* `yt-dlp` pada integration test (`test_download_flow.py`) yang gagal *timeout* akibat pemblokiran IP oleh YouTube di server GitHub Actions, dan tidak di-kill saat *teardown*. Memperbarui panduan integration testing dengan instruksi untuk memastikan `yt-dlp` dibunuh secara eksplisit di *teardown*. Seluruh 435 unit tests (P0-P4) terbukti *green* dan tidak bermasalah.

---

## PATCH-2026-07-15-046

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menambahkan unit test untuk error handling dan WS routing di `server/handlers/websocket

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_artist_selector.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menambahkan unit test untuk error handling dan WS routing di `server/handlers/websocket.py` & `ws_playback.py` (P3) serta fallback prefetch dan radio_next di `engine/radio/engine.py` & `prefetcher.py` (P4) sesuai dengan `PATCH_TEST_COVERAGE.md`.

---

## PATCH-2026-07-15-045

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menambahkan unit test untuk loop event async di `adapters/mpv/observer

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/adapters/mpv/test_observer.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menambahkan unit test untuk loop event async di `adapters/mpv/observer.py` sesuai dengan P2 di `PATCH_TEST_COVERAGE.md` (unknown property change, cleanup path, socket reconnect loop). Coverage keseluruhan naik dari 77.48% menjadi 78.43%.

---

## PATCH-2026-07-15-044

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menambahkan unit test untuk state machine di `engine/playback/controller

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/engine/playback/test_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menambahkan unit test untuk state machine di `engine/playback/controller.py` sesuai dengan P1 di `PATCH_TEST_COVERAGE.md` (race condition, error state, empty queue, rollback). Coverage keseluruhan naik dari 77.10% menjadi 77.48%.

---

## PATCH-2026-07-15-043

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menambahkan unit test untuk fungsi `serve_stream()` di `server/handlers/http

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/server/handlers/test_http.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menambahkan unit test untuk fungsi `serve_stream()` di `server/handlers/http.py` sesuai dengan P0 di `PATCH_TEST_COVERAGE.md`. Coverage keseluruhan naik dari 75.10% menjadi 77.10%.

---

## PATCH-2026-07-15-042

**Tanggal:** 2026-07-15
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Eksekusi integrasi 3 fitur besar secara serentak untuk mematuhi larangan two-stage refactoring: 1

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/schema.sql`
- `core/state.py`
- `persistence/artist_repo.py`
- `core/latency_window.py`
- `config.py`
- `cache/resolver.py`
- `engine/radio/prefetcher.py`
- `engine/loudness/gain_calculator.py`
- `engine/playback/track_loader.py`
- `adapters/mpv/__init__.py`
- `engine/command_router.py`
- `server/serializers.py`
- `main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Eksekusi integrasi 3 fitur besar secara serentak untuk mematuhi larangan two-stage refactoring: 1. Thompson Sampling Bandit untuk Artist Radio. 2. EBU R128 Loudness Normalization. 3. Adaptive Network Prefetch (Latency Window). Fitur dipisah ke service/kelas baru dan controller dimodifikasi untuk injeksi ketergantungan.

---

## PATCH-2026-07-14-041

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Eksekusi P0-P2 dari IMPLEMENTATION_PLAN

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `main.py`
- `config.py`
- `README.md`
- `docs/INDEX.md`
- `engine/download_manager.py`
- `server/handlers/ws_download.py`
- `persistence/__init__.py`
- `launcher/network.py`
- `package.json`
- `.importlinter`
- `.github/workflows/ci.yml`
- `pyproject.toml`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Eksekusi P0-P2 dari IMPLEMENTATION_PLAN.md untuk persiapan Stable Release v1.0.0. Termasuk perbaikan banner password, path downloads, DB migration logging, `shell=False` di network probing, pemblokiran CI gate, metadata `pyproject.toml`, update package metadata, dan setup wheel build di CI.

---

## PATCH-2026-07-14-040

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Finalisasi "stable baseline version" v1

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/STATUS.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Finalisasi "stable baseline version" v1.0.0. Mengubah status item tertunda menjadi ❄️ Frozen (v1.0.0 Baseline) di `STATUS.md`, menambahkan `CHANGELOG.md`, `CONTRIBUTING.md`, dan `SECURITY.md` (Open Source Readiness), dan melakukan tag v1.0.0 pada repositori.

---

## PATCH-2026-07-14-039

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menyeragamkan format docstring pada 145 file menggunakan analisis AST dinamis untuk memastikan kele…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- (tidak ada)

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menyeragamkan format docstring pada 145 file menggunakan analisis AST dinamis untuk memastikan kelengkapan field sesuai standar.

---

## PATCH-2026-07-14-038

**Tanggal:** 2026-07-14
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** automation - all tests and linters passing

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/PATCHLOG.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
automation - all tests and linters passing

---

## PATCH-2026-07-13-037

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Membangun `tests/integration/conftest

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_websocket_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_download_flow.py`
- `scripts/generate_file_index.py`
- `scripts/generate_report.py`
- `scripts/run_all.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Membangun `tests/integration/conftest.py` dengan komponen asli (EventBus, DB, yt-dlp) untuk integration testing. Menambahkan 4 end-to-end flow test (IT-01 sampai IT-04) untuk memastikan fungsionalitas WebSocket, Playback, Radio, dan Download berjalan dengan baik. Selain itu, generator script `generate_file_index.py` direfactor supaya dapat mendeteksi file dan folder secara dinamis tanpa hardcode. Crash encoding cp1252 pada output di terminal Windows juga telah diatasi.

---

## PATCH-2026-07-13-036

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Memindahkan seluruh file dan folder implementasi arsitektur dari `docs/kompas/` ke root dokumentasi…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/kompas/*`
- `docs/Blueprint.md`
- `AI_CONTEXT.md`
- `CONTRIBUTING.md`
- `docs/MIGRATION_GUIDE.md`
- `docs/PATCHLOG.md`
- `docs/STATUS.md`
- `docs/FILE_INDEX.md`
- `scripts/architecture_lint.py`
- `scripts/find_owner.py`
- `scripts/verify_structure.py`
- `tests/conftest.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Memindahkan seluruh file dan folder implementasi arsitektur dari `docs/kompas/` ke root dokumentasi `docs/`. Menghapus folder `docs/kompas/` yang sudah kosong dan memperbarui referensi di seluruh proyek (`AI_CONTEXT.md`, `.py` scripts, `.md` docs). Dokumentasi ini kini menjadi referensi utama karena migrasi telah dinyatakan terealisasi 100%.

---

## PATCH-2026-07-13-035

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Menyelesaikan checklist Tahap 13

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `.importlinter`
- `requirements-dev.txt`
- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `.editorconfig`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Menyelesaikan checklist Tahap 13. Melakukan evaluasi arsitektur berdasarkan `docs/blueprint.md` menggunakan `import-linter`. Hasilnya: 0 pelanggaran (semua dependency contract terpenuhi). Selain itu, semua file standar open source readiness telah ditambahkan.

---

## PATCH-2026-07-13-034

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Melengkapi unit tests Prioritas 2 (Adapter/Plugin/Server logic) menggunakan mocks dan fakes

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/launcher/gui/test_dep_checker.py`
- `tests/unit/server/test_connection_manager.py`
- `tests/unit/server/test_middleware.py`
- `tests/unit/server/test_serializers.py`
- `tests/unit/engine/radio/test_artist_selector.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/plugins/test_lyrics_parser.py`
- `tests/unit/plugins/test_lyrics_sync.py`
- `services/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Melengkapi unit tests Prioritas 2 (Adapter/Plugin/Server logic) menggunakan mocks dan fakes. Menambahkan `services/__init__.py` yang hilang agar test coverage penuh dapat dieksekusi. Total test suite kini berjumlah 295 test case yang lulus penuh.

---

## PATCH-2026-07-13-033

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Melengkapi unit tests Prioritas 1 (Pure Logic / Zero I/O) yang sebelumnya masih *missing* pada fase…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/persistence/test_library_repo.py`
- `tests/unit/engine/radio/test_track_interleaver.py`
- `tests/unit/engine/playback/test_queue_ops.py`
- `tests/unit/engine/playback/test_mode_ops.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Melengkapi unit tests Prioritas 1 (Pure Logic / Zero I/O) yang sebelumnya masih *missing* pada fase 12b. Total 16 test cases ditambahkan dan seluruhnya lulus (`16 passed`).

---

## PATCH-2026-07-13-032

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Setup folder struktur testing, pembuatan *fakes* (LyricsProvider, SponsorBlockProvider), dan modifi…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `tests/unit/adapters/mpv/`
- `tests/unit/engine/radio/`
- `tests/unit/engine/playback/`
- `tests/unit/server/handlers/`
- `tests/unit/server/services/`
- `tests/unit/plugins/`
- `tests/unit/launcher/gui/`
- `tests/integration/`
- `tests/frontend/utils/`
- `tests/fakes/fake_lyrics_provider.py`
- `tests/fakes/fake_sponsorblock_provider.py`
- `tests/conftest.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Setup folder struktur testing, pembuatan *fakes* (LyricsProvider, SponsorBlockProvider), dan modifikasi *fixture* `memory_db` di `conftest.py` sesuai panduan MIGRATION_GUIDE Tahap 12a.

---

## PATCH-2026-07-13-031

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Setup file konfigurasi DevOps/Tooling sesuai MIGRATION_GUIDE tahap 11

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `pyproject.toml`
- `.importlinter`
- `.pre-commit-config.yaml`
- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Setup file konfigurasi DevOps/Tooling sesuai MIGRATION_GUIDE tahap 11.

---

## PATCH-2026-07-13-030

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Memecah monolith frontend (player-events, audio, utils, discover) sesuai tahap 9, dan membereskan p…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/events/*`
- `web/static/js/audio/*`
- `web/static/js/utils/*`
- `web/static/js/render/*`
- `web/static/js/ws.js`
- `web/static/index.html`
- `scripts/verify_docs/checks_docs.py`
- `scripts/architecture_lint.py`
- `scripts/generate_file_index.py`
- `docs/CONSTRAINTS.md`
- `docs/rfc/.keep`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Memecah monolith frontend (player-events, audio, utils, discover) sesuai tahap 9, dan membereskan peringatan `doctor.py`.

---

## PATCH-2026-07-13-029

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Merapikan struktur folder sesuai dengan MIGRATION_GUIDE tahap 8

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `data/export_to_sqlite.py`
- `cache/schema.sql`
- `plugins/lyrics.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Merapikan struktur folder sesuai dengan MIGRATION_GUIDE tahap 8.

---

## PATCH-2026-07-13-028

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Memecah monolith websocket handler dan launcher GUI menjadi komponen diskrit yang sesuai dengan pri…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`
- `server/connection_manager.py`
- `server/handlers/ws_*.py`
- `launcher/gui.py`
- `launcher/gui/app.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Memecah monolith websocket handler dan launcher GUI menjadi komponen diskrit yang sesuai dengan prinsip Single Responsibility.

---

## PATCH-2026-07-13-027

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Memecah monolith controller

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/playback/queue_ops.py`
- `engine/playback/mode_ops.py`
- `engine/playback/controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Memecah monolith controller.py dengan memisahkan mutasi antrean dan pengaturan mode.

---

## PATCH-2026-07-13-026

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Memecah monolith engine/radio_engine

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/radio_engine.py`
- `engine/radio/artist_selector.py`
- `engine/radio/track_interleaver.py`
- `engine/radio/prefetcher.py`
- `engine/radio/engine.py`
- `engine/radio/__init__.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Memecah monolith engine/radio_engine.py berukuran 440 baris menjadi modul terpisah untuk isolasi bug radio mode.

---

## PATCH-2026-07-13-025

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Extract logika integrasi yt-dlp dari `engine/ytdlp_client

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/ytdlp/common.py`
- `adapters/ytdlp/searcher.py`
- `adapters/ytdlp/resolver.py`
- `adapters/ytdlp/downloader.py`
- `adapters/ytdlp/__init__.py`
- `engine/ytdlp_client.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Extract logika integrasi yt-dlp dari `engine/ytdlp_client.py` menjadi modul-modul independen di `adapters/ytdlp/`. Implementasi ini juga menyertakan `ThreadPoolExecutor` yang dibagikan antar komponen dari `YtDlpClient` Facade.

---

## PATCH-2026-07-13-024

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Extract logika koneksi, IPC, dan event loop observasi dari `engine/mpv_controller

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/mpv/connection.py`
- `adapters/mpv/ipc.py`
- `adapters/mpv/observer.py`
- `adapters/mpv/__init__.py`
- `engine/mpv_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Extract logika koneksi, IPC, dan event loop observasi dari `engine/mpv_controller.py` menjadi modul-modul independen di `adapters/mpv/`. Menambahkan pola Facade di `adapters/mpv/__init__.py`. `engine/mpv_controller.py` kini hanya berfungsi sebagai re-export alias untuk backward compatibility.

---

## PATCH-2026-07-13-023

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Extract god-class `cache/db

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `persistence/db.py`
- `persistence/track_repo.py`
- `persistence/session_repo.py`
- `persistence/artist_repo.py`
- `persistence/genre_repo.py`
- `persistence/library_repo.py`
- `persistence/__init__.py`
- `cache/db.py`
- `persistence/schema.sql`
- `scripts/architecture_lint.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Extract god-class `cache/db.py` (388 baris) menjadi repository terpisah di layer `persistence/` (`track_repo`, `artist_repo`, `session_repo`, `genre_repo`, `library_repo`). Mengimplementasikan Facade pattern untuk `Database` di `persistence/__init__.py`. `cache/db.py` diubah menjadi alias re-export agar backward compatible.

---

## PATCH-2026-07-13-022

**Tanggal:** 2026-07-13
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Setup struktur folder target migrasi (`adapters/`, `engine/radio/`, `persistence/`, `launcher/gui/`…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `adapters/__init__.py`
- `engine/radio/__init__.py`
- `persistence/__init__.py`
- `launcher/__init__.py`
- `core/command_bus.py`
- `core/commands.py`
- `config.py`
- `config_security.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Setup struktur folder target migrasi (`adapters/`, `engine/radio/`, `persistence/`, `launcher/gui/`), extract constants `CMD_*` dari `core/command_bus.py` ke `core/commands.py`, dan memisahkan fungsi admin password generation dari `config.py` ke `config_security.py`.

---

## PATCH-2026-07-11-021

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Gabung 7× subprocess dep-check Python menjadi 1×; hapus `sleep`/`ping` artifisial di `start

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `start.sh`
- `start.bat`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Gabung 7× subprocess dep-check Python menjadi 1×; hapus `sleep`/`ping` artifisial di `start.sh` dan `start.bat`.

---

## PATCH-2026-07-11-020

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Hapus OTel span dari `command_bus

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `core/command_bus.py`
- `core/observability.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Hapus OTel span dari `command_bus.py` (tidak ada exporter aktif, 100% sia-sia); hapus setup_tracing dan import OTel dari `observability.py`.

---

## PATCH-2026-07-11-019

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Tambah parameter `include_lyrics` di `state_to_dict()` dan `broadcast_state()`; default False untuk…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/serializers.py`
- `server/services/broadcast_service.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Tambah parameter `include_lyrics` di `state_to_dict()` dan `broadcast_state()`; default False untuk broadcast periodik, True untuk initial snapshot.

---

## PATCH-2026-07-11-018

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** `toggle_pause()` fire-and-forget; broadcast paralel ke semua WS client; parallelkan query Discover…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/websocket.py`
- `engine/playback/controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
`toggle_pause()` fire-and-forget; broadcast paralel ke semua WS client; parallelkan query Discover di action `discover` & `delete_download`.

---

## PATCH-2026-07-11-017

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Tambah `idx_songs_artist_id` pada tabel `songs` untuk JOIN query di Discover/Radio

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `cache/schema.sql`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Tambah `idx_songs_artist_id` pada tabel `songs` untuk JOIN query di Discover/Radio.

---

## PATCH-2026-07-11-016

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Hapus throttle redundant `_on_track_progress` (sudah ditangani di mpv_controller); parallelkan quer…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/event_listeners.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Hapus throttle redundant `_on_track_progress` (sudah ditangani di mpv_controller); parallelkan query Discover di `_on_download_complete`.

---

## PATCH-2026-07-11-015

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** `increment_play_count` dijadikan `safe_create_task` (fire-and-forget) agar tidak menunda playback

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/playback/track_loader.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
`increment_play_count` dijadikan `safe_create_task` (fire-and-forget) agar tidak menunda playback.

---

## PATCH-2026-07-11-014

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Throttle `LyricsUpdatedEvent` (min 0

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `plugins/lyrics.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Throttle `LyricsUpdatedEvent` (min 0.5s antar broadcast); lazy import `syncedlyrics`.

---

## PATCH-2026-07-11-013

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Throttle publish `TrackProgressEvent` ke 1×/detik; parallelkan 3× `observe_property` saat connect

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/mpv_controller.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Throttle publish `TrackProgressEvent` ke 1×/detik; parallelkan 3× `observe_property` saat connect.

---

## PATCH-2026-07-11-012

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Parallelkan `db

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `main.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Parallelkan `db.init()` + `mpv.connect()` via `asyncio.gather`; naikkan interval poller (mpv reconnect 5→30s, connectivity 60→300s); tambah `db_maintenance()` task tiap 6 jam.

---

## PATCH-2026-07-11-011

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** `verify_password()` (PBKDF2 100k iter) dipindah ke `run_in_executor` agar tidak memblokir event loo…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `server/handlers/auth.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
`verify_password()` (PBKDF2 100k iter) dipindah ke `run_in_executor` agar tidak memblokir event loop seluruh client selama proses login.

---

## PATCH-2026-07-11-010

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Lazy import `yt_dlp` di `_extract_sync` & `_download_sync`; tambah `socket_timeout` dan `extractor_…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/ytdlp_client.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Lazy import `yt_dlp` di `_extract_sync` & `_download_sync`; tambah `socket_timeout` dan `extractor_retries` ke `_YDL_OPTS_INFO` untuk mencegah thread zombie saat jaringan buruk.

---

## PATCH-2026-07-11-009

**Tanggal:** 2026-07-11
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pecah `verify_docs

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `scripts/shared/`
- `scripts/verify_docs/`
- `scripts/verify_docs.py`
- `scripts/verify_security.py`
- `scripts/verify_structure.py`
- `scripts/architecture_lint.py`
- `scripts/generate_report.py`
- `scripts/generate_file_index.py`
- `docs/STRUCTURE.md`
- `docs/architecture/folder_structure.md`
- `AI_CONTEXT.md`
- `docs/AI_CONTEXT.md`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pecah `verify_docs.py` (850 baris) menjadi package `verify_docs/`, ekstrak utilitas bersama ke package `shared/`. CLI semua script identik — tidak ada breaking change.

---

## PATCH-2026-07-10-008

**Tanggal:** 2026-07-10
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** `

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `.pre-commit-config.yaml`
- `docs/PATCHLOG.md`
- `docs/devops/tooling.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
`.pre-commit-config.yaml` dipindah dari `scripts/` ke root repo agar pre-commit bisa baca otomatis saat `git commit`.

---

## PATCH-2026-07-10-007

**Tanggal:** 2026-07-10
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Sinkronisasi 5 kontradiksi antara docs dan scripts yang dibuat di sesi sebelumnya

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`
- `docs/STRUCTURE.md`
- `docs/INDEX.md`
- `.pre-commit-config.yaml`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Sinkronisasi 5 kontradiksi antara docs dan scripts yang dibuat di sesi sebelumnya.

---

## PATCH-2026-07-09-006

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Self-host Tabler Icons & hapus Google Fonts CDN

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/index.html`
- `web/static/css/tokens.css`
- `web/static/css/vendor/tabler-icons.min.css`
- `web/static/css/vendor/fonts/*`
- `web/static/sw.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Self-host Tabler Icons & hapus Google Fonts CDN. UI kini berfungsi penuh tanpa internet.

---

## PATCH-2026-07-09-005

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Mengubah logika *download* agar memindahkan (*move*) file langsung ke folder `downloads/` tanpa men…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `engine/download_manager.py`
- `server/handlers/websocket.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Mengubah logika *download* agar memindahkan (*move*) file langsung ke folder `downloads/` tanpa menduplikatnya di `cache/mp3/`.

---

## PATCH-2026-07-09-004

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken ima…

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `web/static/js/render/queue.js`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken image karena  class tidak dihapus saat elemen DOM di-_recycle_.

---

## PATCH-2026-07-09-003

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pembuatan awal dokumentasi knowledge base dari source code scan

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `docs/INDEX.md`
- `docs/STRUCTURE.md`
- `docs/FILE_INDEX.md`
- `docs/PATCHLOG.md`
- `docs/REPORT.md`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pembuatan awal dokumentasi knowledge base dari source code scan.

---

## PATCH-2026-07-09-002

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Pecah monolith `start

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `start.py`
- `launcher/`
- `launcher/__init__.py`
- `launcher/gui.py`
- `launcher/process.py`
- `launcher/network.py`
- `launcher/updater.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Pecah monolith `start.py` menjadi package `launcher/` dengan separation of concerns.

---

## PATCH-2026-07-09-001

**Tanggal:** 2026-07-09
**Timestamp:** -
**Git Branch:** -
**Git Commit:** -
**Type:** Unclassified
**Area:** Unclassified
**Priority:** Unclassified
**Title:** Replace semua identitas legacy (YTGUI, ytgui, bagas

**Reason:** -

**Root Cause:**
-

**Solution:**
-

**Changed Files:**
- `config.py`
- `main.py`
- `core/observability.py`
- `web/static/js/utils.js`
- `web/static/manifest.json`
- `web/static/sw.js`
- `web/static/index.html`
- `scripts/generate_icons.py`

**Changed Symbols:**
- (tidak ada)

**Tests:** -

**Breaking Change:** Unclassified

**Regression Risk:** Unclassified

**Related Patch:** -

**Status:** Unclassified

**Notes:**
Replace semua identitas legacy (YTGUI, ytgui, bagas.fm, YT Termux Player) dengan LunaWave. Zero regresi pada business logic.

