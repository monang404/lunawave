# LAPORAN AUDIT PERFORMA — LUNAWAVE
**Tim Audit:** Performance Engineer · Senior Backend · Senior Frontend · Database Architect  
**Tanggal:** 2026-07-06  
**Scope:** Full-stack performance audit — backend Python/aiosqlite, frontend JS vanilla, bundle, startup, memory

---

## RINGKASAN EKSEKUTIF

| Kategori | Temuan | Critical | High | Medium |
|---|---|---|---|---|
| Slow Query / DB | 4 | 1 | 2 | 1 |
| Redundant Render / Rebuild | 4 | 1 | 2 | 1 |
| Memory Leak | 2 | 0 | 2 | 0 |
| Blocking UI | 2 | 0 | 1 | 1 |
| Large Bundle / Heavy Dep | 2 | 0 | 1 | 1 |
| N+1 Query | 1 | 1 | 0 | 0 |
| Slow Startup | 1 | 0 | 1 | 0 |
| Expensive Widget | 2 | 0 | 1 | 1 |

**Total: 18 temuan performa yang butuh perbaikan sebelum production release.**

---

## P-01 — CRITICAL: Discover Queries Dieksekusi Secara Serial (N+1 Berganda)

**Severity:** CRITICAL  
**Dampak:** Setiap request `DISCOVER` dari klien menjalankan **5 query SQLite secara berurutan** (serial `await`). Dengan SQLite single-connection, masing-masing query menunggu yang sebelumnya selesai. Pada 100+ klien aktif, setiap tab switch ke home/discover menyebabkan burst query berurutan yang memblok event loop. Estimasi: **+80–200ms latensi** per request dibanding eksekusi paralel.

**Penyebab:** `_build_discover_payload()` memanggil 5 method `await` secara sequential, bukan concurrent.

**Lokasi File:** `server/handlers/ws/discover_handlers.py` baris 17–31

**Kode Bermasalah:**
```python
async def _build_discover_payload(db):
    ds = DiscoverService(db)
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)             # ← query 1
    favorites = await ds.get_favorites(DISCOVER_FAVORITES_LIMIT)   # ← query 2
    cached = await ds.get_cached(DISCOVER_CACHED_LIMIT)             # ← query 3
    featured_artists = await ds.get_featured_artists(...)           # ← query 4
    featured_genres = await ds.get_featured_genres(...)             # ← query 5
    # Total: 5 queries sekuensial = blocking
```

**Solusi:** Gunakan `asyncio.gather()` untuk menjalankan semua query concurrent. Karena aiosqlite dengan single connection serializes writes tapi tidak reads, gather masih memberikan manfaat scheduling.

**Implementasi:**
```python
import asyncio

async def _build_discover_payload(db):
    ds = DiscoverService(db)
    (
        recent,
        favorites,
        cached,
        featured_artists,
        featured_genres,
    ) = await asyncio.gather(
        ds.get_recent(DISCOVER_RECENT_LIMIT),
        ds.get_favorites(DISCOVER_FAVORITES_LIMIT),
        ds.get_cached(DISCOVER_CACHED_LIMIT),
        ds.get_featured_artists(DISCOVER_FEATURED_ARTISTS_LIMIT),
        ds.get_featured_genres(DISCOVER_FEATURED_GENRES_LIMIT),
    )
    return {
        "type": "discover_data",
        "data": {
            "recent": [t.to_dict() for t in recent],
            "favorites": [t.to_dict() for t in favorites],
            "cached_tracks": [t.to_dict() for t in cached],
            "featured_artists": featured_artists,
            "featured_genres": featured_genres,
        },
    }
```

---

## P-02 — CRITICAL: Full State Broadcast Setiap Toggle Favorite

**Severity:** CRITICAL  
**Dampak:** Setiap kali user toggle favorite, sistem melakukan `broadcast_state(state)` ke **semua klien aktif**. `state.to_dict()` menserialisasi queue penuh, radio_queue, lyrics, semua metadata — payload bisa 5–50KB. Dengan 50 klien aktif, satu aksi favorite = **50× serialisasi JSON besar + 50× WebSocket send**. Estimasi overhead: **5–100ms** per toggle di high-load.

**Penyebab:** Handler `TOGGLE_FAVORITE` di discover_handlers.py mengirim full state alih-alih pesan targeted minimal.

**Lokasi File:** `server/handlers/ws/discover_handlers.py` baris 81–88

**Kode Bermasalah:**
```python
if state.current_track and state.current_track.video_id == video_id:
    state.current_track.is_favorite = is_fav
    await manager.broadcast({
        "type": "state",
        "data": state.to_dict()   # ← SELURUH state dikirim hanya untuk 1 field!
    })
```

**Solusi:** Kirim event `favorite_status` yang sudah ada (minimal 2 field) — klien sudah bisa handle ini. Hapus broadcast full state.

