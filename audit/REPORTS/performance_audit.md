# Audit Performa — ytgui-main

> Sumber: codebase saja (file `.backup` dan `.md` diabaikan).  
> Tanggal audit: 2026-07-02

---

## Ringkasan Eksekutif

| # | Temuan | Kategori | Severity |
|---|--------|----------|----------|
| 1 | `toggle_favorite` — 3 query terpisah untuk 1 operasi | N+1 Query | 🔴 HIGH |
| 2 | `broadcast_discover_data` dipanggil setelah setiap toggle/delete | Redundant Render | 🔴 HIGH |
| 3 | `ORDER BY RANDOM()` tanpa index — full table scan | Slow Query | 🔴 HIGH |
| 4 | `renderFullState()` memanggil **semua** renderer setiap state update | Redundant Render | 🔴 HIGH |
| 5 | 17 file JS diload terpisah, tanpa bundling | Large Bundle | 🟠 MEDIUM |
| 6 | Icon font CDN (`tabler-icons`) — render-blocking, network-dependent | Heavy Dependency | 🟠 MEDIUM |
| 7 | `db.init()` — 4× `ALTER TABLE` + 1× `CREATE INDEX` setiap startup | Slow Startup | 🟠 MEDIUM |
| 8 | `get_featured_artists(100)` — subquery `IN (SELECT ... ORDER BY RANDOM() LIMIT 100)` | Slow Query | 🟠 MEDIUM |
| 9 | 15× `commit()` per operasi individual di `cache/db.py` | Slow Query | 🟡 LOW |
| 10 | `_on_download_complete` — duplikasi logika `_build_discover_payload` | Redundant Render | 🟡 LOW |
| 11 | `TrackProgressEvent` diterima tiap ~100ms, diproses oleh 2 subscriber | Blocking UI | 🟡 LOW |
| 12 | `syncBrowserAudio()` + `syncLocalLyrics()` dipanggil setiap `progress` message | Unnecessary Rebuild | 🟡 LOW |
| 13 | `renderRecentRow()` — `innerHTML` rebuild + rebind listeners setiap discover update | Unnecessary Rebuild | 🟡 LOW |
| 14 | `SELECT *` di `DiscoverService` — fetch semua kolom termasuk `stream_url` (varchar 2048) | Slow Query | 🟡 LOW |
| 15 | `_bg_tasks` set di `RadioMode` — tasks tidak pernah di-`await`, potensi memory leak | Memory Leak | 🟡 LOW |

---

## Detail Temuan

---

### 1. N+1 Query — `toggle_favorite` (3 round-trip untuk 1 toggle)

**File:** `cache/db.py` — baris 368–390  
**Severity:** 🔴 HIGH  
**Estimasi dampak:** +2 DB round-trip per klik favorit; terasa di Raspberry Pi / storage lambat.

**Masalah:**
```python
# Query 1: cek keberadaan track
async with self._conn.execute("SELECT 1 FROM tracks WHERE video_id = ?", ...)

# Query 2: toggle
await self._conn.execute("UPDATE tracks SET is_favorite = 1 - COALESCE(...) WHERE video_id = ?", ...)
await self._conn.commit()

# Query 3: baca nilai baru
async with self._conn.execute("SELECT is_favorite FROM tracks WHERE video_id = ?", ...)
```

Tiga query untuk operasi yang bisa diselesaikan dalam **satu** UPDATE dengan `RETURNING`.

**Optimisasi:**
```python
async def toggle_favorite(self, video_id: str) -> int:
    cursor = await self._conn.execute(
        """UPDATE tracks
           SET is_favorite = 1 - COALESCE(is_favorite, 0)
           WHERE video_id = ?
           RETURNING is_favorite""",
        (video_id,)
    )
    await self._conn.commit()
    row = await cursor.fetchone()
    return int(row["is_favorite"]) if row else 0  # 0 = video_id tidak ada
```
SQLite 3.35+ mendukung `RETURNING`. Eliminasi 2 dari 3 round-trip.

