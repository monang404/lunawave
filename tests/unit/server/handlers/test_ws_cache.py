import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import CACHE_DIR
from server.handlers.ws_cache import handle_cache_command


@pytest.mark.asyncio
async def test_get_cache_size():
    ws = AsyncMock()
    with patch("os.walk") as mock_walk, patch("os.path.getsize") as mock_getsize:
        mock_walk.return_value = [("/cache/mp3", [], ["f1.mp3", "f2.mp3"])]
        mock_getsize.side_effect = [1000, 2000]
        with patch("pathlib.Path.exists", return_value=True):
            await handle_cache_command("get_cache_size", {}, ws, None, None, None)

    ws.send_str.assert_called_once()
    args = ws.send_str.call_args[0][0]
    data = json.loads(args)
    assert data["type"] == "cache_size"
    assert data["data"]["size_bytes"] == 3000


@pytest.mark.asyncio
async def test_clear_cache():
    ws = AsyncMock()
    manager = AsyncMock()
    with patch("os.walk") as mock_walk, patch("os.remove") as mock_remove:
        mock_walk.return_value = [("/cache/mp3", [], ["f1.mp3", "f2.mp3"])]
        with patch("pathlib.Path.exists", return_value=True):
            await handle_cache_command("clear_cache", {}, ws, None, manager, None)

    assert mock_remove.call_count == 2
    ws.send_str.assert_called_once()
    manager.broadcast.assert_called_once()
