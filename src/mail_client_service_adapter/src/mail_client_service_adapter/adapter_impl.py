"""Service Adapter Implementation.

This module provides an adapter that implements the mail_client_api.Client interface
by wrapping the auto-generated OpenAPI client for the mail_client_service.

This demonstrates the Adapter Pattern: hiding network/HTTP complexity behind
a familiar local interface.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import mail_client_api
from mail_client_api.message import Message
from mail_client_service_client import Client as GeneratedClient
from mail_client_service_client.api.default import (
    delete_message_messages_message_id_delete,
    get_message_messages_message_id_get,
    get_messages_messages_get,
    mark_as_read_messages_message_id_mark_as_read_post,
)
from mail_client_service_client.models.message_detail import MessageDetail
from mail_client_service_client.models.messages_response import MessagesResponse

if TYPE_CHECKING:
    # Standard library
    from collections.abc import Iterator

    # Local / project imports used only for type hints
    from mail_client_service_client.models.error_response import ErrorResponse
    from mail_client_service_client.models.http_validation_error import HTTPValidationError


logger = logging.getLogger(__name__)


@dataclass
class ServiceMessage(Message):
    """Simple Message implementation for service adapter responses."""

    _id: str
    _subject: str
    _from: str
    _to: str
    _date: str
    _body: str

    @property
    def id(self) -> str:
        """Return the unique identifier of the message."""
        return self._id

    @property
    def from_(self) -> str:
        """Return the sender's email address."""
        return self._from

    @property
    def to(self) -> str:
        """Return the recipient's email address."""
        return self._to

    @property
    def date(self) -> str:
        """Return the date the message was sent."""
        return self._date

    @property
    def subject(self) -> str:
        """Return the subject line of the message."""
        return self._subject

    @property
    def body(self) -> str:
        """Return the plain text content of the message."""
        return self._body


class ServiceAdapterClient(mail_client_api.Client):
    """Adapter that wraps the auto-generated service client.

    This class implements the mail_client_api.Client interface by delegating
    to the auto-generated OpenAPI client. It translates between the HTTP/REST
    world and the local interface expected by our application.

    Attributes:
        service_url: Base URL of the mail service (e.g., http://localhost:8000)
        _http_client: The auto-generated HTTP client

    """

    def __init__(self, service_url: str = "http://localhost:8000") -> None:
        """Initialize the service adapter client.

        Args:
            service_url: Base URL of the running mail service

        """
        self.service_url = service_url
        self._http_client = GeneratedClient(base_url=service_url)
        logger.info("Initialized ServiceAdapterClient for %s", service_url)

    def get_message(self, message_id: str) -> Message:
        """Retrieve a specific message by its ID via the service.

        Args:
            message_id: The unique identifier of the message to retrieve.

        Returns:
            A Message object containing the email data.

        Raises:
            ValueError: If the message cannot be retrieved or doesn't exist.

        """
        logger.debug("Fetching message %s from service", message_id)

        response: MessageDetail | ErrorResponse | HTTPValidationError | None = (
            get_message_messages_message_id_get.sync(
                client=self._http_client,
                message_id=message_id,
            )
        )

        # Only proceed if response is actually a MessageDetail
        if not isinstance(response, MessageDetail) or response.id is None:
            msg = f"Failed to retrieve message {message_id} from service"
            raise ValueError(msg)

        # Convert the generated model to our Message interface
        return ServiceMessage(
            _id=response.id,
            _subject=response.subject or "",
            _from=response.from_ or "",
            _to="",  # Service doesn't provide 'to' field in current API
            _date=response.date or "",
            _body=response.body or "",
        )

    def delete_message(self, message_id: str) -> bool:
        """Delete a message via the service.

        Args:
            message_id: The unique identifier of the message to delete.

        Returns:
            True if the message was successfully deleted, False otherwise.

        """
        logger.debug("Deleting message %s via service", message_id)

        response = delete_message_messages_message_id_delete.sync(
            client=self._http_client,
            message_id=message_id,
        )

        return response is not None and hasattr(response, "status") and response.status == "success"

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read via the service.

        Args:
            message_id: The unique identifier of the message to mark as read.

        Returns:
            True if successful, False otherwise.

        """
        logger.debug("Marking message %s as read via service", message_id)

        response = mark_as_read_messages_message_id_mark_as_read_post.sync(
            client=self._http_client,
            message_id=message_id,
        )

        return response is not None and hasattr(response, "status") and response.status == "success"

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Retrieve messages from the service.

        Args:
            max_results: The maximum number of messages to retrieve.

        Yields:
            An iterator of Message objects.

        """
        logger.debug("Fetching up to %d messages from service", max_results)

        response: MessagesResponse | ErrorResponse | HTTPValidationError | None = (
            get_messages_messages_get.sync(
                client=self._http_client,
                max_results=max_results,
            )
        )

        # Check if response is valid and contains messages
        if not isinstance(response, MessagesResponse) or response.messages is None:
            logger.warning("No messages returned from service")
            return

        # Convert each message summary to a Message object
        for msg_id, msg_data in response.messages.additional_properties.items():
            # For the list view, we don't have the body, so we pass empty string
            yield ServiceMessage(
                _id=msg_id,
                _subject=msg_data.additional_properties.get("subject") or "",
                _from=msg_data.additional_properties.get("from") or "",
                _to="",  # Service doesn't provide 'to' field in current API
                _date=msg_data.additional_properties.get("date") or "",
                _body="",  # Body not included in list response
            )


def get_client_impl(service_url: str = "http://localhost:8000") -> mail_client_api.Client:
    """Create a service adapter client.

    Args:
        service_url: Base URL of the running mail service

    Returns:
        A Client implementation that talks to the service

    """
    return ServiceAdapterClient(service_url=service_url)


def register(service_url: str = "http://localhost:8000") -> None:
    """Register the service adapter as the default client implementation.

    Args:
        service_url: Base URL of the running mail service

    """
    # Provide a factory function matching the expected signature
    def _get_client_factory(*, interactive: bool = False) -> mail_client_api.Client:
        # interactive argument is accepted for API compatibility but not used by this adapter
        # keep a local reference to avoid unused-argument linter warnings
        _ = interactive
        return get_client_impl(service_url)

    mail_client_api.get_client = _get_client_factory
