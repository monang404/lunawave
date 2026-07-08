import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.bootstrap import build_app_context, shutdown_app_context, AppContext

@pytest.fixture
def mock_deps():
    with patch("core.bootstrap.Database") as mock_db, \
         patch("core.bootstrap.YtDlpClient") as mock_ytdlp, \
         patch("core.bootstrap.MpvController") as mock_mpv, \
         patch("core.bootstrap.create_app") as mock_create_app:
        
        db_instance = AsyncMock()
        mock_db.return_value = db_instance
        
        ytdlp_instance = AsyncMock()
        mock_ytdlp.return_value = ytdlp_instance
        
        mpv_instance = AsyncMock()
        mock_mpv.return_value = mpv_instance
        
        mock_create_app.return_value = MagicMock()
        
        yield db_instance, ytdlp_instance, mpv_instance, mock_create_app

@pytest.mark.asyncio
async def test_build_app_context(mock_deps):
    db, ytdlp, mpv, create_app_mock = mock_deps
    
    ctx = await build_app_context()
    
    assert isinstance(ctx, AppContext)
    db.init.assert_called_once()
    mpv.connect.assert_called_once()
    create_app_mock.assert_called_once()

@pytest.mark.asyncio
async def test_shutdown_app_context(mock_deps):
    db, ytdlp, mpv, create_app_mock = mock_deps
    
    # Just need an object that looks like AppContext
    ctx = MagicMock(spec=AppContext)
    ctx.nowplaying = AsyncMock()
    ctx.mpv = AsyncMock()
    ctx.lyrics_fetcher = MagicMock()
    ctx.sponsorblock = MagicMock()
    ctx.ytdlp = MagicMock()
    ctx.http_session = AsyncMock()
    ctx.db = AsyncMock()
    
    tasks = []
    await shutdown_app_context(ctx, tasks)
    
    ctx.nowplaying.cleanup.assert_called_once()
    ctx.mpv.close.assert_called_once()
    ctx.http_session.close.assert_called_once()
    ctx.db.close.assert_called_once()

