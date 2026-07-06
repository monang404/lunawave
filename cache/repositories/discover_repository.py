import structlog
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

class DiscoverRepository:
    def __init__(self, db_conn):
        self._conn = db_conn

    async def increment_artist_click(self, artist_name: str):
        """Increment the click count for a given artist."""
        if not self._conn: return
        try:
            await self._conn.execute(
                "UPDATE artists SET click_count = COALESCE(click_count, 0) + 1 WHERE nama = ?", (artist_name,)
            )
            await self._conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing artist click: {e}")

    async def increment_genre_click(self, genre_name: str):
        """Increment the click count for a given genre."""
        if not self._conn: return
        try:
            await self._conn.execute(
                "UPDATE genres SET click_count = COALESCE(click_count, 0) + 1 WHERE nama_genre = ?", (genre_name,)
            )
            await self._conn.commit()
        except Exception as e:
            logger.error(f"Error incrementing genre click: {e}")

    async def get_genre_artists(self, genre_name: str, limit: int = 4) -> list[str]:
        """Get random artist names that belong to a specific genre."""
        if not self._conn: return []
        artists = []
        try:
            async with self._conn.execute(
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
        """Ambil semua nama artis dari DB untuk seed radio mode."""
        if not self._conn: return []
        if kategori:
            query = "SELECT nama FROM artists WHERE kategori = ? ORDER BY id"
            params = (kategori,)
        else:
            query = "SELECT nama FROM artists ORDER BY id"
            params = ()

        async with self._conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()

        return [row["nama"] for row in rows]

    async def get_random_songs(
        self, limit: int = 12, exclude_ids: set[str] = None, artist: str = None, max_per_artist: int = 3
    ) -> list[TrackInfo]:
        """Ambil lagu acak langsung dari database untuk Radio Mode, dengan limit per artis."""
        if not self._conn: return []
        if exclude_ids is None:
            exclude_ids = set()

        placeholders = ','.join('?' for _ in exclude_ids)
        query = """
            WITH RankedSongs AS (
                SELECT s.youtube_id, s.judul, s.duration, a.nama,
                       ROW_NUMBER() OVER (PARTITION BY s.artist_id ORDER BY RANDOM()) as rn
                FROM songs s
                JOIN artists a ON s.artist_id = a.id
                WHERE 1=1
        """
        params = []
        if exclude_ids:
            query += f" AND s.youtube_id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        query += """
            )
            SELECT youtube_id, judul, duration, nama
            FROM RankedSongs
            WHERE rn <= ?
        """
        params.append(max_per_artist)

        if artist:
            query += " ORDER BY CASE WHEN nama = ? THEN 0 ELSE 1 END, RANDOM() LIMIT ?"
            params.extend([artist, limit])
        else:
            query += " ORDER BY RANDOM() LIMIT ?"
            params.append(limit)

        async with self._conn.execute(query, params) as cursor:
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

    async def get_artist_songs_strict(self, artist: str, limit: int = 10) -> list[TrackInfo]:
        """Ambil lagu khusus dari artis tertentu saja (bukan campuran)."""
        if not self._conn: return []
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
            tracks.append(TrackInfo(
                video_id=row["youtube_id"],
                title=row["judul"],
                artist=row["nama"],
                duration=row["duration"],
                thumbnail=f"https://i.ytimg.com/vi/{row['youtube_id']}/mqdefault.jpg"
            ))
        return tracks

    async def get_genre_songs(self, genre_name: str, total_limit: int = 12, max_per_artist: int = 3) -> list[TrackInfo]:
        """Ambil lagu dari genre tertentu, maksimal max_per_artist lagu per artis, total total_limit lagu."""
        if not self._conn: return []
        query = """
            WITH GenreSongs AS (
                SELECT s.youtube_id, s.judul, s.duration, a.nama,
                       ROW_NUMBER() OVER (PARTITION BY s.artist_id ORDER BY RANDOM()) as rn
                FROM songs s
                JOIN artists a ON s.artist_id = a.id
                JOIN artist_genres ag ON a.id = ag.artist_id
                JOIN genres g ON ag.genre_id = g.id
                WHERE g.nama_genre = ?
            )
            SELECT youtube_id, judul, duration, nama
            FROM GenreSongs
            WHERE rn <= ?
            ORDER BY RANDOM() LIMIT ?
        """
        async with self._conn.execute(query, (genre_name, max_per_artist, total_limit)) as cursor:
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
