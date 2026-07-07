import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from server.handlers.ws.discover_handlers import _handle_search
from core.state import TrackInfo

@pytest.mark.asyncio
async def test_search_results_has_pagination_structure():
    mock_ws = AsyncMock()
    mock_ytdlp = AsyncMock()
    mock_track = TrackInfo(
        video_id="abc12345678",
        title="Test Song",
        artist="Test Artist",
        duration=120,
        thumbnail="thumb.jpg",
        view_count=1000
    )
    mock_ytdlp.search.return_value = [mock_track, mock_track]
    
    data = {"query": "test query", "max_results": 2}
    
    await _handle_search(data, mock_ws, None, mock_ytdlp, None, None, None)
    
    mock_ws.send_str.assert_called_once()
    payload_str = mock_ws.send_str.call_args[0][0]
    payload = json.loads(payload_str)
    
    assert payload["type"] == "search_results"
    assert "items" in payload["data"]
    assert "next_page_token" in payload["data"]
    assert "total_count" in payload["data"]
    
    assert len(payload["data"]["items"]) == 2
    assert payload["data"]["total_count"] == 2
    assert payload["data"]["next_page_token"] is None
