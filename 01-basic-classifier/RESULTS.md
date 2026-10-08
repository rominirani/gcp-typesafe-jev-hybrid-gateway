# Stage 01: Live Verification & Test Verdicts (Google Cloud Run)

**Target Environment:**
* **GCP Project:** `YOUR_PROJECT_ID`
* **Region:** `us-central1`
* **Cloud Run Service:** `jev-basic-classifier`
* **Service URL:** `https://jev-basic-classifier-<PROJECT_NUMBER>.us-central1.run.app` (`${SERVICE_URL}`)
* **API Documentation (Swagger UI):** `${SERVICE_URL}/docs`

---

## Live Test 1: High-Confidence Auto-Resolvable Inquiry (Order Tracking)

### Request:
```bash
curl -X POST "${SERVICE_URL}/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "Where is my order #19028? Can you tell me when it arrives?"}'
```

### Verbatim Response (HTTP 200 OK):
```json
{
  "query": "Where is my order #19028? Can you tell me when it arrives?",
  "category": "ORDER_STATUS",
  "urgency": "LOW",
  "calibrated_confidence": 0.985,
  "can_auto_resolve": true,
  "suggested_action": "DISPATCH_ORDER_TRACKING",
  "probabilities": {
    "ORDER_STATUS": 0.985,
    "REFUND_REQUEST": 0.01,
    "UNKNOWN": 0.005
  },
  "latency_ms": 40.55,
  "platform": "Google Cloud Run"
}
```
* **Verdict:** ✅ **PASS**. Execution took **40.55ms** on Cloud Run. Confidence is **98.5%** with `can_auto_resolve: true`.

---

## Live Test 2: High-Confidence Subscription Cancellation

### Request:
```bash
curl -X POST "${SERVICE_URL}/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "Please cancel my subscription before next billing cycle."}'
```

### Verbatim Response (HTTP 200 OK):
```json
{
  "query": "Please cancel my subscription before next billing cycle.",
  "category": "SUBSCRIPTION_CANCEL",
  "urgency": "MEDIUM",
  "calibrated_confidence": 0.962,
  "can_auto_resolve": true,
  "suggested_action": "INITIATE_CANCELLATION",
  "probabilities": {
    "SUBSCRIPTION_CANCEL": 0.962,
    "UNKNOWN": 0.038
  },
  "latency_ms": 40.83,
  "platform": "Google Cloud Run"
}
```
* **Verdict:** ✅ **PASS**. Execution took **40.83ms** on Cloud Run. Confidence is **96.2%** with `can_auto_resolve: true`.

---

## Live Test 3: Complex Outage Requiring Escalation

### Request:
```bash
curl -X POST "${SERVICE_URL}/classify" \
  -H "Content-Type: application/json" \
  -d '{"query": "CRITICAL: Database connection pool exhausted with 500 error on checkout."}'
```

### Verbatim Response (HTTP 200 OK):
```json
{
  "query": "CRITICAL: Database connection pool exhausted with 500 error on checkout.",
  "category": "COMPLEX_TROUBLESHOOTING",
  "urgency": "CRITICAL",
  "calibrated_confidence": 0.88,
  "can_auto_resolve": false,
  "suggested_action": "ESCALATE_TO_ONCALL",
  "probabilities": {
    "COMPLEX_TROUBLESHOOTING": 0.88,
    "UNKNOWN": 0.12
  },
  "latency_ms": 40.37,
  "platform": "Google Cloud Run"
}
```
* **Verdict:** ✅ **PASS**. Execution took **40.37ms** on Cloud Run.
* **Key Behavioral Insight:** Jev correctly flags that `calibrated_confidence` is **0.88** (below the 0.90 threshold) and sets `can_auto_resolve: false`. This provides the exact trigger for **Stage 02 (Hybrid Gateway with Gemini Enterprise Agent Platform)**.
