"""
=============================================================================
 Adaptive Authentication System — Synthetic Data Generator
 Generates 10,000 realistic authentication attempts with injected risk patterns
 for training the Random Forest risk‑classification model.
=============================================================================
"""

import csv
import random
import math
import os

# ─── Configuration ────────────────────────────────────────────────────────────
NUM_ROWS = 10_000
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_auth_data.csv")

DEVICE_TYPES = ["desktop", "mobile", "tablet", "smart_tv", "iot_device"]

# 200 distinct countries (ISO 3166‑1 names subset + common short forms)
COUNTRIES = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
    "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
    "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
    "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
    "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
    "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
    "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Denmark", "Djibouti", "Dominica", "Dominican Republic", "East Timor", "Ecuador",
    "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini",
    "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia",
    "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau",
    "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India", "Indonesia",
    "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia",
    "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania",
    "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
    "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova",
    "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
    "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger",
    "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan",
    "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
    "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent", "Samoa",
    "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia",
    "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
    "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan",
    "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Togo", "Tonga",
    "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
    "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
    "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam", "Yemen",
    "Zambia", "Zimbabwe", "Kosovo", "Ivory Coast", "DR Congo", "Hong Kong",
    "Macau", "Puerto Rico",
]

# Map each country to a rough sub‑region (used for the `region` column)
REGION_MAP = {
    "United States": "North America", "Canada": "North America", "Mexico": "North America",
    "Brazil": "South America", "Argentina": "South America", "Chile": "South America",
    "Colombia": "South America", "Peru": "South America", "Venezuela": "South America",
    "Uruguay": "South America", "Paraguay": "South America", "Bolivia": "South America",
    "Ecuador": "South America", "Guyana": "South America", "Suriname": "South America",
    "United Kingdom": "Western Europe", "France": "Western Europe", "Germany": "Western Europe",
    "Italy": "Western Europe", "Spain": "Western Europe", "Portugal": "Western Europe",
    "Netherlands": "Western Europe", "Belgium": "Western Europe", "Switzerland": "Western Europe",
    "Austria": "Western Europe", "Ireland": "Western Europe", "Luxembourg": "Western Europe",
    "Monaco": "Western Europe", "Liechtenstein": "Western Europe", "Andorra": "Western Europe",
    "San Marino": "Western Europe", "Vatican City": "Western Europe",
    "Poland": "Eastern Europe", "Czech Republic": "Eastern Europe", "Slovakia": "Eastern Europe",
    "Hungary": "Eastern Europe", "Romania": "Eastern Europe", "Bulgaria": "Eastern Europe",
    "Croatia": "Eastern Europe", "Serbia": "Eastern Europe", "Slovenia": "Eastern Europe",
    "Bosnia and Herzegovina": "Eastern Europe", "Montenegro": "Eastern Europe",
    "North Macedonia": "Eastern Europe", "Albania": "Eastern Europe", "Kosovo": "Eastern Europe",
    "Moldova": "Eastern Europe", "Ukraine": "Eastern Europe", "Belarus": "Eastern Europe",
    "Lithuania": "Eastern Europe", "Latvia": "Eastern Europe", "Estonia": "Eastern Europe",
    "Russia": "Eastern Europe",
    "China": "East Asia", "Japan": "East Asia", "South Korea": "East Asia",
    "North Korea": "East Asia", "Mongolia": "East Asia", "Taiwan": "East Asia",
    "Hong Kong": "East Asia", "Macau": "East Asia",
    "India": "South Asia", "Pakistan": "South Asia", "Bangladesh": "South Asia",
    "Sri Lanka": "South Asia", "Nepal": "South Asia", "Bhutan": "South Asia",
    "Maldives": "South Asia", "Afghanistan": "South Asia",
    "Thailand": "Southeast Asia", "Vietnam": "Southeast Asia", "Indonesia": "Southeast Asia",
    "Philippines": "Southeast Asia", "Malaysia": "Southeast Asia", "Singapore": "Southeast Asia",
    "Myanmar": "Southeast Asia", "Cambodia": "Southeast Asia", "Laos": "Southeast Asia",
    "Brunei": "Southeast Asia", "East Timor": "Southeast Asia",
    "Saudi Arabia": "Middle East", "United Arab Emirates": "Middle East",
    "Qatar": "Middle East", "Kuwait": "Middle East", "Bahrain": "Middle East",
    "Oman": "Middle East", "Iran": "Middle East", "Iraq": "Middle East",
    "Israel": "Middle East", "Jordan": "Middle East", "Lebanon": "Middle East",
    "Syria": "Middle East", "Palestine": "Middle East", "Yemen": "Middle East",
    "Turkey": "Middle East", "Cyprus": "Middle East",
    "Australia": "Oceania", "New Zealand": "Oceania", "Fiji": "Oceania",
    "Papua New Guinea": "Oceania", "Samoa": "Oceania", "Tonga": "Oceania",
    "Vanuatu": "Oceania", "Solomon Islands": "Oceania", "Kiribati": "Oceania",
    "Marshall Islands": "Oceania", "Micronesia": "Oceania", "Nauru": "Oceania",
    "Palau": "Oceania", "Tuvalu": "Oceania", "Puerto Rico": "Caribbean",
}

