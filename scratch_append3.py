
output_path = r'c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\docs\verifikasi_ekstraksi.md'
text_to_append = """
---
master_id: M-086
verification_status: SUDAH_BENAR
verified_location: web/static/js/audio.js:290-292, web/static/js/main.js:21
code_evidence: 
```javascript
function initAudio() {
    document.addEventListener("click", unlockBrowserAudio);
}
```
verification_note: Klaim audit salah. Prosedur `unlockBrowserAudio` secara aktif di-_binding_ oleh event listener klik dokumen di dalam `initAudio()`, dan inisiator tersebut telah dipanggil langsung oleh eksekutor startup UI utama (`main.js`). Oleh karena itu fungsi tersebut sama sekali bukan dead code.
---

---
master_id: M-087
verification_status: VALID
verified_location: start.py:419, 431
code_evidence: 
```python
            def on_log(line, tag):
                self._last_stdout_line = line
...
        self._last_stdout_line = ""
```
verification_note: Variabel properti `self._last_stdout_line` ditulis secara aktif setiap iterasi _stream stdout_ tetapi tak pernah ada satu fungsipun yang membacanya. Ini menjadi sampah memori.
---

---
master_id: M-088
verification_status: VALID
verified_location: engine/download_manager.py:33-35, server/handlers/auth.py:44
code_evidence: 
```python
        async def handler(command):
            import asyncio
            res = action(command.track)
```
verification_note: `import asyncio` dipanggil tepat di dalam *scope* (di tengah-tengah fungsi _async def_), menyebabkan instruksi resolusi *module* tertumpuk secara berulang-ulang tiap *handler* terpanggil, sebuah inefisiensi yang kentara.
---

---
master_id: M-089
verification_status: SUDAH_BENAR
verified_location: server/handlers/websocket.py:90, 99
code_evidence: 
```python
            if msg.type == aiohttp.WSMsgType.TEXT:
...
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
```
verification_note: Audit keliru. Modul inti `aiohttp` (bukan sekadar `aiohttp.web`) tetap digunakan namespace-nya untuk memanggil konstanta enum dari jenis _WS message type_ secara eksplisit.
---

---
master_id: M-090
verification_status: VALID
verified_location: config.py:29, engine/mpv_controller.py:21-23, engine/radio_engine.py:121
code_evidence: 
```python
# PATCH-YTDLP-RESOLVE-TIMEOUT-01: yt-dlp.get_stream_url() sebelumnya tidak punya batas waktu
...
    # CRITICAL-03 fix: On Windows, falls back to TCP socket (localhost:port)
...
            # PATCH-RADIO-EMPTY-QUEUE-01: Queue habis — _start() jalan di background
```
verification_note: Jejak revisi perbaikan *issue* tertinggal di berbagai sudut kode produksi (menandakan *tech debt*) tanpa dibersihkan dengan layak usai *merge* dilakukan.
---

---
master_id: M-091
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:19-23
code_evidence: 
```python
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)
    favorites = await ds.get_favorites(DISCOVER_FAVORITES_LIMIT)
    cached = await ds.get_cached(DISCOVER_CACHED_LIMIT)
    featured_artists = await ds.get_featured_artists(DISCOVER_FEATURED_ARTISTS_LIMIT)
    featured_genres = await ds.get_featured_genres(DISCOVER_FEATURED_GENRES_LIMIT)
```
verification_note: Kelima tabel / sumber agregasi _discover_ dieksekusi menunggu berantai (_serial_). Jika 1 baris memakan waktu 15ms, maka klien harus menunggu 75ms hanya untuk mengekstrak struktur query yang padahal bisa ditembakkan independen dengan `asyncio.gather`.
---

---
master_id: M-092
verification_status: VALID
verified_location: cache/db.py:93-121
code_evidence: 
```python
        for artist in data.get('artists', []):
...
            for lagu in artist.get('lagu_populer', []):
...
                    await self._conn.execute('''
                        INSERT OR IGNORE INTO songs (artist_id, judul, youtube_id, duration)
```
verification_note: Mekanisme penanaman _seed database_ tidak disatukan dalam perintah `executemany` secara *batching*. Menembakkan lebih dari ratusan query raw SQL *execute* per perulangan For Loop.
---

---
master_id: M-093
verification_status: VALID
verified_location: core/constants.py:13-14
code_evidence: 
```python
DISCOVER_FEATURED_ARTISTS_LIMIT = 100
DISCOVER_FEATURED_GENRES_LIMIT = 100
```
verification_note: Terdapat dua konstanta batas limit 100 data entri yang memicu pengiriman payload WebSocket raksasa di halaman pencarian kategori ke seluruh klien pada fase awal halaman *discover*.
---

---
master_id: M-094
verification_status: VALID
verified_location: web/static/js/ws.js:226-238
code_evidence: 
```javascript
function renderFullState() {
    renderHeader();
    renderNowPlaying();
...
    renderLyrics();
    renderSettingsSheet();
...
```
verification_note: Sebuah mutasi kedudukan waktu pemutaran (contohnya pergeseran 1 detik track audio) memicu _Redraw_ / perenderan buta ke seluruh seksi aplikasi, karena tidak ada *Dirty Check* (_Diffing_) State per komponen layaknya kerangka JS modern.
---

---
master_id: M-095
verification_status: VALID
verified_location: web/static/js/render/discover.js:126, 192, 412
code_evidence: 
```javascript
                el.dataset.trackStr = JSON.stringify(track).replace(/'/g, "&apos;");
...
            el.dataset.track = JSON.stringify(track);
```
verification_note: Operasi mahal serialisasi obyek metadata (`JSON.stringify`) diulang tanpa belas kasihan di dalam iterasi per-item list hasil *Discover* dan *Recent*, yang bisa berpotensi menghabiskan daya *scripting* Frame secara instan.
---

---
master_id: M-096
verification_status: VALID
verified_location: web/static/js/utils.js:152-156
code_evidence: 
```javascript
        const canvas = document.createElement('canvas');
        const canvasContext = canvas.getContext('2d', { willReadFrequently: true });
...
        const data = canvasContext.getImageData(0, 0, 50, 50).data;
```
verification_note: Pengambilan bit sampel gambar dieksekusi sinkron pada lapisan Main-Thread DOM (bukan pada Worker), memaksa UI mengalami kondisi _freeze/jank_ mikrosekon sejenak tiap cover musik diganti.
---

---
master_id: M-097
verification_status: VALID
verified_location: web/static/js/render/discover.js:291, 432
code_evidence: 
```javascript
    window.loadLazyCovers();
```
verification_note: `window.loadLazyCovers()` dipanggil di akhir iterasi kedua fungsi `renderRecentRow` maupun `renderDiscoverTab`. Karena penempatannya, fungsi yang mengaktifkan peramban `IntersectionObserver` ini menghajar tag secara dobel pada iterasi satu siklus *Event Loop*.
---

---
master_id: M-098
verification_status: VALID
verified_location: web/static/js/main.js:57-59
code_evidence: 
```javascript
        if (tab === "discover" || tab === "home") {
            wsSend(WS_ACTIONS.DISCOVER);
        }
```
verification_note: Klien yang dengan santai klik bolak-balik pergantian menu (misalnya Discover - Search - Discover) akan selalu menghantam WebSocket Server dengan instruksi pengiriman ulang query Database *Discover* (tanpa blok *caching* / jeda *Throttle*).
---

---
master_id: M-099
verification_status: VALID
verified_location: cache/schema.sql:19-22
code_evidence: 
```sql
CREATE INDEX IF NOT EXISTS idx_local_path ON tracks(local_path) WHERE local_path IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_last_played ON tracks(last_played DESC);
CREATE INDEX IF NOT EXISTS idx_play_count ON tracks(play_count DESC) WHERE play_count > 0;
CREATE INDEX IF NOT EXISTS idx_stream_url_ts ON tracks(stream_url_ts);
```
verification_note: Sama sekali tak terdapat formasi blok index semisal `CREATE INDEX idx_is_favorite ON tracks(is_favorite)` guna mempercepat query perburuan daftar lagu-lagu favorit pada dataset ratusan item lagu.
---

---
master_id: M-100
verification_status: VALID
verified_location: web/static/sw.js:5-30
code_evidence: 
```javascript
const PRECACHE_ASSETS = [
...
    '/static/css/tokens.css',
    '/static/css/base/reset.css',
...
```
verification_note: Strategi Service Worker PWA melakukan beban *Precache* belasan CSS statis mentahan yang padahal sudah dienkapsulasi dengan perintah `@import` di `inter.css` atau yang dimuat seutuhnya ke bundle bundler, sehingga mubazir bandwith.
---

Batch ini: 13 valid, 0 tidak ditemukan, 2 sudah benar, 0 perlu konfirmasi.
"""

with open(output_path, 'a', encoding='utf-8') as f:
    f.write(text_to_append)
print('DONE')
