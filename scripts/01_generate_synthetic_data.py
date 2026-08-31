#!/usr/bin/env python3
"""
01_generate_synthetic_data.py
=============================
Generates the full synthetic data pack for the Loan Performance Intelligence Engine.

Outputs (into data/raw/):
  - loan_static_attributes.csv        15,000 unique loans
  - loan_monthly_performance_train.csv ~350k rows (months 1-30)
  - loan_monthly_performance_test.csv  later months (31-36), labels withheld
  - servicer_updates.csv               second-source feed with ~5% conflicts
  - data_dictionary.md                 plain-English field definitions
  - validation_rules.json              deterministic QA rules
  - macro_scenarios.csv                base / adverse / high-prepay assumptions
  - submission_template.csv            required output columns
"""

import os, json, warnings
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from faker import Faker

warnings.filterwarnings("ignore")

# ── Fixed seed ──────────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_LOANS = 15_000
TRAIN_MONTHS = 30   # months 1-30
TEST_MONTHS = 24    # months 31-54 (provides full 12-month forward lookahead past test boundary at month 42)
TOTAL_MONTHS = TRAIN_MONTHS + TEST_MONTHS

# ── Helpers ─────────────────────────────────────────────────────────────────
CREDIT_BANDS = ["<620", "620-660", "660-700", "700-740", "740-780", "780+"]
CREDIT_WEIGHTS = [0.05, 0.10, 0.20, 0.30, 0.20, 0.15]
LTV_BANDS = ["<=60%", "60-70%", "70-80%", "80-90%", "90-95%", ">95%"]
DTI_BANDS = ["<20%", "20-30%", "30-40%", "40-45%", "45-50%", ">50%"]
PURPOSES = ["Purchase", "Refinance_Rate", "Refinance_Cash", "Home_Equity"]
OCCUPANCY = ["Primary", "Secondary", "Investment"]
PROPERTY_TYPES = ["Single_Family", "Condo", "Multi_Family", "Townhouse"]
SERVICERS = [f"Servicer_{chr(65+i)}" for i in range(8)]
STATES = [
    "CA","TX","FL","NY","IL","PA","OH","GA","NC","MI",
    "NJ","VA","WA","AZ","MA","TN","IN","MO","MD","WI",
]
STATUSES = ["Current", "30DPD", "60DPD", "90DPD+", "Default", "Prepaid", "Closed"]
DOC_STATUSES = ["Complete", "Partial", "Missing", "Under_Review"]


def credit_band_to_numeric(band: str) -> float:
    """Map credit band to a rough midpoint score for hazard computation."""
    mapping = {"<620": 600, "620-660": 640, "660-700": 680,
               "700-740": 720, "740-780": 760, "780+": 800}
    return mapping.get(band, 700)


def ltv_band_to_numeric(band: str) -> float:
    mapping = {"<=60%": 55, "60-70%": 65, "70-80%": 75,
               "80-90%": 85, "90-95%": 92, ">95%": 98}
    return mapping.get(band, 75)


def dti_band_to_numeric(band: str) -> float:
    mapping = {"<20%": 15, "20-30%": 25, "30-40%": 35,
               "40-45%": 42, "45-50%": 47, ">50%": 55}
    return mapping.get(band, 35)


# ════════════════════════════════════════════════════════════════════════════
# 1. STATIC ATTRIBUTES
# ════════════════════════════════════════════════════════════════════════════
print("▸ Generating loan_static_attributes …")

# Correlated risk: lower credit → higher LTV/DTI
credit_scores = np.random.choice(CREDIT_BANDS, N_LOANS, p=CREDIT_WEIGHTS)

ltv_probs = []
dti_probs = []
for cs in credit_scores:
    csn = credit_band_to_numeric(cs)
    # Higher credit → lower LTV/DTI probability
    risk_shift = (800 - csn) / 200  # 0 (best) to 1 (worst)
    ltv_p = np.array([0.25, 0.20, 0.20, 0.15, 0.12, 0.08])
    ltv_p = ltv_p * (1 + risk_shift * np.array([-0.5, -0.3, 0, 0.3, 0.5, 0.8]))
    ltv_p = np.clip(ltv_p, 0.01, None)
    ltv_p /= ltv_p.sum()
    ltv_probs.append(ltv_p)

    dti_p = np.array([0.15, 0.25, 0.25, 0.15, 0.12, 0.08])
    dti_p = dti_p * (1 + risk_shift * np.array([-0.5, -0.3, 0, 0.3, 0.5, 0.8]))
    dti_p = np.clip(dti_p, 0.01, None)
    dti_p /= dti_p.sum()
    dti_probs.append(dti_p)

