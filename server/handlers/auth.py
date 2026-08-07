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

import structlog

from core.log_categories import LC_AUTH
from core.security import hash_password, needs_rehash, verify_password

logger = structlog.get_logger(component="ws.auth")

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
    WINDOW_CHAT = 3600  # 1 jam — window untuk chat_history

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

    # BUG-FIX #7: chat_history tidak pernah di-prune, berbeda dengan
    # login_attempts/command_history. Entry IP yang sudah tidak aktif > 1 jam
    # dibersihkan di sini agar tidak tumbuh tanpa batas.
    stale_chat = [
        uid
        for uid, ts_list in manager.chat_history.items()
        if not any(now - t < WINDOW_CHAT for t in ts_list)
    ]
    for uid in stale_chat:
        del manager.chat_history[uid]


async def handle_auth(ws, data, manager, client_ip, repos, now):
    sessions = repos.sessions if repos else None
    async with manager.rl_lock:
        # Prune dict rate-limit agar tidak tumbuh selamanya
        _prune_stale_ips(manager, now)

        token = data.get("token")
        if token and sessions:
            if await sessions.verify_session(token):
                await sessions.extend_session(token, int(now) + 10800)
                manager.authenticated_connections.add(ws)
                logger.info("auth_token_verified", category=LC_AUTH, client_ip=client_ip)
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
            logger.warning(
                "auth_rate_limited",
                category=LC_AUTH,
                client_ip=client_ip,
                attempt_count=len(attempts),
            )
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

        # BUG-FIX #4: Pre-increment counter sebelum lock dilepas untuk PBKDF2.
        # Tanpa ini, N request paralel bisa semua lolos gate saat counter masih 0
        # karena PBKDF2 (~60-180ms) dijalankan setelah lock dilepas. Dengan
        # pre-increment, setiap request paralel langsung "tercatat" sebagai percobaan
        # sebelum memulai verifikasi. Jika login berhasil, counter di-rollback (delete).
        attempts.append(now)
        manager.login_attempts[client_ip] = attempts

    username = data.get("username", "")
    password = data.get("password", "")

    # T-B13.1: kredensial dibaca dari admin_account (SQLite)
    account = await repos.admin_account.get_admin_account() if repos else None
    stored_hash = account["password_hash"] if account else _DUMMY_PASSWORD_HASH
    stored_username = account["username"] if account else None

    # PBKDF2 100k iterasi adalah kerja CPU berat (~60-180ms tergantung device).
    # LOCK DILEPAS DI SINI: agar client lain (yang sekadar mengirim command biasa)
    # tidak antre menunggu PBKDF2 selesai hanya untuk cek check_rate_limit().
    loop = asyncio.get_running_loop()
    password_matches = await loop.run_in_executor(None, verify_password, password, stored_hash)
    password_ok = password_matches and account is not None and username == stored_username

    # Ambil ulang lock untuk update state
    async with manager.rl_lock:
        if password_ok:
            if account and needs_rehash(stored_hash):
                try:
                    new_hash = await loop.run_in_executor(None, hash_password, password)
                    await repos.admin_account.update_password(new_hash)
                    logger.info("auth_password_rehashed", category=LC_AUTH, client_ip=client_ip)
                except Exception as e:
                    logger.warning("auth_password_rehash_failed", category=LC_AUTH, error=str(e))

            new_token = secrets.token_hex(16)
            if sessions:
                await sessions.create_session(new_token, int(now) + 10800)
                logger.info("auth_session_created", category=LC_AUTH, client_ip=client_ip)
            manager.authenticated_connections.add(ws)
            # BUG-FIX #4: Rollback pre-increment — login berhasil bukan percobaan gagal.
            if client_ip in manager.login_attempts:
                del manager.login_attempts[client_ip]
            logger.info("auth_login_succeeded", category=LC_AUTH, client_ip=client_ip)
            await ws.send_str(
                json.dumps({"type": "auth_status", "data": {"success": True, "token": new_token}})
            )
        else:
            # Pre-increment sudah dilakukan sebelum PBKDF2; tidak perlu append lagi.
            # Hanya refresh list (trim entri lama) agar window 5 menit tetap konsisten.
            existing = manager.login_attempts.get(client_ip, [])
            manager.login_attempts[client_ip] = [t for t in existing if now - t < 300]
            logger.info(
                "auth_login_rejected",
                category=LC_AUTH,
                client_ip=client_ip,
                reason="invalid_credentials",
            )
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
