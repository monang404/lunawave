import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.ws_discovery import handle_discovery_command


@pytest.mark.asyncio
async def test_handle_discovery_command_search():
    mock_ytdlp = AsyncMock()
    mock_track = MagicMock()
    mock_ytdlp.search.return_value = [mock_track]

    mock_ws = AsyncMock()

    with patch("server.handlers.ws_discovery.track_to_dict", return_value={"title": "Test"}):
        await handle_discovery_command("search", {"query": "Test Query"}, mock_ytdlp, None, mock_ws)

    mock_ytdlp.search.assert_called_once_with("Test Query", max_results=10)
    mock_ws.send_str.assert_called_once()
    sent_data = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_data["type"] == "search_results"
    assert sent_data["data"] == [{"title": "Test"}]


@pytest.mark.asyncio
@patch("server.handlers.ws_discovery.DiscoverService")
async def test_handle_discovery_command_discover(mock_discover_service):
    mock_ds_instance = mock_discover_service.return_value
    mock_ds_instance.get_recent = AsyncMock(return_value=[])
    mock_ds_instance.get_favorites = AsyncMock(return_value=[])
    mock_ds_instance.get_cached = AsyncMock(return_value=[])
    mock_ds_instance.get_featured_artists = AsyncMock(return_value=["Artist 1"])
    mock_ds_instance.get_featured_genres = AsyncMock(return_value=["Pop"])

    mock_db = AsyncMock()
    mock_ws = AsyncMock()

    await handle_discovery_command("discover", {}, None, mock_db, mock_ws)

    mock_ds_instance.get_recent.assert_called_once_with(15)
    mock_ws.send_str.assert_called_once()

    sent_data = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_data["type"] == "discover_data"
    assert sent_data["data"]["featured_artists"] == ["Artist 1"]
    assert sent_data["data"]["featured_genres"] == ["Pop"]
    assert sent_data["data"]["favorites"] == []


@pytest.mark.asyncio
@patch("server.handlers.ws_discovery.track_to_dict", side_effect=lambda t: {"title": t})
@patch("server.handlers.ws_discovery.DiscoverService")
async def test_handle_discovery_command_discover_includes_favorites(
    mock_discover_service, mock_track_to_dict
):
    """PATCH-061 regresi: get_favorites() diambil tapi dulu dibuang, tidak masuk payload."""
    mock_ds_instance = mock_discover_service.return_value
    mock_ds_instance.get_recent = AsyncMock(return_value=[])
    mock_ds_instance.get_favorites = AsyncMock(return_value=["Favorite Track"])
    mock_ds_instance.get_cached = AsyncMock(return_value=[])
    mock_ds_instance.get_featured_artists = AsyncMock(return_value=[])
    mock_ds_instance.get_featured_genres = AsyncMock(return_value=[])

    mock_db = AsyncMock()
    mock_ws = AsyncMock()

    await handle_discovery_command("discover", {}, None, mock_db, mock_ws)

    mock_ds_instance.get_favorites.assert_called_once_with(15)
    sent_data = json.loads(mock_ws.send_str.call_args[0][0])
    assert sent_data["data"]["favorites"] == [{"title": "Favorite Track"}]
