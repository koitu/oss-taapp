"""FastAPI middleware for telemetry tracking."""

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from shared_telemetry.metrics import (
    get_http_request_counter,
    get_http_request_duration_histogram,
    get_http_request_errors_counter,
)


def add_telemetry_middleware(app: FastAPI, service_name: str) -> None:
    """Add telemetry middleware to a FastAPI application.

    This middleware tracks:
    - Request count by method, endpoint, and status code
    - Request duration (latency) by method and endpoint
    - Error count by method, endpoint, and error type
    Args:
        app: FastAPI application instance.
        service_name: Name of the service for metric labeling.

    """

    @app.middleware("http")
    async def telemetry_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Track metrics for each HTTP request."""
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            response: Response = await call_next(request)
            return response

        start_time = time.time()
        method = request.method
        endpoint = request.url.path

        try:
            # Process the request
            response = await call_next(request)
            duration = time.time() - start_time
            status = response.status_code

            # Track successful request
            get_http_request_counter().labels(
                service=service_name,
                method=method,
                endpoint=endpoint,
                status=status,
            ).inc()

            get_http_request_duration_histogram().labels(
                service=service_name,
                method=method,
                endpoint=endpoint,
            ).observe(duration)

            error_client = 400
            error_server = 500

            # Track errors (4xx and 5xx status codes)
            if status >= error_client:
                error_type = "client_error" if status < error_server else "server_error"
                get_http_request_errors_counter().labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint,
                    error_type=error_type,
                ).inc()

            return response # noqa: TRY300

        except Exception as e:
            # Track exception
            duration = time.time() - start_time

            get_http_request_errors_counter().labels(
                service=service_name,
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__,
            ).inc()

            # Re-raise the exception
            raise

    @app.get("/metrics")
    async def metrics() -> Response:
        """Expose Prometheus metrics endpoint.

        Returns:
            Response: Prometheus metrics in text format.

        """
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

