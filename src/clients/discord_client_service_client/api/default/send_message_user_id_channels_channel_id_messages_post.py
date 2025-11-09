from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.message_detail import MessageDetail
from ...models.send_message_request import SendMessageRequest
from ...types import Response


def _get_kwargs(
    guild_id: str,
    channel_id: str,
    *,
    body: SendMessageRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
              "url": f"/{guild_id}/channels/{channel_id}/messages",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | MessageDetail | None:
    if response.status_code == 200:
        response_200 = MessageDetail.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[HTTPValidationError | MessageDetail]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
) -> Response[HTTPValidationError | MessageDetail]:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        user_id (str):
        channel_id (str):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, MessageDetail]]
    """

    kwargs = _get_kwargs(
        guild_id=guild_id,
        channel_id=channel_id,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
) -> HTTPValidationError | MessageDetail | None:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        user_id (str):
        channel_id (str):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, MessageDetail]
    """

    return sync_detailed(
        guild_id=guild_id,
        channel_id=channel_id,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
) -> Response[HTTPValidationError | MessageDetail]:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        user_id (str):
        channel_id (str):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, MessageDetail]]
    """

    kwargs = _get_kwargs(
        guild_id=guild_id,
        channel_id=channel_id,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    guild_id: str,
    channel_id: str,
    *,
    client: AuthenticatedClient | Client,
    body: SendMessageRequest,
) -> HTTPValidationError | MessageDetail | None:
    """Send message to channel

     Send a message to a Discord channel.

    Args:
        user_id (str):
        channel_id (str):
        body (SendMessageRequest): Request to send a message.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, MessageDetail]
    """

    return (
        await asyncio_detailed(
            guild_id=guild_id,
            channel_id=channel_id,
            client=client,
            body=body,
        )
    ).parsed
