# Adaptive Authentication System — Evaluation Report

**Generated:** 2026-03-24 22:10:42
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
| Precision | 0.9428 | 0.9522 | 0.9449 |
| Recall | 0.9892 | 0.7829 | 0.9445 |
| F1-Score | 0.9654 | 0.8593 | 0.9425 |

- **Accuracy:** 0.9445
- **ROC-AUC:** 0.9019
- **PR-AUC:** 0.8565
- **Training time:** 0.753s

### Cross-Validation

| Folds | Accuracy (mean ± std) |
|-------|----------------------|
| 5-fold | 0.9491 ± 0.0027 |
| 10-fold | 0.95 ± 0.0035 |
| 5-fold F1 (weighted) | 0.9475 ± 0.0029 |
| 5-fold ROC-AUC | 0.9021 ± 0.0066 |

### Feature Importance

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Threat Score | 0.5103 |
| 2 | Distance (km) | 0.225 |
| 3 | Hour of Day | 0.0891 |
| 4 | Prev Login Success | 0.0516 |
| 5 | Country | 0.0499 |
| 6 | Device Type | 0.0462 |
| 7 | Region | 0.028 |

### Threshold Analysis

| Threshold | Accuracy | Precision | Recall | F1 |
|-----------|----------|-----------|--------|-----|
| 0.2 | 0.93 | 0.853 | 0.8176 | 0.8349 |
| 0.3 | 0.944 | 0.9303 | 0.8014 | 0.861 |
| 0.4 | 0.945 | 0.9425 | 0.7945 | 0.8622 |
| 0.5 | 0.9445 | 0.9522 | 0.7829 | 0.8593 |
| 0.6 | 0.9405 | 0.9511 | 0.7644 | 0.8476 |
| 0.7 | 0.9335 | 0.9518 | 0.7298 | 0.8261 |
| 0.8 | 0.9225 | 0.9603 | 0.6697 | 0.7891 |

### Inference Speed
- Median: **27.495 ms**
- p95: **69.775 ms**
- p99: **74.825 ms**

---
## 2. Security Evaluation

- Total scenarios: **1500**
- Attacks: **750** | Legitimate: **750**

### Detection Metrics by Threshold

| Threshold | TPR | FPR | FNR | Precision | Recall | F1 |
|-----------|-----|-----|-----|-----------|--------|-----|
| conservative (0.3) | 0.8747 | 0.0013 | 0.1253 | 0.9985 | 0.8747 | 0.9325 |
| balanced (0.5) | 0.8587 | 0.0 | 0.1413 | 1.0 | 0.8587 | 0.924 |
| aggressive (0.7) | 0.7827 | 0.0 | 0.2173 | 1.0 | 0.7827 | 0.8781 |

### Detection by Category

| Category | Scenarios | Detected | Rate | Avg Score |
|----------|-----------|----------|------|-----------|
| high | 500 | 500 | 100.0% | 0.9362 |
| medium | 250 | 144 | 57.6% | 0.4767 |
| low | 750 | 0 | 0.0% | 0.0712 |

### Risk Score Distribution
- Attack mean: **0.783** (std: 0.29)
- Legitimate mean: **0.0712** (std: 0.0477)
- Score separation: **0.7118**

---
## 3. Performance Benchmarks

### Single-Thread Inference
- Iterations: **1000**
- Median: **26.7501 ms**
- p95: **28.3072 ms**
- p99: **31.5348 ms**
- Throughput: **37.0 pred/s**

### Concurrent Load Test

| Threads | Requests | Time (s) | Throughput | Median (ms) | p99 (ms) |
|---------|----------|----------|------------|-------------|----------|
| 5 | 250 | 5.454 | 45.8/s | 106.4568 | 171.5531 |
| 10 | 500 | 11.074 | 45.2/s | 182.0181 | 631.7909 |
| 25 | 1250 | 28.124 | 44.4/s | 399.6247 | 2411.9239 |
| 50 | 2500 | 61.367 | 40.7/s | 862.0491 | 5702.0387 |

---
## 4. Generated Charts

- **Confusion Matrix**: `evaluation/results/confusion_matrix.png`
- **Cross Validation**: `evaluation/results/cross_validation.png`
- **Feature Importance**: `evaluation/results/feature_importance.png`
- **Latency Distribution**: `evaluation/results/latency_distribution.png`
- **Precision Recall Curve**: `evaluation/results/precision_recall_curve.png`
- **Risk Score Distribution**: `evaluation/results/risk_score_distribution.png`
- **Roc Curve**: `evaluation/results/roc_curve.png`
- **Security Detection**: `evaluation/results/security_detection.png`
- **Threshold Analysis**: `evaluation/results/threshold_analysis.png`
