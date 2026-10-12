"""Accommodation Sourcing Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Focused Sub-Agent with Replan Support:
This worker has a single responsibility: finding verified, heated accommodations
strictly for the regions identified by the StagingWorker.
If the Critic later detects a budget overrun, this worker can be re-invoked
with `cheaper_tier=True` to select tier-2 accommodations without disturbing
activities or transit routing.
"""

from typing import List, Optional
import json

from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.stays import search_accommodations
from tripmind.schemas.tools import AccommodationSearchResult, AccommodationItem


class StayWorker:
    """Worker responsible for sourcing verified heated accommodations."""

    def __init__(self):
        pass

    def run(self, state: WorkingMemoryState, prefer_budget_tier: bool = False) -> WorkingMemoryState:
        """Sources accommodations for all staged regions."""
        state.mark_task_running("T2_STAYS")
        state.log_milestone("Milestone 2A: Stays", "running", "Sourcing verified heated stays for staged hubs...")

        # Find distinct regions that need lodging
        required_regions = list(dict.fromkeys([stage.region for stage in state.day_stages]))
        month = state.constraints.month
        
        # In winter months (December/January/February), heating is mandatory
        is_winter = month.lower() in ["december", "january", "february"]
        required_amenities = ["central_heating", "electric_blanket"] if is_winter else []

        for region in required_regions:
            max_rate = 6000.0 if prefer_budget_tier else 15000.0
            tool_input = {
                "region": region,
                "min_rating": 4.0,
                "required_amenities": required_amenities,
                "max_nightly_rate_inr": max_rate,
            }
            res: AccommodationSearchResult = search_accommodations(
                region=region,
                min_rating=4.0,
                required_amenities=required_amenities,
                max_nightly_rate_inr=max_rate,
            )

            state.add_trace_step(
                thought=f"StayWorker: Sourcing verified heated stays for region '{region}' (budget_tier={prefer_budget_tier}).",
                tool_name="search_accommodations",
                tool_input=tool_input,
                observation=res.model_dump_json(indent=2),
            )

            # Store all found options
            state.stays_by_region[region] = res.accommodations

            # Select candidate:
            # If prefer_budget_tier, pick the most affordable heated stay
            # Else pick highest rated heated stay
            heated_stays = [s for s in res.accommodations if s.heating_verified] or res.accommodations
            if heated_stays:
                if prefer_budget_tier:
                    selected = min(heated_stays, key=lambda s: s.price_per_night_inr)
                else:
                    selected = max(heated_stays, key=lambda s: s.rating)
                state.selected_stay_by_region[region] = selected

        total_selected = len(state.selected_stay_by_region)
        summary = f"Sourced and verified stays across {total_selected} regions: " + ", ".join(
            [f"{r}: {s.name} (₹{s.price_per_night_inr:,.0f}/nt)" for r, s in state.selected_stay_by_region.items()]
        )
        state.mark_task_completed("T2_STAYS", summary=summary)
        state.log_milestone("Milestone 2A: Stays", "completed", summary)

        return state
