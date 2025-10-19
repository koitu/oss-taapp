"""Fake mail client implmentation.

This module defines a fake mail client that allows operations
such as fetching, reading, marking as read, and deleting messages.
"""


class FakeMessage:
    """Represents a simplified email message for testing."""

    def __init__(self, id_: str, subject: str, from_: str, date: str, body: str = "") -> None:
        """Initialize a fake message.

        Args:
            id_: Unique identifier for the message.
            subject: Email subject.
            from_: Sender email address.
            date: Date string.
            body: Message body content.

        """
        self.id = id_
        self.subject = subject
        self.from_ = from_
        self.date = date
        self.body = body


class FakeMailClient:
    """Fake client implementation to simulate mail client behavior."""

    def __init__(self) -> None:
        """Initialize the fake client with a predefined list of messages."""
        self.messages = [
            FakeMessage("1", "Hello", "alice@example.com", "2025-10-01", body="Email body"),
            FakeMessage("2", "World", "bob@example.com", "2025-10-02", body="Another body"),
        ]

    def get_messages(self, max_results: int = 10) -> list[FakeMessage]:
        """Return up to `max_results` messages."""
        return self.messages[:max_results]

    def get_message(self, message_id: str) -> FakeMessage:
        """Return a message by ID or raise ValueError if not found."""
        for msg in self.messages:
            if msg.id == message_id:
                return msg
        raise ValueError(f"Message {message_id} not found")

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read if it exists."""
        return any(msg.id == message_id for msg in self.messages)

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID, returning True if found and deleted."""
        for i, msg in enumerate(self.messages):
            if msg.id == message_id:
                del self.messages[i]
                return True
        return False
