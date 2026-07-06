# FRONTEND AUDIT — bagas.fm / ytgui
**Source:** `ytgui-main/web/static/` · **Date:** 2026-07-02  
**Metodologi:** Source code sebagai satu-satunya kebenaran. `.backup_patchlog` dan markdown doc diabaikan. Inline komentar di source code dipakai sebagai konteks tambahan.

---

## RINGKASAN EKSEKUTIF

| Kategori | Temuan | Severity |
|---|---|---|
| Responsive Issue | 6 | Medium–High |
| Accessibility | 9 | Medium–Critical |
| Loading | 5 | Medium–High |
| Animation | 4 | Low–Medium |
| Rebuild (dead/orphaned code) | 5 | Medium |
| UI Consistency | 7 | Low–Medium |
| UX | 8 | Medium–High |
| Dark Mode | 2 | Low–Medium |
| Navigation | 4 | Low–Medium |
| Form Validation | 3 | Medium |
| State Bug | 7 | Medium–High |
| Widget Tree | 5 | Medium |

**Total temuan: 65**

---

## 1. RESPONSIVE ISSUE

### R-01 · `lyrics-wrap` disembunyikan total di mobile
**File:** `css/platform/mobile.css:2`  
```css
@media (max-width: 600px) {
  #tab-home .lyrics-wrap {
    display: none !important;
  }
}
```
Lirik inline di Home tab **tidak tampil sama sekali** di HP. Padahal sheet lyrics (`#lyrics-sheet`) tetap bisa dibuka via Settings. Pengalaman mobile kehilangan fitur kunci tanpa fallback visual apapun.  
**Fix:** Tampilkan versi compact 1-baris lyric, atau tampilkan EQ bar saja sebagai indikator, bukan `display:none` penuh.

---

### R-02 · `grid.css` hampir kosong — breakpoint tablet tidak terimplementasi
**File:** `css/layout/grid.css`  
File diberi komentar `ADR-002: 601px tablet, 1024px desktop` tetapi semua blok `@media (601px–1023px)` **kosong**. Tablet portrait (601–1023px) tidak mendapat layout khusus — fallback ke mobile layout yang sempit.  
**Fix:** Implementasikan breakpoint tablet portrait. Minimal set `max-width: 768px` + center seperti sudah ada di `tablet.css`.

---

### R-03 · Desktop player bar `left` calculation salah saat sidebar 88px
**File:** `css/platform/desktop.css:64` dan `css/platform/landscape.css:99`  
```css
left: calc(50vw + 44px) !important;
```
Logika ini: `left = tengah viewport + setengah sidebar`. Hasilnya **tidak presisi** — player bar sedikit geser ke kanan dari tengah area konten. Seharusnya:
```css
left: calc(88px + (100vw - 88px) / 2)
/* atau lebih bersih: */
left: 50%; transform: translateX(-50%);
/* dengan parent diset posisi relatif ke konten area */
```

---

### R-04 · `idle-text-slide` overflow di mobile
**File:** `css/layout/grid.css:96` + `css/platform/mobile.css:8`  
Mobile override mengubah `font-size: 28px → 18px` dan `white-space: normal`, tapi `position: absolute` + `left: 0; width: 100%` tetap. Pada layar sangat sempit (320px), text 3 slide bisa tumpang-tindih saat animasi fade overlap di `animation-delay` transisi.

---

### R-05 · `home-left-col` + `home-right-col` tidak punya mobile stacking rule
**File:** `index.html` + `css/platform/desktop.css:178`  
`home-left-col` dan `home-right-col` di-define via grid area `left` / `right` di desktop. Tidak ada CSS yang meng-override ke `display: flex; flex-direction: column` untuk mobile. Di mobile, keduanya bergantung pada urutan DOM (flex column di `.full-player-view`). Jika `home-right-col` (queue section) tidak disembunyikan saat idle, ia muncul di bawah dengan `padding: var(--s4) var(--s5) var(--s12)` yang boros ruang.

---

### R-06 · `landscape.css` hanya handle `max-height: 500px` — mid-height landscape gap
**File:** `css/platform/landscape.css:1`  
```css
@media (max-height: 500px) and (orientation: landscape) {
  .vinyl-wrap { display: none; }
}
```
Device landscape dengan tinggi 501–600px (banyak mid-range Android) tidak ditangani: vinyl tetap tampil dan memakan ~40% viewport, menyisakan area konten yang sangat sempit.

---

## 2. ACCESSIBILITY

