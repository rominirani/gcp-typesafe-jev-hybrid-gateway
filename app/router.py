"""Core Router: Dispatches between System 1 (Jev) and System 2 (Gemini)."""

import time
from typing import Dict, Any
from app.config import settings
from app.models import (
    TriageRequest,
    GatewayResponse,
    RouteTarget,
    IntentCategory
)
from app.jev_client import JevClassifierClient
from app.gemini_client import GeminiAgentPlatformClient


class HybridAIRouter:
    """Orchestrates fast-path reflexes vs slow-path reasoning based on calibrated confidence."""

    def __init__(self):
        self.jev_client = JevClassifierClient()
        self.gemini_client = GeminiAgentPlatformClient()
        self.confidence_threshold = settings.confidence_threshold

    async def process_request(self, request: TriageRequest) -> GatewayResponse:
        """Route incoming query using Jev's RLCD confidence score."""
        overall_start = time.perf_counter()

        # Step 1: Run System 1 Reflex Classification (Sub-100ms)
        jev_result = await self.jev_client.classify(request)

        # Step 2: Evaluate Routing Policy
        # Criteria for Fast Path:
        # 1. Calibrated confidence >= threshold (e.g. 0.90)
        # 2. Model marks the intent as auto-resolvable
        # 3. Intent is not explicitly COMPLEX_TROUBLESHOOTING or UNKNOWN
        is_high_confidence = jev_result.calibrated_confidence >= self.confidence_threshold
        is_deterministic_intent = jev_result.category not in [
            IntentCategory.COMPLEX_TROUBLESHOOTING,
            IntentCategory.UNKNOWN
        ]

        if is_high_confidence and jev_result.can_auto_resolve and is_deterministic_intent:
            # FAST PATH: Resolve immediately without invoking generative LLM
            overall_latency_ms = (time.perf_counter() - overall_start) * 1000

            final_action = f"AUTO_EXECUTE_{jev_result.suggested_action}"
            resolution_payload = {
                "status": "COMPLETED",
                "action": final_action,
                "dispatch_message": f"Automatically handled via System 1 reflex for category '{jev_result.category.value}'.",
                "confidence_score": jev_result.calibrated_confidence
            }

            routing_reason = (
                f"Fast-path selected: Jev calibrated confidence ({jev_result.calibrated_confidence:.3f}) "
                f"meets or exceeds threshold ({self.confidence_threshold:.2f})."
            )

            response = GatewayResponse(
                request_query=request.query,
                route_taken=RouteTarget.FAST_PATH_JEV,
                overall_latency_ms=round(overall_latency_ms, 2),
                overall_cost_usd=jev_result.cost_usd,
                system1_jev=jev_result,
                system2_gemini=None,
                final_action=final_action,
                resolution_payload=resolution_payload,
                routing_reason=routing_reason
            )

        else:
            # SLOW PATH: Escalate to Gemini on Google Cloud Agent Platform for deep reasoning
            routing_reason = (
                f"Slow-path selected: Jev calibrated confidence ({jev_result.calibrated_confidence:.3f}) "
                f"is below threshold ({self.confidence_threshold:.2f}) or requires generative reasoning."
            )

            gemini_result = await self.gemini_client.resolve_complex_query(request, jev_result)
            overall_latency_ms = (time.perf_counter() - overall_start) * 1000
            total_cost = jev_result.cost_usd + gemini_result.cost_usd

            resolution_payload = {
                "status": "ESCALATED_REASONING",
                "gemini_summary": gemini_result.reasoning_summary,
                "response_text": gemini_result.generated_response,
                "requires_human": gemini_result.requires_human_escalation
            }

            response = GatewayResponse(
                request_query=request.query,
                route_taken=RouteTarget.SLOW_PATH_GEMINI,
                overall_latency_ms=round(overall_latency_ms, 2),
                overall_cost_usd=round(total_cost, 6),
                system1_jev=jev_result,
                system2_gemini=gemini_result,
                final_action=gemini_result.suggested_action,
                resolution_payload=resolution_payload,
                routing_reason=routing_reason
            )

        # Async telemetry emission
        await self._log_telemetry(response)

        return response

    async def _log_telemetry(self, response: GatewayResponse):
        """Optionally stream metrics to BigQuery."""
        if not settings.enable_bigquery_telemetry:
            return

        try:
            from google.cloud import bigquery
            client = bigquery.Client(project=settings.google_cloud_project)
            table_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{settings.bigquery_table}"

            rows_to_insert = [{
                "timestamp": bigquery.Timestamp.from_timestamp(time.time()),
                "query": response.request_query[:256],
                "route_taken": response.route_taken.value,
                "overall_latency_ms": response.overall_latency_ms,
                "overall_cost_usd": response.overall_cost_usd,
                "category": response.system1_jev.category.value,
                "confidence": response.system1_jev.calibrated_confidence,
                "final_action": response.final_action
            }]
            client.insert_rows_json(table_id, rows_to_insert)
        except Exception:
            # Telemetry logging should never block the critical request path
            pass
