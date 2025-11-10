"""Unit tests for the discord_client_service FastAPI API.

These tests mirror the style used for the mail client service tests and use
fake client implementations to exercise the HTTP routes without external
dependencies.
"""

from collections.abc import Generator
from importlib import util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from discord_client_service import api, service

# Load the sibling test helper module (works whether pytest imports tests as
# modules or as plain files). This avoids relative import issues during
# test collection when running a subset of tests.
spec = util.spec_from_file_location(
    "test_fake_discord", Path(__file__).with_name("test_fake_discord.py")
)
test_fake = util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(test_fake)

FakeBotClient = test_fake.FakeBotClient
FakeUserClient = test_fake.FakeUserClient
FakeChannel = test_fake.FakeChannel
FakeMessage = test_fake.FakeMessage


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with auth dependency overridden and fake clients patched in."""
    # Override auth dependency so tests don't need real sessions/cookies
    try:
        from discord_client_service.auth_session import require_guild_access

        async def _no_auth() -> None:  # async to match possible async dependency
            return None

        service.app.dependency_overrides[require_guild_access] = _no_auth
    except Exception:
        # If import fails, still attempt to continue — tests will patch necessary
        pass

    # Patch helper functions and DiscordClient class used in the API module so
    # routes call our fakes.
    fake_user_client = FakeUserClient()
    fake_bot_client = FakeBotClient(channels=[FakeChannel("c1", "general")])

    # Replace resolution functions used by the api module
    async def _get_client_for_user(guild_id: str):
        return fake_user_client

    async def _get_bot_client_for_guild(guild_id: str):
        return fake_bot_client

    async def _check_user_authenticated(guild_id: str) -> bool:
        return True

    async def _delete_user_credentials(guild_id: str) -> bool:
        return True

    api.get_client_for_user = _get_client_for_user
    api.get_bot_client_for_guild = _get_bot_client_for_guild
    api.check_user_authenticated = _check_user_authenticated
    api.delete_user_credentials = _delete_user_credentials

    # Provide a fake DiscordClient for oauth login path
    class _FakeDiscordClient:
        def _get_authorization_url(self, state=None):
            return ("http://auth.example/authorize", "state123")

    api.DiscordClient = _FakeDiscordClient

    test_client = TestClient(service.app)
    yield test_client
    service.app.dependency_overrides.clear()


@pytest.mark.unit
def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.unit
def test_oauth_login_returns_url(client: TestClient) -> None:
    response = client.get("/auth/login")
    assert response.status_code == 200
    data = response.json()
    assert "authorization_url" in data
    assert data["authorization_url"].startswith("http")


@pytest.mark.unit
def test_get_channels_success(client: TestClient) -> None:
    response = client.get("/guilds/g1/channels")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["channels"][0]["name"] == "general"


@pytest.mark.unit
def test_get_channel_success(client: TestClient) -> None:
    response = client.get("/g1/channels/c1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "c1"
    assert data["name"] == "general"


@pytest.mark.unit
def test_get_messages_success(client: TestClient) -> None:
    response = client.get("/g1/channels/c1/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["messages"][0]["content"] == "first"


@pytest.mark.unit
def test_send_message_success(client: TestClient) -> None:
    response = client.post("/g1/channels/c1/messages", json={"content": "hi there"})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "hi there"


@pytest.mark.unit
def test_delete_message_success(client: TestClient) -> None:
    # ensure message exists then delete
    response = client.delete("/g1/channels/c1/messages/m1")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.unit
def test_delete_message_not_found(client: TestClient) -> None:
    response = client.delete("/g1/channels/c1/messages/does-not-exist")
    assert response.status_code == 404


@pytest.mark.unit
def test_auth_status(client: TestClient) -> None:
    response = client.get("/auth/status/g1")
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True


@pytest.mark.unit
def test_oauth_logout_success(client: TestClient) -> None:
    response = client.delete("/auth/logout/g1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
