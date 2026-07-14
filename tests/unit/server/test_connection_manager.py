"""
Module: tests.unit.server.test_connection_manager

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import pytest

from server.connection_manager import ConnectionManager


class MockWebSocket:
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    async def send_str(self, data):
        if self.fail:
            raise Exception("Connection failed")
        self.sent.append(data)


@pytest.mark.asyncio
async def test_connect_disconnect():
    cm = ConnectionManager()
    ws = MockWebSocket()

    await cm.connect(ws)
    assert ws in cm.active_connections
    assert len(cm.active_connections) == 1

    cm.disconnect(ws)
    assert ws not in cm.active_connections
    assert len(cm.active_connections) == 0


@pytest.mark.asyncio
async def test_broadcast():
    cm = ConnectionManager()
    ws1 = MockWebSocket()
    ws2 = MockWebSocket(fail=True)  # This one will fail and should be removed

    await cm.connect(ws1)
    await cm.connect(ws2)

    await cm.broadcast({"cmd": "test"})

    assert len(ws1.sent) == 1
    assert '{"cmd": "test"}' in ws1.sent[0]

    # ws2 should be disconnected because it raised an exception
    assert ws2 not in cm.active_connections
    assert len(cm.active_connections) == 1
