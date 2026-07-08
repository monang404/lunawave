import re

text_to_insert = '''
---
master_id: M-101
verification_status: VALID
verified_location: engine/mpv_controller.py:284-290
code_evidence: 
```python
        try:
            self._writer.write(payload.encode())
            await self._writer.drain()
            return await asyncio.wait_for(future, timeout=2.0)
        except (OSError, asyncio.TimeoutError):
            self._pending.pop(request_id, None)
            return None
```
verification_note: Blok eksekusi `await asyncio.wait_for` hanya menangkap `OSError` dan `TimeoutError`. Jika task induk di-cancel (melempar `asyncio.CancelledError`), future di dalam dict `_pending` tidak akan pernah di-pop dan menggantung abadi di memori, berpotensi memory leak.
---

---
master_id: M-102
verification_status: VALID
verified_location: server/handlers/ws/discover_handlers.py:17-33
code_evidence: 
```python
async def _build_discover_payload(db):
    ds = DiscoverService(db)
    recent = await ds.get_recent(DISCOVER_RECENT_LIMIT)
    favorites = await ds.get_favorites(DISCOVER_FAVORITES_LIMIT)
...
    return {
        "type": "discover_data",
        "data": {
            "recent": [t.to_dict() for t in recent],
```
verification_note: Pembentukan muatan data discover memanggil database dengan batas statis (`DISCOVER_RECENT_LIMIT`, dll) namun sama sekali tidak menyediakan kontrol parameter asupan seperti `offset` maupun `page`, sehingga mustahil melakukan infinite-scroll bagi antarmuka klien.
---

---
master_id: M-103
verification_status: VALID
verified_location: (Global CSS Bundle)
code_evidence: 
(Semua aturan CSS disatukan di main.css yang dibundle via esbuild di package.json)
verification_note: Tidak ada mekanisme _Critical CSS_ atau pemecahan chunk asset spesifik mobile. Semua aset gaya diunduh dan diproses penuh meski perangkat pengguna tidak mengakses _layout_ desktop.
---

---
master_id: M-104
verification_status: VALID
verified_location: web/static/js/render/discover.js:1-9
code_evidence: 
```javascript
const _hashtagColors = {};
function getHashtagColor(hashtag) {
    if (_hashtagColors[hashtag]) return _hashtagColors[hashtag];
    const hue = Math.floor(Math.random() * 360);
...
    const color = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    _hashtagColors[hashtag] = color;
    return color;
}
```
verification_note: Pewarnaan elemen UI hash tag/genre sepenuhnya diundi dengan algoritma `Math.random()`. Walaupun menggunakan dictionary memory sementara, warna akan hilang/berubah drastis ketika page _refresh_.
---

---
master_id: M-105
verification_status: VALID
verified_location: cache/db.py:30-36
code_evidence: 
```python
    async def init(self):
...
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")
```
verification_note: Pada saat inisialisasi basis data SQLite, parameter konfigurasi mendasar `PRAGMA busy_timeout = 5000` dihilangkan, berpotensi menghasilkan `SQLITE_BUSY` saat terjadi balapan data simpan antar handler (konkurensi).
---

---
master_id: M-106
verification_status: VALID
verified_location: cache/db.py:42-47, cache/schema.sql
code_evidence: 
```python
        async def add_column_if_not_exists(table, column, definition):
...
            if column not in columns:
                await self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
```
verification_note: Perubahan arsitektur kolom sepenuhnya bergantung injeksi raw skrip ad-hoc saat runtime alih-alih memakai sistem migrasi sah semacam _Alembic_. Menyebabkan jejak evolusi data kacau, susah mundur versi, dan rentan patah.
---

---
master_id: M-107
verification_status: VALID
verified_location: cache/db.py:95-98
code_evidence: 
```python
            await self._conn.execute(\'''
                INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif)
                VALUES (?, ?, ?, ?)
            \''', (artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))
```
verification_note: Karena `INSERT OR REPLACE` di SQLite bermakna "hapus baris lama dan buat baris baru", parameter metrik seperti `click_count` di tabel artis akan dibunuh kembali menjadi default (Nol) jika sinkronisasi re-seed terjadi.
---

---
master_id: M-108
verification_status: VALID
verified_location: cache/repositories/track_repository.py:108-138
code_evidence: 
```python
        cursor = await self._conn.execute(
            """SELECT video_id FROM tracks ..."""
        )
        rows = await cursor.fetchall()
...
        for vid in video_ids:
            p = CACHE_DIR / f"{vid}.mp3"
            if p.exists():
                try: p.unlink()
...
        await self._conn.execute(
            f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids
        )
```
verification_note: Urutan skenario mengambil array id, lalu unlink file IO disusul instruksi DELETE sql sangat rawan bentrok _race condition_. Seandainya server lumpuh sebelum perulangan SQL tereksekusi, maka MP3-nya menguap tapi logik rekam di basis datanya gentayangan tak tersentuh.
---

---
master_id: M-109
verification_status: VALID
verified_location: cache/repositories/track_repository.py:93-97
code_evidence: 
```python
            """UPDATE tracks
               SET is_favorite = 1 - COALESCE(is_favorite, 0)
               WHERE video_id = ?
               RETURNING is_favorite""",
```
verification_note: _Clause_ istimewa `RETURNING` hanya kompatibel di instrumen SQLite v3.35 ke atas. Pemasangan baris ini seketika menumbangkan fungsionalitas tombol favorite bagi pengguna ponsel tua karena dilempar _Syntax Error_.
---

---
master_id: M-110
verification_status: VALID
verified_location: cache/schema.sql:24-27
code_evidence: 
```sql
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL
);
```
verification_note: Tabel penyimpan kunci otentikasi login admin tidak mengaplikasikan _B-Tree Index_ pada kolom penyortir waktu `expires_at`, melambatkan operasi pembersihan (cleanup) seiring menumpuknya session kadaluarsa.
---

---
master_id: M-111
verification_status: VALID
verified_location: cache/repositories/track_repository.py:44-55
code_evidence: 
```python
            INSERT INTO tracks (
...             local_path, last_played
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
...
                last_played=excluded.last_played
```
verification_note: Operasi menimpa/memperbaharui record _track_ mengikutsertakan parameter _last_played_ ke titik waktu saat ini (sekarang), meskipun fungsi _upsert_ juga dapat dipanggil dari interaksi ringan seperti caching tanpa pemutaran player sungguhan, merusak validitas daftar _Recently Played_.
---

---
master_id: M-112
verification_status: VALID
verified_location: cache/db.py:93-98, cache/schema.sql:30-31
code_evidence: 
```sql
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY,
    nama TEXT NOT NULL,
```
verification_note: Desain `artists.id` dicabut status `AUTOINCREMENT`-nya, lalu memaksakan suplai ID mutlak dari berkas JSON di dalam kode Python. Praktek ini amat rapuh merusak konsistensi _foreign keys_ manakala urutan array ID JSON tergusur.
---

---
master_id: M-113
verification_status: VALID
verified_location: cache/repositories/auth_repository.py:28-29
code_evidence: 
```python
            if row:
                await self.delete_session(token)
            return False
```
verification_note: Terjadi penyimpangan side-effect tak terduga; Fungsi yang namanya `verify_session` (yang sejatinya merupakan _Query/Read_) diimbuhi logika perintah menghancurkan sesi (`delete_session`).
---

---
master_id: M-114
verification_status: VALID
verified_location: cache/repositories/discover_repository.py:76-77
code_evidence: 
```sql
                SELECT s.youtube_id, s.judul, s.duration, a.nama,
                       ROW_NUMBER() OVER (PARTITION BY s.artist_id ORDER BY RANDOM()) as rn
```
verification_note: Query kalkulasi radio memanfaatkan fungsi rumit SQL Window `ROW_NUMBER()`, yang tidak diakui oleh piranti lama (SQLite rilis di bawah v3.25), memancing sistem menjadi lumpuh saat dibangkitkan pada lingkungan Android/Debian tua. 
---

---
master_id: M-115
verification_status: VALID
verified_location: cache/schema.sql:3-17
code_evidence: 
```sql
CREATE TABLE IF NOT EXISTS tracks (
    video_id     TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    artist       TEXT,
```
verification_note: Tabel primer `tracks` mengandalkan nama artis dalam format baris _string_ harfiah ketimbang merelasikan _foreign key_ `artist_id` ke dalam tabel `artists`. Menodai esensi normalisasi data (duplikat teks).
---
'''

with open('docs/verifikasi_ekstraksi.md', 'r', encoding='utf-8') as f:
    original_text = f.read()

# find where M-116 starts
match = re.search(r'---[\r\n]+master_id:\s*M-116\b', original_text)
if not match:
    print("Could not find M-116 in file! I will just append at the bottom as a fallback.")
    with open('docs/verifikasi_ekstraksi.md', 'a', encoding='utf-8') as f:
        f.write(text_to_insert)
else:
    insert_pos = match.start()
    new_text = original_text[:insert_pos] + text_to_insert + "\n" + original_text[insert_pos:]
    with open('docs/verifikasi_ekstraksi.md', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Successfully inserted M-101 to M-115 before M-116.")
