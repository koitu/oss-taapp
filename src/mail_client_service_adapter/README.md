# Mail Client Service Adapter

An adapter implementation that wraps the auto-generated OpenAPI client to implement the `mail_client_api.Client` interface.

## Overview

This package demonstrates the **Adapter Pattern** - it takes the auto-generated HTTP client (which talks to the FastAPI service) and wraps it behind the familiar `mail_client_api.Client` interface that the rest of our application expects.

## Architecture

```
┌─────────────────────────────────────┐
│   Application Code                   │
│   (uses mail_client_api.Client)     │
└─────────────┬───────────────────────┘
              │ Familiar Interface
              ▼
┌─────────────────────────────────────┐
│   ServiceAdapterClient               │
│   (Adapter Pattern)                  │
│   - Implements Client ABC            │
│   - Translates calls to HTTP         │
└─────────────┬───────────────────────┘
              │ HTTP/REST
              ▼
┌─────────────────────────────────────┐
│   Auto-Generated OpenAPI Client      │
│   (mail_client_service_client)       │
│   - Type-safe HTTP client            │
│   - Generated from OpenAPI spec      │
└─────────────┬───────────────────────┘
              │ HTTP Requests
              ▼
┌─────────────────────────────────────┐
│   Mail Client Service (FastAPI)      │
│   (Running on localhost:8000)        │
└─────────────┬───────────────────────┘
              │ Uses components
              ▼
┌─────────────────────────────────────┐
│   Gmail Client Implementation        │
│   (talks to Gmail API)               │
└──────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from mail_client_service_adapter import ServiceAdapterClient

# Create adapter pointing to service
client = ServiceAdapterClient(service_url="http://localhost:8000")

# Use it like any other mail_client_api.Client
messages = list(client.get_messages(max_results=5))
for msg in messages:
    print(f"Subject: {msg.subject}")
```

### With Dependency Injection

```python
import mail_client_service_adapter

# Register as the default implementation
mail_client_service_adapter.register(service_url="http://localhost:8000")

# Now anywhere in your code:
import mail_client_api
client = mail_client_api.get_client()

# This will use the ServiceAdapterClient!
messages = list(client.get_messages())
```

## Key Benefits

1. **Transparent Network Calls**: Application code doesn't know it's making HTTP requests
2. **Swappable Implementations**: Can easily switch between direct Gmail access and service access
3. **Type Safety**: Auto-generated client provides full type hints
4. **Testable**: Can mock the HTTP layer or use test services
5. **Clean Separation**: Network details hidden behind clean interface

## Testing

The adapter can be tested independently:

```bash
# Unit tests (with mocked HTTP)
uv run pytest src/mail_client_service_adapter/tests/ -m unit

# Integration tests (requires running service)
uv run pytest src/mail_client_service_adapter/tests/ -m integration
```

## Dependencies

- `mail-client-api` - The interface we implement
- `httpx` - HTTP client library
- Auto-generated OpenAPI client (in `src/generated/`)

## Implementation Details

The adapter:
- Wraps the auto-generated `mail_client_service_client`
- Translates between REST responses and `Message` objects
- Handles HTTP errors gracefully
- Provides logging for debugging
- Maintains the same interface as `GmailClient`

This allows the same application code to work whether using:
- Direct Gmail API access (`GmailClient`)
- Service-based access (`ServiceAdapterClient`)
- Mock implementations for testing
