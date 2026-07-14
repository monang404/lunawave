"""
Module: tests.unit.persistence.test_session_repo

Purpose:
    Auto-generated module docstring.

Subscribes to:
    None

Publishes:
    None
"""

import time


async def test_create_verify_delete_session_lifecycle(db):
    now = int(time.time())
    await db.create_session("token-123", now + 3600)
    assert await db.verify_session("token-123") is True
    await db.delete_session("token-123")
    assert await db.verify_session("token-123") is False


async def test_verify_session_unknown_token_returns_false(db):
    assert await db.verify_session("never-created") is False


async def test_verify_session_expired_token_returns_false_and_self_deletes(db):
    now = int(time.time())
    await db.create_session("expired-token", now - 10)
    assert await db.verify_session("expired-token") is False
    async with db.conn.execute(
        "SELECT 1 FROM sessions WHERE token = ?", ("expired-token",)
    ) as cursor:
        assert await cursor.fetchone() is None


async def test_verify_session_boundary_expires_at_equal_now_is_expired(db):
    now = int(time.time())
    await db.create_session("boundary-token", now)
    assert await db.verify_session("boundary-token") is False


async def test_cleanup_sessions_removes_all_expired_but_keeps_valid(db):
    now = int(time.time())
    await db.create_session("old-1", now - 100)
    await db.create_session("old-2", now - 1)
    await db.create_session("valid", now + 100)
    await db.cleanup_sessions()
    assert await db.verify_session("old-1") is False
    assert await db.verify_session("old-2") is False
    assert await db.verify_session("valid") is True
