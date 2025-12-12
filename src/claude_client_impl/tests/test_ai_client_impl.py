"""Tests for the `claude_client_impl.ai_client` module."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime as real_datetime
from types import SimpleNamespace
from typing import Any

import pytest
from claude_client_impl.ai_client import AIClientImpl, MissingClaudeKeyError

DEFAULT_SUBJECT = "user"
DEFAULT_API_KEY = "sk-ant-test"
DEFAULT_INPUT_TOKENS = 5
DEFAULT_OUTPUT_TOKENS = 6
DEFAULT_ASSISTANT_RESPONSE = "ok-response"
DEFAULT_CONVERSATION_ID = "conv-123"
DEFAULT_CREATED_AT = "2025-01-01T00:00:00Z"
EXPECTED_SAVE_CALLS = 2


@dataclass
class FakeResponse:
    """Lightweight response data container used by the stubs."""

    content: str
    tokens_used: int
    conversation_id: str | None


class DummyMessages:
    """Collects message calls made by the client under test."""

    def __init__(self) -> None:
        """Initialise storage for recorded message payloads."""
        self.calls: list[dict[str, Any]] = []

    def create(self, **payload: Any) -> Any:
        """Record payload and return a fake Claude response."""
        self.calls.append(payload)
        return SimpleNamespace(
            content=[SimpleNamespace(text=DEFAULT_ASSISTANT_RESPONSE)],
            usage=SimpleNamespace(input_tokens=DEFAULT_INPUT_TOKENS, output_tokens=DEFAULT_OUTPUT_TOKENS),
        )


def _patch_anthropic_sdk(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, Any],
    *,
    subject: str,
    api_key: str,
) -> DummyMessages:
    """Patch Anthropic SDK interactions to use deterministic fakes."""

    def fake_get_claude_key(requested_subject: str) -> str:
        return api_key if requested_subject == subject else ""

    monkeypatch.setattr("claude_client_impl.ai_client.get_claude_key", fake_get_claude_key)

    dummy_messages = DummyMessages()

    class DummyAnthropic:
        def __init__(self, *, api_key: str) -> None:
            self.api_key = api_key
            self.messages = dummy_messages

    monkeypatch.setattr("claude_client_impl.ai_client.Anthropic", DummyAnthropic)
    captured["messages"] = dummy_messages
    return dummy_messages


def _patch_storage(monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]) -> None:
    """Patch storage helper functions to capture inputs."""

    def fake_save_conversation(**kwargs: Any) -> None:
        captured["saved"].append(kwargs)

    def fake_delete_conversation(conv_id: str) -> bool:
        captured.setdefault("deleted", set()).add(conv_id)
        return True

    def fake_get_conversation_data(conv_id: str) -> tuple[str, str, str] | None:
        captured["conversation_queries"].append(conv_id)
        return captured.get("conversation_lookup", {}).get(conv_id)

    def fake_get_response(content: str, tokens_used: int, conversation_id: str | None) -> FakeResponse:
        resp = FakeResponse(content=content, tokens_used=tokens_used, conversation_id=conversation_id)
        captured["responses"].append(resp)
        return resp

    def fake_get_conversation(
        conv_id: str,
        messages: list[tuple[str, str]],
        created_at: str,
    ) -> tuple[str, list[tuple[str, str]], str]:
        result = (conv_id, messages, created_at)
        captured["built_conversation"] = result
        return result

    monkeypatch.setattr("claude_client_impl.ai_client.save_conversation", fake_save_conversation)
    monkeypatch.setattr("claude_client_impl.ai_client.delete_conversation", fake_delete_conversation)
    monkeypatch.setattr("claude_client_impl.ai_client.get_conversation_data", fake_get_conversation_data)
    monkeypatch.setattr("claude_client_impl.ai_client.get_response", fake_get_response)
    monkeypatch.setattr("claude_client_impl.ai_client.get_conversation", fake_get_conversation)


def _patch_time_and_uuid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure datetime/uuid helpers return deterministic data."""

    class DummyDateTimeModule:
        UTC = UTC

        @staticmethod
        def now(tz: UTC) -> real_datetime:
            return real_datetime(2025, 1, 1, tzinfo=tz)

    monkeypatch.setattr("claude_client_impl.ai_client.datetime", DummyDateTimeModule)
    monkeypatch.setattr("claude_client_impl.ai_client.uuid", SimpleNamespace(uuid4=lambda: DEFAULT_CONVERSATION_ID))


def _install_common_stubs(
    monkeypatch: pytest.MonkeyPatch,
    *,
    subject: str = DEFAULT_SUBJECT,
    api_key: str = DEFAULT_API_KEY,
) -> dict[str, Any]:
    """Install baseline stubs for storage and Anthropic SDK interactions."""
    captured: dict[str, Any] = {"saved": [], "responses": [], "conversation_queries": []}
    _patch_anthropic_sdk(monkeypatch, captured, subject=subject, api_key=api_key)
    _patch_storage(monkeypatch, captured)
    _patch_time_and_uuid(monkeypatch)
    return captured


