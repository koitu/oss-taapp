# mail-client-service-client

A generated client library for interacting with Mail Client Service APIs.

## Overview

This package provides a small, typed HTTP client wrapper around the Mail Client Service. It exposes a thin runtime `Client` (and an `AuthenticatedClient`) that manage underlying `httpx` clients and convenience modules for each API path.

The library is generated to match an OpenAPI specification. Each path + method pair is a Python module under `mail_client_service_client.api` that exposes four functions: `sync`, `sync_detailed`, `asyncio` and `asyncio_detailed`.

## Scope

- Provide a convenient, typed programmatic interface to the Mail Client Service REST API.
- Keep a small runtime surface: client objects, typed models, API modules, and a small error class for unexpected responses.
- Do not implement business logic; this package only concerns transport and data (models).

## Exposed interfaces

Top-level exports (from `mail_client_service_client`):

- `Client` — a non-authenticated client wrapper. Construct with `Client(base_url=...)`.
- `AuthenticatedClient` — client that injects an Authorization header. Construct with `AuthenticatedClient(base_url=..., token=...)`.

Other important packages and locations:

- `mail_client_service_client.models` — typed model classes for request/response bodies (e.g. `MessageDetail`, `MessagesResponse`).
- `mail_client_service_client.api` — modules mirroring API tags and paths. For tagless operations the functions live in `mail_client_service_client.api.default` (for example: `mail_client_service_client.api.default.get_messages_messages_get`).
- `mail_client_service_client.errors.UnexpectedStatus` — exception raised when a response status is undocumented and `Client.raise_on_unexpected_status` is True.
- `mail_client_service_client.types.Response[T]` — a typed response wrapper used by `*_detailed` methods to include raw metadata like status code and headers.

See the package `__init__.py` and `client.py` for full docstrings and available keyword args.

## Usage patterns

All examples use absolute imports.

1. Simple, synchronous request (blocking)

```python
from mail_client_service_client import Client
from mail_client_service_client.api.default import get_messages_messages_get

client = Client(base_url="https://api.example.com")

with client as client:
    messages = get_messages_messages_get.sync(client=client)
    # `messages` will be the parsed model (or None if the server returned no documented body)
```

2. Authenticated client

```python
from mail_client_service_client import AuthenticatedClient
from mail_client_service_client.api.default import get_message_messages_message_id_get

client = AuthenticatedClient(base_url="https://api.example.com", token="SuperSecretToken")

with client as client:
    message = get_message_messages_message_id_get.sync(client=client, message_id="abc123")
```

3. Async usage

```python
from mail_client_service_client import Client
from mail_client_service_client.api.default import get_messages_messages_get
import asyncio

async def main():
    async with Client(base_url="https://api.example.com") as client:
        messages = await get_messages_messages_get.asyncio(client=client)

asyncio.run(main())
```

4. Using the detailed variants to access status and headers

```python
from mail_client_service_client import Client
from mail_client_service_client.api.default import get_messages_messages_get
from mail_client_service_client.types import Response

client = Client(base_url="https://api.example.com")

with client as client:
    detailed: Response = get_messages_messages_get.sync_detailed(client=client)
    print(detailed.status_code, detailed.headers)
    parsed = detailed.parsed  # typed model or None
```

5. Customizing the underlying httpx client

```python
import httpx
from mail_client_service_client import Client

client = Client(base_url="https://api.example.com")
# Replace the internal httpx client (overrides cookies/headers/timeouts)
client.set_httpx_client(httpx.Client(base_url="https://api.example.com", proxies="http://localhost:8030"))
```

## Error handling

- If `Client.raise_on_unexpected_status` is set to True, API functions will raise `mail_client_service_client.errors.UnexpectedStatus` for undocumented status codes. The exception includes `.status_code` and `.content` attributes.
- Timeouts and transport errors are raised as `httpx` exceptions (for example `httpx.TimeoutException`).

## Component dependencies

- Runtime:

  - Python 3.8+ (the source may use newer typing features; check `pyproject.toml` for the exact requirement)
  - `httpx` — HTTP client used for sync/async requests
  - `attrs` — lightweight data classes used for `Client`/`AuthenticatedClient`

- Development / packaging:
  - Poetry (project uses Poetry; see `pyproject.toml` under this package)

Check the local `pyproject.toml` in this directory for pinned versions.

## Building & publishing

This package follows a typical Poetry workflow:

1. Update metadata in `pyproject.toml` (authors, version).
2. If using a private repository, configure it with Poetry (repositories/http-basic config).
3. Publish with `poetry publish --build` (or `--build -r <repo>` for alternate repositories).

For local development you can install the built wheel or add the path with Poetry.

## Notes and tips

- The generated API modules are small and deterministic. Look under `mail_client_service_client.api` to find functions matching the server paths you need to call.
- Prefer the `*_detailed` functions when you need raw status/headers; prefer the plain `sync`/`asyncio` helpers if you only need parsed models.
- Keep `verify_ssl=True` in production; only disable for local testing with trusted test servers.
