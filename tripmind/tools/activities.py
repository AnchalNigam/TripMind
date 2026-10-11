"""Tool: get_activities.

AGENTIC AI CONCEPT — Negative Constraint Enforcement:
Travelers often say "no adventure activities", but general LLMs easily slip up
and suggest skiing or snowmobiling because they are popular in Gulmarg.
This tool programmatically filters out adventure activities when `exclude_adventure=True`.
"""

from typing import List, Optional
from tripmind.tools.registry import register_tool
from tripmind.services.places_service import get_activities_data
from tripmind.schemas.tools import ActivitySearchResult


@register_tool(
    name="get_activities",
    description="Get curated activities (scenic viewpoints, cultural heritage, authentic culinary dining) with optional strict exclusion of adventure sports.",
)
def get_activities(
    region: str,
    month: str = "December",
    preferred_categories: Optional[List[str]] = None,
    exclude_adventure: bool = True,
) -> ActivitySearchResult:
    """Retrieve curated activities for a region, strictly enforcing negative constraints.
    
    Args:
        region: Region to explore (e.g. 'Srinagar', 'Gulmarg', 'Pahalgam', 'North Goa').
        month: Travel month.
        preferred_categories: Desired types (e.g. ['scenic', 'culinary', 'cultural']).
        exclude_adventure: If True, strictly drops skiing, paragliding, snowmobiling, etc.
        
    Returns:
        ActivitySearchResult containing curated activities and count of filtered adventure sports.
    """
    return get_activities_data(
        region=region,
        month=month,
        preferred_categories=preferred_categories or ["scenic", "culinary"],
        exclude_adventure=exclude_adventure,
    )