def test_compose_response_creates_conversation_and_saves(monkeypatch: pytest.MonkeyPatch) -> None:
    """New conversations should be created and persisted."""
    captured = _install_common_stubs(monkeypatch)

    client = AIClientImpl(subject="user")
    resp = client.compose_response(["hello there"])

    assert isinstance(resp, FakeResponse)
    assert resp.content == "ok-response"
    assert resp.tokens_used == DEFAULT_INPUT_TOKENS + DEFAULT_OUTPUT_TOKENS
    assert resp.conversation_id == DEFAULT_CONVERSATION_ID

    # create_conversation + final save -> two calls
    assert len(captured["saved"]) == EXPECTED_SAVE_CALLS


def test_compose_response_appends_existing_conversation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Continuing a conversation should append new messages."""
    captured = _install_common_stubs(monkeypatch)
    existing_messages = [{"role": "user", "content": "hi"}]
    captured["conversation_lookup"] = {
        DEFAULT_CONVERSATION_ID: (DEFAULT_SUBJECT, DEFAULT_CREATED_AT, json.dumps(existing_messages))
    }

    client = AIClientImpl(subject="user")
    client.compose_response(["new message"], conversation_id=DEFAULT_CONVERSATION_ID)

    # Should query for existing conversation
    assert DEFAULT_CONVERSATION_ID in captured["conversation_queries"]

    # Should pass existing + new messages to Claude
    messages_call = captured["messages"].calls[0]
    assert "messages" in messages_call
    sent_messages = messages_call["messages"]
    assert len(sent_messages) == 2  # existing + new


def test_compose_response_requires_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    """compose_response should raise ValueError for empty messages."""
    _install_common_stubs(monkeypatch)
    client = AIClientImpl(subject="user")

    with pytest.raises(ValueError, match="Messages list cannot be empty"):
        client.compose_response([])


def test_compose_response_propagates_api_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """API failures should surface as RuntimeError."""
    captured = _install_common_stubs(monkeypatch)

    def failing_create(**_payload: Any) -> None:
        error_msg = "API failure"
        raise RuntimeError(error_msg)

    captured["messages"].create = failing_create

    client = AIClientImpl(subject="user")
    with pytest.raises(RuntimeError, match="AI service failed"):
        client.compose_response(["hello"])


def test_create_conversation_handles_storage_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_conversation should raise RuntimeError on storage errors."""
    _install_common_stubs(monkeypatch)

    def failing_save(**_kwargs: Any) -> None:
        error_msg = "Storage error"
        raise RuntimeError(error_msg)

    monkeypatch.setattr("claude_client_impl.ai_client.save_conversation", failing_save)

    client = AIClientImpl(subject="user")
    with pytest.raises(RuntimeError, match="Could not create conversation"):
        client.create_conversation()


def test_get_conversation_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_conversation should retrieve and parse conversation data."""
    captured = _install_common_stubs(monkeypatch)
    messages = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    captured["conversation_lookup"] = {"conv-1": (DEFAULT_SUBJECT, DEFAULT_CREATED_AT, json.dumps(messages))}

    client = AIClientImpl(subject="user")
    result = client.get_conversation("conv-1")

    assert captured["built_conversation"] is not None
    assert result[0] == "conv-1"


def test_get_conversation_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_conversation should raise ValueError for missing conversations."""
    _install_common_stubs(monkeypatch)
    client = AIClientImpl(subject="user")

    with pytest.raises(ValueError, match="Conversation not found"):
        client.get_conversation("nonexistent")


def test_get_conversation_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_conversation should raise ValueError for malformed data."""
    captured = _install_common_stubs(monkeypatch)
    captured["conversation_lookup"] = {"conv-bad": (DEFAULT_SUBJECT, DEFAULT_CREATED_AT, "not-json")}

    client = AIClientImpl(subject="user")
    with pytest.raises(ValueError, match="Invalid conversation data"):
        client.get_conversation("conv-bad")


def test_delete_conversation_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """delete_conversation should remove conversations."""
    captured = _install_common_stubs(monkeypatch)
    client = AIClientImpl(subject="user")

    result = client.delete_conversation("conv-123")
    assert result is True
    assert "conv-123" in captured["deleted"]


def test_delete_conversation_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """delete_conversation should raise ValueError for missing conversations."""
    _install_common_stubs(monkeypatch)

    def fake_delete_returning_false(_conv_id: str) -> int:
        return 0

    monkeypatch.setattr("claude_client_impl.ai_client.delete_conversation", fake_delete_returning_false)

    client = AIClientImpl(subject="user")
    with pytest.raises(ValueError, match="Conversation not found"):
        client.delete_conversation("missing")


def test_missing_claude_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """AIClientImpl should raise MissingClaudeKeyError when no API key is set."""

    def fake_get_claude_key(_subject: str) -> str | None:
        return None

    monkeypatch.setattr("claude_client_impl.ai_client.get_claude_key", fake_get_claude_key)

    with pytest.raises(MissingClaudeKeyError):
        AIClientImpl(subject="user")
