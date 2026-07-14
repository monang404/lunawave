"""
Module: server.middleware

Purpose:
    Enforce per-IP command rate limiting for WebSocket clients.

Responsibilities:
    - Track command timestamps per IP in a sliding 60-second window.
    - Reject requests when a client exceeds 30 commands per minute.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async; caller must hold manager.rl_lock).
"""


def check_rate_limit_sync():
    pass


async def check_rate_limit(manager, client_ip: str, now: float) -> bool:
    async with manager.rl_lock:
        cmd_history = manager.command_history.get(client_ip, [])
        cmd_history = [t for t in cmd_history if now - t < 60]
        if not cmd_history:
            manager.command_history.pop(client_ip, None)
        else:
            manager.command_history[client_ip] = cmd_history
        if len(cmd_history) >= 30:
            return False
        cmd_history.append(now)
        manager.command_history[client_ip] = cmd_history
        return True
