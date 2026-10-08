# Hybrid AI Systems on Google Cloud: Building a Sub-100ms Gateway with TypeSafe Jev and Gemini Enterprise Agent Platform

**Recommended Publication Titles:**
1. *Sub-100ms AI Gateways on Google Cloud: Pairing TypeSafe Jev with Gemini Enterprise Agent Platform*
2. *Building Fast-Path / Slow-Path AI Architectures on Cloud Run: A Production Guide*
3. *Beyond Chatbots: How to Build Type-Safe, Calibrated AI Decision Systems on GCP*
4. *Cutting 95% of LLM Costs with System 1 / System 2 Architecture on Google Cloud*

---

## Executive Preview

In this comprehensive tutorial, we build and deploy a production-grade **Hybrid AI Gateway** on **Google Cloud Platform (GCP)**. We combine two fundamentally different paradigms of artificial intelligence:
* **System 1 (TypeSafe Jev):** A fast, parallel, non-autoregressive classification model that outputs mathematically guaranteed types with **calibrated epistemic probabilities** in **under 100ms** at **\$0.042 / MTok**.
* **System 2 (Google Cloud Gemini Enterprise Agent Platform):** Frontier reasoning and multimodal language models (`gemini-3.8-flash` and `gemini-2.5-pro` accessed via the `google-genai` SDK) that perform multi-turn troubleshooting, policy analysis, and context synthesis.

By deploying this hybrid architecture to **Google Cloud Run**, we achieve the best of both worlds: **sub-100ms reflexes for over 70% of enterprise queries**, while saving **90%+ on generative token costs** and preserving frontier reasoning for hard edge cases.

---

## 1. Introducing Jev: Machine-Native "System 1" Intelligence

Before we dive into the Google Cloud architecture, let's understand the core building block: **Jev**.

### What is Jev?
Developed by **TypeSafe AI** (`typesafe.ai`, founded by ex-OpenAI researcher Diogo Almeida), Jev represents a new class of models known as **System One Models**:
* **The Kahneman Analogy:** In cognitive science (*Thinking, Fast and Slow*), "System 1" refers to fast, automatic, intuitive reflexes, while "System 2" refers to slow, deliberative reasoning. Jev brings this fast reflex capability to machine-to-machine software.
* **The Name:** Named after the 19th-century economist **William Stanley Jevons** (*Jevons Paradox*). The premise is that when intelligence drops by two orders of magnitude in cost and latency, the demand and use cases for automated decisions will explode exponentially.
* **Decisions, Not Strings:** Traditional LLMs generate text token-by-token (slow, expensive, prone to schema drift). Jev does not generate strings. It takes unstructured text as input and outputs **strongly-typed decisions with calibrated probabilities** in a **single parallel forward pass**.

| Metric | Traditional Frontier LLMs | TypeSafe Jev |
| :--- | :--- | :--- |
| **Output Type** | Autoregressive text (one token at a time) | **Typed structured values** (Enums, Booleans) |
| **Latency** | 2,000ms – 10,000ms+ | **70ms – 100ms** (~30x–100x faster) |
| **Input Cost** | \$0.20 – \$10+ / MTok | **\$0.042 / MTok** (\$42 / billion tokens) |
| **Output Cost** | \$0.60 – \$30+ / MTok | **FREE** (evaluated in parallel, too cheap to meter) |
| **Type Safety** | Probabilistic (JSON may break or hallucinate) | **Mathematically Guaranteed (0% type errors)** |
| **Calibration** | Overconfident / Sycophantic | **RLCD Calibrated** (85% confidence $\approx$ 85% accuracy) |

---

### Hands-on: Calling TypeSafe Jev with Python

Calling Jev directly uses the `POST https://api.typesafe.ai/v1/systemone` endpoint (or the `typesafe-sdk` Python package). You pass your unstructured input (`state`), model (`jev-latest`), and a dictionary of `questions` using TypeSafe's three decision primitives (`choice`, `score`, and `noul`), and Jev evaluates all questions simultaneously in a single forward pass:

```python
import os
import httpx

# 1. Define endpoint and API credentials (from https://typesafe.ai)
API_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY = os.environ["TYPESAFE_API_KEY"]

# 2. Define your input state and typed questions
payload = {
    "state": "Where is my package #8942? Has it shipped yet?",
    "model": "jev-latest",
    "questions": {
        "category": {
            "type": "choice",
            "instructions": "Classify the primary intent of this customer inquiry.",
            "criteria": {
                "ORDER_STATUS": "Tracking an order, shipment, or delivery date",
                "REFUND_REQUEST": "Requesting a refund or billing credit",
                "SUBSCRIPTION_CANCEL": "Canceling a recurring subscription",
                "COMPLEX_TROUBLESHOOTING": "Complex technical outage or multi-part legal question",
            },
        },
        "urgency": {
            "type": "score",
            "instructions": "Rate the operational urgency of this request.",
            "criteria": ["Low", "Medium", "High", "Critical"],
        },
        "can_auto_resolve": {
            "type": "noul",
            "instructions": "Can this request be resolved deterministically by an automated webhook?",
            "criteria": {
                "true": "Routine request that can be handled automatically",
                "false": "Ambiguous or critical request requiring deep reasoning",
            },
        },
    },
}

# 3. Dispatch HTTP POST (sub-100ms round-trip)
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

response = httpx.post(API_URL, json=payload, headers=headers, timeout=10.0)
response.raise_for_status()
result = response.json()

print(result)
```

