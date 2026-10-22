"""Deterministic Financial Auditor for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Deterministic Arithmetic over LLM Hallucination:
LLMs are notoriously unreliable at arithmetic (multiplication, 5% GST, percentages).
The FinancialAuditor runs pure deterministic Python arithmetic via the
`calculate_budget_breakdown` tool, evaluating total costs against the LOCKED budget cap.
"""

from typing import Dict, List, Optional, Any

from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.budget import calculate_budget_breakdown
from tripmind.schemas.tools import BudgetBreakdownResult


class FinancialAuditor:
    """Auditor responsible for exact financial calculation and budget compliance check."""

    def __init__(self, mcp_client: Optional[Any] = None):
        self.mcp_client = mcp_client

    def run(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Computes deterministic budget breakdown and audits against locked cap."""
        state.mark_task_running("T5_AUDIT")
        state.log_milestone("Milestone 3: Financial Audit", "running", "Auditing total costs against locked budget cap...")

        # 1. Calculate stays cost for nights
        # We need duration_nights stays
        nights = state.constraints.duration_nights
        stages = state.day_stages
        stays_cost = 0.0

        for i in range(nights):
            if i < len(stages):
                region = stages[i].region
                stay = state.selected_stay_by_region.get(region)
                if stay:
                    stays_cost += stay.price_per_night_inr

        # 2. Calculate transit cost from staged routes
        transit_cost = sum(route.estimated_cost_inr for route in state.transit_routes.values())
        if transit_cost == 0.0:
            transit_cost = 3500.0  # Baseline local transit estimate if no intercity legs

        # 3. Calculate activities cost (top 1-2 curated activities per region)
        activities_cost = 0.0
        for region, acts in state.activities_by_region.items():
            for act in acts[:2]:  # 2 activities per region
                activities_cost += act.cost_inr

        # 4. Standard dining estimate (e.g. ₹1,800/day for 2 people across duration)
        food_cost = state.constraints.duration_days * 1800.0

        # 5. Deterministic budget calculation via tool
        budget_cap = state.constraints.budget_cap_inr
        tool_input = {
            "stays_cost_inr": stays_cost,
            "transit_cost_inr": transit_cost,
            "food_cost_inr": food_cost,
            "activities_cost_inr": activities_cost,
            "emergency_buffer_pct": 10.0,
            "max_budget_cap_inr": budget_cap,
        }

        if self.mcp_client:
            raw_res = self.mcp_client.call_tool_sync("calculate_budget_breakdown", tool_input)
            breakdown = BudgetBreakdownResult(**raw_res) if isinstance(raw_res, dict) else BudgetBreakdownResult.model_validate_json(raw_res)
            tool_label = "calculate_budget_breakdown (via MCP Protocol)"
        else:
            breakdown: BudgetBreakdownResult = calculate_budget_breakdown(**tool_input)
            tool_label = "calculate_budget_breakdown"

        cap_display = f"₹{budget_cap:,.0f}" if budget_cap else "Unconstrained"
        state.add_trace_step(
            thought=(
                f"FinancialAuditor: Running deterministic arithmetic for stays (₹{stays_cost:,.0f}), "
                f"transit (₹{transit_cost:,.0f}), food (₹{food_cost:,.0f}), activities (₹{activities_cost:,.0f}) "
                f"against budget ceiling: {cap_display} (via {tool_label})."
            ),
            tool_name=tool_label,
            tool_input=tool_input,
            observation=breakdown.model_dump_json(indent=2),
        )

        state.financial_audit = breakdown

        summary = (
            f"Total: ₹{breakdown.total_estimated_inr:,.0f} | Cap: {cap_display} | "
            f"Compliant: {breakdown.is_within_budget} | Remaining: ₹{breakdown.remaining_headroom_inr:,.0f}"
        )
        state.mark_task_completed("T5_AUDIT", summary=summary)
        state.log_milestone("Milestone 3: Financial Audit", "completed", summary)

        return state
