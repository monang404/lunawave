"""
Module: persistence.chat_repo

Purpose:
    Repository layer for managing chat messages between Admin and Clients.

Responsibilities:
    - Insert new chat messages into the database.
    - Retrieve recent chat messages based on client IP or fetch all for Admins.

Depends on:
    - aiosqlite
"""
from typing import Any, Dict, List

import aiosqlite
import structlog

logger = structlog.get_logger(component="persistence.chat")


class ChatRepository:
    def __init__(self, conn: aiosqlite.Connection):
        self.conn = conn

    async def add_message(
        self, sender_name: str, message: str, is_admin: bool = False, client_ip: str = None
    ) -> dict[str, Any]:
        """Menambahkan pesan chat baru ke database dan mengembalikan record tersebut."""
        async with self.conn.execute(
            "INSERT INTO chat_messages (sender_name, message, is_admin, client_ip) VALUES (?, ?, ?, ?)",
            (sender_name, message, 1 if is_admin else 0, client_ip),
        ) as cursor:
            await self.conn.commit()
            msg_id = cursor.lastrowid

        async with self.conn.execute(
            "SELECT id, sender_name, message, is_admin, client_ip, created_at FROM chat_messages WHERE id = ?",
            (msg_id,),
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else {}

    async def get_recent_messages(
        self, limit: int = 100, client_ip: str = None
    ) -> list[dict[str, Any]]:
        """Mengambil pesan chat terbaru, diurutkan dari yang terlama ke terbaru (untuk di-render)."""
        if client_ip:
            query = "SELECT id, sender_name, message, is_admin, client_ip, created_at FROM chat_messages WHERE client_ip = ? ORDER BY id DESC LIMIT ?"
            params = (client_ip, limit)
        else:
            query = "SELECT id, sender_name, message, is_admin, client_ip, created_at FROM chat_messages ORDER BY id DESC LIMIT ?"
            params = (limit,)

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            # Balik urutan agar yang tertua di atas, terbaru di bawah
            return [dict(row) for row in reversed(rows)]
