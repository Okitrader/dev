# Deep Research System - Monitoring Dashboard Configuration

## Quick Setup

### 1. Local Development Dashboard

For local development, we provide a built-in metrics server:

```bash
# Start the metrics server (in a separate terminal)
python metrics_server.py

# Access endpoints:
# - http://localhost:9090/metrics      # Prometheus metrics
# - http://localhost:9090/health       # Health check
# - http://localhost:9090/alerts       # Active alerts
# - http://localhost:9090/api/performance/shadow  # Shadow mode data
```

### 2. Grafana Setup (Recommended for Production)

#### Install Grafana
```bash
# Docker
docker run -d -p 3000:3000 --name=grafana grafana/grafana

# Or use your platform's package manager
```

#### Configure Prometheus Data Source
1. Access Grafana at http://localhost:3000 (admin/admin)
2. Add Data Source → Prometheus
3. URL: `http://localhost:9090`
4. Save & Test

#### Import Dashboard
1. Create → Import
2. Upload the provided `grafana_dashboard.json` (see below)
3. Select Prometheus data source

### 3. Prometheus Configuration

Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'deep_research'
    static_configs:
      - targets: ['localhost:9090']
```

Start Prometheus:
```bash
docker run -d -p 9091:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

## Key Metrics to Monitor

### Performance Metrics
- **Request Duration** (`deep_research_request_duration_seconds`)
  - Alert if p95 > 120 seconds
  - Alert if p50 > 60 seconds

- **Architecture Speed Ratio** (`deep_research_architecture_speed_ratio`)
  - Alert if ratio > 1.2 (new architecture 20% slower)

### Quality Metrics
- **Report Quality Score** (`deep_research_quality_score`)
  - Alert if average < 0.6
  - Track by architecture and report type

- **Quality Delta** (`deep_research_architecture_quality_delta`)
  - Alert if delta < -0.1 (new architecture worse quality)

### Reliability Metrics
- **Error Rate** (`deep_research_errors_total`)
  - Alert if rate > 5% over 5 minutes
  - Track by error type and agent

- **Cache Hit Rate**
  ```
  rate(deep_research_cache_hits_total[5m]) / 
  (rate(deep_research_cache_hits_total[5m]) + rate(deep_research_cache_misses_total[5m]))
  ```
  - Alert if < 30% (poor cache utilization)

### System Health
- **Active Requests** (`deep_research_active_requests`)
  - Alert if > 50 concurrent requests

- **Uptime** (`deep_research_uptime_seconds`)
  - Track system stability

## Alert Rules

### Critical Alerts (Page immediately)
```yaml
- alert: HighErrorRate
  expr: rate(deep_research_errors_total[5m]) > 0.1
  for: 2m
  annotations:
    summary: "High error rate: {{ $value | humanizePercentage }}"

- alert: PerformanceDegradation
  expr: deep_research_architecture_speed_ratio > 1.5
  for: 5m
  annotations:
    summary: "New architecture 50% slower than old"
```

### Warning Alerts (Notify team)
```yaml
- alert: LowQualityScores
  expr: avg(deep_research_quality_score) < 0.6
  for: 10m
  annotations:
    summary: "Average quality score below threshold"

- alert: LowCacheHitRate
  expr: |
    rate(deep_research_cache_hits_total[5m]) / 
    (rate(deep_research_cache_hits_total[5m]) + rate(deep_research_cache_misses_total[5m])) < 0.3
  for: 15m
  annotations:
    summary: "Cache hit rate below 30%"
```

## Grafana Dashboard JSON

Save as `grafana_dashboard.json`:
```json
{
  "dashboard": {
    "title": "Deep Research System",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(deep_research_requests_total[5m])",
          "legendFormat": "{{architecture}} - {{status}}"
        }]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, rate(deep_research_request_duration_seconds_bucket[5m]))",
          "legendFormat": "{{architecture}}"
        }]
      },
      {
        "title": "Architecture Comparison",
        "targets": [
          {
            "expr": "deep_research_architecture_speed_ratio",
            "legendFormat": "Speed Ratio (new/old)"
          },
          {
            "expr": "deep_research_architecture_quality_delta",
            "legendFormat": "Quality Delta (new-old)"
          }
        ]
      },
      {
        "title": "Quality Scores",
        "targets": [{
          "expr": "avg(deep_research_quality_score) by (architecture)",
          "legendFormat": "{{architecture}}"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(deep_research_errors_total[5m])",
          "legendFormat": "{{architecture}} - {{error_type}}"
        }]
      },
      {
        "title": "Cache Performance",
        "targets": [
          {
            "expr": "rate(deep_research_cache_hits_total[5m])",
            "legendFormat": "Hits"
          },
          {
            "expr": "rate(deep_research_cache_misses_total[5m])",
            "legendFormat": "Misses"
          }
        ]
      }
    ]
  }
}
```

## DataDog Integration (Alternative)

If using DataDog instead of Prometheus:

1. Install DataDog agent
2. Add custom check in `/etc/datadog-agent/conf.d/deep_research.d/conf.yaml`:
```yaml
init_config:

instances:
  - prometheus_url: http://localhost:9090/metrics
    namespace: deep_research
    metrics:
      - deep_research_*
```

3. Create DataDog dashboard with same metrics

## Monitoring Checklist

### Daily Checks
- [ ] Review error rate trends
- [ ] Check shadow mode comparison results
- [ ] Verify cache hit rates
- [ ] Monitor active alerts

### Weekly Analysis
- [ ] Performance trend analysis
- [ ] Quality score distribution
- [ ] Cost analysis (API usage)
- [ ] User adoption metrics

### Monthly Review
- [ ] Architecture comparison report
- [ ] Optimization opportunities
- [ ] Capacity planning
- [ ] Alert threshold adjustments