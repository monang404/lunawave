# FRONTEND AUDIT REPORT — LunaWave
**Auditor:** Senior Frontend Engineer + UI/UX Expert + Performance Engineer + Security Engineer + QA Lead  
**Scope:** `web/static/index.html`, `web/static/js/**`, `web/static/css/**`, `web/static/sw.js`, `web/static/manifest.json`  
**Eksklusi:** `/archive`, `/arsip`, semua file `.md`  
**Stack:** Vanilla JS (no framework), CSS Custom Properties, WebSocket, Service Worker, Web Audio API  
**Tanggal Audit:** 2026-07-07

---

## RINGKASAN EKSEKUTIF

Frontend LunaWave adalah aplikasi musik berbasis vanilla JS dengan desain mobile-first yang cukup matang. Layout multi-platform (mobile / tablet / desktop / landscape) sudah diimplementasikan. Namun terdapat **24 temuan** dengan severity dari LOW hingga CRITICAL yang mencakup: state bug pada dual event listener, ITUNES_API_URL yang tidak pernah didefinisikan (menyebabkan runtime crash), Service Worker cache stale yang mem-bypass deployment baru, masalah aksesibilitas yang sistemik, dark mode yang tidak lengkap, serta sejumlah UX regression pada mobile.

---

## TEMUAN

---

### FE-001 — `ITUNES_API_URL` Tidak Pernah Didefinisikan: Runtime ReferenceError
**Severity:** 🔴 CRITICAL  
**Kategori:** State Bug, JavaScript Error

**Dampak:**  
Fungsi `getCoverArt()` di `utils.js` menggunakan konstanta `ITUNES_API_URL` yang **tidak pernah didefinisikan** di mana pun dalam codebase. Setiap kali fungsi ini dipanggil untuk mengambil cover art, browser akan melempar `ReferenceError: ITUNES_API_URL is not defined`, yang menyebabkan semua thumbnail track (baik di home, search, discover, maupun queue) menggunakan YouTube fallback yang beresolusi rendah. Ini silent failure yang memengaruhi semua user.

**Lokasi File:** `web/static/js/utils.js`

```javascript
// CRASH: ITUNES_API_URL tidak ada di config.js, index.html, maupun bundle
const response = await fetch(`${ITUNES_API_URL}?term=${query}&media=music&limit=1`);
```

`web/static/js/config.js` hanya berisi:
```javascript
const TABS = ["home", "search", "radio", "discover"];
// ← Tidak ada ITUNES_API_URL
```

**Solusi:** Definisikan konstanta di `config.js`:

```javascript
// config.js
const TABS = ["home", "search", "radio", "discover"];
const ITUNES_API_URL = "https://itunes.apple.com/search";
```

Atau tambahkan fallback aman di `getCoverArt()`:

```javascript
const ITUNES_BASE = typeof ITUNES_API_URL !== "undefined"
    ? ITUNES_API_URL
    : "https://itunes.apple.com/search";

const response = await fetch(`${ITUNES_BASE}?term=${query}&media=music&limit=1`);
```

---

### FE-002 — Service Worker Cache Stale: Deployment Bypass
**Severity:** 🔴 CRITICAL  
**Kategori:** Service Worker, Cache Strategy, Deployment

**Dampak:**  
`bundle.js` di-load dengan query param versi: `bundle.js?v=1783323309`. Namun di `sw.js`, asset yang di-precache adalah `/static/js/bundle.js` **tanpa query param**:

```javascript
// sw.js
const PRECACHE_ASSETS = [
    // ...
    '/static/js/bundle.js',   // ← TIDAK ada ?v=
];
```

Ini berarti setelah deployment baru, SW lama akan terus menyajikan versi `bundle.js` lama dari cache, karena cache key tidak cocok dengan URL baru yang ada query param-nya. Setiap kali ada update JS, sebagian user akan tetap menjalankan kode lama hingga SW expire (yang bisa berminggu-minggu).

Komentar di `index.html` sendiri mengakui masalah ini:
```html
<!-- PATCH-SW-KILLSWITCH-01: Service Worker registration sudah di-DISABLE di main.js,
tapi SW lama yang sempat ter-register di sesi sebelumnya tetap aktif... -->
<script>
// ← Script kill SW tidak ada di sini!
</script>
```

**Penyebab:**  
Inkonsistensi antara URL di HTML (`?v=...`) dan URL di precache list SW.

**Solusi:**  
Sinkronkan versi di kedua tempat, atau gunakan Workbox/Cache-Busting yang benar:

```javascript
// sw.js — gunakan fetch-first strategy untuk JS/CSS (bukan cache-first)
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);
    
    // Bundle JS: network-first, fallback cache
    if (url.pathname.includes('bundle.js')) {
        event.respondWith(
            fetch(event.request)
                .then(resp => {
                    const cloned = resp.clone();
                    caches.open(STATIC_CACHE).then(c => c.put(event.request, cloned));
                    return resp;
                })
                .catch(() => caches.match('/static/js/bundle.js'))
        );
        return;
    }
    // ...static assets: cache-first
});
```

Atau implementasikan `CACHE_VERSION` yang di-bump setiap build:

```javascript
// sw.js — auto-invalidate via version bump
const CACHE_VERSION = 'v1783323309'; // ← harus sama dengan query param di HTML
```

---

### FE-003 — Duplicate Event Listener pada Lyric Offset Controls
**Severity:** 🔴 CRITICAL  
**Kategori:** State Bug, Event Handler Duplication

**Dampak:**  
Di `lyrics-events.js`, terdapat **dua set event listener** yang mendaftarkan handler yang identik untuk tombol `btn-sync-minus` dan `btn-sync-plus`:

