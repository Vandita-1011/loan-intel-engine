"""
test_pipeline_and_api.py
========================
Smoke tests for data shapes, no-leakage verification, and API endpoint integration.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

import json
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"


def test_data_generation_shapes():
    """Verify generated dataset presence and required dimensions."""
    static_file = RAW / "loan_static_attributes.csv"
    train_file = RAW / "loan_monthly_performance_train.csv"
    test_file = RAW / "loan_monthly_performance_test.csv"
    
    assert static_file.exists(), "loan_static_attributes.csv missing"
    assert train_file.exists(), "loan_monthly_performance_train.csv missing"
    assert test_file.exists(), "loan_monthly_performance_test.csv missing"
    
    static_df = pd.read_csv(static_file)
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)
    
    assert len(static_df) == 15000, f"Expected 15000 static loans, got {len(static_df)}"
    assert len(train_df) > 300000, f"Expected >300k train rows, got {len(train_df)}"
    assert len(test_df) > 50000, f"Expected >50k test rows, got {len(test_df)}"
    
    # Check key columns
    assert "loan_id" in static_df.columns
    assert "credit_score_band" in static_df.columns
    assert "current_balance" in train_df.columns
    assert "days_past_due" in train_df.columns


def test_no_leakage_feature_design():
    """Verify feature names do not include forward targets or post-outcome flags."""
    feature_names_file = PROC / "feature_names.json"
    assert feature_names_file.exists(), "feature_names.json missing"
    
    feature_names = json.loads(feature_names_file.read_text())
    
    forbidden_targets = [
        "next_3m_delinquency_flag",
        "next_6m_delinquency_flag",
        "next_12m_default_flag",
        "next_12m_prepayment_flag",
        "next_status",
        "default_flag",
        "prepayment_flag",
        "loss_severity_band",
    ]
    
    for forbidden in forbidden_targets:
        assert forbidden not in feature_names, f"Target leakage detected: {forbidden} in feature set!"


def test_api_health_and_endpoints():
    """Verify FastAPI backend health check and primary endpoints."""
    with TestClient(app) as client:
        # 1. Health check
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["models_loaded"] >= 4
        
        # 2. Anomalies endpoint
        resp_anom = client.get("/anomalies/?limit=10")
        assert resp_anom.status_code == 200
        anoms = resp_anom.json().get("anomalies", [])
        assert len(anoms) > 0
        
        # 3. Prediction endpoint
        sample_loan = "LN000000"
        resp_pred = client.get(f"/predictions/{sample_loan}")
        assert resp_pred.status_code == 200
        pred = resp_pred.json()
        assert pred["loan_id"] == sample_loan
        assert "prob_delinquency_3m" in pred
        assert "predicted_next_state" in pred
        assert "confidence" in pred
        
        # 4. Scenarios endpoint
        resp_scen = client.get("/scenario/results")
        assert resp_scen.status_code == 200
        scens = resp_scen.json().get("scenarios", {})
        assert "base" in scens
        assert "adverse_credit" in scens
        assert "high_prepayment" in scens
        
        # 5. Explainability endpoint
        resp_exp = client.get(f"/explain/{sample_loan}")
        assert resp_exp.status_code == 200
        exp = resp_exp.json()
        assert exp["loan_id"] == sample_loan
        assert "shap_drivers" in exp
        
        # 6. Copilot endpoint
        resp_cop = client.post("/copilot/ask", json={
            "loan_id": sample_loan,
            "question": "What are the primary risk drivers for this loan?"
        })
        assert resp_cop.status_code == 200
        cop = resp_cop.json()
        assert cop["loan_id"] == sample_loan
        assert "RECOMMENDATION — NOT A DECISION" in cop["disclaimer"]
        assert len(cop["answer"]) > 0


def test_label_observability_integrity():
    """Verify that forward-looking targets have complete observability windows and are not censored."""
    features_file = PROC / "features.csv"
    assert features_file.exists(), "features.csv missing"
    
    df = pd.read_csv(features_file)
    
    # We test late train/val rows (months 25-30) and test rows (months 31-42)
    for target in ["delinq_3m", "delinq_6m", "default_12m", "prepay_12m"]:
        obs_col = f"{target}_observable"
        assert obs_col in df.columns, f"{obs_col} missing in features.csv"
        
        # In the modeling dataset (month_index <= 42), all targets must be 100% observable
        # because the underlying panel runs up to month 54.
        obs_rate = df[obs_col].mean()
        assert obs_rate == 1.0, f"Target {target} has unobservable/censored rows! Observability rate: {obs_rate:.4f}"

