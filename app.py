"""
=============================================================================
 Adaptive Authentication System — Flask Application
 Routes: /login, /mfa, /dashboard, /research, /api/stats, /api/export, /logout
=============================================================================
"""

import os
import random
import math
import collections
import csv
import io
from datetime import datetime, timezone, timedelta
from functools import wraps

import requests as http_requests
import pyotp
from flask import (
    Flask, request, render_template, redirect, url_for,
    flash, session, jsonify, send_from_directory, Response,
)
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User, LoginLog
from risk_engine import predict_risk

# ─── App Factory ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "adaptive-auth-dev-key-change-me"),
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{os.path.join(BASE_DIR, 'auth.db')}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)
db.init_app(app)


@app.before_request
def _make_session_permanent():
    session.permanent = True

# ─── Rate Limiter (in‑memory) ─────────────────────────────────────────────────
# Track blocked IPs: { ip: [timestamp, ...] }
_block_history: dict[str, list[datetime]] = collections.defaultdict(list)
RATE_LIMIT_WINDOW = 600   # 10 minutes
RATE_LIMIT_MAX    = 5     # max blocks before auto‑ban
_banned_ips: set[str] = set()


def _check_rate_limit(ip: str) -> bool:
    """Return True if the IP is banned / rate‑limited."""
    if ip in _banned_ips:
        return True
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    _block_history[ip] = [t for t in _block_history[ip] if t > cutoff]
    return False


def _record_block(ip: str):
    """Record a block event; auto‑ban if threshold exceeded."""
    _block_history[ip].append(datetime.now(timezone.utc))
    if len(_block_history[ip]) >= RATE_LIMIT_MAX:
        _banned_ips.add(ip)


# ─── Helpers ──────────────────────────────────────────────────────────────────

# Rough lat/lon centroids for geo‑distance estimation
COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "United States": (38.0, -97.0), "United Kingdom": (54.0, -2.0),
    "India": (20.0, 78.0), "China": (35.0, 105.0), "Russia": (61.0, 105.0),
    "Brazil": (10.0, -55.0), "Australia": (-25.0, 135.0),
    "Germany": (51.0, 10.0), "France": (46.0, 2.0), "Japan": (36.0, 138.0),
    "Canada": (56.0, -106.0), "South Korea": (36.0, 128.0),
    "Italy": (42.0, 12.0), "Spain": (40.0, -4.0), "Mexico": (23.0, -102.0),
    "Indonesia": (-5.0, 120.0), "Turkey": (39.0, 35.0),
    "Saudi Arabia": (24.0, 45.0), "South Africa": (-29.0, 24.0),
    "Nigeria": (10.0, 8.0), "Argentina": (-34.0, -64.0),
    "Egypt": (27.0, 30.0), "Pakistan": (30.0, 70.0),
    "North Korea": (40.0, 127.0), "Iran": (32.0, 53.0),
    "Thailand": (15.0, 100.0), "Vietnam": (16.0, 108.0),
    "Philippines": (13.0, 122.0), "Colombia": (4.0, -72.0),
    "Ukraine": (49.0, 32.0), "Poland": (52.0, 20.0),
}

DEFAULT_COORD = (0.0, 0.0)


def _haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two points on Earth."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _geo_lookup(ip: str) -> dict:
    """Get geolocation from ip‑api.com, fallback to defaults."""
    try:
        resp = http_requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,country,regionName",
            timeout=3,
        )
        data = resp.json()
        if data.get("status") == "success":
            return {
                "country": data.get("country", "Unknown"),
                "region": data.get("regionName", "Unknown"),
            }
    except Exception:
        pass
    return {"country": "Unknown", "region": "Unknown"}


def _calc_distance(country: str, user_id: int) -> float:
    """Estimate distance from user's last logged country."""
    last_log = (LoginLog.query.filter_by(user_id=user_id)
                .order_by(LoginLog.timestamp.desc()).first())
    if not last_log or last_log.country == "Unknown":
        return 0.0

    prev = COUNTRY_COORDS.get(last_log.country, DEFAULT_COORD)
    curr = COUNTRY_COORDS.get(country, DEFAULT_COORD)
    return round(_haversine(prev[0], prev[1], curr[0], curr[1]), 2)


def _simulate_threat_score(ip: str) -> int:
    """Generate a simulated threat score. In production, call an external feed."""
    random.seed(hash(ip) % (2**32))
    return random.randint(0, 100)


def _detect_device(user_agent: str) -> str:
    """Basic device type detection from User‑Agent string."""
    ua = (user_agent or "").lower()
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        return "mobile"
    elif "tablet" in ua or "ipad" in ua:
        return "tablet"
    elif "smart" in ua or "tv" in ua:
        return "smart_tv"
    return "desktop"


