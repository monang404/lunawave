"""
Module: core.command_bus

Purpose:
    Implement a single-writer CommandBus that enforces exactly one handler
    per command name and records Prometheus metrics for every execution.

Responsibilities:
    - Register/unregister command handlers (1-to-1, raises on duplicate).
    - Dispatch commands with OpenTelemetry span and latency/count metrics.

Depends on:
    - core.observability (COMMAND_COUNT, COMMAND_LATENCY, tracer)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async execute).
"""

import asyncio
import structlog
import time
from typing import Callable, Any, Dict
from core.observability import COMMAND_COUNT, COMMAND_LATENCY
from core.commands import *  # noqa: F401, F403

logger = structlog.get_logger(__name__)

class CommandBus:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, command: str, handler: Callable):
        if command in self._handlers:
            raise RuntimeError(f"Command '{command}' is already registered to {self._handlers[command]}")
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

        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(data)
            else:
                return handler(data)
        except Exception as e:
            status = "error"
            logger.error(f"Command execution error for '{command}': {e}", exc_info=True)
            raise
        finally:
            duration = time.perf_counter() - start_time
            COMMAND_LATENCY.labels(command_name=command).observe(duration)
            COMMAND_COUNT.labels(command_name=command, status=status).inc()

command_bus = CommandBus()
