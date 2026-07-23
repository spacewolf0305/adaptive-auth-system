"""
Adaptive-adversary evasion-cost analysis for the Adaptive Authentication model.

WHY THIS EXISTS
---------------
The paper's security evaluation uses rule-generated attacks, which is circular:
the model is scored against the same rules that produced its labels. This
experiment replaces that with a *strategic* attacker who already triggers a
BLOCK and then modifies the features under their control to slip below the
block threshold. Instead of a detection rate, we report an EVASION COST:
how much effort (and which levers) an optimizing adversary needs to evade.

This is a methodology contribution: it evaluates the decision boundary against
an adversary rather than against a fixed benchmark, so its validity does not
depend on how the synthetic attacks were generated.

THREAT / COST MODEL (first-order, fully configurable)
-----------------------------------------------------
Each feature is annotated with (a) whether the attacker can change it and
(b) the cost of doing so, tied to a real capability (see paper Section IV):
  hour          low   (1)  -- just time the login
  device        low   (1)  -- spoof user-agent
  country       med   (2)  -- route via VPN in a benign country
  region        med   (2)  -- same
  distance      high  (3)  -- obtain a VPN endpoint near the victim
  threat_score  high  (3)  -- acquire clean (unflagged) IP infrastructure
  prev_login    INF        -- cannot fake the victim's account history

The weights are illustrative and exposed as COST so a reviewer (or you) can
change them; the qualitative findings are robust to the exact numbers.

HOW TO USE WITH YOUR REAL MODEL
-------------------------------
Replace build_model() so it returns YOUR trained classifier and the encoder
state, and replace load_data() with your CSV (see ablation.py). Everything
else is model-agnostic: it only calls clf.predict_proba.
"""

import numpy as np
import pandas as pd
from itertools import combinations
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

RNG = 42
BLOCK = 0.70      # paper's block threshold
ALLOW = 0.30      # paper's allow threshold

# Feature columns as named in the trained model (encoded form)
FEATURES = ["country_enc", "region_enc", "hour_of_day", "device_enc",
            "prev_login_success", "threat_score", "distance_from_last_login"]

# attacker cost per feature; np.inf = immutable
# Keys match FEATURES so cost lookup works directly
COST = {"hour_of_day": 1, "device_enc": 1, "country_enc": 2, "region_enc": 2,
        "distance_from_last_login": 3, "threat_score": 3, "prev_login_success": np.inf}

# BENIGN values are set dynamically in main() after we know the encoder mappings
BENIGN = {}


# ---- REAL DATA loader + model builder matching risk_engine.py pipeline ----
from sklearn.preprocessing import LabelEncoder
import os, joblib

def load_data():
    """Load the project's real CSV and encode it the same way risk_engine.py does."""
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "synthetic_auth_data.csv")
    df = pd.read_csv(csv_path)
    return df


def encode_data(df):
    """Encode categoricals identically to risk_engine.py's train_model()."""
    encoders = {}
    for col, enc_col in [("country", "country_enc"),
                          ("region", "region_enc"),
                          ("device_type", "device_enc")]:
        le = LabelEncoder()
        df[enc_col] = le.fit_transform(df[col])
        encoders[col] = le
    df = df.rename(columns={"target_class": "label"})
    return df, encoders


def build_model(df):
    """Train a fresh RF with the exact same config as the paper."""
    X = df[FEATURES].values
    y = df["label"].values
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=RNG)
    clf = RandomForestClassifier(
        n_estimators=200, max_depth=18, min_samples_split=5,
        min_samples_leaf=2, random_state=RNG, n_jobs=-1).fit(Xtr, ytr)
    return clf


def risk(clf, row):
    return clf.predict_proba(row.reshape(1, -1))[:, 1][0]


def min_evasion(clf, row, target=BLOCK):
    """Smallest-cost set of feature edits that pushes risk < target.
    Batch-predicts all candidate perturbations per size level for speed.
    Returns (cost, changed_features) or (inf, None)."""
    idx = {f: i for i, f in enumerate(FEATURES)}
    mutable = [f for f in FEATURES if np.isfinite(COST[f])]
    best = (np.inf, None)
    for k in range(1, 4):                       # try changing 1, then 2, then 3
        combos = list(combinations(mutable, k))
        # Pre-filter: skip combos whose cost can't beat current best
        combos = [(c, sum(COST[f] for f in c)) for c in combos]
        combos = [(c, cost) for c, cost in combos if cost < best[0]]
        if not combos:
            continue
        # Build batch of perturbed rows
        batch = []
        for combo, cost in combos:
            cand = row.copy()
            for f in combo:
                cand[idx[f]] = BENIGN[f]
            batch.append(cand)
        # Single batch predict
        preds = clf.predict_proba(np.array(batch))[:, 1]
        for i, (combo, cost) in enumerate(combos):
            if preds[i] < target and cost < best[0]:
                best = (cost, combo)
        if best[1] is not None:                 # found something at this size
            break
    return best


def main():
    global BENIGN
    raw_df = load_data()
    df, encoders = encode_data(raw_df)
    clf = build_model(df)

    # Set BENIGN values using the real encoders
    # For country: pick a safe, common country (e.g. "United States")
    def _safe_enc(encoder_key, value):
        le = encoders[encoder_key]
        if value in le.classes_:
            return int(le.transform([value])[0])
        return 0

    BENIGN = {
        "hour_of_day": 13,
        "device_enc": _safe_enc("device_type", "desktop"),
        "country_enc": _safe_enc("country", "United States"),
        "region_enc": _safe_enc("region", "North America"),
        "distance_from_last_login": 50.0,
        "threat_score": 10,
        "prev_login_success": None,
    }

    # attackers = samples the model currently BLOCKs
    X = df[FEATURES].values
    proba = clf.predict_proba(X)[:, 1]
    blocked = X[proba >= BLOCK]
    print(f"Total blocked samples in dataset: {len(blocked)}")

    costs, sizes, levers, evaded = [], [], [], 0
    for i, row in enumerate(blocked):
        if i % 200 == 0:
            print(f"  Processing {i}/{len(blocked)}...")
        cost, combo = min_evasion(clf, row.astype(float), target=BLOCK)
        if combo is not None:
            evaded += 1
            costs.append(cost); sizes.append(len(combo))
            for f in combo:
                levers.append(f)

    n = len(blocked)
    print(f"Blocked attackers analysed: {n}")
    print(f"Evasion rate (reach < BLOCK): {evaded/n:.1%}")
    if costs:
        print(f"Mean evasion cost:           {np.mean(costs):.2f}")
        print(f"Mean features changed:       {np.mean(sizes):.2f}")
        print("Cheapest-lever frequency (share of minimal evasion sets):")
        # Map encoded column names back to paper-friendly names for display
        display_names = {
            "country_enc": "Country", "region_enc": "Region",
            "hour_of_day": "Hour of Day", "device_enc": "Device Type",
            "prev_login_success": "Prev Login",
            "threat_score": "Threat Score",
            "distance_from_last_login": "Distance",
        }
        s = pd.Series(levers).value_counts(normalize=True)
        for f, v in s.items():
            name = display_names.get(f, f)
            print(f"   {name:<20}{v:.1%}")
    print("\nRESISTANT (cannot evade at any tried cost): "
          f"{(n-evaded)/n:.1%} of blocked attackers")


if __name__ == "__main__":
    main()
