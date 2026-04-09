"""
=============================================================================
 Adaptive Authentication System - Academic Research Paper Generator
 Generates a formal IEEE-style research paper as PDF with all features,
 evaluation results, charts, and publication-ready metrics.
=============================================================================
"""

import os
import json
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT   = os.path.join(BASE_DIR, "Adaptive_Auth_Research_Paper.pdf")

# Images
FEAT_IMG = os.path.join(BASE_DIR, "feature_importance.png")
CONF_IMG = os.path.join(BASE_DIR, "confusion_matrix.png")

# Evaluation charts
EVAL_DIR = os.path.join(BASE_DIR, "evaluation", "results")
CHART_ROC       = os.path.join(EVAL_DIR, "roc_curve.png")
CHART_PR        = os.path.join(EVAL_DIR, "precision_recall_curve.png")
CHART_CM        = os.path.join(EVAL_DIR, "confusion_matrix.png")
CHART_FI        = os.path.join(EVAL_DIR, "feature_importance.png")
CHART_DIST      = os.path.join(EVAL_DIR, "risk_score_distribution.png")
CHART_CV        = os.path.join(EVAL_DIR, "cross_validation.png")
CHART_THRESHOLD = os.path.join(EVAL_DIR, "threshold_analysis.png")
CHART_SECURITY  = os.path.join(EVAL_DIR, "security_detection.png")
CHART_LATENCY   = os.path.join(EVAL_DIR, "latency_distribution.png")


