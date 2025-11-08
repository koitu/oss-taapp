"""API endpoints for Discord operations and OAuth2 flow."""

import logging

from chat_client_api.exceptions import MessageDeleteError, MessageNotFoundError
from discord_client_impl.auth_helper import (
    check_user_authenticated,
    delete_user_credentials,
    get_client_for_user,
    store_user_credentials,
)
from discord_client_impl.discord_impl import DiscordClient
from fastapi import HTTPException, Query, status
from pydantic import BaseModel, Field

from discord_client_service.service import app

logger = logging.getLogger(__name__)


# Pydantic models
class OAuthInitResponse(BaseModel):
    """OAuth2 initialization response."""

    authorization_url: str = Field(..., description="URL to redirect user for OAuth")
    state: str = Field(..., description="CSRF protection state parameter")


class OAuthCallbackRequest(BaseModel):
    """OAuth2 callback request."""

    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str | None = Field(None, description="State parameter for CSRF validation")
    user_id: str = Field(..., description="User ID to associate with credentials")


class OAuthCallbackResponse(BaseModel):
    """OAuth2 callback response."""

    status: str = Field(..., description="Status message")
    user_id: str = Field(..., description="User ID credentials were stored for")


class MessageDetail(BaseModel):
    """Discord message details."""

    id: str = Field(..., description="Message ID")
    channel_id: str = Field(..., description="Channel ID")
    author_id: str = Field(..., description="Author user ID")
    author_name: str = Field(..., description="Author display name")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    edited_timestamp: str | None = Field(None, description="Edit timestamp if edited")


class MessageListResponse(BaseModel):
    """List of Discord messages."""

    messages: list[MessageDetail] = Field(..., description="List of messages")
    count: int = Field(..., description="Number of messages returned")


class SendMessageRequest(BaseModel):
    """Request to send a message."""

    content: str = Field(..., min_length=1, max_length=2000, description="Message content")


class ChannelInfo(BaseModel):
    """Discord channel information."""

    id: str = Field(..., description="Channel ID")
    name: str = Field(..., description="Channel name")
    type: str = Field(..., description="Channel type")


class ChannelListResponse(BaseModel):
    """List of Discord channels."""

    channels: list[ChannelInfo] = Field(..., description="List of channels")
    count: int = Field(..., description="Number of channels returned")


class OperationResponse(BaseModel):
    """Generic operation response."""

    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Status message")


class ErrorResponse(BaseModel):
    """Error response."""

    detail: str = Field(..., description="Error details")


# OAuth2 Endpoints
@app.get(
    "/auth/login",
    response_model=OAuthInitResponse,
    summary="Initialize OAuth2 flow",
)
def oauth_login(
    state: str | None = Query(None, description="Optional state parameter"),
) -> OAuthInitResponse:
    """Initialize OAuth2 flow."""
    try:
        client = DiscordClient()
        auth_url, generated_state = client._get_authorization_url(state=state)
        logger.info("Generated OAuth authorization URL")
        return OAuthInitResponse(authorization_url=auth_url, state=generated_state)
    except Exception as e:
        logger.exception("Failed to generate authorization URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate authorization URL: {e}",
        ) from e


@app.post(
    "/auth/callback",
    response_model=OAuthCallbackResponse,
    summary="Handle OAuth2 callback",
)
async def oauth_callback(request: OAuthCallbackRequest) -> OAuthCallbackResponse:
    """Handle OAuth2 callback after user authorization."""
    try:
        client = DiscordClient()
        token_data = client._exchange_code_for_token(request.code)
        await store_user_credentials(user_id=request.user_id, token_data=token_data)
        logger.info("Successfully stored credentials for user: %s", request.user_id)
        return OAuthCallbackResponse(status="success", user_id=request.user_id)
    except ValueError as e:
        logger.exception("Token exchange failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token exchange failed: {e}",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error during OAuth callback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {e}",
        ) from e


@app.delete(
    "/auth/logout/{user_id}",
    response_model=OperationResponse,
    summary="Logout user",
)
async def oauth_logout(user_id: str) -> OperationResponse:
    """Logout user by deleting stored credentials."""
    try:
        deleted = await delete_user_credentials(user_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No credentials found for user: {user_id}",
            )
        logger.info("Successfully logged out user: %s", user_id)
        return OperationResponse(
            status="success", message=f"User {user_id} logged out successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Logout failed for user: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {e}",
        ) from e


