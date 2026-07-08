from pathlib import Path

import aiosqlite
import structlog

from config import DB_PATH

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
        self._conn.row_factory = aiosqlite.Row  # type: ignore
        await self._conn.execute("PRAGMA journal_mode=WAL")  # type: ignore
        await self._conn.execute("PRAGMA foreign_keys=ON")  # type: ignore

        with open(self._schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        await self._conn.executescript(schema_sql)  # type: ignore

        async def add_column_if_not_exists(table, column, definition):
            assert self._conn is not None
            async with self._conn.execute(f"PRAGMA table_info({table})") as cursor:
                columns = [row["name"] for row in await cursor.fetchall()]
            if column not in columns:
                await self._conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

        await add_column_if_not_exists("tracks", "is_favorite", "INTEGER DEFAULT 0")
        await add_column_if_not_exists("artists", "click_count", "INTEGER DEFAULT 0")
        await add_column_if_not_exists("genres", "click_count", "INTEGER DEFAULT 0")

        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_songs_artist_id ON songs(artist_id)")  # type: ignore
        await self._conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_artists_nama_unique ON artists(nama)")  # type: ignore
        await self._conn.execute("CREATE INDEX IF NOT EXISTS idx_is_favorite ON tracks(is_favorite) WHERE is_favorite = 1")  # type: ignore
        await self._conn.commit()  # type: ignore

        from cache.repositories.auth_repository import AuthRepository
        from cache.repositories.discover_repository import DiscoverRepository
        from cache.repositories.track_repository import TrackRepository

        self.tracks = TrackRepository(self._conn)  # type: ignore
        self.sessions = AuthRepository(self._conn)  # type: ignore
        self.discover = DiscoverRepository(self._conn)  # type: ignore

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
        import sqlite3
        import sys
        logger.info("Auto-seeding database from JSON, this may take a moment...")
        sys.stderr.write("\033[90m  [+] \033[0mMengekspor data ke SQLite untuk pertama kali...\n")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            artists_data = []
            genres_data = set()
            artist_genres_data = []
            songs_data = []

            for artist in data.get('artists', []):
                artist_id = artist['id']
                artists_data.append((artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))

                for genre_name in artist.get('genre', []):
                    genres_data.add((genre_name,))

                for lagu in artist.get('lagu_populer', []):
                    youtube_id = lagu.get('youtube_id')
                    if youtube_id:
                        duration = lagu.get('durasi_detik', 0)
                        songs_data.append((artist_id, lagu['judul'], youtube_id, duration))

            await self._conn.executemany('''
                INSERT OR REPLACE INTO artists (id, nama, kategori, tahun_aktif)
                VALUES (?, ?, ?, ?)
            ''', artists_data)

            await self._conn.executemany('''
                INSERT OR IGNORE INTO genres (nama_genre)
                VALUES (?)
            ''', list(genres_data))

            genre_map = {}
            async with self._conn.execute('SELECT id, nama_genre FROM genres') as c:
                async for row in c:
                    genre_map[row[1]] = row[0]

            for artist in data.get('artists', []):
                artist_id = artist['id']
                for genre_name in artist.get('genre', []):
                    if genre_name in genre_map:
                        artist_genres_data.append((artist_id, genre_map[genre_name]))

            await self._conn.executemany('''
                INSERT OR IGNORE INTO artist_genres (artist_id, genre_id)
                VALUES (?, ?)
            ''', artist_genres_data)

            await self._conn.executemany('''
                INSERT OR IGNORE INTO songs (artist_id, judul, youtube_id, duration)
                VALUES (?, ?, ?, ?)
            ''', songs_data)

            await self._conn.commit()
            logger.info("Database auto-seeded successfully.")
        except (sqlite3.Error, KeyError, ValueError, json.JSONDecodeError) as e:
            # Rollback agar DB tidak tertinggal dalam kondisi partial seed (S02-045)
            logger.error(f"Seed database gagal, melakukan rollback: {e}", exc_info=True)
            try:
                await self._conn.rollback()
            except Exception:
                pass


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

    # ==========================================
    # Explicit Forwarding to Repositories
    # ==========================================
    
    # --- TrackRepository ---
    async def get_track(self, video_id: str):
        return await self.tracks.get_track(video_id)

    async def upsert_track(self, track, stream_url: str = None, local_path: str = None):
        return await self.tracks.upsert_track(track, stream_url, local_path)

    async def update_stream_url_only(self, video_id: str, stream_url: str):
        return await self.tracks.update_stream_url_only(video_id, stream_url)

    async def set_local_path(self, video_id: str, local_path: str = None):
        return await self.tracks.set_local_path(video_id, local_path)

    async def increment_play_count(self, video_id: str):
        return await self.tracks.increment_play_count(video_id)

    async def toggle_favorite(self, video_id: str):
        return await self.tracks.toggle_favorite(video_id)

    async def evict_stale_tracks(self):
        return await self.tracks.evict_stale_tracks()

    # --- DiscoverRepository ---
    async def increment_artist_click(self, artist_name: str):
        return await self.discover.increment_artist_click(artist_name)

    async def increment_genre_click(self, genre_name: str):
        return await self.discover.increment_genre_click(genre_name)

    async def get_genre_artists(self, genre_name: str, limit: int = 4):
        return await self.discover.get_genre_artists(genre_name, limit)

    async def get_all_artists(self, kategori: str | None = None):
        return await self.discover.get_all_artists(kategori)

    async def get_random_songs(self, limit: int = 20, weight_favorite: bool = True, exclude_ids: list = None):
        return await self.discover.get_random_songs(limit, weight_favorite, exclude_ids)

    async def get_artist_songs_strict(self, artist: str, limit: int = 10):
        return await self.discover.get_artist_songs_strict(artist, limit)

    async def get_genre_songs(self, genre_name: str, total_limit: int = 12, max_per_artist: int = 3):
        return await self.discover.get_genre_songs(genre_name, total_limit, max_per_artist)

    # --- AuthRepository ---
    async def create_session(self, token: str, expires_at: int):
        return await self.sessions.create_session(token, expires_at)

    async def verify_session(self, token: str):
        return await self.sessions.verify_session(token)

    async def delete_session(self, token: str):
        return await self.sessions.delete_session(token)

    async def cleanup_sessions(self):
        return await self.sessions.cleanup_sessions()
