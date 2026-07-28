"""
Compile IEEE Paper to PDF using fpdf2
Generates a professional IEEE-style two-column research paper PDF
from the content in ieee_paper.tex without requiring LaTeX installation.
"""

import os
import json
from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation", "results")
OUTPUT = os.path.join(BASE_DIR, "IEEE_Adaptive_Auth_Paper.pdf")


def load_json(name):
    path = os.path.join(EVAL_DIR, name)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None


class IEEEPaper(FPDF):

    def header(self):
        if self.page_no() <= 1:
            return
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 4, "IEEE Conference Paper -- Adaptive Authentication Using Machine Learning", align="C")
        self.ln(2)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 5, f"{self.page_no()}", align="C")

    def title_page(self):
        self.add_page()
        self.ln(25)
        # Title
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 9, "Adaptive Authentication Using Machine Learning:\nA Risk-Based Multi-Tier Security System\nwith SaaS API Platform", align="C")
        self.ln(8)
        # Author
        self.set_font("Helvetica", "", 12)
        self.cell(0, 6, "Satwik Basu (100751), Dr. Sreevani, Dr. Praveen Lalwani, Dr. Pushpinder Singh Patheja", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 10)
        self.cell(0, 5, "School of Computing Science Engineering and Artificial Intelligence", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, "VIT Bhopal University, Madhya Pradesh, India", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, "satwikbasu03@gmail.com", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        # Abstract box
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.3)
        x = 15
        self.set_x(x)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(180, 6, "Abstract", align="L", new_x="LMARGIN", new_y="NEXT")
        self.set_x(x)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(20, 20, 20)
        abstract = (
            "Traditional authentication relies on static, binary accept/reject decisions, leaving systems "
            "vulnerable to credential theft. This paper presents an Adaptive Authentication System that evaluates "
            "contextual features to dynamically assess risk. We deploy a Random Forest classifier achieving "
            "94.45% accuracy (ROC-AUC 0.9019) with a 27ms median inference latency on a 10,000-event benchmark. "
            "Instead of a binary decision, the model drives a three-tier proportional-response framework: ALLOW, "
            "MFA (SMS OTP), and BLOCK. Security evaluation across 1,500 adversarial scenarios demonstrates 100% "
            "detection of high-risk attacks with zero false positives. Finally, we bridge the gap between "
            "academic research and commercial viability by deploying the system as a production-ready SaaS API "
            "platform on AWS with Stripe billing integration. All code and datasets are publicly available."
        )
        self.multi_cell(180, 4.5, abstract)
        self.ln(4)
        self.set_x(x)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(0, 0, 0)
        kw = "Keywords: Adaptive Authentication, Risk-Based Authentication, Machine Learning, Random Forest, Multi-Factor Authentication, SaaS API, Cloud Security"
        self.multi_cell(180, 4.5, kw)

    def section(self, num, title):
        if self.get_y() > 260:
            self.add_page()
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 0, 0)
        label = f"{num}. {title.upper()}" if num else title.upper()
        self.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def subsection(self, title):
        if self.get_y() > 265:
            self.add_page()
        self.ln(1)
        self.set_font("Helvetica", "BI", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def para(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(20, 20, 20)
        self.multi_cell(0, 4.5, text)
        self.ln(1.5)

    def bullet(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(20, 20, 20)
        x = self.get_x()
        self.cell(6, 4.5, "-")
        self.multi_cell(0, 4.5, text)
        self.ln(0.5)

    def add_table(self, headers, rows, title=None, col_widths=None):
        if self.get_y() > 230:
            self.add_page()
        if title:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(40, 40, 40)
            self.cell(0, 5, title, align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

        n = len(headers)
        if not col_widths:
            col_widths = [190 / n] * n

        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(30, 30, 60)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 5, str(h), border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 8)
        self.set_text_color(20, 20, 20)
        for ri, row in enumerate(rows):
            if ri % 2 == 0:
                self.set_fill_color(245, 245, 250)
            else:
                self.set_fill_color(255, 255, 255)
            bold_row = any("**" in str(c) for c in row)
            if bold_row:
                self.set_font("Helvetica", "B", 8)
            for i, c in enumerate(row):
                val = str(c).replace("**", "")
                self.cell(col_widths[i], 5, val, border=1, fill=True, align="C")
            self.ln()
            if bold_row:
                self.set_font("Helvetica", "", 8)
        self.ln(2)

    def add_chart(self, path, caption, w=160):
        if not os.path.exists(path):
            return
        if self.get_y() > 200:
            self.add_page()
        x = (210 - w) / 2
        self.image(path, x=x, w=w)
        self.ln(2)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 4, caption, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)


def build():
    pdf = IEEEPaper()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()

    ml = load_json("ml_metrics.json")
    sec = load_json("security_metrics.json")
    comp = load_json("model_comparison.json")

    # === TITLE PAGE ===
    pdf.title_page()

    # === I. INTRODUCTION ===
    pdf.add_page()
    pdf.section("I", "Introduction")
    pdf.para(
        "Authentication is the cornerstone of digital security, yet the predominant paradigm remains "
        "fundamentally binary: a user either provides correct credentials and gains full access, or fails "
        "and is denied entirely. This static approach provides no defense against credential theft via "
        "phishing, data breaches, or brute-force attacks -- scenarios where an attacker possesses valid "
        "credentials but exhibits anomalous behavioral patterns [1]."
    )
    pdf.para(
        "Risk-Based Authentication (RBA) addresses this limitation by incorporating contextual signals "
        "-- such as geographic location, device fingerprint, and temporal patterns -- to dynamically "
        "assess the risk of each login attempt [2]. Major technology companies (Google, Microsoft, "
        "Facebook) deploy proprietary RBA systems, but their implementations remain opaque, hindering "
        "academic analysis and reproducibility [3]."
    )
    pdf.para("The contributions of this paper are as follows:")
    pdf.bullet("A three-tier proportional response framework (ALLOW/MFA/BLOCK) with configurable dual thresholds, advancing beyond binary risk classification prevalent in the literature.")
    pdf.bullet("A Random Forest-based risk scoring engine that analyzes seven behavioral features per login attempt, achieving 94.45% accuracy with 27ms median inference latency.")
    pdf.bullet("A comprehensive model comparison against four baseline classifiers (XGBoost, Logistic Regression, SVM, KNN) empirically justifying model selection.")
    pdf.bullet("A rigorous security evaluation across 1,500 adversarial scenarios and 21 attack profiles, demonstrating 100% high-risk detection with zero false positives.")
    pdf.bullet("An end-to-end SaaS API platform with cloud deployment (AWS), subscription billing (Stripe), and API key management.")
    pdf.bullet("Full open-source availability of code, datasets, evaluation suite, and publication-ready charts for reproducibility.")

    # === II. RELATED WORK ===
    pdf.section("II", "Related Work")
    pdf.subsection("A. Risk-Based Authentication")
    pdf.para(
        "Freeman et al. [1] proposed a statistical framework for risk-based authentication using IP address "
        "and device features, establishing the theoretical foundation for context-aware login security. "
        "Wiefling et al. [2] conducted the first large-scale empirical study of RBA deployment at major web "
        "services. Their subsequent work [3, 4] produced open-source RBA implementations and evaluation "
        "benchmarks, hosted at riskbasedauthentication.org."
    )
    pdf.subsection("B. Machine Learning in Authentication")
    pdf.para(
        "ML-based approaches to authentication security include anomaly detection using Isolation Forests [5], "
        "behavioral biometrics via LSTM networks [6], and ensemble methods for intrusion detection [7]. "
        "Random Forest classifiers have demonstrated strong performance in network security applications due "
        "to their robustness to mixed feature types and inherent interpretability [8]. Gradient boosting "
        "methods (XGBoost) [9] offer competitive accuracy but with reduced interpretability."
    )
    pdf.subsection("C. Gap Analysis")
    pdf.para(
        "Existing work exhibits three limitations our system addresses: (1) binary risk classification "
        "without proportional response, (2) absence of end-to-end production deployment documentation, "
        "and (3) lack of comprehensive adversarial security evaluation with multiple attack profiles. "
        "The closest related work by Wiefling et al. [4] provides an OpenStack plugin but focuses on "
        "the Freeman algorithm without ML-based risk scoring or SaaS platform engineering."
    )

    # === III. SYSTEM ARCHITECTURE ===
    pdf.section("III", "System Architecture")
    pdf.subsection("A. Dual-Mode Design")
    pdf.para(
        "The system operates in two modes: local mode using SQLite and in-memory caching for development "
        "and research, and cloud mode using AWS RDS (PostgreSQL), ElastiCache (Redis), and S3 for production "
        "deployment. Mode selection is controlled via environment variables with automatic fallback, ensuring "
        "zero code changes between environments."
    )
    pdf.subsection("B. Authentication Pipeline")
    pdf.para("The authentication flow operates as follows:")
    pdf.bullet("User submits credentials (username + password).")
    pdf.bullet("System extracts contextual features and automatically queries a simulated Threat Intelligence feed analyzing the IP address (e.g., detecting Tor Exit Nodes or Commercial VPNs) to retrieve a Threat Score.")
    pdf.bullet("Random Forest model computes risk score r in [0.0, 1.0].")
    pdf.bullet("Three-tier decision: r < 0.3 = ALLOW, 0.3 <= r < 0.7 = MFA (e.g., SMS OTP challenge), r >= 0.7 = BLOCK (access denied + IP rate-limited).")
    pdf.bullet("Decision, risk score, and contributing factors are logged for audit.")

    pdf.subsection("C. Database Schema")
    pdf.para(
        "The system uses four primary tables: User (credentials, TOTP secrets), LoginLog (audit trail "
        "with risk scores), Plan (subscription tiers), and APIKey (key management with usage tracking)."
    )

    # === IV. MACHINE LEARNING MODEL ===
    pdf.section("IV", "Machine Learning Model")
    pdf.subsection("A. Feature Engineering")
    pdf.para("Each login attempt is characterized by seven features:")
    pdf.add_table(
        ["#", "Feature", "Type", "Rationale"],
        [
            ["1", "Country", "Categorical", "Geo-location anomaly"],
            ["2", "Region", "Categorical", "Continental risk zone"],
            ["3", "Hour of Day", "Numerical", "Temporal pattern"],
            ["4", "Device Type", "Categorical", "Device fingerprint"],
            ["5", "Prev. Login", "Binary", "Account history"],
            ["6", "Threat Score", "Numerical", "Network Profile IP Reputation (0-100)"],
            ["7", "Distance (km)", "Numerical", "Impossible travel"],
        ],
        title="Table I: Feature Set for Risk Assessment",
        col_widths=[12, 35, 30, 113],
    )

    pdf.subsection("B. Training Data Generation")
    pdf.para(
        "We generate 10,000 synthetic authentication events spanning 200 countries using five domain-expert "
        "risk injection rules: (1) high threat score (> 70), (2) long distance (> 3000km), (3) unusual "
        "hours (0:00-5:00), (4) combined risk factors, and (5) high-risk country origin. A 5% label noise "
        "injection ensures model robustness to imperfect ground truth -- a standard practice when real "
        "authentication logs are unavailable due to privacy regulations (GDPR, CCPA) [1, 2]."
    )

    pdf.subsection("C. Model Configuration")
    pdf.para(
        "We employ a Random Forest classifier with 200 estimators, maximum depth of 18, minimum samples "
        "split of 5, and minimum samples leaf of 2. The 80/20 train-test split uses stratified sampling "
        "to preserve class distribution (~21.6% positive rate)."
    )

    # === V. EVALUATION ===
    pdf.section("V", "Evaluation")

    pdf.subsection("A. ML Performance Metrics")
    if ml:
        pdf.add_table(
            ["Metric", "Safe Class", "Risk Class"],
            [
                ["Precision", str(ml["precision"]["safe"]), str(ml["precision"]["risk"])],
                ["Recall", str(ml["recall"]["safe"]), str(ml["recall"]["risk"])],
                ["F1 Score", str(ml["f1_score"]["safe"]), str(ml["f1_score"]["risk"])],
                ["Overall Accuracy", "", str(ml["accuracy"])],
                ["ROC-AUC", "", str(ml["roc_auc"])],
                ["PR-AUC", "", str(ml["pr_auc"])],
            ],
            title="Table II: Classification Performance Metrics",
            col_widths=[70, 60, 60],
        )

    # ROC Curve
    roc_path = os.path.join(EVAL_DIR, "roc_curve.png")
    pdf.add_chart(roc_path, "Fig. 1: ROC Curve (AUC = 0.9019)")

    # Confusion Matrix
    cm_path = os.path.join(EVAL_DIR, "confusion_matrix.png")
    pdf.add_chart(cm_path, "Fig. 2: Normalized Confusion Matrix", w=120)

    pdf.subsection("B. Cross-Validation")
    pdf.para(
        "5-fold stratified cross-validation yields 94.91% +/- 0.27% accuracy (10-fold: 95.00% +/- 0.35%), "
        "confirming model generalizability with minimal variance across folds."
    )
    cv_path = os.path.join(EVAL_DIR, "cross_validation.png")
    pdf.add_chart(cv_path, "Fig. 3: Cross-Validation Stability")

    pdf.subsection("C. Feature Importance Analysis")
    pdf.para(
        "Feature importance analysis reveals that Threat Score (51.03%) and Distance (22.50%) collectively "
        "contribute 73.53% of model decisions, aligning with cybersecurity domain knowledge [1]."
    )
    fi_path = os.path.join(EVAL_DIR, "feature_importance.png")
    pdf.add_chart(fi_path, "Fig. 4: Feature Importance Rankings")

    # === MODEL COMPARISON ===
    pdf.subsection("D. Model Comparison")
    pdf.para(
        "To justify model selection, we compare Random Forest against four baselines using identical "
        "data splits and evaluation protocols."
    )
    if comp:
        rows = []
        for name, m in comp.items():
            marker = "**" if name == "Random Forest" else ""
            rows.append([
                f"{marker}{name}{marker}",
                f"{marker}{m['accuracy']}{marker}",
                f"{marker}{m['f1_score']}{marker}",
                f"{marker}{m['roc_auc']}{marker}",
                f"{marker}{m['cv_mean']}+/-{m['cv_std']}{marker}",
                f"{marker}{m['inference_median_ms']}{marker}",
            ])
        pdf.add_table(
            ["Model", "Acc", "F1", "ROC-AUC", "CV (5-fold)", "Inf (ms)"],
            rows,
            title="Table III: Classifier Comparison on Authentication Risk Detection",
            col_widths=[42, 22, 22, 22, 45, 27],
        )

    pdf.para(
        "Random Forest and XGBoost achieve comparable accuracy (94.45% vs. 94.50%) and F1 scores "
        "(0.8593 vs. 0.8622). We select Random Forest for three reasons: (1) Interpretability -- native "
        "feature importance analysis enables security teams to audit risk decisions; (2) Cross-validation "
        "stability -- lowest CV variance (+/-0.0027 vs. +/-0.0034); (3) Hyperparameter robustness -- "
        "fewer tunable parameters reduces deployment risk."
    )

    # Model comparison charts
    roc_comp = os.path.join(EVAL_DIR, "model_comparison_roc.png")
    pdf.add_chart(roc_comp, "Fig. 5: ROC Curve Comparison -- 5 Classifiers")

    heatmap = os.path.join(EVAL_DIR, "model_comparison_heatmap.png")
    pdf.add_chart(heatmap, "Fig. 6: Classifier Performance Heatmap")

    bars = os.path.join(EVAL_DIR, "model_comparison_bars.png")
    pdf.add_chart(bars, "Fig. 7: Model Comparison -- Accuracy, F1, Latency")

    # === SECURITY EVALUATION ===
    pdf.subsection("E. Security Evaluation")
    pdf.para(
        "We evaluate security efficacy against 1,500 adversarial scenarios across 21 attack profiles "
        "categorized into three risk tiers:"
    )
    if sec:
        cat = sec["category_detection"]
        pdf.add_table(
            ["Category", "Scenarios", "Detected", "Rate", "Avg Score"],
            [
                ["**High-Risk**", str(cat["high"]["total_scenarios"]), str(cat["high"]["detected"]), "**100%**", str(cat["high"]["avg_risk_score"])],
                ["Medium-Risk", str(cat["medium"]["total_scenarios"]), str(cat["medium"]["detected"]), "57.6%", str(cat["medium"]["avg_risk_score"])],
                ["Legitimate", str(cat["low"]["total_scenarios"]), str(cat["low"]["detected"]), "**0% FP**", str(cat["low"]["avg_risk_score"])],
            ],
            title="Table IV: Security Evaluation by Risk Category",
            col_widths=[38, 32, 32, 30, 38],
        )
    pdf.para(
        "At the balanced threshold (0.5), the system achieves precision = 1.0 with zero false positives, "
        "meaning no legitimate user is ever wrongly blocked. The false negative rate of 14.13% affects "
        "only medium-risk scenarios, where users receive MFA challenges -- a proportional response."
    )

    sec_chart = os.path.join(EVAL_DIR, "security_detection.png")
    pdf.add_chart(sec_chart, "Fig. 8: Attack Detection by Profile")

    # Threshold analysis
    pdf.subsection("F. Threshold Sensitivity")
    if ml and "threshold_analysis" in ml:
        rows = []
        for t in ml["threshold_analysis"]:
            marker = "**" if t["threshold"] == 0.5 else ""
            rows.append([f"{marker}{t['threshold']}{marker}", f"{marker}{t['accuracy']}{marker}",
                         f"{marker}{t['precision']}{marker}", f"{marker}{t['recall']}{marker}",
                         f"{marker}{t['f1']}{marker}"])
        pdf.add_table(
            ["Threshold", "Accuracy", "Precision", "Recall", "F1"],
            rows,
            title="Table V: Threshold Sensitivity Analysis",
            col_widths=[30, 40, 40, 40, 40],
        )

    thresh_chart = os.path.join(EVAL_DIR, "threshold_analysis.png")
    pdf.add_chart(thresh_chart, "Fig. 9: Threshold Sensitivity Curves")

    pdf.subsection("G. Performance Benchmarks")
    pdf.para(
        "The system achieves 27ms median inference latency (p95: 70ms, p99: 75ms), well within the "
        "100ms threshold for real-time authentication."
    )
    lat_chart = os.path.join(EVAL_DIR, "latency_distribution.png")
    pdf.add_chart(lat_chart, "Fig. 10: Inference Latency Distribution")

    # === VI. SAAS API PLATFORM ===
    pdf.section("VI", "SaaS API Platform")
    pdf.para(
        "To demonstrate commercial viability, we deploy the system as a REST API platform with four "
        "subscription tiers (Free: 500 calls/month; Starter: $29/10K; Business: $99/100K; Enterprise: "
        "$299/1M). The API exposes a single endpoint (POST /api/v1/assess) that accepts login context "
        "and returns risk score, recommended action, and contributing risk factors."
    )
    pdf.para(
        "Key platform features include: API key generation and revocation, usage metering with daily "
        "limits, Stripe webhook integration for subscription management, and a web dashboard for "
        "monitoring API consumption and security events."
    )
    pdf.para(
        "The cloud architecture uses AWS RDS (PostgreSQL) for persistent storage, ElastiCache (Redis) "
        "for session management and rate limiting, S3 for ML model versioning, and Elastic Beanstalk "
        "with Docker for auto-scaling deployment."
    )

    # === VII. DISCUSSION ===
    pdf.section("VII", "Discussion")
    pdf.subsection("A. Key Findings")
    pdf.para(
        "Our evaluation reveals three principal findings: (1) the three-tier response framework eliminates "
        "false positives at the balanced threshold while maintaining 85.87% true positive rate; (2) feature "
        "importance analysis confirms domain knowledge -- IP reputation and impossible travel dominate risk "
        "scoring; (3) the full system, from ML model to SaaS API, operates within real-time latency constraints."
    )
    pdf.subsection("B. Limitations")
    pdf.para(
        "We acknowledge several limitations: (1) synthetic training data may not capture all real-world "
        "behavioral patterns; (2) IP threat scores currently use simplified Network Profiles (Residential, VPN, Tor) and would require full integration with "
        "services like CrowdStrike or AbuseIPDB in production; (3) the feature set is limited to seven "
        "features -- behavioral biometrics (keystroke dynamics, mouse movement) would strengthen "
        "discrimination; (4) the Random Forest model does not capture temporal dependencies in login "
        "sequences, which LSTM or Transformer architectures could address."
    )
    pdf.subsection("C. Comparison with Static Authentication")
    pdf.para(
        "Compared to traditional static authentication, our system provides: (a) zero additional friction "
        "for 83.6% of legitimate logins (ALLOW), (b) graduated response that prevents account lockout for "
        "medium-risk scenarios, and (c) real-time threat detection that adapts to emerging attack patterns "
        "through model retraining."
    )

    # === VIII. CONCLUSION ===
    pdf.section("VIII", "Conclusion and Future Work")
    pdf.para(
        "We presented an Adaptive Authentication System that combines ML-based risk scoring with a "
        "three-tier proportional response framework, deployed as a production-ready SaaS API platform. "
        "Our evaluation demonstrates strong classification performance (94.45% accuracy, 0.9019 ROC-AUC), "
        "robust security (100% high-risk detection, 0% false positives), and real-time latency (27ms median)."
    )
    pdf.para(
        "Future work includes: (1) integration of real IP threat intelligence feeds, (2) temporal modeling "
        "with LSTM/Transformer architectures, (3) behavioral biometrics (keystroke dynamics), (4) federated "
        "learning for privacy-preserving model training across tenants, (5) concept drift detection and "
        "automated retraining, and (6) formal user studies measuring MFA friction impact."
    )

    # === REFERENCES ===
    pdf.section("", "References")
    refs = [
        '[1] D. Freeman et al., "Who are you? A statistical approach to measuring user authenticity," Proc. NDSS, 2016.',
        '[2] S. Wiefling et al., "Is this really you? An empirical study on risk-based authentication applied in the wild," Proc. IFIP SEC, 2019, pp. 134-148.',
        '[3] S. Wiefling et al., "Verify it\'s you: How users (don\'t) verify themselves on the web," Proc. ACM CCS Workshop, 2021.',
        '[4] V. Unsel, S. Wiefling et al., "Risk-based authentication for OpenStack: A fully functional implementation," Proc. ACM CODASPY, 2023.',
        '[5] F. T. Liu et al., "Isolation forest," Proc. IEEE ICDM, 2008, pp. 413-422.',
        '[6] A. Acien et al., "BeCAPTCHA: Behavioral bot detection using touchscreen and mobile sensors," Eng. Appl. of AI, vol. 98, 2021.',
        '[7] Y. Zhang et al., "Intrusion detection for IoT based on improved genetic algorithm and deep belief network," IEEE Access, vol. 7, 2020.',
        '[8] L. Breiman, "Random forests," Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.',
        '[9] T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," Proc. ACM KDD, 2016, pp. 785-794.',
        '[10] NIST, "Digital Identity Guidelines: Authentication and Lifecycle Management," SP 800-63B, 2020.',
        '[11] Verizon, "2024 Data Breach Investigations Report," 2024.',
        '[12] Google, "How effective is basic account hygiene at preventing hijacking," Google Security Blog, 2019.',
        '[13] OWASP, "OWASP Top 10 - 2021," 2021.',
        '[14] F. Pedregosa et al., "Scikit-learn: Machine learning in Python," JMLR, vol. 12, pp. 2825-2830, 2011.',
        '[15] Pallets Projects, "Flask: A Python Micro Web Framework," 2024.',
    ]
    self = pdf
    self.set_font("Helvetica", "", 8)
    self.set_text_color(30, 30, 30)
    for ref in refs:
        if self.get_y() > 270:
            self.add_page()
        self.multi_cell(0, 3.8, ref)
        self.ln(1)

    # === SAVE ===
    pdf.output(OUTPUT)
    print(f"\n  IEEE Paper PDF generated: {OUTPUT}")
    print(f"  Pages: {pdf.page_no()}")
    print(f"  Size: {os.path.getsize(OUTPUT) / 1024:.0f} KB\n")


if __name__ == "__main__":
    build()
