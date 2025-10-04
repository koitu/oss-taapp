import pytest
from fastapi.testclient import TestClient

from mail_client_service import api


# --- Fake client setup ---
class FakeMessage:
    def __init__(self, id_: str, subject: str, from_: str, date: str, body: str = "") -> None:
        self.id = id_
        self.subject = subject
        self.from_ = from_
        self.date = date
        self.body = body


class FakeClient:
    def __init__(self) -> None:
        self.messages = [
            FakeMessage("1", "Hello", "alice@example.com", "2025-10-01", body="Email body"),
            FakeMessage("2", "World", "bob@example.com", "2025-10-02", body="Another body"),
        ]

    def get_messages(self, max_results: int = 10) -> list[FakeMessage]:
        return self.messages[:max_results]

    def get_message(self, message_id: str) -> FakeMessage:
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        raise ValueError(f"Message {message_id} not found")

    def mark_as_read(self, message_id: str) -> bool:
        return any(msg.id == message_id for msg in self.messages)

    def delete_message(self, message_id: str) -> bool:
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                del self.messages[i]
                return True
        return False


# --- Pytest fixture for isolated overrides ---
@pytest.fixture
def client():
    def override_get_mail_client() -> FakeClient:
        return FakeClient()

    api.app.dependency_overrides[api.get_mail_client] = override_get_mail_client
    test_client = TestClient(api.app)
    yield test_client
    api.app.dependency_overrides.clear()


# --- Tests ---
@pytest.mark.unit
def test_get_messages_success(client):
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert data["messages"]["1"]["subject"] == "Hello"
    assert data["messages"]["2"]["from"] == "bob@example.com"


@pytest.mark.unit
def test_get_messages_with_max_results(client):
    response = client.get("/messages?max_results=1")
    assert response.status_code == 200
    assert response.json()["count"] == 1


@pytest.mark.unit
def test_get_message_success(client):
    response = client.get("/messages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["body"] == "Email body"


@pytest.mark.unit
def test_get_message_not_found(client):
    response = client.get("/messages/999")
    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.unit
def test_mark_as_read_success(client):
    response = client.post("/messages/1/mark-as-read")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.unit
def test_mark_as_read_not_found(client):
    response = client.post("/messages/999/mark-as-read")
    assert response.status_code == 404


@pytest.mark.unit
def test_delete_message_success(client):
    response = client.delete("/messages/1")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


@pytest.mark.unit
def test_delete_message_not_found(client):
    response = client.delete("/messages/999")
    assert response.status_code == 404


@pytest.mark.unit
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
