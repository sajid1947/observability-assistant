# Architecture Overview

## System Design

The AI-Powered Observability Assistant follows a microservices architecture
with clear separation of concerns between data extraction (plugins),
data processing (backend), and AI inference (LLM layer).

## Data Flow

```
┌──────────────┐    ┌──────────────┐
│   Grafana    │    │   Kibana     │
│  Dashboard   │    │  Discover    │
└──────┬───────┘    └──────┬───────┘
       │                    │
       │ Extract metrics    │ Extract logs
       │ time range         │ filters
       │ labels             │ time range
       │                    │
       ▼                    ▼
┌─────────────────────────────────────┐
│         FastAPI Backend              │
│                                      │
│  ┌─────────┐  ┌──────────┐          │
│  │Normalize│→ │  Chunk   │          │
│  └────┬────┘  └────┬─────┘          │
│       │             │                │
│       ▼             ▼                │
│  ┌──────────────────────┐           │
│  │   Prompt Builder     │           │
│  └──────────┬───────────┘           │
│             │                        │
│             ▼                        │
│  ┌──────────────────────┐           │
│  │   LLM Client        │           │
│  │ (Ollama / vLLM)      │           │
│  └──────────┬───────────┘           │
│             │                        │
│             ▼                        │
│  ┌──────────────────────┐           │
│  │ Response Formatter   │           │
│  └──────────────────────┘           │
└─────────────────┬───────────────────┘
                  │
                  ▼
         Structured JSON
         InsightResponse
```

## Component Details

### Backend Processing Pipeline

1. **Normalize** — Convert Grafana DataFrames or Kibana logs into a uniform
   internal `NormalizedData` format. Computes basic statistics (min, max, avg,
   trend direction).

2. **Chunk** — Split large log sets into token-bounded chunks with configurable
   overlap. Prioritizes error-level logs to appear first.

3. **Prompt Builder** — Constructs system prompt (SRE persona) and user prompt
   (data-specific) using templates. Each endpoint type has its own template.

4. **LLM Client** — Abstract client with retry logic and exponential backoff.
   Implementations for Ollama (REST API) and vLLM (OpenAI SDK).

5. **Response Formatter** — Parses raw LLM text into `InsightResponse`.
   Multiple JSON extraction strategies with graceful fallback.

### Middleware Stack

Executed in this order (outermost → innermost):

1. **CORS** — Handles preflight requests for Grafana/Kibana origins
2. **Request ID** — Assigns UUID4, binds to structlog context
3. **Rate Limiter** — Per-IP token bucket (30 req/min default)
4. **Logging** — Logs method, path, status, duration for every request

### Security Model

- **API Key** authentication via `X-API-Key` header
- **CORS** whitelist for known origins only
- **Input Sanitization** — HTML/script stripping, length enforcement
- **Pydantic Validation** — Type checking, field constraints, custom validators
- **Rate Limiting** — Prevents abuse and protects the LLM backend

### Caching Strategy

- TTL-based in-memory cache (cachetools)
- Key: SHA-256 hash of serialized request payload
- Default TTL: 5 minutes
- Max entries: 256
- Hit/miss statistics exposed via `/health`
