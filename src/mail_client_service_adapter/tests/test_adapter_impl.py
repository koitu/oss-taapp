import pytest
from unittest.mock import patch, MagicMock

from mail_client_service_adapter.adapter_impl import ServiceAdapterClient, ServiceMessage
from mail_client_service_client.models.message_detail import MessageDetail
from mail_client_service_client.models.messages_response import MessagesResponse
from mail_client_service_client.models.operation_response import OperationResponse


@pytest.fixture
def adapter():
    """Fixture for a ServiceAdapterClient instance."""
    return ServiceAdapterClient(service_url="http://testserver")


# ---------------------------------------------------------------------------
# get_message()
# ---------------------------------------------------------------------------

@patch("mail_client_service_adapter.adapter_impl.get_message_messages_message_id_get")
def test_get_message_success(mock_get, adapter):
    """It should convert a successful service response into a Message object."""
    mock_get.sync.return_value = MessageDetail(
        id="123",
        subject="Hello World",
        from_="alice@example.com",
        date="2025-01-01",
        body="Test body",
    )

    msg = adapter.get_message("123")

    assert isinstance(msg, ServiceMessage)
    assert msg.id == "123"
    assert msg.subject == "Hello World"
    assert msg.from_ == "alice@example.com"
    assert msg.body == "Test body"
    mock_get.sync.assert_called_once()


@patch("mail_client_service_adapter.adapter_impl.get_message_messages_message_id_get")
def test_get_message_invalid_response_raises(mock_get, adapter):
    """It should raise ValueError when the response is not a valid MessageDetail."""
    mock_get.sync.return_value = None
    with pytest.raises(ValueError):
        adapter.get_message("doesnotexist")


# ---------------------------------------------------------------------------
# delete_message()
# ---------------------------------------------------------------------------

@patch("mail_client_service_adapter.adapter_impl.delete_message_messages_message_id_delete")
def test_delete_message_success(mock_delete, adapter):
    """It should return True when delete operation succeeds."""
    mock_delete.sync.return_value = OperationResponse(status="success", message="Deleted")
    result = adapter.delete_message("123")
    assert result is True


@patch("mail_client_service_adapter.adapter_impl.delete_message_messages_message_id_delete")
def test_delete_message_failure(mock_delete, adapter):
    """It should return False when delete operation fails."""
    mock_delete.sync.return_value = OperationResponse(status="failure", message="Error")
    result = adapter.delete_message("123")
    assert result is False


# ---------------------------------------------------------------------------
# mark_as_read()
# ---------------------------------------------------------------------------

@patch("mail_client_service_adapter.adapter_impl.mark_as_read_messages_message_id_mark_as_read_post")
def test_mark_as_read_success(mock_post, adapter):
    """It should return True when mark-as-read operation succeeds."""
    mock_post.sync.return_value = OperationResponse(status="success", message="OK")
    assert adapter.mark_as_read("123") is True


@patch("mail_client_service_adapter.adapter_impl.mark_as_read_messages_message_id_mark_as_read_post")
def test_mark_as_read_failure(mock_post, adapter):
    """It should return False when mark-as-read fails."""
    mock_post.sync.return_value = OperationResponse(status="failure", message="Bad request")
    assert adapter.mark_as_read("123") is False


# ---------------------------------------------------------------------------
# get_messages()
# ---------------------------------------------------------------------------

@patch("mail_client_service_adapter.adapter_impl.get_messages_messages_get")
def test_get_messages_success(mock_get, adapter):
    """It should yield Message objects from a valid MessagesResponse."""
    fake_response = MessagesResponse(messages=MagicMock(), count=1)
    fake_response.messages.additional_properties = {
        "1": MagicMock(additional_properties={"subject": "Hi", "from": "bob@example.com", "date": "2025-01-01"})
    }

    mock_get.sync.return_value = fake_response

    messages = list(adapter.get_messages(max_results=1))
    assert len(messages) == 1
    msg = messages[0]
    assert isinstance(msg, ServiceMessage)
    assert msg.subject == "Hi"
    assert msg.from_ == "bob@example.com"


@patch("mail_client_service_adapter.adapter_impl.get_messages_messages_get")
def test_get_messages_invalid_response(mock_get, adapter):
    """It should yield nothing when service returns invalid response."""
    mock_get.sync.return_value = None
    assert list(adapter.get_messages()) == []
