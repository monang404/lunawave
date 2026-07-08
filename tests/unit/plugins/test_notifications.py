"""
Tests for S02-055: Notifications Plugin
"""
import asyncio
from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_notification_loop_cleanup():
    """
    Memverifikasi bahwa event _stop menghentikan loop notifikasi
    dan tidak hang (S02-055).
    """
    from core.event_bus import EventBus
    from plugins.notifications import TermuxNowPlaying

    # Setup service with mocked os.read
    bus = EventBus()
    service = TermuxNowPlaying(bus=bus, command_bus=MagicMock(), state=MagicMock())
    service._available = True
    service._pipe_r = 1  # Fake file descriptor

    # This will simulate os.read throwing an error after 1 successful read
    # We want to make sure the thread exits gracefully when _stop is set
    with patch("shutil.which", return_value=True):
        with patch("os.mkfifo", create=True):
            with patch("builtins.open", side_effect=OSError("Test Error")):
                with patch("time.sleep", side_effect=lambda x: asyncio.run(asyncio.sleep(0.01))):
                    # Start the read loop
                    await service.start()

                    # Allow event loop to run the thread
                    await asyncio.sleep(0.1)

                    # Stop the service (sets the _stop event)
                    await service.cleanup()

                    # Wait a little bit for the thread to exit
                    await asyncio.sleep(0.1)

                    # Verify the thread is no longer alive
                    assert not service._reader_thread.is_alive(), "Notification thread did not exit after cleanup() was called"


@pytest.mark.asyncio
async def test_notification_io_error_handling():
    """
    Memverifikasi bahwa exception IO (seperti OSError) tidak
    membuat thread crash, tapi menanganinya dengan benar.
    """
    from core.event_bus import EventBus
    from plugins.notifications import TermuxNowPlaying

    bus = EventBus()
    service = TermuxNowPlaying(bus=bus, command_bus=MagicMock(), state=MagicMock())
    service._available = True
    service._pipe_r = 1


    # Simulate an immediate OSError from builtins.open
    with patch("shutil.which", return_value=True):
        with patch("os.mkfifo", create=True):
            with patch("builtins.open", side_effect=OSError("Test IO Error")):
                with patch("time.sleep", side_effect=lambda x: asyncio.run(asyncio.sleep(0.01))):
                    await service.start()

                    # Give it time to hit the exception
                    await asyncio.sleep(0.1)

                    # Stop it
                    await service.cleanup()
                    await asyncio.sleep(0.1)

                    # The thread should have exited gracefully when cleanup() is called,
                    # despite the earlier OSError inside the loop.
                    assert not service._reader_thread.is_alive()