# Default region for any country not explicitly mapped
DEFAULT_REGIONS = [
    "Africa", "Central America", "Caribbean", "Central Asia", "Pacific Islands",
]


def _get_region(country: str) -> str:
    """Return mapped region or assign a plausible default."""
    if country in REGION_MAP:
        return REGION_MAP[country]
    # Deterministic fallback seeded by country name
    return DEFAULT_REGIONS[hash(country) % len(DEFAULT_REGIONS)]


def _random_ip() -> str:
    """Generate a random public‑looking IPv4 address."""
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


# ─── Risk‑Pattern Injection Logic ─────────────────────────────────────────────

def _determine_risk(
    threat_score: int,
    distance_km: float,
    hour: int,
    prev_success: int,
    device: str,
) -> int:
    """
    Inject learnable risk patterns for the classifier.

    High‑risk rules (target_class = 1):
      R1  threat_score > 80                                         → very likely risk
      R2  distance > 3000 km AND hour ∈ [0,5]  (impossible travel)  → risk
      R3  distance > 5000 km AND prev_login_success == 0            → risk
      R4  threat_score > 60 AND device == "iot_device"              → risk
      R5  threat_score > 50 AND distance > 2000 AND hour ∈ [1,4]   → risk

    Some noise is added so the model is realistic (≈5 % label flip).
    """
    risk = 0

    # ── Deterministic rules ──
    if threat_score > 80:
        risk = 1
    elif distance_km > 3000 and hour in range(0, 6):
        risk = 1
    elif distance_km > 5000 and prev_success == 0:
        risk = 1
    elif threat_score > 60 and device == "iot_device":
        risk = 1
    elif threat_score > 50 and distance_km > 2000 and hour in range(1, 5):
        risk = 1

    # ── Add controlled noise (≈5 %) ──
    if random.random() < 0.05:
        risk = 1 - risk  # flip label

    return risk


# ─── Main Generator ───────────────────────────────────────────────────────────

def generate_dataset() -> None:
    """Generate the synthetic CSV and print summary statistics."""

    random.seed(42)  # Reproducibility

    fieldnames = [
        "ip_address",
        "country",
        "region",
        "hour_of_day",
        "device_type",
        "prev_login_success",
        "threat_score",
        "distance_from_last_login",
        "target_class",
    ]

    rows: list[dict] = []

    for _ in range(NUM_ROWS):
        country = random.choice(COUNTRIES)
        region = _get_region(country)
        hour = random.randint(0, 23)
        device = random.choice(DEVICE_TYPES)
        prev_success = random.choices([1, 0], weights=[0.75, 0.25])[0]

        # Threat score: skewed low for normal traffic, occasionally high
        if random.random() < 0.20:
            threat_score = random.randint(60, 100)   # 20 % elevated
        else:
            threat_score = random.randint(0, 59)     # 80 % normal

        # Distance: most logins are local, some are far
        if random.random() < 0.15:
            distance = round(random.uniform(3000, 15000), 2)  # 15 % long‑distance
        else:
            distance = round(random.uniform(0, 2999), 2)

        target = _determine_risk(threat_score, distance, hour, prev_success, device)

        rows.append({
            "ip_address": _random_ip(),
            "country": country,
            "region": region,
            "hour_of_day": hour,
            "device_type": device,
            "prev_login_success": prev_success,
            "threat_score": threat_score,
            "distance_from_last_login": distance,
            "target_class": target,
        })

    # ── Write CSV ──
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Summary ──
    total_risk = sum(r["target_class"] for r in rows)
    unique_countries = len({r["country"] for r in rows})
    print("=" * 60)
    print("  Synthetic Authentication Data — Generation Complete")
    print("=" * 60)
    print(f"  Total rows         : {NUM_ROWS:,}")
    print(f"  Unique countries   : {unique_countries}")
    print(f"  Safe  (class 0)    : {NUM_ROWS - total_risk:,}  ({(NUM_ROWS - total_risk) / NUM_ROWS * 100:.1f}%)")
    print(f"  Risky (class 1)    : {total_risk:,}  ({total_risk / NUM_ROWS * 100:.1f}%)")
    print(f"  Output file        : {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    generate_dataset()
