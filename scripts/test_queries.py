#!/usr/bin/env python3
"""Automated Benchmark & Verification Suite for GCP Hybrid AI Gateway."""

import sys
import time
import httpx

GATEWAY_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"

TEST_CASES = [
    {"query": "Where is my order #19028? Can you tell me when it arrives?", "tier": "STANDARD", "expected_route": "FAST_PATH_JEV"},
    {"query": "Please cancel my subscription before next billing cycle.", "tier": "STANDARD", "expected_route": "FAST_PATH_JEV"},
    {"query": "I was billed twice on invoice INV-9902 for $45. Issue refund.", "tier": "PREMIUM", "expected_route": "FAST_PATH_JEV"},
    {"query": "I forgot my password and my 2FA code is expired. Need login link.", "tier": "STANDARD", "expected_route": "FAST_PATH_JEV"},
    {"query": "Check shipping status for tracking ID TRK-882109.", "tier": "STANDARD", "expected_route": "FAST_PATH_JEV"},
    {"query": "CRITICAL: Database connection pool exhausted with 500 error on checkout.", "tier": "ENTERPRISE", "expected_route": "SLOW_PATH_GEMINI"},
    {"query": "Can you explain how section 4.2 of your data processing agreement handles cross-border EU transfers?", "tier": "ENTERPRISE", "expected_route": "SLOW_PATH_GEMINI"},
    {"query": "The UI feels slightly jittery when scrolling on Android Firefox. What css setting fixes this?", "tier": "STANDARD", "expected_route": "SLOW_PATH_GEMINI"},
    {"query": "We are getting high p99 latency spikes during flash sales. How do we tune auto-scaling?", "tier": "PREMIUM", "expected_route": "SLOW_PATH_GEMINI"},
    {"query": "I have an ambiguous billing dispute with unexpected ledger entries.", "tier": "PREMIUM", "expected_route": "SLOW_PATH_GEMINI"},
]


def run_benchmarks():
    print(f"\n🚀 Running verification against: {GATEWAY_URL}\n")
    print(f"{'Query Preview':<40} | {'Route':<18} | {'Confidence':<10} | {'Latency':<10} | {'Cost':<10}")
    print("-" * 100)

    total_cost = 0.0
    fast_path_count = 0
    slow_path_count = 0
    total_latency_fast = 0.0
    total_latency_slow = 0.0

    client = httpx.Client(timeout=30.0)

    for tc in TEST_CASES:
        payload = {"query": tc["query"], "customer_tier": tc["tier"]}
        resp = client.post(f"{GATEWAY_URL}/api/v1/triage", json=payload)
        if resp.status_code != 200:
            print(f"❌ Error {resp.status_code}: {resp.text}")
            continue

        data = resp.json()
        route = data["route_taken"]
        conf = data["system1_jev"]["calibrated_confidence"]
        lat = data["overall_latency_ms"]
        cost = data["overall_cost_usd"]

        total_cost += cost
        if route == "FAST_PATH_JEV":
            fast_path_count += 1
            total_latency_fast += lat
        else:
            slow_path_count += 1
            total_latency_slow += lat

        preview = (tc["query"][:36] + "...") if len(tc["query"]) > 36 else tc["query"]
        print(f"{preview:<40} | {route:<18} | {conf*100:>8.1f}% | {lat:>7.1f} ms | ${cost:>8.6f}")

    avg_fast = (total_latency_fast / fast_path_count) if fast_path_count else 0
    avg_slow = (total_latency_slow / slow_path_count) if slow_path_count else 0

    print("-" * 100)
    print("\n📊 BENCHMARK SUMMARY:")
    print(f"Total Requests Tested:     {len(TEST_CASES)}")
    print(f"⚡ Fast-Path (Jev):         {fast_path_count} requests | Avg Latency: {avg_fast:.1f} ms")
    print(f"🧠 Slow-Path (Gemini):      {slow_path_count} requests | Avg Latency: {avg_slow:.1f} ms")
    print(f"Speedup on Fast-Path:      {avg_slow / max(avg_fast, 1):.1f}x Faster")
    print(f"Total Blended Cost:        ${total_cost:.6f}")
    print(f"Projected Cost per 10k:    ${(total_cost / len(TEST_CASES) * 10_000):.2f}\n")


if __name__ == "__main__":
    run_benchmarks()
