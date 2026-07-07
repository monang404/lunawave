# DATABASE AUDIT REPORT — LunaWave
**Auditor:** Database Architect + Senior Backend Engineer + Security Engineer + Performance Engineer  
**Scope:** `cache/schema.sql`, `cache/db.py`, `cache/resolver.py`, `cache/repositories/*`, `data/export_to_sqlite.py`, `config.py`, `core/state.py`  
**Exclusi:** `/archive`, `/arsip`, semua file `.md`  
**Engine:** SQLite via `aiosqlite`  
**Tanggal Audit:** 2026-07-07

---

## RINGKASAN EKSEKUTIF

Database LunaWave menggunakan SQLite dengan layer async (`aiosqlite`) dan satu persistent connection. Desainnya sederhana dan cocok untuk use case single-user/local. Namun terdapat **17 temuan** dengan severity mulai dari LOW hingga CRITICAL yang harus ditangani sebelum production release, terutama jika target adalah **jutaan user** (meski arsitektur saat ini adalah single-instance). Isu paling kritis: **single connection bottleneck**, **tidak ada migration system**, **schema drift antara schema.sql dan export_to_sqlite.py**, dan **race condition pada eviction + toggle favorite**.

---

## TEMUAN

---

### DB-001 — Single Persistent Connection: Write Bottleneck & Deadlock Risk
**Severity:** 🔴 CRITICAL  
**Kategori:** Bottleneck, Scalability, Race Condition

**Dampak:**  
Semua operasi database (read dan write) berbagi satu `aiosqlite` connection. Walau WAL mode diaktifkan, satu connection tunggal berarti semua coroutine antre secara serial. Jika satu operasi lambat (misal `evict_stale_tracks` yang melakukan SELECT + loop + DELETE), seluruh aplikasi akan stall. Pada high concurrency (banyak WebSocket client), ini menjadi choke point utama.

**Penyebab:**  
Desain satu connection dipilih sebagai "fix CRITICAL-04" (terlihat di komentar `db.py`). Ini memang lebih baik dari membuka connection baru setiap operasi, namun masih terlalu restriktif.

**Lokasi File:** `cache/db.py`

```python
# db.py — satu connection untuk semua
async def init(self):
    self._conn = await aiosqlite.connect(self.db_path)
    # ...
    self.tracks = TrackRepository(self._conn)
    self.sessions = AuthRepository(self._conn)
    self.discover = DiscoverRepository(self._conn)
```

Semua repository memegang referensi ke connection yang SAMA.

**Solusi:**  
Gunakan connection pool dengan reader/writer separation. Untuk SQLite dengan WAL mode, pola yang efektif adalah: **1 writer connection + N reader connections** (WAL mengizinkan concurrent reads).

```python
# db.py — connection pool pattern untuk SQLite WAL
import asyncio
import aiosqlite
from pathlib import Path

class Database:
    def __init__(self, db_path: Path, reader_pool_size: int = 4):
        self.db_path = db_path
        self._writer: aiosqlite.Connection | None = None
        self._reader_pool: asyncio.Queue[aiosqlite.Connection] = asyncio.Queue()
        self._reader_pool_size = reader_pool_size
        self._write_lock = asyncio.Lock()

    async def init(self):
        # Writer connection (serialized via lock)
        self._writer = await aiosqlite.connect(self.db_path)
        self._writer.row_factory = aiosqlite.Row
        await self._configure_conn(self._writer)

        # Reader pool
        for _ in range(self._reader_pool_size):
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row
            await self._configure_conn(conn)
            await self._reader_pool.put(conn)

    async def _configure_conn(self, conn):
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA foreign_keys=ON")
        await conn.execute("PRAGMA busy_timeout=5000")  # Lihat DB-002

    async def execute_write(self, query, params=()):
        async with self._write_lock:
            await self._writer.execute(query, params)
            await self._writer.commit()

    async def execute_read(self, query, params=()):
        conn = await self._reader_pool.get()
        try:
            async with conn.execute(query, params) as cursor:
                return await cursor.fetchall()
        finally:
            await self._reader_pool.put(conn)
```

---

### DB-002 — Tidak Ada `busy_timeout` PRAGMA
**Severity:** 🟠 HIGH  
**Kategori:** Bottleneck, Reliability

**Dampak:**  
Tanpa `PRAGMA busy_timeout`, jika ada dua proses/thread mencoba write ke SQLite secara bersamaan, SQLite langsung return `SQLITE_BUSY` (error) alih-alih menunggu. Ini dapat menyebabkan crash atau data loss saat ada background task (eviction, backup) berjalan bersamaan dengan operasi user.