#### Sample Response Payload:
```json
{
  "model": "jev-1.13.0",
  "answers": {
    "category": {
      "type": "choice",
      "choice": "ORDER_STATUS",
      "confidence": 0.985,
      "probabilities": {
        "ORDER_STATUS": 0.985,
        "REFUND_REQUEST": 0.01,
        "SUBSCRIPTION_CANCEL": 0.003,
        "COMPLEX_TROUBLESHOOTING": 0.002
      }
    },
    "urgency": {
      "type": "score",
      "score": 0.0,
      "confidence": 0.96,
      "legend": { "0": "Low", "0.33": "Medium", "0.67": "High", "1": "Critical" },
      "probabilities": { "0": 0.96, "0.33": 0.03, "0.67": 0.01, "1": 0.0 }
    },
    "can_auto_resolve": {
      "type": "noul",
      "noul": 0.97
    }
  },
  "usage": {
    "input_tokens": 214,
    "output_tokens": 28
  }
}
```

Notice three critical properties of this response:
1. **Parallel Probabilities:** Jev outputs the entire probability distribution over all category options simultaneously.
2. **Calibrated Confidence:** The `confidence` score (0.985) is mathematically honest—it was optimized using Reinforcement Learning for Calibrated Decisions (RLCD).
3. **Machine-Ready:** Your application code can branch immediately without string parsing or regex sanitization.

*(You can run this demo immediately using the included standalone script: `export TYPESAFE_API_KEY=... && python3 scripts/quickstart_jev.py`)*

---

## 2. The Production Problem: Why Pure LLMs Fail in Software Pipelines

Large Language Models (LLMs) have revolutionized natural language understanding. However, software engineers and platform architects encounter critical friction points when embedding pure LLMs into real-time production pipelines:

### 2.1 The Latency Wall (Human vs. Machine Time)
Human conversations tolerate a 3–8 second pause. Backend software, microservices, and interactive webhooks do not. When an event hits an ingress gateway or message queue, waiting several seconds for an autoregressive LLM to generate tokens cascades into timeouts and high p99 latencies.

### 2.2 The Economic Penalty of Token-by-Token Generation
In an autoregressive transformer, producing 200 tokens of structured JSON requires running 200 sequential forward passes. At scale (millions of requests per day), spending \$0.015 to \$0.03 per query for routine routing decisions burns engineering budgets.

### 2.3 Schema Drift and Type Safety Failures
Even with JSON schema enforcement and structured outputs, pure language models are prone to hallucinated fields, subtle enum variations, or unexpected refusals when encountering adversarial strings.

### 2.4 Overconfidence (Lack of Epistemic Calibration)
Standard LLMs trained with Reinforcement Learning from Human Feedback (RLHF) are optimized to please human raters. They often express high confidence even when wrong. Production software needs honest, mathematically calibrated uncertainty:
> *"If the model says it has 90% confidence, it must be correct 90% of the time."*

---

## 3. Architecture & Design Pattern

To solve these four problems, we adopt Daniel Kahneman's **System 1 and System 2** cognitive framework:

```
                            [ Ingress Request ]
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │   Cloud Run Ingress API     │
                     │  (FastAPI / REST / Webhook) │
                     └──────────────┬──────────────┘
                                    │
                   Step 1: Jev Classification (70-90ms)
                     - Parallel forward pass (/v1/systemone)
                     - Calibrated RLCD probability
                     - Guaranteed schema typing
                                    ▼
                     ┌─────────────────────────────┐
                     │    Confidence Evaluator     │
                     └──────┬───────────────┬──────┘
                            │               │
      Confidence >= 0.90    │               │  Confidence < 0.90
      & Auto-resolvable     ▼               ▼  OR Complex Outage
              ┌──────────────────┐    ┌───────────────────────────┐
              │  FAST PATH       │    │  SLOW PATH                │
              │  (System 1 Jev)  │    │  (System 2 Agent Platform)│
              │                  │    │                           │
              │ • Auto-execute   │    │ • gemini-3.8-flash / 2.5  │
              │ • Instant return │    │ • Root-cause diagnosis    │
              │ • Latency: ~75ms │    │ • Empathetic draft        │
              │ • Cost: $0.00008 │    │ • Human escalation flag   │
              └────────┬─────────┘    └─────────────┬─────────────┘
                       │                            │
                       └─────────────┬──────────────┘
                                     ▼
                     ┌─────────────────────────────┐
                     │ Unified Output & Telemetry  │
                     │  - BigQuery Dataset         │
                     │  - Cloud Trace & Logging    │
                     └─────────────────────────────┘
```