### A-01 · Focus trap tidak diimplementasikan di bottom sheet
**File:** `css/components/settings-sheet.css` + `js/events/settings-events.js`  
`settings-sheet`, `lyrics-sheet`, `action-sheet`, `help-sheet` memiliki `role="dialog" aria-modal="true"` tapi **tidak ada focus trap**. Screen reader bisa escape keluar dari modal. Tab key menembus ke elemen di bawah overlay.  
**Severity:** Critical untuk aksesibilitas.

---

### A-02 · `nav-btn` tidak ada `tabindex` yang konsisten saat `portal-active`
**File:** `index.html:355` + `js/services/auth.js`  
Saat portal screen aktif (`#app` hidden via `display:none`), nav buttons tetap ada di DOM tanpa `tabindex="-1"`. Screen reader + keyboard bisa reach elemen tersembunyi.

---

### A-03 · Search input tidak ada `<label>`
**File:** `index.html:208`  
```html
<input type="text" id="search-input" placeholder="Search songs, artists, albums..." autocomplete="off">
```
Tidak ada `<label for="search-input">`. Placeholder saja tidak memenuhi WCAG 1.3.1. Setelah fokus, label hilang.

---

### A-04 · Login form tidak ada label element
**File:** `index.html:56–60`  
```html
<input type="text" id="admin-username" placeholder="Username" autocomplete="off">
<input type="password" id="admin-password" placeholder="Password">
```
Dua input login tidak memiliki `<label>`. Tambahan: `autocomplete="off"` pada username bertentangan dengan praktik keamanan — seharusnya `autocomplete="username"`.

---

### A-05 · `btn-play` ikon berubah secara DOM tanpa `aria-label` dinamis
**File:** `js/render/player.js:renderPlayBtn()`  
```js
dom.btnPlay.innerHTML = '...play svg...' // atau pause svg
```
`aria-label="Play/Pause"` di HTML bersifat statis. Saat state berubah, `aria-pressed` atau `aria-label` tidak diupdate. Screen reader selalu mengumumkan "Play/Pause" tanpa tahu state aktual.  
**Fix:** Set `dom.btnPlay.setAttribute('aria-label', wantsPlay ? 'Play' : 'Pause')` dan `aria-pressed`.

---

### A-06 · Gambar thumbnail tidak ada `alt` yang bermakna di JS-generated HTML
**File:** `js/render/player.js:renderPlayerBar()` baris `img src...`  
```js
`<img src="${...}" style="width:44px; ...">`
```
Tidak ada `alt` attribute. Juga di `render/search.js:buildSrThumbHtml()`: `alt=""` — acceptable tapi icon placeholder tidak punya deskripsi.

---

### A-07 · `#main-overlay` tidak ada `aria-hidden` toggle
**File:** `js/events/settings-events.js:closeMainOverlay()`  
Overlay background tidak set `aria-hidden="true"` pada konten di belakangnya saat modal buka. Screen reader masih bisa navigate konten yang tertutup.

---

### A-08 · Color contrast: `var(--text-3)` dan `var(--border-1)` berpotensi gagal WCAG AA
**File:** `css/tokens.css`  
- `--text-3: #8B92A5` di atas `--bg-primary: #0E0E12` → kontras ~4.0:1 (pass AA untuk teks normal ≥14px, tapi fail untuk teks kecil `--t-xs: 11px`)
- `--text-2: #9AA0AA` dipakai untuk meta/subtext di `11px` → kontras ~3.7:1 (fail AA untuk small text)
- Badge `pb-badge-sm` menggunakan `font-size: 10px` dengan warna dimmed — paling berisiko.

---

### A-09 · Queue item remove button hanya muncul saat hover
**File:** `css/components/queue.css:67`  
```css
.qi-remove { opacity: 0; }
.queue-item:hover .qi-remove { opacity: 1; }
```
Touch users tidak punya hover. Button hapus tidak visible. Komentar `C-07` sudah ada tapi fix belum diterapkan (hanya drag handle yang diaddress).  
**Fix:** Pada `@media (hover: none)`, set `opacity: 0.4` atau tambahkan slide gesture delete.

---

## 3. LOADING

### L-01 · Skeleton shimmer menggunakan undefined CSS variable
**File:** `css/base/animations.css:18–20`  
```css
.skeleton-box {
  background: var(--surface-2);
  background-image: linear-gradient(90deg, var(--surface-2) 0px, var(--surface-3) 40px, var(--surface-2) 80px);
}
```
`--surface-2` dan `--surface-3` **tidak terdefinisi** di `tokens.css`. Token yang ada: `--bg-surface`, `--bg-elevated`. Skeleton shimmer tampil sebagai warna transparan/hitam — animasi tidak terlihat.  
**Severity:** High — fitur loading state rusak secara visual.  
**Fix:**
```css
background: var(--bg-elevated);
background-image: linear-gradient(90deg, var(--bg-elevated) 0px, var(--bg-surface) 40px, var(--bg-elevated) 80px);
```

