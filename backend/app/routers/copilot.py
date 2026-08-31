"""Copilot router — RAG-grounded LLM assistant."""

from fastapi import APIRouter
from ..models.schemas import CopilotRequest, CopilotResponse
from ..services.model_service import model_service
from ..services.rag_service import rag_service
from ..services.llm_client import llm_client

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/ask", response_model=CopilotResponse)
def ask_copilot(req: CopilotRequest):
    """Ask the AI copilot a question about a loan."""
    # Get loan data
    loan_data = model_service.get_loan(req.loan_id) or {"loan_id": req.loan_id}

    # Get prediction data
    pred = model_service.predict(req.loan_id)
    loan_data.update({k: v for k, v in pred.items() if k != "loan_id"})

    # Get SHAP drivers
    shap_drivers = pred.get("top_drivers", [])

    # Retrieve grounding context
    context_chunks = rag_service.retrieve(req.question, n_results=5)

    # Ask LLM
    result = llm_client.ask(
        question=req.question,
        loan_data=loan_data,
        shap_drivers=shap_drivers,
        context_chunks=context_chunks,
    )

    return CopilotResponse(
        loan_id=req.loan_id,
        answer=result["answer"],
        citations=result["citations"],
        grounding_chunks=[c[:200] for c in result["grounding_chunks"]],
        disclaimer="RECOMMENDATION — NOT A DECISION",
    )
