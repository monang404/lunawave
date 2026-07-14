"""
Module: tests.unit.engine.radio.test_track_filter

Purpose:
    Auto-generated test scaffold.

Subscribes to:
    None

Publishes:
    None
"""

from collections import deque

from core.state import AppState, TrackInfo
from engine.radio.track_filter import TrackFilter


def make_track(vid: str, artist: str = "A") -> TrackInfo:
    return TrackInfo(video_id=vid, title=f"Title {vid}", artist=artist, duration=100)


def test_filter_empty_list():
    state = AppState()
    tf = TrackFilter(state)
    assert tf.filter_tracks([]) == []


def test_filter_duplicates_in_candidates():
    state = AppState()
    tf = TrackFilter(state)

    t1 = make_track("v1", "A")
    t2 = make_track("v1", "A")  # Duplicate video_id
    t3 = make_track("v2", "B")

    filtered = tf.filter_tracks([t1, t2, t3])
    assert len(filtered) == 2
    assert [t.video_id for t in filtered] == ["v1", "v2"]


def test_filter_recently_played_and_queue():
    state = AppState()
    state.current_track = make_track("c1")
    state.radio_queue = deque([make_track("q1"), make_track("q2")])
    state.history = deque([make_track("h1"), make_track("h2")])

    tf = TrackFilter(state)

    candidates = [
        make_track("c1"),  # current
        make_track("q2"),  # in queue
        make_track("h1"),  # in history
        make_track("new1"),  # valid
        make_track("new2", "B"),  # valid
    ]

    filtered = tf.filter_tracks(candidates)
    assert len(filtered) == 2
    assert [t.video_id for t in filtered] == ["new1", "new2"]


def test_filter_artist_quota():
    state = AppState()
    # Already 2 songs by artist A in queue
    state.radio_queue = deque([make_track("q1", "A"), make_track("q2", "A")])

    tf = TrackFilter(state)
    tf.max_per_artist = 3

    candidates = [
        make_track("c1", "A"),  # Should be accepted (total 3)
        make_track("c2", "A"),  # Should be filtered out (would be 4)
        make_track("c3", "B"),  # Should be accepted
    ]

    filtered = tf.filter_tracks(candidates)
    assert len(filtered) == 2
    assert [t.video_id for t in filtered] == ["c1", "c3"]