@app.get(
    "/auth/status/{user_id}",
    response_model=dict[str, bool | str],
    summary="Check authentication status",
)
async def auth_status(user_id: str) -> dict[str, bool | str]:
    """Check if user is authenticated."""
    authenticated = await check_user_authenticated(user_id)
    return {"authenticated": authenticated, "user_id": user_id}


# Discord Message Endpoints
@app.get(
    "/{user_id}/channels/{channel_id}/messages",
    response_model=MessageListResponse,
    summary="Get messages from channel",
)
async def get_messages(
    user_id: str,
    channel_id: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum number of messages"),
) -> MessageListResponse:
    """Get messages from a Discord channel."""
    try:
        client = await get_client_for_user(user_id)
        messages = list(client.get_messages(channel_id=channel_id, max_results=limit))

        message_list = [
            MessageDetail(
                id=msg.id,
                channel_id=msg.channel_id,
                author_id=msg.author_id,
                author_name=msg.author_name,
                content=msg.content,
                timestamp=msg.timestamp,
                edited_timestamp=msg.edited_timestamp,
            )
            for msg in messages
        ]

        logger.info("Retrieved %d messages from channel %s", len(message_list), channel_id)
        return MessageListResponse(messages=message_list, count=len(message_list))

    except ValueError as e:
        logger.warning("User %s not authenticated: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to retrieve messages")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {e}",
        ) from e


@app.post(
    "/{user_id}/channels/{channel_id}/messages",
    response_model=MessageDetail,
    summary="Send message to channel",
)
async def send_message(
    user_id: str,
    channel_id: str,
    request: SendMessageRequest,
) -> MessageDetail:
    """Send a message to a Discord channel."""
    try:
        client = await get_client_for_user(user_id)
        sent_message = client.send_message(channel_id=channel_id, content=request.content)

        logger.info("Sent message to channel %s", channel_id)
        return MessageDetail(
            id=sent_message.id,
            channel_id=sent_message.channel_id,
            author_id=sent_message.author_id,
            author_name=sent_message.author_name,
            content=sent_message.content,
            timestamp=sent_message.timestamp,
            edited_timestamp=sent_message.edited_timestamp,
        )

    except ValueError as e:
        if "not authenticated" in str(e).lower():
            logger.warning("User %s not authenticated", user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User not authenticated: {e}",
            ) from e
        logger.exception("Failed to send message")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to send message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {e}",
        ) from e


@app.delete(
    "/{user_id}/channels/{channel_id}/messages/{message_id}",
    response_model=OperationResponse,
    summary="Delete message",
)
async def delete_message(
    user_id: str,
    channel_id: str,
    message_id: str,
) -> OperationResponse:
    """Delete a message from a Discord channel."""
    try:
        client = await get_client_for_user(user_id)
        client.delete_message(channel_id=channel_id, message_id=message_id)

        logger.info("Deleted message %s", message_id)
        return OperationResponse(status="success", message=f"Message {message_id} deleted")

    except MessageNotFoundError as e:
        logger.warning("Message %s not found", message_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except MessageDeleteError as e:
        logger.exception("Failed to delete message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e
    except ValueError as e:
        logger.warning("User %s not authenticated", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to delete message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete message: {e}",
        ) from e


# Discord Channel Endpoints
@app.get(
    "/{user_id}/channels",
    response_model=ChannelListResponse,
    summary="Get user channels",
)
async def get_channels(user_id: str) -> ChannelListResponse:
    """Get list of Discord channels accessible to the user."""
    try:
        client = await get_client_for_user(user_id)
        channels = list(client.get_channels())

        channel_list = [
            ChannelInfo(id=channel.id, name=channel.name, type=channel.channel_type)
            for channel in channels
        ]

        logger.info("Retrieved %d channels", len(channel_list))
        return ChannelListResponse(channels=channel_list, count=len(channel_list))

    except ValueError as e:
        logger.warning("User %s not authenticated", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to retrieve channels")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channels: {e}",
        ) from e


@app.get(
    "/{user_id}/channels/{channel_id}",
    response_model=ChannelInfo,
    summary="Get channel info",
)
async def get_channel(user_id: str, channel_id: str) -> ChannelInfo:
    """Get information about a specific Discord channel."""
    try:
        client = await get_client_for_user(user_id)
        channel = client.get_channel(channel_id=channel_id)

        logger.info("Retrieved channel %s", channel_id)
        return ChannelInfo(id=channel.id, name=channel.name, type=channel.channel_type)

    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Channel {channel_id} not found",
            ) from e
        logger.warning("User %s not authenticated", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User not authenticated: {e}",
        ) from e
    except Exception as e:
        logger.exception("Failed to retrieve channel")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve channel: {e}",
        ) from e
