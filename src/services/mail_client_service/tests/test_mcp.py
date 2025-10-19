"""Unit tests for MCP server implementation.

This module uses a fake client implementation to test MCP tools
such as fetching, reading, marking as read, and deleting messages.
"""

import json
from collections.abc import Generator
from typing import Any

import pytest
from fastmcp import Client
from mcp.types import TextContent

from mail_client_service import service

from .test_fake_mail import FakeMailClient


@pytest.fixture
def mcp_client() -> Generator[Client[Any], None, None]:
    """Fixture that provides an MCP client with a fake mail client override."""
    # Store original function
    original_client = service._client_instance  # noqa: SLF001

    # Replace with fake client
    service._client_instance = FakeMailClient()  # type: ignore[assignment]  # noqa: SLF001

    # Create MCP client for in-memory testing
    client = Client(service.mcp)

    yield client

    # Restore original
    service._client_instance = original_client  # noqa: SLF001


# Mark all tests as async
pytestmark = pytest.mark.asyncio


@pytest.mark.unit
async def test_get_messages_success(mcp_client: Client[Any]) -> None:
    """Test retrieving all messages returns expected results."""
    async with mcp_client:
        result = await mcp_client.call_tool("get_messages", {})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["count"] == 2
        assert data["messages"]["1"]["subject"] == "Hello"
        assert data["messages"]["2"]["from"] == "bob@example.com"


@pytest.mark.unit
async def test_get_messages_with_max_results(mcp_client: Client[Any]) -> None:
    """Test retrieving messages with max_results parameter works correctly."""
    async with mcp_client:
        result = await mcp_client.call_tool("get_messages", {"max_results": 1})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["count"] == 1


@pytest.mark.unit
async def test_get_messages_invalid_max_results_too_low(mcp_client: Client[Any]) -> None:
    """Test get_messages with max_results below valid range."""
    async with mcp_client:
        result = await mcp_client.call_tool("get_messages", {"max_results": 0})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert "error" in data
        assert data["error"] == "max_results must be between 1 and 100"


@pytest.mark.unit
async def test_get_messages_invalid_max_results_too_high(mcp_client: Client[Any]) -> None:
    """Test get_messages with max_results above valid range."""
    async with mcp_client:
        result = await mcp_client.call_tool("get_messages", {"max_results": 101})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert "error" in data
        assert data["error"] == "max_results must be between 1 and 100"


@pytest.mark.unit
async def test_get_message_success(mcp_client: Client[Any]) -> None:
    """Test retrieving a single message by ID succeeds."""
    async with mcp_client:
        result = await mcp_client.call_tool("get_message", {"message_id": "1"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["id"] == "1"
        assert data["subject"] == "Hello"
        assert data["body"] == "Email body"


@pytest.mark.unit
async def test_get_message_not_found(mcp_client: Client[Any]) -> None:
    """Test retrieving a non-existent message returns error."""
    async with mcp_client:
        result = await mcp_client.call_tool("get_message", {"message_id": "999"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert "error" in data
        assert "Message not found" in data["error"]
        assert data["id"] == "999"


@pytest.mark.unit
async def test_mark_as_read_success(mcp_client: Client[Any]) -> None:
    """Test marking a message as read succeeds."""
    async with mcp_client:
        result = await mcp_client.call_tool("mark_read", {"message_id": "1"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["status"] == "success"
        assert "1 marked as read" in data["message"]


@pytest.mark.unit
async def test_mark_as_read_not_found(mcp_client: Client[Any]) -> None:
    """Test marking a non-existent message as read returns error."""
    async with mcp_client:
        result = await mcp_client.call_tool("mark_read", {"message_id": "999"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["status"] == "error"
        assert "Message not found or operation failed" in data["message"]


@pytest.mark.unit
async def test_delete_message_success(mcp_client: Client[Any]) -> None:
    """Test deleting a message by ID succeeds."""
    async with mcp_client:
        result = await mcp_client.call_tool("delete", {"message_id": "1"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["status"] == "success"
        assert "1 deleted successfully" in data["message"]


@pytest.mark.unit
async def test_delete_message_not_found(mcp_client: Client[Any]) -> None:
    """Test deleting a non-existent message returns error."""
    async with mcp_client:
        result = await mcp_client.call_tool("delete", {"message_id": "999"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)

        assert data["status"] == "error"
        assert "Message not found or operation failed" in data["message"]


@pytest.mark.unit
async def test_list_tools(mcp_client: Client[Any]) -> None:
    """Test that all tools are registered with MCP."""
    async with mcp_client:
        tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in tools]

        assert "get_messages" in tool_names
        assert "get_message" in tool_names
        assert "mark_read" in tool_names
        assert "delete" in tool_names
        assert len(tool_names) == 4


@pytest.mark.unit
async def test_operations_with_empty_message_id(mcp_client: Client[Any]) -> None:
    """Test operations with empty message ID return appropriate errors."""
    async with mcp_client:
        # Test get_message with empty ID
        result = await mcp_client.call_tool("get_message", {"message_id": ""})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert "error" in data

        # Test mark_read with empty ID
        result = await mcp_client.call_tool("mark_read", {"message_id": ""})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["status"] == "error"

        # Test delete with empty ID
        result = await mcp_client.call_tool("delete", {"message_id": ""})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["status"] == "error"


@pytest.mark.unit
async def test_full_workflow(mcp_client: Client[Any]) -> None:
    """Test a complete workflow: get messages, get details, mark read, delete."""
    async with mcp_client:
        # Step 1: Get messages
        result = await mcp_client.call_tool("get_messages", {"max_results": 5})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["count"] == 2

        # Step 2: Get message details
        result = await mcp_client.call_tool("get_message", {"message_id": "1"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["id"] == "1"
        assert data["body"] == "Email body"

        # Step 3: Mark as read
        result = await mcp_client.call_tool("mark_read", {"message_id": "1"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["status"] == "success"

        # Step 4: Delete
        result = await mcp_client.call_tool("delete", {"message_id": "1"})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["status"] == "success"

        # Verify deletion - should only have 1 message left
        result = await mcp_client.call_tool("get_messages", {})
        content = result.content[0]
        assert isinstance(content, TextContent)
        data = json.loads(content.text)
        assert data["count"] == 1
        assert "2" in data["messages"]
        assert "1" not in data["messages"]