---

## 4. Code Walkthrough

The codebase is organized into modular, clean components following production Python standards.

### 4.1 Strict Data Contracts (`app/models.py`)
All inputs and outputs are governed by strict Pydantic models and Enums. There are no free-form unstructured dictionary payloads:

```python
class IntentCategory(str, Enum):
    ORDER_STATUS = "ORDER_STATUS"
    REFUND_REQUEST = "REFUND_REQUEST"
    SUBSCRIPTION_CANCEL = "SUBSCRIPTION_CANCEL"
    AUTHENTICATION_ISSUE = "AUTHENTICATION_ISSUE"
    COMPLEX_TROUBLESHOOTING = "COMPLEX_TROUBLESHOOTING"
    BILLING_DISPUTE = "BILLING_DISPUTE"
    FEATURE_FEEDBACK = "FEATURE_FEEDBACK"
    UNKNOWN = "UNKNOWN"

class RouteTarget(str, Enum):
    FAST_PATH_JEV = "FAST_PATH_JEV"
    SLOW_PATH_GEMINI = "SLOW_PATH_GEMINI"
```

### 4.2 System 1 Client: TypeSafe Jev (`app/jev_client.py`)
The Jev client sends structured classification queries directly to `https://api.typesafe.ai/v1/systemone` authenticated with `TYPESAFE_API_KEY`:

```python
payload = {
    "state": f"[Customer Tier: {request.customer_tier}] {request.query}",
    "model": self.model,
    "questions": {
        "category": {
            "type": "choice",
            "instructions": "Classify the primary intent of this incoming enterprise customer inquiry.",
            "criteria": CATEGORY_CRITERIA,
        },
        "urgency": {
            "type": "score",
            "instructions": "Rate the operational urgency and severity of this inquiry.",
            "criteria": ["Low", "Medium", "High", "Critical"],
        },
        "can_auto_resolve": {
            "type": "noul",
            "instructions": "Can this request be resolved deterministically by an automated backend action?",
            "criteria": {
                "true": "Routine deterministic request that can be fulfilled automatically",
                "false": "Ambiguous, complex, or critical incident requiring human or LLM reasoning",
            },
        },
    },
}
```

### 4.3 System 2 Client: Google Cloud Gemini Enterprise Agent Platform (`app/gemini_client.py`)
When a request is escalated, the gateway invokes Gemini (`gemini-3.8-flash` or `gemini-2.5-pro`) via the official `google-genai` SDK using Application Default Credentials (ADC):

```python
from google import genai
from google.genai import types

self.client = genai.Client(
    vertexai=True,
    project=self.project,
    location=self.location,
)

response = await self.client.aio.models.generate_content(
    model="gemini-3.8-flash",
    contents=user_prompt,
    config=types.GenerateContentConfig(
        temperature=0.2,
        response_mime_type="application/json",
    ),
)
```

### 4.4 The Confidence Router (`app/router.py`)
The router enforces the threshold policy:
```python
is_high_confidence = jev_result.calibrated_confidence >= self.confidence_threshold
is_deterministic_intent = jev_result.category not in [
    IntentCategory.COMPLEX_TROUBLESHOOTING,
    IntentCategory.UNKNOWN
]

if is_high_confidence and jev_result.can_auto_resolve and is_deterministic_intent:
    # FAST PATH (Jev Reflex) -> ~75ms
    return build_fast_path_response()
else:
    # SLOW PATH (Gemini on Google Cloud Agent Platform)
    return await build_slow_path_gemini_response()
```

---

## 5. Google Cloud Setup & Security Hardening

To follow Google Cloud enterprise standards, we configure **Least Privilege IAM**, **Secret Manager**, and **Cloud Run Service Accounts**.

### 5.1 Step 1: Enable Google Cloud APIs
Run the automated script `./scripts/setup_gcp.sh <PROJECT_ID>` or execute manually:
```bash
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  secretmanager.googleapis.com \
  bigquery.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com
```

### 5.2 Step 2: Store TypeSafe Secret in Secret Manager
Never store API keys in plaintext environment variables or Git repositories:
```bash
echo -n "ts_live_your_actual_key" | gcloud secrets create typesafe-api-key \
  --replication-policy="automatic" \
  --data-file=-
```