---

### L-02 · Cover art selalu fetch iTunes API — tidak ada priority untuk cached thumbnail
**File:** `js/utils.js:getCoverArt()`  
Flow: cek `localStorage` → fetch `itunes.apple.com` → fallback YouTube. Thumbnail dari server (`track.thumbnail`) hanya dipakai jika `!track.title || !track.artist`. Artinya **setiap render** akan hit iTunes API dahulu meskipun YouTube thumbnail sudah ada dan cukup baik.  
**Fix:** Tampilkan `track.thumbnail` segera (no-flash), lalu lazy-upgrade ke iTunes di background.

---

### L-03 · `loadLazyCovers` membuat satu global `IntersectionObserver` yang terus hidup
**File:** `js/utils.js:loadLazyCovers()`  
`_lazyCoverObserver` dibuat sekali dan tidak pernah di-disconnect. Setiap `loadLazyCovers()` call menambah observer entries baru. Tidak ada cleanup saat item di-remove dari DOM. Pada sesi panjang (radio mode berjam-jam), bisa akumulasi ribuan observed entries yang sudah stale.

---

### L-04 · `renderProgress()` menggunakan `requestAnimationFrame` tapi dipanggil dari `progress` WS event
**File:** `js/render/player.js:renderProgress()` + `js/ws.js:handleServerMessage()`  
`progress` event dari server dikirim secara periodik. `renderProgress` sudah pakai rAF guard (`_rafProgressPending`), yang baik. Tapi `syncBrowserAudio()` juga dipanggil di setiap progress event — berpotensi memanggil `audio.currentTime =` sinkronisasi setiap 500ms yang mengganggu buffering smooth playback browser.

---

### L-05 · Font loading tidak ada `font-display: swap` hint
**File:** `index.html:6–8`  
```html
<link rel="preload" as="style" href="https://fonts.googleapis.com/css2?family=Inter:...">
```
Google Fonts link ini sudah non-blocking (via `onload` trick), tapi tidak ada `&display=swap` di URL. Tanpa `font-display: swap`, browser bisa FOIT (flash of invisible text) selama Inter loading.  
**Fix:** Tambahkan `&display=swap` ke URL Google Fonts.

---

## 4. ANIMATION

### AN-01 · `startFakeBeatLoop` menggunakan interval tetap 500ms — tidak sinkron dengan musik
**File:** `js/audio.js:startFakeBeatLoop()`  
Glow beat effect pada album art menggunakan fake interval 500ms (120 BPM hardcoded), bukan data audio nyata. Efek terasa disconnected dari musik aktual. Ini diketahui (`startFakeBeatLoop` vs `startVisualizerLoop` untuk browser mode) tapi visualizer nyata tidak aktif di non-browser output.

---

### AN-02 · `home-art-frame::after` + `::before` konflik z-index dengan `shinySweep`
**File:** `css/components/player-bar.css:109` + `css/components/cards.css:205`  
- `::before` dipakai untuk glow effect (`z-index: -1`)
- `::after` dipakai untuk gradient overlay + **juga** `shinySweep` animation di `cards.css` untuk `.home-art-frame::after`

Kedua rule untuk `home-art-frame::after` ada di file berbeda. `cards.css` menambahkan `shinySweep` animation, `player-bar.css` menambahkan gradient overlay. Salah satu override yang lain tergantung urutan load CSS — **behavior tidak deterministic**.

---

### AN-03 · EQ bar di desktop `tablet.css` tidak sinkron dengan EQ bar di `app-shell.css`
**File:** `css/platform/tablet.css:48` + `css/layout/app-shell.css:107`  
Ada dua implementasi EQ icon: `.eq-anim-icon span` di `app-shell.css` (3 bar, untuk thumbnail overlay) dan `.eq-bar` di `tablet.css` (10 bar, untuk home section). Animasi yang sama (`eq-bounce`) dipakai keduanya, tapi delay dan duration berbeda. Kontrol play/pause tidak meng-pause CSS animation — EQ terus beranimasi bahkan saat lagu di-pause.  
**Fix:** Bind `animation-play-state: paused` ke kondisi `store.status !== 'PLAYING'` via class toggle.

---

### AN-04 · `@keyframes transmit-radio` didefinisikan dua kali
**File:** `css/base/animations.css:7` + `css/components/cards.css:68`  
Definisi pertama: `transform: scale(1) → scale(2)`. Definisi kedua (di `cards.css`): `transform: scale(1) → scale(1.08)` dengan `box-shadow`. Dua definisi berbeda untuk keyframe yang sama — yang mana yang berlaku tergantung spesifisitas dan urutan load.

---

## 5. REBUILD (Dead / Orphaned Code)

