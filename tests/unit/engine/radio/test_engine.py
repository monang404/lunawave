"""
Module: tests.unit.engine.radio.test_engine

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import pytest

from core.event_bus import EventBus
from core.state import AppState, PlayerStatus, TrackInfo
from engine.radio.engine import RadioMode


class MockExtractor:
    pass


class MockDB:
    def __init__(self):
        self.conn = True

    async def get_all_artists(self):
        return ["A", "B"]

    async def get_random_songs(self, limit, exclude_ids, artist):
        return [TrackInfo(video_id=f"v_{artist}", title="T", artist=artist, duration=100)]


class MockController:
    def __init__(self):
        self.bus = EventBus()
        self.played = []

    async def play_track(self, track):
        self.played.append(track)


@pytest.mark.asyncio
async def test_radio_activate_deactivate():
    state = AppState()
    db = MockDB()
    radio = RadioMode(ytdlp=MockExtractor(), state=state, db=db)
    controller = MockController()

    await radio.on_activated(controller)
    assert "A" in radio.artist_selector._seed_artists

    await radio.on_deactivated()
    assert len(radio._bg_tasks) == 0


@pytest.mark.asyncio
async def test_radio_next_with_queue():
    state = AppState()
    db = MockDB()
    radio = RadioMode(ytdlp=MockExtractor(), state=state, db=db)
    controller = MockController()

    t1 = TrackInfo(video_id="1", title="T1", artist="A", duration=100)
    state.radio_queue.append(t1)

    await radio.next(controller)
    assert len(state.radio_queue) == 0
    assert len(controller.played) == 1
    assert controller.played[0] == t1


@pytest.mark.asyncio
async def test_radio_next_empty_queue():
    state = AppState()
    db = MockDB()
    radio = RadioMode(ytdlp=MockExtractor(), state=state, db=db)
    controller = MockController()

    await radio.next(controller)
    assert state.status == PlayerStatus.LOADING
    # _start will be triggered as a bg task
