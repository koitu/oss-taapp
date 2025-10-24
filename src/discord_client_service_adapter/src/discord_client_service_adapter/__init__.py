"""Discord Client Service Adapter.

This package provides an adapter that implements the chat_client_api.Client
interface by delegating to the auto-generated Discord service HTTP client.
"""

from discord_client_service_adapter.adapter_impl import ServiceAdapterClient

__all__ = ["ServiceAdapterClient"]
