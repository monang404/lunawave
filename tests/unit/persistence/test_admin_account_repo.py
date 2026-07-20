"""
Module: tests.unit.persistence.test_admin_account_repo

Purpose:
    Unit tests for the admin_account repository: create/read lifecycle and
    the UNIQUE(username) constraint that guards against a second admin
    account being created (submit ganda / race condition, lihat T-B5.3).

Responsibilities:
    - Implement the core functionality described in the purpose.

Depends on:
    None

Subscribes to:
    None

Publishes:
    None

Thread Safety:
    Main thread (async event loop).
"""

import sqlite3

import pytest


async def test_get_admin_account_returns_none_when_empty(db):
    assert await db.admin_account.get_admin_account() is None


async def test_admin_account_exists_false_when_empty(db):
    assert await db.admin_account.admin_account_exists() is False


async def test_create_then_get_admin_account(db):
    await db.admin_account.create_admin_account("admin", "pbkdf2:sha256:100000$salt$key")
    row = await db.admin_account.get_admin_account()
    assert row is not None
    assert row["username"] == "admin"
    assert row["password_hash"] == "pbkdf2:sha256:100000$salt$key"
    assert row["created_at"] is not None


async def test_admin_account_exists_true_after_create(db):
    await db.admin_account.create_admin_account("admin", "pbkdf2:sha256:100000$salt$key")
    assert await db.admin_account.admin_account_exists() is True


async def test_create_admin_account_duplicate_username_raises_unique_error(db):
    await db.admin_account.create_admin_account("admin", "hash-1")
    with pytest.raises(sqlite3.IntegrityError):
        await db.admin_account.create_admin_account("admin", "hash-2")
    # Baris pertama tidak boleh ter-overwrite oleh percobaan kedua yang gagal.
    row = await db.admin_account.get_admin_account()
    assert row["password_hash"] == "hash-1"
