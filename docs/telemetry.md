# Telemetry & Observability

This document describes the telemetry and observability implementation for all services in the project.

## Overview

All services in this project are instrumented with **Prometheus metrics** to track:

- **Request Latency**: How long each HTTP request takes
- **Success Rate**: Percentage of successful requests (2xx status codes)
- **Failure Rate**: Percentage of failed requests (4xx/5xx status codes)
- **Request Volume**: Total number of requests per endpoint

## Architecture

### Shared Telemetry Module

The `shared_telemetry` package provides reusable telemetry utilities for all services:

```
src/shared_telemetry/
├── __init__.py
├── metrics.py          # Prometheus metric definitions
└── middleware.py       # FastAPI middleware for automatic tracking
```

### Metrics Collected

#### 1. HTTP Request Counter
```python
http_requests_total{service, method, endpoint, status}
```
Tracks the total number of HTTP requests by service, method, endpoint, and status code.

#### 2. HTTP Request Duration
```python
http_request_duration_seconds{service, method, endpoint}
```
Histogram tracking request latency in seconds with predefined buckets:
- 0.005s, 0.01s, 0.025s, 0.05s, 0.075s, 0.1s
- 0.25s, 0.5s, 0.75s, 1.0s, 2.5s, 5.0s, 7.5s, 10.0s

#### 3. HTTP Request Errors
```python
http_request_errors_total{service, method, endpoint, error_type}
```
Tracks failed requests by error type (client_error, server_error, or exception name).

## Instrumented Services

### 1. Discord Service
- **Service Name**: `discord-service`
- **Metrics Endpoint**: `http://localhost:8001/metrics`
- **Port**: 8001

### 2. OpenAI Service
- **Service Name**: `openai-service`
- **Metrics Endpoint**: `http://localhost:8002/metrics`
- **Port**: 8002

### 3. Mail Service
- **Service Name**: `mail-service`
- **Metrics Endpoint**: `http://localhost:8000/metrics`
- **Port**: 8000

## Usage

### Accessing Metrics

Each service exposes a `/metrics` endpoint that returns Prometheus-formatted metrics:

```bash
# Discord Service
curl http://localhost:8001/metrics

# OpenAI Service
curl http://localhost:8002/metrics

# Mail Service
curl http://localhost:8000/metrics
```

### Example Metrics Output

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{service="discord-service",method="GET",endpoint="/health",status="200"} 42.0

# HELP http_request_duration_seconds HTTP request latency in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{service="discord-service",method="GET",endpoint="/health",le="0.005"} 10.0
http_request_duration_seconds_bucket{service="discord-service",method="GET",endpoint="/health",le="0.01"} 35.0
http_request_duration_seconds_sum{service="discord-service",method="GET",endpoint="/health"} 0.234
http_request_duration_seconds_count{service="discord-service",method="GET",endpoint="/health"} 42.0

# HELP http_request_errors_total Total HTTP request errors
# TYPE http_request_errors_total counter
http_request_errors_total{service="discord-service",method="GET",endpoint="/api/messages",error_type="client_error"} 3.0
```

## Testing Telemetry

Run the telemetry test script to verify all services are collecting metrics:

```bash
# Start all services first
uv run python run_discord_service.py &  # Port 8001
uv run uvicorn openai_client_service.main:app --port 8002 &
uv run python run_service.py &  # Port 8000

# Run the test
uv run python test_telemetry.py
```

## Monitoring Dashboard

### Option 1: Google Cloud Monitoring (Recommended for Cloud Run)

Since services are deployed on Google Cloud Run, use **Google Cloud Operations** (formerly Stackdriver):

1. Navigate to Google Cloud Console → Monitoring
2. Create a new dashboard
3. Add charts for:
   - Request latency (p50, p95, p99)
   - Success rate (2xx / total requests)
   - Failure rate (4xx+5xx / total requests)
   - Request volume (requests per minute)

### Option 2: Prometheus + Grafana (Local Development)

For local development, you can set up Prometheus and Grafana:

1. **Install Prometheus**:
   ```bash
   # macOS
   brew install prometheus
   
   # Or use Docker
   docker run -p 9090:9090 prom/prometheus
   ```

2. **Configure Prometheus** (`prometheus.yml`):
   ```yaml
   scrape_configs:
     - job_name: 'discord-service'
       static_configs:
         - targets: ['localhost:8001']
     
     - job_name: 'openai-service'
       static_configs:
         - targets: ['localhost:8002']
     
     - job_name: 'mail-service'
       static_configs:
         - targets: ['localhost:8000']
   ```

3. **Install Grafana**:
   ```bash
   # macOS
   brew install grafana
   
   # Or use Docker
   docker run -p 3000:3000 grafana/grafana
   ```

4. **Import Dashboard**:
   - Open Grafana at `http://localhost:3000`
   - Add Prometheus as a data source
   - Create dashboards with the metrics above

## Adding Telemetry to New Services

To add telemetry to a new service:

1. **Add dependency** in `pyproject.toml`:
   ```toml
   dependencies = [
       "shared-telemetry",
       # ... other dependencies
   ]
   
   [tool.uv.sources]
   shared-telemetry = { workspace = true }
   ```

2. **Import and add middleware** in your service:
   ```python
   from shared_telemetry import add_telemetry_middleware
   
   app = FastAPI(title="My Service")
   add_telemetry_middleware(app, service_name="my-service")
   ```

3. **That's it!** The middleware automatically tracks all requests.

## Metrics Best Practices

1. **Service Names**: Use lowercase with hyphens (e.g., `discord-service`)
2. **Endpoint Labels**: Keep endpoint labels low-cardinality (avoid user IDs in paths)
3. **Error Types**: Use consistent error type names across services
4. **Histogram Buckets**: Adjust buckets based on your service's latency profile

## Troubleshooting

### Metrics endpoint returns 404
- Ensure the service has telemetry middleware added
- Check that `shared-telemetry` is installed: `uv sync --all-packages`

### No metrics showing up
- Make requests to the service first to generate metrics
- Check service logs for errors during middleware initialization

### High memory usage
- Prometheus metrics are stored in memory
- Consider reducing the number of label combinations
- Use metric aggregation for high-cardinality data