---

### 2. Redundant Render — `broadcast_discover_data` dipicu setelah setiap toggle/delete

**File:** `server/handlers/websocket.py` — baris 179, 269  
**Severity:** 🔴 HIGH  
**Estimasi dampak:** Setiap klik favorit atau hapus download memicu **5 query sekaligus** (`get_recent`, `get_favorites`, `get_cached`, `get_featured_artists(100)`, `get_featured_genres(100)`) lalu broadcast payload besar ke **semua** WebSocket client.

**Masalah:**
```python
# _handle_toggle_favorite
await broadcast_discover_data(manager, db)   # ← 5 query + broadcast

# _handle_delete_download
await broadcast_discover_data(manager, db)   # ← idem
```

**Optimisasi:**
- Untuk `toggle_favorite`: cukup broadcast perubahan `is_favorite` satu track saja (sudah ada `favorite_status` message). **Hapus** panggilan `broadcast_discover_data`.
- Untuk `delete_download`: kirim invalidation signal ringan, biarkan client request `discover` manual.
- Jika tetap diperlukan: cache payload `discover_data` dengan TTL 5 detik, sehingga burst event tidak memicu 5 query berulang.

---

### 3. Slow Query — `ORDER BY RANDOM()` tanpa batas efisiensi

**File:** `cache/db.py` — baris 272, 291, 294, 318, 339, 349  
`services/discover_service.py` — baris 104, 120  
**Severity:** 🔴 HIGH  
**Estimasi dampak:** SQLite harus **scan seluruh tabel** dan assign nilai random ke setiap baris sebelum sort. Dengan tabel `songs` ribuan baris, ini bisa memakan 50–200ms per query di hardware ringan (Termux/RPi).

**Contoh query bermasalah:**
```sql
-- discover_service.py baris 104
SELECT id, nama, ... FROM artists
WHERE id IN (SELECT id FROM artists ORDER BY RANDOM() LIMIT 100)
```
Subquery `ORDER BY RANDOM()` di sini tidak perlu — hasilnya di-IN ke query luar yang memilih baris yang sama. Ini **double scan**.

**Optimisasi:**
```sql
-- Ganti subquery double-scan dengan satu query langsung
SELECT id, nama, kategori, tahun_aktif, COALESCE(click_count, 0) as click_count
FROM artists
ORDER BY RANDOM()
LIMIT 100
```
Untuk `get_random_songs`, pertimbangkan strategi **rowid sampling** jika tabel besar:
```sql
SELECT * FROM songs WHERE rowid >= (ABS(RANDOM()) % (SELECT MAX(rowid) FROM songs))
LIMIT ?
```
Atau pre-shuffle di Python setelah fetch kandidat kecil.

---

### 4. Redundant Render — `renderFullState()` memanggil semua renderer setiap state update

**File:** `web/static/js/ws.js` — baris 92, 102, 210–220  
**Severity:** 🔴 HIGH  
**Estimasi dampak:** Setiap message `state` dari server (termasuk yang dipicu `QueueUpdatedEvent` yang terjadi sering) memaksa re-render: header, now-playing, progress, player-bar, radio, queue, lyrics, settings sheet, search state, discover state — **10 fungsi render sekaligus**.

**Masalah:**
```javascript
function renderFullState() {
    renderHeader();
    renderNowPlaying();
    renderProgress();
    renderPlayerBar();
    renderRadio();
    renderQueue();
    renderLyrics();
    renderSettingsSheet();
    updateSearchPlayingState();
    updateDiscoverPlayingState();
}
```
Dipanggil di dua tempat berbeda di `handleServerMessage` (case `state`, dan setelah `auth_status`).

