"""
Module: core.log_context

Purpose:
    Thin wrappers over structlog.contextvars for the three correlation
    fields defined in docs/rfc/logging_standard/LOGGING_STANDARD.md §5.2:
    session_id (one WebSocket connection), request_id (one Command Bus
    execution), correlation_id (one flow that crosses separately
    scheduled asyncio tasks, e.g. a radio cycle triggering a prefetch, or
    a download whose progress hook runs in a separate task).

Responsibilities:
    - bind_session(session_id) / bind_request(request_id) /
      bind_correlation(correlation_id): bind one field each into
      structlog's contextvars, following the exact pattern already
      proven correct in server/middleware/traffic.py (req_id).
    - Provide matching unbind_*() helpers for callers that need to scope
      the binding explicitly (e.g. tests, or a caller that wants to clear
      before the enclosing async context ends).
    - Nothing else. These are NOT a replacement for
      structlog.contextvars.bind_contextvars/unbind_contextvars -- they
      are named, single-purpose call sites so every binding site in the
      codebase uses the same field name and the same fail-safe pattern.

Depends on:
    None (structlog is a third-party dependency, already used elsewhere)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Per-asyncio-task contextvars -- safe across concurrent WS
    connections/commands/radio cycles/downloads as long as each task
    binds its own values and callers propagate the SAME id to child
    tasks explicitly (anti-pattern §12.9: never mint a new correlation
    id mid-flow -- pass the existing one down to
    asyncio.create_task(...) callables instead).
"""

import structlog

_SESSION_KEY = "session_id"
_REQUEST_KEY = "request_id"
_CORRELATION_KEY = "correlation_id"


def bind_session(session_id: str) -> None:
    """Bind session_id for the lifetime of a WebSocket connection.
    Call once from ConnectionManager.connect(). Fail-safe: never raises,
    mirroring the pattern in server/middleware/traffic.py."""
    try:
        structlog.contextvars.bind_contextvars(**{_SESSION_KEY: session_id})
    except Exception:
        pass


def unbind_session() -> None:
    """Unbind session_id. Call from ConnectionManager.disconnect()."""
    try:
        structlog.contextvars.unbind_contextvars(_SESSION_KEY)
    except Exception:
        pass


def bind_request(request_id: str) -> None:
    """Bind request_id for one Command Bus execution. Call at the entry
    point of CommandBus.execute(). Stacks on top of session_id (and any
    correlation_id) already bound -- contextvars do not overwrite each
    other, per §5.2."""
    try:
        structlog.contextvars.bind_contextvars(**{_REQUEST_KEY: request_id})
    except Exception:
        pass


def unbind_request() -> None:
    """Unbind request_id. Call when a single command execution ends."""
    try:
        structlog.contextvars.unbind_contextvars(_REQUEST_KEY)
    except Exception:
        pass


def bind_correlation(correlation_id: str) -> None:
    """Bind correlation_id for a flow that crosses separately scheduled
    asyncio tasks (a radio cycle and the prefetch task it triggers; a
    download and its progress hook running in a separate executor task).
    Call at the entry point of that flow, and propagate the SAME value
    explicitly to every child task -- never mint a new one mid-flow
    (anti-pattern §12.9)."""
    try:
        structlog.contextvars.bind_contextvars(**{_CORRELATION_KEY: correlation_id})
    except Exception:
        pass


def unbind_correlation() -> None:
    """Unbind correlation_id. Call when the flow it identifies ends."""
    try:
        structlog.contextvars.unbind_contextvars(_CORRELATION_KEY)
    except Exception:
        pass
