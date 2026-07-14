"""
Module: main

Purpose:
    Unit tests for main.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
@patch("main.Database")
@patch("main.MpvController")
@patch("main.YtDlpClient")
@patch("engine.playback.controller.PlaybackController")
@patch("main.DownloadManager")
@patch("main.CommandRouter")
@patch("main.TermuxNowPlaying")
@patch("main.SponsorBlockHandler")
@patch("main.LyricsFetcher")
@patch("cache.resolver.CacheResolver")
@patch("engine.queue_manager.QueueMode")
@patch("engine.radio_engine.RadioMode")
@patch("engine.volume_service.VolumeService")
@patch("server.app.create_app")
@patch("server.app.run_server", new_callable=AsyncMock)
@patch("main.aiohttp.ClientSession")
async def test_main_smoke(
    mock_session,
    mock_run_server,
    mock_create_app,
    mock_volume,
    mock_radio,
    mock_queue,
    mock_resolver,
    mock_lyrics,
    mock_sponsor,
    mock_nowplaying_cls,
    mock_router,
    mock_dl_manager,
    mock_controller,
    mock_ytdlp,
    mock_mpv,
    mock_db,
):
    from main import main

    # Setup mocks
    db_instance = mock_db.return_value
    db_instance.init = AsyncMock()
    db_instance.close = AsyncMock()

    mpv_instance = mock_mpv.return_value
    mpv_instance.connect = AsyncMock()
    mpv_instance.close = AsyncMock()

    nowplaying_inst = mock_nowplaying_cls.return_value
    nowplaying_inst.start = AsyncMock()
    nowplaying_inst.cleanup = AsyncMock()

    mock_session.return_value.close = AsyncMock()

    # When run_server is called, gracefully exit as if a signal was received
    mock_run_server.side_effect = asyncio.CancelledError()

    await main()

    # Assertions
    db_instance.init.assert_awaited_once()
    mpv_instance.connect.assert_awaited_once()
    mock_create_app.assert_called_once()
    mock_run_server.assert_awaited_once()
    nowplaying_inst.start.assert_awaited_once()
    nowplaying_inst.cleanup.assert_awaited_once()

    # Allow event loop to process task cancellations
    await asyncio.sleep(0.05)