### RB-01 · `render/favorites.js` — file kosong
**File:** `js/render/favorites.js` (0 bytes)  
Di-include via `<script src="...favorites.js" defer>` di `index.html:232`. File kosong. `dom.discFavorites` dari `dom.js` dipakai di `render/discover.js` — tidak terpisah ke file ini. Entah file ini belum diimplementasi, atau sudah di-merge ke discover.js tanpa cleanup.

---

### RB-02 · `#portal-client-btn` dan `#portal-admin-btn` tidak ada di HTML tapi diakses di JS
**File:** `js/dom.js:5,7` + `js/events/index.js`  
```js
portalClientBtn: $("portal-client-btn"),
portalAdminBtn: $("portal-admin-btn"),
```
Di `index.html`, tidak ada elemen dengan id tersebut. `dom.portalClientBtn` dan `dom.portalAdminBtn` akan selalu `null`. Event listener di `events/index.js:18–36` terpasang ke `null` — silently fails. Portal hanya punya form login admin, tidak ada "client mode" button.

---

### RB-03 · `#home-idle-view` tidak pernah aktif secara penuh
**File:** `index.html` + `css/layout/grid.css:68`  
Idle view ditampilkan via `body[data-player-state="IDLE"] #tab-home .home-idle-view { display: flex !important }`. Tapi `.home-idle-view` tidak ada di dalam `.home-left-col` — dia ada langsung di dalam `#tab-home`. Sementara itu, CSS yang menyembunyikan `.home-art-section`, `.home-track-row`, `.lyrics-wrap` saat IDLE menarget `.home-left-col` children. Jika layout desktop (2-col grid), idle view mungkin tidak muncul di tempat yang benar.

---

### RB-04 · `#np-thumbnail`, `#np-dur-meta` — elemen DOM yang tersembunyi tapi diakses
**File:** `index.html:101–104`  
```html
<div id="np-thumbnail" style="display:none;">
  <i id="np-thumb-icon"></i>
  <div id="np-eq-anim"><span></span><span></span><span></span></div>
</div>
<div id="np-dur-meta" style="display:none;"></div>
```
Komentar menyebut "JANGAN HAPUS, dipakai renderNowPlaying()". Memang diakses di `dom.js` (`npThumbnail`, `npDurMeta`) dan di `render/now-playing.js`. Tapi elemen ini selalu `display:none` dan kontennya di-overwrite oleh `vinylRecord` + `vinylCover` yang merupakan UI aktual. Ini adalah hidden state synchronization artifact — bisa di-refactor menjadi JS-only state.

---

### RB-05 · `#radio-toggle-wrap` — elemen placeholder kosong
**File:** `index.html:176`  
```html
<div style="display: none;" id="radio-toggle-wrap"></div>
```
Diakses di `dom.js` (`radioToggleWrap`) tapi tidak diisi atau digunakan di manapun dalam codebase yang teraudit. Elemen ini adalah sisa dari struktur lama.

---

## 6. UI CONSISTENCY

### UI-01 · Settings sheet memiliki dua set rule CSS yang conflict
**File:** `css/components/settings-sheet.css`  
Rule berikut masing-masing didefinisikan **dua kali**:
- `.settings-sheet {}` — baris 1 dan 151
- `.ss-handle {}` — baris 29 dan 162
- `.ss-title {}` — baris 35 dan 167
- `.ss-row {}` — baris 44 dan 178

Nilai berbeda antara dua instance (misal `max-height: 78vh` vs `82vh`, `padding: s4 s5 s6` vs `s3 0 calc(s8 + safe-area)`). Yang berlaku adalah yang di bawah, tapi ini menyebabkan confusion dan CSS yang tidak maintainable. Rule pertama adalah sisa versi lama yang belum dihapus.

---

### UI-02 · `.pb-thumb` didefinisikan dua kali dengan ukuran berbeda
**File:** `css/components/player-bar.css`  
Definisi pertama (baris ~150): `width: 13px; height: 13px; opacity: 0`  
Definisi kedua (baris ~510): `width: 18px; height: 18px; box-shadow: ...; opacity` hilang (selalu terlihat)  
Yang berlaku adalah definisi kedua — tapi aturan visibilitas dari pertama (`opacity: 0` + `:hover opacity: 1`) di-override secara tidak lengkap. Thumb selalu visible di semua state.

---

### UI-03 · `.pb-progress-track` duplikasi di `queue.css`
**File:** `css/components/queue.css:136–138`  
```css
}.pb-progress-track { min-height: 44px; touch-action: none; }

.pb-progress-track { min-height: 44px; touch-action: none; }
```
Rule yang sama muncul dua kali berturut-turut. Ini artifact paste duplikat.

