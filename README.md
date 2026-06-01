# 🔍 AI-Powered Observability Assistant

An intelligent observability platform that integrates with **Grafana** and **Kibana** to provide AI-driven analysis of metrics, logs, and dashboard data using local LLMs (**Ollama** / **vLLM**).

## Architecture

```
Grafana / Kibana
      ↓
Plugin extracts dashboard data
      ↓
FastAPI Backend (normalize → chunk → prompt → LLM → format)
      ↓
Local LLM (Ollama or vLLM)
      ↓
Structured insights returned to dashboard
```

### Components

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Backend API** | Python, FastAPI, Pydantic | Core service that normalizes payloads, builds prompts, queries LLMs |
| **Grafana Plugin** | React, TypeScript | Panel plugin with "Explain Dashboard" button |
| **Kibana Plugin** | React, TypeScript | Application with log analysis interface |
| **LLM Layer** | Ollama / vLLM | Local model inference (qwen3:8b, mistral, llama3.1) |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM (for running LLM models)
- GPU recommended but not required

### 1. Clone and Configure

```bash
cd observability-assistant
cp .env.example .env
# Edit .env to set your API_KEY and other preferences
```

### 2. Start the Backend Stack

```bash
docker compose up -d
```

This starts:
- **Backend API** at `http://localhost:8080` (or your public IP/domain)
- **Ollama** at `http://localhost:11434`

The `ollama-pull` service automatically downloads the configured model on first run.

### 3. Verify

```bash
# Health check
curl http://localhost:8080/health


# Test analysis (with sample payload)
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -d @docs/sample_payloads/analyze_request.json
```

### 4. Use in External Grafana/Kibana

Because your Grafana and Kibana instances are hosted externally on public domains:
1. Ensure this backend API is accessible from the internet (e.g., behind an Nginx reverse proxy with HTTPS).
2. Install the Grafana/Kibana plugins from the `grafana-plugin` and `kibana-plugin` directories into your external instances.
3. Configure the Grafana plugin's "Backend URL" setting to point to your backend's public domain.
4. Set the `API_KEY` in the panel options.
5. Click **"Explain Dashboard"** to analyze your metrics.

## API Reference

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/analyze` | ✅ | Analyze dashboard metrics |
| `POST` | `/summarize_logs` | ✅ | Summarize log entries |
| `POST` | `/explain_metrics` | ✅ | Explain specific metric behavior |
| `GET` | `/health` | ❌ | Service health check |

### Authentication

All protected endpoints require the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/analyze
```

### Response Format

All analysis endpoints return:

```json
{
  "summary": "High error rate detected on api-gateway service",
  "root_cause": "Database connection pool exhaustion",
  "severity": "high",
  "confidence": "87%",
  "evidence": ["Error rate increased from 0.1% to 15.3%"],
  "recommendations": ["Increase connection pool size"],
  "anomalies_detected": ["Sudden spike in p99 latency"],
  "request_id": "uuid",
  "model_used": "qwen3:8b",
  "processing_time_ms": 4500,
  "cached": false
}
```

See [docs/api.md](docs/api.md) for full API documentation.

## Configuration

All settings are configurable via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BACKEND` | `ollama` | LLM backend (`ollama` or `vllm`) |
| `OLLAMA_MODEL` | `qwen3:8b` | Model name for Ollama |
| `API_KEY` | `dev-key-...` | API authentication key |
| `RATE_LIMIT_REQUESTS` | `30` | Max requests per minute per IP |
| `CACHE_TTL` | `300` | Response cache TTL in seconds |
| `MODEL_TEMPERATURE` | `0.1` | LLM temperature (lower = deterministic) |
| `LOG_LEVEL` | `INFO` | Logging level |

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

### Run Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Grafana Plugin

```bash
cd grafana-plugin
npm install
npm run dev    # Watch mode
npm run build  # Production build
```

### Supported Models

| Model | Size | Best For |
|-------|------|----------|
| `qwen3:8b` | ~5GB | General analysis (default) |
| `mistral` | ~4GB | Fast responses |
| `llama3.1:8b` | ~5GB | Detailed explanations |

## Features

- ✅ **Log Chunking** — Intelligent splitting with error prioritization
- ✅ **Rate Limiting** — Per-IP token bucket with configurable limits
- ✅ **Caching** — TTL-based response cache with hit/miss stats
- ✅ **Request IDs** — UUID4 per request for distributed tracing
- ✅ **Async Processing** — Fully async FastAPI with async LLM clients
- ✅ **Structured Logging** — JSON logs via structlog
- ✅ **Error Handling** — Global exception handlers with consistent format
- ✅ **Retry Logic** — Exponential backoff for LLM calls
- ✅ **Health Checks** — Backend + LLM connectivity monitoring
- ✅ **API Authentication** — API key-based auth
- ✅ **CORS Controls** — Configurable origin whitelist
- ✅ **Input Sanitization** — HTML/script stripping, length enforcement

## License

Apache 2.0
