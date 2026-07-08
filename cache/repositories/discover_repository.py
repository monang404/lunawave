import structlog
from core.state import TrackInfo
import random

logger = structlog.get_logger(__name__)

class DiscoverRepository:
    def __init__(self, pool):
        self.pool = pool

    async def increment_artist_click(self, artist_name: str):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE artists SET click_count = COALESCE(click_count, 0) + 1 WHERE nama = ?", (artist_name,)
                )
                await conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing artist click: {e}")

    async def increment_genre_click(self, genre_name: str):
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "UPDATE genres SET click_count = COALESCE(click_count, 0) + 1 WHERE nama_genre = ?", (genre_name,)
                )
                await conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing genre click: {e}")

    async def get_genre_artists(self, genre_name: str, limit: int = 4) -> list[str]:
        artists = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.execute(
                    """SELECT a.nama FROM artists a
                       JOIN artist_genres ag ON a.id = ag.artist_id
                       JOIN genres g ON ag.genre_id = g.id
                       WHERE g.nama_genre = ?
                       ORDER BY RANDOM() LIMIT ?""", (genre_name, limit)
                ) as cursor:
                    async for row in cursor:
                        artists.append(row["nama"])
        except Exception as e:
            logger.error(f"Error getting genre artists: {e}")
        return artists

    async def get_all_artists(self, kategori: str | None = None) -> list[str]:
        if kategori:
            query = "SELECT nama FROM artists WHERE kategori = ? ORDER BY id"
            params = (kategori,)
        else:
            query = "SELECT nama FROM artists ORDER BY id"
            params = ()

        async with self.pool.acquire() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()

        return [row["nama"] for row in rows]

    async def get_random_songs(
        self, limit: int = 12, exclude_ids: set[str] = None, artist: str = None, max_per_artist: int = 3
    ) -> list[TrackInfo]:
        if exclude_ids is None:
            exclude_ids = set()

        placeholders = ','.join('?' for _ in exclude_ids)
        query = """
            SELECT s.youtube_id, s.judul, s.duration, a.nama
            FROM songs s
            JOIN artists a ON s.artist_id = a.id
            WHERE 1=1
        """
        params = []
        if exclude_ids:
            query += f" AND s.youtube_id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        if artist:
            query += " ORDER BY CASE WHEN a.nama = ? THEN 0 ELSE 1 END, RANDOM() LIMIT 100"
            params.append(artist)
        else:
            query += " ORDER BY RANDOM() LIMIT 100"

        async with self.pool.acquire() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()

        # In-memory deduplication & limiting (fixes S05-041 ROW_NUMBER SQLite < 3.25 issue)
        tracks = []
        artist_counts = {}
        for row in rows:
            if len(tracks) >= limit:
                break
            nama = row["nama"]
            if artist_counts.get(nama, 0) >= max_per_artist:
                continue
            
            artist_counts[nama] = artist_counts.get(nama, 0) + 1
            tracks.append(TrackInfo(
                video_id=row["youtube_id"],
                title=row["judul"],
                artist=nama,
                duration=row["duration"],
                thumbnail=f"https://i.ytimg.com/vi/{row['youtube_id']}/mqdefault.jpg"
            ))
            
        return tracks

    async def get_artist_songs_strict(self, artist: str, limit: int = 10) -> list[TrackInfo]:
        query = """
            SELECT s.youtube_id, s.judul, s.duration, a.nama
            FROM songs s
            JOIN artists a ON s.artist_id = a.id
            WHERE a.nama = ?
            ORDER BY RANDOM() LIMIT ?
        """
        async with self.pool.acquire() as conn:
            async with conn.execute(query, (artist, limit)) as cursor:
                rows = await cursor.fetchall()

        tracks = []
        for row in rows:
            tracks.append(TrackInfo(
                video_id=row["youtube_id"],
                title=row["judul"],
                artist=row["nama"],
                duration=row["duration"],
                thumbnail=f"https://i.ytimg.com/vi/{row['youtube_id']}/mqdefault.jpg"
            ))
        return tracks

    async def get_genre_songs(self, genre_name: str, total_limit: int = 12, max_per_artist: int = 3) -> list[TrackInfo]:
        query = """
            SELECT s.youtube_id, s.judul, s.duration, a.nama
            FROM songs s
            JOIN artists a ON s.artist_id = a.id
            JOIN artist_genres ag ON a.id = ag.artist_id
            JOIN genres g ON ag.genre_id = g.id
            WHERE g.nama_genre = ?
            ORDER BY RANDOM() LIMIT 100
        """
        async with self.pool.acquire() as conn:
            async with conn.execute(query, (genre_name,)) as cursor:
                rows = await cursor.fetchall()

        tracks = []
        artist_counts = {}
        for row in rows:
            if len(tracks) >= total_limit:
                break
            nama = row["nama"]
            if artist_counts.get(nama, 0) >= max_per_artist:
                continue
            
            artist_counts[nama] = artist_counts.get(nama, 0) + 1
            tracks.append(TrackInfo(
                video_id=row["youtube_id"],
                title=row["judul"],
                artist=nama,
                duration=row["duration"],
                thumbnail=f"https://i.ytimg.com/vi/{row['youtube_id']}/mqdefault.jpg"
            ))
        return tracks

    async def get_featured_artists(self, limit: int) -> list[dict]:
        artists = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.execute(
                    "SELECT id, nama, kategori, tahun_aktif, COALESCE(click_count, 0) as click_count FROM artists ORDER BY RANDOM() LIMIT ?", (limit,)
                ) as cursor:
                    async for row in cursor:
                        artists.append(dict(row))
        except Exception as e:
            logger.error(f"Error get_featured_artists: {e}")
        return artists

    async def get_featured_genres(self, limit: int) -> list[dict]:
        genres = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.execute(
                    "SELECT id, nama_genre, COALESCE(click_count, 0) as click_count FROM genres ORDER BY RANDOM() LIMIT ?", (limit,)
                ) as cursor:
                    async for row in cursor:
                        genres.append({
                            "id": row["id"],
                            "nama_genre": row["nama_genre"],
                            "click_count": row["click_count"]
                        })
        except Exception as e:
            logger.error(f"Error get_featured_genres: {e}")
        return genres
