#!/usr/bin/env python3
"""
08_generate_explainability_report.py
=====================================
Task 6 — Explainability: SHAP global/local, calibration curves,
false-positive/false-negative case studies, confidence bands.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import json, warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
import shap
import joblib
from backend.app.services.model_service import LGBMWrapper

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"
REPORTS = ROOT / "reports"

print("▸ Generating explainability report …")

df = pd.read_csv(PROC / "features.csv")
feature_names = json.loads((PROC / "feature_names.json").read_text())
config = json.loads((ARTIFACTS / "model_config.json").read_text())

# ── Load primary model (delinq_3m) ──────────────────────────────────────
model_path = ARTIFACTS / "lgbm_delinq_3m.txt"
if not model_path.exists():
    print("  ⚠ No model found, generating minimal report")
    (REPORTS / "explainability_report.md").write_text("# Explainability Report\nNo models available.")
    exit(0)

gbm = lgb.Booster(model_file=str(model_path))

# Sample for SHAP (use validation set)
val_mask = (df["month_index"] > 24) & (df["month_index"] <= 27)
X_val = df.loc[val_mask, feature_names].values
y_val = df.loc[val_mask, "next_3m_delinquency_flag"].values.astype(int)
loan_ids_val = df.loc[val_mask, "loan_id"].values

# Limit SHAP computation
sample_size = min(2000, len(X_val))
idx = np.random.choice(len(X_val), sample_size, replace=False)
X_sample = X_val[idx]
y_sample = y_val[idx]
loan_sample = loan_ids_val[idx]

# ── SHAP values ─────────────────────────────────────────────────────────
print("  Computing SHAP values …")
explainer = shap.TreeExplainer(gbm)
shap_values = explainer.shap_values(X_sample)

# Global feature importance (mean |SHAP|)
mean_abs_shap = np.abs(shap_values).mean(axis=0)
global_importance = sorted(
    zip(feature_names, mean_abs_shap),
    key=lambda x: -x[1]
)

# ── Local explanations for sample loans ─────────────────────────────────
print("  Computing local explanations …")
proba = gbm.predict(X_sample)
local_explanations = []

for i in range(min(20, len(X_sample))):
    shap_dict = dict(zip(feature_names, [round(float(v), 4) for v in shap_values[i]]))
    top_drivers = sorted(shap_dict.items(), key=lambda x: -abs(x[1]))[:5]
    local_explanations.append({
        "loan_id": str(loan_sample[i]),
        "prediction": round(float(proba[i]), 4),
        "actual": int(y_sample[i]),
        "top_shap_drivers": [{"feature": f, "shap_value": v} for f, v in top_drivers],
        "base_value": round(float(explainer.expected_value), 4),
    })

# ── Calibration curve data ──────────────────────────────────────────────
print("  Computing calibration curve …")
from sklearn.calibration import calibration_curve

cal_model = joblib.load(ARTIFACTS / "lgbm_delinq_3m_calibrated.joblib")
cal_proba = cal_model.predict_proba(X_val)[:, 1]

try:
    fraction_pos, mean_predicted = calibration_curve(y_val, cal_proba, n_bins=10, strategy="uniform")
    calibration_data = {
        "fraction_positive": [round(float(v), 4) for v in fraction_pos],
        "mean_predicted": [round(float(v), 4) for v in mean_predicted],
    }
except Exception:
    calibration_data = {"fraction_positive": [], "mean_predicted": []}

# ── False positive / false negative case studies ────────────────────────
print("  Identifying FP/FN cases …")
threshold = config["targets"].get("delinq_3m", 0.5)
preds_binary = (proba > threshold).astype(int)

fp_mask = (preds_binary == 1) & (y_sample == 0)
fn_mask = (preds_binary == 0) & (y_sample == 1)

fp_cases = []
for i in np.where(fp_mask)[0][:5]:
    shap_dict = dict(zip(feature_names, [round(float(v), 4) for v in shap_values[i]]))
    top = sorted(shap_dict.items(), key=lambda x: -abs(x[1]))[:3]
    fp_cases.append({
        "loan_id": str(loan_sample[i]),
        "prediction": round(float(proba[i]), 4),
        "type": "false_positive",
        "drivers": [{"feature": f, "shap_value": v} for f, v in top],
        "explanation": f"Model predicted delinquency (p={proba[i]:.3f}) but loan stayed current. Key drivers: {', '.join(f[0] for f in top)}."
    })

fn_cases = []
for i in np.where(fn_mask)[0][:5]:
    shap_dict = dict(zip(feature_names, [round(float(v), 4) for v in shap_values[i]]))
    top = sorted(shap_dict.items(), key=lambda x: -abs(x[1]))[:3]
    fn_cases.append({
        "loan_id": str(loan_sample[i]),
        "prediction": round(float(proba[i]), 4),
        "type": "false_negative",
        "drivers": [{"feature": f, "shap_value": v} for f, v in top],
        "explanation": f"Model missed delinquency (p={proba[i]:.3f}). Potential blind spots: {', '.join(f[0] for f in top)}."
    })

# ── Confidence / uncertainty bands ──────────────────────────────────────
confidence_bands = {
    "high_confidence": {"range": [0.0, 0.2], "count": int((proba < 0.2).sum()) + int((proba > 0.8).sum())},
    "medium_confidence": {"range": [0.2, 0.4], "count": int(((proba >= 0.2) & (proba < 0.4)).sum()) + int(((proba >= 0.6) & (proba < 0.8)).sum())},
    "low_confidence": {"range": [0.4, 0.6], "count": int(((proba >= 0.4) & (proba <= 0.6)).sum())},
}

# ── Save JSON for API ───────────────────────────────────────────────────
explain_output = {
    "global_importance": [{"feature": f, "mean_abs_shap": round(float(v), 4)} for f, v in global_importance[:20]],
    "local_explanations": local_explanations,
    "calibration": calibration_data,
    "fp_cases": fp_cases,
    "fn_cases": fn_cases,
    "confidence_bands": confidence_bands,
    "shap_base_value": round(float(explainer.expected_value), 4),
}

with open(PROC / "explainability_results.json", "w") as f:
    json.dump(explain_output, f, indent=2, default=str)

with open(ARTIFACTS / "explainability_results.json", "w") as f:
    json.dump(explain_output, f, indent=2, default=str)

# ── SHAP values per loan (for API lookup) ────────────────────────────────
shap_per_loan = {}
for i in range(len(X_sample)):
    lid = str(loan_sample[i])
    shap_dict = dict(zip(feature_names, [round(float(v), 4) for v in shap_values[i]]))
    shap_per_loan[lid] = shap_dict

with open(ARTIFACTS / "shap_values.json", "w") as f:
    json.dump(shap_per_loan, f, indent=2)

# ── Generate markdown report ────────────────────────────────────────────
report = f"""# Explainability Report

*Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}*

## Global Feature Importance (SHAP)
| Rank | Feature | Mean |SHAP| |
|---|---|---|
"""
for i, (feat, val) in enumerate(global_importance[:15], 1):
    report += f"| {i} | {feat} | {val:.4f} |\n"

report += f"""
## Calibration
The model calibration curve shows the relationship between predicted probabilities
and actual outcomes. Values are based on {len(X_val):,} validation samples.

## False Positive Analysis
{len(fp_cases)} cases where the model predicted delinquency but the loan stayed current:
"""
for case in fp_cases:
    report += f"\n- **{case['loan_id']}**: {case['explanation']}\n"

report += f"""
## False Negative Analysis
{len(fn_cases)} cases where the model missed actual delinquency:
"""
for case in fn_cases:
    report += f"\n- **{case['loan_id']}**: {case['explanation']}\n"

report += f"""
## Prediction Confidence Distribution
| Band | Count | % |
|---|---|---|
"""
total = sum(b["count"] for b in confidence_bands.values())
for band_name, band_data in confidence_bands.items():
    pct = band_data["count"] / max(total, 1) * 100
    report += f"| {band_name} | {band_data['count']:,} | {pct:.1f}% |\n"

(REPORTS / "explainability_report.md").write_text(report)

print(f"\n✓ Explainability results: data/processed/explainability_results.json")
print(f"✓ SHAP values per loan: backend/app/artifacts/shap_values.json")
print(f"✓ Report: reports/explainability_report.md")
