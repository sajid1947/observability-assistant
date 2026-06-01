/**
 * Plugin module entry point.
 *
 * Registers the ObservabilityPanel component as a Grafana panel plugin.
 * This is the file Grafana loads when the plugin is initialized.
 */

import { PanelPlugin } from '@grafana/data';
import { ObservabilityPanel } from './components/ObservabilityPanel';
import { ObservabilityOptions, defaults } from './types';

export const plugin = new PanelPlugin<ObservabilityOptions>(ObservabilityPanel)
  .setPanelOptions((builder) => {
    builder
      .addTextInput({
        path: 'backendUrl',
        name: 'Backend API URL',
        description: 'URL of the observability assistant backend (e.g., http://localhost:8080)',
        defaultValue: defaults.backendUrl,
      })
      .addTextInput({
        path: 'apiKey',
        name: 'API Key',
        description: 'API key for backend authentication',
        defaultValue: defaults.apiKey,
      })
      .addBooleanSwitch({
        path: 'autoAnalyze',
        name: 'Auto-Analyze',
        description: 'Automatically analyze data on every panel refresh',
        defaultValue: defaults.autoAnalyze,
      });
  });
