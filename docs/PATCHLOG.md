---

title: LunaWave Patch Log

latest_patch_id: PATCH-2026-07-20-134

total_entries: 134

---



# PATCHLOG.md — LunaWave



> **Format:** Prepend-only (terbaru di atas). Jangan hapus entri sebelumnya.

> **Detail lengkap per sprint:**

> **ID:** setiap entri baru wajib punya ID unik `PATCH-YYYY-MM-DD-NNN` (urut, 3 digit) agar bisa direferensikan dari dokumen lain (mis. `STATUS.md`, `REPORT.md`).

> **File Terdampak:** selalu list per-baris (bukan prosa dipisah koma), supaya AI/tool bisa query "file X pernah diubah di patch mana?".



---


## [2026-07-20] pause_race_condition_fix — FIX-PAUSE-RACE-01: pause auto-play lagi sendiri di jaringan jelek (dilaporkan user, dikonfirmasi lewat eksekusi kode asli sebelum patch). Root cause: optimistic UI update (klik pause -> store.status="PAUSED" instan) dilindungi grace-window waktu TETAP (window.lastToggleTime, 1200ms di ws.js utk progress message, 1500ms terpisah di playback-sync.js utk native pause/play event) yang tujuannya nolak update status server yang datang sebelum server sempat memproses toggle kita. Di jaringan flaky, RTT sering > grace-window itu, jadi progress broadcast BASI (msg.data.status masih status lama, dari sebelum server proses toggle) lolos dan menimpa balik store.status yang baru saja di-set user -> cabang FIX-RADIO-08 di ws.js (awalnya utk recover autoplay-block radio) melihat "status PLAYING tapi audio.paused" -> panggil _resumeAndPlay(audio) tanpa gesture user -> audio kedengaran lanjut main sendiri sebentar sampai broadcast progress yang valid tiba dan mengoreksi lagi. Dikonfirmasi lewat harness Node (vm) yang me-load ws.js + playback-sync.js ASLI (bukan tulis ulang) dan mensimulasikan klik-pause lalu progress basi tiba di t=2000ms: store.status berbalik ke PLAYING dan audio.play() benar-benar terpanggil. Klaim awal soal "ping-pong wsSend ke server" DICABUT setelah diuji — tidak terjadi, karena guard di listener native play sudah anggap store.status === "PLAYING" (sudah kadung ketimpa) jadi tidak resend. Fix: ganti grace-window berbasis WAKTU dengan pending-target tracking (markPendingToggle(target) + isPendingToggleActive(matchStatus) di store.js) — client melacak status APA yang sedang ditunggu konfirmasinya, dan menolak update dari server yang KONTRADIKTIF dengan target itu selama masih menunggu (bukan cuma "belum lewat sekian ms"), dengan safety-valve PENDING_TOGGLE_TIMEOUT_MS=8 detik supaya tidak macet permanen kalau command toggle kita sendiri hilang di jalan. 4 titik yang tadinya manual set window.lastToggleTime (klik tombol pause di transport-events.js; native pause listener, native play listener, dan Media Session _optimisticToggle di playback-sync.js) disatukan lewat helper markPendingToggle() yang sama, menutup inkonsistensi 1200ms vs 1500ms sekaligus. Verifikasi: regression test baru tests/frontend/pause-race.test.js (3 test) jalan terhadap modul ASLI (store.js + ws.js, bukan simulasi) — dibuktikan dua arah: gagal saat logika lama dipasang balik sementara (bug beneran kedeteksi), lulus dengan patch terpasang. Suite lengkap: 19/19 test lulus (ws-routing, store, format, pause-race), tidak ada regresi. Ditemukan juga edge case pas review lanjutan: kalau user pause lalu SEBELUM konfirmasi server datang langsung klik next/prev/pilih track lain, pendingToggleTarget="PAUSED" yang basi ikut nyangkut dan bikin progress message track BARU (LOADING -> PLAYING) salah dianggap kontradiktif -> status macet di LOADING sampai safety-valve 8 detik habis. Fix: wsSend() di ws.js (satu-satunya jalur semua command ke server) clear pendingToggleTarget kalau action-nya next/prev/play_track -- otomatis berlaku ke semua caller (tombol transport, keyboard shortcut, klik track di search/queue, Media Session). Dikonfirmasi reproduksi bug dulu (status stuck di LOADING) dan fix-nya (status lanjut ke PLAYING) lewat harness Node terpisah sebelum ditambahkan sbg test ke-4 di pause-race.test.js. Suite lengkap sekarang 20/20 lulus.

**ID:** `PATCH-2026-07-20-134`

**Tanggal:** 2026-07-20

**Ringkasan:** pause_race_condition_fix — FIX-PAUSE-RACE-01: pause auto-play lagi sendiri di jaringan jelek (dilaporkan user, dikonfirmasi lewat eksekusi kode asli sebelum patch). Root cause: optimistic UI update (klik pause -> store.status="PAUSED" instan) dilindungi grace-window waktu TETAP (window.lastToggleTime, 1200ms di ws.js utk progress message, 1500ms terpisah di playback-sync.js utk native pause/play event) yang tujuannya nolak update status server yang datang sebelum server sempat memproses toggle kita. Di jaringan flaky, RTT sering > grace-window itu, jadi progress broadcast BASI (msg.data.status masih status lama, dari sebelum server proses toggle) lolos dan menimpa balik store.status yang baru saja di-set user -> cabang FIX-RADIO-08 di ws.js (awalnya utk recover autoplay-block radio) melihat "status PLAYING tapi audio.paused" -> panggil _resumeAndPlay(audio) tanpa gesture user -> audio kedengaran lanjut main sendiri sebentar sampai broadcast progress yang valid tiba dan mengoreksi lagi. Dikonfirmasi lewat harness Node (vm) yang me-load ws.js + playback-sync.js ASLI (bukan tulis ulang) dan mensimulasikan klik-pause lalu progress basi tiba di t=2000ms: store.status berbalik ke PLAYING dan audio.play() benar-benar terpanggil. Klaim awal soal "ping-pong wsSend ke server" DICABUT setelah diuji — tidak terjadi, karena guard di listener native play sudah anggap store.status === "PLAYING" (sudah kadung ketimpa) jadi tidak resend. Fix: ganti grace-window berbasis WAKTU dengan pending-target tracking (markPendingToggle(target) + isPendingToggleActive(matchStatus) di store.js) — client melacak status APA yang sedang ditunggu konfirmasinya, dan menolak update dari server yang KONTRADIKTIF dengan target itu selama masih menunggu (bukan cuma "belum lewat sekian ms"), dengan safety-valve PENDING_TOGGLE_TIMEOUT_MS=8 detik supaya tidak macet permanen kalau command toggle kita sendiri hilang di jalan. 4 titik yang tadinya manual set window.lastToggleTime (klik tombol pause di transport-events.js; native pause listener, native play listener, dan Media Session _optimisticToggle di playback-sync.js) disatukan lewat helper markPendingToggle() yang sama, menutup inkonsistensi 1200ms vs 1500ms sekaligus. Verifikasi: regression test baru tests/frontend/pause-race.test.js (3 test) jalan terhadap modul ASLI (store.js + ws.js, bukan simulasi) — dibuktikan dua arah: gagal saat logika lama dipasang balik sementara (bug beneran kedeteksi), lulus dengan patch terpasang. Suite lengkap: 19/19 test lulus (ws-routing, store, format, pause-race), tidak ada regresi. Ditemukan juga edge case pas review lanjutan: kalau user pause lalu SEBELUM konfirmasi server datang langsung klik next/prev/pilih track lain, pendingToggleTarget="PAUSED" yang basi ikut nyangkut dan bikin progress message track BARU (LOADING -> PLAYING) salah dianggap kontradiktif -> status macet di LOADING sampai safety-valve 8 detik habis. Fix: wsSend() di ws.js (satu-satunya jalur semua command ke server) clear pendingToggleTarget kalau action-nya next/prev/play_track -- otomatis berlaku ke semua caller (tombol transport, keyboard shortcut, klik track di search/queue, Media Session). Dikonfirmasi reproduksi bug dulu (status stuck di LOADING) dan fix-nya (status lanjut ke PLAYING) lewat harness Node terpisah sebelum ditambahkan sbg test ke-4 di pause-race.test.js. Suite lengkap sekarang 20/20 lulus.

**File Terdampak:**

- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/events/transport-events.js`
- `web/static/js/audio/playback-sync.js`
- `tests/frontend/pause-race.test.js` [NEW]

---

## [2026-07-20] starfield_and_discover_scrollbar: tambah ambient starfield pure-CSS site-wide + theming scrollbar Discover tab. (1) #content-area (app-shell.css) dikasih background-image 8x radial-gradient kecil (warna rgba(154,160,170,x) sama kaya .radio-hero .star, opacity 0.2-0.35), di-tile 220px x 220px, statis tanpa animasi -- muncul di belakang semua tab (Home/Search/Radio/Discover) tanpa markup baru, index.html tidak disentuh sama sekali (masih locked). Sesi sebelumnya sempat merencanakan pendekatan ini tapi editnya tidak pernah benar-benar tersimpan ke file -- diverifikasi ulang dari awal sebelum implementasi. (2) Scrollbar #tab-discover (discover-cards.css): ditambah ::-webkit-scrollbar (thumb 8px rounded var(--border-3), hover var(--text-3)) + scrollbar-width:thin/scrollbar-color untuk Firefox, gantiin scrollbar default browser yang tidak sesuai tema gelap. (3) Fix 'kurang mentok kanan': #tab-discover scroll sendiri terpisah dari #content-area, tapi ikut aturan .tab-panel (max-width:1200px/1000px + margin auto + padding 40px/32px) sehingga scrollbar jatuh ~79px dari tepi browser asli. Di desktop.css (min-width:1024px) dan landscape.css (tablet landscape), constraint itu dilepas khusus dari #tab-discover sendiri (max-width:none, margin:0, padding hanya bottom 120px untuk player-bar clearance) dan dipindah ke #tab-discover > * (max-width 1200px/1000px + margin auto), memanfaatkan pola existing yang sudah ada di codebase dimana semua direct children #tab-discover (discover-header, taste-block, filter-bar, card-row, section-label-row, sr-item, dst) sudah punya padding horizontal var(--s5)=20px sendiri -- diverifikasi satu-satu lewat grep sebelum implementasi, jadi #discover-cached (satu-satunya child tanpa padding sendiri) tetap aman karena children di dalamnya (.sr-item) juga sudah self-inset. Hasil: scrollbar sekarang flush ke tepi browser, layout visual anak-anaknya tidak berubah. Verifikasi: review manual cascade CSS baris-per-baris (spesifisitas ID vs class + !important); percobaan live-render via Playwright headless gagal karena sandbox network memblokir koneksi localhost (bukan masalah CSS), jadi tidak ada screenshot before/after -- disarankan dicek ulang di browser nyata.

**ID:** `PATCH-2026-07-20-133`

**Tanggal:** 2026-07-20

**Ringkasan:** starfield_and_discover_scrollbar: tambah ambient starfield pure-CSS site-wide + theming scrollbar Discover tab. (1) #content-area (app-shell.css) dikasih background-image 8x radial-gradient kecil (warna rgba(154,160,170,x) sama kaya .radio-hero .star, opacity 0.2-0.35), di-tile 220px x 220px, statis tanpa animasi -- muncul di belakang semua tab (Home/Search/Radio/Discover) tanpa markup baru, index.html tidak disentuh sama sekali (masih locked). Sesi sebelumnya sempat merencanakan pendekatan ini tapi editnya tidak pernah benar-benar tersimpan ke file -- diverifikasi ulang dari awal sebelum implementasi. (2) Scrollbar #tab-discover (discover-cards.css): ditambah ::-webkit-scrollbar (thumb 8px rounded var(--border-3), hover var(--text-3)) + scrollbar-width:thin/scrollbar-color untuk Firefox, gantiin scrollbar default browser yang tidak sesuai tema gelap. (3) Fix 'kurang mentok kanan': #tab-discover scroll sendiri terpisah dari #content-area, tapi ikut aturan .tab-panel (max-width:1200px/1000px + margin auto + padding 40px/32px) sehingga scrollbar jatuh ~79px dari tepi browser asli. Di desktop.css (min-width:1024px) dan landscape.css (tablet landscape), constraint itu dilepas khusus dari #tab-discover sendiri (max-width:none, margin:0, padding hanya bottom 120px untuk player-bar clearance) dan dipindah ke #tab-discover > * (max-width 1200px/1000px + margin auto), memanfaatkan pola existing yang sudah ada di codebase dimana semua direct children #tab-discover (discover-header, taste-block, filter-bar, card-row, section-label-row, sr-item, dst) sudah punya padding horizontal var(--s5)=20px sendiri -- diverifikasi satu-satu lewat grep sebelum implementasi, jadi #discover-cached (satu-satunya child tanpa padding sendiri) tetap aman karena children di dalamnya (.sr-item) juga sudah self-inset. Hasil: scrollbar sekarang flush ke tepi browser, layout visual anak-anaknya tidak berubah. Verifikasi: review manual cascade CSS baris-per-baris (spesifisitas ID vs class + !important); percobaan live-render via Playwright headless gagal karena sandbox network memblokir koneksi localhost (bukan masalah CSS), jadi tidak ada screenshot before/after -- disarankan dicek ulang di browser nyata.

**File Terdampak:**

- `web/static/css/layout/app-shell.css`
- `web/static/css/components/discover-cards.css`
- `web/static/css/platform/desktop.css`
- `web/static/css/platform/landscape.css`

---

## [2026-07-20] radio_toggle_redesign — HOTFIX (real-device report, screenshot bug): .radio-hero collapse ke sliver ~50px saat Radio ON dengan daftar 'All Stations' terisi. Root cause BUKAN RFC lama (§2, min-height vs teks 2 baris) -- ini bug flexbox terpisah: .radio-hero adalah flex item di dalam .tab-panel (nav.css: display:flex; flex-direction:column; height:100%), sementara yang scroll adalah #content-area (app-shell.css: flex:1; overflow-y:scroll), bukan .tab-panel itu sendiri. Begitu 'All Stations' terisi (radio ON) dan total tinggi children .tab-panel (hero + list) melebihi height:100% tsb, flexbox mengecilkan children sesuai flex-shrink (default:1) SEBELUM #content-area sempat scroll -- height:322px fixed saja tidak melindungi karena flex-basis tetap boleh diperas oleh algoritma shrink tanpa flex-shrink:0. Fix: tambah flex-shrink:0 + min-height:322px (backstop) ke .radio-hero di radio-hero.css, comment R2.1 diupdate menjelaskan root cause baru. Diverifikasi via Playwright headless (chromium) mereproduksi struktur nyata index.html + CSS asli, viewport mobile 400x700 dan desktop 1366x660, radio-queue-list diisi item .radio-queue-item sungguhan (bukan simulasi div kosong): SEBELUM fix tinggi .radio-hero jatuh 322px->50px persis begitu daftar terisi (match screenshot 'Radio On' user); SESUDAH fix tetap 322px konsisten di kedua viewport, baik state off/on x kosong/terisi (4 kombinasi diuji eksplisit), dan #content-area tetap scrollable normal (scrollHeight bertambah sesuai jumlah station, tidak clipped). python automation/doctor.py --strict --json -> PASS/100 (tidak ada regresi baru).

**ID:** `PATCH-2026-07-20-132`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — HOTFIX (real-device report, screenshot bug): .radio-hero collapse ke sliver ~50px saat Radio ON dengan daftar 'All Stations' terisi. Root cause BUKAN RFC lama (§2, min-height vs teks 2 baris) -- ini bug flexbox terpisah: .radio-hero adalah flex item di dalam .tab-panel (nav.css: display:flex; flex-direction:column; height:100%), sementara yang scroll adalah #content-area (app-shell.css: flex:1; overflow-y:scroll), bukan .tab-panel itu sendiri. Begitu 'All Stations' terisi (radio ON) dan total tinggi children .tab-panel (hero + list) melebihi height:100% tsb, flexbox mengecilkan children sesuai flex-shrink (default:1) SEBELUM #content-area sempat scroll -- height:322px fixed saja tidak melindungi karena flex-basis tetap boleh diperas oleh algoritma shrink tanpa flex-shrink:0. Fix: tambah flex-shrink:0 + min-height:322px (backstop) ke .radio-hero di radio-hero.css, comment R2.1 diupdate menjelaskan root cause baru. Diverifikasi via Playwright headless (chromium) mereproduksi struktur nyata index.html + CSS asli, viewport mobile 400x700 dan desktop 1366x660, radio-queue-list diisi item .radio-queue-item sungguhan (bukan simulasi div kosong): SEBELUM fix tinggi .radio-hero jatuh 322px->50px persis begitu daftar terisi (match screenshot 'Radio On' user); SESUDAH fix tetap 322px konsisten di kedua viewport, baik state off/on x kosong/terisi (4 kombinasi diuji eksplisit), dan #content-area tetap scrollable normal (scrollHeight bertambah sesuai jumlah station, tidak clipped). python automation/doctor.py --strict --json -> PASS/100 (tidak ada regresi baru).

**File Terdampak:**

- `web/static/css/components/radio-hero.css`

---

## [2026-07-20] radio_toggle_redesign — Sesi 7 (R7.1..R7.3, PENUTUP FITUR "Night Dial"): cleanup CSS lama + regenerasi dokumentasi, entry terpisah dari entry fitur utama sesuai `patchlog_group: "PATCHLOG TERPISAH untuk sesi 7"` di `task_breakdown_radio.yaml`. R7.1: grep ulang dependency `.radio-featured`/`.centerpiece-*`/`.radio-live-badge` (aturan eksekusi #7 di `task_breakdown_radio.yaml`, sesuai RFC docs/rfc/radio_toggle.md §5.2) dikonfirmasi tidak ada referensi tersisa di `web/static/js/` maupun `index.html` (sudah tergantikan total sejak sesi 4). Hapus blok lama dari `web/static/css/components/cards.css`: `.radio-featured`, `.radio-featured::before`, `.radio-featured-inner`, `.radio-centerpiece`, `.centerpiece-icon-wrap`, `.centerpiece-icon`, `.centerpiece-waves` (+ `.left`/`.right`/`span`), `.radio-featured-name`, `.radio-featured-sub`, `.radio-live-badge` (+ `.badge-dot`), dan seluruh varian state `.on`/`:hover`, beserta `@keyframes transmit-radio`, `pulse-live`, `pulse-antenna`, `bounce-wave-1..4` -- total 233 baris terhapus dari `cards.css` (baris ~21-253 versi sebelum sesi ini). `.radio-page-header`/`.radio-page-title`/`.radio-page-sub` di atasnya SENGAJA DIPERTAHANKAN (di luar daftar selector yang ditugaskan untuk dihapus di R7.1, walau saat dicek juga tidak ada referensi pemakaiannya saat ini -- kalau memang dead code, itu di luar scope task ini, dicatat sebagai temuan terpisah, bukan dihapus tanpa izin eksplisit). **Catatan verifikasi grep**: perintah `grep -rn 'centerpiece\\|radio-live-badge\\|radio-featured\\|transmit-radio\\|pulse-antenna\\|bounce-wave' web/static/` masih menyisakan SATU match di `web/static/css/base/animations.css:7` (`@keyframes transmit-radio`) -- diverifikasi ini definisi keyframe LAIN yang tidak terkait (body animasi beda: `scale(1)→scale(2)`+`opacity` vs versi cards.css yang barusan dihapus yang pakai `box-shadow`), sudah tidak dipakai `animation:` manapun (dead code pre-existing, kemungkinan bukan bagian dari fitur radio_toggle_redesign), dan berada di file di luar scope `files:` R7.1 (`web/static/css/components/cards.css` saja) -- TIDAK disentuh, dicatat sebagai temuan terpisah untuk task cleanup lain, bukan bagian dari DoD fitur ini. `python automation/doctor.py --strict --json` -> PASS/100 (5 checker semua PASS: verify_docs, architecture_lint, verify_structure, verify_security, event_graph). R7.2: `python automation/generate_file_index.py` dan `generate_report.py` dijalankan, `docs/FILE_INDEX.md`/`docs/REPORT.md` ter-regenerate mencerminkan penghapusan CSS di atas; `python automation/patchlog.py verify --json` -> 130/130 entry ter-parse bersih (belum termasuk entry ini sendiri), tidak ada entry rusak. R7.3: entry ini sendiri, penutup seluruh fitur `radio_toggle_redesign` (Sesi 1-7): font self-host Fraunces+Space Grotesk (S1, `PATCH-2026-07-20-125` dst), isi penuh `radio-hero.css` dengan `height:322px` fixed yang menutup root cause bug ukuran on/off (S2, `-126`), modul `radio-hero-moon.js` self-contained/terisolasi penuh dari `playback-sync.js` (S3, `-127`), gate `index.html` dengan konfirmasi eksplisit user (S4, `-128`), wiring `renderRadio()` (S5, `-129`), QA headless browser -- 1 bug ditemukan+fix (rAF tidak berhenti saat reduced-motion, S6, `-130`) dan 1 bug ditemukan+didokumentasikan-belum-fix (starfield overflow viewport sempit, DoD R6.2 melarang buka ulang keputusan 322px di task ini), cleanup CSS lama (S7, entry ini). Referensi keputusan produk: R-D1 (label "Radio Mode"), R-D2 (badge "Radio Off"/"Radio On" selalu-visible via CSS, bukan textContent JS), R-D3 (self-host font, bukan CDN), R-D4 (322px final). Lihat `docs/rfc/radio_toggle.md` untuk analisis akar masalah lengkap.

**ID:** `PATCH-2026-07-20-131`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 7 (PENUTUP, R7.1..R7.3): hapus 233 baris CSS lama `.radio-featured`/`.centerpiece-*`/`.radio-live-badge` + keyframes terkait dari `cards.css` setelah grep-ulang dependency (kosong, kecuali 1 keyframe unrelated di file lain, di luar scope, dicatat terpisah); regenerasi `FILE_INDEX.md`/`REPORT.md`; `doctor.py --strict` PASS/100. Menutup seluruh fitur "Night Dial" (Sesi 1-7) -- ringkasan referensi: font self-host (S1), `radio-hero.css` height-fixed (S2), `radio-hero-moon.js` terisolasi (S3), gate `index.html` (S4), wiring (S5), QA + 1 fix reduced-motion (S6), cleanup (S7, entry ini).

**File Terdampak:**

- `web/static/css/components/cards.css`
- `docs/FILE_INDEX.md`
- `docs/REPORT.md`

---


## [2026-07-20] radio_toggle_redesign — Sesi 6 (R6.1..R6.6): QA & verifikasi isolasi, dieksekusi via headless browser (Playwright/Chromium) di sandbox karena tidak ada akses DevTools manual/device fisik -- mpv dan akses internet ke YouTube TIDAK tersedia di sandbox ini, jadi verifikasi playback nyata (>2 menit) di R6.5 tidak bisa dijalankan penuh; sisanya diverifikasi otomatis. R6.1: tinggi `#radio-toggle-btn` diukur 322px identik di kedua state (off/on) dan tetap 322px walau subtitle diganti ke string terpanjang ("Mencari stasiun...") maupun terpendek -- root cause bug lama (RFC §2) terkonfirmasi tertutup. R6.2: diuji lebar 320px/360px/480px + landscape 740x360 -- DITEMUKAN bug starfield overflow batas kartu di 320px (4 star) dan 360px (2 star), serta di landscape 740x360 (tinggi kartu 87px dari platform/landscape.css) hero-name/hero-sub ikut overflow. Sesuai DoD eksplisit R6.2 ("jika ditemukan masalah, catat sebagai bug terpisah, JANGAN ubah keputusan 322px"), bug ini TIDAK diperbaiki di sesi ini -- dicatat sebagai temuan terpisah untuk sesi/task lanjutan, keputusan R-D4 tidak dibuka ulang. R6.3: klik (admin) memicu wsSend("set_mode") & toggle mode dengan benar; keyboard shortcut R (admin) berfungsi sama; guard isTypingContext di keyboard-shortcut-events.js terverifikasi mencegah shortcut R saat fokus di text input; swipe horizontal di atas kartu radio TIDAK memicu wsSend next/prev (guard #radio-toggle-btn di touch.js efektif). R6.4: user non-admin klik kartu -> tidak ada wsSend terkirim, playback_mode tidak berubah (guard role di transport-events.js efektif). R6.5: playback nyata >2 menit tidak bisa diuji (keterbatasan sandbox); sebagai proxy, radio-hero-moon.js diuji terisolasi (tanpa app lain) dengan spam 60x toggle ON/OFF cepat -- dikonfirmasi tidak ada rafId menumpuk (pending rAF = 0 setelah settle, cancelAnimationFrame dipanggil konsisten sebelum reschedule) dan tidak ada console error. R6.6: DITEMUKAN & DIPERBAIKI bug nyata -- `reduceMotion` sebelumnya cuma menonaktifkan transform libration di `render()`, tapi rAF loop `stepCycle`/`stepTween` tetap terus dijadwalkan walau OS-level `prefers-reduced-motion: reduce` aktif (melanggar RFC §5.5 poin 5 & DoD R6.6 "rAF fase bulan fallback ke render statis tanpa loop jalan"). Fix kecil dan terkontain di `goCycling()`/`goTweenToReal()`: kalau `reduceMotion` true, render fase bulan nyata sekali secara statis dan set `mode = "idle"`, tanpa memanggil `requestAnimationFrame` sama sekali -- diverifikasi terisolasi: 0 pemanggilan rAF saat reduced-motion aktif (sebelumnya rAF tetap terjadwal terus-menerus). Fix ini tidak mengubah isolasi RFC §5.4/§6 (re-checked: requestAnimationFrame hanya di modul ini, tidak ada store/wsSend/classList baru, playback-sync.js/player.js tetap tanpa reference ke modul ini). Verifikasi: node --check bersih; python automation/doctor.py --json -> PASS/100 (tidak ada regresi baru). Sesi 7 (cleanup CSS lama) belum dikerjakan.

**ID:** `PATCH-2026-07-20-130`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 6 (R6.1..R6.6, QA via headless browser): tinggi kartu 322px identik off/on terkonfirmasi (R6.1); klik/keyboard/swipe/guard-role berfungsi benar (R6.3, R6.4); rAF isolation stress-test 60x spam toggle bersih tanpa leak (R6.5, proxy -- playback nyata tidak bisa diuji di sandbox); BUG DITEMUKAN+FIX di radio-hero-moon.js -- rAF loop sebelumnya tidak berhenti saat prefers-reduced-motion aktif, sekarang fallback render statis tanpa rAF sama sekali (R6.6). BUG DITEMUKAN, BELUM DIFIX (dicatat terpisah sesuai DoD R6.2) -- starfield overflow di viewport 320/360px dan landscape pendek. doctor.py tetap PASS/100.

**File Terdampak:**

- `web/static/js/render/radio-hero-moon.js`

---


## [2026-07-20] radio_toggle_redesign — Sesi 5 (R5.1): wiring renderRadio() -> modul animasi radio-hero-moon.js, satu-satunya perubahan ke radio-tab.js untuk seluruh fitur (RFC docs/rfc/radio_toggle.md §5.3). radio-tab.js tetap satu-satunya pemilik classList.add/remove("on"/"off") dan dataset.on -- logika itu TIDAK diubah sama sekali. Tambah 1 baris di akhir renderRadio(): typeof-check ke setRadioHeroAnimState(isRadio), hook satu arah yang cuma mengirim boolean, tanpa state lain dibagi. Tambah 1 baris sinkronisasi dom.radioToggleBtn.setAttribute('aria-pressed', ...) di blok classList existing, melengkapi atribut a11y role="button" tabindex="0" yang ditambahkan di markup sesi 4 (R4.1). Tidak ada perubahan lain ke logika classList on/off atau dom.rtSub.textContent yang sudah ada. Verifikasi: node --check bersih; grep radioToggleBtn.classList/dataset.on di seluruh web/static/js/ mengkonfirmasi radio-tab.js tetap satu-satunya file yang menulis state itu; python automation/doctor.py --json -> PASS/100 (baseline tidak berubah). Dengan ini, seluruh Sesi 1-5 dari task_breakdown_radio.yaml selesai: font self-host + skeleton CSS (S1), isi penuh radio-hero.css (S2), modul radio-hero-moon.js self-contained (S3), gate index.html (S4, dengan konfirmasi eksplisit user), wiring renderRadio() (S5). Sesi 6 (QA manual browser) dan Sesi 7 (cleanup cards.css lama) belum dikerjakan -- menunggu instruksi lanjutan.

