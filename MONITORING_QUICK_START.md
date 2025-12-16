# Prometheus + Grafana Monitoring - Quick Start

## TL;DR - 3 Commands

```bash
# 1. Start with monitoring
docker-compose -f docker-compose.monitoring.yml up --build

# 2. Access Grafana
open http://localhost:3000
# Login: admin / admin

# 3. View your dashboard
# Already loaded: "OSPSD Service Metrics"
```

## What You Get

- **Beautiful Dashboards** at http://localhost:3000
  - Request latency graphs
  - Success/failure rates
  - Real-time metrics
  
- **Prometheus** at http://localhost:9090
  - Query metrics directly
  - Set up alerts
  
- **Metrics Endpoint** at http://localhost:8000/metrics
  - Raw Prometheus data
  - Automatic updates

## Dashboard Overview

Your pre-configured dashboard shows:

1. **Request Latency** - How fast is each operation? (p50, p95, p99)
2. **Request Rate** - How many requests per second?
3. **Success Rate** - What % of requests succeed?
4. **Failure Rate** - How many errors per second?
5. **Key Stats** - Total requests, avg latency, failures

## Operations Tracked

- `ai_generate` - AI response times
- `ticket_create` - Creating tickets
- `ticket_list` - Listing tickets
- `ticket_get` - Getting ticket details
- `ticket_update` - Updating tickets
- `ticket_delete` - Deleting tickets
- `chat_message` - Overall message handling

## Common Tasks

### View Logs
```bash
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### Stop Everything
```bash
docker-compose -f docker-compose.monitoring.yml down
```

### Restart After Code Changes
```bash
docker-compose -f docker-compose.monitoring.yml up --build --force-recreate
```

### Check If Metrics Are Working
```bash
curl http://localhost:8000/metrics | grep ospsd_requests_total
```

## Grafana Login

**First Time:**
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`
- You'll be asked to change password

**After Login:**
- Click "Dashboards" → "OSPSD Service Metrics"
- Dashboard loads automatically!

## Prometheus Queries

Try these in Prometheus (http://localhost:9090/graph):

```promql
# Total requests
sum(ospsd_requests_total)

# Average latency for AI
avg(rate(ospsd_request_duration_ms_sum{operation="ai_generate"}[5m]) / 
    rate(ospsd_request_duration_ms_count{operation="ai_generate"}[5m]))

# Success rate
100 * sum(rate(ospsd_requests_success_total[5m])) / 
sum(rate(ospsd_requests_total[5m]))
```

## Troubleshooting

### "No Data" in Grafana
1. Send a Discord message to generate metrics
2. Check http://localhost:8000/metrics shows data
3. Wait 10-30 seconds for Prometheus to scrape

### Can't Access Grafana
```bash
# Check if running
docker ps | grep grafana

# Check logs
docker logs grafana
```

### Metrics Not Updating
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Should see ospsd-service with "UP" status
```

## vs Regular Docker Compose

**Without Monitoring** (`docker-compose.yml`):
```bash
docker-compose up
```
- Just runs OSPSD service
- Metrics saved to JSON file
- No dashboards

**With Monitoring** (`docker-compose.monitoring.yml`):
```bash
docker-compose -f docker-compose.monitoring.yml up
```
- Runs OSPSD + Prometheus + Grafana
- Real-time dashboards
- Historical data
- Alerting capabilities

## What's Running

When you start with monitoring:

| Service | Port | Purpose |
|---------|------|---------|
| OSPSD | 8000 | Your app + /metrics endpoint |
| Prometheus | 9090 | Metrics collection & storage |
| Grafana | 3000 | Visualization dashboards |

## Resource Usage

- OSPSD: ~300MB RAM
- Prometheus: ~200MB RAM
- Grafana: ~150MB RAM
- **Total: ~650MB RAM**

## Next Steps

1. **Explore Dashboard**
   - Click different time ranges
   - Zoom into graphs
   - Check out single stats

2. **Customize**
   - Add new panels
   - Create alerts
   - Share dashboards

3. **Learn More**
   - See [MONITORING_GUIDE.md](MONITORING_GUIDE.md) for full details
   - Prometheus queries: https://prometheus.io/docs/prometheus/latest/querying/basics/
   - Grafana docs: https://grafana.com/docs/

## Quick Tips

- ✅ Dashboard auto-refreshes every 10s
- ✅ Data persists across restarts (volumes)
- ✅ Can export dashboard as JSON
- ✅ Can set up email/Slack alerts
- ✅ Both JSON and Prometheus metrics work together!

## Demo Workflow

```bash
# Start everything
docker-compose -f docker-compose.monitoring.yml up -d

# Send Discord message: "Create a ticket for testing"
# (triggers metrics)

# View in Grafana
open http://localhost:3000

# See the spike in:
# - Request latency (ai_generate)
# - Request rate (ticket_create)
# - Success rate (should be 100%)

# Clean up
docker-compose -f docker-compose.monitoring.yml down
```

That's it! You now have professional-grade monitoring 📊
