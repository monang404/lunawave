import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from cache.resolver import CacheResolver
from core.state import TrackInfo


@pytest.mark.asyncio
async def test_resolver_concurrency_and_timeout():
    db = MagicMock()
    db.get_track = AsyncMock(return_value=None)
    db.upsert_track = AsyncMock()

    ytdlp = MagicMock()

    fetch_event = asyncio.Event()

    async def delayed_fetch(video_id):
        await fetch_event.wait()
        return f"http://stream.url/{video_id}"

    ytdlp.get_stream_url = AsyncMock(side_effect=delayed_fetch)

    resolver = CacheResolver(db, ytdlp)

    track1 = TrackInfo(video_id="vid1", title="test", artist="test", duration=100)
    track2 = TrackInfo(video_id="vid1", title="test", artist="test", duration=100)

    task1 = asyncio.create_task(resolver.resolve(track1))

    # Let task1 start and acquire the lock
    await asyncio.sleep(0.01)

    # Task2 should join the same future
    task2 = asyncio.create_task(resolver.resolve(track2))

    await asyncio.sleep(0.01)

    # Both tasks are waiting on fetch_event
    assert "vid1" in resolver._fetching

    # Let it finish
    fetch_event.set()

    url1 = await task1
    url2 = await task2

    assert url1 == url2 == "http://stream.url/vid1"

    # ytdlp should only be called once!
    assert ytdlp.get_stream_url.call_count == 1

    assert "vid1" not in resolver._fetching

@pytest.mark.asyncio
async def test_resolver_propagates_exception():
    db = MagicMock()
    db.get_track = AsyncMock(return_value=None)
    db.upsert_track = AsyncMock()

    ytdlp = MagicMock()

    fetch_event = asyncio.Event()

    async def failing_fetch(video_id):
        await fetch_event.wait()
        raise ValueError("YtDlp failed")

    ytdlp.get_stream_url = AsyncMock(side_effect=failing_fetch)

    resolver = CacheResolver(db, ytdlp)
    track1 = TrackInfo(video_id="vid2", title="test", artist="test", duration=100)
    track2 = TrackInfo(video_id="vid2", title="test", artist="test", duration=100)

    task1 = asyncio.create_task(resolver.resolve(track1))
    await asyncio.sleep(0.01)
    task2 = asyncio.create_task(resolver.resolve(track2))
    await asyncio.sleep(0.01)

    fetch_event.set()

    with pytest.raises(ValueError, match="YtDlp failed"):
        await task1

    with pytest.raises(ValueError, match="YtDlp failed"):
        await task2

    assert ytdlp.get_stream_url.call_count == 1
    assert "vid2" not in resolver._fetching
