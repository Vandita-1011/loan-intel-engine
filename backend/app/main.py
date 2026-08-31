import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .services.model_service import model_service
from .services.rag_service import rag_service
from .services.llm_client import seed_prompt_log
from .routers import predict, anomaly, scenario, explain, copilot, dev_log

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.app.main")

app = FastAPI(
    title="Loan Performance Intelligence Engine API",
    description="API serving predictions, anomalies, survival curves, and AI copilot interactions",
    version="1.0.0"
)

# Add CORS Middleware to allow Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to load models and initialize RAG
@app.on_event("startup")
def startup_event():
    logger.info("Starting up backend services...")
    
    # Load trained ML models and datasets
    try:
        model_service.load()
        logger.info(f"Models loaded successfully: {model_service.models_count} models online")
    except Exception as e:
        logger.error(f"Error loading model service: {e}", exc_info=True)
        
    # Index validation rules and data dictionary in ChromaDB
    try:
        rag_service.load()
        logger.info("RAG service initialized successfully")
    except Exception as e:
        logger.error(f"Error loading RAG service: {e}", exc_info=True)
        
    # Seed prompt log for Copilot demonstrations
    try:
        seed_prompt_log()
        logger.info("Copilot prompt log seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding prompt log: {e}", exc_info=True)

# Include API routers
app.include_router(predict.router)
app.include_router(anomaly.router)
app.include_router(scenario.router)
app.include_router(explain.router)
app.include_router(copilot.router)
app.include_router(dev_log.router)

@app.get("/health", tags=["health"])
def health_check():
    """Returns the API status and configuration metadata."""
    return {
        "status": "ok",
        "models_loaded": model_service.models_count,
        "rag_indexed": len(rag_service.chunks) if rag_service.chunks else 0,
        "version": "1.0.0"
    }