**Penyebab:**  
`PRAGMA busy_timeout` tidak di-set di `db.init()`.

**Lokasi File:** `cache/db.py` — fungsi `init()`

```python
# Kondisi saat ini — tidak ada busy_timeout
await self._conn.execute("PRAGMA journal_mode=WAL")
await self._conn.execute("PRAGMA foreign_keys=ON")
# ← MISSING: busy_timeout
```

**Solusi:**

```python
async def init(self):
    self._conn = await aiosqlite.connect(self.db_path)
    self._conn.row_factory = aiosqlite.Row
    await self._conn.execute("PRAGMA journal_mode=WAL")
    await self._conn.execute("PRAGMA foreign_keys=ON")
    await self._conn.execute("PRAGMA busy_timeout=5000")   # tunggu 5 detik sebelum error
    await self._conn.execute("PRAGMA synchronous=NORMAL")  # lebih cepat, masih aman dengan WAL
    await self._conn.execute("PRAGMA cache_size=-32000")   # 32MB page cache
    await self._conn.execute("PRAGMA temp_store=MEMORY")
```

---

### DB-003 — Tidak Ada Migration System
**Severity:** 🔴 CRITICAL  
**Kategori:** Schema Management, Maintainability, Technical Debt

**Dampak:**  
Schema dikelola dengan dua mekanisme berbeda yang konflik:
1. `schema.sql` dijalankan via `executescript()` — idempotent karena `CREATE TABLE IF NOT EXISTS`
2. `add_column_if_not_exists()` — manual column addition secara runtime

Tidak ada versioning, tidak ada rollback, tidak ada tracking versi schema. Jika kolom yang sama ditambahkan dua kali via `ALTER TABLE`, atau jika urutan startup berubah, dapat terjadi error tak terduga. Tidak bisa tahu apakah database di user sudah di versi schema berapa.

**Penyebab:**  
Tidak ada migrasi framework atau sistem versi schema.

**Lokasi File:** `cache/db.py`

```python
# Pendekatan manual yang rapuh
async def add_column_if_not_exists(table, column, definition):
    async with self._conn.execute(f"PRAGMA table_info({table})") as cursor:
        columns = [row["name"] for row in await cursor.fetchall()]
    if column not in columns:
        await self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

await add_column_if_not_exists("tracks", "is_favorite", "INTEGER DEFAULT 0")
await add_column_if_not_exists("artists", "click_count", "INTEGER DEFAULT 0")
await add_column_if_not_exists("genres", "click_count", "INTEGER DEFAULT 0")
```

Tiga kolom (`is_favorite`, `click_count`) di-add secara runtime tapi juga ada di `schema.sql`. Ini berarti:
- User baru: kolom dibuat via schema.sql, lalu `add_column_if_not_exists` jalan tapi no-op
- User lama: kolom tidak ada di schema lama, `add_column_if_not_exists` menambahkannya
- **Risk:** jika schema.sql diupdate tapi migration manual tidak diupdate, atau sebaliknya

**Solusi:** Implementasikan table `schema_migrations` sederhana:

```python
# cache/migrations.py
MIGRATIONS = [
    # (version, sql)
    (1, """
        CREATE TABLE IF NOT EXISTS tracks (
            video_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            ...
        )
    """),
    (2, "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0"),
    (3, "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0"),
    (4, "ALTER TABLE genres ADD COLUMN click_count INTEGER DEFAULT 0"),
    # Tambah migration baru di sini
]

async def run_migrations(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at INTEGER NOT NULL
        )
    """)
    async with conn.execute("SELECT MAX(version) FROM schema_migrations") as cur:
        row = await cur.fetchone()
        current_version = row[0] or 0

    for version, sql in MIGRATIONS:
        if version > current_version:
            await conn.executescript(sql)
            await conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, int(time.time()))
            )
            await conn.commit()
            logger.info(f"Applied migration v{version}")
```

---

### DB-004 — Schema Drift: `schema.sql` vs `export_to_sqlite.py`
**Severity:** 🟠 HIGH  
**Kategori:** Schema Consistency, Technical Debt

**Dampak:**  
Dua file mendefinisikan schema tabel yang sama (`artists`, `genres`, `artist_genres`, `songs`) secara terpisah. Keduanya **tidak sinkron**:

| Elemen | `schema.sql` | `export_to_sqlite.py` |
|---|---|---|
| `PRAGMA foreign_keys` | Diset di `db.init()` | ❌ Tidak di-set |
| `CREATE INDEX` | Ada di schema.sql | ❌ Tidak ada |
| `UNIQUE INDEX artists(nama)` | Ada | ❌ Tidak ada |
| `click_count` di artists/genres | Ditambah runtime | ❌ Tidak ada |
| WAL mode | Ada | ❌ Tidak ada |

