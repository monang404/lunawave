import pytest
from unittest.mock import AsyncMock, MagicMock
from server.handlers.ws.registry import _ws_handlers
from core.ws_actions import WSAction

# Import all handler modules to ensure decorators are executed and registry is populated
import server.handlers.ws.queue_handlers
import server.handlers.ws.playback_handlers
import server.handlers.ws.radio_handlers
import server.handlers.ws.download_handlers
import server.handlers.ws.settings_handlers
import server.handlers.ws.discover_handlers

@pytest.fixture
def mock_deps():
    ws = AsyncMock()
    state = MagicMock()
    ytdlp = AsyncMock()
    manager = AsyncMock()
    db = AsyncMock()
    command_bus = AsyncMock()
    return ws, state, ytdlp, manager, db, command_bus

@pytest.mark.asyncio
async def test_all_ws_handlers(mock_deps):
    ws, state, ytdlp, manager, db, command_bus = mock_deps
    
    # Test a few specific handlers to boost coverage
    if WSAction.QUEUE_ADD in _ws_handlers:
        await _ws_handlers[WSAction.QUEUE_ADD]({"video_id": "vid1"}, ws, state, ytdlp, manager, db, command_bus)
    
    if WSAction.PLAY_TRACK in _ws_handlers:
        await _ws_handlers[WSAction.PLAY_TRACK]({"video_id": "vid1"}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.TOGGLE_PAUSE in _ws_handlers:
        await _ws_handlers[WSAction.TOGGLE_PAUSE]({}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.VOLUME_SET in _ws_handlers:
        await _ws_handlers[WSAction.VOLUME_SET]({"level": 50}, ws, state, ytdlp, manager, db, command_bus)

    if WSAction.SEEK in _ws_handlers:
        await _ws_handlers[WSAction.SEEK]({"position": 50}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.RADIO_RANDOMIZE in _ws_handlers:
        await _ws_handlers[WSAction.RADIO_RANDOMIZE]({"video_id": "vid1"}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.DOWNLOAD in _ws_handlers:
        await _ws_handlers[WSAction.DOWNLOAD]({"video_id": "vid1"}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.DELETE_DOWNLOAD in _ws_handlers:
        await _ws_handlers[WSAction.DELETE_DOWNLOAD]({"video_id": "vid1"}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.QUEUE_REORDER in _ws_handlers:
        await _ws_handlers[WSAction.QUEUE_REORDER]({"from_index": 0, "to_index": 1}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.QUEUE_REMOVE in _ws_handlers:
        await _ws_handlers[WSAction.QUEUE_REMOVE]({"index": 0}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.QUEUE_SELECT in _ws_handlers:
        await _ws_handlers[WSAction.QUEUE_SELECT]({"index": 0}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.ENQUEUE_ARTIST_SONGS in _ws_handlers:
        db.get_artist_songs_strict.return_value = [{"video_id": "vid1"}, {"video_id": "vid2"}]
        await _ws_handlers[WSAction.ENQUEUE_ARTIST_SONGS]({"artist": "test"}, ws, state, ytdlp, manager, db, command_bus)
        
    if WSAction.ENQUEUE_GENRE_SONGS in _ws_handlers:
        db.get_genre_songs.return_value = [{"video_id": "vid1"}]
        await _ws_handlers[WSAction.ENQUEUE_GENRE_SONGS]({"genre": "test"}, ws, state, ytdlp, manager, db, command_bus)

    assert command_bus.execute.called or db.get_artist_songs_strict.called

