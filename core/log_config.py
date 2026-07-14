"""
Module: core.log_config

Purpose:
    Configure structlog and stdlib logging with an async queue handler,
    rotating file output, and a compact single-line renderer.

Responsibilities:
    - Wire QueueHandler + QueueListener to decouple log I/O from hot paths.
    - Set up RotatingFileHandler (1 MB, 2 backups) and a console handler.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread only (called once during startup).
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

import structlog

from config import BASE_DIR


def simple_renderer(logger, name, event_dict):
    ts = event_dict.pop("timestamp", "")
    level = event_dict.pop("level", "").upper()
    event = event_dict.pop("event", "")

    # Extract any extra keys
    extras = []
    for k, v in event_dict.items():
        if k not in ("logger", "exc_info"):
            extras.append(f"{k}={v}")

    extra_str = f" ({', '.join(extras)})" if extras else ""
    return f"[{ts}] {level}: {event}{extra_str}"


def setup_logging():
    import queue
    from logging.handlers import QueueHandler, QueueListener

    log_path = BASE_DIR / "lunawave.log"
    _file_handler = RotatingFileHandler(
        log_path, maxBytes=1 * 1024 * 1024, backupCount=2, encoding="utf-8"
    )
    _console_handler = logging.StreamHandler(sys.stdout)

    log_queue = queue.Queue(-1)
    queue_handler = QueueHandler(log_queue)
    listener = QueueListener(log_queue, _file_handler, _console_handler)
    listener.start()

    logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=[queue_handler])

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="%H:%M:%S"),
            simple_renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
