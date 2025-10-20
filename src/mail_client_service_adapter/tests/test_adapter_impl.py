"""Unit tests for the ServiceAdapterClient implementation."""

from unittest.mock import MagicMock, patch

import pytest
from mail_client_service_client.models.message_detail import MessageDetail
from mail_client_service_client.models.messages_response import MessagesResponse
from mail_client_service_client.models.operation_response import OperationResponse

from mail_client_service_adapter.adapter_impl import ServiceAdapterClient, ServiceMessage


@pytest.fixture
def adapter() -> ServiceAdapterClient:
    """Fixture for a ServiceAdapterClient instance."""
    return ServiceAdapterClient(service_url="http://testserver")


@patch("mail_client_service_adapter.adapter_impl.get_message_messages_message_id_get")
def test_get_message_success(mock_get: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should convert a successful service response into a Message object."""
    mock_get.sync.return_value = MessageDetail(
        id="123",
        subject="Test subject",
        sender="user@example.com",
        body="Hello world",
        read=False,
    )

    message = adapter.get_message("123")

    assert isinstance(message, ServiceMessage)
    assert message.id == "123"
    assert message.subject == "Test subject"


@patch("mail_client_service_adapter.adapter_impl.get_message_messages_message_id_get")
def test_get_message_invalid_response_raises(mock_get: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should raise ValueError when the response is not a valid MessageDetail."""
    mock_get.sync.return_value = None

    with pytest.raises(ValueError, match="Invalid response from service"):
        adapter.get_message("doesnotexist")


@patch("mail_client_service_adapter.adapter_impl.delete_message_messages_message_id_delete")
def test_delete_message_success(mock_delete: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should return True when delete operation succeeds."""
    mock_delete.sync.return_value = OperationResponse(status="success", message="Deleted")

    result = adapter.delete_message("123")

    assert result is True


@patch("mail_client_service_adapter.adapter_impl.delete_message_messages_message_id_delete")
def test_delete_message_failure(mock_delete: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should return False when delete operation fails."""
    mock_delete.sync.return_value = OperationResponse(status="failure", message="Error")

    result = adapter.delete_message("123")

    assert result is False


@patch("mail_client_service_adapter.adapter_impl.mark_as_read_messages_message_id_mark_as_read_post")
def test_mark_as_read_success(mock_post: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should return True when mark-as-read operation succeeds."""
    mock_post.sync.return_value = OperationResponse(status="success", message="OK")

    result = adapter.mark_as_read("123")

    assert result is True


@patch("mail_client_service_adapter.adapter_impl.mark_as_read_messages_message_id_mark_as_read_post")
def test_mark_as_read_failure(mock_post: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should return False when mark-as-read fails."""
    mock_post.sync.return_value = OperationResponse(status="failure", message="Bad request")

    result = adapter.mark_as_read("123")

    assert result is False


@patch("mail_client_service_adapter.adapter_impl.get_messages_messages_get")
def test_get_messages_success(mock_get: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should yield Message objects from a valid MessagesResponse."""
    fake_message = MagicMock(id="1", subject="Hello", sender="a@example.com", body="Body", read=False)
    fake_response = MessagesResponse(messages=[fake_message], count=1)
    mock_get.sync.return_value = fake_response

    messages = list(adapter.get_messages())

    assert len(messages) == 1
    assert isinstance(messages[0], ServiceMessage)
    assert messages[0].subject == "Hello"


@patch("mail_client_service_adapter.adapter_impl.get_messages_messages_get")
def test_get_messages_invalid_response(mock_get: MagicMock, adapter: ServiceAdapterClient) -> None:
    """It should yield nothing when service returns invalid response."""
    mock_get.sync.return_value = None

    messages = list(adapter.get_messages())

    assert messages == []
