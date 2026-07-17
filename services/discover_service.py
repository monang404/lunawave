"""
Module: services.discover_service

Purpose:
    Query the SQLite database to provide discover-page data: recently played
    tracks, favorites, cached tracks, and featured artists/genres.

Responsibilities:
    - Expose async methods for each discover data category.
    - Return empty lists gracefully when the DB connection is unavailable.
    - Expose personalization wrappers (for_you, unheard, genre_affinity,
      taste_spectrum, artist_detail) backed by persistence.discover_repo.

Depends on:
    - core.ports
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async; read-only queries).
"""

from core.ports import DatabasePort
from core.state import TrackInfo


class DiscoverService:
    def __init__(self, db: DatabasePort):
        self.db = db

    async def get_recent(self, n: int) -> list[TrackInfo]:
        """Mengambil n lagu yang terakhir diputar dari DB."""
        if not getattr(self.db, "conn", None):
            return []

        tracks = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT * FROM tracks ORDER BY last_played DESC LIMIT ?", (n,)
            ) as cursor:
                async for row in cursor:
                    d = dict(row)
                    tracks.append(
                        TrackInfo(
                            video_id=d["video_id"],
                            title=d["title"],
                            artist=d["artist"],
                            duration=d["duration"],
                            thumbnail=d["thumbnail"],
                            local_path=d["local_path"],
                            stream_url=d["stream_url"],
                            view_count=d["view_count"],
                            is_favorite=d.get("is_favorite", 0),
                        )
                    )
        except Exception as e:
            raise e
        return tracks

    async def get_favorites(self, n: int) -> list[TrackInfo]:
        """Mengambil n lagu dengan play_count tertinggi atau eksplisit difavoritkan dari DB."""
        if not getattr(self.db, "conn", None):
            return []

        tracks = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT * FROM tracks WHERE is_favorite = 1 OR play_count > 0 ORDER BY is_favorite DESC, play_count DESC LIMIT ?",
                (n,),
            ) as cursor:
                async for row in cursor:
                    d = dict(row)
                    tracks.append(
                        TrackInfo(
                            video_id=d["video_id"],
                            title=d["title"],
                            artist=d["artist"],
                            duration=d["duration"],
                            thumbnail=d["thumbnail"],
                            local_path=d["local_path"],
                            stream_url=d["stream_url"],
                            view_count=d["view_count"],
                            is_favorite=d.get("is_favorite", 0),
                        )
                    )
        except Exception as e:
            raise e
        return tracks

    async def get_cached(self, n: int) -> list[TrackInfo]:
        """Mengambil n lagu yang sudah ter-cache (local_path is not null)."""
        if not getattr(self.db, "conn", None):
            return []

        tracks = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT * FROM tracks WHERE local_path IS NOT NULL ORDER BY last_played DESC LIMIT ?",
                (n,),
            ) as cursor:
                async for row in cursor:
                    d = dict(row)
                    tracks.append(
                        TrackInfo(
                            video_id=d["video_id"],
                            title=d["title"],
                            artist=d["artist"],
                            duration=d["duration"],
                            thumbnail=d["thumbnail"],
                            local_path=d["local_path"],
                            stream_url=d["stream_url"],
                            view_count=d["view_count"],
                            is_favorite=d.get("is_favorite", 0),
                        )
                    )
        except Exception as e:
            raise e
        return tracks

    async def get_featured_artists(self, n: int) -> list[dict]:
        """Mengambil n artis acak dari tabel artists beserta click_count."""
        if not getattr(self.db, "conn", None):
            return []

        artists = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT id, nama, kategori, tahun_aktif, COALESCE(click_count, 0) as click_count FROM artists WHERE id IN (SELECT id FROM artists ORDER BY RANDOM() LIMIT ?)",
                (n,),
            ) as cursor:
                async for row in cursor:
                    artists.append(dict(row))
        except Exception as e:
            raise e
        return artists

    async def get_featured_genres(self, n: int) -> list[dict]:
        """Mengambil n genre acak dari tabel genres beserta click_count."""
        if not getattr(self.db, "conn", None):
            return []

        genres = []
        try:
            async with self.db.conn.execute(  # type: ignore
                "SELECT id, nama_genre, COALESCE(click_count, 0) as click_count FROM genres WHERE id IN (SELECT id FROM genres ORDER BY RANDOM() LIMIT ?)",
                (n,),
            ) as cursor:
                async for row in cursor:
                    genres.append(
                        {
                            "id": row["id"],
                            "nama_genre": row["nama_genre"],
                            "click_count": row["click_count"],
                        }
                    )
        except Exception as e:
            print(f"Error in get_featured_genres: {e}")
        return genres

    # --- Discover personalization (PATCH-2026-07-17-070) ---
    # Delegates to persistence.discover_repo.DiscoverRepository through the
    # Database facade — this service doesn't need to know the split exists.

    async def get_for_you(self, n: int) -> list[dict]:
        """ "Untuk Kamu": artis top hasil bandit ranking. Kosong kalau
        bandit belum pernah belajar apapun (semua artis masih alpha=beta=1)
        — caller/frontend fallback ke featured/random seperti sekarang."""
        if not getattr(self.db, "conn", None):
            return []
        return await self.db.get_bandit_ranked_artists(n)

    async def get_unheard(self, n: int) -> list[dict]:
        """ "Belum Pernah Kamu Dengar": artis yang benar-benar belum
        tersentuh (bandit maupun click)."""
        if not getattr(self.db, "conn", None):
            return []
        return await self.db.get_unheard_artists(n)

    async def get_genre_affinity(self, n: int) -> dict:
        """ "Karena Kamu Suka [Genre]": genre teratas dari taste spectrum +
        artis lain di genre itu. `genre=None` kalau histori putar kosong
        (user baru) — caller menampilkan fallback UI, bukan section kosong."""
        if not getattr(self.db, "conn", None):
            return {"genre": None, "artists": []}
        genre = await self.db.get_top_genre()
        if not genre:
            return {"genre": None, "artists": []}
        artists = await self.db.get_genre_artists_enriched(genre, n)
        return {"genre": genre, "artists": artists}

    async def get_taste_spectrum(self) -> list[dict]:
        """Breakdown genre dari histori putar, dinormalisasi ke persentase.
        [] kalau histori kosong."""
        if not getattr(self.db, "conn", None):
            return []
        return await self.db.get_taste_spectrum()

    async def get_artist_detail(self, nama: str) -> dict | None:
        """Detail lengkap satu artis (untuk artist detail sheet). None
        kalau artis tidak ditemukan."""
        if not getattr(self.db, "conn", None):
            return None
        return await self.db.get_artist_detail(nama)
