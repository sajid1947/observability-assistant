/**
 * InsightDisplay component.
 *
 * Renders the InsightResponse from the backend in a visually rich card format.
 * Includes severity badge with color coding, confidence progress bar,
 * and expandable sections for evidence and recommendations.
 */

import React, { useState } from 'react';
import { InsightResponse, SeverityLevel } from '../types';
import { useTheme2 } from '@grafana/ui';

interface Props {
  insight: InsightResponse;
}

/** Map severity levels to display colors. */
const severityColors: Record<SeverityLevel, string> = {
  critical: '#FF4444',
  high: '#FF8C00',
  medium: '#FFD700',
  low: '#4FC3F7',
  info: '#81C784',
};

/** Map severity to human-readable labels. */
const severityLabels: Record<SeverityLevel, string> = {
  critical: '🔴 CRITICAL',
  high: '🟠 HIGH',
  medium: '🟡 MEDIUM',
  low: '🔵 LOW',
  info: '🟢 INFO',
};

export const InsightDisplay: React.FC<Props> = ({ insight }) => {
  const theme = useTheme2();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    evidence: false,
    recommendations: true,
    anomalies: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const confidenceValue = parseInt(insight.confidence.replace('%', ''), 10) || 0;

  const cardStyle: React.CSSProperties = {
    background: theme.colors.background.secondary,
    borderRadius: '8px',
    padding: '16px',
    marginTop: '12px',
    border: `1px solid ${theme.colors.border.weak}`,
  };

  const badgeStyle: React.CSSProperties = {
    display: 'inline-block',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 700,
    color: '#fff',
    backgroundColor: severityColors[insight.severity],
  };

  const sectionHeaderStyle: React.CSSProperties = {
    cursor: 'pointer',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 0',
    borderBottom: `1px solid ${theme.colors.border.weak}`,
    fontWeight: 600,
    fontSize: '13px',
    color: theme.colors.text.primary,
  };

  const progressBarBg: React.CSSProperties = {
    width: '100%',
    height: '8px',
    borderRadius: '4px',
    backgroundColor: theme.colors.background.canvas,
    marginTop: '4px',
  };

  const progressBarFill: React.CSSProperties = {
    width: `${Math.min(confidenceValue, 100)}%`,
    height: '100%',
    borderRadius: '4px',
    backgroundColor: confidenceValue >= 80 ? '#4FC3F7' : confidenceValue >= 50 ? '#FFD700' : '#FF8C00',
    transition: 'width 0.3s ease',
  };

  return (
    <div style={cardStyle}>
      {/* Header: Severity + Confidence */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={badgeStyle}>{severityLabels[insight.severity]}</span>
        <div style={{ textAlign: 'right', fontSize: '12px', color: theme.colors.text.secondary }}>
          <div>Confidence: {insight.confidence}</div>
          <div style={progressBarBg}>
            <div style={progressBarFill} />
          </div>
        </div>
      </div>

      {/* Summary */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontWeight: 600, fontSize: '14px', color: theme.colors.text.primary, marginBottom: '4px' }}>
          Summary
        </div>
        <div style={{ fontSize: '13px', color: theme.colors.text.secondary, lineHeight: 1.5 }}>
          {insight.summary}
        </div>
      </div>

      {/* Root Cause */}
      <div style={{ marginBottom: '12px' }}>
        <div style={{ fontWeight: 600, fontSize: '14px', color: theme.colors.text.primary, marginBottom: '4px' }}>
          Root Cause
        </div>
        <div style={{ fontSize: '13px', color: theme.colors.text.secondary, lineHeight: 1.5 }}>
          {insight.root_cause}
        </div>
      </div>

      {/* Evidence (expandable) */}
      {insight.evidence.length > 0 && (
        <div>
          <div style={sectionHeaderStyle} onClick={() => toggleSection('evidence')}>
            <span>Evidence ({insight.evidence.length})</span>
            <span>{expandedSections.evidence ? '▼' : '▶'}</span>
          </div>
          {expandedSections.evidence && (
            <ul style={{ margin: '8px 0', paddingLeft: '20px', fontSize: '12px', color: theme.colors.text.secondary }}>
              {insight.evidence.map((e, i) => (
                <li key={i} style={{ marginBottom: '4px', lineHeight: 1.4 }}>{e}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Recommendations (expandable) */}
      {insight.recommendations.length > 0 && (
        <div>
          <div style={sectionHeaderStyle} onClick={() => toggleSection('recommendations')}>
            <span>Recommendations ({insight.recommendations.length})</span>
            <span>{expandedSections.recommendations ? '▼' : '▶'}</span>
          </div>
          {expandedSections.recommendations && (
            <ul style={{ margin: '8px 0', paddingLeft: '20px', fontSize: '12px', color: theme.colors.text.secondary }}>
              {insight.recommendations.map((r, i) => (
                <li key={i} style={{ marginBottom: '4px', lineHeight: 1.4 }}>{r}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Anomalies (expandable) */}
      {insight.anomalies_detected.length > 0 && (
        <div>
          <div style={sectionHeaderStyle} onClick={() => toggleSection('anomalies')}>
            <span>Anomalies ({insight.anomalies_detected.length})</span>
            <span>{expandedSections.anomalies ? '▼' : '▶'}</span>
          </div>
          {expandedSections.anomalies && (
            <ul style={{ margin: '8px 0', paddingLeft: '20px', fontSize: '12px', color: theme.colors.text.secondary }}>
              {insight.anomalies_detected.map((a, i) => (
                <li key={i} style={{ marginBottom: '4px', lineHeight: 1.4 }}>{a}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Metadata footer */}
      <div style={{ marginTop: '12px', fontSize: '11px', color: theme.colors.text.disabled, borderTop: `1px solid ${theme.colors.border.weak}`, paddingTop: '8px' }}>
        {insight.model_used && <span>Model: {insight.model_used} · </span>}
        {insight.processing_time_ms && <span>{insight.processing_time_ms}ms · </span>}
        {insight.cached && <span>⚡ Cached · </span>}
        {insight.request_id && <span>ID: {insight.request_id.slice(0, 8)}</span>}
      </div>
    </div>
  );
};
