"""tests/unit/core/test_event_bus.py — mirrors core/event_bus.py
Purpose:
    Auto-generated purpose.

Subscribes to:
    - LogMessageEvent
    - QueueUpdatedEvent

Publishes:
    - LogMessageEvent
    - QueueUpdatedEvent
"""

import gc

from core.event_bus import EventBus
from core.event_bus import bus as singleton_bus
from core.events import LogMessageEvent, QueueUpdatedEvent


class _Listener:
    """Plain object whose bound method is used as a subscriber, so the
    EventBus stores it via weakref.WeakMethod (see L-3 note in source)."""

    def __init__(self):
        self.received = []

    def on_event(self, event):
        self.received.append(event)

    async def on_event_async(self, event):
        self.received.append(event)


async def test_publish_delivers_to_sync_function_subscriber():
    eb = EventBus()
    received = []

    def handler(event):
        received.append(event)

    eb.subscribe(LogMessageEvent, handler)
    await eb.publish(LogMessageEvent(message="hi"))
    assert len(received) == 1
    assert received[0].message == "hi"


async def test_publish_delivers_to_async_function_subscriber():
    eb = EventBus()
    received = []

    async def handler(event):
        received.append(event)

    eb.subscribe(LogMessageEvent, handler)
    await eb.publish(LogMessageEvent(message="async-hi"))
    assert len(received) == 1


async def test_publish_delivers_to_bound_method_subscriber_via_weakref():
    eb = EventBus()
    listener = _Listener()
    eb.subscribe(QueueUpdatedEvent, listener.on_event)
    await eb.publish(QueueUpdatedEvent())
    assert len(listener.received) == 1


async def test_publish_only_notifies_subscribers_of_matching_event_type():
    eb = EventBus()
    received = []
    eb.subscribe(LogMessageEvent, lambda e: received.append(e))
    await eb.publish(QueueUpdatedEvent())
    assert received == []


async def test_publish_with_no_subscribers_does_not_raise():
    eb = EventBus()
    await eb.publish(QueueUpdatedEvent())


async def test_one_handler_exception_does_not_block_other_handlers():
    eb = EventBus()
    received = []

    def broken(event):
        raise ValueError("boom")

    def working(event):
        received.append(event)

    eb.subscribe(LogMessageEvent, broken)
    eb.subscribe(LogMessageEvent, working)
    await eb.publish(LogMessageEvent(message="x"))
    assert len(received) == 1


async def test_async_handler_exception_does_not_block_other_handlers():
    eb = EventBus()
    received = []

    async def broken(event):
        raise ValueError("boom")

    async def working(event):
        received.append(event)

    eb.subscribe(LogMessageEvent, broken)
    eb.subscribe(LogMessageEvent, working)
    await eb.publish(LogMessageEvent(message="x"))
    assert len(received) == 1


def test_unsubscribe_removes_handler():
    eb = EventBus()
    listener = _Listener()
    eb.subscribe(QueueUpdatedEvent, listener.on_event)
    eb.unsubscribe(QueueUpdatedEvent, listener.on_event)
    assert QueueUpdatedEvent not in eb._subscribers


def test_unsubscribe_unknown_handler_is_a_noop():
    eb = EventBus()
    eb.unsubscribe(QueueUpdatedEvent, lambda e: None)  # must not raise


async def test_dead_weakref_is_pruned_and_not_delivered_to():
    eb = EventBus()
    listener = _Listener()
    eb.subscribe(QueueUpdatedEvent, listener.on_event)
    del listener
    gc.collect()
    # Should not raise even though the weakref is dead.
    await eb.publish(QueueUpdatedEvent())
    eb.purge_dead_refs()
    assert QueueUpdatedEvent not in eb._subscribers


def test_purge_dead_refs_removes_empty_event_type_keys():
    eb = EventBus()
    listener = _Listener()
    eb.subscribe(QueueUpdatedEvent, listener.on_event)
    del listener
    gc.collect()
    eb.purge_dead_refs()
    assert QueueUpdatedEvent not in eb._subscribers


async def test_multiple_subscribers_all_receive_the_event():
    eb = EventBus()
    counts = {"a": 0, "b": 0}
    eb.subscribe(LogMessageEvent, lambda e: counts.__setitem__("a", counts["a"] + 1))
    eb.subscribe(LogMessageEvent, lambda e: counts.__setitem__("b", counts["b"] + 1))
    await eb.publish(LogMessageEvent())
    assert counts == {"a": 1, "b": 1}


def test_module_level_singleton_bus_is_an_event_bus_instance():
    assert isinstance(singleton_bus, EventBus)