**ID:** `PATCH-2026-07-20-129`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 5 (R5.1): hook setRadioHeroAnimState(isRadio) dari renderRadio() + sinkronisasi aria-pressed, satu baris tambahan masing-masing, radio-tab.js tetap satu-satunya pemilik state on/off. Menutup Sesi 1-5 fitur "Night Dial" (font, CSS, modul JS animasi, markup index.html, wiring) -- Sesi 6 (QA) & Sesi 7 (cleanup CSS lama) masih pending.

**File Terdampak:**

- `web/static/js/render/radio-tab.js`

---

## [2026-07-20] radio_toggle_redesign — Sesi 4 (R4.1, GATE governance-locked): perubahan index.html untuk fitur "Night Dial", dieksekusi setelah konfirmasi eksplisit user (index.html tercantum di AI_CONTEXT.md sebagai file yang tidak boleh disentuh tanpa izin). Satu-satunya sesi yang menyentuh file locked ini untuk seluruh fitur radio_toggle_redesign, sesuai RFC docs/rfc/radio_toggle.md §5.1/§5.2. Tambah 1 baris <link rel="stylesheet" href="/static/css/components/radio-hero.css"> tepat setelah cards.css; tambah 1 baris <script src="/static/js/render/radio-hero-moon.js?v=1" defer> tepat sebelum radio-tab.js di urutan <script> (dependency dulu, konsisten dengan konvensi typeof-check codebase). Ganti total blok markup #radio-toggle-btn (baseline .radio-featured, badge "LIVE", icon broadcast + centerpiece-waves) dengan markup baru sesuai peta RFC §5.1: id="radio-toggle-btn", data-on, id="rt-sub" DIPERTAHANKAN apa adanya (dipakai touch.js swipe-guard, dom.js, transport-events.js, radio-tab.js -- tidak satupun disentuh); class container jadi radio-hero (bukan radio-featured); nama hero "Radio Mode" (R-D1); badge 2-span "Radio Off"/"Radio On" selalu-visible (R-D2, struktur dari R2.3); markup SVG moon (litGradCool/litGradWarm/softEdge filter, #moonGroup/#moonLitCool/#moonLitWarm dipertahankan supaya cocok dengan query getElementById di radio-hero-moon.js), tuner ticks, freq-label, dan 14 starfield div dari mockup; tambah role="button" tabindex="0" aria-pressed="false" (peningkatan a11y, aria-pressed akan di-sync oleh radio-tab.js di sesi 5). TIDAK diporting: toggle-hint dan section .compare (penjelasan demo, di luar scope produk). div#radio-toggle-wrap dipertahankan apa adanya, tidak disentuh. Verifikasi: grep centerpiece/radio-live-badge/radio-featured di web/static/js/ + index.html kosong total (markup lama tergantikan penuh); id/data-on/rt-sub terkonfirmasi masih ada persis dengan nama sama; python automation/doctor.py --json -> PASS/100; python automation/architecture_lint.py --json -> PASS/100 (tidak ada error baru dibanding baseline sebelum task ini).

**ID:** `PATCH-2026-07-20-128`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 4 (R4.1, gate governance-locked, dieksekusi setelah konfirmasi eksplisit user): satu-satunya sentuhan ke index.html untuk seluruh fitur -- markup #radio-toggle-btn diganti total ke desain "Night Dial" (id/data-on/rt-sub dipertahankan), tambah <link> radio-hero.css dan <script> radio-hero-moon.js. doctor.py & architecture_lint.py tetap PASS 100.

**File Terdampak:**

- `web/static/index.html`

---

## [2026-07-20] radio_toggle_redesign — Sesi 3 (R3.1..R3.4): modul JS baru web/static/js/render/radio-hero-moon.js, self-contained, dibangun bertahap dalam 1 sesi dedicated (RFC docs/rfc/radio_toggle.md §5.3, §5.4 -- bagian paling kritis untuk mencegah regresi hipotesis §3, `playback_sync` error). Belum di-load dari index.html manapun (gate sesi 4). R3.1: porting realPhase(date)/moonPathD(phase)/render(phase) + libration apa adanya dari mockup; SEMUA query elemen (getElementById untuk #radio-toggle-btn, moonLitCool/moonLitWarm/moonGroup) dilakukan di dalam modul ini sendiri, TIDAK ada entry baru ditambah ke dom.js (hindari 2 sumber kebenaran, RFC §5.3); modul terverifikasi bisa di-load standalone tanpa error walau elemen SVG belum ada di DOM (guard null-check eksplisit di render()). R3.2: state machine rAF (stepCycle/stepTween/goCycling/goTweenToReal/easeInOutCubic/shortestDelta) porting apa adanya; SEMUA variabel state (rafId, mode, cycleStartTs, dst) di module-scope lewat closure IIFE, BUKAN di window -- grep window.raf/window.mode/window.cycleStart di file ini kosong; const reduceMotion dipertahankan (rAF JS tidak kena CSS kill-switch global, RFC §5.5 poin 5). R3.3: ekspos SATU fungsi publik window.setRadioHeroAnimState(isOn) yang cuma memanggil goCycling()/goTweenToReal(), tidak return apa pun yang dikonsumsi caller; init render(realPhase(new Date())) sekali saat modul dimuat; HAPUS dari hasil porting: hero.addEventListener('click'/'keydown') (klik tetap 100% milik transport-events.js) dan semua baris sub.textContent (subtitle tetap 100% milik radio-tab.js). R3.4: self-audit checklist isolasi RFC §5.4 dijalankan penuh -- requestAnimationFrame cuma muncul di file baru ini (tidak ada file baru lain yang pakai rAF); grep store./wsSend/resetAnchorClock/setPositionAnchor/classList di file ini kosong (cuma muncul di komentar dokumentasi "TIDAK boleh", bukan kode); playback-sync.js dan player.js dikonfirmasi tidak punya reference apa pun ke radio-hero-moon.js. Verifikasi tambahan: node --check bersih, simulasi load standalone dengan document/window/requestAnimationFrame ter-stub berhasil tanpa error, setRadioHeroAnimState terkonfirmasi ter-expose sebagai function global.

**ID:** `PATCH-2026-07-20-127`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 3 (R3.1..R3.4): modul baru radio-hero-moon.js (astronomi fase bulan, state machine rAF cycling/tweening, API publik setRadioHeroAnimState(isOn)) -- self-contained, module-scoped, self-audit isolasi RFC §5.4 penuh lolos (tidak ada state global bocor, tidak ada coupling ke playback-sync.js/player.js, klik & subtitle tetap 100% milik file lain sesuai RFC §5.3). Belum reachable dari UI -- lanjutan di sesi 4 (gate index.html, wajib konfirmasi eksplisit user).

**File Terdampak:**

- `web/static/js/render/radio-hero-moon.js`

---

## [2026-07-20] radio_toggle_redesign — Sesi 2 (R2.1..R2.4): isi penuh web/static/css/components/radio-hero.css, dibangun bertahap dalam satu sesi dedicated (RFC docs/rfc/radio_toggle.md §4, §5.2). Belum di-link ke index.html manapun (gate sesi 4). R2.1: container .radio-hero (rename dari .hero mockup, hindari bentrok nama generik) dengan height: 322px FIXED (bukan min-height) -- ini yang menutup root cause bug ukuran on/off beda (RFC §2); porting starfield (.star, .shooting-star, @keyframes shootingStarMove) dan .radio-hero.on border/shadow apa adanya. R2.2: moon SVG (.dial-svg, .moon-lit-cool/.moon-lit-warm cross-fade, .moon-group, .moon-glow-wrap, @keyframes moonBreathe), tuner ticks (.tick + @keyframes tickPulse + delay per nth-child, .tick.tuned), freq-label -- verifikasi terprogram: semua @keyframes di file hanya mengubah transform/opacity/filter/stroke/fill (tidak ada width/height/margin/padding, guard reflow RFC §4). R2.3: badge status DEVIASI dari mockup (R-D2) -- .radio-status-badge selalu visible di kedua state (bukan visibility:hidden saat off seperti .onair-tag mockup), markup 2 span teks exclusive (.badge-text-off "Radio Off"/.badge-text-on "Radio On") murni via CSS class .radio-hero.on, TIDAK ada textContent JS di file ini; .hero-name pakai Fraunces (font-family var(--font-display) dari sesi 1) dengan teks final "Radio Mode" (R-D1); .hero-sub/#rt-sub styling only, teks tetap 100% dikontrol radio-tab.js existing. R2.4: audit -- dikonfirmasi tidak ada @media (prefers-reduced-motion) baru ditambah (kill-switch global sudah ada di base/animations.css:52); starfield dijamin tidak overflow visual di lebar berapa pun karena overflow:hidden sudah ada di container sejak R2.1 (bukan fix baru, verifikasi struktural). Reuse token existing dari tokens.css (var(--accent) untuk --moon-glow, var(--text-1)/var(--text-2)/var(--text-3)/var(--r-full)/var(--border-2)) -- tidak ada variable terduplikasi dengan tokens.css maupun skeleton R1.2. Verifikasi: python automation/doctor.py --json -> overall_status PASS, aggregate_score 100 (baseline tidak berubah, tidak ada error baru).

**ID:** `PATCH-2026-07-20-126`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 2 (R2.1..R2.4): isi penuh radio-hero.css (container height:322px fixed, starfield, moon SVG + tuner ticks, badge status 2-state selalu-visible sesuai R-D2, hero-name/hero-sub) dibangun bertahap dalam 1 sesi dedicated. Semua animasi transform/opacity/filter/stroke/fill only (tidak ada reflow di keyframes). Belum reachable dari UI -- lanjutan di sesi 3 (modul JS animasi).

**File Terdampak:**

- `web/static/css/components/radio-hero.css`

---

## [2026-07-20] radio_toggle_redesign — Sesi 1 (R1.1..R1.2): fondasi font self-host + skeleton radio-hero.css. Sesuai task_breakdown_radio.yaml (sumber: docs/rfc/radio_toggle.md), belum menyentuh file lain manapun (radio-hero.css belum di-link di index.html, aset belum reachable dari UI). R1.1: vendor 2 font baru self-host (R-D3) -- Fraunces (italic 500, untuk hero-name "Radio Mode") dan Space Grotesk (400/500/600, untuk label mono/badge/freq-label) -- subset latin saja diambil dari build resmi Fontsource (self-hostable, OFL-1.1) lewat npm registry, BUKAN dari fonts.googleapis.com/fonts.gstatic.com (constraint self-hosted/offline app di CONSTRAINTS.md & AI_CONTEXT.md); total 4 file woff2 ~61.4KB gabungan (di bawah batas 150KB); lisensi dicatat ringkas di web/static/fonts/LICENSE.md. R1.2: skeleton web/static/css/components/radio-hero.css baru -- 4 blok @font-face untuk font R1.1, plus variable baru discoped ke selector .radio-hero (--void, --void-2, --moon-light, --indigo-deep, --static-grey, --font-display, --font-mono) TANPA duplikasi variable yang sudah ada di tokens.css (--moon-glow/--text-1/--text-2/--r-full sengaja tidak didefinisikan ulang, akan reuse var(--accent) dst langsung di rule sesi 2). Verifikasi: grep repo-wide untuk fonts.googleapis.com/fonts.gstatic.com kosong; comm terhadap daftar variable tokens.css tidak menemukan definisi ganda; brace-balance check pada radio-hero.css OK.

**ID:** `PATCH-2026-07-20-125`

**Tanggal:** 2026-07-20

**Ringkasan:** radio_toggle_redesign — Sesi 1 (R1.1..R1.2): fondasi font self-host (Fraunces italic 500, Space Grotesk 400/500/600 via Fontsource/npm, bukan CDN Google Fonts) + skeleton radio-hero.css (baru) dengan @font-face dan variable scoped ke .radio-hero (tidak duplikasi tokens.css). Belum reachable dari UI manapun -- lanjutan di sesi 2 (CSS komponen penuh).

**File Terdampak:**

- `web/static/fonts/fraunces/fraunces-latin-500-italic.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-400-normal.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-500-normal.woff2`
- `web/static/fonts/space-grotesk/space-grotesk-latin-600-normal.woff2`
- `web/static/fonts/LICENSE.md`
- `web/static/css/components/radio-hero.css`

---

## [2026-07-19] Doc cleanup (di luar task_breakdown_agent.yaml, atas permintaan user): perbaiki drift dokumentasi vs kode aktual di docs/backend/persistence.md dan docs/backend/services.md, ditemukan saat audit pasca T-B19. persistence.md: skema tracks/sessions/artists/genres di dokumen sebelumnya tidak cocok dengan persistence/schema.sql aktual (mis. sessions didoc sebagai id/started_at/ended_at/track_count/mode, padahal aktual token/expires_at) -- diganti skema akurat untuk 7 tabel (tracks, sessions, admin_account, artists, genres, artist_genres, songs), tambah tabel artist_genres & songs yang sebelumnya tidak terdokumentasi sama sekali; Repository API diperbaiki total (TrackRepository/ArtistRepository/GenreRepository/LibraryRepository method-nya sebelumnya fiksi/tidak cocok nama method aktual); section Inisialisasi Database diganti dari class Database (sudah dihapus PATCH-2026-07-18-084) ke DatabaseConnection+Repositories aktual; tambah section Cache Resolver (link ke caching.md, hindari duplikasi); Migrasi Skema diperbaiki jadi 2 jalur nyata (loop ALTER TABLE di Repositories.init() + _migrate_songs_unique_constraint di db.py); contoh Testing diganti pakai API upsert_track/get_track yang benar. services.md: command_router.py -- HANDLERS dict fiktif diganti pola CommandRouter.register() aktual dgn CMD_PLAY_TRACK dst; playback/controller.py -- tabel sub-modul diupdate lengkap (queue_controller.py, settings_controller.py, crossfade.py, track_ended_ops.py sebelumnya tidak disebut); radio/engine.py -- alur radio fiktif (artist_selector.select_next -> ytdlp_adapter.search -> track_filter.filter -> queue_manager.enqueue) diganti alur nyata RadioMode (on_activated/_start dengan standby prefetch, next() dengan radio_queue popleft, _backfill_and_standby); queue_manager.py -- method add/remove/reorder/clear fiktif dihapus, diganti catatan bahwa operasi queue nyata ada di engine/playback/queue_ops.py (QueueOps) + queue_controller.py, queue_manager.py sendiri cuma QueueMode.next(); volume_service.py -- contoh kode function bebas diganti method class VolumeService aktual (_on_volume_up/_on_volume_set/_apply_volume, range 0-150 bukan 0-100); discover_service.py -- deskripsi 'rule-based, belum ada ML' diganti (sekarang wrapper DiscoverRepository dengan bandit ranking). Semua path test yang direferensikan diverifikasi ada di disk. doctor.py --strict tetap PASS 100 setelah perubahan (checker tidak menangkap drift semantik ini -- hanya cek struktur/frontmatter/docstring coverage, bukan kecocokan konten kode vs prosa).

**ID:** `PATCH-2026-07-19-124`

**Tanggal:** 2026-07-19

**Ringkasan:** Doc cleanup (di luar task_breakdown_agent.yaml, atas permintaan user): perbaiki drift dokumentasi vs kode aktual di docs/backend/persistence.md dan docs/backend/services.md, ditemukan saat audit pasca T-B19. persistence.md: skema tracks/sessions/artists/genres di dokumen sebelumnya tidak cocok dengan persistence/schema.sql aktual (mis. sessions didoc sebagai id/started_at/ended_at/track_count/mode, padahal aktual token/expires_at) -- diganti skema akurat untuk 7 tabel (tracks, sessions, admin_account, artists, genres, artist_genres, songs), tambah tabel artist_genres & songs yang sebelumnya tidak terdokumentasi sama sekali; Repository API diperbaiki total (TrackRepository/ArtistRepository/GenreRepository/LibraryRepository method-nya sebelumnya fiksi/tidak cocok nama method aktual); section Inisialisasi Database diganti dari class Database (sudah dihapus PATCH-2026-07-18-084) ke DatabaseConnection+Repositories aktual; tambah section Cache Resolver (link ke caching.md, hindari duplikasi); Migrasi Skema diperbaiki jadi 2 jalur nyata (loop ALTER TABLE di Repositories.init() + _migrate_songs_unique_constraint di db.py); contoh Testing diganti pakai API upsert_track/get_track yang benar. services.md: command_router.py -- HANDLERS dict fiktif diganti pola CommandRouter.register() aktual dgn CMD_PLAY_TRACK dst; playback/controller.py -- tabel sub-modul diupdate lengkap (queue_controller.py, settings_controller.py, crossfade.py, track_ended_ops.py sebelumnya tidak disebut); radio/engine.py -- alur radio fiktif (artist_selector.select_next -> ytdlp_adapter.search -> track_filter.filter -> queue_manager.enqueue) diganti alur nyata RadioMode (on_activated/_start dengan standby prefetch, next() dengan radio_queue popleft, _backfill_and_standby); queue_manager.py -- method add/remove/reorder/clear fiktif dihapus, diganti catatan bahwa operasi queue nyata ada di engine/playback/queue_ops.py (QueueOps) + queue_controller.py, queue_manager.py sendiri cuma QueueMode.next(); volume_service.py -- contoh kode function bebas diganti method class VolumeService aktual (_on_volume_up/_on_volume_set/_apply_volume, range 0-150 bukan 0-100); discover_service.py -- deskripsi 'rule-based, belum ada ML' diganti (sekarang wrapper DiscoverRepository dengan bandit ranking). Semua path test yang direferensikan diverifikasi ada di disk. doctor.py --strict tetap PASS 100 setelah perubahan (checker tidak menangkap drift semantik ini -- hanya cek struktur/frontmatter/docstring coverage, bukan kecocokan konten kode vs prosa).

**File Terdampak:**

- `docs/backend/persistence.md`
- `docs/backend/services.md`

---

## [2026-07-19] T-B19 (lanjutan): finalisasi entry CHANGELOG.md untuk login_redesign. Entry [Unreleased] sebelumnya ditulis sebagai draft 'dalam progres' merujuk task_breakdown_agent.yaml -- sekarang Fitur B sudah selesai (T-B1..T-B19), entry difinalisasi: hapus framing draft, tambahkan poin launcher tanpa mekanisme auth sendiri (K5) dan env var override (K4) yang sebelumnya tidak disebut, section Dampak Upgrade (K3) link ke ADR-0008 yang sudah terbit (gantikan link langsung ke threat_model.md#anchor).

