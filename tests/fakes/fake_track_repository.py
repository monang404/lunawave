"""Fake implementation of core.ports.TrackRepositoryPort for tests.
Purpose:
    Auto-generated purpose.

Subscribes to:
    None

Publishes:
    None
"""

from core.state import TrackInfo


class FakeTrackRepository:
    def __init__(self):
        self._tracks: dict[str, TrackInfo] = {}
        self.call_log: list[tuple] = []

    def seed(self, track: TrackInfo) -> None:
        """Test helper: directly place a TrackInfo row into the fake DB."""
        self._tracks[track.video_id] = track

    async def upsert_track(
        self, track: TrackInfo, stream_url: str = None, local_path: str = None
    ) -> None:
        self.call_log.append(("upsert_track", track.video_id, stream_url, local_path))
        existing = self._tracks.get(track.video_id)
        stored = TrackInfo(
            video_id=track.video_id,
            title=track.title,
            artist=track.artist,
            duration=track.duration,
            thumbnail=track.thumbnail,
            local_path=local_path
            if local_path is not None
            else (existing.local_path if existing else None),
            stream_url=stream_url
            if stream_url is not None
            else (existing.stream_url if existing else None),
            view_count=track.view_count,
            stream_url_ts=None,
            play_count=existing.play_count if existing else 0,
            last_played=existing.last_played if existing else None,
            is_favorite=existing.is_favorite if existing else 0,
        )
        if stream_url is not None:
            import time

            stored.stream_url_ts = int(time.time())
        self._tracks[track.video_id] = stored

    async def update_stream_url_only(self, video_id: str, stream_url: str) -> None:
        self.call_log.append(("update_stream_url_only", video_id, stream_url))
        if video_id in self._tracks:
            self._tracks[video_id].stream_url = stream_url

    async def get_track(self, video_id: str) -> TrackInfo | None:
        self.call_log.append(("get_track", video_id))
        return self._tracks.get(video_id)

    async def increment_play_count(self, video_id: str) -> None:
        self.call_log.append(("increment_play_count", video_id))
        if video_id in self._tracks:
            self._tracks[video_id].play_count = (self._tracks[video_id].play_count or 0) + 1
