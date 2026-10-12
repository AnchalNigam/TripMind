"""Unit & Integration Tests for TripMind Level 2: Plan-and-Solve Engine."""

import pytest
from fastapi.testclient import TestClient

from tripmind.api.app import app
from tripmind.v2.state import WorkingMemoryState, ParsedConstraints
from tripmind.v2.planner import StrategicPlanner
from tripmind.v2.workers.staging import StagingWorker
from tripmind.v2.workers.stays import StayWorker
from tripmind.v2.workers.activities import ActivityWorker
from tripmind.v2.workers.transit import TransitWorker
from tripmind.v2.auditor import FinancialAuditor
from tripmind.v2.critic import CriticAgent
from tripmind.v2.compiler import ItineraryCompiler
from tripmind.v2.engine import PlanAndSolveEngine
from tripmind.schemas.itinerary import TripPlanResponse


client = TestClient(app)

BENCHMARK_QUERY = (
    "I want to visit Kashmir in December for 5 days. I'm going with my wife. "
    "We don't want a hectic trip. We love scenic places and food, but aren't "
    "interested in adventure activities. Budget around ₹80k excluding flights."
)

TIGHT_BUDGET_QUERY = (
    "I want to visit Kashmir in December for 5 days. Budget ₹6,000."
)


def test_planner_constraint_locking():
    """Verify that user budget and parameters are strictly locked upon ingestion."""
    planner = StrategicPlanner(llm_client=None)
    constraints: ParsedConstraints = planner.parse_user_constraints(BENCHMARK_QUERY)

    assert constraints.destination == "Kashmir"
    assert constraints.month == "December"
    assert constraints.duration_days == 5
    assert constraints.duration_nights == 4
    assert constraints.budget_cap_inr == 80000.0
    assert constraints.exclude_adventure is True
    assert constraints.pace == "relaxed"
    assert constraints.traveler_profile == "Couple"


def test_planner_tight_budget_locking():
    """Verify that a small budget cap (₹6,000) is locked exactly and not overridden."""
    planner = StrategicPlanner(llm_client=None)
    constraints = planner.parse_user_constraints(TIGHT_BUDGET_QUERY)
    assert constraints.budget_cap_inr == 6000.0
    assert constraints.duration_days == 5


def test_staging_worker_spatial_partitioning():
    """Verify that StagingWorker partitions days into spatial hubs and filters closed passes."""
    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(BENCHMARK_QUERY)
    
    stager = StagingWorker()
    state = stager.run(state)

    # Verify Sonamarg is excluded due to winter closure
    accessible_names = [r.region_name for r in state.accessible_regions]
    assert "Srinagar" in accessible_names
    assert "Gulmarg" in accessible_names
    assert "Sonamarg" not in accessible_names

    # Verify day stages
    assert len(state.day_stages) == 5
    assert state.day_stages[0].region == "Srinagar"
    assert state.day_stages[1].region == "Srinagar"
    assert state.day_stages[2].region == "Srinagar"
    assert state.day_stages[3].region == "Gulmarg"
    assert state.day_stages[4].region == "Gulmarg"

    # Verify transit days
    assert state.day_stages[0].is_transit_day is True  # Airport to Srinagar
    assert state.day_stages[2].is_transit_day is True  # Srinagar to Gulmarg
    assert state.day_stages[4].is_transit_day is True  # Gulmarg to Airport


def test_worker_pool_execution():
    """Verify isolated execution of Stays, Activities, and Transit workers."""
    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(BENCHMARK_QUERY)
    state = StagingWorker().run(state)

    # Run Stays worker
    state = StayWorker().run(state)
    assert "Srinagar" in state.selected_stay_by_region
    assert "Gulmarg" in state.selected_stay_by_region
    assert state.selected_stay_by_region["Srinagar"].heating_verified is True
    assert state.selected_stay_by_region["Gulmarg"].heating_verified is True

    # Run Activities worker
    state = ActivityWorker().run(state)
    srinagar_acts = state.activities_by_region.get("Srinagar", [])
    assert len(srinagar_acts) > 0
    # Negative constraint check: zero adventure sports
    for act in srinagar_acts:
        assert act.is_adventure is False

    # Run Transit worker
    state = TransitWorker().run(state)
    assert len(state.transit_routes) > 0
    # Srinagar to Gulmarg must have route
    assert "Srinagar->Gulmarg" in state.transit_routes
    assert state.transit_routes["Srinagar->Gulmarg"].distance_km > 0


def test_financial_auditor_deterministic_math():
    """Verify that FinancialAuditor performs exact mathematical calculations."""
    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(BENCHMARK_QUERY)
    state = StagingWorker().run(state)
    state = StayWorker().run(state)
    state = ActivityWorker().run(state)
    state = TransitWorker().run(state)

    state = FinancialAuditor().run(state)
    assert state.financial_audit is not None
    assert state.financial_audit.total_estimated_inr > 0
    assert state.financial_audit.budget_cap_inr == 80000.0
    assert state.financial_audit.is_within_budget is True
    assert state.financial_audit.remaining_headroom_inr >= 0


def test_critic_and_constraint_relaxation():
    """Verify that Critic applies Constraint Relaxation on impossible budgets without looping."""
    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(TIGHT_BUDGET_QUERY)
    state = StagingWorker().run(state)
    state = StayWorker().run(state)
    state = ActivityWorker().run(state)
    state = TransitWorker().run(state)
    state = FinancialAuditor().run(state)

    # Audit must detect overrun
    assert state.financial_audit.is_within_budget is False

    # Critic evaluates
    critic = CriticAgent()
    state = critic.evaluate_and_replan(state)

    assert state.critic_passed is True
    assert state.constraint_relaxation_applied is True
    assert any("Constraint Relaxation" in note for note in state.critic_notes)


def test_end_to_end_v2_engine():
    """Verify end-to-end PlanAndSolveEngine pipeline delivers schema-guaranteed output."""
    engine = PlanAndSolveEngine(provider="mock")
    plan: TripPlanResponse = engine.plan(BENCHMARK_QUERY)

    assert plan.destination == "Kashmir"
    assert plan.duration_days == 5
    assert len(plan.days) == 5
    assert plan.budget_summary.budget_cap_inr == 80000.0
    assert plan.budget_summary.is_within_budget is True

    # Spatial consistency check: Day 1 must have Srinagar stay & activity, Day 4 must have Gulmarg stay
    assert plan.days[0].region == "Srinagar"
    assert plan.days[0].stay.region == "Srinagar"
    assert plan.days[3].region == "Gulmarg"
    assert plan.days[3].stay.region == "Gulmarg"

    # Negative constraint check: no adventure sports in any day
    for day in plan.days:
        for act in day.activities:
            assert act.is_adventure is False


def test_api_v2_planner_endpoint():
    """Verify HTTP POST /api/v2/planner/plan endpoint returns 200 OK with valid schema."""
    response = client.post(
        "/api/v2/planner/plan",
        json={"user_query": BENCHMARK_QUERY, "preferred_provider": "mock"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["destination"] == "Kashmir"
    assert len(data["days"]) == 5
    assert data["budget_summary"]["budget_cap_inr"] == 80000.0
