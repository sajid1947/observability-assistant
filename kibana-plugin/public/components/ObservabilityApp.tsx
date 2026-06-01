/**
 * ObservabilityApp — main Kibana application component.
 *
 * Provides a log analysis interface using EUI components.
 * Users can paste/view logs and send them to the AI backend for analysis.
 * Also provides a renderApp function for mounting into Kibana's app container.
 */

import React, { useState } from 'react';
import ReactDOM from 'react-dom';
import { AppMountParameters, CoreStart } from '@kbn/core/public';
import { InsightResponse, LogEntry } from '../types';
import { ObservabilityApiClient } from '../services/api';

/**
 * Main application component.
 * Renders a log analysis interface with input area and results display.
 */
const ObservabilityApp: React.FC<{ coreStart: CoreStart }> = ({ coreStart }) => {
  const [logText, setLogText] = useState('');
  const [insight, setInsight] = useState<InsightResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiClient = new ObservabilityApiClient(coreStart.http);

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);
    setInsight(null);

    try {
      // Parse log text into structured entries
      const lines = logText.split('\n').filter((l) => l.trim());
      const logs: LogEntry[] = lines.map((line) => {
        // Simple heuristic to extract level from log lines
        const levelMatch = line.match(/\b(ERROR|WARN|WARNING|INFO|DEBUG|FATAL|CRITICAL)\b/i);
        return {
          message: line,
          level: levelMatch ? levelMatch[1].toUpperCase() : undefined,
        };
      });

      if (logs.length === 0) {
        setError('Please paste some log entries to analyze.');
        return;
      }

      const result = await apiClient.summarizeLogs({
        logs,
        filters: {},
        time_range: {
          start: new Date(Date.now() - 3600000).toISOString(),
          end: new Date().toISOString(),
        },
        source: 'kibana',
      });

      setInsight(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  // Inline styles using a dark professional theme
  const containerStyle: React.CSSProperties = {
    maxWidth: '900px',
    margin: '0 auto',
    padding: '24px',
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
  };

  const headerStyle: React.CSSProperties = {
    fontSize: '24px',
    fontWeight: 700,
    marginBottom: '8px',
    color: '#1a1a2e',
  };

  const textAreaStyle: React.CSSProperties = {
    width: '100%',
    minHeight: '200px',
    padding: '12px',
    fontFamily: "'Fira Code', 'Courier New', monospace",
    fontSize: '13px',
    border: '1px solid #d3dae6',
    borderRadius: '6px',
    resize: 'vertical',
    lineHeight: 1.6,
  };

  const buttonStyle: React.CSSProperties = {
    padding: '10px 24px',
    fontSize: '14px',
    fontWeight: 600,
    color: '#fff',
    backgroundColor: loading ? '#98a2b3' : '#006bb4',
    border: 'none',
    borderRadius: '6px',
    cursor: loading ? 'not-allowed' : 'pointer',
    marginTop: '12px',
  };

  const severityColors: Record<string, string> = {
    critical: '#BD271E',
    high: '#F5A623',
    medium: '#FEC514',
    low: '#006BB4',
    info: '#017D73',
  };

  return (
    <div style={containerStyle}>
      <h1 style={headerStyle}>🔍 AI Observability Assistant</h1>
      <p style={{ color: '#69707d', marginBottom: '20px' }}>
        Paste log entries below and click Analyze to get AI-powered insights.
      </p>

      <textarea
        style={textAreaStyle}
        value={logText}
        onChange={(e) => setLogText(e.target.value)}
        placeholder={`Paste your log entries here, one per line...\n\nExample:\n2024-01-01 14:32:01 ERROR [api-gateway] Connection timeout to database\n2024-01-01 14:32:02 WARN [api-gateway] Retrying connection attempt 3/5\n2024-01-01 14:32:03 ERROR [api-gateway] Connection pool exhausted`}
      />

      <button style={buttonStyle} onClick={handleAnalyze} disabled={loading}>
        {loading ? '⏳ Analyzing...' : '🧠 Analyze Logs'}
      </button>

      {error && (
        <div style={{
          marginTop: '16px', padding: '12px', background: '#FFF6E5',
          border: '1px solid #F5A623', borderRadius: '6px', color: '#8A6914',
        }}>
          ⚠️ {error}
        </div>
      )}

      {insight && (
        <div style={{
          marginTop: '20px', padding: '20px', background: '#f5f7fa',
          borderRadius: '8px', border: '1px solid #d3dae6',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <span style={{
              padding: '4px 12px', borderRadius: '12px', fontSize: '12px',
              fontWeight: 700, color: '#fff',
              backgroundColor: severityColors[insight.severity] || '#69707d',
            }}>
              {insight.severity.toUpperCase()}
            </span>
            <span style={{ fontSize: '13px', color: '#69707d' }}>
              Confidence: {insight.confidence}
            </span>
          </div>

          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>Summary</h3>
          <p style={{ fontSize: '14px', color: '#343741', lineHeight: 1.6 }}>{insight.summary}</p>

          <h3 style={{ fontSize: '16px', fontWeight: 600, marginTop: '16px', marginBottom: '8px' }}>Root Cause</h3>
          <p style={{ fontSize: '14px', color: '#343741', lineHeight: 1.6 }}>{insight.root_cause}</p>

          {insight.evidence.length > 0 && (
            <>
              <h3 style={{ fontSize: '16px', fontWeight: 600, marginTop: '16px', marginBottom: '8px' }}>Evidence</h3>
              <ul style={{ paddingLeft: '20px' }}>
                {insight.evidence.map((e, i) => (
                  <li key={i} style={{ fontSize: '13px', color: '#343741', marginBottom: '4px' }}>{e}</li>
                ))}
              </ul>
            </>
          )}

          {insight.recommendations.length > 0 && (
            <>
              <h3 style={{ fontSize: '16px', fontWeight: 600, marginTop: '16px', marginBottom: '8px' }}>Recommendations</h3>
              <ul style={{ paddingLeft: '20px' }}>
                {insight.recommendations.map((r, i) => (
                  <li key={i} style={{ fontSize: '13px', color: '#343741', marginBottom: '4px' }}>{r}</li>
                ))}
              </ul>
            </>
          )}

          <div style={{ marginTop: '16px', fontSize: '11px', color: '#98a2b3', borderTop: '1px solid #d3dae6', paddingTop: '8px' }}>
            {insight.model_used && <span>Model: {insight.model_used} · </span>}
            {insight.processing_time_ms && <span>{insight.processing_time_ms}ms · </span>}
            {insight.cached && <span>⚡ Cached</span>}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Mount the React app into Kibana's application container.
 * Returns an unmount function for cleanup.
 */
export function renderApp(coreStart: CoreStart, { element }: AppMountParameters) {
  ReactDOM.render(<ObservabilityApp coreStart={coreStart} />, element);
  return () => ReactDOM.unmountComponentAtNode(element);
}
