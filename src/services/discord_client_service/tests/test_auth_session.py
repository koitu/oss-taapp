"""Tests for auth_session in-memory helpers."""

import time
import pytest

from discord_client_service import auth_session
from fastapi import HTTPException


def test_create_and_pop_state_and_ttl():
    s = auth_session.create_state("g1")
    assert isinstance(s, str)
    entry = auth_session.pop_state(s)
    assert entry is not None
    assert entry.get("guild_id") == "g1"

    # pop again -> None
    assert auth_session.pop_state(s) is None


def test_pop_state_expired(monkeypatch):
    s = auth_session.create_state("g2")
    # make it appear old
    auth_session._STATE_STORE[s]["created"] = time.time() - auth_session.STATE_TTL - 10
    assert auth_session.pop_state(s) is None


@pytest.mark.asyncio
async def test_credentials_set_get_delete():
    await auth_session.set_credential("g1", {"a": 1})
    got = await auth_session.get_credential("g1")
    assert got["a"] == 1
    deleted = await auth_session.delete_credential("g1")
    assert deleted is True
    assert await auth_session.get_credential("g1") is None


def test_create_session_and_check_and_expiry():
    sid = auth_session.create_session(["g1"])
    assert auth_session.check_session(sid, "g1") is True

    # expire it
    auth_session._SESSION_STORE[sid]["created"] = time.time() - auth_session.SESSION_TTL - 1
    assert auth_session.check_session(sid, "g1") is False


def test_require_guild_access_forbidden():
    with pytest.raises(HTTPException):
        auth_session.require_guild_access("g1", None)


def test_check_session_none_and_missing():
    # session id None should be false
    assert auth_session.check_session(None, "g1") is False
    # random id not present
    assert auth_session.check_session("no-such-id", "g1") is False
