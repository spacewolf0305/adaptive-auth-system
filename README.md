**Conceptualized and Developed by Satwik Basu**

# 🛡️ Adaptive Authentication System

> AI-powered risk-based login system combining a trained Random Forest classifier with a real-time Flask web application.

---

## 📐 Architecture

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
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies
```bash
cd adaptive_auth
pip install -r requirements.txt
```

### 2. Generate Data & Train Model
```bash
python generate_data.py
python risk_engine.py
```
This produces:
- `synthetic_auth_data.csv` — 10,000 labeled login attempts
- `adaptive_auth_model.pkl` — Trained Random Forest (200 trees)
- `feature_importance.png` — Top risk factors chart
- `confusion_matrix.png` — Model accuracy visualization

### 3. Start the Server
```bash
python app.py
```
Open in browser:
- **Login:** http://localhost:5000/login
- **Dashboard:** http://localhost:5000/dashboard
- **Research Artifacts:** http://localhost:5000/research

Demo credentials: `admin` / `admin123`

### 4. Run Attack Simulation
```bash
# Balanced mix
python attack_sim.py --count 50

# Demo mode (70% high-risk — floods dashboard with red blocks)
python attack_sim.py --demo --count 60

# Wave mode (3 escalating phases for cinematic demos)
python attack_sim.py --wave --count 45
```

### 5. Docker Deployment
```bash
docker build -t adaptive-auth .
docker run -p 5000:5000 adaptive-auth
```

---

## 📂 Project Structure

```
adaptive_auth/
├── generate_data.py          # Synthetic dataset generator
├── risk_engine.py            # ML training + inference
├── models.py                 # SQLAlchemy ORM models
├── app.py                    # Flask application
├── attack_sim.py             # Brute-force attack simulator
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container configuration
├── synthetic_auth_data.csv   # Generated training data
├── adaptive_auth_model.pkl   # Trained model
├── label_encoders.pkl        # Feature encoders
├── feature_importance.png    # Research chart
├── confusion_matrix.png      # Research chart
├── auth.db                   # SQLite database (auto-created)
└── templates/
    ├── login.html            # Login + Attacker Simulator
    ├── mfa.html              # MFA challenge page
    ├── dashboard.html        # Live threat dashboard
    └── research.html         # Model performance viewer
```

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
- **IP rate limiting** — auto-bans IPs after 5 blocks within 10 minutes
- **Geo-distance tracking** — detects impossible travel patterns
- **Full audit logging** — every attempt recorded with risk factors
- **Password hashing** — Werkzeug scrypt hashing

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
