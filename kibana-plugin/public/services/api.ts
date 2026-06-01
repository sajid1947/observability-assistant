/**
 * Kibana API client service.
 *
 * Calls the backend through Kibana's server-side proxy route
 * to avoid CORS issues. The proxy route is registered in
 * server/routes/index.ts.
 */

import { HttpSetup } from '@kbn/core/public';
import { SummarizeLogsRequest, InsightResponse } from '../types';

/**
 * API client that routes through Kibana's server-side proxy.
 *
 * Instead of calling the backend directly from the browser (which
 * would require CORS), we go through a Kibana server route that
 * forwards the request to our backend.
 */
export class ObservabilityApiClient {
  private http: HttpSetup;

  constructor(http: HttpSetup) {
    this.http = http;
  }

  /**
   * Summarize logs via the server-side proxy.
   */
  async summarizeLogs(payload: SummarizeLogsRequest): Promise<InsightResponse> {
    return this.http.post('/api/observability_assistant/summarize_logs', {
      body: JSON.stringify(payload),
    });
  }

  /**
   * Health check via the server-side proxy.
   */
  async healthCheck(): Promise<Record<string, unknown>> {
    return this.http.get('/api/observability_assistant/health');
  }
}
