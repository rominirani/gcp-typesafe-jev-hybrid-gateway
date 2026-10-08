"""Domain Models and Strict Data Contracts for Type-Safe AI Gateway."""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    """Categorical classification domains for incoming requests."""
    ORDER_STATUS = "ORDER_STATUS"
    REFUND_REQUEST = "REFUND_REQUEST"
    SUBSCRIPTION_CANCEL = "SUBSCRIPTION_CANCEL"
    AUTHENTICATION_ISSUE = "AUTHENTICATION_ISSUE"
    COMPLEX_TROUBLESHOOTING = "COMPLEX_TROUBLESHOOTING"
    BILLING_DISPUTE = "BILLING_DISPUTE"
    FEATURE_FEEDBACK = "FEATURE_FEEDBACK"
    UNKNOWN = "UNKNOWN"


class UrgencyLevel(str, Enum):
    """Triage priority level."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RouteTarget(str, Enum):
    """Execution route taken by the gateway."""
    FAST_PATH_JEV = "FAST_PATH_JEV"
    SLOW_PATH_GEMINI = "SLOW_PATH_GEMINI"


class TriageRequest(BaseModel):
    """Incoming user inquiry or webhook payload."""
    query: str = Field(..., description="Raw text of customer inquiry or event.")
    customer_tier: Optional[str] = Field(default="STANDARD", description="Customer tier: STANDARD, PREMIUM, ENTERPRISE.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Arbitrary context payload.")


class JevClassificationResult(BaseModel):
    """Structured response from TypeSafe Jev System 1 model."""
    category: IntentCategory
    urgency: UrgencyLevel
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0, description="Epistemic probability from RLCD.")
    can_auto_resolve: bool = Field(..., description="Whether action can proceed without human/generative review.")
    suggested_action: str
    probabilities: Dict[str, float] = Field(default_factory=dict, description="Parallel output probabilities.")
    latency_ms: float
    cost_usd: float


class GeminiResolutionResult(BaseModel):
    """Structured response from Gemini on Google Cloud Agent Platform."""
    reasoning_summary: str
    generated_response: str
    suggested_action: str
    requires_human_escalation: bool
    latency_ms: float
    cost_usd: float
    input_tokens: int
    output_tokens: int


class GatewayResponse(BaseModel):
    """Final unified response returned to client."""
    request_query: str
    route_taken: RouteTarget
    overall_latency_ms: float
    overall_cost_usd: float
    system1_jev: JevClassificationResult
    system2_gemini: Optional[GeminiResolutionResult] = None
    final_action: str
    resolution_payload: Dict[str, Any]
    routing_reason: str
