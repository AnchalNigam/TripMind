"""Accommodation Sourcing Deliberative Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Sub-Agent Persona Deliberation:
1. In toy implementations, workers call tools and use dumb deterministic heuristics
   (e.g. `min(price)` or `options[0]`).
2. In a true Agentic DAG, the worker is an autonomous Persona Specialist:
   - Perception: Retrieves candidate accommodations via domain tools.
   - Cognition & Deliberation: The agent analyzes candidates against user budget ceiling,
     traveler profile (Couple, Family), heating safety requirements, and location.
   - Action: Emits the chosen accommodation along with an explicit rationale recorded
     in working memory.
"""

from typing import List, Optional, Dict, Any
import json
from pydantic import BaseModel, Field

from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.stays import search_accommodations
from tripmind.schemas.tools import AccommodationSearchResult, AccommodationItem
from tripmind.core.llm import LLMClient


class StayDeliberationDecision(BaseModel):
    """Structured decision emitted by the Stay Specialist during deliberation."""
    selected_name: str = Field(..., description="Exact name of the selected accommodation from candidate options.")
    rationale: str = Field(..., description="Explanation of why this accommodation best satisfies user constraints, budget, and amenities.")


class StayWorker:
    """Deliberative Sub-Agent responsible for sourcing verified accommodations per staged region."""

    def __init__(self, llm_client: Optional[LLMClient] = None, mcp_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.mcp_client = mcp_client

    def run(self, state: WorkingMemoryState, prefer_budget_tier: bool = False) -> WorkingMemoryState:
        """Sources accommodations for all staged regions with persona deliberation."""
        state.mark_task_running("T2_STAYS")
        state.log_milestone("Milestone 2A: Stays", "running", "Sourcing and deliberating verified stays for staged hubs...")

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
            if self.mcp_client:
                raw_res = self.mcp_client.call_tool_sync("search_accommodations", tool_input)
                res = AccommodationSearchResult(**raw_res) if isinstance(raw_res, dict) else AccommodationSearchResult.model_validate_json(raw_res)
                tool_label = "search_accommodations (via MCP Protocol)"
            else:
                res: AccommodationSearchResult = search_accommodations(**tool_input)
                tool_label = "search_accommodations"

            state.add_trace_step(
                thought=f"StayWorker [Perception]: Sourcing stays for region '{region}' (via {tool_label}, budget_tier={prefer_budget_tier}, max_rate=₹{max_rate:,.0f}).",
                tool_name=tool_label,
                tool_input=tool_input,
                observation=res.model_dump_json(indent=2),
            )

            # Store all found options
            state.stays_by_region[region] = res.accommodations

            # Filter candidates: if heating required, prioritize heated stays
            valid_candidates = [s for s in res.accommodations if s.heating_verified] if needs_heating else res.accommodations
            if not valid_candidates:
                valid_candidates = res.accommodations

            if valid_candidates:
                selected_item, rationale = self._deliberate_stay_selection(
                    region=region,
                    candidates=valid_candidates,
                    prefer_budget_tier=prefer_budget_tier,
                    state=state,
                )
                state.selected_stay_by_region[region] = selected_item
                state.deliberation_rationales[f"stay_{region}"] = rationale

                state.add_trace_step(
                    thought=f"StayWorker [Deliberation]: Selected '{selected_item.name}' for {region}. Rationale: {rationale}",
                    observation=f"Selected stay: {selected_item.name} at ₹{selected_item.price_per_night_inr:,.0f}/night."
                )

        total_selected = len(state.selected_stay_by_region)
        summary = f"Deliberated stays across {total_selected} regions: " + ", ".join(
            [f"{r}: {s.name} (₹{s.price_per_night_inr:,.0f}/nt)" for r, s in state.selected_stay_by_region.items()]
        )
        state.mark_task_completed("T2_STAYS", summary=summary)
        state.log_milestone("Milestone 2A: Stays", "completed", summary)

        return state

    def _deliberate_stay_selection(
        self,
        region: str,
        candidates: List[AccommodationItem],
        prefer_budget_tier: bool,
        state: WorkingMemoryState,
    ) -> tuple[AccommodationItem, str]:
        """Cognitive deliberation step over candidate stays using LLM or structured heuristic."""
        if self.llm_client and len(candidates) > 1:
            try:
                candidates_summary = [
                    {
                        "name": c.name,
                        "rating": c.rating,
                        "price_per_night_inr": c.price_per_night_inr,
                        "heating_verified": c.heating_verified,
                        "amenities": c.amenities,
                        "suitability": c.couple_suitability,
                    }
                    for c in candidates
                ]
                prompt = (
                    f"You are the Stay Specialist Agent for an itinerary in {region}.\n"
                    f"User Profile: {state.constraints.traveler_profile}, Pace: {state.constraints.pace}.\n"
                    f"Budget Mode: {'Budget/Tier-2 focus' if prefer_budget_tier else 'Standard / Quality focus'}.\n"
                    f"Candidate Hotels:\n{json.dumps(candidates_summary, indent=2)}\n\n"
                    f"Select the single best hotel that balances traveler comfort, amenities, and budget.\n"
                    f"Return your decision strictly in the structured schema."
                )
                decision: StayDeliberationDecision = self.llm_client.extract_structured(
                    prompt=prompt,
                    schema=StayDeliberationDecision,
                    system_instruction="You are an expert hospitality curation agent. Select the best hotel from candidates."
                )
                for cand in candidates:
                    if cand.name.strip().lower() == decision.selected_name.strip().lower():
                        return cand, decision.rationale
            except Exception:
                pass  # Fallback to deterministic heuristic on LLM parsing error

        # Deliberative Heuristic fallback
        if prefer_budget_tier:
            selected = min(candidates, key=lambda s: s.price_per_night_inr)
            rationale = (
                f"Selected '{selected.name}' as the most cost-effective verified accommodation "
                f"(₹{selected.price_per_night_inr:,.0f}/night, rating {selected.rating}) to maintain budget headroom."
            )
        else:
            selected = max(candidates, key=lambda s: s.rating)
            rationale = (
                f"Selected '{selected.name}' for highest guest rating ({selected.rating}/5.0) "
                f"and verified heating comfort at ₹{selected.price_per_night_inr:,.0f}/night."
            )
        return selected, rationale
