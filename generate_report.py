"""
=============================================================================
 Adaptive Authentication System - PDF Report Generator
 Generates a professional PDF report with diagrams and charts.
=============================================================================
"""

import os
import json
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEAT_IMG = os.path.join(BASE_DIR, "feature_importance.png")
CONF_IMG = os.path.join(BASE_DIR, "confusion_matrix.png")
OUTPUT   = os.path.join(BASE_DIR, "Adaptive_Auth_Report.pdf")

# Evaluation results directory
EVAL_RESULTS = os.path.join(BASE_DIR, "evaluation", "results")

# Research charts from evaluation suite
CHART_ROC       = os.path.join(EVAL_RESULTS, "roc_curve.png")
CHART_PR        = os.path.join(EVAL_RESULTS, "precision_recall_curve.png")
CHART_CM        = os.path.join(EVAL_RESULTS, "confusion_matrix.png")
CHART_FI        = os.path.join(EVAL_RESULTS, "feature_importance.png")
CHART_DIST      = os.path.join(EVAL_RESULTS, "risk_score_distribution.png")
CHART_CV        = os.path.join(EVAL_RESULTS, "cross_validation.png")
CHART_THRESHOLD = os.path.join(EVAL_RESULTS, "threshold_analysis.png")
CHART_SECURITY  = os.path.join(EVAL_RESULTS, "security_detection.png")
CHART_LATENCY   = os.path.join(EVAL_RESULTS, "latency_distribution.png")


def _load_json(filename):
    """Load a JSON file from the evaluation results directory."""
    path = os.path.join(EVAL_RESULTS, filename)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


class ReportPDF(FPDF):

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 140)
        self.cell(0, 6, "Adaptive Authentication System - Research Report", align="R")
        self.ln(4)
        self.set_draw_color(100, 80, 200)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, num, title):
        if self.get_y() > 250:
            self.add_page()
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(60, 40, 160)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(60, 40, 160)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 90, self.get_y())
        self.ln(4)

    def sub_title(self, text):
        if self.get_y() > 260:
            self.add_page()
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(80, 80, 100)
        self.cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 60)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text):
        if self.get_y() > 268:
            self.add_page()
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(50, 50, 60)
        self.multi_cell(0, 5.5, "  - " + text)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(240, 240, 245)
        self.set_text_color(40, 40, 60)
        for line in text.strip().split("\n"):
            if self.get_y() > 272:
                self.add_page()
            self.cell(0, 5, f"  {line}", new_x="LMARGIN", new_y="NEXT", fill=True)
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
        self.set_fill_color(60, 40, 160)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        # Rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(50, 50, 60)
        fill = False
        for row in rows:
            if self.get_y() > 265:
                self.add_page()
                self.set_font("Helvetica", "", 8)
            if fill:
                self.set_fill_color(245, 243, 255)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell_text in enumerate(row):
                txt = str(cell_text)
                # Truncate if too long for cell
                max_chars = int(col_widths[i] / 1.8)
                if len(txt) > max_chars and col_widths[i] < 40:
                    txt = txt[:max_chars-2] + ".."
                al = "C" if col_widths[i] >= 40 else "L"
                self.cell(col_widths[i], 6.5, txt, border=1, fill=True, align=al)
            self.ln()
            fill = not fill
        self.ln(3)

    def add_image_safe(self, path, w=160):
        if os.path.exists(path):
            if self.get_y() > 180:
                self.add_page()
            x = (210 - w) / 2
            self.image(path, x=x, w=w)
            self.ln(5)
        else:
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(180, 50, 50)
            self.cell(0, 6, f"[Image not found: {os.path.basename(path)}]",
                      new_x="LMARGIN", new_y="NEXT")
            self.ln(3)

    def flow_box(self, text, color=(60, 40, 160), w=50, h=12):
        x, y = self.get_x(), self.get_y()
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        fs = 8 if len(text) > 12 else 9
        self.set_font("Helvetica", "B", fs)
        self.rect(x, y, w, h, style="F")
        self.set_xy(x, y + 2)
        self.cell(w, h - 4, text, align="C")
        return x, y

    def arrow_right(self, x, y, length=10):
        mid_y = y + 6
        self.set_draw_color(100, 100, 120)
        self.set_line_width(0.4)
        self.line(x, mid_y, x + length, mid_y)
        self.line(x + length - 2, mid_y - 2, x + length, mid_y)
        self.line(x + length - 2, mid_y + 2, x + length, mid_y)

    def arrow_down(self, x, y, length=8):
        self.set_draw_color(100, 100, 120)
        self.set_line_width(0.4)
        self.line(x, y, x, y + length)
        self.line(x - 2, y + length - 2, x, y + length)
        self.line(x + 2, y + length - 2, x, y + length)


