"""Integration tests: adapter -> service -> mocked discord implementation.

These tests verify that the ServiceAdapterClient talks to the running
`discord_client_service` FastAPI app and that the app calls into a mocked
Discord client implementation.

The test uses an in-process httpx client bound to the FastAPI app so all
networking stays in-process and fast.
"""

import logging
from collections.abc import Callable, Generator
from typing import Any, cast
from unittest.mock import MagicMock

import httpx
import pytest
from discord_client_service import api, service
from discord_client_service_adapter import ServiceAdapterClient
from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def mock_discord_user_client() -> MagicMock:
    """Provide a MagicMock used as the Discord user client for tests."""
    return MagicMock()


@pytest.fixture(scope="module")
def mock_discord_bot_client() -> MagicMock:
    """Provide a MagicMock used as the Discord bot client for tests."""
    return MagicMock()


@pytest.fixture(scope="module")
def test_client(mock_discord_user_client: MagicMock, mock_discord_bot_client: MagicMock) -> Generator[TestClient, None, None]:
    """Start the FastAPI TestClient with auth dependency overridden and fake clients patched in."""
    try:
        from discord_client_service.auth_session import require_guild_access

        async def _no_auth() -> None:
            return None

        service.app.dependency_overrides[require_guild_access] = _no_auth
    except Exception as e:
        # Log the exception so linters don't flag a bare except/pass.
        logger.debug("Failed to override require_guild_access dependency: %s", e)

    # Patch the resolution functions used by the API module so the service
    # calls our mocked clients.
    async def _get_client_for_user(guild_id: str) -> MagicMock:
        """Return the mocked user client for the given guild id."""
        return mock_discord_user_client

    async def _get_bot_client_for_guild(guild_id: str) -> MagicMock:
        """Return the mocked bot client for the given guild id."""
        return mock_discord_bot_client

    async def _check_user_authenticated(guild_id: str) -> bool:
        return True

    # Cast to Any so mypy permits assigning test doubles to module attributes
    cast("Any", api).get_client_for_user = _get_client_for_user
    cast("Any", api).get_bot_client_for_guild = _get_bot_client_for_guild
    cast("Any", api).check_user_authenticated = _check_user_authenticated

    with TestClient(service.app) as client:
        yield client

    service.app.dependency_overrides.clear()


def _make_message(id_: str) -> MagicMock:
    m = MagicMock()
    m.id = id_
    m.channel_id = "c1"
    m.content = "hello"
    m.sender_id = "u1"
    m.sender_name = "tester"
    m.timestamp = "2025-10-10T12:00:00Z"
    m.edited_timestamp = None
    return m


def _make_forward(test_client: TestClient) -> Callable[[httpx.Request], httpx.Response]:
    def _forward(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        resp = test_client.request(request.method, url, headers=dict(request.headers), content=request.content)
        return httpx.Response(
            status_code=resp.status_code,
            headers=resp.headers,
            content=resp.content,
            request=request,
        )

    return _forward


@pytest.mark.circleci
def test_get_messages_via_adapter(test_client: TestClient, mock_discord_user_client: MagicMock) -> None:
    """Adapter should request messages from the service and return them."""
    mock_msg = _make_message("m1")
    mock_discord_user_client.get_messages.return_value = [mock_msg]

    adapter = ServiceAdapterClient(service_url=str(test_client.base_url), guild_id="g1")
    forward = _make_forward(test_client)
    adapter._http_client.set_httpx_client(
        httpx.Client(base_url=str(test_client.base_url), transport=httpx.MockTransport(forward))
    )

    msgs = list(adapter.get_messages(channel_id="c1", limit=5))
    assert len(msgs) == 1
    assert msgs[0].id == "m1"
    mock_discord_user_client.get_messages.assert_called_once_with(channel_id="c1", limit=5)


@pytest.mark.circleci
def test_get_message_via_adapter(test_client: TestClient, mock_discord_user_client: MagicMock) -> None:
    """Adapter.get_message should return the requested message by id."""
    mock_msg = _make_message("m2")
    mock_discord_user_client.get_messages.return_value = [mock_msg]

    # Reset call history so assertions are local to this test
    mock_discord_user_client.reset_mock()

    adapter = ServiceAdapterClient(service_url=str(test_client.base_url), guild_id="g1")
    forward = _make_forward(test_client)
    adapter._http_client.set_httpx_client(
        httpx.Client(base_url=str(test_client.base_url), transport=httpx.MockTransport(forward))
    )

    msg = adapter.get_message(channel_id="c1", message_id="m2")
    assert msg.id == "m2"
    mock_discord_user_client.get_messages.assert_called_once_with(channel_id="c1", limit=100)


@pytest.mark.circleci
def test_send_and_delete_via_adapter(
    test_client: TestClient, mock_discord_user_client: MagicMock, mock_discord_bot_client: MagicMock
) -> None:
    """Adapter should send a message via the service and allow deletion."""
    # Sending
    sent = MagicMock()
    sent.id = "s1"
    sent.channel_id = "c1"
    sent.content = "hi"
    sent.sender_id = "u1"
    sent.sender_name = "tester"
    sent.timestamp = "2025-10-10T12:00:00Z"
    # Ensure edited_timestamp is a valid value (pydantic will validate types)
    sent.edited_timestamp = None
    mock_discord_user_client.send_message.return_value = True

    # Reset call history so assertions are local to this test
    mock_discord_user_client.reset_mock()

    adapter = ServiceAdapterClient(service_url=str(test_client.base_url), guild_id="g1")
    forward = _make_forward(test_client)
    adapter._http_client.set_httpx_client(
        httpx.Client(base_url=str(test_client.base_url), transport=httpx.MockTransport(forward))
    )

    assert adapter.send_message(channel_id="c1", content="hi") is True
    mock_discord_user_client.send_message.assert_called_once_with(channel_id="c1", content="hi")

    # Deleting
    mock_discord_user_client.delete_message.return_value = True
    assert adapter.delete_message(channel_id="c1", message_id="s1") is True
    mock_discord_user_client.delete_message.assert_called_once_with(channel_id="c1", message_id="s1")
