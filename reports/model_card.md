# Model Card — Loan Performance Prediction

*Generated: 2026-08-31 01:10*

## Model Overview
- **Primary model**: LightGBM (gradient boosted trees)
- **Baseline model**: Logistic Regression (balanced class weights)
- **Calibration**: Isotonic regression via CalibratedClassifierCV
- **Split strategy**: Time-aware (train ≤ month 24, val 25-30, test 31-42)
- **Observability**: Only rows with fully observable forward horizons are used for training and evaluation

## Targets & Sample Sizes
| Target | Pos Rate (Train) | Train Pos | Val Pos | Test Pos | Reliable? |
|---|---|---|---|---|---|
| delinq_3m | 0.2079 | 65017 | 14455 | 24796 | ✓ |
| delinq_6m | 0.3131 | 97910 | 21228 | 36137 | ✓ |
| default_12m | 0.0816 | 25504 | 6515 | 11073 | ✓ |
| prepay_12m | 0.0894 | 27944 | 4095 | 7275 | ✓ |

## Performance (LightGBM, calibrated)
| Target | Val AUC | Test AUC | Brier | F1 | Reliable? |
|---|---|---|---|---|---|
| delinq_3m | 0.7438 | 0.7341 | 0.125 | 0.5955 | ✓ |
| delinq_6m | 0.6972 | 0.6756 | 0.185 | 0.4785 | ✓ |
| default_12m | 0.8543 | 0.7917 | 0.0704 | 0.3191 | ✓ |
| prepay_12m | 0.7876 | 0.5492 | 0.0666 | 0.0323 | ✓ |

> **Note**: Metrics marked "⚠ LOW SAMPLE" have fewer than 30 positive examples in val or test and
> should be treated as statistically unreliable. Consider widening the evaluation window or
> increasing the data generation period for these targets.

## Top Features (by LightGBM gain)

### delinq_3m
- status_num: 911533.46
- is_delinquent: 72184.29
- rate_x_dti: 14045.63
- interest_rate: 12922.94
- credit_score_num: 12464.34
- rate_x_ltv: 9646.19
- original_balance: 8935.54
- loan_age_months: 7559.06
- balance_ratio: 6393.81
- balance_rolling_mean_3: 5209.82

### delinq_6m
- status_num: 481685.26
- is_delinquent: 40925.81
- rate_x_dti: 21143.9
- interest_rate: 19979.06
- rate_x_ltv: 17895.66
- credit_score_num: 15961.63
- original_balance: 15808.15
- loan_age_months: 8843.53
- balance_rolling_mean_3: 7708.93
- balance_ratio: 6910.78

### default_12m
- status_num: 1079559.76
- rate_x_dti: 310512.89
- interest_rate: 295367.4
- rate_x_ltv: 264020.38
- original_balance: 262643.45
- credit_score_num: 250055.56
- loan_age_months: 103340.71
- balance_rolling_mean_3: 95024.11
- credit_x_ltv: 94727.91
- remaining_term_months: 83997.56

### prepay_12m
- interest_rate: 396883.83
- rate_x_dti: 369322.54
- original_balance: 345256.92
- rate_x_ltv: 302424.25
- credit_x_ltv: 138716.52
- credit_score_num: 112650.56
- balance_rolling_mean_3: 111879.64
- remaining_term_months: 98645.99
- purpose_num: 88956.98
- property_num: 84431.49

## Limitations
- Trained on synthetic data; real-world performance will differ
- Class imbalance addressed via scale_pos_weight and threshold tuning
- Calibration assumes validation distribution ≈ deployment distribution
- Rare-event targets (e.g., 12-month default) may have unstable metrics due to low positive counts

## Ethical Considerations
- Model outputs are recommendations, not decisions
- No protected class features used directly (but proxy effects possible via geography/LTV)
- All predictions include confidence scores and explanations
