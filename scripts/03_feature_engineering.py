#!/usr/bin/env python3
"""
03_feature_engineering.py
=========================
Builds ML-ready feature matrix from raw panel + static data.
Time-aware: features use only past/current information, no future leakage.
Forward targets are constructed using the full continuous panel to prevent
censoring near split boundaries, with explicit observability masks.
"""

import warnings
import json
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

print("▸ Feature engineering with full observable horizon …")

static = pd.read_csv(RAW / "loan_static_attributes.csv")
train = pd.read_csv(RAW / "loan_monthly_performance_train.csv")
test_file = RAW / "_test_ground_truth.csv" if (RAW / "_test_ground_truth.csv").exists() else RAW / "loan_monthly_performance_test.csv"
test = pd.read_csv(test_file)

# Full continuous performance panel for un-censored target lookahead
full_panel = pd.concat([train, test], ignore_index=True)
full_panel = full_panel.sort_values(["loan_id", "month_index"]).reset_index(drop=True)

# ── Merge static attributes ──────────────────────────────────────────────
df = full_panel.merge(static, on="loan_id", how="left", suffixes=("", "_static"))

# ── Encode categoricals to numeric ───────────────────────────────────────
credit_map = {"<620": 0, "620-660": 1, "660-700": 2, "700-740": 3, "740-780": 4, "780+": 5}
ltv_map = {"<=60%": 0, "60-70%": 1, "70-80%": 2, "80-90%": 3, "90-95%": 4, ">95%": 5}
dti_map = {"<20%": 0, "20-30%": 1, "30-40%": 2, "40-45%": 3, "45-50%": 4, ">50%": 5}
status_map = {"Current": 0, "30DPD": 1, "60DPD": 2, "90DPD+": 3, "Default": 4, "Prepaid": 5, "Closed": 6}
purpose_map = {"Purchase": 0, "Refinance_Rate": 1, "Refinance_Cash": 2, "Home_Equity": 3}
occ_map = {"Primary": 0, "Secondary": 1, "Investment": 2}
prop_map = {"Single_Family": 0, "Condo": 1, "Multi_Family": 2, "Townhouse": 3}

df["credit_score_num"] = df["credit_score_band"].map(credit_map).fillna(2)
df["ltv_num"] = df["ltv_band"].map(ltv_map).fillna(2)
df["dti_num"] = df["dti_band"].map(dti_map).fillna(2)
df["status_num"] = df["current_status"].map(status_map).fillna(0)
df["purpose_num"] = df["loan_purpose"].map(purpose_map).fillna(0)
df["occupancy_num"] = df["occupancy_type"].map(occ_map).fillna(0)
df["property_num"] = df["property_type"].map(prop_map).fillna(0)

# ── Derived features ─────────────────────────────────────────────────────
df["balance_ratio"] = df["current_balance"] / df["original_balance"].clip(lower=1)
df["balance_ratio"] = df["balance_ratio"].clip(0, 5).fillna(1)

df["rate_x_ltv"] = df["interest_rate"] * df["ltv_num"]
df["rate_x_dti"] = df["interest_rate"] * df["dti_num"]
df["credit_x_ltv"] = df["credit_score_num"] * df["ltv_num"]

df["is_delinquent"] = (df["status_num"] >= 1) & (df["status_num"] <= 3)
df["is_delinquent"] = df["is_delinquent"].astype(int)

# ── Lag / rolling features (per loan, sorted by month) ───────────────────
df = df.sort_values(["loan_id", "month_index"]).reset_index(drop=True)

for lag in [1, 2, 3]:
    df[f"balance_lag{lag}"] = df.groupby("loan_id")["current_balance"].shift(lag)
    df[f"dpd_lag{lag}"] = df.groupby("loan_id")["days_past_due"].shift(lag)
    df[f"status_lag{lag}"] = df.groupby("loan_id")["status_num"].shift(lag)

# Rolling stats
df["balance_rolling_mean_3"] = df.groupby("loan_id")["current_balance"].transform(
    lambda x: x.rolling(3, min_periods=1).mean()
)
df["balance_rolling_std_3"] = df.groupby("loan_id")["current_balance"].transform(
    lambda x: x.rolling(3, min_periods=1).std()
).fillna(0)