**Implementasi:**
```python
# discover_handlers.py — TOGGLE_FAVORITE handler
is_fav = await db.toggle_favorite(video_id)

# Update state lokal
if state.current_track and state.current_track.video_id == video_id:
    state.current_track.is_favorite = is_fav

# Broadcast HANYA perubahan minimal — bukan full state
await manager.broadcast({
    "type": "favorite_status",
    "data": {
        "video_id": video_id,
        "is_favorite": bool(is_fav),
    },
})
# HAPUS: broadcast state.to_dict() di sini
```

---

## P-03 — HIGH: Seeding Database 1000 Songs dengan Serial INSERT (Startup Lambat)

**Severity:** HIGH  
**Dampak:** Saat database kosong (deploy pertama atau reset), `_seed_initial_data()` menginsert **100 artists + ~1000 songs** satu per satu dalam loop dengan `await self._conn.execute()` per row. Ini berarti 1100+ round-trip ke SQLite engine. Pada environment lambat (SBC/Termux/HDD), startup bisa **10–60 detik**. Server tidak siap melayani request selama ini.

**Penyebab:** Loop seeding tanpa batch insert dan tanpa executemany.

**Lokasi File:** `cache/db.py` baris 71–107

**Kode Bermasalah:**
```python
for artist in data.get('artists', []):
    await self._conn.execute('''INSERT OR REPLACE INTO artists...''', ...)  # 1 trip per artist
    for genre_name in artist.get('genre', []):
        await self._conn.execute('''INSERT OR IGNORE INTO genres...''', ...)
        async with self._conn.execute('SELECT id FROM genres...') as c:    # ← N+1: SELECT dalam loop
            genre_id = (await c.fetchone())[0]
        await self._conn.execute('''INSERT OR IGNORE INTO artist_genres...''', ...)
    for lagu in artist.get('lagu_populer', []):
        await self._conn.execute('''INSERT OR IGNORE INTO songs...''', ...) # 10 trip per artist
# Total: 100 + 300 + 300 + 1000 = ~1700 statements, masing-masing ter-await
```

**Solusi:** Gunakan `executemany()` dengan batch data yang sudah dipersiapkan, dan pre-load semua genre dengan single query. Commit sekali di akhir.

**Implementasi:**
```python
async def _seed_initial_data(self):
    # ... (check count sama) ...

    import json
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    artists_data = data.get('artists', [])

    # 1. Batch insert semua artists
    artist_rows = [
        (a['id'], a['nama'], a['kategori'], a['tahun_aktif'])
        for a in artists_data
    ]
    await self._conn.executemany(
        'INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif) VALUES (?, ?, ?, ?)',
        artist_rows
    )

    # 2. Kumpulkan semua genre unik lalu batch insert
    all_genres = {g for a in artists_data for g in a.get('genre', [])}
    await self._conn.executemany(
        'INSERT OR IGNORE INTO genres (nama_genre) VALUES (?)',
        [(g,) for g in all_genres]
    )

    # 3. Baca semua genre dalam 1 query (bukan N queries)
    async with self._conn.execute('SELECT id, nama_genre FROM genres') as cur:
        genre_map = {row['nama_genre']: row['id'] for row in await cur.fetchall()}

    # 4. Batch insert artist_genres dan songs
    ag_rows, song_rows = [], []
    for a in artists_data:
        for g in a.get('genre', []):
            if g in genre_map:
                ag_rows.append((a['id'], genre_map[g]))
        for lagu in a.get('lagu_populer', []):
            if lagu.get('youtube_id'):
                song_rows.append((a['id'], lagu['judul'], lagu['youtube_id'], lagu.get('durasi_detik', 0)))

    await self._conn.executemany(
        'INSERT OR IGNORE INTO artist_genres (artist_id, genre_id) VALUES (?, ?)', ag_rows
    )
    await self._conn.executemany(
        'INSERT OR IGNORE INTO songs (artist_id, judul, youtube_id, duration) VALUES (?, ?, ?, ?)',
        song_rows
    )
    await self._conn.commit()  # commit 1x saja
```
**Estimasi speedup:** 15–40× lebih cepat (dari ~30 detik → <2 detik).

---

## P-04 — HIGH: 100 Artist + 100 Genre Dikirim ke Klien Setiap Discover

**Severity:** HIGH  
**Dampak:** `DISCOVER_FEATURED_ARTISTS_LIMIT = 100` dan `DISCOVER_FEATURED_GENRES_LIMIT = 100` artinya setiap request DISCOVER mengirim **200 objek** dalam payload JSON. Pada mobile dengan bandwidth terbatas, payload ini bisa 15–30KB hanya untuk artist/genre pills. Ini juga di-render semuanya ke DOM sekaligus (200 `hashtag-pill` element). Scroll performance menurun signifikan.

**Penyebab:** Nilai limit di `constants.py` terlalu besar; tidak ada pagination atau lazy load untuk artist/genre pills.

