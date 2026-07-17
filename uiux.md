# Audit UI/UX — Tab Discover (Lunawave)

Berdasarkan implementasi aktual: `index.html` (struktur), `discover-tab.js`, `discover-personalize.js`, `discover-cards.css`.

---

## 1. Visual Hierarchy

Halaman menumpuk **8 section vertikal** tanpa penekanan: Taste Spectrum → Filter Bar → Untuk Kamu → Karena Kamu Suka → Belum Pernah Kamu Dengar → Jelajahi Artis → Jelajahi Genre → Baru Diputar → Favorit → Tersimpan Lokal. Semua section punya bobot visual yang hampir sama (label kecil + baris card/list), jadi tidak ada satu focal point. Ini melanggar prinsip **hierarchy through contrast** — kalau semuanya ditonjolkan sama rata, tidak ada yang benar-benar menonjol (efek "semua penting = tidak ada yang penting").

Section "Untuk Kamu" (rekomendasi personalisasi paling berharga) dan "Tersimpan Lokal" (housekeeping teknis) mendapat perlakuan visual yang setara: label kecil sama, tanpa hero/lead visual besar. Padahal secara *information value*, rekomendasi personal seharusnya mendapat area/skala visual lebih besar (mirip hero carousel di Spotify/Apple Music Home).

Hashtag cloud (`discover-artists`, `discover-genres`) menggunakan **ukuran font dinamis berbasis click_count** (`getHashtagColor`, `bonusSize`) — niatnya membuat hierarchy otomatis, tapi warnanya `hsl(random)` per hashtag, bukan berdasarkan skala data yang konsisten. Ini menciptakan noise visual: browser mata harus memproses variasi warna + ukuran acak sekaligus, padahal seharusnya hanya satu variabel (ukuran) yang membawa makna (Gestalt — *principle of uniform connectedness* terganggu karena warna tidak konsisten mengelompokkan sesuatu, ia acak per string).

**Verdict:** urutan informasi secara garis besar cukup logis (personalisasi dulu, browsing manual belakangan), tapi tidak ada anchor visual yang jelas di atas fold — semuanya rata.

---

## 2. Layout

- **Section terlalu banyak untuk satu scroll panjang** — 10 blok konten berturutan tanpa card besar / grouping visual (tidak ada card container yang membedakan satu section dari yang lain, hanya `.section-label` teks kecil sebagai pemisah). Whitespace antar-section terlihat seragam kecil (`var(--s3)`/`s4`), sehingga secara Gestalt **proximity** semua section terasa "menyatu" jadi satu blok panjang, padahal secara semantik mereka adalah kategori yang berbeda.
- **Row Recent/Favorite/Cached (`.sr-item`)** dirender sebagai list vertikal penuh (bukan card horizontal seperti artist row), sehingga tiga section terakhir jadi *long list* murni tanpa cover besar — kontras drastis dengan section atas yang pakai card 118–150px. Ini inkonsistensi pola visual dalam satu halaman: bagian atas "discovery browsing" (card grid horizontal), bagian bawah "library management" (list linear) — pengguna harus switch mental model di tengah scroll.
- **Filter bar sticky** (`position: sticky; top: 0`) hanya mengontrol 2 dari ~5 row card (`row-for-you`, `row-genre-affinity`, `row-unheard`); Jelajahi Artis/Genre serta Recent/Favorite/Cached tidak terpengaruh filter tapi tetap ada di bawah filter bar yang sama — ini **misleading affordance**: pengguna bisa mengira filter kategori/dekade berlaku untuk seluruh halaman, padahal cuma 3 row.
- Card 118px (mobile) / 150px (≥760px) untuk artist — proporsi cover 1:1 konsisten, itu baik.
- Tidak ada max-width/container constraint terlihat di `#tab-discover` untuk layar lebar — berisiko row card meregang atau whitespace kanan-kiri tidak terkontrol di desktop besar (tidak bisa dipastikan tanpa lihat container global, tapi tidak ada bukti pembatasan lebar di file yang direview).

---

## 3. Typography

