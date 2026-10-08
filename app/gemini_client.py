"""Gemini Enterprise Agent Platform Client - System 2 Deep Reasoning Engine (No Fallbacks)."""

import time
import json
from google import genai
from google.genai import types
from app.config import settings
from app.models import TriageRequest, GeminiResolutionResult, JevClassificationResult


class GeminiAgentPlatformClient:
    """Client for invoking Gemini models on Google Cloud Agent Platform via the google-genai SDK."""

    def __init__(self):
        self.project = settings.google_cloud_project
        self.location = settings.google_cloud_location
        self.model_name = settings.gemini_model
        self.client = genai.Client(
            vertexai=True,
            project=self.project,
            location=self.location,
        )

    async def resolve_complex_query(
        self, request: TriageRequest, jev_result: JevClassificationResult
    ) -> GeminiResolutionResult:
        """Execute multi-step reasoning using Gemini on Google Cloud Agent Platform."""
        start_time = time.perf_counter()

        user_prompt = f"""You are an expert Google Cloud autonomous resolution agent running on Gemini Enterprise Agent Platform.
A fast System 1 model (TypeSafe Jev) flagged this user query as requiring deep reasoning.
Analyze the problem, identify root causes, draft an empathetic resolution, and decide if human intervention is required.

Incoming Query: "{request.query}"
Customer Tier: {request.customer_tier}
System 1 Preliminary Triage:
- Category: {jev_result.category.value}
- Urgency: {jev_result.urgency.value}
- Calibrated Confidence: {jev_result.calibrated_confidence}

Return strict JSON with keys:
- "reasoning_summary": string
- "generated_response": string
- "suggested_action": string
- "requires_human_escalation": boolean
"""

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        latency_ms = (time.perf_counter() - start_time) * 1000
        data = json.loads(response.text)

        usage = response.usage_metadata
        input_tokens = int((usage.prompt_token_count if usage else 0) or 0)
        output_tokens = int((usage.candidates_token_count if usage else 0) or 0)
        cost = (input_tokens / 1_000_000 * 0.30) + (output_tokens / 1_000_000 * 2.50)

        return GeminiResolutionResult(
            reasoning_summary=data["reasoning_summary"],
            generated_response=data["generated_response"],
            suggested_action=data["suggested_action"],
            requires_human_escalation=bool(data["requires_human_escalation"]),
            latency_ms=round(latency_ms, 2),
            cost_usd=round(cost, 6),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
