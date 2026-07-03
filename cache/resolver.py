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

    async def resolve(self, track: TrackInfo) -> str:
        """Returns the playback URI (local path atau YouTube URL untuk MPV)."""
        import asyncio

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

        if track.video_id in self._fetching:
            await self._fetching[track.video_id].wait()
            return await self.resolve(track)

        event = asyncio.Event()
        self._fetching[track.video_id] = event

        try:
            url = await self.ytdlp.get_stream_url(track.video_id)
            track.stream_url = url
            await self.db.upsert_track(track, stream_url=url)
            return url  # type: ignore
        finally:
            event.set()
            self._fetching.pop(track.video_id, None)
