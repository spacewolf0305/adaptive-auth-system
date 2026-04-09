"""
=============================================================================
 Adaptive Authentication System — Research-Grade ML Evaluation
 Generates publication-ready metrics for the Random Forest risk classifier.
 
 Metrics produced:
   • Accuracy, Precision, Recall, F1 (per-class + weighted)
   • ROC-AUC with plotted curve
   • Precision-Recall AUC with plotted curve
   • 5-fold and 10-fold stratified cross-validation (mean ± std)
   • Confusion matrix (normalized + raw)
   • Feature importance with ranking
   • Decision threshold sensitivity analysis
   • Full classification report
=============================================================================
"""

import os
import sys
import json
import time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, auc,
    precision_recall_curve, average_precision_score,
    confusion_matrix, classification_report,
)
from sklearn.preprocessing import LabelEncoder

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "synthetic_auth_data.csv")
RESULTS_DIR = os.path.join(BASE_DIR, "evaluation", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

FEATURE_COLS = [
    "country_enc", "region_enc", "hour_of_day",
    "device_enc", "prev_login_success", "threat_score",
    "distance_from_last_login",
]

PRETTY_NAMES = [
    "Country", "Region", "Hour of Day", "Device Type",
    "Prev Login Success", "Threat Score", "Distance (km)",
]


# ─── Data Loading ─────────────────────────────────────────────────────────────

def load_and_prepare_data():
    """Load CSV, encode categoricals, return X, y, encoders, and dataframe."""
    df = pd.read_csv(DATA_FILE)

    encoders = {}
    for col, enc_col in [("country", "country_enc"),
                          ("region", "region_enc"),
                          ("device_type", "device_enc")]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col])
        encoders[col] = le

    X = df[FEATURE_COLS].values
    y = df["target_class"].values
    return X, y, encoders, df


# ─── Core Evaluation ──────────────────────────────────────────────────────────