```javascript
// Set 1: via dom.lyricOffsetMinus (dari initLyricsEvents)
dom.lyricOffsetMinus.addEventListener("click", () => {
    store.lyrics_offset = (store.lyrics_offset || 0) - 0.5;
    // ...
});

// Set 2: via btnSyncMinus (direct getElementById di top-level)
btnSyncMinus.addEventListener("click", (e) => {
    e.stopPropagation();
    store.lyrics_offset = (store.lyrics_offset || 0) - 0.5;  // ← SAMA!
    // ...
});
```

`dom.lyricOffsetMinus` dan `btnSyncMinus` merujuk pada **elemen yang sama** (`#lyric-offset-minus`). Akibatnya setiap klik pada tombol offset akan mengubah `lyrics_offset` **dua kali** (misalnya -0.5 + -0.5 = -1.0 alih-alih -0.5). Ini adalah bug yang akan merusak sinkronisasi lirik secara silent.

**Lokasi File:** `web/static/js/events/lyrics-events.js` — baris 34-45 dan 59-70

**Solusi:** Hapus salah satu set listener. Pertahankan yang di dalam `initLyricsEvents()` dan hapus top-level binding:

```javascript
// lyrics-events.js — hapus top-level variable dan listener duplikat
// HAPUS baris ini dari top-level:
// const btnSyncMinus = document.getElementById("btn-sync-minus");
// const btnSyncPlus = document.getElementById("btn-sync-plus");

// HAPUS block if (btnSyncMinus) {...} dan if (btnSyncPlus) {...} dari initLyricsEvents
// Pertahankan hanya yang menggunakan dom.lyricOffsetMinus / dom.lyricOffsetPlus
```

---

### FE-004 — `renderSheetLyrics()` Menambah Scroll Listener Tanpa Batas
**Severity:** 🟠 HIGH  
**Kategori:** Memory Leak, Event Handler

**Dampak:**  
`renderSheetLyrics()` dipanggil setiap kali lirik berubah (via `renderLyrics()` → dipanggil dari `progress` message setiap detik). Di dalamnya, terdapat guard `_scrollBound` untuk mencegah listener ditambah berulang, **namun guard ini menggunakan property pada DOM element** (`dom.lyricsContent._scrollBound`), yang merupakan non-standard dan rentan:

```javascript
function renderSheetLyrics() {
    if (!dom.lyricsContent._scrollBound) {
        dom.lyricsContent._scrollBound = true;
        // ...
        dom.lyricsContent.addEventListener("wheel", setScrolling, {passive: true});
        dom.lyricsContent.addEventListener("touchmove", setScrolling, {passive: true});
    }
    // ...innerHTML = ... (HAPUS dan RE-CREATE elemen setiap render!)
}
```

Setiap kali `innerHTML` di-set ulang, elemen lama dihapus dan elemen baru dibuat, tapi `_scrollBound` masih `true` di referensi `dom.lyricsContent` yang sama. Ini mungkin aman untuk listener pada container, tapi jika `dom.lyricsContent` diganti (misal via innerHTML parent), listener lama akan leak.

**Lokasi File:** `web/static/js/render/lyrics.js`

**Solusi:** Gunakan `AbortController` atau pastikan listener hanya ditambah sekali di `initLyricsEvents()`, bukan di render function:

```javascript
// Pindahkan ke initLyricsEvents(), bukan di render function
function initLyricsEvents() {
    // ...existing code...
    
    // Scroll listener — sekali saja, bukan setiap render
    if (dom.lyricsContent) {
        const setScrolling = () => {
            window.isScrollingLyrics = true;
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => window.isScrollingLyrics = false, 3000);
        };
        dom.lyricsContent.addEventListener("wheel", setScrolling, {passive: true});
        dom.lyricsContent.addEventListener("touchmove", setScrolling, {passive: true});
    }
}
```

---

### FE-005 — Tidak Ada Focus Trap pada Modal/Bottom Sheet
**Severity:** 🟠 HIGH  
**Kategori:** Accessibility (WCAG 2.1 — 2.1.2 No Keyboard Trap)

**Dampak:**  
Settings sheet, lyrics sheet, action sheet, dan help sheet tidak mengimplementasikan focus trap. Saat sheet terbuka, pengguna keyboard dapat berpindah focus ke elemen di belakang overlay, yang tidak seharusnya bisa diinteraksi. Ini melanggar WCAG 2.1.2 dan merupakan masalah serius bagi pengguna screen reader dan keyboard-only.

**Lokasi File:** `web/static/index.html` — semua `.settings-sheet`, `web/static/js/events/settings-events.js`

```javascript
// openSettings() — tidak ada focus trap
function openSettings() {
    if (dom.settingsSheet) dom.settingsSheet.classList.add("open");
    if (dom.mainOverlay) dom.mainOverlay.classList.add("open");
    renderSettingsSheet();
    // ← MISSING: focus trap, focus first element
}
```

**Solusi:** Implementasikan focus trap sederhana:

```javascript
function trapFocus(element) {
    const focusable = element.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    
    // Focus first element
    first.focus();
    
    // Trap Tab key
    const trap = (e) => {
        if (e.key !== "Tab") return;
        if (e.shiftKey) {
            if (document.activeElement === first) { e.preventDefault(); last.focus(); }
        } else {
            if (document.activeElement === last) { e.preventDefault(); first.focus(); }
        }
    };
    element.addEventListener("keydown", trap);
    return () => element.removeEventListener("keydown", trap); // cleanup
}

function openSettings() {
    dom.settingsSheet.classList.add("open");
    dom.mainOverlay.classList.add("open");
    renderSettingsSheet();
    const cleanup = trapFocus(dom.settingsSheet);
    dom.settingsSheet._focusTrapCleanup = cleanup;
}

function closeSettings() {
    if (dom.settingsSheet._focusTrapCleanup) {
        dom.settingsSheet._focusTrapCleanup();
        delete dom.settingsSheet._focusTrapCleanup;
    }
    dom.settingsSheet.classList.remove("open");
    closeMainOverlay();
    dom.btnSettings.focus(); // return focus ke trigger
}
```

