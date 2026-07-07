import time
import structlog
from typing import Optional

from core.state import TrackInfo
from core.ports import TrackRepositoryPort

logger = structlog.get_logger(__name__)

class TrackRepository(TrackRepositoryPort):
    def __init__(self, db_conn):
        self._conn = db_conn

    async def get_track(self, video_id: str) -> Optional[TrackInfo]:
        if not self._conn: return None
        async with self._conn.execute(
            "SELECT * FROM tracks WHERE video_id = ?", (video_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            is_fav = row["is_favorite"] if "is_favorite" in row.keys() else 0
            return TrackInfo(
                video_id=row["video_id"],
                title=row["title"],
                artist=row["artist"],
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
        if not self._conn: return
        ts = int(time.time())
        query = """
            INSERT INTO tracks (
                video_id, title, artist, duration, view_count, thumbnail,
                stream_url, stream_url_ts, local_path, last_played
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id) DO UPDATE SET
                title=excluded.title,
                artist=excluded.artist,
                duration=excluded.duration,
                view_count=excluded.view_count,
                thumbnail=excluded.thumbnail,
                stream_url=COALESCE(excluded.stream_url, tracks.stream_url),
                stream_url_ts=COALESCE(excluded.stream_url_ts, tracks.stream_url_ts),
                local_path=COALESCE(excluded.local_path, tracks.local_path),
                last_played=excluded.last_played
        """
        await self._conn.execute(query, (
            track.video_id, track.title, track.artist, track.duration,
            track.view_count, track.thumbnail, stream_url, ts if stream_url else None,
            local_path, ts
        ))
        await self._conn.commit()

    async def update_stream_url_only(self, video_id: str, stream_url: str) -> None:
        if not self._conn: return
        ts = int(time.time())
        await self._conn.execute(
            "UPDATE tracks SET stream_url=?, stream_url_ts=? WHERE video_id=?",
            (stream_url, ts, video_id)
        )
        await self._conn.commit()

    async def set_local_path(self, video_id: str, local_path: Optional[str]) -> None:
        if not self._conn: return
        await self._conn.execute(
            "UPDATE tracks SET local_path=? WHERE video_id=?",
            (local_path, video_id)
        )
        await self._conn.commit()

    async def increment_play_count(self, video_id: str) -> None:
        if not self._conn: return
        ts = int(time.time())
        await self._conn.execute(
            "UPDATE tracks SET play_count = play_count + 1, last_played = ? WHERE video_id = ?",
            (ts, video_id)
        )
        await self._conn.commit()

    async def toggle_favorite(self, video_id: str) -> int:
        if not self._conn: return 0
        async with self._conn.execute(
            """UPDATE tracks
               SET is_favorite = 1 - COALESCE(is_favorite, 0)
               WHERE video_id = ?
               RETURNING is_favorite""",
            (video_id,)
        ) as cursor:
            row = await cursor.fetchone()

        await self._conn.commit()
        return row["is_favorite"] if row else 0

    async def evict_stale_tracks(self) -> int:
        if not self._conn: return 0
        thirty_days_ago = int(time.time()) - (30 * 24 * 3600)

        cursor = await self._conn.execute(
            """SELECT video_id FROM tracks
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

        from config import CACHE_DIR
        for vid in video_ids:
            p = CACHE_DIR / f"{vid}.mp3"
            if p.exists():
                try:
                    p.unlink()
                except Exception as e:
                    logger.error(f"Gagal hapus file cache {p}: {e}")

        placeholders = ','.join(['?'] * len(video_ids))
        await self._conn.execute(
            f"DELETE FROM tracks WHERE video_id IN ({placeholders})", tuple(video_ids)
        )
        await self._conn.commit()

        logger.info(f"Eviction: {len(video_ids)} track stale dihapus dari cache DB")
        return len(video_ids)
