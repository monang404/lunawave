from dataclasses import dataclass

import pytest

from core.command_bus import CommandBus
from core.commands import DomainCommand


@dataclass
class TestCommand(DomainCommand):
    payload: str

@dataclass
class UnregisteredCommand(DomainCommand):
    pass

@pytest.fixture
def command_bus():
    return CommandBus()

@pytest.mark.asyncio
async def test_command_bus_register_and_execute(command_bus):
    called = False

    async def my_handler(cmd: TestCommand):
        nonlocal called
        called = True
        assert cmd.payload == "test_payload"

    command_bus.register(TestCommand, my_handler)
    await command_bus.execute(TestCommand(payload="test_payload"))

    assert called is True

@pytest.mark.asyncio
async def test_command_bus_single_writer(command_bus):
    async def handler1(cmd): pass
    async def handler2(cmd): pass

    command_bus.register(TestCommand, handler1)

    with pytest.raises(RuntimeError) as exc_info:
        command_bus.register(TestCommand, handler2)

    assert "already registered" in str(exc_info.value)

@pytest.mark.asyncio
async def test_command_bus_execute_unregistered(command_bus):
    with pytest.raises(RuntimeError) as exc_info:
        await command_bus.execute(UnregisteredCommand())

    assert "No handler registered for command" in str(exc_info.value)
