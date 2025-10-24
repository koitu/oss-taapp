from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.http_validation_error import HTTPValidationError
from ...models.o_auth_init_response import OAuthInitResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    state: None | Unset | str = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_state: None | Unset | str
    if isinstance(state, Unset):
        json_state = UNSET
    else:
        json_state = state
    params["state"] = json_state

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/auth/login",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> HTTPValidationError | OAuthInitResponse | None:
    if response.status_code == 200:
        response_200 = OAuthInitResponse.from_dict(response.json())

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
) -> Response[HTTPValidationError | OAuthInitResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    state: None | Unset | str = UNSET,
) -> Response[HTTPValidationError | OAuthInitResponse]:
    """Initialize OAuth2 flow

     Initialize OAuth2 flow.

    Args:
        state (Union[None, Unset, str]): Optional state parameter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, OAuthInitResponse]]
    """

    kwargs = _get_kwargs(
        state=state,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    state: None | Unset | str = UNSET,
) -> HTTPValidationError | OAuthInitResponse | None:
    """Initialize OAuth2 flow

     Initialize OAuth2 flow.

    Args:
        state (Union[None, Unset, str]): Optional state parameter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, OAuthInitResponse]
    """

    return sync_detailed(
        client=client,
        state=state,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    state: None | Unset | str = UNSET,
) -> Response[HTTPValidationError | OAuthInitResponse]:
    """Initialize OAuth2 flow

     Initialize OAuth2 flow.

    Args:
        state (Union[None, Unset, str]): Optional state parameter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[HTTPValidationError, OAuthInitResponse]]
    """

    kwargs = _get_kwargs(
        state=state,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    state: None | Unset | str = UNSET,
) -> HTTPValidationError | OAuthInitResponse | None:
    """Initialize OAuth2 flow

     Initialize OAuth2 flow.

    Args:
        state (Union[None, Unset, str]): Optional state parameter

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[HTTPValidationError, OAuthInitResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            state=state,
        )
    ).parsed
