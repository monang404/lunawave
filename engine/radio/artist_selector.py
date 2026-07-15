"""
Module: engine.radio.artist_selector

Purpose:
    Selects and rotates artists intelligently to maintain variety in radio mode.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.state
    - engine.radio.common
    - engine.radio.track_filter
    - engine.radio.track_interleaver

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
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

    async def _sampled_seed_artist(self) -> str | None:
        if not self._seed_artists:
            return None
        stats = {}
        if self.db and getattr(self.db, "conn", None):
            try:
                stats = await self.db.get_reward_stats()
            except Exception as e:
                _log.warning(f"Gagal ambil reward stats: {e}")
        from engine.radio.artist_bandit import ArtistStat, sample_artists

        candidates = [
            ArtistStat(name=name, alpha=stats.get(name, (1, 1))[0], beta=stats.get(name, (1, 1))[1])
            for name in self._seed_artists
        ]
        picked = sample_artists(candidates, k=1)
        return picked[0] if picked else None

    async def gather_batch(
        self, prioritized_artist: str | None = None, max_artists: int = ARTISTS_PER_BATCH
    ) -> list:
        limit = max_artists * TRACKS_PER_ARTIST_TARGET
        existing = self.build_exclusion_set()

        if not prioritized_artist and self._seed_artists:
            prioritized_artist = await self._sampled_seed_artist()

        if self.db and getattr(self.db, "conn", None):  # Use getattr for safety
            try:
                artists = [prioritized_artist] if prioritized_artist else None
                tracks = await self.db.get_random_songs(
                    limit=limit, exclude_ids=existing, artists=artists
                )
                track_filter = TrackFilter(self.state)
                filtered_tracks = track_filter.filter_tracks(tracks)
                return interleave_by_artist(filtered_tracks)
            except Exception as e:
                _log.warning(f"Gagal mengambil lagu acak dari DB: {e}")
        return []
