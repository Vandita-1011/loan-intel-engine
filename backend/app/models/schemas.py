"""Pydantic schemas for the Loan Intelligence API."""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class LoanStatic(BaseModel):
    """Static loan attributes."""
    loan_id: str
    original_balance: float
    credit_score_band: str
    ltv_band: str
    dti_band: str
    state: str
    loan_purpose: str
    occupancy_type: str
    property_type: str
    origination_month: str
    servicer_name: str
    interest_rate: float
    original_term_months: int


class PredictionResponse(BaseModel):
    """Prediction output for a single loan."""
    loan_id: str
    prob_delinquency_3m: float = 0.0
    prob_delinquency_6m: float = 0.0
    prob_default_12m: float = 0.0
    prob_prepayment_12m: float = 0.0
    predicted_next_state: str = "Current"
    confidence: float = 0.5
    top_drivers: list[dict] = Field(default_factory=list)


class AnomalyRecord(BaseModel):
    """Anomaly detection result."""
    loan_id: str
    month_index: int
    anomaly_score: float
    exception_type: str
    current_status: Optional[str] = None
    current_balance: Optional[float] = None
    days_past_due: Optional[int] = None
    drivers: list[str] = Field(default_factory=list)
    recommended_action: str = ""


class ScenarioRequest(BaseModel):
    """Request to run a scenario simulation."""
    scenario_name: str = "base"


class ScenarioResponse(BaseModel):
    """Scenario simulation results."""
    scenario_name: str
    quarters: list[dict]
    segments: dict = Field(default_factory=dict)


class ExplainResponse(BaseModel):
    """Explainability output for a loan."""
    loan_id: str
    prediction: float = 0.0
    shap_drivers: list[dict] = Field(default_factory=list)
    base_value: float = 0.0
    confidence_band: str = "medium"


class CopilotRequest(BaseModel):
    """Copilot chat request."""
    loan_id: str
    question: str


class CopilotResponse(BaseModel):
    """Copilot response with grounding."""
    loan_id: str
    answer: str
    citations: list[str] = Field(default_factory=list)
    disclaimer: str = "RECOMMENDATION — NOT A DECISION"
    grounding_chunks: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    models_loaded: int = 0
    version: str = "1.0.0"
