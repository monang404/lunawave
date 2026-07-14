"""
Module: server.services.stream_prefetch

Purpose:
    Pre-fetch and cache the stream URL for the next track in the background
    to reduce playback latency at track transitions.

Responsibilities:
    - Skip pre-fetch when a valid cached URL is already available.
    - Resolve a fresh URL via yt-dlp and persist it to the database.

Depends on:
    - core.ports

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async; spawned as background task).
"""

import time

import structlog

from config import STREAM_URL_TTL_SEC
from core.ports import DatabasePort, MediaExtractorPort

logger = structlog.get_logger(__name__)


class StreamPrefetchService:
    def __init__(self, db: DatabasePort, ytdlp: MediaExtractorPort):
        self.db = db
        self.ytdlp = ytdlp

    async def prefetch_stream_url(self, video_id: str):
        row = await self.db.get_track(video_id)
        if row and row.stream_url and row.stream_url_ts:
            if time.time() - row.stream_url_ts < STREAM_URL_TTL_SEC:
                return
        try:
            url = await self.ytdlp.get_stream_url(video_id)
            await self.db.update_stream_url_only(video_id, url)  # type: ignore
        except Exception as e:
            logger.warning(f"Pre-fetch stream URL gagal untuk {video_id}: {e}")