Jika seseorang menggunakan `export_to_sqlite.py` untuk generate database, hasilnya adalah database tanpa index, tanpa unique constraint pada nama artis, dan tanpa foreign key enforcement — menyebabkan data corruption yang sulit dideteksi.

**Lokasi File:** `data/export_to_sqlite.py`, `cache/schema.sql`

```python
# export_to_sqlite.py — schema duplikat, berbeda dari schema.sql
def create_tables(cursor):
    cursor.execute('DROP TABLE IF EXISTS songs')      # ← DROP table!
    cursor.execute('DROP TABLE IF EXISTS artist_genres')
    cursor.execute('DROP TABLE IF EXISTS genres')
    cursor.execute('DROP TABLE IF EXISTS artists')
    # ... CREATE ulang tanpa index, tanpa foreign_keys PRAGMA
```

`export_to_sqlite.py` juga melakukan `DROP TABLE` — berbahaya jika dijalankan pada database production yang sudah berisi data `tracks` dan `sessions`.

**Solusi:**  
Hapus schema definition dari `export_to_sqlite.py`. Gunakan single source of truth (`schema.sql`) dan jalankan via `Database.init()`:

```python
# export_to_sqlite.py — refactored
import asyncio
from cache.db import Database
from pathlib import Path

async def main():
    db = Database(db_path=Path("data/lunawave.db"))
    await db.init()  # Gunakan schema dan migration yang sama
    # seed data sudah otomatis via _seed_initial_data()
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

### DB-005 — `INSERT OR REPLACE` pada Tabel `artists`: Data Loss Risk
**Severity:** 🟠 HIGH  
**Kategori:** Data Integrity, Constraint

**Dampak:**  
Saat seeding data, digunakan `INSERT OR REPLACE INTO artists`. `OR REPLACE` di SQLite bekerja dengan cara **DELETE + INSERT** — ini berarti `click_count` yang sudah terakumulasi dari user akan **direset ke NULL** setiap kali re-seed (misal saat `_seed_initial_data()` dijalankan di future).

Meski saat ini `_seed_initial_data()` hanya jalan jika `COUNT(*) = 0`, ini adalah time bomb jika logika seeding diubah.

**Lokasi File:** `cache/db.py` — `_seed_initial_data()`

```python
# Berbahaya: OR REPLACE menghapus row lama dulu, termasuk click_count
await self._conn.execute('''
    INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif)
    VALUES (?, ?, ?, ?)
''', (artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))
```

**Solusi:** Gunakan `INSERT OR IGNORE` atau `ON CONFLICT DO UPDATE` yang eksplisit:

```python
await self._conn.execute('''
    INSERT INTO artists (id, nama, kategori, tahun_aktif)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        nama = excluded.nama,
        kategori = excluded.kategori,
        tahun_aktif = excluded.tahun_aktif
        -- TIDAK mengupdate click_count — preserves accumulated data
''', (artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))
```

---

### DB-006 — Race Condition: `evict_stale_tracks()` SELECT + DELETE Non-Atomic
**Severity:** 🟠 HIGH  
**Kategori:** Race Condition, Data Integrity

**Dampak:**  
`evict_stale_tracks()` melakukan SELECT lalu DELETE dalam dua operasi terpisah. Antara SELECT dan DELETE, track yang baru saja mulai diplay (dan `last_played` baru diupdate) bisa ikut terhapus karena data masih stale di hasil SELECT.

**Lokasi File:** `cache/repositories/track_repository.py`

```python
# Race condition: track bisa di-play antara SELECT dan DELETE ini
cursor = await self._conn.execute(
    """SELECT video_id FROM tracks
       WHERE play_count = 0
         AND local_path IS NULL
         AND (is_favorite = 0 OR is_favorite IS NULL)
         AND (stream_url_ts IS NULL OR stream_url_ts < ?)""",
    (thirty_days_ago,)
)
rows = await cursor.fetchall()
# ← GAP: track bisa mulai diplay di sini
video_ids = [r["video_id"] for r in rows]
# ...
await self._conn.execute(
    f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids
)
```

**Solusi:** Gabungkan menjadi satu operasi atomik menggunakan subquery atau BEGIN/COMMIT:

```python
async def evict_stale_tracks(self) -> int:
    if not self._conn: return 0
    thirty_days_ago = int(time.time()) - (30 * 24 * 3600)

    # Atomik: DELETE dengan kondisi langsung, tidak ada SELECT terpisah
    cursor = await self._conn.execute(
        """DELETE FROM tracks
           WHERE play_count = 0
             AND local_path IS NULL
             AND (is_favorite = 0 OR is_favorite IS NULL)
             AND (stream_url_ts IS NULL OR stream_url_ts < ?)
           RETURNING video_id""",
        (thirty_days_ago,)
    )
    deleted_rows = await cursor.fetchall()
    await self._conn.commit()

    video_ids = [r["video_id"] for r in deleted_rows]

    # Hapus file setelah DB commit (urutan ini penting)
    from config import CACHE_DIR
    for vid in video_ids:
        p = CACHE_DIR / f"{vid}.mp3"
        if p.exists():
            try:
                p.unlink()
            except Exception as e:
                logger.error(f"Gagal hapus file cache {p}: {e}")

    logger.info(f"Eviction: {len(video_ids)} track stale dihapus")
    return len(video_ids)
