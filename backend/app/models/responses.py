"""
Pydantic response models for all API endpoints.

These models define the exact shape of API responses.
The InsightResponse is the primary output format, matching
the structured JSON spec from the requirements.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for observability insights."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InsightResponse(BaseModel):
    """
    Primary response model for all analysis endpoints.
    
    This is the structured output format returned to Grafana/Kibana,
    containing the LLM's analysis of the provided observability data.
    
    Example:
        {
            "summary": "High error rate detected on api-gateway service",
            "root_cause": "Database connection pool exhaustion causing timeout errors",
            "severity": "high",
            "confidence": "87%",
            "evidence": [
                "Error rate increased from 0.1% to 15.3% at 14:32 UTC",
                "Connection pool utilization at 98% during the incident"
            ],
            "recommendations": [
                "Increase database connection pool size from 20 to 50",
                "Add circuit breaker pattern to database calls"
            ]
        }
    """
    summary: str = Field(
        ...,
        description="Concise summary of the analysis"
    )
    root_cause: str = Field(
        ...,
        description="Most probable root cause of any issues detected"
    )
    severity: SeverityLevel = Field(
        ...,
        description="Severity classification"
    )
    confidence: str = Field(
        ...,
        description="Confidence score as percentage (e.g., '85%')"
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="List of specific data points supporting the analysis"
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable remediation steps"
    )
    anomalies_detected: list[str] = Field(
        default_factory=list,
        description="List of anomalies found in the data"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Unique request ID for tracing"
    )
    model_used: Optional[str] = Field(
        default=None,
        description="Name of the LLM model used for analysis"
    )
    processing_time_ms: Optional[int] = Field(
        default=None,
        description="Processing time in milliseconds"
    )
    cached: bool = Field(
        default=False,
        description="Whether this response was served from cache"
    )


class HealthResponse(BaseModel):
    """
    Response model for the GET /health endpoint.
    
    Reports the health status of the backend service
    and connectivity to the configured LLM backend.
    """
    status: str = Field(..., description="Overall service status ('healthy' or 'degraded')")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    llm_backend: str = Field(..., description="Configured LLM backend name")
    llm_status: str = Field(..., description="LLM connectivity status ('connected' or 'unavailable')")
    model_loaded: Optional[str] = Field(default=None, description="Currently loaded model name")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Current server time (UTC)"
    )
    cache_stats: Optional[dict] = Field(
        default=None,
        description="Cache hit/miss statistics"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    Used across all error scenarios for consistent error reporting
    to clients. Includes a machine-readable error code and a
    human-readable detail message.
    """
    error: str = Field(..., description="Machine-readable error code")
    detail: str = Field(..., description="Human-readable error description")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z",
        description="Error timestamp (UTC)"
    )
