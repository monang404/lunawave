from unittest.mock import MagicMock, patch

import pytest

from server.handlers.http import serve_stream
from core.rate_limit import global_rate_limiter


@pytest.mark.asyncio
async def test_rate_limit_garbage_collection():
    # Arrange
    mock_request = MagicMock()
    mock_request.match_info.get.return_value = "dQw4w9WgXcQ"
    mock_request.remote = "192.168.1.200"
    mock_request.headers.get.side_effect = lambda k, d="": "http://localhost:8765" if k in ("Referer", "Origin") else d
    mock_request.host = "localhost:8765"

    # Fill global_rate_limiter.clients with 1005 stale entries
    global_rate_limiter.clients.clear()
    global_rate_limiter.last_gc = 0
    for i in range(1005):
        global_rate_limiter.clients[f"10.0.0.{i}"] = [0.0] # Very old timestamp

    assert len(global_rate_limiter.clients) == 1005

    # Act
    with patch("server.handlers.http.time.monotonic", return_value=100.0):
        # We don't care about the final response, just that it doesn't crash on rate limit gc
        # It will likely fail at cache_file.resolve() or db, but we can catch it or mock it
        try:
            await serve_stream(mock_request)
        except Exception:
            pass # Ignore downstream errors, GC already happened

    # Assert
    # The garbage collection should have cleared the 1005 stale entries
    # and added the new client_ip
    assert len(global_rate_limiter.clients) == 1
    assert "192.168.1.200" in global_rate_limiter.clients
