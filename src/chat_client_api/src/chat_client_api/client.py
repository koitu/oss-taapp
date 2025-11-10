"""Core chat client contract definitions and factory placeholder."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from chat_client_api.message import Channel, ChatMessage

__all__ = ["Client", "get_client"]


class Client(ABC):
    """Abstract base class representing a chat client for messaging operations."""

    @abstractmethod
    def get_message(self, channel_id: str, message_id: str) -> ChatMessage:
        """Retrieve a specific message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to retrieve.

        Returns:
            ChatMessage: The requested message.

        Raises:
            ValueError: If the message is not found.

        """
        raise NotImplementedError

    @abstractmethod
    def get_messages(self, channel_id: str, max_results: int = 10) -> Iterator[ChatMessage]:
        """Retrieve recent messages from a channel.

        Args:
            channel_id: The ID of the channel to retrieve messages from.
            max_results: Maximum number of messages to retrieve (default: 10).

        Returns:
            Iterator[ChatMessage]: An iterator of messages from the channel.

        """
        raise NotImplementedError

    @abstractmethod
    def send_message(self, channel_id: str, content: str) -> ChatMessage:
        """Send a message to a channel.

        Args:
            channel_id: The ID of the channel to send the message to.
            content: The text content of the message.

        Returns:
            ChatMessage: The sent message.

        Raises:
            ValueError: If the message could not be sent.

        """
        raise NotImplementedError

    @abstractmethod
    def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a message from a channel.

        Args:
            channel_id: The ID of the channel containing the message.
            message_id: The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted, False otherwise.

        """
        raise NotImplementedError

    @abstractmethod
    def get_channels(self) -> Iterator[Channel]:
        """Retrieve all accessible channels.

        Returns:
            Iterator[Channel]: An iterator of available channels.

        """
        raise NotImplementedError

    @abstractmethod
    def get_channel(self, channel_id: str) -> Channel:
        """Retrieve information about a specific channel.

        Args:
            channel_id: The ID of the channel to retrieve.

        Returns:
            Channel: The requested channel.

        Raises:
            ValueError: If the channel is not found.

        """
        raise NotImplementedError


def get_client(user_id: str | None = None) -> Client:
    """Return an instance of a Chat Client.

    Args:
        user_id: Optional user ID for multi-user authentication.
                 If None, uses a default/service account.

    Returns:
        Client: An instance conforming to the Client contract.

    Raises:
        NotImplementedError: If the function is not overridden by an implementation.

    """
    raise NotImplementedError
