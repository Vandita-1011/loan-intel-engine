#!/usr/bin/env python3
"""
05_train_survival_model.py
===========================
Task 3 — Survival & Transition: Cox Proportional Hazards for time-to-default,
plus monthly Markov transition probability matrix.
"""

import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"
REPORTS = ROOT / "reports"

print("▸ Training survival models …")

static = pd.read_csv(RAW / "loan_static_attributes.csv")
train = pd.read_csv(RAW / "loan_monthly_performance_train.csv")

# ── Build survival dataset ───────────────────────────────────────────────
# For each loan: time-to-event (default or right-censored), covariates
credit_map = {"<620": 600, "620-660": 640, "660-700": 680, "700-740": 720, "740-780": 760, "780+": 800}
ltv_map = {"<=60%": 55, "60-70%": 65, "70-80%": 75, "80-90%": 85, "90-95%": 92, ">95%": 98}
dti_map = {"<20%": 15, "20-30%": 25, "30-40%": 35, "40-45%": 42, "45-50%": 47, ">50%": 55}

static_enc = static.copy()
static_enc["credit_score"] = static_enc["credit_score_band"].map(credit_map)
static_enc["ltv"] = static_enc["ltv_band"].map(ltv_map)
static_enc["dti"] = static_enc["dti_band"].map(dti_map)

# Find time to default or censoring for each loan
loan_events = []
for lid, grp in train.groupby("loan_id"):
    grp = grp.sort_values("month_index")
    defaulted = grp[grp["current_status"] == "Default"]
    if len(defaulted) > 0:
        event_time = defaulted.iloc[0]["month_index"]
        event = 1
    else:
        event_time = grp["month_index"].max()
        event = 0  # right censored
    loan_events.append({"loan_id": lid, "duration": event_time, "event": event})

survival_df = pd.DataFrame(loan_events).merge(
    static_enc[["loan_id", "credit_score", "ltv", "dti", "interest_rate",
                "credit_score_band", "origination_month"]],
    on="loan_id", how="left"
)

# Fill NaN
survival_df = survival_df.dropna(subset=["duration", "event", "credit_score", "ltv", "dti", "interest_rate"])
survival_df["duration"] = survival_df["duration"].clip(lower=1)

print(f"  Survival dataset: {len(survival_df):,} loans, {survival_df['event'].sum():.0f} defaults")

# ── Cox Proportional Hazards ─────────────────────────────────────────────
cox_features = ["credit_score", "ltv", "dti", "interest_rate"]
cox_df = survival_df[["duration", "event"] + cox_features].copy()

cph = CoxPHFitter(penalizer=0.01)
cph.fit(cox_df, duration_col="duration", event_col="event")

print("\n  Cox PH Summary:")
cph.print_summary(columns=["coef", "exp(coef)", "p"])

# Save coefficients
cox_summary = cph.summary.reset_index()
cox_coefs = cox_summary[["covariate", "coef", "exp(coef)", "p"]].to_dict(orient="records")

# ── Kaplan-Meier by credit band ──────────────────────────────────────────
km_curves = {}
kmf = KaplanMeierFitter()

for band in ["<620", "620-660", "660-700", "700-740", "740-780", "780+"]:
    subset = survival_df[survival_df["credit_score_band"] == band]
    if len(subset) < 10:
        continue
    kmf.fit(subset["duration"], subset["event"], label=band)
    timeline = kmf.survival_function_.reset_index()
    timeline.columns = ["time", "survival"]
    km_curves[band] = {
        "time": timeline["time"].tolist(),
        "survival": [round(v, 4) for v in timeline["survival"].tolist()],
        "n_loans": len(subset),
        "n_events": int(subset["event"].sum()),
    }

# ── Kaplan-Meier by vintage ─────────────────────────────────────────────
km_vintage = {}
survival_df["vintage_year"] = survival_df["origination_month"].str[:4]
for vintage in survival_df["vintage_year"].unique():
    subset = survival_df[survival_df["vintage_year"] == vintage]
    if len(subset) < 50:
        continue
    kmf.fit(subset["duration"], subset["event"], label=vintage)
    timeline = kmf.survival_function_.reset_index()
    timeline.columns = ["time", "survival"]
    km_vintage[vintage] = {
        "time": timeline["time"].tolist(),
        "survival": [round(v, 4) for v in timeline["survival"].tolist()],
    }

# ── Markov Transition Matrix ────────────────────────────────────────────
print("\n  Building Markov transition matrix …")
states = ["Current", "30DPD", "60DPD", "90DPD+", "Default", "Prepaid", "Closed"]
state_idx = {s: i for i, s in enumerate(states)}

# Count transitions
n_states = len(states)
trans_counts = np.zeros((n_states, n_states))

for _, grp in train.groupby("loan_id"):
    grp = grp.sort_values("month_index")
    statuses = grp["current_status"].values
    for i in range(len(statuses) - 1):
        s_from = state_idx.get(statuses[i])
        s_to = state_idx.get(statuses[i + 1])
        if s_from is not None and s_to is not None:
            trans_counts[s_from, s_to] += 1

# Normalize to probabilities
trans_matrix = np.zeros_like(trans_counts)
for i in range(n_states):
    row_sum = trans_counts[i].sum()
    if row_sum > 0:
        trans_matrix[i] = trans_counts[i] / row_sum

# Absorbing states (Default, Prepaid, Closed) stay put
for absorbing in [4, 5, 6]:
    trans_matrix[absorbing] = 0
    trans_matrix[absorbing, absorbing] = 1.0

trans_dict = {
    "states": states,
    "matrix": [[round(v, 4) for v in row] for row in trans_matrix.tolist()],
    "counts": [[int(v) for v in row] for row in trans_counts.tolist()],
}

print("  Transition matrix (row=from, col=to):")
print(f"  {'':>10}", "  ".join(f"{s:>8}" for s in states))
for i, s in enumerate(states):
    print(f"  {s:>10}", "  ".join(f"{trans_matrix[i,j]:8.4f}" for j in range(n_states)))

# ── Save everything ──────────────────────────────────────────────────────
import joblib
joblib.dump(cph, ARTIFACTS / "cox_model.joblib")

survival_output = {
    "cox_coefficients": cox_coefs,
    "km_by_credit_band": km_curves,
    "km_by_vintage": km_vintage,
    "transition_matrix": trans_dict,
    "summary_stats": {
        "total_loans": len(survival_df),
        "total_defaults": int(survival_df["event"].sum()),
        "default_rate": round(float(survival_df["event"].mean()), 4),
        "median_duration": round(float(survival_df["duration"].median()), 1),
    }
}

with open(PROC / "survival_results.json", "w") as f:
    json.dump(survival_output, f, indent=2, default=str)

with open(ARTIFACTS / "transition_matrix.json", "w") as f:
    json.dump(trans_dict, f, indent=2)

print(f"\n✓ Cox model: backend/app/artifacts/cox_model.joblib")
print(f"✓ Results: data/processed/survival_results.json")
print(f"✓ Transition matrix: backend/app/artifacts/transition_matrix.json")