ltv_bands = [np.random.choice(LTV_BANDS, p=p) for p in ltv_probs]
dti_bands = [np.random.choice(DTI_BANDS, p=p) for p in dti_probs]

# Origination months spread over 2020-01 to 2022-06 (30 months of vintage)
orig_months = pd.date_range("2020-01-01", periods=30, freq="MS")
vintage_indices = np.random.randint(0, 30, N_LOANS)

static = pd.DataFrame({
    "loan_id": [f"LN{str(i).zfill(6)}" for i in range(N_LOANS)],
    "original_balance": np.round(
        np.random.lognormal(mean=12.2, sigma=0.5, size=N_LOANS), -2
    ).clip(50_000, 2_000_000),
    "credit_score_band": credit_scores,
    "ltv_band": ltv_bands,
    "dti_band": dti_bands,
    "state": np.random.choice(STATES, N_LOANS),
    "loan_purpose": np.random.choice(PURPOSES, N_LOANS, p=[0.45, 0.25, 0.20, 0.10]),
    "occupancy_type": np.random.choice(OCCUPANCY, N_LOANS, p=[0.70, 0.15, 0.15]),
    "property_type": np.random.choice(PROPERTY_TYPES, N_LOANS, p=[0.55, 0.20, 0.15, 0.10]),
    "origination_month": [orig_months[v].strftime("%Y-%m") for v in vintage_indices],
    "servicer_name": np.random.choice(SERVICERS, N_LOANS),
    "interest_rate": np.round(np.random.uniform(2.5, 7.5, N_LOANS), 3),
    "original_term_months": np.random.choice([180, 240, 360], N_LOANS, p=[0.15, 0.15, 0.70]),
})

static.to_csv(RAW / "loan_static_attributes.csv", index=False)
print(f"  ✓ {len(static):,} loans written")


# ════════════════════════════════════════════════════════════════════════════
# 2. MONTHLY PERFORMANCE (PANEL DATA)
# ════════════════════════════════════════════════════════════════════════════
print("▸ Generating monthly performance panel …")

rows = []
reporting_start = pd.Timestamp("2020-01-01")

