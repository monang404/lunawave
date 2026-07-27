"""tests/unit/core/test_command_bus.py — mirrors core/command_bus.py

Includes the small `commands` constants block that lives in the same file
(no separate core/commands.py in the actual repo layout).

Purpose:
    Auto-generated purpose.

Subscribes to:
    None

Publishes:
    None
"""

import pytest

from core.command_bus import CMD_PLAY_TRACK, CMD_QUIT, CommandBus


def test_register_and_execute_sync_handler():
    bus = CommandBus()
    bus.register("cmd.echo", lambda data: data)
    result = None

    async def run():
        nonlocal result
        result = await bus.execute("cmd.echo", "hello")

    import asyncio

    asyncio.run(run())
    assert result == "hello"


async def test_execute_awaits_async_handlers():
    bus = CommandBus()

    async def handler(data):
        return data * 2

    bus.register("cmd.double", handler)
    result = await bus.execute("cmd.double", 21)
    assert result == 42


def test_register_raises_on_duplicate_command():
    bus = CommandBus()
    bus.register("cmd.dup", lambda data: None)
    with pytest.raises(RuntimeError):
        bus.register("cmd.dup", lambda data: None)


def test_unregister_removes_handler():
    bus = CommandBus()
    bus.register("cmd.temp", lambda data: None)
    bus.unregister("cmd.temp")
    # Re-registering after unregister should succeed, not raise duplicate.
    bus.register("cmd.temp", lambda data: None)


def test_unregister_unknown_command_is_a_noop():
    bus = CommandBus()
    bus.unregister("cmd.does.not.exist")  # must not raise


async def test_execute_unknown_command_raises_runtime_error():
    bus = CommandBus()
    with pytest.raises(RuntimeError):
        await bus.execute("cmd.unknown")


async def test_execute_propagates_handler_exceptions():
    bus = CommandBus()

    async def failing(data):
        raise ValueError("handler broke")

    bus.register("cmd.fail", failing)
    with pytest.raises(ValueError):
        await bus.execute("cmd.fail")


async def test_execute_passes_none_data_by_default():
    bus = CommandBus()
    received = []

    async def handler(data):
        received.append(data)

    bus.register("cmd.nodata", handler)
    await bus.execute("cmd.nodata")
    assert received == [None]


def test_command_constants_are_unique_strings():
    from core import command_bus as module

    constants = [
        value
        for name, value in vars(module).items()
        if name.startswith("CMD_") and isinstance(value, str)
    ]
    assert len(constants) >= 15
    assert len(constants) == len(set(constants)), "duplicate command name constants"
    assert CMD_PLAY_TRACK == "cmd.play.track"
    assert CMD_QUIT == "cmd.quit"
