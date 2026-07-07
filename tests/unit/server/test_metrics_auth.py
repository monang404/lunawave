import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiohttp import web
from server.handlers.http import serve_metrics

@pytest.mark.asyncio
async def test_metrics_auth_bearer(monkeypatch):
    monkeypatch.setenv("LUNAWAVE_METRICS_TOKEN", "supersecrettoken")
    
    # Test Unauthorized
    request = MagicMock()
    request.remote = "192.168.1.10"
    request.headers.get.return_value = None
    
    resp = await serve_metrics(request)
    assert resp.status == 403
    assert "Authorization: Bearer token" in resp.text
    
    # Test Authorized Bearer
    request.headers.get.return_value = "Bearer supersecrettoken"
    
    with patch("server.handlers.http.get_metrics_content", return_value=("test_metrics", "text/plain")):
        resp2 = await serve_metrics(request)
        assert resp2.status == 200
        assert resp2.text == "test_metrics"
