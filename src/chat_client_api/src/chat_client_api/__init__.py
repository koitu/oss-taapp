"""Chat Client API - Abstract contract for chat service implementations.

This module provides abstract base classes and factory functions that define
the contract for chat client implementations (Discord, Slack, etc.).

Public API:
    - Client: Abstract base class for chat clients
    - ChatMessage: Abstract base class for chat messages
    - Channel: Abstract base class for channels
    - get_client: Factory function to get a client implementation
    - get_message: Factory function to create message instances
    - get_channel: Factory function to create channel instances

"""

from chat_client_api.client import Client as Client
from chat_client_api.client import get_client as get_client
from chat_client_api.message import (
    Channel as Channel,
)
from chat_client_api.message import (
    ChatMessage as ChatMessage,
)
from chat_client_api.message import (
    get_channel as get_channel,
)
from chat_client_api.message import (
    get_message as get_message,
)