---

### FE-006 — Login Form: Tidak Ada `<label>` pada Input Fields
**Severity:** 🟠 HIGH  
**Kategori:** Accessibility (WCAG 2.1 — 1.3.1 Info and Relationships)

**Dampak:**  
Kedua field login (username dan password) tidak memiliki elemen `<label>` yang terasosiasi. Screen reader tidak bisa mengidentifikasi tujuan field-field ini. `placeholder` bukan pengganti `<label>` yang valid secara aksesibilitas.

**Lokasi File:** `web/static/index.html`

```html
<!-- Kondisi saat ini — tidak ada label -->
<div class="login-input-group">
    <input type="text" id="admin-username" placeholder="Username" autocomplete="off">
</div>
<div class="login-input-group">
    <input type="password" id="admin-password" placeholder="Password">
</div>
```

**Solusi:**

```html
<div class="login-input-group">
    <label for="admin-username" class="sr-only">Username</label>
    <input type="text" id="admin-username" placeholder="Username" 
           autocomplete="username" autocapitalize="none" spellcheck="false">
</div>
<div class="login-input-group">
    <label for="admin-password" class="sr-only">Password</label>
    <input type="password" id="admin-password" placeholder="Password"
           autocomplete="current-password">
</div>
```

Tambahkan CSS untuk visually hidden label:

```css
.sr-only {
    position: absolute;
    width: 1px; height: 1px;
    padding: 0; margin: -1px;
    overflow: hidden; clip: rect(0,0,0,0);
    white-space: nowrap; border: 0;
}
```

---

### FE-007 — Volume Slider Tidak Ada `aria-label` dan `aria-valuenow`
**Severity:** 🟠 HIGH  
**Kategori:** Accessibility (WCAG 2.1 — 1.3.1)

**Dampak:**  
Input range untuk volume tidak memiliki `aria-label`, `aria-valuemin`, `aria-valuemax`, dan `aria-valuenow` yang dinamis. Screen reader hanya membaca "80" tanpa konteks bahwa ini adalah volume control.

**Lokasi File:** `web/static/index.html`

```html
<!-- Tidak ada aria attributes -->
<input type="range" min="0" max="150" value="80" class="vol-slider" id="vol-slider">
```

**Solusi:**

```html
<input type="range" 
       min="0" max="150" value="80" 
       class="vol-slider" id="vol-slider"
       aria-label="Volume"
       aria-valuemin="0"
       aria-valuemax="150"
       aria-valuenow="80"
       aria-valuetext="80%">
```

Update `aria-valuenow` dan `aria-valuetext` saat slider berubah:

```javascript
// player-events.js
dom.volSlider.addEventListener("input", () => {
    store.volume = parseInt(dom.volSlider.value);
    dom.volSlider.setAttribute("aria-valuenow", store.volume);
    dom.volSlider.setAttribute("aria-valuetext", store.volume + "%");
    // ...
});
```

---

### FE-008 — Dark Mode: Aplikasi Hanya Mendukung Dark, Tidak Ada Light Mode Support
**Severity:** 🟠 HIGH  
**Kategori:** Dark Mode, Accessibility (WCAG 2.1 — 1.4.3 Contrast)

**Dampak:**  
Seluruh design system menggunakan warna hardcoded dark (`#0E0E12`, `#151518`, dst). Tidak ada `@media (prefers-color-scheme: light)` di mana pun dalam codebase. User yang sistem operasinya dalam light mode akan dipaksa menggunakan dark mode — tidak ada respek terhadap preferensi sistem.

Meski ini aplikasi yang secara brand "Midnight Audio Experience" (dark-only), absennya `color-scheme` deklarasi menyebabkan browser scrollbar, input fields, dan form controls tetap menggunakan OS default (putih), yang menciptakan kontras yang menyilaukan di dalam UI dark.

**Lokasi File:** `web/static/css/tokens.css` — tidak ada `@media (prefers-color-scheme: light)`

**Solusi minimum:** Deklarasikan `color-scheme` agar browser tahu ini adalah dark-only app, sehingga browser controls (scrollbar, input native) juga menggunakan dark style:

```css
/* tokens.css */
:root {
    color-scheme: dark;  /* ← Tambahkan ini */
    /* ...existing vars... */
}
```

Untuk support penuh light mode, buat token override:

```css
@media (prefers-color-scheme: light) {
    :root {
        --bg-primary: #F8F9FA;
        --bg-surface: #FFFFFF;
        --bg-elevated: #F0F1F3;
        --text-1: #111318;
        --text-2: #4A5568;
        --text-3: #6B7280;
        --border-1: rgba(0, 0, 0, 0.06);
        --border-2: rgba(0, 0, 0, 0.10);
        --border-3: rgba(0, 0, 0, 0.18);
    }
}
```

---

### FE-009 — Responsive: Lirik Dipotong Paksa di Mobile (Max-Height 40px)
**Severity:** 🟠 HIGH  
**Kategori:** Responsive Issue, UX

**Dampak:**  
Di mobile (<600px), `lyrics-wrap` dibatasi `max-height: 40px` dan `overflow: hidden`, yang menyebabkan teks lirik terpotong. Lyric `prev` dan `next` disembunyikan, hanya `current` yang tampil tapi dengan ukuran font 14px dipaksa `text-overflow: ellipsis`. Ini menyebabkan lirik panjang tidak terbaca sama sekali.

**Lokasi File:** `web/static/css/platform/mobile.css`

