import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from plugins.sponsorblock import SponsorBlockHandler
from core.events import TrackProgressEvent
from core.state import AppState

class MockResponse:
    def __init__(self, data, event=None, status=200, error=False):
        self.data = data
        self.status = status
        self.event = event
        self.error = error
    
    async def json(self):
        return self.data
    
    async def __aenter__(self):
        if self.event:
            await self.event.wait()
        if self.error:
            raise ValueError("Network error")
        return self
        
    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
async def test_sponsorblock_fetch_segments_preserves_old_segments_during_fetch():
    mpv = MagicMock()
    mpv.seek = AsyncMock()
    state = AppState()
    session = MagicMock()
    bus = MagicMock()
    bus.publish = AsyncMock()
    
    handler = SponsorBlockHandler(mpv, state, session, bus)
    handler.segments = [(10, 20)]
    
    fetch_event = asyncio.Event()
    
    def delayed_get(*args, **kwargs):
        return MockResponse([{"segment": [30, 40]}], event=fetch_event)
        
    session.get = delayed_get
    
    # Start fetch task
    fetch_task = asyncio.create_task(handler.fetch_segments("new_video"))
    
    # Yield control to the event loop so fetch_task starts and hits delayed_get
    await asyncio.sleep(0.01)
    
    # Check that segments are still (10, 20) during fetch!
    assert handler.segments == [(10, 20)]
    
    # Now simulate a TrackProgressEvent while fetching
    # Should seek because 15 is in (10, 20)
    event = TrackProgressEvent(position=15)
    await handler._on_progress(event)
    
    mpv.seek.assert_called_once_with(20)
    
    # Let fetch complete
    fetch_event.set()
    await fetch_task
    
    # Now segments should be updated to (30, 40)
    assert handler.segments == [(30, 40)]

@pytest.mark.asyncio
async def test_sponsorblock_fetch_failed_clears_segments():
    mpv = MagicMock()
    state = AppState()
    session = MagicMock()
    bus = MagicMock()
    
    handler = SponsorBlockHandler(mpv, state, session, bus)
    handler.segments = [(10, 20)]
    
    def error_get(*args, **kwargs):
        return MockResponse([], error=True)
        
    session.get = error_get
    
    await handler.fetch_segments("new_video")
    
    # If fetch fails, we expect it to clear segments to avoid using old track's segments for the new track
    assert handler.segments == []
