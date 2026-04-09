"""
=============================================================================
 Adaptive Authentication System — Performance Benchmark
 Measures API response times, throughput, and model inference speed.

 Two modes:
   1. Offline (default): Benchmarks the model directly (no server needed)
   2. Online (--live): Benchmarks the running Flask API via HTTP

 Outputs:
   • Latency percentiles (p50, p95, p99)
   • Throughput (predictions/second)
   • Concurrent load test results
   • Results saved to evaluation/results/performance_metrics.json
=============================================================================
"""

import os
import sys
import json
import time
import random
import argparse
import statistics
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure project root is on the path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

RESULTS_DIR = os.path.join(BASE_DIR, "evaluation", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ─── Test Scenarios ───────────────────────────────────────────────────────────

def _random_scenario():
    """Generate a random login scenario for benchmarking."""
    countries = ["United States", "Germany", "India", "Russia", "China",
                 "Brazil", "Japan", "North Korea", "Iran", "Australia"]
    regions = ["North America", "Western Europe", "South Asia", "Eastern Europe",
               "East Asia", "South America", "East Asia", "East Asia",
               "Middle East", "Oceania"]
    devices = ["desktop", "mobile", "tablet", "iot_device", "smart_tv"]

    idx = random.randint(0, len(countries) - 1)
    return {
        "country": countries[idx],
        "region": regions[idx],
        "hour_of_day": random.randint(0, 23),
        "device_type": random.choice(devices),
        "prev_login_success": random.choice([0, 1]),
        "threat_score": random.randint(0, 100),
        "distance_from_last_login": round(random.uniform(0, 15000), 2),
    }


# ─── Offline Benchmark (Model Only) ──────────────────────────────────────────

def run_offline_benchmark(num_iterations=1000):
    """Benchmark predict_risk() directly without network overhead."""
    from risk_engine import predict_risk

    print("\n" + "=" * 70)
    print("  ⚡  Performance Benchmark — Offline (Model Only)")
    print("=" * 70)

    random.seed(42)
    scenarios = [_random_scenario() for _ in range(num_iterations)]

    # ── Warmup ──
    print("\n  🔥  Warming up (50 predictions)...")
    for s in scenarios[:50]:
        predict_risk(s)

    # ── Single-threaded latency ──
    print(f"  ⏱️  Running {num_iterations} predictions (single-threaded)...")
    latencies = []
    for s in scenarios:
        t0 = time.perf_counter()
        predict_risk(s)
        latencies.append((time.perf_counter() - t0) * 1000)  # ms

    latencies_arr = np.array(latencies)
    single_thread = {
        "iterations": num_iterations,
        "mean_ms":   round(float(latencies_arr.mean()), 4),
        "median_ms": round(float(np.median(latencies_arr)), 4),
        "p95_ms":    round(float(np.percentile(latencies_arr, 95)), 4),
        "p99_ms":    round(float(np.percentile(latencies_arr, 99)), 4),
        "min_ms":    round(float(latencies_arr.min()), 4),
        "max_ms":    round(float(latencies_arr.max()), 4),
        "std_ms":    round(float(latencies_arr.std()), 4),
    }

    total_time_s = sum(latencies) / 1000
    throughput = num_iterations / total_time_s

    print(f"\n  📊  Single-Thread Results:")
    print(f"       Mean:       {single_thread['mean_ms']:.3f} ms")
    print(f"       Median:     {single_thread['median_ms']:.3f} ms")
    print(f"       p95:        {single_thread['p95_ms']:.3f} ms")
    print(f"       p99:        {single_thread['p99_ms']:.3f} ms")
    print(f"       Throughput: {throughput:.0f} predictions/sec")

    # ── Concurrent load test ──
    concurrent_results = {}
    for num_workers in [5, 10, 25, 50]:
        print(f"\n  🔄  Concurrent test: {num_workers} threads × 50 requests each...")

        def _benchmark_one():
            s = _random_scenario()
            t0 = time.perf_counter()
            predict_risk(s)
            return (time.perf_counter() - t0) * 1000

        overall_start = time.perf_counter()
        all_latencies = []
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_benchmark_one) for _ in range(num_workers * 50)]
            for f in as_completed(futures):
                all_latencies.append(f.result())
        overall_time = time.perf_counter() - overall_start

        arr = np.array(all_latencies)
        concurrent_results[f"{num_workers}_threads"] = {
            "threads": num_workers,
            "total_requests": len(all_latencies),
            "total_time_seconds": round(overall_time, 3),
            "throughput_per_sec": round(len(all_latencies) / overall_time, 1),
            "mean_ms": round(float(arr.mean()), 4),
            "median_ms": round(float(np.median(arr)), 4),
            "p95_ms": round(float(np.percentile(arr, 95)), 4),
            "p99_ms": round(float(np.percentile(arr, 99)), 4),
        }
        r = concurrent_results[f"{num_workers}_threads"]
        print(f"       → {r['throughput_per_sec']} pred/s  |  median: {r['median_ms']:.2f}ms  |  p99: {r['p99_ms']:.2f}ms")

    # ── Assemble results ──
    perf_metrics = {
        "mode": "offline",
        "single_thread": single_thread,
        "throughput_per_sec": round(throughput, 1),
        "concurrent": concurrent_results,
        "latency_distribution": {
            "percentiles": {
                f"p{p}": round(float(np.percentile(latencies_arr, p)), 4)
                for p in [10, 25, 50, 75, 90, 95, 99]
            },
        },
    }

    # ── Save ──
    json_path = os.path.join(RESULTS_DIR, "performance_metrics.json")
    with open(json_path, "w") as f:
        json.dump(perf_metrics, f, indent=2)
    print(f"\n  💾  Saved → {os.path.relpath(json_path, BASE_DIR)}")
    print("=" * 70 + "\n")

    return perf_metrics, latencies_arr


