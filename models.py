"""
=============================================================================
 Adaptive Authentication System — Database Models
 SQLAlchemy models for User accounts and Login audit logs.
=============================================================================
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Registered user with hashed password and optional MFA secret."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    mfa_secret = db.Column(db.String(32), nullable=True)  # PyOTP base32 secret

    login_logs = db.relationship("LoginLog", backref="user", lazy="dynamic")

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