**Lokasi File:** `core/constants.py` baris 13–14

**Kode Bermasalah:**
```python
DISCOVER_FEATURED_ARTISTS_LIMIT = 100   # ← 100 artists semua dikirm
DISCOVER_FEATURED_GENRES_LIMIT = 100    # ← 100 genres semua dikirim
```

**Solusi:** Kurangi limit ke jumlah yang reasonable untuk tampilan. Tambahkan "load more" jika diperlukan.

**Implementasi:**
```python
# core/constants.py
DISCOVER_FEATURED_ARTISTS_LIMIT = 20   # cukup untuk pills display
DISCOVER_FEATURED_GENRES_LIMIT = 15    # cukup untuk pills display

# Atau: pisahkan limit untuk fetch vs display
# Dan gunakan virtual scroll / IntersectionObserver untuk pills
```
**Estimasi payload reduction:** 80% lebih kecil untuk artist/genre data.

---

## P-05 — HIGH: `renderFullState()` Merender Semua Komponen Tanpa Dirty Check

**Severity:** HIGH  
**Dampak:** Setiap `state` message dari server (termasuk perubahan kecil seperti status online/offline) memicu `renderFullState()` yang memanggil **8 fungsi render sekaligus**: header, now-playing, progress, player bar, radio, queue, lyrics, settings. Semua DOM update ini terjadi dalam satu frame, menyebabkan **layout thrashing** dan frame drops di mobile. Estimasi: 5–15ms render time per event, yang bisa menumpuk hingga **janky animation** saat banyak event masuk.

**Penyebab:** Tidak ada diffing atau dirty-check sebelum merender komponen. `Object.assign(store, msg.data)` tidak memberitahu komponen mana yang berubah.

**Lokasi File:** `web/static/js/ws.js` baris 95–97 dan 147–157

**Kode Bermasalah:**
```javascript
case "state":
    Object.assign(store, msg.data);   // update semua field sekaligus
    requestRenderFullState();          // render SEMUA komponen

// ...
function renderFullState() {
    renderHeader();         // always
    renderNowPlaying();     // always
    renderProgress();       // always
    renderPlayerBar();      // always
    renderRadio();          // always
    renderQueue();          // always
    renderLyrics();         // always
    renderSettingsSheet();  // always
    updateSearchPlayingState();
    updateDiscoverPlayingState();
}
```

**Solusi:** Implementasikan dirty tracking — hanya render komponen yang datanya berubah.

**Implementasi:**
```javascript
// store.js — tambahkan snapshot tracking
let _prevStore = {};

function applyStateUpdate(newData) {
    const changed = {};
    for (const key of Object.keys(newData)) {
        if (JSON.stringify(store[key]) !== JSON.stringify(newData[key])) {
            changed[key] = true;
        }
    }
    Object.assign(store, newData);
    return changed;
}

// ws.js — gunakan di case "state"
case "state":
    const changed = applyStateUpdate(msg.data);
    requestRenderFullState(changed);
    break;

function renderFullState(changed = null) {
    const all = !changed;
    if (all || changed.is_online) renderHeader();
    if (all || changed.current_track || changed.status) renderNowPlaying();
    if (all || changed.position) renderProgress();
    if (all || changed.current_track || changed.status || changed.volume) renderPlayerBar();
    if (all || changed.playback_mode) renderRadio();
    if (all || changed.queue || changed.radio_queue || changed.current_track) renderQueue();
    if (all || changed.lyrics_lines) renderLyrics();
    if (all || changed.sponsorblock_active || changed.download_progress) renderSettingsSheet();
}
```

---

## P-06 — HIGH: `JSON.stringify(track)` di Setiap Render Item (Expensive per Frame)

**Severity:** HIGH  
**Dampak:** Fungsi `renderDiscoverTab()` dan `renderRecentRow()` memanggil `JSON.stringify(track)` untuk **setiap item di setiap render cycle**. Jika discover list memiliki 15 recent + 15 favorites + 15 cached = 45 items, dan render dipanggil setiap status change, ini adalah **45× JSON.stringify per render** — operasi yang cukup mahal di main thread terutama untuk track objects yang berisi banyak field.

**Penyebab:** Data track di-encode ke JSON string dan disimpan di `dataset.trackStr` / `dataset.track` supaya bisa di-retrieve saat click. Tidak ada cache invalidation.

**Lokasi File:** `web/static/js/render/discover.js` baris 126, 192, 412

**Kode Bermasalah:**
```javascript
// Dipanggil SETIAP render, untuk setiap item
el.dataset.trackStr = JSON.stringify(track).replace(/'/g, "&apos;");  // line 126
el.dataset.track = JSON.stringify(track);  // line 412
```

**Solusi:** Ganti pendekatan dataset serialization dengan in-memory Map keyed by video_id. Tidak perlu stringify sama sekali.

