# Telemetry Quick Reference Card

## 🚀 Quick Start

### View Metrics

```bash
# Discord Service
curl http://localhost:8001/metrics

# OpenAI Service
curl http://localhost:8002/metrics

# Mail Service
curl http://localhost:8000/metrics
```

### Test Telemetry

```bash
# Start services
uv run python run_discord_service.py &
uv run uvicorn openai_client_service.main:app --port 8002 &
uv run python run_service.py &

# Run test
uv run python test_telemetry.py
```

## 📊 Metrics Reference

### 1. Request Count

```
http_requests_total{service="discord-service",method="GET",endpoint="/health",status="200"}
```

**Use:** Calculate success rate, request volume

### 2. Request Latency

```
http_request_duration_seconds{service="discord-service",method="GET",endpoint="/health"}
```

**Use:** Calculate p50, p95, p99 latency

### 3. Error Count

```
http_request_errors_total{service="discord-service",method="GET",endpoint="/api/messages",error_type="client_error"}
```

**Use:** Calculate failure rate, identify error patterns

## 🔧 Add to New Service

1. **Update `pyproject.toml`:**

```toml
dependencies = ["shared-telemetry"]

[tool.uv.sources]
shared-telemetry = { workspace = true }
```

2. **Add to service code:**

```python
from shared_telemetry import add_telemetry_middleware

app = FastAPI(title="My Service")
add_telemetry_middleware(app, service_name="my-service")
```

## 📈 Calculate Key Metrics

### Success Rate

```
(sum(http_requests_total{status=~"2.."}) / sum(http_requests_total)) * 100
```

### Failure Rate

```
(sum(http_requests_total{status=~"[45].."}) / sum(http_requests_total)) * 100
```

### P95 Latency

```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Request Rate (per minute)

```
rate(http_requests_total[1m]) * 60
```

## 🎯 Service Endpoints

| Service | Port | Metrics URL                   |
| ------- | ---- | ----------------------------- |
| Discord | 8001 | http://localhost:8001/metrics |
| OpenAI  | 8002 | http://localhost:8002/metrics |
| Mail    | 8000 | http://localhost:8000/metrics |

## 📚 Documentation

- **Full Guide:** [docs/telemetry.md](docs/telemetry.md)
- **Package Docs:** [src/shared_telemetry/README.md](src/shared_telemetry/README.md)
- **Implementation Summary:** [TELEMETRY_IMPLEMENTATION_SUMMARY.md](TELEMETRY_IMPLEMENTATION_SUMMARY.md)

## 🔍 Troubleshooting

**Metrics endpoint 404?**

- Check middleware is added: `add_telemetry_middleware(app, service_name="...")`
- Run: `uv sync --all-packages`

**No metrics showing?**

- Make requests to service first
- Check service logs for errors

**Import errors?**

- Ensure `shared-telemetry` in workspace members
- Run: `uv sync --all-packages`
