# Explainability Report

*Generated: 2026-08-31 01:12*

## Global Feature Importance (SHAP)
| Rank | Feature | Mean |SHAP| |
|---|---|---|
| 1 | status_num | 0.4735 |
| 2 | loan_age_months | 0.0882 |
| 3 | credit_score_num | 0.0782 |
| 4 | is_delinquent | 0.0780 |
| 5 | rate_x_dti | 0.0340 |
| 6 | original_balance | 0.0230 |
| 7 | remaining_term_months | 0.0220 |
| 8 | interest_rate | 0.0211 |
| 9 | dti_num | 0.0172 |
| 10 | days_past_due | 0.0163 |
| 11 | ltv_num | 0.0145 |
| 12 | balance_ratio | 0.0134 |
| 13 | rate_x_ltv | 0.0109 |
| 14 | current_balance | 0.0096 |
| 15 | balance_rolling_mean_3 | 0.0084 |

## Calibration
The model calibration curve shows the relationship between predicted probabilities
and actual outcomes. Values are based on 31,353 validation samples.

## False Positive Analysis
5 cases where the model predicted delinquency but the loan stayed current:

- **LN010162**: Model predicted delinquency (p=0.877) but loan stayed current. Key drivers: status_num, is_delinquent, days_past_due.

- **LN008061**: Model predicted delinquency (p=0.560) but loan stayed current. Key drivers: loan_age_months, status_num, rate_x_dti.

- **LN005713**: Model predicted delinquency (p=0.885) but loan stayed current. Key drivers: status_num, is_delinquent, credit_score_num.

- **LN010858**: Model predicted delinquency (p=0.874) but loan stayed current. Key drivers: status_num, is_delinquent, loan_age_months.

- **LN006187**: Model predicted delinquency (p=0.873) but loan stayed current. Key drivers: status_num, is_delinquent, loan_age_months.

## False Negative Analysis
5 cases where the model missed actual delinquency:

- **LN012339**: Model missed delinquency (p=0.425). Potential blind spots: status_num, credit_score_num, loan_age_months.

- **LN011055**: Model missed delinquency (p=0.431). Potential blind spots: status_num, credit_score_num, loan_age_months.

- **LN009718**: Model missed delinquency (p=0.411). Potential blind spots: status_num, loan_age_months, interest_rate.

- **LN011379**: Model missed delinquency (p=0.363). Potential blind spots: status_num, rate_x_dti, credit_score_num.

- **LN009096**: Model missed delinquency (p=0.423). Potential blind spots: status_num, loan_age_months, credit_score_num.

## Prediction Confidence Distribution
| Band | Count | % |
|---|---|---|
| high_confidence | 266 | 13.3% |
| medium_confidence | 1,204 | 60.2% |
| low_confidence | 530 | 26.5% |