**Optimisasi:**
- Implementasi **dirty-checking**: bandingkan field yang berubah antara state lama dan baru, render hanya komponen yang relevan.
- Pisahkan update berdasarkan tipe event: `QueueUpdatedEvent` → hanya `renderQueue()`; `TrackStartedEvent` → `renderNowPlaying()` + `renderPlayerBar()`; dll.
- Minimal: debounce `renderFullState` dengan `requestAnimationFrame` jika dipanggil beberapa kali dalam satu frame.

---

### 5. Large Bundle — 17 file JS diload terpisah, tanpa minifikasi/bundling

**File:** `web/static/index.html` — baris 623–646  
**Severity:** 🟠 MEDIUM  
**Estimasi dampak:** 17 HTTP request terpisah pada page load. Walaupun kecil secara ukuran total (~150KB unminified), di koneksi latensi tinggi (mobile/WiFi lemah) setiap round-trip menambah 20–100ms. Total overhead bisa 300–500ms extra.

**File yang diload:**
```
config.js, store.js, dom.js, utils.js, auth.js,
player.js, now-playing.js, queue.js, discover.js, favorites.js,
lyrics.js, search.js, player-events.js, queue-events.js,
lyrics-events.js, settings-events.js, index.js, portal.js,
viewport.js, touch.js, keyboard.js, audio.js, ws.js, main.js
```

**Optimisasi:**
- Gunakan `esbuild` atau `rollup` untuk bundle semua JS menjadi 1–2 file. Build step sederhana, tidak perlu webpack.
- Aktifkan gzip/brotli di aiohttp (atau nginx reverse proxy).
- Tambahkan `Cache-Control: public, max-age=31536000` dengan content-hash pada static assets.

---

### 6. Heavy Dependency — Tabler Icons dari CDN, render-blocking

**File:** `web/static/index.html` — baris 20  
**Severity:** 🟠 MEDIUM  
**Estimasi dampak:** Jika CDN lambat atau offline, seluruh icon tidak muncul. Font CSS di `<head>` **memblokir rendering** sampai resource diunduh. Di kondisi offline/intranet (skenario Termux), ini menyebabkan halaman tampil tanpa icon sampai timeout.

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/dist/tabler-icons.min.css">
```

Versi `@latest` juga rentan breaking change tanpa notice.

**Optimisasi:**
- Self-host file CSS + font (`tabler-icons.min.css` + `.woff2`) di `/static/`.
- Pin ke versi spesifik (sudah ada `@3.33.0` di beberapa referensi).
- Atau ganti dengan SVG sprite inline untuk icon yang digunakan saja (≈ 15–20 icon).

---

### 7. Slow Startup — 4× `ALTER TABLE` + `CREATE INDEX` setiap boot

**File:** `cache/db.py` — baris 36–62  
**Severity:** 🟠 MEDIUM  
**Estimasi dampak:** Setiap startup aplikasi menjalankan 5 DDL statement yang masing-masing dibungkus `try/except` (mengharap `OperationalError` jika kolom/index sudah ada). Ini pattern migrasi manual yang tidak bersih dan menambah ~50–150ms overhead startup.

**Masalah:**
```python
try:
    await self._conn.execute("ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0")
    await self._conn.commit()
except Exception:
    pass  # ← suppress error setiap kali (kolom sudah ada)