**Implementasi:**
```javascript
// Tambahkan di store.js atau utils.js
window._trackCache = new Map(); // video_id → TrackInfo object

// render/discover.js — updateItem function
(el, track, i) => {
    el.dataset.vid = track.video_id || '';
    // Simpan referensi objek langsung — tanpa stringify
    window._trackCache.set(track.video_id, track);
    // ... update DOM elements ...
}

// Event handler saat click
div.addEventListener('click', (e) => {
    const vid = div.dataset.vid;
    const track = window._trackCache.get(vid);  // O(1) lookup, no JSON.parse
    if (track) window.wsSend(WS_ACTIONS.PLAY_TRACK, track);
});
```

---

## P-07 — HIGH: `active_connections` Adalah List, Bukan Set (O(n) Remove)

**Severity:** HIGH  
**Dampak:** `ConnectionManager` menyimpan koneksi WebSocket aktif sebagai Python `list`. Saat klien disconnect, `list.remove(ws)` melakukan **linear scan O(n)** untuk menemukan elemen. Dengan 500 koneksi aktif, setiap disconnect = 500 komparasi. Lebih kritis: di `broadcast()`, saat ada dead connection, `self.disconnect(dead_ws)` dipanggil untuk setiap dead WS — dan masing-masing kembali melakukan `list.remove()` O(n). Ini race condition potensial dan bottleneck performa.

**Penyebab:** Penggunaan `list` alih-alih `set` untuk koleksi yang memerlukan O(1) membership test dan removal.

**Lokasi File:** `server/handlers/websocket.py` baris 25, 40–41

**Kode Bermasalah:**
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections = []   # ← list = O(n) remove

    def disconnect(self, ws):
        if ws in self.active_connections:           # O(n) scan
            self.active_connections.remove(ws)      # O(n) remove
```

**Solusi:** Ganti `list` dengan `set` untuk `active_connections`. WebSocket objects hashable (by identity).

**Implementasi:**
```python
class ConnectionManager:
    def __init__(self):
        self.active_connections: set = set()   # O(1) add/remove/membership
        self.authenticated_connections: set = set()

    async def connect(self, ws):
        self.active_connections.add(ws)         # O(1)
        ACTIVE_WEBSOCKETS.inc()

    def disconnect(self, ws):
        self.active_connections.discard(ws)     # O(1), tidak error jika tidak ada
        self.authenticated_connections.discard(ws)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        data = json.dumps(message, ensure_ascii=False)
        targets = list(self.active_connections)  # snapshot untuk iterasi aman
        results = await asyncio.gather(*(self._send_one(ws, data) for ws in targets))
        for dead_ws in results:
            if dead_ws is not None:
                self.disconnect(dead_ws)

    async def _send_one(self, ws, data: str):
        try:
            await ws.send_str(data)
            return None
        except Exception:
            return ws
