import structlog

from cache.resolver import CacheResolver
from core.ports import DatabasePort, LyricsProvider, SponsorBlockProvider
from core.state import TrackInfo
from core.task_utils import safe_create_task

logger = structlog.get_logger(__name__)

class TrackLoader:
    def __init__(
        self,
        resolver: CacheResolver,
        sponsorblock: SponsorBlockProvider,
        lyrics_fetcher: LyricsProvider,
        db: DatabasePort
    ):
        self.resolver = resolver
        self.sponsorblock = sponsorblock
        self.lyrics_fetcher = lyrics_fetcher
        self.db = db

    async def load_track(self, track: TrackInfo) -> str:
        """
        Resolves the track URI and triggers background tasks
        for lyrics and sponsorblock. Also increments play count.
        Returns the playable URI.
        """
        uri = await self.resolver.resolve(track)

        await self.db.increment_play_count(track.video_id)

        safe_create_task(self.sponsorblock.fetch_segments(track.video_id), name=f"fetch_sponsorblock_{track.video_id}")
        safe_create_task(self.lyrics_fetcher.fetch(track), name=f"fetch_lyrics_{track.video_id}")

        return uri