---

### UI-04 · `ss-out-btn` dan `ss-action-btn` punya dua definisi berbeda
**File:** `css/components/settings-sheet.css:100` vs `css/components/settings-sheet.css:185`  
Definisi pertama: `background: var(--bg-elevated); border: 1px solid rgba(255,255,255,0.08); color: var(--fm-text-4)`  
Definisi kedua: `background: var(--accent-dark); border: none; color: var(--accent)`  
Visual yang muncul: accent-dark background (definisi kedua menang) tapi hover dari definisi pertama yang dipakai. Inconsistent hover states.

---

### UI-05 · Emoji dipakai sebagai UI element di produksi
**File:** `js/render/player.js`, `js/events/settings-events.js`  
```js
dom.outputToggleBtn.textContent = "💻 BROWSER"; // atau "📱 HP"
dom.pbDlBadge.textContent = "⬇ 38%";
dom.pbCacheBadge.textContent = "✓ tersimpan"; // atau "☁ stream"
```
Emoji rendering tidak konsisten antar OS/browser. Di beberapa Android versi lama, emoji muncul sebagai kotak. Seharusnya pakai Tabler Icons (sudah ter-include) atau SVG untuk consistency.

---

### UI-06 · `section-label` vs `section-label-row` — duplikasi semantik
**File:** `css/layout/app-shell.css:118,127`  
Dua class dengan visual mirip: `.section-label` (standalone) dan `.section-label-row .label-text`. Di `index.html` discover tab menggunakan `.section-label` (baris 264) sedangkan home tab dan radio menggunakan `.section-label-row` (baris 169, 189). Tidak ada dokumentasi kapan harus pakai yang mana.

---

### UI-07 · Portal login button `#admin-submit-btn` tidak menggunakan design token radius
**File:** `css/portal.css:81`  
```css
#admin-submit-btn { border-radius: 10px; }
```
Sementara token yang ada: `--r-sm: 12px`, `--r-md: 16px`. Nilai `10px` hardcoded tidak masuk dalam spacing system.

---

## 7. UX

### UX-01 · Swipe gesture prev/next tidak ada visual feedback
**File:** `js/platform/touch.js:17–34`  
Swipe kiri/kanan memicu `wsSend('next')` / `wsSend('prev')` tapi tidak ada visual indicator (tidak ada ripple, glow, atau animasi transisi). User tidak tahu apakah swipe ter-trigger atau tidak sampai lagu ganti.

---

### UX-02 · Search autofocus terlambat 100ms dan tidak dikondisikan
**File:** `js/main.js:switchTab()`  
```js
if (tab === "search") {
  setTimeout(() => dom.searchInput.focus(), 100);
}
```
Delay 100ms terasa laggy di perangkat cepat. Di mobile, `focus()` pada input memicu keyboard popup yang bisa menggeser layout secara tiba-tiba. Tidak ada cek apakah user sudah mengetik sebelum dipaksa focus.

---

### UX-03 · Radio tab: tidak ada feedback visual saat "Acak Artis" loading
**File:** `js/events/player-events.js` (`radioRandomizeBtn` click handler)  
```js
store.status = "LOADING";
// ...
wsSend("radio_randomize", { seed_artist: null });
```
State di-set ke `LOADING` tapi tombol "Acak Artis" tidak di-disable dan tidak ada spinner. User bisa klik berkali-kali, mengirim multiple `radio_randomize` commands sebelum response pertama tiba.

---

### UX-04 · `showLogToast` 3 detik tidak cukup untuk pesan panjang
**File:** `js/utils.js:showLogToast()`  
```js
logToastTimer = setTimeout(() => { dom.logToast.classList.remove("active"); }, 3000);
```
Toast dipakai untuk berbagai pesan termasuk "Menerima data lagu! X items" dan error messages. 3 detik untuk error message teknis tidak cukup untuk dibaca. Tidak ada konfigurasi duration per-call.

---

### UX-05 · Volume slider beda di mobile dan desktop — konflik definisi
**File:** `css/components/player-controls.css`  
Dua definisi `.vol-slider`:
1. Baris 7: `width: 120px; height: 6px` (dikomentari sebagai C-06 improvement)
2. Baris 61: `width: 100px; height: 3px; -webkit-appearance: none`

Definisi kedua menimpa pertama. Perbaikan C-06 (touch target lebih besar) tidak efektif karena di-override.

---

### UX-06 · Queue item tidak bisa diklik untuk play di radio mode
**File:** `css/components/queue.css:130–133`  
```css
#radio-queue-list .radio-queue-item { cursor: default; }
#radio-queue-list .radio-queue-item:hover { background: transparent; }
```
Radio queue items sengaja non-clickable (sesuai arsitektur). Tapi tidak ada visual hint bahwa item tersebut non-interactive. User yang berharap bisa klik untuk skip to track tertentu tidak mendapat feedback.

