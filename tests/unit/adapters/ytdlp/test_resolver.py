"""
Module: adapters.ytdlp.resolver

Purpose:
    Unit tests for adapters.ytdlp.resolver.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    - adapters.ytdlp.resolver

Subscribes to:
    None

Publishes:
    None
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from adapters.ytdlp.resolver import YtDlpResolver

@pytest.fixture
def mock_executor():
    return MagicMock()

@pytest.mark.asyncio
async def test_get_stream_url_success(mock_executor):
    resolver = YtDlpResolver(mock_executor)

    with patch.object(resolver, "_extract_sync", return_value={"url": "http://stream.url/audio.mp3"}):
        with patch("asyncio.get_running_loop", return_value=MagicMock(
            run_in_executor=AsyncMock(return_value={"url": "http://stream.url/audio.mp3"})
        )):
            # The method also calls _pick_audio_url internally, let's mock it
            with patch.object(resolver, "_pick_audio_url", return_value="http://stream.url/audio.mp3"):
                url = await resolver.get_stream_url("abc123_")
                assert url == "http://stream.url/audio.mp3"

@pytest.mark.asyncio
async def test_get_stream_url_failure(mock_executor):
    resolver = YtDlpResolver(mock_executor)

    with patch("asyncio.get_running_loop", return_value=MagicMock(
        run_in_executor=AsyncMock(side_effect=Exception("yt-dlp error"))
    )):
        with pytest.raises(RuntimeError):
            await resolver.get_stream_url("abc123_")

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)
