# ═══════════════════════════════════════════════════════════════
#  Adaptive Authentication System in Cloud — Docker Image
#  Supports both LOCAL (SQLite) and CLOUD (RDS + Redis + S3) modes
# ═══════════════════════════════════════════════════════════════

FROM python:3.9-slim

# System deps (includes PostgreSQL client libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate training data & train model at build time (local mode)
# In cloud mode, models are loaded from S3 at runtime instead
RUN python generate_data.py && python risk_engine.py

# Environment variable defaults (override in cloud deployment)
ENV SECRET_KEY="change-me-in-production"
ENV AWS_REGION="us-east-1"

# Expose Flask port
EXPOSE 5000

# Production entry point via gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
