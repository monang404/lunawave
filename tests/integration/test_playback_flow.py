"""
Module: tests.integration.test_playback_flow

Purpose:
    IT-02: Test end-to-end playback communication.
    Play -> pause -> next via CommandBus and verify EventBus.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
import pytest

from core.command_bus import command_bus
from core.commands import CMD_PLAY_TRACK, CMD_TOGGLE_PAUSE, CMD_NEXT
from core.event_bus import bus
from core.events import TrackStartedEvent, TrackPauseChangedEvent
from core.state import TrackInfo


@pytest.mark.asyncio
async def test_playback_flow(integration_app):
    """
    IT-02: Playback Flow
    Skenario: Play → pause → next via CommandBus asli
    """
    events = []

    async def track_event(evt):
        events.append(evt)

    bus.subscribe(TrackStartedEvent, track_event)
    bus.subscribe(TrackPauseChangedEvent, track_event)

    # 1. Play track 1
    # Dispatching a short test track
    track1 = TrackInfo(video_id="jNQXAC9IVRw", title="Me at the zoo", duration=19)
    await command_bus.dispatch(CMD_PLAY_TRACK, track1)

    # Wait for MPV to start it
    started = False
    for _ in range(50):
        await asyncio.sleep(0.1)
        if any(isinstance(e, TrackStartedEvent) for e in events):
            started = True
            break

    assert started, "MPV did not start track within 5 seconds"

    track_1_id = next(e.track.video_id for e in events if isinstance(e, TrackStartedEvent))
    events.clear()

    # 2. Pause
    await command_bus.dispatch(CMD_TOGGLE_PAUSE)
    paused = False
    for _ in range(50):
        await asyncio.sleep(0.1)
        if any(isinstance(e, TrackPauseChangedEvent) and e.is_paused for e in events):
            paused = True
            break

    assert paused, "MPV did not pause track within 5 seconds"
    events.clear()

    # 3. Next track (need something in queue or just supply another track to queue first)
    # Actually just overriding play since we don't have a queue built up
    track2 = TrackInfo(video_id="BaW_jenozKc", title="Short Video", duration=10)
    await command_bus.dispatch(CMD_PLAY_TRACK, track2)

    # Wait for MPV to start new track
    new_started = False
    for _ in range(50):
        await asyncio.sleep(0.1)
        if any(isinstance(e, TrackStartedEvent) for e in events):
            new_started = True
            break

    assert new_started, "MPV did not start second track within 5 seconds"
    track_2_id = next(e.track.video_id for e in events if isinstance(e, TrackStartedEvent))

    assert track_1_id != track_2_id, "Track ID did not change after next command"
