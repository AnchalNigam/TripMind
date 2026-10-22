"""Activity Curation Deliberative Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Sub-Agent Deliberation & Negative Invariant Enforcement:
1. Perception: Queries domain activities strictly within each staged region.
2. Negative Invariant Enforcement: Filters out adventure sports if `exclude_adventure` is True.
3. Cognition & Deliberation: The Activity Specialist Agent reasons over traveler pace,
   daylight constraints, and special interests (e.g. scenic viewpoints, culinary depth)
   to curate an unhurried, contextually coherent set of activities per hub.
"""

from typing import List, Optional, Dict, Any
import json
from pydantic import BaseModel, Field

from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.activities import get_activities
from tripmind.schemas.tools import ActivitySearchResult, ActivityItem
from tripmind.core.llm import LLMClient


class ActivityDeliberationDecision(BaseModel):
    """Structured decision emitted by the Activity Specialist during deliberation."""
    selected_activity_names: List[str] = Field(
        default_factory=list,
        description="Names of chosen activities strictly matching candidate options."
    )
    rationale: str = Field(
        ...,
        description="Detailed explanation of how selected activities match pace, daylight, and interests."
    )


class ActivityWorker:
    """Deliberative Sub-Agent responsible for sourcing and curating activities per staged region."""

    def __init__(self, llm_client: Optional[LLMClient] = None, mcp_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.mcp_client = mcp_client

    def run(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Sources and deliberates activities for each distinct staged region."""
        state.mark_task_running("T3_ACTIVITIES")
        state.log_milestone("Milestone 2B: Activities", "running", "Curation and deliberation of scenic and culinary experiences...")

        required_regions = list(dict.fromkeys([stage.region for stage in state.day_stages]))
        if not required_regions:
            required_regions = [state.constraints.destination]
        month = state.constraints.month or "December"
        exclude_adventure = state.constraints.exclude_adventure
        categories = state.constraints.special_interests or ["scenic", "culinary"]

        for region in required_regions:
            tool_input = {
                "region": region,
                "month": month,
                "preferred_categories": categories,
                "exclude_adventure": exclude_adventure,
            }
            if self.mcp_client:
                raw_res = self.mcp_client.call_tool_sync("get_activities", tool_input)
                res = ActivitySearchResult(**raw_res) if isinstance(raw_res, dict) else ActivitySearchResult.model_validate_json(raw_res)
                tool_label = "get_activities (via MCP Protocol)"
            else:
                res: ActivitySearchResult = get_activities(**tool_input)
                tool_label = "get_activities"

            state.add_trace_step(
                thought=f"ActivityWorker [Perception]: Querying activities in '{region}' with negative constraint exclude_adventure={exclude_adventure} (via {tool_label}).",
                tool_name=tool_label,
                tool_input=tool_input,
                observation=res.model_dump_json(indent=2),
            )

            # Safety enforcement: ensure no adventure sports slipped through if excluded
            filtered_candidates: List[ActivityItem] = [
                act for act in res.activities if not act.is_adventure or not exclude_adventure
            ]

            # Deliberation: select activities matching pace and theme
            curated_activities, rationale = self._deliberate_activities(
                region=region,
                candidates=filtered_candidates,
                state=state,
            )

            state.activities_by_region[region] = curated_activities
            state.deliberation_rationales[f"activities_{region}"] = rationale

            state.add_trace_step(
                thought=f"ActivityWorker [Deliberation]: Curated {len(curated_activities)} activities in {region}. Rationale: {rationale}",
                observation=f"Curated {len(curated_activities)} activities: " + ", ".join([a.name for a in curated_activities])
            )

        total_activities = sum(len(acts) for acts in state.activities_by_region.values())
        summary = f"Deliberated {total_activities} scenic/culinary activities across {len(required_regions)} regions (zero adventure sports)."
        state.mark_task_completed("T3_ACTIVITIES", summary=summary)
        state.log_milestone("Milestone 2B: Activities", "completed", summary)

        return state

    def _deliberate_activities(
        self,
        region: str,
        candidates: List[ActivityItem],
        state: WorkingMemoryState,
    ) -> tuple[List[ActivityItem], str]:
        """Deliberates over candidate activities based on pace, daylight, and user themes."""
        if not candidates:
            return [], f"No suitable activities found for {region}."

        if self.llm_client and len(candidates) > 2:
            try:
                cand_summary = [
                    {
                        "name": a.name,
                        "category": a.category,
                        "duration_hours": a.estimated_duration_hours,
                        "cost_inr": a.cost_inr,
                        "best_time": a.best_time_of_day,
                        "description": a.description,
                    }
                    for a in candidates
                ]
                prompt = (
                    f"You are the Activity Specialist Agent for {region}.\n"
                    f"User Profile: {state.constraints.traveler_profile}, Pace: {state.constraints.pace}.\n"
                    f"Negative Invariant: Avoid all intense adventure sports: {state.constraints.exclude_adventure}.\n"
                    f"Candidate Activities:\n{json.dumps(cand_summary, indent=2)}\n\n"
                    f"Select 2 to 4 activities that provide a balanced, non-hectic experience matching daytime hours.\n"
                    f"Return your decision strictly in the structured schema."
                )
                decision: ActivityDeliberationDecision = self.llm_client.extract_structured(
                    prompt=prompt,
                    schema=ActivityDeliberationDecision,
                    system_instruction="You are an expert cultural and scenic travel curator. Select the best activities."
                )
                selected_acts = [
                    c for c in candidates
                    if any(sel.strip().lower() in c.name.strip().lower() for sel in decision.selected_activity_names)
                ]
                if selected_acts:
                    return selected_acts, decision.rationale
            except Exception:
                pass  # Fallback to heuristic

        # Heuristic fallback: select up to 3 activities prioritizing special interest categories
        pace = state.constraints.pace
        limit = 2 if pace == "relaxed" else 3
        selected = candidates[:limit]
        rationale = (
            f"Curated {len(selected)} activities for {region} maintaining a {pace} tempo "
            f"with focus on {' & '.join(state.constraints.special_interests or ['scenic', 'culinary'])}."
        )
        return selected, rationale
