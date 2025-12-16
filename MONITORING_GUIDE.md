# Monitoring Setup Guide - Prometheus + Grafana

## Overview

This guide explains how to run OSPSD with Prometheus and Grafana for comprehensive monitoring and visualization.

## Architecture

```
┌──────────────────┐
│  OSPSD Service   │  Exposes /metrics endpoint
│  (Port 8000)     │  
└────────┬─────────┘
         │ HTTP GET /metrics (every 10s)
         ▼
┌──────────────────┐
│   Prometheus     │  Scrapes and stores metrics
│   (Port 9090)    │
└────────┬─────────┘
         │ PromQL queries
         ▼
┌──────────────────┐
│    Grafana       │  Visualizes data
│   (Port 3000)    │
└──────────────────┘
```

## Quick Start

### 1. Start Everything
```bash
docker-compose -f docker-compose.monitoring.yml up --build
```

This starts 3 services:
- **OSPSD** on http://localhost:8000
- **Prometheus** on http://localhost:9090
- **Grafana** on http://localhost:3000

### 2. Access Dashboards

**Grafana Dashboard:**
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin` (change on first login)
- Pre-loaded dashboard: "OSPSD Service Metrics"

**Prometheus UI:**
- URL: http://localhost:9090
- Query metrics directly
- View targets and alerts

**OSPSD Metrics Endpoint:**
- URL: http://localhost:8000/metrics
- Raw Prometheus-formatted metrics

## Available Metrics

### Request Latency
- **Metric:** `ospsd_request_duration_ms`
- **Type:** Histogram
- **Labels:** `operation`
- **Buckets:** 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000 ms

### Request Counters
- **ospsd_requests_total** - Total requests by operation
- **ospsd_requests_success_total** - Successful requests
- **ospsd_requests_failure_total** - Failed requests

### Operations Tracked
- `ai_generate` - AI response generation
- `ticket_create` - Create new ticket
- `ticket_list` - List tickets
- `ticket_get` - Get ticket details
- `ticket_update` - Update ticket
- `ticket_delete` - Delete/close ticket
- `chat_message` - Overall message handling

## Grafana Dashboard

The pre-configured dashboard includes:

### 1. Request Latency by Operation (Graph)
Shows p50, p95, and p99 latency percentiles for each operation type.

### 2. Request Rate by Operation (Graph)
Displays requests per second for each operation.

### 3. Success Rate % (Graph)
Percentage of successful requests per operation.

### 4. Failure Rate (Graph)
Failed requests per second per operation.

### 5. Key Metrics (Single Stats)
- Total Requests (5m window)
- Success Rate % (5m window)
- Average Latency (5m window)
- Total Failures (5m window)

## Example Queries

### Prometheus PromQL Queries

**95th percentile latency for AI generation:**
```promql
histogram_quantile(0.95, rate(ospsd_request_duration_ms_bucket{operation="ai_generate"}[5m]))
```

**Success rate for ticket creation:**
```promql
100 * rate(ospsd_requests_success_total{operation="ticket_create"}[5m]) / 
rate(ospsd_requests_total{operation="ticket_create"}[5m])
```

**Total failures across all operations:**
```promql
sum(increase(ospsd_requests_failure_total[5m]))
```

**Average latency per operation:**
```promql
rate(ospsd_request_duration_ms_sum[5m]) / rate(ospsd_request_duration_ms_count[5m])
```

## Alerting Rules (Optional)

Create `/monitoring/prometheus/alerts.yml`:

```yaml
groups:
  - name: ospsd_alerts
    interval: 30s
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          100 * rate(ospsd_requests_failure_total[5m]) / 
          rate(ospsd_requests_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "{{ $labels.operation }} has >10% error rate"

      # High latency
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(ospsd_request_duration_ms_bucket[5m])) > 2000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "{{ $labels.operation }} p95 latency >2s"
```

Then update `prometheus.yml`:
```yaml
rule_files:
  - 'alerts.yml'
```

## Common Commands

### View Logs
```bash
# All services
docker-compose -f docker-compose.monitoring.yml logs -f

# Just OSPSD
docker-compose -f docker-compose.monitoring.yml logs -f ospsd-service

# Just Prometheus
docker-compose -f docker-compose.monitoring.yml logs -f prometheus

# Just Grafana
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### Stop Services
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### Restart Specific Service
```bash
docker-compose -f docker-compose.monitoring.yml restart ospsd-service
```

