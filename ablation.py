"""
Feature-ablation study for the Adaptive Authentication risk model.

PURPOSE
-------
Tests how much the model's performance depends on each individual feature,
with special attention to Threat Score -- which is both the top-ranked
feature AND one of the rules used to generate the training labels. If the
model collapses when Threat Score is removed, its high importance is partly
an artifact of label construction (circularity). If performance holds, the
signal is distributed and the circularity concern is weaker.

HOW TO USE WITH YOUR REAL DATA
------------------------------
Replace the load_data() body with a single line that reads your CSV, e.g.:

    df = pd.read_csv("your_auth_events.csv")

It must contain the 7 feature columns named in FEATURES plus a binary
label column named "label" (1 = risk, 0 = safe). Everything else runs
unchanged. The synthetic generator below is ONLY a stand-in so the script
runs out-of-the-box and shows you the output format -- its numbers are NOT
your paper's numbers.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.preprocessing import LabelEncoder

RNG = 42
FEATURES = ["country", "region", "hour", "device", "prev_login",
            "threat_score", "distance"]
CATEGORICAL = ["country", "region", "device"]

# Model config exactly as described in the paper (Section IV-C)
RF_PARAMS = dict(n_estimators=200, max_depth=18, min_samples_split=5,
                 min_samples_leaf=2, random_state=RNG, n_jobs=-1)


# --------------------------------------------------------------------------
# REAL DATA -- loads the project's actual synthetic_auth_data.csv
# --------------------------------------------------------------------------
def load_data():
    import os
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "synthetic_auth_data.csv")
    df = pd.read_csv(csv_path)
    # Rename columns to match the experiment's FEATURES list
    df = df.rename(columns={
        "hour_of_day": "hour",
        "device_type": "device",
        "prev_login_success": "prev_login",
        "distance_from_last_login": "distance",
        "target_class": "label",
    })
    # Keep only the columns we need
    return df[FEATURES + ["label"]]


def encode(df):
    df = df.copy()
    for col in CATEGORICAL:
        df[col] = LabelEncoder().fit_transform(df[col].astype(str))
    return df


def evaluate(df, feature_subset, label="label"):
    X = df[feature_subset].values
    y = df[label].values
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=RNG)
    clf = RandomForestClassifier(**RF_PARAMS).fit(Xtr, ytr)
    proba = clf.predict_proba(Xte)[:, 1]
    pred = (proba >= 0.5).astype(int)
    cv = cross_val_score(
        RandomForestClassifier(**RF_PARAMS), X, y,
        cv=StratifiedKFold(5, shuffle=True, random_state=RNG),
        scoring="accuracy")
    return {
        "acc": accuracy_score(yte, pred),
        "f1": f1_score(yte, pred),
        "auc": roc_auc_score(yte, proba),
        "cv_mean": cv.mean(), "cv_std": cv.std(),
    }


def main():
    df = encode(load_data())
    pos_rate = df["label"].mean()
    print(f"Loaded {len(df)} events | positive rate {pos_rate:.1%}\n")

    # 1) Full model (all 7 features) -- the reference
    full = evaluate(df, FEATURES)

    # 2) Leave-one-feature-out sweep
    loo = {}
    for f in FEATURES:
        subset = [x for x in FEATURES if x != f]
        loo[f] = evaluate(df, subset)

    # 3) Threat Score ONLY -- how much can that single feature do alone?
    ts_only = evaluate(df, ["threat_score"])

    # ---- report ----
    print("=" * 64)
    print("FULL MODEL (all 7 features)")
    print(f"  acc {full['acc']:.4f} | F1 {full['f1']:.4f} | "
          f"AUC {full['auc']:.4f} | CV {full['cv_mean']:.4f}"
          f"+/-{full['cv_std']:.4f}")
    print("=" * 64)
    print("LEAVE-ONE-FEATURE-OUT  (delta vs. full; big drop = model relies on it)")
    print(f"{'removed feature':<16}{'acc':>8}{'d-acc':>9}{'F1':>8}{'AUC':>8}")
    for f in FEATURES:
        d = loo[f]["acc"] - full["acc"]
        print(f"{f:<16}{loo[f]['acc']:>8.4f}{d:>+9.4f}"
              f"{loo[f]['f1']:>8.4f}{loo[f]['auc']:>8.4f}")
    print("-" * 64)
    print(f"THREAT SCORE ALONE  ->  acc {ts_only['acc']:.4f} | "
          f"F1 {ts_only['f1']:.4f} | AUC {ts_only['auc']:.4f}")
    print("=" * 64)

    # ---- automatic interpretation ----
    drop = full["acc"] - loo["threat_score"]["acc"]
    print("\nINTERPRETATION")
    print(f"  Removing Threat Score changes accuracy by {drop:+.4f}.")
    if drop > 0.05:
        print("  -> LARGE drop: the model leans heavily on Threat Score.")
        print("     Because Threat Score is also a label-generation rule, its")
        print("     importance is partly circular. Report this honestly and")
        print("     frame Threat Score as a strong prior, not a learned finding.")
    else:
        print("  -> SMALL drop: signal is distributed across features.")
        print("     This substantially weakens the circularity objection and")
        print("     is a genuine, reportable finding -- state it explicitly.")
    print(f"  Threat Score alone reaches {ts_only['acc']:.1%} accuracy "
          f"(vs. {full['acc']:.1%} full).")


if __name__ == "__main__":
    main()
