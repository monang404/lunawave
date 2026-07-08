from unittest.mock import MagicMock, patch

import pytest

from server.handlers.http import _stream_rate_limit, serve_stream


@pytest.mark.asyncio
async def test_rate_limit_garbage_collection():
    # Arrange
    mock_request = MagicMock()
    mock_request.match_info.get.return_value = "dQw4w9WgXcQ"
    mock_request.remote = "192.168.1.200"
    mock_request.headers.get.side_effect = lambda k, d="": "http://localhost:8765" if k in ("Referer", "Origin") else d
    mock_request.host = "localhost:8765"

    # Fill _stream_rate_limit with 1005 stale entries
    _stream_rate_limit.clear()
    for i in range(1005):
        _stream_rate_limit[f"10.0.0.{i}"] = [0.0] # Very old timestamp

    assert len(_stream_rate_limit) == 1005

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
    assert len(_stream_rate_limit) == 1
    assert "192.168.1.200" in _stream_rate_limit
