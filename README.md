**Conceptualized and Developed by Satwik Basu**

# 🛡️ Adaptive Authentication System in Cloud

> AI-powered risk-based login system combining a trained Random Forest classifier with a real-time Flask web application, **deployed on AWS Cloud**.

---

## ☁️ Cloud Architecture

```
┌───────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Login Form   │────▶│   Flask App      │────▶│  Risk Engine    │
│  (browser)    │     │   (app.py)       │     │  (Random Forest)│
└───────────────┘     └────────┬─────────┘     └────────┬────────┘
                               │                        │
                    ┌──────────▼──────────┐   ┌─────────▼────────┐
                    │  Feature Extraction │   │  predict_risk()  │
                    │  • Geo-Location     │   │  Returns 0.0–1.0 │
                    │  • Distance Calc    │   └─────────┬────────┘
                    │  • Threat Score     │             │
                    │  • Device Detection │   ┌─────────▼────────┐
                    │  • Login History    │   │ Adaptive Action   │
                    └─────────────────────┘   │ <0.3 → ALLOW     │
                                              │ 0.3–0.7 → MFA   │
                                              │ >0.7 → BLOCK     │
                                              └──────────────────┘

              ┌──────────────── AWS Cloud ────────────────┐
              │                                           │
              │  ┌─────────────┐    ┌──────────────────┐  │
              │  │  RDS        │    │  ElastiCache     │  │
              │  │  PostgreSQL │    │  Redis           │  │
              │  │  (Database) │    │  (Rate Limiting  │  │
              │  │             │    │   & Sessions)    │  │
              │  └─────────────┘    └──────────────────┘  │
              │                                           │
              │  ┌─────────────┐    ┌──────────────────┐  │
              │  │  S3 Bucket  │    │ Elastic Beanstalk│  │
              │  │  (ML Models │    │  (App Hosting    │  │
              │  │   & Charts) │    │   + Auto-Scale)  │  │
              │  └─────────────┘    └──────────────────┘  │
              └───────────────────────────────────────────┘
```

## 🚀 Quick Start

### Option 1: Run Locally (No AWS Required)

```bash
pip install -r requirements.txt
python generate_data.py
python risk_engine.py
python app.py
```
Open: http://localhost:5000/login — Demo credentials: `admin` / `admin123`

### Option 2: Run with Docker Compose (Cloud-like Local Stack)

```bash
docker-compose up --build
```
This spins up PostgreSQL + Redis + Flask locally, mirroring the AWS cloud setup.

### Option 3: Deploy to AWS Cloud

#### Prerequisites
- AWS CLI configured (`aws configure`)
- EB CLI installed (`pip install awsebcli`)

#### Step 1: Create AWS Resources
```bash
# Create S3 bucket for ML models
aws s3 mb s3://adaptive-auth-models --region us-east-1

# Train model and upload to S3
S3_BUCKET=adaptive-auth-models python risk_engine.py

# Create RDS PostgreSQL instance (free tier)
aws rds create-db-instance \
    --db-instance-identifier adaptive-auth-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username auth_user \
    --master-user-password your-secure-password \
    --allocated-storage 20

# Create ElastiCache Redis cluster (free tier)
aws elasticache create-cache-cluster \
    --cache-cluster-id adaptive-auth-cache \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1
```

#### Step 2: Deploy with Elastic Beanstalk
```bash
eb init adaptive-auth-system --platform docker --region us-east-1
eb create adaptive-auth-prod

# Set environment variables
eb setenv \
    DATABASE_URL=postgresql://auth_user:your-password@rds-endpoint:5432/adaptiveauth \
    REDIS_URL=redis://elasticache-endpoint:6379/0 \
    S3_BUCKET=adaptive-auth-models \
    SECRET_KEY=your-production-secret-key \
    AWS_REGION=us-east-1
```

#### Step 3: Open Your App
```bash
eb open
```

---

## 📂 Project Structure

