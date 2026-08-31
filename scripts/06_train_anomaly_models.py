#!/usr/bin/env python3
"""
06_train_anomaly_models.py
===========================
Task 4 — Anomaly/Exception Detection: IsolationForest + PyTorch autoencoder
ensemble, plus exception-type classifier.
"""

import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import joblib

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"
REPORTS = ROOT / "reports"

print("▸ Training anomaly models …")

static = pd.read_csv(RAW / "loan_static_attributes.csv")
train = pd.read_csv(RAW / "loan_monthly_performance_train.csv")
rules = json.loads((RAW / "validation_rules.json").read_text())

# ── Merge and prepare ────────────────────────────────────────────────────
credit_map = {"<620": 0, "620-660": 1, "660-700": 2, "700-740": 3, "740-780": 4, "780+": 5}
ltv_map = {"<=60%": 0, "60-70%": 1, "70-80%": 2, "80-90%": 3, "90-95%": 4, ">95%": 5}
dti_map = {"<20%": 0, "20-30%": 1, "30-40%": 2, "40-45%": 3, "45-50%": 4, ">50%": 5}
status_map = {"Current": 0, "30DPD": 1, "60DPD": 2, "90DPD+": 3, "Default": 4, "Prepaid": 5, "Closed": 6}

df = train.merge(static[["loan_id", "credit_score_band", "ltv_band", "dti_band",
                          "original_balance", "origination_month"]], on="loan_id", how="left")

df["credit_num"] = df["credit_score_band"].map(credit_map).fillna(2)
df["ltv_num"] = df["ltv_band"].map(ltv_map).fillna(2)
df["dti_num"] = df["dti_band"].map(dti_map).fillna(2)
df["status_num"] = df["current_status"].map(status_map).fillna(0)
df["balance_ratio"] = (df["current_balance"] / df["original_balance"].clip(lower=1)).fillna(1).clip(0, 20)

# ── Label anomalies from injected messiness ──────────────────────────────
# VR003: Prepaid/Closed with balance > 0
df["exc_balance_mismatch"] = (
    df["current_status"].isin(["Prepaid", "Closed"]) &
    (df["current_balance"].fillna(0) > 0)
).astype(int)

# VR004: DPD/status mismatch
df["exc_status_conflict"] = (
    (df["current_status"] == "Current") & (df["days_past_due"] > 0)
).astype(int)

# VR005: Invalid dates — last_updated_at must not be before its own reporting month.
# (Comparing against origination_month was a bug: script 01 generates performance
# rows from 2020-01 for ALL loans regardless of origination, so rows for loans
# originated later legitimately have last_updated_at before origination. The truly
# injected invalid dates have last_updated_at = "2018-06-15", which is before
# any reporting_month in the dataset.)
df["last_updated_at"] = pd.to_datetime(df["last_updated_at"], errors="coerce")
df["reporting_date"] = pd.to_datetime(df["reporting_month"], format="%Y-%m")
df["exc_date_invalid"] = (df["last_updated_at"] < df["reporting_date"]).fillna(False).astype(int)

# Missing document
df["exc_missing_doc"] = (df["document_status"].isna() | (df["document_status"] == "Missing")).astype(int)

# Stale record (last_updated too old — more than 90 days before reporting month)
# Exclude rows already caught by date_invalid to avoid double-counting
df["exc_stale_record"] = (
    (~df["exc_date_invalid"].astype(bool)) &
    ((df["reporting_date"] - df["last_updated_at"]).dt.days > 90)
).fillna(False).astype(int)

# Outlier balance
df["exc_outlier_balance"] = (df["balance_ratio"] > 3).astype(int)

# Composite exception type
def get_exception_type(row):
    if row["exc_missing_doc"]:
        return "missing_doc"
    if row["exc_balance_mismatch"]:
        return "balance_mismatch"
    if row["exc_status_conflict"]:
        return "status_conflict"
    if row["exc_date_invalid"]:
        return "date_invalid"
    if row["exc_stale_record"]:
        return "stale_record"
    if row["exc_outlier_balance"]:
        return "outlier_balance"
    return "none"

df["exception_type"] = df.apply(get_exception_type, axis=1)
df["is_anomaly"] = (df["exception_type"] != "none").astype(int)

print(f"  Labeled anomalies: {df['is_anomaly'].sum():,} / {len(df):,} ({df['is_anomaly'].mean():.2%})")
print(f"  Exception types: {df[df['is_anomaly']==1]['exception_type'].value_counts().to_dict()}")

# ── Features for anomaly detection ───────────────────────────────────────
anomaly_features = [
    "credit_num", "ltv_num", "dti_num", "status_num",
    "balance_ratio", "days_past_due", "interest_rate",
    "loan_age_months", "remaining_term_months", "modification_flag"
]

X = df[anomaly_features].fillna(0).values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ── IsolationForest ─────────────────────────────────────────────────────
print("  Training IsolationForest …")
iso = IsolationForest(
    n_estimators=200, contamination=0.05,
    max_features=0.8, random_state=42, n_jobs=-1
)
iso.fit(X_scaled)
iso_scores = -iso.decision_function(X_scaled)  # Higher = more anomalous
iso_scores_norm = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-8)

