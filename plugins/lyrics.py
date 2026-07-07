import asyncio
import bisect
import re

import aiohttp
import structlog
import syncedlyrics

from config import LYRICS_API_BASE
from core.event_bus import EventBus
from core.events import LyricsUpdatedEvent, TrackProgressEvent

logger = structlog.get_logger(__name__)

from core.state import TrackInfo


class LyricsFetcher:
    """
    MED-01 fix: Accepts a shared aiohttp session.
    LOW-07 fix: Strips timestamp prefixes from displayed lyrics.
    """
    def __init__(self, state, session: aiohttp.ClientSession = None, event_bus: EventBus = None):  # type: ignore
        if session is None:
            raise RuntimeError("aiohttp.ClientSession must be injected")
        if event_bus is None:
            raise RuntimeError("EventBus must be injected")
        self.state = state
        self.lyrics_data: list[tuple[float, str]] = []
        self._session = session
        self._current_generation = 0
        self._cache: dict[str, str] = {}
        self._bus = event_bus
        self._bus.subscribe(TrackProgressEvent, self._on_progress)

    def cleanup(self):
        self._bus.unsubscribe(TrackProgressEvent, self._on_progress)

    async def fetch(self, track: TrackInfo):
        """Fetches synchronized lyrics from lrclib.net and parses them."""
        title = track.title
        artist = track.artist
        duration = track.duration
        self.lyrics_data = []
        self.state.lyrics_lines = []
        self.state.lyrics_index = 0
        self.state.lyrics_offset = 0.0
        self.state.lyrics_loading = True

        self._current_generation += 1
        gen = self._current_generation

        await self._bus.publish(LyricsUpdatedEvent())

        try:
            lrc = None
            if track.video_id in self._cache:
                lrc = self._cache[track.video_id]
                logger.debug(f"Lyrics: Using cached lyrics for {track.video_id}")
            else:
                session = self._session
                url_get = f"{LYRICS_API_BASE}/get"
                params_get = {"track_name": title, "artist_name": artist, "duration": duration}

                async with session.get(url_get, params=params_get, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        lrc = data.get("syncedLyrics") or data.get("plainLyrics", "")

            if not lrc:
                clean_title = re.sub(r'[\(\[].*?[\)\]]', '', title)
                for kw in ['official', 'music video', 'lyric', 'lyrics', 'audio', 'video', 'mv', 'hq']:
                    clean_title = re.sub(rf'\b{kw}s?\b', '', clean_title, flags=re.IGNORECASE)
                clean_title = re.sub(r'\s+', ' ', clean_title).strip('- ')

                if "-" in title:
                    search_query = clean_title
                else:
                    search_query = f"{clean_title} {artist}" if artist and artist.lower() not in ["unknown", "topic"] else clean_title

                url_search = f"{LYRICS_API_BASE}/search"
                params_search = {"q": search_query}

                async with session.get(url_search, params=params_search, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        if isinstance(results, list):
                            for res in results:
                                lrc = res.get("syncedLyrics") or res.get("plainLyrics", "")
                                if lrc:
                                    break

            if not lrc:
                logger.info("lrclib failed. Falling back to syncedlyrics (Musixmatch/NetEase/etc)...")
                logger.info(f"syncedlyrics query: {search_query}")
                loop = asyncio.get_running_loop()
                try:
                    lrc = await asyncio.wait_for(loop.run_in_executor(None, syncedlyrics.search, search_query), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning("syncedlyrics timeout (5.0s)")
                    lrc = None
                except (ValueError, KeyError, TypeError, AttributeError) as e:
                    logger.error("syncedlyrics plugin crashed (API structure changed?)", exc_info=e)
                    lrc = None

            if self._current_generation == gen:
                if lrc:
                    if track.video_id not in self._cache:
                        self._cache[track.video_id] = lrc
                        if len(self._cache) > 50:
                            self._cache.pop(next(iter(self._cache)))
                    self.lyrics_data = self._parse_lrc(lrc)
                    self.state.lyrics_lines = [text for _, text in self.lyrics_data]
                    self.state.lyrics_timestamps = [t for t, _ in self.lyrics_data]
                    await self._bus.publish(LyricsUpdatedEvent())
                    logger.info(f"Lyrics: fetched {len(self.lyrics_data)} lines")
                else:
                    logger.info("Lyrics: No lyrics found anywhere")

        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError, KeyError) as e:
            if self._current_generation == gen:
                logger.warning("Lyrics fetch failed", exc_info=e)
        finally:
            if self._current_generation == gen:
                self.state.lyrics_loading = False
                await self._bus.publish(LyricsUpdatedEvent())

    def _parse_lrc(self, lrc_text: str) -> list[tuple[float, str]]:
        """Parse LRC format. Strips timestamp tags from text content."""
        pattern = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)")
        result = []
        for line in lrc_text.splitlines():
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                minutes, seconds, text = m.groups()
                timestamp = int(minutes) * 60 + float(seconds)
                result.append((timestamp, text.strip()))

        return sorted(result, key=lambda x: x[0])

    async def _on_progress(self, event: TrackProgressEvent):
        """Find the active lyric index based on current playback position."""
        position = event.position
        if not self.lyrics_data or not isinstance(position, (int, float)):
            return

        timestamps = getattr(self.state, "lyrics_timestamps", [])
        if not timestamps:
            timestamps = [t for t, _ in self.lyrics_data]
            self.state.lyrics_timestamps = timestamps
        adjusted_position = position + self.state.lyrics_offset
        active_idx = bisect.bisect_right(timestamps, adjusted_position) - 1
        active_idx = max(0, active_idx)

        if self.state.lyrics_index != active_idx:
            self.state.lyrics_index = active_idx
            await self._bus.publish(LyricsUpdatedEvent())
