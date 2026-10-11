"""Structured Itinerary & Agent Trace Schemas.

AGENTIC AI CONCEPT — Structured Synthesis & Explainable Traces:
1. Explainability (Observability): Unlike black-box chatbots where you can't
   tell why a decision was made, an Agentic AI must provide an audit trail of
   every Thought, Action, and Observation (Trace Steps).
2. Machine-Readable Itinerary: Structured DayPlan objects allow downstream
   systems (calendars, frontend UI cards, booking engines) to reliably render
   each day without fragile regex scraping.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from tripmind.schemas.tools import (
    AccommodationItem,
    ActivityItem,
    RouteResult,
    BudgetBreakdownResult,
)


class AgentTraceStep(BaseModel):
    """Represents a single step in the ReAct (Reasoning + Acting) loop."""
    step_number: int
    thought: str = Field(..., description="The internal reasoning/deliberation of the agent before acting.")
    tool_name: Optional[str] = Field(default=None, description="Name of the tool invoked, if an action was taken.")
    tool_input: Optional[Dict[str, Any]] = Field(default=None, description="Arguments passed to the tool.")
    observation: Optional[str] = Field(default=None, description="The deterministic feedback/result returned by the tool.")


class DayPlan(BaseModel):
    """The schedule and bookings for a single day of the trip."""
    day_number: int
    title: str = Field(..., description="E.g., 'Day 1: Arrival, Dal Lake Sunset & Authentic Wazwan'")
    region: str
    stay: AccommodationItem
    activities: List[ActivityItem]
    transit: Optional[RouteResult] = None
    daily_cost_inr: float
    pace_notes: str = Field(..., description="E.g., 'Slow pace, 1 hr transit, sunset at 5:15 PM factored in.'")


class TripPlanResponse(BaseModel):
    """The final verified, constraint-compliant itinerary synthesized by TripMind."""
    trip_title: str
    destination: str
    month: str
    duration_days: int
    duration_nights: int
    traveler_profile: str
    days: List[DayPlan]
    budget_summary: BudgetBreakdownResult
    constraints_verified: Dict[str, bool] = Field(
        ...,
        description="Boolean audit of all hard constraints: budget_compliant, winter_heating_guaranteed, no_adventure_sports, relaxed_pace.",
    )
    agent_reasoning_summary: str = Field(
        ...,
        description="High-level narrative explaining how trade-offs were balanced and why this itinerary meets the user goal.",
    )
    execution_trace: List[AgentTraceStep] = Field(
        default_factory=list,
        description="Full multi-turn ReAct trace showing Thought -> Action -> Observation steps.",
    )


class PlannerRequest(BaseModel):
    """Inbound API request payload."""
    user_query: str = Field(
        ...,
        description="Natural language trip request, e.g. 'I want to visit Kashmir in December for 5 days. Budget ₹80k...'",
        examples=[
            "I want to visit Kashmir in December for 5 days. I'm going with my wife. We don't want a hectic trip. We love scenic places and food, but aren't interested in adventure activities. Budget around ₹80k excluding flights."
        ],
    )
    preferred_provider: Optional[str] = Field(
        default=None,
        description="Override provider ('gemini', 'groq', or 'mock'). Defaults to config settings.",
    )
