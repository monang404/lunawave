"""
Module: server.handlers.auth

Purpose:
    Handle WebSocket authentication, session token verification, and
    per-IP login rate limiting.

Responsibilities:
    - Verify existing session tokens against the database.
    - Validate credentials via PBKDF2 and issue new session tokens.
    - Reject IPs that exceed 5 failed login attempts in a 5-minute window.

Depends on:
    - core.security

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async; protected by manager.rl_lock).
"""

import asyncio
import json
import secrets

from config import ADMIN_PASSWORD, ADMIN_USERNAME
from core.security import verify_password


def _prune_stale_ips(manager, now: float) -> None:
    """Hapus entry IP yang sudah melewati window dari kedua dict rate-limit.
    Dipanggil tiap handle_auth agar dict tidak tumbuh tanpa batas (memory leak).
    """
    WINDOW_AUTH = 300  # 5 menit — sama dengan window login_attempts
    WINDOW_CMD = 60  # 1 menit — sama dengan window command_history

    stale_auth = [
        ip
        for ip, ts_list in manager.login_attempts.items()
        if not any(now - t < WINDOW_AUTH for t in ts_list)
    ]
    for ip in stale_auth:
        del manager.login_attempts[ip]

    stale_cmd = [
        ip
        for ip, ts_list in manager.command_history.items()
        if not any(now - t < WINDOW_CMD for t in ts_list)
    ]
    for ip in stale_cmd:
        del manager.command_history[ip]


async def handle_auth(ws, data, manager, client_ip, sessions, now):
    async with manager.rl_lock:
        # Prune dict rate-limit agar tidak tumbuh selamanya
        _prune_stale_ips(manager, now)

        token = data.get("token")
        if token and sessions:
            if await sessions.verify_session(token):
                manager.authenticated_connections.add(ws)
                await ws.send_str(
                    json.dumps({"type": "auth_status", "data": {"success": True, "token": token}})
                )
                return

        attempts = manager.login_attempts.get(client_ip, [])
        attempts = [t for t in attempts if now - t < 300]
        if not attempts:
            manager.login_attempts.pop(client_ip, None)
        else:
            manager.login_attempts[client_ip] = attempts
        if len(attempts) >= 5:
            await ws.send_str(
                json.dumps(
                    {
                        "type": "auth_status",
                        "data": {
                            "success": False,
                            "message": "Terlalu banyak percobaan login. Coba lagi dalam 5 menit.",
                        },
                    }
                )
            )
            return

        username = data.get("username", "")
        password = data.get("password", "")
        # PBKDF2 100k iterasi adalah kerja CPU berat (~60-180ms tergantung
        # device) — kalau dijalankan sinkron di sini, seluruh event loop
        # (termasuk broadcast progress ke client lain & observer mpv) ikut
        # berhenti selama itu. Jalankan di thread executor agar event loop
        # tetap responsif untuk client lain selagi verifikasi berjalan.
        loop = asyncio.get_running_loop()
        # PATCH-2026-07-16-001: verify_password SELALU dipanggil, terlepas
        # dari username, baru dicek username-nya setelah itu. Short-circuit
        # `and` sebelumnya membuat response time berbeda antara username
        # salah (instan) vs username benar+password salah (~60-180ms PBKDF2)
        # -- celah timing side-channel yang bisa dipakai enumerasi username.
        password_matches = await loop.run_in_executor(
            None, verify_password, password, ADMIN_PASSWORD
        )
        password_ok = password_matches and username == ADMIN_USERNAME
        if password_ok:
            new_token = secrets.token_hex(16)
            if sessions:
                await sessions.create_session(new_token, int(now) + 86400)
            manager.authenticated_connections.add(ws)
            if client_ip in manager.login_attempts:
                del manager.login_attempts[client_ip]
            await ws.send_str(
                json.dumps({"type": "auth_status", "data": {"success": True, "token": new_token}})
            )
        else:
            attempts.append(now)
            manager.login_attempts[client_ip] = attempts
            await ws.send_str(
                json.dumps(
                    {
                        "type": "auth_status",
                        "data": {"success": False, "message": "Username atau Password salah!"},
                    }
                )
            )


def require_auth(manager, ws) -> bool:
    return ws in manager.authenticated_connections