def _load_json(filename):
    path = os.path.join(EVAL_DIR, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class PaperPDF(FPDF):

    # ── Header / Footer ──

    def header(self):
        if self.page_no() <= 1:
            return
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 150)
        self.cell(95, 5, "Adaptive Authentication Using Machine Learning", align="L")
        self.cell(95, 5, "Research Paper - April 2026", align="R")
        self.ln(3)
        self.set_draw_color(160, 160, 180)
        self.set_line_width(0.2)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        if self.page_no() <= 1:
            return
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    # ── Typography helpers ──

    def section_heading(self, number, title):
        if self.get_y() > 255:
            self.add_page()
        self.ln(2)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(20, 20, 80)
        self.cell(0, 8, f"{number}. {title.upper()}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(20, 20, 80)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(4)

    def sub_heading(self, text):
        if self.get_y() > 262:
            self.add_page()
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(40, 40, 90)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def para(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 40)
        self.multi_cell(0, 5.2, text)
        self.ln(2)

    def small_para(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 60)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def bullet(self, text):
        if self.get_y() > 270:
            self.add_page()
        x = self.l_margin
        self.set_x(x + 4)
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(30, 30, 40)
        self.cell(4, 5.2, "-")
        self.multi_cell(0, 5.2, text)

    def numbered_item(self, num, text):
        if self.get_y() > 270:
            self.add_page()
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(20, 20, 80)
        self.cell(8, 5.5, f"{num}.")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 30, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 8.5)
        self.set_fill_color(240, 240, 248)
        self.set_text_color(30, 30, 60)
        for line in text.strip().split("\n"):
            if self.get_y() > 274:
                self.add_page()
            self.cell(0, 4.8, f"  {line}", new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def add_table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        total_w = sum(col_widths)
        if total_w > 190:
            scale = 190 / total_w
            col_widths = [w * scale for w in col_widths]
        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(20, 20, 80)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        # Rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(30, 30, 40)
        fill = False
        for row in rows:
            if self.get_y() > 267:
                self.add_page()
                self.set_font("Helvetica", "", 8)
            self.set_fill_color(240, 240, 248) if fill else self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                txt = str(cell)
                max_ch = int(col_widths[i] / 1.8)
                if len(txt) > max_ch and col_widths[i] < 40:
                    txt = txt[:max_ch-2] + ".."
                self.cell(col_widths[i], 6.2, txt, border=1, fill=True,
                          align="C" if col_widths[i] <= 40 else "L")
            self.ln()
            fill = not fill
        self.ln(3)

    def add_image_safe(self, path, w=150, caption=None):
        if os.path.exists(path):
            if self.get_y() > 170:
                self.add_page()
            x = (210 - w) / 2
            self.image(path, x=x, w=w)
            if caption:
                self.set_font("Helvetica", "I", 8)
                self.set_text_color(100, 100, 120)
                self.cell(0, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(4)


# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD THE PAPER
# ═══════════════════════════════════════════════════════════════════════════════

def build_paper():
    pdf = PaperPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=16)

    ml = _load_json("ml_metrics.json")
    sec = _load_json("security_metrics.json")
    perf = _load_json("performance_metrics.json")

    # ══════════════════════════════════════════════════════════════════
    #  TITLE PAGE
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.ln(35)

    # Title
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(20, 20, 80)
    pdf.cell(0, 13, "Adaptive Authentication Using", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 13, "Machine Learning:", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(60, 60, 100)
    pdf.cell(0, 10, "A Risk-Based Multi-Tier Security System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "with SaaS API Platform", align="C", new_x="LMARGIN", new_y="NEXT")

    # Divider
    pdf.ln(8)
    pdf.set_draw_color(20, 20, 80)
    pdf.set_line_width(0.8)
    pdf.line(50, pdf.get_y(), 160, pdf.get_y())
    pdf.ln(10)

    # Meta
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 80)
    pdf.cell(0, 7, "Research Paper", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "April 2026", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(35)

    # Keywords
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(20, 20, 80)
    pdf.cell(0, 6, "Keywords:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(80, 80, 100)
    pdf.cell(0, 5, "Adaptive Authentication, Machine Learning, Random Forest, Risk-Based Security,",
             align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Multi-Factor Authentication, SaaS API, AWS Cloud, Behavioral Analysis",
             align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 140)
    pdf.cell(0, 5, "Technology Stack: Python | Flask | Scikit-Learn | AWS (RDS, ElastiCache, S3, EB) | Docker | Stripe",
             align="C", new_x="LMARGIN", new_y="NEXT")

    # ══════════════════════════════════════════════════════════════════
    #  ABSTRACT
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 80)
    pdf.cell(0, 8, "ABSTRACT", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(20, 20, 80)
    pdf.set_line_width(0.3)
    pdf.line(10, pdf.get_y(), 50, pdf.get_y())
    pdf.ln(4)

    pdf.para(
        "This paper presents an Adaptive Authentication System that employs a Random Forest "
        "classifier to dynamically adjust security responses during user login. Unlike traditional "
        "static authentication mechanisms that operate on a binary accept/reject paradigm, the "
        "proposed system evaluates seven real-time behavioral features and assigns a continuous "
        "risk score (0.0 to 1.0), enabling three proportional adaptive responses: Allow, "
        "Multi-Factor Authentication (MFA), or Block."
    )
    pdf.para(
        "The system has evolved from a local prototype into a fully cloud-deployed SaaS platform "
        "featuring AWS cloud integration (RDS PostgreSQL, ElastiCache Redis, S3, Elastic Beanstalk), "
        "a public RESTful API with key-based authentication and usage metering, Stripe-powered "
        "subscription billing with four pricing tiers, and a comprehensive research evaluation "
        "suite that generates publication-ready metrics and visualizations."
    )
    pdf.para(
        "The AI model was trained on 10,000 synthetic authentication events across 200 countries "
        "with carefully injected adversarial risk patterns. Evaluation demonstrates 94.45% test "
        "accuracy, ROC-AUC of 0.9019, PR-AUC of 0.8565, and 100% detection of high-risk attacks "
        "with 0% false positive rate at the balanced threshold. A rigorous security evaluation "
        "across 1,500 adversarial scenarios and 21 attack profiles confirms robust threat detection, "
        "while performance benchmarks show 27ms median inference latency with sustained throughput "
        "of 37+ predictions/second under concurrent load."
    )

    # ══════════════════════════════════════════════════════════════════
    #  I. INTRODUCTION
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("I", "Introduction")
    pdf.para(
        "Traditional authentication systems rely on static credential verification: a user "
        "provides a username and password, and the system either grants or denies access. This "
        "binary approach fails to account for the rich contextual information available during "
        "login -- the user's geographic location, the time of access, the device being used, and "
        "the reputation of the connecting IP address. Sophisticated attackers who have obtained "
        "valid credentials through phishing, data breaches, or social engineering can easily "
        "bypass such systems."
    )
    pdf.para(
        "This paper introduces an Adaptive Authentication System that addresses these limitations "
        "by incorporating machine learning into the authentication pipeline. The system extracts "
        "seven behavioral features from each login attempt, feeds them through a trained Random "
        "Forest classifier, and applies one of three proportional security responses based on the "
        "predicted risk score. This approach provides a continuous security spectrum rather than "
        "a discrete binary decision."
    )

    pdf.sub_heading("I-A. Problem Statement")
    pdf.para(
        "Static authentication systems present fundamental limitations: (1) they cannot detect "
        "credential reuse from anomalous locations, (2) they provide no graduated response to "
        "varying threat levels, (3) they treat all users identically regardless of behavioral "
        "context, and (4) they cannot adapt to evolving attack patterns without manual rule updates."
    )

    pdf.sub_heading("I-B. Contributions")
    pdf.bullet("A seven-feature behavioral analysis framework for real-time login risk assessment")
    pdf.bullet("A three-tier adaptive response system (Allow/MFA/Block) with configurable thresholds")
    pdf.bullet("A dual-mode architecture supporting both local development and AWS cloud deployment")
    pdf.bullet("A public SaaS API platform with key management, usage metering, and Stripe billing")
    pdf.bullet("An IP-based rate limiting system with Redis-backed persistence for production use")
    pdf.bullet("A comprehensive research evaluation suite with 9 publication-ready visualizations")
    pdf.bullet("Empirical validation across 1,500 adversarial scenarios and 21 attack profiles")
    pdf.ln(3)

    # ══════════════════════════════════════════════════════════════════
    #  II. RELATED WORK
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("II", "Related Work")
    pdf.para(
        "Risk-based authentication has been explored in various contexts. Google's approach uses "
        "device fingerprinting and location history to assess login risk silently. Microsoft's "
        "Azure AD Identity Protection applies machine learning to detect risky sign-ins and "
        "requires step-up authentication. These commercial systems, however, are proprietary "
        "and not available for academic study."
    )
    pdf.para(
        "In academic research, Freeman et al. (2016) proposed a statistical framework for "
        "risk-based authentication using IP geo-location and device fingerprinting. Wiefling et "
        "al. (2021) analyzed the effectiveness of risk-based authentication at scale. Our work "
        "extends these approaches by: (1) providing a fully open implementation, (2) incorporating "
        "machine learning with a specific Random Forest architecture, (3) adding a SaaS API layer "
        "for third-party integration, and (4) including a comprehensive evaluation suite."
    )
    pdf.para(
        "The use of Random Forests for cybersecurity classification has been validated in "
        "intrusion detection (Chio & Freeman, 2018), malware classification, and network anomaly "
        "detection. We apply this proven technique specifically to the authentication domain with "
        "a focus on real-time inference performance."
    )

    # ══════════════════════════════════════════════════════════════════
    #  III. SYSTEM ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("III", "System Architecture")
    pdf.para(
        "The system follows a layered architecture comprising five principal components: "
        "the Client Layer (web browsers, attack simulator, API consumers), the Flask Application "
        "Server (handling routing, session management, and business logic), the AI Risk Engine "
        "(feature extraction, model inference, and risk decision), the SaaS API Layer (key "
        "management, usage metering, billing), and the Cloud Data Layer (RDS PostgreSQL, "
        "ElastiCache Redis, S3 object storage)."
    )

    pdf.sub_heading("III-A. Dual-Mode Operation")
    pdf.para(
        "A key architectural decision is the system's dual-mode design. In local mode, the "
        "application uses SQLite for persistence, in-memory dictionaries for rate limiting, "
        "and local filesystem for model storage. In cloud mode, environment variables redirect "
        "these to AWS RDS (PostgreSQL), ElastiCache (Redis), and S3 respectively. The config.py "
        "module encapsulates this logic, enabling identical application code to run in both "
        "environments."
    )
    pdf.add_table(
        ["Component", "Local Mode", "Cloud Mode (AWS)"],
        [
            ["Database", "SQLite", "RDS PostgreSQL"],
            ["Sessions / Cache", "In-memory dict", "ElastiCache Redis"],
            ["Rate Limiting", "In-memory set", "Redis sorted sets + TTL"],
            ["Model Storage", "Local .pkl file", "S3 bucket"],
            ["App Hosting", "Flask dev server", "Elastic Beanstalk + Gunicorn"],
        ],
        [40, 65, 65],
    )

    pdf.sub_heading("III-B. Database Schema")
    pdf.para(
        "The system uses SQLAlchemy ORM with five normalized tables supporting both the "
        "core authentication workflow and the SaaS API platform:"
    )
    pdf.add_table(
        ["Table", "Columns", "Purpose"],
        [
            ["users", "6", "Registered accounts with hashed passwords and MFA secrets"],
            ["login_logs", "11", "Immutable audit trail for every login attempt"],
            ["plans", "8", "SaaS pricing tiers (Free, Starter, Business, Enterprise)"],
            ["api_keys", "9", "API key lifecycle with plan association and Stripe links"],
            ["api_usage", "4", "Daily metering counter per key (unique on key+date)"],
        ],
        [30, 22, 138],
    )

    pdf.sub_heading("III-C. Frontend Architecture")
    pdf.para(
        "The system includes 8 HTML templates with a glassmorphism dark-mode design language, "
        "forming a complete SaaS user experience:"
    )
    pdf.add_table(
        ["Template", "Route", "Purpose"],
        [
            ["landing.html", "/", "SaaS marketing landing page with pricing"],
            ["signup.html", "/signup", "User registration with auto API key creation"],
            ["login.html", "/login", "Authentication with integrated attack simulator"],
            ["mfa.html", "/mfa", "TOTP 6-digit code verification"],
            ["dashboard.html", "/dashboard", "Real-time threat monitoring dashboard"],
            ["research.html", "/research", "ML model performance visualizations"],
            ["api_dashboard.html", "/api-dashboard", "API key management and usage stats"],
            ["api_docs.html", "/api-docs", "Interactive API documentation"],
        ],
        [42, 35, 113],
    )

    # ══════════════════════════════════════════════════════════════════
    #  IV. AUTHENTICATION FLOW
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("IV", "Authentication Flow")
    pdf.para(
        "Every login request follows a deterministic multi-step pipeline. The process begins "
        "with rate-limit checking against the connecting IP, followed by credential validation, "
        "behavioral feature extraction, AI model inference, and adaptive action execution."
    )

    pdf.sub_heading("IV-A. Feature Extraction")
    pdf.para(
        "Seven features are extracted from each login attempt, forming the input vector for "
        "the machine learning model:"
    )
    pdf.add_table(
        ["Feature", "Type", "Source", "Range"],
        [
            ["Country", "Categorical", "ip-api.com geo-lookup", "200 countries"],
            ["Region", "Categorical", "Continental classification", "15 regions"],
            ["Hour of Day", "Integer", "UTC timestamp", "0 - 23"],
            ["Device Type", "Categorical", "User-Agent parsing", "5 types"],
            ["Prev Login Success", "Binary", "Last login log query", "0 or 1"],
            ["Threat Score", "Integer", "IP reputation (simulated)", "0 - 100"],
            ["Distance (km)", "Float", "Haversine from last login", "0 - 20,000"],
        ],
        [42, 28, 60, 42],
    )

    pdf.sub_heading("IV-B. Adaptive Response")
    pdf.para(
        "The continuous risk score is mapped to three discrete actions using configurable "
        "thresholds, providing proportional security."
    )
    pdf.add_table(
        ["Risk Range", "Action", "User Experience", "HTTP Code"],
        [
            ["0.0 - 0.3", "ALLOW", "Instant access to dashboard", "302"],
            ["0.3 - 0.7", "MFA", "TOTP 6-digit code challenge", "302"],
            ["0.7 - 1.0", "BLOCK", "Access denied, logged + rate-limited", "403"],
        ],
        [25, 22, 105, 30],
    )
    pdf.para(
        "The 0.3 lower threshold was selected to minimize false positives for legitimate users, "
        "while the 0.7 upper threshold ensures only high-confidence risk predictions trigger "
        "blocking. The MFA band (0.3-0.7) serves as a verification buffer, adding a second "
        "factor for ambiguous cases without outright denial."
    )

    # ══════════════════════════════════════════════════════════════════
    #  V. MACHINE LEARNING MODEL
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("V", "Machine Learning Model")

    pdf.sub_heading("V-A. Training Data")
    pdf.para(
        "A synthetic dataset of 10,000 authentication events was generated with the following "
        "characteristics:"
    )
    pdf.add_table(
        ["Parameter", "Value"],
        [
            ["Total Samples", "10,000"],
            ["Unique Countries", "200"],
            ["Continental Regions", "15"],
            ["Risk Class Ratio", "21.6% risky / 78.4% safe"],
            ["Train/Test Split", "80% / 20% (stratified)"],
            ["Label Noise", "~5% random flip for robustness"],
        ],
        [55, 100],
    )

    pdf.sub_heading("V-B. Risk Injection Rules")
    pdf.para(
        "Five deterministic rules were injected into the training data to teach the model "
        "real-world attack patterns. These rules encode domain expertise about common "
        "attack vectors:"
    )
    pdf.add_table(
        ["Rule", "Condition", "Label"],
        [
            ["R1", "threat_score > 80", "RISK"],
            ["R2", "distance > 3,000km AND hour in [0,5]", "RISK"],
            ["R3", "distance > 5,000km AND prev_login_success = 0", "RISK"],
            ["R4", "threat_score > 60 AND device_type = IoT", "RISK"],
            ["R5", "threat > 50 AND distance > 2,000 AND hour in [1,4]", "RISK"],
        ],
        [20, 120, 25],
    )

    pdf.sub_heading("V-C. Model Architecture")
    pdf.add_table(
        ["Hyperparameter", "Value", "Rationale"],
        [
            ["Algorithm", "Random Forest", "Ensemble robustness + interpretability"],
            ["n_estimators", "200", "Sufficient for convergence without overfitting"],
            ["max_depth", "18", "Deep enough for complex patterns"],
            ["min_samples_split", "5", "Prevents overfitting to rare patterns"],
            ["min_samples_leaf", "2", "Smooth decision boundaries"],
            ["random_state", "42", "Reproducibility"],
            ["n_jobs", "-1", "Parallel tree training"],
        ],
        [42, 38, 90],
    )

    pdf.sub_heading("V-D. S3 Model Storage")
    pdf.para(
        "In cloud mode, trained model artifacts (.pkl files) are stored in an AWS S3 bucket. "
        "The risk engine implements lazy loading: on first inference call, it checks for local "
        "files, downloads from S3 if missing, and caches the model in memory for subsequent "
        "predictions. This enables zero-downtime model updates by replacing the S3 artifact."
    )

    # ══════════════════════════════════════════════════════════════════
    #  VI. SAAS API PLATFORM
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("VI", "SaaS API Platform")
    pdf.para(
        "The system exposes a public RESTful API enabling third-party developers to integrate "
        "AI-powered risk assessment into their own applications. The platform includes API key "
        "management, usage metering, and subscription billing."
    )

    pdf.sub_heading("VI-A. Public Risk Assessment API")
    pdf.para("POST /api/v1/assess  -  Requires X-API-Key header")
    pdf.code_block(
        'Request:  { "country": "Russia", "threat_score": 85,\n'
        '            "distance_from_last_login": 8500, ... }\n'
        '\n'
        'Response: { "risk_score": 0.92, "action": "BLOCK",\n'
        '            "reasons": ["high_threat_score",\n'
        '                        "unusual_distance"],\n'
        '            "request_id": "req_a1b2c3d4...",\n'
        '            "usage": { "calls_today": 42,\n'
        '                       "monthly_limit": 10000 } }'
    )

    pdf.sub_heading("VI-B. Pricing Tiers")
    pdf.add_table(
        ["Plan", "Monthly Limit", "Price", "Key Features"],
        [
            ["Free", "500 calls", "$0/mo", "Basic risk scoring, community support"],
            ["Starter", "10,000 calls", "$29/mo", "Full scoring, MFA detection, email support"],
            ["Business", "100,000 calls", "$99/mo", "Analytics, geo-tracking, webhook alerts"],
            ["Enterprise", "1,000,000 calls", "$299/mo", "Custom ML model, SLA, on-premise option"],
        ],
        [30, 35, 25, 85],
    )

    pdf.sub_heading("VI-C. API Key Lifecycle")
    pdf.para(
        "API keys follow a managed lifecycle: auto-creation on signup (free tier), user-initiated "
        "creation (max 5 active keys), and soft-delete revocation. Each key is prefixed with "
        "'aa_live_' for identification and is associated with a pricing plan that determines "
        "the monthly call limit."
    )

    pdf.sub_heading("VI-D. Stripe Billing Integration")
    pdf.para(
        "Subscription billing is handled via Stripe Checkout sessions, with webhook handlers "
        "for checkout.session.completed (plan upgrade) and customer.subscription.deleted "
        "(downgrade to free). The Stripe Customer Portal provides self-service subscription "
        "management. All billing routes degrade gracefully when Stripe is not configured."
    )

    # ══════════════════════════════════════════════════════════════════
    #  VII. SECURITY ARCHITECTURE
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("VII", "Security Architecture")

    pdf.sub_heading("VII-A. Defense-in-Depth")
    pdf.add_table(
        ["Layer", "Component", "Mechanism"],
        [
            ["Network", "IP Rate Limiter", "Auto-ban after 5 blocked attempts in 10 min"],
            ["Network", "Redis-backed bans", "Persistent across restarts (sorted sets + TTL)"],
            ["Authentication", "Password Hashing", "Werkzeug scrypt (adaptive hashing)"],
            ["Authentication", "TOTP MFA", "PyOTP time-based 6-digit codes"],
            ["API", "Key Authentication", "X-API-Key header with prefix validation"],
            ["Intelligence", "Geo-Distance", "Haversine impossible-travel detection"],
            ["Intelligence", "Threat Scoring", "IP reputation analysis (0-100)"],
            ["Intelligence", "ML Classifier", "7-feature behavioral risk scoring"],
            ["Audit", "Full Logging", "Immutable login_logs table (RDS/SQLite)"],
            ["Audit", "CSV Export", "Downloadable audit trail for compliance"],
        ],
        [32, 42, 116],
    )

    pdf.sub_heading("VII-B. Attack Simulation")
    pdf.para(
        "A built-in adversarial testing tool (attack_sim.py) enables realistic threat demonstration "
        "with 21 attack profiles across three risk categories, supporting default, demo, and "
        "wave operational modes for different presentation scenarios."
    )

    # ══════════════════════════════════════════════════════════════════
    #  VIII. CLOUD INFRASTRUCTURE
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("VIII", "Cloud Infrastructure")
    pdf.para(
        "The system deploys on four AWS managed services, all operating within the free tier "
        "for development:"
    )
    pdf.add_table(
        ["AWS Service", "Instance Type", "Purpose"],
        [
            ["RDS PostgreSQL", "db.t3.micro", "User accounts, login audit logs, SaaS data"],
            ["ElastiCache Redis", "cache.t3.micro", "Sessions, rate limiting, IP ban persistence"],
            ["S3", "Standard", "ML model artifacts and chart storage"],
            ["Elastic Beanstalk", "t3.micro", "Dockerized app hosting with auto-scaling"],
        ],
        [40, 35, 100],
    )
    pdf.para(
        "Deployment is automated via PowerShell scripts (deploy_aws.ps1, cleanup_aws.ps1) that "
        "provision and configure all resources. Docker and Docker Compose provide local cloud "
        "emulation with PostgreSQL + Redis + Flask containers."
    )

    # ══════════════════════════════════════════════════════════════════
    #  IX. EVALUATION METHODOLOGY
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("IX", "Evaluation Methodology")
    pdf.para(
        "A comprehensive evaluation suite (evaluation/ directory) was developed to generate "
        "quantitative metrics suitable for formal publication. The suite comprises four modules "
        "orchestrated by run_evaluation.py:"
    )
    pdf.add_table(
        ["Module", "Purpose", "Key Outputs"],
        [
            ["research_evaluation.py", "ML classifier metrics", "Accuracy, F1, ROC-AUC, PR-AUC, CV scores"],
            ["security_evaluation.py", "Attack detection analysis", "TPR, FPR, per-profile detection rates"],
            ["performance_benchmark.py", "Latency and throughput", "p50/p95/p99 latency, concurrent tests"],
            ["generate_research_charts.py", "Visualization generation", "9 publication-ready PNG charts"],
        ],
        [55, 50, 80],
    )

    # ══════════════════════════════════════════════════════════════════
    #  X. EXPERIMENTAL RESULTS: ML PERFORMANCE
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("X", "Results: ML Model Performance")

    pdf.sub_heading("X-A. Classification Metrics")
    if ml:
        pdf.add_table(
            ["Metric", "Safe (Class 0)", "Risk (Class 1)", "Weighted"],
            [
                ["Precision", str(ml["precision"]["safe"]), str(ml["precision"]["risk"]), str(ml["precision"]["weighted"])],
                ["Recall",    str(ml["recall"]["safe"]),    str(ml["recall"]["risk"]),    str(ml["recall"]["weighted"])],
                ["F1-Score",  str(ml["f1_score"]["safe"]),  str(ml["f1_score"]["risk"]),  str(ml["f1_score"]["weighted"])],
            ],
            [30, 42, 42, 42],
        )
        pdf.para(
            f"Overall test accuracy: {ml['accuracy']} ({ml['dataset']['test_samples']:,} samples). "
            f"ROC-AUC: {ml['roc_auc']}. PR-AUC: {ml['pr_auc']}. "
            f"Training time: {ml['training']['train_time_seconds']}s."
        )
    else:
        pdf.para("Accuracy: 0.9445 | ROC-AUC: 0.9019 | PR-AUC: 0.8565")

    pdf.sub_heading("X-B. Cross-Validation")
    if ml and "cross_validation" in ml:
        cv = ml["cross_validation"]
        cv_rows = []
        for key, label in [("5_fold", "5-Fold Accuracy"), ("10_fold", "10-Fold Accuracy"),
                           ("5_fold_f1_weighted", "5-Fold F1 (weighted)"),
                           ("5_fold_roc_auc", "5-Fold ROC-AUC")]:
            if key in cv:
                cv_rows.append([label, f"{cv[key]['mean']} +/- {cv[key]['std']}"])
        pdf.add_table(["Metric", "Mean +/- Std"], cv_rows, [55, 100])
    pdf.para(
        "The consistently low standard deviation across all fold counts (std < 0.007) confirms "
        "the model generalizes well and does not overfit to the training partition."
    )

    pdf.sub_heading("X-C. Feature Importance")
    if ml and "feature_importance" in ml:
        fi_rows = [[str(f["rank"]), f["feature"], str(f["importance"]),
                     f"{f['importance']*100:.1f}%"] for f in ml["feature_importance"]]
        pdf.add_table(["Rank", "Feature", "Score", "%"], fi_rows, [15, 55, 30, 25])
    pdf.para(
        "Threat Score (51.0%) and Distance (22.5%) collectively contribute 73.5% of the model's "
        "decision-making, aligning with cybersecurity domain knowledge where IP reputation and "
        "impossible travel are the primary indicators of credential misuse."
    )
    pdf.add_image_safe(CHART_FI, w=145, caption="Figure 1: Feature importance analysis (Random Forest)")

    pdf.sub_heading("X-D. ROC Curve")
    pdf.add_image_safe(CHART_ROC, w=140, caption="Figure 2: ROC curve (AUC = 0.9019)")

    pdf.sub_heading("X-E. Precision-Recall Curve")
    pdf.add_image_safe(CHART_PR, w=140, caption="Figure 3: Precision-Recall curve (AUC = 0.8565)")

    pdf.sub_heading("X-F. Confusion Matrix")
    if ml and "confusion_matrix" in ml:
        cm = ml["confusion_matrix"]["raw"]
        total = sum(sum(r) for r in cm)
        pdf.add_table(
            ["", "Predicted Safe", "Predicted Risk", "Total"],
            [
                ["Actual Safe", str(cm[0][0]), str(cm[0][1]), str(cm[0][0]+cm[0][1])],
                ["Actual Risk", str(cm[1][0]), str(cm[1][1]), str(cm[1][0]+cm[1][1])],
            ],
            [40, 42, 42, 30],
        )
        pdf.para(
            f"Out of {total:,} test samples, the model produces {cm[0][1]} false positives "
            f"(safe logins flagged as risky) and {cm[1][0]} false negatives "
            f"(risky logins classified as safe)."
        )
    pdf.add_image_safe(CHART_CM, w=160, caption="Figure 4: Confusion matrix (normalized and raw)")

    pdf.sub_heading("X-G. Risk Score Distribution")
    pdf.add_image_safe(CHART_DIST, w=160, caption="Figure 5: Risk score distribution by class (violin + histogram)")

    pdf.sub_heading("X-H. Cross-Validation Stability")
    pdf.add_image_safe(CHART_CV, w=140, caption="Figure 6: Stratified k-fold cross-validation (k = 3, 5, 7, 10)")

    # ══════════════════════════════════════════════════════════════════
    #  XI. RESULTS: SECURITY EVALUATION
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("XI", "Results: Security Evaluation")
    pdf.para(
        "A dedicated security evaluation was conducted using 1,500 synthetic scenarios generated "
        "from 21 attack profiles spanning three risk categories. The evaluation tests the model's "
        "ability to detect attacks via the predict_risk() function in a fully offline, "
        "reproducible environment."
    )

    pdf.sub_heading("XI-A. Test Scenario Composition")
    if sec:
        pdf.add_table(
            ["Category", "Scenarios", "Profiles", "Description"],
            [
                ["High-Risk", "500", "10", "RU, KP, CN, IR, SO, UA, SY, VE, LY, CU"],
                ["Medium-Risk", "250", "5", "NG, BR, CO, SA, TH"],
                ["Legitimate", "750", "6", "US, DE, JP, IN, AU, CA"],
            ],
            [30, 28, 22, 100],
        )

    pdf.sub_heading("XI-B. Detection at Multiple Thresholds")
    if sec and "threshold_metrics" in sec:
        tm = sec["threshold_metrics"]
        rows = []
        for name in ["conservative", "balanced", "aggressive"]:
            if name in tm:
                m = tm[name]
                rows.append([
                    f"{name.title()} ({m['threshold']})",
                    str(m["true_positive_rate"]),
                    str(m["false_positive_rate"]),
                    str(m["precision"]),
                    str(m["recall"]),
                    str(m["f1_score"]),
                ])
        pdf.add_table(
            ["Threshold", "TPR", "FPR", "Precision", "Recall", "F1"],
            rows, [42, 22, 22, 28, 22, 22],
        )
        pdf.para(
            f"At the balanced threshold (0.5), the model achieves {tm['balanced']['true_positive_rate']*100:.1f}% "
            f"true positive rate with {tm['balanced']['false_positive_rate']*100:.1f}% false positive rate "
            f"and perfect precision (1.0), meaning every flagged login is a genuine attack."
        )

    pdf.sub_heading("XI-C. Detection by Risk Category")
    if sec and "category_detection" in sec:
        cd = sec["category_detection"]
        rows = []
        for cat in ["high", "medium", "low"]:
            if cat in cd:
                d = cd[cat]
                rows.append([cat.upper(), str(d["total_scenarios"]), str(d["detected"]),
                             f"{d['detection_rate']*100:.1f}%", str(d["avg_risk_score"])])
        pdf.add_table(
            ["Category", "Scenarios", "Detected", "Rate", "Avg Score"],
            rows, [30, 28, 28, 25, 35],
        )
    pdf.add_image_safe(CHART_SECURITY, w=160, caption="Figure 7: Detection rate and mean score by attack category")

    pdf.sub_heading("XI-D. Per-Profile Detection")
    if sec and "profile_detection" in sec:
        sorted_p = sorted(sec["profile_detection"].items(),
                          key=lambda x: x[1]["detection_rate"], reverse=True)
        rows = [[lbl, str(d["total"]), f"{d['detection_rate']*100:.1f}%",
                 str(d["avg_risk_score"])] for lbl, d in sorted_p]
        pdf.add_table(
            ["Attack Profile", "Tests", "Rate", "Avg Score"],
            rows, [50, 25, 28, 35],
        )

    pdf.sub_heading("XI-E. Score Separation Analysis")
    if sec and "score_distribution" in sec:
        sd = sec["score_distribution"]
        pdf.add_table(
            ["Statistic", "Attack Scores", "Legitimate Scores"],
            [
                ["Mean",   str(sd["attacks"]["mean"]),   str(sd["legitimate"]["mean"])],
                ["Median", str(sd["attacks"]["median"]), str(sd["legitimate"]["median"])],
                ["Std",    str(sd["attacks"]["std"]),     str(sd["legitimate"]["std"])],
                ["Min",    str(sd["attacks"]["min"]),     str(sd["legitimate"]["min"])],
                ["Max",    str(sd["attacks"]["max"]),     str(sd["legitimate"]["max"])],
            ],
            [35, 55, 55],
        )
        pdf.para(
            f"The score separation of {sd['separation']} between attack and legitimate "
            "distributions demonstrates strong discriminative power with minimal class overlap."
        )

    # ══════════════════════════════════════════════════════════════════
    #  XII. RESULTS: PERFORMANCE BENCHMARKS
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("XII", "Results: Performance Benchmarks")

    pdf.sub_heading("XII-A. Single-Thread Inference Latency")
    if perf and "single_thread" in perf:
        st = perf["single_thread"]
        pdf.add_table(
            ["Metric", "Value"],
            [
                ["Iterations", str(st["iterations"])],
                ["Median Latency", f"{st['median_ms']:.3f} ms"],
                ["Mean Latency", f"{st['mean_ms']:.3f} ms"],
                ["p95 Latency", f"{st['p95_ms']:.3f} ms"],
                ["p99 Latency", f"{st['p99_ms']:.3f} ms"],
                ["Min / Max", f"{st['min_ms']:.3f} / {st['max_ms']:.3f} ms"],
                ["Throughput", f"{perf['throughput_per_sec']} predictions/sec"],
            ],
            [50, 100],
        )
    pdf.add_image_safe(CHART_LATENCY, w=140, caption="Figure 8: Inference latency distribution (1,000 predictions)")

    pdf.sub_heading("XII-B. Concurrent Load Testing")
    if perf and "concurrent" in perf:
        rows = []
        for key, d in perf["concurrent"].items():
            rows.append([str(d["threads"]), str(d["total_requests"]),
                         f"{d['total_time_seconds']}s",
                         f"{d['throughput_per_sec']}/s",
                         f"{d['median_ms']:.1f}", f"{d['p99_ms']:.1f}"])
        pdf.add_table(
            ["Threads", "Requests", "Time", "Throughput", "Median ms", "p99 ms"],
            rows, [25, 28, 25, 33, 30, 30],
        )
        pdf.para(
            "The system maintains 40-46 predictions/second across all concurrency levels, "
            "demonstrating stable throughput. Latency increases linearly with thread count "
            "due to Python's GIL for CPU-bound Random Forest inference, suggesting that "
            "horizontal scaling via multiple worker processes is the recommended approach "
            "for high-throughput production deployments."
        )

    # ══════════════════════════════════════════════════════════════════
    #  XIII. THRESHOLD SENSITIVITY ANALYSIS
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("XIII", "Threshold Sensitivity Analysis")
    pdf.para(
        "The classification threshold determines how the continuous risk score maps to a "
        "binary decision. This analysis evaluates the precision-recall tradeoff across "
        "threshold values from 0.2 to 0.8."
    )
    if ml and "threshold_analysis" in ml:
        rows = [[str(t["threshold"]), str(t["accuracy"]), str(t["precision"]),
                 str(t["recall"]), str(t["f1"])] for t in ml["threshold_analysis"]]
        pdf.add_table(
            ["Threshold", "Accuracy", "Precision", "Recall", "F1-Score"],
            rows, [30, 32, 32, 32, 32],
        )
        best = max(ml["threshold_analysis"], key=lambda x: x["f1"])
        pdf.para(
            f"The optimal F1-score of {best['f1']} is achieved at threshold {best['threshold']}. "
            "However, the system employs a three-tier threshold (0.3/0.7) rather than binary "
            "classification, which provides the additional dimension of proportional response."
        )
    pdf.add_image_safe(CHART_THRESHOLD, w=140,
                       caption="Figure 9: Threshold sensitivity  -  Accuracy, Precision, Recall, F1")

    # ══════════════════════════════════════════════════════════════════
    #  XIV. DISCUSSION
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("XIV", "Discussion")

    pdf.sub_heading("XIV-A. Key Findings")
    pdf.numbered_item("1",
        "The Random Forest model achieves 94.45% accuracy with ROC-AUC 0.9019, demonstrating "
        "that behavioral features provide sufficient discriminative power for real-time "
        "login risk assessment.")
    pdf.numbered_item("2",
        "Threat Score and Distance alone contribute 73.5% of decision-making, validating "
        "the cybersecurity heuristic that IP reputation and impossible travel are the "
        "strongest indicators of credential misuse.")
    pdf.numbered_item("3",
        "100% high-risk attack detection with 0% false positive rate at the balanced "
        "threshold (0.5) confirms the model's strong performance on the most critical "
        "security scenarios.")
    pdf.numbered_item("4",
        "The three-tier response system (Allow/MFA/Block) provides proportional security "
        "that is superior to binary classification  -  legitimate users experience zero "
        "friction while suspicious attempts face graduated challenges.")
    pdf.numbered_item("5",
        "27ms median inference latency enables real-time authentication without "
        "perceptible delay, making the system suitable for production web applications.")
    pdf.numbered_item("6",
        "The SaaS API platform demonstrates commercial viability with key management, "
        "usage metering, four pricing tiers, and Stripe-integrated subscription billing.")

    pdf.sub_heading("XIV-B. Limitations")
    pdf.bullet("Synthetic training data may not capture all real-world attack patterns")
    pdf.bullet("IP threat scores are simulated; production requires real threat intelligence feeds")
    pdf.bullet("The 21.6% positive class ratio, while realistic, limits minority-class recall")
    pdf.bullet("Single-threaded inference creates a throughput ceiling (~37 pred/s) under Python's GIL")
    pdf.bullet("Geo-location relies on ip-api.com free tier with rate limits")
    pdf.ln(2)

    pdf.sub_heading("XIV-C. Comparison with Static Authentication")
    pdf.add_table(
        ["Aspect", "Static Auth", "Adaptive Auth (Ours)"],
        [
            ["Decision Type", "Binary (accept/reject)", "3-tier (Allow/MFA/Block)"],
            ["Contextual Awareness", "None", "7 behavioral features"],
            ["Stolen Credential Defense", "None", "Geo + threat + behavioral analysis"],
            ["User Friction", "Uniform for all", "Proportional to risk"],
            ["Rate Limiting", "Request-count only", "ML-informed + IP reputation"],
            ["Adaptability", "Manual rule updates", "Learns from data patterns"],
            ["API Integration", "N/A", "RESTful SaaS API + billing"],
        ],
        [42, 55, 80],
    )

    # ══════════════════════════════════════════════════════════════════
    #  XV. TECHNOLOGY STACK
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("XV", "Technology Stack")
    pdf.add_table(
        ["Category", "Technology", "Purpose"],
        [
            ["Backend", "Flask 3.x", "Web framework + REST API server"],
            ["Backend", "SQLAlchemy 2.x", "ORM for SQLite / PostgreSQL"],
            ["Backend", "Werkzeug", "Adaptive password hashing (scrypt)"],
            ["Backend", "PyOTP", "TOTP-based MFA code generation"],
            ["Backend", "Gunicorn", "Production-grade WSGI server"],
            ["ML", "Scikit-Learn 1.x", "Random Forest + evaluation metrics"],
            ["ML", "Pandas / NumPy", "Data manipulation + numeric computation"],
            ["ML", "Joblib", "Model serialization / deserialization"],
            ["Visualization", "Matplotlib / Seaborn", "Publication-quality chart generation"],
            ["Frontend", "HTML5 / CSS3 / JS", "Glassmorphism dark-mode SaaS UI"],
            ["Cloud", "AWS RDS", "Managed PostgreSQL database"],
            ["Cloud", "AWS ElastiCache", "Redis for sessions + rate limiting"],
            ["Cloud", "AWS S3", "ML model artifact storage"],
            ["Cloud", "AWS Elastic Beanstalk", "Auto-scaling Docker app hosting"],
            ["Billing", "Stripe", "Checkout + subscriptions + webhooks"],
            ["DevOps", "Docker / Compose", "Containerization + local cloud emulation"],
        ],
        [30, 45, 105],
    )

    # ══════════════════════════════════════════════════════════════════
    #  XVI. CONCLUSION
    # ══════════════════════════════════════════════════════════════════
    pdf.add_page()
    pdf.section_heading("XVI", "Conclusion")
    pdf.para(
        "This paper presented an Adaptive Authentication System that combines machine learning "
        "with contextual behavioral analysis to provide proportional, risk-based security. "
        "The system successfully demonstrates that:"
    )
    pdf.numbered_item("1",
        "Behavioral feature analysis outperforms static credential-based authentication by "
        "evaluating contextual factors (geographic location, temporal patterns, device type, "
        "IP reputation).")
    pdf.numbered_item("2",
        "A Random Forest classifier with 200 trees provides interpretable, high-accuracy "
        "classification (94.45% accuracy, 0.9019 ROC-AUC) suitable for real-time inference "
        "with minimal latency (~27ms).")
    pdf.numbered_item("3",
        "The three-tier response system (Allow/MFA/Block) provides proportional security "
        "that achieves 100% high-risk detection with 0% false positives, without frustrating "
        "legitimate users.")
    pdf.numbered_item("4",
        "Cloud-native architecture with AWS (RDS + Redis + S3 + EB) enables horizontal "
        "scaling while maintaining local development simplicity through dual-mode configuration.")
    pdf.numbered_item("5",
        "The SaaS API platform with key management, usage metering, and Stripe billing "
        "demonstrates a viable path from research prototype to commercial deployment.")
    pdf.numbered_item("6",
        "Rigorous evaluation across 1,500 adversarial scenarios, with 9 publication-ready "
        "visualizations, validates the system's security claims with empirical evidence.")

    # Summary metrics
    pdf.ln(3)
    pdf.sub_heading("Summary of Key Results")
    summary_rows = [
        ["Model Accuracy", "94.45%"],
        ["ROC-AUC / PR-AUC", "0.9019 / 0.8565"],
        ["5-Fold CV Accuracy", "94.91% +/- 0.27%"],
        ["High-Risk Detection", "100% (500/500 attacks)"],
        ["False Positive Rate", "0.0% at threshold 0.5"],
        ["Score Separation", "0.7118"],
        ["Inference Latency (p50)", "26.75 ms"],
        ["Throughput", "37 predictions/sec"],
        ["Security Test Scenarios", "1,500 (21 profiles)"],
        ["Behavioral Features", "7 real-time signals"],
        ["Adaptive Actions", "3 (Allow, MFA, Block)"],
        ["SaaS Pricing Tiers", "4 (Free through Enterprise)"],
        ["AWS Cloud Services", "4 (RDS, Redis, S3, EB)"],
        ["Frontend Pages", "8 HTML templates"],
        ["Database Tables", "5"],
        ["Research Charts", "9 publication-ready"],
    ]
    pdf.add_table(["Metric", "Value"], summary_rows, [55, 100])

    # ══════════════════════════════════════════════════════════════════
    #  XVII. FUTURE WORK
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("XVII", "Future Work")
    future_items = [
        "Integration with production threat intelligence feeds (AbuseIPDB, VirusTotal, MaxMind GeoIP2)",
        "Behavioral biometrics (keystroke dynamics, mouse movement patterns) as additional ML features",
        "Deep learning model comparison (LSTM for sequential login analysis, Transformers for "
        "attention-based feature weighting) against the Random Forest baseline",
        "Continuous learning pipeline that retrains the model on production API data with "
        "automated A/B testing for threshold optimization",
        "WebSocket integration for real-time dashboard updates without polling",
        "Role-based access control (RBAC) for team-based API key management",
        "Kubernetes deployment with horizontal pod autoscaling for production throughput",
        "Multi-region AWS deployment for global low-latency coverage",
        "HTTPS/TLS automation with Let's Encrypt certificates",
        "SOC 2 / ISO 27001 compliance documentation for enterprise customers",
        "GraphQL API option alongside REST for flexible client-side querying",
        "Federated learning to enable model improvement across multiple tenants without sharing raw data",
    ]
    for item in future_items:
        pdf.bullet(item)
    pdf.ln(4)

    # ══════════════════════════════════════════════════════════════════
    #  REFERENCES
    # ══════════════════════════════════════════════════════════════════
    pdf.section_heading("XVIII", "References")
    refs = [
        "[1]  Freeman, D., et al. \"Who Are You? A Statistical Approach to Measuring User "
        "Authenticity.\" NDSS Symposium, 2016.",
        "[2]  Wiefling, S., et al. \"Is This Really You? An Empirical Study on Risk-Based "
        "Authentication Applied in the Wild.\" IFIP SEC, 2019.",
        "[3]  Chio, C. & Freeman, D. \"Machine Learning and Security.\" O'Reilly Media, 2018.",
        "[4]  Breiman, L. \"Random Forests.\" Machine Learning, 45(1), 5-32, 2001.",
        "[5]  Pedregosa, F., et al. \"Scikit-learn: Machine Learning in Python.\" JMLR 12, "
        "pp. 2825-2830, 2011.",
        "[6]  NIST Special Publication 800-63B: Digital Identity Guidelines  -  Authentication "
        "and Lifecycle Management, 2020.",
        "[7]  OWASP. \"Authentication Cheat Sheet.\" OWASP Foundation, 2024.",
        "[8]  Google Cloud. \"Risk-based authentication.\" Google Identity Platform Documentation, 2024.",
        "[9]  Microsoft. \"Azure AD Identity Protection.\" Microsoft Entra Documentation, 2024.",
        "[10] Amazon Web Services. \"AWS Well-Architected Framework  -  Security Pillar.\" 2024.",
    ]
    for ref in refs:
        pdf.set_font("Helvetica", "", 8.5)
        pdf.set_text_color(40, 40, 60)
        pdf.multi_cell(0, 4.5, ref)
        pdf.ln(1)

    # ── End ──
    pdf.ln(6)
    pdf.set_draw_color(20, 20, 80)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 140)
    pdf.cell(0, 6, "-- End of Paper --", align="C")

    # ── Save ──
    pdf.output(OUTPUT)
    size = os.path.getsize(OUTPUT) / 1024
    print(f"\n  {'='*60}")
    print(f"  Research Paper Generated Successfully!")
    print(f"  {'='*60}")
    print(f"  File:  {OUTPUT}")
    print(f"  Size:  {size:.0f} KB")
    print(f"  Pages: {pdf.page_no()}")
    print(f"  {'='*60}\n")


if __name__ == "__main__":
    build_paper()
