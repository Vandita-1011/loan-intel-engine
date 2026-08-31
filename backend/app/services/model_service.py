"""
model_service.py
=================
Loads and serves all trained ML artifacts. Provides prediction, anomaly scoring,
and explainability lookup for the API layer.
"""

import json, logging
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

# Paths — resolve relative to this file's location
_APP = Path(__file__).resolve().parent.parent
_ARTIFACTS = _APP / "artifacts"
_ROOT = _APP.parent.parent
_RAW = _ROOT / "data" / "raw"
_PROC = _ROOT / "data" / "processed"


from sklearn.base import BaseEstimator, ClassifierMixin

class LGBMWrapper(BaseEstimator, ClassifierMixin):
    """Wrapper to make LightGBM Booster compatible with CalibratedClassifierCV."""
    def __init__(self, booster=None):
        self.booster = booster
        self.classes_ = np.array([0, 1])
    def fit(self, X, y):
        return self
    def predict_proba(self, X):
        p = self.booster.predict(X)
        return np.column_stack([1 - p, p])
    def predict(self, X):
        return (self.booster.predict(X) > 0.5).astype(int)
    def decision_function(self, X):
        return self.booster.predict(X)


class ModelService:
    """Centralized model loading and inference service."""

    def __init__(self):
        self.models = {}
        self.config = {}
        self.feature_names = []
        self.static_df = None
        self.performance_df = None
        self.features_df = None
        self.anomaly_df = None
        self.shap_values = {}
        self.transition_matrix = None
        self.scenario_results = None
        self.explainability = None
        self.anomaly_examples = []
        self._loaded = False

    def load(self):
        """Load all artifacts with graceful fallbacks."""
        logger.info("Loading model artifacts …")

        # ── Config ─────────────────────────────────────────────────────
        config_path = _ARTIFACTS / "model_config.json"
        if config_path.exists():
            self.config = json.loads(config_path.read_text())
            self.feature_names = self.config.get("feature_names", [])

        # ── Calibrated prediction models ───────────────────────────────
        for target in ["delinq_3m", "delinq_6m", "default_12m", "prepay_12m"]:
            path = _ARTIFACTS / f"lgbm_{target}_calibrated.joblib"
            if path.exists():
                try:
                    self.models[target] = joblib.load(path)
                    logger.info(f"  ✓ Loaded {target}")
                except Exception as e:
                    logger.warning(f"  ✗ Failed to load {target}: {e}")

        # ── Multiclass model ──────────────────────────────────────────
        mc_path = _ARTIFACTS / "lgbm_next_state.txt"
        if mc_path.exists():
            try:
                import lightgbm as lgb
                self.models["next_state"] = lgb.Booster(model_file=str(mc_path))
                logger.info("  ✓ Loaded next_state model")
            except Exception as e:
                logger.warning(f"  ✗ Failed to load next_state: {e}")

        # ── Anomaly models ────────────────────────────────────────────
        iso_path = _ARTIFACTS / "isolation_forest.joblib"
        if iso_path.exists():
            try:
                self.models["isolation_forest"] = joblib.load(iso_path)
                self.models["anomaly_scaler"] = joblib.load(_ARTIFACTS / "anomaly_scaler.joblib")
                logger.info("  ✓ Loaded anomaly models")
            except Exception as e:
                logger.warning(f"  ✗ Failed to load anomaly models: {e}")

        # ── Data files ────────────────────────────────────────────────
        try:
            if (_RAW / "loan_static_attributes.csv").exists():
                self.static_df = pd.read_csv(_RAW / "loan_static_attributes.csv")
            if (_RAW / "loan_monthly_performance_train.csv").exists():
                self.performance_df = pd.read_csv(_RAW / "loan_monthly_performance_train.csv")
            if (_PROC / "features.csv").exists():
                self.features_df = pd.read_csv(_PROC / "features.csv")
            if (_PROC / "anomaly_scores.csv").exists():
                self.anomaly_df = pd.read_csv(_PROC / "anomaly_scores.csv")
        except Exception as e:
            logger.warning(f"  ✗ Data loading issue: {e}")

        # ── JSON artifacts ────────────────────────────────────────────
        for name, path in [
            ("shap_values", _ARTIFACTS / "shap_values.json"),
            ("transition_matrix", _ARTIFACTS / "transition_matrix.json"),
            ("scenario_results", _ARTIFACTS / "scenario_results.json"),
            ("explainability", _ARTIFACTS / "explainability_results.json"),
        ]:
            if path.exists():
                data = json.loads(path.read_text())
                setattr(self, name, data)

        # Anomaly examples
        ae_path = _ROOT / "reports" / "anomaly_examples.json"
        if ae_path.exists():
            self.anomaly_examples = json.loads(ae_path.read_text())

        self._loaded = True
        logger.info(f"  Models loaded: {len(self.models)}")

    def get_loan(self, loan_id: str) -> Optional[dict]:
        """Get static + latest performance data for a loan."""
        if self.static_df is None:
            return None
        row = self.static_df[self.static_df["loan_id"] == loan_id]
        if row.empty:
            return None
        result = row.iloc[0].to_dict()

        if self.performance_df is not None:
            perf = self.performance_df[self.performance_df["loan_id"] == loan_id]
            if not perf.empty:
                latest = perf.sort_values("month_index").iloc[-1]
                result["latest_performance"] = latest.to_dict()

        return result

    def predict(self, loan_id: str) -> dict:
        """Run predictions for a single loan."""
        result = {
            "loan_id": loan_id,
            "prob_delinquency_3m": 0.0,
            "prob_delinquency_6m": 0.0,
            "prob_default_12m": 0.0,
            "prob_prepayment_12m": 0.0,
            "predicted_next_state": "Current",
            "confidence": 0.5,
            "top_drivers": [],
        }

        if self.features_df is None or not self.feature_names:
            return result

        loan_rows = self.features_df[self.features_df["loan_id"] == loan_id]
        if loan_rows.empty:
            return result

        latest = loan_rows.sort_values("month_index").iloc[-1]
        X = latest[self.feature_names].fillna(0).values.reshape(1, -1)

        status_labels = {0: "Current", 1: "30DPD", 2: "60DPD", 3: "90DPD+",
                         4: "Default", 5: "Prepaid", 6: "Closed"}

        for target_key, result_key in [
            ("delinq_3m", "prob_delinquency_3m"),
            ("delinq_6m", "prob_delinquency_6m"),
            ("default_12m", "prob_default_12m"),
            ("prepay_12m", "prob_prepayment_12m"),
        ]:
            if target_key in self.models:
                try:
                    p = self.models[target_key].predict_proba(X)[0, 1]
                    result[result_key] = round(float(p), 4)
                except Exception:
                    pass

        if "next_state" in self.models:
            try:
                proba = self.models["next_state"].predict(X)[0]
                result["predicted_next_state"] = status_labels.get(int(proba.argmax()), "Current")
                result["confidence"] = round(float(proba.max()), 4)
            except Exception:
                pass

        # SHAP drivers
        if loan_id in self.shap_values:
            sv = self.shap_values[loan_id]
            top = sorted(sv.items(), key=lambda x: -abs(x[1]))[:5]
            result["top_drivers"] = [{"feature": f, "shap_value": v} for f, v in top]

        return result

    def get_anomalies(self, limit: int = 20) -> list[dict]:
        """Get top anomalies."""
        if self.anomaly_examples:
            return self.anomaly_examples[:limit]
        if self.anomaly_df is not None:
            top = self.anomaly_df.nlargest(limit, "anomaly_score")
            return top.to_dict(orient="records")
        return []

    def get_explanation(self, loan_id: str) -> dict:
        """Get SHAP explanation for a loan."""
        result = {"loan_id": loan_id, "shap_drivers": [], "base_value": 0.0, "prediction": 0.0}

        if loan_id in self.shap_values:
            sv = self.shap_values[loan_id]
            top = sorted(sv.items(), key=lambda x: -abs(x[1]))[:10]
            result["shap_drivers"] = [{"feature": f, "shap_value": v} for f, v in top]

        if self.explainability:
            result["base_value"] = self.explainability.get("shap_base_value", 0.0)
            for le in self.explainability.get("local_explanations", []):
                if le["loan_id"] == loan_id:
                    result["prediction"] = le["prediction"]
                    break

        pred = self.predict(loan_id)
        result["prediction"] = pred.get("prob_delinquency_3m", 0.0)

        p = result["prediction"]
        if p < 0.2 or p > 0.8:
            result["confidence_band"] = "high"
        elif p < 0.4 or p > 0.6:
            result["confidence_band"] = "medium"
        else:
            result["confidence_band"] = "low"

        return result

    @property
    def models_count(self) -> int:
        return len(self.models)


# Singleton
model_service = ModelService()