```css
@media (max-width: 600px) {
    #tab-home .lyrics-wrap {
        max-height: 40px;   /* ← Terlalu kecil */
        overflow: hidden;
    }
    #tab-home .lyrics-line.current {
        font-size: 14px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;  /* ← Lirik panjang terpotong */
    }
}
```

**Solusi:**

```css
@media (max-width: 600px) {
    #tab-home .lyrics-wrap {
        max-height: 80px;    /* Lebih ruang */
        overflow: hidden;
    }
    #tab-home .lyrics-line.current {
        font-size: 15px;
        white-space: normal;      /* Biarkan wrap */
        overflow: visible;
        text-overflow: unset;
        line-height: 1.4;
        display: -webkit-box;
        -webkit-line-clamp: 2;    /* Maksimal 2 baris */
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
}
```

---

### FE-010 — Responsive: Desktop Player Bar Menggunakan `!important` Berlebihan (CSS Specificity War)
**Severity:** 🟡 MEDIUM  
**Kategori:** Responsive Issue, CSS Anti-Pattern, Maintainability

**Dampak:**  
`desktop.css` menggunakan 30+ deklarasi `!important` untuk meng-override player bar layout. Ini adalah tanda specificity war — CSS arsitektur yang buruk. Setiap perubahan di base CSS membutuhkan tambahan `!important` baru, menyebabkan kode semakin tidak maintainable.

**Lokasi File:** `web/static/css/platform/desktop.css` dan `landscape.css`

```css
/* desktop.css — pola berulang */
#player-bar {
    position: fixed !important;
    bottom: 24px !important;
    left: calc(50vw + 44px) !important;
    transform: translateX(-50%) !important;
    width: calc(100vw - 88px - 48px) !important;
    max-width: 1000px !important;
    height: 76px !important;
    min-height: 76px !important;
    /* ... 15+ deklarasi !important lagi */
}
```

`landscape.css` menduplikasi blok yang **identik** dengan `desktop.css` untuk player bar floating pill.

**Solusi:**  
Ekstrak player bar floating style ke class `.player-bar--floating` dan apply via JS:

```css
/* Satu definisi, bukan duplikat di 2 file */
.player-bar--floating {
    position: fixed;
    bottom: 24px;
    border-radius: var(--r-lg);
    box-shadow: var(--shadow-lg);
}

@media (min-width: 1024px) {
    #player-bar { /* apply class via media query or JS */ }
    #nav-bar { /* sidebar */ }
}
```

---

### FE-011 — UX: Swipe Gesture Hanya Tersedia untuk Admin
**Severity:** 🟡 MEDIUM  
**Kategori:** UX, Navigation

**Dampak:**  
Gesture swipe horizontal (next/prev track) di `touch.js` langsung return jika `store.userRole !== "admin"`, dan hanya menampilkan toast pesan "Hanya admin yang bisa memutar musik". Client mode user yang hanya mendengarkan tidak mendapatkan feedback apa pun untuk swipe yang tidak tersedia — desain yang buruk karena gesture terdaftar tapi hasilnya confusing.

**Lokasi File:** `web/static/js/platform/touch.js`

```javascript
if (diffX > 80 && diffX > diffY) {
    if (store.userRole !== "admin") {
        showLogToast("Hanya admin yang bisa memutar musik");
        return;  // ← Toast muncul, lalu tidak ada yang terjadi
    }
    // ...
}
```

**Solusi:**  
Untuk client mode, gesture sebaiknya melakukan sesuatu (misal scroll ke track info) atau tidak ada feedback sama sekali. Toast "hanya admin" untuk gesture terasa sangat mengganggu:

```javascript
document.addEventListener('touchend', e => {
    // ...
    if (diffX > 80 && diffX > diffY) {
        if (store.userRole !== "admin") return; // Silent - jangan toast
        // ...
    }
});
```

---

### FE-012 — UX: Login Error State Tidak Di-Clear Saat Re-attempt
**Severity:** 🟡 MEDIUM  
**Kategori:** Form Validation, UX

**Dampak:**  
Pesan error login (`#login-error-msg`) hanya di-clear ketika auth berhasil. Jika user salah password, tampil error. Jika user mengetik ulang tapi belum klik submit, error lama masih tampil, memberikan false negative impression.

**Lokasi File:** `web/static/js/services/auth.js`

```javascript
function login(user, pass) {
    if (!user || !pass) {
        dom.loginErrorMsg.textContent = "Isi username dan password!";
        return;
    }
    // ← MISSING: clear error message on new attempt
    dom.loginErrorMsg.textContent = "";  // Ini ada, tapi setelah null check
```

`dom.loginErrorMsg.textContent = ""` hanya dijalankan setelah validasi `!user || !pass`. Jika sebelumnya error dari server, lalu user mengetik dan klik lagi, error lama akan langsung hilang saat `wsSend` dipanggil — ini sebenarnya sudah benar. Namun, error tidak hilang saat user **mulai mengetik** di field.

**Solusi:** Clear error saat input berubah:

```javascript
// events/index.js — di inisialisasi form
if (dom.adminUsername) {
    dom.adminUsername.addEventListener("input", () => {
        dom.loginErrorMsg.textContent = "";
    });
}
if (dom.adminPassword) {
    dom.adminPassword.addEventListener("input", () => {
        dom.loginErrorMsg.textContent = "";
    });
}
```

---

### FE-013 — Form Validation: Login Submit dengan Enter Hanya dari Password Field
**Severity:** 🟡 MEDIUM  
**Kategori:** Form Validation, UX

**Dampak:**  
Shortcut Enter untuk submit hanya terdaftar di `admin-password`. Jika user mengetik username lalu langsung Enter (tanpa pindah ke password), tidak ada yang terjadi. Alur yang diharapkan oleh kebanyakan user adalah Tab→Tab→Enter.

