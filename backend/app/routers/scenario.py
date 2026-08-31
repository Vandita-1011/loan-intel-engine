"""Scenario router."""

from fastapi import APIRouter
from ..models.schemas import ScenarioRequest
from ..services.scenario_engine import scenario_engine

router = APIRouter(prefix="/scenario", tags=["scenarios"])


@router.post("/run")
def run_scenario(req: ScenarioRequest):
    """Run a scenario simulation."""
    result = scenario_engine.run(req.scenario_name)
    return result


@router.get("/results")
def get_all_scenarios():
    """Get pre-computed scenario results."""
    import json
    from pathlib import Path
    results_path = Path(__file__).resolve().parent.parent / "artifacts" / "scenario_results.json"
    if results_path.exists():
        return json.loads(results_path.read_text())
    return {"scenarios": {}, "segments": {}}
