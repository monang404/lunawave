"""
Module: server.handlers.setup

Purpose:
    Handle Initial Setup: creation of the single admin_account row that
    becomes the sole source of login credentials (Fitur B: login_redesign,
    lihat decisions K3/K4/K5 di task_breakdown_agent.yaml). Runs before any
    admin account exists, so it lives outside the normal require_auth gate
    -- the same way "auth" itself is special-cased in websocket.py.

Responsibilities:
    - Validate username/password input for the setup_admin WS action.
    - Hash the password (via core.security, tidak reimplement hashing) and
      persist the account through repos.admin_account.
    - Reject a second submit after an account already exists, without ever
      silently overwriting the first one (race condition submit ganda).
    - Report whether setup is still required, for GET /api/setup-required.
    - Rate limit setup attempts 5x/5menit per IP, pola sama persis dengan
      handle_auth() di server.handlers.auth.

Depends on:
    - core.security
    - server.handlers (get_repos)

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Worker thread (async; protected by manager.rl_lock).
"""

import json
import sqlite3

import structlog
from aiohttp import web

from core.security import hash_password
from server.handlers import get_repos

logger = structlog.get_logger(__name__)

MIN_PASSWORD_LENGTH = 8
RATE_LIMIT_WINDOW_SEC = 300  # 5 menit -- sama dengan window login_attempts di auth.py
RATE_LIMIT_MAX_ATTEMPTS = 5

_ALREADY_SET_UP_MESSAGE = "Akun admin sudah pernah dibuat. Silakan login."


def _validate_setup_input(username: str, password: str) -> str | None:
    """Return pesan error kalau input invalid, None kalau valid dan boleh
    lanjut ke tahap hashing. Field confirm password TIDAK divalidasi di
    sini -- field itu tidak pernah dikirim ke server sama sekali (kontrak
    dengan T-B12.2, validasi match dilakukan murni di client)."""
    if not username or not username.strip():
        return "Username wajib diisi."
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return f"Password minimal {MIN_PASSWORD_LENGTH} karakter."
    return None


def _prune_stale_setup_ips(manager, now: float) -> None:
    """Hapus entry IP yang sudah lewat window dari setup_attempts, mirror
    _prune_stale_ips di auth.py, supaya dict tidak tumbuh tanpa batas."""
    stale = [
        ip
        for ip, ts_list in manager.setup_attempts.items()
        if not any(now - t < RATE_LIMIT_WINDOW_SEC for t in ts_list)
    ]
    for ip in stale:
        del manager.setup_attempts[ip]


async def handle_setup_admin(ws, data, manager, client_ip, repos, now):
    async with manager.rl_lock:
        _prune_stale_setup_ips(manager, now)

        attempts = manager.setup_attempts.get(client_ip, [])
        attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW_SEC]
        if attempts:
            manager.setup_attempts[client_ip] = attempts
        else:
            manager.setup_attempts.pop(client_ip, None)

        if len(attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
            await ws.send_str(
                json.dumps(
                    {
                        "type": "setup_status",
                        "data": {
                            "success": False,
                            "message": "Terlalu banyak percobaan. Coba lagi dalam 5 menit.",
                        },
                    }
                )
            )
            return

        username = data.get("username", "")
        password = data.get("password", "")

        error = _validate_setup_input(username, password)
        if error:
            attempts.append(now)
            manager.setup_attempts[client_ip] = attempts
            await ws.send_str(
                json.dumps({"type": "setup_status", "data": {"success": False, "message": error}})
            )
            return

        # Race condition submit ganda, lapis 1: cek dulu sebelum insert.
        # Ini BUKAN garis pertahanan utama -- dua request nyaris bersamaan
        # bisa lolos cek ini berdua (TOCTOU). Garis pertahanan sesungguhnya
        # adalah UNIQUE(username) di DB, ditangani lewat IntegrityError
        # di bawah. Cek ini murni supaya kasus non-race (submit kedua lama
        # setelah yang pertama) dapat pesan cepat tanpa buang-buang hash.
        try:
            already_exists = await repos.admin_account.admin_account_exists()
        except Exception:
            # Fallback kegagalan setup (lihat catatan lengkap di except
            # Exception setelah create_admin_account di bawah): DB tidak
            # bisa dibaca sama sekali -> jangan lanjut ke hashing/insert.
            logger.error("setup_admin_exists_check_failed", client_ip=client_ip, exc_info=True)
            await ws.send_str(
                json.dumps(
                    {
                        "type": "setup_status",
                        "data": {
                            "success": False,
                            "message": "Gagal menyimpan akun admin. Coba lagi, atau cek log server.",
                        },
                    }
                )
            )
            return
        if already_exists:
            await ws.send_str(
                json.dumps(
                    {
                        "type": "setup_status",
                        "data": {"success": False, "message": _ALREADY_SET_UP_MESSAGE},
                    }
                )
            )
            return

        password_hash = hash_password(password)
        try:
            await repos.admin_account.create_admin_account(username.strip(), password_hash)
        except sqlite3.IntegrityError:
            # Race condition submit ganda, lapis 2: dua request nyaris
            # bersamaan lolos cek exists() di atas, tapi UNIQUE constraint
            # di DB menolak yang kedua -- tidak pernah overwrite diam-diam.
            await ws.send_str(
                json.dumps(
                    {
                        "type": "setup_status",
                        "data": {"success": False, "message": _ALREADY_SET_UP_MESSAGE},
                    }
                )
            )
            return
        except Exception:
            # Fallback kegagalan setup: DB corrupt, disk penuh, atau
            # kegagalan I/O lain di luar dugaan. Penting:
            # 1. Server TIDAK boleh crash -- exception ditangkap di sini,
            #    bukan dibiarkan menjalar (WS handler tetap hidup untuk
            #    client lain, aiohttp app tetap jalan).
            # 2. Client dapat pesan jelas, TANPA membocorkan detail
            #    internal (path DB, stack trace) -- detail lengkap hanya
            #    masuk log server.
            # 3. INSERT gagal berarti tidak ada row admin_account yang
            #    tersimpan sama sekali (single atomic statement) -- tidak
            #    pernah ada akun "kosong" yang bisa login tanpa password.
            logger.error("setup_admin_failed", client_ip=client_ip, exc_info=True)
            await ws.send_str(
                json.dumps(
                    {
                        "type": "setup_status",
                        "data": {
                            "success": False,
                            "message": "Gagal menyimpan akun admin. Coba lagi, atau cek log server.",
                        },
                    }
                )
            )
            return

        manager.setup_attempts.pop(client_ip, None)
        await ws.send_str(json.dumps({"type": "setup_status", "data": {"success": True}}))


async def setup_required(request: web.Request) -> web.Response:
    """GET /api/setup-required -- dipanggil client saat load, SEBELUM
    koneksi WS dibuka, untuk memutuskan tampilkan #setup-screen atau
    #portal-screen (lihat T-B11.1/T-B11.2). Registrasi route-nya sendiri
    ada di T-B8 (gate websocket.py/app.py)."""
    repos = get_repos(request)
    try:
        exists = await repos.admin_account.admin_account_exists()
    except Exception:
        # Fallback kegagalan setup: DB corrupt/disk penuh saat startup
        # tidak boleh menjatuhkan seluruh server -- request ini gagal
        # dengan jelas (503), bukan 500 generik/stack trace bocor.
        logger.error("setup_required_check_failed", exc_info=True)
        return web.json_response(
            {"error": "Gagal memeriksa status setup. Cek log server."}, status=503
        )
    return web.json_response({"setup_required": not exists})
