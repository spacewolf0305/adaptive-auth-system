"""
=============================================================================
 Adaptive Authentication System in Cloud — AI Risk Engine
 Trains a Random Forest Classifier on synthetic auth data, generates
 research-grade visualisations, and exposes a real-time inference function.
 Cloud:  Stores/loads model artifacts from AWS S3 when configured.
=============================================================================
"""

import os
import warnings
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
)
from sklearn.preprocessing import LabelEncoder

warnings.filterwarnings("ignore")

from config import Config
_cfg = Config()

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "synthetic_auth_data.csv")
MODEL_FILE = os.path.join(BASE_DIR, "adaptive_auth_model.pkl")
ENCODER_FILE = os.path.join(BASE_DIR, "label_encoders.pkl")
FEATURE_IMG = os.path.join(BASE_DIR, "feature_importance.png")
CONFUSION_IMG = os.path.join(BASE_DIR, "confusion_matrix.png")

# Features the model will use (same order expected at inference time)
FEATURE_COLS = [
    "country_enc",
    "region_enc",
    "hour_of_day",
    "device_enc",
    "prev_login_success",
    "threat_score",
    "distance_from_last_login",
]

PRETTY_FEATURE_NAMES = [
    "Country",
    "Region",
    "Hour of Day",
    "Device Type",
    "Prev Login Success",
    "Threat Score",
    "Distance (km)",
]


# ─── S3 Helpers ─────────────────────────────────────────────────────────────────

def _get_s3_client():
    """Return a boto3 S3 client if cloud mode is enabled."""
    if not _cfg.use_s3:
        return None
    try:
        import boto3
        return boto3.client("s3", region_name=_cfg.AWS_REGION)
    except Exception as e:
        print(f"  ⚠️  S3 client failed: {e}")
        return None


def _upload_to_s3(local_path: str, s3_key: str) -> bool:
    """Upload a local file to S3. Returns True on success."""
    s3 = _get_s3_client()
    if not s3:
        return False
    try:
        s3.upload_file(local_path, _cfg.S3_BUCKET, s3_key)
        print(f"  ☁️  Uploaded to s3://{_cfg.S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        print(f"  ⚠️  S3 upload failed for {s3_key}: {e}")
        return False


def _download_from_s3(s3_key: str, local_path: str) -> bool:
    """Download a file from S3 to local path. Returns True on success."""
    s3 = _get_s3_client()
    if not s3:
        return False
    try:
        s3.download_file(_cfg.S3_BUCKET, s3_key, local_path)
        print(f"  ☁️  Downloaded from s3://{_cfg.S3_BUCKET}/{s3_key}")
        return True
    except Exception as e:
        print(f"  ⚠️  S3 download failed for {s3_key}: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#  TRAINING
# ═══════════════════════════════════════════════════════════════════════════════

def train_model() -> None:
    """
    End‑to‑end training pipeline:
      1. Load & preprocess the synthetic CSV
      2. Train a Random Forest (80/20 split)
      3. Print classification report
      4. Save model + label encoders
      5. Generate feature_importance.png & confusion_matrix.png
    """
    print("\n" + "=" * 60)
    print("  🧠  AI Risk Engine — Training Pipeline")
    print("=" * 60)

    # ── 1. Load ──
    df = pd.read_csv(DATA_FILE)
    print(f"\n  📂  Loaded {len(df):,} rows from {os.path.basename(DATA_FILE)}")

    # ── 2. Encode categorical columns ──
    encoders: dict[str, LabelEncoder] = {}
    for col, enc_col in [("country", "country_enc"),
                          ("region", "region_enc"),
                          ("device_type", "device_enc")]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col])
        encoders[col] = le

    X = df[FEATURE_COLS]
    y = df["target_class"]

    # ── 3. Split ──
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y,
    )
    print(f"  📊  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # ── 4. Train Random Forest ──
    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=18,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n  ✅  Accuracy: {acc:.4f}")
    print("\n  📋  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Safe", "Risk"]))

    # ── 5. Persist model + encoders ──
    joblib.dump(clf, MODEL_FILE)
    joblib.dump(encoders, ENCODER_FILE)
    print(f"  💾  Model saved  → {os.path.basename(MODEL_FILE)}")
    print(f"  💾  Encoders saved → {os.path.basename(ENCODER_FILE)}")

    # ── 6. Visualisations ──
    _plot_feature_importance(clf)
    _plot_confusion_matrix(y_test, y_pred)

    # ── 7. Upload to S3 (if cloud mode) ──
    if _cfg.use_s3:
        print("\n  ☁️  Uploading artifacts to S3...")
        _upload_to_s3(MODEL_FILE, "models/adaptive_auth_model.pkl")
        _upload_to_s3(ENCODER_FILE, "models/label_encoders.pkl")
        _upload_to_s3(FEATURE_IMG, "charts/feature_importance.png")
        _upload_to_s3(CONFUSION_IMG, "charts/confusion_matrix.png")

    print("\n" + "=" * 60)
    print("  🎉  Training complete — all artifacts saved.")
    print("=" * 60 + "\n")


