"""
Module: persistence

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from pathlib import Path

from persistence.artist_repo import ArtistRepository
from persistence.db import DatabaseConnection
from persistence.genre_repo import GenreRepository
from persistence.library_repo import LibraryRepository
from persistence.session_repo import SessionRepository
from persistence.track_repo import TrackRepository


class Database:
    """
    Backward-compat wrapper. Semua method delegate ke repo masing-masing.
    Kode lama yang pakai `db.get_track()` tetap jalan tanpa ubah apapun.
    """

    def __init__(self, db_path=None):
        from config import DB_PATH

        self._db = DatabaseConnection(db_path or DB_PATH)
        self._tracks: TrackRepository = None
        self._sessions: SessionRepository = None
        self._artists: ArtistRepository = None
        self._genres: GenreRepository = None
        self._library: LibraryRepository = None

    async def init(self):
        schema_path = Path(__file__).parent / "schema.sql"
        await self._db.init(schema_path)
        # Jalankan migrasi ALTER TABLE (sama seperti cache/db.py lama)
        for sql in [
            "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0",
            "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0",
            "ALTER TABLE genres ADD COLUMN click_count INTEGER DEFAULT 0",
        ]:
            try:
                await self._db.conn.execute(sql)
                await self._db.conn.commit()
            except Exception:
                pass
        self._tracks = TrackRepository(self._db.conn)
        self._sessions = SessionRepository(self._db.conn)
        self._artists = ArtistRepository(self._db.conn)
        self._genres = GenreRepository(self._db.conn)
        self._library = LibraryRepository(self._db.conn)

    async def close(self):
        await self._db.close()

    @property
    def conn(self):
        return self._db.conn

    # Delegate semua method ke repo yang tepat:
    async def get_track(self, *a, **kw):
        return await self._tracks.get_track(*a, **kw)

    async def upsert_track(self, *a, **kw):
        return await self._tracks.upsert_track(*a, **kw)

    async def update_stream_url_only(self, *a, **kw):
        return await self._tracks.update_stream_url_only(*a, **kw)

    async def set_local_path(self, *a, **kw):
        return await self._tracks.set_local_path(*a, **kw)

    async def increment_play_count(self, *a, **kw):
        return await self._tracks.increment_play_count(*a, **kw)

    async def evict_stale_tracks(self, *a, **kw):
        return await self._tracks.evict_stale_tracks(*a, **kw)

    async def toggle_favorite(self, *a, **kw):
        return await self._tracks.toggle_favorite(*a, **kw)

    async def create_session(self, *a, **kw):
        return await self._sessions.create_session(*a, **kw)

    async def verify_session(self, *a, **kw):
        return await self._sessions.verify_session(*a, **kw)

    async def delete_session(self, *a, **kw):
        return await self._sessions.delete_session(*a, **kw)

    async def cleanup_sessions(self, *a, **kw):
        return await self._sessions.cleanup_sessions(*a, **kw)

    async def increment_artist_click(self, *a, **kw):
        return await self._artists.increment_artist_click(*a, **kw)

    async def get_all_artists(self, *a, **kw):
        return await self._artists.get_all_artists(*a, **kw)

    async def get_artist_songs_strict(self, *a, **kw):
        return await self._artists.get_artist_songs_strict(*a, **kw)

    async def increment_genre_click(self, *a, **kw):
        return await self._genres.increment_genre_click(*a, **kw)

    async def get_genre_artists(self, *a, **kw):
        return await self._genres.get_genre_artists(*a, **kw)

    async def get_genre_songs(self, *a, **kw):
        return await self._genres.get_genre_songs(*a, **kw)

    async def get_random_songs(self, *a, **kw):
        return await self._library.get_random_songs(*a, **kw)
