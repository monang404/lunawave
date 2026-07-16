"""
Module: tests.integration.test_radio_flow

Purpose:
    IT-03: Test end-to-end radio communication.
    Radio enabled -> prefetch -> auto-next.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.command_bus
    - core.commands
    - core.event_bus
    - core.events
    - core.state

Subscribes to:
    - TrackStartedEvent

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio

import pytest

from core.command_bus import command_bus
from core.commands import CMD_SET_MODE
from core.event_bus import bus
from core.events import TrackStartedEvent
from core.state import PlaybackMode


@pytest.mark.asyncio
async def test_radio_flow(integration_app):
    """
    IT-03: Radio Flow
    Skenario: Radio aktif → prefetch → isi queue
    """
    events = []

    async def track_event(evt):
        events.append(evt)

    bus.subscribe(TrackStartedEvent, track_event)

    # 1. Enable radio using a famous artist seed
    integration_app["state"].radio_artist = "Me at the zoo"
    await command_bus.execute(CMD_SET_MODE, PlaybackMode.RADIO)

    # Check that RadioEngine resolves at least one track and starts it
    # Resolving via yt-dlp might take a few seconds
    started = False
    for _ in range(300):
        await asyncio.sleep(0.1)
        if any(isinstance(e, TrackStartedEvent) for e in events):
            started = True
            break

    assert started, "Radio did not start a track within 30 seconds"

    # Wait another few seconds to ensure prefetcher adds to queue
    # The queue mode should show at least 1 track in standby
    # Since we can't easily inspect standby queue from outside,
    # the integration_app fixture exposes state
    state = integration_app["state"]

    prefetched = False
    for _ in range(300):
        await asyncio.sleep(0.1)
        if len(state.queue) > 0:
            prefetched = True
            break

    assert prefetched, "Radio did not prefetch and populate queue within 30 seconds"
