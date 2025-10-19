"""MCP server implementation for mail client operations.

This module provides an MCP (Model Context Protocol) server that exposes
mail client functionality as resources and tools that can be used by AI assistants.
"""

import logging
from typing import Any

from .service import get_mail_client, mcp

__all__ = ["mcp"]


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@mcp.tool()
def get_messages(max_results: int = 10) -> dict[str, Any]:
    """Get a list of recent email messages.

    Args:
        max_results: Maximum number of messages to retrieve (1-100). Default is 10.

    Returns:
        Dictionary containing message summaries with count and messages dict.
        Each message includes id, subject, from, and date.

    """
    try:
        # Validate max_results
        if max_results < 1 or max_results > 100:  # noqa: PLR2004
            return {"error": "max_results must be between 1 and 100", "count": 0, "messages": {}}

        mail_client = get_mail_client()
        messages = list(mail_client.get_messages(max_results=max_results))

        result: dict[str, dict[str, str | None]] = {}
        for msg in messages:
            result[msg.id] = {
                "subject": msg.subject,
                "from": msg.from_,
                "date": msg.date,
            }

        return {"count": len(result), "messages": result}

    except Exception as e:
        logger.exception("Failed to retrieve messages via MCP")
        return {"error": f"Failed to retrieve messages: {e!s}", "count": 0, "messages": {}}


@mcp.tool()
def get_message_resource(message_id: str) -> dict[str, Any]:
    """Get the full details of a specific email message as a resource.

    Args:
        message_id: The unique identifier of the message to retrieve.

    Returns:
        Dictionary containing full message details including id, subject,
        from, date, and body content.

    """
    try:
        mail_client = get_mail_client()
        msg = mail_client.get_message(message_id)

    except ValueError:
        logger.warning("Message not found via MCP resource: %s", message_id)
        return {"error": f"Message not found: {message_id}", "id": message_id}

    except Exception as e:
        logger.exception("Failed to retrieve message via MCP resource: %s", message_id)
        return {"error": f"Failed to retrieve message: {e!s}", "id": message_id}

    else:
        return {
            "id": message_id,
            "subject": msg.subject,
            "from": msg.from_,
            "date": msg.date,
            "body": msg.body,
        }


@mcp.tool()
def mark_read(message_id: str) -> dict[str, str]:
    """Mark an email message as read.

    Args:
        message_id: The unique identifier of the message to mark as read.

    Returns:
        Dictionary with status and message indicating success or failure.

    Example:
        {"status": "success", "message": "Message msg123 marked as read"}

    """
    try:
        mail_client = get_mail_client()
        success = mail_client.mark_as_read(message_id)

        if success:
            logger.info("Marked message as read via MCP: %s", message_id)
            return {"status": "success", "message": f"Message {message_id} marked as read"}

    except Exception as e:
        logger.exception("Error marking message as read via MCP: %s", message_id)
        return {"status": "error", "message": f"Failed to mark message as read: {e!s}"}

    else:
        logger.warning("Failed to mark message as read via MCP: %s", message_id)
        return {
            "status": "error",
            "message": f"Message not found or operation failed: {message_id}",
        }


@mcp.tool()
def delete(message_id: str) -> dict[str, str]:
    """Delete an email message permanently.

    WARNING: This permanently deletes the message and cannot be undone.

    Args:
        message_id: The unique identifier of the message to delete.

    Returns:
        Dictionary with status and message indicating success or failure.

    Example:
        {"status": "success", "message": "Message msg123 deleted successfully"}

    """
    try:
        mail_client = get_mail_client()
        success = mail_client.delete_message(message_id)

        if success:
            logger.info("Deleted message via MCP: %s", message_id)
            return {"status": "success", "message": f"Message {message_id} deleted successfully"}

    except Exception as e:
        logger.exception("Error deleting message via MCP: %s", message_id)
        return {"status": "error", "message": f"Failed to delete message: {e!s}"}

    else:
        logger.warning("Failed to delete message via MCP: %s", message_id)
        return {
            "status": "error",
            "message": f"Message not found or operation failed: {message_id}",
        }
