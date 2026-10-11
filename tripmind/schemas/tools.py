"""Tool Input and Output Pydantic Schemas.

AGENTIC AI CONCEPT — Tool Schemas as Formal Inbound/Outbound Contracts:
1. Inbound Contract: When an LLM calls a tool, it generates JSON parameters.
   Pydantic validates this JSON. If the LLM generates an invalid type
   (e.g., string instead of float for budget), Pydantic raises a ValidationError,
   which our agent catches and sends back to the LLM so it can self-correct.
2. Outbound Contract: The structured return type gives the agent reliable,
   machine-readable perceptions (Observations) rather than vague prose.
3. Schema Reflection: The docstrings and Field descriptions here are converted
   directly into JSON Schema sent to Gemini/Groq as the tool definitions.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Tool 1: search_regions
# ---------------------------------------------------------------------------
class RegionSearchInput(BaseModel):
    destination: str = Field(
        ...,
        description="The primary destination or territory (e.g. 'Kashmir', 'Goa', 'Himachal', 'Paris', 'Kyoto').",
    )
    month: str = Field(
        ...,
        description="Month of travel (e.g. 'December', 'November', 'July') to assess seasonal accessibility, weather, and daylight.",
    )


class RegionInfo(BaseModel):
    region_name: str
    is_accessible: bool
    status_note: str = Field(
        ...,
        description="Seasonal advisories, e.g. 'Sonamarg pass closed due to heavy winter snowfall', 'Open with beach shacks active'."
    )
    temp_range_celsius: str
    daylight_hours: str
    sunset_time: str
    recommended_stay_nights: int = Field(default=2)
    scenic_highlights: List[str] = Field(default_factory=list)


class RegionSearchResult(BaseModel):
    destination: str
    month: str
    general_weather: str
    regions: List[RegionInfo]
    safety_advisory: Optional[str] = None


# ---------------------------------------------------------------------------
# Tool 2: calculate_travel_route
# ---------------------------------------------------------------------------
class RouteCalculateInput(BaseModel):
    origin: str = Field(..., description="Starting location or airport (e.g. 'Srinagar Airport', 'Tangmarg', 'Madgaon', 'Dabolim Airport').")
    destination: str = Field(..., description="Arrival destination (e.g. 'Gulmarg', 'Pahalgam', 'Panaji', 'Palolem').")
    month: str = Field(default="December", description="Travel month to adjust for weather/road conditions.")
    mode: Literal["road", "train", "flight", "local_transit"] = Field(
        default="road",
        description="Transit mode: 'road' (cab/car), 'train', 'flight', or 'local_transit' (scooty/ferry/auto).",
    )


class RouteResult(BaseModel):
    origin: str
    destination: str
    mode: str
    distance_km: float
    estimated_duration_hours: float
    estimated_cost_inr: float
    road_condition: str
    requires_special_vehicle: bool = Field(
        default=False,
        description="True if snow-chains / 4x4 or specialized local permit required."
    )
    advisory: str


# ---------------------------------------------------------------------------
# Tool 3: search_accommodations
# ---------------------------------------------------------------------------
class AccommodationSearchInput(BaseModel):
    region: str = Field(..., description="Specific region or town (e.g. 'Srinagar', 'Gulmarg', 'Pahalgam', 'North Goa', 'South Goa').")
    min_rating: float = Field(default=4.0, description="Minimum guest review rating (out of 5.0).")
    required_amenities: List[str] = Field(
        default_factory=list,
        description="Required amenities, e.g. ['central_heating', 'electric_blanket'] for sub-zero winter or ['ac', 'pool'] for beaches.",
    )
    max_nightly_rate_inr: float = Field(default=12000.0, description="Maximum budget per room per night in INR.")


class AccommodationItem(BaseModel):
    name: str
    region: str
    rating: float
    price_per_night_inr: float
    heating_verified: bool = Field(default=False, description="Guaranteed central heating, bukhari, or electric blankets for winter.")
    amenities: List[str]
    couple_suitability: str
    address_or_area: str


class AccommodationSearchResult(BaseModel):
    region: str
    accommodations: List[AccommodationItem]
    total_found: int


# ---------------------------------------------------------------------------
# Tool 4: get_activities
# ---------------------------------------------------------------------------
class ActivitySearchInput(BaseModel):
    region: str = Field(..., description="Region to explore (e.g. 'Srinagar', 'Gulmarg', 'Pahalgam', 'North Goa').")
    month: str = Field(default="December", description="Month of visit.")
    preferred_categories: List[str] = Field(
        default_factory=lambda: ["scenic", "culinary"],
        description="Desired types, e.g. ['scenic', 'culinary', 'cultural', 'heritage', 'relaxation'].",
    )
    exclude_adventure: bool = Field(
        default=True,
        description="Negative constraint flag: If True, strictly excludes high-risk/intense adventure activities like skiing, paragliding, jet-skiing, snowmobiles.",
    )


class ActivityItem(BaseModel):
    name: str
    region: str
    category: str = Field(..., description="E.g. 'scenic', 'culinary', 'cultural', 'leisure', 'adventure'.")
    is_adventure: bool
    estimated_duration_hours: float
    cost_inr: float
    description: str
    best_time_of_day: str


class ActivitySearchResult(BaseModel):
    region: str
    activities: List[ActivityItem]
    filtered_out_adventure_count: int = Field(
        default=0,
        description="Tracks how many adventure sports were eliminated to enforce the negative constraint."
    )


# ---------------------------------------------------------------------------
# Tool 5: calculate_budget_breakdown
# ---------------------------------------------------------------------------
class BudgetCalculateInput(BaseModel):
    stays_cost_inr: float = Field(..., description="Total cost of accommodations across all nights.")
    transit_cost_inr: float = Field(..., description="Total transit cost (airport cabs, inter-region transfers, local cabs).")
    food_cost_inr: float = Field(..., description="Estimated food/dining budget for the duration.")
    activities_cost_inr: float = Field(..., description="Total cost for curated experiences (Shikara, guides, tickets).")
    emergency_buffer_pct: float = Field(
        default=10.0,
        description="Contingency buffer percentage (e.g. 10.0 for 10% winter/unforeseen weather cushion).",
    )
    max_budget_cap_inr: float = Field(
        default=80000.0,
        description="User's ceiling budget (excluding flights).",
    )


class BudgetItem(BaseModel):
    category: str
    amount_inr: float
    notes: str


class BudgetBreakdownResult(BaseModel):
    items: List[BudgetItem]
    subtotal_inr: float
    tax_gst_inr: float = Field(..., description="Estimated 5% GST on travel/hospitality services.")
    buffer_inr: float = Field(..., description="Contingency cushion amount.")
    total_estimated_inr: float
    budget_cap_inr: float
    remaining_headroom_inr: float
    is_within_budget: bool
    audit_notes: str
