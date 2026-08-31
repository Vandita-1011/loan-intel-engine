"""Explainability router."""

from fastapi import APIRouter, HTTPException
from ..services.model_service import model_service

router = APIRouter(prefix="/explain", tags=["explainability"])


@router.get("/{loan_id}")
def explain_loan(loan_id: str):
    """Get SHAP explanation for a loan."""
    return model_service.get_explanation(loan_id)


@router.get("/global/summary")
def global_summary():
    """Get global explainability summary."""
    if model_service.explainability:
        return {
            "global_importance": model_service.explainability.get("global_importance", []),
            "calibration": model_service.explainability.get("calibration", {}),
            "fp_cases": model_service.explainability.get("fp_cases", []),
            "fn_cases": model_service.explainability.get("fn_cases", []),
            "confidence_bands": model_service.explainability.get("confidence_bands", {}),
        }
    return {"global_importance": [], "calibration": {}, "fp_cases": [], "fn_cases": [], "confidence_bands": {}}
