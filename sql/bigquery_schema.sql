-- ==============================================================================
-- BigQuery Telemetry Table Schema for AI Gateway Metrics
-- ==============================================================================

CREATE SCHEMA IF NOT EXISTS `ai_gateway_telemetry`
OPTIONS(
  location="US"
);

CREATE TABLE IF NOT EXISTS `ai_gateway_telemetry.gateway_metrics`
(
  timestamp TIMESTAMP OPTIONS(description="UTC timestamp of the gateway request"),
  query STRING OPTIONS(description="Truncated user inquiry or event payload"),
  route_taken STRING OPTIONS(description="FAST_PATH_JEV or SLOW_PATH_GEMINI"),
  overall_latency_ms FLOAT64 OPTIONS(description="End-to-end processing latency in ms"),
  overall_cost_usd FLOAT64 OPTIONS(description="Total blended cost in USD"),
  category STRING OPTIONS(description="Classified intent category"),
  confidence FLOAT64 OPTIONS(description="Jev calibrated RLCD confidence score (0.0 to 1.0)"),
  final_action STRING OPTIONS(description="Dispatched execution action")
)
PARTITION BY DATE(timestamp)
CLUSTER BY route_taken, category;
