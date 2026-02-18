"""
=============================================================================
 Adaptive Authentication System — Attack Simulator
 Sends rapid POST requests to /login with different IPs, countries, and
 threat parameters to trigger ALLOW / MFA / BLOCK responses.

 Modes:
   default   — balanced mix of safe, medium, and high‑risk attacks
   --demo    — 70 % high‑risk traffic → floods dashboard with 🔴 BLOCKs
   --wave    — 3 escalating waves (safe → mixed → full assault)
=============================================================================
"""

import random
import time
import sys
import argparse
import requests

# ─── Attack Profiles ──────────────────────────────────────────────────────────
#  (country, region, device, threat_range, dist_range, description)

HIGH_RISK = [
    ("Russia",       "Eastern Europe", "desktop",    (80, 100), (5000, 14000), "🔴 RU brute-force"),
    ("North Korea",  "East Asia",      "iot_device", (88, 100), (8000, 15000), "🔴 NK IoT botnet"),
    ("China",        "East Asia",      "mobile",     (70,  98), (4000, 12000), "🔴 CN credential stuff"),
    ("Iran",         "Middle East",    "desktop",    (75,  99), (6000, 13000), "🔴 IR APT probe"),
    ("Somalia",      "Africa",         "iot_device", (85, 100), (7000, 14000), "🔴 SO bot swarm"),
    ("Ukraine",      "Eastern Europe", "desktop",    (72,  96), (4500, 11000), "🔴 UA DarkWeb dump"),
    ("Syria",        "Middle East",    "mobile",     (78,  99), (5500, 12000), "🔴 SY state actor"),
    ("Venezuela",    "South America",  "tablet",     (70,  95), (5000, 11000), "🔴 VE mass scan"),
    ("Libya",        "Africa",         "desktop",    (82, 100), (6000, 13000), "🔴 LY credential flood"),
    ("Cuba",         "Caribbean",      "iot_device", (76,  98), (4000, 10000), "🔴 CU botnet relay"),
]

MEDIUM_RISK = [
    ("Nigeria",      "Africa",         "mobile",     (45,  75), (3000,  8000), "🟡 NG phishing"),
    ("Brazil",       "South America",  "tablet",     (35,  65), (2000,  6000), "🟡 BR suspicious"),
    ("Colombia",     "South America",  "tablet",     (30,  60), (1500,  5000), "🟡 CO mixed signals"),
    ("Saudi Arabia", "Middle East",    "smart_tv",   (25,  55), (1000,  4500), "🟡 SA odd device"),
    ("Thailand",     "Southeast Asia", "mobile",     (30,  58), (1200,  4000), "🟡 TH unusual hour"),
]

LOW_RISK = [
    ("United States","North America",  "desktop",    ( 3,  18), (  10,   400), "🟢 US trusted"),
    ("Germany",      "Western Europe", "desktop",    ( 2,  15), (  30,   600), "🟢 DE regular"),
    ("Japan",        "East Asia",      "mobile",     ( 5,  22), ( 100,  1200), "🟢 JP normal"),
    ("India",        "South Asia",     "mobile",     ( 8,  30), ( 200,  2000), "🟢 IN routine"),
    ("Australia",    "Oceania",        "desktop",    ( 3,  12), (  50,   500), "🟢 AU safe"),
    ("Canada",       "North America",  "desktop",    ( 2,  14), (  20,   350), "🟢 CA trusted"),
]

ALL_PROFILES = HIGH_RISK + MEDIUM_RISK + LOW_RISK