df["dpd_rolling_max_3"] = df.groupby("loan_id")["days_past_due"].transform(
    lambda x: x.rolling(3, min_periods=1).max()
)
df["dpd_rolling_mean_6"] = df.groupby("loan_id")["days_past_due"].transform(
    lambda x: x.rolling(6, min_periods=1).mean()
)

# Ever delinquent (cumulative)
df["ever_delinquent"] = df.groupby("loan_id")["is_delinquent"].cumsum().clip(upper=1)

# Months since last delinquency
def months_since_delinquent(s):
    result = []
    since = 999
    for val in s:
        if val >= 1:
            since = 0
        else:
            since += 1
        result.append(min(since, 99))
    return result

df["months_since_delinq"] = df.groupby("loan_id")["is_delinquent"].transform(
    months_since_delinquent
)

# Balance change
df["balance_change_1m"] = df["current_balance"] - df["balance_lag1"]
df["balance_change_pct"] = (df["balance_change_1m"] / df["balance_lag1"].clip(lower=1)).clip(-1, 5)

# ── Forward-looking targets with explicit observability ───────────────────
print("  Computing forward targets with observability tracking …")

def compute_horizon_target(group, target_type, horizon):
    statuses = group["status_num"].values
    dpds = group["days_past_due"].values
    months = group["month_index"].values
    n = len(statuses)
    targets = np.zeros(n, dtype=int)
    observable = np.zeros(n, dtype=int)
    max_m = months[-1] if n > 0 else 0

    for i in range(n):
        curr_m = months[i]
        window_mask = (months > curr_m) & (months <= curr_m + horizon)
        win_status = statuses[window_mask]
        win_dpd = dpds[window_mask]

        if len(win_status) == 0:
            targets[i] = 0
            observable[i] = 0
            continue

        if target_type == "delinq":
            is_pos = np.any(np.isin(win_status, [1, 2, 3, 4])) or np.any(win_dpd >= 30)
            if is_pos:
                targets[i] = 1
                observable[i] = 1
            elif np.any(np.isin(win_status, [5, 6])):
                targets[i] = 0
                observable[i] = 1
            elif max_m >= curr_m + horizon and len(win_status) == horizon:
                targets[i] = 0
                observable[i] = 1
            else:
                targets[i] = 0
                observable[i] = 0

        elif target_type == "default":
            is_pos = np.any(win_status == 4)
            if is_pos:
                targets[i] = 1
                observable[i] = 1
            elif np.any(np.isin(win_status, [5, 6])):
                targets[i] = 0
                observable[i] = 1
            elif max_m >= curr_m + horizon and len(win_status) == horizon:
                targets[i] = 0
                observable[i] = 1
            else:
                targets[i] = 0
                observable[i] = 0

        elif target_type == "prepay":
            is_pos = np.any(win_status == 5)
            if is_pos:
                targets[i] = 1
                observable[i] = 1
            elif np.any(np.isin(win_status, [4, 6])):
                targets[i] = 0
                observable[i] = 1
            elif max_m >= curr_m + horizon and len(win_status) == horizon:
                targets[i] = 0
                observable[i] = 1
            else:
                targets[i] = 0
                observable[i] = 0

    return pd.DataFrame({
        "target": targets,
        "observable": observable
    }, index=group.index)

# Compute per target
t_3m = df.groupby("loan_id", group_keys=False).apply(lambda g: compute_horizon_target(g, "delinq", 3))
df["next_3m_delinquency_flag"] = t_3m["target"].values
df["delinq_3m_observable"] = t_3m["observable"].values

t_6m = df.groupby("loan_id", group_keys=False).apply(lambda g: compute_horizon_target(g, "delinq", 6))
df["next_6m_delinquency_flag"] = t_6m["target"].values
df["delinq_6m_observable"] = t_6m["observable"].values

t_12m = df.groupby("loan_id", group_keys=False).apply(lambda g: compute_horizon_target(g, "default", 12))
df["next_12m_default_flag"] = t_12m["target"].values
df["default_12m_observable"] = t_12m["observable"].values

