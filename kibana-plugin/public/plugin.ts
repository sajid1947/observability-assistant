/**
 * Kibana client-side plugin class.
 *
 * Registers the Observability Assistant application in Kibana's navigation
 * and mounts the React app when the user navigates to it.
 */

import { AppMountParameters, CoreSetup, CoreStart, Plugin } from '@kbn/core/public';
import {
  ObservabilityAssistantPluginSetup,
  ObservabilityAssistantPluginStart,
} from './types';

export class ObservabilityAssistantPlugin
  implements Plugin<ObservabilityAssistantPluginSetup, ObservabilityAssistantPluginStart>
{
  public setup(core: CoreSetup): ObservabilityAssistantPluginSetup {
    // Register the application in Kibana's navigation
    core.application.register({
      id: 'observabilityAssistant',
      title: 'AI Observability Assistant',
      async mount(params: AppMountParameters) {
        // Lazy-load the app component to avoid bundling React with the plugin manifest
        const { renderApp } = await import('./components/ObservabilityApp');
        const [coreStart] = await core.getStartServices();
        return renderApp(coreStart, params);
      },
    });

    return {};
  }

  public start(core: CoreStart): ObservabilityAssistantPluginStart {
    return {};
  }

  public stop() {}
}
