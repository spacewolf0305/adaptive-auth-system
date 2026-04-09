"""
=============================================================================
 Adaptive Authentication System — Database Models
 SQLAlchemy models for User accounts, Login audit logs, and SaaS API.
=============================================================================
"""

import uuid
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _generate_api_key() -> str:
    """Generate a unique API key prefixed with 'aa_live_'."""
    return f"aa_live_{uuid.uuid4().hex}"


class User(db.Model):
    """Registered user with hashed password and optional MFA secret."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(200), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    mfa_secret = db.Column(db.String(32), nullable=True)  # PyOTP base32 secret
    stripe_customer_id = db.Column(db.String(100), nullable=True)

    login_logs = db.relationship("LoginLog", backref="user", lazy="dynamic")
    api_keys = db.relationship("APIKey", backref="owner", lazy="dynamic")

    def __repr__(self):
        return f"<User {self.username}>"


class LoginLog(db.Model):
    """Immutable audit record for every login attempt."""
    __tablename__ = "login_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = db.Column(db.String(45), nullable=False)
    country = db.Column(db.String(100), default="Unknown")
    region = db.Column(db.String(100), default="Unknown")
    risk_score = db.Column(db.Float, default=0.0)
    action_taken = db.Column(db.String(20), default="ALLOW")  # ALLOW | MFA | BLOCK
    device_type = db.Column(db.String(30), default="desktop")
    threat_score = db.Column(db.Integer, default=0)
    distance_km = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<LoginLog {self.ip_address} → {self.action_taken}>"

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else "",
            "ip_address": self.ip_address,
            "country": self.country,
            "region": self.region,
            "risk_score": round(self.risk_score, 4),
            "action_taken": self.action_taken,
            "device_type": self.device_type,
            "threat_score": self.threat_score,
            "distance_km": round(self.distance_km, 2),
        }


# ─── SaaS API Models ─────────────────────────────────────────────────────────

class Plan(db.Model):
    """Pricing tier for API access."""
    __tablename__ = "plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)       # free, starter, business, enterprise
    display_name = db.Column(db.String(100), nullable=False)            # "Free", "Starter", etc.
    monthly_limit = db.Column(db.Integer, nullable=False, default=500)  # max API calls per month
    price_cents = db.Column(db.Integer, nullable=False, default=0)      # price in cents ($29 = 2900)
    stripe_price_id = db.Column(db.String(100), nullable=True)          # Stripe Price object ID
    features = db.Column(db.Text, nullable=True)                        # JSON string of feature list
    is_active = db.Column(db.Boolean, default=True)

    api_keys = db.relationship("APIKey", backref="plan", lazy="dynamic")

    def __repr__(self):
        return f"<Plan {self.display_name}>"


class APIKey(db.Model):
    """API key for authenticated access to the risk assessment API."""
    __tablename__ = "api_keys"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True, default=_generate_api_key)
    name = db.Column(db.String(100), default="Default Key")            # user-friendly label
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("plans.id"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    revoked_at = db.Column(db.DateTime, nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)

    usage_records = db.relationship("APIUsage", backref="api_key", lazy="dynamic")

    def __repr__(self):
        return f"<APIKey {self.key[:16]}...>"

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "plan": self.plan.display_name if self.plan else "Unknown",
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else "",
            "revoked_at": self.revoked_at.strftime("%Y-%m-%d %H:%M") if self.revoked_at else None,
        }


class APIUsage(db.Model):
    """Daily usage counter for API metering."""
    __tablename__ = "api_usage"

    id = db.Column(db.Integer, primary_key=True)
    api_key_id = db.Column(db.Integer, db.ForeignKey("api_keys.id"), nullable=False)
    date = db.Column(db.Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    call_count = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint("api_key_id", "date", name="uq_apikey_date"),
    )

    def __repr__(self):
        return f"<APIUsage key={self.api_key_id} date={self.date} calls={self.call_count}>"

