"""
scenario_engine.py
===================
Runs on-demand scenario simulations using the trained transition matrix.
"""

import json, logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts"
_RAW = _ROOT / "data" / "raw"


class ScenarioEngine:
    """On-demand scenario simulation engine."""

    def __init__(self):
        self.base_matrix = None
        self.scenarios_df = None
        self.states = []

    def load(self):
        tm_path = _ARTIFACTS / "transition_matrix.json"
        if tm_path.exists():
            data = json.loads(tm_path.read_text())
            self.base_matrix = np.array(data["matrix"])
            self.states = data["states"]

        sc_path = _RAW / "macro_scenarios.csv"
        if sc_path.exists():
            import pandas as pd
            self.scenarios_df = pd.read_csv(sc_path)

    def run(self, scenario_name: str, n_sims: int = 500) -> dict:
        """Run a scenario simulation."""
        if self.base_matrix is None:
            # Return pre-computed results if available
            results_path = _ARTIFACTS / "scenario_results.json"
            if results_path.exists():
                data = json.loads(results_path.read_text())
                sc = data.get("scenarios", {}).get(scenario_name, [])
                return {"scenario_name": scenario_name, "quarters": sc,
                        "segments": data.get("segments", {})}
            return {"scenario_name": scenario_name, "quarters": [], "segments": {}}

        if self.scenarios_df is None:
            return {"scenario_name": scenario_name, "quarters": [], "segments": {}}

        sc = self.scenarios_df[self.scenarios_df["scenario"] == scenario_name]
        if sc.empty:
            return {"scenario_name": scenario_name, "quarters": [], "segments": {}}

        quarters = []
        for _, row in sc.sort_values("quarter").iterrows():
            default_mult = float(row["default_multiplier"])
            prepay_mult = float(row["prepayment_multiplier"])

            adj = self.base_matrix.copy()
            # Increase delinquency transitions under credit stress
            adj[0, 1] *= default_mult  # Current -> 30DPD
            adj[1, 2] *= default_mult  # 30DPD -> 60DPD
            adj[2, 3] *= default_mult  # 60DPD -> 90DPD+

            for i in range(4):
                adj[i, 4] *= default_mult
            adj[0, 5] *= prepay_mult
            for i in range(len(self.states)):
                s = adj[i].sum()
                if s > 0:
                    adj[i] /= s

            delinq, defaults, prepays = [], [], []
            for _ in range(n_sims):
                pool = np.array([0.85, 0.06, 0.03, 0.02, 0.01, 0.02, 0.01])
                for _ in range(3):
                    pool = pool @ adj + np.random.normal(0, 0.003, len(pool))
                    pool = np.clip(pool, 0, None)
                    pool /= pool.sum()
                delinq.append(float(pool[1]+pool[2]+pool[3]))
                defaults.append(float(pool[4]))
                prepays.append(float(pool[5]))

            quarters.append({
                "quarter": row["quarter"],
                "delinquency_rate": {
                    "mean": round(np.mean(delinq), 4),
                    "p5": round(np.percentile(delinq, 5), 4),
                    "p95": round(np.percentile(delinq, 95), 4),
                },
                "default_rate": {
                    "mean": round(np.mean(defaults), 4),
                    "p5": round(np.percentile(defaults, 5), 4),
                    "p95": round(np.percentile(defaults, 95), 4),
                },
                "prepayment_rate": {
                    "mean": round(np.mean(prepays), 4),
                    "p5": round(np.percentile(prepays, 5), 4),
                    "p95": round(np.percentile(prepays, 95), 4),
                },
            })

        return {"scenario_name": scenario_name, "quarters": quarters, "segments": {}}


# Singleton
scenario_engine = ScenarioEngine()
