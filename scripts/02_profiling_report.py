#!/usr/bin/env python3
"""
02_profiling_report.py
======================
Task 1 — Data Intelligence: distributions, missingness, outliers,
invalid dates, cross-field checks, correlations, drift scores, DQ scores.
Outputs reports/data_intelligence_report.md + data/processed/dq_summary.json
"""

import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
PROC.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# ── Load data ──────────────────────────────────────────────────────────────
static = pd.read_csv(RAW / "loan_static_attributes.csv")
train = pd.read_csv(RAW / "loan_monthly_performance_train.csv")
test = pd.read_csv(RAW / "loan_monthly_performance_test.csv")
rules = json.loads((RAW / "validation_rules.json").read_text())

print("▸ Running data profiling …")

# ── 1. Missingness ────────────────────────────────────────────────────────
missing = train.isnull().sum()
missing_pct = (missing / len(train) * 100).round(2)
missing_report = missing_pct[missing_pct > 0].to_dict()

# ── 2. Distributions ──────────────────────────────────────────────────────
num_cols = train.select_dtypes(include=[np.number]).columns.tolist()
dist_stats = {}
for col in num_cols:
    s = train[col].dropna()
    if len(s) == 0:
        continue
    dist_stats[col] = {
        "mean": round(float(s.mean()), 4),
        "median": round(float(s.median()), 4),
        "std": round(float(s.std()), 4),
        "min": round(float(s.min()), 4),
        "max": round(float(s.max()), 4),
        "skew": round(float(s.skew()), 4),
        "kurtosis": round(float(s.kurtosis()), 4),
    }

# ── 3. Outliers (IQR + z-score) ───────────────────────────────────────────
outlier_report = {}
for col in ["current_balance", "days_past_due", "interest_rate"]:
    s = train[col].dropna()
    if len(s) == 0:
        continue
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    iqr_outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
    z = np.abs(stats.zscore(s))
    z_outliers = int((z > 3).sum())
    outlier_report[col] = {"iqr_outliers": iqr_outliers, "zscore_outliers": z_outliers}

# ── 4. Invalid dates ──────────────────────────────────────────────────────
# Compare last_updated_at against reporting_month (the record's own period),
# not origination_month. Script 01 generates pre-origination performance rows
# with legitimate dates; only the ~1% injected "2018-06-15" dates are truly invalid.
train_dates = train.copy()
train_dates["last_updated_at"] = pd.to_datetime(train_dates["last_updated_at"], errors="coerce")
train_dates["reporting_date"] = pd.to_datetime(train_dates["reporting_month"], format="%Y-%m")
invalid_dates = int((train_dates["last_updated_at"] < train_dates["reporting_date"]).sum())

# ── 5. Cross-field contradictions ──────────────────────────────────────────
prepaid_with_balance = int(
    ((train["current_status"] == "Prepaid") & (train["current_balance"].fillna(0) > 0)).sum()
)
current_with_dpd = int(
    ((train["current_status"] == "Current") & (train["days_past_due"] > 0)).sum()
)
contradictions = {
    "prepaid_with_balance": prepaid_with_balance,
    "current_with_dpd": current_with_dpd,
    "invalid_dates": invalid_dates,
}

# ── 6. Correlations ───────────────────────────────────────────────────────
corr_cols = ["current_balance", "interest_rate", "days_past_due",
             "loan_age_months", "remaining_term_months"]
corr_matrix = train[corr_cols].corr().round(3).to_dict()

# ── 7. Status distribution ────────────────────────────────────────────────
status_dist = train["current_status"].value_counts(normalize=True).round(4).to_dict()

# ── 8. PSI / KS Drift (train vs test) ────────────────────────────────────
def compute_psi(train_col, test_col, bins=10):
    """Population Stability Index."""
    breakpoints = np.linspace(
        min(train_col.min(), test_col.min()),
        max(train_col.max(), test_col.max()),
        bins + 1
    )
    train_pct = np.histogram(train_col, breakpoints)[0] / len(train_col)
    test_pct = np.histogram(test_col, breakpoints)[0] / len(test_col)
    train_pct = np.clip(train_pct, 0.001, None)
    test_pct = np.clip(test_pct, 0.001, None)
    return float(np.sum((test_pct - train_pct) * np.log(test_pct / train_pct)))

