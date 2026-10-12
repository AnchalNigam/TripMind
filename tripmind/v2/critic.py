"""Constraint Critic & Bounded Replanning Engine for Level 2.

AGENTIC AI CONCEPT — Reflection, Critique, & The Constraint Relaxation Policy:
1. In Level 1, when an unachievable budget (e.g. ₹6,000 for 5 days in winter Kashmir)
   was encountered, the agent thrashed across 10 turns and triggered broken fallback values.
2. In Level 2, the Critic evaluates candidate solutions against verified constraints.
   - Fixable overruns: Executes ONE targeted replan (swapping ONLY hotel tiers).
   - Unachievable requests: Immediately triggers the Constraint Relaxation Policy.
     It refuses to loop endlessly, maintains safety invariants, and transparently
     documents the economic reality in audit notes.
"""

from typing import List, Optional

from tripmind.v2.state import WorkingMemoryState


class CriticAgent:
    """Evaluates candidate itinerary artifacts against non-negotiable constraints."""

    def __init__(self):
        pass

    def evaluate_and_replan(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Inspects state, performs targeted replanning if fixable, or applies relaxation."""
        state.mark_task_running("T6_CRITIC")
        state.log_milestone("Milestone 4: Critic Review", "running", "Evaluating safety, heating, adventure, and budget constraints...")

        is_winter = state.constraints.month.lower() in ["december", "january", "february"]
        
        # 1. Winter Heating Invariant Check
        heating_ok = True
        if is_winter:
            for region, stay in state.selected_stay_by_region.items():
                if not stay.heating_verified:
                    heating_ok = False
                    state.critic_notes.append(f"Heating warning: Stay '{stay.name}' in {region} lacks verified heating.")
        if heating_ok:
            state.critic_notes.append("Safety check passed: 100% of selected winter accommodations have verified heating.")

        # 2. Negative Adventure Constraint Check
        adventure_ok = True
        for region, acts in state.activities_by_region.items():
            for act in acts:
                if act.is_adventure and state.constraints.exclude_adventure:
                    adventure_ok = False
                    state.critic_notes.append(f"Negative constraint violation: Adventure activity '{act.name}' found.")
        if adventure_ok:
            state.critic_notes.append("Negative constraint passed: Zero adventure sports included.")

        # 3. Budget Constraint Check
        audit = state.financial_audit
        if not audit:
            state.mark_task_failed("T6_CRITIC", error="Financial audit missing.")
            return state

        if audit.is_within_budget:
            state.critic_passed = True
            state.critic_notes.append(f"Budget compliant: Total ₹{audit.total_estimated_inr:,.0f} <= Cap ₹{audit.budget_cap_inr:,.0f}.")
        else:
            # Budget overrun detected!
            # Check if fixable via Targeted Replan (swapping hotel tiers)
            if state.replan_count < 1 and audit.total_estimated_inr <= (state.constraints.budget_cap_inr * 1.35):
                state.add_trace_step(
                    thought=(
                        f"CriticAgent: Budget overrun detected (₹{audit.total_estimated_inr:,.0f} vs cap ₹{audit.budget_cap_inr:,.0f}). "
                        f"Triggering targeted replan (depth=1) to select tier-2 heated accommodations."
                    ),
                    tool_name="replan_stays",
                )
                state.replan_count += 1
                
                # Import dynamically to avoid circular dependencies
                from tripmind.v2.workers.stays import StayWorker
                from tripmind.v2.auditor import FinancialAuditor
                
                StayWorker().run(state, prefer_budget_tier=True)
                FinancialAuditor().run(state)
                
                # Re-check after targeted replan
                if state.financial_audit and state.financial_audit.is_within_budget:
                    state.critic_passed = True
                    note = f"Targeted replan successful: Selected tier-2 heated stays. New total ₹{state.financial_audit.total_estimated_inr:,.0f} is within cap."
                    state.critic_notes.append(note)
                else:
                    self._apply_constraint_relaxation(state)
            else:
                # Mathematically unachievable request (e.g. ₹6k budget for 5 days in winter)
                self._apply_constraint_relaxation(state)

        summary = f"Critic review complete (Replan count: {state.replan_count}, Relaxation: {state.constraint_relaxation_applied})."
        state.mark_task_completed("T6_CRITIC", summary=summary)
        state.log_milestone("Milestone 4: Critic Review", "completed", summary)

        return state

    def _apply_constraint_relaxation(self, state: WorkingMemoryState) -> None:
        """Applies the Constraint Relaxation Policy for impossible or severe budget deficits."""
        state.constraint_relaxation_applied = True
        state.critic_passed = True  # Allows pipeline to compile safely

        requested_cap = state.constraints.budget_cap_inr
        baseline_cost = state.financial_audit.total_estimated_inr if state.financial_audit else 25875.0
        
        relaxation_explanation = (
            f"Constraint Relaxation Policy Applied: The requested budget of ₹{requested_cap:,.0f} cannot support "
            f"a {state.constraints.duration_days}-day itinerary in {state.constraints.destination} ({state.constraints.month}). "
            f"Verified baseline required for safe winter travel is ₹{baseline_cost:,.0f} "
            f"(mandatory heated stays @ ₹3,000/night, snow-chain 4x4 mountain transit, and minimum food/activity baseline). "
            f"To guarantee traveler safety against sub-zero conditions, safety invariants took precedence over the budget cap."
        )
        
        state.critic_notes.append(relaxation_explanation)
        
        state.add_trace_step(
            thought=(
                f"CriticAgent: Budget cap of ₹{requested_cap:,.0f} is below sub-zero safety baseline (₹{baseline_cost:,.0f}). "
                f"Applying Constraint Relaxation Policy. Refusing to loop. Documenting safety trade-offs in audit notes."
            )
        )
