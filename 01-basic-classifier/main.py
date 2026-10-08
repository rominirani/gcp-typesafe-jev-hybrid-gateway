"""Standalone Jev Classification Microservice on Google Cloud Run (No Fallbacks)."""

import os
import time
from typing import Dict
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Jev Standalone Classifier on Cloud Run",
    description="Stage 01: Deploying TypeSafe Jev System 1 intelligence to Cloud Run.",
    version="1.0.0"
)

TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY", "")
TYPESAFE_API_URL = os.getenv("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
TYPESAFE_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest")

URGENCY_LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

ACTION_MAP = {
    "ORDER_STATUS": "DISPATCH_ORDER_TRACKING",
    "REFUND_REQUEST": "VALIDATE_REFUND_POLICY",
    "SUBSCRIPTION_CANCEL": "INITIATE_CANCELLATION",
    "AUTHENTICATION_ISSUE": "DISPATCH_AUTH_RESET",
    "COMPLEX_TROUBLESHOOTING": "ESCALATE_TO_ONCALL",
    "BILLING_DISPUTE": "ESCALATE_TO_BILLING_SPECIALIST",
    "FEATURE_FEEDBACK": "LOG_PRODUCT_FEEDBACK",
}


class ClassificationRequest(BaseModel):
    query: str = Field(..., description="Unstructured user inquiry or event string.")


class ClassificationResponse(BaseModel):
    query: str
    model: str
    category: str
    urgency: str
    urgency_score: float
    calibrated_confidence: float
    can_auto_resolve: bool
    auto_resolve_noul: float
    suggested_action: str
    probabilities: Dict[str, float]
    input_tokens: int
    output_tokens: int
    latency_ms: float
    platform: str = "Google Cloud Run"


@app.get("/health")
def health_check():
    """Health check endpoint."""
    if not TYPESAFE_API_KEY:
        raise HTTPException(status_code=500, detail="TYPESAFE_API_KEY is not configured.")
    return {
        "status": "healthy",
        "model": TYPESAFE_MODEL,
        "service": "jev-basic-classifier"
    }


@app.post("/classify", response_model=ClassificationResponse)
async def classify_text(req: ClassificationRequest):
    """Classify input text using live TypeSafe Jev API (/v1/systemone)."""
    if not TYPESAFE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="TYPESAFE_API_KEY environment variable is required."
        )

    start_time = time.perf_counter()

    payload = {
        "state": req.query,
        "model": TYPESAFE_MODEL,
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
                    "FEATURE_FEEDBACK": "Product suggestions or feature requests"
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

    headers = {
        "Authorization": f"Bearer {TYPESAFE_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(TYPESAFE_API_URL, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"TypeSafe API error: {response.text}"
            )
        data = response.json()

    latency_ms = (time.perf_counter() - start_time) * 1000

    answers = data["answers"]
    cat_ans = answers["category"]
    urg_ans = answers["urgency"]
    auto_ans = answers["can_auto_resolve"]
    usage = data.get("usage", {})

    choice_val = cat_ans["choice"]
    urg_score = float(urg_ans["score"])
    urg_idx = min(max(int(round(urg_score)), 0), len(URGENCY_LABELS) - 1)
    noul_val = float(auto_ans["noul"])

    return ClassificationResponse(
        query=req.query,
        model=data.get("model", TYPESAFE_MODEL),
        category=choice_val,
        urgency=URGENCY_LABELS[urg_idx],
        urgency_score=round(urg_score, 3),
        calibrated_confidence=round(float(cat_ans["confidence"]), 4),
        can_auto_resolve=noul_val >= 0.75,
        auto_resolve_noul=round(noul_val, 4),
        suggested_action=ACTION_MAP.get(choice_val, "ESCALATE_FOR_CLARIFICATION"),
        probabilities=cat_ans["probabilities"],
        input_tokens=int(usage.get("input_tokens", 0)),
        output_tokens=int(usage.get("output_tokens", 0)),
        latency_ms=round(latency_ms, 2)
    )