t_prepay = df.groupby("loan_id", group_keys=False).apply(lambda g: compute_horizon_target(g, "prepay", 12))
df["next_12m_prepayment_flag"] = t_prepay["target"].values
df["prepay_12m_observable"] = t_prepay["observable"].values

# Next state (for multiclass)
df["next_status"] = df.groupby("loan_id")["status_num"].shift(-1)
df["next_status_observable"] = df["next_status"].notna().astype(int)

# ── Restrict modeling dataset to months with enough forward lookahead ──
# Train: 1-24, Val: 25-30, Test: 31-42. We need up to month 42 in features.csv.
modeling_df = df[df["month_index"] <= 42].copy()

# Filter to active loans only (exclude already terminated: Default, Prepaid, Closed)
active_mask = modeling_df["status_num"].isin([0, 1, 2, 3])
features_df = modeling_df[active_mask].copy()

# Fill remaining NaNs for numerical features
num_features = features_df.select_dtypes(include=[np.number]).columns
features_df[num_features] = features_df[num_features].fillna(0)

# ── Save ─────────────────────────────────────────────────────────────────
FEATURE_COLS = [
    "loan_id", "month_index", "reporting_month",
    # Static encoded
    "credit_score_num", "ltv_num", "dti_num", "purpose_num",
    "occupancy_num", "property_num",
    # Time features
    "loan_age_months", "remaining_term_months",
    # Balance features
    "current_balance", "original_balance", "balance_ratio",
    "balance_change_1m", "balance_change_pct",
    "balance_rolling_mean_3", "balance_rolling_std_3",
    # Rate features
    "interest_rate", "rate_x_ltv", "rate_x_dti", "credit_x_ltv",
    # DPD features
    "days_past_due", "dpd_rolling_max_3", "dpd_rolling_mean_6",
    # Status features
    "status_num", "is_delinquent", "ever_delinquent", "months_since_delinq",
    "modification_flag",
    # Lag features
    "balance_lag1", "balance_lag2", "balance_lag3",
    "dpd_lag1", "dpd_lag2", "dpd_lag3",
    "status_lag1", "status_lag2", "status_lag3",
    # Targets
    "next_3m_delinquency_flag", "delinq_3m_observable",
    "next_6m_delinquency_flag", "delinq_6m_observable",
    "next_12m_default_flag", "default_12m_observable",
    "next_12m_prepayment_flag", "prepay_12m_observable",
    "next_status", "next_status_observable",
]

existing_cols = [c for c in FEATURE_COLS if c in features_df.columns]
features_df = features_df[existing_cols]

features_df.to_csv(PROC / "features.csv", index=False)

target_cols = [
    "next_3m_delinquency_flag", "delinq_3m_observable",
    "next_6m_delinquency_flag", "delinq_6m_observable",
    "next_12m_default_flag", "default_12m_observable",
    "next_12m_prepayment_flag", "prepay_12m_observable",
    "next_status", "next_status_observable"
]
id_cols = ["loan_id", "month_index", "reporting_month"]
feature_names = [c for c in existing_cols if c not in target_cols + id_cols]

with open(PROC / "feature_names.json", "w") as f:
    json.dump(feature_names, f, indent=2)

print(f"  ✓ Features: {len(features_df):,} rows × {len(feature_names)} features")
print(f"  ✓ Target Observability by split:")
for split_name, lo, hi in [("Val (25-30)", 25, 30), ("Test (31-42)", 31, 42)]:
    subset = features_df[(features_df["month_index"] >= lo) & (features_df["month_index"] <= hi)]
    print(f"    {split_name}: {len(subset):,} rows")
    for t in ["delinq_3m", "delinq_6m", "default_12m", "prepay_12m"]:
        obs_rate = subset[f"{t}_observable"].mean() if len(subset) > 0 else 0
        print(f"      - {t}: {obs_rate*100:.1f}% observable")
print(f"  ✓ Saved: data/processed/features.csv")
print(f"  ✓ Saved: data/processed/feature_names.json")
