from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.command_bus import (
    CMD_PLAY_TRACK,
    CMD_QUEUE_ADD,
    CMD_QUEUE_REMOVE,
    CMD_QUEUE_REORDER,
    CMD_QUEUE_REPLACE,
    CMD_QUEUE_SELECT,
    CMD_SET_MODE,
)
from core.state import PlaybackMode
from server.handlers.ws_queue import handle_queue_command


@pytest.mark.asyncio
@patch("server.handlers.ws_queue.command_bus.execute", new_callable=AsyncMock)
async def test_handle_queue_command_queue_select(mock_execute):
    await handle_queue_command("queue_select", {"index": 5}, None)
    mock_execute.assert_called_once_with(CMD_QUEUE_SELECT, 5)


@pytest.mark.asyncio
@patch("server.handlers.ws_queue.command_bus.execute", new_callable=AsyncMock)
async def test_handle_queue_command_queue_remove(mock_execute):
    await handle_queue_command("queue_remove", {"index": 2}, None)
    mock_execute.assert_called_once_with(CMD_QUEUE_REMOVE, 2)


@pytest.mark.asyncio
@patch("server.handlers.ws_queue.command_bus.execute", new_callable=AsyncMock)
@patch("server.handlers.ws_queue.dict_to_track")
async def test_handle_queue_command_queue_add(mock_dict_to_track, mock_execute):
    mock_track = MagicMock()
    mock_dict_to_track.return_value = mock_track
    await handle_queue_command("queue_add", {"title": "Test"}, None)
    mock_dict_to_track.assert_called_once_with({"title": "Test"})
    mock_execute.assert_called_once_with(CMD_QUEUE_ADD, mock_track)


@pytest.mark.asyncio
@patch("server.handlers.ws_queue.command_bus.execute", new_callable=AsyncMock)
async def test_handle_queue_command_queue_reorder(mock_execute):
    await handle_queue_command("queue_reorder", {"from_index": 1, "to_index": 3}, None)
    mock_execute.assert_called_once_with(CMD_QUEUE_REORDER, {"from_index": 1, "to_index": 3})


@pytest.mark.asyncio
@patch("server.handlers.ws_queue.command_bus.execute", new_callable=AsyncMock)
async def test_handle_queue_command_enqueue_artist_songs(mock_execute):
    mock_db = AsyncMock()
    mock_db.get_artist_songs_strict.return_value = ["track1", "track2"]

    await handle_queue_command("enqueue_artist_songs", {"artist": "ArtistName"}, mock_db)

    mock_db.get_artist_songs_strict.assert_called_once_with(artist="ArtistName", limit=10)
    mock_db.increment_artist_click.assert_called_once_with("ArtistName")

    assert mock_execute.call_count == 2
    mock_execute.assert_any_call(CMD_QUEUE_REPLACE, ["track2"])
    mock_execute.assert_any_call(CMD_PLAY_TRACK, "track1")


@pytest.mark.asyncio
@patch("server.handlers.ws_queue.command_bus.execute", new_callable=AsyncMock)
async def test_handle_queue_command_enqueue_genre_songs(mock_execute):
    mock_db = AsyncMock()
    mock_db.get_genre_songs.return_value = ["track1", "track2", "track3"]

    await handle_queue_command("enqueue_genre_songs", {"genre": "Pop"}, mock_db)

    mock_db.get_genre_songs.assert_called_once_with("Pop", total_limit=12, max_per_artist=3)
    mock_db.increment_genre_click.assert_called_once_with("Pop")

    assert mock_execute.call_count == 3
    mock_execute.assert_any_call(CMD_SET_MODE, PlaybackMode.QUEUE)
    mock_execute.assert_any_call(CMD_QUEUE_REPLACE, ["track1", "track2", "track3"])
    mock_execute.assert_any_call(CMD_QUEUE_SELECT, 0)
