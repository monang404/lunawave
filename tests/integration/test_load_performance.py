import asyncio
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.ports import DatabasePort, MediaExtractorPort
from core.state import AppState
from server.app import create_app
from server.handlers.websocket import ConnectionManager


@pytest.fixture
def mock_load_deps():
    db = MagicMock(spec=DatabasePort)
    db.conn = True
    db.verify_session = AsyncMock(return_value=True)
    db.get_track = AsyncMock(return_value=None)

    ytdlp = MagicMock(spec=MediaExtractorPort)
    return db, ytdlp

@pytest.mark.asyncio
@patch('scripts.build_js.build')
@patch('server.handlers.websocket.logger')
async def test_websocket_concurrent_load(mock_logger, mock_build, aiohttp_client, mock_load_deps):
    db, ytdlp = mock_load_deps
    mock_pc = MagicMock()
    mock_pc.state = AppState()

    # We will simulate 100 concurrent WebSocket connections hitting /ws
    app = create_app(mock_pc, ytdlp, db, ConnectionManager())
    app["command_bus"] = AsyncMock()
    app["event_bus"] = AsyncMock()

    client = await aiohttp_client(app)

    async def connect_and_receive(i):
        try:
            ws = await client.ws_connect("/ws")
            # First message should be the initial state (sys_info etc.)
            msg = await ws.receive()
            if msg.type == 1: # aiohttp.WSMsgType.TEXT
                data = json.loads(msg.data)
                # Ensure it has 'type'
                if "type" in data:
                    await ws.close()
                    return True
            else:
                print(f"Received msg type: {msg.type}, data: {msg.data}")
            await ws.close()
            return False
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    start_time = time.time()

    # Launch 100 concurrent connection requests
    tasks = [connect_and_receive(i) for i in range(100)]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    successful_connections = sum(1 for r in results if r)

    # Assertions
    assert successful_connections == 100, f"Expected 100 successful connections, got {successful_connections}"
    assert duration < 5.0, f"Load test took too long: {duration:.2f} seconds"
