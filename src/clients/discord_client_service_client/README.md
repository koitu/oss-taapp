# discord-client-service-client

A generated client library for interacting with Discord Client Service APIs.

## Overview

This package provides a small, typed HTTP client wrapper around the Discord Client Service. It exposes a thin runtime `Client` (and an `AuthenticatedClient`) that manage underlying `httpx` clients and convenience modules for each API path.

The library is generated to match an OpenAPI specification.

## Usage

```python
from discord_client_service_client import Client
from discord_client_service_client.api.default import get_messages_user_id_channels_channel_id_messages_get

async def main():
    async with Client(base_url="http://localhost:8000") as client:
        messages = await get_messages_user_id_channels_channel_id_messages_get.asyncio(
            client=client,
            user_id="12345",
            channel_id="67890"
        )
        print(messages)
```

## Components

- `Client` — non-authenticated client
- `AuthenticatedClient` — client that injects an Authorization header
- `discord_client_service_client.models` — typed model classes
- `discord_client_service_client.api` — API endpoint functions
- `discord_client_service_client.errors.UnexpectedStatus` — exception for undocumented status codes
