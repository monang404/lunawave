from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.command_bus import CMD_DOWNLOAD
from server.handlers.ws_download import handle_download_command


@pytest.mark.asyncio
@patch("server.handlers.ws_download.command_bus.execute", new_callable=AsyncMock)
@patch("server.handlers.ws_download.dict_to_track")
async def test_handle_download_command_download(mock_dict_to_track, mock_execute):
    mock_track = MagicMock()
    mock_dict_to_track.return_value = mock_track

    await handle_download_command("download", {"title": "Test Track"}, None, None, None)

    mock_dict_to_track.assert_called_once_with({"title": "Test Track"})
    mock_execute.assert_called_once_with(CMD_DOWNLOAD, mock_track)


@pytest.mark.asyncio
@patch("server.handlers.ws_download.DiscoverService")
@patch("server.handlers.ws_download.os.remove")
@patch("server.handlers.ws_download.os.path.exists")
async def test_handle_download_command_delete_download(
    mock_exists, mock_remove, mock_discover_service
):
    mock_db = AsyncMock()
    mock_track = MagicMock()
    mock_track.video_id = "test_vid"
    mock_track.local_path = "/path/to/test.mp3"
    mock_track.artist = "Test Artist"
    mock_track.title = "Test Title"

    mock_db.get_track.return_value = mock_track
    mock_exists.return_value = True

    mock_ds_instance = mock_discover_service.return_value
    mock_ds_instance.get_recent = AsyncMock(return_value=[])
    mock_ds_instance.get_favorites = AsyncMock(return_value=[])
    mock_ds_instance.get_cached = AsyncMock(return_value=[])
    mock_ds_instance.get_featured_artists = AsyncMock(return_value=[])
    mock_ds_instance.get_featured_genres = AsyncMock(return_value=[])

    mock_manager = AsyncMock()
    mock_state = MagicMock()

    with patch("server.handlers.ws_download.dict_to_track", return_value=mock_track):
        await handle_download_command(
            "delete_download", {"video_id": "test_vid"}, mock_db, mock_manager, mock_state
        )

    mock_db.get_track.assert_called_once_with("test_vid")
    mock_exists.assert_called_with("/path/to/test.mp3")
    mock_remove.assert_any_call("/path/to/test.mp3")
    mock_db.set_local_path.assert_called_once_with("test_vid", None)

    assert mock_manager.broadcast.call_count == 2
    mock_manager.broadcast.assert_any_call(
        {"type": "log", "data": f"Unduhan dihapus: {mock_track.title}"}
    )
    discover_data_call = mock_manager.broadcast.call_args_list[0]
    assert discover_data_call[0][0]["type"] == "discover_data"
    assert discover_data_call[0][0]["data"]["favorites"] == []
