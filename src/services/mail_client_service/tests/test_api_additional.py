"""Additional unit tests for mail_client_service to hit error branches.

These tests exercise the internal `get_mail_client` initialization logic and the
500-error exception handlers on the endpoints by overriding the FastAPI
dependency to return faulty clients.
"""

from typing import Never

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from mail_client_service import service


def test_get_mail_client_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """When mail_client_api.get_client returns a client, get_mail_client should return it."""

    class DummyClient:
        pass

    def fake_get_client(*, interactive: bool = False) -> DummyClient:
        return DummyClient()

    # Force re-initialization and patch the factory
    monkeypatch.setattr(service, "_client_instance", None)
    # Patch the mail_client_api attribute on the module to a simple object exposing get_client
    fake_module = type("M", (), {"get_client": staticmethod(fake_get_client)})()
    monkeypatch.setattr(service, "mail_client_api", fake_module)

    client = service.get_mail_client()
    assert isinstance(client, DummyClient)


def test_get_mail_client_failure_raises_http_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """If the underlying get_client raises, get_mail_client should raise HTTPException(503)."""

    def broken_get_client(*, interactive: bool = False) -> Never:
        msg = "nope"
        raise RuntimeError(msg)

    monkeypatch.setattr(service, "_client_instance", None)
    fake_module = type("M", (), {"get_client": staticmethod(broken_get_client)})()
    monkeypatch.setattr(service, "mail_client_api", fake_module)

    with pytest.raises(HTTPException) as exc:
        service.get_mail_client()

    assert exc.value.status_code == 503
    assert "Mail client initialization failed" in exc.value.detail


@pytest.mark.unit
def test_get_messages_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """If client.get_messages raises, endpoint returns 500 with detail."""

    class Faulty:
        def get_messages(self, max_results: int = 10) -> Never:
            msg = "boom"
            raise RuntimeError(msg)

    # Override dependency by setting attribute on the FastAPI app
    service.app.dependency_overrides[service.get_mail_client] = lambda: Faulty()
    client = TestClient(service.app)

    resp = client.get("/messages")
    assert resp.status_code == 500
    assert "Failed to retrieve messages" in resp.json().get("detail", "")


@pytest.mark.unit
def test_get_message_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """If client.get_message raises a generic exception, endpoint returns 500."""

    class Faulty:
        def get_message(self, message_id: str) -> Never:
            msg = "boom"
            raise RuntimeError(msg)

    service.app.dependency_overrides[service.get_mail_client] = lambda: Faulty()
    client = TestClient(service.app)

    resp = client.get("/messages/1")
    assert resp.status_code == 500
    assert "Failed to retrieve message" in resp.json().get("detail", "")


@pytest.mark.unit
def test_mark_as_read_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """If client.mark_as_read raises, endpoint returns 500."""

    class Faulty:
        def mark_as_read(self, message_id: str) -> Never:
            msg = "boom"
            raise RuntimeError(msg)

    service.app.dependency_overrides[service.get_mail_client] = lambda: Faulty()
    client = TestClient(service.app)

    resp = client.post("/messages/1/mark-as-read")
    assert resp.status_code == 500
    assert "Failed to mark message as read" in resp.json().get("detail", "")


@pytest.mark.unit
def test_delete_message_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """If client.delete_message raises, endpoint returns 500."""

    class Faulty:
        def delete_message(self, message_id: str) -> Never:
            msg = "boom"
            raise RuntimeError(msg)

    service.app.dependency_overrides[service.get_mail_client] = lambda: Faulty()
    client = TestClient(service.app)

    resp = client.delete("/messages/1")
    assert resp.status_code == 500
    assert "Failed to delete message" in resp.json().get("detail", "")
