"""Tools package: Exports the tool registry and imports all registered tools."""

from tripmind.tools.registry import default_registry, register_tool, ToolRegistry
from tripmind.tools.regions import search_regions
from tripmind.tools.transit import calculate_travel_route
from tripmind.tools.stays import search_accommodations
from tripmind.tools.activities import get_activities
from tripmind.tools.budget import calculate_budget_breakdown

__all__ = [
    "default_registry",
    "register_tool",
    "ToolRegistry",
    "search_regions",
    "calculate_travel_route",
    "search_accommodations",
    "get_activities",
    "calculate_budget_breakdown",
]