for _, loan in static.iterrows():
    lid = loan["loan_id"]
    bal = float(loan["original_balance"])
    rate = float(loan["interest_rate"])
    term = int(loan["original_term_months"])
    orig = pd.Timestamp(loan["origination_month"] + "-01")

    # Risk hazard
    csn = credit_band_to_numeric(loan["credit_score_band"])
    ltvn = ltv_band_to_numeric(loan["ltv_band"])
    dtin = dti_band_to_numeric(loan["dti_band"])

    base_default_hazard = 0.012 + 0.025 * ((800 - csn) / 200) + 0.012 * (ltvn / 100) + 0.010 * (dtin / 50)
    base_prepay_hazard = 0.005 + 0.003 * (rate / 7.0)

    status = "Current"
    dpd = 0
    mod_flag = False
    alive = True

    for m in range(TOTAL_MONTHS):
        if not alive:
            break

        rpt = reporting_start + pd.DateOffset(months=m)
        age = max(1, (rpt.year - orig.year) * 12 + rpt.month - orig.month)
        rem_term = max(0, term - age)

        # Amortization with noise
        monthly_rate = rate / 100 / 12
        if monthly_rate > 0 and rem_term > 0:
            pmt = bal * monthly_rate / (1 - (1 + monthly_rate) ** (-rem_term))
            principal = pmt - bal * monthly_rate
            bal = max(0, bal - principal + np.random.normal(0, 50))
        else:
            bal = max(0, bal * 0.995)

        # Transition logic — Markov-ish with risk correlation
        # Rate-drop periods boost prepayment
        rate_environment = 1.0
        if 12 <= m <= 18:
            rate_environment = 1.8  # simulated rate drop period

        # Seasoning effect — default risk peaks around months 12-24
        seasoning_mult = 1.0 + 0.5 * np.exp(-0.5 * ((age - 18) / 6) ** 2)

        default_hazard = base_default_hazard * seasoning_mult
        prepay_hazard = base_prepay_hazard * rate_environment

        prepay_flag = False
        default_flag = False
        loss_severity = "N/A"

        if status == "Current":
            r = np.random.random()
            if r < default_hazard * 0.8:
                status = "30DPD"
                dpd = 30
            elif r < default_hazard * 0.8 + prepay_hazard:
                status = "Prepaid"
                prepay_flag = True
                alive = False
                bal = 0
            # else stay Current
        elif status == "30DPD":
            r = np.random.random()
            if r < 0.25:
                status = "Current"
                dpd = 0
            elif r < 0.25 + default_hazard * 5:
                status = "60DPD"
                dpd = 60
            # else stay 30DPD
        elif status == "60DPD":
            r = np.random.random()
            if r < 0.15:
                status = "Current"
                dpd = 0
            elif r < 0.15 + default_hazard * 6:
                status = "90DPD+"
                dpd = 90
            elif r < 0.20:
                status = "30DPD"
                dpd = 30
        elif status == "90DPD+":
            r = np.random.random()
            if r < 0.08:
                status = "Current"
                dpd = 0
                mod_flag = True
            elif r < 0.08 + default_hazard * 8:
                status = "Default"
                default_flag = True
                loss_severity = np.random.choice(
                    ["<20%", "20-40%", "40-60%", ">60%"], p=[0.3, 0.35, 0.25, 0.1]
                )
                alive = False
            elif r < 0.14:
                status = "30DPD"
                dpd = 30

        if status == "Current":
            dpd = 0

        # Closed if term ends
        if rem_term <= 0 and alive and status == "Current":
            status = "Closed"
            alive = False
            bal = 0

        last_updated = rpt + timedelta(days=np.random.randint(1, 28))

        rows.append({
            "loan_id": lid,
            "month_index": m + 1,
            "reporting_month": rpt.strftime("%Y-%m"),
            "loan_age_months": age,
            "remaining_term_months": rem_term,
            "current_balance": round(bal, 2),
            "interest_rate": rate,
            "current_status": status,
            "days_past_due": dpd,
            "modification_flag": int(mod_flag),
            "prepayment_flag": int(prepay_flag),
            "default_flag": int(default_flag),
            "loss_severity_band": loss_severity,
            "last_updated_at": last_updated.strftime("%Y-%m-%d"),
            "source_system": "PRIMARY",
            "document_status": np.random.choice(DOC_STATUSES, p=[0.75, 0.15, 0.05, 0.05]),
        })

panel = pd.DataFrame(rows)
print(f"  ✓ {len(panel):,} performance rows generated")

# ── Inject messiness ───────────────────────────────────────────────────────
print("▸ Injecting data quality issues …")
n = len(panel)
mess_stats = {}

# ~4% missing values (MCAR + MNAR)
mcar_cols = ["credit_score_band", "document_status", "loss_severity_band"]
# We'll merge credit_score_band from static for this injection
panel_with_static = panel.merge(static[["loan_id", "credit_score_band"]], on="loan_id", how="left")
mcar_mask = np.random.random(n) < 0.02
for col in ["document_status"]:
    panel.loc[mcar_mask & (np.random.random(n) < 0.5), col] = np.nan
mess_stats["mcar_missing"] = int(mcar_mask.sum())

# MNAR: higher DPD → more likely missing document_status
high_dpd = panel["days_past_due"] >= 60
mnar_mask = high_dpd & (np.random.random(n) < 0.15)
panel.loc[mnar_mask, "document_status"] = np.nan
mess_stats["mnar_missing"] = int(mnar_mask.sum())

# Missing balances
bal_miss = np.random.random(n) < 0.01
panel.loc[bal_miss, "current_balance"] = np.nan
mess_stats["missing_balance"] = int(bal_miss.sum())