# ...diulang 3× lagi untuk kolom lain
```

**Optimisasi:**
- Pindahkan semua kolom ini ke `schema.sql` dengan `IF NOT EXISTS` atau gunakan sistem migrasi ringan (versi schema di tabel `schema_version`).
- Atau query `PRAGMA table_info(tracks)` sekali saat startup, cek kolom yang ada, baru ALTER jika perlu.

---

### 8. Slow Query — `get_featured_artists` dengan double-scan subquery

**File:** `services/discover_service.py` — baris 104  
**Severity:** 🟠 MEDIUM  
**Estimasi dampak:** Query meminta 100 artis dengan subquery `WHERE id IN (SELECT id FROM artists ORDER BY RANDOM() LIMIT 100)`. SQLite akan sort **semua baris** dua kali (inner SELECT + outer WHERE IN). Untuk tabel 500+ artis ini bisa 30–80ms.

**Masalah:**
```sql
SELECT id, nama, ... FROM artists
WHERE id IN (SELECT id FROM artists ORDER BY RANDOM() LIMIT 100)
```

**Optimisasi:**
```sql
-- Langsung satu scan
SELECT id, nama, kategori, tahun_aktif, COALESCE(click_count, 0) as click_count
FROM artists
ORDER BY RANDOM()
LIMIT 100
```

---

### 9. Slow Query — 15× `commit()` individual di `cache/db.py`

**File:** `cache/db.py`  
**Severity:** 🟡 LOW  
**Estimasi dampak:** Setiap operasi tulis memanggil `commit()` tersendiri. Di WAL mode ini relatif ringan, tapi untuk operasi batch (misalnya `upsert_track` dipanggil saat track started + duration poll + download) menghasilkan 3–4 fsync terpisah.

**Optimisasi:**
- Untuk operasi yang sering beriringan, gunakan `BEGIN` / `COMMIT` explicit di level controller.
- Pertimbangkan `executemany` untuk batch insert saat import awal.

---

### 10. Redundant Render — Duplikasi logika discover di `_on_download_complete`

**File:** `server/handlers/event_listeners.py` — baris 49–66  
**Severity:** 🟡 LOW  
**Estimasi dampak:** `_on_download_complete` membangun payload discover secara manual (copy-paste dari `_build_discover_payload`), sehingga ada **dua implementasi** dari logika yang sama. Potensi drift jika salah satu diupdate.

**Optimisasi:**
- Ekstrak `_build_discover_payload` dari `websocket.py` ke modul `discover_service.py` atau `broadcast_service.py`.
- `_on_download_complete` cukup panggil fungsi yang sudah ada.

---

### 11. Blocking UI — Progress message setiap ~100ms, 2 subscriber aktif

**File:** `server/handlers/event_listeners.py` — `_on_track_progress`  
`engine/playback/controller.py` — `_on_track_progress`  
**Severity:** 🟡 LOW  
**Estimasi dampak:** `TrackProgressEvent` dari MPV diterima ~10x/detik. Walaupun sudah ada throttle 0.33s di event_listener, controller juga subscribe ke event yang sama untuk update SponsorBlock dan lyric sync — artinya event diproses dua kali setiap kali masuk.

**Optimisasi:**
- Pastikan hanya **satu subscriber** yang handle progress. Controller bisa menerima notifikasi dari broadcast_service, bukan langsung dari event bus.
- Atau tingkatkan throttle ke 0.5s (update posisi setiap 500ms cukup untuk UI playback bar).

---

### 12. Unnecessary Rebuild — `syncBrowserAudio()` + `syncLocalLyrics()` setiap progress tick

**File:** `web/static/js/ws.js` — baris 104, 147–148  
**Severity:** 🟡 LOW  
**Estimasi dampak:** Setiap message `progress` dari server (3x/detik) memanggil `syncBrowserAudio()` yang memeriksa `audio.currentTime`, `audio.paused`, `audio.readyState` — operasi DOM/Web Audio yang tidak gratis. Di perangkat low-end ini berkontribusi frame jank.

**Optimisasi:**
- `syncBrowserAudio()`: jalankan hanya jika `audio_output === 'browser'` DAN status berubah atau diff > threshold. Tambahkan early-return.
- `syncLocalLyrics()`: sudah ringan (array iteration), tapi bisa di-debounce ke `requestAnimationFrame`.

---

### 13. Unnecessary Rebuild — `renderRecentRow()` rebuild innerHTML + rebind listeners

**File:** `web/static/js/render/discover.js` — fungsi `renderRecentRow()`  
**Severity:** 🟡 LOW  
**Estimasi dampak:** Setiap `discover_data` message (dipicu setelah toggle favorit, delete, dll.) membangun ulang seluruh HTML untuk 5 item terbaru dengan `innerHTML = items.slice(0,5).map(...).join('')` dan kemudian me-rebind semua event listener. Ini memaksa browser untuk re-parse HTML + re-attach listeners.

**Optimisasi:**
- Gunakan pola `renderList` yang sudah ada di `render/queue.js` (reuse DOM element, update isi saja).
- Atau gunakan event delegation pada container alih-alih listener per item.

---

### 14. Slow Query — `SELECT *` di DiscoverService mengambil `stream_url` (2KB per baris)

**File:** `services/discover_service.py` — baris 23, 50, 77  
**Severity:** 🟡 LOW  
**Estimasi dampak:** `stream_url` adalah `VARCHAR(2048)` berisi URL YouTube panjang. `SELECT *` di `get_recent(15)`, `get_favorites(15)`, `get_cached(15)` menarik kolom ini untuk 45 baris padahal UI tidak membutuhkannya.

**Optimisasi:**
```sql
-- Ganti SELECT * dengan kolom yang dibutuhkan UI saja
SELECT video_id, title, artist, duration, thumbnail, local_path,
       view_count, play_count, is_favorite
