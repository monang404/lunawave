import pytest
from unittest.mock import AsyncMock
from server.services.stream_prefetch import StreamPrefetchService

@pytest.mark.asyncio
async def test_stream_prefetch_service():
    # Basic instantiation
    state = AsyncMock()
    ytdlp = AsyncMock()
    svc = StreamPrefetchService(state, ytdlp)
    assert svc is not None