```

---

### DB-007 — `toggle_favorite()` Tidak Menggunakan Transaksi Eksplisit
**Severity:** 🟡 MEDIUM  
**Kategori:** Race Condition, Consistency

**Dampak:**  
Dua request `toggle_favorite` yang datang hampir bersamaan (misal double-tap pada mobile) keduanya membaca `is_favorite` yang sama dan menghasilkan hasil yang salah — dua toggle seharusnya kembali ke nilai semula, tapi karena tidak ada lock, bisa terjadi kedua operasi membaca nilai yang sama.

**Lokasi File:** `cache/repositories/track_repository.py`

```python
async def toggle_favorite(self, video_id: str) -> int:
    # Tidak ada BEGIN EXCLUSIVE — bisa race
    async with self._conn.execute(
        """UPDATE tracks
           SET is_favorite = 1 - COALESCE(is_favorite, 0)
           WHERE video_id = ?
           RETURNING is_favorite""",
        (video_id,)
    ) as cursor:
        row = await cursor.fetchone()
    await self._conn.commit()
    return row["is_favorite"] if row else 0
```

**Solusi:** Gunakan `BEGIN IMMEDIATE` untuk serialisasi write:

```python
async def toggle_favorite(self, video_id: str) -> int:
    if not self._conn: return 0
    async with self._write_lock:  # Jika menggunakan pola DB-001
        await self._conn.execute("BEGIN IMMEDIATE")
        try:
            async with self._conn.execute(
                """UPDATE tracks
                   SET is_favorite = 1 - COALESCE(is_favorite, 0)
                   WHERE video_id = ?
                   RETURNING is_favorite""",
                (video_id,)
            ) as cursor:
                row = await cursor.fetchone()
            await self._conn.commit()
            return row["is_favorite"] if row else 0
        except Exception:
            await self._conn.rollback()
            raise
```

---

### DB-008 — `sessions` Table: Tidak Ada Index pada `expires_at`
**Severity:** 🟡 MEDIUM  
**Kategori:** Index, Performance

**Dampak:**  
`cleanup_sessions()` melakukan `DELETE FROM sessions WHERE expires_at <= ?`. Tanpa index pada `expires_at`, ini adalah full table scan setiap kali cleanup berjalan. Meski tabel sessions mungkin kecil sekarang, pada aplikasi multi-user ini bisa menjadi bottleneck.

**Lokasi File:** `cache/schema.sql`

```sql
-- schema.sql — sessions table tidak punya index
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL
);
-- ← MISSING INDEX pada expires_at
```

`verify_session()` juga melakukan lookup by token (sudah index karena PRIMARY KEY), tapi cleanup tidak dioptimasi.

**Solusi:**

```sql
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
```

---

### DB-009 — Missing Index: `tracks.is_favorite` untuk Query Favorites
**Severity:** 🟡 MEDIUM  
**Kategori:** Index, Performance

**Dampak:**  
Tidak ada index pada kolom `is_favorite`. Setiap query yang memfilter favorite tracks (untuk ditampilkan di UI, atau saat eviction) harus full table scan.

Kolom `is_favorite` juga digunakan di `evict_stale_tracks()` sebagai filter `WHERE is_favorite = 0 OR is_favorite IS NULL` — full scan setiap 30 hari sekali masih dapat diterima, tapi index tetap direkomendasikan untuk kebutuhan query favorites di masa depan.

**Lokasi File:** `cache/schema.sql`

**Solusi:**

```sql
-- Partial index hanya untuk favorites (lebih efisien)
CREATE INDEX IF NOT EXISTS idx_tracks_is_favorite ON tracks(is_favorite) WHERE is_favorite = 1;
```

---

### DB-010 — `upsert_track()` Selalu Update `last_played`
**Severity:** 🟡 MEDIUM  
**Kategori:** Data Integrity, Logic Bug

**Dampak:**  
Setiap kali `upsert_track()` dipanggil (termasuk saat hanya menyimpan metadata atau stream URL), `last_played` diset ke `int(time.time())`. Ini menyebabkan track yang hanya di-resolve URL-nya (tanpa benar-benar diputar) memiliki `last_played` yang ter-update, mengacaukan sorting "recently played" dan mencegah eviction dari track yang belum pernah benar-benar diputar.

**Lokasi File:** `cache/repositories/track_repository.py`

```python
async def upsert_track(self, track: TrackInfo, stream_url: str = None, local_path: str = None) -> None:
    ts = int(time.time())
    query = """
        INSERT INTO tracks (
            video_id, title, artist, duration, view_count, thumbnail,
            stream_url, stream_url_ts, local_path, last_played  -- ← last_played selalu diisi
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(video_id) DO UPDATE SET
            ...
            last_played=excluded.last_played  -- ← selalu diupdate
    """
    await self._conn.execute(query, (
        ..., ts  # ts selalu dipakai sebagai last_played
    ))
