"""Tool: search_regions.

AGENTIC AI CONCEPT — Tool Specialization & Seasonal Grounding:
The agent must verify if sub-regions are accessible before attempting to book
stays or plan transit. In December Kashmir, Sonamarg is closed due to avalanches.
Calling this tool prevents the agent from making fatal routing mistakes.
"""

from tripmind.tools.registry import register_tool
from tripmind.services.weather_service import get_weather_and_climate
from tripmind.schemas.tools import RegionSearchResult


@register_tool(
    name="search_regions",
    description="Search accessible sub-regions, weather, temperature range, daylight hours, sunset time, and seasonal closures for any destination.",
)
def search_regions(destination: str, month: str) -> RegionSearchResult:
    """Search accessible sub-regions and weather for a destination and travel month.
    
    Args:
        destination: Destination territory or city (e.g. 'Kashmir', 'Goa', 'Paris').
        month: Travel month (e.g. 'December', 'November', 'July').
        
    Returns:
        RegionSearchResult containing sub-regions with accessibility status, temperatures, and daylight limits.
    """
    return get_weather_and_climate(destination=destination, month=month)
