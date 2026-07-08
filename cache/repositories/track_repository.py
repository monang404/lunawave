import time
from typing import Optional
import structlog
from core.ports import TrackRepositoryPort
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

class TrackRepository(TrackRepositoryPort):
    def __init__(self, pool):
        self.pool = pool

    async def get_track(self, video_id: str) -> Optional[TrackInfo]:
        async with self.pool.acquire() as conn:
            async with conn.execute(
                """SELECT t.*, a.nama as artist_name 
                   FROM tracks t 
                   LEFT JOIN artists a ON t.artist_id = a.id 
                   WHERE t.video_id = ?""", (video_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                is_fav = row["is_favorite"] if "is_favorite" in row.keys() else 0
                return TrackInfo(
                    video_id=row["video_id"],
                    title=row["title"],
                    artist=row["artist_name"] or "",
                    duration=row["duration"],
                    thumbnail=row["thumbnail"],
                    local_path=row["local_path"],
                    stream_url=row["stream_url"],
                    view_count=row["view_count"],
                    stream_url_ts=row["stream_url_ts"],
                    play_count=row["play_count"],
                    last_played=row["last_played"],
                    is_favorite=is_fav,
                )

    async def upsert_track(self, track: TrackInfo, stream_url: str = None, local_path: str = None) -> None:
        ts = int(time.time())
        async with self.pool.acquire() as conn:
            await conn.execute("INSERT OR IGNORE INTO artists (nama) VALUES (?)", (track.artist,))
            async with conn.execute("SELECT id FROM artists WHERE nama = ?", (track.artist,)) as cur:
                row = await cur.fetchone()
                artist_id = row["id"] if row else None
                
            query = """
                INSERT INTO tracks (
                    video_id, title, artist_id, duration, view_count, thumbnail,
                    stream_url, stream_url_ts, local_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(video_id) DO UPDATE SET
                    title=excluded.title,
                    artist_id=excluded.artist_id,
                    duration=excluded.duration,
                    view_count=excluded.view_count,
                    thumbnail=excluded.thumbnail,
                    stream_url=COALESCE(excluded.stream_url, tracks.stream_url),
                    stream_url_ts=COALESCE(excluded.stream_url_ts, tracks.stream_url_ts),
                    local_path=COALESCE(excluded.local_path, tracks.local_path)
            """
            await conn.execute(query, (
                track.video_id, track.title, artist_id, track.duration,
                track.view_count, track.thumbnail, stream_url, ts if stream_url else None,
                local_path
            ))
            await conn.commit()

    async def update_stream_url_only(self, video_id: str, stream_url: str) -> None:
        ts = int(time.time())
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE tracks SET stream_url=?, stream_url_ts=? WHERE video_id=?",
                (stream_url, ts, video_id)
            )
            await conn.commit()

    async def set_local_path(self, video_id: str, local_path: Optional[str]) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE tracks SET local_path=? WHERE video_id=?",
                (local_path, video_id)
            )
            await conn.commit()

    async def increment_play_count(self, video_id: str) -> None:
        ts = int(time.time())
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE tracks SET play_count = play_count + 1, last_played = ? WHERE video_id = ?",
                (ts, video_id)
            )
            await conn.commit()
    async def toggle_favorite(self, video_id: str) -> int:
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE tracks SET is_favorite = 1 - COALESCE(is_favorite, 0) WHERE video_id = ?",
                (video_id,)
            )
            await conn.commit()
            async with conn.execute(
                "SELECT is_favorite FROM tracks WHERE video_id = ?", (video_id,)
            ) as cursor:
                row = await cursor.fetchone()
            return row["is_favorite"] if row else 0

    async def set_favorite(self, video_id: str, is_favorite: int) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE tracks SET is_favorite = ? WHERE video_id = ?", (is_favorite, video_id))
            await conn.commit()


    async def evict_stale_tracks(self) -> int:
        thirty_days_ago = int(time.time()) - (30 * 24 * 3600)

        async with self.pool.acquire() as conn:
            cursor = await conn.execute(
                """SELECT video_id, local_path FROM tracks
                   WHERE play_count = 0
                     AND local_path IS NULL
                     AND (is_favorite = 0 OR is_favorite IS NULL)
                     AND (
                         stream_url_ts IS NULL
                         OR stream_url_ts < ?
                     )""",
                (thirty_days_ago,)
            )
            rows = await cursor.fetchall()
            if not rows:
                return 0

            video_ids = [r["video_id"] for r in rows]
            
            placeholders = ','.join(['?'] * len(video_ids))
            await conn.execute(
                f"DELETE FROM tracks WHERE video_id IN ({placeholders})", tuple(video_ids)
            )
            await conn.commit()

        from config import CACHE_DIR
        for vid in video_ids:
            p = CACHE_DIR / f"{vid}.mp3"
            if p.exists():
                try:
                    p.unlink()
                except Exception as e:
                    logger.error(f"Gagal hapus file cache {p}: {e}")

        logger.info(f"Eviction: {len(video_ids)} track stale dihapus dari cache DB")
        return len(video_ids)

    async def get_recent_tracks(self, limit: int) -> list[TrackInfo]:
        tracks = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.execute(
                    "SELECT video_id, title, artist_id, duration, thumbnail, local_path, stream_url, view_count, play_count, is_favorite FROM tracks ORDER BY last_played DESC LIMIT ?", (limit,)
                ) as cursor:
                    async for row in cursor:
                        d = dict(row)
                        tracks.append(TrackInfo(
                            video_id=d["video_id"],
                            title=d["title"],
                            artist="Unknown",  # Requires JOIN or just let frontend ignore
                            duration=d["duration"],
                            thumbnail=d["thumbnail"],
                            local_path=d["local_path"],
                            stream_url=d.get("stream_url"),
                            view_count=d["view_count"],
                            is_favorite=bool(d.get("is_favorite", 0))
                        ))
        except Exception as e:
            logger.error(f"Error get_recent_tracks: {e}")
        return tracks

    async def get_favorite_tracks(self, limit: int) -> list[TrackInfo]:
        tracks = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.execute(
                    "SELECT video_id, title, artist_id, duration, thumbnail, local_path, stream_url, view_count, play_count, is_favorite FROM tracks WHERE is_favorite = 1 OR play_count > 0 ORDER BY is_favorite DESC, play_count DESC LIMIT ?", (limit,)
                ) as cursor:
                    async for row in cursor:
                        d = dict(row)
                        tracks.append(TrackInfo(
                            video_id=d["video_id"],
                            title=d["title"],
                            artist="Unknown",
                            duration=d["duration"],
                            thumbnail=d["thumbnail"],
                            local_path=d["local_path"],
                            stream_url=d.get("stream_url"),
                            view_count=d["view_count"],
                            is_favorite=bool(d.get("is_favorite", 0))
                        ))
        except Exception as e:
            logger.error(f"Error get_favorite_tracks: {e}")
        return tracks

    async def get_cached_tracks(self, limit: int) -> list[TrackInfo]:
        tracks = []
        try:
            async with self.pool.acquire() as conn:
                async with conn.execute(
                    "SELECT video_id, title, artist_id, duration, thumbnail, local_path, stream_url, view_count, play_count, is_favorite FROM tracks WHERE local_path IS NOT NULL ORDER BY last_played DESC LIMIT ?", (limit,)
                ) as cursor:
                    async for row in cursor:
                        d = dict(row)
                        tracks.append(TrackInfo(
                            video_id=d["video_id"],
                            title=d["title"],
                            artist="Unknown",
                            duration=d["duration"],
                            thumbnail=d["thumbnail"],
                            local_path=d["local_path"],
                            stream_url=d.get("stream_url"),
                            view_count=d["view_count"],
                            is_favorite=bool(d.get("is_favorite", 0))
                        ))
        except Exception as e:
            logger.error(f"Error get_cached_tracks: {e}")
        return tracks
