#!/usr/bin/env python3
"""
04_train_prediction_models.py
==============================
Task 2 — Prediction: LightGBM (primary) + Logistic Regression (baseline)
for delinquency, default, prepayment, and next-state prediction.
Time-aware split, class imbalance handling, calibration, MLflow logging.
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))

import json, warnings, os
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (roc_auc_score, average_precision_score, f1_score,
                             brier_score_loss, classification_report, precision_recall_curve)
from sklearn.preprocessing import LabelEncoder
import lightgbm as lgb
import joblib
from backend.app.services.model_service import LGBMWrapper

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# MLflow setup
try:
    import mlflow
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", str(ROOT / "mlruns")))
    mlflow.set_experiment("loan_prediction")
    USE_MLFLOW = True
except Exception:
    USE_MLFLOW = False

print("▸ Loading features …")
df = pd.read_csv(PROC / "features.csv")
feature_names = json.loads((PROC / "feature_names.json").read_text())

# ── Time-aware split (widened for rare-event targets) ────────────────────
train_mask = df["month_index"] <= 24
val_mask = (df["month_index"] > 24) & (df["month_index"] <= 30)    # 6 months
test_mask = df["month_index"] > 30                                 # months 31-42 (12 months)

print(f"  Train: {train_mask.sum():,} | Val: {val_mask.sum():,} | Test: {test_mask.sum():,}")

# ── Binary targets ───────────────────────────────────────────────────────
TARGETS = {
    "delinq_3m": "next_3m_delinquency_flag",
    "delinq_6m": "next_6m_delinquency_flag",
    "default_12m": "next_12m_default_flag",
    "prepay_12m": "next_12m_prepayment_flag",
}

results = {}
all_metrics = {}

for target_name, target_col in TARGETS.items():
    print(f"\n{'─'*60}")
    print(f"  Training: {target_name} ({target_col})")
    print(f"{'─'*60}")

    obs_col = f"{target_name}_observable"
    has_obs = obs_col in df.columns
    
    t_train_mask = train_mask & (df[obs_col] == 1) if has_obs else train_mask
    t_val_mask = val_mask & (df[obs_col] == 1) if has_obs else val_mask
    t_test_mask = test_mask & (df[obs_col] == 1) if has_obs else test_mask

    X_train_t = df.loc[t_train_mask, feature_names].values
    y_train = df.loc[t_train_mask, target_col].values.astype(int)
    
    X_val_t = df.loc[t_val_mask, feature_names].values
    y_val = df.loc[t_val_mask, target_col].values.astype(int)
    
    X_test_t = df.loc[t_test_mask, feature_names].values
    y_test = df.loc[t_test_mask, target_col].values.astype(int)

    print(f"  Observable: Train={len(y_train):,} | Val={len(y_val):,} | Test={len(y_test):,}")
    print(f"  Positive counts: Train={int(y_train.sum())} | Val={int(y_val.sum())} | Test={int(y_test.sum())}")

    # Statistical reliability warning
    MIN_POS_FOR_RELIABLE_AUC = 30
    for split_name, y_split in [("val", y_val), ("test", y_test)]:
        if y_split.sum() < MIN_POS_FOR_RELIABLE_AUC:
            print(f"  ⚠ WARNING: {split_name} has only {int(y_split.sum())} positives — AUC/F1 may be statistically unreliable")

    # Skip if insufficient positive samples
    if y_train.sum() < 10:
        print(f"  ⚠ Skipping {target_name}: only {y_train.sum()} positives in training")
        continue

    pos_rate = y_train.mean()
    scale_pos = (1 - pos_rate) / max(pos_rate, 0.001)
    print(f"  Positive rate: {pos_rate:.4f} | scale_pos_weight: {scale_pos:.2f}")

    # ── Baseline: Logistic Regression ────────────────────────────────────
    lr = LogisticRegression(
        max_iter=1000, class_weight="balanced", solver="lbfgs", random_state=42
    )
    lr.fit(X_train_t, y_train)
    lr_proba_val = lr.predict_proba(X_val_t)[:, 1]
    lr_proba_test = lr.predict_proba(X_test_t)[:, 1]

    lr_auc = roc_auc_score(y_val, lr_proba_val) if y_val.sum() > 0 else 0
    lr_prauc = average_precision_score(y_val, lr_proba_val) if y_val.sum() > 0 else 0
    print(f"  LR — Val AUC: {lr_auc:.4f} | PR-AUC: {lr_prauc:.4f}")

    # ── Primary: LightGBM ────────────────────────────────────────────────
    lgb_train = lgb.Dataset(X_train_t, label=y_train)
    lgb_val_ds = lgb.Dataset(X_val_t, label=y_val, reference=lgb_train)

    params = {
        "objective": "binary",
        "metric": "auc",
        "scale_pos_weight": scale_pos,
        "learning_rate": 0.05,
        "num_leaves": 63,
        "max_depth": 7,
        "min_child_samples": 50,
        "feature_fraction": 0.8,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }

    gbm = lgb.train(
        params, lgb_train,
        num_boost_round=500,
        valid_sets=[lgb_val_ds],
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
    )

    gbm_proba_val = gbm.predict(X_val_t)
    gbm_proba_test = gbm.predict(X_test_t)

    gbm_auc = roc_auc_score(y_val, gbm_proba_val) if y_val.sum() > 0 else 0
    gbm_prauc = average_precision_score(y_val, gbm_proba_val) if y_val.sum() > 0 else 0

    try:
        from sklearn.frozen import FrozenEstimator
        HAS_FROZEN = True
    except ImportError:
        HAS_FROZEN = False

    wrapper = LGBMWrapper(gbm)
    if HAS_FROZEN:
        cal = CalibratedClassifierCV(FrozenEstimator(wrapper), method="isotonic")
    else:
        cal = CalibratedClassifierCV(wrapper, method="isotonic", cv="prefit")
    cal.fit(X_val_t, y_val)
    cal_proba_test = cal.predict_proba(X_test_t)[:, 1]

    cal_auc = roc_auc_score(y_test, cal_proba_test) if y_test.sum() > 0 else gbm_auc
    brier = brier_score_loss(y_test, cal_proba_test) if y_test.sum() > 0 else 0

    # Optimal threshold via F1
    if y_val.sum() > 0:
        prec, rec, thresholds = precision_recall_curve(y_val, gbm_proba_val)
        f1_scores = 2 * prec * rec / (prec + rec + 1e-8)
        best_idx = np.argmax(f1_scores)
        best_threshold = float(thresholds[min(best_idx, len(thresholds)-1)])
    else:
        best_threshold = 0.5

    preds = (cal_proba_test > best_threshold).astype(int)
    f1 = f1_score(y_test, preds) if y_test.sum() > 0 else 0

    metrics = {
        "lr_val_auc": round(lr_auc, 4),
        "lr_val_prauc": round(lr_prauc, 4),
        "lgbm_val_auc": round(gbm_auc, 4),
        "lgbm_val_prauc": round(gbm_prauc, 4),
        "lgbm_test_auc_calibrated": round(cal_auc, 4),
        "brier_score": round(brier, 4),
        "f1_score": round(f1, 4),
        "best_threshold": round(best_threshold, 4),
        "positive_rate_train": round(float(pos_rate), 4),
        "positive_count_train": int(y_train.sum()),
        "positive_count_val": int(y_val.sum()),
        "positive_count_test": int(y_test.sum()),
        "sample_reliable": bool(y_val.sum() >= MIN_POS_FOR_RELIABLE_AUC and y_test.sum() >= MIN_POS_FOR_RELIABLE_AUC),
    }
    all_metrics[target_name] = metrics
    print(f"  LGBM — Val AUC: {gbm_auc:.4f} | Cal Test AUC: {cal_auc:.4f} | F1: {f1:.4f} | Brier: {brier:.4f}")

    # Save models
    joblib.dump(cal, ARTIFACTS / f"lgbm_{target_name}_calibrated.joblib")
    joblib.dump(lr, ARTIFACTS / f"lr_{target_name}.joblib")
    gbm.save_model(str(ARTIFACTS / f"lgbm_{target_name}.txt"))

    # Feature importance
    importance = gbm.feature_importance(importance_type="gain")
    feat_imp = sorted(zip(feature_names, importance), key=lambda x: -x[1])[:15]
    results[target_name] = {
        "metrics": metrics,
        "top_features": [{"feature": f, "importance": round(float(v), 2)} for f, v in feat_imp],
        "threshold": best_threshold,
    }

    # MLflow logging
    if USE_MLFLOW:
        with mlflow.start_run(run_name=f"{target_name}_lgbm"):
            mlflow.log_params(params)
            mlflow.log_metrics({k: v for k, v in metrics.items() if isinstance(v, (int, float))})

# ── Multiclass next-state model ──────────────────────────────────────────
print(f"\n{'─'*60}")
print(f"  Training: next_state (multiclass)")
print(f"{'─'*60}")

mc_obs = (df["next_status_observable"] == 1) if "next_status_observable" in df.columns else np.ones(len(df), dtype=bool)
mc_train_mask = train_mask & mc_obs
mc_val_mask = val_mask & mc_obs

X_train_mc = df.loc[mc_train_mask, feature_names].values
y_train_mc = df.loc[mc_train_mask, "next_status"].fillna(0).astype(int).values

X_val_mc = df.loc[mc_val_mask, feature_names].values
y_val_mc = df.loc[mc_val_mask, "next_status"].fillna(0).astype(int).values

lgb_mc_train = lgb.Dataset(X_train_mc, label=y_train_mc)
lgb_mc_val = lgb.Dataset(X_val_mc, label=y_val_mc, reference=lgb_mc_train)

n_classes = len(np.unique(y_train_mc))
mc_params = {
    "objective": "multiclass",
    "num_class": max(n_classes, 7),
    "metric": "multi_logloss",
    "learning_rate": 0.05,
    "num_leaves": 63,
    "max_depth": 7,
    "verbose": -1,
    "seed": 42,
}

mc_gbm = lgb.train(
    mc_params, lgb_mc_train,
    num_boost_round=300,
    valid_sets=[lgb_mc_val],
    callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)],
)

mc_proba = mc_gbm.predict(X_val_mc)
mc_preds = mc_proba.argmax(axis=1)
mc_f1 = f1_score(y_val_mc, mc_preds, average="macro")

mc_gbm.save_model(str(ARTIFACTS / "lgbm_next_state.txt"))
results["next_state"] = {
    "metrics": {"macro_f1": round(mc_f1, 4), "n_classes": int(n_classes)},
    "top_features": [],
}
print(f"  Multiclass macro-F1: {mc_f1:.4f}")

# ── Save all results ─────────────────────────────────────────────────────
with open(PROC / "prediction_results.json", "w") as f:
    json.dump(results, f, indent=2, default=str)

# Save feature names and thresholds for the API
with open(ARTIFACTS / "model_config.json", "w") as f:
    json.dump({
        "feature_names": feature_names,
        "targets": {k: v.get("threshold", 0.5) for k, v in results.items()},
        "metrics": all_metrics,
    }, f, indent=2, default=str)

# ── Model Card ───────────────────────────────────────────────────────────
card = f"""# Model Card — Loan Performance Prediction

*Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}*

## Model Overview
- **Primary model**: LightGBM (gradient boosted trees)
- **Baseline model**: Logistic Regression (balanced class weights)
- **Calibration**: Isotonic regression via CalibratedClassifierCV
- **Split strategy**: Time-aware (train ≤ month 24, val 25-30, test 31-42)
- **Observability**: Only rows with fully observable forward horizons are used for training and evaluation

## Targets & Sample Sizes
| Target | Pos Rate (Train) | Train Pos | Val Pos | Test Pos | Reliable? |
|---|---|---|---|---|---|
"""
for tname, tres in results.items():
    m = tres.get("metrics", {})
    if "positive_rate_train" in m:
        reliable = "✓" if m.get("sample_reliable", False) else "⚠ LOW"
        card += f"| {tname} | {m['positive_rate_train']:.4f} | {m.get('positive_count_train', '-')} | {m.get('positive_count_val', '-')} | {m.get('positive_count_test', '-')} | {reliable} |\n"

card += """
## Performance (LightGBM, calibrated)
| Target | Val AUC | Test AUC | Brier | F1 | Reliable? |
|---|---|---|---|---|---|
"""
for tname, tres in results.items():
    m = tres.get("metrics", {})
    if "lgbm_val_auc" in m:
        reliable = "✓" if m.get("sample_reliable", False) else "⚠ LOW SAMPLE"
        card += f"| {tname} | {m.get('lgbm_val_auc', '-')} | {m.get('lgbm_test_auc_calibrated', '-')} | {m.get('brier_score', '-')} | {m.get('f1_score', '-')} | {reliable} |\n"

card += """
> **Note**: Metrics marked "⚠ LOW SAMPLE" have fewer than 30 positive examples in val or test and
> should be treated as statistically unreliable. Consider widening the evaluation window or
> increasing the data generation period for these targets.

## Top Features (by LightGBM gain)
"""
for tname, tres in results.items():
    if tres.get("top_features"):
        card += f"\n### {tname}\n"
        for feat in tres["top_features"][:10]:
            card += f"- {feat['feature']}: {feat['importance']}\n"

card += """
## Limitations
- Trained on synthetic data; real-world performance will differ
- Class imbalance addressed via scale_pos_weight and threshold tuning
- Calibration assumes validation distribution ≈ deployment distribution
- Rare-event targets (e.g., 12-month default) may have unstable metrics due to low positive counts

## Ethical Considerations
- Model outputs are recommendations, not decisions
- No protected class features used directly (but proxy effects possible via geography/LTV)
- All predictions include confidence scores and explanations
"""

(REPORTS / "model_card.md").write_text(card)

print(f"\n✓ All models saved to backend/app/artifacts/")
print(f"✓ Model card: reports/model_card.md")
print(f"✓ Results: data/processed/prediction_results.json")
