# Mail Client Service

Lightweight FastAPI service that exposes the mail client functionality over HTTP. This repo contains a small REST wrapper around the mail client components used in this project so they can be invoked as a networked service.

## Overview

This service provides a thin network layer for the underlying mail client implementation(s). It translates HTTP requests to calls into the project's mail client abstraction (the `mail_client_api` component) and returns HTTP responses with validated payloads. The service is intentionally small: business logic remains in the client components; the service focuses on transport, validation, and error mapping.

## Scope

- What this service does

  - Exposes mail client operations over HTTP (list messages, get message details, mark-as-read, delete, health check).
  - Converts HTTP payloads to typed Python objects and vice versa (FastAPI + Pydantic).
  - Performs authentication and authorization at the HTTP layer when configured by the deployment.

- What this service does NOT do
  - It is not a full mail server or message store. It delegates storage and remote API calls to the mail client implementations (for example, `gmail_client_impl`).
  - It does not implement long-running background workers—these belong to other components.

## Exposed interfaces (HTTP)

Below are the primary HTTP endpoints. These are documented in the running app's OpenAPI schema (`/docs`) but are reproduced here for convenience.

- GET /messages

  - Description: Returns a list of message summaries (id, subject, sender, snippet, is_read, received_at).
  - Response: 200 OK with JSON array of message summary objects.

- GET /messages/{message_id}

  - Description: Returns full message details for the given message_id.
  - Response: 200 OK with JSON object containing full message fields (headers, body, attachments metadata).
  - Errors: 404 Not Found if message_id does not exist.

- POST /messages/{message_id}/mark-as-read

  - Description: Marks the message as read.
    - Response: 200 OK with JSON object containing a message acknowledging success.
  - Errors: 404 Not Found if message_id does not exist.

- DELETE /messages/{message_id}

  - Description: Deletes the message referenced by message_id.
    - Response: 200 OK with JSON object containing a message acknowledging success.
  - Errors: 404 Not Found if message_id does not exist.

- GET /health
  - Description: Basic health check for the service (returns service-ready status and optionally downstream status).
  - Response: 200 OK with JSON {"status": "ok"} when healthy.

Notes

- The exact JSON schema for request/response bodies is provided by the running app's OpenAPI schema. Use `/docs` (Swagger UI) or `/openapi.json` to inspect shapes programmatically.

## Usage pattern (examples using absolute imports)

You can import the FastAPI app directly for testing or embedding. Use absolute imports as shown below.

Python (test or embed the app):

```python
from mail_client_service.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

resp = client.get('/messages')
print(resp.status_code, resp.json())
```

Start the service with uvicorn from the project root (examples use the project-level utility `uv` when available; adjust to your environment):

PowerShell example (project root):

```powershell
# run development server with auto-reload
uv run uvicorn mail_client_service.api:app --reload

# or explicit host/port
uv run uvicorn mail_client_service.api:app --host 0.0.0.0 --port 8000
```

If you don't have the `uv` helper, run directly with Python -m uvicorn:

```powershell
python -m uvicorn mail_client_service.api:app --reload
```

HTTP examples (curl-equivalent):

```powershell
# list messages
Invoke-RestMethod -Method Get -Uri http://localhost:8000/messages

# get full message
Invoke-RestMethod -Method Get -Uri http://localhost:8000/messages/{message_id}
```

Programmatic client example (absolute imports to integrate the service app into tests or other processes):

```python
from mail_client_service.api import app

# mount or run the app inside another FastAPI process, or use TestClient as shown earlier
```

## Component dependencies

This service relies on the following internal components (packages under `src/`) and may depend on external packages declared in its `pyproject.toml`:

- mail_client_api

  - The API/abstraction used by the service to talk to mail client implementations (defines the operations and DTOs).

- gmail_client_impl (optional)

  - A concrete implementation of the mail client API that talks to Gmail. The service will use whatever implementation is wired into its dependency injection.

- mail_client_service_adapter (optional)
  - Adapter utilities that convert between service-level models and client-level models when needed.

External runtime dependencies (declared in this package's pyproject.toml)

- fastapi
- uvicorn
- pydantic

## Testing

Unit and integration tests live under `src/services/mail_client_service/tests/`. Tests typically import the app with absolute imports and use the FastAPI `TestClient` or a fake mail client implementation to avoid external API calls.

Run tests from project root:

```powershell
# using project helper
uv run pytest src/services/mail_client_service/tests/ -v

# or directly
pytest src/services/mail_client_service/tests/ -v
```

## OpenAPI / Docs

When running the service, interactive documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Notes and troubleshooting

- If the service cannot contact an external mail provider, the health endpoint may report degraded status. Check environment variables and credentials used by the underlying implementation (for example, Gmail credentials).
- For local development prefer using the provided fake client implementations in tests to avoid needing real credentials.
- To access the (HTTP) MCP service simply point your client to https://127.0.0.1:8000/mcp/