drift_report = {}
for col in ["current_balance", "interest_rate", "days_past_due"]:
    tr = train[col].dropna()
    te = test[col].dropna()
    if len(tr) > 0 and len(te) > 0:
        psi = compute_psi(tr, te)
        ks_stat, ks_p = stats.ks_2samp(tr, te)
        drift_report[col] = {
            "psi": round(psi, 4),
            "ks_statistic": round(float(ks_stat), 4),
            "ks_pvalue": round(float(ks_p), 6),
        }

# ── 9. Data Quality Score ─────────────────────────────────────────────────
total_cells = len(train) * len(train.columns)
missing_cells = int(train.isnull().sum().sum())
completeness = 1 - missing_cells / total_cells

# Validity (no contradictions, no invalid dates, no outliers)
total_issues = (prepaid_with_balance + current_with_dpd + invalid_dates +
                sum(v["iqr_outliers"] for v in outlier_report.values()))
validity = max(0, 1 - total_issues / len(train))

dq_score = round((completeness * 0.5 + validity * 0.5) * 100, 1)

# ── Assemble summary ──────────────────────────────────────────────────────
summary = {
    "dataset_shape": {"train_rows": len(train), "test_rows": len(test),
                      "static_rows": len(static), "columns": len(train.columns)},
    "missing_pct": missing_report,
    "distributions": dist_stats,
    "outliers": outlier_report,
    "contradictions": contradictions,
    "correlation_matrix": corr_matrix,
    "status_distribution": status_dist,
    "drift": drift_report,
    "data_quality_score": dq_score,
    "completeness_pct": round(completeness * 100, 2),
    "validity_pct": round(validity * 100, 2),
}

# Save JSON for frontend
with open(PROC / "dq_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)

# ── Generate Markdown Report ──────────────────────────────────────────────
report = f"""# Data Intelligence Report

*Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}*

## Dataset Overview
| Metric | Value |
|---|---|
| Training rows | {len(train):,} |
| Test rows | {len(test):,} |
| Static attributes | {len(static):,} loans |
| Columns | {len(train.columns)} |

## Data Quality Score: **{dq_score}/100**
- Completeness: {round(completeness*100,1)}%
- Validity: {round(validity*100,1)}%

## Missingness
| Column | Missing % |
|---|---|
"""
for col, pct in sorted(missing_report.items(), key=lambda x: -x[1]):
    report += f"| {col} | {pct}% |\n"

report += f"""
## Outliers
| Column | IQR Outliers | Z-Score Outliers |
|---|---|---|
"""
for col, vals in outlier_report.items():
    report += f"| {col} | {vals['iqr_outliers']:,} | {vals['zscore_outliers']:,} |\n"

report += f"""
## Cross-Field Contradictions
| Issue | Count |
|---|---|
| Prepaid with balance > 0 | {prepaid_with_balance:,} |
| Current with DPD > 0 | {current_with_dpd:,} |
| Invalid dates | {invalid_dates:,} |

## Status Distribution (Training)
| Status | Proportion |
|---|---|
"""
for status, prop in sorted(status_dist.items(), key=lambda x: -x[1]):
    report += f"| {status} | {prop:.2%} |\n"

report += f"""
## Train vs Test Drift
| Feature | PSI | KS Statistic | KS p-value |
|---|---|---|---|
"""
for col, vals in drift_report.items():
    report += f"| {col} | {vals['psi']:.4f} | {vals['ks_statistic']:.4f} | {vals['ks_pvalue']:.6f} |\n"

(REPORTS / "data_intelligence_report.md").write_text(report)

print(f"  ✓ DQ Score: {dq_score}/100")
print(f"  ✓ Report: reports/data_intelligence_report.md")
print(f"  ✓ JSON:   data/processed/dq_summary.json")