```

---

## P-08 — MEDIUM: `extractDominantColor()` Membuat Canvas 50×50 di Main Thread per Track Change

**Severity:** MEDIUM  
**Dampak:** Setiap kali lagu berganti, `renderNowPlaying()` → `getCoverArt()` → `extractDominantColor()` membuat **Canvas element baru**, menggambar image 50×50, membaca pixel data dengan `getImageData()` (operasi yang **memblok main thread** dan menginvalidate GPU compositing). Pada mobile, ini bisa menyebabkan **jank 10–50ms** per track change, terasa sebagai UI freeze singkat.

**Penyebab:** `extractDominantColor` menggunakan synchronous canvas pixel read `getImageData()` di main thread tanpa offloading ke OffscreenCanvas atau Web Worker.

**Lokasi File:** `web/static/js/utils.js` fungsi `extractDominantColor`

**Kode Bermasalah:**
```javascript
window.extractDominantColor = function(imageElement, callback) {
    const canvas = document.createElement('canvas');    // buat DOM element baru
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    canvas.width = 50;
    canvas.height = 50;
    ctx.drawImage(imageElement, 0, 0, 50, 50);
    const data = ctx.getImageData(0, 0, 50, 50).data;  // ← BLOCKING main thread
    // ... 2500 pixel loop ...
```

**Solusi:** Gunakan `OffscreenCanvas` di Web Worker untuk pixel processing, atau cache hasil per video_id agar tidak dihitung ulang.

**Implementasi:**
```javascript
// Cache hasil per video_id — solusi cepat
const _colorCache = new Map();

window.extractDominantColor = function(imageElement, callback) {
    const vid = imageElement.dataset?.vid;
    if (vid && _colorCache.has(vid)) {
        callback(_colorCache.get(vid));
        return;
    }

    // Gunakan OffscreenCanvas jika tersedia
    const doExtract = () => {
        try {
            const canvas = new OffscreenCanvas(16, 16);  // 16×16 cukup untuk dominant color
            const ctx = canvas.getContext('2d');
            ctx.drawImage(imageElement, 0, 0, 16, 16);
            const data = ctx.getImageData(0, 0, 16, 16).data;
            // ... simplified color extraction ...
            const color = { r, g, b };
            if (vid) _colorCache.set(vid, color);
            callback(color);
        } catch(e) {
            callback(null);
        }
    };

    if (!imageElement.complete) {
        imageElement.addEventListener('load', doExtract, { once: true });
    } else {
        // Defer ke idle time — jangan block paint
        requestIdleCallback ? requestIdleCallback(doExtract) : setTimeout(doExtract, 0);
    }
};
```

---

## P-09 — MEDIUM: `loadLazyCovers()` Dipanggil Berulang Kali per Render Cycle

**Severity:** MEDIUM  
**Dampak:** `loadLazyCovers()` melakukan `document.querySelectorAll('img.lazy-cover:not(.observed)')` — **full DOM scan** — dan dipanggil di akhir `renderDiscoverTab()` DAN `renderRecentRow()`. Jika kedua fungsi ini dipanggil bersamaan (seperti saat `discover_data` datang), ada **2× full DOM scan** dalam 1 event loop tick. Pada halaman dengan 50+ lazy images, ini terasa di scroll performance.

**Penyebab:** Tidak ada debounce atau batching untuk `loadLazyCovers()`. Setiap render function memanggil langsung.

**Lokasi File:** `web/static/js/render/discover.js` baris 218, 242 (di akhir `renderDiscoverTab` dan `renderRecentRow`)

**Kode Bermasalah:**
```javascript
// Di renderDiscoverTab():
window.loadLazyCovers();   // DOM scan #1

// Di renderRecentRow() (dipanggil bersamaan dari discover_data handler):
window.loadLazyCovers();   // DOM scan #2 — dalam frame yang sama!
```

**Solusi:** Debounce `loadLazyCovers()` dengan `requestAnimationFrame`, sehingga multiple calls dalam 1 frame digabung menjadi 1 execution.

**Implementasi:**
```javascript
// utils.js — ganti implementasi loadLazyCovers
let _lazyCoversPending = false;
window.loadLazyCovers = function() {
    if (_lazyCoversPending) return;  // sudah dijadwalkan
    _lazyCoversPending = true;
    requestAnimationFrame(() => {
        _lazyCoversPending = false;
        _doLoadLazyCovers();
    });
};

function _doLoadLazyCovers() {
    if (!_lazyCoverObserver) {
        _lazyCoverObserver = new IntersectionObserver(/* ... same ... */);
    }
    document.querySelectorAll('img.lazy-cover:not(.observed)')
        .forEach(img => {
            img.classList.add('observed');
            _lazyCoverObserver.observe(img);
        });
}
```

---

## P-10 — MEDIUM: Bundle JS Tidak di-Minify dalam Development Build (105KB Unminified)

**Severity:** MEDIUM  
**Dampak:** File `bundle.js` saat ini **105,303 bytes (105KB) tidak terkompresi** dan berisi komentar, whitespace, dan nama variabel panjang. Setelah gzip menjadi ~21KB, tapi ini tetap lambat di 3G (estimasi: 1–2 detik tambahan load time). Lebih kritis: bundle ini di-precache oleh Service Worker — jika cache tidak di-invalidate dengan benar, user bisa menjalankan versi lama.

**Penyebab:** Build script menggunakan `--minify` flag tapi bundle yang ada di repo kemungkinan merupakan hasil `build:watch` (non-minified) berdasarkan isi file yang menunjukkan komentar dan format tidak terminify (`// --- config.js ---`).

**Lokasi File:** `web/static/js/bundle.js`, `package.json`

**Kode Bermasalah:**
```javascript
// Dari bundle.js — ada komentar yang seharusnya tidak ada di minified output:
// --- config.js ---
const TABS = ["home", "search", "radio", "discover"];

// --- store.js ---
const store = {
```

**Solusi:** Pastikan build production selalu menggunakan minified output. Tambahkan content hash ke filename untuk cache busting.

**Implementasi:**
```json
// package.json
{
  "scripts": {
    "build": "npm run build:js && npm run build:css",
    "build:js": "esbuild web/static/js/main.js --bundle --minify --sourcemap=external --outfile=web/static/js/bundle.js --platform=browser --format=iife --pure:console.log --drop:debugger",
    "build:css": "esbuild web/static/css/main.css --bundle --minify --outfile=web/static/css/bundle.css",
    "build:dev": "esbuild web/static/js/main.js --bundle --outfile=web/static/js/bundle.js --platform=browser --format=iife --watch",
    "build:analyze": "esbuild web/static/js/main.js --bundle --metafile=meta.json --outfile=/dev/null && node -e \"require('fs').writeFileSync('meta.json', JSON.stringify(require('./meta.json'), null, 2))\""
  }
}
```

---

## P-11 — MEDIUM: `switchTab('discover')` Memicu DISCOVER Request Setiap Kali Tab Diklik

**Severity:** MEDIUM  
**Dampak:** Setiap kali user switch ke tab home atau discover, `wsSend(WS_ACTIONS.DISCOVER)` langsung dieksekusi. Jika user bolak-balik tab, server menerima burst DISCOVER requests yang masing-masing men-trigger 5 DB queries. Tidak ada cooldown atau check apakah data sudah fresh.

**Penyebab:** Tidak ada cache TTL untuk discover data di frontend. `switchTab` di `main.js` memanggil DISCOVER unconditionally.

**Lokasi File:** `web/static/js/main.js` baris 53–56

**Kode Bermasalah:**
```javascript
if (tab === "discover" || tab === "home") {
    wsSend(WS_ACTIONS.DISCOVER);   // ← dipanggil setiap kali, tanpa throttle
}
```

**Solusi:** Tambahkan timestamp-based cache dengan TTL 30 detik. Jika data masih fresh, skip request.

**Implementasi:**
```javascript
// store.js
const store = {
    // ... existing ...
    discover_fetched_at: 0,   // timestamp terakhir discover data di-fetch
};

// main.js
const DISCOVER_CACHE_TTL_MS = 30_000; // 30 detik

window.switchTab = function(tab) {
    // ... tab switching logic ...
    if (tab === "discover" || tab === "home") {
        const age = Date.now() - store.discover_fetched_at;
        if (age > DISCOVER_CACHE_TTL_MS) {
            wsSend(WS_ACTIONS.DISCOVER);
        }
    }
};

// ws.js — update timestamp saat data diterima
case "discover_data":
    store.discover_fetched_at = Date.now();
    // ... rest of handler ...
```

---

## P-12 — MEDIUM: Missing Index untuk Favorites Query

**Severity:** MEDIUM  
**Dampak:** Query `get_favorites()` menggunakan `WHERE is_favorite = 1 OR play_count > 0 ORDER BY is_favorite DESC, play_count DESC`. Kolom `is_favorite` tidak memiliki index spesifik untuk nilai `= 1`. SQLite harus full-scan tabel `tracks` untuk setiap favorites request. Ketika tracks table tumbuh ke 10.000+ rows (heavy user), query ini bisa memakan **5–50ms** alih-alih <1ms dengan index.

**Penyebab:** Schema SQL tidak mendefinisikan index compound untuk `is_favorite` + `play_count` query pattern.

**Lokasi File:** `cache/schema.sql`

**Kode Bermasalah:**
```sql
-- Query yang berjalan tanpa index optimal:
SELECT ... FROM tracks 
WHERE is_favorite = 1 OR play_count > 0 
ORDER BY is_favorite DESC, play_count DESC 
LIMIT 15;
-- is_favorite tidak terindex untuk equality check
```

**Solusi:** Tambahkan partial index untuk favorites.

**Implementasi:**
```sql
-- Tambahkan ke schema.sql
CREATE INDEX IF NOT EXISTS idx_is_favorite 
    ON tracks(is_favorite, play_count DESC) 
    WHERE is_favorite = 1 OR play_count > 0;

-- Untuk discover recent query:
-- Index idx_last_played sudah ada, tapi pastikan query menggunakannya:
-- EXPLAIN QUERY PLAN SELECT ... FROM tracks ORDER BY last_played DESC LIMIT 15;
-- Seharusnya: "USING INDEX idx_last_played"
```

---

## P-13 — MEDIUM: Service Worker Precache 20+ File CSS Terpisah (Tidak Perlu)

**Severity:** MEDIUM  
**Dampak:** Service Worker di `sw.js` me-precache **20+ file CSS individual** (tokens.css, reset.css, typography.css, animations.css, dll.) plus bundle.css. Ini berarti 20+ HTTP requests saat install SW pertama kali, masing-masing dengan TCP overhead. Padahal semua CSS sudah di-bundle ke `bundle.css`. File individual hanya dibutuhkan saat development.

**Penyebab:** PRECACHE_ASSETS list mencantumkan file source CSS individual yang sudah ter-bundle.

**Lokasi File:** `web/static/sw.js` baris 4–29

**Kode Bermasalah:**
```javascript
const PRECACHE_ASSETS = [
    '/',
    '/static/inter.css',
    '/static/css/tokens.css',
    '/static/css/base/reset.css',
    '/static/css/base/typography.css',    // ← sudah ada di bundle.css
    '/static/css/base/animations.css',    // ← sudah ada di bundle.css
    '/static/css/layout/app-shell.css',   // ← sudah ada di bundle.css
    // ... 15 file lagi yang semuanya sudah di-bundle ...
    '/static/css/bundle.css',             // bundle sudah include semua di atas!
    '/static/js/bundle.js',
];
```

**Solusi:** Precache hanya asset final yang benar-benar diserve ke production browser.

**Implementasi:**
```javascript
const PRECACHE_ASSETS = [
    '/',                        // index.html
    '/static/css/bundle.css',   // semua CSS sudah di sini
    '/static/js/bundle.js',     // semua JS sudah di sini
    // Tambahkan font jika ada:
    // '/static/fonts/inter.woff2',
];
// Hasil: 20+ requests → 3 requests saat SW install
```

---

## P-14 — MEDIUM: `_stream_rate_limit` Dictionary Tidak Di-cleanup (Memory Leak Bertahap)

**Severity:** MEDIUM  
**Dampak:** `http.py` menggunakan `_stream_rate_limit = collections.defaultdict(list)` yang menyimpan timestamp requests per IP. Old timestamps di-cleanup (filter `now - t < 60`), tapi **kunci IP-nya tidak pernah dihapus dari dictionary**. Dalam environment dengan banyak unik IP (VPN users, banyak client), dictionary ini tumbuh tanpa batas. Pada 10.000 unique IPs, ini bisa menggunakan 1–5MB memory yang tidak pernah dibebaskan.

**Penyebab:** Cleanup hanya memfilter timestamps dalam list, bukan menghapus entries dengan empty list.

**Lokasi File:** `server/handlers/http.py` baris 16–20

**Kode Bermasalah:**
```python
_stream_rate_limit = collections.defaultdict(list)

# Di serve_stream():
history = _stream_rate_limit[client_ip]
history = [t for t in history if now - t < 60]   # filter lama
# ← Jika history kosong setelah filter, key IP tetap ada di dict!
_stream_rate_limit[client_ip] = history
```

**Solusi:** Hapus key ketika history kosong setelah cleanup. Atau gunakan TTL-based eviction.

**Implementasi:**
```python
# serve_stream() — cleanup yang benar
history = _stream_rate_limit.get(client_ip, [])
history = [t for t in history if now - t < 60]

if len(history) >= STREAM_RATE_LIMIT_MAX:
    return web.json_response(..., status=429)

if history:
    history.append(now)
    _stream_rate_limit[client_ip] = history
else:
    # Hanya simpan jika ada request — hapus key jika kosong
    _stream_rate_limit.pop(client_ip, None)
    _stream_rate_limit[client_ip] = [now]

# Atau: gunakan background task untuk evict expired IPs setiap 5 menit
```

---

## P-15 — MEDIUM: `_pending` Dict di MpvController Tidak Dibersihkan Saat Timeout

**Severity:** MEDIUM  
**Dampak:** `MpvController._pending` menyimpan `Future` objects untuk setiap IPC request yang belum mendapat response. Saat timeout (2 detik), future di-pop dengan `self._pending.pop(request_id, None)`, tapi jika `_send_request` di-cancel dari luar (asyncio task cancellation), `finally` block tidak menjamin cleanup. Dalam skenario reconnect yang agresif (mpv crash-restart loop), `_pending` bisa accumulate stale futures yang tidak pernah di-resolve, causing memory growth.

**Penyebab:** Task cancellation path tidak dihandle dalam `_send_request`.

**Lokasi File:** `engine/mpv_controller.py` baris 198–209

**Kode Bermasalah:**
```python
async def _send_request(self, command_payload: list):
    # ...
    try:
        self._writer.write(payload.encode())
        await self._writer.drain()
        return await asyncio.wait_for(future, timeout=2.0)
    except (OSError, asyncio.TimeoutError):
        self._pending.pop(request_id, None)
        return None
    # ← Tidak ada 'except asyncio.CancelledError' — jika task di-cancel,
    #   future tetap di _pending hingga observer loop cleanup
```

**Solusi:** Tambahkan `CancelledError` handler dan gunakan `try/finally` untuk garantikan cleanup.

**Implementasi:**
```python
async def _send_request(self, command_payload: list):
    if not self.is_connected or not self._writer:
        return None
    loop = asyncio.get_running_loop()
    async with self._req_lock:
        self._request_id += 1
        request_id = self._request_id
        future = loop.create_future()
        self._pending[request_id] = future

    payload = json.dumps({"command": command_payload, "request_id": request_id}) + "\n"
    try:
        self._writer.write(payload.encode())
        await self._writer.drain()
        return await asyncio.wait_for(future, timeout=2.0)
    except asyncio.CancelledError:
        self._pending.pop(request_id, None)
        if not future.done():
            future.cancel()
        raise  # re-raise agar asyncio task cancellation bekerja benar
    except (OSError, asyncio.TimeoutError):
        self._pending.pop(request_id, None)
        return None
    finally:
        # Jaminan tambahan — cleanup jika future selesai tapi belum di-pop
        self._pending.pop(request_id, None)
```

---

## P-16 — LOW: `DiscoverService` Di-instantiasi Ulang di Setiap Request

**Severity:** LOW  
**Dampak:** `_build_discover_payload(db)` membuat objek `DiscoverService(db)` baru setiap kali dipanggil. Meskipun object creation Python cukup murah, ini adalah pola yang tidak perlu — service bisa menjadi singleton atau disimpan di app context.

**Penyebab:** DiscoverService tidak di-inject sebagai singleton; di-create on-demand setiap request.

**Lokasi File:** `server/handlers/ws/discover_handlers.py` baris 17

**Kode Bermasalah:**
```python
async def _build_discover_payload(db):
    ds = DiscoverService(db)   # ← object baru setiap call
```

**Solusi:** Simpan DiscoverService instance di app context dan inject ke handlers.

---

## P-17 — LOW: Bundle CSS 55KB — Tidak Perlu Critical CSS Split

**Severity:** LOW  
**Dampak:** `bundle.css` sebesar 55KB (gzipped ~10KB) di-load secara blocking di `<head>`. Platform-specific CSS (desktop.css, landscape.css, tablet.css) di-load semua, padahal mobile user tidak perlu desktop.css dan vice versa. Estimasi: 20–30% CSS tidak digunakan pada setiap platform.

**Solusi:** Gunakan `media` query di `<link>` untuk platform CSS, atau gunakan CSS custom properties yang render-safe. Minimal: pastikan `bundle.css` exclude platform CSS dan gunakan `@import` dengan media queries.

---

## P-18 — LOW: `getHashtagColor()` Warna Acak Tidak Konsisten Antar Session

**Severity:** LOW  
**Dampak:** Warna hashtag pills di-generate dengan `Math.random()` dan di-cache di `_hashtagColors` object (in-memory). Setiap page refresh, warna berubah — tidak konsisten secara visual. Lebih dari itu, jika `renderDiscoverTab()` dipanggil sebelum `getHashtagColor()` di-seed, warna bisa berubah mid-session jika DOM di-recreate.

**Penyebab:** Warna berdasarkan random, bukan deterministik hash dari nama hashtag.

**Lokasi File:** `web/static/js/render/discover.js` baris 1–7

**Solusi:** Gunakan string hash deterministik dari nama hashtag.

**Implementasi:**
```javascript
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag];
    // Deterministik: hash nama → hue
    let hash = 0;
    for (let i = 0; i < hashtag.length; i++) {
        hash = ((hash << 5) - hash + hashtag.charCodeAt(i)) | 0;
    }
    const hue = Math.abs(hash) % 360;
    const color = `hsl(${hue}, 65%, 58%)`;
    _hashtagColors[hashtag] = color;
    return color;
}
```

---

## PRIORITAS PERBAIKAN

| Prioritas | ID | Temuan | Estimasi Effort |
|---|---|---|---|
| 🔴 SEGERA | P-01 | Serial discover queries → asyncio.gather | 30 menit |
| 🔴 SEGERA | P-02 | Full state broadcast saat toggle favorite | 15 menit |
| 🟠 MINGGU INI | P-03 | Serial seeding → executemany batch | 2 jam |
| 🟠 MINGGU INI | P-04 | Limit 100 artist/genre → 20/15 | 5 menit |
| 🟠 MINGGU INI | P-05 | renderFullState tanpa dirty check | 3 jam |
| 🟠 MINGGU INI | P-06 | JSON.stringify per item → Map | 1 jam |
| 🟠 MINGGU INI | P-07 | list → set untuk WebSocket connections | 30 menit |
| 🟡 SPRINT INI | P-08 | extractDominantColor blocking → cache | 2 jam |
| 🟡 SPRINT INI | P-09 | loadLazyCovers debounce | 30 menit |
| 🟡 SPRINT INI | P-10 | Pastikan bundle minified di production | 15 menit |
| 🟡 SPRINT INI | P-11 | Discover tab TTL cache | 1 jam |
| 🟡 SPRINT INI | P-12 | Index is_favorite di schema | 15 menit |
| 🟡 SPRINT INI | P-13 | SW precache slim down | 15 menit |
| 🟡 SPRINT INI | P-14 | Rate limit dict memory leak | 30 menit |
| 🟡 SPRINT INI | P-15 | MpvController _pending cleanup | 1 jam |
| 🟢 BACKLOG | P-16 | DiscoverService singleton | 30 menit |
| 🟢 BACKLOG | P-17 | CSS critical split | 3 jam |
| 🟢 BACKLOG | P-18 | Deterministic hashtag color | 15 menit |

---

## ESTIMASI DAMPAK GABUNGAN

Setelah semua perbaikan Critical + High diimplementasikan:

- **Discover request latency:** -60–80% (serial 5 queries → parallel, TTL cache)  
- **WebSocket broadcast overhead:** -70% (minimal events alih-alih full state)  
- **Startup time (cold deploy):** -90% (batch seeding vs serial inserts)  
- **Payload size per discover:** -80% (100 artists → 20 artists)  
- **Frontend frame time:** -40% (dirty rendering, debounced lazy load)  
- **Memory footprint (server):** stabil (set vs list, rate limit cleanup)

---

*Laporan ini mencakup temuan dari: Performance Engineer, Principal Backend Engineer, Senior Frontend Engineer, Database Architect.*
