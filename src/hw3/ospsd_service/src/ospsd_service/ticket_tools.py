"""Tool definitions and handlers for ticket operations."""

from typing import Any

# Description preview length for list_tickets
TICKET_DESC_PREVIEW_LEN = 50

# Tool/Function definitions for AI to understand ticket operations
TICKET_TOOLS_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": [
                "create_ticket",
                "list_tickets",
                "close_ticket",
                "update_ticket",
                "get_ticket",
                "chat_response",
            ],
            "description": "The action to perform",
        },
        "parameters": {
            "type": "object",
            "description": "Parameters for the action",
            "properties": {
                "title": {"type": ["string", "null"], "description": "Ticket title/name"},
                "description": {"type": ["string", "null"], "description": "Ticket description"},
                "ticket_id": {"type": ["string", "null"], "description": "ID of the ticket"},
                "status": {
                    "type": ["string", "null"],
                    "enum": ["open", "in_progress", "closed", None],
                    "description": "Ticket status: 'open', 'in_progress', or 'closed'",
                },
                "limit": {
                    "type": ["integer", "null"],
                    "description": "Number of tickets to return",
                },
                "message": {"type": ["string", "null"], "description": "Chat response message"},
            },
            "required": ["title", "description", "ticket_id", "status", "limit", "message"],
            "additionalProperties": False,
        },
    },
    "required": ["action", "parameters"],
    "additionalProperties": False,
}


TICKET_SYS_PROMPT = """You are a helpful assistant that manages work tickets via natural language.

You have access to the following ticket operations:

1. **create_ticket**: Create a new ticket
   - Required: title
   - Optional: description
   - Example: "Create a ticket for fixing the login bug"

2. **list_tickets**: List recent tickets
   - Optional: limit (default shows all), status ('open', 'in_progress', 'closed')
   - Example: "Show me my recent tickets" or "List open tickets" or "Show closed tickets"

3. **get_ticket**: Get details of a specific ticket
   - Required: ticket_id
   - Example: "Show me ticket ABC123"

4. **close_ticket**: Close/archive a ticket
   - Required: ticket_id
   - Example: "Close ticket ABC123"

5. **update_ticket**: Update a ticket's title, description, or status
   - Required: ticket_id
   - Optional: title, description, status
   - Status must be one of: 'open', 'in_progress', 'closed'
   - Example: "Update ticket ABC123 with title 'New Title'"
   - Example: "Move ticket ABC123 to in progress"
   - Example: "Mark ticket ABC123 as closed"

6. **chat_response**: Just respond conversationally (no ticket action)
   - Use this for greetings, questions, or general chat
   - Example: "Hello!" or "How are you?"

When a user sends a message, analyze their intent and respond with:
- action: The operation to perform
- parameters: The extracted data

Examples:
- "Create a ticket for fixing login"
  → {{"action": "create_ticket", "parameters": {{"title": "Fix login bug"}}}}
- "Show my 3 recent tickets"
  → {{"action": "list_tickets", "parameters": {{"limit": 3}}}}
- "List open tickets"
  → {{"action": "list_tickets", "parameters": {{"status": "open"}}}}
- "Show me closed tickets"
  → {{"action": "list_tickets", "parameters": {{"status": "closed"}}}}
- "Move ticket abc123 to in progress"
  → {{"action": "update_ticket", "parameters": {{"ticket_id": "abc123", "status": "in_progress"}}}}
- "Close ticket abc123"
  → {{"action": "close_ticket", "parameters": {{"ticket_id": "abc123"}}}}
- "Hello!"
  → {{"action": "chat_response", "parameters": {{"message": "Hello!"}}}}

Always respond with valid JSON matching the schema."""


def validate_tool_call(  # noqa: C901, PLR0911
    tool_call: dict[str, Any],
) -> tuple[bool, str]:
    """Validate a tool call from the AI.

    Args:
        tool_call: The tool call dictionary from AI

    Returns:
        Tuple of (is_valid, error_message)

    """
    if "action" not in tool_call:
        return False, "Missing 'action' field"

    action = tool_call["action"]
    params = tool_call.get("parameters", {})

    # Validate required parameters for each action (null values are treated as missing)
    if action == "create_ticket":
        if not params.get("title"):
            return False, "create_ticket requires 'title' parameter"

    elif action == "list_tickets":
        # Optional parameters only
        pass

    elif action in ["get_ticket", "close_ticket"]:
        if not params.get("ticket_id"):
            return False, f"{action} requires 'ticket_id' parameter"

    elif action == "update_ticket":
        if not params.get("ticket_id"):
            return False, "update_ticket requires 'ticket_id' parameter"
        if not params.get("title") and not params.get("description") and not params.get("status"):
            return False, "update_ticket requires at least 'title', 'description', or 'status'"

    elif action == "chat_response":
        if not params.get("message"):
            return False, "chat_response requires 'message' parameter"

    else:
        return False, f"Unknown action: {action}"

    return True, ""
