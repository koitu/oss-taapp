"""Mail Client Service Adapter.

This package provides an adapter that implements the mail_client_api.Client interface
using the auto-generated OpenAPI client for the mail_client_service.

This demonstrates how to wrap a network service client behind a familiar local interface,
implementing the Adapter Pattern.
"""

from mail_client_service_adapter.adapter_impl import (
    ServiceAdapterClient as ServiceAdapterClient,
)
from mail_client_service_adapter.adapter_impl import (
    get_client_impl as get_client_impl,
)
from mail_client_service_adapter.adapter_impl import (
    register as register,
)