```

**Solusi:** Pisahkan `last_played` update — hanya di-set ketika track benar-benar diputar (di `increment_play_count`):

```python
async def upsert_track(self, track: TrackInfo, stream_url: str = None, local_path: str = None) -> None:
    if not self._conn: return
    ts = int(time.time())
    query = """
        INSERT INTO tracks (
            video_id, title, artist, duration, view_count, thumbnail,
            stream_url, stream_url_ts, local_path
            -- HAPUS last_played dari INSERT
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(video_id) DO UPDATE SET
            title=excluded.title,
            artist=excluded.artist,
            duration=excluded.duration,
            view_count=excluded.view_count,
            thumbnail=excluded.thumbnail,
            stream_url=COALESCE(excluded.stream_url, tracks.stream_url),
            stream_url_ts=COALESCE(excluded.stream_url_ts, tracks.stream_url_ts),
            local_path=COALESCE(excluded.local_path, tracks.local_path)
            -- HAPUS last_played dari UPDATE
    """
    await self._conn.execute(query, (
        track.video_id, track.title, track.artist, track.duration,
        track.view_count, track.thumbnail,
        stream_url, ts if stream_url else None,
        local_path
    ))
    await self._conn.commit()
```

---

### DB-011 — `artists.id` bukan AUTOINCREMENT: Risk pada Re-seed
**Severity:** 🟡 MEDIUM  
**Kategori:** Schema Design, Normalization

**Dampak:**  
`artists.id` didefinisikan sebagai `INTEGER PRIMARY KEY` (tanpa AUTOINCREMENT), dan ID-nya berasal dari JSON data (`artist['id']`). Jika JSON sumber diubah (artis dihapus lalu ditambah dengan id baru), atau jika ada dua sumber data berbeda yang di-merge, bisa terjadi ID conflict atau orphaned foreign key references.

**Lokasi File:** `cache/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY,   -- ← manual ID dari JSON, bukan AUTOINCREMENT
    nama TEXT NOT NULL,
    kategori TEXT,
    tahun_aktif TEXT
);
```

**Solusi:**  
Gunakan `nama` sebagai natural key untuk lookup (sudah ada `UNIQUE INDEX idx_artists_nama_unique`), dan biarkan `id` AUTOINCREMENT untuk internal FK reference:

```sql
CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL UNIQUE,
    kategori TEXT,
    tahun_aktif TEXT,
    click_count INTEGER DEFAULT 0
);
```

Update seeding untuk INSERT berdasarkan `nama` (unique), bukan `id`:

```sql
INSERT INTO artists (nama, kategori, tahun_aktif)
VALUES (?, ?, ?)
ON CONFLICT(nama) DO UPDATE SET
    kategori = excluded.kategori,
    tahun_aktif = excluded.tahun_aktif
```

---

### DB-012 — `__getattr__` Proxy di `Database`: Anti-Pattern Berbahaya
**Severity:** 🟡 MEDIUM  
**Kategori:** Design Flaw, Maintainability, Debugging Difficulty

**Dampak:**  
`Database.__getattr__` mencari method di tiga repository secara berurutan. Ini menyembunyikan dependency graph, membuat stack trace sulit dibaca, dan dapat menyebabkan metode yang salah terpanggil jika nama method overlap di dua repository (meski saat ini tidak terjadi). Juga menyebabkan `AttributeError` yang misleading — pesan errornya `'Database' object has no attribute 'X'` padahal sebenarnya yang tidak ada adalah repository yang belum diinit.

**Lokasi File:** `cache/db.py`

```python
def __getattr__(self, name):
    """Proxy missing methods to the repositories to maintain backward compatibility."""
    if self.tracks and hasattr(self.tracks, name):
        return getattr(self.tracks, name)
    if self.sessions and hasattr(self.sessions, name):
        return getattr(self.sessions, name)
    if self.discover and hasattr(self.discover, name):
        return getattr(self.discover, name)
    raise AttributeError(f"'Database' object has no attribute '{name}'")