# ─── Online Benchmark (HTTP API) ─────────────────────────────────────────────

def run_online_benchmark(base_url="http://localhost:5000", api_key=None, num_requests=200):
    """Benchmark the live API via HTTP requests. Requires running server."""
    import requests as req

    print("\n" + "=" * 70)
    print("  🌐  Performance Benchmark — Online (HTTP API)")
    print("=" * 70)

    if not api_key:
        # Try to get key from database
        try:
            import sqlite3
            conn = sqlite3.connect(os.path.join(BASE_DIR, "auth.db"))
            c = conn.cursor()
            c.execute("SELECT key FROM api_keys WHERE is_active=1 LIMIT 1")
            row = c.fetchone()
            conn.close()
            if row:
                api_key = row[0]
        except Exception:
            pass

    if not api_key:
        print("  ❌  No API key found. Please provide --api-key or create one via signup.")
        return None, None

    print(f"  🔑  Using key: {api_key[:20]}...{api_key[-6:]}")

    random.seed(42)
    url = f"{base_url}/api/v1/assess"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    # ── Warmup ──
    print("  🔥  Warming up (10 requests)...")
    for _ in range(10):
        try:
            req.post(url, headers=headers, json=_random_scenario(), timeout=10)
        except Exception:
            print("  ❌  Server not reachable. Start with: python app.py")
            return None, None

    # ── Latency test ──
    print(f"  ⏱️  Running {num_requests} requests...")
    latencies = []
    errors = 0
    for i in range(num_requests):
        scenario = _random_scenario()
        t0 = time.perf_counter()
        try:
            r = req.post(url, headers=headers, json=scenario, timeout=10)
            lat = (time.perf_counter() - t0) * 1000
            if r.status_code == 200:
                latencies.append(lat)
            else:
                errors += 1
        except Exception:
            errors += 1

        if (i + 1) % 50 == 0:
            print(f"       {i+1}/{num_requests} completed...")

    if not latencies:
        print("  ❌  All requests failed.")
        return None, None

    arr = np.array(latencies)
    total_time_s = sum(latencies) / 1000

    online_metrics = {
        "mode": "online",
        "base_url": base_url,
        "total_requests": num_requests,
        "successful": len(latencies),
        "errors": errors,
        "mean_ms":   round(float(arr.mean()), 2),
        "median_ms": round(float(np.median(arr)), 2),
        "p95_ms":    round(float(np.percentile(arr, 95)), 2),
        "p99_ms":    round(float(np.percentile(arr, 99)), 2),
        "min_ms":    round(float(arr.min()), 2),
        "max_ms":    round(float(arr.max()), 2),
        "throughput_per_sec": round(len(latencies) / total_time_s, 1),
    }

    print(f"\n  📊  API Results:")
    print(f"       Successful: {len(latencies)}/{num_requests}")
    print(f"       Mean:       {online_metrics['mean_ms']:.1f} ms")
    print(f"       Median:     {online_metrics['median_ms']:.1f} ms")
    print(f"       p95:        {online_metrics['p95_ms']:.1f} ms")
    print(f"       p99:        {online_metrics['p99_ms']:.1f} ms")
    print(f"       Throughput: {online_metrics['throughput_per_sec']} req/s")

    json_path = os.path.join(RESULTS_DIR, "performance_online_metrics.json")
    with open(json_path, "w") as f:
        json.dump(online_metrics, f, indent=2)
    print(f"\n  💾  Saved → {os.path.relpath(json_path, BASE_DIR)}")
    print("=" * 70 + "\n")

    return online_metrics, arr


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Performance Benchmark")
    parser.add_argument("--live", action="store_true", help="Test live API (requires running server)")
    parser.add_argument("--url", default="http://localhost:5000", help="API base URL")
    parser.add_argument("--api-key", default=None, help="API key for live testing")
    parser.add_argument("--count", type=int, default=1000, help="Number of iterations")
    args = parser.parse_args()

    run_offline_benchmark(num_iterations=args.count)

    if args.live:
        run_online_benchmark(base_url=args.url, api_key=args.api_key)
