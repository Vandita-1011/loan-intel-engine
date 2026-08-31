"""Prediction router."""

from fastapi import APIRouter, HTTPException
from ..services.model_service import model_service

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{loan_id}")
def get_prediction(loan_id: str):
    """Get prediction for a specific loan."""
    loan = model_service.get_loan(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
    return model_service.predict(loan_id)


@router.get("/")
def list_predictions(limit: int = 50, offset: int = 0):
    """Get predictions for multiple loans."""
    if model_service.features_df is None:
        return {"predictions": [], "total": 0}

    loan_ids = model_service.features_df["loan_id"].unique()
    subset = loan_ids[offset:offset+limit]
    predictions = [model_service.predict(lid) for lid in subset]
    return {"predictions": predictions, "total": len(loan_ids)}