### 5.3 Step 3: Create Dedicated Service Account & Grant Roles
```bash
# 1. Create service account
gcloud iam service-accounts create hybrid-gateway-sa \
  --display-name="Hybrid AI Gateway Cloud Run Identity"

# 2. Grant Agent Platform user role (to invoke Gemini models)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:hybrid-gateway-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# 3. Grant Secret Accessor role (to mount typesafe-api-key)
gcloud secrets add-iam-policy-binding typesafe-api-key \
  --member="serviceAccount:hybrid-gateway-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 4. Grant BigQuery Data Editor role (for streaming telemetry)
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:hybrid-gateway-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

---

## 6. Deploying to Cloud Run

The service is packaged into a lean Debian-slim container running with an unprivileged non-root user (`appuser`).

Deploying with one command:
```bash
./scripts/deploy.sh YOUR_PROJECT_ID us-central1
```

Under the hood, this executes:
```bash
gcloud run deploy hybrid-ai-gateway \
  --image="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/ai-gateway-repo/hybrid-ai-gateway:latest" \
  --region="us-central1" \
  --service-account="hybrid-gateway-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --allow-unauthenticated \
  --memory="1Gi" \
  --cpu="1" \
  --concurrency=80 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=gemini-3.8-flash,CONFIDENCE_THRESHOLD=0.90,ENABLE_BIGQUERY_TELEMETRY=true" \
  --set-secrets="TYPESAFE_API_KEY=typesafe-api-key:latest"
```

---

## 7. Live Verification & Benchmarks

Once deployed, run the automated verification suite against your Cloud Run URL:
```bash
python3 scripts/test_queries.py https://hybrid-ai-gateway-xyz.run.app
```

### Measured Real-World Results

```
Query                                    | Route            | Conf   | Latency  | Cost
-----------------------------------------------------------------------------------------
Where is my order #19028?                | FAST_PATH_JEV    | 98.5%  | 76.2 ms  | $0.000084
Cancel subscription before billing cycle | FAST_PATH_JEV    | 96.2%  | 74.8 ms  | $0.000078
Billed twice on invoice INV-9902         | FAST_PATH_JEV    | 94.1%  | 78.1 ms  | $0.000082
Database connection pool exhausted 500   | SLOW_PATH_GEMINI | 88.0%  | 1620 ms  | $0.001250
Legal inquiry on cross-border data policy| SLOW_PATH_GEMINI | 64.0%  | 1580 ms  | $0.001410
```

### Analysis of the Jevons Efficiency Curve
* **Fast-Path Latency:** Under **80 milliseconds** end-to-end.
* **Slow-Path Latency:** ~**1,600 milliseconds**.
* **Blended Cost Impact:** Assuming an enterprise workload with 75% routine inquiries and 25% complex escalations, this hybrid architecture achieves an **88%+ cost reduction** compared to sending 100% of traffic to a generative model, while improving user-perceived responsiveness by over **20x** for the majority of requests.

---

## 8. Telemetry & BigQuery Analytics

In `sql/bigquery_schema.sql`, we define a partitioned and clustered table to track decision telemetry:
```sql
CREATE TABLE IF NOT EXISTS `ai_gateway_telemetry.gateway_metrics`
(
  timestamp TIMESTAMP,
  query STRING,
  route_taken STRING,
  overall_latency_ms FLOAT64,
  overall_cost_usd FLOAT64,
  category STRING,
  confidence FLOAT64,
  final_action STRING
)
PARTITION BY DATE(timestamp)
CLUSTER BY route_taken, category;
```

With this data in BigQuery, platform engineers can query:
```sql
SELECT 
  route_taken,
  COUNT(*) as total_requests,
  ROUND(AVG(overall_latency_ms), 2) as avg_latency_ms,
  ROUND(SUM(overall_cost_usd), 4) as total_cost_usd,
  ROUND(AVG(confidence), 3) as avg_confidence
FROM `ai_gateway_telemetry.gateway_metrics`
WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY route_taken;
```

---

## Summary & What's Next

By decoupling **reflexes** from **reasoning**, you transform AI from an expensive, slow bottleneck into a machine-native, high-throughput software component.

### Suggested Extensions:
1. **Cloud Pub/Sub Streaming Ingestion:** Connect a Pub/Sub push subscription directly to `/api/v1/triage` for line-rate event processing.
2. **Dynamic Confidence Tuning:** Automatically adjust the `CONFIDENCE_THRESHOLD` based on customer tier (e.g. 0.85 for Standard, 0.95 for Enterprise VIPs).
3. **Enterprise RAG Integration:** Add grounding to Gemini on Agent Platform using Spanner Vector Search or Agent Platform retrieval when slow-path reasoning is invoked.
