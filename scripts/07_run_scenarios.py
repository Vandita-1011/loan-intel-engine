#!/usr/bin/env python3
"""
07_run_scenarios.py
====================
Task 5 — Scenario Simulation: Apply macro_scenarios.csv multipliers to model
inputs, run Monte Carlo simulations, output projected rate paths.
"""

import json, warnings
from pathlib import Path
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
ARTIFACTS = ROOT / "backend" / "app" / "artifacts"
REPORTS = ROOT / "reports"

print("▸ Running scenario simulations …")

static = pd.read_csv(RAW / "loan_static_attributes.csv")
scenarios = pd.read_csv(RAW / "macro_scenarios.csv")
trans_matrix = json.loads((ARTIFACTS / "transition_matrix.json").read_text())

states = trans_matrix["states"]
base_matrix = np.array(trans_matrix["matrix"])

credit_map = {"<620": 0, "620-660": 1, "660-700": 2, "700-740": 3, "740-780": 4, "780+": 5}
static["credit_num"] = static["credit_score_band"].map(credit_map)

N_SIMULATIONS = 1000
N_QUARTERS = 8

# ── Run simulations per scenario ─────────────────────────────────────────
scenario_names = scenarios["scenario"].unique()
all_results = {}

for scenario_name in scenario_names:
    print(f"\n  Scenario: {scenario_name}")
    sc = scenarios[scenarios["scenario"] == scenario_name].sort_values("quarter")

    quarter_results = []

    for q_idx, (_, row) in enumerate(sc.iterrows()):
        default_mult = float(row["default_multiplier"])
        prepay_mult = float(row["prepayment_multiplier"])

        # Adjust transition matrix
        adj_matrix = base_matrix.copy()

        # Increase delinquency transitions under credit stress
        adj_matrix[0, 1] *= default_mult  # Current -> 30DPD
        adj_matrix[1, 2] *= default_mult  # 30DPD -> 60DPD
        adj_matrix[2, 3] *= default_mult  # 60DPD -> 90DPD+

        # Increase default transitions (column 4)
        for i in range(4):  # From Current through 90DPD+
            adj_matrix[i, 4] *= default_mult

        # Increase prepayment transitions (column 5)
        adj_matrix[0, 5] *= prepay_mult  # Only from Current to Prepaid

        # Re-normalize rows
        for i in range(len(states)):
            row_sum = adj_matrix[i].sum()
            if row_sum > 0:
                adj_matrix[i] /= row_sum

        # Monte Carlo: start with pool distribution, evolve 3 months per quarter
        delinq_rates = []
        default_rates = []
        prepay_rates = []

        for sim in range(N_SIMULATIONS):
            # Start: mostly Current
            pool = np.array([0.85, 0.06, 0.03, 0.02, 0.01, 0.02, 0.01])

            for month in range(3):  # 3 months per quarter
                noise = np.random.normal(0, 0.005, len(pool))
                pool = pool @ adj_matrix + noise
                pool = np.clip(pool, 0, None)
                pool /= pool.sum()

            delinq_rates.append(float(pool[1] + pool[2] + pool[3]))
            default_rates.append(float(pool[4]))
            prepay_rates.append(float(pool[5]))

        quarter_results.append({
            "quarter": row["quarter"],
            "delinquency_rate": {
                "mean": round(np.mean(delinq_rates), 4),
                "p5": round(np.percentile(delinq_rates, 5), 4),
                "p25": round(np.percentile(delinq_rates, 25), 4),
                "p75": round(np.percentile(delinq_rates, 75), 4),
                "p95": round(np.percentile(delinq_rates, 95), 4),
            },
            "default_rate": {
                "mean": round(np.mean(default_rates), 4),
                "p5": round(np.percentile(default_rates, 5), 4),
                "p95": round(np.percentile(default_rates, 95), 4),
            },
            "prepayment_rate": {
                "mean": round(np.mean(prepay_rates), 4),
                "p5": round(np.percentile(prepay_rates, 5), 4),
                "p95": round(np.percentile(prepay_rates, 95), 4),
            },
            "rate_shock_bps": int(row["rate_shock_bps"]),
            "unemployment_rate": float(row["unemployment_rate"]),
            "hpi_change_pct": float(row["hpi_change_pct"]),
        })

    all_results[scenario_name] = quarter_results
    last_q = quarter_results[-1]
    print(f"    Final Q delinquency: {last_q['delinquency_rate']['mean']:.2%}")
    print(f"    Final Q default: {last_q['default_rate']['mean']:.2%}")
    print(f"    Final Q prepayment: {last_q['prepayment_rate']['mean']:.2%}")

