"""FastAPI REST API Endpoints for TripMind V1."""

from fastapi import APIRouter, HTTPException
from tripmind.config import settings
from tripmind.tools.registry import default_registry
from tripmind.core.agent import ReActAgent
from tripmind.core.llm import get_llm_provider
from tripmind.schemas.itinerary import PlannerRequest, TripPlanResponse
import logging

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger("tripmind.agent")

@router.get("/health")
def health_check():
    """Service health and diagnostic check, including PostgreSQL connection."""
    from sqlalchemy import text
    db_connected = False
    db_stats = {}
    try:
        from tripmind.db.session import SessionLocal
        from tripmind.db.models import RegionModel, AccommodationModel, ActivityModel
        if SessionLocal:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                db_connected = True
                db_stats = {
                    "regions_count": db.query(RegionModel).count(),
                    "accommodations_count": db.query(AccommodationModel).count(),
                    "activities_count": db.query(ActivityModel).count(),
                }
            finally:
                db.close()
    except Exception as e:
        db_stats = {"error": str(e)}

    return {
        "status": "healthy",
        "service": "TripMind V1 ReAct Engine",
        "version": "0.1.0",
        "default_provider": settings.TRIPMIND_LLM_PROVIDER,
        "database": {
            "connected": db_connected,
            "port": 5433,
            "database_name": "tripmind",
            "stats": db_stats,
        },
        "tools_registered_count": len(default_registry.list_tools()),
    }


@router.get("/tools")
def list_available_tools():
    """Inspect all active tools and their auto-generated JSON schemas."""
    return {
        "tools": default_registry.get_schemas(),
    }


@router.post("/planner/plan", response_model=TripPlanResponse)
def generate_trip_plan(request: PlannerRequest):
    """Execute the multi-turn ReAct planning agent on a user query."""
    try:
        provider = get_llm_provider(request.preferred_provider)
        logger.info(f"User Choosen LLM provider - ({provider})")
        agent = ReActAgent(provider=provider, registry=default_registry)
        plan = agent.plan(request.user_query)
        return plan
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning execution error: {str(e)}")
