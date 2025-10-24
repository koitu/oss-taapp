from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.auth_status_auth_status_user_id_get_response_auth_status_auth_status_user_id_get import (
    AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet,
)
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    user_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/auth/status/{user_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet.from_dict(response.json())

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
) -> Response[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet | HTTPValidationError]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet | HTTPValidationError]:
    """Check authentication status

     Check if user is authenticated.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet | HTTPValidationError | None:
    """Check authentication status

     Check if user is authenticated.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet, HTTPValidationError]
    """

    return sync_detailed(
        user_id=user_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet | HTTPValidationError]:
    """Check authentication status

     Check if user is authenticated.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet, HTTPValidationError]]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    user_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet | HTTPValidationError | None:
    """Check authentication status

     Check if user is authenticated.

    Args:
        user_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[AuthStatusAuthStatusUserIdGetResponseAuthStatusAuthStatusUserIdGet, HTTPValidationError]
    """

    return (
        await asyncio_detailed(
            user_id=user_id,
            client=client,
        )
    ).parsed