# ── PyTorch Autoencoder ─────────────────────────────────────────────────
print("  Training autoencoder …")
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    class Autoencoder(nn.Module):
        def __init__(self, input_dim):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 16), nn.ReLU(),
                nn.Linear(16, 8), nn.ReLU(),
                nn.Linear(8, 4), nn.ReLU(),
            )
            self.decoder = nn.Sequential(
                nn.Linear(4, 8), nn.ReLU(),
                nn.Linear(8, 16), nn.ReLU(),
                nn.Linear(16, input_dim),
            )
        def forward(self, x):
            return self.decoder(self.encoder(x))

    input_dim = X_scaled.shape[1]
    ae_model = Autoencoder(input_dim)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(ae_model.parameters(), lr=0.001)

    dataset = TensorDataset(torch.FloatTensor(X_scaled))
    loader = DataLoader(dataset, batch_size=512, shuffle=True)

    ae_model.train()
    for epoch in range(20):
        total_loss = 0
        for (batch,) in loader:
            optimizer.zero_grad()
            reconstructed = ae_model(batch)
            loss = criterion(reconstructed, batch)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

    ae_model.eval()
    with torch.no_grad():
        X_tensor = torch.FloatTensor(X_scaled)
        recon = ae_model(X_tensor).numpy()
        ae_errors = np.mean((X_scaled - recon) ** 2, axis=1)
        ae_scores_norm = (ae_errors - ae_errors.min()) / (ae_errors.max() - ae_errors.min() + 1e-8)

    torch.save(ae_model.state_dict(), str(ARTIFACTS / "autoencoder.pt"))
    USE_AE = True
    print(f"    Autoencoder trained (final loss: {total_loss/len(loader):.4f})")
except Exception as e:
    print(f"  ⚠ Autoencoder skipped: {e}")
    ae_scores_norm = np.zeros(len(X_scaled))
    USE_AE = False

# ── Blended anomaly score ───────────────────────────────────────────────
blend_weight_iso = 0.6
blend_weight_ae = 0.4 if USE_AE else 0.0
blend_weight_iso = 1.0 - blend_weight_ae

blended = blend_weight_iso * iso_scores_norm + blend_weight_ae * ae_scores_norm
df["anomaly_score"] = blended

# ── Exception Type Classifier (LightGBM multiclass) ─────────────────────
print("  Training exception-type classifier …")
import lightgbm as lgb

exc_types = ["missing_doc", "balance_mismatch", "status_conflict", "stale_record", "date_invalid", "outlier_balance", "none"]
exc_map = {t: i for i, t in enumerate(exc_types)}
df["exc_label"] = df["exception_type"].map(exc_map)

X_exc = df[anomaly_features].fillna(0).values
y_exc = df["exc_label"].values

exc_train = lgb.Dataset(X_exc, label=y_exc)
exc_params = {
    "objective": "multiclass",
    "num_class": len(exc_types),
    "metric": "multi_logloss",
    "learning_rate": 0.05,
    "num_leaves": 31,
    "verbose": -1,
    "seed": 42,
}
exc_model = lgb.train(exc_params, exc_train, num_boost_round=200)
exc_model.save_model(str(ARTIFACTS / "exception_classifier.txt"))

# ── Save models ─────────────────────────────────────────────────────────
joblib.dump(iso, ARTIFACTS / "isolation_forest.joblib")
joblib.dump(scaler, ARTIFACTS / "anomaly_scaler.joblib")

anomaly_config = {
    "features": anomaly_features,
    "exception_types": exc_types,
    "blend_weights": {"isolation_forest": blend_weight_iso, "autoencoder": blend_weight_ae},
    "use_autoencoder": USE_AE,
    "autoencoder_input_dim": int(X_scaled.shape[1]),
}
with open(ARTIFACTS / "anomaly_config.json", "w") as f:
    json.dump(anomaly_config, f, indent=2)

# ── Generate curated anomaly examples ────────────────────────────────────
print("  Generating reviewer-ready anomaly examples …")
anomalies = df[df["is_anomaly"] == 1].nlargest(30, "anomaly_score")

examples = []
for _, row in anomalies.head(25).iterrows():
    drivers = []
    if row.get("exc_balance_mismatch"):
        drivers.append(f"Balance is {row['current_balance']:.0f} but status is {row['current_status']}")
    if row.get("exc_status_conflict"):
        drivers.append(f"Status is Current but DPD={row['days_past_due']}")
    if row.get("exc_date_invalid"):
        drivers.append("Last updated date is before origination")
    if row.get("exc_missing_doc"):
        drivers.append("Document status is missing or incomplete")
    if row.get("exc_stale_record"):
        drivers.append("Record not updated in >90 days")
    if row.get("exc_outlier_balance"):
        drivers.append(f"Balance ratio {row['balance_ratio']:.1f}x is an outlier")

    examples.append({
        "loan_id": row["loan_id"],
        "month_index": int(row["month_index"]),
        "anomaly_score": round(float(row["anomaly_score"]), 4),
        "exception_type": row["exception_type"],
        "current_status": row["current_status"],
        "current_balance": round(float(row["current_balance"]), 2) if pd.notna(row["current_balance"]) else None,
        "days_past_due": int(row["days_past_due"]),
        "drivers": drivers,
        "recommended_action": "Review and reconcile" if row["exception_type"] in ["balance_mismatch", "status_conflict"]
                              else "Request updated documentation" if row["exception_type"] == "missing_doc"
                              else "Validate date records" if row["exception_type"] == "date_invalid"
                              else "Follow up with servicer",
    })

with open(REPORTS / "anomaly_examples.json", "w") as f:
    json.dump(examples, f, indent=2, default=str)

# Save anomaly scores for all records (for API)
df[["loan_id", "month_index", "anomaly_score", "exception_type", "is_anomaly"]].to_csv(
    PROC / "anomaly_scores.csv", index=False
)

print(f"\n✓ IsolationForest + Autoencoder ensemble saved")
print(f"✓ Exception classifier saved")
print(f"✓ {len(examples)} anomaly examples: reports/anomaly_examples.json")
