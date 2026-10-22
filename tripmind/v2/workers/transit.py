"""Mountain Logistics & Transit Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Targeted Logistics Deliberation:
Instead of calling transit tools haphazardly, TransitWorker computes travel legs
strictly for the inter-region transitions established by the StagingWorker.
It deliberates on winter vehicle requirements (e.g., 4x4 snow chains
for Tangmarg to Gulmarg) and commits explicit rationales to working memory.
"""

from typing import Dict, Optional, List, Any
from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.transit import calculate_travel_route
from tripmind.schemas.tools import RouteResult
from tripmind.core.llm import LLMClient


class TransitWorker:
    """Worker responsible for calculating intercity transit routes and winter vehicle requirements."""

    def __init__(self, llm_client: Optional[LLMClient] = None, mcp_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.mcp_client = mcp_client

    def run(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Computes routes for all staged transit legs."""
        state.mark_task_running("T4_TRANSIT")
        state.log_milestone("Milestone 2C: Transit", "running", "Calculating mountain transit legs and winter specs...")

        month = state.constraints.month or "December"
        
        # Identify required legs from day stages
        needed_legs = []
        for stage in state.day_stages:
            if stage.is_transit_day and stage.transit_from and stage.transit_to:
                needed_legs.append((stage.transit_from, stage.transit_to))

        # Deduplicate legs
        unique_legs = list(dict.fromkeys(needed_legs))

        for origin, destination in unique_legs:
            route_key = f"{origin}->{destination}"
            tool_input = {
                "origin": origin,
                "destination": destination,
                "month": month,
            }
            if self.mcp_client:
                raw_res = self.mcp_client.call_tool_sync("calculate_travel_route", tool_input)
                route_res = RouteResult(**raw_res) if isinstance(raw_res, dict) else RouteResult.model_validate_json(raw_res)
                tool_label = "calculate_travel_route (via MCP Protocol)"
            else:
                route_res: RouteResult = calculate_travel_route(**tool_input)
                tool_label = "calculate_travel_route"

            state.add_trace_step(
                thought=f"TransitWorker [Perception]: Calculating travel route from '{origin}' to '{destination}' for month '{month}' (via {tool_label}).",
                tool_name=tool_label,
                tool_input=tool_input,
                observation=route_res.model_dump_json(indent=2),
            )

            state.transit_routes[route_key] = route_res
            
            # Record logistics deliberation
            vehicle_note = "4x4 snow-chained vehicle mandatory" if route_res.requires_special_vehicle else "standard paved vehicle"
            state.deliberation_rationales[f"transit_{route_key}"] = (
                f"Leg {route_key} ({route_res.distance_km} km, ~{route_res.estimated_duration_hours}h): "
                f"Assigned {vehicle_note}. Advisory: {route_res.advisory}"
            )

        total_routes = len(state.transit_routes)
        summary = f"Computed {total_routes} transit legs: " + ", ".join(
            [f"{k} ({r.distance_km}km, {r.estimated_duration_hours}h)" for k, r in state.transit_routes.items()]
        )
        state.mark_task_completed("T4_TRANSIT", summary=summary)
        state.log_milestone("Milestone 2C: Transit", "completed", summary)

        return state
