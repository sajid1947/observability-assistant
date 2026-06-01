/**
 * ObservabilityPanel — main Grafana panel component.
 *
 * This is the top-level React component rendered inside the Grafana panel.
 * It provides "Explain Dashboard" and "Explain Metrics" buttons that:
 * 1. Extract metric data from the current panel's DataFrames
 * 2. Send the data to the observability assistant backend
 * 3. Display the structured LLM insights
 */

import React, { useState, useCallback } from 'react';
import { PanelProps } from '@grafana/data';
import { Button, useTheme2, Alert, Spinner } from '@grafana/ui';
import { ObservabilityOptions, InsightResponse } from '../types';
import { extractMetrics, extractTimeRange, extractLabels } from '../utils/dataExtractor';
import { ApiClient } from '../services/api';
import { InsightDisplay } from './InsightDisplay';

type Props = PanelProps<ObservabilityOptions>;

export const ObservabilityPanel: React.FC<Props> = ({
  data,
  options,
  width,
  height,
}) => {
  const theme = useTheme2();
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const api = new ApiClient(options.backendUrl, options.apiKey);

  /**
   * Handle "Explain Dashboard" click.
   * Extracts all metrics and sends them for comprehensive analysis.
   */
  const handleAnalyze = useCallback(async () => {
    setLoading(true);
    setError(null);
    setInsight(null);

    try {
      const metrics = extractMetrics(data);
      const timeRange = extractTimeRange(data);
      const labels = extractLabels(data);

      if (metrics.length === 0) {
        setError('No metric data available in this panel. Add a data source first.');
        return;
      }

      const result = await api.analyzeMetrics({
        source: 'grafana',
        metrics,
        time_range: timeRange,
        labels,
        query_results: [],
        dashboard_name: (window as any).__grafana_dashboard_name || undefined,
        panel_name: undefined,
      });

      setInsight(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  }, [data, api]);

  /**
   * Handle "Explain Metrics" click.
   * Picks the first metric for detailed single-metric analysis.
   */
  const handleExplainMetrics = useCallback(async () => {
    setLoading(true);
    setError(null);
    setInsight(null);

    try {
      const metrics = extractMetrics(data);
      const timeRange = extractTimeRange(data);

      if (metrics.length === 0) {
        setError('No metric data available for explanation.');
        return;
      }

      const firstMetric = metrics[0];
      const result = await api.explainMetrics({
        metric_name: firstMetric.name,
        values: firstMetric.values,
        timestamps: firstMetric.timestamps,
        labels: firstMetric.labels,
        time_range: timeRange,
      });

      setInsight(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  }, [data, api]);

  // Panel container styles
  const containerStyle: React.CSSProperties = {
    width,
    height,
    padding: '12px',
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
    fontFamily: theme.typography.fontFamily,
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '12px',
    flexWrap: 'wrap',
  };

  const titleStyle: React.CSSProperties = {
    fontSize: '16px',
    fontWeight: 700,
    color: theme.colors.text.primary,
    marginRight: 'auto',
  };

  return (
    <div style={containerStyle}>
      {/* Header with action buttons */}
      <div style={headerStyle}>
        <span style={titleStyle}>🔍 AI Observability</span>
        <Button
          size="sm"
          variant="primary"
          icon="brain"
          onClick={handleAnalyze}
          disabled={loading}
          tooltip="Analyze all metrics in this panel using AI"
        >
          Explain Dashboard
        </Button>
        <Button
          size="sm"
          variant="secondary"
          icon="graph-bar"
          onClick={handleExplainMetrics}
          disabled={loading}
          tooltip="Get a detailed explanation of the primary metric"
        >
          Explain Metrics
        </Button>
      </div>

      {/* Loading state */}
      {loading && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '20px 0' }}>
          <Spinner size={24} />
          <span style={{ color: theme.colors.text.secondary, fontSize: '13px' }}>
            Analyzing with AI... This may take 10-30 seconds.
          </span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <Alert title="Analysis Error" severity="error">
          {error}
        </Alert>
      )}

      {/* Results */}
      {insight && <InsightDisplay insight={insight} />}

      {/* Empty state */}
      {!loading && !error && !insight && (
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: theme.colors.text.disabled,
          fontSize: '13px',
          textAlign: 'center',
          padding: '20px',
        }}>
          Click "Explain Dashboard" to analyze your metrics with AI,
          <br />
          or "Explain Metrics" for a detailed metric breakdown.
        </div>
      )}
    </div>
  );
};
