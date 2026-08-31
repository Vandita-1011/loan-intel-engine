"""Dev log and reports router."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

router = APIRouter(tags=["reports"])

_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_REPORTS = _ROOT / "reports"
_PROC = _ROOT / "data" / "processed"


@router.get("/devlog")
def get_devlog():
    """Get the AI development log."""
    path = _REPORTS / "ai_development_log.md"
    if path.exists():
        return {"content": path.read_text(encoding="utf-8")}
    return {"content": "# AI Development Log\n\nNot yet generated."}


@router.get("/reports/{name}")
def get_report(name: str):
    """Get a named report."""
    safe_name = name.replace("..", "").replace("/", "").replace("\\", "")
    if not safe_name.endswith(".md"):
        safe_name += ".md"

    path = _REPORTS / safe_name
    if path.exists():
        return {"name": safe_name, "content": path.read_text(encoding="utf-8")}

    raise HTTPException(status_code=404, detail=f"Report '{name}' not found")


@router.get("/data/dq-summary")
def get_dq_summary():
    """Get data quality summary."""
    path = _PROC / "dq_summary.json"
    if path.exists():
        return json.loads(path.read_text())
    return {"data_quality_score": 0, "missing_pct": {}, "outliers": {}}


@router.get("/data/prediction-results")
def get_prediction_results():
    """Get prediction model results."""
    path = _PROC / "prediction_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


@router.get("/data/survival-results")
def get_survival_results():
    """Get survival model results."""
    path = _PROC / "survival_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


@router.get("/data/explainability-results")
def get_explainability_results():
    """Get explainability results."""
    path = _PROC / "explainability_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


@router.get("/data/scenario-results")
def get_scenario_results():
    """Get scenario results."""
    path = _PROC / "scenario_results.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}


@router.get("/data/anomaly-examples")
def get_anomaly_examples():
    """Get curated anomaly examples."""
    path = _REPORTS / "anomaly_examples.json"
    if path.exists():
        return json.loads(path.read_text())
    return []


@router.get("/prompt-log")
def get_prompt_log():
    """Get the LLM prompt log."""
    path = _REPORTS / "llm_prompt_log.jsonl"
    if path.exists():
        entries = []
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return {"entries": entries}
    return {"entries": []}
