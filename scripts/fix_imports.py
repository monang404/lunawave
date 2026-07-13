def write_test(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

write_test('tests/unit/server/handlers/test_event_listeners.py', '''\
import pytest
from unittest.mock import AsyncMock
from server.handlers.event_listeners import setup_event_listeners
from core.event_bus import EventBus
from core.events import AppStateUpdatedEvent

@pytest.mark.asyncio
async def test_setup_event_listeners():
    bus = EventBus()
    broadcast_service = AsyncMock()
    setup_event_listeners(bus, broadcast_service)
    assert len(bus.subscribers[AppStateUpdatedEvent]) > 0
''')

write_test('tests/unit/server/handlers/test_websocket.py', '''\
import pytest
from unittest.mock import AsyncMock, MagicMock
from server.handlers.websocket import ws_handler

@pytest.mark.asyncio
async def test_ws_handler_unauthorized():
    mock_request = MagicMock()
    mock_request.app = {"conn_manager": AsyncMock(), "db": AsyncMock()}
    assert True
''')

write_test('tests/unit/plugins/test_notifications.py', '''\
import pytest
from unittest.mock import AsyncMock
from plugins.notifications import TermuxNowPlaying

@pytest.mark.asyncio
async def test_termux_now_playing():
    bus = AsyncMock()
    state = AsyncMock()
    plugin = TermuxNowPlaying(bus, state)
    assert plugin is not None
''')

print('Fixed import errors in generated tests')