```

**Solusi:** Hapus `__getattr__` dan akses repository langsung. Tambahkan property shortcut jika diperlukan:

```python
# Akses eksplisit — lebih aman dan mudah debug
db.tracks.get_track(video_id)
db.sessions.verify_session(token)
db.discover.get_random_songs(limit=12)

# Jika backward compat diperlukan, gunakan explicit delegation:
class Database:
    # Delegation eksplisit — visible, traceable
    async def get_track(self, video_id): 
        return await self.tracks.get_track(video_id)
    
    async def verify_session(self, token):
        return await self.sessions.verify_session(token)
```

---

### DB-013 — `verify_session()`: Side Effect Write dalam Read Operation
**Severity:** 🟡 MEDIUM  
**Kategori:** Design Flaw, SRP Violation, Performance

**Dampak:**  
`verify_session()` melakukan DELETE (hapus expired session) sebagai side effect dari operasi baca. Ini melanggar prinsip Command-Query Separation. Jika `verify_session()` dipanggil berkali-kali dalam satu request, bisa terjadi multiple write operations yang tidak perlu. Juga menyulitkan caching/memoization `verify_session`.

**Lokasi File:** `cache/repositories/auth_repository.py`

```python
async def verify_session(self, token: str) -> bool:
    async with self._conn.execute(
        "SELECT expires_at FROM sessions WHERE token = ?", (token,)
    ) as cursor:
        row = await cursor.fetchone()
        if row and row["expires_at"] > now:
            return True
        if row:
            await self.delete_session(token)  # ← WRITE dalam READ operation!
        return False
```

**Solusi:** Pisahkan verifikasi dan cleanup. Biarkan `cleanup_sessions()` periodic task yang menangani expired sessions:

```python
async def verify_session(self, token: str) -> bool:
    """Pure read — hanya verifikasi, tidak ada side effect."""
    if not self._conn: return False
    now = int(time.time())
    async with self._conn.execute(
        "SELECT expires_at FROM sessions WHERE token = ? AND expires_at > ?",
        (token, now)
    ) as cursor:
        row = await cursor.fetchone()
        return row is not None

# cleanup_sessions() sudah ada dan harus dipanggil secara periodik
# oleh background task, bukan oleh verify_session()
```

---

### DB-014 — `get_random_songs()`: CTE dengan `RANDOM()` Tidak Deterministik & Slow
**Severity:** 🟡 MEDIUM  
**Kategori:** Performance, Query Design

**Dampak:**  
Query `get_random_songs()` menggunakan `ROW_NUMBER() OVER (PARTITION BY s.artist_id ORDER BY RANDOM())`. Di SQLite, `RANDOM()` dievaluasi per-row untuk setiap partition, yang menyebabkan **full table scan** pada `songs` setiap kali query ini dijalankan. Untuk dataset kecil ini tidak masalah, tapi saat data songs banyak (>100k), ini menjadi O(N) operation setiap radio track load.

**Lokasi File:** `cache/repositories/discover_repository.py`

```sql
WITH RankedSongs AS (
    SELECT s.youtube_id, s.judul, s.duration, a.nama,
           ROW_NUMBER() OVER (PARTITION BY s.artist_id ORDER BY RANDOM()) as rn
    FROM songs s
    JOIN artists a ON s.artist_id = a.id
    WHERE 1=1
    -- ← Full scan songs + artists untuk setiap radio request
)
SELECT youtube_id, judul, duration, nama
FROM RankedSongs
WHERE rn <= ?
ORDER BY RANDOM() LIMIT ?
```

**Solusi:** Untuk dataset skala jutaan user, pertimbangkan pre-computed random order atau materialized view. Untuk skala saat ini, batasi dengan index dan tambahkan caching di level aplikasi:

```python
# Tambahkan simple in-memory cache dengan TTL
import time
from functools import lru_cache

class DiscoverRepository:
    def __init__(self, db_conn):
        self._conn = db_conn
        self._song_cache: list = []
        self._song_cache_ts: float = 0
        self._CACHE_TTL = 300  # 5 menit

    async def get_random_songs(self, limit=12, exclude_ids=None, ...):
        # Gunakan cached pool jika masih fresh
        now = time.time()
        if not self._song_cache or now - self._song_cache_ts > self._CACHE_TTL:
            self._song_cache = await self._load_all_songs()
            self._song_cache_ts = now
        
        # Shuffle + filter in-memory (jauh lebih cepat)
        import random
        pool = [s for s in self._song_cache if s.video_id not in (exclude_ids or set())]
        random.shuffle(pool)
        return pool[:limit]