# ─── Visualisation Helpers ────────────────────────────────────────────────────

def _plot_feature_importance(clf: RandomForestClassifier) -> None:
    """Save a horizontal bar chart of feature importances."""
    importances = clf.feature_importances_
    indices = np.argsort(importances)

    fig, ax = plt.subplots(figsize=(10, 6))
    colours = sns.color_palette("viridis", len(indices))
    ax.barh(
        [PRETTY_FEATURE_NAMES[i] for i in indices],
        importances[indices],
        color=colours,
        edgecolor="white",
        linewidth=0.5,
    )
    ax.set_xlabel("Importance", fontsize=12)
    ax.set_title("Random Forest — Feature Importance", fontsize=14, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    fig.savefig(FEATURE_IMG, dpi=200)
    plt.close(fig)
    print(f"  📈  Chart saved   → {os.path.basename(FEATURE_IMG)}")


def _plot_confusion_matrix(y_true, y_pred) -> None:
    """Save an annotated confusion‑matrix heatmap."""
    cm = confusion_matrix(y_true, y_pred)

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["Safe", "Risk"],
        yticklabels=["Safe", "Risk"],
        linewidths=1,
        linecolor="white",
        ax=ax,
    )
    ax.set_xlabel("Predicted", fontsize=12)
    ax.set_ylabel("Actual", fontsize=12)
    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
    plt.tight_layout()
    fig.savefig(CONFUSION_IMG, dpi=200)
    plt.close(fig)
    print(f"  📊  Chart saved   → {os.path.basename(CONFUSION_IMG)}")


# ═══════════════════════════════════════════════════════════════════════════════
#  INFERENCE
# ═══════════════════════════════════════════════════════════════════════════════

_cached_model = None
_cached_encoders = None


def _load_artifacts():
    """Lazy-load model and encoders. Downloads from S3 if local files are missing."""
    global _cached_model, _cached_encoders
    if _cached_model is None:
        # If local files missing but S3 is configured, download them
        if not os.path.exists(MODEL_FILE) and _cfg.use_s3:
            print("  ☁️  Local model not found — downloading from S3...")
            _download_from_s3("models/adaptive_auth_model.pkl", MODEL_FILE)
            _download_from_s3("models/label_encoders.pkl", ENCODER_FILE)

        _cached_model = joblib.load(MODEL_FILE)
        _cached_encoders = joblib.load(ENCODER_FILE)
    return _cached_model, _cached_encoders


def predict_risk(real_time_data: dict) -> float:
    """
    Predict the risk probability (0.0 – 1.0) for a login attempt.

    Parameters
    ----------
    real_time_data : dict
        Must contain the following keys:
            - country          (str)   e.g. "Russia"
            - region           (str)   e.g. "Eastern Europe"
            - hour_of_day      (int)   0‑23
            - device_type      (str)   e.g. "mobile"
            - prev_login_success (int) 0 or 1
            - threat_score     (int)   0‑100
            - distance_from_last_login (float) km

    Returns
    -------
    float
        Probability that this attempt is risky (class 1).
    """
    clf, encoders = _load_artifacts()

    # Encode categoricals — unseen labels fall back to 0 (safe default)
    def _safe_encode(encoder_key: str, value: str) -> int:
        le = encoders[encoder_key]
        if value in le.classes_:
            return int(le.transform([value])[0])
        return 0

    features = np.array([[
        _safe_encode("country", real_time_data.get("country", "")),
        _safe_encode("region", real_time_data.get("region", "")),
        int(real_time_data.get("hour_of_day", 12)),
        _safe_encode("device_type", real_time_data.get("device_type", "desktop")),
        int(real_time_data.get("prev_login_success", 1)),
        int(real_time_data.get("threat_score", 0)),
        float(real_time_data.get("distance_from_last_login", 0)),
    ]])

    proba = clf.predict_proba(features)[0]
    # proba[1] = probability of class 1 (risk)
    return round(float(proba[1]), 4)


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    train_model()

    # Quick smoke test
    print("\n  🔍  Smoke Test — predict_risk():")
    safe = predict_risk({
        "country": "United States",
        "region": "North America",
        "hour_of_day": 10,
        "device_type": "desktop",
        "prev_login_success": 1,
        "threat_score": 15,
        "distance_from_last_login": 50,
    })
    print(f"      Safe login   → risk = {safe}")

    risky = predict_risk({
        "country": "North Korea",
        "region": "East Asia",
        "hour_of_day": 3,
        "device_type": "iot_device",
        "prev_login_success": 0,
        "threat_score": 92,
        "distance_from_last_login": 8000,
    })
    print(f"      Risky login  → risk = {risky}\n")
