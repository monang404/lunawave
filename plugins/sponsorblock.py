import json
from typing import Optional

import aiohttp
import structlog

from config import SPONSORBLOCK_CATS
from core.event_bus import EventBus
from core.events import LogMessageEvent, TrackProgressEvent
from core.ports import AudioPlayerPort
from core.state import AppState

logger = structlog.get_logger(__name__)
SPONSORBLOCK_API = "https://sponsor.ajay.app/api/skipSegments"

import asyncio


class SponsorBlockHandler:
    """
    HIGH-02 fix: Uses json.dumps for category serialization.
    MED-01 fix: Accepts a shared aiohttp session.
    """
    def __init__(self, mpv: AudioPlayerPort, state: AppState, session: Optional[aiohttp.ClientSession] = None, event_bus: EventBus = None):
        if session is None:
            raise RuntimeError("aiohttp.ClientSession must be injected")
        if event_bus is None:
            raise RuntimeError("EventBus must be injected")
        self.mpv = mpv
        self.state = state
        self.segments: list[tuple[float, float]] = []
        self._session = session
        self._bus = event_bus
        self._lock = asyncio.Lock()
        self._bus.subscribe(TrackProgressEvent, self._on_progress)

    def cleanup(self):
        self._bus.unsubscribe(TrackProgressEvent, self._on_progress)

    async def fetch_segments(self, video_id: str):
        """Fetches skip segments and stores them in memory for the current track."""
        params = {
            "videoID": video_id,
            "categories": json.dumps(SPONSORBLOCK_CATS),
        }

        new_segments = []
        try:
            async with self._session.get(
                SPONSORBLOCK_API, params=params,
                timeout=aiohttp.ClientTimeout(total=3)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    new_segments = [
                        (seg["segment"][0], seg["segment"][1]) for seg in data
                    ]
                    logger.info(f"SponsorBlock: {len(new_segments)} segments for {video_id}")
                elif resp.status == 404:
                    pass
        except Exception as e:
            logger.debug(f"SponsorBlock fetch failed: {e}")

        async with self._lock:
            self.segments = new_segments

    async def _on_progress(self, event: TrackProgressEvent):
        """Called every ~0.5s by MpvController. Seeks past sponsored segments."""
        current_pos = event.position
        if getattr(self.state, "sponsorblock_active", True) == False:
            return

        async with self._lock:
            if not self.segments or not isinstance(current_pos, (int, float)):
                return
            segments_to_check = self.segments.copy()

        for start, end in segments_to_check:
            if start <= current_pos < end:
                await self.mpv.seek(end)
                await self._bus.publish(LogMessageEvent(message=f"Melewati sponsor ({int(start)}s - {int(end)}s)"))
                break
