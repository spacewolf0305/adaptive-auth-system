"""
=============================================================================
 Adaptive Authentication System — Cloud Configuration
 Reads environment variables to switch between Local and AWS Cloud mode.
=============================================================================
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """
    Unified configuration.
    ─ Cloud mode:  Set DATABASE_URL, REDIS_URL, S3_BUCKET env vars.
    ─ Local mode:  Leave them unset → SQLite + in-memory fallback.
    """

    # ── Flask ──
    SECRET_KEY = os.environ.get("SECRET_KEY", "adaptive-auth-dev-key-change-me")
    PERMANENT_SESSION_LIFETIME_MINUTES = int(os.environ.get("SESSION_LIFETIME", "30"))

    # ── Database ──
    # AWS RDS PostgreSQL:  postgres://user:pass@host:5432/dbname
    # Local fallback:      sqlite:///path/to/auth.db
    DATABASE_URL = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'auth.db')}"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Redis (AWS ElastiCache) ──
    # Format: redis://host:6379/0
    REDIS_URL = os.environ.get("REDIS_URL", None)

    # ── S3 (ML Model Storage) ──
    S3_BUCKET = os.environ.get("S3_BUCKET", None)
    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

    # ── Stripe (Billing) ──
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", None)
    STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", None)
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", None)

    # ── Derived flags ──
    @property
    def is_cloud_mode(self) -> bool:
        """True when at least the database points to a cloud provider."""
        return not self.DATABASE_URL.startswith("sqlite")

    @property
    def use_redis(self) -> bool:
        return self.REDIS_URL is not None

    @property
    def use_s3(self) -> bool:
        return self.S3_BUCKET is not None

    def summary(self) -> str:
        mode = "☁️  CLOUD" if self.is_cloud_mode else "💻  LOCAL"
        db = "PostgreSQL (RDS)" if self.is_cloud_mode else "SQLite"
        cache = "Redis (ElastiCache)" if self.use_redis else "In-memory"
        storage = f"S3 ({self.S3_BUCKET})" if self.use_s3 else "Local filesystem"
        return (
            f"\n  ┌─────────────────────────────────────────┐\n"
            f"  │  Mode    : {mode:<30}│\n"
            f"  │  DB      : {db:<30}│\n"
            f"  │  Cache   : {cache:<30}│\n"
            f"  │  Storage : {storage:<30}│\n"
            f"  └─────────────────────────────────────────┘"
        )
