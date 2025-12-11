"""Shared telemetry utilities for all services."""

from .middleware import add_telemetry_middleware
from .metrics import (
    get_http_request_counter,
    get_http_request_duration_histogram,
    get_http_request_errors_counter,
)

__all__ = [
    "add_telemetry_middleware",
    "get_http_request_counter",
    "get_http_request_duration_histogram",
    "get_http_request_errors_counter",
]

