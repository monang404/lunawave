import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from config import DOWNLOAD_DIR
from server.handlers.ws_cache import handle_cache_command


@pytest.mark.asyncio
async def test_get_cache_size():
    ws = AsyncMock()
    with patch("os.walk") as mock_walk, patch("os.path.getsize") as mock_getsize:
        mock_walk.return_value = [("/downloads", [], ["f1.mp3", "f2.mp3"])]
        mock_getsize.side_effect = [1000, 2000]
        with patch("pathlib.Path.exists", return_value=True):
            await handle_cache_command("get_cache_size", {}, ws, None, None, None)

    ws.send_str.assert_called_once()
    args = ws.send_str.call_args[0][0]
    data = json.loads(args)
    assert data["type"] == "cache_size"
    assert data["data"]["size_bytes"] == 3000


@pytest.mark.asyncio
async def test_get_cache_size_reads_download_dir_not_cache_dir():
    # Regression: this used to read config.CACHE_DIR (cache/mp3), which is
    # emptied right after each download finishes, so the Settings UI stayed
    # stuck at 0.00 MB even with real files sitting in downloads/.
    ws = AsyncMock()
    with patch("os.walk") as mock_walk, patch("os.path.getsize", return_value=100):
        mock_walk.return_value = [(str(DOWNLOAD_DIR), [], ["song.mp3"])]
        with patch("pathlib.Path.exists", return_value=True):
            await handle_cache_command("get_cache_size", {}, ws, None, None, None)

    walked_paths = [call.args[0] for call in mock_walk.call_args_list]
    assert str(DOWNLOAD_DIR) in walked_paths


@pytest.mark.asyncio
async def test_clear_cache():
    ws = AsyncMock()
    manager = AsyncMock()
    with patch("os.walk") as mock_walk, patch("os.remove") as mock_remove:
        mock_walk.return_value = [("/downloads", [], ["f1.mp3", "f2.mp3"])]
        with patch("pathlib.Path.exists", return_value=True):
            await handle_cache_command("clear_cache", {}, ws, None, manager, None)

    assert mock_remove.call_count == 2
    ws.send_str.assert_called_once()
    manager.broadcast.assert_called_once()