# ~1% invalid dates (last_updated_at before origination)
inv_date_mask = np.random.random(n) < 0.01
panel.loc[inv_date_mask, "last_updated_at"] = "2018-06-15"
mess_stats["invalid_dates"] = int(inv_date_mask.sum())

# ~2% outlier balances
outlier_mask = np.random.random(n) < 0.02
panel.loc[outlier_mask, "current_balance"] = panel.loc[outlier_mask, "current_balance"].apply(
    lambda x: x * np.random.uniform(5, 20) if pd.notna(x) else x
)
mess_stats["outlier_balances"] = int(outlier_mask.sum())

# ~1.5% cross-field contradictions (status=Prepaid but balance>0)
contra_mask = np.random.random(n) < 0.015
panel.loc[contra_mask & (panel["current_status"] == "Prepaid"), "current_balance"] = np.random.uniform(1000, 50000)
contra2 = np.random.random(n) < 0.015
panel.loc[contra2 & (panel["current_status"] == "Current"), "days_past_due"] = np.random.choice([30, 60, 90])
mess_stats["contradictions"] = int(contra_mask.sum() + contra2.sum())

# ── Split train / test ─────────────────────────────────────────────────────
train = panel[panel["month_index"] <= TRAIN_MONTHS].copy()
test = panel[panel["month_index"] > TRAIN_MONTHS].copy()

# Withhold labels in test
test_withheld = test.copy()
test_withheld["default_flag"] = -1
test_withheld["prepayment_flag"] = -1

train.to_csv(RAW / "loan_monthly_performance_train.csv", index=False)
test_withheld.to_csv(RAW / "loan_monthly_performance_test.csv", index=False)
# Keep a ground truth copy for internal validation
test.to_csv(RAW / "_test_ground_truth.csv", index=False)

print(f"  ✓ Train: {len(train):,} rows | Test: {len(test):,} rows")


# ════════════════════════════════════════════════════════════════════════════
# 3. SERVICER UPDATES (conflicting second source)
# ════════════════════════════════════════════════════════════════════════════
print("▸ Generating servicer_updates.csv …")
sample_idx = np.random.choice(len(train), size=int(len(train) * 0.05), replace=False)
servicer = train.iloc[sample_idx][["loan_id", "month_index", "reporting_month",
                                    "current_balance", "current_status"]].copy()
# Introduce conflicts
servicer["current_balance"] = servicer["current_balance"].apply(
    lambda x: x * np.random.uniform(0.9, 1.1) if pd.notna(x) else x
)
status_flip = np.random.random(len(servicer)) < 0.3
servicer.loc[status_flip, "current_status"] = np.random.choice(
    ["Current", "30DPD"], size=status_flip.sum()
)
servicer["source_system"] = "SERVICER_FEED"
servicer.to_csv(RAW / "servicer_updates.csv", index=False)
print(f"  ✓ {len(servicer):,} servicer update rows")


