"""FastAPI service for mail client operations.

This module provides a RESTful API wrapper around the mail_client_api components.
It exposes endpoints for fetching, reading, marking as read, and deleting email messages.
"""

import logging
from typing import Annotated

import gmail_client_impl  # noqa: F401 - Register implementation
import mail_client_api
from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Mail Client Service",
    description="RESTful API for email operations using Gmail",
    version="0.1.0",
)

# Global client instance (initialized lazily)
_client_instance: mail_client_api.Client | None = None


def get_mail_client() -> mail_client_api.Client:
    """Get or create the mail client instance (dependency injection).

    This function is used as a FastAPI dependency to provide the mail client
    to route handlers. It initializes the client lazily on first request.

    Returns:
        mail_client_api.Client: The mail client instance.

    Raises:
        HTTPException: If client initialization fails.

    """
    global _client_instance  # noqa: PLW0603
    if _client_instance is None:
        try:
            _client_instance = mail_client_api.get_client(interactive=False)
            logger.info("Mail client initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize mail client")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Mail client initialization failed: {e!s}",
            ) from e
    return _client_instance


# Response Models
class MessageSummary(BaseModel):
    """Summary information for an email message."""

    id: str = Field(..., description="Unique message identifier")
    subject: str | None = Field(None, description="Email subject line")
    from_: str | None = Field(None, alias="from", description="Sender email address")
    date: str | None = Field(None, description="Message date")


class MessageDetail(BaseModel):
    """Detailed information for an email message."""

    id: str = Field(..., description="Unique message identifier")
    subject: str | None = Field(None, description="Email subject line")
    from_: str | None = Field(None, alias="from", description="Sender email address")
    date: str | None = Field(None, description="Message date")
    body: str | None = Field(None, description="Email body content")


class MessagesResponse(BaseModel):
    """Response containing multiple message summaries."""

    messages: dict[str, dict[str, str | None]] = Field(
        ...,
        description="Dictionary mapping message IDs to their summaries",
    )
    count: int = Field(..., description="Number of messages returned")


class OperationResponse(BaseModel):
    """Response for successful operations."""

    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")


class ErrorResponse(BaseModel):
    """Response for error conditions."""

    detail: str = Field(..., description="Error message")


# Endpoints
@app.get(
    "/messages",
    response_model=MessagesResponse,
    responses={
        200: {"description": "Successfully retrieved messages"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get message list",
    description="Retrieve a list of email message summaries from the inbox",
)
def get_messages(
    max_results: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of messages to retrieve",
    ),
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)] = None,  # type: ignore[assignment]
) -> MessagesResponse:
    """Get the summary of recent emails.

    Args:
        max_results: Maximum number of messages to retrieve (1-100).
        client: Mail client instance (injected).

    Returns:
        Dictionary containing message summaries keyed by message ID.

    Raises:
        HTTPException: If message retrieval fails.

    """
    try:
        messages = list(client.get_messages(max_results=max_results))

        result: dict[str, dict[str, str | None]] = {}
        for msg in messages:
            result[msg.id] = {
                "subject": msg.subject,
                "from": msg.from_,
                "date": msg.date,
            }

        return MessagesResponse(messages=result, count=len(result))

    except Exception as e:
        logger.exception("Failed to retrieve messages")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {e!s}",
        ) from e


@app.get(
    "/messages/{message_id}",
    response_model=MessageDetail,
    responses={
        200: {"description": "Successfully retrieved message"},
        404: {"description": "Message not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get message details",
    description="Retrieve the full details of a specific email message",
)
def get_message(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)] = None,  # type: ignore[assignment]
) -> MessageDetail:
    """Get the full contents of a single email.

    Args:
        message_id: The unique identifier of the message to retrieve.
        client: Mail client instance (injected).

    Returns:
        Full message details including body content.

    Raises:
        HTTPException: If message is not found or retrieval fails.

    """
    try:
        msg = client.get_message(message_id)
        return MessageDetail(
            id=message_id,
            subject=msg.subject,
            from_=msg.from_,
            date=msg.date,
            body=msg.body,
        )

    except ValueError as e:
        logger.warning("Message not found: %s", message_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found: {message_id}",
        ) from e

    except Exception as e:
        logger.exception("Failed to retrieve message: %s", message_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve message: {e!s}",
        ) from e


@app.post(
    "/messages/{message_id}/mark-as-read",
    response_model=OperationResponse,
    responses={
        200: {"description": "Successfully marked as read"},
        404: {"description": "Message not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Mark message as read",
    description="Mark a specific email message as read",
)
def mark_as_read(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)] = None,  # type: ignore[assignment]
) -> OperationResponse:
    """Mark an email as read.

    Args:
        message_id: The unique identifier of the message to mark as read.
        client: Mail client instance (injected).

    Returns:
        Success status and message.

    Raises:
        HTTPException: If operation fails or message not found.

    """
    try:
        success = client.mark_as_read(message_id)
        if success:
            logger.info("Marked message as read: %s", message_id)
            return OperationResponse(
                status="success",
                message=f"Message {message_id} marked as read",
            )

        logger.warning("Failed to mark message as read: %s", message_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found or operation failed: {message_id}",
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Error marking message as read: %s", message_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as read: {e!s}",
        ) from e


@app.delete(
    "/messages/{message_id}",
    response_model=OperationResponse,
    responses={
        200: {"description": "Successfully deleted message"},
        404: {"description": "Message not found", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Delete message",
    description="Permanently delete a specific email message",
)
def delete_message(
    message_id: str,
    client: Annotated[mail_client_api.Client, Depends(get_mail_client)] = None,  # type: ignore[assignment]
) -> OperationResponse:
    """Delete an email permanently.

    Args:
        message_id: The unique identifier of the message to delete.
        client: Mail client instance (injected).

    Returns:
        Success status and message.

    Raises:
        HTTPException: If operation fails or message not found.

    Warning:
        This permanently deletes the message and cannot be undone.

    """
    try:
        success = client.delete_message(message_id)
        if success:
            logger.info("Deleted message: %s", message_id)
            return OperationResponse(
                status="success",
                message=f"Message {message_id} deleted successfully",
            )

        logger.warning("Failed to delete message: %s", message_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message not found or operation failed: {message_id}",
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.exception("Error deleting message: %s", message_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {e!s}",
        ) from e


@app.get(
    "/health",
    response_model=dict[str, str],
    summary="Health check",
    description="Check if the service is running",
)
def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status indicating service health.

    """
    return {"status": "healthy"}
