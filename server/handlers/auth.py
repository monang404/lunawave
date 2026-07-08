import asyncio
import json
import secrets
import time

from config import ADMIN_USERNAME, get_admin_password
from core.constants import AUTH_TIMEOUT, AUTH_MAX_LIMIT, TOKEN_TTL, MAX_LOGIN_ATTEMPTS
from core.security import verify_password


def _prune_stale_ips(manager, now: float) -> None:
    """Hapus entry IP yang sudah melewati window dari kedua dict rate-limit.
    Dipanggil tiap handle_auth agar dict tidak tumbuh tanpa batas (memory leak).
    """
    WINDOW_AUTH = AUTH_TIMEOUT
    WINDOW_CMD  = 60

    stale_auth = [ip for ip, ts_list in manager.login_attempts.items()
                  if not any(now - t < WINDOW_AUTH for t in ts_list)]
    for ip in stale_auth:
        del manager.login_attempts[ip]

    stale_cmd = [ip for ip, ts_list in manager.command_history.items()
                 if not any(now - t < WINDOW_CMD for t in ts_list)]
    for ip in stale_cmd:
        del manager.command_history[ip]


async def _verify_token(ws, token, manager, db) -> bool:
    if token and db:
        if await db.verify_session(token):
            manager.authenticated_connections.add(ws)
            await ws.send_str(json.dumps({
                "type": "auth_status",
                "data": {"success": True, "token": token}
            }))
            return True
    return False

async def _check_rate_limit(ws, client_ip, manager, now) -> list:
    attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < AUTH_TIMEOUT]
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        manager.login_attempts[client_ip] = attempts
        await ws.send_str(json.dumps({
            "type": "auth_status",
            "data": {"success": False, "message": "Terlalu banyak percobaan login. Coba lagi dalam 5 menit."}
        }))
        return None
    return attempts

async def _process_credentials(ws, data, manager, client_ip, db, now, attempts):
    username = data.get("username", "")
    password = data.get("password", "")
    if secrets.compare_digest(username, ADMIN_USERNAME) and verify_password(password, get_admin_password()):
        new_token = secrets.token_hex(32)
        if db:
            await db.create_session(new_token, int(now) + TOKEN_TTL)
        manager.authenticated_connections.add(ws)
        manager.login_attempts.pop(client_ip, None)
        await ws.send_str(json.dumps({
            "type": "auth_status",
            "data": {"success": True, "token": new_token}
        }))
    else:
        attempts.append(now)
        manager.login_attempts[client_ip] = attempts
        await ws.send_str(json.dumps({
            "type": "auth_status",
            "data": {"success": False, "message": "Username atau Password salah!"}
        }))

async def handle_auth(ws, data, manager, client_ip, db, now):
    async with manager.rl_lock:
        attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < AUTH_TIMEOUT]
        delay = min(len(attempts), 5) if attempts else 0

    if delay > 0:
        await asyncio.sleep(delay)

    async with manager.rl_lock:
        now = time.monotonic()
        _prune_stale_ips(manager, now)

        if await _verify_token(ws, data.get("token"), manager, db):
            return

        attempts = await _check_rate_limit(ws, client_ip, manager, now)
        if attempts is None:
            return

    # _process_credentials dipanggil di LUAR rl_lock agar operasi I/O
    # (db.create_session) tidak menahan request login client lain (S02-008 fix lengkap)
    await _process_credentials(ws, data, manager, client_ip, db, now, attempts)


def require_auth(manager, ws) -> bool:
    return ws in manager.authenticated_connections

async def handle_logout(ws, data, manager, db):
    token = data.get("token")
    if db and token:
        await db.delete_session(token)

    if ws in manager.authenticated_connections:
        manager.authenticated_connections.remove(ws)

    await ws.send_str(json.dumps({
        "type": "auth_status",
        "data": {"success": False, "message": "Logged out successfully."}
    }))