- Struktur type scale terpakai konsisten (`--t-xs, --t-sm, --t-md, --t-2xl` dst) — baik untuk maintainability.
- Tapi **hashtag pill** memakai font-size dinamis inline (`14px–28px`) berdasarkan `click_count` — ini di luar type-scale sistem (`--t-*` tokens), menciptakan ukuran font yang tidak konsisten dengan skala tipografi lain di halaman. Risiko: kombinasi lebar teks acak + ukuran acak menyulitkan alignment baseline pada layout flex-wrap.
- Label section (`section-label`, `label-text`) semuanya kecil dan seragam — baik untuk menjaga row list tetap ringkas, tapi berarti section "Untuk Kamu" dan "Tersimpan Lokal" secara tipografis tidak dibedakan sama sekali (lihat poin Visual Hierarchy).
- Artist name di card (`.artist-card-name`) di-truncate 1 baris (`white-space: nowrap; text-overflow: ellipsis`) tanpa `title` attribute pada elemen — nama artis panjang tidak bisa dibaca penuh tanpa interaksi lanjut (klik untuk buka detail sheet). Minor, tapi mengurangi *scanability*.

---

## 4. Color & Visual Design

- **Masalah signifikan:** dua sistem warna berbeda dipakai untuk hal yang konseptual serupa (genre/kategori tag):
  - `GENRE_COLORS` di `discover-personalize.js` — palet kuratif tetap, terikat brand (`--g-pop`, `--g-rock`, dst).
  - `getHashtagColor()` di `discover-tab.js` — `hsl(random)` per string, disimpan di cache in-memory, **berubah setiap reload halaman** (karena `_hashtagColors` object direset saat script reload).

  Konsekuensi: warna hashtag artist/genre di "Jelajahi Artis/Genre" **tidak konsisten antar sesi**, padahal warna genre yang sama di Taste Spectrum bersifat tetap. Ini melanggar **konsistensi** (Nielsen Heuristic #4) — pengguna yang mengasosiasikan warna tertentu dengan genre favorit mereka di Taste Spectrum tidak akan menemukan warna yang sama di hashtag cloud.
- Warna acak juga tidak menyampaikan makna — dalam Gestalt, warna seharusnya dipakai untuk *grouping* (menyatukan/differensiasi kategori). Random hue tidak melakukan itu; ia justru menambah **visual noise** tanpa fungsi.
- Badge (`badge-match`, `badge-new`) sudah baik: warna solid accent untuk match%, outline netral untuk "Baru" — kontras & makna jelas.
- Tidak ditemukan referensi eksplisit dark-mode alternate palette di file yang direview; asumsi UI ini dark-mode-only (`rgba(14,14,18,.92)` di filter-bar, dsb). Jika benar demikian, tidak ada masalah — tapi berarti tidak ada dark/light toggle audit yang relevan di sini.

---

## 5. Card Design

- **Artist card** (`.artist-card`): cover persegi, nama, meta genre, badge opsional. Affordance klik: card adalah elemen `<button>` (baik secara semantik dan aksesibilitas), tapi **secara visual tidak ada indikasi kuat "bisa diklik"** — tidak ada shadow, border highlight, atau elevation di state normal. Hanya scale transform 1.06x di hover (`transform: scale(1.06)`), yang tidak terlihat di layar sentuh/non-hover (misal via keyboard sebelum fokus, device tanpa mouse-hover reveal cepat).
- **Undiscovered card** (`Belum Pernah Kamu Dengar`) sengaja di-desaturasi (`grayscale(.85) brightness(.75)`) sampai hover/touch. Ini pola *progressive disclosure* yang menarik secara konsep (mendorong eksplorasi), tapi berisiko disalahartikan sebagai **elemen disabled/tidak aktif** — konvensi UI umum: abu-abu/desaturasi = tidak bisa diklik. Ini bertentangan langsung dengan affordance konvensional (kontradiksi terhadap *Jakob's Law* — pengguna datang dengan ekspektasi dari aplikasi lain).
- **List item (`.sr-item`)** dipakai untuk Recent/Favorite/Cached — punya thumbnail kecil kotak + tombol "more" (dots-vertical). Namun **seluruh row `.sr-item` tidak punya cursor:pointer/affordance style eksplisit di CSS yang direview** kecuali lewat class `.current`/`.playing`; apakah klik pada row memutar lagu tidak eksplisit terlihat dari CSS (perlu event listener JS lain yang tidak termasuk dalam file ini) — potensi *hidden interaction*, tidak terverifikasi dari kode yang tersedia sehingga saya tandai sebagai risiko, bukan kepastian.
- Hover state pada card cukup (scale + brightness track), tapi **tidak ada focus-visible state khusus untuk `.sr-item`** (hanya `.artist-card`, `.chip`, `.segmented button` yang punya `outline` on focus). Baris Recent/Favorite/Cached — yang jumlahnya berpotensi paling banyak dan paling sering dinavigasi via keyboard — justru tidak mendapat focus indicator.

---

## 6. Navigation

- Filter (kategori: Semua/Solo/Band; dekade: chip per tahun) hanya scoped ke 3 dari ~6 grup konten (lihat poin Layout) — **discoverability lemah**: tidak ada indikasi visual bahwa filter tidak berlaku ke section di bawahnya.
- Dekade chip di-generate dinamis dari union semua artist (`buildDecadeChips`) — jumlah chip bisa banyak & di-scroll horizontal tanpa panah/indikator "ada lebih banyak di kanan" (`overflow-x: auto` + hidden scrollbar). Ini **Hick's Law** issue kalau daftar dekade panjang: waktu keputusan makin lama karena tidak ada scan cepat (hidden scrollbar tanpa indikator gradient-fade juga membuat pengguna tidak tahu ada opsi tersembunyi — poor discoverability of overflow).
- Klik pada hashtag pill (artist/genre) langsung men-trigger `wsSend('enqueue_artist_songs', ...)` dan **pindah tab ke Home** (`switchTab('home')`) — perpindahan konteks otomatis tanpa konfirmasi. Bagi pengguna non-admin, klik menghasilkan toast "Hanya admin yang bisa memutar musik" — artinya **elemen interaktif terlihat sama untuk semua role**, tapi hanya berfungsi untuk admin. Ini melanggar **Nielsen Heuristic #1 (visibility of system status)** dan **#5 (error prevention)** — non-admin tidak tahu di awal bahwa hashtag itu tidak akan berfungsi untuknya sampai mereka mengklik dan gagal.
- Sama untuk `playAllFromArtistDetail` dan artist card klik → buka sheet (ini oke, tidak butuh admin) tapi "Play All" di dalam sheet juga admin-only dengan pola gagal-baru-tahu yang sama.

---

## 7. UX

- **Cognitive load tinggi** karena banyaknya section berbeda jenis (spectrum bar, filter, 3 card-row personalisasi, 2 hashtag cloud, 3 list linear) — total 9 unit konten berbeda pola interaksi dalam satu tab. Pengguna harus mempelajari 3 pola UI berbeda (segmented control, card carousel, list item) hanya untuk satu tab "Discover".
- **Role-gated interaction tanpa visual differentiation** (dibahas di atas) adalah masalah UX paling konkret: sistem tidak transparan terhadap kemampuan pengguna saat ini — pengguna non-admin mengalami *dead click* berulang di banyak titik (hashtag artist, hashtag genre, play-all di artist detail).
- **Loading state:** ada skeleton box di HTML awal (baik — mengurangi perceived latency), tapi begitu `store.discover_recent.length === 0`, empty-state teks ("Belum ada riwayat") langsung menggantikan skeleton tanpa transisi — cukup, tidak masalah besar.
- **Empty state artist detail sheet** ("Artis tidak ditemukan") — sudah ditangani, baik.
- Tidak ada bukti *undo* atau konfirmasi saat "Play All" mengganti antrian pemutaran yang sedang berjalan — berpotensi mengganggu (pengguna kehilangan antrian tanpa peringatan), tapi ini asumsi behavior backend yang tidak sepenuhnya terverifikasi dari front-end saja.

---

## 8. Information Architecture

Urutan saat ini:
1. Taste Spectrum (statistik)
2. Filter bar
3. Untuk Kamu (rekomendasi)
4. Karena Kamu Suka [Genre]
5. Belum Pernah Kamu Dengar
6. Jelajahi Artis (hashtag cloud, tanpa filter)
7. Jelajahi Genre (hashtag cloud, tanpa filter)
8. Baru Diputar (recent, list)
9. Favorit (list)
10. Tersimpan Lokal (cache, list)

Ini sudah **cukup mendekati praktik terbaik** (personalisasi → eksplorasi luas → riwayat), namun ada dua masalah:

- **"Jelajahi Artis/Genre" (hashtag cloud) letaknya di antara rekomendasi personalisasi (bercard) dan riwayat (list)** — secara pola interaksi ia berbeda dari keduanya (pill-cloud, bukan card atau list), memutus alur visual/pola. Sebaiknya hashtag cloud diletakkan **setelah seluruh blok personalisasi (poin 3–5) tapi sebagai satu grup "Jelajah" bersama filter**, karena secara fungsi sama-sama alat eksplorasi manual (bukan riwayat).
- **Recently Played di tab Discover vs Home**: kode menunjukkan `renderRecentRow()` juga dipakai di Home (`home-recent-list`). Duplikasi "recently played" antara Home dan Discover berpotensi membingungkan pengguna soal *"di mana saya harus mencari riwayat saya?"* — kalau Home sudah punya recent-row, section "Baru Diputar" di Discover jadi redundant secara IA (redundansi konten menaikkan cognitive load tanpa menambah value baru).

**Rekomendasi urutan:**
1. Taste Spectrum + Filter (statistik & kontrol)
2. Untuk Kamu / Karena Kamu Suka / Belum Pernah Dengar (personalisasi, di-filter)
3. Jelajahi Artis & Genre (eksplorasi manual, di luar filter, tapi diberi label eksplisit "Semua Artis/Genre — tidak difilter" agar jelas)
4. Favorit (higher priority daripada Recent — ini koleksi curated pengguna, lebih actionable)
5. Baru Diputar — **pertimbangkan hapus dari Discover** kalau sudah ada di Home, atau gabungkan sebagai satu section referensi silang.
6. Tersimpan Lokal (paling teknis, cocok di posisi terakhir).

---

## 9. Mobile Readiness

- CSS sudah punya breakpoint mobile-first eksplisit (`@media (min-width: 760px)` mengubah card jadi grid & filter-bar jadi row) — arsitektur CSS mendukung adaptasi mobile.
- Card-row pakai `overflow-x: auto` + `scroll-snap-type: x proximity` — pola swipe-carousel yang familiar di mobile, baik.
- Namun tap-target kategori/dekade chip (`padding: 6-7px 14-16px`) mendekati/border minimum 44×44px yang direkomendasikan untuk touch target (Fitts's Law) — chip kecil dengan padding vertikal ~13-14px total tinggi bisa jadi <36px, berisiko mis-tap di layar sentuh.
- Hashtag cloud dengan ukuran font dinamis (14–28px) tidak reliable di mobile — ukuran klik-area pill mengikuti ukuran teks yang variatif, sehingga pill kecil (klik jarang) punya target sentuh yang jauh lebih kecil dari pill populer — ini justru mempersulit klik pertama kali untuk artis yang belum familiar (padahal itu tujuan discovery).

---

## 10. Accessibility

- **Positif:** `aria-label="More"` pada tombol icon-only sudah ada; `focus-visible` outline diterapkan pada `.segmented button`, `.chip`, `.artist-card`.
- **Negatif — kontras warna acak tak terverifikasi:** `getHashtagColor()` men-generate `hsl(hue random, sat 60-90%, light 50-70%)` tanpa pengecekan kontras terhadap background. Ada risiko nyata sejumlah kombinasi hue/lightness menghasilkan kontras di bawah WCAG AA (4.5:1) terhadap background gelap/terang — ini bug aksesibilitas struktural karena warnanya tidak diaudit sama sekali (random by design berarti tidak reproducible untuk testing kontras).
- **Color dependency:** Genre pada Taste Spectrum dibedakan **hanya lewat warna** (segmen bar + dot legend) — walau ada label teks di legend (baik, jadi tidak 100% color-only), tapi bar-nya sendiri (`.taste-seg`) tidak punya pattern/texture pembeda, hanya warna. Untuk pengguna color-blind, legend teks menyelamatkan makna, jadi ini masih dapat diterima (Nielsen: tidak 100% bergantung warna karena ada teks penyerta).
- **Keyboard navigation:** `.sr-item` (Recent/Favorite/Cached rows) tidak memiliki `tabindex`/role button eksplisit di markup yang terlihat — jika interaksinya bergantung pada listener JS di elemen div biasa (bukan button/anchor), maka **tidak bisa diakses via keyboard** sama sekali. Ini pelanggaran serius terhadap operability (WCAG 2.1.1).
- **Icon-only button** (`sr-more-btn`, dots-vertical) sudah punya aria-label — baik.
- Ukuran teks dinamis hashtag (14-28px) tidak akan terpengaruh oleh browser zoom/user font-size preference dengan predictable karena base size dihitung dari px absolut, bukan rem — berpotensi tidak scale dengan pengaturan aksesibilitas teks pengguna.

---

### Catatan verifikasi (revisi setelah cek ulang kode)

Klaim awal bahwa "Favorit" dan "Baru Diputar" menampilkan lagu tanpa batas **tidak akurat** — sudah dicek langsung:

- `server/handlers/ws_discovery.py` baris 59-61: `ds.get_recent(15)`, `ds.get_favorites(15)`, `ds.get_cached(15)`.
- `services/discover_service.py`: query SQL-nya memang pakai `ORDER BY ... LIMIT ?` — jadi ketiga section ini **sudah dibatasi backend ke 15 lagu**, bukan unlimited.

Yang **benar-benar tidak dibatasi** adalah dua section lain di baris yang sama:

- `ds.get_featured_artists(100)` dan `ds.get_featured_genres(100)` — masing-masing menarik **100 item**.
- Di frontend, `.hashtag-cloud-container` (`cards.css` baris 463-470) hanya `display:flex; flex-wrap:wrap` — **tidak ada max-height, overflow control, atau pagination apa pun**. Kalau data di DB penuh, "Jelajahi Artis" + "Jelajahi Genre" bisa merender **200 pill sekaligus**, bikin panjang halaman meledak tanpa kendali.

Jadi gejala "list kepanjangan tanpa batasan" itu nyata, tapi lokasinya di **Jelajahi Artis/Genre**, bukan di Favorit/Baru Diputar. Favorit/Baru Diputar punya masalah berbeda: sudah dibatasi 15, tapi tetap dirender sebagai **list vertikal penuh tanpa preview/collapse**, sehingga 3 section × 15 baris = 45 baris berturutan tetap terasa panjang secara persepsi meski datanya sudah dibatasi.

---

## 11.1 Solusi Konkret (untuk menaikkan skor Layout, Discoverability, Cognitive Load)

### Fix 1 — Batasi render hashtag cloud + progressive disclosure (Critical → langsung fix)

**Backend** (`server/handlers/ws_discovery.py`): turunkan angka fetch mentah, tidak perlu 100 sekaligus:
```python
ds.get_featured_artists(30),
ds.get_featured_genres(30),
```

**Frontend** (`discover-tab.js`): render dengan cap + tombol expand, bukan sekadar mengurangi angka:
```javascript
const HASHTAG_VISIBLE_CAP = 16;

function renderHashtagCloud(container, items, buildPillHTML) {
    if (!container) return;
    if (!items || items.length === 0) { container.innerHTML = ''; return; }
    const visible = items.slice(0, HASHTAG_VISIBLE_CAP);
    const rest = items.slice(HASHTAG_VISIBLE_CAP);
    container.innerHTML = visible.map(buildPillHTML).join('') +
        (rest.length
            ? `<button class="hashtag-more-btn" data-remaining="${rest.length}">+${rest.length} lainnya</button>`
            : '');
}
```
Klik "+N lainnya" baru render sisanya (append, bukan reload halaman). Ini menerapkan **Progressive Disclosure**: pengguna baru lihat detail/volume penuh saat mereka minta, bukan dipaksa scroll semua di awal (mengurangi Cognitive Load, sekaligus benerin masalah *tap-target hilang di scroll horizontal* karena sekarang jadi grid wrap terkontrol, bukan cloud tak terbatas).

Sekalian pakai kesempatan ini benerin **warna random** (temuan Critical/High sebelumnya) — ganti `getHashtagColor()` dari `hsl(random)` ke palet tetap berbasis hash string:
```javascript
const HASHTAG_PALETTE = ['var(--g-pop)','var(--g-rock)','var(--g-indopop)','var(--g-jazz)','var(--g-electronic)','var(--g-other)'];
function getHashtagColor(hashtag) {
    let hash = 0;
    for (let i = 0; i < hashtag.length; i++) hash = (hash * 31 + hashtag.charCodeAt(i)) >>> 0;
    return HASHTAG_PALETTE[hash % HASHTAG_PALETTE.length];
}
```
Ini deterministik (warna sama tiap reload) dan sudah pasti lolos kontras karena diambil dari token warna brand yang sudah didesain, bukan `hsl(random)`.

### Fix 2 — Preview cap untuk Recent/Favorit/Cached (High → langsung fix)

Backend tetap 15 (sudah tepat, tidak perlu diubah — 15 item adalah buffer wajar untuk fitur "lihat semua" nantinya). Yang diubah cuma **cara render**:

```javascript
const LIST_PREVIEW_CAP = 5;

function renderTrackList(container, tracks, itemHTMLFn, emptyHTML) {
    if (!container) return;
    if (!tracks || tracks.length === 0) { container.innerHTML = emptyHTML; return; }
    const preview = tracks.slice(0, LIST_PREVIEW_CAP);
    const rest = tracks.length - preview.length;
    container.innerHTML = preview.map(itemHTMLFn).join('') +
        (rest > 0 ? `<button class="list-expand-btn" data-remaining="${rest}">Lihat Semua (${tracks.length})</button>` : '');
    container.querySelector('.list-expand-btn')?.addEventListener('click', function () {
        container.innerHTML = tracks.map(itemHTMLFn).join('');
        if (typeof window.loadLazyCovers === 'function') window.loadLazyCovers();
    }, { once: true });
}
```

Dampak: 3 section × 15 baris (45 baris) jadi 3 section × 5 baris (15 baris) di initial render — panjang halaman turun signifikan tanpa kehilangan data, dan pengguna yang memang mau lihat semua tetap bisa satu klik. Ini langsung menjawab kritik *Layout* (section terlalu padat/panjang) dan *Hick's Law* (jumlah pilihan yang harus di-scan berkurang di awal).

**Setelah kedua fix ini diterapkan:**
- Layout: 5 → 7-8 (panjang halaman terkendali, section tidak lagi menyatu jadi satu scroll raksasa)
- Discoverability: 5 → 7 (tombol "lihat semua"/"lainnya" eksplisit, bukan cloud tak berujung)
- Visual Design: 4 → 6-7 (warna hashtag konsisten & deterministik)

Catatan jujur: skor **Overall UI/UX 10/10 tidak realistis dicapai hanya dari dua fix ini** — item Critical lain di roadmap (role-gated affordance tanpa disabled state, kemungkinan `.sr-item` tidak keyboard-accessible) tetap harus dibereskan juga karena itu menyentuh aksesibilitas & kejujuran sistem (Nielsen #1/#5), bukan sekadar panjang halaman. Kalau seluruh item Critical + High di roadmap (bagian 12) diterapkan bersamaan, skor gabungan realistis naik ke kisaran **8.5-9/10** — angka 10/10 sendiri lebih cocok jadi arah/target daripada klaim pasti tercapai, karena selalu ada ruang iterasi (mis. riset pengguna nyata, A/B testing hierarchy) yang belum bisa dipastikan dari code review saja.

---

### Fix 3 — `.sr-item` (Recent/Favorit/Cached) tidak keyboard-accessible + silent failure untuk non-admin (Critical, verifikasi baru)

Verifikasi ulang di `click-delegation-events.js` baris 19-32 mengonfirmasi **dua bug sekaligus**, lebih parah dari dugaan awal:

1. `.sr-item` cuma didengarkan lewat `document.addEventListener("click", ...)` pada `<div>` polos — tidak ada `tabindex`, `role`, atau `keydown` handler. **Sama sekali tidak bisa diakses keyboard.**
2. Kalau `store.userRole !== "admin"`, blok `if (store.userRole === "admin") { wsSend(...) }` membuat klik **tidak melakukan apa-apa** — tidak ada `showLogToast` sama sekali. Ini silent failure, lebih buruk dari hashtag pill yang setidaknya kasih toast.

**Fix markup** (`discover-tab.js`, di semua template `.sr-item` — recent/favorites/cached, 3 tempat):
```javascript
return `
<div class="sr-item" tabindex="0" role="button"
     aria-label="Putar ${escapeHtml(title)} — ${escapeHtml(artistName)}"
     data-vid="${escapeHtml(track.video_id || '')}" data-track-str='${trackStr}'>
    ...
</div>`;
```

**Fix interaksi** (`click-delegation-events.js`) — tambah keyboard equivalent + feedback yang konsisten dengan pola hashtag pill:
```javascript
function handleSrItemActivate(srItem) {
    const trackStr = srItem.dataset.trackStr || srItem.dataset.searchTrackStr;
    if (!trackStr) return;
    try {
        const track = JSON.parse(trackStr);
        if (store.userRole === "admin") {
            wsSend("play_track", track);
        } else if (typeof showLogToast === "function") {
            showLogToast("Hanya admin yang bisa memutar musik");
        }
    } catch (err) { console.error(err); }
}

function initClickDelegationEvents() {
    document.addEventListener("click", (e) => {
        // ...(moreBtn block tetap sama)...
        const srItem = e.target.closest(".sr-item");
        if (srItem) { handleSrItemActivate(srItem); return; }
        // ...(disc-card/fav-card block tetap sama)...
    });

    // BARU: keyboard equivalent
    document.addEventListener("keydown", (e) => {
        if (e.key !== "Enter" && e.key !== " ") return;
        const srItem = e.target.closest(".sr-item");
        if (srItem) { e.preventDefault(); handleSrItemActivate(srItem); }
    });
}
```
Sekarang perilaku non-admin konsisten di semua titik interaksi (hashtag, Play All, track row) — selalu ada toast, tidak ada dead click yang diam-diam gagal.

### Fix 4 — Filter bar scope tidak jelas (High)

Tambahkan sub-label eksplisit di bawah filter bar agar jelas cakupannya, dan visually pisahkan dari section yang tidak difilter:
```html
<div class="filter-bar" id="discover-filter-bar">
    <div class="segmented" id="kategori-toggle">...</div>
    <div class="chip-row" id="decade-chips">...</div>
</div>
<div class="filter-scope-hint">Filter berlaku untuk rekomendasi di bawah ini</div>
```
```css
.filter-scope-hint {
    font-size: var(--t-xs);
    color: var(--text-3);
    padding: 0 var(--s5) var(--s2);
    font-style: italic;
}
```
Alternatif lebih kuat: pindahkan filter bar agar tidak `position: sticky` mengambang di atas seluruh halaman, cukup sticky relatif terhadap 3 row personalisasi saja (bungkus filter + 3 row dalam satu `<div class="filterable-section">` dengan `position: sticky` di container itu, bukan global).

### Fix 5 — Undiscovered card terlihat seperti disabled (Medium)

Ganti treatment dari grayscale penuh ke indikator non-destruktif — cukup andalkan badge "Baru" yang sudah ada, hilangkan filter grayscale:
```css
/* SEBELUM */
.artist-card.undiscovered .artist-card-art img {
    filter: grayscale(.85) brightness(.75);
}

/* SESUDAH — ganti ke ring accent tipis, tetap warna asli */
.artist-card.undiscovered .artist-card-art {
    box-shadow: 0 0 0 2px var(--accent-alpha);
}
```
Card tetap terlihat "hidup"/klikable secara konvensional, tapi tetap dibedakan visualnya dari card biasa lewat ring, bukan lewat pola yang secara konvensi berarti "tidak aktif".

### Fix 6 — Redundansi "Baru Diputar" dengan Home (Medium)

Karena `renderRecentRow()` di Home dan section "Baru Diputar" di Discover mengambil sumber data yang sama (`store.discover_recent`), ganti section di Discover jadi ringkas + link silang, bukan duplikat penuh:
```html
<div class="section-label-row">
    <span class="label-text">Baru Diputar</span>
    <button class="section-link-btn" onclick="switchTab('home')">Lihat di Home →</button>
</div>
```
Hapus daftar penuh dari Discover, atau tampilkan maksimal 3 item sebagai preview saja.

### Fix 7 — Tap target chip terlalu kecil (Medium)

```css
.chip, .segmented button {
    min-height: 44px;      /* tambahan */
    display: inline-flex;  /* tambahan, supaya align-center bekerja dgn min-height */
    align-items: center;
}
```

### Fix 8 & 9 — Overflow indicator + title attribute (Low)

```css
.chip-row, .card-row {
    mask-image: linear-gradient(to right, black 92%, transparent 100%);
}
```
```javascript
// di artistCardHTML()
<div class="artist-card-name" title="${escapeHtml(a.nama)}">${escapeHtml(a.nama)}</div>
```

---

**Ringkasan cakupan fix sekarang:** 2 Critical (role-gated affordance + keyboard/silent-failure `.sr-item`) sudah ada solusi kode siap pakai, 2 High (hashtag unbounded + filter scope) sudah ada solusi, 3 Medium (undiscovered treatment, redundansi, tap target) sudah ada solusi, 2 Low sudah ada solusi. Yang tersisa murni riset/subjektif (mis. apakah urutan IA final butuh A/B test dengan user asli) — itu di luar jangkauan code review.

---

## 11. UX Problems (Ringkasan)

- **Dead click / misleading affordance:** hashtag artist/genre & tombol Play All tampil sama untuk semua role tapi hanya berfungsi untuk admin.
- **Visual clutter:** warna hashtag random tidak konsisten antar reload, menambah noise tanpa fungsi.
- **Inkonsistensi pola card vs list** dalam satu halaman tanpa transisi visual yang jelas.
- **Redundant content:** "Baru Diputar" kemungkinan duplikat dengan recent-row di Home.
- **Scope filter yang tidak jelas** — filter kategori/dekade hanya berlaku ke 3 dari 6 grup konten tanpa indikasi visual.
- **Potential keyboard-inaccessible list rows** (`.sr-item`) jika tidak punya role/tabindex.
- **Weak clickability cue** pada artist card di keadaan non-hover (hanya scale transform di hover, tidak ada persistent affordance).

---

## 12. Improvement Roadmap

### Critical
1. **Role-gated UI tanpa disabled state** (hashtag artist/genre, Play All)
   - Lokasi: `discover-tab.js` (onclick handlers hashtag), `discover-personalize.js` (`playAllFromArtistDetail`)
   - Alasan: melanggar Nielsen #1 & #5 — sistem tidak jujur soal kemampuan aktualnya
   - Dampak: user non-admin frustrasi, trust menurun, dianggap bug bukan restriksi
   - Solusi: render elemen dalam state `disabled`/dimmed + tooltip "Hanya admin" untuk non-admin, jangan tunggu klik untuk memberi tahu
   - Prioritas: **Critical**

2. **Kemungkinan `.sr-item` tidak keyboard-accessible**
   - Lokasi: markup `#discover-recent`, `#discover-favorites`, `#discover-cached`
   - Alasan: WCAG 2.1.1 Operable — semua fungsi harus bisa diakses keyboard
   - Dampak: user keyboard-only/screen reader tidak bisa memutar lagu dari list ini
   - Solusi: tambahkan `role="button" tabindex="0"` + handler `keydown` (Enter/Space), atau ganti ke elemen `<button>` semantik
   - Prioritas: **Critical**

### High
3. **Warna hashtag random tanpa jaminan kontras & tidak persisten**
   - Lokasi: `getHashtagColor()` di `discover-tab.js`
   - Alasan: WCAG kontras tidak terjamin; inkonsistensi Nielsen #4
   - Dampak: sebagian teks pill sulit dibaca; user tidak bisa mengasosiasikan warna dengan genre/artist dari waktu ke waktu
   - Solusi: gunakan palet tetap (hash string → index warna dari array terbatas yang sudah dites kontras), bukan `hsl(random)`
   - Prioritas: **High**

4. **Filter bar scope tidak jelas (hanya 3/6 section terpengaruh)**
   - Lokasi: `applyDiscoverFilters()`, layout index.html baris 337-394
   - Alasan: Nielsen #1 visibility of system status
   - Dampak: user mengira filter berlaku global, bingung kenapa hashtag cloud tidak berubah
   - Solusi: pindahkan filter bar agar visually-scoped hanya di atas 3 row personalisasi (bukan sticky global), atau beri sub-label "Filter berlaku untuk rekomendasi di atas"
   - Prioritas: **High**

### Medium
5. **Section "Belum Pernah Kamu Dengar" pakai desaturasi = terlihat disabled**
   - Lokasi: `.artist-card.undiscovered` CSS
   - Alasan: konvensi UI umum grayscale = tidak aktif (Jakob's Law)
   - Dampak: user skip section ini karena mengira tidak bisa diklik
   - Solusi: ganti treatment ke border/badge subtil ("Baru" badge sudah ada — cukup andalkan itu saja) tanpa grayscale penuh
   - Prioritas: **Medium**

6. **Redundansi "Baru Diputar" dengan Home**
   - Lokasi: index.html baris 398-408 vs `renderRecentRow()`/`home-recent-list`
   - Alasan: IA duplikasi menambah panjang halaman tanpa value baru
   - Dampak: halaman Discover terasa lebih panjang dari perlu, cognitive load naik
   - Solusi: hapus section ini dari Discover atau jadikan preview singkat dengan link "Lihat semua di Home"
   - Prioritas: **Medium**

7. **Tap target chip dekade/kategori mendekati batas minimum**
   - Lokasi: `.chip`, `.segmented button` CSS
   - Alasan: Fitts's Law — target kecil meningkatkan error rate di touch
   - Dampak: mis-tap di mobile
   - Solusi: pastikan total tap-area ≥44×44px (tambah padding vertikal atau min-height)
   - Prioritas: **Medium**

### Low
8. **Tidak ada indikator overflow-scroll pada chip-row / hashtag cloud**
   - Alasan: discoverability — pengguna tidak tahu ada opsi tersembunyi di kanan
   - Solusi: tambahkan fade-gradient di ujung kanan container saat konten overflow
   - Prioritas: **Low**

9. **Artist name truncated tanpa `title` attribute**
   - Solusi: tambah `title="{nama}"` pada `.artist-card-name` untuk native tooltip
   - Prioritas: **Low**

---

## Penilaian

| Aspek | Skor |
|---|---|
| Visual Hierarchy | 5/10 |
| Layout | 5/10 |
| Typography | 6/10 |
| Visual Design | 4/10 |
| Navigation | 5/10 |
| Interaction | 4/10 |
| Discoverability | 5/10 |
| Accessibility | 4/10 |
| **Overall UI** | 5/10 |
| **Overall UX** | 4.5/10 |

**Ringkasan:** Fondasi IA (urutan personalisasi → eksplorasi → riwayat) sudah cukup masuk akal, dan sistem token desain (CSS variables) menunjukkan disiplin di level implementasi. Namun ada dua kelas masalah yang menurunkan skor signifikan: (1) **affordance yang menipu** — elemen tampak interaktif untuk semua orang tapi diam-diam role-gated, dan (2) **inkonsistensi sistem warna/pola visual** antar section (random hue vs curated palette, card vs list) yang membuat halaman terasa seperti gabungan beberapa modul yang dibangun terpisah tanpa unified design pass.
