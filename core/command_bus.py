"""
Module: core.command_bus

Purpose:
    Implement a single-writer CommandBus that enforces exactly one handler
    per command name and records Prometheus metrics for every execution.

Responsibilities:
    - Register/unregister command handlers (1-to-1, raises on duplicate).
    - Dispatch commands with OpenTelemetry span and latency/count metrics.

Depends on:
    - core.commands
    - core.observability

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async execute).
"""

import asyncio
import secrets
import time
from collections.abc import Callable
from typing import Any

import structlog

from core.commands import *  # noqa: F401, F403
from core.log_categories import LC_COMMAND
from core.log_context import bind_request, unbind_request
from core.observability import COMMAND_COUNT, COMMAND_LATENCY

logger = structlog.get_logger(component="core.command_bus")


class CommandBus:
    def __init__(self):
        self._handlers: dict[str, Callable] = {}

    def register(self, command: str, handler: Callable):
        if command in self._handlers:
            raise RuntimeError(
                f"Command '{command}' is already registered to {self._handlers[command]}"
            )
        self._handlers[command] = handler

    def unregister(self, command: str):
        if command in self._handlers:
            del self._handlers[command]

    async def execute(self, command: str, data: Any = None) -> Any:
        if command not in self._handlers:
            raise RuntimeError(f"No handler registered for command '{command}'")

        handler = self._handlers[command]
        start_time = time.perf_counter()
        status = "success"

        # L5.2: request_id baru per eksekusi command, ditumpuk di atas
        # session_id yang sudah aktif (jika ada) via contextvars -- tidak
        # saling menimpa (§5.2). Dilepas lagi di finally supaya tidak bocor
        # ke eksekusi command berikutnya dalam task WS yang sama.
        request_id = secrets.token_hex(4)
        bind_request(request_id)

        # L7.1: entry/exit alur command. DEBUG (volume tinggi, §8.2/§8.3) --
        # bukan kejadian yang tiap kali perlu dilihat operator.
        logger.debug(
            "command_received",
            category=LC_COMMAND,
            command_name=command,
        )

        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(data)
            else:
                result = handler(data)
            logger.debug(
                "command_succeeded",
                category=LC_COMMAND,
                command_name=command,
            )
            return result
        except Exception as e:
            status = "error"
            logger.error(
                "command_execution_failed",
                category=LC_COMMAND,
                command_name=command,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )
            raise
        finally:
            duration = time.perf_counter() - start_time
            COMMAND_LATENCY.labels(command_name=command).observe(duration)
            COMMAND_COUNT.labels(command_name=command, status=status).inc()
            unbind_request()
