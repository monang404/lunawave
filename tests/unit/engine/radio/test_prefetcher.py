"""
Module: tests.unit.engine.radio.test_prefetcher

Purpose:
    Unit tests for radio track prefetching.

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    - core.state
    - engine.radio.prefetcher

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import pytest

from core.state import AppState, TrackInfo
from engine.radio.prefetcher import RadioPrefetcher


class MockArtistSelector:
    async def gather_batch(self, prioritized_artist=None, max_artists=1):
        return [
            TrackInfo(video_id="1", title="T1", artist="A", duration=100),
            TrackInfo(video_id="2", title="T2", artist="B", duration=100),
        ]


class MockPlaybackController:
    pass


@pytest.mark.asyncio
async def test_build_and_pop_standby():
    state = AppState()
    selector = MockArtistSelector()
    prefetcher = RadioPrefetcher(state, selector)
    controller = MockPlaybackController()

    # Standby is initially empty
    assert await prefetcher.pop_standby() is None

    # Build standby
    await prefetcher.build_standby(controller)
    assert len(prefetcher._standby) == 2

    # Pop standby
    popped = await prefetcher.pop_standby()
    assert len(popped) == 2
    assert popped[0].video_id == "1"

    # Standby is empty again
    assert await prefetcher.pop_standby() is None


@pytest.mark.asyncio
async def test_clear_standby():
    state = AppState()
    selector = MockArtistSelector()
    prefetcher = RadioPrefetcher(state, selector)
    controller = MockPlaybackController()

    await prefetcher.build_standby(controller)
    assert len(prefetcher._standby) == 2

    await prefetcher.async_clear_standby()
    assert len(prefetcher._standby) == 0
