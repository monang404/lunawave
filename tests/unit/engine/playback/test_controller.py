"""
Module: tests.unit.engine.test_playback_orchestrator

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
from collections import deque

import pytest

from core.events import LogMessageEvent, TrackEndedEvent, TrackPauseChangedEvent, TrackStartedEvent
from core.state import AudioOutput, PlayerStatus
from tests.unit.engine.conftest import make_track


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
        assert state.status == PlayerStatus.PLAYING
