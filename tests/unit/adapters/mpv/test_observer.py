"""
Module: adapters.mpv.observer

Purpose:
    Unit tests for adapters.mpv.observer.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    - adapters.mpv.observer

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from adapters.mpv.observer import MpvObserver


@pytest.fixture
def mock_connection():
    conn = MagicMock()
    conn.is_connected = True
    conn.reader = AsyncMock()
    return conn


@pytest.fixture
def mock_ipc():
    ipc = MagicMock()
    ipc.send_command = AsyncMock()
    return ipc


@pytest.fixture
def mock_event_bus():
    bus = MagicMock()
    bus.publish = AsyncMock()
    return bus


def test_observer_initialization(mock_connection, mock_ipc, mock_event_bus):
    observer = MpvObserver(mock_connection, mock_ipc, mock_event_bus, room_id="test_room")
    assert observer._conn == mock_connection
    assert observer._ipc == mock_ipc
    assert observer._bus == mock_event_bus
    assert observer._room_id == "test_room"


@pytest.mark.asyncio
async def test_observer_start_and_stop(mock_connection, mock_ipc, mock_event_bus):
    observer = MpvObserver(mock_connection, mock_ipc, mock_event_bus)

    # Mocking read_readline so the loop doesn't block forever
    # It returns one empty byte to break the loop internally
    mock_connection.reader.readline.return_value = b""

    await observer.start()
    assert observer._task is not None
    assert not observer._task.done()

    # Let the event loop run so the task can start and await the coroutine
    await asyncio.sleep(0)

    await observer.stop()
    try:
        await observer._task
    except asyncio.CancelledError:
        pass

    assert observer._task.cancelled() or observer._task.done()


@pytest.mark.asyncio
async def test_observer_handles_property_change(mock_connection, mock_ipc, mock_event_bus):
    observer = MpvObserver(mock_connection, mock_ipc, mock_event_bus)

    # Simulate an MPV property-change event for 'time-pos'
    event_data = {"event": "property-change", "name": "time-pos", "data": 12.5}
    await observer._handle_event(event_data)

    # It should have published a TrackPositionEvent
    assert mock_event_bus.publish.call_count == 1
    call_args = mock_event_bus.publish.call_args[0][0]
    assert call_args.__class__.__name__ == "TrackProgressEvent"
    assert call_args.position == 12.5


@pytest.mark.asyncio
async def test_observer_handles_pause_change(mock_connection, mock_ipc, mock_event_bus):
    observer = MpvObserver(mock_connection, mock_ipc, mock_event_bus)

    event_data = {"event": "property-change", "name": "pause", "data": True}
    await observer._handle_event(event_data)

    assert mock_event_bus.publish.call_count == 1
    call_args = mock_event_bus.publish.call_args[0][0]
    assert call_args.__class__.__name__ == "TrackPauseChangedEvent"
    assert call_args.is_paused is True
