"""End-to-end integration tests: adapter -> service -> mocked gmail implementation.

These tests verify that the ServiceAdapterClient talks to the running
`mail_client_service` FastAPI app and that the app calls into the mocked
Gmail client implementation via the `get_mail_client` dependency.

The test uses an in-process httpx client bound to the FastAPI app so all
networking stays in-process and fast.
"""

from collections.abc import Callable, Generator
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from mail_client_service.api import app, get_mail_client

import mail_client_api
from mail_client_service_adapter import ServiceAdapterClient

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def mock_gmail_client() -> MagicMock:
    """Provide a MagicMock acting as the Gmail client implementation.

    This mock will be injected into the FastAPI app via dependency overrides.
    """
    return MagicMock()


@pytest.fixture(scope="module")
def test_client(mock_gmail_client: MagicMock) -> Generator[TestClient, None, None]:
    """Start the FastAPI TestClient with the mail client dependency overridden.

    We override `get_mail_client` so the service will call the mocked gmail
    client during the tests.
    """
    app.dependency_overrides[get_mail_client] = lambda: mock_gmail_client
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def _make_message(id_: str, subject: str, from_: str, date: str, body: str | None = None) -> mail_client_api.Message:
    m = MagicMock(spec=mail_client_api.Message)
    m.id = id_
    m.subject = subject
    m.from_ = from_
    m.date = date
    m.body = body
    return m


def _make_forward(test_client: TestClient) -> Callable[[httpx.Request], httpx.Response]:
    """Return a sync forward function that adapts httpx.Request -> httpx.Response via TestClient."""

    def _forward(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        resp = test_client.request(request.method, url, headers=dict(request.headers), content=request.content)
        return httpx.Response(status_code=resp.status_code, headers=resp.headers, content=resp.content, request=request)

    return _forward


@pytest.mark.circleci
def test_get_messages_via_adapter(test_client: TestClient, mock_gmail_client: MagicMock) -> None:
    """Adapter.get_messages should return messages provided by the mocked gmail client via service."""
    # Prepare mocked return from gmail client
    mock_msg = _make_message("m1", "Hello", "alice@example.com", "2025-10-03")
    mock_gmail_client.get_messages.return_value = [mock_msg]

    # Create adapter pointing to the in-process test client's base URL
    adapter = ServiceAdapterClient(service_url=str(test_client.base_url))

    # Set a sync MockTransport that forwards requests to the FastAPI TestClient
    forward = _make_forward(test_client)
    adapter._http_client.set_httpx_client(
        httpx.Client(base_url=str(test_client.base_url), transport=httpx.MockTransport(forward))
    )

    # Call through adapter (this performs an in-process HTTP request to the app)
    msgs = list(adapter.get_messages(max_results=5))
    assert len(msgs) == 1
    assert msgs[0].id == "m1"
    assert msgs[0].subject == "Hello"
    mock_gmail_client.get_messages.assert_called_once_with(max_results=5)


@pytest.mark.circleci
def test_get_message_via_adapter(test_client: TestClient, mock_gmail_client: MagicMock) -> None:
    """Adapter.get_message should return the message provided by the mocked gmail client via service."""
    mock_msg = _make_message("m2", "Detail", "bob@example.com", "2025-10-04", body="body text")
    mock_gmail_client.get_message.return_value = mock_msg

    adapter = ServiceAdapterClient(service_url=str(test_client.base_url))
    forward = _make_forward(test_client)
    adapter._http_client.set_httpx_client(
        httpx.Client(base_url=str(test_client.base_url), transport=httpx.MockTransport(forward))
    )

    msg = adapter.get_message("m2")
    assert msg.id == "m2"
    assert msg.body == "body text"
    mock_gmail_client.get_message.assert_called_once_with("m2")


@pytest.mark.circleci
def test_mark_as_read_and_delete_via_adapter(test_client: TestClient, mock_gmail_client: MagicMock) -> None:
    """Adapter.mark_as_read and Adapter.delete_message should delegate correctly to the mocked gmail client."""
    mock_gmail_client.mark_as_read.return_value = True
    mock_gmail_client.delete_message.return_value = True

    adapter = ServiceAdapterClient(service_url=str(test_client.base_url))
    forward = _make_forward(test_client)
    adapter._http_client.set_httpx_client(
        httpx.Client(base_url=str(test_client.base_url), transport=httpx.MockTransport(forward))
    )

    assert adapter.mark_as_read("m3") is True
    mock_gmail_client.mark_as_read.assert_called_once_with("m3")

    assert adapter.delete_message("m4") is True
    mock_gmail_client.delete_message.assert_called_once_with("m4")