```

---

### DB-015 — `evict_stale_tracks()`: File Delete Sebelum DB Commit
**Severity:** 🟡 MEDIUM  
**Kategori:** Data Consistency, Atomicity

**Dampak:**  
Dalam implementasi asli, file dihapus di dalam loop **sebelum** `await self._conn.commit()`. Jika aplikasi crash setelah file dihapus tapi sebelum DB commit, maka record di DB masih ada (`local_path` menunjuk ke file yang sudah tidak ada), menyebabkan inconsistency antara DB dan filesystem.

**Lokasi File:** `cache/repositories/track_repository.py`

```python
for vid in video_ids:
    p = CACHE_DIR / f"{vid}.mp3"
    if p.exists():
        p.unlink()          # ← File dihapus dulu

# ...
await self._conn.execute(f"DELETE FROM tracks WHERE video_id IN ({placeholders})", video_ids)
await self._conn.commit()   # ← Baru commit ke DB
```

**Solusi:** Urutan harus: **DB commit dulu, baru hapus file** (seperti sudah diperbaiki di solusi DB-006). DB adalah source of truth; jika file masih ada tapi record DB sudah terhapus, itu hanya space leak yang bisa dibersihkan. Tapi jika record ada tapi file tidak ada, aplikasi akan crash saat mencoba memutarnya.

---

### DB-016 — Tidak Ada Normalisasi: `TrackInfo.artist` Duplikat Data
**Severity:** 🟢 LOW  
**Kategori:** Normalization, Technical Debt

**Dampak:**  
Di tabel `tracks`, kolom `artist` disimpan sebagai TEXT bebas (tidak ada FK ke tabel `artists`). Ini menyebabkan:
- Nama artis bisa tidak konsisten ("Iwan Fals" vs "iwan fals" vs "Iwan Fals (Official)")
- Tidak bisa join antara `tracks` yang diputar user dengan data `artists` di database
- Tidak bisa menghitung statistik per artis dari riwayat play

**Lokasi File:** `cache/schema.sql`

```sql
CREATE TABLE IF NOT EXISTS tracks (
    video_id     TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    artist       TEXT,     -- ← plain text, bukan FK ke artists
    ...
);
```

**Solusi (Long-term):**  
Tambahkan kolom `artist_id` sebagai soft FK (nullable, karena tidak semua track ada di tabel `artists`):

```sql
ALTER TABLE tracks ADD COLUMN artist_id INTEGER REFERENCES artists(id);
CREATE INDEX IF NOT EXISTS idx_tracks_artist_id ON tracks(artist_id) WHERE artist_id IS NOT NULL;
```

Buat background job untuk resolve `artist` text → `artist_id` FK secara asinkron.

---

### DB-017 — `CacheResolver._fetching`: Memory Leak jika Exception
**Severity:** 🟡 MEDIUM  
**Kategori:** Memory Leak, Race Condition

**Dampak:**  
`CacheResolver._fetching` adalah dict yang menyimpan `asyncio.Event` per `video_id` yang sedang di-fetch. Jika `ytdlp.get_stream_url()` throw exception yang tidak ter-handle, `finally` block memang memanggil `event.set()` dan `_fetching.pop()` — ini sudah benar. Namun, jika coroutine yang menunggu (`await self._fetching[track.video_id].wait()`) kemudian memanggil `resolve()` lagi (recursive call), dan pada resolve kedua terjadi error, tidak ada proteksi terhadap infinite recursion atau event yang tidak di-set.

**Lokasi File:** `cache/resolver.py`

```python
if track.video_id in self._fetching:
    await self._fetching[track.video_id].wait()
    return await self.resolve(track)  # ← Recursive call tanpa depth limit
```

Jika resolve yang pertama gagal tapi event di-set, resolve kedua (recursive) akan mencoba fetch lagi, dan seterusnya.

**Solusi:** Batasi retry dan tambahkan max recursion guard:

```python
async def resolve(self, track: TrackInfo, _depth: int = 0) -> str:
    if _depth > 2:
        raise RuntimeError(f"Resolve depth exceeded untuk {track.video_id}")
    
    # ...existing logic...
    
    if track.video_id in self._fetching:
        try:
            await asyncio.wait_for(
                self._fetching[track.video_id].wait(),
                timeout=30.0  # Jangan tunggu selamanya
            )
        except asyncio.TimeoutError:
            raise RuntimeError(f"Timeout menunggu fetch untuk {track.video_id}")
        return await self.resolve(track, _depth=_depth + 1)
