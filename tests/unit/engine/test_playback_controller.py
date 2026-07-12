"""tests/unit/engine/test_playback_controller.py — mirrors engine/playback/controller.py

Menggunakan FakeAudioPlayer, FakeTrackRepository, dan FakeMediaExtractor.
RadioMode dikecualikan dari test ini — fokus ke QUEUE mode dan logika
core controller.
"""

import asyncio
from collections import deque
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.event_bus import EventBus
from core.events import (
    LogMessageEvent, QueueUpdatedEvent, TrackEndedEvent,
    TrackStartedEvent, TrackPauseChangedEvent, TrackDurationEvent,
)
from core.state import AppState, PlayerStatus, PlaybackMode, AudioOutput, TrackInfo
from tests.fakes.fake_audio_player import FakeAudioPlayer
from tests.fakes.fake_media_extractor import FakeMediaExtractor
from tests.fakes.fake_track_repository import FakeTrackRepository


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class FakeSponsorBlock:
    async def fetch_segments(self, video_id: str) -> None:
        pass


class FakeLyrics:
    async def fetch(self, track: TrackInfo) -> None:
        pass


class FakeQueueMode:
    def __init__(self):
        self.next_calls: list = []

    async def next(self, controller) -> None:
        self.next_calls.append(controller)


class FakeRadioMode:
    def __init__(self):
        self.next_calls = []
        self.activated = False
        self.deactivated = False

    async def next(self, controller) -> None:
        self.next_calls.append(controller)

    async def on_activated(self, controller) -> None:
        self.activated = True

    async def on_deactivated(self) -> None:
        self.deactivated = True

    def check_prefetch(self, controller, position, duration) -> None:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_track(video_id="v1", duration=200):
    return TrackInfo(video_id=video_id, title="Test Song", artist="Artist", duration=duration)


@pytest.fixture
def player():
    p = FakeAudioPlayer()
    # Add missing methods expected by controller
    async def get_position():
        return 0.0
    async def get_duration():
        return 200.0
    async def toggle_pause():
        pass
    p.get_position = get_position
    p.get_duration = get_duration
    p.toggle_pause = toggle_pause
    return p


@pytest.fixture
def bus():
    return EventBus()


@pytest.fixture
def state():
    return AppState(volume=80)


@pytest.fixture
def repo():
    r = FakeTrackRepository()
    r.seed(make_track("v1"))
    return r


@pytest.fixture
def extractor():
    e = FakeMediaExtractor()
    e.stream_urls["v1"] = "https://stream/v1.m4a"
    e.stream_urls["v2"] = "https://stream/v2.m4a"
    return e


@pytest.fixture
def queue_mode():
    return FakeQueueMode()


@pytest.fixture
def radio_mode():
    return FakeRadioMode()


@pytest.fixture
def controller(bus, state, player, repo, extractor, queue_mode, radio_mode):
    from cache.resolver import CacheResolver
    resolver = CacheResolver(db=repo, ytdlp=extractor)
    from engine.playback.controller import PlaybackController
    return PlaybackController(
        bus=bus,
        state=state,
        mpv=player,
        resolver=resolver,
        sponsorblock=FakeSponsorBlock(),
        lyrics_fetcher=FakeLyrics(),
        queue_mode=queue_mode,
        radio_mode=radio_mode,
    )


# ---------------------------------------------------------------------------
# play_track
# ---------------------------------------------------------------------------

class TestPlayTrack:
    async def test_sets_status_to_playing_on_success(self, controller, state, extractor):
        extractor.stream_urls["v1"] = "https://stream/v1"
        track = make_track("v1")
        await controller.play_track(track)
        assert state.status == PlayerStatus.PLAYING

    async def test_sets_current_track(self, controller, state):
        track = make_track("v1")
        await controller.play_track(track)
        assert state.current_track == track

    async def test_publishes_track_started_event(self, controller, bus):
        received = []
        bus.subscribe(TrackStartedEvent, received.append)
        await controller.play_track(make_track("v1"))
        assert len(received) == 1
        assert received[0].track.video_id == "v1"

    async def test_pushes_previous_track_to_history(self, controller, state):
        first = make_track("first")
        second = make_track("v1")
        state.current_track = first
        await controller.play_track(second)
        assert first in list(state.history)

    async def test_resets_position_to_zero(self, controller, state):
        state.position = 999.0
        await controller.play_track(make_track("v1"))
        assert state.position == 0.0

    async def test_sets_status_to_error_on_failure(self, controller, state, extractor):
        # Remove stream URL so resolver can't resolve → raises RuntimeError
        extractor.stream_urls.clear()

        async def raise_on_get(*_a, **_kw):
            raise RuntimeError("no url")

        extractor.get_stream_url = raise_on_get

        track = make_track("v1")
        await controller.play_track(track)
        assert state.status == PlayerStatus.ERROR

    async def test_sets_volume_for_device_output(self, controller, player, state):
        state.audio_output = AudioOutput.DEVICE
        state.volume = 55
        await controller.play_track(make_track("v1"))
        assert ("set_volume", 55) in player.call_log

    async def test_mutes_mpv_for_browser_output(self, controller, player, state):
        state.audio_output = AudioOutput.BROWSER
        await controller.play_track(make_track("v1"))
        assert ("set_volume", 0) in player.call_log


