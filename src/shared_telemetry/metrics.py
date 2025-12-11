"""Prometheus metrics definitions for all services."""

from prometheus_client import Counter, Histogram

# HTTP Request Counter - tracks total requests by method, endpoint, and status
_http_request_counter = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status"],
)

# HTTP Request Duration - tracks request latency
_http_request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0),
)

# HTTP Request Errors - tracks failed requests
_http_request_errors = Counter(
    "http_request_errors_total",
    "Total HTTP request errors",
    ["service", "method", "endpoint", "error_type"],
)


def get_http_request_counter() -> Counter:
    """Get the HTTP request counter metric.
    
    Returns:
        Counter: Prometheus counter for HTTP requests.
    """
    return _http_request_counter


def get_http_request_duration_histogram() -> Histogram:
    """Get the HTTP request duration histogram metric.
    
    Returns:
        Histogram: Prometheus histogram for request duration.
    """
    return _http_request_duration


def get_http_request_errors_counter() -> Counter:
    """Get the HTTP request errors counter metric.
    
    Returns:
        Counter: Prometheus counter for HTTP errors.
    """
    return _http_request_errors

