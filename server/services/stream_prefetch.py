
import time

import structlog

from config import STREAM_URL_TTL_SEC
from core.ports import DatabasePort, MediaExtractorPort

logger = structlog.get_logger(__name__)
from core.cli_ui import STATS as _LOG_STATS


class StreamPrefetchService:
    def __init__(self, db: DatabasePort, ytdlp: MediaExtractorPort):
        self.db = db
        self.ytdlp = ytdlp
        self._fetching = {}

    async def prefetch_stream_url(self, video_id: str):
        import asyncio
        row = await self.db.get_track(video_id)
        if row and row.stream_url and row.stream_url_ts:
            if time.time() - row.stream_url_ts < STREAM_URL_TTL_SEC:
                return

        if video_id in self._fetching:
            await self._fetching[video_id].wait()
            return

        event = asyncio.Event()
        self._fetching[video_id] = event

        try:
            url = await self.ytdlp.get_stream_url(video_id)
            await self.db.update_stream_url_only(video_id, url)
        except Exception as e:
            _LOG_STATS.inc("timeouts") if "timeout" in str(e).lower() or "Timeout" in str(e) else None
            logger.warning(f"Pre-fetch stream URL gagal untuk {video_id}: {e}")
        finally:
            event.set()
            self._fetching.pop(video_id, None)