FROM tracks ORDER BY last_played DESC LIMIT ?
```
Mengurangi data transfer DB↔Python ~30–40% per query discover.

---

### 15. Memory Leak — `_bg_tasks` set di RadioMode tidak di-cleanup saat task error

**File:** `engine/radio_engine.py` — fungsi `_track_task()`  
**Severity:** 🟡 LOW  
**Estimasi dampak:** Task ditambahkan ke `_bg_tasks` set dengan `done_callback` `task_set.discard`. Namun jika task selesai **sebelum** `add_done_callback` dipanggil (kondisi race pada event loop tight), task tidak di-discard:

```python
def _track_task(task_set: set, coro, name: str):
    task = safe_create_task(coro, name=name)
    task.add_done_callback(task_set.discard)
    task_set.add(task)
    if task.done():
        task_set.discard(task)  # ← mitigation ada, tapi callback race masih mungkin
    return task
```

Selain itu, task yang di-cancel di `on_deactivated()` hanya di-cancel tanpa di-await, sehingga exception dari task yang di-cancel tidak ter-handle dan bisa tertinggal sebagai `Task exception was never retrieved`.

**Optimisasi:**
```python
async def on_deactivated(self) -> None:
    self.state.radio_queue.clear()
    tasks = list(self._bg_tasks)
    self._bg_tasks.clear()
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
```

---

## Prioritas Perbaikan

| Prioritas | Temuan | Effort | Impact |
|-----------|--------|--------|--------|
| 🔴 1 | Ganti 3-query `toggle_favorite` dengan `RETURNING` | Rendah | Tinggi |
| 🔴 2 | Hapus `broadcast_discover_data` dari toggle/delete | Rendah | Tinggi |
| 🔴 3 | Ganti double-scan `ORDER BY RANDOM()` subquery | Rendah | Tinggi |
| 🔴 4 | Partial render — jangan `renderFullState()` untuk semua event | Sedang | Tinggi |
| 🟠 5 | Bundle JS dengan esbuild | Sedang | Medium |
| 🟠 6 | Self-host Tabler Icons | Rendah | Medium |
| 🟠 7 | Pindahkan migrasi ke schema.sql | Rendah | Medium |
| 🟠 8 | Perbaiki `get_featured_artists` query | Rendah | Medium |
| 🟡 9 | Spesifikkan kolom di DiscoverService (hapus SELECT *) | Rendah | Low |
| 🟡 10 | Refactor `renderRecentRow` ke DOM reuse pattern | Sedang | Low |
| 🟡 11 | Await tasks di `RadioMode.on_deactivated` | Rendah | Low |
