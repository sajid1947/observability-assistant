# API Documentation

## Base URL

```
http://localhost:8080
```

## Authentication

All endpoints except `/health` require an API key via the `X-API-Key` header.

```
X-API-Key: your-api-key-here
```

## Rate Limiting

- **Limit**: 30 requests per minute per IP (configurable)
- **Response**: HTTP 429 with `Retry-After` header when exceeded
- **Exempt**: `/health`, `/docs`, `/openapi.json`

## Caching

Responses are cached for 5 minutes (configurable via `CACHE_TTL`).
Cached responses include `"cached": true` in the response body.

---

## POST /analyze

Analyze dashboard metrics and return structured observability insights.

### Request

```json
{
  "source": "grafana",
  "metrics": [
    {
      "name": "cpu_usage_percent",
      "values": [45.2, 48.1, 52.3, 78.9, 95.1],
      "timestamps": ["2024-01-01T00:00:00Z", "..."],
      "labels": {"host": "web-01", "region": "us-east-1"}
    }
  ],
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T00:30:00Z"
  },
  "labels": {"env": "production"},
  "dashboard_name": "Web Server Monitoring",
  "panel_name": "CPU Usage"
}
```

### Response

```json
{
  "summary": "CPU usage trending upward with critical spike",
  "root_cause": "Possible resource exhaustion from increased traffic",
  "severity": "high",
  "confidence": "82%",
  "evidence": ["CPU spiked from 45% to 95% in 20 minutes"],
  "recommendations": ["Scale horizontally", "Check for memory leaks"],
  "anomalies_detected": ["95% CPU at 00:20 exceeds normal baseline"],
  "request_id": "abc-123",
  "model_used": "qwen3:8b",
  "processing_time_ms": 4500,
  "cached": false
}
```

---

## POST /summarize_logs

Summarize log entries and identify patterns, errors, and anomalies.

### Request

```json
{
  "logs": [
    {
      "message": "Connection timeout to database",
      "level": "ERROR",
      "timestamp": "2024-01-01T00:15:00Z",
      "source": "api-gateway"
    }
  ],
  "filters": {"level": "ERROR"},
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T00:30:00Z"
  },
  "source": "kibana",
  "index_pattern": "logs-*"
}
```

### Response

Same format as `/analyze`.

---

## POST /explain_metrics

Get a detailed explanation of a specific metric's behavior.

### Request

```json
{
  "metric_name": "http_request_duration_seconds",
  "values": [0.12, 0.15, 0.11, 1.2, 2.3, 0.14],
  "timestamps": ["2024-01-01T00:00:00Z", "..."],
  "labels": {"service": "api-gateway"},
  "time_range": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-01T00:30:00Z"
  },
  "query": "histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))",
  "threshold": 1.0,
  "unit": "seconds"
}
```

### Response

Same format as `/analyze`.

---

## GET /health

Returns service health status. **No authentication required.**

### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "llm_backend": "ollama",
  "llm_status": "connected",
  "model_loaded": "qwen3:8b",
  "timestamp": "2024-01-01T12:00:00Z",
  "cache_stats": {
    "hits": 42,
    "misses": 15,
    "hit_rate": "73.7%",
    "current_size": 28,
    "max_size": 256,
    "ttl_seconds": 300
  }
}
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "error_code",
  "detail": "Human-readable error message",
  "request_id": "uuid"
}
```

### Status Codes

| Code | Meaning |
|------|---------|
| 401 | Missing API key |
| 403 | Invalid API key |
| 422 | Validation error (bad payload) |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | LLM backend unreachable |

---

## Interactive Docs

- **Swagger UI**: `http://localhost:8080/docs`
- **ReDoc**: `http://localhost:8080/redoc`
