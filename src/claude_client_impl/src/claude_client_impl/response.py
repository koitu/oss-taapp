"""Response and conversation data structures for Claude client."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Response:
    """Response data from AI model."""

    content: str
    tokens_used: int
    conversation_id: str | None


@dataclass
class Conversation:
    """Conversation with history."""

    id: str
    messages: list[tuple[str, str]]  # List of (role, content) tuples
    created_at: str


def get_response(content: str, tokens_used: int, conversation_id: str | None) -> Response:
    """Create a Response object."""
    return Response(content=content, tokens_used=tokens_used, conversation_id=conversation_id)


def get_conversation(conv_id: str, messages: list[tuple[str, str]], created_at: str) -> Conversation:
    """Create a Conversation object."""
    return Conversation(id=conv_id, messages=messages, created_at=created_at)
