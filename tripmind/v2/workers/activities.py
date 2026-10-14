"""Activity Curation Worker for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Negative Constraint Enforcement:
This worker queries activities strictly within each staged region and enforces
the negative constraint (excluding adventure sports like skiing, paragliding, etc.).
Because activities are keyed strictly by region, Gulmarg activities can never be
assigned to Srinagar days.
"""

from typing import List, Optional

from tripmind.v2.state import WorkingMemoryState
from tripmind.tools.activities import get_activities
from tripmind.schemas.tools import ActivitySearchResult, ActivityItem


class ActivityWorker:
    """Worker responsible for sourcing scenic and culinary activities per staged region."""

    def __init__(self):
        pass

    def run(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Sources activities for each distinct staged region."""
        state.mark_task_running("T3_ACTIVITIES")
        state.log_milestone("Milestone 2B: Activities", "running", "Curation of scenic and culinary experiences...")

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
            res: ActivitySearchResult = get_activities(
                region=region,
                month=month,
                preferred_categories=categories,
                exclude_adventure=exclude_adventure,
            )

            state.add_trace_step(
                thought=f"ActivityWorker: Querying activities in '{region}' with negative constraint exclude_adventure={exclude_adventure}.",
                tool_name="get_activities",
                tool_input=tool_input,
                observation=res.model_dump_json(indent=2),
            )

            # Extra safety check: ensure no adventure sports slipped through
            curated_activities: List[ActivityItem] = [
                act for act in res.activities if not act.is_adventure or not exclude_adventure
            ]
            state.activities_by_region[region] = curated_activities

        total_activities = sum(len(acts) for acts in state.activities_by_region.values())
        summary = f"Curated {total_activities} scenic/culinary activities across {len(required_regions)} regions (zero adventure sports)."
        state.mark_task_completed("T3_ACTIVITIES", summary=summary)
        state.log_milestone("Milestone 2B: Activities", "completed", summary)

        return state