# ─── Seed Demo User ──────────────────────────────────────────────────────────

def _seed_demo_user():
    """Create a demo user (admin/admin123) with MFA if not exists."""
    if not User.query.filter_by(username="admin").first():
        mfa_secret = pyotp.random_base32()
        user = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            mfa_secret=mfa_secret,
        )
        db.session.add(user)
        db.session.commit()
        totp_uri = pyotp.totp.TOTP(mfa_secret).provisioning_uri(
            name="admin", issuer_name="AdaptiveAuth"
        )
        print(f"\n  👤  Demo user created: admin / admin123")
        print(f"  🔑  MFA Secret : {mfa_secret}")
        print(f"  📱  OTP URI    : {totp_uri}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return redirect(url_for("login_page"))


# ─── Login ────────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html")

    # ── Collect inputs ──
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Support overrides from attack simulator (JSON or form)
    sim_ip      = request.form.get("sim_ip") or request.headers.get("X-Sim-IP")
    sim_country = request.form.get("sim_country") or request.headers.get("X-Sim-Country")
    sim_region  = request.form.get("sim_region") or request.headers.get("X-Sim-Region")
    sim_device  = request.form.get("sim_device") or request.headers.get("X-Sim-Device")
    sim_threat  = request.form.get("sim_threat") or request.headers.get("X-Sim-Threat")
    sim_dist    = request.form.get("sim_distance") or request.headers.get("X-Sim-Distance")

    ip = sim_ip or request.remote_addr or "127.0.0.1"

    # ── Rate‑limit check ──
    if _check_rate_limit(ip):
        log = LoginLog(
            ip_address=ip,
            country="BANNED",
            region="AUTO-BAN",
            risk_score=1.0,
            action_taken="RATE_LIMITED",
            device_type=sim_device or _detect_device(request.user_agent.string),
        )
        db.session.add(log)
        db.session.commit()
        flash(f"⛔ IP {ip} auto‑banned — too many blocked attempts.", "danger")
        return render_template("login.html"), 403

    # ── Step 1: Geo‑Location ──
    if sim_country:
        geo = {"country": sim_country, "region": sim_region or "Unknown"}
    else:
        geo = _geo_lookup(ip)

    # ── Authenticate ──
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        # Still log the attempt
        log = LoginLog(
            ip_address=ip,
            country=geo["country"],
            region=geo["region"],
            risk_score=1.0,
            action_taken="DENY",
            device_type=sim_device or _detect_device(request.user_agent.string),
        )
        db.session.add(log)
        db.session.commit()
        flash("Invalid credentials.", "danger")
        return render_template("login.html"), 401

    # ── Step 2: Feature Extraction ──
    device = sim_device or _detect_device(request.user_agent.string)
    distance = float(sim_dist) if sim_dist else _calc_distance(geo["country"], user.id)
    threat = int(sim_threat) if sim_threat else _simulate_threat_score(ip)

    last_log = (LoginLog.query.filter_by(user_id=user.id)
                .order_by(LoginLog.timestamp.desc()).first())
    prev_success = 1 if (last_log and last_log.action_taken == "ALLOW") else 0

    now = datetime.now(timezone.utc)

    # ── Step 3: AI Decision ──
    risk = predict_risk({
        "country": geo["country"],
        "region": geo["region"],
        "hour_of_day": now.hour,
        "device_type": device,
        "prev_login_success": prev_success,
        "threat_score": threat,
        "distance_from_last_login": distance,
    })

    # ── Step 4: Adaptive Action ──
    if risk < 0.3:
        action = "ALLOW"
    elif risk <= 0.7:
        action = "MFA"
    else:
        action = "BLOCK"

    # ── Log ──
    log = LoginLog(
        user_id=user.id,
        ip_address=ip,
        country=geo["country"],
        region=geo["region"],
        risk_score=risk,
        action_taken=action,
        device_type=device,
        threat_score=threat,
        distance_km=distance,
    )
    db.session.add(log)
    db.session.commit()

    # ── Respond ──
    if action == "BLOCK":
        _record_block(ip)
        flash(f"🚫 Access BLOCKED — Risk score {risk:.2f}", "danger")
        return render_template("login.html"), 403

    if action == "MFA":
        session["mfa_user_id"] = user.id
        session["mfa_log_id"] = log.id
        return redirect(url_for("mfa_page"))

    # ALLOW
    session["user_id"] = user.id
    flash(f"✅ Welcome, {user.username}! Risk: {risk:.2f}", "success")
    return redirect(url_for("dashboard_page"))


# ─── MFA ──────────────────────────────────────────────────────────────────────

@app.route("/mfa", methods=["GET", "POST"])
def mfa_page():
    user_id = session.get("mfa_user_id")
    if not user_id:
        return redirect(url_for("login_page"))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for("login_page"))

    if request.method == "GET":
        return render_template("mfa.html", mfa_secret=user.mfa_secret)

    code = request.form.get("code", "").strip()
    totp = pyotp.TOTP(user.mfa_secret)

    if totp.verify(code, valid_window=1):
        session.pop("mfa_user_id", None)
        session["user_id"] = user.id

        # Update log
        log_id = session.pop("mfa_log_id", None)
        if log_id:
            log = LoginLog.query.get(log_id)
            if log:
                log.action_taken = "MFA_PASS"
                db.session.commit()

        flash("✅ MFA verified — access granted!", "success")
        return redirect(url_for("dashboard_page"))
    else:
        flash("❌ Invalid MFA code. Try again.", "danger")
        return render_template("mfa.html", mfa_secret=user.mfa_secret)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


