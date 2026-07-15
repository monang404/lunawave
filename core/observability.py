"""
Module: core.observability

Purpose:
    Expose Prometheus metric singletons and an OpenTelemetry tracer for
    application-wide instrumentation.

Responsibilities:
    - Define Counter/Histogram/Gauge for commands, events, and WebSockets.
    - Initialize a TracerProvider and return the application tracer.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Thread-safe (prometheus_client handles concurrent metric updates).
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# --- Prometheus Metrics ---

# 1. Total Command Executions (Counter)
COMMAND_COUNT = Counter(
    "ytplayer_commands_total", "Total number of commands executed", ["command_name", "status"]
)

# 2. Command Latency (Histogram)
COMMAND_LATENCY = Histogram(
    "ytplayer_command_duration_seconds",
    "Duration of command execution in seconds",
    ["command_name"],
)

# 3. Domain Events Published (Counter)
EVENT_COUNT = Counter("lunawave_events_total", "Total events published", ["event_type"])

# 4. Active WebSockets (Gauge)
ACTIVE_WEBSOCKETS = Gauge(
    "ytplayer_active_websockets",
    "Number of currently active WebSocket connections",
)

# 5. Resolve Latency (Histogram)
RESOLVE_LATENCY = Histogram(
    "lunawave_stream_resolve_duration_seconds",
    "Duration of yt-dlp stream URL resolution (Rule 3 cache miss only)",
)


def get_metrics_content():
    """Returns the Prometheus metrics in text format."""
    return generate_latest(), CONTENT_TYPE_LATEST
