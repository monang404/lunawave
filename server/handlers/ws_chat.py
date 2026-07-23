import json
from typing import Any, Dict

import structlog

from persistence import Repositories

logger = structlog.get_logger(component="ws.chat")


async def handle_chat_command(
    action: str,
    data: dict[str, Any],
    ws,
    repos: Repositories,
    manager,
    is_admin: bool,
    client_ip: str,
):
    if not repos.chat:
        return

    if action == "get_chat_history":
        target_ip = data.get("target_ip") if is_admin else client_ip
        messages = await repos.chat.get_recent_messages(client_ip=target_ip)
        await ws.send_str(json.dumps({"type": "chat_history", "data": messages}))

    elif action == "send_chat":
        sender = data.get("sender_name", "Anonymous").strip()
        message = data.get("message", "").strip()
        target_ip = data.get("target_ip") if is_admin else client_ip

        if not sender:
            sender = "Anonymous"
        if not message or not target_ip:
            return

        # Add to database
        saved_msg = await repos.chat.add_message(sender, message, is_admin, target_ip)

        # Broadcast to Admins and the specific Client
        if saved_msg:
            payload = json.dumps({"type": "chat_message", "data": saved_msg}, ensure_ascii=False)

            for conn in manager.active_connections:
                conn_is_admin = conn in manager.authenticated_connections
                conn_ip = manager.client_ips.get(conn, {}).get("ip")

                # Kirim ke Admin ATAU ke Klien yang bersangkutan
                if conn_is_admin or conn_ip == target_ip:
                    try:
                        await conn.send_str(payload)
                    except Exception:
                        pass