def build_report():
    pdf = ReportPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    # Load evaluation data
    ml_metrics = _load_json("ml_metrics.json")
    sec_metrics = _load_json("security_metrics.json")
    perf_metrics = _load_json("performance_metrics.json")

    # ================================================================
    #  TITLE PAGE
    # ================================================================
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(60, 40, 160)
    pdf.cell(0, 14, "Adaptive Authentication", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 14, "System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 120)
    pdf.cell(0, 8, "AI-Powered Risk-Based Login System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_draw_color(60, 40, 160)
    pdf.set_line_width(0.6)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 100)
    pdf.cell(0, 7, "Research Project Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "April 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(140, 140, 160)
    pdf.cell(0, 6, "Technology: Python | Flask | Scikit-Learn | AWS (RDS, Redis, S3, EB) | Docker | Stripe", align="C",
             new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    #  TABLE OF CONTENTS
    # ================================================================
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(60, 40, 160)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    toc = [
        ("1", "Abstract"),
        ("2", "System Architecture"),
        ("3", "Cloud Infrastructure (AWS)"),
        ("4", "Authentication Flow"),
        ("5", "Machine Learning Model"),
        ("6", "Adaptive Response System"),
        ("7", "Security Features"),
        ("8", "Data Model"),
        ("9", "SaaS API Platform"),
        ("10", "API Key Management & Usage Metering"),
        ("11", "Stripe Billing Integration"),
        ("12", "Technology Stack"),
        ("13", "Frontend & SaaS UI"),
        ("14", "Project Structure"),
        ("15", "API Endpoints"),
        ("16", "Attack Simulation"),
        ("17", "Dashboard Features"),
        ("18", "Deployment"),
        ("19", "Research Evaluation Suite"),
        ("20", "Security Evaluation Results"),
        ("21", "Performance Benchmarks"),
        ("22", "Threshold Sensitivity Analysis"),
        ("23", "Research Visualizations"),
        ("24", "Results & Conclusions"),
        ("25", "Future Work"),
    ]
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 60)
    for num, title in toc:
        pdf.cell(12, 7, num + ".")
        pdf.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")

    # ================================================================
    #  1. ABSTRACT
    # ================================================================
    pdf.add_page()
    pdf.section_title("1", "Abstract")
    pdf.body_text(
        "This project presents a risk-based Adaptive Authentication System that uses a "
        "Machine Learning classifier to dynamically adjust security responses during user login. "
        "Unlike traditional static authentication (accept/reject), the system evaluates 7 real-time "
        "behavioral features and assigns a continuous risk score (0.0 to 1.0), enabling three "
        "adaptive responses: Allow, Multi-Factor Authentication (MFA), or Block."
    )
    pdf.body_text(
        "The system has evolved from a local prototype into a fully cloud-deployed SaaS platform. "
        "It features AWS cloud integration (RDS PostgreSQL, ElastiCache Redis, S3 model storage, "
        "Elastic Beanstalk hosting), a public RESTful API with key-based authentication and "
        "usage metering, Stripe-powered subscription billing with 4 pricing tiers, and a "
        "comprehensive research evaluation suite for generating publication-ready metrics."
    )
    pdf.body_text(
        "The AI model is trained on 10,000 synthetic authentication events across 200 countries "
        "with carefully injected risk patterns, achieving 94.45% test accuracy with a ROC-AUC of "
        "0.9019 and 100% high-risk attack detection rate. The system includes a live threat dashboard, "
        "an IP rate limiter with auto-ban, an attack simulator for adversarial testing, Docker "
        "containerization, and full SaaS infrastructure."
    )
    pdf.body_text(
        "A rigorous research evaluation suite validates the system with 1,500 adversarial test "
        "scenarios across 21 attack profiles, concurrent performance benchmarks under 50-thread "
        "load, and 9 publication-ready visualizations covering ROC curves, precision-recall analysis, "
        "threshold sensitivity, and latency distribution analysis."
    )

    # ================================================================
    #  2. SYSTEM ARCHITECTURE
    # ================================================================
    pdf.section_title("2", "System Architecture")
    pdf.body_text(
        "The system follows a layered architecture with five main components: "
        "Client Layer (Web + API consumers), Flask Application Server, AI Risk Engine, "
        "SaaS API Layer, and Cloud Data Layer."
    )

    y_start = pdf.get_y() + 2

    # --- Client Layer ---
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 150)
    pdf.set_xy(15, y_start - 2)
    pdf.cell(0, 4, "CLIENT LAYER")
    pdf.set_xy(15, y_start + 3)
    pdf.flow_box("Web Browser", (40, 90, 180), 35, 10)
    pdf.set_xy(53, y_start + 3)
    pdf.flow_box("Attack Sim", (40, 90, 180), 35, 10)
    pdf.set_xy(91, y_start + 3)
    pdf.flow_box("API Clients", (40, 90, 180), 35, 10)

    pdf.arrow_down(32, y_start + 13)
    pdf.arrow_down(70, y_start + 13)
    pdf.arrow_down(108, y_start + 13)

    # --- Server Layer ---
    y2 = y_start + 25
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 150)
    pdf.set_xy(15, y2 - 2)
    pdf.cell(0, 4, "FLASK SERVER + SAAS API")
    pdf.set_xy(15, y2 + 3)
    pdf.flow_box("/login", (30, 140, 80), 22, 10)
    pdf.set_xy(39, y2 + 3)
    pdf.flow_box("/signup", (30, 140, 80), 24, 10)
    pdf.set_xy(65, y2 + 3)
    pdf.flow_box("/dashboard", (30, 140, 80), 32, 10)
    pdf.set_xy(99, y2 + 3)
    pdf.flow_box("/api/v1/*", (30, 140, 80), 30, 10)
    pdf.set_xy(131, y2 + 3)
    pdf.flow_box("/billing/*", (30, 140, 80), 30, 10)
    pdf.set_xy(163, y2 + 3)
    pdf.flow_box("/api-docs", (30, 140, 80), 30, 10)

    pdf.arrow_down(29, y2 + 13)

    # --- AI Layer ---
    y3 = y2 + 25
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 150)
    pdf.set_xy(15, y3 - 2)
    pdf.cell(0, 4, "AI RISK ENGINE")
    pdf.set_xy(15, y3 + 3)
    pdf.flow_box("Feature Extract", (100, 60, 200), 42, 10)
    pdf.arrow_right(57, y3 + 3, 8)
    pdf.set_xy(67, y3 + 3)
    pdf.flow_box("Random Forest (200)", (100, 60, 200), 50, 10)
    pdf.arrow_right(117, y3 + 3, 8)
    pdf.set_xy(127, y3 + 3)
    pdf.flow_box("Risk Decision", (100, 60, 200), 40, 10)

    pdf.arrow_down(50, y3 + 13)

    # --- Data Layer ---
    y4 = y3 + 25
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(130, 130, 150)
    pdf.set_xy(15, y4 - 2)
    pdf.cell(0, 4, "CLOUD DATA LAYER")
    pdf.set_xy(15, y4 + 3)
    pdf.flow_box("RDS / SQLite", (200, 160, 40), 35, 10)
    pdf.set_xy(53, y4 + 3)
    pdf.flow_box("Redis / Mem", (200, 160, 40), 35, 10)
    pdf.set_xy(91, y4 + 3)
    pdf.flow_box("S3 / Local", (200, 160, 40), 32, 10)
    pdf.set_xy(126, y4 + 3)
    pdf.flow_box("Model .pkl", (200, 160, 40), 32, 10)

    pdf.set_y(y4 + 20)

    # ================================================================
    #  3. CLOUD INFRASTRUCTURE (AWS)
    # ================================================================
    pdf.add_page()
    pdf.section_title("3", "Cloud Infrastructure (AWS)")
    pdf.body_text(
        "The system is designed for dual-mode operation: local development with SQLite "
        "and in-memory stores, or full cloud deployment on AWS. The cloud architecture "
        "uses four managed AWS services to achieve scalability, persistence, and high availability."
    )

    pdf.sub_title("3.1 AWS Services")
    pdf.add_table(
        ["AWS Service", "Purpose", "Free Tier"],
        [
            ["RDS PostgreSQL", "User accounts & login audit logs", "db.t3.micro (750 hrs/mo)"],
            ["ElastiCache Redis", "Rate limiting, sessions, IP bans", "cache.t3.micro (750 hrs/mo)"],
            ["S3", "ML model & chart artifact storage", "5 GB free"],
            ["Elastic Beanstalk", "App hosting with auto-scaling", "t3.micro (750 hrs/mo)"],
        ],
        [40, 80, 70],
    )

    pdf.sub_title("3.2 Environment-Based Configuration")
    pdf.body_text(
        "The config.py module reads environment variables to determine the runtime mode. "
        "When DATABASE_URL, REDIS_URL, and S3_BUCKET are set, the app operates in cloud mode. "
        "Otherwise it falls back to SQLite, in-memory rate limiting, and local file storage."
    )
    pdf.add_table(
        ["Variable", "Default", "Description"],
        [
            ["DATABASE_URL", "sqlite:///auth.db", "PostgreSQL RDS connection string"],
            ["REDIS_URL", "None (in-memory)", "ElastiCache Redis endpoint"],
            ["S3_BUCKET", "None (local files)", "S3 bucket for ML artifacts"],
            ["AWS_REGION", "us-east-1", "AWS region"],
            ["SECRET_KEY", "dev key", "Flask session encryption key"],
            ["STRIPE_SECRET_KEY", "None", "Stripe billing integration"],
        ],
        [45, 55, 90],
    )

    pdf.sub_title("3.3 Docker Compose (Local Cloud Emulation)")
    pdf.body_text(
        "For local development mimicking the cloud stack, docker-compose.yml spins up "
        "PostgreSQL + Redis + Flask in containers:"
    )
    pdf.code_block(
        "services:\n"
        "  db:       postgres:15 (port 5432)\n"
        "  redis:    redis:7-alpine (port 6379)\n"
        "  web:      Flask app (port 5000)\n"
        "            depends_on: [db, redis]"
    )

    # ================================================================
    #  4. AUTHENTICATION FLOW
    # ================================================================
    pdf.add_page()
    pdf.section_title("4", "Authentication Flow")
    pdf.body_text(
        "Every login request follows a multi-step decision process. The system first validates "
        "credentials, then extracts 7 behavioral features, passes them through the AI model, "
        "and takes an adaptive action based on the predicted risk score."
    )

    pdf.sub_title("Step-by-Step Process")
    steps = [
        ("Step 1", "User submits username + password via /login"),
        ("Step 2", "Server validates against hashed password in DB"),
        ("Step 3", "If invalid: DENY (log attempt, return 401)"),
        ("Step 4", "If valid: Extract 7 behavioral features"),
        ("",       "    - Geo-location (country from IP via ip-api.com)"),
        ("",       "    - Distance from last login (haversine formula)"),
        ("",       "    - IP threat score (0-100 reputation)"),
        ("",       "    - Device type (User-Agent parsing)"),
        ("",       "    - Previous login success (binary flag)"),
        ("",       "    - Hour of day (0-23)"),
        ("",       "    - Region (continental classification)"),
        ("Step 5", "Feed features into Random Forest model"),
        ("Step 6", "Model returns risk probability (0.0 to 1.0)"),
        ("Step 7", "Adaptive action based on risk:"),
        ("",       "    risk < 0.3    =>  ALLOW (grant access)"),
        ("",       "    risk 0.3-0.7  =>  MFA (TOTP challenge)"),
        ("",       "    risk > 0.7    =>  BLOCK (deny + rate-limit)"),
    ]
    for label, desc in steps:
        if label:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(60, 40, 160)
            pdf.cell(20, 5.5, label)
        else:
            pdf.cell(20, 5.5, "")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 60)
        pdf.cell(0, 5.5, desc, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Decision flow diagram
    pdf.sub_title("Decision Diagram")
    y = pdf.get_y() + 2
    pdf.set_xy(15, y)
    pdf.flow_box("Credentials?", (100, 100, 120), 36, 12)
    pdf.arrow_right(51, y, 10)
    pdf.set_xy(63, y)
    pdf.flow_box("Feature Extract", (80, 80, 160), 40, 12)
    pdf.arrow_right(103, y, 10)
    pdf.set_xy(115, y)
    pdf.flow_box("AI Model", (100, 60, 200), 32, 12)

    y2 = y + 20
    pdf.set_xy(15, y2)
    pdf.flow_box("ALLOW", (34, 197, 94), 32, 10)
    pdf.set_xy(51, y2)
    pdf.flow_box("MFA", (251, 191, 36), 32, 10)
    pdf.set_xy(87, y2)
    pdf.flow_box("BLOCK", (239, 68, 68), 32, 10)
    pdf.set_xy(123, y2)
    pdf.flow_box("DENY", (249, 115, 22), 32, 10)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(100, 100, 120)
    pdf.set_xy(15, y2 + 12)
    pdf.cell(32, 5, "risk < 0.3", align="C")
    pdf.cell(32, 5, "0.3 to 0.7", align="C")
    pdf.cell(32, 5, "> 0.7", align="C")
    pdf.cell(32, 5, "Bad creds", align="C")

    pdf.set_y(y2 + 24)

    # ================================================================
    #  5. MACHINE LEARNING MODEL
    # ================================================================
    pdf.add_page()
    pdf.section_title("5", "Machine Learning Model")

    pdf.sub_title("5.1 Training Data Specification")
    pdf.add_table(
        ["Parameter", "Value"],
        [
            ["Total Samples", "10,000"],
            ["Unique Countries", "200"],
            ["Continental Regions", "15"],
            ["Risk Class Ratio", "~21.6% risky / ~78.4% safe"],
            ["Train/Test Split", "80% / 20%"],
            ["Label Noise", "~5% random flip for robustness"],
        ],
        [70, 120],
    )

    pdf.sub_title("5.2 Risk Injection Rules")
    pdf.body_text(
        "The following rules were injected into the training data to teach the model "
        "real-world attack patterns:"
    )
    pdf.add_table(
        ["Rule", "Condition", "Result"],
        [
            ["R1", "threat_score > 80", "RISK"],
            ["R2", "distance > 3000km AND hour in [0,5]", "RISK"],
            ["R3", "distance > 5000km AND no prior success", "RISK"],
            ["R4", "threat > 60 AND device = IoT", "RISK"],
            ["R5", "threat>50 AND dist>2000 AND hour in [1,4]", "RISK"],
        ],
        [20, 110, 60],
    )

    pdf.sub_title("5.3 Model Configuration")
    pdf.add_table(
        ["Hyperparameter", "Value"],
        [
            ["Algorithm", "Random Forest Classifier"],
            ["Number of Trees", "200 (n_estimators)"],
            ["Max Depth", "18"],
            ["Min Samples Split", "5"],
            ["Random State", "42 (reproducible)"],
            ["Test Accuracy", "94.45%"],
            ["ROC-AUC", "0.9019"],
            ["PR-AUC", "0.8565"],
            ["5-Fold CV Accuracy", "94.91% +/- 0.27%"],
            ["Training Time", "0.75 seconds"],
            ["Inference Time", "~27ms median per prediction"],
        ],
        [70, 120],
    )

    pdf.sub_title("5.4 Per-Class Performance Metrics")
    pdf.body_text(
        "Detailed classification performance broken down by class, showing the model's "
        "high precision for both safe and risky login attempts:"
    )
    if ml_metrics:
        pdf.add_table(
            ["Metric", "Safe (Class 0)", "Risk (Class 1)", "Weighted Avg"],
            [
                ["Precision", str(ml_metrics["precision"]["safe"]),
                 str(ml_metrics["precision"]["risk"]), str(ml_metrics["precision"]["weighted"])],
                ["Recall", str(ml_metrics["recall"]["safe"]),
                 str(ml_metrics["recall"]["risk"]), str(ml_metrics["recall"]["weighted"])],
                ["F1-Score", str(ml_metrics["f1_score"]["safe"]),
                 str(ml_metrics["f1_score"]["risk"]), str(ml_metrics["f1_score"]["weighted"])],
            ],
            [35, 45, 45, 55],
        )
    else:
        pdf.add_table(
            ["Metric", "Safe (Class 0)", "Risk (Class 1)", "Weighted Avg"],
            [
                ["Precision", "0.9428", "0.9522", "0.9449"],
                ["Recall", "0.9892", "0.7829", "0.9445"],
                ["F1-Score", "0.9654", "0.8593", "0.9425"],
            ],
            [35, 45, 45, 55],
        )

    pdf.sub_title("5.5 Cross-Validation Results")
    pdf.body_text(
        "Stratified k-fold cross-validation was performed to validate model stability "
        "and guard against overfitting. Results show consistent performance across all folds:"
    )
    if ml_metrics and "cross_validation" in ml_metrics:
        cv = ml_metrics["cross_validation"]
        cv_rows = []
        if "5_fold" in cv:
            cv_rows.append(["5-Fold Accuracy", f"{cv['5_fold']['mean']} +/- {cv['5_fold']['std']}"])
        if "10_fold" in cv:
            cv_rows.append(["10-Fold Accuracy", f"{cv['10_fold']['mean']} +/- {cv['10_fold']['std']}"])
        if "5_fold_f1_weighted" in cv:
            cv_rows.append(["5-Fold F1 (weighted)", f"{cv['5_fold_f1_weighted']['mean']} +/- {cv['5_fold_f1_weighted']['std']}"])
        if "5_fold_roc_auc" in cv:
            cv_rows.append(["5-Fold ROC-AUC", f"{cv['5_fold_roc_auc']['mean']} +/- {cv['5_fold_roc_auc']['std']}"])
        pdf.add_table(["Metric", "Score (mean +/- std)"], cv_rows, [60, 130])
    else:
        pdf.add_table(
            ["Metric", "Score (mean +/- std)"],
            [
                ["5-Fold Accuracy", "0.9491 +/- 0.0027"],
                ["10-Fold Accuracy", "0.9500 +/- 0.0035"],
                ["5-Fold F1 (weighted)", "0.9475 +/- 0.0029"],
                ["5-Fold ROC-AUC", "0.9021 +/- 0.0066"],
            ],
            [60, 130],
        )

    pdf.sub_title("5.6 Feature Importance")
    pdf.body_text(
        "The chart below shows each feature's contribution to the model's decision. "
        "threat_score and distance_from_last_login dominate, aligning with cybersecurity "
        "heuristics where IP reputation and impossible travel are the strongest indicators."
    )
    if ml_metrics and "feature_importance" in ml_metrics:
        fi_rows = []
        for fi in ml_metrics["feature_importance"]:
            pct = f"{fi['importance']*100:.1f}%"
            fi_rows.append([str(fi["rank"]), fi["feature"], str(fi["importance"]), pct])
        pdf.add_table(
            ["Rank", "Feature", "Importance", "Contribution"],
            fi_rows,
            [20, 60, 40, 40],
        )
    pdf.add_image_safe(FEAT_IMG, w=150)

    pdf.sub_title("5.7 Confusion Matrix")
    pdf.body_text(
        "Classification performance on the held-out 20% test set (2,000 samples), "
        "demonstrating high precision and recall for both classes."
    )
    if ml_metrics and "confusion_matrix" in ml_metrics:
        cm = ml_metrics["confusion_matrix"]
        raw = cm["raw"]
        pdf.add_table(
            ["", "Predicted Safe", "Predicted Risk"],
            [
                ["Actual Safe", str(raw[0][0]), str(raw[0][1])],
                ["Actual Risk", str(raw[1][0]), str(raw[1][1])],
            ],
            [45, 50, 50],
        )
    pdf.add_image_safe(CONF_IMG, w=120)

    # ================================================================
    #  6. ADAPTIVE RESPONSE SYSTEM
    # ================================================================
    pdf.add_page()
    pdf.section_title("6", "Adaptive Response System")
    pdf.body_text(
        "The system maps continuous risk scores to discrete security actions. This provides "
        "proportional security: low-risk users get frictionless access, suspicious users "
        "face an extra challenge, and high-risk attempts are immediately denied."
    )
    pdf.add_table(
        ["Risk Range", "Action", "User Experience", "HTTP"],
        [
            ["0.0 - 0.3", "ALLOW", "Instant access to dashboard", "302"],
            ["0.3 - 0.7", "MFA", "TOTP 6-digit code challenge", "302"],
            ["0.7 - 1.0", "BLOCK", "Access denied, red warning", "403"],
            ["N/A", "DENY", "Invalid credentials message", "401"],
            ["N/A", "RATE_LIMITED", "IP auto-banned", "403"],
        ],
        [28, 28, 100, 30],
    )

    pdf.sub_title("Threshold Selection Rationale")
    pdf.bullet("0.3 lower bound minimizes false positives for legitimate users")
    pdf.bullet("0.7 upper bound ensures high-confidence blocking")
    pdf.bullet("The MFA band (0.3-0.7) serves as a verification buffer for ambiguous cases")
    pdf.ln(3)

    # ================================================================
    #  7. SECURITY FEATURES
    # ================================================================
    pdf.section_title("7", "Security Features")
    pdf.sub_title("7.1 Defense-in-Depth Layers")
    pdf.add_table(
        ["Layer", "Component", "Protection"],
        [
            ["Network", "IP Rate Limiter", "Auto-ban after 5 blocks in 10 min"],
            ["Network", "Redis-backed bans", "Persistent across restarts (cloud)"],
            ["Auth", "Password Hashing", "Werkzeug scrypt"],
            ["Auth", "TOTP MFA", "PyOTP time-based codes"],
            ["Auth", "API Key Auth", "X-API-Key header validation"],
            ["Intel", "Geo-Distance", "Haversine impossible travel"],
            ["Intel", "Threat Scoring", "IP reputation analysis"],
            ["Intel", "ML Classifier", "7-feature behavioral analysis"],
            ["Audit", "Full Logging", "Every attempt recorded in RDS/SQLite"],
            ["Audit", "CSV Export", "Downloadable audit trail"],
        ],
        [28, 42, 120],
    )

    pdf.sub_title("7.2 Rate Limiting (Dual-Mode)")
    pdf.add_table(
        ["Parameter", "Local Mode", "Cloud Mode"],
        [
            ["Time Window", "10 min (600s)", "10 min (600s)"],
            ["Threshold", "5 blocks/IP", "5 blocks/IP"],
            ["Action", "Auto IP ban", "Auto IP ban"],
            ["Storage", "In-memory dict", "Redis sorted set + TTL"],
            ["Persistence", "Lost on restart", "Survives restarts"],
            ["Recovery", "/api/clear", "/api/clear + Redis flush"],
        ],
        [40, 75, 75],
    )

    # ================================================================
    #  8. DATA MODEL
    # ================================================================
    pdf.add_page()
    pdf.section_title("8", "Data Model")
    pdf.body_text(
        "The application uses SQLAlchemy ORM with five tables. In local mode this maps to "
        "SQLite; in cloud mode it connects to AWS RDS PostgreSQL. The schema supports both "
        "the core authentication system and the SaaS API platform."
    )

    pdf.sub_title("8.1 User Table")
    pdf.add_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer", "Primary Key"],
            ["username", "String(80)", "Unique, Not Null, Indexed"],
            ["email", "String(200)", "Unique, Nullable, Indexed"],
            ["password_hash", "String(256)", "Werkzeug scrypt hash"],
            ["mfa_secret", "String(32)", "PyOTP base32 secret"],
            ["stripe_customer_id", "String(100)", "Stripe customer reference"],
        ],
        [45, 45, 100],
    )

    pdf.sub_title("8.2 LoginLog Table")
    pdf.add_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer", "Primary Key"],
            ["user_id", "Integer (FK)", "References users.id"],
            ["ip_address", "String(45)", "IPv4/IPv6 address"],
            ["country", "String(100)", "Geo-located country"],
            ["region", "String(100)", "Continental region"],
            ["device_type", "String(30)", "desktop / mobile / IoT"],
            ["risk_score", "Float", "0.0 to 1.0"],
            ["threat_score", "Integer", "0 to 100"],
            ["distance_km", "Float", "km from last login"],
            ["action_taken", "String(20)", "ALLOW / MFA / BLOCK / DENY"],
            ["timestamp", "DateTime", "UTC timestamp"],
        ],
        [38, 42, 110],
    )

    pdf.sub_title("8.3 Plan Table (SaaS Pricing Tiers)")
    pdf.add_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer", "Primary Key"],
            ["name", "String(50)", "Unique slug: free, starter, etc."],
            ["display_name", "String(100)", "Human-readable name"],
            ["monthly_limit", "Integer", "Max API calls per month"],
            ["price_cents", "Integer", "Price in cents ($29 = 2900)"],
            ["stripe_price_id", "String(100)", "Stripe Price object ID"],
            ["features", "Text", "JSON array of feature strings"],
            ["is_active", "Boolean", "Soft-delete flag"],
        ],
        [42, 42, 106],
    )

    pdf.sub_title("8.4 APIKey Table")
    pdf.add_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer", "Primary Key"],
            ["key", "String(100)", "Unique, prefixed aa_live_*"],
            ["name", "String(100)", "User-friendly label"],
            ["user_id", "Integer (FK)", "References users.id"],
            ["plan_id", "Integer (FK)", "References plans.id"],
            ["is_active", "Boolean", "Revocation flag"],
            ["created_at", "DateTime", "Key creation timestamp"],
            ["revoked_at", "DateTime", "Nullable revocation time"],
            ["stripe_subscription_id", "String(100)", "Stripe sub reference"],
        ],
        [50, 42, 98],
    )

    pdf.sub_title("8.5 APIUsage Table (Daily Metering)")
    pdf.add_table(
        ["Column", "Type", "Description"],
        [
            ["id", "Integer", "Primary Key"],
            ["api_key_id", "Integer (FK)", "References api_keys.id"],
            ["date", "Date", "Calendar day"],
            ["call_count", "Integer", "Number of calls that day"],
        ],
        [42, 42, 106],
    )
    pdf.body_text(
        "A unique constraint on (api_key_id, date) ensures one row per key per day. "
        "Monthly usage is computed by summing call_count for the current calendar month."
    )

    # ================================================================
    #  9. SAAS API PLATFORM
    # ================================================================
    pdf.add_page()
    pdf.section_title("9", "SaaS API Platform")
    pdf.body_text(
        "The system exposes a public RESTful API that allows third-party developers to "
        "integrate AI-powered risk assessment into their own applications. Developers sign up, "
        "receive an API key, and call the /api/v1/assess endpoint to get risk scores."
    )

    pdf.sub_title("9.1 Public Risk Assessment Endpoint")
    pdf.body_text("POST /api/v1/assess  (requires X-API-Key header)")
    pdf.code_block(
        "Request Body (JSON):\n"
        '  { "country": "Russia",\n'
        '    "region": "Eastern Europe",\n'
        '    "hour_of_day": 3,\n'
        '    "device_type": "desktop",\n'
        '    "prev_login_success": 0,\n'
        '    "threat_score": 85,\n'
        '    "distance_from_last_login": 8500 }\n'
        "\n"
        "Response (JSON):\n"
        '  { "risk_score": 0.92,\n'
        '    "action": "BLOCK",\n'
        '    "reasons": ["high_threat_score",\n'
        '                "unusual_distance",\n'
        '                "high_risk_country"],\n'
        '    "request_id": "req_a1b2c3d4e5f6...",\n'
        '    "usage": { "calls_today": 42,\n'
        '              "calls_this_month": 1250,\n'
        '              "monthly_limit": 10000 } }'
    )

    pdf.sub_title("9.2 Risk Reason Codes")
    pdf.add_table(
        ["Reason Code", "Trigger Condition"],
        [
            ["high_threat_score", "threat_score > 60"],
            ["unusual_distance", "distance > 3000 km"],
            ["unusual_hour", "hour < 5 or hour > 23"],
            ["unusual_device", "device_type is IoT or smart_tv"],
            ["high_risk_country", "Country in sanctioned list"],
            ["no_previous_success", "prev_login_success == 0"],
        ],
        [55, 135],
    )

    pdf.sub_title("9.3 Pricing Tiers")
    pdf.add_table(
        ["Plan", "Monthly Limit", "Price", "Key Features"],
        [
            ["Free", "500 calls", "$0/mo", "Basic risk scoring"],
            ["Starter", "10,000 calls", "$29/mo", "Full scoring + MFA detection"],
            ["Business", "100,000 calls", "$99/mo", "Analytics + geo-tracking + webhooks"],
            ["Enterprise", "1,000,000 calls", "$299/mo", "Custom ML + SLA + on-premise"],
        ],
        [30, 35, 30, 95],
    )

    # ================================================================
    #  10. API KEY MANAGEMENT & USAGE METERING
    # ================================================================
    pdf.add_page()
    pdf.section_title("10", "API Key Management & Usage Metering")

    pdf.sub_title("10.1 Key Lifecycle")
    pdf.body_text(
        "API keys follow a managed lifecycle. On signup, every user receives a free-tier key "
        "automatically. Users can create up to 5 active keys, each associated with a pricing "
        "plan. Keys can be revoked at any time via the dashboard."
    )
    pdf.add_table(
        ["Action", "Endpoint", "Details"],
        [
            ["Auto-create", "POST /signup", "Free key generated on registration"],
            ["Create", "POST /api/keys/create", "Max 5 active keys per user"],
            ["Revoke", "POST /api/keys/<id>/revoke", "Soft-delete, marks revoked_at"],
            ["View Usage", "GET /api/usage", "JSON: per-key monthly usage stats"],
        ],
        [30, 55, 105],
    )

    pdf.sub_title("10.2 Usage Metering")
    pdf.body_text(
        "Every API call to /api/v1/assess increments a daily counter in the APIUsage table. "
        "Monthly usage is calculated by summing all daily counters for the current calendar "
        "month. When usage exceeds the plan's monthly_limit, the API returns HTTP 429 with "
        "a clear error message including current usage and limit."
    )

    pdf.sub_title("10.3 Rate Limit Response")
    pdf.code_block(
        "HTTP 429 Too Many Requests\n"
        '{ "error": "Monthly API limit exceeded",\n'
        '  "code": "LIMIT_EXCEEDED",\n'
        '  "usage": 10000,\n'
        '  "limit": 10000,\n'
        '  "plan": "Starter" }'
    )

    # ================================================================
    #  11. STRIPE BILLING INTEGRATION
    # ================================================================
    pdf.section_title("11", "Stripe Billing Integration")
    pdf.body_text(
        "The SaaS platform integrates with Stripe for subscription billing. Users can "
        "upgrade their plan via a Stripe Checkout session, manage their subscription "
        "through the Stripe Customer Portal, and the system handles webhook events "
        "for automatic plan changes and cancellations."
    )

    pdf.sub_title("11.1 Billing Routes")
    pdf.add_table(
        ["Route", "Method", "Purpose"],
        [
            ["/billing/checkout", "POST", "Create Stripe Checkout session"],
            ["/billing/webhook", "POST", "Handle Stripe webhook events"],
            ["/billing/portal", "POST", "Redirect to Stripe Customer Portal"],
        ],
        [45, 20, 125],
    )

    pdf.sub_title("11.2 Webhook Event Handling")
    pdf.add_table(
        ["Event Type", "Action"],
        [
            ["checkout.session.completed", "Upgrade user key to purchased plan"],
            ["customer.subscription.deleted", "Downgrade user key to free plan"],
        ],
        [65, 125],
    )
    pdf.body_text(
        "When billing is not configured (no STRIPE_SECRET_KEY), all billing routes "
        "gracefully degrade with a 'not configured' message, allowing the app to run "
        "without Stripe in development mode."
    )

    # ================================================================
    #  12. TECHNOLOGY STACK
    # ================================================================
    pdf.add_page()
    pdf.section_title("12", "Technology Stack")
    pdf.add_table(
        ["Category", "Technology", "Purpose"],
        [
            ["Backend", "Flask", "Web framework + REST API"],
            ["Backend", "SQLAlchemy", "ORM (SQLite / PostgreSQL)"],
            ["Backend", "Werkzeug", "Password hashing (scrypt)"],
            ["Backend", "PyOTP", "TOTP MFA generation"],
            ["Backend", "Gunicorn", "Production WSGI server"],
            ["ML", "Scikit-Learn", "Random Forest training"],
            ["ML", "Pandas", "Data manipulation"],
            ["ML", "Joblib", "Model serialization"],
            ["ML", "Matplotlib", "Chart generation"],
            ["Frontend", "HTML5 / CSS3", "Glassmorphism dark-mode UI"],
            ["Frontend", "JavaScript", "Fetch API / AJAX dashboards"],
            ["Frontend", "SVG", "Animated threat gauge"],
            ["Cloud", "AWS RDS", "PostgreSQL managed database"],
            ["Cloud", "ElastiCache", "Redis for sessions & rate limits"],
            ["Cloud", "S3", "ML model artifact storage"],
            ["Cloud", "Elastic Beanstalk", "Auto-scaling app hosting"],
            ["Billing", "Stripe", "Subscriptions & checkout"],
            ["Infra", "Docker", "Containerization"],
            ["Infra", "Docker Compose", "Local cloud-like dev stack"],
            ["Eval", "Seaborn", "Publication-quality charts"],
            ["Eval", "NumPy", "Numeric computation & benchmarking"],
        ],
        [30, 42, 118],
    )

    # ================================================================
    #  13. FRONTEND & SAAS UI
    # ================================================================
    pdf.section_title("13", "Frontend & SaaS UI")
    pdf.body_text(
        "The system includes 8 HTML templates forming a complete SaaS user experience. "
        "All pages use a glassmorphism dark-mode design language with smooth animations."
    )
    pdf.add_table(
        ["Template", "Route", "Purpose"],
        [
            ["landing.html", "/", "SaaS marketing page with pricing tiers"],
            ["signup.html", "/signup", "User registration with auto API key"],
            ["login.html", "/login", "Authentication + attacker simulator panel"],
            ["mfa.html", "/mfa", "TOTP 6-digit code verification"],
            ["dashboard.html", "/dashboard", "Live threat monitoring dashboard"],
            ["research.html", "/research", "ML model performance charts"],
            ["api_dashboard.html", "/api-dashboard", "API key management & usage stats"],
            ["api_docs.html", "/api-docs", "Interactive API documentation"],
        ],
        [42, 38, 110],
    )

    # ================================================================
    #  14. PROJECT STRUCTURE
    # ================================================================
    pdf.add_page()
    pdf.section_title("14", "Project Structure")
    pdf.code_block(
        "adaptive-auth-system/\n"
        "|-- config.py                Cloud/Local config (env vars)\n"
        "|-- app.py                   Flask app (all routes + SaaS API)\n"
        "|-- models.py                SQLAlchemy ORM (5 tables)\n"
        "|-- risk_engine.py           ML engine (S3 model storage)\n"
        "|-- generate_data.py         Synthetic dataset generator\n"
        "|-- attack_sim.py            CLI attack simulator\n"
        "|-- generate_report.py       PDF report generator\n"
        "|-- test_api.py              API endpoint tests\n"
        "|-- requirements.txt         Python dependencies\n"
        "|-- Dockerfile               Cloud-ready container\n"
        "|-- docker-compose.yml       Local dev stack (PG + Redis)\n"
        "|-- deploy_aws.ps1           AWS deployment script\n"
        "|-- cleanup_aws.ps1          AWS resource cleanup\n"
        "|-- .ebextensions/\n"
        "|   |-- 01_flask.config      EB app + auto-scaling\n"
        "|   |-- 02_packages.config   System packages for RDS\n"
        "|-- templates/\n"
        "|   |-- landing.html         SaaS marketing page\n"
        "|   |-- signup.html          User registration\n"
        "|   |-- login.html           Login + Attacker Simulator\n"
        "|   |-- mfa.html             TOTP verification\n"
        "|   |-- dashboard.html       Live threat dashboard\n"
        "|   |-- research.html        Model performance viewer\n"
        "|   |-- api_dashboard.html   API key management\n"
        "|   |-- api_docs.html        API documentation\n"
        "|-- evaluation/\n"
        "|   |-- research_evaluation.py   ML metrics suite\n"
        "|   |-- security_evaluation.py   Attack sim benchmarks\n"
        "|   |-- performance_benchmark.py API latency tests\n"
        "|   |-- generate_research_charts.py  Publication charts\n"
        "|   |-- results/                 Generated data\n"
        "|-- run_evaluation.py        Master evaluation runner\n"
        "|-- adaptive_auth_model.pkl  Trained RF model\n"
        "|-- label_encoders.pkl       Feature encoders\n"
        "|-- Adaptive_Auth_Report.pdf         Generated report\n"
        "|-- Adaptive_Auth_Research_Paper.pdf  Research paper"
    )

    # ================================================================
    #  15. API ENDPOINTS (COMPLETE)
    # ================================================================
    pdf.add_page()
    pdf.section_title("15", "API Endpoints")
    pdf.sub_title("15.1 Core Authentication Routes")
    pdf.add_table(
        ["Route", "Method", "Purpose", "Response"],
        [
            ["/", "GET", "Landing page", "HTML"],
            ["/login", "GET/POST", "Authentication", "HTML / 302 / 401 / 403"],
            ["/signup", "GET/POST", "User registration", "HTML / 302"],
            ["/mfa", "GET/POST", "MFA challenge", "HTML / 302"],
            ["/dashboard", "GET", "Threat dashboard", "HTML"],
            ["/research", "GET", "Model performance", "HTML"],
            ["/logout", "GET", "End session", "302 => /login"],
        ],
        [30, 25, 55, 80],
    )

    pdf.sub_title("15.2 Internal Data API")
    pdf.add_table(
        ["Route", "Method", "Purpose", "Response"],
        [
            ["/api/stats", "GET", "Dashboard summary data", "JSON"],
            ["/api/export", "GET", "Download audit logs", "CSV file"],
            ["/api/clear", "POST", "Reset all logs & bans", "JSON"],
            ["/api/usage", "GET", "Per-key usage stats", "JSON"],
        ],
        [30, 25, 55, 80],
    )

    pdf.sub_title("15.3 Public SaaS API")
    pdf.add_table(
        ["Route", "Method", "Auth", "Purpose"],
        [
            ["/api/v1/assess", "POST", "X-API-Key", "Risk assessment"],
            ["/api/keys/create", "POST", "Session", "Create new API key"],
            ["/api/keys/<id>/revoke", "POST", "Session", "Revoke an API key"],
        ],
        [45, 20, 35, 90],
    )

    pdf.sub_title("15.4 Billing Routes")
    pdf.add_table(
        ["Route", "Method", "Purpose"],
        [
            ["/billing/checkout", "POST", "Start Stripe checkout"],
            ["/billing/webhook", "POST", "Handle Stripe events"],
            ["/billing/portal", "POST", "Stripe customer portal"],
            ["/pricing", "GET", "Landing page (scroll to pricing)"],
            ["/api-dashboard", "GET", "Developer API dashboard"],
            ["/api-docs", "GET", "API documentation page"],
        ],
        [45, 20, 125],
    )

    # ================================================================
    #  16. ATTACK SIMULATION
    # ================================================================
    pdf.add_page()
    pdf.section_title("16", "Attack Simulation")
    pdf.body_text(
        "The system includes a built-in adversarial testing tool (attack_sim.py) "
        "with three operational modes for different demo scenarios:"
    )
    pdf.add_table(
        ["Mode", "Flag", "Block Rate", "Best For"],
        [
            ["Default", "(none)", "~25-35%", "Balanced detection demo"],
            ["Demo", "--demo", "~50-65%", "Dramatic demo recording"],
            ["Wave", "--wave", "0% => 70%", "Cinematic presentation"],
        ],
        [30, 30, 40, 90],
    )

    pdf.sub_title("Attack Profiles")
    pdf.add_table(
        ["Category", "Countries", "Threat", "Distance"],
        [
            ["HIGH RISK", "RU, KP, CN, IR, SO, LY, SY, VE", "70-100", "4K-14K km"],
            ["MEDIUM", "UA, BR, TR, ID, PH", "35-70", "1.5K-6K km"],
            ["LOW RISK", "US, UK, DE, JP, IN, AU", "0-25", "0-500 km"],
        ],
        [30, 82, 28, 50],
    )

    # ================================================================
    #  17. DASHBOARD FEATURES
    # ================================================================
    pdf.section_title("17", "Dashboard Features")
    pdf.add_table(
        ["Component", "Description"],
        [
            ["8 Summary Cards", "Total, allowed, MFA, blocked, banned, IPs, risk, level"],
            ["SVG Threat Gauge", "Animated semicircle: green to yellow to red"],
            ["Risk Timeline", "Last 20 events as color-coded bars + tooltips"],
            ["Live Attack Feed", "Auto-refresh table with slide-in animations"],
            ["Attack Origins", "Country rankings with mini progress bars"],
            ["Toast Alerts", "Red notifications + audio beep on blocks"],
            ["Export CSV", "Download full audit trail as CSV file"],
            ["Reset Button", "Clear all logs and unban all IPs"],
        ],
        [40, 150],
    )

    # ================================================================
    #  18. DEPLOYMENT
    # ================================================================
    pdf.add_page()
    pdf.section_title("18", "Deployment")

    pdf.sub_title("18.1 Local Development")
    pdf.code_block(
        "pip install -r requirements.txt\n"
        "python generate_data.py\n"
        "python risk_engine.py\n"
        "python app.py\n"
        "# Open http://localhost:5000"
    )

    pdf.sub_title("18.2 Docker Compose (Cloud-like Local)")
    pdf.code_block(
        "docker-compose up --build\n"
        "# Spins up PostgreSQL + Redis + Flask"
    )

    pdf.sub_title("18.3 AWS Elastic Beanstalk Deployment")
    pdf.code_block(
        "# 1. Create S3 bucket for ML models\n"
        "aws s3 mb s3://adaptive-auth-models\n"
        "\n"
        "# 2. Create RDS PostgreSQL\n"
        "aws rds create-db-instance \\\n"
        "  --db-instance-identifier adaptive-auth-db \\\n"
        "  --engine postgres --db-instance-class db.t3.micro\n"
        "\n"
        "# 3. Create ElastiCache Redis\n"
        "aws elasticache create-cache-cluster \\\n"
        "  --cache-cluster-id adaptive-auth-cache \\\n"
        "  --engine redis --cache-node-type cache.t3.micro\n"
        "\n"
        "# 4. Deploy with EB\n"
        "eb init adaptive-auth-system --platform docker\n"
        "eb create adaptive-auth-prod\n"
        "eb setenv DATABASE_URL=... REDIS_URL=... S3_BUCKET=..."
    )
    pdf.body_text(
        "PowerShell scripts deploy_aws.ps1 and cleanup_aws.ps1 automate the full "
        "provisioning and teardown of all AWS resources."
    )

    # ================================================================
    #  19. RESEARCH EVALUATION SUITE
    # ================================================================
    pdf.add_page()
    pdf.section_title("19", "Research Evaluation Suite")
    pdf.body_text(
        "A comprehensive evaluation framework was built in the evaluation/ directory "
        "to generate quantitative metrics suitable for a formal research paper. The suite "
        "is orchestrated by run_evaluation.py which runs all modules sequentially."
    )

    pdf.sub_title("19.1 Evaluation Modules")
    pdf.add_table(
        ["Module", "Purpose", "Output"],
        [
            ["research_evaluation.py", "ML metrics (accuracy, precision, recall, F1, ROC-AUC)", "JSON + console"],
            ["security_evaluation.py", "Attack simulations & detection rate analysis", "JSON + console"],
            ["performance_benchmark.py", "API latency & throughput benchmarks", "JSON + console"],
            ["generate_research_charts.py", "Publication-ready visualizations", "PNG charts"],
        ],
        [55, 75, 60],
    )

    pdf.sub_title("19.2 Generated Research Artifacts")
    pdf.add_table(
        ["Artifact", "Description"],
        [
            ["Adaptive_Auth_Report.pdf", "Comprehensive technical report (this document)"],
            ["Adaptive_Auth_Research_Paper.pdf", "Formal academic research paper"],
            ["confusion_matrix.png", "Classification confusion matrix visualization"],
            ["feature_importance.png", "Feature contribution bar chart"],
            ["roc_curve.png", "ROC curve with AUC annotation"],
            ["precision_recall_curve.png", "Precision-recall curve with baseline"],
            ["risk_score_distribution.png", "Violin + histogram of score distributions"],
            ["cross_validation.png", "k-Fold cross-validation boxplot"],
            ["threshold_analysis.png", "Threshold sensitivity analysis (4 metrics)"],
            ["security_detection.png", "Detection rate by attack category"],
            ["latency_distribution.png", "Inference latency histogram"],
            ["evaluation/results/", "Raw JSON metrics and benchmark data"],
        ],
        [65, 125],
    )

    pdf.sub_title("19.3 Running the Full Evaluation")
    pdf.code_block(
        "# Run all evaluation modules\n"
        "python run_evaluation.py\n"
        "\n"
        "# Or run individual modules\n"
        "python evaluation/research_evaluation.py\n"
        "python evaluation/security_evaluation.py\n"
        "python evaluation/performance_benchmark.py\n"
        "python evaluation/generate_research_charts.py\n"
        "\n"
        "# Regenerate PDF reports\n"
        "python generate_report.py"
    )

    # ================================================================
    #  20. SECURITY EVALUATION RESULTS
    # ================================================================
    pdf.add_page()
    pdf.section_title("20", "Security Evaluation Results")
    pdf.body_text(
        "A rigorous security evaluation was conducted using 1,500 synthetic attack scenarios "
        "across 21 distinct attack profiles. The evaluation measures the model's ability to "
        "distinguish real attacks from legitimate logins using the predict_risk() function "
        "in a fully offline, reproducible manner."
    )

    if sec_metrics:
        pdf.sub_title("20.1 Test Scenario Composition")
        pdf.add_table(
            ["Category", "Count", "Description"],
            [
                ["High-Risk Attacks", "500", "10 profiles: RU, KP, CN, IR, SO, UA, SY, VE, LY, CU"],
                ["Medium-Risk Attacks", "250", "5 profiles: NG, BR, CO, SA, TH"],
                ["Legitimate Logins", "750", "6 profiles: US, DE, JP, IN, AU, CA"],
                ["Total Scenarios", str(sec_metrics["total_scenarios"]), "Balanced adversarial test set"],
            ],
            [45, 30, 115],
        )

        pdf.sub_title("20.2 Detection Metrics at Multiple Thresholds")
        pdf.body_text(
            "The model was evaluated at three decision thresholds (conservative=0.3, "
            "balanced=0.5, aggressive=0.7) to demonstrate the precision-recall tradeoff:"
        )
        tm = sec_metrics.get("threshold_metrics", {})
        if tm:
            rows = []
            for name, m in tm.items():
                rows.append([
                    f"{name} ({m['threshold']})",
                    str(m["true_positive_rate"]),
                    str(m["false_positive_rate"]),
                    str(m["false_negative_rate"]),
                    str(m["precision"]),
                    str(m["f1_score"]),
                ])
            pdf.add_table(
                ["Threshold", "TPR", "FPR", "FNR", "Precision", "F1"],
                rows,
                [40, 25, 25, 25, 30, 25],
            )

        pdf.sub_title("20.3 Detection Rate by Attack Category")
        cd = sec_metrics.get("category_detection", {})
        if cd:
            rows = []
            for cat, data in cd.items():
                rate_pct = f"{data['detection_rate']*100:.1f}%"
                rows.append([
                    cat.upper(),
                    str(data["total_scenarios"]),
                    str(data["detected"]),
                    rate_pct,
                    str(data["avg_risk_score"]),
                ])
            pdf.add_table(
                ["Category", "Scenarios", "Detected", "Rate", "Avg Score"],
                rows,
                [30, 30, 30, 30, 35],
            )

        pdf.sub_title("20.4 Per-Profile Attack Detection")
        pdf.body_text(
            "Detection rates for individual attack profiles demonstrate the model's "
            "ability to identify specific threat patterns. All 10 high-risk profiles "
            "achieve 100% detection:"
        )
        pd_data = sec_metrics.get("profile_detection", {})
        if pd_data:
            # Sort by detection rate descending
            sorted_profiles = sorted(pd_data.items(), key=lambda x: x[1]["detection_rate"], reverse=True)
            rows = []
            for label, data in sorted_profiles:
                rate_pct = f"{data['detection_rate']*100:.1f}%"
                rows.append([label, str(data["total"]), str(data["detected"]),
                             rate_pct, str(data["avg_risk_score"])])
            pdf.add_table(
                ["Attack Profile", "Total", "Detected", "Rate", "Avg Score"],
                rows,
                [40, 22, 28, 28, 35],
            )

        pdf.sub_title("20.5 Risk Score Distribution Analysis")
        sd = sec_metrics.get("score_distribution", {})
        if sd:
            pdf.add_table(
                ["Statistic", "Attacks", "Legitimate"],
                [
                    ["Mean", str(sd["attacks"]["mean"]), str(sd["legitimate"]["mean"])],
                    ["Median", str(sd["attacks"]["median"]), str(sd["legitimate"]["median"])],
                    ["Std Dev", str(sd["attacks"]["std"]), str(sd["legitimate"]["std"])],
                    ["Min", str(sd["attacks"]["min"]), str(sd["legitimate"]["min"])],
                    ["Max", str(sd["attacks"]["max"]), str(sd["legitimate"]["max"])],
                ],
                [40, 55, 55],
            )
            pdf.body_text(
                f"Score separation (attack mean - legitimate mean): {sd['separation']}. "
                "A high separation value indicates strong discriminative power between "
                "malicious and legitimate login attempts."
            )
    else:
        pdf.body_text(
            "Security evaluation data not available. Run: python evaluation/security_evaluation.py"
        )

    # ================================================================
    #  21. PERFORMANCE BENCHMARKS
    # ================================================================
    pdf.add_page()
    pdf.section_title("21", "Performance Benchmarks")
    pdf.body_text(
        "Comprehensive performance benchmarks were conducted to measure model inference "
        "latency and throughput under various load conditions. The offline benchmark tests "
        "the predict_risk() function directly, eliminating network overhead."
    )

    if perf_metrics:
        pdf.sub_title("21.1 Single-Thread Inference Latency")
        st = perf_metrics.get("single_thread", {})
        if st:
            pdf.add_table(
                ["Metric", "Value"],
                [
                    ["Iterations", str(st.get("iterations", "N/A"))],
                    ["Mean Latency", f"{st.get('mean_ms', 'N/A')} ms"],
                    ["Median Latency (p50)", f"{st.get('median_ms', 'N/A')} ms"],
                    ["p95 Latency", f"{st.get('p95_ms', 'N/A')} ms"],
                    ["p99 Latency", f"{st.get('p99_ms', 'N/A')} ms"],
                    ["Min Latency", f"{st.get('min_ms', 'N/A')} ms"],
                    ["Max Latency", f"{st.get('max_ms', 'N/A')} ms"],
                    ["Std Dev", f"{st.get('std_ms', 'N/A')} ms"],
                    ["Throughput", f"{perf_metrics.get('throughput_per_sec', 'N/A')} predictions/sec"],
                ],
                [60, 130],
            )

        pdf.sub_title("21.2 Latency Percentile Distribution")
        dist = perf_metrics.get("latency_distribution", {}).get("percentiles", {})
        if dist:
            rows = [[p, f"{val} ms"] for p, val in dist.items()]
            pdf.add_table(["Percentile", "Latency"], rows, [50, 100])

        pdf.sub_title("21.3 Concurrent Load Test Results")
        pdf.body_text(
            "Multi-threaded benchmark simulating concurrent API requests to evaluate "
            "model performance under load. Each thread performs 50 sequential predictions:"
        )
        concurrent = perf_metrics.get("concurrent", {})
        if concurrent:
            rows = []
            for key, data in concurrent.items():
                rows.append([
                    str(data["threads"]),
                    str(data["total_requests"]),
                    f"{data['total_time_seconds']}s",
                    f"{data['throughput_per_sec']}/s",
                    f"{data['median_ms']} ms",
                    f"{data['p99_ms']} ms",
                ])
            pdf.add_table(
                ["Threads", "Requests", "Total Time", "Throughput", "Median (ms)", "p99 (ms)"],
                rows,
                [25, 30, 30, 30, 35, 35],
            )
        pdf.body_text(
            "Results show the model maintains consistent throughput (40-46 pred/s) even "
            "under heavy concurrent load, with latency scaling linearly with thread count "
            "due to Python's GIL for CPU-bound inference tasks."
        )
    else:
        pdf.body_text(
            "Performance benchmark data not available. Run: python evaluation/performance_benchmark.py"
        )

    # ================================================================
    #  22. THRESHOLD SENSITIVITY ANALYSIS
    # ================================================================
    pdf.add_page()
    pdf.section_title("22", "Threshold Sensitivity Analysis")
    pdf.body_text(
        "The decision threshold determines how the continuous risk score (0.0-1.0) is "
        "converted into a binary classification. This analysis evaluates how accuracy, "
        "precision, recall, and F1-score vary across different threshold values, helping "
        "select the optimal operating point for the system."
    )

    if ml_metrics and "threshold_analysis" in ml_metrics:
        pdf.sub_title("22.1 Metrics at Standard Thresholds")
        rows = []
        for t in ml_metrics["threshold_analysis"]:
            rows.append([
                str(t["threshold"]),
                str(t["accuracy"]),
                str(t["precision"]),
                str(t["recall"]),
                str(t["f1"]),
            ])
        pdf.add_table(
            ["Threshold", "Accuracy", "Precision", "Recall", "F1-Score"],
            rows,
            [30, 35, 35, 35, 35],
        )

        pdf.sub_title("22.2 Optimal Threshold Analysis")
        # Find the best F1
        best_t = max(ml_metrics["threshold_analysis"], key=lambda x: x["f1"])
        pdf.body_text(
            f"The optimal F1-score of {best_t['f1']} is achieved at threshold {best_t['threshold']}, "
            f"with precision={best_t['precision']} and recall={best_t['recall']}. "
            "The system uses a three-tier threshold (0.3/0.7) rather than binary classification, "
            "which provides the additional benefit of proportional security responses."
        )

        pdf.sub_title("22.3 Threshold Trade-off Observation")
        pdf.bullet("Lowering the threshold (e.g., 0.2) increases recall but reduces precision")
        pdf.bullet("Raising the threshold (e.g., 0.8) increases precision but misses more attacks")
        pdf.bullet("The system's 0.3 threshold for MFA captures 80.1% of attacks with 93.0% precision")
        pdf.bullet("The system's 0.7 threshold for BLOCK ensures zero false positives (100% precision)")
        pdf.ln(3)

    if ml_metrics and "inference_speed" in ml_metrics:
        pdf.sub_title("22.4 Inference Speed Benchmark")
        inf = ml_metrics["inference_speed"]
        pdf.add_table(
            ["Metric", "Value"],
            [
                ["Benchmark Samples", str(inf["samples"])],
                ["Median Latency", f"{inf['median_ms']:.4f} ms"],
                ["Mean Latency", f"{inf['mean_ms']:.4f} ms"],
                ["p95 Latency", f"{inf['p95_ms']:.4f} ms"],
                ["p99 Latency", f"{inf['p99_ms']:.4f} ms"],
            ],
            [60, 130],
        )

    # ================================================================
    #  23. RESEARCH VISUALIZATIONS
    # ================================================================
    pdf.add_page()
    pdf.section_title("23", "Research Visualizations")
    pdf.body_text(
        "The following publication-ready charts were generated by the evaluation suite "
        "(300 DPI, dark theme, tight layout). These visualizations provide comprehensive "
        "insight into model performance, security capabilities, and system behavior."
    )

    # 23.1 ROC Curve
    pdf.sub_title("23.1 ROC Curve (Receiver Operating Characteristic)")
    pdf.body_text(
        "The ROC curve plots True Positive Rate against False Positive Rate across all "
        "classification thresholds. The area under the curve (AUC = 0.9019) indicates "
        "strong discriminative ability, well above the random baseline of 0.5."
    )
    pdf.add_image_safe(CHART_ROC, w=150)

    # 23.2 Precision-Recall Curve
    pdf.add_page()
    pdf.sub_title("23.2 Precision-Recall Curve")
    pdf.body_text(
        "The PR curve is particularly informative for imbalanced datasets (21.6% positive rate). "
        "PR-AUC = 0.8565 demonstrates that the model maintains high precision even at elevated "
        "recall levels, critical for a security application where false negatives (missed attacks) "
        "are dangerous."
    )
    pdf.add_image_safe(CHART_PR, w=150)

    # 23.3 Confusion Matrix
    pdf.add_page()
    pdf.sub_title("23.3 Confusion Matrix (Normalized & Raw)")
    pdf.body_text(
        "Side-by-side confusion matrices showing both normalized rates and raw counts. "
        "The model correctly identifies 98.9% of safe logins and 78.3% of risky logins, "
        "with only 17 false positives and 94 false negatives out of 2,000 test samples."
    )
    pdf.add_image_safe(CHART_CM, w=170)

    # 23.4 Feature Importance
    pdf.add_page()
    pdf.sub_title("23.4 Feature Importance Analysis")
    pdf.body_text(
        "Horizontal bar chart of Random Forest feature importances with numeric annotations. "
        "Threat Score (0.510) and Distance (0.225) dominate, collectively contributing 73.5% "
        "of the model's decision-making capability."
    )
    pdf.add_image_safe(CHART_FI, w=150)

    # 23.5 Risk Score Distribution
    pdf.add_page()
    pdf.sub_title("23.5 Risk Score Distribution")
    pdf.body_text(
        "Violin plot and histogram overlay showing the distribution of predicted risk scores "
        "for safe vs. risky login attempts. Clear separation between the two distributions "
        "validates the model's discriminative power. The separation score of 0.7118 indicates "
        "minimal overlap between attack and legitimate score distributions."
    )
    pdf.add_image_safe(CHART_DIST, w=170)

    # 23.6 Cross-Validation
    pdf.add_page()
    pdf.sub_title("23.6 Cross-Validation Results")
    pdf.body_text(
        "Stratified k-fold cross-validation boxplot (k=3,5,7,10) with mean accuracy annotations. "
        "The consistently tight distributions (std < 0.005) across all fold counts confirm "
        "robust model generalization and no overfitting to the training data."
    )
    pdf.add_image_safe(CHART_CV, w=150)

    # 23.7 Threshold Analysis
    pdf.add_page()
    pdf.sub_title("23.7 Threshold Sensitivity Analysis")
    pdf.body_text(
        "Four-metric sensitivity plot showing how accuracy, precision, recall, and F1-score "
        "vary across classification thresholds from 0.05 to 0.95. The optimal F1 point is "
        "marked, and the plot illustrates the precision-recall tradeoff central to "
        "configuring the system's ALLOW/MFA/BLOCK thresholds."
    )
    pdf.add_image_safe(CHART_THRESHOLD, w=150)

    # 23.8 Security Detection
    pdf.add_page()
    pdf.sub_title("23.8 Security Detection by Category")
    pdf.body_text(
        "Bar charts showing detection rate and mean risk score by attack category "
        "(high/medium/low risk). High-risk attacks achieve 100% detection with avg "
        "score 0.936, medium-risk at 57.6% with avg score 0.477, and legitimate logins "
        "show 0% false positive rate with avg score 0.071."
    )
    pdf.add_image_safe(CHART_SECURITY, w=170)

    # 23.9 Latency Distribution
    pdf.add_page()
    pdf.sub_title("23.9 Inference Latency Distribution")
    pdf.body_text(
        "Histogram of model inference latency across 1,000 predictions with p50/p95/p99 "
        "percentile markers. The tight distribution around 27ms median demonstrates "
        "consistent real-time inference performance suitable for production deployment."
    )
    pdf.add_image_safe(CHART_LATENCY, w=150)

    # ================================================================
    #  24. RESULTS & CONCLUSIONS
    # ================================================================
    pdf.add_page()
    pdf.section_title("24", "Results & Conclusions")

    pdf.sub_title("Key Metrics")
    key_metrics_rows = [
        ["Model Test Accuracy", "94.45%"],
        ["Precision (weighted)", "94.49%"],
        ["Recall (weighted)", "94.45%"],
        ["F1-Score (weighted)", "94.25%"],
        ["ROC-AUC", "0.9019"],
        ["PR-AUC", "0.8565"],
        ["5-Fold CV Accuracy", "94.91% +/- 0.27%"],
        ["10-Fold CV Accuracy", "95.00% +/- 0.35%"],
        ["5-Fold CV F1 (weighted)", "94.75% +/- 0.29%"],
        ["5-Fold CV ROC-AUC", "0.9021 +/- 0.0066"],
        ["High-Risk Detection Rate", "100% (500/500)"],
        ["False Positive Rate", "0.0% (threshold=0.5)"],
        ["Score Separation", "0.7118 (attack vs legitimate)"],
    ]
    # Add performance data if available
    if perf_metrics:
        st = perf_metrics.get("single_thread", {})
        key_metrics_rows.extend([
            ["Inference Latency (median)", f"{st.get('median_ms', '~27')} ms"],
            ["Inference Latency (p99)", f"{st.get('p99_ms', '~32')} ms"],
            ["Throughput (single-thread)", f"{perf_metrics.get('throughput_per_sec', 37)} predictions/sec"],
        ])
    else:
        key_metrics_rows.extend([
            ["Inference Latency", "~27ms median per prediction"],
            ["Throughput", "37 predictions/sec (single-thread)"],
        ])

    # Add concurrent performance
    if perf_metrics and "concurrent" in perf_metrics:
        c50 = perf_metrics["concurrent"].get("50_threads", {})
        if c50:
            key_metrics_rows.append(
                ["Peak Concurrent Throughput", f"{c50.get('throughput_per_sec', 'N/A')}/s (50 threads)"]
            )

    key_metrics_rows.extend([
        ["Features Used", "7 behavioral signals"],
        ["Adaptive Actions", "3 (Allow, MFA, Block)"],
        ["Rate Limit Threshold", "5 blocks => auto-ban"],
        ["API Pricing Tiers", "4 (Free, Starter, Business, Enterprise)"],
        ["Frontend Pages", "8 HTML templates"],
        ["Database Tables", "5 (User, LoginLog, Plan, APIKey, APIUsage)"],
        ["AWS Services", "4 (RDS, ElastiCache, S3, EB)"],
        ["Research Charts", "9 publication-ready visualizations"],
        ["Evaluation Modules", "4 (ML, Security, Performance, Charts)"],
        ["Attack Profiles Tested", "21 (10 high, 5 medium, 6 low)"],
    ])

    # Add security test data if available
    if sec_metrics:
        key_metrics_rows.append(
            ["Security Test Scenarios", str(sec_metrics["total_scenarios"])]
        )

    pdf.add_table(
        ["Metric", "Result"],
        key_metrics_rows,
        [60, 130],
    )

    pdf.sub_title("Conclusions")
    conclusions = [
        ("1.", "Behavioral feature analysis outperforms static credential-based "
               "authentication by evaluating context (where, when, what device)."),
        ("2.", "Random Forest provides interpretable, high-accuracy classification "
               "suitable for real-time inference with minimal latency (~27ms median)."),
        ("3.", "Multi-tier response (Allow/MFA/Block) provides proportional security "
               "without frustrating legitimate users, achieving 0% false positive rate."),
        ("4.", "Cloud-native architecture (RDS + Redis + S3) enables horizontal scaling "
               "while maintaining local development simplicity via dual-mode config."),
        ("5.", "The SaaS API platform with key management, usage metering, and Stripe "
               "billing demonstrates a viable commercial deployment model."),
        ("6.", "Rate limiting with Redis-backed persistence adds a temporal defense layer "
               "that survives application restarts in production."),
        ("7.", "The research evaluation suite provides reproducible, publication-ready "
               "metrics that validate the system's security claims empirically."),
        ("8.", "Security evaluation across 1,500 scenarios and 21 attack profiles confirms "
               "100% detection of high-risk attacks with zero false positives."),
        ("9.", "Threshold sensitivity analysis validates the three-tier (0.3/0.5/0.7) "
               "approach as optimal for balancing security and user experience."),
        ("10.", "Performance benchmarks demonstrate production-ready latency with consistent "
                "throughput under concurrent load (40+ predictions/sec)."),
    ]
    for num, text in conclusions:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(60, 40, 160)
        pdf.cell(10, 5.5, num)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(50, 50, 60)
        pdf.multi_cell(0, 5.5, text)
        pdf.ln(1)

    # ================================================================
    #  25. FUTURE WORK
    # ================================================================
    pdf.add_page()
    pdf.section_title("25", "Future Work")
    future = [
        "Integration with real IP threat intelligence feeds (AbuseIPDB, VirusTotal)",
        "MaxMind GeoIP2 database for production-grade geo-location",
        "Behavioral biometrics (typing speed, mouse patterns) as additional ML features",
        "Model retraining pipeline with continuous learning from production API data",
        "WebSocket integration for truly real-time dashboard updates",
        "Role-based access control (RBAC) for team API key management",
        "HTTPS/TLS with Let's Encrypt certificate automation",
        "Kubernetes deployment with horizontal pod autoscaling",
        "Webhook notifications to customers on high-risk detections",
        "GraphQL API option alongside REST for flexible querying",
        "Multi-region AWS deployment for global low-latency coverage",
        "Deep learning model comparison (LSTM, Transformer) for sequential login analysis",
        "A/B testing framework for threshold optimization in production",
        "SOC 2 / ISO 27001 compliance documentation for enterprise customers",
    ]
    for item in future:
        pdf.bullet(item)
    pdf.ln(6)

    # End
    pdf.set_draw_color(60, 40, 160)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(120, 120, 140)
    pdf.cell(0, 6, "-- End of Report --", align="C")

    # SAVE
    pdf.output(OUTPUT)
    print(f"\n  {'='*55}")
    print(f"  PDF Report Generated Successfully!")
    print(f"  {'='*55}")
    print(f"  File: {OUTPUT}")
    size = os.path.getsize(OUTPUT)
    print(f"  Size: {size / 1024:.0f} KB")
    print(f"  Pages: {pdf.page_no()}")
    print(f"  {'='*55}\n")


if __name__ == "__main__":
    build_report()
