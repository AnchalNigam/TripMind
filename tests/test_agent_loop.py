"""Tests for the ReAct (Reasoning + Acting) Agent loop mechanics."""

import pytest
from tripmind.core.agent import ReActAgent
from tripmind.core.llm import MockProvider
from tripmind.tools.registry import default_registry
from tripmind.schemas.itinerary import TripPlanResponse


def test_react_agent_full_loop_execution(mock_agent):
    """The ReAct agent must execute multi-turn thought-action-observation cycles and synthesize a valid plan."""
    query = (
        "I want to visit Kashmir in December for 5 days. I'm going with my wife. "
        "We don't want a hectic trip. We love scenic places and food, but aren't "
        "interested in adventure activities. Budget around ₹80k excluding flights."
    )

    plan: TripPlanResponse = mock_agent.plan(query)

    # 1. Structure Verification
    assert plan.duration_days == 5
    assert plan.duration_nights == 4
    assert len(plan.days) == 5

    # 2. ReAct Execution Trace Verification
    assert len(plan.execution_trace) == 5
    tool_sequence = [step.tool_name for step in plan.execution_trace]
    expected_sequence = [
        "search_regions",
        "calculate_travel_route",
        "search_accommodations",
        "get_activities",
        "calculate_budget_breakdown",
    ]
    assert tool_sequence == expected_sequence

    # Verify each trace step contains reasoning (Thought) and feedback (Observation)
    for step in plan.execution_trace:
        assert len(step.thought) > 0
        assert step.tool_name is not None
        assert step.tool_input is not None
        assert step.observation is not None

    # 3. Constraint Satisfactions
    assert plan.constraints_verified["budget_compliant"] is True
    assert plan.constraints_verified["winter_heating_guaranteed"] is True
    assert plan.constraints_verified["no_adventure_sports"] is True
    assert plan.constraints_verified["relaxed_pace"] is True

    # 4. Budget Compliance
    assert plan.budget_summary.is_within_budget is True
    assert plan.budget_summary.total_estimated_inr <= 80000.0


def test_react_agent_max_iterations_guardrail():
    """Agent must terminate safely if max iterations threshold is reached."""
    class InfiniteLoopProvider(MockProvider):
        def generate_turn(self, messages, tools):
            # Always requests another tool call without ever terminating
            from tripmind.core.llm import LLMTurnResponse, ToolCallItem
            return LLMTurnResponse(
                thought="I am trapped in an infinite loop.",
                tool_calls=[
                    ToolCallItem(call_id="call_inf", name="search_regions", arguments={"destination": "Kashmir", "month": "December"})
                ],
            )

    runaway_agent = ReActAgent(
        provider=InfiniteLoopProvider(),
        registry=default_registry,
        max_iterations=3,  # Strict limit
    )

    with pytest.raises(RuntimeError) as exc_info:
        runaway_agent.plan("Plan an impossible trip")

    assert "exceeded maximum iterations" in str(exc_info.value)
