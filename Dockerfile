# ═══════════════════════════════════════════════════════════════
#  Adaptive Authentication System — Docker Image
# ═══════════════════════════════════════════════════════════════

FROM python:3.9-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Generate training data & train model at build time
RUN python generate_data.py && python risk_engine.py

# Expose Flask port
EXPOSE 5000

# Production entry point via gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
