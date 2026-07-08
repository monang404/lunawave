"""
Purpose: Menyediakan data discover (recent dan favorites).
Subscribes to: (tidak ada)
Publishes: (tidak ada)
"""

import structlog

from cache.db import Database
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

import sqlite3


class DiscoverService:
    def __init__(self, db: Database):
        self.db = db

    async def get_recent(self, n: int) -> list[TrackInfo]:
        """Mengambil n lagu yang terakhir diputar dari DB."""
        if getattr(self.db, 'conn', None) is None:
            return []

        tracks = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT video_id, title, artist, duration, thumbnail, local_path, stream_url, view_count, play_count, is_favorite FROM tracks ORDER BY last_played DESC LIMIT ?", (n,)
            ) as cursor:
                async for row in cursor:
                    d = dict(row)
                    tracks.append(TrackInfo(
                        video_id=d["video_id"],
                        title=d["title"],
                        artist=d["artist"],
                        duration=d["duration"],
                        thumbnail=d["thumbnail"],
                        local_path=d["local_path"],
                        stream_url=d.get("stream_url"),
                        view_count=d["view_count"],
                        is_favorite=d.get("is_favorite", 0)
                    ))
        except (KeyError, ValueError, sqlite3.Error) as e:
            logger.error(f"Data error in get_recent: {e}")
        return tracks

    async def get_favorites(self, n: int) -> list[TrackInfo]:
        """Mengambil n lagu dengan play_count tertinggi atau eksplisit difavoritkan dari DB."""
        if getattr(self.db, 'conn', None) is None:
            return []

        tracks = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT video_id, title, artist, duration, thumbnail, local_path, stream_url, view_count, play_count, is_favorite FROM tracks WHERE is_favorite = 1 OR play_count > 0 ORDER BY is_favorite DESC, play_count DESC LIMIT ?", (n,)
            ) as cursor:
                async for row in cursor:
                    d = dict(row)
                    tracks.append(TrackInfo(
                        video_id=d["video_id"],
                        title=d["title"],
                        artist=d["artist"],
                        duration=d["duration"],
                        thumbnail=d["thumbnail"],
                        local_path=d["local_path"],
                        stream_url=d.get("stream_url"),
                        view_count=d["view_count"],
                        is_favorite=d.get("is_favorite", 0)
                    ))
        except (KeyError, ValueError, sqlite3.Error) as e:
            logger.error(f"Data error in get_favorites: {e}")
        return tracks

    async def get_cached(self, n: int) -> list[TrackInfo]:
        """Mengambil n lagu yang sudah ter-cache (local_path is not null)."""
        if getattr(self.db, 'conn', None) is None:
            return []

        tracks = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT video_id, title, artist, duration, thumbnail, local_path, stream_url, view_count, play_count, is_favorite FROM tracks WHERE local_path IS NOT NULL ORDER BY last_played DESC LIMIT ?", (n,)
            ) as cursor:
                async for row in cursor:
                    d = dict(row)
                    tracks.append(TrackInfo(
                        video_id=d["video_id"],
                        title=d["title"],
                        artist=d["artist"],
                        duration=d["duration"],
                        thumbnail=d["thumbnail"],
                        local_path=d["local_path"],
                        stream_url=d.get("stream_url"),
                        view_count=d["view_count"],
                        is_favorite=d.get("is_favorite", 0)
                    ))
        except (KeyError, ValueError, sqlite3.Error) as e:
            logger.error(f"Data error in get_cached: {e}")
        return tracks

    async def get_featured_artists(self, n: int) -> list[dict]:
        """Mengambil n artis acak dari tabel artists beserta click_count."""
        if getattr(self.db, 'conn', None) is None:
            return []

        artists = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT id, nama, kategori, tahun_aktif, COALESCE(click_count, 0) as click_count FROM artists ORDER BY RANDOM() LIMIT ?", (n,)
            ) as cursor:
                async for row in cursor:
                    artists.append(dict(row))
        except (KeyError, ValueError, sqlite3.Error) as e:
            logger.error(f"Data error in get_featured_artists: {e}")
        return artists

    async def get_featured_genres(self, n: int) -> list[dict]:
        """Mengambil n genre acak dari tabel genres beserta click_count."""
        if getattr(self.db, 'conn', None) is None:
            return []

        genres = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT id, nama_genre, COALESCE(click_count, 0) as click_count FROM genres ORDER BY RANDOM() LIMIT ?", (n,)
            ) as cursor:
                async for row in cursor:
                    genres.append({
                        "id": row["id"],
                        "nama_genre": row["nama_genre"],
                        "click_count": row["click_count"]
                    })
        except (KeyError, ValueError, sqlite3.Error) as e:
            logger.error(f"Data error in get_featured_genres: {e}")
        return genres
