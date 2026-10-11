"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from tripmind.api.app import app

client = TestClient(app)


def test_health_check_endpoint():
    """GET /api/v1/health should return service health and registration stats."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["tools_registered_count"] == 5


def test_list_tools_endpoint():
    """GET /api/v1/tools should return OpenAPI schemas for all 5 tools."""
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    tool_names = [t["name"] for t in data["tools"]]
    assert "search_regions" in tool_names
    assert "calculate_budget_breakdown" in tool_names


def test_planner_plan_endpoint():
    """POST /api/v1/planner/plan should execute ReAct agent and return structured response."""
    payload = {
        "user_query": (
            "I want to visit Kashmir in December for 5 days. I'm going with my wife. "
            "We don't want a hectic trip. We love scenic places and food, but aren't "
            "interested in adventure activities. Budget around ₹80k excluding flights."
        ),
        "preferred_provider": "mock",
    }
    response = client.post("/api/v1/planner/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["duration_days"] == 5
    assert len(data["days"]) == 5
    assert data["constraints_verified"]["budget_compliant"] is True
    assert data["budget_summary"]["total_estimated_inr"] <= 80000.0
    assert len(data["execution_trace"]) > 0
