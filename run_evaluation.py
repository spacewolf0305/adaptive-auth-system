"""
=============================================================================
 Adaptive Authentication System — Master Evaluation Runner
 One command to run all evaluations and generate a comprehensive report.

 Usage:
   python run_evaluation.py          # All evaluations (offline)
   python run_evaluation.py --ml     # ML metrics only
   python run_evaluation.py --sec    # Security evaluation only
   python run_evaluation.py --perf   # Performance benchmarks only
   python run_evaluation.py --charts # Generate charts only
   python run_evaluation.py --all    # Everything including charts
=============================================================================
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

RESULTS_DIR = os.path.join(BASE_DIR, "evaluation", "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


def run_ml_evaluation():
    """Run ML model evaluation."""
    from evaluation.research_evaluation import run_evaluation
    return run_evaluation()


def run_security_evaluation():
    """Run security evaluation."""
    from evaluation.security_evaluation import run_security_evaluation as sec_eval
    return sec_eval()


def run_performance_benchmark():
    """Run performance benchmarks (offline)."""
    from evaluation.performance_benchmark import run_offline_benchmark
    return run_offline_benchmark(num_iterations=1000)


def run_chart_generation():
    """Generate all charts."""
    from evaluation.generate_research_charts import generate_all_charts
    generate_all_charts()


def generate_report():
    """Generate a comprehensive markdown report from all JSON results."""
    print("\n" + "=" * 70)
    print("  📝  Generating Evaluation Report")
    print("=" * 70)

    report_lines = [
        "# Adaptive Authentication System — Evaluation Report",
        f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Model:** Random Forest Classifier (200 trees, max_depth=18)",
        "",
    ]

    # ── ML Metrics ──
    ml_path = os.path.join(RESULTS_DIR, "ml_metrics.json")
    if os.path.exists(ml_path):
        with open(ml_path) as f:
            ml = json.load(f)

        report_lines.extend([
            "---",
            "## 1. ML Model Performance",
            "",
            "### Dataset",
            f"- Total samples: **{ml['dataset']['total_samples']:,}**",
            f"- Train/Test split: **{ml['dataset']['train_samples']:,}** / **{ml['dataset']['test_samples']:,}** (80/20)",
            f"- Positive (risky) rate: **{ml['dataset']['positive_rate']*100:.1f}%**",
            "",
            "### Core Metrics",
            "",
            "| Metric | Safe (0) | Risk (1) | Weighted |",
            "|--------|----------|----------|----------|",
            f"| Precision | {ml['precision']['safe']} | {ml['precision']['risk']} | {ml['precision']['weighted']} |",
            f"| Recall | {ml['recall']['safe']} | {ml['recall']['risk']} | {ml['recall']['weighted']} |",
            f"| F1-Score | {ml['f1_score']['safe']} | {ml['f1_score']['risk']} | {ml['f1_score']['weighted']} |",
            "",
            f"- **Accuracy:** {ml['accuracy']}",
            f"- **ROC-AUC:** {ml['roc_auc']}",
            f"- **PR-AUC:** {ml['pr_auc']}",
            f"- **Training time:** {ml['training']['train_time_seconds']}s",
            "",
            "### Cross-Validation",
            "",
            "| Folds | Accuracy (mean ± std) |",
            "|-------|----------------------|",
        ])

        cv = ml.get("cross_validation", {})
        for key in ["5_fold", "10_fold"]:
            if key in cv:
                report_lines.append(
                    f"| {key.replace('_', '-')} | {cv[key]['mean']} ± {cv[key]['std']} |"
                )
        if "5_fold_f1_weighted" in cv:
            report_lines.append(f"| 5-fold F1 (weighted) | {cv['5_fold_f1_weighted']['mean']} ± {cv['5_fold_f1_weighted']['std']} |")
        if "5_fold_roc_auc" in cv:
            report_lines.append(f"| 5-fold ROC-AUC | {cv['5_fold_roc_auc']['mean']} ± {cv['5_fold_roc_auc']['std']} |")

        report_lines.extend(["", "### Feature Importance", "", "| Rank | Feature | Importance |", "|------|---------|------------|"])
        for fi in ml.get("feature_importance", []):
            report_lines.append(f"| {fi['rank']} | {fi['feature']} | {fi['importance']} |")

        report_lines.extend(["", "### Threshold Analysis", "",
                            "| Threshold | Accuracy | Precision | Recall | F1 |",
                            "|-----------|----------|-----------|--------|-----|"])
        for t in ml.get("threshold_analysis", []):
            report_lines.append(
                f"| {t['threshold']} | {t['accuracy']} | {t['precision']} | {t['recall']} | {t['f1']} |"
            )

        if "inference_speed" in ml:
            inf = ml["inference_speed"]
            report_lines.extend(["",
                "### Inference Speed",
                f"- Median: **{inf['median_ms']:.3f} ms**",
                f"- p95: **{inf['p95_ms']:.3f} ms**",
                f"- p99: **{inf['p99_ms']:.3f} ms**",
            ])

        report_lines.append("")

    # ── Security Metrics ──
    sec_path = os.path.join(RESULTS_DIR, "security_metrics.json")
    if os.path.exists(sec_path):
        with open(sec_path) as f:
            sec = json.load(f)

        report_lines.extend([
            "---",
            "## 2. Security Evaluation",
            "",
            f"- Total scenarios: **{sec['total_scenarios']}**",
            f"- Attacks: **{sec['total_attacks']}** | Legitimate: **{sec['total_legitimate']}**",
            "",
            "### Detection Metrics by Threshold",
            "",
            "| Threshold | TPR | FPR | FNR | Precision | Recall | F1 |",
            "|-----------|-----|-----|-----|-----------|--------|-----|",
        ])

        for name, m in sec.get("threshold_metrics", {}).items():
            report_lines.append(
                f"| {name} ({m['threshold']}) | {m['true_positive_rate']} | {m['false_positive_rate']} | "
                f"{m['false_negative_rate']} | {m['precision']} | {m['recall']} | {m['f1_score']} |"
            )

        report_lines.extend(["", "### Detection by Category", "",
                            "| Category | Scenarios | Detected | Rate | Avg Score |",
                            "|----------|-----------|----------|------|-----------|"])
        for cat, data in sec.get("category_detection", {}).items():
            report_lines.append(
                f"| {cat} | {data['total_scenarios']} | {data['detected']} | "
                f"{data['detection_rate']*100:.1f}% | {data['avg_risk_score']} |"
            )

        sd = sec.get("score_distribution", {})
        if sd:
            report_lines.extend(["",
                "### Risk Score Distribution",
                f"- Attack mean: **{sd['attacks']['mean']}** (std: {sd['attacks']['std']})",
                f"- Legitimate mean: **{sd['legitimate']['mean']}** (std: {sd['legitimate']['std']})",
                f"- Score separation: **{sd['separation']}**",
            ])
        report_lines.append("")

    # ── Performance Metrics ──
    perf_path = os.path.join(RESULTS_DIR, "performance_metrics.json")
    if os.path.exists(perf_path):
        with open(perf_path) as f:
            perf = json.load(f)

        st = perf.get("single_thread", {})
        report_lines.extend([
            "---",
            "## 3. Performance Benchmarks",
            "",
            "### Single-Thread Inference",
            f"- Iterations: **{st.get('iterations', 'N/A')}**",
            f"- Median: **{st.get('median_ms', 'N/A')} ms**",
            f"- p95: **{st.get('p95_ms', 'N/A')} ms**",
            f"- p99: **{st.get('p99_ms', 'N/A')} ms**",
            f"- Throughput: **{perf.get('throughput_per_sec', 'N/A')} pred/s**",
            "",
            "### Concurrent Load Test",
            "",
            "| Threads | Requests | Time (s) | Throughput | Median (ms) | p99 (ms) |",
            "|---------|----------|----------|------------|-------------|----------|",
        ])

        for key, data in perf.get("concurrent", {}).items():
            report_lines.append(
                f"| {data['threads']} | {data['total_requests']} | {data['total_time_seconds']} | "
                f"{data['throughput_per_sec']}/s | {data['median_ms']} | {data['p99_ms']} |"
            )
        report_lines.append("")

    # ── Charts ──
    chart_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".png")]
    if chart_files:
        report_lines.extend(["---", "## 4. Generated Charts", ""])
        for cf in sorted(chart_files):
            name = cf.replace(".png", "").replace("_", " ").title()
            report_lines.append(f"- **{name}**: `evaluation/results/{cf}`")
        report_lines.append("")

    # ── Save ──
    report_text = "\n".join(report_lines)
    report_path = os.path.join(RESULTS_DIR, "evaluation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n  💾  Report saved → evaluation/results/evaluation_report.md")
    print("=" * 70 + "\n")
    return report_path


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Adaptive Auth — Master Evaluation Runner")
    parser.add_argument("--ml", action="store_true", help="Run ML evaluation only")
    parser.add_argument("--sec", action="store_true", help="Run security evaluation only")
    parser.add_argument("--perf", action="store_true", help="Run performance benchmark only")
    parser.add_argument("--charts", action="store_true", help="Generate charts only")
    parser.add_argument("--all", action="store_true", help="Run everything")
    args = parser.parse_args()

    # If no flags, run all offline evaluations
    run_all = args.all or not any([args.ml, args.sec, args.perf, args.charts])

    print("\n" + "█" * 70)
    print("  🔬  ADAPTIVE AUTH — RESEARCH EVALUATION SUITE")
    print("█" * 70)

    total_start = time.time()

    if run_all or args.ml:
        run_ml_evaluation()

    if run_all or args.sec:
        run_security_evaluation()

    if run_all or args.perf:
        run_performance_benchmark()

    if run_all or args.charts:
        run_chart_generation()

    generate_report()

    total_time = time.time() - total_start

    print("█" * 70)
    print(f"  ✅  ALL EVALUATIONS COMPLETE — {total_time:.1f}s total")
    print(f"  📁  Results: evaluation/results/")
    print(f"  📝  Report:  evaluation/results/evaluation_report.md")
    print("█" * 70 + "\n")


if __name__ == "__main__":
    main()
