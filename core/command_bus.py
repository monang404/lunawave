"""
Purpose: CommandBus untuk single-writer pattern (1-to-1).
Berbeda dengan EventBus (pub/sub 1-to-many), CommandBus menjamin
hanya ada SATU handler untuk setiap command.
"""

import asyncio
import time
from typing import Any, Callable, Dict, Type, TypeVar

import structlog

from core.commands import DomainCommand
from core.observability import COMMAND_COUNT, COMMAND_LATENCY

logger = structlog.get_logger(__name__)

C = TypeVar("C", bound=DomainCommand)

class CommandBus:
    def __init__(self):
        self._handlers: Dict[Type[DomainCommand], Callable] = {}

    def register(self, command_type: Type[C], handler: Callable[[C], Any]):
        if command_type in self._handlers:
            raise RuntimeError(f"Command '{command_type.__name__}' is already registered to {self._handlers[command_type]}")
        self._handlers[command_type] = handler

    def unregister(self, command_type: Type[C]):
        if command_type in self._handlers:
            del self._handlers[command_type]

    async def execute(self, command: DomainCommand) -> Any:
        command_type = type(command)
        if command_type not in self._handlers:
            raise RuntimeError(f"No handler registered for command '{command_type.__name__}'")

        handler = self._handlers[command_type]
        start_time = time.perf_counter()
        status = "success"

        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(command)
            else:
                return handler(command)
        except Exception as e:
            status = "error"
            logger.error(f"Command execution error for '{command_type.__name__}': {e}", exc_info=True)
            raise
        finally:
            duration = time.perf_counter() - start_time
            COMMAND_LATENCY.labels(command_name=command_type.__name__).observe(duration)
            COMMAND_COUNT.labels(command_name=command_type.__name__, status=status).inc()