# ─── Research Artifacts ───────────────────────────────────────────────────────

@app.route("/research")
def research_page():
    return render_template("research.html")


@app.route("/static/<path:filename>")
def serve_static_file(filename):
    """Serve ML chart images from the project root."""
    return send_from_directory(BASE_DIR, filename)


# ─── Logout ───────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()
    flash("🔒 You have been logged out.", "success")
    return redirect(url_for("login_page"))


# ─── API: Stats ───────────────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    """Return the last 10 login attempts + global threat summary."""
    recent = (LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(10).all())

    total = LoginLog.query.count()
    blocked = LoginLog.query.filter_by(action_taken="BLOCK").count()
    rate_lim = LoginLog.query.filter_by(action_taken="RATE_LIMITED").count()
    mfa = LoginLog.query.filter(LoginLog.action_taken.in_(["MFA", "MFA_PASS"])).count()
    allowed = LoginLog.query.filter_by(action_taken="ALLOW").count()
    denied = LoginLog.query.filter_by(action_taken="DENY").count()

    threat_level = "LOW"
    if total > 0:
        block_pct = (blocked + rate_lim) / total
        if block_pct > 0.4:
            threat_level = "CRITICAL"
        elif block_pct > 0.2:
            threat_level = "HIGH"
        elif block_pct > 0.1:
            threat_level = "MEDIUM"

    # Average risk score
    all_logs = LoginLog.query.all()
    avg_risk = 0.0
    unique_ips = set()
    if all_logs:
        avg_risk = round(sum(l.risk_score for l in all_logs) / len(all_logs), 4)
        unique_ips = {l.ip_address for l in all_logs}

    # Country breakdown for threat map
    country_stats = {}
    for log in all_logs:
        c = log.country
        if c not in country_stats:
            country_stats[c] = {"total": 0, "blocked": 0}
        country_stats[c]["total"] += 1
        if log.action_taken in ("BLOCK", "RATE_LIMITED"):
            country_stats[c]["blocked"] += 1

    attacking = sorted(
        [{"country": k, **v} for k, v in country_stats.items() if v["blocked"] > 0],
        key=lambda x: x["blocked"],
        reverse=True,
    )[:15]

    # Timeline: last 20 events with risk scores for charting
    timeline_logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(20).all()
    timeline = [{
        "time": l.timestamp.strftime("%H:%M:%S") if l.timestamp else "",
        "risk": round(l.risk_score, 3),
        "action": l.action_taken,
    } for l in reversed(timeline_logs)]

    return jsonify({
        "recent": [r.to_dict() for r in recent],
        "summary": {
            "total": total,
            "allowed": allowed,
            "mfa_challenges": mfa,
            "blocked": blocked,
            "rate_limited": rate_lim,
            "denied": denied,
            "threat_level": threat_level,
            "avg_risk": avg_risk,
            "unique_ips": len(unique_ips),
            "banned_ips": len(_banned_ips),
        },
        "attacking_countries": attacking,
        "timeline": timeline,
    })


@app.route("/api/clear", methods=["POST"])
def api_clear():
    """Reset dashboard data and unban all IPs."""
    LoginLog.query.delete()
    db.session.commit()
    _banned_ips.clear()
    _block_history.clear()
    return jsonify({"status": "ok", "message": "All logs cleared."})


@app.route("/api/export")
def api_export():
    """Export all login logs as a downloadable CSV."""
    logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "ip_address", "country", "region",
        "device_type", "risk_score", "threat_score",
        "distance_km", "action_taken",
    ])
    for log in logs:
        writer.writerow([
            log.timestamp.isoformat() if log.timestamp else "",
            log.ip_address, log.country, log.region,
            log.device_type, round(log.risk_score, 4),
            log.threat_score, log.distance_km, log.action_taken,
        ])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=auth_logs.csv"},
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()
    _seed_demo_user()


if __name__ == "__main__":
    print("\n  🚀  Adaptive Auth running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
