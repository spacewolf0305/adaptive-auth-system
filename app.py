"""
=============================================================================
 Adaptive Authentication System in Cloud — Flask Application
 Routes: /login, /mfa, /dashboard, /research, /api/stats, /api/export, /logout
 Cloud:  AWS RDS (PostgreSQL) · ElastiCache (Redis) · S3 (ML Models)
=============================================================================
"""

import os
import random
import math
import collections
import csv
import io
import json
from datetime import datetime, timezone, timedelta
from functools import wraps

import requests as http_requests
import pyotp
from flask import (
    Flask, request, render_template, redirect, url_for,
    flash, session, jsonify, send_from_directory, Response,
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, LoginLog, Plan, APIKey, APIUsage
from risk_engine import predict_risk
import uuid as uuid_mod

# ─── App Factory ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cfg = Config()

app = Flask(__name__)
app.config.update(
    SECRET_KEY=cfg.SECRET_KEY,
    SQLALCHEMY_DATABASE_URI=cfg.SQLALCHEMY_DATABASE_URI,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=cfg.PERMANENT_SESSION_LIFETIME_MINUTES),
)

# ─── Redis Session Store (cloud) or default cookie sessions (local) ──────────
_redis_client = None
if cfg.use_redis:
    try:
        import redis as redis_lib
        _redis_client = redis_lib.from_url(cfg.REDIS_URL, decode_responses=True)
        _redis_client.ping()
        print(f"  ✅  Redis connected: {cfg.REDIS_URL}")

        # Use server-side sessions stored in Redis
        from flask_session import Session
        app.config["SESSION_TYPE"] = "redis"
        app.config["SESSION_REDIS"] = redis_lib.from_url(cfg.REDIS_URL)
        app.config["SESSION_PERMANENT"] = True
        Session(app)
    except Exception as e:
        print(f"  ⚠️  Redis unavailable ({e}), falling back to in-memory")
        _redis_client = None

db.init_app(app)

print(cfg.summary())


@app.before_request
def _make_session_permanent():
    session.permanent = True


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated


# ─── Rate Limiter (Redis-backed in cloud, in-memory locally) ─────────────────
RATE_LIMIT_WINDOW = 600   # 10 minutes
RATE_LIMIT_MAX    = 5     # max blocks before auto-ban

# In-memory fallback
_block_history: dict[str, list[datetime]] = collections.defaultdict(list)
_banned_ips: set[str] = set()


def _check_rate_limit(ip: str) -> bool:
    """Return True if the IP is banned / rate-limited."""
    if _redis_client:
        # Cloud mode: check Redis
        if _redis_client.sismember("adaptive_auth:banned_ips", ip):
            return True
        # Clean old entries automatically via Redis TTL (sorted set)
        return False
    else:
        # Local mode: in-memory
        if ip in _banned_ips:
            return True
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
        _block_history[ip] = [t for t in _block_history[ip] if t > cutoff]
        return False


def _record_block(ip: str):
    """Record a block event; auto-ban if threshold exceeded."""
    if _redis_client:
        # Cloud mode: Redis sorted set with timestamp scores
        now_ts = datetime.now(timezone.utc).timestamp()
        key = f"adaptive_auth:blocks:{ip}"
        _redis_client.zadd(key, {str(now_ts): now_ts})
        _redis_client.expire(key, RATE_LIMIT_WINDOW)
        # Remove old entries
        cutoff = now_ts - RATE_LIMIT_WINDOW
        _redis_client.zremrangebyscore(key, "-inf", cutoff)
        count = _redis_client.zcard(key)
        if count >= RATE_LIMIT_MAX:
            _redis_client.sadd("adaptive_auth:banned_ips", ip)
    else:
        # Local mode: in-memory
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


def _seed_plans():
    """Create default pricing plans if they don't exist."""
    plans = [
        {"name": "free",       "display_name": "Free",       "monthly_limit": 500,     "price_cents": 0,
         "features": '["500 API calls/month", "Basic risk scoring", "Community support"]'},
        {"name": "starter",    "display_name": "Starter",    "monthly_limit": 10000,   "price_cents": 2900,
         "features": '["10,000 API calls/month", "Full risk scoring", "MFA detection", "Email support"]'},
        {"name": "business",   "display_name": "Business",   "monthly_limit": 100000,  "price_cents": 9900,
         "features": '["100,000 API calls/month", "Advanced analytics", "Geo-tracking", "Priority support", "Webhook alerts"]'},
        {"name": "enterprise", "display_name": "Enterprise", "monthly_limit": 1000000, "price_cents": 29900,
         "features": '["1,000,000 API calls/month", "Custom ML model", "Dedicated support", "SLA guarantee", "On-premise option"]'},
    ]
    for p in plans:
        if not Plan.query.filter_by(name=p["name"]).first():
            db.session.add(Plan(**p))
    db.session.commit()
    print(f"  💰  {Plan.query.count()} pricing plans ready")


# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    plans = Plan.query.filter_by(is_active=True).order_by(Plan.price_cents).all()
    return render_template("landing.html", plans=plans)


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
    # Clear rate limiter state
    if _redis_client:
        # Delete all adaptive_auth keys from Redis
        for key in _redis_client.scan_iter("adaptive_auth:*"):
            _redis_client.delete(key)
    else:
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
#  SAAS API — ROUTES
# ═══════════════════════════════════════════════════════════════════════════════


# ─── Helper: monthly usage for an API key ────────────────────────────────────

def _get_monthly_usage(api_key_id: int) -> int:
    """Return total API calls this calendar month for a given key."""
    today = datetime.now(timezone.utc).date()
    first_of_month = today.replace(day=1)
    rows = APIUsage.query.filter(
        APIUsage.api_key_id == api_key_id,
        APIUsage.date >= first_of_month,
    ).all()
    return sum(r.call_count for r in rows)


# ─── Signup ───────────────────────────────────────────────────────────────────

@app.route("/signup", methods=["GET", "POST"])
def signup_page():
    if request.method == "GET":
        return render_template("signup.html")

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not username or not email or not password:
        flash("All fields are required.", "danger")
        return render_template("signup.html"), 400

    if password != confirm:
        flash("Passwords do not match.", "danger")
        return render_template("signup.html"), 400

    if User.query.filter_by(username=username).first():
        flash("Username already taken.", "danger")
        return render_template("signup.html"), 409

    if User.query.filter_by(email=email).first():
        flash("Email already registered.", "danger")
        return render_template("signup.html"), 409

    mfa_secret = pyotp.random_base32()
    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        mfa_secret=mfa_secret,
    )
    db.session.add(user)
    db.session.commit()

    # Auto-create a free API key
    free_plan = Plan.query.filter_by(name="free").first()
    if free_plan:
        key = APIKey(user_id=user.id, plan_id=free_plan.id, name="Default Key")
        db.session.add(key)
        db.session.commit()

    session["user_id"] = user.id
    flash(f"✅ Welcome, {username}! Your free API key is ready.", "success")
    return redirect(url_for("api_dashboard"))


# ─── Public API: Risk Assessment ──────────────────────────────────────────────

@app.route("/api/v1/assess", methods=["POST"])
def api_v1_assess():
    """
    Public risk assessment endpoint. Requires X-API-Key header.
    Accepts JSON body with login context, returns risk score and action.
    """
    # 1. Validate API key
    api_key_str = request.headers.get("X-API-Key", "").strip()
    if not api_key_str:
        return jsonify({"error": "Missing X-API-Key header", "code": "AUTH_REQUIRED"}), 401

    api_key = APIKey.query.filter_by(key=api_key_str, is_active=True).first()
    if not api_key:
        return jsonify({"error": "Invalid or revoked API key", "code": "INVALID_KEY"}), 401

    # 2. Check usage limits
    monthly_usage = _get_monthly_usage(api_key.id)
    monthly_limit = api_key.plan.monthly_limit if api_key.plan else 500

    if monthly_usage >= monthly_limit:
        return jsonify({
            "error": "Monthly API limit exceeded",
            "code": "LIMIT_EXCEEDED",
            "usage": monthly_usage,
            "limit": monthly_limit,
            "plan": api_key.plan.display_name if api_key.plan else "Free",
        }), 429

    # 3. Parse request body
    data = request.get_json(silent=True) or {}

    country = data.get("country", "Unknown")
    region = data.get("region", "Unknown")
    hour = int(data.get("hour_of_day", datetime.now(timezone.utc).hour))
    device = data.get("device_type", "desktop")
    prev_success = int(data.get("prev_login_success", 1))
    threat = int(data.get("threat_score", 0))
    distance = float(data.get("distance_from_last_login", 0))

    # 4. Run the AI model
    risk = predict_risk({
        "country": country,
        "region": region,
        "hour_of_day": hour,
        "device_type": device,
        "prev_login_success": prev_success,
        "threat_score": threat,
        "distance_from_last_login": distance,
    })

    # 5. Determine action
    if risk < 0.3:
        action = "ALLOW"
    elif risk <= 0.7:
        action = "MFA"
    else:
        action = "BLOCK"

    # 6. Build reasons
    reasons = []
    if threat > 60:
        reasons.append("high_threat_score")
    if distance > 3000:
        reasons.append("unusual_distance")
    if hour < 5 or hour > 23:
        reasons.append("unusual_hour")
    if device in ("iot_device", "smart_tv"):
        reasons.append("unusual_device")
    if country in ("North Korea", "Iran", "Russia"):
        reasons.append("high_risk_country")
    if prev_success == 0:
        reasons.append("no_previous_success")

    # 7. Record usage
    today = datetime.now(timezone.utc).date()
    usage = APIUsage.query.filter_by(api_key_id=api_key.id, date=today).first()
    if usage:
        usage.call_count += 1
    else:
        usage = APIUsage(api_key_id=api_key.id, date=today, call_count=1)
        db.session.add(usage)
    db.session.commit()

    # 8. Return response
    request_id = f"req_{uuid_mod.uuid4().hex[:16]}"
    return jsonify({
        "risk_score": risk,
        "action": action,
        "reasons": reasons,
        "request_id": request_id,
        "usage": {
            "calls_today": usage.call_count,
            "calls_this_month": monthly_usage + 1,
            "monthly_limit": monthly_limit,
        },
    })


