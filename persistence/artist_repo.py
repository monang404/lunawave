"""
Module: persistence.artist_repo

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import structlog

from core.state import TrackInfo

logger = structlog.get_logger(__name__)


class ArtistRepository:
    def __init__(self, conn):
        self._conn = conn

    async def increment_artist_click(self, artist_name: str):
        if not self._conn:
            return
        try:
            await self._conn.execute(
                "UPDATE artists SET click_count = COALESCE(click_count, 0) + 1 WHERE nama = ?",
                (artist_name,),
            )
            await self._conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing artist click: {e}")

    async def get_all_artists(self, kategori: str | None = None) -> list[str]:
        if kategori:
            query = "SELECT nama FROM artists WHERE kategori = ? ORDER BY id"
            params = (kategori,)
        else:
            query = "SELECT nama FROM artists ORDER BY id"
            params = ()  # type: ignore

        async with self._conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        return [row["nama"] for row in rows]

    async def get_artist_songs_strict(self, artist: str, limit: int = 10) -> list[TrackInfo]:
        query = """
            SELECT s.youtube_id, s.judul, s.duration, a.nama
            FROM songs s
            JOIN artists a ON s.artist_id = a.id
            WHERE a.nama = ?
            ORDER BY RANDOM() LIMIT ?
        """
        async with self._conn.execute(query, (artist, limit)) as cursor:
            rows = await cursor.fetchall()

        tracks = []
        for row in rows:
            tracks.append(
                TrackInfo(
                    video_id=row["youtube_id"],
                    title=row["judul"],
                    artist=row["nama"],
                    duration=row["duration"],
                    thumbnail=f"https://i.ytimg.com/vi/{row['youtube_id']}/mqdefault.jpg",
                )
            )
        return tracks
