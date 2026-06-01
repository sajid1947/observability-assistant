/**
 * TypeScript type definitions for the Observability Assistant Grafana plugin.
 *
 * Defines the panel options schema, API request/response types,
 * and internal data structures used across components.
 */

/**
 * Plugin panel options — configurable in the Grafana panel editor.
 * Users set the backend API URL and API key here.
 */
export interface ObservabilityOptions {
  /** URL of the backend API (e.g., http://localhost:8080) */
  backendUrl: string;
  /** API key for authentication */
  apiKey: string;
  /** Whether to auto-analyze on data refresh */
  autoAnalyze: boolean;
}

/** Default option values for new panel instances. */
export const defaults: ObservabilityOptions = {
  backendUrl: 'http://localhost:8080',
  apiKey: '',
  autoAnalyze: false,
};

/** Time range sent to the backend API. */
export interface TimeRange {
  start: string;
  end: string;
}

/** A single metric extracted from the Grafana panel data. */
export interface MetricData {
  name: string;
  values: (number | null)[];
  timestamps: string[];
  labels: Record<string, string>;
}

/** Request payload for POST /analyze. */
export interface AnalyzeRequest {
  source: string;
  metrics: MetricData[];
  time_range: TimeRange;
  labels: Record<string, string>;
  query_results: Record<string, unknown>[];
  dashboard_name?: string;
  panel_name?: string;
}

/** Request payload for POST /explain_metrics. */
export interface ExplainMetricsRequest {
  metric_name: string;
  values: (number | null)[];
  timestamps: string[];
  labels: Record<string, string>;
  time_range: TimeRange;
  query?: string;
  threshold?: number;
  unit?: string;
}

/** Severity levels matching the backend enum. */
export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

/** Response from all analysis endpoints. */
export interface InsightResponse {
  summary: string;
  root_cause: string;
  severity: SeverityLevel;
  confidence: string;
  evidence: string[];
  recommendations: string[];
  anomalies_detected: string[];
  request_id?: string;
  model_used?: string;
  processing_time_ms?: number;
  cached?: boolean;
}