**Lokasi File:** `web/static/js/events/index.js`

```javascript
if (dom.adminPassword) {
    dom.adminPassword.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
    });
}
// ← MISSING: Enter handler di admin-username juga
```

**Solusi:**

```javascript
// Tambahkan Enter handler di username field juga
if (dom.adminUsername) {
    dom.adminUsername.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            if (dom.adminPassword) dom.adminPassword.focus(); // Tab ke password
        }
    });
}
if (dom.adminPassword) {
    dom.adminPassword.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && dom.adminSubmitBtn) dom.adminSubmitBtn.click();
    });
}
```

---

### FE-014 — State Bug: `store.status` Di-set Optimistik Sebelum Server Konfirmasi
**Severity:** 🟡 MEDIUM  
**Kategori:** State Bug

**Dampak:**  
Ketika user klik Play/Pause atau Next/Prev, `store.status` langsung diubah di frontend sebelum server merespons:

```javascript
// player-events.js
dom.btnPlay.addEventListener("click", () => {
    const wantsPlay = store.status !== "PLAYING";
    store.status = wantsPlay ? "PLAYING" : "PAUSED";  // ← Optimistic, bisa salah
    window.lastToggleTime = Date.now();
    renderPlayBtn();
    renderNowPlaying();
    wsSend(WS_ACTIONS.TOGGLE_PAUSE);
});
```

Jika server gagal atau command diabaikan, UI akan menampilkan status yang berbeda dengan kondisi aktual. Ada guard `lastToggleTime` untuk mencegah server override selama 1 detik, tapi ini menimbulkan window di mana state bisa tidak sinkron permanen jika WebSocket drop tepat saat command dikirim.

**Solusi:**  
Untuk PLAYING/PAUSED, optimistic update dapat diterima jika ada rollback mechanism. Tambahkan rollback jika `state` message tidak datang dalam 3 detik:

```javascript
dom.btnPlay.addEventListener("click", () => {
    if (store.userRole !== "admin") return;
    const prevStatus = store.status;
    const wantsPlay = store.status !== "PLAYING";
    store.status = wantsPlay ? "PLAYING" : "PAUSED";
    window.lastToggleTime = Date.now();
    renderPlayBtn();
    
    // Rollback jika tidak ada konfirmasi dalam 3 detik
    const rollbackTimer = setTimeout(() => {
        if (Date.now() - window.lastToggleTime >= 3000) {
            store.status = prevStatus;
            renderPlayBtn();
        }
    }, 3000);
    
    wsSend(WS_ACTIONS.TOGGLE_PAUSE);
});
```

---

### FE-015 — Navigation: `aria-selected` Tidak Update Saat Tab Berubah via Swipe
**Severity:** 🟡 MEDIUM  
**Kategori:** Navigation, Accessibility

**Dampak:**  
`switchTab()` memperbarui `aria-selected` pada `.nav-btn`. Namun swipe gesture di `touch.js` tidak memanggil `switchTab()` — ia langsung mengirim `WS_ACTIONS.NEXT/PREV` tanpa mengubah tab aktif. Ini tidak langsung terkait navigation tab, tapi jika ada tab switching dari gesture di masa depan, pola ini akan menyebabkan `aria-selected` tidak sync.

Yang lebih kritis: Navigasi tab menggunakan `role="tab"` dan `role="tablist"`, tapi tidak ada `role="tabpanel"` yang terasosiasi dengan `aria-controls` di nav button. Screen reader tidak bisa memahami hubungan antara tab button dan konten panel.

**Lokasi File:** `web/static/index.html` dan `web/static/js/main.js`

```html
<!-- nav button tidak memiliki aria-controls -->
<button class="nav-btn" data-tab="home" id="nav-home" role="tab" aria-selected="false">
    <!-- ← MISSING: aria-controls="tab-home" -->
```

```html
<!-- tab panel tidak memiliki role="tabpanel" -->
<section id="tab-home" class="tab-panel full-player-view">
    <!-- ← MISSING: role="tabpanel" aria-labelledby="nav-home" -->
```

**Solusi:**

```html
<button class="nav-btn" data-tab="home" id="nav-home" 
        role="tab" aria-selected="false" aria-controls="tab-home">

<section id="tab-home" class="tab-panel full-player-view"
         role="tabpanel" aria-labelledby="nav-home" tabindex="0">
```

---

### FE-016 — UI Consistency: Inline Style vs CSS Class (Anti-Pattern)
**Severity:** 🟡 MEDIUM  
**Kategori:** UI Consistency, Maintainability, Code Smell

**Dampak:**  
Terdapat banyak inline style langsung di HTML yang seharusnya menggunakan CSS class:

```html
<!-- index.html — style inline tersebar di mana-mana -->
<div id="queue-footer" style="font-size: var(--t-xs); color: var(--text-3); font-weight: var(--w-medium);">
<button id="radio-randomize-btn" class="label-link" style="background:none; border:none; display:flex; align-items:center; gap:6px; font-family:inherit; min-height: 44px; min-width: 44px; padding: 10px; margin: -10px;">
<div id="radio-queue-list" style="display:flex; flex-direction:column; padding-bottom:80px;">
<div id="discover-cached" style="display:flex; flex-direction:column; padding-bottom:80px;">
```

Ada 15+ elemen dengan inline style di `index.html`. Ini menyulitkan theming, dark/light mode toggle, dan debugging via DevTools.

**Solusi:** Ekstrak semua inline style ke CSS classes yang bermakna:

```css
/* queue.css */
.queue-footer-label {
    font-size: var(--t-xs);
    color: var(--text-3);
    font-weight: var(--w-medium);
}

.radio-queue-container {
    display: flex;
    flex-direction: column;
    padding-bottom: var(--s12);  /* 80px → gunakan token */
}
```

