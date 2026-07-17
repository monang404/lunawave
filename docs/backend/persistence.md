# Persistence

← [architecture/backend.md](../architecture/backend.md) | [Blueprint.md](../Blueprint.md)

---

## Gambaran Umum

LunaWave menyimpan data di **SQLite** via `persistence/`. Domain tidak mengakses database secara langsung — semua lewat repository yang mengimplementasikan interface dari `core/ports.py`.

Alasan pilih SQLite atas JSON cache → [ADR-0002](../adr/0002-sqlite-over-json-cache.md)

---

## Struktur `persistence/`

```
persistence/
├── db.py            Inisialisasi SQLite, connection pool
├── schema.sql       DDL — single source of truth skema database
├── track_repo.py    CRUD track
├── session_repo.py  CRUD session playback
├── artist_repo.py   CRUD artis
├── genre_repo.py    CRUD genre
├── library_repo.py  Query library (filter, sort, search)
└── __init__.py      Facade Database, backward-compat import
```

---

## Skema Database

### `tracks`

```sql
CREATE TABLE tracks (
    id          TEXT PRIMARY KEY,        -- video_id dari YouTube
    title       TEXT NOT NULL,
    artist      TEXT NOT NULL,
    duration    INTEGER NOT NULL,        -- detik
    thumbnail   TEXT,                    -- URL thumbnail
    file_path   TEXT,                    -- NULL jika belum didownload
    play_count  INTEGER DEFAULT 0,
    last_played TEXT,                    -- ISO 8601
    added_at    TEXT NOT NULL,           -- ISO 8601
    genre_id    INTEGER REFERENCES genres(id)
);
```

### `sessions`

```sql
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    track_count INTEGER DEFAULT 0,
    mode        TEXT DEFAULT 'normal'    -- normal | radio | shuffle
);
```

### `artists`

```sql
CREATE TABLE artists (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    play_count  INTEGER DEFAULT 0,
    last_played TEXT
);
```

### `genres`

```sql
CREATE TABLE genres (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE
);
```

> **Single Source of Truth:** Skema hanya ada di `persistence/schema.sql`. Tidak ada DDL yang diduplikasi di tempat lain.

---

## Repository API

### `TrackRepository` (`track_repo.py`)

```python
class TrackRepository:
    async def get(self, video_id: str) -> TrackInfo | None
    async def get_all(self) -> list[TrackInfo]
    async def save(self, track: TrackInfo) -> None
    async def delete(self, video_id: str) -> None
    async def increment_play_count(self, video_id: str) -> None
    async def update_last_played(self, video_id: str) -> None
    async def search(self, query: str) -> list[TrackInfo]
```

### `SessionRepository` (`session_repo.py`)

```python
class SessionRepository:
    async def start_session(self, mode: str) -> int          # returns session_id
    async def end_session(self, session_id: int) -> None
    async def increment_track_count(self, session_id: int) -> None
    async def get_recent(self, limit: int = 10) -> list[Session]
```

### `ArtistRepository` (`artist_repo.py`)

```python
class ArtistRepository:
    async def get_or_create(self, name: str) -> Artist
    async def increment_play_count(self, name: str) -> None
    async def get_top(self, limit: int = 20) -> list[Artist]
    async def get_all(self) -> list[Artist]
```

### `GenreRepository` (`genre_repo.py`)

```python
class GenreRepository:
    async def get_or_create(self, name: str) -> Genre
    async def get_all(self) -> list[Genre]
```

### `LibraryRepository` (`library_repo.py`)

Query kompleks untuk library view — filter, sort, pagination.

```python
class LibraryRepository:
    async def get_library(
        self,
        query: str | None = None,
        artist: str | None = None,
        genre: str | None = None,
        sort_by: str = "last_played",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[TrackInfo]

    async def get_stats(self) -> LibraryStats
    # LibraryStats: total_tracks, total_artists, total_duration, most_played
```

---

## Inisialisasi Database (`db.py`)

```python
class Database:
    def __init__(self, path: str = "data/lunawave.db"):
        self.path = path

    async def initialize(self) -> None:
        # Buat file DB jika belum ada
        # Jalankan schema.sql
        # Jalankan migrasi jika versi skema berbeda

    async def get_connection(self) -> aiosqlite.Connection:
        ...
```

**Untuk testing:** gunakan `Database(":memory:")` — database in-memory yang dibuat ulang setiap test.

```python
# conftest.py
@pytest.fixture
async def db():
    database = Database(":memory:")
    await database.initialize()
    yield database
    await database.close()
```

---

## Data Statis — `artists_enriched.json`

Bukan bagian dari database runtime. File ini adalah **sumber data statis** untuk enrichment artis (genre, nama alternatif, popularitas).

```
data/artists_enriched.json   ← di-commit ke repo, bukan di-gitignore
data/lunawave.db             ← runtime, di-gitignore
```

Format:
```json
[
  {
    "name": "Radiohead",
    "genres": ["alternative rock", "art rock"],
    "aliases": ["Radiohead"],
    "popularity": 92
  }
]
```

Digunakan oleh `discover_service.py` untuk rekomendasi dan `radio/artist_selector.py` untuk mode radio.

---

## Migrasi Skema

Migrasi dilakukan via `automation/export_to_sqlite.py` untuk data lama (dari format JSON cache).

Untuk skema baru: tambahkan file `persistence/migrations/V{N}__description.sql` dan panggil dari `db.py` saat inisialisasi.

---

## Testing

Semua repository dapat di-test dengan SQLite in-memory:

```python
# Contoh test track_repo
async def test_save_and_get(db):
    repo = TrackRepository(db)
    track = TrackInfo(video_id="abc", title="Test", artist="Artist", duration=180, thumbnail_url="")
    await repo.save(track)
    result = await repo.get("abc")
    assert result.title == "Test"
```

Test → `tests/unit/persistence/`

---

## Dokumen Terkait

- [backend/caching.md](caching.md) — Cache resolver (bukan persistence, tapi berkaitan)
- [architecture/domain.md](../architecture/domain.md) — `TrackInfo` domain object
- [architecture/folder_structure.md](../architecture/folder_structure.md) — Lokasi file di repo
- [ADR-0002](../adr/0002-sqlite-over-json-cache.md) — Kenapa SQLite?
