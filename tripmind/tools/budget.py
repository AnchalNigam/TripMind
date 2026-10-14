"""Tool: calculate_budget_breakdown.

AGENTIC AI CONCEPT — Deterministic Arithmetic over Stochastic Guessing:
LLMs are token prediction engines, not calculators. Asking an LLM to add up
hotel nights, cab rates, meals, 5% GST, and emergency buffers often leads to
subtle math errors that break the user's budget.
This tool performs pure deterministic Python arithmetic and audits the ₹80k cap.
"""

from typing import Optional
from tripmind.tools.registry import register_tool
from tripmind.schemas.tools import (
    BudgetItem,
    BudgetBreakdownResult,
)


@register_tool(
    name="calculate_budget_breakdown",
    description="Calculate exact itemized trip budget, 5% travel/hospitality GST, contingency cushion, and remaining headroom against the budget cap.",
)
def calculate_budget_breakdown(
    stays_cost_inr: float,
    transit_cost_inr: float,
    food_cost_inr: float,
    activities_cost_inr: float,
    emergency_buffer_pct: float = 10.0,
    max_budget_cap_inr: Optional[float] = None,
) -> BudgetBreakdownResult:
    """Perform exact itemized financial calculation and audit budget cap compliance.
    
    Args:
        stays_cost_inr: Total accommodation expenditure across all nights.
        transit_cost_inr: Total transit expenses (airport transfers, intercity cabs, local cabs).
        food_cost_inr: Estimated dining and food expenses.
        activities_cost_inr: Total cost for curated experiences (tickets, shikara, entry).
        emergency_buffer_pct: Contingency buffer percentage (e.g. 10.0 for 10% winter cushion).
        max_budget_cap_inr: User budget ceiling (excluding flights), or None if unconstrained.
        
    Returns:
        BudgetBreakdownResult with itemized ledger, GST, total amount, and budget headroom.
    """
    subtotal = float(stays_cost_inr + transit_cost_inr + food_cost_inr + activities_cost_inr)
    gst = round(subtotal * 0.05, 2)  # 5% composite GST on tour services
    buffer_amt = round(subtotal * (emergency_buffer_pct / 100.0), 2)
    grand_total = round(subtotal + gst + buffer_amt, 2)

    if max_budget_cap_inr is not None and max_budget_cap_inr > 0:
        remaining_headroom = round(max_budget_cap_inr - grand_total, 2)
        is_within = grand_total <= max_budget_cap_inr
    else:
        remaining_headroom = 0.0
        is_within = True

    items = [
        BudgetItem(
            category="Accommodations",
            amount_inr=stays_cost_inr,
            notes="Heated boutique stays / houseboats.",
        ),
        BudgetItem(
            category="Transit & Transfers",
            amount_inr=transit_cost_inr,
            notes="Private airport cab, intercity transfers, and chain-taxi segments.",
        ),
        BudgetItem(
            category="Dining & Culinary",
            amount_inr=food_cost_inr,
            notes="Authentic dining (Wazwan, cafe tea breaks, riverside meals).",
        ),
        BudgetItem(
            category="Curated Experiences",
            amount_inr=activities_cost_inr,
            notes="Shikara ride, Gondola Phase 1 tickets, heritage walking tours.",
        ),
        BudgetItem(
            category="Taxes (GST 5%)",
            amount_inr=gst,
            notes="Standard Indian tourism & hospitality GST.",
        ),
        BudgetItem(
            category="Emergency Cushion",
            amount_inr=buffer_amt,
            notes=f"{emergency_buffer_pct}% contingency cushion for winter weather adjustments.",
        ),
    ]

    if max_budget_cap_inr is not None and max_budget_cap_inr > 0:
        status_str = (
            f"COMPLIANT: Total of ₹{grand_total:,.2f} is well within ₹{max_budget_cap_inr:,.2f} cap (Headroom: ₹{remaining_headroom:,.2f})."
            if is_within
            else f"OVER BUDGET: Total of ₹{grand_total:,.2f} exceeds ₹{max_budget_cap_inr:,.2f} cap by ₹{abs(remaining_headroom):,.2f}. Must reduce stay or activity tier."
        )
        reported_cap = float(max_budget_cap_inr)
    else:
        status_str = f"UNCONSTRAINED: No explicit budget cap provided by user. Total estimated expenditure is ₹{grand_total:,.2f}."
        reported_cap = grand_total

    return BudgetBreakdownResult(
        items=items,
        subtotal_inr=subtotal,
        tax_gst_inr=gst,
        buffer_inr=buffer_amt,
        total_estimated_inr=grand_total,
        budget_cap_inr=reported_cap,
        remaining_headroom_inr=remaining_headroom,
        is_within_budget=is_within,
        audit_notes=status_str,
    )
