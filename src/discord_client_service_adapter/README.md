# Discord Client Service Adapter

This package provides an adapter that implements the `chat_client_api.Client` interface by wrapping the auto-generated OpenAPI client for the Discord service.

## Purpose

The adapter allows user code to interact with Discord through a remote HTTP service while using the same interface as the local `DiscordClient` implementation. This demonstrates the Adapter pattern and service-oriented architecture.

## Usage

```python
from discord_client_service_adapter import ServiceAdapterClient

# Create adapter pointing to running service
client = ServiceAdapterClient(
    service_url="http://localhost:8000",
    user_id="my_user_id"
)

# Use the same interface as local DiscordClient
messages = list(client.get_messages(channel_id="123456", max_results=10))
client.send_message(channel_id="123456", content="Hello from adapter!")
```

## Architecture

```
User Code → ServiceAdapterClient → Generated HTTP Client → FastAPI Service → DiscordClient
```

The adapter translates between:
- The local `chat_client_api.Client` interface (Python objects, iterators)
- The remote HTTP API (JSON requests/responses, status codes)

## Dependencies

- `chat-client-api`: Defines the Client interface this adapter implements
- `discord-client-service-client`: Auto-generated HTTP client from OpenAPI spec
- `httpx`: HTTP client library used by the generated client
