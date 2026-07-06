import time
from pathlib import Path

import aiosqlite
import structlog

from config import DB_PATH
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

class Database:
    """
    CRITICAL-04 fix: Uses a single persistent connection instead of
    opening a new connection for every operation.
    MED-10 fix: Added separate increment_play_count method.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._schema_path = Path(__file__).parent / "schema.sql"
        self._conn = None
        self.tracks = None
        self.sessions = None
        self.discover = None

    @property
    def conn(self):
        return self._conn

    async def init(self):
        """Initializes the database using the schema.sql file."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")

        with open(self._schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        await self._conn.executescript(schema_sql)

        async def add_column_if_not_exists(table, column, definition):
            assert self._conn is not None
            async with self._conn.execute(f"PRAGMA table_info({table})") as cursor:
                columns = [row["name"] for row in await cursor.fetchall()]
            if column not in columns:
                await self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

        await add_column_if_not_exists("tracks", "is_favorite", "INTEGER DEFAULT 0")
        await add_column_if_not_exists("artists", "click_count", "INTEGER DEFAULT 0")
        await add_column_if_not_exists("genres", "click_count", "INTEGER DEFAULT 0")

        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_songs_artist_id ON songs(artist_id)")
        await self._conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_artists_nama_unique ON artists(nama)")
        await self._conn.commit()

        from cache.repositories.track_repository import TrackRepository
        from cache.repositories.auth_repository import AuthRepository
        from cache.repositories.discover_repository import DiscoverRepository

        self.tracks = TrackRepository(self._conn)
        self.sessions = AuthRepository(self._conn)
        self.discover = DiscoverRepository(self._conn)

        await self._seed_initial_data()

        logger.info(f"Database initialized at {self.db_path}")

    async def _seed_initial_data(self):
        """Seeds initial data from JSON if the artists table is empty."""
        assert self._conn is not None
        async with self._conn.execute("SELECT COUNT(*) FROM artists") as cursor:
            count = (await cursor.fetchone())[0]
            if count > 0:
                return

        json_path = self.db_path.parent / "artists_enriched.json"
        if not json_path.exists():
            # Fallback if enriched doesn't exist
            json_path = self.db_path.parent / "artists.json"
            if not json_path.exists():
                logger.warning("No initial data found to seed database.")
                return

        import json
        import sys
        logger.info("Auto-seeding database from JSON, this may take a moment...")
        sys.stderr.write("\033[90m  [+] \033[0mMengekspor data ke SQLite untuk pertama kali...\n")

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for artist in data.get('artists', []):
            artist_id = artist['id']
            await self._conn.execute('''
                INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif)
                VALUES (?, ?, ?, ?)
            ''', (artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))

            for genre_name in artist.get('genre', []):
                await self._conn.execute('''
                    INSERT OR IGNORE INTO genres (nama_genre)
                    VALUES (?)
                ''', (genre_name,))
                
                async with self._conn.execute('SELECT id FROM genres WHERE nama_genre = ?', (genre_name,)) as c:
                    genre_id = (await c.fetchone())[0]

                await self._conn.execute('''
                    INSERT OR IGNORE INTO artist_genres (artist_id, genre_id)
                    VALUES (?, ?)
                ''', (artist_id, genre_id))

            for lagu in artist.get('lagu_populer', []):
                youtube_id = lagu.get('youtube_id')
                if youtube_id:
                    duration = lagu.get('durasi_detik', 0)
                    await self._conn.execute('''
                        INSERT OR IGNORE INTO songs (artist_id, judul, youtube_id, duration)
                        VALUES (?, ?, ?, ?)
                    ''', (artist_id, lagu['judul'], youtube_id, duration))
        
        await self._conn.commit()
        logger.info("Database auto-seeded successfully.")

    async def close(self):
        """Close the persistent connection gracefully."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def backup(self, backup_path):
        """Creates a safe backup of the database using SQLite's backup API."""
        if not self._conn:
            return
        import aiosqlite
        async with aiosqlite.connect(backup_path) as dest:
            await self._conn.backup(dest)

    def __getattr__(self, name):
        """Proxy missing methods to the repositories to maintain backward compatibility."""
        if self.tracks and hasattr(self.tracks, name):
            return getattr(self.tracks, name)
        if self.sessions and hasattr(self.sessions, name):
            return getattr(self.sessions, name)
        if self.discover and hasattr(self.discover, name):
            return getattr(self.discover, name)
        raise AttributeError(f"'Database' object has no attribute '{name}'")
