"""
Module: tests.unit.server.test_serializers

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

from core.state import AppState, PlaybackMode, PlayerStatus, TrackInfo
from server.serializers import dict_to_track, state_to_dict, track_to_dict


def test_track_to_dict():
    assert track_to_dict(None) is None

    t = TrackInfo(video_id="v1", title="Title", artist="Artist", duration=100, is_favorite=1)
    d = track_to_dict(t)
    assert d["video_id"] == "v1"
    assert d["title"] == "Title"
    assert d["is_favorite"] is True


def test_dict_to_track():
    d = {"video_id": "v1", "title": "Title", "duration": 100, "is_favorite": True}
    t = dict_to_track(d)
    assert t.video_id == "v1"
    assert t.title == "Title"
    assert getattr(t, "is_favorite", 0) == 1

    assert dict_to_track({"title": "Only Title"}) is None


def test_state_to_dict():
    state = AppState()
    state.status = PlayerStatus.PLAYING
    state.playback_mode = PlaybackMode.RADIO
    state.lyrics_lines = ["Line 1"]

    d = state_to_dict(state)
    assert d["status"] == "PLAYING"
    assert d["playback_mode"] == "RADIO"
    assert d["lyrics_lines"] == ["Line 1"]

    d_no_lyrics = state_to_dict(state, include_lyrics=False)
    assert "lyrics_lines" not in d_no_lyrics
