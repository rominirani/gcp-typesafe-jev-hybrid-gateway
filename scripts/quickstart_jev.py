#!/usr/bin/env python3
"""Python Quickstart: Calling TypeSafe Jev directly via the official SystemOne API.

Requires TYPESAFE_API_KEY in the environment (https://console.typesafe.ai/keys).
Evaluates unstructured state against Choice, Score, and Noul primitives in a
single parallel call to https://api.typesafe.ai/v1/systemone.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error

TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY")
TYPESAFE_API_URL = os.getenv("TYPESAFE_API_URL", "https://api.typesafe.ai/v1/systemone")
TYPESAFE_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest")


def classify_with_jev(query: str) -> None:
    if not TYPESAFE_API_KEY:
        raise RuntimeError(
            "TYPESAFE_API_KEY environment variable is required. "
            "Export your key via: export TYPESAFE_API_KEY='ts_live_...'"
        )

    print(f"\n📡 Input State: \"{query}\"")
    print(f"⏳ Calling TypeSafe SystemOne API ({TYPESAFE_MODEL})...")

    start_time = time.perf_counter()

    # Official TypeSafe /v1/systemone request body using Choice, Score, and Noul primitives
    payload = {
        "state": query,
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
                    "LOW: Routine question, can wait",
                    "MEDIUM: Standard support request",
                    "HIGH: Time-sensitive customer impact",
                    "CRITICAL: Severe production outage or blocker"
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

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TYPESAFE_API_URL,
        data=req_data,
        headers={
            "Authorization": f"Bearer {TYPESAFE_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=10.0) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    latency_ms = (time.perf_counter() - start_time) * 1000

    answers = result["answers"]
    cat_ans = answers["category"]
    urg_ans = answers["urgency"]
    auto_ans = answers["can_auto_resolve"]
    usage = result.get("usage", {})

    print(f"⚡ Latency:          {latency_ms:.1f} ms")
    print(f"🤖 Model:            {result.get('model')}")
    print(f"🎯 Category Choice:  {cat_ans['choice']} (confidence: {cat_ans['confidence']:.3f})")
    print(f"🔥 Urgency Score:    {urg_ans['score']:.2f} / 3.0 (confidence: {urg_ans['confidence']:.3f})")
    print(f"✅ Auto-Resolvable:  {auto_ans['noul']:.3f} (Noul probability)")
    print(f"🎲 Probabilities:    {json.dumps(cat_ans['probabilities'])}")
    print(f"📊 Token Usage:      input={usage.get('input_tokens')}, output={usage.get('output_tokens')}\n")


if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "Where is my package #8942? Has it shipped yet?"
    classify_with_jev(test_query)