# ─── API Dashboard ────────────────────────────────────────────────────────────

@app.route("/api-dashboard")
@login_required
def api_dashboard():
    user = User.query.get(session["user_id"])
    keys = APIKey.query.filter_by(user_id=user.id).order_by(APIKey.created_at.desc()).all()

    # Enrich keys with usage data
    enriched_keys = []
    for k in keys:
        monthly = _get_monthly_usage(k.id)
        today_usage = APIUsage.query.filter_by(
            api_key_id=k.id,
            date=datetime.now(timezone.utc).date()
        ).first()
        enriched_keys.append({
            **k.to_dict(),
            "calls_today": today_usage.call_count if today_usage else 0,
            "calls_this_month": monthly,
            "monthly_limit": k.plan.monthly_limit if k.plan else 500,
            "plan_name": k.plan.display_name if k.plan else "Free",
        })

    plans = Plan.query.filter_by(is_active=True).order_by(Plan.price_cents).all()
    return render_template("api_dashboard.html", user=user, keys=enriched_keys, plans=plans)


@app.route("/api/keys/create", methods=["POST"])
@login_required
def api_key_create():
    user = User.query.get(session["user_id"])
    key_name = request.form.get("key_name", "").strip() or "API Key"
    plan_name = request.form.get("plan", "free")

    plan = Plan.query.filter_by(name=plan_name).first()
    if not plan:
        plan = Plan.query.filter_by(name="free").first()

    # Limit: max 5 keys per user
    active_keys = APIKey.query.filter_by(user_id=user.id, is_active=True).count()
    if active_keys >= 5:
        flash("Maximum 5 active API keys allowed.", "warning")
        return redirect(url_for("api_dashboard"))

    key = APIKey(user_id=user.id, plan_id=plan.id, name=key_name)
    db.session.add(key)
    db.session.commit()
    flash(f"✅ New API key created: {key.key[:20]}...", "success")
    return redirect(url_for("api_dashboard"))


@app.route("/api/keys/<int:key_id>/revoke", methods=["POST"])
@login_required
def api_key_revoke(key_id):
    key = APIKey.query.get(key_id)
    if not key or key.user_id != session["user_id"]:
        flash("API key not found.", "danger")
        return redirect(url_for("api_dashboard"))

    key.is_active = False
    key.revoked_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f"🔒 API key revoked.", "success")
    return redirect(url_for("api_dashboard"))


@app.route("/api/usage")
@login_required
def api_usage_stats():
    """JSON endpoint: usage stats for the logged-in user's keys."""
    user = User.query.get(session["user_id"])
    keys = APIKey.query.filter_by(user_id=user.id).all()
    result = []
    for k in keys:
        monthly = _get_monthly_usage(k.id)
        result.append({
            "key_id": k.id,
            "key_name": k.name,
            "key_prefix": k.key[:16] + "...",
            "plan": k.plan.display_name if k.plan else "Free",
            "calls_this_month": monthly,
            "monthly_limit": k.plan.monthly_limit if k.plan else 500,
            "is_active": k.is_active,
        })
    return jsonify({"keys": result})


# ─── Pricing ──────────────────────────────────────────────────────────────────

@app.route("/pricing")
def pricing_page():
    plans = Plan.query.filter_by(is_active=True).order_by(Plan.price_cents).all()
    return render_template("landing.html", plans=plans, scroll_to="pricing")


# ─── API Docs ─────────────────────────────────────────────────────────────────

