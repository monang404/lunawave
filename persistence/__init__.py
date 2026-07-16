"""
Module: persistence

Purpose:
    Database facade that aggregates all repositories into a unified data access layer.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - persistence.artist_repo
    - persistence.db
    - persistence.genre_repo
    - persistence.library_repo
    - persistence.session_repo
    - persistence.track_repo

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

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
        await self._migrate_songs_unique_constraint()
        # Jalankan migrasi ALTER TABLE (sama seperti cache/db.py lama)
        for sql in [
            "ALTER TABLE tracks ADD COLUMN is_favorite INTEGER DEFAULT 0",
            "ALTER TABLE artists ADD COLUMN click_count INTEGER DEFAULT 0",
            "ALTER TABLE genres ADD COLUMN click_count INTEGER DEFAULT 0",
            "ALTER TABLE artists ADD COLUMN reward_alpha INTEGER DEFAULT 1",
            "ALTER TABLE artists ADD COLUMN reward_beta INTEGER DEFAULT 1",
            "ALTER TABLE tracks ADD COLUMN loudness_lufs REAL",
            "ALTER TABLE tracks ADD COLUMN last_position REAL DEFAULT 0.0",
            "ALTER TABLE tracks ADD COLUMN true_peak_dbtp REAL",  # H-3: true peak dari ffmpeg loudnorm
        ]:
            try:
                await self._db.conn.execute(sql)
                await self._db.conn.commit()
            except Exception as e:
                # "duplicate column" itu NORMAL (migrasi sudah pernah jalan) — jangan di-log sebagai error.
                # Selain itu (disk full, DB corrupt, dll) WAJIB tercatat.
                if "duplicate column" not in str(e).lower():
                    logger.error(
                        "db_migration_failed",
                        sql=sql,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
        self._tracks = TrackRepository(self._db.conn)
        self._sessions = SessionRepository(self._db.conn)
        self._artists = ArtistRepository(self._db.conn)
        self._genres = GenreRepository(self._db.conn)
        self._library = LibraryRepository(self._db.conn)

    async def _migrate_songs_unique_constraint(self) -> None:
        """PATCH-2026-07-16-048: `songs.youtube_id` used to be globally UNIQUE,
        which silently dropped collaboration/duet tracks for every artist
        after the first one encountered on import. This migrates any
        pre-existing DB to a composite UNIQUE(artist_id, youtube_id), which
        keeps per-artist uniqueness (no dupes within one artist's list) while
        letting the same video appear under multiple artists. No-op on a
        fresh DB, since schema.sql already creates the new constraint."""
        conn = self._db.conn
        try:
            async with conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='songs'"
            ) as cursor:
                row = await cursor.fetchone()
        except Exception as e:
            logger.error("songs_migration_check_failed", error=str(e))
            return

        if not row or "youtube_id TEXT NOT NULL" in row[0]:
            # Table doesn't exist yet, or already has the new (non-globally-unique) schema.
            return

        logger.info("songs_migration_starting", reason="global_unique_youtube_id_detected")
        try:
            await conn.execute("ALTER TABLE songs RENAME TO songs_old_migration")
            await conn.execute(
                """
                CREATE TABLE songs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artist_id INTEGER,
                    judul TEXT NOT NULL,
                    youtube_id TEXT NOT NULL,
                    duration INTEGER DEFAULT 0,
                    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE,
                    UNIQUE (artist_id, youtube_id)
                )
                """
            )
            await conn.execute(
                "INSERT INTO songs (id, artist_id, judul, youtube_id, duration) "
                "SELECT id, artist_id, judul, youtube_id, duration FROM songs_old_migration"
            )
            await conn.execute("DROP TABLE songs_old_migration")
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_songs_youtube_id ON songs(youtube_id)"
            )
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_songs_artist_id ON songs(artist_id)")
            await conn.commit()
            logger.info("songs_migration_completed")
        except Exception as e:
            await conn.rollback()
            logger.error("songs_migration_failed", error=str(e), error_type=type(e).__name__)

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

    async def get_reward_stats(self, *a, **kw):
        return await self._artists.get_reward_stats(*a, **kw)

    async def record_completion(self, *a, **kw):
        return await self._artists.record_completion(*a, **kw)

    async def record_skip(self, *a, **kw):
        return await self._artists.record_skip(*a, **kw)

    async def increment_genre_click(self, *a, **kw):
        return await self._genres.increment_genre_click(*a, **kw)

    async def get_genre_artists(self, *a, **kw):
        return await self._genres.get_genre_artists(*a, **kw)

    async def get_genre_songs(self, *a, **kw):
        return await self._genres.get_genre_songs(*a, **kw)

    async def get_random_songs(self, *a, **kw):
        return await self._library.get_random_songs(*a, **kw)

    async def set_loudness(self, *a, **kw):
        return await self._tracks.set_loudness(*a, **kw)

    async def set_last_position(self, *a, **kw):
        return await self._tracks.set_last_position(*a, **kw)
