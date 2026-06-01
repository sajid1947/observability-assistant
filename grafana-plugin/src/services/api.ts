/**
 * Backend API client service.
 *
 * Provides typed methods for calling the observability assistant
 * backend from the Grafana plugin. Handles authentication, error
 * formatting, and response typing.
 */

import {
  AnalyzeRequest,
  ExplainMetricsRequest,
  InsightResponse,
} from '../types';

/**
 * API client for the observability assistant backend.
 *
 * Usage:
 *   const api = new ApiClient('http://localhost:8080', 'my-api-key');
 *   const result = await api.analyzeMetrics(requestPayload);
 */
export class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(baseUrl: string, apiKey: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = apiKey;
  }

  /**
   * Common fetch wrapper with auth headers and error handling.
   */
  private async request<T>(path: string, body: unknown): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const detail = (errorData as any).detail || response.statusText;
        throw new Error(`API Error (${response.status}): ${detail}`);
      }

      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error(
          `Cannot reach backend at ${this.baseUrl}. Is the service running?`
        );
      }
      throw error;
    }
  }

  /**
   * Analyze dashboard metrics (POST /analyze).
   *
   * @param payload - Metrics data extracted from the Grafana panel
   * @returns Structured insight response from the LLM
   */
  async analyzeMetrics(payload: AnalyzeRequest): Promise<InsightResponse> {
    return this.request<InsightResponse>('/analyze', payload);
  }

  /**
   * Explain a specific metric (POST /explain_metrics).
   *
   * @param payload - Single metric data for detailed analysis
   * @returns Structured insight response from the LLM
   */
  async explainMetrics(
    payload: ExplainMetricsRequest
  ): Promise<InsightResponse> {
    return this.request<InsightResponse>('/explain_metrics', payload);
  }

  /**
   * Health check (GET /health).
   *
   * @returns Backend health status
   */
  async healthCheck(): Promise<Record<string, unknown>> {
    const url = `${this.baseUrl}/health`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }
}
