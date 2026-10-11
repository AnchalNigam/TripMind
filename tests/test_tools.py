"""Unit tests for the 5 deterministic travel tools."""

import pytest
from tripmind.tools.regions import search_regions
from tripmind.tools.transit import calculate_travel_route
from tripmind.tools.stays import search_accommodations
from tripmind.tools.activities import get_activities
from tripmind.tools.budget import calculate_budget_breakdown


class TestTool1SearchRegions:
    def test_kashmir_winter_closure_and_daylight(self):
        """Sonamarg must be marked closed in December; daylight should reflect early sunset."""
        res = search_regions(destination="Kashmir", month="December")
        assert res.destination == "Kashmir"
        assert len(res.regions) > 0

        # Sonamarg check
        sonamarg = next((r for r in res.regions if "sonamarg" in r.region_name.lower()), None)
        assert sonamarg is not None
        assert sonamarg.is_accessible is False
        assert "closed" in sonamarg.status_note.lower()

        # Srinagar check
        srinagar = next((r for r in res.regions if "srinagar" in r.region_name.lower()), None)
        assert srinagar is not None
        assert srinagar.is_accessible is True
        assert "5:15 PM" in srinagar.sunset_time

    def test_goa_open_season(self):
        """Goa in November should be fully open with beach season active."""
        res = search_regions(destination="Goa", month="November")
        assert any(r.is_accessible for r in res.regions)

    def test_assam_open_season(self):
        """Assam in November should be accessible with early sunset."""
        res = search_regions(destination="Assam", month="November")
        assert any(r.is_accessible for r in res.regions)
        guwahati = next((r for r in res.regions if "guwahati" in r.region_name.lower()), None)
        if guwahati:
            assert guwahati.is_accessible is True


class TestTool2CalculateTravelRoute:
    def test_mountain_snow_chain_requirement(self):
        """Tangmarg to Gulmarg must report snow chains / 4x4 requirement and realistic duration."""
        route = calculate_travel_route(
            origin="Srinagar",
            destination="Gulmarg",
            month="December",
            mode="road",
        )
        assert route.distance_km == 52.0
        assert route.estimated_duration_hours >= 2.0  # Cannot be unrealistically short
        assert route.requires_special_vehicle is True
        assert "snow chains" in route.advisory.lower()

    def test_coastal_goa_route(self):
        """Dabolim Airport to North Goa route calculation."""
        route = calculate_travel_route(
            origin="Dabolim Airport",
            destination="North Goa",
            month="November",
            mode="road",
        )
        assert route.distance_km > 20.0
        assert route.requires_special_vehicle is False

    def test_assam_guwahati_route(self):
        """Guwahati airport to city route."""
        route = calculate_travel_route(
            origin="Guwahati Airport",
            destination="Guwahati",
            month="November",
            mode="road",
        )
        assert route.distance_km > 15.0
        assert route.estimated_duration_hours < 1.5


class TestTool3SearchAccommodations:
    def test_winter_heating_enforcement(self):
        """Accommodations in December Kashmir must have heating verified."""
        res = search_accommodations(
            region="Srinagar",
            min_rating=4.5,
            required_amenities=["central_heating", "electric_blanket"],
            max_nightly_rate_inr=10000.0,
        )
        assert res.total_found > 0
        for acc in res.accommodations:
            assert acc.heating_verified is True
            assert acc.price_per_night_inr <= 10000.0

    def test_budget_cap_filtering(self):
        """Stays exceeding nightly rate must be filtered out."""
        res = search_accommodations(
            region="Gulmarg",
            min_rating=4.0,
            max_nightly_rate_inr=10000.0,
        )
        for acc in res.accommodations:
            assert acc.price_per_night_inr <= 10000.0

    def test_assam_guwahati_accommodations(self):
        """Guwahati stays should return boutique/luxury hotels like Vivanta / Radisson."""
        res = search_accommodations(
            region="Guwahati",
            min_rating=4.5,
            max_nightly_rate_inr=8000.0,
        )
        assert res.total_found > 0
        names = [a.name.lower() for a in res.accommodations]
        assert any("vivanta" in n or "radisson" in n for n in names)


class TestTool4GetActivities:
    def test_negative_adventure_constraint_enforcement(self):
        """When exclude_adventure=True, skiing, snowmobiling, and parasailing must be excluded."""
        res = get_activities(
            region="Gulmarg",
            month="December",
            preferred_categories=["scenic", "culinary"],
            exclude_adventure=True,
        )
        assert res.filtered_out_adventure_count > 0
        for act in res.activities:
            assert act.is_adventure is False
            assert "skiing" not in act.name.lower()
            assert "snowmobile" not in act.name.lower()

    def test_culinary_activities_included(self):
        """Srinagar should include authentic culinary items like Wazwan and Kahwa."""
        res = get_activities(
            region="Srinagar",
            month="December",
            preferred_categories=["culinary", "scenic"],
            exclude_adventure=True,
        )
        act_names = [a.name.lower() for a in res.activities]
        assert any("wazwan" in name for name in act_names) or any("kahwa" in name for name in act_names)

    def test_assam_guwahati_culinary_and_adventure_exclusion(self):
        """Guwahati should include Paradise Thali, Brahmaputra cruise, and filter rafting."""
        res = get_activities(
            region="Guwahati",
            month="November",
            preferred_categories=["culinary", "scenic"],
            exclude_adventure=True,
        )
        act_names = [a.name.lower() for a in res.activities]
        assert any("thali" in n or "paradise" in n or "cruise" in n for n in act_names)
        assert not any("rafting" in n for n in act_names)


class TestTool5CalculateBudgetBreakdown:
    def test_exact_budget_arithmetic_and_gst(self):
        """Itemized budget must calculate 5% GST and check headroom against 80,000 cap."""
        budget = calculate_budget_breakdown(
            stays_cost_inr=30000.0,
            transit_cost_inr=7000.0,
            food_cost_inr=12000.0,
            activities_cost_inr=5000.0,
            emergency_buffer_pct=10.0,
            max_budget_cap_inr=80000.0,
        )
        # Subtotal: 30000 + 7000 + 12000 + 5000 = 54,000
        assert budget.subtotal_inr == 54000.0
        # GST (5%): 2,700
        assert budget.tax_gst_inr == 2700.0
        # Buffer (10%): 5,400
        assert budget.buffer_inr == 5400.0
        # Total: 54000 + 2700 + 5400 = 62,100
        assert budget.total_estimated_inr == 62100.0
        # Headroom: 80000 - 62100 = 17,900
        assert budget.remaining_headroom_inr == 17900.0
        assert budget.is_within_budget is True
        assert "COMPLIANT" in budget.audit_notes

    def test_over_budget_detection(self):
        """Budget exceeding cap must be flagged as non-compliant."""
        budget = calculate_budget_breakdown(
            stays_cost_inr=70000.0,
            transit_cost_inr=15000.0,
            food_cost_inr=15000.0,
            activities_cost_inr=10000.0,
            emergency_buffer_pct=10.0,
            max_budget_cap_inr=80000.0,
        )
        assert budget.is_within_budget is False
        assert budget.remaining_headroom_inr < 0
        assert "OVER BUDGET" in budget.audit_notes
