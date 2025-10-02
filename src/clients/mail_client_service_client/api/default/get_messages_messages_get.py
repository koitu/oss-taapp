from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.messages_response import MessagesResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    max_results: Union[Unset, int] = 10,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["max_results"] = max_results

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/messages",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]:
    if response.status_code == 200:
        response_200 = MessagesResponse.from_dict(response.json())

        return response_200

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if response.status_code == 500:
        response_500 = ErrorResponse.from_dict(response.json())

        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    max_results: Union[Unset, int] = 10,
) -> Response[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]:
    """Get message list

     Retrieve a list of email message summaries from the inbox

    Args:
        max_results (Union[Unset, int]): Maximum number of messages to retrieve Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]
    """

    kwargs = _get_kwargs(
        max_results=max_results,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    max_results: Union[Unset, int] = 10,
) -> Optional[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]:
    """Get message list

     Retrieve a list of email message summaries from the inbox

    Args:
        max_results (Union[Unset, int]): Maximum number of messages to retrieve Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, HTTPValidationError, MessagesResponse]
    """

    return sync_detailed(
        client=client,
        max_results=max_results,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    max_results: Union[Unset, int] = 10,
) -> Response[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]:
    """Get message list

     Retrieve a list of email message summaries from the inbox

    Args:
        max_results (Union[Unset, int]): Maximum number of messages to retrieve Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]
    """

    kwargs = _get_kwargs(
        max_results=max_results,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    max_results: Union[Unset, int] = 10,
) -> Optional[Union[ErrorResponse, HTTPValidationError, MessagesResponse]]:
    """Get message list

     Retrieve a list of email message summaries from the inbox

    Args:
        max_results (Union[Unset, int]): Maximum number of messages to retrieve Default: 10.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Union[ErrorResponse, HTTPValidationError, MessagesResponse]
    """

    return (
        await asyncio_detailed(
            client=client,
            max_results=max_results,
        )
    ).parsed