def run_evaluation():
    """Full ML evaluation pipeline. Returns dict of all metrics."""
    print("\n" + "=" * 70)
    print("  🔬  Research-Grade ML Evaluation")
    print("=" * 70)

    start = time.time()
    X, y, encoders, df = load_and_prepare_data()
    print(f"\n  📂  Dataset: {len(X):,} samples  |  {y.sum():,} risky ({y.mean()*100:.1f}%)")

    # ── Train/Test Split (same as production) ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )
    print(f"  📊  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # ── Train Model (replicate production config) ──
    clf = RandomForestClassifier(
        n_estimators=200, max_depth=18, min_samples_split=5,
        min_samples_leaf=2, random_state=42, n_jobs=-1,
    )
    t0 = time.time()
    clf.fit(X_train, y_train)
    train_time = time.time() - t0

    y_pred = clf.predict(X_test)
    y_proba = clf.predict_proba(X_test)[:, 1]

    # ════════════════════════════════════════════════════════════════════════
    # 1. CORE METRICS
    # ════════════════════════════════════════════════════════════════════════
    metrics = {
        "dataset": {
            "total_samples": int(len(X)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
            "positive_rate": round(float(y.mean()), 4),
        },
        "training": {
            "model": "RandomForestClassifier",
            "n_estimators": 200,
            "max_depth": 18,
            "train_time_seconds": round(train_time, 3),
        },
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": {
            "safe":     round(float(precision_score(y_test, y_pred, pos_label=0)), 4),
            "risk":     round(float(precision_score(y_test, y_pred, pos_label=1)), 4),
            "weighted": round(float(precision_score(y_test, y_pred, average="weighted")), 4),
        },
        "recall": {
            "safe":     round(float(recall_score(y_test, y_pred, pos_label=0)), 4),
            "risk":     round(float(recall_score(y_test, y_pred, pos_label=1)), 4),
            "weighted": round(float(recall_score(y_test, y_pred, average="weighted")), 4),
        },
        "f1_score": {
            "safe":     round(float(f1_score(y_test, y_pred, pos_label=0)), 4),
            "risk":     round(float(f1_score(y_test, y_pred, pos_label=1)), 4),
            "weighted": round(float(f1_score(y_test, y_pred, average="weighted")), 4),
        },
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "pr_auc": round(float(average_precision_score(y_test, y_proba)), 4),
    }

    print(f"\n  ✅  Accuracy:       {metrics['accuracy']}")
    print(f"  ✅  F1 (weighted):  {metrics['f1_score']['weighted']}")
    print(f"  ✅  ROC-AUC:        {metrics['roc_auc']}")
    print(f"  ✅  PR-AUC:         {metrics['pr_auc']}")

    # ════════════════════════════════════════════════════════════════════════
    # 2. CONFUSION MATRIX
    # ════════════════════════════════════════════════════════════════════════
    cm = confusion_matrix(y_test, y_pred)
    cm_norm = confusion_matrix(y_test, y_pred, normalize="true")
    metrics["confusion_matrix"] = {
        "raw": cm.tolist(),
        "normalized": np.round(cm_norm, 4).tolist(),
        "labels": ["Safe (0)", "Risk (1)"],
    }
    print(f"\n  📋  Confusion Matrix (raw):\n       {cm.tolist()}")

    # ════════════════════════════════════════════════════════════════════════
    # 3. CROSS-VALIDATION
    # ════════════════════════════════════════════════════════════════════════
    print("\n  ⏳  Running cross-validation...")

    cv_results = {}
    for k in [5, 10]:
        skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
        scores = cross_val_score(clf, X, y, cv=skf, scoring="accuracy", n_jobs=-1)
        cv_results[f"{k}_fold"] = {
            "mean": round(float(scores.mean()), 4),
            "std": round(float(scores.std()), 4),
            "all_scores": [round(float(s), 4) for s in scores],
        }
        print(f"  📊  {k}-fold CV:     {scores.mean():.4f} ± {scores.std():.4f}")

    # Additional CV metrics: F1 and ROC-AUC
    for scoring_name in ["f1_weighted", "roc_auc"]:
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(clf, X, y, cv=skf, scoring=scoring_name, n_jobs=-1)
        cv_results[f"5_fold_{scoring_name}"] = {
            "mean": round(float(scores.mean()), 4),
            "std": round(float(scores.std()), 4),
        }
        print(f"  📊  5-fold {scoring_name}: {scores.mean():.4f} ± {scores.std():.4f}")

    metrics["cross_validation"] = cv_results

    # ════════════════════════════════════════════════════════════════════════
    # 4. FEATURE IMPORTANCE
    # ════════════════════════════════════════════════════════════════════════
    importances = clf.feature_importances_
    indices = np.argsort(importances)[::-1]
    fi_list = []
    for i, idx in enumerate(indices):
        fi_list.append({
            "rank": i + 1,
            "feature": PRETTY_NAMES[idx],
            "importance": round(float(importances[idx]), 4),
        })
    metrics["feature_importance"] = fi_list

    print("\n  📈  Feature Importance:")
    for fi in fi_list:
        bar = "█" * int(fi["importance"] * 50)
        print(f"       {fi['rank']}. {fi['feature']:<20} {fi['importance']:.4f}  {bar}")

    # ════════════════════════════════════════════════════════════════════════
    # 5. THRESHOLD ANALYSIS
    # ════════════════════════════════════════════════════════════════════════
    thresholds_to_test = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
    threshold_results = []
    for t in thresholds_to_test:
        y_pred_t = (y_proba >= t).astype(int)
        threshold_results.append({
            "threshold": t,
            "accuracy":  round(float(accuracy_score(y_test, y_pred_t)), 4),
            "precision": round(float(precision_score(y_test, y_pred_t, zero_division=0)), 4),
            "recall":    round(float(recall_score(y_test, y_pred_t, zero_division=0)), 4),
            "f1":        round(float(f1_score(y_test, y_pred_t, zero_division=0)), 4),
        })
    metrics["threshold_analysis"] = threshold_results

    print("\n  🎚️  Threshold Analysis:")
    print(f"       {'Threshold':<11} {'Accuracy':<10} {'Precision':<11} {'Recall':<9} {'F1':<8}")
    for r in threshold_results:
        print(f"       {r['threshold']:<11} {r['accuracy']:<10} {r['precision']:<11} {r['recall']:<9} {r['f1']:<8}")

    # ════════════════════════════════════════════════════════════════════════
    # 6. ROC & PR CURVE DATA (for plotting)
    # ════════════════════════════════════════════════════════════════════════
    fpr, tpr, roc_thresholds = roc_curve(y_test, y_proba)
    prec_curve, rec_curve, pr_thresholds = precision_recall_curve(y_test, y_proba)

    metrics["roc_curve"] = {
        "fpr": [round(float(x), 4) for x in fpr[::max(1, len(fpr)//100)]],
        "tpr": [round(float(x), 4) for x in tpr[::max(1, len(tpr)//100)]],
    }
    metrics["pr_curve"] = {
        "precision": [round(float(x), 4) for x in prec_curve[::max(1, len(prec_curve)//100)]],
        "recall":    [round(float(x), 4) for x in rec_curve[::max(1, len(rec_curve)//100)]],
    }

    # ════════════════════════════════════════════════════════════════════════
    # 7. CLASSIFICATION REPORT (text)
    # ════════════════════════════════════════════════════════════════════════
    report_text = classification_report(y_test, y_pred, target_names=["Safe", "Risk"])
    metrics["classification_report"] = report_text

    # ════════════════════════════════════════════════════════════════════════
    # 8. INFERENCE SPEED
    # ════════════════════════════════════════════════════════════════════════
    # Benchmark single-sample inference time
    sample = X_test[0:1]
    times = []
    for _ in range(500):
        t0 = time.perf_counter()
        clf.predict_proba(sample)
        times.append(time.perf_counter() - t0)

    times_ms = np.array(times) * 1000
    metrics["inference_speed"] = {
        "samples": 500,
        "median_ms": round(float(np.median(times_ms)), 4),
        "p95_ms":    round(float(np.percentile(times_ms, 95)), 4),
        "p99_ms":    round(float(np.percentile(times_ms, 99)), 4),
        "mean_ms":   round(float(np.mean(times_ms)), 4),
    }
    print(f"\n  ⚡  Inference: {metrics['inference_speed']['median_ms']:.2f}ms median"
          f"  |  {metrics['inference_speed']['p95_ms']:.2f}ms p95"
          f"  |  {metrics['inference_speed']['p99_ms']:.2f}ms p99")

    total_time = time.time() - start
    metrics["total_evaluation_time_seconds"] = round(total_time, 2)

    # ── Save JSON ──
    json_path = os.path.join(RESULTS_DIR, "ml_metrics.json")
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"\n  💾  Metrics saved → {os.path.relpath(json_path, BASE_DIR)}")

    # ── Save classification report text ──
    report_path = os.path.join(RESULTS_DIR, "classification_report.txt")
    with open(report_path, "w") as f:
        f.write("Adaptive Auth System — Classification Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(report_text)
    print(f"  💾  Report saved  → {os.path.relpath(report_path, BASE_DIR)}")

    print(f"\n  ⏱️  Total time: {total_time:.1f}s")
    print("=" * 70 + "\n")

    return metrics, clf, X_test, y_test, y_proba, fpr, tpr, prec_curve, rec_curve


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_evaluation()
