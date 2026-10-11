"""Pydantic schemas for tools, itineraries, and agent communication."""

from tripmind.schemas.tools import (
    RegionSearchInput,
    RegionInfo,
    RegionSearchResult,
    RouteCalculateInput,
    RouteResult,
    AccommodationSearchInput,
    AccommodationItem,
    AccommodationSearchResult,
    ActivitySearchInput,
    ActivityItem,
    ActivitySearchResult,
    BudgetCalculateInput,
    BudgetBreakdownResult,
)
from tripmind.schemas.itinerary import (
    DayPlan,
    TripPlanResponse,
    PlannerRequest,
    AgentTraceStep,
)

__all__ = [
    "RegionSearchInput",
    "RegionInfo",
    "RegionSearchResult",
    "RouteCalculateInput",
    "RouteResult",
    "AccommodationSearchInput",
    "AccommodationItem",
    "AccommodationSearchResult",
    "ActivitySearchInput",
    "ActivityItem",
    "ActivitySearchResult",
    "BudgetCalculateInput",
    "BudgetBreakdownResult",
    "DayPlan",
    "TripPlanResponse",
    "PlannerRequest",
    "AgentTraceStep",
]
