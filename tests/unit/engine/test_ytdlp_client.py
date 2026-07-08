import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from engine.ytdlp_client import YtDlpClient
from core.state import TrackInfo

@pytest.fixture
def ytdlp_client():
    return YtDlpClient()

@pytest.mark.asyncio
async def test_ytdlp_search(ytdlp_client):
    with patch.object(asyncio.get_running_loop(), "run_in_executor", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "entries": [
                {"id": "12345678901", "title": "Test 1", "duration": 180, "uploader": "Artist 1"},
                {"id": "vid2", "title": "Test 2 compilation", "duration": 3600, "uploader": "Artist 2"} # Should be skipped
            ]
        }
        
        results = await ytdlp_client.search("test")
        
        assert len(results) == 1
        assert results[0].video_id == "12345678901"
        assert results[0].title == "Test 1"
        assert results[0].artist == "Artist 1"

@pytest.mark.asyncio
async def test_ytdlp_get_stream_url_success(ytdlp_client):
    with patch.object(asyncio.get_running_loop(), "run_in_executor", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {
            "url": "fallback_url",
            "formats": [
                {"url": "stream_url_audio", "acodec": "mp4a", "vcodec": "none"},
                {"url": "stream_url_video", "acodec": "none", "vcodec": "h264"}
            ]
        }
        
        url = await ytdlp_client.get_stream_url("12345678901")
        assert url == "stream_url_audio"

@pytest.mark.asyncio
async def test_ytdlp_get_stream_url_timeout(ytdlp_client):
    with patch.object(asyncio.get_running_loop(), "run_in_executor", new_callable=AsyncMock) as mock_run:
        with patch.object(asyncio, "wait_for") as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError()
            
            with pytest.raises(RuntimeError) as exc_info:
                await ytdlp_client.get_stream_url("12345678901")
            assert "Timeout" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ytdlp_download_mp3(ytdlp_client):
    with patch.object(asyncio.get_running_loop(), "run_in_executor", new_callable=AsyncMock) as mock_run:
        path = await ytdlp_client.download_mp3("12345678901")
        assert "12345678901.mp3" in path
        mock_run.assert_called_once()
