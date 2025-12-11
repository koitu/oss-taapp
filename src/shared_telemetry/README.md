# Shared Telemetry

Reusable telemetry utilities for all services in the project.

## Overview

This package provides Prometheus-based telemetry for FastAPI services, automatically tracking:

- Request count by method, endpoint, and status code
- Request duration (latency) with histogram buckets
- Error count by type

## Installation

This package is part of the workspace. Add it to your service's `pyproject.toml`:

```toml
[project]
dependencies = [
    "shared-telemetry",
    # ... other dependencies
]

[tool.uv.sources]
shared-telemetry = { workspace = true }
```

## Usage

### Basic Setup

```python
from fastapi import FastAPI
from shared_telemetry import add_telemetry_middleware

app = FastAPI(title="My Service")

# Add telemetry middleware
add_telemetry_middleware(app, service_name="my-service")
```

That's it! The middleware will automatically:
- Track all HTTP requests
- Expose metrics at `/metrics` endpoint
- Record latency, success/failure rates, and error types

### Accessing Metrics

Once your service is running, metrics are available at:

```bash
curl http://localhost:8000/metrics
```

## Metrics Collected

### 1. `http_requests_total`
Counter tracking total requests.

**Labels:**
- `service`: Service name (e.g., "discord-service")
- `method`: HTTP method (GET, POST, etc.)
- `endpoint`: Request path (e.g., "/health")
- `status`: HTTP status code (200, 404, 500, etc.)

**Example:**
```
http_requests_total{service="my-service",method="GET",endpoint="/health",status="200"} 42.0
```

### 2. `http_request_duration_seconds`
Histogram tracking request latency.

**Labels:**
- `service`: Service name
- `method`: HTTP method
- `endpoint`: Request path

**Buckets:** 0.005s, 0.01s, 0.025s, 0.05s, 0.075s, 0.1s, 0.25s, 0.5s, 0.75s, 1.0s, 2.5s, 5.0s, 7.5s, 10.0s

**Example:**
```
http_request_duration_seconds_bucket{service="my-service",method="GET",endpoint="/health",le="0.01"} 35.0
http_request_duration_seconds_sum{service="my-service",method="GET",endpoint="/health"} 0.234
http_request_duration_seconds_count{service="my-service",method="GET",endpoint="/health"} 42.0
```

### 3. `http_request_errors_total`
Counter tracking failed requests.

**Labels:**
- `service`: Service name
- `method`: HTTP method
- `endpoint`: Request path
- `error_type`: Type of error (client_error, server_error, or exception name)

**Example:**
```
http_request_errors_total{service="my-service",method="GET",endpoint="/api/data",error_type="client_error"} 3.0
```

## API Reference

### `add_telemetry_middleware(app: FastAPI, service_name: str)`

Adds telemetry middleware to a FastAPI application.

**Parameters:**
- `app`: FastAPI application instance
- `service_name`: Name of the service for metric labeling (use lowercase with hyphens)

**Example:**
```python
add_telemetry_middleware(app, service_name="discord-service")
```

### Metric Accessors

```python
from shared_telemetry import (
    get_http_request_counter,
    get_http_request_duration_histogram,
    get_http_request_errors_counter,
)

# Get metric instances for custom tracking
counter = get_http_request_counter()
histogram = get_http_request_duration_histogram()
errors = get_http_request_errors_counter()
```

## Integration with Monitoring Systems

### Prometheus

Configure Prometheus to scrape your service:

```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['localhost:8000']
```

### Google Cloud Monitoring

For services deployed on Google Cloud Run, metrics are automatically available in Cloud Monitoring.

### Grafana

Import metrics into Grafana dashboards:
1. Add Prometheus as a data source
2. Create panels using the metrics above
3. Use PromQL queries like:
   - `rate(http_requests_total[5m])` - Request rate
   - `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` - 95th percentile latency

## Best Practices

1. **Service Naming**: Use lowercase with hyphens (e.g., `my-service`, not `MyService`)
2. **Low Cardinality**: Avoid high-cardinality labels (e.g., user IDs in endpoint paths)
3. **Consistent Error Types**: Use standard error type names across services
4. **Histogram Buckets**: Adjust buckets if your service has different latency characteristics

## Troubleshooting

**Metrics endpoint returns 404:**
- Ensure middleware is added after creating the FastAPI app
- Check that `shared-telemetry` is installed: `uv sync --all-packages`

**No metrics showing:**
- Make requests to your service first to generate metrics
- Check service logs for middleware initialization messages

**High memory usage:**
- Reduce label cardinality
- Consider metric aggregation for high-traffic endpoints

## Dependencies

- `fastapi>=0.118.0`
- `prometheus-client>=0.23.0`
- `prometheus-fastapi-instrumentator>=7.0.0`

## License

Same as the parent project.

