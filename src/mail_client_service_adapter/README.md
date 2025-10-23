# Mail Client Service Adapter

An adapter that implements the `mail_client_api.Client` interface by wrapping the
auto-generated OpenAPI client for the mail service. The adapter hides HTTP details
behind a local, testable interface so application code can use the same API whether
it talks directly to Gmail or to a networked mail service.

## Overview

This package implements the Adapter Pattern for the project's mail client API.
It delegates calls to the auto-generated `mail_client_service_client` (the OpenAPI
client) and converts the generated models into the `mail_client_api.Message`
abstraction used by the rest of the application.

## Scope

- Implements the `mail_client_api.Client` contract using a remote mail service.
- Focused on basic mailbox operations: listing messages, fetching a single
    message, deleting a message, and marking a message as read.
- Does not implement message composition / sending.
- Some fields are currently omitted by the service API (for example `to` in list
    responses). The adapter documents these gaps and provides reasonable defaults.

## Architecture

Application code -> mail_client_api.Client (expected interface)
        ↳ ServiceAdapterClient (this package) -> mail_client_service_client (generated OpenAPI client) -> Mail Service (FastAPI)

The adapter is intentionally thin: it handles request/response translation,
error handling, and logging, while leaving HTTP retries and transport details to
the generated client.

## Exposed interfaces

The package exports three top-level symbols (see `src/mail_client_service_adapter/__init__.py`):

- ServiceAdapterClient(service_url: str = "http://localhost:8000")
    - Implements `mail_client_api.Client`
    - Methods (signatures shown):
        - get_messages(max_results: int = 10) -> Iterator[mail_client_api.message.Message]
            - Yields lightweight Message objects for list responses (body may be empty)
        - get_message(message_id: str) -> mail_client_api.message.Message
            - Returns a full Message; raises `ValueError` if the message cannot be retrieved
        - delete_message(message_id: str) -> bool
            - Returns True on success, False otherwise
        - mark_as_read(message_id: str) -> bool
            - Returns True on success, False otherwise

- get_client_impl(service_url: str = "http://localhost:8000") -> mail_client_api.Client
    - Factory that constructs and returns a `ServiceAdapterClient` instance.

- register(service_url: str = "http://localhost:8000") -> None
    - Installs a factory on `mail_client_api.get_client` so `mail_client_api.get_client()`
        returns a service-backed client (convenience for dependency injection in apps).

Notes:
- The package provides a `ServiceMessage` dataclass (internal) that implements the
    `mail_client_api.message.Message` interface. Consumers should treat it as a
    normal `Message` instance and rely on the documented properties.

## Usage patterns

All examples use absolute imports.

Basic (direct) usage:

```python
from mail_client_service_adapter import ServiceAdapterClient

# Create adapter pointing to running service
client = ServiceAdapterClient(service_url="http://localhost:8000")

# Iterate messages (list-view; body/content may be empty)
for msg in client.get_messages(max_results=5):
        print(msg.id, msg.subject)

# Fetch a single message (full detail)
message = client.get_message("message-id-123")
print(message.from_, message.subject, message.body)

# Mutations
deleted = client.delete_message("message-id-123")
marked = client.mark_as_read("message-id-456")
```

Dependency-injection / registration pattern:

```python
import mail_client_service_adapter

# Replace mail_client_api.get_client with a factory that returns the service client
mail_client_service_adapter.register(service_url="http://localhost:8000")

import mail_client_api
client = mail_client_api.get_client()  # now uses the ServiceAdapterClient
```

When using `register()`, the function installs a factory that returns the
service-backed client. The factory accepts an optional `interactive` keyword-only
argument for compatibility with other client factories; it is ignored by this
adapter.

## Component dependencies

- mail-client-api: the abstract client and Message interfaces this adapter implements.
- mail_client_service_client: the generated OpenAPI HTTP client this adapter wraps.
    (The generated client provides model classes like `MessageDetail` and
    request functions used by the adapter.)
- httpx: used by the generated client for HTTP transport (installed as a
    dependency of the generated client).

Install / packaging: this package is intended to be installed alongside the
generated client and `mail-client-api`. See the `pyproject.toml` in this folder
for the package metadata.

## Error handling & behavior

- get_message raises `ValueError` when the service response does not contain a
    valid message (for example, not found or validation error).
- get_messages returns an iterator; if the service returns no messages the iterator
    will be empty.
- delete_message and mark_as_read return boolean success flags. They do not
    raise on ordinary service-level errors; the generated client may still raise
    transport exceptions (e.g. network errors).

Known limitations / notes
- The current mail service's list API does not provide a `to` field or message
    body in the list view. The adapter fills those fields with empty strings for
    list responses and only includes body content for `get_message` results.
- The adapter depends on the shape of the generated models. If the OpenAPI
    schema changes, the adapter may need to be updated to match the new models.

## Testing

Unit tests should mock the generated client functions. Integration tests require
the mail service to be running (default: `http://localhost:8000`). Example test
commands (from the repository root):

```powershell
# Run unit tests for this package (example)
pytest src/mail_client_service_adapter/tests/ -m unit

# Run integration tests (service must be running)
pytest src/mail_client_service_adapter/tests/ -m integration
```

## Implementation details (brief)

- The adapter lives in `src/mail_client_service_adapter/adapter_impl.py`.
- Top-level exports are in `src/mail_client_service_adapter/__init__.py`.
- Logging is used for debug and warning messages; configure the standard
    library `logging` module to capture adapter logs.

## Quick checklist (developer)

- [x] Exposes ServiceAdapterClient, get_client_impl, register
- [x] Converts generated models to `mail_client_api.message.Message`
- [x] Provides clear failure modes and boolean success results for mutations

If you want, I can also add a minimal example script under `examples/` that
demonstrates wiring and a short integration smoke-test.
