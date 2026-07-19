"""
Module: bootstrap.services

Purpose:
    Unit tests for bootstrap.services.

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

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.state import PlayerStatus


@pytest.fixture(autouse=True)
def _reset_context():
    """Reset the module-level context singleton in place before/after each
    test (see tests/unit/test_main.py for why rebinding wouldn't work)."""
    import bootstrap.services as services

    services.context.__init__()
    yield
    services.context.__init__()


@pytest.mark.asyncio
@patch("bootstrap.services.Repositories")
@patch("bootstrap.services.MpvController")
@patch("bootstrap.services.YtDlpClient")
@patch("engine.playback.controller.PlaybackController")
@patch("bootstrap.services.DownloadManager")
@patch("bootstrap.services.CommandRouter")
@patch("bootstrap.services.TermuxNowPlaying")
@patch("bootstrap.services.SponsorBlockHandler")
@patch("bootstrap.services.LyricsFetcher")
@patch("persistence.stream_cache.CacheResolver")
@patch("engine.queue_manager.QueueMode")
@patch("engine.radio.RadioMode")
@patch("engine.volume_service.VolumeService")
@patch("bootstrap.services.aiohttp.ClientSession")
@patch("engine.loudness.service.LoudnessService")
async def test_init_core_services_wires_and_returns_context(
    mock_loudness,
    mock_session,
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
    mock_repos_cls,
):
    from bootstrap.services import context, init_core_services

    repos_instance = mock_repos_cls.return_value
    repos_instance.init = AsyncMock()
    repos_instance.tracks = MagicMock()
    repos_instance.artists = MagicMock()
    repos_instance.discover = MagicMock()
    repos_instance.library = MagicMock()

    nowplaying_inst = mock_nowplaying_cls.return_value
    nowplaying_inst.start = AsyncMock()

    result = await init_core_services()

    # Returns the shared context, fully populated.
    assert result is context
    repos_instance.init.assert_awaited_once()
    nowplaying_inst.start.assert_awaited_once()

    assert context.state is not None
    assert context.mpv_ready_event is not None
    assert context.repos is repos_instance
    assert context.mpv is mock_mpv.return_value
    assert context.ytdlp is mock_ytdlp.return_value
    assert context.http_session is mock_session.return_value
    assert context.resolver is mock_resolver.return_value
    assert context.sponsorblock is mock_sponsor.return_value
    assert context.lyrics_fetcher is mock_lyrics.return_value
    assert context.loudness_service is mock_loudness.return_value
    assert context.queue_mode is mock_queue.return_value
    assert context.radio_mode is mock_radio.return_value
    assert context.volume_service is mock_volume.return_value
    assert context.playback_controller is mock_controller.return_value
    assert context.download_manager is mock_dl_manager.return_value
    assert context.command_router is mock_router.return_value
    assert context.nowplaying is nowplaying_inst
    assert context.tasks == []


@pytest.mark.asyncio
async def test_init_mpv_success_sets_ready_event():
    from bootstrap.services import _init_mpv, context

    context.state = MagicMock()
    context.mpv = MagicMock()
    context.mpv.connect = AsyncMock()
    context.mpv_ready_event = MagicMock()
    context.mpv_ready_event.set = MagicMock()

    await _init_mpv()

    context.mpv.connect.assert_awaited_once()
    context.mpv_ready_event.set.assert_called_once()


@pytest.mark.asyncio
async def test_init_mpv_failure_sets_error_state_and_ready_event():
    from bootstrap.services import _init_mpv, context

    context.state = MagicMock()
    context.mpv = MagicMock()
    context.mpv.connect = AsyncMock(side_effect=RuntimeError("mpv not found"))
    context.mpv_ready_event = MagicMock()
    context.mpv_ready_event.set = MagicMock()

    await _init_mpv()

    assert context.state.status == PlayerStatus.ERROR
    assert "MPV" in context.state.error_msg
    # Event is still set on failure so waiters (resume_last_track) never hang.
    context.mpv_ready_event.set.assert_called_once()
