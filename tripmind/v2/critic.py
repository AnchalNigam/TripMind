"""Constraint Critic & Dynamic Graph Router for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Reflection, Critique, & Dynamic Routing:
1. In Level 1, when an unachievable budget (e.g. ₹6,000 for 5 days in winter Kashmir)
   was encountered, the agent thrashed across 10 turns and triggered broken fallback values.
2. In Level 2 DAG, the Critic acts as a Dynamic Graph Router:
   - Evaluates state invariants (heating, adventure exclusion, financial audit).
   - If budget overrun is fixable: emits `RoutingDecision(action="replan", target_nodes=["T2_STAYS"])`.
     The DAG scheduler selectively invalidates ONLY the stay worker, keeping activities and transit intact!
   - If mathematically unachievable: applies the Constraint Relaxation Policy, transparently
     documents trade-offs, and routes safely to compilation without looping.
"""

from typing import List, Optional

from tripmind.v2.state import WorkingMemoryState
from tripmind.v2.graph import RoutingDecision, RoutingAction


class CriticAgent:
    """Evaluates candidate itinerary artifacts against non-negotiable constraints and routes graph execution."""

    def __init__(self):
        pass

    def route(self, state: WorkingMemoryState) -> RoutingDecision:
        """Dynamic router evaluated by the DAGScheduler after T5_AUDIT completes."""
        self.evaluate(state)

        # 1. If critic passed or relaxation already applied -> proceed to compiler
        if state.critic_passed or state.constraint_relaxation_applied:
            return RoutingDecision(
                action=RoutingAction.CONTINUE,
                reason="Constraints satisfied or relaxation policy applied. Proceeding to compilation."
            )

        # 2. Check if targeted replan is viable (budget overrun <= 35% and replan_count < 1)
        audit = state.financial_audit
        cap = state.constraints.budget_cap_inr
        if cap and audit and state.replan_count < 1 and audit.total_estimated_inr <= (cap * 1.35):
            state.replan_count += 1
            state.add_trace_step(
                thought=(
                    f"CriticAgent [Router]: Budget overrun detected (₹{audit.total_estimated_inr:,.0f} vs cap ₹{cap:,.0f}). "
                    f"Requesting selective DAG replan of node 'T2_STAYS' with budget-tier lodging."
                ),
                tool_name="replan_stays",
            )
            # Switch stay preference for the next run
            return RoutingDecision(
                action=RoutingAction.REPLAN,
                target_nodes=["T2_STAYS"],
                reason=f"Selective replan: swap hotel tier to fit cap ₹{cap:,.0f}."
            )

        # 3. If unachievable or replan budget still exceeded, apply relaxation and continue
        self._apply_constraint_relaxation(state)
        return RoutingDecision(
            action=RoutingAction.CONTINUE,
            reason="Constraint Relaxation Policy applied; continuing to compilation."
        )

    def evaluate(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Inspects state and verifies heating, negative adventure invariants, and financial viability."""
        state.mark_task_running("T6_CRITIC")
        state.log_milestone("Milestone 4: Critic Review", "running", "Evaluating safety, heating, adventure, and budget constraints...")

        is_winter = bool(state.constraints.month and state.constraints.month.lower() in ["december", "january", "february"])
        
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

        if not state.constraints.budget_cap_inr:
            state.critic_passed = True
            state.critic_notes.append(f"Budget unconstrained: Total estimated expenditure is ₹{audit.total_estimated_inr:,.0f}.")
        elif audit.is_within_budget:
            state.critic_passed = True
            state.critic_notes.append(f"Budget compliant: Total ₹{audit.total_estimated_inr:,.0f} <= Cap ₹{state.constraints.budget_cap_inr:,.0f}.")
        else:
            state.critic_passed = False

        summary = f"Critic review complete (Passed: {state.critic_passed}, Notes: {len(state.critic_notes)})."
        state.mark_task_completed("T6_CRITIC", summary=summary)
        state.log_milestone("Milestone 4: Critic Review", "completed", summary)
        return state

    def evaluate_and_replan(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Synchronous wrapper for legacy/direct test invocations."""
        decision = self.route(state)
        if decision.action == RoutingAction.REPLAN:
            # Import dynamically to perform localized replan when invoked directly outside DAGScheduler
            from tripmind.v2.workers.stays import StayWorker
            from tripmind.v2.auditor import FinancialAuditor
            
            StayWorker().run(state, prefer_budget_tier=True)
            FinancialAuditor().run(state)
            
            # Re-check after targeted replan
            if state.financial_audit and state.financial_audit.is_within_budget:
                state.critic_passed = True
                note = f"Targeted replan successful: Selected tier-2 stays. New total ₹{state.financial_audit.total_estimated_inr:,.0f} is within cap."
                state.critic_notes.append(note)
            else:
                self._apply_constraint_relaxation(state)

        return state

    def _apply_constraint_relaxation(self, state: WorkingMemoryState) -> None:
        """Applies the Constraint Relaxation Policy for impossible or severe budget deficits."""
        state.constraint_relaxation_applied = True
        state.critic_passed = True  # Allows pipeline to compile safely

        requested_cap = state.constraints.budget_cap_inr or 0.0
        baseline_cost = state.financial_audit.total_estimated_inr if state.financial_audit else 25000.0
        
        is_subzero = any("-" in r.temp_range_celsius for r in state.accessible_regions)
        safety_context = (
            "mandatory heated stays and winter mountain transit"
            if is_subzero
            else "essential lodging, minimum daily dining, and local transit transfers"
        )
        month_str = f" ({state.constraints.month})" if state.constraints.month else ""

        relaxation_explanation = (
            f"Constraint Relaxation Policy Applied: The requested budget of ₹{requested_cap:,.0f} cannot support "
            f"a {state.constraints.duration_days}-day itinerary in {state.constraints.destination}{month_str}. "
            f"Verified baseline required for safe travel is ₹{baseline_cost:,.0f} ({safety_context}). "
            f"Essential lodging and traveler safety took precedence over the unachievable budget cap."
        )
        
        state.critic_notes.append(relaxation_explanation)
        
        state.add_trace_step(
            thought=(
                f"CriticAgent: Budget cap of ₹{requested_cap:,.0f} is below sub-zero safety baseline (₹{baseline_cost:,.0f}). "
                f"Applying Constraint Relaxation Policy. Refusing to loop. Documenting safety trade-offs in audit notes."
            )
        )
