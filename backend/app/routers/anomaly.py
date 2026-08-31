"""Anomaly router."""

from fastapi import APIRouter
from ..services.model_service import model_service

router = APIRouter(prefix="/anomalies", tags=["anomalies"])


@router.get("/")
def list_anomalies(limit: int = 20):
    """Get top anomalies sorted by score."""
    return {"anomalies": model_service.get_anomalies(limit), "total": limit}