@app.route("/api-docs")
def api_docs_page():
    return render_template("api_docs.html")


# ─── Stripe Billing ──────────────────────────────────────────────────────────

@app.route("/billing/checkout", methods=["POST"])
@login_required
def billing_checkout():
    """Create a Stripe checkout session for a plan upgrade."""
    if not cfg.STRIPE_SECRET_KEY:
        flash("Billing is not configured yet.", "warning")
        return redirect(url_for("api_dashboard"))

    try:
        import stripe
        stripe.api_key = cfg.STRIPE_SECRET_KEY

        plan_name = request.form.get("plan", "starter")
        plan = Plan.query.filter_by(name=plan_name).first()

        if not plan or not plan.stripe_price_id:
            flash("This plan is not available for purchase yet.", "warning")
            return redirect(url_for("api_dashboard"))

        user = User.query.get(session["user_id"])

        # Create or reuse Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email or f"{user.username}@adaptiveauth.local",
                metadata={"user_id": user.id, "username": user.username},
            )
            user.stripe_customer_id = customer.id
            db.session.commit()

        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
            mode="subscription",
            success_url=request.host_url + "api-dashboard?upgraded=1",
            cancel_url=request.host_url + "api-dashboard?cancelled=1",
            metadata={"user_id": user.id, "plan_name": plan.name},
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        flash(f"Billing error: {str(e)}", "danger")
        return redirect(url_for("api_dashboard"))


@app.route("/billing/webhook", methods=["POST"])
def billing_webhook():
    """Handle Stripe webhook events."""
    if not cfg.STRIPE_SECRET_KEY or not cfg.STRIPE_WEBHOOK_SECRET:
        return jsonify({"error": "Not configured"}), 503

    try:
        import stripe
        stripe.api_key = cfg.STRIPE_SECRET_KEY

        payload = request.get_data(as_text=True)
        sig_header = request.headers.get("Stripe-Signature")

        event = stripe.Webhook.construct_event(
            payload, sig_header, cfg.STRIPE_WEBHOOK_SECRET
        )

        if event.type == "checkout.session.completed":
            session_data = event.data.object
            user_id = session_data.metadata.get("user_id")
            plan_name = session_data.metadata.get("plan_name")
            subscription_id = session_data.get("subscription")

            if user_id and plan_name:
                user = User.query.get(int(user_id))
                plan = Plan.query.filter_by(name=plan_name).first()
                if user and plan:
                    # Upgrade user's latest key or create new one
                    latest_key = APIKey.query.filter_by(
                        user_id=user.id, is_active=True
                    ).order_by(APIKey.created_at.desc()).first()

                    if latest_key:
                        latest_key.plan_id = plan.id
                        latest_key.stripe_subscription_id = subscription_id
                    else:
                        new_key = APIKey(
                            user_id=user.id,
                            plan_id=plan.id,
                            stripe_subscription_id=subscription_id,
                        )
                        db.session.add(new_key)
                    db.session.commit()

        elif event.type == "customer.subscription.deleted":
            sub = event.data.object
            # Downgrade to free
            key = APIKey.query.filter_by(stripe_subscription_id=sub.id).first()
            if key:
                free_plan = Plan.query.filter_by(name="free").first()
                if free_plan:
                    key.plan_id = free_plan.id
                    key.stripe_subscription_id = None
                    db.session.commit()

        return jsonify({"status": "ok"})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/billing/portal", methods=["POST"])
@login_required
def billing_portal():
    """Redirect to Stripe customer billing portal."""
    if not cfg.STRIPE_SECRET_KEY:
        flash("Billing is not configured yet.", "warning")
        return redirect(url_for("api_dashboard"))

    try:
        import stripe
        stripe.api_key = cfg.STRIPE_SECRET_KEY

        user = User.query.get(session["user_id"])
        if not user.stripe_customer_id:
            flash("No billing account found.", "warning")
            return redirect(url_for("api_dashboard"))

        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=request.host_url + "api-dashboard",
        )
        return redirect(portal_session.url, code=303)

    except Exception as e:
        flash(f"Billing error: {str(e)}", "danger")
        return redirect(url_for("api_dashboard"))


# ═══════════════════════════════════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════════════════════════════════

with app.app_context():
    db.create_all()
    _seed_demo_user()
    _seed_plans()


if __name__ == "__main__":
    cloud_tag = " [CLOUD]" if cfg.is_cloud_mode else " [LOCAL]"
    print(f"\n  🚀  Adaptive Auth SaaS{cloud_tag} running at http://localhost:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=not cfg.is_cloud_mode)

