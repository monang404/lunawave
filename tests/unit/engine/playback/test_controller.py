"""
Module: tests.unit.engine.test_playback_orchestrator

Purpose:
    Unit tests for the main playback controller logic.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.events
    - core.state
    - tests.unit.engine.conftest

Subscribes to:
    - LogMessageEvent
    - TrackStartedEvent

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
from collections import deque
from unittest.mock import AsyncMock, patch

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

    async def test_play_track_start_paused(self, controller, state, player, extractor):
        extractor.stream_urls["v1"] = "https://stream/v1"
        track = make_track("v1")
        await controller.play_track(track, start_position=10.5, start_paused=True)

        assert state.position == 10.5
        assert state.status == PlayerStatus.PAUSED
        assert ("pause",) in player.call_log
        assert ("seek", 10.5) in player.call_log

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

    async def test_play_track_concurrent(self, controller, state, extractor):
        extractor.stream_urls["v1"] = "https://stream/v1"
        extractor.stream_urls["v2"] = "https://stream/v2"

        async def delayed_get(*args, **kwargs):
            await asyncio.sleep(0.01)
            return "https://stream/mock"

        extractor.get_stream_url = delayed_get

        t1 = asyncio.create_task(controller.play_track(make_track("v1")))
        t2 = asyncio.create_task(controller.play_track(make_track("v2")))
        await asyncio.gather(t1, t2)

        assert len(state.history) == 1
        assert state.current_track.video_id in ["v1", "v2"]
        assert state.status == PlayerStatus.PLAYING


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

    async def test_prev_with_empty_history(self, controller, state, bus):
        state.history.clear()
        logs = []
        bus.subscribe(LogMessageEvent, logs.append)
        await controller._on_prev()
        assert len(logs) == 1
        assert "Tidak ada lagu sebelumnya" in logs[0].message
        assert state.current_track is None


class TestOnNext:
    async def test_next_with_empty_queue(self, controller, state, queue_mode):
        from core.state import PlaybackMode

        state.playback_mode = PlaybackMode.QUEUE
        state.queue.clear()

        await controller._on_next()

        assert len(queue_mode.next_calls) == 1


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

    async def test_seek_exception_rollback(self, controller, state, player):
        state.status = PlayerStatus.PLAYING
        state.position = 10.0

        async def seek_mock(*args):
            raise RuntimeError("Seek failed")

        player.seek = seek_mock

        with pytest.raises(RuntimeError):
            await controller._on_seek(50.0)

        assert state.position == 10.0


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

    async def test_stale_stop_within_grace_window_after_transition_is_ignored(
        self, controller, state
    ):
        # Simulasikan track baru baru saja mulai play_track() (mis. mpv.play sudah
        # dipanggil), lalu event 'stop' basi dari track LAMA nyampe telat setelah
        # _loading balik False tapi masih dalam grace window transisi.
        controller._last_play_start_ts = asyncio.get_event_loop().time()
        controller._loading = False
        state.status = PlayerStatus.PLAYING
        await controller._on_track_ended(TrackEndedEvent(reason="stop"))
        # Karena masih dalam grace window & status sudah PLAYING lagi (track baru),
        # stop basi ini harus diabaikan, bukan meng-overwrite jadi IDLE.
        assert state.status == PlayerStatus.PLAYING

    async def test_stop_long_after_transition_sets_idle_immediately(self, controller, state):
        # Stop yang datang jauh di luar grace window (tidak ada transisi baru
        # yang relevan) harus langsung IDLE tanpa nunggu sleep 0.35s.
        controller._last_play_start_ts = asyncio.get_event_loop().time() - 10.0
        controller._loading = False
        state.status = PlayerStatus.PLAYING
        await controller._on_track_ended(TrackEndedEvent(reason="stop"))
        assert state.status == PlayerStatus.IDLE

    async def test_error_sets_status_error_and_advances_after_sleep(
        self, controller, state, queue_mode, bus
    ):
        state.status = PlayerStatus.PLAYING
        state.current_track = make_track("v1")

        logs = []
        bus.subscribe(LogMessageEvent, logs.append)

        with patch("engine.playback.controller.asyncio.sleep", AsyncMock()):
            await controller._on_track_ended(TrackEndedEvent(reason="error"))

            assert state.status == PlayerStatus.ERROR
            assert len(queue_mode.next_calls) == 1
            assert any("kesalahan pemutaran" in m.message for m in logs)


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


class TestDispose:
    async def test_dispose_unsubscribes_all_handlers(self, controller, bus, state):
        """PATCH-2026-07-16-001: setelah dispose(), controller tidak lagi
        bereaksi terhadap event apapun -- baik yang disubscribe lewat
        lambda closure maupun lewat bound method langsung."""
        controller.dispose()

        state.status = PlayerStatus.PLAYING
        await bus.publish(TrackPauseChangedEvent(is_paused=True))
        # Kalau masih subscribed, _on_pause_changed akan set PAUSED.
        assert state.status == PlayerStatus.PLAYING

    async def test_dispose_cancels_pending_fade_task(self, controller):
        async def never_finishes():
            await asyncio.sleep(100)

        controller._fade_task = asyncio.ensure_future(never_finishes())

        controller.dispose()
        await asyncio.sleep(0)

        assert controller._fade_task.cancelled() or controller._fade_task.cancelling()

    async def test_dispose_is_safe_to_call_when_no_fade_task(self, controller):
        controller._fade_task = None
        controller.dispose()  # should not raise


class TestTogglePause:
    async def test_toggle_pause_ignored_during_loading(self, controller, state, player):
        state.status = PlayerStatus.LOADING

        await controller._on_cmd_toggle_pause()

        assert all(op[0] != "toggle_pause" for op in player.call_log)
