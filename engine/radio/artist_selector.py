"""
Module: engine.radio.artist_selector

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import logging
import random

from core.state import AppState
from engine.radio.common import ARTISTS_PER_BATCH, TRACKS_PER_ARTIST_TARGET
from engine.radio.track_filter import TrackFilter
from engine.radio.track_interleaver import interleave_by_artist

_log = logging.getLogger(__name__)


class ArtistSelector:
    """Rotasi artis, seed selection, deduplication pool."""

    def __init__(self, db, state: AppState):
        self.db = db
        self.state = state
        self._seed_artists: list[str] = []
        self._artist_rotation: list[str] = []

    async def ensure_artists_loaded(self) -> None:
        if self._seed_artists:
            return
        try:
            if self.db and self.db.conn:
                self._seed_artists = await self.db.get_all_artists()
        except Exception as e:
            _log.warning(f"Gagal load artis dari DB: {e}")

        if not self._seed_artists:
            # Bug #3 fix: pesan error sebut path DB yang benar
            raise RuntimeError(
                "Tabel artists kosong. Jalankan: python data/import_artists.py "
                "--db data/lunawave.db --json data/artists.json"
            )

    def reset_rotation(self):
        self._artist_rotation = []

    def build_exclusion_set(self) -> set[str]:
        ids = {t.video_id for t in self.state.radio_queue}
        if self.state.current_track:
            ids.add(self.state.current_track.video_id)
        for t in list(self.state.history)[-20:]:
            ids.add(t.video_id)
        return ids

    async def gather_batch(
        self, prioritized_artist: str | None = None, max_artists: int = ARTISTS_PER_BATCH
    ) -> list:
        limit = max_artists * TRACKS_PER_ARTIST_TARGET
        existing = self.build_exclusion_set()

        if not prioritized_artist and self._seed_artists:
            prioritized_artist = random.choice(self._seed_artists)

        if self.db and getattr(self.db, "conn", None):  # Use getattr for safety
            try:
                tracks = await self.db.get_random_songs(
                    limit=limit, exclude_ids=existing, artist=prioritized_artist
                )
                track_filter = TrackFilter(self.state)
                filtered_tracks = track_filter.filter_tracks(tracks)
                return interleave_by_artist(filtered_tracks)
            except Exception as e:
                _log.warning(f"Gagal mengambil lagu acak dari DB: {e}")
        return []
