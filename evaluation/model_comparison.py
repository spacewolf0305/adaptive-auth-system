"""
=============================================================================
 Adaptive Authentication System -- Model Comparison Experiment
 Compares Random Forest against 4 baseline classifiers to justify model
 selection for IEEE publication.
 
 Models tested:
   1. Random Forest (proposed)
   2. XGBoost (gradient boosting baseline)
   3. Logistic Regression (linear baseline)
   4. Support Vector Machine (kernel baseline)
   5. K-Nearest Neighbors (instance baseline)
=============================================================================
"""

import os
import sys
import json
import time
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, auc,
    precision_recall_curve, average_precision_score,
    confusion_matrix, classification_report,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler

warnings.filterwarnings("ignore")

# --- Paths ---
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


def load_and_prepare_data():
    """Load CSV, encode categoricals, return X, y."""
    df = pd.read_csv(DATA_FILE)
    for col, enc_col in [("country", "country_enc"),
                          ("region", "region_enc"),
                          ("device_type", "device_enc")]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col])
    X = df[FEATURE_COLS].values
    y = df["target_class"].values
    return X, y


def run_model_comparison():
    """Compare 5 classifiers and save results + charts."""
    print("\n" + "=" * 70)
    print("  MODEL COMPARISON EXPERIMENT")
    print("=" * 70)

    X, y = load_and_prepare_data()
    print(f"\n  Dataset: {len(X):,} samples | {y.sum():,} risky ({y.mean()*100:.1f}%)")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )

    # Scale features for SVM, LR, KNN
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # --- Define models ---
    models = {
        "Random Forest": {
            "clf": RandomForestClassifier(
                n_estimators=200, max_depth=18, min_samples_split=5,
                min_samples_leaf=2, random_state=42, n_jobs=-1,
            ),
            "scaled": False,
        },
        "XGBoost (GBT)": {
            "clf": GradientBoostingClassifier(
                n_estimators=200, max_depth=6, learning_rate=0.1,
                min_samples_split=5, random_state=42,
            ),
            "scaled": False,
        },
        "Logistic Regression": {
            "clf": LogisticRegression(
                max_iter=1000, random_state=42, n_jobs=-1,
            ),
            "scaled": True,
        },
        "SVM (RBF)": {
            "clf": SVC(
                kernel="rbf", probability=True, random_state=42,
            ),
            "scaled": True,
        },
        "K-Nearest Neighbors": {
            "clf": KNeighborsClassifier(
                n_neighbors=7, n_jobs=-1,
            ),
            "scaled": True,
        },
    }

    results = {}
    roc_data = {}

    for name, config in models.items():
        print(f"\n  Training: {name}...")
        clf = config["clf"]
        use_scaled = config["scaled"]

        Xtr = X_train_scaled if use_scaled else X_train
        Xte = X_test_scaled if use_scaled else X_test

        # Train
        t0 = time.time()
        clf.fit(Xtr, y_train)
        train_time = time.time() - t0

        # Predict
        y_pred = clf.predict(Xte)
        y_proba = clf.predict_proba(Xte)[:, 1]

        # Inference speed
        sample = Xte[0:1]
        inf_times = []
        for _ in range(200):
            t0 = time.perf_counter()
            clf.predict_proba(sample)
            inf_times.append(time.perf_counter() - t0)
        inf_ms = np.array(inf_times) * 1000

        # Metrics
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        roc = roc_auc_score(y_test, y_proba)
        pr_auc_val = average_precision_score(y_test, y_proba)

        # Cross-validation
        Xfull = scaler.transform(X) if use_scaled else X
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(clf, Xfull, y, cv=skf, scoring="accuracy", n_jobs=-1)

        results[name] = {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc), 4),
            "pr_auc": round(float(pr_auc_val), 4),
            "cv_mean": round(float(cv_scores.mean()), 4),
            "cv_std": round(float(cv_scores.std()), 4),
            "train_time_s": round(train_time, 3),
            "inference_median_ms": round(float(np.median(inf_ms)), 4),
            "inference_p95_ms": round(float(np.percentile(inf_ms, 95)), 4),
        }

        # ROC data for plot
        fpr, tpr, _ = roc_curve(y_test, y_proba)
        roc_data[name] = {"fpr": fpr, "tpr": tpr, "auc": roc}

        print(f"    Acc: {acc:.4f} | F1: {f1:.4f} | ROC-AUC: {roc:.4f} "
              f"| CV: {cv_scores.mean():.4f}+/-{cv_scores.std():.4f} "
              f"| Train: {train_time:.2f}s | Inf: {np.median(inf_ms):.2f}ms")

    # --- Print comparison table ---
    print("\n" + "=" * 70)
    print("  COMPARISON RESULTS")
    print("=" * 70)
    print(f"\n  {'Model':<22} {'Acc':>7} {'F1':>7} {'ROC':>7} {'CV':>12} {'Inf(ms)':>8}")
    print("  " + "-" * 66)
    for name, m in results.items():
        marker = " <-- PROPOSED" if name == "Random Forest" else ""
        print(f"  {name:<22} {m['accuracy']:>7.4f} {m['f1_score']:>7.4f} "
              f"{m['roc_auc']:>7.4f} {m['cv_mean']:.4f}+/-{m['cv_std']:.4f} "
              f"{m['inference_median_ms']:>8.2f}{marker}")

    # --- Save JSON ---
    json_path = os.path.join(RESULTS_DIR, "model_comparison.json")
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Saved: {os.path.relpath(json_path, BASE_DIR)}")

    # --- Chart 1: ROC Comparison ---
    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#6366f1", "#ef4444", "#22c55e", "#f59e0b", "#06b6d4"]
    for (name, data), color in zip(roc_data.items(), colors):
        lw = 3 if name == "Random Forest" else 1.5
        ax.plot(data["fpr"], data["tpr"],
                label=f"{name} (AUC={data['auc']:.4f})",
                color=color, linewidth=lw)
    ax.plot([0, 1], [0, 1], "k--", alpha=0.3, label="Random Baseline")
    ax.set_xlabel("False Positive Rate", fontsize=12)
    ax.set_ylabel("True Positive Rate", fontsize=12)
    ax.set_title("ROC Curve Comparison -- 5 Classifiers", fontsize=14, fontweight="bold")
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "model_comparison_roc.png"), dpi=150)
    plt.close()
    print("  Saved: evaluation/results/model_comparison_roc.png")

    # --- Chart 2: Bar comparison ---
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    model_names = list(results.keys())
    short_names = ["RF", "XGB", "LR", "SVM", "KNN"]

    # Accuracy bars
    accs = [results[n]["accuracy"] for n in model_names]
    bars = axes[0].bar(short_names, accs, color=colors, edgecolor="white", linewidth=0.5)
    axes[0].set_ylim(min(accs) - 0.05, max(accs) + 0.02)
    axes[0].set_title("Accuracy", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("Score")
    for bar, v in zip(bars, accs):
        axes[0].text(bar.get_x() + bar.get_width()/2, v + 0.003,
                     f"{v:.4f}", ha="center", fontsize=9, fontweight="bold")

    # F1 bars
    f1s = [results[n]["f1_score"] for n in model_names]
    bars = axes[1].bar(short_names, f1s, color=colors, edgecolor="white", linewidth=0.5)
    axes[1].set_ylim(min(f1s) - 0.05, max(f1s) + 0.02)
    axes[1].set_title("F1 Score (Risk Class)", fontsize=13, fontweight="bold")
    for bar, v in zip(bars, f1s):
        axes[1].text(bar.get_x() + bar.get_width()/2, v + 0.003,
                     f"{v:.4f}", ha="center", fontsize=9, fontweight="bold")

    # Inference time bars
    infs = [results[n]["inference_median_ms"] for n in model_names]
    bars = axes[2].bar(short_names, infs, color=colors, edgecolor="white", linewidth=0.5)
    axes[2].set_title("Inference Latency (ms)", fontsize=13, fontweight="bold")
    axes[2].set_ylabel("Milliseconds")
    for bar, v in zip(bars, infs):
        axes[2].text(bar.get_x() + bar.get_width()/2, v + max(infs)*0.02,
                     f"{v:.1f}", ha="center", fontsize=9, fontweight="bold")

    plt.suptitle("Model Comparison -- Adaptive Authentication",
                 fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "model_comparison_bars.png"),
                dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: evaluation/results/model_comparison_bars.png")

    # --- Chart 3: Heatmap ---
    metrics_for_heatmap = ["accuracy", "precision", "recall", "f1_score", "roc_auc", "pr_auc"]
    data_matrix = []
    for name in model_names:
        row = [results[name][m] for m in metrics_for_heatmap]
        data_matrix.append(row)

    fig, ax = plt.subplots(figsize=(10, 5))
    hm = sns.heatmap(
        data_matrix, annot=True, fmt=".4f",
        xticklabels=["Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "PR-AUC"],
        yticklabels=model_names,
        cmap="YlOrRd", vmin=0.7, vmax=1.0,
        linewidths=0.5, ax=ax,
    )
    ax.set_title("Classifier Performance Heatmap", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(os.path.join(RESULTS_DIR, "model_comparison_heatmap.png"), dpi=150)
    plt.close()
    print("  Saved: evaluation/results/model_comparison_heatmap.png")

    print("\n" + "=" * 70)
    print("  MODEL COMPARISON COMPLETE")
    print("=" * 70 + "\n")

    return results


if __name__ == "__main__":
    run_model_comparison()
