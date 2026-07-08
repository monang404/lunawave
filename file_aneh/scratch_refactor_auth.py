import sys
from pathlib import Path

file_path = Path(r"c:\Users\PUTRA JAYA LIMBANGAN\Documents\ytgui\ytgui-project\server\handlers\auth.py")
content = file_path.read_text(encoding="utf-8")

start_marker = "async def handle_auth(ws, data, manager, client_ip, db, now):"
end_marker = "def require_auth(manager, ws) -> bool:"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find markers!")
    sys.exit(1)

new_code = """async def _verify_token(ws, token, manager, db) -> bool:
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
    attempts = [t for t in manager.login_attempts.get(client_ip, []) if now - t < 300]
    if attempts:
        import asyncio
        await asyncio.sleep(min(len(attempts), 5))

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
            await db.create_session(new_token, int(now) + 14400)
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
        _prune_stale_ips(manager, now)

        if await _verify_token(ws, data.get("token"), manager, db):
            return

        attempts = await _check_rate_limit(ws, client_ip, manager, now)
        if attempts is None:
            return

        await _process_credentials(ws, data, manager, client_ip, db, now, attempts)

"""

new_content = content[:start_idx] + new_code + content[end_idx:]
file_path.write_text(new_content, encoding="utf-8")
print("Refactored auth.py successfully.")
