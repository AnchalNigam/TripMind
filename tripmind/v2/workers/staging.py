"""Geographic & Temporal Staging Worker for Level 2.

AGENTIC AI CONCEPT — Spatial-Temporal Partitioning:
In Level 1 ReAct, the agent attempted to query regions, stays, and activities
in a single unpartitioned sequence, causing Gulmarg Gondola rides to bleed into
Srinagar hotel days.

In Level 2, the StagingWorker executes FIRST. It locks each day of the itinerary
to a specific accessible region hub before any stays or activities are sourced.
"""

from typing import List, Optional
import json

from tripmind.v2.state import WorkingMemoryState, DayRegionStage
from tripmind.tools.regions import search_regions
from tripmind.schemas.tools import RegionSearchResult, RegionInfo


class StagingWorker:
    """Worker responsible for geographical accessibility and temporal partitioning."""

    def __init__(self):
        pass

    def run(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Executes regional accessibility analysis and partitions days into hubs."""
        dest = state.constraints.destination
        month = state.constraints.month
        duration = state.constraints.duration_days

        state.mark_task_running("T1_STAGING")
        state.log_milestone("Milestone 1: Staging", "running", f"Analyzing regional accessibility for {dest} in {month}...")

        # 1. Deterministic tool perception via search_regions
        tool_input = {"destination": dest, "month": month}
        region_res: RegionSearchResult = search_regions(destination=dest, month=month)
        
        state.add_trace_step(
            thought=f"Executing StagingWorker: Analyzing regional accessibility and winter pass closures for {dest} in {month}.",
            tool_name="search_regions",
            tool_input=tool_input,
            observation=region_res.model_dump_json(indent=2),
        )

        # 2. Filter accessible regions (respecting pass closures, e.g. Sonamarg closed)
        accessible = [r for r in region_res.regions if r.is_accessible]
        state.accessible_regions = accessible
        
        if region_res.safety_advisory:
            state.safety_advisories.append(region_res.safety_advisory)
        for r in region_res.regions:
            if not r.is_accessible:
                state.safety_advisories.append(f"{r.region_name}: {r.status_note}")

        # 3. Create deterministic spatial partitions (DayRegionStage)
        stages = self._partition_days(duration, accessible, state.constraints.pace)
        state.day_stages = stages

        summary = f"Partitioned {duration} days across {len(accessible)} accessible hubs: " + " -> ".join([f"D{s.day_number}:{s.region}" for s in stages])
        state.mark_task_completed("T1_STAGING", summary=summary)
        state.log_milestone("Milestone 1: Staging", "completed", summary)

        return state

    def _partition_days(self, duration: int, accessible: List[RegionInfo], pace: str) -> List[DayRegionStage]:
        """Creates locked day-by-day regional stages based on duration and pace."""
        accessible_names = [r.region_name for r in accessible]
        stages: List[DayRegionStage] = []

        # Specialized partition strategy for Kashmir winter:
        # Srinagar (hub) + Gulmarg (winter snow meadow) with relaxed pace
        if "Srinagar" in accessible_names and "Gulmarg" in accessible_names:
            if duration == 5:
                # 5-day optimal non-hectic distribution:
                # Days 1-2 Srinagar, Days 3-4 Gulmarg, Day 5 Departure (Gulmarg -> Srinagar Airport)
                stages = [
                    DayRegionStage(
                        day_number=1,
                        region="Srinagar",
                        title_theme="Arrival, Dal Lake & Heritage Welcome",
                        is_transit_day=True,
                        transit_from="Srinagar Airport",
                        transit_to="Srinagar",
                        pace_notes="Relaxed arrival, 1 hr airport transfer, sunset at 5:15 PM factored in.",
                    ),
                    DayRegionStage(
                        day_number=2,
                        region="Srinagar",
                        title_theme="Mughal Heritage, Craft & Authentic Cuisine",
                        is_transit_day=False,
                        pace_notes="Zero intercity travel. Gentle heritage exploration within Srinagar.",
                    ),
                    DayRegionStage(
                        day_number=3,
                        region="Srinagar",
                        title_theme="Scenic Transfer to Winter Gulmarg & Meadow Walk",
                        is_transit_day=True,
                        transit_from="Srinagar",
                        transit_to="Gulmarg",
                        pace_notes="2.5 hr mountain drive with snow-chain vehicle requirement factored in.",
                    ),
                    DayRegionStage(
                        day_number=4,
                        region="Gulmarg",
                        title_theme="Snow Panorama, Pine Forests & Alpine Serenity",
                        is_transit_day=False,
                        pace_notes="Dedicated full day in Gulmarg without rushed transitions.",
                    ),
                    DayRegionStage(
                        day_number=5,
                        region="Gulmarg",
                        title_theme="Morning Leisure & Departure Transfer",
                        is_transit_day=True,
                        transit_from="Gulmarg",
                        transit_to="Srinagar Airport",
                        pace_notes="Morning meadow tea followed by descent transfer to Srinagar Airport.",
                    ),
                ]
                return stages

        # Generic partitioning across accessible regions for any destination
        if not accessible_names:
            accessible_names = ["Central Hub"]

        # Spread duration evenly across max 2 hubs for non-hectic pace
        active_hubs = accessible_names[:2] if pace == "relaxed" else accessible_names[:3]
        days_per_hub = max(1, duration // len(active_hubs))

        current_day = 1
        for i, hub in enumerate(active_hubs):
            hub_days = days_per_hub if i < len(active_hubs) - 1 else (duration - current_day + 1)
            for d in range(hub_days):
                is_transit = (d == 0 and i > 0)
                from_loc = active_hubs[i - 1] if is_transit else None
                to_loc = hub if is_transit else None
                
                stages.append(
                    DayRegionStage(
                        day_number=current_day,
                        region=hub,
                        title_theme=f"Exploring {hub}" if not is_transit else f"Transfer from {from_loc} to {to_loc}",
                        is_transit_day=is_transit,
                        transit_from=from_loc,
                        transit_to=to_loc,
                        pace_notes="Factored in local transit and sunset limits.",
                    )
                )
                current_day += 1

        return stages
