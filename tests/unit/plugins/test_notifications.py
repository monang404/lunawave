import pytest
from unittest.mock import AsyncMock
from plugins.notifications import TermuxNowPlaying

@pytest.mark.asyncio
async def test_termux_now_playing():
    bus = AsyncMock()
    state = AsyncMock()
    plugin = TermuxNowPlaying(bus, state)
    assert plugin is not None