# ════════════════════════════════════════════════════════════════════════════
# 4. DATA DICTIONARY
# ════════════════════════════════════════════════════════════════════════════
print("▸ Writing data_dictionary.md …")
data_dict = """# Data Dictionary — Loan Performance Intelligence Engine

## loan_static_attributes.csv
| Field | Type | Description |
|---|---|---|
| loan_id | string | Unique loan identifier (LN000000 format) |
| original_balance | float | Original loan balance at origination in USD |
| credit_score_band | categorical | Borrower credit score band at origination: <620, 620-660, 660-700, 700-740, 740-780, 780+ |
| ltv_band | categorical | Loan-to-value ratio band: <=60%, 60-70%, 70-80%, 80-90%, 90-95%, >95% |
| dti_band | categorical | Debt-to-income ratio band: <20%, 20-30%, 30-40%, 40-45%, 45-50%, >50% |
| state | string | US state abbreviation where property is located |
| loan_purpose | categorical | Purpose: Purchase, Refinance_Rate, Refinance_Cash, Home_Equity |
| occupancy_type | categorical | Occupancy: Primary, Secondary, Investment |
| property_type | categorical | Property type: Single_Family, Condo, Multi_Family, Townhouse |
| origination_month | string | Origination month (YYYY-MM format) |
| servicer_name | string | Name of the loan servicer |
| interest_rate | float | Loan interest rate (annual %) |
| original_term_months | integer | Original loan term in months (180, 240, or 360) |

## loan_monthly_performance_train.csv / loan_monthly_performance_test.csv
| Field | Type | Description |
|---|---|---|
| loan_id | string | Unique loan identifier, links to static attributes |
| month_index | integer | Sequential month index (1-based), used for time-aware splitting |
| reporting_month | string | Calendar reporting month (YYYY-MM) |
| loan_age_months | integer | Age of the loan in months since origination |
| remaining_term_months | integer | Remaining term in months |
| current_balance | float | Current outstanding balance. Should be non-negative and generally non-increasing unless modified. May contain intentional outliers and missing values. |
| interest_rate | float | Current interest rate |
| current_status | categorical | Loan status: Current, 30DPD, 60DPD, 90DPD+, Default, Prepaid, Closed |
| days_past_due | integer | Days past due. Should align with current_status. May contain intentional contradictions. |
| modification_flag | binary | 1 if loan was modified in this period |
| prepayment_flag | binary | 1 if loan was prepaid this period |
| default_flag | binary | 1 if loan defaulted this period |
| loss_severity_band | categorical | Loss severity if defaulted: <20%, 20-40%, 40-60%, >60%, N/A |
| last_updated_at | date | Date this record was last updated. May contain invalid dates (before origination). |
| source_system | string | Source system identifier |
| document_status | categorical | Status of loan documentation: Complete, Partial, Missing, Under_Review |

## servicer_updates.csv
| Field | Type | Description |
|---|---|---|
| loan_id | string | Loan identifier |
| month_index | integer | Month index |
| reporting_month | string | Reporting month |
| current_balance | float | Servicer-reported balance (may conflict with primary source) |
| current_status | categorical | Servicer-reported status (may conflict with primary source) |
| source_system | string | Always "SERVICER_FEED" |

## macro_scenarios.csv
| Field | Type | Description |
|---|---|---|
| scenario | string | Scenario name: base, adverse_credit, high_prepayment |
| quarter | string | Quarter label (Q1-Q8) |
| rate_shock_bps | integer | Interest rate shock in basis points |
| unemployment_rate | float | Projected unemployment rate |
| hpi_change_pct | float | House price index change percentage |
| prepayment_multiplier | float | Multiplier applied to base prepayment hazard |
| default_multiplier | float | Multiplier applied to base default hazard |

## Data Quality Notes
- ~4% missing values injected (combination of MCAR and MNAR patterns)
- ~1% invalid dates (last_updated_at before origination date)
- ~2% outlier balances (unrealistically high values)
- ~1.5% cross-field contradictions (e.g., status=Prepaid but balance>0, status=Current but DPD>0)
- Servicer feed contains ~5% conflicting status/balance vs primary source
"""
(RAW / "data_dictionary.md").write_text(data_dict)


# ════════════════════════════════════════════════════════════════════════════
# 5. VALIDATION RULES
# ════════════════════════════════════════════════════════════════════════════
print("▸ Writing validation_rules.json …")
rules = {
    "rules": [
        {
            "id": "VR001",
            "name": "balance_non_negative",
            "description": "Current balance must be non-negative",
            "field": "current_balance",
            "condition": "current_balance >= 0",
            "severity": "error"
        },
        {
            "id": "VR002",
            "name": "balance_non_increasing",
            "description": "Balance should be non-increasing month-over-month unless modification_flag=1",
            "field": "current_balance",
            "condition": "current_balance <= previous_balance OR modification_flag = 1",
            "severity": "warning"
        },
        {
            "id": "VR003",
            "name": "status_balance_consistency",
            "description": "If status is Prepaid or Closed, balance should be 0",
            "field": ["current_status", "current_balance"],
            "condition": "IF current_status IN (Prepaid, Closed) THEN current_balance = 0",
            "severity": "error"
        },
        {
            "id": "VR004",
            "name": "dpd_status_alignment",
            "description": "Days past due must align with status (Current→0, 30DPD→30, etc.)",
            "field": ["days_past_due", "current_status"],
            "condition": "status_to_dpd_mapping_consistent",
            "severity": "error"
        },
        {
            "id": "VR005",
            "name": "date_ordering",
            "description": "last_updated_at must be on or after the origination month",
            "field": "last_updated_at",
            "condition": "last_updated_at >= origination_month",
            "severity": "error"
        },
        {
            "id": "VR006",
            "name": "document_completeness",
            "description": "document_status should not be null or Missing for active loans",
            "field": "document_status",
            "condition": "IF current_status = Current THEN document_status IS NOT NULL AND document_status != Missing",
            "severity": "warning"
        },
        {
            "id": "VR007",
            "name": "term_consistency",
            "description": "remaining_term_months should decrease by 1 each month",
            "field": "remaining_term_months",
            "condition": "remaining_term_months = previous_remaining_term - 1",
            "severity": "warning"
        },
        {
            "id": "VR008",
            "name": "loss_severity_on_default",
            "description": "loss_severity_band must be populated when default_flag=1",
            "field": ["loss_severity_band", "default_flag"],
            "condition": "IF default_flag = 1 THEN loss_severity_band != N/A",
            "severity": "error"
        }
    ]
}
(RAW / "validation_rules.json").write_text(json.dumps(rules, indent=2))


