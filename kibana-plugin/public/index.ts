/**
 * Kibana plugin — public entry point.
 *
 * Exports the plugin class for Kibana's plugin system to discover and instantiate.
 */

import { ObservabilityAssistantPlugin } from './plugin';

export function plugin() {
  return new ObservabilityAssistantPlugin();
}
