"""Accommodation Sourcing Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Focused Sub-Agent with Replan Support:
This worker has a single responsibility: finding verified, appropriate accommodations
strictly for the regions identified by the StagingWorker.
It dynamically calculates nightly budget ceilings based on user budget constraints
and environmental heating requirements.
"""

from typing import List, Optional
import json

from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.stays import search_accommodations
from tripmind.schemas.tools import AccommodationSearchResult, AccommodationItem


class StayWorker:
    """Worker responsible for sourcing verified accommodations per staged region."""

    def __init__(self):
        pass

    def run(self, state: WorkingMemoryState, prefer_budget_tier: bool = False) -> WorkingMemoryState:
        """Sources accommodations for all staged regions."""
        state.mark_task_running("T2_STAYS")
        state.log_milestone("Milestone 2A: Stays", "running", "Sourcing verified stays for staged hubs...")

        # Find distinct regions that need lodging
        required_regions = list(dict.fromkeys([stage.region for stage in state.day_stages]))
        if not required_regions:
            required_regions = [state.constraints.destination]

        month = state.constraints.month
        
        # Check if sub-zero / winter heating is required based on month or region temperature
        is_winter = bool(month and month.lower() in ["december", "january", "february"])
        has_subzero = any("-" in r.temp_range_celsius for r in state.accessible_regions)
        needs_heating = is_winter or has_subzero
        required_amenities = ["central_heating", "electric_blanket"] if needs_heating else []

        # Dynamically calculate nightly accommodation ceiling from user's budget cap
        nights = max(1, state.constraints.duration_nights)
        budget_cap = state.constraints.budget_cap_inr
        if budget_cap:
            nightly_budget = (budget_cap * 0.45) / nights
            max_rate = max(2500.0, nightly_budget * 0.75) if prefer_budget_tier else max(4000.0, nightly_budget * 1.25)
        else:
            max_rate = 8000.0 if prefer_budget_tier else 18000.0

        for region in required_regions:
            tool_input = {
                "region": region,
                "min_rating": 3.8 if prefer_budget_tier else 4.0,
                "required_amenities": required_amenities,
                "max_nightly_rate_inr": max_rate,
            }
            res: AccommodationSearchResult = search_accommodations(
                region=region,
                min_rating=3.8 if prefer_budget_tier else 4.0,
                required_amenities=required_amenities,
                max_nightly_rate_inr=max_rate,
            )

            state.add_trace_step(
                thought=f"StayWorker: Sourcing stays for region '{region}' (budget_tier={prefer_budget_tier}, max_rate=₹{max_rate:,.0f}).",
                tool_name="search_accommodations",
                tool_input=tool_input,
                observation=res.model_dump_json(indent=2),
            )

            # Store all found options
            state.stays_by_region[region] = res.accommodations

            # Select candidate:
            # If heating required, prioritize heated stays
            valid_candidates = [s for s in res.accommodations if s.heating_verified] if needs_heating else res.accommodations
            if not valid_candidates:
                valid_candidates = res.accommodations

            if valid_candidates:
                if prefer_budget_tier:
                    selected = min(valid_candidates, key=lambda s: s.price_per_night_inr)
                else:
                    selected = max(valid_candidates, key=lambda s: s.rating)
                state.selected_stay_by_region[region] = selected

        total_selected = len(state.selected_stay_by_region)
        summary = f"Sourced stays across {total_selected} regions: " + ", ".join(
            [f"{r}: {s.name} (₹{s.price_per_night_inr:,.0f}/nt)" for r, s in state.selected_stay_by_region.items()]
        )
        state.mark_task_completed("T2_STAYS", summary=summary)
        state.log_milestone("Milestone 2A: Stays", "completed", summary)

        return state