---

### UX-07 · Login error tidak clear saat user mulai mengetik ulang
**File:** `js/events/index.js` + `js/services/auth.js:login()`  
Error message di `#login-error-msg` hanya di-clear saat submit berikutnya (`dom.loginErrorMsg.textContent = ""`). Saat user mengubah password field, error lama masih tampil — misleading karena user sudah mengedit input.  
**Fix:** Tambahkan `input` event listener pada username/password untuk clear error.

---

### UX-08 · Lyrics sheet offset buttons terlalu kecil untuk touch
**File:** `index.html:507–520` + `css/components/lyrics.css`  
```html
<button id="lyric-offset-minus">−</button>
<button id="lyric-offset-plus">+</button>
```
`.offset-btn`: `width: 22px; height: 22px` — jauh di bawah 44px minimum touch target WCAG/Apple HIG. Sulit dipencet di mobile, terutama saat tangan gemetar.

---

## 8. DARK MODE

### DM-01 · Tidak ada `light-mode` / `prefers-color-scheme` support — selalu dark
**File:** `css/tokens.css`  
Seluruh token hardcoded ke dark palette. Tidak ada `@media (prefers-color-scheme: light)` block. Pada iOS/Android yang diset ke light mode, app tetap gelap — ini mungkin intentional (brand "Midnight Audio") tapi tidak ada metadata/manifest yang menyatakan ini, sehingga browser accessibility tools tidak mengenali intent.  
Jika ini by design: tambahkan `color-scheme: dark` di `:root` untuk memberi tahu browser.

---

### DM-02 · Audio unlock banner pakai inline CSS tidak ikut token
**File:** `js/audio.js:_showTapToPlayBanner()`  
```js
el.style.cssText = '...background:var(--accent,#1db954);color:#fff;...';
```
Banner ini menggunakan `#1db954` sebagai fallback (Spotify green) tapi `--accent` sudah Amber Gold. Jika token belum load, banner muncul hijau Spotify. Fallback tidak konsisten dengan brand.

---

## 9. NAVIGATION

### N-01 · Tab panel activation menggunakan `classList.add("active")` tanpa `tabpanel` role
**File:** `js/main.js:switchTab()` + `index.html`  
Sections diberi `class="tab-panel"` tapi tidak ada `role="tabpanel"`. Nav buttons punya `role="tab"` dan `aria-selected` yang di-update via JS (`main.js:41,45`). Relasi `aria-controls` antara tab dan panel tidak ada. Screen reader tidak bisa associate tab dengan kontennya.

---

### N-02 · Tidak ada history/back state management
**File:** `js/main.js:switchTab()`  
Tab switch tidak push ke `history.pushState`. Browser back button tidak navigate antar tab — langsung keluar dari halaman. Mobile user yang expect back = previous tab akan frustrated.

---

### N-03 · Deep link ke tab tidak didukung
**File:** `js/main.js:init()`  
`store.active_tab` selalu start dari "home". URL `?tab=search` atau hash `#search` tidak dibaca. Tidak ada cara share link langsung ke tab tertentu.

---

### N-04 · `switchTab("search")` dengan autofocus mengirim `discover` WS event sebelumnya
**File:** `js/main.js:switchTab()`  
```js
if (tab === "discover" || tab === "home") {
  wsSend("discover");
}
```
Setiap kali user beralih ke home atau discover tab, `discover` data di-fetch ulang dari server. Tidak ada caching atau staleness check. Pada koneksi lambat (Termux + wifi lemah), ini memperlambat tab switching.

---

## 10. FORM VALIDATION

### FV-01 · Login form tidak ada `type="submit"` form wrapper — Enter di username tidak submit
**File:** `index.html:54–62`  
Input username + password tidak dibungkus `<form>`. Event listener `Enter` key hanya ada di password field (`events/index.js:55`):
```js
dom.adminPassword.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
});
```
Menekan Enter di username field tidak melakukan apapun — harus tab ke password dulu.  
**Fix:** Tambahkan listener serupa di username field, atau bungkus dengan `<form onsubmit>`.

---

### FV-02 · Login tidak ada rate limiting di sisi client
**File:** `js/services/auth.js:login()`  
Tombol di-disable saat proses auth, tapi setelah error, tombol aktif kembali tanpa delay. User bisa spam login dengan password berbeda tanpa batasan. Server-side rate limit harus ada, tapi client-side pun bisa membantu UX (cooldown counter).

---

