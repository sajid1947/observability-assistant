/**
 * Kibana server-side plugin entry point.
 */

import { ObservabilityAssistantServerPlugin } from './plugin';

export function plugin() {
  return new ObservabilityAssistantServerPlugin();
}
