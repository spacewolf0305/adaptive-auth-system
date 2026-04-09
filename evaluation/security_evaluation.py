"""
=============================================================================
 Adaptive Authentication System — Security Evaluation
 Tests the ML model's attack detection capabilities using synthetic
 attack profiles (from attack_sim.py). Runs fully offline.

 Outputs:
   • True Positive Rate, False Positive Rate, False Negative Rate
   • Detection rate per attack category (high / medium / low risk)
   • Security ROC curve data
   • Results saved to evaluation/results/security_metrics.json
=============================================================================
"""

import os
import sys
import json
import time
import random
import numpy as np
import matplotlib
matplotlib.use("Agg")

# Ensure project root is on the path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from risk_engine import predict_risk

RESULTS_DIR = os.path.join(BASE_DIR, "evaluation", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

# ─── Attack Profiles (matching attack_sim.py) ────────────────────────────────

HIGH_RISK = [
    {"country": "Russia",      "region": "Eastern Europe", "device_type": "desktop",    "threat_range": (80, 100), "dist_range": (5000, 14000), "label": "RU brute-force"},
    {"country": "North Korea", "region": "East Asia",      "device_type": "iot_device", "threat_range": (88, 100), "dist_range": (8000, 15000), "label": "NK IoT botnet"},
    {"country": "China",       "region": "East Asia",      "device_type": "mobile",     "threat_range": (70, 98),  "dist_range": (4000, 12000), "label": "CN credential stuff"},
    {"country": "Iran",        "region": "Middle East",    "device_type": "desktop",    "threat_range": (75, 99),  "dist_range": (6000, 13000), "label": "IR APT probe"},
    {"country": "Somalia",     "region": "Africa",         "device_type": "iot_device", "threat_range": (85, 100), "dist_range": (7000, 14000), "label": "SO bot swarm"},
    {"country": "Ukraine",     "region": "Eastern Europe", "device_type": "desktop",    "threat_range": (72, 96),  "dist_range": (4500, 11000), "label": "UA DarkWeb dump"},
    {"country": "Syria",       "region": "Middle East",    "device_type": "mobile",     "threat_range": (78, 99),  "dist_range": (5500, 12000), "label": "SY state actor"},
    {"country": "Venezuela",   "region": "South America",  "device_type": "tablet",     "threat_range": (70, 95),  "dist_range": (5000, 11000), "label": "VE mass scan"},
    {"country": "Libya",       "region": "Africa",         "device_type": "desktop",    "threat_range": (82, 100), "dist_range": (6000, 13000), "label": "LY credential flood"},
    {"country": "Cuba",        "region": "Caribbean",      "device_type": "iot_device", "threat_range": (76, 98),  "dist_range": (4000, 10000), "label": "CU botnet relay"},
]

MEDIUM_RISK = [
    {"country": "Nigeria",      "region": "Africa",         "device_type": "mobile",    "threat_range": (45, 75), "dist_range": (3000, 8000),  "label": "NG phishing"},
    {"country": "Brazil",       "region": "South America",  "device_type": "tablet",    "threat_range": (35, 65), "dist_range": (2000, 6000),  "label": "BR suspicious"},
    {"country": "Colombia",     "region": "South America",  "device_type": "tablet",    "threat_range": (30, 60), "dist_range": (1500, 5000),  "label": "CO mixed signals"},
    {"country": "Saudi Arabia", "region": "Middle East",    "device_type": "smart_tv",  "threat_range": (25, 55), "dist_range": (1000, 4500),  "label": "SA odd device"},
    {"country": "Thailand",     "region": "Southeast Asia", "device_type": "mobile",    "threat_range": (30, 58), "dist_range": (1200, 4000),  "label": "TH unusual hour"},
]

LOW_RISK = [
    {"country": "United States", "region": "North America",  "device_type": "desktop", "threat_range": (3, 18),  "dist_range": (10, 400),   "label": "US trusted"},
    {"country": "Germany",       "region": "Western Europe", "device_type": "desktop", "threat_range": (2, 15),  "dist_range": (30, 600),   "label": "DE regular"},
    {"country": "Japan",         "region": "East Asia",      "device_type": "mobile",  "threat_range": (5, 22),  "dist_range": (100, 1200), "label": "JP normal"},
    {"country": "India",         "region": "South Asia",     "device_type": "mobile",  "threat_range": (8, 30),  "dist_range": (200, 2000), "label": "IN routine"},
    {"country": "Australia",     "region": "Oceania",        "device_type": "desktop", "threat_range": (3, 12),  "dist_range": (50, 500),   "label": "AU safe"},
    {"country": "Canada",        "region": "North America",  "device_type": "desktop", "threat_range": (2, 14),  "dist_range": (20, 350),   "label": "CA trusted"},
]


def _generate_scenario(profile, is_attack):
    """Generate a single test scenario from a profile."""
    threat = random.randint(*profile["threat_range"])
    distance = round(random.uniform(*profile["dist_range"]), 2)
    hour = random.randint(0, 5) if is_attack else random.randint(8, 20)

    return {
        "country": profile["country"],
        "region": profile["region"],
        "device_type": profile["device_type"],
        "hour_of_day": hour,
        "prev_login_success": 0 if is_attack else 1,
        "threat_score": threat,
        "distance_from_last_login": distance,
        "expected_risky": is_attack,
        "category": "high" if profile in HIGH_RISK else ("medium" if profile in MEDIUM_RISK else "low"),
        "profile_label": profile["label"],
    }


def run_security_evaluation(num_scenarios=1500):
    """Evaluate the model's attack detection capability."""
    print("\n" + "=" * 70)
    print("  🔒  Security Evaluation — Attack Detection Analysis")
    print("=" * 70)

    random.seed(42)
    start = time.time()

    # Generate balanced test scenarios
    scenarios = []

    # 500 high-risk attacks
    for _ in range(500):
        profile = random.choice(HIGH_RISK)
        scenarios.append(_generate_scenario(profile, is_attack=True))

    # 250 medium-risk attacks
    for _ in range(250):
        profile = random.choice(MEDIUM_RISK)
        scenarios.append(_generate_scenario(profile, is_attack=True))

    # 750 legitimate logins (using low-risk profiles)
    for _ in range(750):
        profile = random.choice(LOW_RISK)
        scenarios.append(_generate_scenario(profile, is_attack=False))

    random.shuffle(scenarios)

    print(f"\n  📦  Generated {len(scenarios)} test scenarios")
    print(f"       Attacks: {sum(1 for s in scenarios if s['expected_risky'])}")
    print(f"       Legitimate: {sum(1 for s in scenarios if not s['expected_risky'])}")

    # ── Run predictions ──
    results = []
    risk_scores = []
    ground_truth = []

    for i, scenario in enumerate(scenarios):
        risk_data = {k: v for k, v in scenario.items()
                     if k not in ("expected_risky", "category", "profile_label")}
        risk_score = predict_risk(risk_data)
        risk_scores.append(risk_score)
        ground_truth.append(1 if scenario["expected_risky"] else 0)

        # Use 0.5 as default threshold
        predicted_risky = risk_score >= 0.5
        results.append({
            "risk_score": risk_score,
            "predicted_risky": predicted_risky,
            "actually_risky": scenario["expected_risky"],
            "category": scenario["category"],
            "profile_label": scenario["profile_label"],
        })

        if (i + 1) % 500 == 0:
            print(f"  ⏳  Processed {i+1}/{len(scenarios)}...")

    # ── Compute metrics ──
    risk_scores = np.array(risk_scores)
    ground_truth = np.array(ground_truth)

    # Test at multiple thresholds
    THRESHOLDS = {"conservative": 0.3, "balanced": 0.5, "aggressive": 0.7}
    threshold_metrics = {}

    for name, threshold in THRESHOLDS.items():
        predictions = (risk_scores >= threshold).astype(int)
        tp = int(np.sum((predictions == 1) & (ground_truth == 1)))
        fp = int(np.sum((predictions == 1) & (ground_truth == 0)))
        tn = int(np.sum((predictions == 0) & (ground_truth == 0)))
        fn = int(np.sum((predictions == 0) & (ground_truth == 1)))

        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tpr
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        threshold_metrics[name] = {
            "threshold": threshold,
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "true_positive_rate": round(tpr, 4),
            "false_positive_rate": round(fpr, 4),
            "false_negative_rate": round(fnr, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

    # ── Detection rate by category ──
    category_detection = {}
    for cat in ["high", "medium", "low"]:
        cat_results = [r for r in results if r["category"] == cat]
        if not cat_results:
            continue
        detected = sum(1 for r in cat_results if r["predicted_risky"])
        total = len(cat_results)
        avg_score = np.mean([r["risk_score"] for r in cat_results])

        category_detection[cat] = {
            "total_scenarios": total,
            "detected": detected,
            "detection_rate": round(detected / total, 4),
            "avg_risk_score": round(float(avg_score), 4),
        }

    # ── Per-profile detection ──
    profile_detection = {}
    for r in results:
        label = r["profile_label"]
        if label not in profile_detection:
            profile_detection[label] = {"total": 0, "detected": 0, "scores": []}
        profile_detection[label]["total"] += 1
        profile_detection[label]["scores"].append(r["risk_score"])
        if r["predicted_risky"]:
            profile_detection[label]["detected"] += 1

    for label, data in profile_detection.items():
        data["detection_rate"] = round(data["detected"] / data["total"], 4)
        data["avg_risk_score"] = round(float(np.mean(data["scores"])), 4)
        del data["scores"]  # Don't save raw scores

    # ── Risk score distribution stats ──
    attack_scores = risk_scores[ground_truth == 1]
    legit_scores = risk_scores[ground_truth == 0]

    score_distribution = {
        "attacks": {
            "mean": round(float(attack_scores.mean()), 4),
            "median": round(float(np.median(attack_scores)), 4),
            "std": round(float(attack_scores.std()), 4),
            "min": round(float(attack_scores.min()), 4),
            "max": round(float(attack_scores.max()), 4),
        },
        "legitimate": {
            "mean": round(float(legit_scores.mean()), 4),
            "median": round(float(np.median(legit_scores)), 4),
            "std": round(float(legit_scores.std()), 4),
            "min": round(float(legit_scores.min()), 4),
            "max": round(float(legit_scores.max()), 4),
        },
        "separation": round(float(attack_scores.mean() - legit_scores.mean()), 4),
    }

    total_time = time.time() - start

    # ── Assemble final metrics ──
    security_metrics = {
        "total_scenarios": len(scenarios),
        "total_attacks": int(ground_truth.sum()),
        "total_legitimate": int((ground_truth == 0).sum()),
        "threshold_metrics": threshold_metrics,
        "category_detection": category_detection,
        "profile_detection": profile_detection,
        "score_distribution": score_distribution,
        "evaluation_time_seconds": round(total_time, 2),
    }

    # ── Print Summary ──
    print("\n  📊  Results (threshold = 0.5):")
    m = threshold_metrics["balanced"]
    print(f"       True Positive Rate:  {m['true_positive_rate']:.4f}")
    print(f"       False Positive Rate: {m['false_positive_rate']:.4f}")
    print(f"       False Negative Rate: {m['false_negative_rate']:.4f}")
    print(f"       Precision:           {m['precision']:.4f}")
    print(f"       Recall:              {m['recall']:.4f}")
    print(f"       F1 Score:            {m['f1_score']:.4f}")

    print("\n  🎯  Detection Rate by Category:")
    for cat, data in category_detection.items():
        icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(cat, "⚪")
        print(f"       {icon} {cat:<8}: {data['detection_rate']*100:.1f}%  "
              f"(avg score: {data['avg_risk_score']:.4f})")

    print(f"\n  📈  Score Separation: {score_distribution['separation']:.4f}")
    print(f"       Attacks mean:    {score_distribution['attacks']['mean']:.4f}")
    print(f"       Legitimate mean: {score_distribution['legitimate']['mean']:.4f}")

    # ── Save ──
    json_path = os.path.join(RESULTS_DIR, "security_metrics.json")
    with open(json_path, "w") as f:
        json.dump(security_metrics, f, indent=2)
    print(f"\n  💾  Saved → {os.path.relpath(json_path, BASE_DIR)}")

    print(f"  ⏱️  Total time: {total_time:.1f}s")
    print("=" * 70 + "\n")

    return security_metrics, risk_scores, ground_truth


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_security_evaluation()
