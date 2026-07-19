"""
Module: server.handlers.auth

Purpose:
    Handle WebSocket authentication, session token verification, and
    per-IP login rate limiting.

Responsibilities:
    - Verify existing session tokens against the database.
    - Validate credentials via PBKDF2 (dibaca dari admin_account_repo,
      T-B13.1) dan issue new session tokens.
    - Reject IPs that exceed 5 failed login attempts in a 5-minute window.

Depends on:
    - core.security
    - persistence.admin_account_repo (via repos.admin_account)

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

from core.security import hash_password, verify_password

# T-B13.1: sumber kredensial sekarang admin_account (SQLite), bukan lagi
# config.ADMIN_USERNAME/ADMIN_PASSWORD. Saat admin_account belum ada
# (instalasi baru, belum lewat Initial Setup) kita TETAP harus menjalankan
# PBKDF2 penuh (bukan short-circuit) agar profil waktu respons identik
# dengan kasus "akun ada tapi password salah" -- mempertahankan mitigasi
# timing side-channel PATCH-2026-07-16-001. Hash dummy ini dibuat sekali
# saat modul di-import, dengan password acak yang tidak pernah dipakai di
# manapun -- hanya untuk memberi verify_password() sesuatu yang valid
# secara format untuk diproses dengan biaya PBKDF2 yang sama.
_DUMMY_PASSWORD_HASH = hash_password(secrets.token_hex(32))


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


async def handle_auth(ws, data, manager, client_ip, repos, now):
    sessions = repos.sessions if repos else None
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

        # T-B13.1: kredensial dibaca dari admin_account (SQLite), bukan lagi
        # config.ADMIN_USERNAME/ADMIN_PASSWORD. Saat admin_account belum ada
        # sama sekali (instalasi baru, belum lewat Initial Setup), pakai
        # _DUMMY_PASSWORD_HASH agar verify_password tetap menjalankan PBKDF2
        # penuh -- lihat catatan di _DUMMY_PASSWORD_HASH di atas modul.
        account = await repos.admin_account.get_admin_account() if repos else None
        stored_hash = account["password_hash"] if account else _DUMMY_PASSWORD_HASH
        stored_username = account["username"] if account else None

        # PBKDF2 100k iterasi adalah kerja CPU berat (~60-180ms tergantung
        # device) — kalau dijalankan sinkron di sini, seluruh event loop
        # (termasuk broadcast progress ke client lain & observer mpv) ikut
        # berhenti selama itu. Jalankan di thread executor agar event loop
        # tetap responsif untuk client lain selagi verifikasi berjalan.
        loop = asyncio.get_running_loop()
        # PATCH-2026-07-16-001: verify_password SELALU dipanggil, terlepas
        # dari username maupun ada/tidaknya admin_account, baru dicek
        # username-nya setelah itu. Short-circuit `and` sebelumnya membuat
        # response time berbeda antara username salah (instan) vs username
        # benar+password salah (~60-180ms PBKDF2) -- celah timing
        # side-channel yang bisa dipakai enumerasi username. Pola yang sama
        # dipertahankan di sini walau sumber datanya sekarang admin_account,
        # bukan config.
        password_matches = await loop.run_in_executor(
            None, verify_password, password, stored_hash
        )
        password_ok = password_matches and account is not None and username == stored_username
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