# Fake usernames the simulator cycles through for "wrong credential" attacks
FAKE_USERS = [
    ("admin",   "admin123"),   # ← correct creds (triggers AI decision)
    ("admin",   "password"),   # ← wrong password  (triggers DENY)
    ("root",    "toor"),
    ("test",    "test123"),
    ("admin",   "admin123"),   # weighted toward correct
    ("admin",   "admin123"),
    ("admin",   "letmein"),
    ("admin",   "admin123"),
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def random_ip() -> str:
    """Generate a random public IPv4."""
    return (f"{random.randint(1, 223)}.{random.randint(0, 255)}"
            f".{random.randint(0, 255)}.{random.randint(1, 254)}")


def pick_profile(mode: str, wave_phase: int = 0):
    """Select an attack profile depending on the mode."""
    if mode == "demo":
        # 70 % high risk, 20 % medium, 10 % low
        roll = random.random()
        if roll < 0.70:
            return random.choice(HIGH_RISK)
        elif roll < 0.90:
            return random.choice(MEDIUM_RISK)
        else:
            return random.choice(LOW_RISK)
    elif mode == "wave":
        if wave_phase == 1:
            return random.choice(LOW_RISK)           # calm
        elif wave_phase == 2:
            return random.choice(MEDIUM_RISK + LOW_RISK)  # escalating
        else:
            return random.choice(HIGH_RISK + HIGH_RISK + MEDIUM_RISK)  # assault
    else:
        return random.choice(ALL_PROFILES)


# ─── Core Simulation Loop ────────────────────────────────────────────────────

def fire_request(target_url, username, password, profile):
    """Send a single simulated login and return (action, detail_str)."""
    country, region, device, threat_range, dist_range, desc = profile
    sim_ip = random_ip()
    threat = random.randint(*threat_range)
    distance = round(random.uniform(*dist_range), 2)

    payload = {
        "username": username,
        "password": password,
        "sim_ip": sim_ip,
        "sim_country": country,
        "sim_region": region,
        "sim_device": device,
        "sim_threat": str(threat),
        "sim_distance": str(distance),
    }

    resp = requests.post(target_url, data=payload,
                         allow_redirects=False, timeout=8)

    status = resp.status_code
    if status == 403:
        action = "BLOCK"
    elif status == 302:
        action = "MFA" if "mfa" in resp.headers.get("Location", "") else "ALLOW"
    elif status == 200:
        action = "ALLOW"
    elif status == 401:
        action = "DENY"
    else:
        action = "ERROR"

    detail = (f"{sim_ip:<16} | {country:<18} | "
              f"threat={threat:<3} dist={distance:>9.1f}km | {desc}")
    return action, detail


def run_simulation(
    target_url: str = "http://localhost:5000/login",
    num_attacks: int = 50,
    delay: float = 0.3,
    mode: str = "default",
):
    """Main simulation loop."""

    banner = {
        "default": "⚔️   BALANCED ATTACK SIMULATION",
        "demo":    "💀   DEMO MODE — HIGH‑RISK FLOOD",
        "wave":    "🌊   WAVE MODE — ESCALATING ASSAULT",
    }

    print("\n" + "=" * 74)
    print(f"  {banner.get(mode, banner['default'])}")
    print("=" * 74)
    print(f"  Target : {target_url}")
    print(f"  Attacks: {num_attacks}    Delay: {delay}s    Mode: {mode.upper()}")
    print("=" * 74 + "\n")

    stats = {"ALLOW": 0, "MFA": 0, "BLOCK": 0, "DENY": 0, "ERROR": 0}

    # Wave splits into 3 phases
    wave_boundaries = (
        (num_attacks // 3, 1),
        (2 * num_attacks // 3, 2),
        (num_attacks, 3),
    ) if mode == "wave" else []

    for i in range(1, num_attacks + 1):
        # ── Determine wave phase ──
        wave_phase = 0
        if mode == "wave":
            for boundary, phase in wave_boundaries:
                if i <= boundary:
                    wave_phase = phase
                    break
            # Print wave header once
            if i == 1:
                print("  ── 🟢 WAVE 1: Reconnaissance (safe traffic) ──\n")
            elif i == wave_boundaries[0][0] + 1:
                print("\n  ── 🟡 WAVE 2: Escalation (mixed traffic) ──\n")
            elif i == wave_boundaries[1][0] + 1:
                print("\n  ── 🔴 WAVE 3: Full Assault (high‑risk flood) ──\n")

        profile = pick_profile(mode, wave_phase)

        # Cycle credentials — sometimes wrong to trigger DENY
        if mode == "demo":
            # In demo mode: ~85 % correct creds so AI engine runs
            username, password = random.choices(
                FAKE_USERS, weights=[3,1,1,1,3,3,1,3], k=1
            )[0]
        else:
            username, password = random.choice(FAKE_USERS)

        try:
            action, detail = fire_request(
                target_url, username, password, profile
            )
            stats[action] = stats.get(action, 0) + 1

            icon = {
                "ALLOW": "🟢", "MFA": "🟡",
                "BLOCK": "🔴", "DENY": "🟠",
            }.get(action, "⚪")
            print(f"  [{i:>3}/{num_attacks}] {icon} {action:<6} | {detail}")

        except requests.RequestException as e:
            stats["ERROR"] += 1
            print(f"  [{i:>3}/{num_attacks}] ⚪ ERROR | {e}")

        time.sleep(delay)

    # ── Summary ──
    print("\n" + "=" * 74)
    print("  📊  SIMULATION RESULTS")
    print("=" * 74)
    total = sum(stats.values())
    for action in ["ALLOW", "MFA", "BLOCK", "DENY", "ERROR"]:
        count = stats[action]
        pct = f"{count/total*100:.0f}%" if total else "0%"
        bar = "█" * min(count, 60)
        print(f"    {action:<8} : {count:>4}  ({pct:>4})  {bar}")
    print(f"\n    Total    : {total}")

    if total > 0:
        block_pct = stats["BLOCK"] / total * 100
        if block_pct > 40:
            lvl = "🔴 CRITICAL"
        elif block_pct > 20:
            lvl = "🟠 HIGH"
        elif block_pct > 10:
            lvl = "🟡 MEDIUM"
        else:
            lvl = "🟢 LOW"
        print(f"    Threat   : {lvl}")
    print("=" * 74 + "\n")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Adaptive Auth — Attack Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python attack_sim.py --demo --count 60     # Flood dashboard with red blocks
  python attack_sim.py --wave --count 45     # 3‑phase escalating attack
  python attack_sim.py --count 30            # Balanced random mix
        """,
    )
    parser.add_argument("--url",   default="http://localhost:5000/login",
                        help="Target login URL")
    parser.add_argument("--count", type=int, default=50,
                        help="Number of attacks (default: 50)")
    parser.add_argument("--delay", type=float, default=0.3,
                        help="Delay between requests in seconds (default: 0.3)")
    parser.add_argument("--demo",  action="store_true",
                        help="Demo mode — 70%% high‑risk attacks for recording")
    parser.add_argument("--wave",  action="store_true",
                        help="Wave mode — 3 escalating phases")

    args = parser.parse_args()

    mode = "default"
    if args.demo:
        mode = "demo"
    elif args.wave:
        mode = "wave"

    run_simulation(
        target_url=args.url,
        num_attacks=args.count,
        delay=args.delay,
        mode=mode,
    )