---

### FE-017 — Loading State: Tidak Ada Skeleton Screen untuk Queue dan Radio
**Severity:** 🟡 MEDIUM  
**Kategori:** Loading, UX

**Dampak:**  
Tab Discover memiliki skeleton loader yang bagus. Namun queue list (`#queue-list`) dan radio queue (`#radio-queue-list`) tidak memiliki loading state sama sekali. Saat aplikasi pertama kali load dan WebSocket belum terhubung, kedua container ini kosong tanpa indikasi apapun — user tidak tahu apakah data sedang dimuat atau memang tidak ada data.

**Lokasi File:** `web/static/js/render/queue.js`, `web/static/index.html`

```javascript
// renderQueue() — langsung render empty state, tidak ada loading state
function renderQueue() {
    if (window.isDraggingQueue) return;
    // ← Tidak ada kondisi "isLoading"
    renderList(dom.queueList, store.queue, false, ...);
}
```

**Solusi:** Tambahkan loading state awal dan gunakan skeleton loader yang konsisten dengan Discover tab:

```javascript
function renderQueue() {
    if (window.isDraggingQueue) return;
    if (!store.is_online) {
        dom.queueList.innerHTML = '<div class="queue-empty">Menghubungkan ke server...</div>';
        return;
    }
    renderList(dom.queueList, store.queue, false, ...);
}
```

```html
<!-- index.html — initial skeleton di queue -->
<div id="queue-list" class="u-flex-col">
    <!-- Skeleton sementara sebelum WS connect -->
    <div class="queue-item" style="pointer-events:none;">
        <div class="skeleton-box" style="width:20px; height:14px; border-radius:4px;"></div>
        <div class="qi-info">
            <div class="skeleton-box" style="width:70%; height:14px; margin-bottom:4px;"></div>
            <div class="skeleton-box" style="width:40%; height:12px;"></div>
        </div>
    </div>
</div>
```

---

### FE-018 — Animation: Fake Beat Loop Berjalan Saat Tab Tidak Aktif
**Severity:** 🟡 MEDIUM  
**Kategori:** Animation, Performance

**Dampak:**  
`startFakeBeatLoop()` di `audio.js` menggunakan `requestAnimationFrame` yang terus berjalan selama `store.status === 'PLAYING'`. Namun tidak ada pause saat browser tab tidak aktif atau saat user pindah ke tab lain. `requestAnimationFrame` memang otomatis pause saat tab tidak visible di browser modern, tapi `setTimeout` di dalamnya tidak.

Juga, beat loop ini berjalan setiap 500ms tanpa mempertimbangkan `prefers-reduced-motion`. User dengan vestibular disorder yang mengaktifkan `prefers-reduced-motion` akan tetap melihat glow effect berkedip setiap 500ms.

**Lokasi File:** `web/static/js/audio.js`

```javascript
function startFakeBeatLoop() {
    const BASE_INTERVAL = 500;
    // ...
    setTimeout(() => {
        // Set CSS property — berjalan walau tab tidak aktif
        dom.tabHome.style.setProperty('--beat-glow-opacity', '0.4');
    }, 150);  // ← setTimeout tidak terpengaruh rAF pause
}
```

**Solusi:**

```javascript
function startFakeBeatLoop() {
    if (_fakeBeatRaf) return;
    
    // Respek reduced motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    
    // ... existing loop code ...
    
    // Pause saat tab tidak visible
    document.addEventListener('visibilitychange', () => {
        if (document.hidden && _fakeBeatRaf) {
            cancelAnimationFrame(_fakeBeatRaf);
            _fakeBeatRaf = null;
        } else if (!document.hidden && store.status === 'PLAYING') {
            startFakeBeatLoop();
        }
    });
}
```

---

### FE-019 — PWA: Manifest Hanya Satu Icon (1024x1024)
**Severity:** 🟡 MEDIUM  
**Kategori:** PWA, UI Consistency

**Dampak:**  
`manifest.json` hanya mendefinisikan satu icon dalam satu ukuran (1024x1024). Ini menyebabkan:
- Android Chrome tidak punya icon yang tepat untuk home screen shortcut (butuh 192x192 dan 512x512 minimal)
- iOS tidak punya `apple-touch-icon`
- Tidak ada `maskable` icon untuk Android adaptive icons

**Lokasi File:** `web/static/manifest.json`

```json
{
  "icons": [
    {
      "src": "/static/lunawave_logo.png",
      "sizes": "1024x1024",
      "type": "image/png"
      // ← MISSING: "purpose": "maskable any"
    }
  ]
}
```

**Solusi:**