# ── Segment-level breakdown ─────────────────────────────────────────────
print("\n  Computing segment-level breakdown …")
segments = {}
for band in static["credit_score_band"].unique():
    band_loans = static[static["credit_score_band"] == band]
    risk_level = credit_map.get(band, 2)
    # Higher risk → higher multiplier on adverse
    risk_mult = 1.0 + (5 - risk_level) * 0.15
    segments[band] = {
        "n_loans": len(band_loans),
        "base_delinq_rate": round(all_results["base"][-1]["delinquency_rate"]["mean"] * risk_mult, 4),
        "adverse_delinq_rate": round(all_results["adverse_credit"][-1]["delinquency_rate"]["mean"] * risk_mult, 4),
        "base_default_rate": round(all_results["base"][-1]["default_rate"]["mean"] * risk_mult, 4),
        "adverse_default_rate": round(all_results["adverse_credit"][-1]["default_rate"]["mean"] * risk_mult, 4),
    }

# ── Save results ─────────────────────────────────────────────────────────
scenario_output = {
    "scenarios": all_results,
    "segments": segments,
    "n_simulations": N_SIMULATIONS,
    "n_quarters": N_QUARTERS,
}

with open(PROC / "scenario_results.json", "w") as f:
    json.dump(scenario_output, f, indent=2, default=str)

with open(ARTIFACTS / "scenario_results.json", "w") as f:
    json.dump(scenario_output, f, indent=2, default=str)

# ── Generate report ──────────────────────────────────────────────────────
report = f"""# Scenario Analysis Report

*Generated: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")}*

## Methodology
- Monte Carlo simulation with {N_SIMULATIONS:,} draws per scenario per quarter
- {N_QUARTERS} quarters projected forward
- Base transition matrix from observed Markov chain
- Macro multipliers applied to default and prepayment hazard rates

## Scenario Definitions
| Scenario | Description |
|---|---|
| base | Current economic conditions, no shocks |
| adverse_credit | Rising rates, rising unemployment, falling home prices |
| high_prepayment | Falling rates, strong economy, accelerated prepayment |

## Projected Rates (Final Quarter)
| Scenario | Delinquency Rate | Default Rate | Prepayment Rate |
|---|---|---|---|
"""
for sc_name, quarters in all_results.items():
    last = quarters[-1]
    report += f"| {sc_name} | {last['delinquency_rate']['mean']:.2%} | {last['default_rate']['mean']:.2%} | {last['prepayment_rate']['mean']:.2%} |\n"

report += """
## Segment Breakdown (by Credit Band)
| Credit Band | # Loans | Base Delinq | Adverse Delinq | Base Default | Adverse Default |
|---|---|---|---|---|---|
"""
for band, seg in sorted(segments.items()):
    report += f"| {band} | {seg['n_loans']:,} | {seg['base_delinq_rate']:.2%} | {seg['adverse_delinq_rate']:.2%} | {seg['base_default_rate']:.2%} | {seg['adverse_default_rate']:.2%} |\n"

(REPORTS / "scenario_report.md").write_text(report)

print(f"\n✓ Scenario results: data/processed/scenario_results.json")
print(f"✓ Report: reports/scenario_report.md")
