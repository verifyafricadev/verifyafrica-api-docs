import { RuntimeExtensions } from "@zuplo/runtime";
import { McpGatewayPlugin } from "@zuplo/runtime/mcp-gateway";

// To enable the optional examples below, install the relevant package(s) and
// uncomment the matching import:
// import { OpenTelemetryPlugin } from "@zuplo/otel";
// import { DataDogLoggingPlugin, environment } from "@zuplo/runtime";

/**
 * `runtimeInit` runs once when your gateway boots. Use it to register plugins
 * and lifecycle hooks. Docs:
 * https://zuplo.com/docs/programmable-api/runtime-extensions
 */
export function runtimeInit(runtime: RuntimeExtensions) {
  // --- MCP Gateway ---------------------------------------------------------
  // Registers the MCP Gateway, which adds the OAuth and upstream-connection
  // routes used to expose and secure MCP servers through your gateway. It is a
  // no-op until you add an MCP route/policy, so it is safe to leave enabled.
  // Docs: https://zuplo.com/docs/mcp-server/introduction
  //
  // Remove this plugin if you are not using the MCP Gateway features.
  runtime.addPlugin(
    new McpGatewayPlugin({
      // basePath: "/", // defaults to /__zuplo
    })
  );

  // --- OpenTelemetry tracing (optional) ------------------------------------
  // Export traces and logs to any OpenTelemetry-compatible backend (Honeycomb,
  // Grafana, Dynatrace, and others). Requires the `@zuplo/otel` package and the
  // import above.
  // Docs: https://zuplo.com/docs/articles/opentelemetry
  //
  // runtime.addPlugin(
  //   new OpenTelemetryPlugin({
  //     exporter: {
  //       url: "https://otel-collector.example.com/v1/traces",
  //       headers: { "api-key": environment.OTEL_API_KEY },
  //     },
  //     service: { name: "my-api", version: "1.0.0" },
  //   }),
  // );

  // --- Datadog logging (optional) ------------------------------------------
  // Ship request logs to Datadog. Other log integrations (New Relic, Splunk,
  // Loki, Dynatrace, and others) follow the same pattern — see the logging
  // overview at https://zuplo.com/docs/articles/logging.
  // Docs: https://zuplo.com/docs/articles/log-plugin-datadog
  //
  // runtime.addPlugin(
  //   new DataDogLoggingPlugin({
  //     apiKey: environment.DATADOG_API_KEY,
  //     source: "my-api",
  //   }),
  // );
}
