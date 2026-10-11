"""Tool: search_accommodations.

AGENTIC AI CONCEPT — Attribute Verification & Safety Grounding:
Ensures stays meet traveler constraints. In December Kashmir, sub-zero nights
demand confirmed heating (central heating, electric blankets, bukhari).
"""

from typing import List, Optional
from tripmind.tools.registry import register_tool
from tripmind.services.places_service import get_accommodations_data
from tripmind.schemas.tools import AccommodationSearchResult


@register_tool(
    name="search_accommodations",
    description="Search verified accommodations filtered by region, minimum rating, nightly price cap, and essential amenities (like central heating, electric blankets, pool).",
)
def search_accommodations(
    region: str,
    min_rating: float = 4.0,
    required_amenities: Optional[List[str]] = None,
    max_nightly_rate_inr: float = 12000.0,
) -> AccommodationSearchResult:
    """Search accommodations filtered by heating, couple suitability, and price.
    
    Args:
        region: Region to find stays (e.g. 'Srinagar', 'Gulmarg', 'Pahalgam', 'North Goa').
        min_rating: Minimum guest review rating (default 4.0 out of 5.0).
        required_amenities: List of mandatory amenities, e.g. ['central_heating', 'electric_blanket'].
        max_nightly_rate_inr: Maximum nightly rate in INR.
        
    Returns:
        AccommodationSearchResult with matching properties and heating verification status.
    """
    return get_accommodations_data(
        region=region,
        min_rating=min_rating,
        required_amenities=required_amenities or [],
        max_nightly_rate_inr=max_nightly_rate_inr,
    )