# ---------------------------------------------------------------------------
# _on_stop
# ---------------------------------------------------------------------------

class TestOnStop:
    async def test_stop_sets_idle_and_clears_track(self, controller, state):
        state.current_track = make_track("v1")
        state.status = PlayerStatus.PLAYING
        await controller._on_stop()
        assert state.status == PlayerStatus.IDLE
        assert state.current_track is None

    async def test_stop_clears_queue(self, controller, state):
        state.queue = deque([make_track("v2"), make_track("v3")])
        await controller._on_stop()
        assert len(state.queue) == 0

    async def test_stop_publishes_log_and_queue_updated(self, controller, bus):
        logs = []
        queues = []
        bus.subscribe(LogMessageEvent, logs.append)
        bus.subscribe(QueueUpdatedEvent, queues.append)
        await controller._on_stop()
        assert len(logs) >= 1
        assert len(queues) >= 1


# ---------------------------------------------------------------------------
# _on_prev
# ---------------------------------------------------------------------------

class TestOnPrev:
    async def test_prev_plays_last_history_track(self, controller, state, extractor):
        prev_track = make_track("prev")
        extractor.stream_urls["prev"] = "https://stream/prev"
        state.history.append(prev_track)
        await controller._on_prev()
        assert state.current_track == prev_track

    async def test_prev_publishes_log_when_history_empty(self, controller, bus):
        logs = []
        bus.subscribe(LogMessageEvent, logs.append)
        await controller._on_prev()
        assert any("sebelumnya" in m.message for m in logs)


# ---------------------------------------------------------------------------
# _on_seek
# ---------------------------------------------------------------------------

class TestOnSeek:
    async def test_seek_updates_state_position(self, controller, state, player):
        state.status = PlayerStatus.PLAYING
        await controller._on_seek(42.5)
        assert state.position == pytest.approx(42.5)

    async def test_seek_calls_mpv_seek(self, controller, state, player):
        state.status = PlayerStatus.PLAYING
        await controller._on_seek(30.0)
        assert ("seek", 30.0) in player.call_log

    async def test_seek_is_noop_when_idle(self, controller, state, player):
        state.status = PlayerStatus.IDLE
        await controller._on_seek(30.0)
        assert all(op[0] != "seek" for op in player.call_log)


# ---------------------------------------------------------------------------
# _on_track_ended
# ---------------------------------------------------------------------------

class TestOnTrackEnded:
    async def test_eof_delegates_to_queue_mode_next(self, controller, queue_mode):
        await controller._on_track_ended(TrackEndedEvent(reason="eof"))
        await asyncio.sleep(0.05)
        assert len(queue_mode.next_calls) == 1

    async def test_stop_during_loading_is_ignored(self, controller, queue_mode):
        controller._loading = True
        await controller._on_track_ended(TrackEndedEvent(reason="stop"))
        assert len(queue_mode.next_calls) == 0

    async def test_stop_not_during_loading_sets_idle(self, controller, state):
        state.status = PlayerStatus.PLAYING
        controller._loading = False
        await controller._on_track_ended(TrackEndedEvent(reason="stop"))
        assert state.status == PlayerStatus.IDLE


# ---------------------------------------------------------------------------
# _on_pause_changed
# ---------------------------------------------------------------------------

