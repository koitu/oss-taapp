"""Tool definitions and handlers for ticket operations."""

from typing import Any

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
                "title": {"type": "string", "description": "Ticket title/name"},
                "description": {"type": "string", "description": "Ticket description"},
                "ticket_id": {"type": "string", "description": "ID of the ticket"},
                "list_id": {"type": "string", "description": "ID of the list/column"},
                "board_id": {"type": "string", "description": "ID of the board"},
                "limit": {"type": "integer", "description": "Number of tickets to return"},
                "message": {"type": "string", "description": "Chat response message"},
            },
        },
    },
    "required": ["action"],
}


def get_system_prompt_with_tools() -> str:
    """Generate system prompt that explains available ticket operations.

    Returns:
        System prompt with tool instructions

    """
    return f"""You are a helpful assistant that manages work tickets via natural language.

You have access to the following ticket operations:

1. **create_ticket**: Create a new ticket
   - Required: title
   - Optional: description
   - Example: "Create a ticket for fixing the login bug"

2. **list_tickets**: List recent open tickets
   - Optional: limit (default 3)
   - Example: "Show me my recent tickets" or "List 5 open tickets"

3. **get_ticket**: Get details of a specific ticket
   - Required: ticket_id
   - Example: "Show me ticket ABC123"

4. **close_ticket**: Close/archive a ticket
   - Required: ticket_id
   - Example: "Close ticket ABC123"

5. **update_ticket**: Update a ticket's title or description
   - Required: ticket_id
   - Optional: title, description
   - Example: "Update ticket ABC123 with title 'New Title'"

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

    # Validate required parameters for each action
    if action == "create_ticket":
        if "title" not in params:
            return False, "create_ticket requires 'title' parameter"

    elif action == "list_tickets":
        # Optional parameters only
        pass

    elif action in ["get_ticket", "close_ticket"]:
        if "ticket_id" not in params:
            return False, f"{action} requires 'ticket_id' parameter"

    elif action == "update_ticket":
        if "ticket_id" not in params:
            return False, "update_ticket requires 'ticket_id' parameter"
        if "title" not in params and "description" not in params:
            return False, "update_ticket requires at least 'title' or 'description'"

    elif action == "chat_response":
        if "message" not in params:
            return False, "chat_response requires 'message' parameter"

    else:
        return False, f"Unknown action: {action}"

    return True, ""
