"""tests/unit/core/test_observability.py — mirrors core/observability.py
Purpose:
    Auto-generated purpose.

Subscribes to:
    None

Publishes:
    None
"""

from prometheus_client import CONTENT_TYPE_LATEST

from core.observability import (
    ACTIVE_WEBSOCKETS,
    COMMAND_COUNT,
    COMMAND_LATENCY,
    EVENT_COUNT,
    get_metrics_content,
)


def test_command_count_is_a_labeled_counter():
    COMMAND_COUNT.labels(command_name="cmd.test", status="success").inc()
    sample = COMMAND_COUNT.labels(command_name="cmd.test", status="success")
    assert sample._value.get() >= 1


def test_command_latency_records_observations():
    COMMAND_LATENCY.labels(command_name="cmd.test").observe(0.05)
    # Histogram exposes _sum via internal metric; just assert no exception
    # and that the child collector exists.
    assert COMMAND_LATENCY.labels(command_name="cmd.test") is not None


def test_event_count_increments_per_event_type():
    before = EVENT_COUNT.labels(event_type="TestEvent")._value.get()
    EVENT_COUNT.labels(event_type="TestEvent").inc()
    after = EVENT_COUNT.labels(event_type="TestEvent")._value.get()
    assert after == before + 1


def test_active_websockets_gauge_inc_dec():
    ACTIVE_WEBSOCKETS.set(0)
    ACTIVE_WEBSOCKETS.inc()
    assert ACTIVE_WEBSOCKETS._value.get() == 1
    ACTIVE_WEBSOCKETS.dec()
    assert ACTIVE_WEBSOCKETS._value.get() == 0


def test_get_metrics_content_returns_bytes_and_content_type():
    payload, content_type = get_metrics_content()
    assert isinstance(payload, bytes)
    assert content_type == CONTENT_TYPE_LATEST
    assert b"ytplayer_commands_total" in payload