**ID:** `PATCH-2026-07-19-123`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B19 (lanjutan): finalisasi entry CHANGELOG.md untuk login_redesign. Entry [Unreleased] sebelumnya ditulis sebagai draft 'dalam progres' merujuk task_breakdown_agent.yaml -- sekarang Fitur B sudah selesai (T-B1..T-B19), entry difinalisasi: hapus framing draft, tambahkan poin launcher tanpa mekanisme auth sendiri (K5) dan env var override (K4) yang sebelumnya tidak disebut, section Dampak Upgrade (K3) link ke ADR-0008 yang sudah terbit (gantikan link langsung ke threat_model.md#anchor).

**File Terdampak:**

- `CHANGELOG.md`

---

## [2026-07-19] T-B19: dokumentasi akhir Fitur B (login_redesign) & regenerasi index. docs/backend/api.md: ganti bagian auth HTTP basi (POST /auth/login, /portal, query-param token di koneksi WS) dengan alur nyata Fitur B -- section baru Autentikasi & Setup mendokumentasikan action WS setup_admin/auth (payload, response setup_status/auth_status), GET /api/setup-required, dan gate require_auth() per-action (bukan lagi gate di level koneksi); tabel Kode Error WebSocket dikoreksi (4001/4002 lama tidak lagi relevan, kegagalan auth sekarang dikirim sebagai pesan bukan close code); route table disamakan dengan server/app.py aktual (/, /admin, /api/stream/{video_id}, /api/setup-required, /health, /metrics). docs/backend/persistence.md: tambah skema admin_account dan AdminAccountRepository (create_admin_account, get_admin_account, admin_account_exists), link ke ADR-0008. docs/security/threat_model.md: sudah diupdate di T-B18 (link ke ADR-0008 terbit). docs/STATUS.md: section baru Status Fitur menyatakan Fitur A (quick_search_discover, done sesi sebelumnya) dan Fitur B (login_redesign, done sesi ini T-B1..T-B19) sama-sama selesai. README.md: bagian Mengakses Antarmuka Web diperbaiki (password admin tidak lagi auto-generate, sekarang lewat Initial Setup) plus catatan upgrade eksplisit (dari T-B6): kredensial lama tidak dimigrasikan otomatis, upgrade = logout paksa + wajib re-setup, link ke ADR-0008. run_all.py + generate_file_index.py + generate_report.py dijalankan ulang; doctor.py --strict PASS penuh; patchlog.py verify tanpa entry rusak.

**ID:** `PATCH-2026-07-19-122`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B19: dokumentasi akhir Fitur B (login_redesign) & regenerasi index. docs/backend/api.md: ganti bagian auth HTTP basi (POST /auth/login, /portal, query-param token di koneksi WS) dengan alur nyata Fitur B -- section baru Autentikasi & Setup mendokumentasikan action WS setup_admin/auth (payload, response setup_status/auth_status), GET /api/setup-required, dan gate require_auth() per-action (bukan lagi gate di level koneksi); tabel Kode Error WebSocket dikoreksi (4001/4002 lama tidak lagi relevan, kegagalan auth sekarang dikirim sebagai pesan bukan close code); route table disamakan dengan server/app.py aktual (/, /admin, /api/stream/{video_id}, /api/setup-required, /health, /metrics). docs/backend/persistence.md: tambah skema admin_account dan AdminAccountRepository (create_admin_account, get_admin_account, admin_account_exists), link ke ADR-0008. docs/security/threat_model.md: sudah diupdate di T-B18 (link ke ADR-0008 terbit). docs/STATUS.md: section baru Status Fitur menyatakan Fitur A (quick_search_discover, done sesi sebelumnya) dan Fitur B (login_redesign, done sesi ini T-B1..T-B19) sama-sama selesai. README.md: bagian Mengakses Antarmuka Web diperbaiki (password admin tidak lagi auto-generate, sekarang lewat Initial Setup) plus catatan upgrade eksplisit (dari T-B6): kredensial lama tidak dimigrasikan otomatis, upgrade = logout paksa + wajib re-setup, link ke ADR-0008. run_all.py + generate_file_index.py + generate_report.py dijalankan ulang; doctor.py --strict PASS penuh; patchlog.py verify tanpa entry rusak.

**File Terdampak:**

- `docs/backend/api.md`
- `docs/backend/persistence.md`
- `docs/STATUS.md`
- `README.md`
- `docs/PATCHLOG.md`

---

## [2026-07-19] T-B18: ADR-0008 — kredensial admin di SQLite, tanpa migrasi otomatis. Menyatukan keputusan K3 (tidak ada migrasi otomatis dari cache/admin_password.txt maupun instance/admin_password.txt, instalasi lama & baru diarahkan ke Initial Setup identik), K4 (env var override LUNAWAVE_ADMIN_PASS/YTGUI_ADMIN_PASS dipertahankan sebagai jalur non-default untuk provisioning non-interaktif, dikonsumsi satu-satunya kali oleh bootstrap.services._seed_admin_account_from_env saat admin_account masih kosong, tidak pernah overwrite akun existing), dan K5 (launcher tanpa mekanisme auth sendiri, tombol Reset Password di launcher/gui/auth_panel.py redirect ke web via webbrowser.open) menjadi satu ADR mengikuti pola 0002-sqlite-over-json-cache.md. Mencatat alternatif yang dipertimbangkan (migrasi otomatis, hapus env var override, launcher pertahankan mekanisme sendiri) beserta alasan penolakan masing-masing, dan konsekuensi eksplisit: user existing wajib re-setup (logout paksa) saat upgrade. docs/security/threat_model.md diupdate agar catatan K3 menunjuk ke ADR-0008 yang sudah terbit, bukan lagi forward-reference.

**ID:** `PATCH-2026-07-19-121`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B18: ADR-0008 — kredensial admin di SQLite, tanpa migrasi otomatis. Menyatukan keputusan K3 (tidak ada migrasi otomatis dari cache/admin_password.txt maupun instance/admin_password.txt, instalasi lama & baru diarahkan ke Initial Setup identik), K4 (env var override LUNAWAVE_ADMIN_PASS/YTGUI_ADMIN_PASS dipertahankan sebagai jalur non-default untuk provisioning non-interaktif, dikonsumsi satu-satunya kali oleh bootstrap.services._seed_admin_account_from_env saat admin_account masih kosong, tidak pernah overwrite akun existing), dan K5 (launcher tanpa mekanisme auth sendiri, tombol Reset Password di launcher/gui/auth_panel.py redirect ke web via webbrowser.open) menjadi satu ADR mengikuti pola 0002-sqlite-over-json-cache.md. Mencatat alternatif yang dipertimbangkan (migrasi otomatis, hapus env var override, launcher pertahankan mekanisme sendiri) beserta alasan penolakan masing-masing, dan konsekuensi eksplisit: user existing wajib re-setup (logout paksa) saat upgrade. docs/security/threat_model.md diupdate agar catatan K3 menunjuk ke ADR-0008 yang sudah terbit, bukan lagi forward-reference.

**File Terdampak:**

- `docs/adr/0008-admin-credentials-in-sqlite.md`
- `docs/security/threat_model.md`

---

## [2026-07-19] T-B16.1..T-B17: Sesi 10 — launcher tanpa mekanisme auth sendiri, tombol Reset Password redirect ke web (K5), review .gitignore/verify_security.py. T-B16.1 hapus launcher/auth_service.py (satu-satunya konsumen: launcher/gui/auth_panel.py; find_owner.py mengonfirmasi file sudah tidak ada). T-B16.2 tulis ulang auth_panel.py: on_reset_password() sekarang cuma buka http://localhost:{server_port} di browser (webbrowser.open), tidak ada lagi generate/simpan password lokal; konsekuensi wajib di luar files resmi task tapi diperlukan agar import tidak patah -- app.py: hapus panggilan handle_first_run (fungsi ini juga sudah tidak ada, launcher tidak lagi punya alur first-run sendiri, web sendiri yang cek /api/setup-required); ui_builder.py: panggilan on_reset_password disederhanakan jadi satu argumen (app). Test disesuaikan: tests/unit/launcher/gui/test_auth_panel.py ditulis ulang total (assert webbrowser.open dipanggil ke URL yang benar, assert tidak ada file instance/ ditulis); tests/unit/launcher/gui/test_app.py -- helper _make_app() berhenti monkeypatch handle_first_run yang sudah dihapus. T-B16.3 manual QA end-to-end dengan server nyata (bukan mock), BASE_DIR sementara, tanpa mpv (tidak tersedia di sandbox, di luar scope jalur auth): (1) boot instalasi baru -> GET /api/setup-required -> {"setup_required": true}, direktori instance/ tidak pernah dibuat; (2) via WS nyata: action setup_admin (username admin) -> {"success": true}, lalu action auth dengan password yang sama -> {"success": true, token diterbitkan}; (3) GET /api/setup-required setelah itu -> {"setup_required": false}; instance/ tetap tidak pernah ada di seluruh skenario -- mengonfirmasi dod T-B16.3 (start server dari launcher -> browser -> setup/login berhasil, tanpa instance/admin_password.txt terlibat). T-B17 review: .gitignore TIDAK diubah (pola cache/admin_password.txt & instance/ sengaja dipertahankan selama masa transisi, sesuai instruksi task); verify_security.py --json -> PASS 100/100 (Credential Ignore PASS, DB Files Ignore PASS). Regresi penuh: 667 passed, 6 skipped (skip krn tkinter tidak ada display di sandbox verifikasi -- python3-tk sendiri terpasang & bisa diimport, cuma tidak ada X server, di luar scope T-B16).

**ID:** `PATCH-2026-07-19-120`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B16.1..T-B17: Sesi 10 — launcher tanpa mekanisme auth sendiri, tombol Reset Password redirect ke web (K5), review .gitignore/verify_security.py. T-B16.1 hapus launcher/auth_service.py (satu-satunya konsumen: launcher/gui/auth_panel.py; find_owner.py mengonfirmasi file sudah tidak ada). T-B16.2 tulis ulang auth_panel.py: on_reset_password() sekarang cuma buka http://localhost:{server_port} di browser (webbrowser.open), tidak ada lagi generate/simpan password lokal; konsekuensi wajib di luar files resmi task tapi diperlukan agar import tidak patah -- app.py: hapus panggilan handle_first_run (fungsi ini juga sudah tidak ada, launcher tidak lagi punya alur first-run sendiri, web sendiri yang cek /api/setup-required); ui_builder.py: panggilan on_reset_password disederhanakan jadi satu argumen (app). Test disesuaikan: tests/unit/launcher/gui/test_auth_panel.py ditulis ulang total (assert webbrowser.open dipanggil ke URL yang benar, assert tidak ada file instance/ ditulis); tests/unit/launcher/gui/test_app.py -- helper _make_app() berhenti monkeypatch handle_first_run yang sudah dihapus. T-B16.3 manual QA end-to-end dengan server nyata (bukan mock), BASE_DIR sementara, tanpa mpv (tidak tersedia di sandbox, di luar scope jalur auth): (1) boot instalasi baru -> GET /api/setup-required -> {"setup_required": true}, direktori instance/ tidak pernah dibuat; (2) via WS nyata: action setup_admin (username admin) -> {"success": true}, lalu action auth dengan password yang sama -> {"success": true, token diterbitkan}; (3) GET /api/setup-required setelah itu -> {"setup_required": false}; instance/ tetap tidak pernah ada di seluruh skenario -- mengonfirmasi dod T-B16.3 (start server dari launcher -> browser -> setup/login berhasil, tanpa instance/admin_password.txt terlibat). T-B17 review: .gitignore TIDAK diubah (pola cache/admin_password.txt & instance/ sengaja dipertahankan selama masa transisi, sesuai instruksi task); verify_security.py --json -> PASS 100/100 (Credential Ignore PASS, DB Files Ignore PASS). Regresi penuh: 667 passed, 6 skipped (skip krn tkinter tidak ada display di sandbox verifikasi -- python3-tk sendiri terpasang & bisa diimport, cuma tidak ada X server, di luar scope T-B16).

**File Terdampak:**

- `launcher/auth_service.py` (dihapus)
- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/ui_builder.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app.py`

---

## [2026-07-19] T-B15.1..T-B15.3: bersih-bersih pasca cut-over kredensial. T-B15.1 find_owner.py config_security.py -> satu-satunya konsumen adalah tests/unit/test_config_security.py (tidak ada konsumen produksi lain; config.py sudah lepas dependency di T-B14.1). T-B15.2 hapus config_security.py & tests/unit/test_config_security.py; print banner PASSWORD ADMIN GENERATED sudah tidak ada sejak T-B14.1 (tidak ada sisa di main.py). docs/FILE_INDEX.md di-regenerate (entry config_security.py basi dihapus otomatis) -- doctor.py --strict sempat FAIL karena ini, sekarang PASS 100 setelah regenerate. T-B15.3 regression: full suite 665 passed/4 skipped (unit+integration, di luar tkinter GUI yang tidak tersedia di sandbox verifikasi); 3 skenario e2e boot manual dengan SQLite nyata (bukan mock) -- (A) instalasi baru tanpa override: admin_account kosong, tidak ada file password ditulis; (B) instalasi lama dengan artifact cache/admin_password.txt sisa pra-redesign tanpa override: perilaku identik skenario A (K3, tidak ada migrasi otomatis, file lama diabaikan bukan dihapus paksa); (C) provisioning non-interaktif via LUNAWAVE_ADMIN_PASS (K4): admin_account ter-seed dengan hash PBKDF2 valid (diverifikasi cocok/tidak-cocok via verify_password), reboot kedua dengan env var berbeda tidak overwrite akun existing (K3). impact.py tetap gagal karena bug lama ImportError collect_py_files di find_owner.py (pre-existing, sudah dicatat sejak T-B14, di luar scope perbaikan sesi ini).

**ID:** `PATCH-2026-07-19-119`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B15.1..T-B15.3: bersih-bersih pasca cut-over kredensial. T-B15.1 find_owner.py config_security.py -> satu-satunya konsumen adalah tests/unit/test_config_security.py (tidak ada konsumen produksi lain; config.py sudah lepas dependency di T-B14.1). T-B15.2 hapus config_security.py & tests/unit/test_config_security.py; print banner PASSWORD ADMIN GENERATED sudah tidak ada sejak T-B14.1 (tidak ada sisa di main.py). docs/FILE_INDEX.md di-regenerate (entry config_security.py basi dihapus otomatis) -- doctor.py --strict sempat FAIL karena ini, sekarang PASS 100 setelah regenerate. T-B15.3 regression: full suite 665 passed/4 skipped (unit+integration, di luar tkinter GUI yang tidak tersedia di sandbox verifikasi); 3 skenario e2e boot manual dengan SQLite nyata (bukan mock) -- (A) instalasi baru tanpa override: admin_account kosong, tidak ada file password ditulis; (B) instalasi lama dengan artifact cache/admin_password.txt sisa pra-redesign tanpa override: perilaku identik skenario A (K3, tidak ada migrasi otomatis, file lama diabaikan bukan dihapus paksa); (C) provisioning non-interaktif via LUNAWAVE_ADMIN_PASS (K4): admin_account ter-seed dengan hash PBKDF2 valid (diverifikasi cocok/tidak-cocok via verify_password), reboot kedua dengan env var berbeda tidak overwrite akun existing (K3). impact.py tetap gagal karena bug lama ImportError collect_py_files di find_owner.py (pre-existing, sudah dicatat sejak T-B14, di luar scope perbaikan sesi ini).

**File Terdampak:**

- `config_security.py`
- `tests/unit/test_config_security.py`
- `docs/FILE_INDEX.md`

---

## [2026-07-19] T-B14.1..T-B14.2: hapus mekanisme legacy auto-generated admin password di config.py (IS_PASSWORD_AUTO_GENERATED, cache/admin_password.txt, chmod, banner). admin_account (SQLite) tetap satu-satunya source of truth untuk login (T-B13.1). Env var override LUNAWAVE_ADMIN_PASS/YTGUI_ADMIN_PASS dipertahankan (K4) lewat symbol baru config.ADMIN_PASSWORD_OVERRIDE, dikonsumsi satu-satunya oleh bootstrap.services._seed_admin_account_from_env() yang seed admin_account sekali saat tabel masih kosong dan tidak pernah overwrite akun existing (K3). main.py: hapus blok banner kredensial yang bergantung ke IS_PASSWORD_AUTO_GENERATED (konsekuensi wajib dari penghapusan simbol tsb, di luar files config.py tapi diperlukan agar import tidak patah). Test suite disesuaikan: tests/unit/test_config.py, tests/unit/bootstrap/test_services.py (3 test baru untuk _seed_admin_account_from_env), tests/conftest.py (hapus workaround LUNAWAVE_ADMIN_PASS default yang sudah tidak relevan). Verifikasi: 666 passed, 4 skipped (skip krn tkinter tidak ada di sandbox verifikasi, di luar scope); doctor.py --strict PASS; impact.py config.py gagal karena bug lama ImportError collect_py_files di find_owner.py (pre-existing, di luar scope T-B14).

**ID:** `PATCH-2026-07-19-118`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B14.1..T-B14.2: hapus mekanisme legacy auto-generated admin password di config.py (IS_PASSWORD_AUTO_GENERATED, cache/admin_password.txt, chmod, banner). admin_account (SQLite) tetap satu-satunya source of truth untuk login (T-B13.1). Env var override LUNAWAVE_ADMIN_PASS/YTGUI_ADMIN_PASS dipertahankan (K4) lewat symbol baru config.ADMIN_PASSWORD_OVERRIDE, dikonsumsi satu-satunya oleh bootstrap.services._seed_admin_account_from_env() yang seed admin_account sekali saat tabel masih kosong dan tidak pernah overwrite akun existing (K3). main.py: hapus blok banner kredensial yang bergantung ke IS_PASSWORD_AUTO_GENERATED (konsekuensi wajib dari penghapusan simbol tsb, di luar files config.py tapi diperlukan agar import tidak patah). Test suite disesuaikan: tests/unit/test_config.py, tests/unit/bootstrap/test_services.py (3 test baru untuk _seed_admin_account_from_env), tests/conftest.py (hapus workaround LUNAWAVE_ADMIN_PASS default yang sudah tidak relevan). Verifikasi: 666 passed, 4 skipped (skip krn tkinter tidak ada di sandbox verifikasi, di luar scope); doctor.py --strict PASS; impact.py config.py gagal karena bug lama ImportError collect_py_files di find_owner.py (pre-existing, di luar scope T-B14).

**File Terdampak:**

- `config.py`
- `bootstrap/services.py`
- `main.py`
- `tests/unit/test_config.py`
- `tests/unit/bootstrap/test_services.py`
- `tests/conftest.py`

---

## [2026-07-19] T-B13.1..T-B13.2: cut-over sumber kredensial login dari config.ADMIN_USERNAME/ADMIN_PASSWORD ke admin_account_repo (SQLite). handle_auth sekarang menerima repos penuh (bukan hanya repos.sessions) untuk akses repos.admin_account. Mitigasi timing side-channel PATCH-2026-07-16-001 dipertahankan via dummy PBKDF2 hash saat admin_account belum ada (instalasi baru). Perubahan izin gate BARU (terpisah dari T-B8) di server/handlers/websocket.py: satu baris pemanggilan handle_auth diteruskan repos, bukan repos.sessions. Regresi T-B13.2: skenario instalasi baru dan instalasi lama kini identik (K3, wajib Initial Setup ulang, tidak ada migrasi otomatis).

**ID:** `PATCH-2026-07-19-117`

**Tanggal:** 2026-07-19

**Ringkasan:** T-B13.1..T-B13.2: cut-over sumber kredensial login dari config.ADMIN_USERNAME/ADMIN_PASSWORD ke admin_account_repo (SQLite). handle_auth sekarang menerima repos penuh (bukan hanya repos.sessions) untuk akses repos.admin_account. Mitigasi timing side-channel PATCH-2026-07-16-001 dipertahankan via dummy PBKDF2 hash saat admin_account belum ada (instalasi baru). Perubahan izin gate BARU (terpisah dari T-B8) di server/handlers/websocket.py: satu baris pemanggilan handle_auth diteruskan repos, bukan repos.sessions. Regresi T-B13.2: skenario instalasi baru dan instalasi lama kini identik (K3, wajib Initial Setup ulang, tidak ada migrasi otomatis).

**File Terdampak:**

- `server/handlers/auth.py`
- `server/handlers/websocket.py`
- `tests/unit/server/handlers/test_auth.py`
- `tests/unit/server/handlers/test_websocket.py`

---

## [2026-07-19] Fitur B (login_redesign) — Sesi 6, T-B10..T-B12.2: CSS #setup-screen + wiring JS + validasi client (parallel_ok, tidak locked, tidak butuh izin tambahan). T-B10: web/static/css/portal.css -- rule #setup-screen (mirror persis #portal-screen: fixed/flex/hidden, toggle lewat class portal-active) dan #setup-submit-btn (mirror #admin-submit-btn, plus state :disabled) ditambahkan; field Confirm Password otomatis konsisten di 3 breakpoint karena reuse .login-input-group/.login-error dan portal.css sendiri tidak punya override per-breakpoint (tidak ada selector 'portal' di platform/*.css). T-B11.1/T-B11.2: web/static/js/portal.js -- fungsi baru initSetupCheck() (async) memanggil GET /api/setup-required SEBELUM memutuskan tampilkan #setup-screen atau #portal-screen, sengaja tidak ditebak murni dari localStorage (kontrak K3: upgrade instalasi lama tanpa migrasi otomatis bisa saja localStorage masih simpan role lama padahal admin_account kosong); fetch gagal (network/non-200) fail-open ke alur login normal (initPortal() tetap dipanggil) supaya user existing tidak pernah terkunci gara-gara check ini sendiri gagal. web/static/js/main.js: init() manggil initSetupCheck() menggantikan initPortal() langsung. web/static/js/dom.js: 8 elemen #setup-screen baru didaftarkan (setupScreen, setupForm, setupUsername, setupPassword, setupConfirmPassword, setupConfirmErrorMsg, setupSubmitBtn, setupErrorMsg). T-B12.1: web/static/js/events/index.js -- fungsi updateSetupSubmitState() disable submit selama password!=confirm (dicek live tiap input, bukan cuma saat submit), listener input pada setup-password & setup-confirm-password, Enter key pada confirm-password men-trigger klik submit kalau tidak disabled. T-B12.2: web/static/js/services/auth.js -- fungsi baru submitSetup(user, pass, confirmPass): validasi ulang match sebagai jaring pengaman (submit seharusnya sudah disabled duluan), lalu wsSend('setup_admin', {username, password}) -- confirmPass TIDAK PERNAH masuk payload, sesuai kontrak T-B5.1 (_validate_setup_input di server/handlers/setup.py memang tidak pernah menerima field ini). web/static/js/ws.js: case baru 'setup_status' di handleServerMessage -- sukses: re-enable submit button, toast, toggle #setup-screen -> #portal-screen (TIDAK auto-login sebagai admin, user login manual pakai kredensial yang baru dibuat); gagal: re-enable submit button, tampilkan msg.data.message di #setup-error-msg, tetap di #setup-screen. Test baru: tests/frontend/ws-routing.test.js -- 2 skenario setup_status (success toggle screen + reset field, failure tetap di setup-screen dengan pesan server) ditambah ke mock dom yang sudah ada; total 16 test frontend (vitest), semua hijau (naik dari 14). Checkpoint end-to-end manual (folder data kosong -> Initial Setup -> submit -> redirect Login -> login berhasil) TIDAK bisa dijalankan sungguhan di browser -- sandbox ini tanpa network/display DAN tanpa mpv/yt-dlp (bahkan fixture app_client integration test butuh keduanya, lihat tests/integration/conftest.py), sama seperti precedent semua sesi sebelumnya (T-B8: 'belum ditest manual di browser sungguhan'). Sebagai gantinya, alur penuh sudah ditelusuri baris-per-baris end-to-end (GET /api/setup-required -> setup_required true -> #setup-screen tampil -> isi form -> validasi match client -> submit -> wsSend('setup_admin') tanpa confirm -> server handle_setup_admin (T-B5, sudah 11+3 skenario unit test hijau) -> setup_status success -> toggle ke #portal-screen -> login manual via action 'auth' existing yang sudah reachable sejak T-B8) dan didukung unit test di kedua sisi (backend: test_setup.py 14 skenario + test_websocket.py; frontend: ws-routing.test.js 16 skenario). Regresi penuh: 663 passed, 6 skipped (skip count sama seperti sesi 5, murni sandbox tanpa mpv/X display, tidak terkait Fitur B). doctor.py --strict PASS 100 semua checker. vitest: 16/16 passed (naik dari 14 baseline sesi 5).

**ID:** `PATCH-2026-07-19-116`

**Tanggal:** 2026-07-19

**Ringkasan:** Fitur B (login_redesign) — Sesi 6, T-B10..T-B12.2: CSS #setup-screen + wiring JS + validasi client (parallel_ok, tidak locked, tidak butuh izin tambahan). T-B10: web/static/css/portal.css -- rule #setup-screen (mirror persis #portal-screen: fixed/flex/hidden, toggle lewat class portal-active) dan #setup-submit-btn (mirror #admin-submit-btn, plus state :disabled) ditambahkan; field Confirm Password otomatis konsisten di 3 breakpoint karena reuse .login-input-group/.login-error dan portal.css sendiri tidak punya override per-breakpoint (tidak ada selector 'portal' di platform/*.css). T-B11.1/T-B11.2: web/static/js/portal.js -- fungsi baru initSetupCheck() (async) memanggil GET /api/setup-required SEBELUM memutuskan tampilkan #setup-screen atau #portal-screen, sengaja tidak ditebak murni dari localStorage (kontrak K3: upgrade instalasi lama tanpa migrasi otomatis bisa saja localStorage masih simpan role lama padahal admin_account kosong); fetch gagal (network/non-200) fail-open ke alur login normal (initPortal() tetap dipanggil) supaya user existing tidak pernah terkunci gara-gara check ini sendiri gagal. web/static/js/main.js: init() manggil initSetupCheck() menggantikan initPortal() langsung. web/static/js/dom.js: 8 elemen #setup-screen baru didaftarkan (setupScreen, setupForm, setupUsername, setupPassword, setupConfirmPassword, setupConfirmErrorMsg, setupSubmitBtn, setupErrorMsg). T-B12.1: web/static/js/events/index.js -- fungsi updateSetupSubmitState() disable submit selama password!=confirm (dicek live tiap input, bukan cuma saat submit), listener input pada setup-password & setup-confirm-password, Enter key pada confirm-password men-trigger klik submit kalau tidak disabled. T-B12.2: web/static/js/services/auth.js -- fungsi baru submitSetup(user, pass, confirmPass): validasi ulang match sebagai jaring pengaman (submit seharusnya sudah disabled duluan), lalu wsSend('setup_admin', {username, password}) -- confirmPass TIDAK PERNAH masuk payload, sesuai kontrak T-B5.1 (_validate_setup_input di server/handlers/setup.py memang tidak pernah menerima field ini). web/static/js/ws.js: case baru 'setup_status' di handleServerMessage -- sukses: re-enable submit button, toast, toggle #setup-screen -> #portal-screen (TIDAK auto-login sebagai admin, user login manual pakai kredensial yang baru dibuat); gagal: re-enable submit button, tampilkan msg.data.message di #setup-error-msg, tetap di #setup-screen. Test baru: tests/frontend/ws-routing.test.js -- 2 skenario setup_status (success toggle screen + reset field, failure tetap di setup-screen dengan pesan server) ditambah ke mock dom yang sudah ada; total 16 test frontend (vitest), semua hijau (naik dari 14). Checkpoint end-to-end manual (folder data kosong -> Initial Setup -> submit -> redirect Login -> login berhasil) TIDAK bisa dijalankan sungguhan di browser -- sandbox ini tanpa network/display DAN tanpa mpv/yt-dlp (bahkan fixture app_client integration test butuh keduanya, lihat tests/integration/conftest.py), sama seperti precedent semua sesi sebelumnya (T-B8: 'belum ditest manual di browser sungguhan'). Sebagai gantinya, alur penuh sudah ditelusuri baris-per-baris end-to-end (GET /api/setup-required -> setup_required true -> #setup-screen tampil -> isi form -> validasi match client -> submit -> wsSend('setup_admin') tanpa confirm -> server handle_setup_admin (T-B5, sudah 11+3 skenario unit test hijau) -> setup_status success -> toggle ke #portal-screen -> login manual via action 'auth' existing yang sudah reachable sejak T-B8) dan didukung unit test di kedua sisi (backend: test_setup.py 14 skenario + test_websocket.py; frontend: ws-routing.test.js 16 skenario). Regresi penuh: 663 passed, 6 skipped (skip count sama seperti sesi 5, murni sandbox tanpa mpv/X display, tidak terkait Fitur B). doctor.py --strict PASS 100 semua checker. vitest: 16/16 passed (naik dari 14 baseline sesi 5).

**File Terdampak:**

- `web/static/css/portal.css`
- `web/static/js/portal.js`
- `web/static/js/main.js`
- `web/static/js/dom.js`
- `web/static/js/events/index.js`
- `web/static/js/services/auth.js`
- `web/static/js/ws.js`
- `tests/frontend/ws-routing.test.js`

---

## [2026-07-19] Fitur B (login_redesign) — Sesi 5, T-B9.1..T-B9.2: gate index.html #2 (izin eksplisit user diberikan PERSIS sebelum T-B9.1, terpisah dari izin T-B8 meski satu fitur). Menambahkan #setup-screen ke web/static/index.html, reuse struktur .portal-card/.portal-title/.portal-subtitle/.portal-options/.portal-admin-wrapper/.portal-login-form/.login-input-group/.login-error dari #portal-screen existing (T-B9.1), lalu field Confirm Password + area pesan validasi tersendiri (T-B9.2). Elemen baru: #setup-screen, #setup-form, #setup-username, #setup-password, #setup-confirm-password, #setup-confirm-error-msg, #setup-submit-btn, #setup-error-msg -- semua id baru, tidak ada id/class #portal-screen existing yang diubah (portal-screen, portal-login-form, admin-username, admin-password, admin-submit-btn, login-error-msg persis sama seperti sebelumnya). Field Confirm Password sengaja diberi area pesan validasi terpisah (#setup-confirm-error-msg) dari error server (#setup-error-msg) karena kontrak T-B5: confirm password tidak pernah dikirim ke server, jadi pesan mismatch-nya murni client-side (akan divalidasi di T-B12.1/T-B12.2). Markup belum berfungsi -- belum ada CSS untuk #setup-screen (display:none/flex, styling Confirm Password) dan belum ada wiring JS (cek /api/setup-required, toggle vs #portal-screen, validasi submit) -- itu T-B10..T-B12.2 di sesi 6. Setup-screen saat ini tidak memiliki class display CSS sendiri sehingga akan tampak tanpa styling/positioning jika dirender langsung sebelum T-B10 -- ini disengaja, konsisten dengan pola inkremental fitur ini (mis. setup_admin action T-B5 belum reachable sampai T-B8). post_commands verify_structure.py --verbose --json: flag --verbose tidak dikenali script actual (error argparse) -- bug pre-existing tidak terkait perubahan sesi ini (mirip catatan impact.py di PATCH-2026-07-19-113), dijalankan tanpa --verbose sebagai gantinya, PASS 100 (Big Files, Pending Items) baik setelah T-B9.1 maupun setelah T-B9.2. Regresi penuh: 663 passed, 6 skipped (naik 4 dari 2 baseline tercatat sesi 4 -- 4 skip tambahan murni environment sandbox ini, integration test butuh mpv tidak ada + GUI test butuh X display tidak ada, tidak terkait Fitur B, tidak ada test baru gagal/berkurang). doctor.py --strict PASS 100 semua checker (verify_docs, architecture_lint, verify_structure, verify_security, event_graph).

**ID:** `PATCH-2026-07-19-115`

**Tanggal:** 2026-07-19

**Ringkasan:** Fitur B (login_redesign) — Sesi 5, T-B9.1..T-B9.2: gate index.html #2 (izin eksplisit user diberikan PERSIS sebelum T-B9.1, terpisah dari izin T-B8 meski satu fitur). Menambahkan #setup-screen ke web/static/index.html, reuse struktur .portal-card/.portal-title/.portal-subtitle/.portal-options/.portal-admin-wrapper/.portal-login-form/.login-input-group/.login-error dari #portal-screen existing (T-B9.1), lalu field Confirm Password + area pesan validasi tersendiri (T-B9.2). Elemen baru: #setup-screen, #setup-form, #setup-username, #setup-password, #setup-confirm-password, #setup-confirm-error-msg, #setup-submit-btn, #setup-error-msg -- semua id baru, tidak ada id/class #portal-screen existing yang diubah (portal-screen, portal-login-form, admin-username, admin-password, admin-submit-btn, login-error-msg persis sama seperti sebelumnya). Field Confirm Password sengaja diberi area pesan validasi terpisah (#setup-confirm-error-msg) dari error server (#setup-error-msg) karena kontrak T-B5: confirm password tidak pernah dikirim ke server, jadi pesan mismatch-nya murni client-side (akan divalidasi di T-B12.1/T-B12.2). Markup belum berfungsi -- belum ada CSS untuk #setup-screen (display:none/flex, styling Confirm Password) dan belum ada wiring JS (cek /api/setup-required, toggle vs #portal-screen, validasi submit) -- itu T-B10..T-B12.2 di sesi 6. Setup-screen saat ini tidak memiliki class display CSS sendiri sehingga akan tampak tanpa styling/positioning jika dirender langsung sebelum T-B10 -- ini disengaja, konsisten dengan pola inkremental fitur ini (mis. setup_admin action T-B5 belum reachable sampai T-B8). post_commands verify_structure.py --verbose --json: flag --verbose tidak dikenali script actual (error argparse) -- bug pre-existing tidak terkait perubahan sesi ini (mirip catatan impact.py di PATCH-2026-07-19-113), dijalankan tanpa --verbose sebagai gantinya, PASS 100 (Big Files, Pending Items) baik setelah T-B9.1 maupun setelah T-B9.2. Regresi penuh: 663 passed, 6 skipped (naik 4 dari 2 baseline tercatat sesi 4 -- 4 skip tambahan murni environment sandbox ini, integration test butuh mpv tidak ada + GUI test butuh X display tidak ada, tidak terkait Fitur B, tidak ada test baru gagal/berkurang). doctor.py --strict PASS 100 semua checker (verify_docs, architecture_lint, verify_structure, verify_security, event_graph).

**File Terdampak:**

- `web/static/index.html`

---

## [2026-07-19] Fitur B (login_redesign) — Sesi 4, T-B8: routing setup_admin ke whitelist (GATE, izin eksplisit user diberikan PERSIS sebelum task ini, terpisah dari izin manapun sebelumnya di file yang sama). server/handlers/websocket.py: action 'setup_admin' di-special-case di handle_ws_message() SEBELUM require_auth() -- mirror persis pola action 'auth', karena saat Initial Setup belum ada admin_account sama sekali sehingga tidak ada cara 'sudah login' pada titik itu. Memanggil handle_setup_admin() dari server/handlers/setup.py (T-B5/T-B7). Command lama (auth, playback, queue, discovery, download, cache) tidak diubah/disentuh sama sekali. server/app.py (TIDAK locked): endpoint GET /api/setup-required didaftarkan via app.router.add_get(), memanggil setup_required() dari setup.py -- akan dipanggil client saat load, SEBELUM koneksi WS dibuka (T-B11.1). Unit test baru: test_handle_ws_message_setup_admin (dispatch benar, args match) + test_handle_ws_message_setup_admin_bypasses_require_auth (regresi guard -- setup_admin TIDAK PERNAH memanggil require_auth(), krusial karena kalau ini regresi instalasi baru tidak akan pernah bisa menyelesaikan Initial Setup) di tests/unit/server/handlers/test_websocket.py. tests/unit/server/test_app.py: assertion route '/api/setup-required' ditambah ke test_create_app_registers_routes_and_services. Regresi WS lengkap: 663 passed, 2 skipped (naik 2 dari 661 baseline sesi 3), tidak ada command lama yang regresi. doctor.py --strict PASS 100 semua checker (architecture_lint, verify_docs, verify_structure, verify_security, event_graph). setup_admin & GET /api/setup-required kini reachable end-to-end dari WS/HTTP client (belum ditest manual di browser sungguhan -- sandbox tanpa network/display, sama seperti precedent Fitur A). Belum ada markup UI (#setup-screen) di index.html -- itu T-B9 (gate index.html, sesi 5, izin terpisah lagi).

**ID:** `PATCH-2026-07-19-114`

**Tanggal:** 2026-07-19

**Ringkasan:** Fitur B (login_redesign) — Sesi 4, T-B8: routing setup_admin ke whitelist (GATE, izin eksplisit user diberikan PERSIS sebelum task ini, terpisah dari izin manapun sebelumnya di file yang sama). server/handlers/websocket.py: action 'setup_admin' di-special-case di handle_ws_message() SEBELUM require_auth() -- mirror persis pola action 'auth', karena saat Initial Setup belum ada admin_account sama sekali sehingga tidak ada cara 'sudah login' pada titik itu. Memanggil handle_setup_admin() dari server/handlers/setup.py (T-B5/T-B7). Command lama (auth, playback, queue, discovery, download, cache) tidak diubah/disentuh sama sekali. server/app.py (TIDAK locked): endpoint GET /api/setup-required didaftarkan via app.router.add_get(), memanggil setup_required() dari setup.py -- akan dipanggil client saat load, SEBELUM koneksi WS dibuka (T-B11.1). Unit test baru: test_handle_ws_message_setup_admin (dispatch benar, args match) + test_handle_ws_message_setup_admin_bypasses_require_auth (regresi guard -- setup_admin TIDAK PERNAH memanggil require_auth(), krusial karena kalau ini regresi instalasi baru tidak akan pernah bisa menyelesaikan Initial Setup) di tests/unit/server/handlers/test_websocket.py. tests/unit/server/test_app.py: assertion route '/api/setup-required' ditambah ke test_create_app_registers_routes_and_services. Regresi WS lengkap: 663 passed, 2 skipped (naik 2 dari 661 baseline sesi 3), tidak ada command lama yang regresi. doctor.py --strict PASS 100 semua checker (architecture_lint, verify_docs, verify_structure, verify_security, event_graph). setup_admin & GET /api/setup-required kini reachable end-to-end dari WS/HTTP client (belum ditest manual di browser sungguhan -- sandbox tanpa network/display, sama seperti precedent Fitur A). Belum ada markup UI (#setup-screen) di index.html -- itu T-B9 (gate index.html, sesi 5, izin terpisah lagi).

**File Terdampak:**

- `server/handlers/websocket.py`
- `server/app.py`
- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_app.py`

---

## [2026-07-19] Fitur B (login_redesign) — Sesi 3, T-B6..T-B7: dokumentasi K3 (tanpa migrasi otomatis) + fallback kegagalan setup. T-B6: tambah section 'Catatan Desain: Kredensial Admin Tidak Dimigrasikan Otomatis (K3)' di docs/security/threat_model.md -- rasional (dua file password lama tidak sinkron di lapangan, risiko salah pilih sumber > biaya re-setup), konsekuensi (upgrade = wajib Initial Setup lagi), pointer ke ADR resmi yang akan ditulis di T-B18 setelah cut-over selesai. DoD terpenuhi by construction: TIDAK ADA kode migrasi ditulis sama sekali (tidak ada baca cache/admin_password.txt atau instance/admin_password.txt di manapun) sehingga instalasi baru & lama otomatis berperilaku identik terhadap admin_account -- keduanya kosong sampai lewat Initial Setup. Draft catatan upgrade ditambah ke CHANGELOG.md (## [Unreleased], ditandai draft/dalam-progres, akan difinalisasi T-B19). T-B7: fallback kegagalan di server/handlers/setup.py -- 3 titik try/except baru (admin_account_exists() awal, create_admin_account() non-IntegrityError, setup_required() HTTP endpoint): kegagalan DB corrupt/disk penuh/OSError ditangkap eksplisit, di-log via structlog (detail lengkap TIDAK dikirim ke client, cuma pesan generik 'Gagal menyimpan akun admin...'), handler TIDAK melempar exception ke luar (server tetap start & jalan untuk client lain), dan karena create_admin_account adalah single atomic INSERT, kegagalan tidak pernah menyisakan row admin_account setengah-jadi/kosong yang bisa login tanpa password. setup_required() HTTP mengembalikan 503 + pesan generik alih-alih 500 stack-trace bocor. Unit test baru (3 skenario fallback ditambah ke tests/unit/server/handlers/test_setup.py, total 14 skenario di file itu): create gagal (OSError, pesan tidak bocor), exists-check gagal (OperationalError, insert TIDAK dipanggil), endpoint setup_required gagal (503, pesan tidak bocor) -- semua hijau. Regresi penuh: 661 passed, 2 skipped (naik 3 dari 658 baseline sesi 2). verify_security.py PASS 100. doctor.py --strict PASS 100 semua checker. Catatan insidental: automation/impact.py punya bug pre-existing tidak terkait Fitur B (ImportError: cannot import name 'collect_py_files' from find_owner -- terjadi di SEMUA target file, bukan spesifik ke perubahan sesi ini), post_command T-B6 yang memanggilnya dilewati, dicatat di sini untuk visibilitas, tidak diperbaiki (di luar scope Fitur B). Belum reachable dari client -- handler setup_admin masih menunggu whitelist websocket.py (T-B8).

**ID:** `PATCH-2026-07-19-113`

**Tanggal:** 2026-07-19

**Ringkasan:** Fitur B (login_redesign) — Sesi 3, T-B6..T-B7: dokumentasi K3 (tanpa migrasi otomatis) + fallback kegagalan setup. T-B6: tambah section 'Catatan Desain: Kredensial Admin Tidak Dimigrasikan Otomatis (K3)' di docs/security/threat_model.md -- rasional (dua file password lama tidak sinkron di lapangan, risiko salah pilih sumber > biaya re-setup), konsekuensi (upgrade = wajib Initial Setup lagi), pointer ke ADR resmi yang akan ditulis di T-B18 setelah cut-over selesai. DoD terpenuhi by construction: TIDAK ADA kode migrasi ditulis sama sekali (tidak ada baca cache/admin_password.txt atau instance/admin_password.txt di manapun) sehingga instalasi baru & lama otomatis berperilaku identik terhadap admin_account -- keduanya kosong sampai lewat Initial Setup. Draft catatan upgrade ditambah ke CHANGELOG.md (## [Unreleased], ditandai draft/dalam-progres, akan difinalisasi T-B19). T-B7: fallback kegagalan di server/handlers/setup.py -- 3 titik try/except baru (admin_account_exists() awal, create_admin_account() non-IntegrityError, setup_required() HTTP endpoint): kegagalan DB corrupt/disk penuh/OSError ditangkap eksplisit, di-log via structlog (detail lengkap TIDAK dikirim ke client, cuma pesan generik 'Gagal menyimpan akun admin...'), handler TIDAK melempar exception ke luar (server tetap start & jalan untuk client lain), dan karena create_admin_account adalah single atomic INSERT, kegagalan tidak pernah menyisakan row admin_account setengah-jadi/kosong yang bisa login tanpa password. setup_required() HTTP mengembalikan 503 + pesan generik alih-alih 500 stack-trace bocor. Unit test baru (3 skenario fallback ditambah ke tests/unit/server/handlers/test_setup.py, total 14 skenario di file itu): create gagal (OSError, pesan tidak bocor), exists-check gagal (OperationalError, insert TIDAK dipanggil), endpoint setup_required gagal (503, pesan tidak bocor) -- semua hijau. Regresi penuh: 661 passed, 2 skipped (naik 3 dari 658 baseline sesi 2). verify_security.py PASS 100. doctor.py --strict PASS 100 semua checker. Catatan insidental: automation/impact.py punya bug pre-existing tidak terkait Fitur B (ImportError: cannot import name 'collect_py_files' from find_owner -- terjadi di SEMUA target file, bukan spesifik ke perubahan sesi ini), post_command T-B6 yang memanggilnya dilewati, dicatat di sini untuk visibilitas, tidak diperbaiki (di luar scope Fitur B). Belum reachable dari client -- handler setup_admin masih menunggu whitelist websocket.py (T-B8).

**File Terdampak:**

- `docs/security/threat_model.md`
- `CHANGELOG.md`
- `server/handlers/setup.py`
- `tests/unit/server/handlers/test_setup.py`

---

## [2026-07-19] Fitur B (login_redesign) — Sesi 2, T-B5.1..T-B5.6: handler setup_admin lengkap. File baru server/handlers/setup.py: handle_setup_admin(ws, data, manager, client_ip, repos, now) -- validasi username wajib + password minimal 8 karakter (field confirm password TIDAK pernah dikirim/divalidasi di server, kontrak dengan T-B12.2), hashing via core.security.hash_password (existing, tidak reimplement), simpan via repos.admin_account.create_admin_account(). Race condition submit ganda ditangani 2 lapis: cek admin_account_exists() dulu (fast-path, bukan pertahanan utama), lalu tangkap sqlite3.IntegrityError dari UNIQUE constraint (T-B1) sebagai pertahanan sesungguhnya utk kasus TOCTOU -- keduanya kirim pesan 'Akun admin sudah pernah dibuat', tidak pernah overwrite diam-diam. Rate limit 5x/5menit per IP: state baru manager.setup_attempts (terpisah dari login_attempts, ditambah di server/connection_manager.py, tidak locked), pola prune+lock identik handle_auth di auth.py. Fungsi setup_required(request) -- calon handler GET /api/setup-required, cek admin_account_exists() -> {setup_required: bool}; belum didaftarkan ke router (menunggu gate T-B8, websocket.py/app.py locked). Unit test baru tests/unit/server/handlers/test_setup.py: 11 skenario (validasi kosong/pendek, sukses hash+save, username di-strip, submit-ganda via exists()=True, submit-ganda via IntegrityError race, rate limit ke-6 ditolak, stale attempts di-prune, input invalid tetap kena hitungan rate limit, endpoint setup_required true/false) -- semua hijau. Regresi penuh: 658 passed, 2 skipped (tidak ada regresi). Environment fix insidental: apt-get install python3-tk (dependency test launcher/gui yang sebelumnya ModuleNotFoundError di sandbox ini, dicatat STATUS.md T0.2 sebelumnya). generate_file_index.py & generate_report.py dijalankan. doctor.py --strict PASS 100 semua checker. Belum reachable dari client sama sekali -- action setup_admin belum ada di whitelist websocket.py, endpoint HTTP belum terdaftar di app.py.

**ID:** `PATCH-2026-07-19-112`

**Tanggal:** 2026-07-19

**Ringkasan:** Fitur B (login_redesign) — Sesi 2, T-B5.1..T-B5.6: handler setup_admin lengkap. File baru server/handlers/setup.py: handle_setup_admin(ws, data, manager, client_ip, repos, now) -- validasi username wajib + password minimal 8 karakter (field confirm password TIDAK pernah dikirim/divalidasi di server, kontrak dengan T-B12.2), hashing via core.security.hash_password (existing, tidak reimplement), simpan via repos.admin_account.create_admin_account(). Race condition submit ganda ditangani 2 lapis: cek admin_account_exists() dulu (fast-path, bukan pertahanan utama), lalu tangkap sqlite3.IntegrityError dari UNIQUE constraint (T-B1) sebagai pertahanan sesungguhnya utk kasus TOCTOU -- keduanya kirim pesan 'Akun admin sudah pernah dibuat', tidak pernah overwrite diam-diam. Rate limit 5x/5menit per IP: state baru manager.setup_attempts (terpisah dari login_attempts, ditambah di server/connection_manager.py, tidak locked), pola prune+lock identik handle_auth di auth.py. Fungsi setup_required(request) -- calon handler GET /api/setup-required, cek admin_account_exists() -> {setup_required: bool}; belum didaftarkan ke router (menunggu gate T-B8, websocket.py/app.py locked). Unit test baru tests/unit/server/handlers/test_setup.py: 11 skenario (validasi kosong/pendek, sukses hash+save, username di-strip, submit-ganda via exists()=True, submit-ganda via IntegrityError race, rate limit ke-6 ditolak, stale attempts di-prune, input invalid tetap kena hitungan rate limit, endpoint setup_required true/false) -- semua hijau. Regresi penuh: 658 passed, 2 skipped (tidak ada regresi). Environment fix insidental: apt-get install python3-tk (dependency test launcher/gui yang sebelumnya ModuleNotFoundError di sandbox ini, dicatat STATUS.md T0.2 sebelumnya). generate_file_index.py & generate_report.py dijalankan. doctor.py --strict PASS 100 semua checker. Belum reachable dari client sama sekali -- action setup_admin belum ada di whitelist websocket.py, endpoint HTTP belum terdaftar di app.py.

**File Terdampak:**

- `server/handlers/setup.py`
- `server/connection_manager.py`
- `tests/unit/server/handlers/test_setup.py`

---

## [2026-07-19] Fitur B (login_redesign) — Sesi 1, T-B1..T-B4: infrastruktur admin_account. Tabel admin_account (username UNIQUE, password_hash, created_at) ditambah ke persistence/schema.sql via CREATE TABLE IF NOT EXISTS -- otomatis terbuat di DB lama maupun baru karena executescript() jalan tiap startup (persistence/db.py), tidak perlu ALTER TABLE migration terpisah. Repository baru persistence/admin_account_repo.py (AdminAccountRepository) mirror pola session_repo.py: create_admin_account(username, password_hash) -- TANPA logika hashing di layer ini, hashing dilakukan di caller (T-B5); get_admin_account() -> None saat kosong; admin_account_exists() konsisten dengan get_admin_account(). Didaftarkan ke persistence/__init__.py (repos.admin_account), mengikuti pola facade tipis repos.discover -- tidak ada method delegasi tambahan di Repositories. Unit test baru tests/unit/persistence/test_admin_account_repo.py: create/get/exists lifecycle (4 skenario) + UNIQUE constraint pada percobaan create kedua dengan username sama (sqlite3.IntegrityError, baris pertama tidak ter-overwrite) -- kontrak dasar untuk race condition submit ganda yang akan diimplementasikan penuh di T-B5.3. Belum reachable dari client (belum ada handler/route) -- infrastruktur murni, menunggu T-B5 (handler setup_admin). generate_file_index.py & generate_report.py dijalankan (file baru terindeks). doctor.py --strict PASS 100 (architecture_lint, verify_docs, verify_structure, verify_security, event_graph semua PASS).

**ID:** `PATCH-2026-07-19-111`

**Tanggal:** 2026-07-19

**Ringkasan:** Fitur B (login_redesign) — Sesi 1, T-B1..T-B4: infrastruktur admin_account. Tabel admin_account (username UNIQUE, password_hash, created_at) ditambah ke persistence/schema.sql via CREATE TABLE IF NOT EXISTS -- otomatis terbuat di DB lama maupun baru karena executescript() jalan tiap startup (persistence/db.py), tidak perlu ALTER TABLE migration terpisah. Repository baru persistence/admin_account_repo.py (AdminAccountRepository) mirror pola session_repo.py: create_admin_account(username, password_hash) -- TANPA logika hashing di layer ini, hashing dilakukan di caller (T-B5); get_admin_account() -> None saat kosong; admin_account_exists() konsisten dengan get_admin_account(). Didaftarkan ke persistence/__init__.py (repos.admin_account), mengikuti pola facade tipis repos.discover -- tidak ada method delegasi tambahan di Repositories. Unit test baru tests/unit/persistence/test_admin_account_repo.py: create/get/exists lifecycle (4 skenario) + UNIQUE constraint pada percobaan create kedua dengan username sama (sqlite3.IntegrityError, baris pertama tidak ter-overwrite) -- kontrak dasar untuk race condition submit ganda yang akan diimplementasikan penuh di T-B5.3. Belum reachable dari client (belum ada handler/route) -- infrastruktur murni, menunggu T-B5 (handler setup_admin). generate_file_index.py & generate_report.py dijalankan (file baru terindeks). doctor.py --strict PASS 100 (architecture_lint, verify_docs, verify_structure, verify_security, event_graph semua PASS).

**File Terdampak:**

- `persistence/schema.sql`
- `persistence/admin_account_repo.py`
- `persistence/__init__.py`
- `tests/unit/persistence/test_admin_account_repo.py`

---

## [2026-07-19] T-A9: registrasi elemen DOM baru Quick Search Discover ke web/static/js/dom.js -- 10 elemen (discoverSearchWrap/Input/ClearBtn/FilterRow/KategoriToggle/DecadeBtn/DecadeContainer/DecadeChips/Status/Results) via $() (getElementById), plus filterScopeHint (querySelector, markup existing tidak punya id) dan rowUnheardLabel (computed dari sibling row-unheard) -- keduanya tetap terkurung di dalam dom.js sesuai aturan "tidak ada querySelector liar di luar dom.js". web/static/js/events/discover-search-events.js (T-A7) dan web/static/js/render/discover-search.js (T-A8) diupdate pakai dom.* alih-alih document.getElementById langsung (kedua file tidak locked, sudah dalam scope perbaikan wajar mengikuti dod T-A9). web/static/js/main.js: tidak ada perubahan diperlukan (initDOM() sudah dipanggil sebelum initEvents() di init(), urutan sudah benar). doctor.py --strict & verify_structure.py PASS 100.

**ID:** `PATCH-2026-07-19-110`

**Tanggal:** 2026-07-19

**Ringkasan:** T-A9: registrasi elemen DOM baru Quick Search Discover ke dom.js (10 elemen via $() + filterScopeHint/rowUnheardLabel yang di-resolve di dalam dom.js). discover-search-events.js (T-A7) & render/discover-search.js (T-A8) diupdate pakai dom.* alih-alih document.getElementById langsung. main.js tidak berubah (urutan initDOM()/initEvents() sudah benar). doctor.py --strict PASS 100.

**File Terdampak:**

- `web/static/js/dom.js`
- `web/static/js/events/discover-search-events.js`
- `web/static/js/render/discover-search.js`

---

## [2026-07-19] T-A8: file baru web/static/js/render/discover-search.js -- render hasil pencarian Quick Search Discover, mirror ringan render/search.js (bangun .sr-item yang sama, reuse di semua breakpoint, tanpa CSS baru). 5 state: Initial (default, belum ada state khusus), Loading (enterDiscoverSearchLoading(), dipanggil dari events/discover-search-events.js T-A7 tepat sebelum wsSend), Empty (exitDiscoverSearchMode(), query dikosongkan -> balik ke rekomendasi personalisasi TANPA reload), No result (renderDiscoverSearchResults([]) -> pesan "Tidak ditemukan hasil"), Error (handleDiscoverSearchError(), hook ke case "error" umum di ws.js, hanya render inline kalau mode search sedang aktif). Toggle visibilitas blok personalisasi (taste-block, discover-filter-bar, filter-scope-hint, row-for-you*, row-genre-affinity*, row-unheard + label row-nya) saat masuk/keluar mode pencarian -- discover-artists/discover-genres/discover-cached (di luar cakupan "personalisasi") tidak disentuh. Guard _discoverSearchActive mencegah respons WS basi (query sudah diganti/dikosongkan) menimpa UI. Perubahan pendukung (izin eksplisit user, di luar cakupan file asli T-A8, precedent T-A6/T-A7): web/static/index.html -- 2 baris container (#discover-search-status, #discover-search-results) di dalam .discover-search-wrap + 1 baris <script> render/discover-search.js. web/static/js/ws.js (tidak locked) -- case baru "discover_search_results", hook handleDiscoverSearchError() di case "error". web/static/js/events/discover-search-events.js (tidak locked, dari T-A7) -- panggil enterDiscoverSearchLoading() di sendSearch(). doctor.py --strict & verify_structure.py PASS 100.

**ID:** `PATCH-2026-07-19-109`

**Tanggal:** 2026-07-19

**Ringkasan:** T-A8: file baru web/static/js/render/discover-search.js -- render hasil pencarian Quick Search Discover, mirror ringan render/search.js, reuse .sr-item. 5 state (Initial/Loading/Empty/No result/Error) lengkap dengan toggle blok personalisasi & guard request basi. Perlu 2 baris container + 1 baris <script> di index.html (izin eksplisit user) dan wiring kecil di ws.js (tidak locked) + discover-search-events.js (tidak locked). doctor.py --strict PASS 100.

**File Terdampak:**

- `web/static/js/render/discover-search.js`
- `web/static/index.html`
- `web/static/js/ws.js`
- `web/static/js/events/discover-search-events.js`

---

## [2026-07-19] T-A7: file baru web/static/js/events/discover-search-events.js -- event handling + debounce 500ms untuk Quick Search Discover, mirror pola search-input-events.js. wsSend('discover_search', {query, kategori, decade}) terpicu setelah 500ms idle (atau Enter langsung). Tombol clear reset input, filter row, kategori/decade ke default TANPA round-trip ke server saat query kosong. Filter row (.discover-search-filter-row) progressive disclosure show/hide berdasar query aktif. Opsi dekade (K2) diturunkan dari store.discover_for_you/genre_affinity_artists/unheard yang sudah dimuat -- pola sama persis dgn buildDecadeChips() filter-bar Discover existing, tanpa query/kolom skema baru. Didaftarkan ke initEvents() via events/index.js (file tidak locked). Ditambahkan 1 baris <script src="/static/js/events/discover-search-events.js" defer> di web/static/index.html (izin eksplisit user, di luar cakupan file asli T-A7, sama seperti precedent T-A6) -- action kini reachable end-to-end dari browser. doctor.py --strict & verify_structure.py PASS 100, identik baseline.

**ID:** `PATCH-2026-07-19-108`

**Tanggal:** 2026-07-19

**Ringkasan:** T-A7: file baru web/static/js/events/discover-search-events.js -- event handling + debounce 500ms untuk Quick Search Discover, mirror pola search-input-events.js. wsSend('discover_search', {query, kategori, decade}) terpicu setelah 500ms idle (atau Enter langsung). Tombol clear reset input, filter row, kategori/decade ke default TANPA round-trip ke server saat query kosong. Opsi dekade diturunkan dari data personalisasi yang sudah dimuat, tanpa query/kolom skema baru. Didaftarkan ke initEvents() via events/index.js. Ditambahkan 1 baris <script> di index.html (izin eksplisit user) -- reachable end-to-end. doctor.py --strict PASS 100.

**File Terdampak:**

- `web/static/js/events/discover-search-events.js`
- `web/static/js/events/index.js`
- `web/static/index.html`

---

## [2026-07-19] T-A6: CSS baru web/static/css/components/discover-search.css untuk Quick Search Discover (search bar + filter row), pakai token spacing --s* project-wide, tanpa breakpoint baru. .filter-bar/.segmented/.custom-dropdown di-reuse apa adanya (tidak ada rule baru untuk itu). Perlu 1 baris tambahan <link rel=stylesheet> di web/static/index.html (izin eksplisit user, di luar cakupan file asli T-A6) supaya CSS ini benar-benar termuat. verify_structure.py & doctor.py --strict PASS 100.

**ID:** `PATCH-2026-07-19-107`

**Tanggal:** 2026-07-19

**Ringkasan:** T-A6: CSS baru web/static/css/components/discover-search.css untuk Quick Search Discover (search bar + filter row), pakai token spacing --s* project-wide, tanpa breakpoint baru. .filter-bar/.segmented/.custom-dropdown di-reuse apa adanya (tidak ada rule baru untuk itu). Perlu 1 baris tambahan <link rel=stylesheet> di web/static/index.html (izin eksplisit user, di luar cakupan file asli T-A6) supaya CSS ini benar-benar termuat. verify_structure.py & doctor.py --strict PASS 100.

**File Terdampak:**

- `web/static/css/components/discover-search.css`
- `web/static/index.html`

---

## [2026-07-19] T-A5: markup Quick Search Discover di web/static/index.html (izin eksplisit user) -- search bar (.discover-search-wrap) + filter row (reuse .segmented kategori K1 + .custom-dropdown dekade K2, progressive disclosure via display:none) disisipkan sebelum .taste-block di #tab-discover. Terisolasi via id/class baru, tidak ada duplicate id, elemen Discover existing (taste-block, kategori-toggle, decade-dropdown-container) tidak berubah. Belum ada JS wiring (menunggu T-A7/T-A8).

**ID:** `PATCH-2026-07-19-106`

**Tanggal:** 2026-07-19

**Ringkasan:** T-A5: markup Quick Search Discover di web/static/index.html (izin eksplisit user) -- search bar (.discover-search-wrap) + filter row (reuse .segmented kategori K1 + .custom-dropdown dekade K2, progressive disclosure via display:none) disisipkan sebelum .taste-block di #tab-discover. Terisolasi via id/class baru, tidak ada duplicate id, elemen Discover existing (taste-block, kategori-toggle, decade-dropdown-container) tidak berubah. Belum ada JS wiring (menunggu T-A7/T-A8).

**File Terdampak:**

- `web/static/index.html`

---

## [2026-07-19] T-A4: tambah 'discover_search' ke DISCOVERY_CMDS di server/handlers/websocket.py (izin eksplisit user, perubahan 1 baris) -- action discover_search kini reachable dari client. Command lama (search, discover, get_artist_detail) diverifikasi tetap jalan. doctor.py --strict PASS 100, identik baseline T0.1. Belum ditest manual di browser sungguhan (sandbox tanpa network/display), sama seperti catatan get_artist_detail sebelumnya.

**ID:** `PATCH-2026-07-19-105`

**Tanggal:** 2026-07-19

**Ringkasan:** T-A4: tambah 'discover_search' ke DISCOVERY_CMDS di server/handlers/websocket.py (izin eksplisit user, perubahan 1 baris) -- action discover_search kini reachable dari client. Command lama (search, discover, get_artist_detail) diverifikasi tetap jalan. doctor.py --strict PASS 100, identik baseline T0.1. Belum ditest manual di browser sungguhan (sandbox tanpa network/display), sama seperti catatan get_artist_detail sebelumnya.

**File Terdampak:**

- `server/handlers/websocket.py`

---

## [2026-07-19] Quick Search Discover (T-A1..T-A3): search_tracks() di discover_repo.py (LIKE title/artist, filter kategori Solo/Band K1 & dekade K2 via subquery tanpa JOIN artists/artist_genres, tanpa logika skor/ranking), unit test baru, branch discover_search di ws_discovery.py. Belum reachable dari client -- menunggu izin eksplisit T-A4 (DISCOVERY_CMDS di server/handlers/websocket.py, file governance-locked).

**ID:** `PATCH-2026-07-19-104`

**Tanggal:** 2026-07-19

**Ringkasan:** Quick Search Discover (T-A1..T-A3): search_tracks() di discover_repo.py (LIKE title/artist, filter kategori Solo/Band K1 & dekade K2 via subquery tanpa JOIN artists/artist_genres, tanpa logika skor/ranking), unit test baru, branch discover_search di ws_discovery.py. Belum reachable dari client -- menunggu izin eksplisit T-A4 (DISCOVERY_CMDS di server/handlers/websocket.py, file governance-locked).

**File Terdampak:**

- `persistence/discover_repo.py`
- `tests/unit/persistence/test_discover_repo_search.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/server/handlers/test_ws_discovery.py`

---

## [2026-07-18] Rename nama generik: adapters/ytdlp/common.py -> ydl_options.py, engine/radio/common.py -> radio_config.py, automation/verify_docs/helpers.py -> doc_parsing_utils.py; sekalian perbaiki docstring 'Depends on' yang masih menyebut scripts.verify_docs.helpers (sisa lupa update dari PATCH-2026-07-17-072)

**ID:** `PATCH-2026-07-18-103`

**Tanggal:** 2026-07-18

**Ringkasan:** Rename nama generik: adapters/ytdlp/common.py -> ydl_options.py, engine/radio/common.py -> radio_config.py, automation/verify_docs/helpers.py -> doc_parsing_utils.py; sekalian perbaiki docstring 'Depends on' yang masih menyebut scripts.verify_docs.helpers (sisa lupa update dari PATCH-2026-07-17-072)

**File Terdampak:**

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

---

## [2026-07-18] Rename file test yang menyimpang konvensi penamaan (tests/frontend/test_store.test.js -> store.test.js, test_ws-routing.test.js -> ws-routing.test.js, tests/unit/launcher/gui/test_app_lifecycle.py -> test_app.py); konsolidasi test_ytdlp.py + test_ytdlp_client.py jadi satu file test_ytdlp.py (kelas facade disuffix ViaYtDlpClient agar tidak bentrok nama, semua 42 assertion/test case dipertahankan, verified: 620 passed tetap sama)

**ID:** `PATCH-2026-07-18-102`

**Tanggal:** 2026-07-18

**Ringkasan:** Rename file test yang menyimpang konvensi penamaan (tests/frontend/test_store.test.js -> store.test.js, test_ws-routing.test.js -> ws-routing.test.js, tests/unit/launcher/gui/test_app_lifecycle.py -> test_app.py); konsolidasi test_ytdlp.py + test_ytdlp_client.py jadi satu file test_ytdlp.py (kelas facade disuffix ViaYtDlpClient agar tidak bentrok nama, semua 42 assertion/test case dipertahankan, verified: 620 passed tetap sama)

**File Terdampak:**

- `tests/frontend/store.test.js`
- `tests/frontend/ws-routing.test.js`
- `tests/unit/launcher/gui/test_app.py`
- `tests/unit/adapters/ytdlp/test_ytdlp.py`
- `docs/testing/README.md`
- `docs/testing/frontend_testing.md`
- `docs/architecture/folder_structure.md`

---

## [2026-07-18] Rename ADR 003-Crossfade.md ke konvensi 0007-crossfade.md, samakan judul internal jadi ADR-0007 (tidak ada referensi lain yang perlu diupdate selain entri historis di PATCHLOG.md yang sengaja dibiarkan sebagai catatan riwayat)

**ID:** `PATCH-2026-07-18-101`

**Tanggal:** 2026-07-18

**Ringkasan:** Rename ADR 003-Crossfade.md ke konvensi 0007-crossfade.md, samakan judul internal jadi ADR-0007 (tidak ada referensi lain yang perlu diupdate selain entri historis di PATCHLOG.md yang sengaja dibiarkan sebagai catatan riwayat)

**File Terdampak:**

- `docs/adr/0007-crossfade.md`

---

## [2026-07-18] Perluas .importlinter: kontrak automation dan data sebagai root package terisolasi (automation tidak boleh diimpor, data hanya boleh diimpor automation); dikonfirmasi cache/ sudah bukan python package sejak T2.6 sehingga tidak perlu entri forbidden_modules tambahan

**ID:** `PATCH-2026-07-18-100`

**Tanggal:** 2026-07-18

**Ringkasan:** Perluas .importlinter: kontrak automation dan data sebagai root package terisolasi (automation tidak boleh diimpor, data hanya boleh diimpor automation); dikonfirmasi cache/ sudah bukan python package sejak T2.6 sehingga tidak perlu entri forbidden_modules tambahan

**File Terdampak:**

- `.importlinter`

---

## [2026-07-18] Tambahkan accessor get_*() bertipe di server/handlers/__init__.py untuk semua key request.app[...] (repos, tracks, conn, state, manager, ytdlp, playback_controller) - rencana asli get_db() untuk request.app['db'] sudah tidak relevan sejak Database God Facade dipecah T2.2, diganti akses per-repo

**ID:** `PATCH-2026-07-18-099`

**Tanggal:** 2026-07-18

**Ringkasan:** Tambahkan accessor get_*() bertipe di server/handlers/__init__.py untuk semua key request.app[...] (repos, tracks, conn, state, manager, ytdlp, playback_controller) - rencana asli get_db() untuk request.app['db'] sudah tidak relevan sejak Database God Facade dipecah T2.2, diganti akses per-repo

**File Terdampak:**

- `server/handlers/__init__.py`
- `server/handlers/http.py`
- `server/handlers/websocket.py`
- `server/handlers/audio_stream_handler.py`

---

## [2026-07-18] Tambahkan type hint DatabasePort ke constructor engine/ yang menerima db tanpa tipe

**ID:** `PATCH-2026-07-18-098`

**Tanggal:** 2026-07-18

**Ringkasan:** Tambahkan type hint DatabasePort ke constructor engine/ yang menerima db tanpa tipe

**File Terdampak:**

- `core/ports.py`
- `engine/radio/artist_selector.py`
- `engine/radio/engine.py`

---

## [2026-07-18] Audit data/: artists_enriched1.json TERNYATA BUKAN duplikat (854 vs 100 artis, beda substantif) - tidak dihapus, didokumentasikan di STATUS.md, butuh keputusan pemilik project. export_to_sqlite.py dikonfirmasi tetap di data/ (kontradiksi dengan rencana pindah ke automation/ di TASK_BREAKDOWN.md dibatalkan karena state riil sudah selesai)

**ID:** `PATCH-2026-07-18-097`

**Tanggal:** 2026-07-18

**Ringkasan:** Audit data/: artists_enriched1.json TERNYATA BUKAN duplikat (854 vs 100 artis, beda substantif) - tidak dihapus, didokumentasikan di STATUS.md, butuh keputusan pemilik project. export_to_sqlite.py dikonfirmasi tetap di data/ (kontradiksi dengan rencana pindah ke automation/ di TASK_BREAKDOWN.md dibatalkan karena state riil sudah selesai)

**File Terdampak:**

- `docs/STATUS.md`

---

## [2026-07-18] Pisah serve_stream (range-request) ke audio_stream_handler.py

**ID:** `PATCH-2026-07-18-096`

**Tanggal:** 2026-07-18

**Ringkasan:** Pisah serve_stream (range-request) ke audio_stream_handler.py

**File Terdampak:**

- `server/handlers/audio_stream_handler.py`
- `server/handlers/http.py`
- `server/app.py`
- `tests/unit/server/handlers/test_audio_stream_handler.py`
- `tests/unit/server/handlers/test_http.py`

---

## [2026-07-18] Pisah skor rekomendasi (compute_match_pct, taste spectrum) ke services/discover_ranking.py, fungsi murni tanpa DB

**ID:** `PATCH-2026-07-18-095`

**Tanggal:** 2026-07-18

**Ringkasan:** Pisah skor rekomendasi (compute_match_pct, taste spectrum) ke services/discover_ranking.py, fungsi murni tanpa DB

**File Terdampak:**

- `services/discover_ranking.py`
- `persistence/discover_repo.py`
- `services/discover_service.py`
- `tests/unit/services/test_discover_ranking.py`
- `tests/unit/persistence/test_discover_repo.py`

---

## [2026-07-18] Ekstrak auth_service.py dari auth_panel.py, pisah logic dari UI

**ID:** `PATCH-2026-07-18-094`

**Tanggal:** 2026-07-18

**Ringkasan:** Ekstrak auth_service.py dari auth_panel.py, pisah logic dari UI

**File Terdampak:**

- `launcher/auth_service.py`
- `launcher/gui/auth_panel.py`

---

## [2026-07-18] Pecah build_ui() jadi 4 method privat di ui_builder.py

**ID:** `PATCH-2026-07-18-093`

**Tanggal:** 2026-07-18

**Ringkasan:** Pecah build_ui() jadi 4 method privat di ui_builder.py

**File Terdampak:**

- `launcher/gui/ui_builder.py`

---

## [2026-07-18] Ekstrak ServerLifecycle (tanpa dependency Tkinter) dari ServerManager di launcher/gui/app.py

**ID:** `PATCH-2026-07-18-092`

**Tanggal:** 2026-07-18

**Ringkasan:** Ekstrak ServerLifecycle (tanpa dependency Tkinter) dari ServerManager di launcher/gui/app.py

**File Terdampak:**

- `launcher/gui/app.py`
- `launcher/server_lifecycle.py`
- `launcher/gui/log_view.py`
- `tests/unit/launcher/test_server_lifecycle.py`

---

## [2026-07-18] Perbaiki typo/leftover text di docs/STATUS.md pada baris services/stream_prefetch.py (sisa draf tidak sengaja ke-commit).

**ID:** `PATCH-2026-07-18-091`

**Tanggal:** 2026-07-18

**Ringkasan:** Perbaiki typo/leftover text di docs/STATUS.md pada baris services/stream_prefetch.py (sisa draf tidak sengaja ke-commit).

**File Terdampak:**

- `docs/STATUS.md`

---

## [2026-07-18] T2.7: Satukan services/ (root) dan server/services/. stream_prefetch.py pindah ke services/stream_prefetch.py sesuai rencana (hanya impor config+core). broadcast_service.py TIDAK dipindah ke root services/ (deviasi dari rencana) melainkan ke server/broadcast_service.py, karena mengimpor server.connection_manager dan server.serializers (konstruksi web/wire layer) -- begitu bug .importlinter (PATCH-2026-07-18-089) diperbaiki, memindahkannya ke services/ akan melanggar kontrak 'services hanya boleh import core dan persistence'. Folder server/services/ dihapus. Update importer: server/handlers/event_listeners.py, server/app.py. Test dipindah: tests/unit/services/test_stream_prefetch.py, tests/unit/server/test_broadcast_service.py. Dokumentasi diupdate: docs/backend/services.md (keputusan+konvensi suffix), docs/backend/background_jobs.md, docs/testing/unit_testing.md, docs/INDEX.md, docs/architecture/backend.md, docs/architecture/data_flow.md, docs/adr/0005-websocket-single-channel.md. Verifikasi: pytest 594 passed 0 failed, lint-imports 7 kept 0 broken (verified real, bukan false positive), architecture_lint PASS, doctor PASS, wiring server/app.py dicek manual.

**ID:** `PATCH-2026-07-18-090`

**Tanggal:** 2026-07-18

**Ringkasan:** T2.7: Satukan services/ (root) dan server/services/. stream_prefetch.py pindah ke services/stream_prefetch.py sesuai rencana (hanya impor config+core). broadcast_service.py TIDAK dipindah ke root services/ (deviasi dari rencana) melainkan ke server/broadcast_service.py, karena mengimpor server.connection_manager dan server.serializers (konstruksi web/wire layer) -- begitu bug .importlinter (PATCH-2026-07-18-089) diperbaiki, memindahkannya ke services/ akan melanggar kontrak 'services hanya boleh import core dan persistence'. Folder server/services/ dihapus. Update importer: server/handlers/event_listeners.py, server/app.py. Test dipindah: tests/unit/services/test_stream_prefetch.py, tests/unit/server/test_broadcast_service.py. Dokumentasi diupdate: docs/backend/services.md (keputusan+konvensi suffix), docs/backend/background_jobs.md, docs/testing/unit_testing.md, docs/INDEX.md, docs/architecture/backend.md, docs/architecture/data_flow.md, docs/adr/0005-websocket-single-channel.md. Verifikasi: pytest 594 passed 0 failed, lint-imports 7 kept 0 broken (verified real, bukan false positive), architecture_lint PASS, doctor PASS, wiring server/app.py dicek manual.

**File Terdampak:**

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

---

## [2026-07-18] Perbaiki bug syntax .importlinter: forbidden_modules/source_modules pakai koma-satu-baris yang TIDAK di-parse import-linter (SetField hanya split per-baris, bukan per-koma) — 6 dari 7 kontrak selama ini silently no-op (selalu KEPT tanpa benar-benar cek apa pun). Diverifikasi langsung ke source import-linter (grimp.find_shortest_chains + ForbiddenContract.check). Diperbaiki jadi format list per-baris (sama seperti root_packages yang sudah benar). Baseline lint-imports pasca-perbaikan: 7 kept, 0 broken (genuinely verified, bukan false positive).

**ID:** `PATCH-2026-07-18-089`

**Tanggal:** 2026-07-18

**Ringkasan:** Perbaiki bug syntax .importlinter: forbidden_modules/source_modules pakai koma-satu-baris yang TIDAK di-parse import-linter (SetField hanya split per-baris, bukan per-koma) — 6 dari 7 kontrak selama ini silently no-op (selalu KEPT tanpa benar-benar cek apa pun). Diverifikasi langsung ke source import-linter (grimp.find_shortest_chains + ForbiddenContract.check). Diperbaiki jadi format list per-baris (sama seperti root_packages yang sudah benar). Baseline lint-imports pasca-perbaikan: 7 kept, 0 broken (genuinely verified, bukan false positive).

**File Terdampak:**

- `.importlinter`

---

## [2026-07-18] Perbaiki assertion salah di test_handle_playback_command_other_commands: CMD_PREV memang dikirim beserta data (simetris dengan CMD_NEXT, mendukung guard video_id opsional di _on_prev), bukan tanpa argumen. Baseline test suite sekarang 594 passed, 0 failed.

**ID:** `PATCH-2026-07-18-088`

**Tanggal:** 2026-07-18

**Ringkasan:** Perbaiki assertion salah di test_handle_playback_command_other_commands: CMD_PREV memang dikirim beserta data (simetris dengan CMD_NEXT, mendukung guard video_id opsional di _on_prev), bukan tanpa argumen. Baseline test suite sekarang 594 passed, 0 failed.

**File Terdampak:**

- `tests/unit/server/handlers/test_ws_playback.py`

---

## [2026-07-18] Gabungkan cache/resolver.py ke persistence/stream_cache.py, hapus folder cache/ (pb_html.txt statis dipindah ke data/, ws_cache.py tidak di-rename karena tidak terkait stream cache)

**ID:** `PATCH-2026-07-18-087`

**Tanggal:** 2026-07-18

**Ringkasan:** Gabungkan cache/resolver.py ke persistence/stream_cache.py, hapus folder cache/ (pb_html.txt statis dipindah ke data/, ws_cache.py tidak di-rename karena tidak terkait stream cache)

**File Terdampak:**

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

---

## [2026-07-18] Pecah main.py jadi bootstrap/ (services, startup_tasks, maintenance), main() jadi orkestrasi 4 langkah

**ID:** `PATCH-2026-07-18-086`

**Tanggal:** 2026-07-18

**Ringkasan:** Pecah main.py jadi bootstrap/ (services, startup_tasks, maintenance), main() jadi orkestrasi 4 langkah

**File Terdampak:**

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

---

## [2026-07-18] Pecah PlaybackController: ekstrak QueueController dan SettingsController, wiring delegasi via command_router

**ID:** `PATCH-2026-07-18-085`

**Tanggal:** 2026-07-18

**Ringkasan:** Pecah PlaybackController: ekstrak QueueController dan SettingsController, wiring delegasi via command_router

**File Terdampak:**

- `engine/playback/controller.py`
- `engine/playback/queue_controller.py`
- `engine/playback/settings_controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `tests/unit/engine/playback/test_queue_controller.py`
- `tests/unit/engine/playback/test_settings_controller.py`

---

## [2026-07-18] T2.2e: hapus facade Database (God Facade) dari persistence/__init__.py. Diganti Repositories: container tipis 1 koneksi + 6 repo domain (tracks/sessions/artists/genres/library/discover) tanpa method delegasi. main.py wiring ulang: CacheResolver dapat ResolverDbCompat (gabungan TrackRepository+ArtistRepository+DiscoverRepository, cuma utk resolver.db yg dipakai lintas domain oleh controller/track_loader/track_ended_ops/event_listeners -- BUKAN facade baru, tidak ada logic sendiri), LoudnessService dapat repos.tracks langsung, RadioMode dapat repos.artists+repos.library. server/app.py: create_app terima Repositories, app dict simpan 'repos'+'conn'+'tracks' (bukan 'db' facade penuh). http.py health_check pakai app['conn']. websocket.py: db->repos, handle_download_command sekarang terima tracks+discover terpisah (bukan db penuh) - ws_download.py diperbaiki mengikuti. scratch/check_db.py diperbaiki (Database sudah tidak ada). Enam file test yang pakai db fixture dgn flat facade call (test_track_repo, test_session_repo, test_artist_repo, test_genre_repo, test_discover_repo, test_discover_service) di-sed ke db.<repo>.<method>. test_ports.py ditulis ulang per-repo (bukan cek 1 Database god object). test_db.py ditulis ulang menguji persistence.db.DatabaseConnection langsung (bukan lewat facade). test_main.py, test_app.py, test_http.py, test_ws_download.py disesuaikan ke wiring baru. Hasil: 558 passed (baseline T0.2 sama persis), 1 failed pre-existing (test_ws_playback, tidak terkait), import-linter 7 kept/0 broken.

**ID:** `PATCH-2026-07-18-084`

**Tanggal:** 2026-07-18

**Ringkasan:** T2.2e: hapus facade Database (God Facade) dari persistence/__init__.py. Diganti Repositories: container tipis 1 koneksi + 6 repo domain (tracks/sessions/artists/genres/library/discover) tanpa method delegasi. main.py wiring ulang: CacheResolver dapat ResolverDbCompat (gabungan TrackRepository+ArtistRepository+DiscoverRepository, cuma utk resolver.db yg dipakai lintas domain oleh controller/track_loader/track_ended_ops/event_listeners -- BUKAN facade baru, tidak ada logic sendiri), LoudnessService dapat repos.tracks langsung, RadioMode dapat repos.artists+repos.library. server/app.py: create_app terima Repositories, app dict simpan 'repos'+'conn'+'tracks' (bukan 'db' facade penuh). http.py health_check pakai app['conn']. websocket.py: db->repos, handle_download_command sekarang terima tracks+discover terpisah (bukan db penuh) - ws_download.py diperbaiki mengikuti. scratch/check_db.py diperbaiki (Database sudah tidak ada). Enam file test yang pakai db fixture dgn flat facade call (test_track_repo, test_session_repo, test_artist_repo, test_genre_repo, test_discover_repo, test_discover_service) di-sed ke db.<repo>.<method>. test_ports.py ditulis ulang per-repo (bukan cek 1 Database god object). test_db.py ditulis ulang menguji persistence.db.DatabaseConnection langsung (bukan lewat facade). test_main.py, test_app.py, test_http.py, test_ws_download.py disesuaikan ke wiring baru. Hasil: 558 passed (baseline T0.2 sama persis), 1 failed pre-existing (test_ws_playback, tidak terkait), import-linter 7 kept/0 broken.

**File Terdampak:**

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

---

## [2026-07-18] Migrasi discover_service dan ws_discovery ke DiscoverRepository langsung (T2.2d). DiscoverService kini menerima DiscoverRepository (bukan facade Database) via param 'discover'; tambah DiscoverRepositoryPort di core/ports.py dan property conn publik di DiscoverRepository (pola sama dgn artist_repo.py/library_repo.py T2.2c). handle_discovery_command di ws_discovery.py menerima discover_repo langsung. server/handlers/websocket.py disentuh 1 baris untuk wiring db.discover (melanjutkan izin eksplisit yg sama dgn T2.2c). Konsumen lain DiscoverService yang tadinya pass facade penuh (event_listeners.py, ws_download.py) ikut diperbaiki ke db.discover supaya tidak pecah runtime, walau di luar SOP-A target eksplisit task ini.

**ID:** `PATCH-2026-07-18-083`

**Tanggal:** 2026-07-18

**Ringkasan:** Migrasi discover_service dan ws_discovery ke DiscoverRepository langsung (T2.2d). DiscoverService kini menerima DiscoverRepository (bukan facade Database) via param 'discover'; tambah DiscoverRepositoryPort di core/ports.py dan property conn publik di DiscoverRepository (pola sama dgn artist_repo.py/library_repo.py T2.2c). handle_discovery_command di ws_discovery.py menerima discover_repo langsung. server/handlers/websocket.py disentuh 1 baris untuk wiring db.discover (melanjutkan izin eksplisit yg sama dgn T2.2c). Konsumen lain DiscoverService yang tadinya pass facade penuh (event_listeners.py, ws_download.py) ikut diperbaiki ke db.discover supaya tidak pecah runtime, walau di luar SOP-A target eksplisit task ini.

**File Terdampak:**

- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `server/handlers/websocket.py`
- `server/handlers/event_listeners.py`
- `server/handlers/ws_download.py`
- `persistence/discover_repo.py`
- `core/ports.py`
- `tests/unit/services/test_discover_service.py`

---

## [2026-07-18] T2.2c: migrasi konsumen domain session/artist/genre/library ke repository masing-masing langsung (session/artist/genre/library repo properties baru di facade Database: sessions, artists, genres, library). auth.py->SessionRepository, ws_queue.py->ArtistRepository+GenreRepository (mixed 2 domain dalam 1 file), artist_selector.py/RadioMode->ArtistRepository+LibraryRepository (mixed 2 domain). Tambah properti conn publik di ArtistRepository & LibraryRepository utk liveness-check yang sudah ada sebelumnya. websocket.py (sebelumnya frozen) diedit di call-site dispatch (izin eksplisit user, bukan spontan) utk narrow db->db.sessions / db.artists,db.genres. Discovery/download/cache command tetap pakai db penuh (butuh T2.2d).

**ID:** `PATCH-2026-07-18-082`

**Tanggal:** 2026-07-18

**Ringkasan:** T2.2c: migrasi konsumen domain session/artist/genre/library ke repository masing-masing langsung (session/artist/genre/library repo properties baru di facade Database: sessions, artists, genres, library). auth.py->SessionRepository, ws_queue.py->ArtistRepository+GenreRepository (mixed 2 domain dalam 1 file), artist_selector.py/RadioMode->ArtistRepository+LibraryRepository (mixed 2 domain). Tambah properti conn publik di ArtistRepository & LibraryRepository utk liveness-check yang sudah ada sebelumnya. websocket.py (sebelumnya frozen) diedit di call-site dispatch (izin eksplisit user, bukan spontan) utk narrow db->db.sessions / db.artists,db.genres. Discovery/download/cache command tetap pakai db penuh (butuh T2.2d).

**File Terdampak:**

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

---

## [2026-07-18] T2.2b: migrasi konsumen domain track yang aman (StreamPrefetchService, serve_stream di http.py) ke TrackRepository langsung via db.tracks property baru di facade Database. resolver.py/event_listeners.py/ws_download.py/track_loader.py/track_ended_ops.py TIDAK dinarrow di task ini — resolver.db dipakai lintas-domain (StreamResolverPort.db bertipe DatabasePort penuh, dipakai controller.py utk record_completion/record_skip [artis] dan event_listeners.py/ws_download.py utk instansiasi DiscoverService inline [discover]); narrow resolver.py baru aman setelah T2.2c (artist) dan T2.2d (discover) beres, dan controller.py sendiri frozen (butuh T2.3 utk disentuh).

**ID:** `PATCH-2026-07-18-081`

**Tanggal:** 2026-07-18

**Ringkasan:** T2.2b: migrasi konsumen domain track yang aman (StreamPrefetchService, serve_stream di http.py) ke TrackRepository langsung via db.tracks property baru di facade Database. resolver.py/event_listeners.py/ws_download.py/track_loader.py/track_ended_ops.py TIDAK dinarrow di task ini — resolver.db dipakai lintas-domain (StreamResolverPort.db bertipe DatabasePort penuh, dipakai controller.py utk record_completion/record_skip [artis] dan event_listeners.py/ws_download.py utk instansiasi DiscoverService inline [discover]); narrow resolver.py baru aman setelah T2.2c (artist) dan T2.2d (discover) beres, dan controller.py sendiri frozen (butuh T2.3 utk disentuh).

**File Terdampak:**

- `persistence/__init__.py`
- `server/services/stream_prefetch.py`
- `server/app.py`
- `server/handlers/http.py`
- `tests/unit/server/handlers/test_http.py`

---

## [2026-07-18] T2.2a: Ekstrak lifecycle koneksi Database ke persistence/db.py (DatabaseConnection sudah ada sejak sebelumnya; pindahkan _migrate_songs_unique_constraint ke sana juga), Database jadi facade tipis

**ID:** `PATCH-2026-07-18-080`

**Tanggal:** 2026-07-18

**Ringkasan:** T2.2a: Ekstrak lifecycle koneksi Database ke persistence/db.py (DatabaseConnection sudah ada sejak sebelumnya; pindahkan _migrate_songs_unique_constraint ke sana juga), Database jadi facade tipis

**File Terdampak:**

- `persistence/db.py`
- `persistence/__init__.py`

---

## [2026-07-18] Hapus 6 file alias backward-compat setelah semua konsumen dipindah ke sumber asli

**ID:** `PATCH-2026-07-18-079`

**Tanggal:** 2026-07-18

**Ringkasan:** Hapus 6 file alias backward-compat setelah semua konsumen dipindah ke sumber asli

**File Terdampak:**

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

---

## [2026-07-18] Luruskan import di main.py dan controller.py ke sumber asli (persistence, adapters.mpv, adapters.ytdlp, engine.radio), file alias masih ada sebagai fallback

**ID:** `PATCH-2026-07-18-078`

**Tanggal:** 2026-07-18

**Ringkasan:** Luruskan import di main.py dan controller.py ke sumber asli (persistence, adapters.mpv, adapters.ytdlp, engine.radio), file alias masih ada sebagai fallback

**File Terdampak:**

- `main.py`
- `engine/playback/controller.py`

---

## [2026-07-18] Pindahkan admin_password.txt ke instance/ (di luar tracking git) dan perluas .gitignore

**ID:** `PATCH-2026-07-18-077`

**Tanggal:** 2026-07-18

**Ringkasan:** Pindahkan admin_password.txt ke instance/ (di luar tracking git) dan perluas .gitignore

**File Terdampak:**

- `.gitignore`
- `launcher/gui/auth_panel.py`
- `tests/unit/launcher/gui/test_auth_panel.py`

---

## [2026-07-18] Fase 0 selesai: buat branch refactor/roadmap, catat baseline pytest (558 passed, 1 pre-existing failed, 6 skipped) dan baseline lint-imports (7 kept, 0 broken) di docs/STATUS.md

**ID:** `PATCH-2026-07-18-076`

**Tanggal:** 2026-07-18

**Ringkasan:** Fase 0 selesai: buat branch refactor/roadmap, catat baseline pytest (558 passed, 1 pre-existing failed, 6 skipped) dan baseline lint-imports (7 kept, 0 broken) di docs/STATUS.md

**File Terdampak:**

- `docs/STATUS.md`

---

## [2026-07-18] fix bug tools patchloh yang gagal mengurutkan patch dan membuat patch tidak increment jadi jadi 001 bukan meneruskan id yang ada

**ID:** `PATCH-2026-07-18-075`

**Tanggal:** 2026-07-18

**Ringkasan:** fix bug tools patchloh yang gagal mengurutkan patch dan membuat patch tidak increment jadi jadi 001 bukan meneruskan id yang ada

**File Terdampak:**

- `patchlog.py`

---

## [2026-07-17] merapikan dokumen patchlog

**ID:** `PATCH-2026-07-17-074`

**Tanggal:** 2026-07-17

**Ringkasan:** merapikan dokumen patchlog

**File Terdampak:**

- `PATCHLOG.MD`

---

## [2026-07-17] UI/UX revamp tab discover (progressive disclosure hashtag/list, role-gate access, keyboard accessibility, filter scope)

**ID:** `PATCH-2026-07-17-073`

**Tanggal:** 2026-07-17

**Ringkasan:** UI/UX revamp tab discover (progressive disclosure hashtag/list, role-gate access, keyboard accessibility, filter scope)

**File Terdampak:**

- `server/handlers/ws_discovery.py`
- `web/static/js/render/discover-tab.js`
- `web/static/js/events/click-delegation-events.js`
- `web/static/index.html`
- `web/static/css/components/discover-cards.css`
- `web/static/js/render/discover-personalize.js`

---

## [2026-07-17] Patch — Sinkronisasi Referensi automation/

**ID:** `PATCH-2026-07-17-072`

**Tanggal:** 2026-07-17

**Ringkasan:** Menyelaraskan nama direktori dan modul internal dari `scripts/` menjadi `automation/` di seluruh dokumentasi dan docstring file Python. Juga menghapus blok instruksi peringatan migrasi di `AI_CONTEXT.md` sesuai dengan instruksi yang tertera di sana.

**File Terdampak:**

- `AI_CONTEXT.md` — [MODIFIED] hapus catatan migrasi.
- `automation/**/*.py` — [MODIFIED] update docstring Module dari `scripts.` menjadi `automation.`.
- `automation/shared/skip_dirs.py` — [MODIFIED] update skip dirs `"scripts"` menjadi `"automation"`.
- `automation/shared/arch_rules.py` — [MODIFIED] update arch rules.
- `automation/find_owner.py` — [MODIFIED] update pemetaan folder.
- `docs/*.md` — [MODIFIED] referensi `scripts/` di-update ke `automation/` (non-historical file).

---

## [2026-07-17] Discover Tab revamp — frontend wiring (taste spectrum, filter bar, 3 card-row, artist detail sheet)

**ID:** `PATCH-2026-07-17-071`

**Tanggal:** 2026-07-17

**Ringkasan:** Melanjutkan `PATCH-2026-07-17-070` (backend-only) sesuai `discover-tab-frontend-handoff.md`. Semua data personalisasi yang sudah dikirim backend kini benar-benar sampai ke UI dan bisa dipakai user. 1. **`server/handlers/websocket.py`** — izin eksplisit diberikan user (file ini *restricted* per `AI_CONTEXT.md`). Ditambah 1 baris: `"get_artist_detail"` ke `DISCOVERY_CMDS`, sehingga action yang sudah diimplementasi di `ws_discovery.py` sejak PATCH-070 kini benar-benar reachable dari client. 2. **`web/static/js/store.js`** — tambah default `discover_for_you`, `discover_unheard`, `discover_genre_affinity_genre`, `discover_genre_affinity_artists`, `discover_taste_spectrum`. 3. **`web/static/js/ws.js`** — `case "discover_data"` sekarang menyimpan 5 field baru dari payload + memanggil `renderDiscoverPersonalization()`. Tambah `case "artist_detail"` baru (sebelumnya di-drop diam-diam karena tidak ada `default:` case). 4. **`web/static/js/dom.js`** — register elemen baru: taste bar/legend, filter bar (segmented + chip row), 3 card-row (`rowForYou`, `rowGenreAffinity`, `rowUnheard`), sheet `artistDetailSheet` + cover/nama/tag/track-list/tombol di dalamnya. 5. **`web/static/js/render/discover-personalize.js` (baru, 185 baris).** Semua logic render + interaksi personalisasi: taste bar dari `discover_taste_spectrum` (dengan fallback "Dengarkan beberapa lagu dulu..." kalau kosong), kartu artis generik (cover + nama + genre tag, badge `match_pct` untuk "Untuk Kamu", badge "Baru" + varian `.undiscovered` untuk "Belum Pernah Kamu Dengar"), filter kategori + dekade client-side (dekade dibangun dari nilai `tahun_aktif` aktual yang ada di data, bukan hard-coded), handler tap kartu → `wsSend('get_artist_detail', ...)` → isi & buka sheet saat `handleArtistDetail()` dipanggil dari `ws.js`, tombol "Putar Semua" → reuse `enqueue_artist_songs` dengan role-gate (`store.userRole !== 'admin'` → toast) konsisten dengan pola Discover lain. `discover-tab.js` (sudah lewat ambang 200 baris) **tidak disentuh sama sekali** — tetap fokus ke recent/favorites/cached/hashtag-cloud. 6. **`web/static/css/components/discover-cards.css` (baru).** `.taste-bar`/ `.taste-legend`, `.filter-bar`/`.segmented`/`.chip`, `.artist-card` (+ varian `.undiscovered`), styling konten `.ads-*` untuk artist detail sheet. Genre tag pakai palet kecil kurasi (`--g-pop`, `--g-rock`, dst, didefinisikan lokal di file ini) bukan `hsl(random)`. Tidak ada CSS baru untuk shell sheet — reuse `.settings-sheet` yang sudah ada. 7. **`web/static/index.html`** — markup taste spectrum + filter bar + 3 card-row disisipkan di bawah header Discover, sebelum "Jelajahi Artis"/"Jelajahi Genre" yang sudah ada. Sheet baru `<div class="settings-sheet" id="artist-detail-sheet">` (reuse pola `#action-sheet`/`#help-sheet` + `#main-overlay`). Ditambah 1 link CSS (`discover-cards.css`) dan 1 script tag (`render/discover-personalize.js`). 8. **`web/static/js/events/settings-events.js`** — `closeMainOverlay()` ditambah 1 baris supaya `artistDetailSheet` ikut ketutup saat backdrop di-tap, konsisten dengan sheet lain. 9. **`web/static/js/events/index.js`** — daftarkan `initDiscoverFilterEvents()` di urutan init yang sama dengan `initSettingsEvents()` dkk. **Verifikasi otomatis:** `automation/doctor.py`, `generate_file_index.py`, `generate_report.py` dijalankan bersih untuk file yang disentuh sesi ini (2 FAIL yang tersisa — `engine/playback/controller.py` 464 baris & `.gitignore` hilang — sudah ada sebelum sesi ini, tidak disentuh/diperparah oleh patch ini).

**File Terdampak:**

- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/ws.js`
- `web/static/js/dom.js`
- `web/static/js/render/discover-personalize.js` (baru)
- `web/static/css/components/discover-cards.css` (baru)
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/events/index.js`

---

## [2026-07-17] Discover Tab revamp — backend saja (personalisasi: bandit ranking, unheard artists, taste spectrum, genre affinity, artist detail)

**ID:** `PATCH-2026-07-17-070`

**Tanggal:** 2026-07-17

**Ringkasan:** Eksekusi bagian backend dari `discover-tab-implementation-plan-v2.md` (v2 dipakai, bukan v1 — lihat alasan di bawah). **Frontend sengaja belum disentuh sama sekali** — task ini eksplisit diminta backend-only, siap dilanjutkan sesi lain oleh frontend designer/programmer. Lihat `docs/STATUS.md` §"Discover Tab Personalization — Backend" untuk ringkasan siap-pakai yang ditujukan buat sesi lanjutan itu. 1. **`persistence/discover_enrich.py` (baru, 78 baris).** `enrich_artists(conn, rows)` — helper bersama: attach `cover` (thumbnail YouTube dari lagu pertama artis, `MIN(id)` bukan `RANDOM()` supaya deterministic/tidak flicker) + `genres` (list tag) ke sekumpulan artist row sekaligus. 2 query total untuk berapa pun jumlah artis (hindari N+1). 2. **`persistence/discover_repo.py` (baru, 242 baris).** `class DiscoverRepository` — **keputusan v2, bukan v1**: v1 rencananya nambah method ini ke `artist_repo.py`/`genre_repo.py` (116/97 baris saat itu), tapi itu akan mendorong keduanya ke zona Waspada (>150 baris) padahal tanggung jawab aslinya cuma click/reward tracking, bukan personalisasi. Jadi repo terpisah, sejajar `LibraryRepository`. Method: `get_bandit_ranked_artists(limit)` ("Untuk Kamu", ranking posterior mean `alpha/(alpha+beta)`, exclude artis yang belum tersentuh bandit sama sekali), `get_unheard_artists(limit)` ("Belum Pernah Kamu Dengar", filter `alpha=beta=1 AND click_count=0`), `get_taste_spectrum(limit=6)` (agregasi genre dari `tracks.play_count + is_favorite*3`, dinormalisasi ke persentase + bucket "Lainnya" untuk sisa genre di luar top-N; `[]` kalau histori kosong), `get_top_genre()` (elemen pertama taste spectrum atau `None`), `get_genre_artists_enriched(genre, limit)`, `get_artist_detail(nama)` (info + genre + hingga 10 lagu, urut by id bukan random, untuk detail sheet yang stabil antar-buka). File ini masuk zona **Waspada** (242 baris, ambang 150-300) — bukan pelanggaran, tapi kalau nanti ada section Discover baru lagi, pertimbangkan pecah per jenis query dulu sebelum tembus 300. 3. **`persistence/__init__.py`:** import + instansiasi `DiscoverRepository` (`self._discover`), delegasi 6 method baru di atas — pola sama persis dengan repo lain yang sudah ada. 4. **`services/discover_service.py`** (161 → 208 baris, tetap zona Waspada tapi belum "wajib pecah"): 5 wrapper method baru — `get_for_you`, `get_unheard`, `get_genre_affinity` (return `{genre, artists}`, `genre=None` kalau histori kosong), `get_taste_spectrum`, `get_artist_detail` — semua delegasi ke facade `Database` seperti method lain di file ini, guard `getattr(self.db, "conn", None)` konsisten dengan pola existing. 5. **`server/handlers/ws_discovery.py`:** action `discover` — `asyncio.gather` diperluas dari 5 jadi 9 query paralel, payload `discover_data` nambah 5 field (`for_you`, `unheard`, `genre_affinity_genre`, `genre_affinity_artists`, `taste_spectrum`). Action baru `get_artist_detail` diimplementasikan lengkap (terima `{artist: nama}`, balas `{type: "artist_detail", data: {...} | null}`). 6. **`server/handlers/websocket.py` — SENGAJA TIDAK DISENTUH.** File ini *restricted* di `AI_CONTEXT.md` ("tidak boleh disentuh tanpa izin eksplisit"). Perubahan yang dibutuhkan cuma 1 baris (tambah `"get_artist_detail"` ke `DISCOVERY_CMDS`), tapi izin eksplisit belum diminta/didapat di sesi ini — jadi **action `get_artist_detail` sudah diimplementasikan di `ws_discovery.py` tapi belum bisa dipanggil sama sekali** lewat WS asli sampai baris itu ditambah. Action `discover` yang sudah diperluas TIDAK terpengaruh blocker ini (sudah ada di `DISCOVERY_CMDS` sebelumnya). 7. **Test (mirror per Prinsip #2):** `tests/unit/persistence/test_discover_repo.py` (baru, 14 test, mencakup semua method + edge case histori kosong/artist tidak ditemukan/cap 10 lagu). `test_discover_service.py` (+12 test untuk 5 wrapper baru). `test_ws_discovery.py` (+4 test: payload personalisasi lengkap, `get_artist_detail` sukses, `get_artist_detail` dengan nama kosong tidak memanggil service — plus 1 test lama diupdate supaya tidak break setelah `gather` diperluas dari 5→9 query). 8. **Automation:** `generate_file_index.py` + `generate_report.py` dijalankan ulang (file baru: `discover_repo.py`, `discover_enrich.py`, `test_discover_repo.py`). `doctor.py` bersih untuk semua yang diubah di patch ini — satu-satunya FAIL yang tersisa (`engine/playback/controller.py` 464 baris) adalah temuan pre-existing dari sesi sebelumnya, tidak disentuh atau diperparah oleh patch ini. **Hasil test:** 522 unit test lulus (naik dari 508 baseline), 0 gagal. `tests/unit/launcher/gui/*` tidak ikut collect di environment eksekusi ini (`ModuleNotFoundError: tkinter`, pre-existing keterbatasan environment, bukan regresi dari patch ini).

**File Terdampak:**

- `persistence/discover_enrich.py` (baru)
- `persistence/discover_repo.py` (baru)
- `persistence/__init__.py`
- `services/discover_service.py`
- `server/handlers/ws_discovery.py`
- `tests/unit/persistence/test_discover_repo.py` (baru)
- `tests/unit/services/test_discover_service.py`
- `tests/unit/server/handlers/test_ws_discovery.py`
- `docs/STATUS.md`
- `docs/discover-tab-frontend-handoff.md` (baru — laporan handoff detail utk sesi frontend berikutnya: kontrak payload, gap ws.js/store.js yang tidak disebut di implementation-plan-v2.md, urutan pengerjaan, checklist)
- `docs/FILE_INDEX.md` (auto-generated)
- `docs/REPORT.md` (auto-generated)
- `server/handlers/websocket.py` (butuh izin eksplisit, 1 baris)
- `web/static/js/dom.js`, `web/static/index.html`,

---

## [2026-07-16] Eksekusi implementation-plan.md (Batch 0–4.2): CI hang, timing side-channel, race condition crossfade, SponsorBlock window, parser LRC, lifecycle EventBus/CommandBus

**ID:** `PATCH-2026-07-16-069`

**Tanggal:** 2026-07-16

**Ringkasan:** Eksekusi penuh `implementation-plan.md` (hasil verifikasi `summary-1.md`, 16 Juli 2026), batch demi batch. Beberapa item (#1 dedup title radio, #2 race crossfade, #4 metrics token compare, #11 sebagian dead code) ternyata **sudah** diperbaiki sebelumnya di codebase (kemungkinan patch manual terpisah) — diverifikasi ulang, tidak diubah lagi. Item yang benar-benar dieksekusi di sesi ini: 1. **Batch 0 (CI hang):** Tambah `pytest-timeout` (jaring pengaman, 60s/thread) di `pytest.ini` + `requirements-dev.txt`. `main.py` shutdown: `task.cancel()` sekarang diikuti `await asyncio.gather(*tasks, return_exceptions=True)`. `adapters/mpv/observer.py.stop()`: await task sampai tuntas setelah cancel. **Terverifikasi lewat eksekusi nyata** (bukan cuma analisis): baseline suite sebelumnya meninggalkan zombie non-daemon thread (`conftest.py` sampai perlu `os._exit()` paksa); setelah fix, suite exit bersih tanpa paksaan. 2. **Batch 1:** (#3) fast-skip `shutil.which("mpv")` dipindah SEBELUM `db.init()` di `tests/integration/conftest.py` — ditemukan lewat testing bahwa urutan lama (db.init() sebelum skip check) bikin fixture generator skip sebelum `yield`, jadi teardown `db.close()` tidak pernah jalan -> connection thread leak (root cause zombie thread kedua, di luar dugaan awal plan). (#5) `persistence/db.py.close()`: ganti `asyncio.sleep(0.01)` dengan `asyncio.to_thread(worker_thread.join, timeout=1.0)` -- join asli, bukan tebak-tebakan delay. (#4) `server/handlers/auth.py`: hilangkan short-circuit `and` yang skip `verify_password` kalau username salah (celah timing side-channel enumerasi username) — sekarang `verify_password` selalu jalan. (#11) hapus `clear_standby()` (stub `pass`, tak terpakai) di `engine/radio/prefetcher.py`; `check_rate_limit_sync()` & `secrets.compare_digest()` di `http.py` ternyata sudah dibersihkan sebelumnya. `controller.py._last_position_save` ternyata sudah tersambung benar (bukan dead code seperti dugaan plan, tidak diubah). (#12) `main.py:339` bare `except:` -> `except Exception:`. 3. **Batch 2.3 (#7):** `plugins/sponsorblock.py` — ganti window deteksi sempit (`start <= pos <= start+0.6`) yang bisa terlewat kalau progress event melompat, dengan one-directional check (`start <= pos < end`) + flag `_skipped_segments` per-track (direset tiap `fetch_segments`). Perbaiki docstring throttle interval yang salah ("~0.5s" -> "~1.0s"). 4. **Batch 3:** Test baru `tests/unit/engine/playback/test_track_ended_ops.py` (modul sebelumnya nol coverage) — grace-window `_handle_stop()`, dispatch eof/stop/error, `poll_duration`. 5. **Batch 4.1 (#8):** `plugins/lyrics_parser.py` — parser LRC diganti total: dukung multi-timestamp per baris (chorus berulang), skip tag metadata (`[ar:...]`, `[ti:...]`) alih-alih dianggap teks lirik biasa. 6. **Batch 4.2 (#6):** `core/command_bus.py` tambah `reset()` resmi (ganti akses langsung `_handlers.clear()` di `tests/integration/conftest.py`). `engine/playback/controller.py` tambah `dispose()` — unsubscribe 5 handler (termasuk 3 lambda closure yang referensinya kini disimpan sebagai atribut instance agar bisa di-unsubscribe balik), cancel `_fade_task` pending. Didokumentasikan eksplisit kenapa 3 lambda itu sengaja strong-ref (bukan bug WeakMethod). 7. **Bonus (ditemukan saat eksekusi, di luar 12 temuan awal):** `automation/patchlog.py.parse_entries()` — regex tunggal dengan beberapa `.*?` + `re.DOTALL` di-scan ke seluruh file (35KB, 28 entry berulang) menyebabkan catastrophic backtracking, hang tak terhingga (dikonfirmasi lewat eksekusi langsung dengan timeout). Diganti dengan split per-entry (separator `\n\n---\n\n`) dulu, baru regex sederhana per-chunk. 8. **Tidak dieksekusi (sesuai arahan plan sendiri):** #10 (tombol "prev" / forward-stack) — butuh keputusan produk dulu, belum diajukan ke user di sesi ini. `test_radio_flow.py` mock network (0.4, opsional/prioritas rendah) — tidak disentuh. **Hasil akhir:** 508 passed, 6 skipped (naik dari baseline 475 passed, 6 skipped) — unit + integration (integration tetap skip karena `mpv`/`yt-dlp` tidak terpasang di sandbox). `ruff check` bersih, `mypy` bersih (10 file diubah), `bandit` tanpa temuan baru, coverage total 88%.

**File Terdampak:**

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

---

## [2026-07-16] Migration to Windows Named Pipes IPC & Integration Test Stabilization

**ID:** `PATCH-2026-07-16-068`

**Tanggal:** 2026-07-16

**Ringkasan:** 1. Mengubah mekanisme IPC dari TCP Sockets menjadi Windows Named Pipes (`\\.\pipe\mpv-lunawave`) untuk meningkatkan reliabilitas koneksi dengan proses MPV di OS Windows, menghilangkan limitasi socket exhaustion, dan mengurangi latensi. 2. Memperbaiki *regression* (Zombie non-daemon threads / Timeout) dan *flakiness* di dalam suite tes integrasi akibat perubahan *interface*, serta menyesuaikan timeout ekspektasi dari `yt-dlp`. - **Fix 1 (Pipes IPC):** `MpvConnection` kini melakukan inisialisasi pada `\\.\pipe\mpv-lunawave` alih-alih port TCP `6666`. `MpvObserver` disesuaikan untuk membaca dari pipe yang sama. Seluruh parameter setup TCP di `run_server()` dihilangkan. - **Fix 2 (Integration Test Setup):** `tests/integration/conftest.py` ditambahkan command `command_bus._handlers.clear()` untuk menghindari `RuntimeError` duplikasi handler pada tes yang dijalankan secara berurutan. - **Fix 3 (Test Syncs):** Penyesuaian nama metode (`download_mp3` -> `download_audio`), penambahan field `artist` pada objek `TrackInfo`, perubahan field `file_path` pada `DownloadCompleteEvent` menjadi `track.local_path`, serta update ID video yang *geo-restricted* ke video yang stabil (`jNQXAC9IVRw` - Me at the zoo).

**File Terdampak:**

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

---

## [2026-07-16] Startup Latency Optimization — 3 Fix: MPV Non-Blocking, Resume Background Task, Windows TCP Polling

**ID:** `PATCH-2026-07-16-067`

**Tanggal:** 2026-07-16

**Ringkasan:** Tiga perbaikan startup latency berurutan berdasarkan analisis mendalam 5-tahap chain dari GUI klik "Start" sampai browser dapat diakses. Total estimasi gain: **1.5–25+ detik** tergantung kondisi. - **Fix 1 (Dampak terbesar, 1–20+ detik):** "Resume last playback" dipindah dari critical path ke background task (`safe_create_task`). Sebelumnya, kalau stream URL track terakhir sudah expired >6 jam, `main.py` akan melakukan network request ke YouTube via `yt-dlp` (max 25 detik timeout) *sebelum* `run_server()` dipanggil. Sekarang resume berjalan concurrently — browser bisa connect ke UI sementara resume masih diproses di background. - **Fix 2 (0.3–2 detik):** `mpv.connect()` dipindah dari `asyncio.gather()` blocking ke background task. Web server kini bisa bind port dan menerima koneksi tanpa menunggu MPV spawn + IPC handshake. Koordinasi lewat `asyncio.Event _mpv_ready_event` — resume task menunggu MPV siap (tanpa timeout) sebelum memanggil `play_track()`, tanpa memblok server. - **Fix 3 (0–1 detik, selalu di Windows):** Ganti `await asyncio.sleep(1.0)` blind wait di Windows dengan polling TCP port aktif (50 iterasi × 100ms = max 5 detik, keluar lebih awal begitu MPV siap). Best-case selesai dalam ~100ms, bukan selalu 1000ms. - **Tests:** Update 4 test lama di `test_connection.py` (assertion call count disesuaikan dengan polling behavior baru), tambah 2 test baru untuk polling Windows, tambah 1 test baru `test_run_server_not_blocked_by_mpv` dengan event-based coordination. 11/11 test pass.

**File Terdampak:**

- `main.py`
- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`
- `tests/unit/test_main.py`

---

## [2026-07-16] Full Audit — Frontend (web/static/js/) — Search Mati Total, Volume Slider Dead, Crossfade Dead Code

**ID:** `PATCH-2026-07-16-066`

**Tanggal:** 2026-07-16

**Ringkasan:** Audit menyeluruh pertama kali untuk SELURUH `web/static/js/` (31 file, semua diperiksa baris-per-baris; backend tidak disentuh). 6 bug CONFIRMED (dieksekusi/reproduksi nyata, bukan cuma baca kode) dan beberapa dead-code/minor findings. - **BUG-1 (Kritis, CONFIRMED):** `#vol-slider` ada di `index.html` tapi tidak pernah dipetakan di `dom.js` (`dom.volSlider` selalu `undefined`). Akibatnya seluruh listener drag volume di `transport-events.js` tidak pernah ter-attach (`if (dom.volSlider)` selalu false) dan render/player.js tidak pernah sinkron nilainya — slider volume 100% non-fungsional dari awal. Fix: tambah `volSlider: $("vol-slider")` ke `dom.js`. - **BUG-2 (Kritis, CONFIRMED lewat eksekusi nyata):** `window.safeStorage` cuma expose `.get/.set/.remove` (lihat `utils/toast.js`), tapi `search-input-events.js` memanggil `.getItem/.setItem/.removeItem` gaya `localStorage` yang TIDAK ADA di objek itu. `saveSearchHistory()` throw `TypeError` tak tertangkap, dan karena baris ini dipanggil SEBELUM `wsSend("search", ...)` baik di debounce-input maupun handler Enter, exception ini menghentikan seluruh callback → `wsSend("search")` TIDAK PERNAH terpanggil. Direproduksi dengan skrip Node standalone yang meniru pola kode persis — dikonfirmasi search tidak terkirim. **Dampak: fitur SEARCH mati total di seluruh aplikasi**, bukan cuma riwayat pencarian. Fix: ganti ke `.get/.set/.remove`, bungkus `saveSearchHistory` dengan try/catch sebagai defense-in-depth. - **BUG-3 (Kritis, CONFIRMED):** `render/player.js` (`_renderProgressCore`) memakai `window.audio` untuk logic volume-fade crossfade, tapi `window.audio` TIDAK PERNAH di-assign di manapun (elemen `<audio>` browser diakses lewat `getOrInitAudio()`/`localAudio` di `audio/playback-sync.js`, bukan `window.audio`). Kondisi selalu falsy → seluruh efek fade-out/fade-in volume crossfade untuk output browser adalah dead code, toggle crossfade di Settings tidak berefek pada audio yang sedang main di mode browser. Fix: ganti ke `getOrInitAudio()`. - **BUG-4 (Sedang, CONFIRMED):** `platform/keyboard.js` memanggil `cmd('play')/cmd('next')/cmd('prev')` — fungsi `cmd` tidak pernah didefinisikan di manapun di codebase (grep kosong). `typeof cmd === 'function'` selalu false → ArrowLeft/ArrowRight/Space di desktop cuma `preventDefault()` tanpa efek (fitur mati sejak awal). Kasus `Space` juga duplicate listener dengan `events/keyboard-shortcut-events.js` (yang sudah admin-gated dan benar-benar jalan). Fix: hapus case Space yang duplikat, sambungkan ArrowLeft/ArrowRight langsung ke `wsSend` dengan guard admin. - **BUG-5 (XSS, CONFIRMED):** `search-input-events.js` → `renderSearchHistory()` menyisipkan query pencarian (asal input user, disimpan di localStorage) langsung ke `innerHTML` tanpa escape untuk teks yang tampil (`<span>${q}</span>`) — cuma tanda kutip `"` yang di-escape untuk atribut `data-query`. Query berisi markup HTML/script tersimpan lalu dieksekusi ulang tiap kali riwayat pencarian dirender (stored self-XSS). Fix: pakai `escapeHtml()` untuk teks maupun atribut. - **BUG-6 (Sedang, SUSPECTED — pola dikonfirmasi lewat perbandingan kode, belum direproduksi di device fisik):** `events/progress-events.js` (drag seek bar) tidak punya handler `pointercancel`, tidak seperti drag-reorder queue (`events/queue-events.js`) yang sudah benar menanganinya. Kalau pointer sequence di-cancel OS/browser di tengah drag (gesture back, incoming call, multi-touch) tanpa `pointerup`, `window.isDraggingPb` nyangkut `true` selamanya → progress bar freeze permanen (rAF interpolation loop dan `renderProgress()` sama-sama early-return selama flag itu true), walau playback tetap jalan normal. Fix: tambah handler `pointercancel` yang reset flag + release pointer capture. - **MINOR-1:** `ws.js` — `store.userRole = "admin"` ter-assign 2x berturut-turut di `auth_status` handler (sisa edit sebelumnya, harmless). Fix: hapus baris duplikat. - **MINOR-2:** `sw.js` — `PRECACHE_ASSETS` tidak menyertakan `audio/playback-sync.js` dan `audio/visualizer.js` (script inti pemutar audio browser). SW registration saat ini masih dimatikan di `main.js` jadi belum berdampak, tapi akan menyebabkan first-offline-load kehilangan script pemutar audio kalau SW diaktifkan lagi tanpa fix ini. Fix: tambahkan ke daftar precache. - **DEAD CODE (dilaporkan, TIDAK dihapus — di luar scope "fix bug", risiko regresi kalau dihapus tanpa keputusan desain):** - `events/click-delegation-events.js` blok 3 menangani selector `.disc-card, .fav-card, .search-result-item` — tidak ada kode render manapun (discover-tab.js, search.js) yang menghasilkan elemen dengan class ini (semua pakai `.sr-item`). Blok ini 100% unreachable, kemungkinan sisa refactor/rename lama. - `audio/visualizer.js`: `startVisualizerLoop()`/`resumeVisualizerLoop()` (visualizer asli berbasis Web Audio API `analyser`/`dataArray`) tidak pernah dipanggil dari manapun, dan `analyser`/`dataArray` (dideklarasikan di `playback-sync.js`) tidak pernah di-assign (tidak ada `createAnalyser()`/`createMediaElementSource()`). `initAudio()` cuma memanggil `startFakeBeatLoop()` (efek beat berbasis timer, bukan analisis audio asli) — implementasi analyser sepenuhnya mati, tergantikan tanpa dibersihkan. - `transport-events.js` mereferensikan `dom.btnStop` — tidak ada elemen `#btn-stop` di `index.html` dan tidak dipetakan di `dom.js`; guard `if (dom.btnStop)` membuat ini no-op aman, Stop tetap bisa diakses lewat `ss-stop-btn` di Settings sheet yang sudah benar. **Verifikasi:** `vitest run` 14/14 tetap passed (3 file test, tidak ada regresi), `node --check` bersih untuk semua 7 file yang diedit, reproduksi manual (skrip Node standalone) mengkonfirmasi BUG-2 sebelum & sesudah fix.

**File Terdampak:**

- `web/static/js/dom.js`
- `web/static/js/events/search-input-events.js`
- `web/static/js/render/player.js`
- `web/static/js/platform/keyboard.js`
- `web/static/js/events/progress-events.js`
- `web/static/js/ws.js`
- `web/static/sw.js`

---

## [2026-07-16] Full Audit — Race Condition di ConnectionManager.broadcast()

**ID:** `PATCH-2026-07-16-065`

**Tanggal:** 2026-07-16

**Ringkasan:** Full-codebase audit (breadth scan seluruh package + deep-dive area berisiko tinggi: core/event_bus.py, persistence/db.py, engine/sleep_timer.py, server/handlers/websocket.py, engine/radio/prefetcher.py lock ordering, server/connection_manager.py). Ditemukan CONFIRMED race condition di `ConnectionManager.broadcast()`: `results` dari `asyncio.gather()` dipasangkan (`zip()`) dengan `list(self.active_connections)` yang di-fetch ULANG setelah await, bukan snapshot yang sama dipakai untuk gather(). Kalau ada connect/disconnect konkuren selagi broadcast() masih await (mis. client baru connect, atau client lain di-disconnect independen oleh handler-nya sendiri), index/urutan list itu bisa berubah -> hasil send_str() salah dipasangkan ke ws yang salah -> client SEHAT bisa ikut ke-disconnect secara keliru. Direproduksi nyata (script manual + test suite, gagal 3/3 run di kode lama). Fix: pin SATU snapshot list, dipakai ulang untuk gather() maupun zip(), sehingga urutan selalu align terlepas dari mutasi konkuren pada active_connections.

**File Terdampak:**

- `server/connection_manager.py`
- `tests/unit/server/test_connection_manager.py`

---

## [2026-07-16] Audit launcher/ — Admin Lockout Total & Crash Thread Setelah GUI Ditutup

**ID:** `PATCH-2026-07-16-064`

**Tanggal:** 2026-07-16

**Ringkasan:** Audit mendalam pertama untuk `launcher/` (tkinter GUI server manager, sebelumnya belum pernah diaudit). Dua bug confirmed lewat eksekusi nyata: (1) **Kontrak file `cache/admin_password.txt` tidak sinkron** — `launcher/gui/auth_panel.py` menulis password yang SUDAH di-hash ke file itu, padahal `config.py` (dan `config_security.generate_admin_password()`) membaca isi file sebagai plaintext mentah lalu meng-hash-nya sendiri di setiap startup server. Akibatnya password yang ditampilkan ke user di dialog first-run/reset TIDAK PERNAH cocok dengan hash yang dipakai server untuk verifikasi login — admin lockout total. Dibuktikan lewat skrip reproduksi yang meniru alur `config.py`: `verify_password(raw_password, ADMIN_PASSWORD)` selalu `False`. Fix: `_reset_password()` sekarang menulis raw password (root cause ada di kontrak antar-modul, bukan di `core.security`). (2) **Race destroy vs background thread** — semua callback dari background thread (dependency checker, loop refresh status tiap 2 detik, log writer, restart timer, popup server-ready) memanggil `self.after()`/`app.after()` tanpa guard apapun. Begitu window GUI ditutup sementara thread masih berjalan, callback yang telat crash dengan `RuntimeError: main thread is not in main loop`. Direproduksi nyata lewat Xvfb headless + `threading.excepthook`. Fix: tambah flag `ServerManager._closing` (di-set di `destroy()`) dan helper `_safe_after()` yang dipakai di semua titik pemanggilan `.after()` dari thread/loop; loop `_refresh_status()` juga berhenti reschedule begitu closing. **Catatan tooling:** ditemukan bug tambahan (belum di-fix, di luar scope sesi ini) di `automation/patchlog.py` — `parse_entries()` gagal mem-parse `docs/PATCHLOG.md` yang sudah ada (mengembalikan 0 entri walau ada 63 entri valid), sehingga `patchlog.py add` salah menomori ID baru jadi `-001` dan menimpa `total_entries` jadi `1`. File tidak sengaja sempat tertimpa saat sesi ini dan sudah dipulihkan dari arsip asli sebelum lanjut. **SUSPECTED root cause** (belum diverifikasi lebih lanjut): kemungkinan mismatch regex `ENTRY_RE` terhadap format aktual (spasi/newline ganda) di file nyata — perlu audit terpisah, jangan pakai `patchlog.py add` sampai ini diperbaiki, edit `docs/PATCHLOG.md` manual dulu.

**File Terdampak:**

- `launcher/gui/auth_panel.py`
- `launcher/gui/app.py`
- `launcher/gui/controller.py`
- `tests/unit/launcher/gui/test_auth_panel.py`
- `tests/unit/launcher/gui/test_app_lifecycle.py`

---

## [2026-07-16] Data Integrity — Kolaborasi/Duet Lagu Hilang di Katalog Multi-Artis

**ID:** `PATCH-2026-07-16-063`

**Tanggal:** 2026-07-16

**Ringkasan:** Konfirmasi eksekusi nyata (bukan asumsi baca kode): `songs.youtube_id` punya constraint `UNIQUE` global, padahal lagu kolaborasi/duet (mis. "Separuh Aku" — Peterpan/NOAH/Ariel NOAH) sah dimiliki lebih dari satu artis. Akibatnya `data/export_to_sqlite.py` (dijalankan nyata terhadap `data/artists_enriched.json`) diam-diam membuang lagu itu dari katalog semua artis kecuali yang pertama ditemukan di JSON — 33 `youtube_id` di data nyata terpengaruh, total lagu ter-export turun dari 1000 jadi 963. Root cause bukan di logic exclusion radio (itu tetap sound, karena sudah keyed di `video_id` langsung, bukan pasangan `(artist_id, video_id)`), murni di schema. Fix: ganti constraint jadi composite `UNIQUE(artist_id, youtube_id)` di `persistence/schema.sql` (skema baru) + migrasi rebuild tabel untuk DB lama yang sudah ada di `persistence/__init__.py` (`_migrate_songs_unique_constraint`), plus scope ulang duplicate-check & duration-backfill di `data/export_to_sqlite.py` ke pasangan `(artist_id, youtube_id)`.

**File Terdampak:**

- `persistence/schema.sql`
- `persistence/__init__.py`
- `data/export_to_sqlite.py`
- `tests/unit/persistence/test_db.py`
- `tests/unit/data/test_export_to_sqlite.py`

---

## [2026-07-16] Race Condition — Pinned TCP Port MPV Diabaikan di Windows

**ID:** `PATCH-2026-07-16-062`

**Tanggal:** 2026-07-16

**Ringkasan:** Baseline test suite menemukan 1 test gagal (`test_mpv_connection_connect_windows`), dikonfirmasi lewat skrip reproduksi: di `adapters/mpv/connection.py`, `_do_connect()` pada path Windows (`os.name == "nt"`) *selalu* menimpa `self.tcp_port` dengan port dinamis hasil bind ke port 0 — bahkan ketika caller (constructor arg atau env var `YT_PLAYER_MPV_PORT`) sudah men-pin port tertentu. Ini merusak deployment yang butuh port tetap (mis. firewall rule spesifik). Root cause: tidak ada pembeda antara "port default fallback" vs "port yang sengaja dipin". Fix: tambah flag `_port_pinned` (True jika `tcp_port` di-pass eksplisit ke constructor ATAU dari env var), auto dynamic-port selection hanya jalan kalau `_port_pinned` False. Sekalian perbaiki pesan error `MpvConnectionError` yang sebelumnya selalu nampilin `os.environ.get('YT_PLAYER_MPV_PORT', 'N/A')` mentah (misleading — tidak reflect port dinamis aktual yang dipakai saat gagal connect), sekarang pakai `self.tcp_port` yang sebenarnya.

**File Terdampak:**

- `adapters/mpv/connection.py`
- `tests/unit/adapters/mpv/test_connection.py`

---

## [2026-07-16] Race Condition — Pinned TCP Port MPV Diabaikan di Windows

**ID:** `PATCH-2026-07-15-061`

**Tanggal:** 2026-07-15

**Ringkasan:** Audit manual (bukan dari automation/, karena `event_graph.py` cs. hanya cek pub/sub event & arsitektur, bukan kelengkapan WS-action↔frontend-wiring) menemukan 5 fitur backend yang "orphan" (tidak reachable dari client) dan 1 dead code, ditemukan bertahap saat implementasi berjalan. - **BUG-1 (Kritis, fitur baru sprint 3.3 tidak pernah tersambung):** Loudness Normalization — pipeline lengkap (`LoudnessService`, `gain_calculator.py`, `CMD_SET_LOUDNESS_NORMALIZATION` di `command_router.py`) sudah ada sejak sprint 3.3, tapi action `set_loudness_normalization` tidak pernah didaftarkan di `PLAYBACK_CMDS`/`handle_playback_command`, dan tidak ada UI toggle sama sekali. Fix: tambah action ke WS routing + toggle di Settings sheet (pola sama seperti Crossfade), termasuk sync `data-on` di `renderSettingsSheet()`. - **BUG-2 (Kritis):** `queue_select` (`CMD_QUEUE_SELECT`) sudah full-implemented & full-tested di backend, tapi `queue-events.js` cuma daftarin click listener untuk `.qi-remove` — klik baris lagu di antrean manual tidak melakukan apapun. Fix: tambah click delegation di `queueList` yang kirim `queue_select` saat item (bukan drag handle/tombol hapus) diklik. - **BUG-3 (Dead code + fitur mati sejak awal):** Drag-to-reorder queue (`_onDragStart` di `queue-events.js`) butuh elemen `.qi-drag` (CSS-nya sudah ada di `queue.css`), tapi `createQueueItemTemplate()` di `render/queue.js` tidak pernah membuat elemen itu — drag-reorder gak pernah bisa dipakai dari awal. Fix: tambah `<span class="qi-drag">` ke template, disembunyikan untuk current-track item (sama seperti tombol hapus). - **BUG-4 (Dead code, query DB sia-sia):** `ws_discovery.py` action `discover` mengambil `ds.get_favorites(15)` tapi hasilnya dibuang — tidak dimasukkan ke payload `discover_data`. Kolom `is_favorite` + `toggle_favorite()` di `persistence/track_repo.py` sudah ada tapi datanya tidak pernah sampai ke client. Fix: masukkan `favorites` ke payload (di `ws_discovery.py` dan `ws_download.py` — dua tempat yang broadcast `discover_data`), tambah section "Favorit" di tab Discover (pola sama seperti "Tersimpan Lokal"). - **Catatan lanjutan (belum dikerjakan, butuh keputusan desain terpisah):** `toggle_favorite()` di persistence masih belum ada command/WS action untuk memicunya (belum ada tombol "like"/heart di UI). Favorit saat ini hanya bisa terisi lewat kolom `play_count`/`is_favorite` yang di-set manual di DB. Fitur "like" penuh (heart button, `CMD_TOGGLE_FAVORITE`) sengaja tidak dibuat di patch ini karena itu fitur baru, bukan bug fix. - **BUG-5 (Dead code sejak awal, ditemukan sampingan):** `dom.discRecent` di `dom.js` menunjuk ke `#discover-recent` yang tidak pernah ada di `index.html` — section "Baru Diputar" di tab Discover selalu `null`/dead. Fix: tambah container `#discover-recent` di `index.html`. - **DITEMUKAN TAPI BELUM DIPERBAIKI (di luar scope patch ini, butuh konfirmasi):** `pytest` penuh menemukan 2 test gagal yang **tidak berkaitan** dengan perubahan patch ini — `test_app_state_defaults` (`core/state.py`: default `sponsorblock_active` seharusnya `True` tapi aktual `False`) dan `test_sponsorblock_on_progress_seeks_past_segment` (`plugins/sponsorblock.py`: seek tidak terpanggil saat posisi masuk segmen). Kedua file tidak disentuh oleh patch ini — kemungkinan regresi lama yang belum ketahuan. Perlu sesi audit terpisah. **Verifikasi:** `ruff check` bersih, `mypy` bersih (4 file tersentuh), `pytest` 456 passed/2 failed-pre-existing/4 skipped, `vitest run` 14/14 passed, `automation/doctor.py` skornya identik dengan sebelum patch (tidak ada regresi arsitektur/dokumentasi/keamanan baru).

**File Terdampak:**

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

---

## [2026-07-15] Test Coverage — Sesi Audit Bug Fix

**ID:** `PATCH-2026-07-15-060`

**Tanggal:** 2026-07-15

**Ringkasan:** Penambahan test yang hilang pasca-implementasi PATCH-058 dan PATCH-059. - `test_websocket.py`: Tambah `test_new_playback_actions_are_routed` (parametrize 5 action: stop, set_sleep_timer, set_speed, set_loop, set_crossfade), `test_cache_commands_are_routed`, `test_unknown_action_does_not_crash`. - `test_serializers.py`: Tambah assert untuk 3 field baru di `state_to_dict` (playback_speed, loop_mode, crossfade_enabled) termasuk verifikasi nilai non-default.

**File Terdampak:**

- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/test_serializers.py`

---

## [2026-07-15] Test Coverage — Sesi Audit Bug Fix

**ID:** `PATCH-2026-07-15-059`

**Tanggal:** 2026-07-15

**Ringkasan:** Audit runtime menemukan 3 bug lanjutan setelah PATCH-058. - **BUG-A (Kritis):** `server/serializers.py` tidak menyertakan `playback_speed`, `loop_mode`, `crossfade_enabled` di payload state WS. Akibatnya toggle crossfade tidak bisa di-sync dari server, speed tidak persist setelah reconnect, loop mode button tidak reflect state server. Fix: tambahkan 3 field ke `state_to_dict()`. - **BUG-B (Kritis):** Kecepatan pemutaran hanya dikirim ke MPV (hanya berlaku untuk output Device). Browser audio (`<audio>`) tidak punya hook ke MPV property. Fix: tambahkan `audio.playbackRate = speed` di `settings-events.js` dan `full-state.js`. - **IMPROVE-C:** Sleep timer tidak punya feedback visual — subtitle hanya menampilkan "15 Menit" statis. Fix: tambahkan countdown timer client-side yang mundur detik per detik dan reset ke "Mati" saat habis.

**File Terdampak:**

- `server/serializers.py`
- `web/static/js/render/full-state.js`
- `web/static/js/events/settings-events.js`

---

## [2026-07-15] Audit Pasca-Implementasi T1–T16 — 4 Bug Kritis & 2 Bug Minor

**ID:** `PATCH-2026-07-15-058`

**Tanggal:** 2026-07-15

**Ringkasan:** Audit pasca-implementasi T1–T16 menemukan 4 bug kritis dan 2 bug minor yang menyebabkan beberapa fitur baru tidak berfungsi dari frontend. - **BUG-1 (Kritis):** `PLAYBACK_CMDS` di `server/handlers/websocket.py` tidak mencakup 5 action baru (`stop`, `set_sleep_timer`, `set_speed`, `set_loop`, `set_crossfade`). WebSocket menerima pesan tapi diam-diam mengabaikannya. Fix: tambahkan 5 action ke set. - **BUG-2 (Kritis):** `store.js` tidak punya field `crossfade_enabled`. Fix: tambahkan `crossfade_enabled: false` ke `createStore()`. - **BUG-3 (Kritis):** `transport-events.js` membaca `store.loopMode` (camelCase) padahal store memakai `store.loop_mode` (snake_case). Tombol Repeat selalu cycle ke "track". Fix: rename ke `loop_mode`. - **BUG-4 (Kritis):** `queue_manager.py` punya dead code `pass` di blok `loop_mode == "queue"` saat queue kosong. Fix: hapus blok if/pass yang tidak berguna. - **MINOR-1:** `core/state.py` mendefinisikan `playback_speed` dan `loop_mode` dua kali di dataclass. Fix: hapus duplikat. - **MINOR-2:** `settings-events.js` mendaftarkan listener `sbToggle.click` dua kali, yang kedua mengirim action `toggle_sponsorblock` yang tidak ada handler-nya. Fix: hapus listener duplikat.

**File Terdampak:**

- `server/handlers/websocket.py`
- `web/static/js/store.js`
- `web/static/js/events/transport-events.js`
- `engine/queue_manager.py`
- `core/state.py`
- `web/static/js/events/settings-events.js`

---

## [2026-07-15] T16: Implementasi Crossfade Eksperimental

**ID:** `PATCH-2026-07-15-057`

**Tanggal:** 2026-07-15

**Ringkasan:** T16: Implementasi efek crossfade eksperimental. Menambah `crossfade_enabled` di state, command `CMD_SET_CROSSFADE`, pengaturan UI di Settings, fade-out manual 2 detik di `controller.py`, fade-in di `controller.py` saat putar track baru untuk DEVICE output, dan JS client-side volume fade untuk BROWSER output. Refactoring crossfade dilakukan dengan memisahkan logika ke `crossfade.py` untuk menjaga ukuran file `controller.py` di bawah batas.

**File Terdampak:**

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

---

## [2026-07-15] Queue Duration UI (Tier 2 - T15)

**ID:** `PATCH-2026-07-15-056`

**Tanggal:** 2026-07-15

**Ringkasan:** T15: Penambahan informasi jumlah lagu dan total durasi estimasi secara real-time pada footer panel "Antrean Putar".

**File Terdampak:**

- `web/static/js/render/queue.js`

---

## [2026-07-15] Retry Stream Indicator (Tier 2 - T14)

**ID:** `PATCH-2026-07-15-055`

**Tanggal:** 2026-07-15

**Ringkasan:** T14: Menambahkan log publish (berupa `LogMessageEvent`) yang diekspos ke UI apabila endpoint `/stream/<video_id>` menerima respons 403 atau 410 dari upstream.

**File Terdampak:**

- `server/handlers/http.py`

---

## [2026-07-15] Loop Mode (Tier 2 - T13)

**ID:** `PATCH-2026-07-15-054`

**Tanggal:** 2026-07-15

**Ringkasan:** T13: Menambahkan fitur Loop Mode (off/track/queue). Menambah flag di AppState, logic `next()` pada `queue_manager.py`, command WS baru, serta toggle UI button yang disinkronisasi dengan state.

**File Terdampak:**

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

---

## [2026-07-15] Recent Search History (Tier 2 - T12)

**ID:** `PATCH-2026-07-15-053`

**Tanggal:** 2026-07-15

**Ringkasan:** T12: Riwayat pencarian terkini menggunakan safeStorage di sisi client beserta dukungan penghapusan manual. Juga memperbaiki fitur penghapusan item individual di daftar antrean.

**File Terdampak:**

- `web/static/js/events/search-input-events.js`
- `web/static/js/render/queue.js`
- `web/static/js/events/queue-events.js`
- `server/handlers/ws_playback.py`

---

## [2026-07-15] Playback Speed Control (Tier 2 - T11)

**ID:** `PATCH-2026-07-15-052`

**Tanggal:** 2026-07-15

**Ringkasan:** T11: Fitur kontrol kecepatan pemutaran. Menambahkan dropdown kecepatan di Setting, menghubungkannya melalui event WebSocket, serta pengaturan real-time menggunakan `mpv.set_property("speed", value)`.

**File Terdampak:**

- `core/state.py`
- `core/commands.py`
- `engine/playback/mode_ops.py`
- `server/handlers/ws_playback.py`
- `web/static/js/store.js`
- `web/static/js/render/player.js`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`

---

## [2026-07-15] Sleep Timer (Tier 2 - T10)

**ID:** `PATCH-2026-07-15-051`

**Tanggal:** 2026-07-15

**Ringkasan:** T10: Implementasi mode Sleep Timer. Mengatur waktu tidur dengan opsi countdown, mengintegrasikannya dengan command bus agar memicu auto-stop playback setelah waktu terlampaui, dan menambah test.

**File Terdampak:**

- `core/commands.py`
- `engine/sleep_timer.py`
- `engine/command_router.py`
- `server/handlers/ws_playback.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `web/static/js/render/player.js`
- `tests/unit/engine/test_sleep_timer.py`

---

## [2026-07-15] Cache Size Indicator & Clear (Tier 2 - T9)

**ID:** `PATCH-2026-07-15-050`

**Tanggal:** 2026-07-15

**Ringkasan:** T9: Penambahan handler `ws_cache.py` untuk mengukur direktori cache MP3 (`config.CACHE_DIR`) dan menghapusnya tanpa menyentuh file statis atau unduhan manual, disertai unit test. Di UI ditambahkan tampilan ukuran disk pada tab Settings.

**File Terdampak:**

- `server/handlers/ws_cache.py`
- `web/static/index.html`
- `web/static/js/events/settings-events.js`
- `tests/unit/server/handlers/test_ws_cache.py`

---

## [2026-07-15] Playback Resume Functionality (Tier 2 - T8)

**ID:** `PATCH-2026-07-15-049`

**Tanggal:** 2026-07-15

**Ringkasan:** Implementasi Task T8: Resume posisi playback setelah restart server. Modifikasi meliputi penambahan kolom `last_position` di tabel `tracks`, method di repositori untuk write/read posisi, `_on_track_progress` di controller untuk menyimpan secara periodik (setiap 10 detik), dan script `main.py` untuk load last state saat startup. Unit test untuk start_paused pada controller telah ditambahkan. Panjang file `controller.py` telah dikompres kembali sehingga lolos pengecekan `<400 baris` doctor.

**File Terdampak:**

- `core/state.py`
- `persistence/schema.sql`
- `persistence/track_repo.py`
- `persistence/__init__.py`
- `engine/playback/controller.py`
- `tests/unit/engine/playback/test_controller.py`
- `main.py`

---

## [2026-07-15] Fixes and Optimizations Tier 1

**ID:** `PATCH-2026-07-15-048`

**Tanggal:** 2026-07-15

**Ringkasan:** Implementasi Task T1-T7 Tier 1: Perbaikan bug data integrity hash fallback, precompile regex di searcher, lrc parser, HTTP handler, optimasi regex noise-keyword lirik, dan penggantian list ke deque pada rate limiter. Menambahkan unique index pada `artists.nama` di schema DB.

**File Terdampak:**

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

---

## [2026-07-15] CI Hang Diagnosis & Documentation Update

**ID:** `PATCH-2026-07-15-047`

**Tanggal:** 2026-07-15

**Ringkasan:** Mendiagnosa dan menemukan akar masalah "hang 1 jam 54 menit" pada CI pytest. Hang terbukti disebabkan oleh *zombie process* `yt-dlp` pada integration test (`test_download_flow.py`) yang gagal *timeout* akibat pemblokiran IP oleh YouTube di server GitHub Actions, dan tidak di-kill saat *teardown*. Memperbarui panduan integration testing dengan instruksi untuk memastikan `yt-dlp` dibunuh secara eksplisit di *teardown*. Seluruh 435 unit tests (P0-P4) terbukti *green* dan tidak bermasalah.

**File Terdampak:**

- `docs/testing/integration_testing.md`
- `log.md` (Catatan Mentah / Laporan Investigasi)

---

## [2026-07-15] Test Coverage P3 & P4 - WS & Radio Engine

**ID:** `PATCH-2026-07-15-046`

**Tanggal:** 2026-07-15

**Ringkasan:** Menambahkan unit test untuk error handling dan WS routing di `server/handlers/websocket.py` & `ws_playback.py` (P3) serta fallback prefetch dan radio_next di `engine/radio/engine.py` & `prefetcher.py` (P4) sesuai dengan `PATCH_TEST_COVERAGE.md`.

**File Terdampak:**

- `tests/unit/server/handlers/test_websocket.py`
- `tests/unit/server/handlers/test_ws_playback.py`
- `tests/unit/engine/radio/test_engine.py`
- `tests/unit/engine/radio/test_prefetcher.py`
- `tests/unit/engine/radio/test_artist_selector.py`

---

## [2026-07-15] Test Coverage P2 - observer.py

**ID:** `PATCH-2026-07-15-045`

**Tanggal:** 2026-07-15

**Ringkasan:** Menambahkan unit test untuk loop event async di `adapters/mpv/observer.py` sesuai dengan P2 di `PATCH_TEST_COVERAGE.md` (unknown property change, cleanup path, socket reconnect loop). Coverage keseluruhan naik dari 77.48% menjadi 78.43%.

**File Terdampak:**

- `tests/unit/adapters/mpv/test_observer.py`

---

## [2026-07-15] Test Coverage P1 - controller.py

**ID:** `PATCH-2026-07-15-044`

**Tanggal:** 2026-07-15

**Ringkasan:** Menambahkan unit test untuk state machine di `engine/playback/controller.py` sesuai dengan P1 di `PATCH_TEST_COVERAGE.md` (race condition, error state, empty queue, rollback). Coverage keseluruhan naik dari 77.10% menjadi 77.48%.

**File Terdampak:**

- `tests/unit/engine/playback/test_controller.py`

---

## [2026-07-15] Test Coverage P0 - serve_stream

**ID:** `PATCH-2026-07-15-043`

**Tanggal:** 2026-07-15

**Ringkasan:** Menambahkan unit test untuk fungsi `serve_stream()` di `server/handlers/http.py` sesuai dengan P0 di `PATCH_TEST_COVERAGE.md`. Coverage keseluruhan naik dari 75.10% menjadi 77.10%.

**File Terdampak:**

- `tests/unit/server/handlers/test_http.py`

---

## [2026-07-15] Quality of Life (QoL) Enhancements: Bandit, Loudness, Adaptive Prefetch

**ID:** `PATCH-2026-07-15-042`

**Tanggal:** 2026-07-15

**Ringkasan:** Eksekusi integrasi 3 fitur besar secara serentak untuk mematuhi larangan two-stage refactoring: 1. Thompson Sampling Bandit untuk Artist Radio. 2. EBU R128 Loudness Normalization. 3. Adaptive Network Prefetch (Latency Window). Fitur dipisah ke service/kelas baru dan controller dimodifikasi untuk injeksi ketergantungan.

**File Terdampak:**

- `persistence/schema.sql` & `__init__.py`
- `core/state.py`, `core/commands.py`, `core/ports.py`
- `persistence/artist_repo.py`, `persistence/track_repo.py`, `persistence/library_repo.py`
- `core/latency_window.py`
- `config.py` & `core/observability.py`
- `cache/resolver.py`
- `engine/radio/prefetcher.py`, `engine/radio/artist_bandit.py`, `engine/radio/artist_selector.py`
- `engine/loudness/gain_calculator.py`, `engine/loudness/analyzer.py`, `engine/loudness/service.py`
- `engine/playback/track_loader.py`, `engine/playback/mode_ops.py`, `engine/playback/controller.py`
- `adapters/mpv/__init__.py`
- `engine/command_router.py`
- `server/serializers.py`
- `main.py`

---

## [2026-07-14] Stable Release Hardening & Bug Fixes

**ID:** `PATCH-2026-07-14-041`

**Tanggal:** 2026-07-14

**Ringkasan:** Eksekusi P0-P2 dari IMPLEMENTATION_PLAN.md untuk persiapan Stable Release v1.0.0. Termasuk perbaikan banner password, path downloads, DB migration logging, `shell=False` di network probing, pemblokiran CI gate, metadata `pyproject.toml`, update package metadata, dan setup wheel build di CI.

**File Terdampak:**

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

---

## [2026-07-14] Baseline Stable v1.0.0 Release

**ID:** `PATCH-2026-07-14-040`

**Tanggal:** 2026-07-14

**Ringkasan:** Finalisasi "stable baseline version" v1.0.0. Mengubah status item tertunda menjadi ❄️ Frozen (v1.0.0 Baseline) di `STATUS.md`, menambahkan `CHANGELOG.md`, `CONTRIBUTING.md`, dan `SECURITY.md` (Open Source Readiness), dan melakukan tag v1.0.0 pada repositori.

**File Terdampak:**

- `docs/STATUS.md`
- `CHANGELOG.md` [NEW]
- `CONTRIBUTING.md` [NEW]
- `SECURITY.md` [NEW]

---

## [2026-07-14] Standardize Docstrings Format

**ID:** `PATCH-2026-07-14-039`

**Tanggal:** 2026-07-14

**Ringkasan:** Menyeragamkan format docstring pada 145 file menggunakan analisis AST dinamis untuk memastikan kelengkapan field sesuai standar.

**File Terdampak:**

- All python files (145 files across the codebase)

---

## [2026-07-14] automation - all tests and linters passing

**ID:** `PATCH-2026-07-14-038`

**Tanggal:** 2026-07-14

**Ringkasan:** automation - all tests and linters passing

**File Terdampak:**

- `docs/PATCHLOG.md`

---

## [2026-07-13] Skenario Integration Test & Generator Script Fix

**ID:** `PATCH-2026-07-13-037`

**Tanggal:** 2026-07-13

**Ringkasan:** Membangun `tests/integration/conftest.py` dengan komponen asli (EventBus, DB, yt-dlp) untuk integration testing. Menambahkan 4 end-to-end flow test (IT-01 sampai IT-04) untuk memastikan fungsionalitas WebSocket, Playback, Radio, dan Download berjalan dengan baik. Selain itu, generator script `generate_file_index.py` direfactor supaya dapat mendeteksi file dan folder secara dinamis tanpa hardcode. Crash encoding cp1252 pada output di terminal Windows juga telah diatasi.

**File Terdampak:**

- `tests/integration/__init__.py`
- `tests/integration/conftest.py`
- `tests/integration/test_websocket_flow.py`
- `tests/integration/test_playback_flow.py`
- `tests/integration/test_radio_flow.py`
- `tests/integration/test_download_flow.py`
- `scripts/generate_file_index.py`
- `scripts/generate_report.py`
- `scripts/run_all.py`

---

## [2026-07-13] Patch — Reorganisasi Dokumentasi (docs/kompas/ → docs/)

**ID:** `PATCH-2026-07-13-036`

**Tanggal:** 2026-07-13

**Ringkasan:** Memindahkan seluruh file dan folder implementasi arsitektur dari `docs/kompas/` ke root dokumentasi `docs/`. Menghapus folder `docs/kompas/` yang sudah kosong dan memperbarui referensi di seluruh proyek (`AI_CONTEXT.md`, `.py` scripts, `.md` docs). Dokumentasi ini kini menjadi referensi utama karena migrasi telah dinyatakan terealisasi 100%.

**File Terdampak:**

- `docs/kompas/*` ➔ `docs/*` [MOVED]
- `docs/Blueprint.md`, `docs/architecture/`, `docs/adr/`, `docs/backend/`, `docs/frontend/`, `docs/testing/`, `docs/devops/`, `docs/development/`, `docs/security/`, `docs/opensource/` [NEW PATHS]
- `AI_CONTEXT.md` [MODIFIED]
- `CONTRIBUTING.md` [MODIFIED]
- `docs/MIGRATION_GUIDE.md` [MODIFIED]
- `docs/PATCHLOG.md` [MODIFIED]
- `docs/STATUS.md` [MODIFIED]
- `docs/FILE_INDEX.md` [MODIFIED]
- `scripts/architecture_lint.py` [MODIFIED]
- `scripts/find_owner.py` [MODIFIED]
- `scripts/verify_structure.py` [MODIFIED]
- `tests/conftest.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 13: Evaluasi Arsitektur & Open Source Readiness

**ID:** `PATCH-2026-07-13-035`

**Tanggal:** 2026-07-13

**Ringkasan:** Menyelesaikan checklist Tahap 13. Melakukan evaluasi arsitektur berdasarkan `docs/blueprint.md` menggunakan `import-linter`. Hasilnya: 0 pelanggaran (semua dependency contract terpenuhi). Selain itu, semua file standar open source readiness telah ditambahkan.

**File Terdampak:**

- `.importlinter` [MODIFIED] — menambahkan `include_external_packages = True` dan multiline root_packages
- `requirements-dev.txt` [MODIFIED] — ditambahkan secara otomatis pada environment lokal
- `LICENSE` [NEW] — MIT License
- `CHANGELOG.md` [NEW] — Changelog file
- `CONTRIBUTING.md` [NEW] — Panduan kontribusi
- `SECURITY.md` [NEW] — Kebijakan keamanan
- `.editorconfig` [NEW] — Editor config
- `.github/PULL_REQUEST_TEMPLATE.md` [NEW]
- `.github/ISSUE_TEMPLATE/bug_report.md` [NEW]
- `.github/ISSUE_TEMPLATE/feature_request.md` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 12b: Prioritas Test per Layer (Adapter/Plugin/Server)

**ID:** `PATCH-2026-07-13-034`

**Tanggal:** 2026-07-13

**Ringkasan:** Melengkapi unit tests Prioritas 2 (Adapter/Plugin/Server logic) menggunakan mocks dan fakes. Menambahkan `services/__init__.py` yang hilang agar test coverage penuh dapat dieksekusi. Total test suite kini berjumlah 295 test case yang lulus penuh.

**File Terdampak:**

- `tests/unit/launcher/gui/test_dep_checker.py` [NEW]
- `tests/unit/server/test_connection_manager.py` [NEW]
- `tests/unit/server/test_middleware.py` [NEW]
- `tests/unit/server/test_serializers.py` [NEW]
- `tests/unit/engine/radio/test_artist_selector.py` [NEW]
- `tests/unit/engine/radio/test_prefetcher.py` [NEW]
- `tests/unit/engine/radio/test_engine.py` [NEW]
- `tests/unit/plugins/test_lyrics_parser.py` [NEW]
- `tests/unit/plugins/test_lyrics_sync.py` [NEW]
- `services/__init__.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 12b: Prioritas Test per Layer (Pure Logic)

**ID:** `PATCH-2026-07-13-033`

**Tanggal:** 2026-07-13

**Ringkasan:** Melengkapi unit tests Prioritas 1 (Pure Logic / Zero I/O) yang sebelumnya masih *missing* pada fase 12b. Total 16 test cases ditambahkan dan seluruhnya lulus (`16 passed`).

**File Terdampak:**

- `tests/unit/persistence/test_library_repo.py` [NEW]
- `tests/unit/engine/radio/test_track_interleaver.py` [NEW]
- `tests/unit/engine/playback/test_queue_ops.py` [NEW]
- `tests/unit/engine/playback/test_mode_ops.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 12a: Setup Testing Infrastructure

**ID:** `PATCH-2026-07-13-032`

**Tanggal:** 2026-07-13

**Ringkasan:** Setup folder struktur testing, pembuatan *fakes* (LyricsProvider, SponsorBlockProvider), dan modifikasi *fixture* `memory_db` di `conftest.py` sesuai panduan MIGRATION_GUIDE Tahap 12a.

**File Terdampak:**

- `tests/unit/adapters/mpv/` [NEW DIR]
- `tests/unit/engine/radio/` [NEW DIR]
- `tests/unit/engine/playback/` [NEW DIR]
- `tests/unit/server/handlers/` [NEW DIR]
- `tests/unit/server/services/` [NEW DIR]
- `tests/unit/plugins/` [NEW DIR]
- `tests/unit/launcher/gui/` [NEW DIR]
- `tests/integration/` [NEW DIR]
- `tests/frontend/utils/` [NEW DIR]
- `tests/fakes/fake_lyrics_provider.py` [NEW]
- `tests/fakes/fake_sponsorblock_provider.py` [NEW]
- `tests/conftest.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 11: Config, Tooling, CI

**ID:** `PATCH-2026-07-13-031`

**Tanggal:** 2026-07-13

**Ringkasan:** Setup file konfigurasi DevOps/Tooling sesuai MIGRATION_GUIDE tahap 11.

**File Terdampak:**

- `pyproject.toml` [MODIFIED]
- `.importlinter` [NEW]
- `.pre-commit-config.yaml` [MODIFIED]
- `.github/workflows/ci.yml` [MODIFIED]
- `.github/workflows/release.yml` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 9: Ekstraksi Frontend & Fix Doctor

**ID:** `PATCH-2026-07-13-030`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith frontend (player-events, audio, utils, discover) sesuai tahap 9, dan membereskan peringatan `doctor.py`.

**File Terdampak:**

- `web/static/js/events/*` [NEW]
- `web/static/js/audio/*` [NEW]
- `web/static/js/utils/*` [NEW]
- `web/static/js/render/*` [NEW]
- `web/static/js/ws.js` [MODIFIED]
- `web/static/index.html` [MODIFIED]
- `scripts/verify_docs/checks_docs.py` [MODIFIED]
- `scripts/architecture_lint.py` [MODIFIED]
- `scripts/generate_file_index.py` [MODIFIED]
- `docs/CONSTRAINTS.md` [NEW]
- `docs/rfc/.keep` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 8: Pembersihan Sisa

**ID:** `PATCH-2026-07-13-029`

**Tanggal:** 2026-07-13

**Ringkasan:** Merapikan struktur folder sesuai dengan MIGRATION_GUIDE tahap 8.

**File Terdampak:**

- `data/export_to_sqlite.py` -> `scripts/export_to_sqlite.py` [MOVED]
- `cache/schema.sql` [DELETED]
- `plugins/lyrics.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 7: Extract server/ WebSocket + launcher/gui/

**ID:** `PATCH-2026-07-13-028`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith websocket handler dan launcher GUI menjadi komponen diskrit yang sesuai dengan prinsip Single Responsibility.

**File Terdampak:**

- `server/handlers/websocket.py` [MODIFIED]
- `server/connection_manager.py` [NEW]
- `server/handlers/ws_*.py` [NEW]
- `launcher/gui.py` [MODIFIED]
- `launcher/gui/app.py`, `ui_builder.py`, `popups.py`,  `auth_panel.py`, `dep_checker.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 6: Extract engine/playback/controller.py

**ID:** `PATCH-2026-07-13-027`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith controller.py dengan memisahkan mutasi antrean dan pengaturan mode.

**File Terdampak:**

- `engine/playback/queue_ops.py` [NEW]
- `engine/playback/mode_ops.py` [NEW]
- `engine/playback/controller.py` [MODIFIED]

---

## [2026-07-13] Patch — MIGRATION Tahap 5: Extract engine/radio/

**ID:** `PATCH-2026-07-13-026`

**Tanggal:** 2026-07-13

**Ringkasan:** Memecah monolith engine/radio_engine.py berukuran 440 baris menjadi modul terpisah untuk isolasi bug radio mode.

**File Terdampak:**

- `engine/radio_engine.py` (menjadi alias)
- `engine/radio/artist_selector.py` [NEW]
- `engine/radio/track_interleaver.py` [NEW]
- `engine/radio/prefetcher.py` [NEW]
- `engine/radio/engine.py` [NEW]
- `engine/radio/__init__.py` [NEW]

---

## [2026-07-13] Patch — MIGRATION Tahap 4: Extract adapters/ytdlp/

**ID:** `PATCH-2026-07-13-025`

**Tanggal:** 2026-07-13

**Ringkasan:** Extract logika integrasi yt-dlp dari `engine/ytdlp_client.py` menjadi modul-modul independen di `adapters/ytdlp/`. Implementasi ini juga menyertakan `ThreadPoolExecutor` yang dibagikan antar komponen dari `YtDlpClient` Facade.

**File Terdampak:**

- `adapters/ytdlp/common.py` [NEW] — `YDL_OPTS_INFO`
- `adapters/ytdlp/searcher.py` [NEW] — `YtDlpSearcher`
- `adapters/ytdlp/resolver.py` [NEW] — `YtDlpResolver`
- `adapters/ytdlp/downloader.py` [NEW] — `YtDlpDownloader`
- `adapters/ytdlp/__init__.py` [NEW] — `YtDlpClient` Facade
- `engine/ytdlp_client.py` — [MODIFIED] re-export alias untuk backward compatibility

---

## [2026-07-13] Patch — MIGRATION Tahap 3: Extract adapters/mpv/

**ID:** `PATCH-2026-07-13-024`

**Tanggal:** 2026-07-13

**Ringkasan:** Extract logika koneksi, IPC, dan event loop observasi dari `engine/mpv_controller.py` menjadi modul-modul independen di `adapters/mpv/`. Menambahkan pola Facade di `adapters/mpv/__init__.py`. `engine/mpv_controller.py` kini hanya berfungsi sebagai re-export alias untuk backward compatibility.

**File Terdampak:**

- `adapters/mpv/connection.py` [NEW] — `MpvConnection`
- `adapters/mpv/ipc.py` [NEW] — `MpvIPC`
- `adapters/mpv/observer.py` [NEW] — `MpvObserver`
- `adapters/mpv/__init__.py` [NEW] — `MpvController` Facade
- `engine/mpv_controller.py` — [MODIFIED] acts as alias

---

## [2026-07-13] Patch — MIGRATION Tahap 2: Extract persistence/

**ID:** `PATCH-2026-07-13-023`

**Tanggal:** 2026-07-13

**Ringkasan:** Extract god-class `cache/db.py` (388 baris) menjadi repository terpisah di layer `persistence/` (`track_repo`, `artist_repo`, `session_repo`, `genre_repo`, `library_repo`). Mengimplementasikan Facade pattern untuk `Database` di `persistence/__init__.py`. `cache/db.py` diubah menjadi alias re-export agar backward compatible.

**File Terdampak:**

- `persistence/db.py` [NEW] — SQLite connection logic
- `persistence/track_repo.py` [NEW] — Track metadata & url caching
- `persistence/session_repo.py` [NEW] — Web sessions
- `persistence/artist_repo.py` [NEW] — Artist data
- `persistence/genre_repo.py` [NEW] — Genre data
- `persistence/library_repo.py` [NEW] — Cross-domain/random queries
- `persistence/__init__.py` — [MODIFIED] Facade pattern
- `cache/db.py` — [MODIFIED] acts as alias
- `persistence/schema.sql` — [NEW] copy dari cache/
- `scripts/architecture_lint.py` — [MODIFIED] izinkan `cache` import `persistence`

---

## [2026-07-13] Patch — MIGRATION Tahap 1: Setup Pondasi

**ID:** `PATCH-2026-07-13-022`

**Tanggal:** 2026-07-13

**Ringkasan:** Setup struktur folder target migrasi (`adapters/`, `engine/radio/`, `persistence/`, `launcher/gui/`), extract constants `CMD_*` dari `core/command_bus.py` ke `core/commands.py`, dan memisahkan fungsi admin password generation dari `config.py` ke `config_security.py`.

**File Terdampak:**

- `adapters/__init__.py`, `adapters/mpv/__init__.py`, `adapters/ytdlp/__init__.py` [NEW]
- `engine/radio/__init__.py` [NEW]
- `persistence/__init__.py` [NEW]
- `launcher/__init__.py`, `launcher/gui/__init__.py` [NEW]
- `core/command_bus.py` — pindah CMD_* ke core.commands
- `core/commands.py` — [NEW] menampung CMD_*
- `config.py` — pakai fungsi generate_admin_password
- `config_security.py` — [NEW] fungsi generate_admin_password

---

## [2026-07-11] Patch — Batch 12: Startup Script Cleanup

**ID:** `PATCH-2026-07-11-021`

**Tanggal:** 2026-07-11

**Ringkasan:** Gabung 7× subprocess dep-check Python menjadi 1×; hapus `sleep`/`ping` artifisial di `start.sh` dan `start.bat`.

**File Terdampak:**

- `start.sh` — single-import dep check, hapus sleep 0.5 dan sleep 1
- `start.bat` — single-import dep check, hapus ping delays

---

## [2026-07-11] Patch — Batch 11: OTel Tracing Dead Weight (Opsi A)

**ID:** `PATCH-2026-07-11-020`

**Tanggal:** 2026-07-11

**Ringkasan:** Hapus OTel span dari `command_bus.py` (tidak ada exporter aktif, 100% sia-sia); hapus setup_tracing dan import OTel dari `observability.py`.

**File Terdampak:**

- `core/command_bus.py` — hapus tracer import dan span context manager
- `core/observability.py` — hapus OTel imports, setup_tracing, tracer

---

## [2026-07-11] Patch — Batch 10: Serializers Lirik (Variant A)

**ID:** `PATCH-2026-07-11-019`

**Tanggal:** 2026-07-11

**Ringkasan:** Tambah parameter `include_lyrics` di `state_to_dict()` dan `broadcast_state()`; default False untuk broadcast periodik, True untuk initial snapshot.

**File Terdampak:**

- `server/serializers.py` — tambah include_lyrics param
- `server/services/broadcast_service.py` — default include_lyrics=False

---

## [2026-07-11] Patch — Batch 9: websocket.py + controller.py (Restricted, gabungan)

**ID:** `PATCH-2026-07-11-018`

**Tanggal:** 2026-07-11

**Ringkasan:** `toggle_pause()` fire-and-forget; broadcast paralel ke semua WS client; parallelkan query Discover di action `discover` & `delete_download`.

**File Terdampak:**

- `server/handlers/websocket.py` — asyncio import, parallel broadcast, parallel discover queries, include_lyrics=True initial snapshot
- `engine/playback/controller.py` — safe_create_task mpv_toggle_pause

---

## [2026-07-11] Patch — Batch 8: DB Index

**ID:** `PATCH-2026-07-11-017`

**Tanggal:** 2026-07-11

**Ringkasan:** Tambah `idx_songs_artist_id` pada tabel `songs` untuk JOIN query di Discover/Radio.

**File Terdampak:**

- `cache/schema.sql` — tambah index idx_songs_artist_id

---

## [2026-07-11] Patch — Batch 7: Event Listeners

**ID:** `PATCH-2026-07-11-016`

**Tanggal:** 2026-07-11

**Ringkasan:** Hapus throttle redundant `_on_track_progress` (sudah ditangani di mpv_controller); parallelkan query Discover di `_on_download_complete`.

**File Terdampak:**

- `server/handlers/event_listeners.py` — hapus throttle, asyncio.gather discover queries

---

## [2026-07-11] Patch — Batch 6: Track Loader

**ID:** `PATCH-2026-07-11-015`

**Tanggal:** 2026-07-11

**Ringkasan:** `increment_play_count` dijadikan `safe_create_task` (fire-and-forget) agar tidak menunda playback.

**File Terdampak:**

- `engine/playback/track_loader.py` — increment_play_count non-blocking

---

## [2026-07-11] Patch — Batch 5: Lyrics Plugin

**ID:** `PATCH-2026-07-11-014`

**Tanggal:** 2026-07-11

**Ringkasan:** Throttle `LyricsUpdatedEvent` (min 0.5s antar broadcast); lazy import `syncedlyrics`.

**File Terdampak:**

- `plugins/lyrics.py` — throttle LyricsUpdatedEvent, lazy import syncedlyrics

---

## [2026-07-11] Patch — Batch 4: mpv Controller

**ID:** `PATCH-2026-07-11-013`

**Tanggal:** 2026-07-11

**Ringkasan:** Throttle publish `TrackProgressEvent` ke 1×/detik; parallelkan 3× `observe_property` saat connect.

**File Terdampak:**

- `engine/mpv_controller.py` — throttle TrackProgressEvent, parallel observe_property

---

## [2026-07-11] Patch — Batch 3: main.py Housekeeping

**ID:** `PATCH-2026-07-11-012`

**Tanggal:** 2026-07-11

**Ringkasan:** Parallelkan `db.init()` + `mpv.connect()` via `asyncio.gather`; naikkan interval poller (mpv reconnect 5→30s, connectivity 60→300s); tambah `db_maintenance()` task tiap 6 jam.

**File Terdampak:**

- `main.py` — parallel init, interval poller, db_maintenance task

---

## [2026-07-11] Patch — Batch 2: Auth Non-Blocking

**ID:** `PATCH-2026-07-11-011`

**Tanggal:** 2026-07-11

**Ringkasan:** `verify_password()` (PBKDF2 100k iter) dipindah ke `run_in_executor` agar tidak memblokir event loop seluruh client selama proses login.

**File Terdampak:**

- `server/handlers/auth.py` — tambah asyncio import, ganti verify_password ke run_in_executor

---

## [2026-07-11] Patch — Batch 1: yt-dlp Client

**ID:** `PATCH-2026-07-11-010`

**Tanggal:** 2026-07-11

**Ringkasan:** Lazy import `yt_dlp` di `_extract_sync` & `_download_sync`; tambah `socket_timeout` dan `extractor_retries` ke `_YDL_OPTS_INFO` untuk mencegah thread zombie saat jaringan buruk.

**File Terdampak:**

- `engine/ytdlp_client.py` — lazy import yt_dlp, socket_timeout=10, extractor_retries=1

---

## [2026-07-11] Patch — Refactor scripts/ → shared/ + verify_docs/

**ID:** `PATCH-2026-07-11-009`

**Tanggal:** 2026-07-11

**Ringkasan:** Pecah `verify_docs.py` (850 baris) menjadi package `verify_docs/`, ekstrak utilitas bersama ke package `shared/`. CLI semua script identik — tidak ada breaking change.

**File Terdampak:**

- `scripts/shared/` — [NEW package] `__init__.py`, `check_result.py`, `skip_dirs.py`, `generated_block.py`
- `scripts/verify_docs/` — [NEW package] `__init__.py`, `helpers.py`, `checks_docs.py`, `checks_coverage.py`, `checks_files.py`, `render.py`
- `scripts/verify_docs.py` — refactor jadi thin CLI (~60 baris)
- `scripts/verify_security.py` — hapus local `CheckResult`, pakai `shared.check_result`
- `scripts/verify_structure.py` — hapus local `CheckResult`, pakai `shared.check_result`; pakai `shared.skip_dirs`
- `scripts/architecture_lint.py` — pakai `shared.skip_dirs`; bungkus hasil sebagai `shared.CheckResult`
- `scripts/generate_report.py` — pakai `shared.skip_dirs`, `shared.generated_block`
- `scripts/generate_file_index.py` — pakai `shared.skip_dirs`, `shared.generated_block`
- `docs/STRUCTURE.md` — update deskripsi `scripts/`
- `docs/architecture/folder_structure.md` — update tree `scripts/`
- `AI_CONTEXT.md` — tambah seksi "Struktur internal scripts/"
- `docs/AI_CONTEXT.md` — idem
- `docs/FILE_INDEX.md` — regenerate (file baru masuk index)
- `docs/REPORT.md` — regenerate (statistik file .py bertambah)

---

## [2026-07-10] Patch — Pindah .pre-commit-config.yaml ke Root

**ID:** `PATCH-2026-07-10-008`

**Tanggal:** 2026-07-10

**Ringkasan:** `.pre-commit-config.yaml` dipindah dari `scripts/` ke root repo agar pre-commit bisa baca otomatis saat `git commit`.

**File Terdampak:**

- `.pre-commit-config.yaml` — [MOVED] dari `scripts/` ke root
- `docs/PATCHLOG.md` — koreksi entry sebelumnya
- `docs/devops/tooling.md` — update status dari ❌ ke ✅

---

## [2026-07-10] Patch — Fix Kontradiksi Dokumentasi & Scripts

**ID:** `PATCH-2026-07-10-007`

**Tanggal:** 2026-07-10

**Ringkasan:** Sinkronisasi 5 kontradiksi antara docs dan scripts yang dibuat di sesi sebelumnya.

**File Terdampak:**

- `docs/FILE_INDEX.md` — hapus warning "mungkin stale", tambah marker `BEGIN/END:GENERATED`, update frontmatter ke `generated: true`
- `docs/REPORT.md` — tambah marker `BEGIN/END:GENERATED` di section Statistik Project
- `docs/STRUCTURE.md` — update deskripsi `scripts/` dari isi lama (generate_icons, inject_svgs) ke isi aktual (6 dev tooling scripts)
- `docs/INDEX.md` — selaraskan instruksi "setelah selesai kerja" dengan AI_CONTEXT.md (langkah per-script + run_all), hapus warning "mungkin stale" yang kontradiktif
- `.pre-commit-config.yaml` — dipindah dari `scripts/` ke root repo (opsi A); install dengan `pip install pre-commit && pre-commit install`

---

## [2026-07-09] Patch — Offline CDN Fix

**ID:** `PATCH-2026-07-09-006`

**Tanggal:** 2026-07-09

**Ringkasan:** Self-host Tabler Icons & hapus Google Fonts CDN. UI kini berfungsi penuh tanpa internet.

**File Terdampak:**

- `web/static/index.html` — hapus 4 baris Google Fonts, ganti 1 baris Tabler CDN → lokal
- `web/static/css/tokens.css` — pastikan font fallback stack
- `web/static/css/vendor/tabler-icons.min.css` — [NEW] self-hosted
- `web/static/css/vendor/fonts/*` — [NEW] font files
- `web/static/sw.js` — bump CACHE_VERSION, tambah vendor ke PRECACHE_ASSETS

---

## [2026-07-09] Optimasi Storage Unduhan (Single-File)

**ID:** `PATCH-2026-07-09-005`

**Tanggal:** 2026-07-09

**Ringkasan:** Mengubah logika *download* agar memindahkan (*move*) file langsung ke folder `downloads/` tanpa menduplikatnya di `cache/mp3/`.

**File Terdampak:**

- `engine/download_manager.py`
- `server/handlers/websocket.py`

---

## [2026-07-09] Bugfix — Radio Cover Image Disappearing

**ID:** `PATCH-2026-07-09-004`

**Tanggal:** 2026-07-09

**Ringkasan:** Memperbaiki bug dimana cover image pada mode radio (dan antrean) menghilang atau menjadi broken image karena  class tidak dihapus saat elemen DOM di-_recycle_.

**File Terdampak:**

- `web/static/js/render/queue.js`

---

## [2026-07-09] Knowledge Base — Initial Documentation

**ID:** `PATCH-2026-07-09-003`

**Tanggal:** 2026-07-09

**Ringkasan:** Pembuatan awal dokumentasi knowledge base dari source code scan.

**File Terdampak:**

- `docs/INDEX.md` [NEW]
- `docs/STRUCTURE.md` [NEW]
- `docs/FILE_INDEX.md` [NEW]
- `docs/PATCHLOG.md` [NEW]
- `docs/REPORT.md` [NEW]

---

## [2026-07-09] Sprint 3.2 — Extract `start.py` → `launcher/`

**ID:** `PATCH-2026-07-09-002`

**Tanggal:** 2026-07-09

**Ringkasan:** Pecah monolith `start.py` menjadi package `launcher/` dengan separation of concerns.

**File Terdampak:**

- `start.py` (jadi hollow re-export)
- `launcher/` [NEW package — 6 file, lihat "File baru" di bawah]
- `launcher/__init__.py`, `launcher/__main__.py` — coordinator
- `launcher/gui.py` — `ServerManager` Tkinter UI
- `launcher/process.py` — `ServerProcess`, `kill_process_tree()`, `kill_mpv()`
- `launcher/network.py` — `check_port_in_use()`, `get_pid_occupying_port()`
- `launcher/updater.py` — stub OTA updater

---

## [2026-07-09] Sprint 2.1 — LunaWave Rebranding

**ID:** `PATCH-2026-07-09-001`

**Tanggal:** 2026-07-09

**Ringkasan:** Replace semua identitas legacy (YTGUI, ytgui, bagas.fm, YT Termux Player) dengan LunaWave. Zero regresi pada business logic.

**File Terdampak:**

- `config.py`
- `main.py`
- `core/observability.py`
- `web/static/js/utils.js`
- `web/static/manifest.json`
- `web/static/sw.js`
- `web/static/index.html`
- `scripts/generate_icons.py` [NEW]
- `config.py` — env vars primary → `LUNAWAVE_*`, fallback `YTGUI_*`
- `main.py` — log → `lunawave.log`, banner → LunaWave
- `core/observability.py` — metric → `lunawave_events_total`
- `web/static/js/utils.js` — auto-migrate `ytgui_*` → `lunawave_*` localStorage keys
- `web/static/manifest.json`, `sw.js`, `index.html` — PWA identity → LunaWave
- `scripts/generate_icons.py` — [NEW] icon generator PWA

---
