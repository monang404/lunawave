import asyncio
import os
import time

import structlog

from config import STREAM_URL_TTL_SEC
from core.ports import MediaExtractorPort, TrackRepositoryPort
from core.state import TrackInfo

logger = structlog.get_logger(__name__)

class CacheResolver:
    """
    Priority Rules:
    1. Local file exists -> return local_path
    2. Stream URL is fresh -> return stream_url
    3. Stale -> fetch new stream URL from yt-dlp, save to DB, return it
    """

    def __init__(self, db: TrackRepositoryPort, ytdlp: MediaExtractorPort):
        self.db = db
        self.ytdlp = ytdlp
        self._fetching = {}  # type: ignore
        self._lock = asyncio.Lock()

    async def resolve(self, track: TrackInfo) -> str:
        """Returns the playback URI (local path atau YouTube URL untuk MPV)."""
        row = await self.db.get_track(track.video_id)

        if row and row.local_path:
            path = row.local_path
            if await asyncio.to_thread(os.path.isfile, path):
                track.local_path = path
                return path

        if row and row.stream_url and row.stream_url_ts:
            ts = row.stream_url_ts
            if time.time() - ts < STREAM_URL_TTL_SEC:
                track.stream_url = row.stream_url
                return track.stream_url

        async with self._lock:
            if track.video_id in self._fetching:
                fut = self._fetching[track.video_id]
                needs_fetch = False
            else:
                fut = asyncio.get_running_loop().create_future()
                self._fetching[track.video_id] = fut
                needs_fetch = True

        if needs_fetch:
            try:
                url = await asyncio.wait_for(self.ytdlp.get_stream_url(track.video_id), timeout=30.0)
                track.stream_url = url
                await self.db.upsert_track(track, stream_url=url)
                if not fut.done():
                    fut.set_result(url)
                return url  # type: ignore
            except Exception as e:
                if not fut.done():
                    fut.set_exception(e)
                raise
            finally:
                async with self._lock:
                    self._fetching.pop(track.video_id, None)
        else:
            return await asyncio.wait_for(fut, timeout=35.0)
