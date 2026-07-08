import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from aiohttp import web
from server.app import run_server

@pytest.mark.asyncio
async def test_run_server_sets_default_executor():
    app = web.Application()
    
    with patch("server.app.web.AppRunner") as mock_runner_cls, \
         patch("server.app.web.TCPSite") as mock_site_cls, \
         patch("asyncio.sleep") as mock_sleep:
        
        mock_runner = MagicMock()
        mock_runner.setup = AsyncMock()
        mock_runner.cleanup = AsyncMock()
        mock_runner_cls.return_value = mock_runner
        
        mock_site = MagicMock()
        mock_site.start = AsyncMock()
        mock_site_cls.return_value = mock_site
        
        mock_sleep.side_effect = asyncio.CancelledError()
        
        loop = asyncio.get_running_loop()
        original_executor = None # We can't easily get it in some python versions, but we can verify it changed if we want, or mock set_default_executor.
        
        with patch.object(loop, "set_default_executor") as mock_set_default_executor:
            await run_server(app, "127.0.0.1", 8080)
            
            # Verify set_default_executor was called with a ThreadPoolExecutor
            mock_set_default_executor.assert_called_once()
            args, kwargs = mock_set_default_executor.call_args
            executor = args[0]
            assert executor.__class__.__name__ == "ThreadPoolExecutor"
            assert executor._thread_name_prefix == "aiohttp_worker"
