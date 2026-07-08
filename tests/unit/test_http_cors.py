from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.handlers.http import serve_stream
from core.rate_limit import global_rate_limiter


@pytest.mark.asyncio
async def test_stream_cors_no_wildcard():
    # Arrange
    mock_request = MagicMock()
    mock_request.match_info.get.return_value = "dQw4w9WgXcQ"
    mock_request.remote = "192.168.1.100"

    headers = {"Origin": "http://localhost:8765"}
    mock_request.headers.get.side_effect = lambda k, d="": headers.get(k, d)
    mock_request.host = "localhost:8765"
    mock_request.scheme = "http"
    mock_request.query = {"token": "dummy_token"}
    mock_request.app = {"db": AsyncMock()}
    mock_request.app["db"].verify_session = AsyncMock(return_value=True)

    global_rate_limiter.clients.clear()

    with patch("server.handlers.http.CACHE_DIR") as mock_cache_dir:
        mock_cache_file = MagicMock()
        mock_cache_file.exists.return_value = True

        stat_mock = MagicMock()
        stat_mock.st_mtime = 1000
        stat_mock.st_size = 500
        mock_cache_file.stat.return_value = stat_mock

        # Bypass Path resolution
        mock_cache_file.resolve.return_value.is_relative_to.return_value = True
        mock_cache_dir.__truediv__.return_value = mock_cache_file

        with patch("server.handlers.http.web.FileResponse") as mock_file_response:
            mock_file_response.return_value = MagicMock()

            # Act
            await serve_stream(mock_request)

            # Assert
            mock_file_response.assert_called_once()
            args, kwargs = mock_file_response.call_args
            response_headers = kwargs.get("headers", {})
            assert "Access-Control-Allow-Origin" in response_headers
            assert response_headers["Access-Control-Allow-Origin"] != "*"
            assert response_headers["Access-Control-Allow-Origin"] == "http://localhost:8765"
