"""
Module: tests.integration.test_download_flow

Purpose:
    IT-04: Test end-to-end download communication.
    Download -> progress event -> complete event -> file exists.

Subscribes to:
    None

Publishes:
    None
"""

import asyncio
from pathlib import Path

import pytest

from core.command_bus import command_bus
from core.commands import CMD_DOWNLOAD
from core.event_bus import bus
from core.events import DownloadCompleteEvent, LogMessageEvent
from core.state import TrackInfo


@pytest.mark.asyncio
async def test_download_flow(integration_app):
    """
    IT-04: Download Flow
    Skenario: Download → yt-dlp → selesai
    """
    events = []

    async def capture_event(evt):
        events.append(evt)

    bus.subscribe(DownloadCompleteEvent, capture_event)
    bus.subscribe(LogMessageEvent, capture_event)

    # We need a track object to download. We can just create one manually.
    # Use a very short video to not hang the test forever.
    # "Me at the zoo" is 19 seconds.
    track = TrackInfo(video_id="jNQXAC9IVRw", title="Me at the zoo", artist="jawed", duration=19)

    # Dispatch download command
    await command_bus.dispatch(CMD_DOWNLOAD, track)

    # Wait for completion event
    # yt-dlp download takes a few seconds
    completed = False
    for _ in range(200):  # max 20 seconds
        await asyncio.sleep(0.1)
        if any(isinstance(e, DownloadCompleteEvent) for e in events):
            completed = True
            break

    assert completed, "Download did not complete within 20 seconds"

    # Get the file path from the event
    completion_event = next(e for e in events if isinstance(e, DownloadCompleteEvent))

    # File should exist on disk
    path = Path(completion_event.file_path)
    assert path.exists(), f"Downloaded file does not exist at {path}"
    assert path.stat().st_size > 0, "Downloaded file is empty"
