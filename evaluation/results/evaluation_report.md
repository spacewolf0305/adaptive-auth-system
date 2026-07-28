# Adaptive Authentication System — Evaluation Report

**Generated:** 2026-07-28 14:38:20
**Model:** Random Forest Classifier (200 trees, max_depth=18)

---
## 1. ML Model Performance

### Dataset
- Total samples: **10,000**
- Train/Test split: **8,000** / **2,000** (80/20)
- Positive (risky) rate: **21.6%**

### Core Metrics

| Metric | Safe (0) | Risk (1) | Weighted |
|--------|----------|----------|----------|
| Precision | 0.9434 | 0.9524 | 0.9453 |
| Recall | 0.9892 | 0.7852 | 0.945 |
| F1-Score | 0.9657 | 0.8608 | 0.943 |

- **Accuracy:** 0.945
- **ROC-AUC:** 0.9013
- **PR-AUC:** 0.8494
- **Training time:** 0.552s

### Cross-Validation

| Folds | Accuracy (mean ± std) |
|-------|----------------------|
| 5-fold | 0.9484 ± 0.0029 |
| 10-fold | 0.9493 ± 0.0036 |
| 5-fold F1 (weighted) | 0.9468 ± 0.0032 |
| 5-fold ROC-AUC | 0.9037 ± 0.007 |

### Feature Importance

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Threat Score | 0.5092 |
| 2 | Distance (km) | 0.2301 |
| 3 | Hour of Day | 0.09 |
| 4 | Country | 0.0508 |
| 5 | Prev Login Success | 0.0472 |
| 6 | Device Type | 0.0447 |
| 7 | Region | 0.0279 |

### Threshold Analysis

| Threshold | Accuracy | Precision | Recall | F1 |
|-----------|----------|-----------|--------|-----|
| 0.2 | 0.928 | 0.8482 | 0.8129 | 0.8302 |
| 0.3 | 0.945 | 0.9284 | 0.8083 | 0.8642 |
| 0.4 | 0.9455 | 0.9451 | 0.7945 | 0.8632 |
| 0.5 | 0.945 | 0.9524 | 0.7852 | 0.8608 |
| 0.6 | 0.9405 | 0.9511 | 0.7644 | 0.8476 |
| 0.7 | 0.9315 | 0.954 | 0.7182 | 0.8195 |
| 0.8 | 0.918 | 0.959 | 0.649 | 0.7741 |

### Inference Speed
- Median: **40.166 ms**
- p95: **67.433 ms**
- p99: **94.769 ms**

---
## 2. Security Evaluation

- Total scenarios: **1500**
- Attacks: **750** | Legitimate: **750**

### Detection Metrics by Threshold

| Threshold | TPR | FPR | FNR | Precision | Recall | F1 |
|-----------|-----|-----|-----|-----------|--------|-----|
| conservative (0.3) | 0.8747 | 0.0027 | 0.1253 | 0.997 | 0.8747 | 0.9318 |
| balanced (0.5) | 0.8627 | 0.0 | 0.1373 | 1.0 | 0.8627 | 0.9263 |
| aggressive (0.7) | 0.7907 | 0.0 | 0.2093 | 1.0 | 0.7907 | 0.8831 |

### Detection by Category

| Category | Scenarios | Detected | Rate | Avg Score |
|----------|-----------|----------|------|-----------|
| high | 500 | 500 | 100.0% | 0.9413 |
| medium | 250 | 147 | 58.8% | 0.4833 |
| low | 750 | 0 | 0.0% | 0.0766 |

### Risk Score Distribution
- Attack mean: **0.7886** (std: 0.2893)
- Legitimate mean: **0.0766** (std: 0.0461)
- Score separation: **0.7121**

---
## 3. Performance Benchmarks

### Single-Thread Inference
- Iterations: **1000**
- Median: **73.9322 ms**
- p95: **111.9713 ms**
- p99: **142.1759 ms**
- Throughput: **13.7 pred/s**

### Concurrent Load Test

| Threads | Requests | Time (s) | Throughput | Median (ms) | p99 (ms) |
|---------|----------|----------|------------|-------------|----------|
| 5 | 250 | 7.98 | 31.3/s | 151.7044 | 324.0881 |
| 10 | 500 | 16.425 | 30.4/s | 277.3102 | 941.9087 |
| 25 | 1250 | 43.602 | 28.7/s | 664.8061 | 3501.1549 |
| 50 | 2500 | 84.749 | 29.5/s | 1188.9145 | 7540.8323 |

---
## 4. Generated Charts

- **Confusion Matrix**: `evaluation/results/confusion_matrix.png`
- **Cross Validation**: `evaluation/results/cross_validation.png`
- **Feature Importance**: `evaluation/results/feature_importance.png`
- **Latency Distribution**: `evaluation/results/latency_distribution.png`
- **Model Comparison Bars**: `evaluation/results/model_comparison_bars.png`
- **Model Comparison Heatmap**: `evaluation/results/model_comparison_heatmap.png`
- **Model Comparison Roc**: `evaluation/results/model_comparison_roc.png`
- **Precision Recall Curve**: `evaluation/results/precision_recall_curve.png`
- **Risk Score Distribution**: `evaluation/results/risk_score_distribution.png`
- **Roc Curve**: `evaluation/results/roc_curve.png`
- **Security Detection**: `evaluation/results/security_detection.png`
- **Threshold Analysis**: `evaluation/results/threshold_analysis.png`
