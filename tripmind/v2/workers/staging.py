"""Geographic & Temporal Staging Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Spatial-Temporal Partitioning:
In Level 1 ReAct, the agent attempted to query regions, stays, and activities
in a single unpartitioned sequence, causing Gulmarg Gondola rides to bleed into
Srinagar hotel days.

In Level 2, the StagingWorker executes FIRST. It locks each day of the itinerary
to an accessible region hub before any stays or activities are sourced.
Zero hardcoded city names or hardcoded day-length branches are used.
"""

from typing import List, Optional, Any
import json

from tripmind.v2.state import WorkingMemoryState, DayRegionStage, StagingPlan
from tripmind.tools.regions import search_regions
from tripmind.schemas.tools import RegionSearchResult, RegionInfo
from tripmind.core.llm import LLMClient


class StagingWorker:
    """Worker responsible for geographical accessibility and temporal partitioning."""

    def __init__(self, llm_client: Optional[LLMClient] = None, mcp_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.mcp_client = mcp_client

    def run(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Executes regional accessibility analysis and partitions days into hubs."""
        dest = state.constraints.destination
        month = state.constraints.month or "Current"
        duration = state.constraints.duration_days

        state.mark_task_running("T1_STAGING")
        state.log_milestone("Milestone 1: Staging", "running", f"Analyzing regional accessibility for {dest} in {month}...")

        # 1. Tool perception via MCP or local function
        tool_input = {"destination": dest, "month": month}
        if self.mcp_client:
            raw_res = self.mcp_client.call_tool_sync("search_regions", tool_input)
            region_res = RegionSearchResult(**raw_res) if isinstance(raw_res, dict) else RegionSearchResult.model_validate_json(raw_res)
            tool_label = "search_regions (via MCP Protocol)"
        else:
            region_res: RegionSearchResult = search_regions(destination=dest, month=month)
            tool_label = "search_regions"
        
        state.add_trace_step(
            thought=f"Executing StagingWorker: Querying regional accessibility and seasonal closures for '{dest}' in month '{month}' (via {tool_label}).",
            tool_name=tool_label,
            tool_input=tool_input,
            observation=region_res.model_dump_json(indent=2),
        )

        # 2. Filter accessible regions (respecting pass closures)
        accessible = [r for r in region_res.regions if r.is_accessible]
        if not accessible:
            # Fallback if no sub-regions found: treat destination itself as the single primary hub
            accessible = [
                RegionInfo(
                    region_name=dest,
                    is_accessible=True,
                    status_note="Accessible primary destination hub.",
                    temp_range_celsius="Moderate",
                    daylight_hours="10 hours",
                    sunset_time="6:00 PM",
                    recommended_stay_nights=duration,
                    scenic_highlights=[f"Highlights of {dest}"],
                )
            ]
        state.accessible_regions = accessible
        
        if region_res.safety_advisory:
            state.safety_advisories.append(region_res.safety_advisory)
        for r in region_res.regions:
            if not r.is_accessible:
                state.safety_advisories.append(f"{r.region_name}: {r.status_note}")

        # 3. Create dynamic spatial partitions (DayRegionStage)
        stages = self._partition_days(duration, accessible, state.constraints.pace, state)
        state.day_stages = stages

        summary = f"Partitioned {duration} days across {len(accessible)} accessible hubs: " + " -> ".join([f"D{s.day_number}:{s.region}" for s in stages])
        state.mark_task_completed("T1_STAGING", summary=summary)
        state.log_milestone("Milestone 1: Staging", "completed", summary)

        return state

    def _partition_days(
        self,
        duration: int,
        accessible: List[RegionInfo],
        pace: str,
        state: WorkingMemoryState,
    ) -> List[DayRegionStage]:
        """Creates locked day-by-day regional stages dynamically for ANY destination and duration."""
        # 1. If LLM client is available, use LLM spatial reasoning to generate stages
        if self.llm_client:
            try:
                hubs_summary = [
                    {
                        "name": r.region_name,
                        "advisory": r.status_note,
                        "daylight": r.daylight_hours,
                        "sunset": r.sunset_time,
                        "recommended_nights": r.recommended_stay_nights,
                        "highlights": r.scenic_highlights,
                    }
                    for r in accessible
                ]
                prompt = (
                    f"You are the Spatial Staging Planner. Allocate {duration} days for a trip to '{state.constraints.destination}'.\n"
                    f"Traveler Pace: {pace} | Season/Month: {state.constraints.month or 'Not specified'}\n"
                    f"Accessible Hubs: {json.dumps(hubs_summary, indent=2)}\n\n"
                    f"Rules:\n"
                    f"- Generate exactly {duration} day stages (day_number 1 to {duration}).\n"
                    f"- If pace is 'relaxed', do not split across more than 2 hubs.\n"
                    f"- When moving from Hub A to Hub B, set is_transit_day=True with transit_from and transit_to.\n"
                    f"- On Day 1, set is_transit_day=True (arrival transfer from Airport/Station to Hub 1).\n"
                    f"- On Day {duration}, set is_transit_day=True (departure transfer from last hub to Airport/Station).\n"
                    f"- For days spent exploring inside the same hub, set is_transit_day=False."
                )
                staging_plan: StagingPlan = self.llm_client.extract_structured(
                    prompt=prompt,
                    schema=StagingPlan,
                    system_instruction="You are a spatial-temporal travel planner. Produce a valid StagingPlan with day_stages."
                )
                if staging_plan and len(staging_plan.stages) == duration:
                    return staging_plan.stages
            except Exception:
                pass  # Fall back to dynamic mathematical partitioner

        # 2. Dynamic Mathematical Partitioner (works for any city, any duration, completely unhardcoded)
        stages: List[DayRegionStage] = []
        # For relaxed pace, limit to 2 hubs; for moderate, up to 3
        max_hubs = 2 if pace == "relaxed" else 3
        active_hubs = accessible[:max_hubs]
        num_hubs = len(active_hubs)

        # Distribute duration days across active hubs
        days_per_hub = [duration // num_hubs] * num_hubs
        # Distribute remainder to the primary (first) hub
        remainder = duration % num_hubs
        days_per_hub[0] += remainder

        current_day = 1
        for hub_idx, hub in enumerate(active_hubs):
            hub_days = days_per_hub[hub_idx]
            for d in range(hub_days):
                is_arrival = (current_day == 1)
                is_intercity_transfer = (d == 0 and hub_idx > 0)
                is_departure = (current_day == duration)

                is_transit = is_arrival or is_intercity_transfer or is_departure
                transit_from = None
                transit_to = None

                if is_arrival:
                    transit_from = f"{hub.region_name} Airport"
                    transit_to = hub.region_name
                    theme = f"Arrival in {hub.region_name} & Welcome Leisure"
                    pace_note = "Arrival and check-in; daylight limits factored in."
                elif is_intercity_transfer:
                    prev_hub = active_hubs[hub_idx - 1].region_name
                    transit_from = prev_hub
                    transit_to = hub.region_name
                    theme = f"Scenic Transfer from {prev_hub} to {hub.region_name}"
                    pace_note = f"Intercity transfer between {prev_hub} and {hub.region_name}."
                elif is_departure:
                    transit_from = hub.region_name
                    transit_to = f"{active_hubs[0].region_name} Airport"
                    theme = f"Departure Transfer from {hub.region_name}"
                    pace_note = "Departure logistics and transit to airport."
                else:
                    theme = f"Exploring {hub.region_name} & Cultural Highlights"
                    pace_note = f"Dedicated leisure day in {hub.region_name} with zero intercity travel."

                stages.append(
                    DayRegionStage(
                        day_number=current_day,
                        region=hub.region_name,
                        title_theme=theme,
                        is_transit_day=is_transit,
                        transit_from=transit_from,
                        transit_to=transit_to,
                        pace_notes=pace_note,
                    )
                )
                current_day += 1

        return stages
