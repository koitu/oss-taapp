# DESIGN.md

## Architecture Overview

This project extends the original single-process mail client library into a distributed, service-based architecture.  
Originally, the Gmail implementation (`gmail_client_impl`) was imported and executed locally. Now, that implementation is wrapped in a **FastAPI service** so that any client can access it remotely, independent of the original library.  
To preserve the same developer experience and interface, two additional “bridges” were added: an **auto-generated client** and a **custom adapter**.

Together, these three layers allow user code to call the same functions (`get_messages`, `get_message`, etc.) while the actual implementation runs remotely. This allows for easier scaling, fault tolerance, and management.

### Components

1. **FastAPI Service (Backend)**

   - Wraps the existing Gmail client implementation.
   - Exposes REST endpoints for fetching message summaries, retrieving details, marking messages as read, and deleting messages.
   - Handles dependency injection for the Gmail client and maps exceptions to proper HTTP responses.

2. **Auto-Generated Client**

   - Generated from the FastAPI OpenAPI schema using `openapi-python-client`.
   - Provides type-safe Python methods for interacting with the service.
   - Eliminates the need to manually write `requests` calls or parse JSON responses.

3. **Adapter (Shim)**
   - Implements the same `mail_client_api.Client` interface as the original Gmail client.
   - Internally calls the auto-generated client to communicate with the FastAPI service.
   - Ensures user code does not need to change, regardless of whether it’s using the local library or the remote service.

---

## Request Flow

The following illustrates how a single request travels through the system when a user retrieves messages:

User Code → Adapter → Auto-generated Client → FastAPI Service → GmailClient Implementation → FastAPI Response → Auto-generated Client → Adapter → User Code

### Step-by-step example (`get_messages()`):

1. **User Code:**  
   Calls `client.get_messages(max_results=5)`.
2. **Adapter:**  
   Invokes the auto-generated client’s `get_messages_messages_get.sync()` method.
3. **Generated Client:**  
   Sends a `GET /messages?max_results=5` HTTP request to the FastAPI service.
4. **FastAPI Service:**  
   Routes the request to the `/messages` endpoint, which calls the injected Gmail client’s `get_messages()` method.
5. **Gmail Implementation:**  
   Fetches data from Gmail and returns a list of messages to the FastAPI service.
6. **FastAPI Response:**  
   Returns a structured JSON response to the client.
7. **Adapter:**  
   Converts the JSON into `mail_client_api.message.Message` objects and yields them to user code.

---

## Sample API Response

**Request**
GET /messages?max_results=2

**Response**

````json
{
  "messages": {
    "a1b2c3": {
      "subject": "Welcome to the project!",
      "from": "teamlead@example.com",
      "date": "2025-10-01T10:00:00Z"
    },
    "d4e5f6": {
      "subject": "Meeting Tomorrow",
      "from": "prof.kamen@example.edu",
      "date": "2025-10-02T09:30:00Z"
    }
  },
  "count": 2
}
```

---

## API Design

### Endpoints

| Method | Path | Description | Request Params | Response |
|--------|------|--------------|----------------|-----------|
| **GET** | `/messages` | Fetch message summaries | `max_results: int` | `MessagesResponse` |
| **GET** | `/messages/{message_id}` | Retrieve message details | `message_id: str` | `MessageDetail` |
| **POST** | `/messages/{message_id}/mark-as-read` | Mark message as read | `message_id: str` | `OperationResponse` |
| **DELETE** | `/messages/{message_id}` | Delete message | `message_id: str` | `OperationResponse` |
| **GET** | `/health` | Health check | — | `{ "status": "healthy" }` |

---

### Error Handling

| Error Type | Underlying Cause | HTTP Status | Example Response |
|-------------|------------------|--------------|------------------|
| **Message not found** | `ValueError` raised by Gmail implementation | `404 Not Found` | `{ "detail": "Message not found" }` |
| **Invalid input** | Request validation error | `422 Unprocessable Entity` | `{ "detail": "Invalid query parameter" }` |
| **Gmail auth or token failure** | Credential issue in Gmail client | `503 Service Unavailable` | `{ "detail": "Gmail service unavailable" }` |
| **Unexpected error** | Any uncaught exception | `500 Internal Server Error` | `{ "detail": "Internal server error" }` |

---

## The Adapter Pattern

### Why It’s Needed

The auto-generated client alone doesn’t satisfy the original `mail_client_api.Client` interface because:

- It organizes methods differently (by HTTP endpoints).
- It returns Pydantic models instead of `mail_client_api.message.Message` objects.
- It exposes HTTP-specific logic (status codes, responses) that the user shouldn’t need to handle.

Without the adapter, the user’s existing code would have to change to accommodate these differences.

---

### How It Works

The adapter translates between the OpenAPI client’s methods and the expected interface.
This ensures user code remains identical to how it was when the Gmail client was imported directly.

**User code (unchanged):**

```python
from mail_client_api import get_client

client = get_client()  # returns ServiceAdapterClient
messages = client.get_messages(max_results=5)
for msg in messages:
    print(msg.subject)
````

**Adapter implementation:**

```python
def get_messages(self, max_results: int = 10):
    response = get_messages_messages_get.sync(client=self._client, max_results=max_results)
    for msg_id, data in response.messages.additional_properties.items():
        yield Message(
            _id=msg_id,
            _subject=data.get("subject", ""),
            _from=data.get("from", ""),
            _date=data.get("date", ""),
            _body=""
        )
```
