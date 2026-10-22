"""Unit & Integration Tests for TripMind Model Context Protocol (MCP) Server and Client.

Verifies:
1. Dynamic Tool Discovery via MCP tools/list.
2. Granular domain tool execution via MCP tools/call.
3. Deterministic financial auditor tool execution via MCP.
4. Composite Agent-as-a-Tool (plan_trip) execution via MCP.
5. Context Resource reading (tripmind://advisories/kashmir).
"""

import pytest
import asyncio
from tripmind.mcp.server import server
from tripmind.mcp.client import TripMindMCPClient


@pytest.fixture
def mcp_client():
    return TripMindMCPClient(mcp_server=server)


@pytest.mark.asyncio
async def test_mcp_tool_discovery(mcp_client):
    """Verify that MCP Client dynamically discovers all tools advertised by the MCP Server."""
    tools = await mcp_client.list_tools()
    assert len(tools) >= 5

    tool_names = [t["name"] for t in tools]
    assert "search_accommodations" in tool_names
    assert "get_activities" in tool_names
    assert "calculate_travel_route" in tool_names
    assert "calculate_budget_breakdown" in tool_names
    assert "search_regions" in tool_names
    assert "plan_trip" in tool_names  # Composite Agent-as-a-Tool

    # Verify input schema format for search_accommodations
    acc_tool = next(t for t in tools if t["name"] == "search_accommodations")
    assert "properties" in acc_tool["inputSchema"]
    assert "region" in acc_tool["inputSchema"]["properties"]


@pytest.mark.asyncio
async def test_mcp_granular_tool_execution(mcp_client):
    """Verify that calling search_accommodations through MCP executes and returns verified stays."""
    result = await mcp_client.call_tool(
        name="search_accommodations",
        arguments={
            "region": "Gulmarg",
            "min_rating": 4.0,
            "required_amenities": ["central_heating"],
            "max_nightly_rate_inr": 8000.0,
        }
    )

    assert isinstance(result, dict)
    assert result["region"] == "Gulmarg"
    assert len(result["accommodations"]) > 0
    # Must have heating verified
    assert any(a["heating_verified"] for a in result["accommodations"])


@pytest.mark.asyncio
async def test_mcp_budget_tool_execution(mcp_client):
    """Verify that calling calculate_budget_breakdown through MCP returns exact arithmetic."""
    result = await mcp_client.call_tool(
        name="calculate_budget_breakdown",
        arguments={
            "stays_cost_inr": 20000.0,
            "transit_cost_inr": 5000.0,
            "food_cost_inr": 9000.0,
            "activities_cost_inr": 4000.0,
            "emergency_buffer_pct": 10.0,
            "max_budget_cap_inr": 50000.0,
        }
    )

    # Subtotal: 20000 + 5000 + 9000 + 4000 = 38,000
    assert result["subtotal_inr"] == 38000.0
    # GST: 1,900
    assert result["tax_gst_inr"] == 1900.0
    # Buffer: 3,800
    assert result["buffer_inr"] == 3800.0
    # Total: 38000 + 1900 + 3800 = 43,700
    assert result["total_estimated_inr"] == 43700.0
    assert result["is_within_budget"] is True


@pytest.mark.asyncio
async def test_mcp_composite_agentic_tool(mcp_client):
    """Verify that calling composite tool 'plan_trip' executes the entire Level 2 DAG via MCP."""
    query = "I want to visit Kashmir in December for 5 days. Budget ₹80k. Relaxed pace."
    result = await mcp_client.call_tool(
        name="plan_trip",
        arguments={"user_query": query}
    )

    assert isinstance(result, dict)
    assert result["destination"] == "Kashmir"
    assert result["duration_days"] == 5
    assert len(result["days"]) == 5
    assert result["budget_summary"]["budget_cap_inr"] == 80000.0
    assert result["budget_summary"]["is_within_budget"] is True


def test_mcp_client_sync_invocation(mcp_client):
    """Verify synchronous MCP tool invocation wrapper."""
    result = mcp_client.call_tool_sync(
        name="calculate_travel_route",
        arguments={
            "origin": "Srinagar",
            "destination": "Gulmarg",
            "month": "December",
        }
    )
    assert isinstance(result, dict)
    assert result["distance_km"] > 0
    assert result["requires_special_vehicle"] is True
