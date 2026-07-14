"""
Module: engine.playback.track_loader

Purpose:
    Resolve a track URI and trigger background side-effects (sponsorblock,
    lyrics fetch, play-count increment) before playback begins.

Responsibilities:
    - Delegate URI resolution to CacheResolver.
    - Increment play count and launch sponsorblock/lyrics tasks in parallel.

Depends on:
    - cache.resolver
    - core.ports (LyricsProvider, SponsorBlockProvider)
    - core.state (TrackInfo)
    - core.task_utils

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async).
"""

import structlog

from core.ports import LyricsProvider, SponsorBlockProvider, StreamResolverPort
from core.state import TrackInfo
from core.task_utils import safe_create_task

logger = structlog.get_logger(__name__)


class TrackLoader:
    def __init__(
        self,
        resolver: StreamResolverPort,
        sponsorblock: SponsorBlockProvider,
        lyrics_fetcher: LyricsProvider,
    ):
        self.resolver = resolver
        self.sponsorblock = sponsorblock
        self.lyrics_fetcher = lyrics_fetcher

    async def load_track(self, track: TrackInfo) -> str:
        """
        Resolves the track URI and triggers background tasks
        for lyrics and sponsorblock. Also increments play count.
        Returns the playable URI.
        """
        # Resolve URI
        uri = await self.resolver.resolve(track)

        # C-02: Increment play count — fire-and-forget, tidak boleh menunda mpv.play(uri)
        safe_create_task(
            self.resolver.db.increment_play_count(track.video_id),
            name=f"incr_play_count_{track.video_id}",
        )

        # Fetch sponsorblock and lyrics
        safe_create_task(
            self.sponsorblock.fetch_segments(track.video_id),
            name=f"fetch_sponsorblock_{track.video_id}",
        )
        safe_create_task(self.lyrics_fetcher.fetch(track), name=f"fetch_lyrics_{track.video_id}")

        return uri
