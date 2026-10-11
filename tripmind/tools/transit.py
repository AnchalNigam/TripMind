"""Tool: calculate_travel_route.

AGENTIC AI CONCEPT — Deterministic Transit Calculation:
Prevents the agent from hallucinating rapid transit times on mountain roads.
Calculates road distance, realistic transit time factoring snow/curves,
cost estimates, and chain-taxi warnings.
"""

from tripmind.tools.registry import register_tool
from tripmind.services.geo_service import get_route_details
from tripmind.schemas.tools import RouteResult


@register_tool(
    name="calculate_travel_route",
    description="Calculate transit distance, realistic duration, cost, road conditions, and special vehicle requirements (e.g. snow-chains/4x4) between two points.",
)
def calculate_travel_route(
    origin: str,
    destination: str,
    month: str = "December",
    mode: str = "road",
) -> RouteResult:
    """Calculate realistic travel route duration, cost, and terrain advisories.
    
    Args:
        origin: Starting town, airport, or waypoint (e.g. 'Srinagar Airport', 'Tangmarg', 'Dabolim Airport').
        destination: Arrival destination (e.g. 'Gulmarg', 'Pahalgam', 'North Goa').
        month: Travel month to account for snow or seasonal delays.
        mode: Transit mode ('road', 'train', 'flight', 'local_transit').
        
    Returns:
        RouteResult containing distance in km, realistic duration in hours, cost in INR, and safety advisories.
    """
    return get_route_details(
        origin=origin,
        destination=destination,
        month=month,
        mode=mode,
    )
