# Data Intelligence Report

*Generated: 2026-08-31 11:25*

## Dataset Overview
| Metric | Value |
|---|---|
| Training rows | 379,139 |
| Test rows | 197,475 |
| Static attributes | 15,000 loans |
| Columns | 16 |

## Data Quality Score: **86.7/100**
- Completeness: 93.6%
- Validity: 79.8%

## Missingness
| Column | Missing % |
|---|---|
| loss_severity_band | 99.41% |
| document_status | 1.78% |
| current_balance | 0.99% |

## Outliers
| Column | IQR Outliers | Z-Score Outliers |
|---|---|---|
| current_balance | 19,711 | 5,260 |
| days_past_due | 48,129 | 13,478 |
| interest_rate | 0 | 0 |

## Cross-Field Contradictions
| Issue | Count |
|---|---|
| Prepaid with balance > 0 | 35 |
| Current with DPD > 0 | 5,052 |
| Invalid dates | 3,773 |

## Status Distribution (Training)
| Status | Proportion |
|---|---|
| Current | 87.86% |
| 30DPD | 6.22% |
| 60DPD | 2.92% |
| 90DPD+ | 1.63% |
| Prepaid | 0.78% |
| Default | 0.59% |

## Train vs Test Drift
| Feature | PSI | KS Statistic | KS p-value |
|---|---|---|---|
| current_balance | 0.0000 | 0.0394 | 0.000000 |
| interest_rate | 0.0004 | 0.0087 | 0.000000 |
| days_past_due | 0.0046 | 0.0206 | 0.000000 |