### View Prometheus Targets
Visit http://localhost:9090/targets to see scrape status.

### Reload Prometheus Config
```bash
curl -X POST http://localhost:9090/-/reload
```

## Troubleshooting

### Prometheus Can't Scrape OSPSD
**Check:**
1. OSPSD is running: `curl http://localhost:8000/health`
2. Metrics endpoint works: `curl http://localhost:8000/metrics`
3. Prometheus config is correct: Check `/monitoring/prometheus/prometheus.yml`
4. Services are on same network: `docker network inspect oss-taapp_monitoring`

**Fix:**
```bash
# Check Prometheus logs
docker-compose -f docker-compose.monitoring.yml logs prometheus

# Verify network connectivity
docker exec prometheus ping ospsd-service
```

### Grafana Shows "No Data"
**Check:**
1. Prometheus is receiving data: http://localhost:9090/graph
2. Datasource is configured: Grafana → Configuration → Data Sources
3. Query is correct: Try simple query like `ospsd_requests_total`

**Fix:**
```bash
# Restart Grafana
docker-compose -f docker-compose.monitoring.yml restart grafana

# Check datasource
curl http://localhost:3000/api/datasources
```

### OSPSD Metrics Not Updating
**Check:**
1. Send a Discord message to trigger metrics
2. Refresh metrics endpoint: http://localhost:8000/metrics
3. Check if counters are incrementing

### Can't Access Grafana
**Fix:**
```bash
# Check if port 3000 is available
lsof -i :3000

# If in use, change port in docker-compose.monitoring.yml
# ports:
#   - "3001:3000"
```

## Data Retention

### Prometheus
- Default retention: 15 days
- Configure in `docker-compose.monitoring.yml`:
  ```yaml
  command:
    - '--storage.tsdb.retention.time=30d'
  ```

### Grafana
- Dashboards and settings persist in `grafana-data` volume
- To reset: `docker volume rm oss-taapp_grafana-data`

## Performance Impact

### Resource Usage
- **Prometheus:** ~200MB RAM, minimal CPU
- **Grafana:** ~150MB RAM, minimal CPU
- **OSPSD overhead:** <5ms per request

### Network
- Prometheus scrapes every 10s
- Each scrape: <10KB
- Total bandwidth: <1MB/day

## Advanced Configuration

### Custom Dashboards
1. Go to Grafana → Create → Dashboard
2. Add panels with PromQL queries
3. Export JSON
4. Save to `/monitoring/grafana/dashboards/`

### Multiple Environments
Run separate stacks with different ports:

```bash
# Production
docker-compose -f docker-compose.monitoring.yml up -d

# Staging (different ports)
GRAFANA_PORT=3001 PROMETHEUS_PORT=9091 \
docker-compose -f docker-compose.monitoring.yml up -d
```

### External Prometheus
Point existing Prometheus to OSPSD:

```yaml
# In your prometheus.yml
scrape_configs:
  - job_name: 'ospsd-prod'
    static_configs:
      - targets: ['your-ospsd-host:8000']
```

## Comparison: JSON vs Prometheus

### JSON Telemetry (Current)
- ✅ Simple, no extra services
- ✅ Easy to read/parse
- ❌ No real-time dashboards
- ❌ No alerting
- ❌ Manual analysis

### Prometheus + Grafana (New)
- ✅ Real-time dashboards
- ✅ Alerting capabilities
- ✅ Historical data analysis
- ✅ Industry standard
- ❌ More complex setup
- ❌ Extra resources (2 containers)

**Recommendation:** Use both!
- Keep JSON for debugging/development
- Use Prometheus+Grafana for production monitoring

## Next Steps

1. **Customize Dashboard**
   - Add more panels
   - Adjust time windows
   - Create alerts

2. **Set Up Alerting**
   - Configure alert rules
   - Connect to Slack/Email
   - Set up on-call rotation

3. **Monitor Infrastructure**
   - Add node_exporter for system metrics
   - Monitor Docker itself
   - Track network/disk usage

4. **Long-term Storage**
   - Configure remote write to cloud
   - Set up backups
   - Archive historical data

## Resources

- **Prometheus Docs:** https://prometheus.io/docs/
- **Grafana Docs:** https://grafana.com/docs/
- **PromQL Tutorial:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Dashboard Examples:** https://grafana.com/grafana/dashboards/
