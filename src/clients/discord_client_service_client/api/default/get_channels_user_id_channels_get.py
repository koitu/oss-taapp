from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.channel_list_response import ChannelListResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    guild_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/guilds/{guild_id}/channels",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ChannelListResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = ChannelListResponse.from_dict(response.json())

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
) -> Response[ChannelListResponse | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    guild_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ChannelListResponse | HTTPValidationError]:
    """Get user channels

     Get list of Discord channels accessible to the user.

    Args:
        guild_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ChannelListResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        guild_id=guild_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    guild_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ChannelListResponse | HTTPValidationError | None:
    """Get user channels

     Get list of Discord channels accessible to the user.

    Args:
        guild_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ChannelListResponse, HTTPValidationError]
    """

    return sync_detailed(
        guild_id=guild_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    guild_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[ChannelListResponse | HTTPValidationError]:
    """Get user channels

     Get list of Discord channels accessible to the user.

    Args:
        guild_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ChannelListResponse, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        guild_id=guild_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    guild_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> ChannelListResponse | HTTPValidationError | None:
    """Get user channels

     Get list of Discord channels accessible to the user.

    Args:
        guild_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ChannelListResponse, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            guild_id=guild_id,
            client=client,
        )
    ).parsed
