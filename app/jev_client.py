"""TypeSafe AI Jev Client - System 1 Parallel Classification Engine (No Fallbacks)."""

import time
import httpx
from app.config import settings
from app.models import (
    TriageRequest,
    JevClassificationResult,
    IntentCategory,
    UrgencyLevel
)

URGENCY_INDEX_MAP = [
    UrgencyLevel.LOW,
    UrgencyLevel.MEDIUM,
    UrgencyLevel.HIGH,
    UrgencyLevel.CRITICAL
]

ACTION_MAP = {
    IntentCategory.ORDER_STATUS: "FETCH_ORDER_TRACKING_AND_DISPATCH",
    IntentCategory.REFUND_REQUEST: "INITIATE_AUTOMATED_REFUND_VERIFICATION",
    IntentCategory.SUBSCRIPTION_CANCEL: "TRIGGER_CANCELLATION_FLOW",
    IntentCategory.AUTHENTICATION_ISSUE: "DISPATCH_MAGIC_LINK_OR_RESET_TOKEN",
    IntentCategory.COMPLEX_TROUBLESHOOTING: "ESCALATE_TO_SYSTEM2_OR_ONCALL",
    IntentCategory.BILLING_DISPUTE: "ESCALATE_TO_BILLING_REVIEW",
    IntentCategory.FEATURE_FEEDBACK: "LOG_PRODUCT_FEEDBACK",
    IntentCategory.UNKNOWN: "ESCALATE_FOR_DEEP_REASONING",
}


class JevClassifierClient:
    """Client for calling TypeSafe Jev System 1 models (/v1/systemone) with zero fallbacks."""

    def __init__(self):
        self.api_key = settings.typesafe_api_key
        self.api_url = settings.typesafe_api_url
        self.model = settings.typesafe_model
        self.cost_per_million_input = 0.042  # $0.042 per MTok ($42 / billion input tokens)

    async def classify(self, request: TriageRequest) -> JevClassificationResult:
        """Classify input text using live TypeSafe Jev API with Choice, Score, and Noul primitives."""
        if not self.api_key:
            raise RuntimeError(
                "TYPESAFE_API_KEY is not configured. Provide a valid TypeSafe API key."
            )

        start_time = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "state": {
                "query": request.query,
                "customer_tier": request.customer_tier,
                "metadata": request.metadata
            },
            "model": self.model,
            "questions": {
                "category": {
                    "type": "choice",
                    "instructions": "Which support category best describes this customer inquiry?",
                    "criteria": {
                        "ORDER_STATUS": "Order tracking, shipping updates, delivery status",
                        "REFUND_REQUEST": "Refunds, duplicate charges, billing returns",
                        "SUBSCRIPTION_CANCEL": "Cancel recurring subscription or membership",
                        "AUTHENTICATION_ISSUE": "Login failures, password resets, 2FA issues",
                        "COMPLEX_TROUBLESHOOTING": "Production outages, HTTP 500 errors, database crashes, bugs",
                        "BILLING_DISPUTE": "Complex invoice or ledger discrepancies",
                        "FEATURE_FEEDBACK": "Product suggestions or feature requests",
                        "UNKNOWN": "Ambiguous or unclassified inquiry"
                    }
                },
                "urgency": {
                    "type": "score",
                    "instructions": "How urgent or time-sensitive is this request?",
                    "criteria": [
                        "Routine question, can wait",
                        "Standard support request",
                        "Time-sensitive customer impact",
                        "Severe production outage or blocker"
                    ]
                },
                "can_auto_resolve": {
                    "type": "noul",
                    "instructions": "Can this request be resolved automatically by a deterministic workflow without human or deep engineering intervention?",
                    "criteria": {
                        "true": "Routine, well-defined action (order lookup, subscription cancel, password reset, standard refund)",
                        "false": "Ambiguous, complex technical outage, or policy question requiring investigation"
                    }
                }
            }
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        latency_ms = (time.perf_counter() - start_time) * 1000

        answers = data["answers"]
        cat_ans = answers["category"]
        urg_ans = answers["urgency"]
        auto_ans = answers["can_auto_resolve"]
        usage = data.get("usage", {})

        category = IntentCategory(cat_ans["choice"])
        urg_score = float(urg_ans["score"])
        urg_idx = min(max(int(round(urg_score)), 0), len(URGENCY_INDEX_MAP) - 1)
        urgency = URGENCY_INDEX_MAP[urg_idx]

        input_tokens = int(usage.get("input_tokens", 0))
        cost_usd = (input_tokens / 1_000_000) * self.cost_per_million_input

        return JevClassificationResult(
            category=category,
            urgency=urgency,
            calibrated_confidence=round(float(cat_ans["confidence"]), 4),
            can_auto_resolve=float(auto_ans["noul"]) >= 0.75,
            suggested_action=ACTION_MAP.get(category, "ESCALATE_FOR_DEEP_REASONING"),
            probabilities=cat_ans["probabilities"],
            latency_ms=round(latency_ms, 2),
            cost_usd=round(cost_usd, 8)
        )