```json
{
  "icons": [
    { "src": "/static/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/static/icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/static/icons/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

Tambahkan di `index.html`:
```html
<link rel="apple-touch-icon" sizes="180x180" href="/static/icons/apple-touch-icon.png">
```

---

### FE-020 — Widget Tree: `favorites.js` adalah File Kosong
**Severity:** 🟡 MEDIUM  
**Kategori:** Widget Tree, Code Smell, Technical Debt

**Dampak:**  
File `web/static/js/render/favorites.js` ada di direktori render namun **isinya kosong**. Logika render favorites justru ada di `render/discover.js`. Ini menyebabkan:
- Kebingungan saat developer baru mencari kode favorites
- File kosong yang di-bundle (menambah overhead kecil tapi tetap technical debt)
- Indikasi bahwa refactoring belum selesai dilakukan

**Lokasi File:** `web/static/js/render/favorites.js` — 0 bytes

**Solusi:** Hapus file kosong atau pindahkan logika favorites dari `discover.js` ke `favorites.js`:

```javascript
// render/favorites.js — pindahkan dari discover.js
function renderFavorites(container, items) {
    if (!container || !items) return;
    renderDiscoverList(
        container,
        items,
        '<div class="discover-empty">...</div>',
        createFavoriteTemplate,
        updateFavoriteItem
    );
}
```

---

### FE-021 — Rebuild: Hashtag Color Menggunakan `Math.random()` — Warna Berubah Setiap Render
**Severity:** 🟡 MEDIUM  
**Kategori:** Rebuild, UI Consistency, State Bug

**Dampak:**  
`getHashtagColor()` di `discover.js` menggunakan `Math.random()` untuk generate warna, dengan cache di `_hashtagColors` dict. Namun cache ini hanya persist selama sesi (in-memory). Setiap kali halaman di-refresh atau komponen re-mount, warna artis/genre akan berubah secara random. Ini menyebabkan visual yang tidak konsisten — artis yang sama bisa berwarna kuning di satu sesi dan merah di sesi lain.

**Lokasi File:** `web/static/js/render/discover.js`

```javascript
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag]; // only in-memory
    const hue = Math.floor(Math.random() * 360); // ← Random setiap sesi
    // ...
}
```

**Solusi:** Gunakan hash deterministik dari nama artis/genre:

```javascript
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag];
    
    // Deterministic hash dari string
    let hash = 0;
    for (let i = 0; i < hashtag.length; i++) {
        hash = ((hash << 5) - hash) + hashtag.charCodeAt(i);
        hash |= 0; // Convert to 32bit int
    }
    const hue = Math.abs(hash) % 360;
    const saturation = 60 + (Math.abs(hash >> 8) % 30);
    const lightness = 50 + (Math.abs(hash >> 16) % 20);
    
    const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    _hashtagColors[hashtag] = color;
    return color;
}
```

---

### FE-022 — UX: Artist Name Truncated di 25 Karakter dengan Nilai Hardcoded
**Severity:** 🟢 LOW  
**Kategori:** UX, Code Smell

**Dampak:**  
Di `render/search.js` dan `render/discover.js`, nama artis di-truncate di 25 karakter dengan logika manual yang di-hardcode:

```javascript
// Duplikasi di search.js DAN discover.js
if (artistName.length > 25) {
    artistName = artistName.substring(0, 22) + "...";
}
```

Duplikat logika ini muncul setidaknya 3 kali. Selain itu, truncation via JS tidak responsif — di layar lebar, 25 karakter mungkin terlalu sedikit; di layar sempit, mungkin sudah cukup. CSS `text-overflow: ellipsis` lebih tepat karena responsif terhadap lebar container.

**Solusi:** Hapus JS truncation, gunakan CSS:

```css
.sr-meta, .fav-cnt, .radio-queue-artist {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%; /* Biarkan container yang tentukan */
}
```

Dan buat helper terpusat jika truncation tetap perlu:

```javascript
// utils.js
window.truncateText = (text, maxLen = 40) => 
    text && text.length > maxLen ? text.substring(0, maxLen - 3) + "..." : (text || "");
```

---

### FE-023 — Console.log Masih Ada di Production Code
**Severity:** 🟢 LOW  
**Kategori:** Code Smell, Security

**Dampak:**  
Beberapa `console.log` debug masih ada di production code:

```javascript
// audio.js
console.log("[audio] play() OK");
console.log("[audio] unlocking via AudioContext...");
console.log("[audio] unlocked, syncing...");
console.log("[radio] track ended, requesting next...");

// utils.js
console.log("Cover Color Extracted:", bestR, bestG, bestB); // ← Expose internal data
```

Khususnya `console.log("Cover Color Extracted:", ...)` mengekspos informasi internal yang tidak perlu ke user mana pun yang membuka DevTools.

**Solusi:** Ganti semua `console.log` dengan logger conditional:

```javascript
// utils.js
const DEBUG = false; // Set true only in dev
const log = (...args) => DEBUG && console.log(...args);

