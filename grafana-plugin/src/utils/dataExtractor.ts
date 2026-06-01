/**
 * Data extractor utility.
 *
 * Extracts metrics, labels, and time range from Grafana's DataFrames.
 * This bridges Grafana's internal data format with our backend API format.
 */

import { PanelData, DataFrame, FieldType } from '@grafana/data';
import { MetricData, TimeRange } from '../types';

/**
 * Extract all metrics from a Grafana PanelData object.
 *
 * Iterates through all DataFrames (series) in the panel data,
 * extracting numeric fields as metrics with their associated
 * timestamps and labels.
 *
 * @param data - Grafana PanelData from PanelProps
 * @returns Array of MetricData objects for the backend API
 */
export function extractMetrics(data: PanelData): MetricData[] {
  const metrics: MetricData[] = [];

  for (const frame of data.series) {
    // Find time field
    const timeField = frame.fields.find((f) => f.type === FieldType.time);

    // Extract all numeric fields as metrics
    const numericFields = frame.fields.filter(
      (f) => f.type === FieldType.number
    );

    for (const field of numericFields) {
      const metricName = field.name || frame.name || 'unknown_metric';

      // Collect values
      const values: (number | null)[] = [];
      const timestamps: string[] = [];

      for (let i = 0; i < field.values.length; i++) {
        const val = field.values.get ? field.values.get(i) : (field.values as any)[i];
        values.push(val !== undefined && val !== null ? Number(val) : null);

        if (timeField) {
          const ts = timeField.values.get
            ? timeField.values.get(i)
            : (timeField.values as any)[i];
          timestamps.push(new Date(ts).toISOString());
        }
      }

      // Extract labels from field config
      const labels: Record<string, string> = {};
      if (field.labels) {
        Object.entries(field.labels).forEach(([k, v]) => {
          labels[k] = String(v);
        });
      }
      // Also check frame-level labels
      if ((frame as any).labels) {
        Object.entries((frame as any).labels).forEach(([k, v]) => {
          labels[k] = String(v);
        });
      }

      metrics.push({
        name: metricName,
        values,
        timestamps,
        labels,
      });
    }
  }

  return metrics;
}

/**
 * Extract the current time range from PanelData.
 *
 * @param data - Grafana PanelData
 * @returns TimeRange object with ISO 8601 strings
 */
export function extractTimeRange(data: PanelData): TimeRange {
  const timeRange = data.timeRange;
  return {
    start: timeRange.from.toISOString(),
    end: timeRange.to.toISOString(),
  };
}

/**
 * Collect all unique labels/tags across all series.
 *
 * @param data - Grafana PanelData
 * @returns Combined labels dictionary
 */
export function extractLabels(data: PanelData): Record<string, string> {
  const labels: Record<string, string> = {};

  for (const frame of data.series) {
    for (const field of frame.fields) {
      if (field.labels) {
        Object.entries(field.labels).forEach(([k, v]) => {
          labels[k] = String(v);
        });
      }
    }
  }

  return labels;
}