class TestOnPauseChanged:
    async def test_pause_changed_true_sets_paused_when_playing(self, controller, state):
        state.status = PlayerStatus.PLAYING
        await controller._on_pause_changed(TrackPauseChangedEvent(is_paused=True))
        assert state.status == PlayerStatus.PAUSED

    async def test_pause_changed_false_sets_playing_when_paused(self, controller, state):
        state.status = PlayerStatus.PAUSED
        await controller._on_pause_changed(TrackPauseChangedEvent(is_paused=False))
        assert state.status == PlayerStatus.PLAYING

    async def test_pause_change_ignored_during_loading(self, controller, state):
        state.status = PlayerStatus.PLAYING
        controller._loading = True
        await controller._on_pause_changed(TrackPauseChangedEvent(is_paused=True))
        assert state.status == PlayerStatus.PLAYING  # not changed


# ---------------------------------------------------------------------------
# _on_queue_add / _on_queue_remove / _on_queue_reorder
# ---------------------------------------------------------------------------

class TestQueueManagement:
    async def test_queue_add_appends_track(self, controller, state):
        track = make_track("new")
        await controller._on_queue_add(track)
        assert make_track("new") in list(state.queue)

    async def test_queue_add_publishes_log(self, controller, bus):
        logs = []
        bus.subscribe(LogMessageEvent, logs.append)
        await controller._on_queue_add(make_track("new"))
        assert any("antrean" in m.message.lower() for m in logs)

    async def test_queue_remove_removes_by_index(self, controller, state):
        state.queue = deque([make_track("v1"), make_track("v2")])
        await controller._on_queue_remove(0)
        ids = [t.video_id for t in state.queue]
        assert "v1" not in ids
        assert "v2" in ids

    async def test_queue_remove_out_of_range_is_noop(self, controller, state):
        state.queue = deque([make_track("v1")])
        await controller._on_queue_remove(99)
        assert len(state.queue) == 1

    async def test_queue_reorder_moves_item(self, controller, state):
        t0 = make_track("t0")
        t1 = make_track("t1")
        t2 = make_track("t2")
        state.queue = deque([t0, t1, t2])
        await controller._on_queue_reorder({"from_index": 0, "to_index": 2})
        ids = [t.video_id for t in state.queue]
        assert ids[2] == "t0"

    async def test_queue_replace_clears_and_sets_new(self, controller, state):
        state.queue = deque([make_track("old")])
        new_tracks = [make_track("n1"), make_track("n2")]
        await controller._on_queue_replace(new_tracks)
        ids = [t.video_id for t in state.queue]
        assert ids == ["n1", "n2"]


# ---------------------------------------------------------------------------
# _on_track_duration
# ---------------------------------------------------------------------------

class TestOnTrackDuration:
    async def test_sets_state_duration_when_zero(self, controller, state):
        state.duration = 0
        state.current_track = make_track("v1", duration=0)
        await controller._on_track_duration(TrackDurationEvent(duration=250.0))
        assert state.duration == 250.0

    async def test_does_not_overwrite_known_duration(self, controller, state):
        state.duration = 200.0
        await controller._on_track_duration(TrackDurationEvent(duration=999.0))
        assert state.duration == 200.0  # unchanged


# ---------------------------------------------------------------------------
# _on_set_output
# ---------------------------------------------------------------------------

class TestOnSetOutput:
    async def test_switching_to_browser_mutes_mpv(self, controller, player, state):
        state.volume = 80
        await controller._on_set_output(AudioOutput.BROWSER)
        assert ("set_volume", 0) in player.call_log

    async def test_switching_to_device_restores_volume(self, controller, player, state):
        state.audio_output = AudioOutput.BROWSER
        state.volume = 70
        await controller._on_set_output(AudioOutput.DEVICE)
        assert ("set_volume", 70) in player.call_log

    async def test_output_change_publishes_log(self, controller, bus):
        logs = []
        bus.subscribe(LogMessageEvent, logs.append)
        await controller._on_set_output(AudioOutput.BROWSER)
        assert len(logs) >= 1


# ---------------------------------------------------------------------------
# _on_set_sponsorblock
# ---------------------------------------------------------------------------

class TestOnSetSponsorblock:
    async def test_enables_sponsorblock(self, controller, state):
        state.sponsorblock_active = False
        await controller._on_set_sponsorblock(True)
        assert state.sponsorblock_active is True

    async def test_disables_sponsorblock(self, controller, state):
        state.sponsorblock_active = True
        await controller._on_set_sponsorblock(False)
        assert state.sponsorblock_active is False
