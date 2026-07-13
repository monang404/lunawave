"""
Module: adapters.mpv.connection

Purpose:
    Unit tests for adapters.mpv.connection.

Responsibilities:
    - Test functionality and edge cases.

Depends on:
    - adapters.mpv.connection

Subscribes to:
    None

Publishes:
    None
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
import os
from adapters.mpv.connection import MpvConnection
from core.exceptions import MpvConnectionError

@pytest.fixture
def mock_subprocess():
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        process_mock = AsyncMock()
        process_mock.terminate = MagicMock()
        process_mock.kill = MagicMock()
        process_mock.wait = AsyncMock()
        mock_exec.return_value = process_mock
        yield mock_exec

@pytest.fixture
def mock_open_connection():
    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_conn:
        reader = AsyncMock()
        writer = AsyncMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        mock_conn.return_value = (reader, writer)
        yield mock_conn

@pytest.fixture
def mock_open_unix_connection():
    with patch("asyncio.open_unix_connection", new_callable=AsyncMock, create=True) as mock_unix:
        reader = AsyncMock()
        writer = AsyncMock()
        writer.close = MagicMock()
        writer.wait_closed = AsyncMock()
        mock_unix.return_value = (reader, writer)
        yield mock_unix

@pytest.mark.asyncio
@patch("os.name", "nt")
async def test_mpv_connection_connect_windows(mock_subprocess, mock_open_connection):
    conn = MpvConnection(tcp_port="12345")

    success = await conn.connect()

    assert success is True
    assert conn.is_connected is True
    assert conn.shutting_down is False
    mock_subprocess.assert_called_once()
    mock_open_connection.assert_called_once_with('127.0.0.1', 12345)

@pytest.mark.asyncio
@patch("os.name", "posix")
@patch("os.path.exists", return_value=True)
async def test_mpv_connection_connect_unix(mock_exists, mock_subprocess, mock_open_unix_connection):
    conn = MpvConnection(socket_path="/tmp/mpv.sock")

    success = await conn.connect()

    assert success is True
    assert conn.is_connected is True
    mock_subprocess.assert_called_once()
    mock_open_unix_connection.assert_called_once_with("/tmp/mpv.sock")

@pytest.mark.asyncio
async def test_mpv_connection_already_connected(mock_subprocess):
    conn = MpvConnection()
    conn.is_connected = True

    success = await conn.connect()

    assert success is True
    mock_subprocess.assert_not_called()

@pytest.mark.asyncio
@patch("os.name", "nt")
async def test_mpv_connection_fails_after_10_attempts(mock_subprocess, mock_open_connection):
    # Make open_connection always fail
    mock_open_connection.side_effect = ConnectionError("Mock error")

    conn = MpvConnection(tcp_port="12345")

    with pytest.raises(MpvConnectionError):
        await conn.connect()

    assert mock_open_connection.call_count == 10
    assert conn.is_connected is False

@pytest.mark.asyncio
@patch("os.name", "nt")
async def test_mpv_connection_disconnect(mock_subprocess, mock_open_connection):
    conn = MpvConnection()
    await conn.connect()

    assert conn.is_connected is True
    assert conn._writer is not None

    writer_mock = conn._writer
    process_mock = conn._mpv_process

    await conn.disconnect()

    assert conn.is_connected is False
    assert conn.shutting_down is True
    writer_mock.close.assert_called_once()
    writer_mock.wait_closed.assert_awaited_once()
    process_mock.terminate.assert_called_once()
