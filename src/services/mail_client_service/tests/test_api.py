"""Unit tests for FastAPI mail client service endpoints."""

import pytest
from fastapi.testclient import TestClient

class FakeEmail:
    def __init__(self, id_, subject, from_, date, body=""):
        self.id = id_
        self.subject = subject
        self.from_ = from_
        self.date = date
        self.body = body


class FakeClient:
    def __init__(self):
        self.messages = [
            FakeEmail("1", "Hello", "alice@example.com", "2025-10-01", body="Email body"),
            FakeEmail("2", "World", "bob@example.com", "2025-10-02", body="Another body"),
        ]

    def get_messages(self, max_results=10):
        return self.messages[:max_results]

    def get_message(self, message_id):
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        raise Exception("Not found")

    def mark_as_read(self, message_id):
        for msg in self.messages:
            if msg.id == message_id:
                return True
        return False

    def delete_message(self, message_id):
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                del self.messages[i]
                return True
        return False


# Use the fake client
from src.services.mail_client_service import api

api.client = FakeClient() 

client_app = TestClient(api.app)


# --- Tests ---
@pytest.mark.unit 
def test_get_emails():
    response = client_app.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert "1" in data
    assert data["1"]["Subject"] == "Hello"
    assert data["2"]["From"] == "bob@example.com"

@pytest.mark.unit 
def test_get_email_contents_success():
    response = client_app.get("/messages/1")
    assert response.status_code == 200
    data = response.json()
    assert data["ID"] == "1"
    assert data["Body"] == "Email body"

@pytest.mark.unit 
def test_get_email_contents_not_found():
    response = client_app.get("/messages/999")
    assert response.status_code == 404

@pytest.mark.unit 
def test_mark_email_read_success():
    response = client_app.post("/messages/1/mark-as-read")
    assert response.status_code == 200
    assert response.json()["Status"] == "Success"

@pytest.mark.unit 
def test_mark_email_read_fail():
    response = client_app.post("/messages/999/mark-as-read")
    assert response.status_code == 404

@pytest.mark.unit 
def test_delete_email_success():
    response = client_app.delete("/messages/1")
    assert response.status_code == 200
    assert response.json()["Status"] == "Success"

@pytest.mark.unit 
def test_delete_email_fail():
    response = client_app.delete("/messages/999")
    assert response.status_code == 404