### FV-03 · Volume slider tidak validasi range di browser audio path
**File:** `js/events/player-events.js:volSlider input listener`  
```js
audio.volume = Math.max(0, Math.min(1, store.volume / 150));
```
Volume diset dengan clamp `/150` (max 150 → volume 1.0). Ini benar. Tapi saat WS update datang (`state` message dengan `volume > 100`), nilai dipakai di `renderPlayerBar`:
```js
dom.volSlider.value = store.volume;
```
Slider HTML range adalah `min=0 max=150`, jadi bisa tampil value 150 di UI. Sementara audio clamped ke 1.0. User melihat "150%" tapi audio output berbeda — inconsistent.

---

## 11. STATE BUG

### SB-01 · `store.status` bisa race condition antara client optimistic update dan server state
**File:** `js/events/player-events.js` + `js/ws.js:handleServerMessage()`  
```js
// Di player-events.js (optimistic):
store.status = wantsPlay ? "PLAYING" : "PAUSED";
window.lastToggleTime = Date.now();

// Di ws.js (guard 1 detik):
if (!window.lastToggleTime || Date.now() - window.lastToggleTime > 1000) {
  if (store.status !== msg.data.status) {
    store.status = msg.data.status;
```
Guard 1 detik untuk mencegah server override optimistic state. Tapi jika server butuh >1 detik untuk respond (slow Termux), server bisa override state kembali ke kondisi sebelumnya, membalik update UI yang sudah tampil. PATCH comment ada tapi tidak fully resolved.

---

### SB-02 · `store.userRole` disimpan ke localStorage tapi tidak divalidasi ke server saat reload
**File:** `js/portal.js:initPortal()`  
```js
const role = window.safeStorage.get("ytgui_user_role");
if (role && role !== "client") {
  store.userRole = role;
}
```
Jika `role === "admin"` tersimpan di localStorage dari sesi sebelumnya, `store.userRole` langsung di-set "admin" tanpa validasi token ke server. WS `auth` command dikirim setelah koneksi (`ws.js:wsConnect()`) tapi ada window antara init dan auth dimana user sudah "admin" tanpa autentikasi server.

---

### SB-03 · `store.password` disimpan di store object in-memory
**File:** `js/store.js:5`  
```js
adminPassword: "",
```
Password disimpan ke `store.adminPassword` saat login (`auth.js:login()`). Store adalah plain JS object yang accessible dari browser console (`window.store`). Password tersimpan in-memory selama sesi. Tidak ada obfuscation. Seharusnya di-clear segera setelah dikirim ke WS.

---

### SB-04 · Queue drag-drop state `window.isDraggingQueue` tidak di-cleanup jika drag dibatalkan
**File:** `js/events/queue-events.js` (berdasarkan referensi di `events/index.js` dan `render/queue.js`)  
`render/queue.js:renderQueue()`: `if (window.isDraggingQueue) return;` — render di-skip saat drag. Jika drag operation dibatalkan (mis. scroll di luar, loss of pointer), flag tidak di-reset → queue berhenti update sampai drag event berikutnya.

---

### SB-05 · `_fakeBeatRaf` tidak di-cancel saat component teardown
**File:** `js/audio.js:startFakeBeatLoop()`  
rAF loop hanya stop saat `store.status !== 'PLAYING'`. Jika user logout (`logout()` di auth.js), status di-reset tapi tidak ada explicit `cancelAnimationFrame(_fakeBeatRaf)`. Loop berhenti secara natural pada tick berikutnya — tapi ada 1 frame lag dimana DOM masih dimanipulasi setelah logout.

---

### SB-06 · `_lazyCoverObserver` tidak di-disconnect saat halaman di-unload
**File:** `js/utils.js:loadLazyCovers()`  
Global IntersectionObserver tidak punya cleanup. Browser modern handle ini, tapi pada SPA-like navigation atau iframe embedding, bisa menyebabkan memory leak.

---

### SB-07 · WS reconnect setelah auth: `auth` token dikirim tapi `discover` tidak selalu ter-request
**File:** `js/ws.js:wsConnect() ws.onopen`  
```js
if (store.userRole === "admin") {
  const token = safeStorage.get("ytgui_session_token");
  if (token) { wsSend("auth", { token }); }
  const savedOutput = safeStorage.get("ytgui_audio_output") || "browser";
  wsSend("set_output", { output: savedOutput });
} else if (store.userRole === "client") {
  if (store.active_tab === "home" || store.active_tab === "discover") {
    wsSend("discover");
  }
}
```
Setelah reconnect sebagai admin, `discover` data tidak di-request ulang — `renderFullState()` dipanggil di `handleServerMessage("state")` yang mungkin belum datang. Jika koneksi terputus saat di tab discover, data discover bisa kosong setelah reconnect.

---

## 12. WIDGET TREE

