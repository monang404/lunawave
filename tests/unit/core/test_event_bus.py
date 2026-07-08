import gc

from core.event_bus import DomainEvent, EventBus


class DummyEvent(DomainEvent):
    pass

import pytest


@pytest.mark.asyncio
async def test_event_bus_weakref_closure():
    bus = EventBus()
    called = []

    def outer():
        def closure_handler(event: DummyEvent):
            called.append(True)
        bus.subscribe(DummyEvent, closure_handler)

    outer()

    # After outer returns, the closure is lost from local scope.
    # We force GC to clear weakrefs.
    gc.collect()

    # We trigger the event. The handler should have been garbage collected.
    await bus.publish(DummyEvent())

    # Verify that the handler was not called.
    assert len(called) == 0

@pytest.mark.asyncio
async def test_event_bus_strong_ref_method():
    bus = EventBus()
    called = []

    class MyHandler:
        def handle(self, event: DummyEvent):
            called.append(True)

    handler = MyHandler()
    bus.subscribe(DummyEvent, handler.handle)

    # We trigger the event. The handler should be called.
    await bus.publish(DummyEvent())

    assert len(called) == 1
