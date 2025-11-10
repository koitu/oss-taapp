"""Additional tests to exercise error branches in api.py."""

import pytest
from fastapi.testclient import TestClient

from discord_client_service import api, service


@pytest.fixture
def client():
    # override auth dependency
    try:
        from discord_client_service.auth_session import require_guild_access

        async def _no_auth():
            return None

        service.app.dependency_overrides[require_guild_access] = _no_auth
    except Exception:
        pass

    test_client = TestClient(service.app)
    yield test_client
    service.app.dependency_overrides.clear()


@pytest.mark.unit
def test_oauth_login_exception(client: TestClient, monkeypatch):
    class BadClient:
        def _get_authorization_url(self, state=None):
            raise RuntimeError("boom")

    monkeypatch.setattr(api, "DiscordClient", BadClient)
    r = client.get("/auth/login")
    assert r.status_code == 500


@pytest.mark.unit
def test_oauth_callback_missing_guild(monkeypatch, client: TestClient):
    class C:
        def _exchange_code_for_token(self, code):
            return {"access_token": "t"}

    monkeypatch.setattr(api, "DiscordClient", C)
    # pop_state returns None by default; do not provide guild_id
    r = client.get("/auth/callback?code=abc")
    assert r.status_code == 400


@pytest.mark.unit
def test_oauth_callback_exchange_error(monkeypatch, client: TestClient):
    class C:
        def _exchange_code_for_token(self, code):
            raise RuntimeError("fail exchange")

    monkeypatch.setattr(api, "DiscordClient", C)
    r = client.get("/auth/callback?code=abc&guild_id=g1")
    assert r.status_code == 500


@pytest.mark.unit
def test_oauth_callback_success(monkeypatch, client: TestClient):
    # Successful token exchange and credential storage should set a session cookie
    class C:
        def _exchange_code_for_token(self, code):
            return {"access_token": "t"}

    stored = {}

    async def _store_user_credentials(guild_id, token_data):
        stored["guild_id"] = guild_id
        stored["token"] = token_data

    monkeypatch.setattr(api, "DiscordClient", C)
    monkeypatch.setattr(api, "store_user_credentials", _store_user_credentials)
    # Use guild_id query param to avoid needing server-side state
    # Some TestClient versions do not accept `allow_redirects`; rely on default
    # behavior and verify cookie presence on the final response.
    r = client.get("/auth/callback?code=abc&guild_id=g1")
    # RedirectResponse may be followed by TestClient; allow final 200 as well
    assert r.status_code in (200, 301, 302, 303, 307, 308)
    # Different TestClient versions expose cookies on the response or the
    # client's cookie jar. Accept either location for compatibility.
    assert ("session_id" in r.cookies) or ("session_id" in client.cookies)


@pytest.mark.unit
def test_oauth_logout_not_found(monkeypatch, client: TestClient):
    async def _delete_user_credentials(guild_id):
        return False

    monkeypatch.setattr(api, "delete_user_credentials", _delete_user_credentials)
    r = client.delete("/auth/logout/g1")
    assert r.status_code == 404


@pytest.mark.unit
def test_oauth_logout_bot_leave_failure(monkeypatch, client: TestClient):
    async def _delete_user_credentials(gid):
        return True

    class Bot:
        def leave_guild(self, gid):
            raise RuntimeError("leave failed")

    async def _get_bot_client_for_guild(gid):
        return Bot()

    monkeypatch.setattr(api, "delete_user_credentials", _delete_user_credentials)
    monkeypatch.setattr(api, "get_bot_client_for_guild", _get_bot_client_for_guild)
    r = client.delete("/auth/logout/g1")
    assert r.status_code == 200


@pytest.mark.unit
def test_get_channels_unauth(monkeypatch, client: TestClient):
    async def _gb(gid):
        raise ValueError("not authenticated")

    monkeypatch.setattr(api, "get_bot_client_for_guild", _gb)
    r = client.get("/guilds/g1/channels")
    assert r.status_code == 401


@pytest.mark.unit
def test_get_channels_error(monkeypatch, client: TestClient):
    async def _gb(gid):
        raise RuntimeError("oh")

    monkeypatch.setattr(api, "get_bot_client_for_guild", _gb)
    r = client.get("/guilds/g1/channels")
    assert r.status_code == 500


@pytest.mark.unit
def test_get_channel_not_found(monkeypatch, client: TestClient):
    async def _gc(gid):
        raise ValueError("not found")

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c99")
    assert r.status_code == 404


@pytest.mark.unit
def test_get_channel_unauth(monkeypatch, client: TestClient):
    async def _gc(gid):
        raise ValueError("no auth")

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1")
    assert r.status_code == 401


@pytest.mark.unit
def test_get_channel_error(monkeypatch, client: TestClient):
    async def _gc(gid):
        raise RuntimeError("bad")

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1")
    assert r.status_code == 500


@pytest.mark.unit
def test_get_messages_unauth(monkeypatch, client: TestClient):
    async def _gc(gid):
        raise ValueError("auth")

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1/messages")
    assert r.status_code == 401


@pytest.mark.unit
def test_get_messages_error(monkeypatch, client: TestClient):
    async def _gc(gid):
        raise RuntimeError("boom")

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.get("/g1/channels/c1/messages")
    assert r.status_code == 500


@pytest.mark.unit
def test_send_message_not_authenticated(monkeypatch, client: TestClient):
    async def _gc(gid):
        class C:
            def send_message(self, channel_id, content):
                raise ValueError("not authenticated")

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.post("/g1/channels/c1/messages", json={"content": "x"})
    assert r.status_code == 401


@pytest.mark.unit
def test_send_message_bad_request(monkeypatch, client: TestClient):
    async def _gc(gid):
        class C:
            def send_message(self, channel_id, content):
                raise ValueError("other")

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.post("/g1/channels/c1/messages", json={"content": "x"})
    assert r.status_code == 400


@pytest.mark.unit
def test_send_message_error(monkeypatch, client: TestClient):
    async def _gc(gid):
        class C:
            def send_message(self, channel_id, content):
                raise RuntimeError("boom")

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.post("/g1/channels/c1/messages", json={"content": "x"})
    assert r.status_code == 500


@pytest.mark.unit
def test_delete_message_delete_error(monkeypatch, client: TestClient):
    from chat_client_api.exceptions import MessageDeleteError

    async def _gc(gid):
        class C:
            def delete_message(self, channel_id, message_id):
                raise MessageDeleteError("bad")

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.delete("/g1/channels/c1/messages/mx")
    assert r.status_code == 500


@pytest.mark.unit
def test_delete_message_unauth(monkeypatch, client: TestClient):
    async def _gc(gid):
        class C:
            def delete_message(self, channel_id, message_id):
                raise ValueError("no auth")

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.delete("/g1/channels/c1/messages/mx")
    assert r.status_code == 401


@pytest.mark.unit
def test_delete_message_error_general(monkeypatch, client: TestClient):
    async def _gc(gid):
        class C:
            def delete_message(self, channel_id, message_id):
                raise RuntimeError("boom")

        return C()

    monkeypatch.setattr(api, "get_client_for_user", _gc)
    r = client.delete("/g1/channels/c1/messages/mx")
    assert r.status_code == 500