```
adaptive-auth-system/
├── config.py                 # ☁️ Cloud/Local config (env vars)
├── app.py                    # Flask app (Redis rate-limiter)
├── models.py                 # SQLAlchemy ORM (RDS/SQLite)
├── risk_engine.py            # ML engine (S3 model storage)
├── attack_sim.py             # Brute-force attack simulator
├── generate_data.py          # Synthetic dataset generator
├── requirements.txt          # Python deps (incl. AWS SDK)
├── Dockerfile                # Cloud-ready container
├── docker-compose.yml        # Local dev stack (PG + Redis)
├── .ebextensions/
│   ├── 01_flask.config       # EB app + auto-scaling config
│   └── 02_packages.config    # System packages for RDS
├── templates/
│   ├── login.html            # Login + Attacker Simulator
│   ├── mfa.html              # MFA challenge page
│   ├── dashboard.html        # Live threat dashboard
│   └── research.html         # Model performance viewer
├── adaptive_auth_model.pkl   # Trained model (or from S3)
├── label_encoders.pkl        # Feature encoders (or from S3)
└── auth.db                   # SQLite (local mode only)
```

## ☁️ Cloud Services Used

| AWS Service | Purpose | Free Tier |
|---|---|---|
| **RDS PostgreSQL** | User accounts & login audit logs | db.t3.micro (750 hrs/mo) |
| **ElastiCache Redis** | Rate limiting, sessions, IP bans | cache.t3.micro (750 hrs/mo) |
| **S3** | ML model & chart artifact storage | 5 GB free |
| **Elastic Beanstalk** | App hosting with auto-scaling | t3.micro (750 hrs/mo) |

## 🔌 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | No | `sqlite:///auth.db` | PostgreSQL RDS connection string |
| `REDIS_URL` | No | `None` (in-memory) | ElastiCache Redis endpoint |
| `S3_BUCKET` | No | `None` (local files) | S3 bucket for ML artifacts |
| `AWS_REGION` | No | `us-east-1` | AWS region |
| `SECRET_KEY` | Yes | dev key | Flask session encryption key |

> When no cloud env vars are set, the app runs in **local mode** with SQLite + in-memory rate limiting.

## 🧠 How the AI Works

The Random Forest classifier uses **7 features** to score each login attempt:

| Feature | Description | Impact |
|---------|-------------|--------|
| `threat_score` | IP reputation (0–100) | ⬆️ Highest |
| `distance_from_last_login` | km from previous login | ⬆️ High |
| `hour_of_day` | Login time (0–23) | ⬆️ Medium |
| `device_type` | desktop/mobile/IoT/etc. | ⬆️ Medium |
| `country` | Geographic origin | ⬆️ Medium |
| `prev_login_success` | Last login outcome | ⬇️ Lower |
| `region` | Continental region | ⬇️ Lower |

## 🔐 Security Features

- **Adaptive AI scoring** — risk-proportional response (allow/challenge/block)
- **MFA with TOTP** — time-based one-time passwords via PyOTP
- **IP rate limiting** — Redis-backed auto-bans (persistent across restarts in cloud)
- **Geo-distance tracking** — detects impossible travel patterns
- **Full audit logging** — every attempt recorded in PostgreSQL with risk factors
- **Password hashing** — Werkzeug scrypt hashing
- **Server-side sessions** — Redis-backed sessions (no sensitive data in cookies)

## 📊 API Endpoints

| Route | Method | Description |
|-------|--------|-------------|
| `/login` | GET/POST | Login page + authentication |
| `/mfa` | GET/POST | TOTP verification challenge |
| `/dashboard` | GET | Live threat monitoring dashboard |
| `/research` | GET | Model performance & charts |
| `/api/stats` | GET | JSON: recent attempts, stats, timeline |
| `/api/export` | GET | Download all logs as CSV |
| `/api/clear` | POST | Reset all logs and bans |
| `/logout` | GET | End session |

## 🔧 Attack Simulation

```bash
python attack_sim.py --count 50          # Balanced mix
python attack_sim.py --demo --count 60   # 70% high-risk flood
python attack_sim.py --wave --count 45   # 3-phase escalating attack
```

---

## 📄 License

MIT License

Copyright (c) 2026 Satwik Basu

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
