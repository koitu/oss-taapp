"""FastAPI middleware for telemetry tracking."""

import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .metrics import (
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
    async def telemetry_middleware(request: Request, call_next: Callable) -> Response:
        """Track metrics for each HTTP request."""
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
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
            
            # Track errors (4xx and 5xx status codes)
            if status >= 400:
                error_type = "client_error" if status < 500 else "server_error"
                get_http_request_errors_counter().labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint,
                    error_type=error_type,
                ).inc()
            
            return response
            
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