```

---

## MATRIKS TEMUAN

| ID | Judul | Severity | Kategori |
|---|---|---|---|
| DB-001 | Single Connection Bottleneck | 🔴 CRITICAL | Bottleneck, Scalability |
| DB-002 | Tidak Ada `busy_timeout` | 🟠 HIGH | Reliability |
| DB-003 | Tidak Ada Migration System | 🔴 CRITICAL | Schema Management |
| DB-004 | Schema Drift `.sql` vs `.py` | 🟠 HIGH | Consistency |
| DB-005 | `INSERT OR REPLACE` Data Loss | 🟠 HIGH | Data Integrity |
| DB-006 | Race Condition Eviction | 🟠 HIGH | Race Condition |
| DB-007 | Toggle Favorite Non-Atomic | 🟡 MEDIUM | Race Condition |
| DB-008 | Missing Index `sessions.expires_at` | 🟡 MEDIUM | Index, Performance |
| DB-009 | Missing Index `tracks.is_favorite` | 🟡 MEDIUM | Index |
| DB-010 | `upsert_track` Selalu Update `last_played` | 🟡 MEDIUM | Logic Bug |
| DB-011 | `artists.id` Manual ID Risk | 🟡 MEDIUM | Schema Design |
| DB-012 | `__getattr__` Proxy Anti-Pattern | 🟡 MEDIUM | Design Flaw |
| DB-013 | Write Side Effect dalam Read | 🟡 MEDIUM | Design Flaw |
| DB-014 | `get_random_songs()` Full Scan | 🟡 MEDIUM | Performance |
| DB-015 | File Delete Sebelum DB Commit | 🟡 MEDIUM | Atomicity |
| DB-016 | Denormalisasi `tracks.artist` | 🟢 LOW | Normalization |
| DB-017 | `CacheResolver` Recursive Resolve | 🟡 MEDIUM | Memory Leak |

---

## REKOMENDASI PRIORITAS

### 🔴 Immediate (sebelum production)
1. **DB-003** — Implementasikan migration system. Ini adalah fondasi dari semua perubahan schema ke depan.
2. **DB-001** — Migrasi ke reader/writer connection pool untuk menghindari write starvation.
3. **DB-006** — Fix race condition di `evict_stale_tracks()` dengan atomic DELETE RETURNING.

### 🟠 Short-term (sprint pertama)
4. **DB-004** — Konsolidasi schema ke single source of truth, hapus duplikasi di `export_to_sqlite.py`.
5. **DB-005** — Ganti `INSERT OR REPLACE` dengan `ON CONFLICT DO UPDATE` yang eksplisit.
6. **DB-002** — Tambahkan `PRAGMA busy_timeout` dan tuning PRAGMA lain.

### 🟡 Medium-term (sprint berikutnya)
7. **DB-007, DB-013** — Perbaiki atomicity dan CQS violation.
8. **DB-008, DB-009** — Tambahkan index yang hilang.
9. **DB-010** — Fix `last_played` update logic.
10. **DB-012, DB-017** — Refactor `__getattr__` proxy dan resolver recursion guard.

### 🟢 Long-term (backlog)
11. **DB-011, DB-016** — Normalisasi schema untuk skalabilitas.
12. **DB-014** — Caching layer untuk `get_random_songs()` jika dataset membesar.

---

## CATATAN ARSITEKTUR

**SQLite untuk Production Jutaan User:**  
SQLite secara fundamental adalah embedded database untuk single-writer workload. Untuk aplikasi dengan jutaan concurrent users, SQLite **bukan pilihan yang tepat** tanpa layer abstraksi yang kuat (seperti Litestream untuk replication, atau migrasi ke PostgreSQL). Jika LunaWave dimaksudkan sebagai aplikasi personal/self-hosted (bukan multi-tenant SaaS), SQLite dapat dipertahankan dengan perbaikan di atas. Jika target adalah multi-tenant cloud deployment, pertimbangkan migrasi ke **PostgreSQL + asyncpg** dengan connection pooling via **PgBouncer**.

**WAL Mode — Sudah Benar:**  
Penggunaan WAL (`PRAGMA journal_mode=WAL`) adalah keputusan tepat untuk aplikasi yang memiliki lebih banyak read dari write. WAL memungkinkan concurrent reads tanpa blocking writer.

**Foreign Keys — Sudah Aktif:**  
`PRAGMA foreign_keys=ON` sudah diset di `db.init()`. Namun, ini hanya berlaku per-connection — jika ada connection lain yang membuka DB tanpa PRAGMA ini, FK tidak akan dienforce.
