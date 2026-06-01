/**
 * Kibana server-side plugin class.
 *
 * Registers server-side proxy routes that forward requests from the
 * Kibana browser client to the observability assistant backend.
 * This avoids CORS issues since all requests go through Kibana's server.
 */

import { CoreSetup, CoreStart, Plugin, Logger, PluginInitializerContext } from '@kbn/core/server';
import { registerRoutes } from './routes';

export class ObservabilityAssistantServerPlugin implements Plugin {
  private readonly logger: Logger;

  constructor(initializerContext?: PluginInitializerContext) {
    this.logger = initializerContext
      ? initializerContext.logger.get()
      : console as unknown as Logger;
  }

  public setup(core: CoreSetup) {
    const router = core.http.createRouter();
    registerRoutes(router, this.logger);
    return {};
  }

  public start(core: CoreStart) {
    return {};
  }

  public stop() {}
}