// Gunakan: log("[audio] play() OK");
```

---

### FE-024 — UX: Tidak Ada Konfirmasi Saat Hapus Unduhan
**Severity:** 🟢 LOW  
**Kategori:** UX, Destructive Action Safety

**Dampak:**  
Action "Hapus Unduhan" di action sheet langsung mengirim `DELETE_DOWNLOAD` ke server tanpa konfirmasi. Ini adalah destructive action yang tidak dapat di-undo.

**Lokasi File:** `web/static/js/events/player-events.js`

```javascript
dom.actionDelete.addEventListener("click", () => {
    if (store.userRole !== "admin") return;
    if (window.pendingTrack) {
        wsSend(WS_ACTIONS.DELETE_DOWNLOAD, window.pendingTrack); // ← Langsung hapus!
    }
    hideActionModal();
});
```

**Solusi:** Tambahkan konfirmasi inline di action sheet:

```javascript
dom.actionDelete.addEventListener("click", () => {
    if (store.userRole !== "admin") return;
    
    // Ubah tombol menjadi konfirmasi
    dom.actionDelete.textContent = "Konfirmasi Hapus?";
    dom.actionDelete.style.background = "rgba(239, 68, 68, 0.2)";
    
    dom.actionDelete.addEventListener("click", function confirm() {
        if (window.pendingTrack) wsSend(WS_ACTIONS.DELETE_DOWNLOAD, window.pendingTrack);
        hideActionModal();
        dom.actionDelete.removeEventListener("click", confirm);
    }, { once: true });
});
```

---

## MATRIKS TEMUAN

| ID | Judul | Severity | Kategori |
|---|---|---|---|
| FE-001 | `ITUNES_API_URL` tidak didefinisikan | 🔴 CRITICAL | State Bug, Runtime Error |
| FE-002 | Service Worker Cache Stale — Deployment Bypass | 🔴 CRITICAL | SW, Cache Strategy |
| FE-003 | Duplicate Event Listener — Lyric Offset Bug | 🔴 CRITICAL | State Bug, Event |
| FE-004 | `renderSheetLyrics` Scroll Listener Memory Leak | 🟠 HIGH | Memory Leak |
| FE-005 | Tidak Ada Focus Trap di Modal/Sheet | 🟠 HIGH | Accessibility |
| FE-006 | Login Form Tanpa `<label>` | 🟠 HIGH | Accessibility |
| FE-007 | Volume Slider Tanpa Aria Attributes | 🟠 HIGH | Accessibility |
| FE-008 | Dark Mode Only — Tidak Ada `color-scheme` | 🟠 HIGH | Dark Mode |
| FE-009 | Lirik Dipotong Paksa di Mobile | 🟠 HIGH | Responsive, UX |
| FE-010 | CSS `!important` War di Desktop/Landscape | 🟡 MEDIUM | Responsive, Maintainability |
| FE-011 | Swipe Gesture Toast Mengganggu untuk Client | 🟡 MEDIUM | UX, Navigation |
| FE-012 | Login Error Tidak Clear Saat Typing | 🟡 MEDIUM | Form Validation, UX |
| FE-013 | Enter dari Username Field Tidak Submit | 🟡 MEDIUM | Form Validation |
| FE-014 | `store.status` Optimistic Tanpa Rollback | 🟡 MEDIUM | State Bug |
| FE-015 | Tab Panel Tanpa `aria-controls`/`tabpanel` | 🟡 MEDIUM | Navigation, Accessibility |
| FE-016 | Inline Style Berlebihan di HTML | 🟡 MEDIUM | UI Consistency |
| FE-017 | Tidak Ada Skeleton untuk Queue & Radio | 🟡 MEDIUM | Loading, UX |
| FE-018 | Fake Beat Loop Tanpa Reduced Motion Support | 🟡 MEDIUM | Animation, Accessibility |
| FE-019 | PWA Manifest Hanya Satu Icon | 🟡 MEDIUM | PWA |
| FE-020 | `favorites.js` File Kosong | 🟡 MEDIUM | Widget Tree, Tech Debt |
| FE-021 | Hashtag Color Random Setiap Sesi | 🟡 MEDIUM | Rebuild, UI Consistency |
| FE-022 | Truncate Artis Hardcoded, Duplikat | 🟢 LOW | UX, Code Smell |
| FE-023 | `console.log` di Production | 🟢 LOW | Code Smell |
| FE-024 | Hapus Unduhan Tanpa Konfirmasi | 🟢 LOW | UX |

---

## REKOMENDASI PRIORITAS

### 🔴 Immediate (sebelum production)
1. **FE-001** — Definisikan `ITUNES_API_URL` di `config.js`. Tanpa ini, cover art tidak pernah bisa dimuat dari iTunes — semua user hanya mendapat thumbnail YouTube beresolusi rendah.
2. **FE-003** — Hapus duplicate event listener pada lyric offset. Ini menyebabkan offset melompat 2x setiap klik.
3. **FE-002** — Fix Service Worker cache mismatch agar deployment baru langsung terasa oleh semua user.

### 🟠 Short-term (sprint pertama)
4. **FE-005** — Implementasikan focus trap pada semua modal/sheet (requirement aksesibilitas fundamental).
5. **FE-006, FE-007** — Tambahkan `<label>` pada login form dan aria attributes pada volume slider.
6. **FE-008** — Tambahkan `color-scheme: dark` agar browser controls sinkron dengan dark theme.
7. **FE-009** — Perbaiki lyrics display di mobile agar tidak terpotong.

### 🟡 Medium-term (sprint berikutnya)
8. **FE-010, FE-016** — Refactor CSS `!important` war dan ekstrak inline style.
9. **FE-004** — Pindahkan scroll listener dari render function ke init function.
10. **FE-014** — Tambahkan rollback mechanism untuk optimistic state update.
11. **FE-015** — Lengkapi ARIA untuk tab navigation.
12. **FE-017, FE-018, FE-021** — Skeleton loader, reduced motion support, deterministik color hash.

### 🟢 Long-term (backlog)
13. **FE-011, FE-012, FE-013** — UX polish: swipe toast, error clearing, Enter submission.
14. **FE-019** — Multi-size PWA icons.
15. **FE-020, FE-022, FE-023, FE-024** — Housekeeping: hapus file kosong, konsolidasi helper, remove console.log, konfirmasi destructive action.

---

## CATATAN ARSITEKTUR FRONTEND

**Pola Global State (`store`):**  
Menggunakan plain JS object yang di-mutasi langsung dari mana saja. Ini rentan terhadap state corruption pada aplikasi besar. Pertimbangkan pola immutable state atau minimal event-driven mutation untuk LunaWave v2.

**Render Functions sebagai "Dirty Render":**  
Semua fungsi `renderXxx()` melakukan full DOM update setiap kali dipanggil. `renderDiscoverList()` sudah mengimplementasikan keyed DOM reconciliation yang cukup baik (reuse element yang ada). Namun `renderSheetLyrics()` masih menggunakan `innerHTML =` yang menyebabkan full re-create DOM setiap lyric tick. Untuk 60 fps animations, ini perlu dioptimalkan ke in-place text update.

**Bundle Architecture:**  
Satu file `bundle.js` untuk semua JS. Pada scale jutaan user, code splitting per route (home, search, discover) akan signifikan mengurangi Time to Interactive untuk tab yang tidak diakses.

**Tidak Ada TypeScript / Type Safety:**  
Seluruh codebase vanilla JS tanpa type annotation. `TrackInfo` object (yang sering di-pass antar fungsi) tidak ada validasi schema di layer frontend. Pertimbangkan JSDoc types minimal atau migrasi ke TypeScript untuk codebase yang akan berkembang.