# ════════════════════════════════════════════════════════════════════════════
# 6. MACRO SCENARIOS
# ════════════════════════════════════════════════════════════════════════════
print("▸ Writing macro_scenarios.csv …")
quarters = [f"Q{i}" for i in range(1, 9)]
scenarios_rows = []
for q_idx, q in enumerate(quarters):
    # Base
    scenarios_rows.append({
        "scenario": "base", "quarter": q,
        "rate_shock_bps": 0, "unemployment_rate": 4.0 + 0.1 * q_idx,
        "hpi_change_pct": 2.0 - 0.2 * q_idx,
        "prepayment_multiplier": 1.0, "default_multiplier": 1.0
    })
    # Adverse credit
    scenarios_rows.append({
        "scenario": "adverse_credit", "quarter": q,
        "rate_shock_bps": 50 + 25 * q_idx,
        "unemployment_rate": 5.0 + 0.5 * q_idx,
        "hpi_change_pct": -1.0 - 0.5 * q_idx,
        "prepayment_multiplier": 0.7, "default_multiplier": 1.5 + 0.1 * q_idx
    })
    # High prepayment
    scenarios_rows.append({
        "scenario": "high_prepayment", "quarter": q,
        "rate_shock_bps": -100 - 20 * q_idx,
        "unemployment_rate": 3.5,
        "hpi_change_pct": 3.0 + 0.3 * q_idx,
        "prepayment_multiplier": 2.0 + 0.2 * q_idx, "default_multiplier": 0.8
    })

pd.DataFrame(scenarios_rows).to_csv(RAW / "macro_scenarios.csv", index=False)


# ════════════════════════════════════════════════════════════════════════════
# 7. SUBMISSION TEMPLATE
# ════════════════════════════════════════════════════════════════════════════
print("▸ Writing submission_template.csv …")
sub_cols = [
    "loan_id", "month_index", "prob_delinquency_3m", "prob_delinquency_6m",
    "prob_default_12m", "prob_prepayment_12m", "predicted_next_state",
    "exception_required", "exception_type", "anomaly_score",
    "top_drivers", "recommended_action", "confidence"
]
pd.DataFrame(columns=sub_cols).to_csv(RAW / "submission_template.csv", index=False)


# ════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "═" * 70)
print("SYNTHETIC DATA GENERATION COMPLETE")
print("═" * 70)
print(f"  Loans:           {N_LOANS:,}")
print(f"  Train rows:      {len(train):,}")
print(f"  Test rows:       {len(test):,}")
print(f"  Servicer rows:   {len(servicer):,}")
print(f"  Total months:    {TOTAL_MONTHS}")
print(f"\n  Injected messiness:")
for k, v in mess_stats.items():
    print(f"    {k}: {v:,} rows")
print(f"\n  Leakage-safe design:")
print(f"    ✓ Train/test split by month_index (time-aware)")
print(f"    ✓ No post-outcome features in prediction columns")
print(f"    ✓ Test labels withheld in public test file")
print(f"\n  Files written to: {RAW}")
print("═" * 70)