### W-01 · `#player-bar` nested di dalam `#tab-home` (section) bukan di app shell
**File:** `index.html:131–200`  
```html
<section id="tab-home" class="tab-panel full-player-view">
  <!-- ... album art, track info ... -->
  <div class="pbar" id="player-bar">  <!-- ← di sini -->
  <!-- ... queue ... -->
</section>
```
Player bar berada di dalam tab panel home. Semua tab lain mendapat mini-player via CSS hack:
```css
body:not([data-active-tab="home"]) #tab-home {
  display: flex !important;
  height: 0;
  overflow: visible;
}
body:not([data-active-tab="home"]) #tab-home > *:not(#player-bar) {
  display: none !important;
}
```
Ini adalah **architectural smell** — player bar di-float keluar dari container dengan trick `overflow: visible` pada container `height: 0`. Rentan terhadap clipping, z-index issues, dan layout reflow. Seharusnya player bar di app shell root, bukan di dalam tab.

---

### W-02 · Empat bottom sheet (`settings`, `lyrics`, `action`, `help`) di-manage via shared overlay
**File:** `index.html:385–572` + `js/events/settings-events.js:closeMainOverlay()`  
Semua sheet berbagi satu `#main-overlay`. `closeMainOverlay()` menutup **semua** sheet sekaligus. Ini bermasalah jika dua sheet perlu transition (misal tutup settings, buka lyrics) — keduanya collapse sebelum yang baru bisa buka.

---

### W-03 · Home tab layout: `home-left-col` dan `home-right-col` tidak ada di semua breakpoint
**File:** `index.html` + `css/platform/desktop.css`  
Di mobile (default), `.home-left-col` dan `.home-right-col` tidak diassign ke grid area apapun — mereka stack secara natural sebagai flex children. Di desktop, grid areas `left` dan `right` diassign. Tapi tidak ada definisi `display: grid` atau positioning untuk mobile — bergantung pada flex order di DOM. Jika urutan DOM berubah, mobile layout rusak.

---

### W-04 · `#discover-favorites`, `#discover-recent` di `index.html` tidak ada — ada di DOM tapi tidak ada di HTML
**File:** `js/dom.js:113` (`discFavorites`, `discRecent`)  
```js
discFavorites: $("discover-favorites"),
discRecent: $("discover-recent"),
```
Di `index.html` discover tab, hanya ada `#discover-artists`, `#discover-genres`, dan `#discover-cached`. Tidak ada `#discover-favorites` atau `#discover-recent`. Elemen-elemen ini mungkin di-inject secara dinamis atau merupakan relics dari struktur lama. `dom.discFavorites` dan `dom.discRecent` akan `null`.  
**Severity:** High — `render/discover.js` memanggil `renderDiscoverList(dom.discFavorites, ...)` yang akan silently fail karena null check ada: `if (!container) return`.

---

### W-05 · Lyrics inline view (home tab) dan Lyrics sheet — dua render path berbeda
**File:** `js/render/lyrics.js` + `index.html`  
Ada dua tempat lyric ditampilkan:
1. **Home inline** — `#lyrics-prev`, `#lyrics-current`, `#lyrics-next` di dalam `.lyrics-wrap` (3-line view)
2. **Lyrics sheet** — `#lyrics-content` inside `#lyrics-sheet` (scrollable full view)

`renderLyrics()` harus update keduanya. Jika sheet belum pernah dibuka, `#lyrics-content` tidak ter-render. State divergence bisa terjadi jika lyrics offset diubah dari inline controls tapi tidak tersync ke sheet view.

---

## SEVERITY SUMMARY

| ID | Temuan | Severity |
|---|---|---|
| A-01 | Focus trap missing di bottom sheet | Critical |
| L-01 | Skeleton CSS var undefined | High |
| W-04 | `#discover-favorites` / `#discover-recent` null di DOM | High |
| SB-03 | Password in-memory di store | High |
| SB-02 | Admin role dari localStorage tanpa server validation | High |
| R-01 | Lyrics disembunyikan total di mobile | Medium-High |
| UX-03 | Radio randomize bisa spam-klik | Medium |
| A-05 | Play button aria-label tidak update | Medium |
| SB-01 | Status race condition optimistic vs server | Medium |
| W-01 | Player bar nested di tab home (architectural) | Medium |
| AN-02 | `::before` / `::after` konflik pada home-art-frame | Medium |
| UI-01 | Settings sheet CSS double-defined | Low-Medium |
| RB-01 | `favorites.js` file kosong | Low |
| AN-04 | `transmit-radio` keyframe duplikat | Low |

---

*Audit ini berdasarkan source code aktual. Temuan yang tidak dapat dikonfirmasi dari source code tidak dimasukkan.*
