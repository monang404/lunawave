from pathlib import Path
import asyncio
import aiosqlite
import structlog

from config import DB_PATH

logger = structlog.get_logger(__name__)

class ConnectionPool:
    def __init__(self, db_path: Path, max_size: int = 5):
        self.db_path = db_path
        self.max_size = max_size
        self._pool = asyncio.Queue(maxsize=max_size)
        self._conns = []

    async def init(self):
        for _ in range(self.max_size):
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("PRAGMA foreign_keys=ON")
            await conn.execute("PRAGMA busy_timeout=5000")
            self._pool.put_nowait(conn)
            self._conns.append(conn)
            
    def acquire(self):
        return PoolContext(self)
        
    def release(self, conn):
        self._pool.put_nowait(conn)
        
    async def close(self):
        for conn in self._conns:
            await conn.close()
            
class PoolContext:
    def __init__(self, pool):
        self.pool = pool
        self.conn = None
        
    async def __aenter__(self):
        self.conn = await self.pool._pool.get()
        return self.conn
        
    async def __aexit__(self, exc_type, exc, tb):
        self.pool.release(self.conn)

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._schema_path = Path(__file__).parent / "schema.sql"
        self.pool = ConnectionPool(db_path)
        self.tracks = None
        self.sessions = None
        self.discover = None

    async def init(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        await self.pool.init()

        with open(self._schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
            
        async with self.pool.acquire() as conn:
            await conn.executescript(schema_sql)
            
            # Simple migration system
            async with conn.execute("SELECT MAX(version) as v FROM schema_migrations") as cur:
                row = await cur.fetchone()
                current_version = row["v"] if row and row["v"] else 0
                
            if current_version < 1:
                # Add version 1 logic if needed
                await conn.execute("INSERT INTO schema_migrations (version) VALUES (1)")
                await conn.commit()

        from cache.repositories.auth_repository import AuthRepository
        from cache.repositories.discover_repository import DiscoverRepository
        from cache.repositories.track_repository import TrackRepository

        self.tracks = TrackRepository(self.pool)
        self.sessions = AuthRepository(self.pool)
        self.discover = DiscoverRepository(self.pool)

        await self._seed_initial_data()

        logger.info(f"Database initialized at {self.db_path}")

    async def _seed_initial_data(self):
        async with self.pool.acquire() as conn:
            async with conn.execute("SELECT COUNT(*) as cnt FROM artists") as cursor:
                row = await cursor.fetchone()
                if row["cnt"] > 0:
                    return

        json_path = self.db_path.parent / "artists_enriched.json"
        if not json_path.exists():
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
                # We skip manual id parsing for artists since it's AUTOINCREMENT now, 
                # but if we must maintain relations from json:
                artist_id = artist['id']
                artists_data.append((artist_id, artist['nama'], artist['kategori'], artist['tahun_aktif']))

                for genre_name in artist.get('genre', []):
                    genres_data.add((genre_name,))

                for lagu in artist.get('lagu_populer', []):
                    youtube_id = lagu.get('youtube_id')
                    if youtube_id:
                        duration = lagu.get('durasi_detik', 0)
                        songs_data.append((artist_id, lagu['judul'], youtube_id, duration))

            async with self.pool.acquire() as conn:
                await conn.executemany('''
                    INSERT INTO artists (id, nama, kategori, tahun_aktif)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(nama) DO UPDATE SET 
                        kategori=excluded.kategori, 
                        tahun_aktif=excluded.tahun_aktif
                ''', artists_data)

                await conn.executemany('''
                    INSERT OR IGNORE INTO genres (nama_genre)
                    VALUES (?)
                ''', list(genres_data))

                genre_map = {}
                async with conn.execute('SELECT id, nama_genre FROM genres') as c:
                    async for row in c:
                        genre_map[row["nama_genre"]] = row["id"]

                for artist in data.get('artists', []):
                    artist_id = artist['id']
                    for genre_name in artist.get('genre', []):
                        if genre_name in genre_map:
                            artist_genres_data.append((artist_id, genre_map[genre_name]))

                await conn.executemany('''
                    INSERT OR IGNORE INTO artist_genres (artist_id, genre_id)
                    VALUES (?, ?)
                ''', artist_genres_data)

                await conn.executemany('''
                    INSERT OR IGNORE INTO songs (artist_id, judul, youtube_id, duration)
                    VALUES (?, ?, ?, ?)
                ''', songs_data)

                await conn.commit()
            logger.info("Database auto-seeded successfully.")
        except Exception as e:
            logger.error(f"Seed database gagal: {e}", exc_info=True)

    async def close(self):
        await self.pool.close()

    async def backup(self, backup_path):
        import aiosqlite
        # Since we use WAL, we acquire one connection to do backup
        async with self.pool.acquire() as conn:
            async with aiosqlite.connect(backup_path) as dest:
                await conn.backup(dest)

    # --- Explicit Forwarding (Optional, but kept for compatibility) ---
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

    async def increment_artist_click(self, artist_name: str):
        return await self.discover.increment_artist_click(artist_name)

    async def increment_genre_click(self, genre_name: str):
        return await self.discover.increment_genre_click(genre_name)

    async def get_genre_artists(self, genre_name: str, limit: int = 4):
        return await self.discover.get_genre_artists(genre_name, limit)

    async def get_all_artists(self, kategori: str | None = None):
        return await self.discover.get_all_artists(kategori)

    async def get_random_songs(self, limit: int = 20, exclude_ids: list = None, artist: str = None, max_per_artist: int = 3):
        return await self.discover.get_random_songs(limit, exclude_ids, artist, max_per_artist)

    async def get_artist_songs_strict(self, artist: str, limit: int = 10):
        return await self.discover.get_artist_songs_strict(artist, limit)

    async def get_genre_songs(self, genre_name: str, total_limit: int = 12, max_per_artist: int = 3):
        return await self.discover.get_genre_songs(genre_name, total_limit, max_per_artist)

    async def create_session(self, token: str, expires_at: int):
        return await self.sessions.create_session(token, expires_at)

    async def verify_session(self, token: str):
        return await self.sessions.verify_session(token)

    async def delete_session(self, token: str):
        return await self.sessions.delete_session(token)

    async def cleanup_sessions(self):
        return await self.sessions.cleanup_sessions()
