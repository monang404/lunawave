"""
Module: cache.resolver

Purpose:
    Resolve the playback URI for a track using a priority-based cache
    strategy: local file > cached stream URL > fresh yt-dlp extraction.

Responsibilities:
    - Check DB for a valid local path or a non-stale stream URL.
    - Fetch a fresh stream URL via yt-dlp on cache miss and persist it.

Depends on:
    - cache.db (TrackRepositoryPort)
    - core.ports (MediaExtractorPort)
    - config (STREAM_URL_TTL_SEC)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async).
"""

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

    async def resolve(self, track: TrackInfo) -> str:
        """Returns the playback URI (local path atau YouTube URL untuk MPV)."""
        row = await self.db.get_track(track.video_id)

        # Rule 1: Local file — ini yang benar-benar berguna
        if row and row.local_path:
            path = row.local_path
            import asyncio

            if await asyncio.to_thread(os.path.isfile, path):
                track.local_path = path
                return path

        # Rule 2: Gunakan stream_url dari cache jika belum kadaluwarsa
        if row and row.stream_url and row.stream_url_ts:
            ts = row.stream_url_ts
            if time.time() - ts < STREAM_URL_TTL_SEC:
                track.stream_url = row.stream_url
                return track.stream_url

        # Rule 3: Ambil direct URL dari yt-dlp
        url = await self.ytdlp.get_stream_url(track.video_id)
        track.stream_url = url
        # Simpan metadata track ke DB
        await self.db.upsert_track(track, stream_url=url)
        return url  # type: ignore
