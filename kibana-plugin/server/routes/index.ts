/**
 * Kibana server-side proxy routes.
 *
 * These routes forward requests from the browser to the observability
 * assistant backend API. This avoids CORS issues and allows Kibana
 * to act as a reverse proxy.
 *
 * Routes:
 *   POST /api/observability_assistant/summarize_logs → Backend POST /summarize_logs
 *   GET  /api/observability_assistant/health           → Backend GET /health
 */

import { IRouter, Logger } from '@kbn/core/server';
import { schema } from '@kbn/config-schema';

// Backend URL — configurable via environment variable
const BACKEND_URL = process.env.OBSERVABILITY_BACKEND_URL || 'http://localhost:8080';
const API_KEY = process.env.OBSERVABILITY_API_KEY || 'dev-key-change-me-in-production';

export function registerRoutes(router: IRouter, logger: Logger) {
  /**
   * POST /api/observability_assistant/summarize_logs
   *
   * Proxy route that forwards log summarization requests to the backend.
   */
  router.post(
    {
      path: '/api/observability_assistant/summarize_logs',
      validate: {
        body: schema.object({}, { unknowns: 'allow' }), // Pass through to backend for validation
      },
    },
    async (context, request, response) => {
      try {
        logger.info('Proxying summarize_logs request to backend');

        const backendResponse = await fetch(`${BACKEND_URL}/summarize_logs`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
          },
          body: JSON.stringify(request.body),
        });

        if (!backendResponse.ok) {
          const errorBody = await backendResponse.text();
          logger.error(`Backend error: ${backendResponse.status} ${errorBody}`);
          return response.customError({
            statusCode: backendResponse.status,
            body: { message: `Backend error: ${errorBody}` },
          });
        }

        const data = await backendResponse.json();
        return response.ok({ body: data });
      } catch (error) {
        logger.error(`Failed to proxy to backend: ${error}`);
        return response.customError({
          statusCode: 502,
          body: { message: `Cannot reach backend at ${BACKEND_URL}` },
        });
      }
    }
  );

  /**
   * GET /api/observability_assistant/health
   *
   * Proxy route for health checks.
   */
  router.get(
    {
      path: '/api/observability_assistant/health',
      validate: false,
    },
    async (context, request, response) => {
      try {
        const backendResponse = await fetch(`${BACKEND_URL}/health`);
        const data = await backendResponse.json();
        return response.ok({ body: data });
      } catch (error) {
        return response.customError({
          statusCode: 502,
          body: { message: `Cannot reach backend at ${BACKEND_URL}` },
        });
      }
    }
  );
}
