"""TripMind Model Context Protocol (MCP) Server.

AGENTIC AI CONCEPT — Universal Decoupled Tool Server:
1. In traditional monolithic agents, tool functions are directly imported in Python.
   This couples the agent to the runtime environment, credentials, and local libraries.
2. In the MCP architecture (Anthropic / OpenAI open standard):
   - This file runs as an independent MCP Server speaking JSON-RPC 2.0.
   - It exposes:
     A) Granular Primitive Tools: Leaf functions for stays, activities, transit, budget.
     B) Composite Agentic Tool: `plan_trip`, exposing the entire Level 2 DAG engine
        as an "Agent-as-a-Tool" (AaaT) to external hosts like Claude Desktop or Cursor.
     C) Resources: Read-only context URIs (`tripmind://advisories/{region}`).
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from mcp.server.mcpserver import MCPServer

from tripmind.tools.stays import search_accommodations as _search_accommodations
from tripmind.tools.activities import get_activities as _get_activities
from tripmind.tools.transit import calculate_travel_route as _calculate_travel_route
from tripmind.tools.budget import calculate_budget_breakdown as _calculate_budget_breakdown
from tripmind.tools.regions import search_regions as _search_regions

# ---------------------------------------------------------------------------
# Observability & Audit Logging (File + stderr)
# In MCP stdio transport:
# - stdout is STRICTLY reserved for JSON-RPC protocol bytes.
# - stderr is streamed to host developer consoles.
# - logs/mcp_server.log allows full-stack style inspection: `tail -f logs/mcp_server.log`
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "mcp_server.log"

logger = logging.getLogger("tripmind.mcp")
logger.setLevel(logging.INFO)

if not logger.handlers:
    file_fmt = logging.Formatter("[%(asctime)s] [%(levelname)s] [TripMind-MCP] %(message)s")
    
    fh = logging.FileHandler(LOG_FILE)
    fh.setFormatter(file_fmt)
    logger.addHandler(fh)
    
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(file_fmt)
    logger.addHandler(sh)

# Initialize the official MCP Server
server = MCPServer(
    name="tripmind-travel-mcp",
    version="1.0.0",
    description="TripMind Autonomous Travel Intelligence MCP Server. Provides verified hotel sourcing, mountain transit logistics, activities curation, and deterministic budget auditing."
)


# ---------------------------------------------------------------------------
# 1. Granular Domain Tools (The "Hands")
# ---------------------------------------------------------------------------

@server.tool(
    name="search_accommodations",
    description="Source verified hotels, boutique resorts, and houseboats for a specific region with verified heating and amenity filtering."
)
def search_accommodations(
    region: str,
    min_rating: float = 4.0,
    required_amenities: Optional[List[str]] = None,
    max_nightly_rate_inr: Optional[float] = None,
) -> str:
    """Queries verified accommodations in the target region."""
    logger.info(f"📥 TOOL_CALL: search_accommodations(region='{region}', min_rating={min_rating}, max_nightly_rate={max_nightly_rate_inr})")
    result = _search_accommodations(
        region=region,
        min_rating=min_rating,
        required_amenities=required_amenities or [],
        max_nightly_rate_inr=max_nightly_rate_inr,
    )
    logger.info(f"📤 TOOL_SUCCESS: search_accommodations -> found {len(result.accommodations)} stays")
    return result.model_dump_json(indent=2)


@server.tool(
    name="get_activities",
    description="Query verified cultural, culinary, and scenic experiences for a region and month with negative constraint filtering (excluding adventure sports)."
)
def get_activities(
    region: str,
    month: str = "December",
    preferred_categories: Optional[List[str]] = None,
    exclude_adventure: bool = False,
) -> str:
    """Queries verified activities adhering to negative constraints."""
    logger.info(f"📥 TOOL_CALL: get_activities(region='{region}', month='{month}', exclude_adventure={exclude_adventure})")
    result = _get_activities(
        region=region,
        month=month,
        preferred_categories=preferred_categories or ["scenic", "culinary"],
        exclude_adventure=exclude_adventure,
    )
    logger.info(f"📤 TOOL_SUCCESS: get_activities -> found {len(result.activities)} activities")
    return result.model_dump_json(indent=2)


@server.tool(
    name="calculate_travel_route",
    description="Calculate mountain transit distance, drive duration, cost, and winter vehicle specs (e.g. 4x4 snow chains for mountain passes)."
)
def calculate_travel_route(
    origin: str,
    destination: str,
    month: str = "December",
) -> str:
    """Calculates intercity transit route and vehicle requirements."""
    logger.info(f"📥 TOOL_CALL: calculate_travel_route({origin} -> {destination}, month='{month}')")
    result = _calculate_travel_route(
        origin=origin,
        destination=destination,
        month=month,
    )
    logger.info(f"📤 TOOL_SUCCESS: calculate_travel_route -> {result.distance_km}km, {result.estimated_duration_hours}h, ₹{result.estimated_cost_inr}")
    return result.model_dump_json(indent=2)


@server.tool(
    name="calculate_budget_breakdown",
    description="Deterministic zero-math financial auditor: calculates exact subtotals, 5% Indian tourism GST, emergency buffer, and audits headroom against budget cap."
)
def calculate_budget_breakdown(
    stays_cost_inr: float,
    transit_cost_inr: float,
    food_cost_inr: float,
    activities_cost_inr: float,
    emergency_buffer_pct: float = 10.0,
    max_budget_cap_inr: Optional[float] = None,
) -> str:
    """Executes deterministic financial calculations."""
    logger.info(f"📥 TOOL_CALL: calculate_budget_breakdown(stays={stays_cost_inr}, transit={transit_cost_inr}, cap={max_budget_cap_inr})")
    result = _calculate_budget_breakdown(
        stays_cost_inr=stays_cost_inr,
        transit_cost_inr=transit_cost_inr,
        food_cost_inr=food_cost_inr,
        activities_cost_inr=activities_cost_inr,
        emergency_buffer_pct=emergency_buffer_pct,
        max_budget_cap_inr=max_budget_cap_inr,
    )
    logger.info(f"📤 TOOL_SUCCESS: calculate_budget_breakdown -> Total: ₹{result.total_estimated_inr}, Compliant: {result.is_within_budget}")
    return result.model_dump_json(indent=2)


@server.tool(
    name="search_regions",
    description="Query regional accessibility, seasonal closures (e.g. Sonamarg pass closures in winter), daylight hours, and temperature ranges."
)
def search_regions(
    destination: str,
    month: str = "December",
) -> str:
    """Analyzes regional accessibility and seasonal closures."""
    logger.info(f"📥 TOOL_CALL: search_regions(destination='{destination}', month='{month}')")
    result = _search_regions(destination=destination, month=month)
    logger.info(f"📤 TOOL_SUCCESS: search_regions -> {result.destination}, hubs: {len(result.regions)}")
    return result.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# 2. Composite Agentic Tool: Agent-as-a-Tool (AaaT)
# ---------------------------------------------------------------------------

@server.tool(
    name="plan_trip",
    description="End-to-end autonomous travel planner: executes the full Level 2 Plan-and-Solve DAG Engine to synthesize a verified, budget-audited itinerary."
)
def plan_trip(user_query: str) -> str:
    """Runs the full TripMind Level 2 DAG Multi-Agent Pipeline.

    Enables external hosts like Claude Desktop or Cursor to invoke TripMind
    as an expert autonomous agent tool!
    """
    logger.info(f"🚀 [AGENT-AS-A-TOOL] plan_trip invoked with query: '{user_query[:80]}...'")
    from tripmind.v2.engine import PlanAndSolveEngine
    engine = PlanAndSolveEngine(provider="mock", use_mcp=False)
    plan = engine.plan(user_query)
    logger.info(
        f"✅ [AGENT-AS-A-TOOL] plan_trip completed! "
        f"Days: {len(plan.days)}, Nights: {plan.duration_nights}, "
        f"Total: ₹{plan.budget_summary.total_estimated_inr:,.2f}, Compliant: {plan.budget_summary.is_within_budget}"
    )
    return plan.model_dump_json(indent=2)


# ---------------------------------------------------------------------------
# 3. Read-Only Context Resources
# ---------------------------------------------------------------------------

@server.resource(
    uri="tripmind://advisories/kashmir",
    name="Kashmir Winter Safety & Road Status Advisory",
    description="Real-time environmental guidelines for winter travel in Kashmir.",
    mime_type="text/markdown",
)
def get_kashmir_winter_advisory() -> str:
    logger.info("📖 RESOURCE_READ: tripmind://advisories/kashmir")
    return (
        "# Kashmir Winter Travel Safety Advisory (December - February)\n\n"
        "- **Sonamarg & Zojila Pass**: Strictly closed due to heavy snow accumulation.\n"
        "- **Gulmarg Access**: Tangmarg to Gulmarg switchback road requires mandatory 4x4 vehicles with tire snow chains.\n"
        "- **Heating Requirement**: Nighttime temperatures drop to -8°C. Verified central heating or electric blankets mandatory for safety.\n"
        "- **Daylight Constraint**: Sunset occurs around 5:15 PM. Outdoor sightseeing must conclude before dusk.\n"
    )


# ---------------------------------------------------------------------------
# 4. Standard CLI Entrypoint for Claude Desktop / Cursor
# ---------------------------------------------------------------------------

def run_server():
    """Runs the MCP server over standard I/O (stdio) for local agent hosts."""
    server.run(transport="stdio")


if __name__ == "__main__":
    run_server()
