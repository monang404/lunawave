"""
Module: engine.radio.track_filter

Purpose:
    Filter candidate tracks for the radio queue to prevent duplicates,
    skip recently played tracks, and limit artist dominance.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.state

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread.
"""

import logging

from core.state import AppState, TrackInfo

_log = logging.getLogger(__name__)


class TrackFilter:
    def __init__(self, state: AppState):
        self.state = state
        self.max_history_check = 50
        self.max_per_artist = 3

    def filter_tracks(self, candidates: list[TrackInfo]) -> list[TrackInfo]:
        """
        Filters a list of candidate tracks based on history, queue, duplicates,
        and artist quotas.
        """
        if not candidates:
            return []

        # Build exclusion set from active queue and history
        exclude_ids = set()
        if self.state.current_track:
            exclude_ids.add(self.state.current_track.video_id)

        for t in self.state.radio_queue:
            exclude_ids.add(t.video_id)

        history_list = list(self.state.history)
        for t in history_list[-self.max_history_check :]:
            exclude_ids.add(t.video_id)

        # Build current artist quota from the queue
        artist_counts = {}  # type: ignore
        for t in self.state.radio_queue:
            artist_counts[t.artist] = artist_counts.get(t.artist, 0) + 1

        filtered = []
        seen_in_batch = set()

        for track in candidates:
            # 1. Filter out completely if recently played or in queue
            if track.video_id in exclude_ids:
                continue

            # 2. Filter out duplicates within the candidate batch itself
            if track.video_id in seen_in_batch:
                continue

            # 3. Filter by artist quota to prevent one artist from dominating
            current_count = artist_counts.get(track.artist, 0)
            if current_count >= self.max_per_artist:
                # We skip this track but we might want to log it if debugging
                continue

            # If it passes all filters, add to results and update trackers
            seen_in_batch.add(track.video_id)
            artist_counts[track.artist] = current_count + 1
            filtered.append(track)

        return filtered
