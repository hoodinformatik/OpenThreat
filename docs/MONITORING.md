# Monitoring Guide for OpenThreat

## 📊 Overview

OpenThreat provides comprehensive monitoring through health checks, Prometheus metrics, and structured logging.

---

## 🏥 Health Checks

### Basic Health Check

**Endpoint:** `GET /health`

Returns basic API and database status.

```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-16T10:00:00Z"
}
```

---

### Detailed Health Check

**Endpoint:** `GET /health/detailed`

Returns comprehensive system health information.

```bash
curl http://localhost:8001/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-16T10:00:00Z",
  "version": "0.1.0",
  "checks": {
    "database": {
      "status": "healthy",
      "response_time_ms": "<10",
      "vulnerability_count": 314419
    },
    "system": {
      "status": "healthy",
      "cpu_percent": 15.2,
      "memory_percent": 45.8,
      "memory_available_mb": 4096,
      "disk_percent": 60.5,
      "disk_free_gb": 50
    },
    "environment": {
      "python_version": "3.13.0",
      "database_url_configured": true,
      "redis_url_configured": true
    }
  }
}
```

---

### Kubernetes Probes

#### Readiness Probe

**Endpoint:** `GET /health/ready`

Returns 200 when service is ready to accept traffic.

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8001
  initialDelaySeconds: 10
  periodSeconds: 5
```

#### Liveness Probe

**Endpoint:** `GET /health/live`

Returns 200 when service is alive.

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8001
  initialDelaySeconds: 30
  periodSeconds: 10
```

---

## 📈 Prometheus Metrics

### Metrics Endpoint

**Endpoint:** `GET /metrics`

Returns Prometheus-formatted metrics.

```bash
curl http://localhost:8001/metrics
```

---

### Available Metrics

#### HTTP Metrics

**`http_requests_total`**
- Type: Counter
- Labels: method, endpoint, status
- Description: Total HTTP requests

**`http_request_duration_seconds`**
- Type: Histogram
- Labels: method, endpoint
- Description: HTTP request duration

**`http_requests_in_progress`**
- Type: Gauge
- Description: HTTP requests currently in progress

**`http_errors_total`**
- Type: Counter
- Labels: method, endpoint, status
- Description: Total HTTP errors

#### Application Metrics

**`vulnerabilities_total`**
- Type: Gauge
- Description: Total vulnerabilities in database

**`exploited_vulnerabilities_total`**
- Type: Gauge
- Description: Total exploited vulnerabilities

---

### Prometheus Configuration

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'openthreat'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']
```

---

### Grafana Dashboard

#### Import Dashboard

1. Open Grafana
2. Go to Dashboards → Import
3. Upload `monitoring/grafana-dashboard.json`

#### Key Panels

- **Request Rate:** Requests per second
- **Error Rate:** Errors per second
- **Response Time:** P50, P95, P99 latencies
- **Vulnerability Count:** Total and exploited
- **System Resources:** CPU, Memory, Disk

---

## 📝 Logging

### Log Levels

- **DEBUG:** Detailed information for debugging
- **INFO:** General information
- **WARNING:** Warning messages
- **ERROR:** Error messages
- **CRITICAL:** Critical errors

### Configuration

Set log level via environment variable:

```bash
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/openthreat/app.log
```

### Log Format

```
2025-10-16 10:00:00 - backend.main - INFO - main.py:86 - 🚀 OpenThreat API starting...
```

### Sensitive Data Filtering

Passwords, API keys, and tokens are automatically filtered from logs:

```python
# Before filtering
logger.info("API key: sk-1234567890")

# After filtering
# API key: ***REDACTED***
```

---

## 🔔 Alerting

### Recommended Alerts

#### High Error Rate
```yaml
alert: HighErrorRate
expr: rate(http_errors_total[5m]) > 0.1
for: 5m
annotations:
  summary: "High error rate detected"
```

#### High Response Time
```yaml
alert: HighResponseTime
expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
for: 5m
annotations:
  summary: "95th percentile response time > 1s"
```

#### Database Connection Issues
```yaml
alert: DatabaseUnhealthy
expr: up{job="openthreat"} == 0
for: 1m
annotations:
  summary: "Database health check failing"
```

#### High Memory Usage
```yaml
alert: HighMemoryUsage
expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > 0.9
for: 5m
annotations:
  summary: "Memory usage > 90%"
```

---

## 📊 Monitoring Stack

### Docker Compose Setup

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana-dashboard.json:/etc/grafana/provisioning/dashboards/openthreat.json

volumes:
  prometheus-data:
  grafana-data:
```

### Start Monitoring Stack

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

**Access:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

---

## 🔍 Troubleshooting

### High Memory Usage

1. Check `/health/detailed` for system metrics
2. Review application logs
3. Check for memory leaks
4. Restart service if necessary

### Slow Response Times

1. Check Prometheus metrics for slow endpoints
2. Review database query performance
3. Check system resources
4. Enable query logging

### Database Connection Issues

1. Check database health: `curl http://localhost:8001/health`
2. Verify database is running: `docker ps`
3. Check database logs: `docker logs openthreat-db`
4. Verify connection string in `.env`

---

## 📈 Performance Benchmarks

### Expected Performance

- **Response Time (P95):** <100ms
- **Throughput:** >1000 req/s
- **Error Rate:** <0.1%
- **Memory Usage:** <2GB
- **CPU Usage:** <50%

### Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test
ab -n 10000 -c 100 http://localhost:8001/api/v1/vulnerabilities
```

---

## 📧 Support

For monitoring issues:
- Check logs first
- Review health checks
- Check Prometheus metrics
- Email: hoodinformatik@gmail.com

---

## 🔗 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Monitoring](https://fastapi.tiangolo.com/advanced/monitoring/)
