"""Prometheus metrics for OSPSD service."""

from prometheus_client import Counter, Histogram, generate_latest

# Request latency histogram (in milliseconds)
REQUEST_LATENCY = Histogram(
    "ospsd_request_duration_ms",
    "Request latency in milliseconds",
    ["operation"],
    buckets=[10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000],
)

# Success counter
REQUEST_SUCCESS = Counter(
    "ospsd_requests_success_total",
    "Total number of successful requests",
    ["operation"],
)

# Failure counter
REQUEST_FAILURE = Counter(
    "ospsd_requests_failure_total",
    "Total number of failed requests",
    ["operation"],
)

# Total requests counter
REQUEST_TOTAL = Counter(
    "ospsd_requests_total",
    "Total number of requests",
    ["operation"],
)


def record_latency(operation: str, duration_ms: float, *, success: bool = True) -> None:
    """Record request latency and increment counters.

    Args:
        operation: The operation type (e.g., 'ai_generate', 'ticket_create')
        duration_ms: Duration in milliseconds
        success: Whether the operation was successful

    """
    REQUEST_LATENCY.labels(operation=operation).observe(duration_ms)
    REQUEST_TOTAL.labels(operation=operation).inc()

    if success:
        REQUEST_SUCCESS.labels(operation=operation).inc()
    else:
        REQUEST_FAILURE.labels(operation=operation).inc()


def get_metrics() -> bytes:
    """Get current metrics in Prometheus format.

    Returns:
        Metrics in Prometheus text format

    """
    return generate_latest()
