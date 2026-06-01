/**
 * TypeScript types for the Kibana plugin.
 */

export interface TimeRange {
  start: string;
  end: string;
}

export interface LogEntry {
  message: string;
  level?: string;
  timestamp?: string;
  source?: string;
  metadata?: Record<string, unknown>;
}

export interface SummarizeLogsRequest {
  logs: LogEntry[];
  filters: Record<string, unknown>;
  time_range: TimeRange;
  source: string;
  index_pattern?: string;
}

export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

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

/** Plugin setup contract — what this plugin provides to others during setup. */
export interface ObservabilityAssistantPluginSetup {}

/** Plugin start contract — what this plugin provides to others after start. */
export interface ObservabilityAssistantPluginStart {}
