"""Strategic Planner & Upfront Task DAG Generator for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — LLM-Driven Goal Normalization & Invariant Locking:
1. In production Agentic AI, user intent extraction is performed by the LLM using
   schema-constrained decoding (Pydantic / Structured Outputs). We never rely on fragile
   English keyword if-else branches or hardcoded city lists.
2. The user's budget ceiling is locked into `ParsedConstraints.budget_cap_inr`. If the user
   did not state a budget, it is set to `None` — the agent never invents an arbitrary cap.
3. The Planner generates a Directed Acyclic Graph (DAG) of typed tasks with explicit
   dependency relations.
"""

from typing import Optional, Dict, Any, List

from tripmind.v2.state import ParsedConstraints, TaskStep, WorkingMemoryState
from tripmind.core.llm import LLMClient


class StrategicPlanner:
    """Ingests raw user intent, locks hard constraints via LLM structured outputs, and initializes Task DAG."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def parse_user_constraints(self, user_query: str) -> ParsedConstraints:
        """Extracts and locks constraints from user query using LLM Structured Outputs."""
        client = self.llm_client or LLMClient(provider="mock")

        prompt = (
            f"Analyze the following travel request and extract all parameters into the structured schema:\n"
            f"User Query: \"{user_query}\"\n\n"
            f"Extraction Rules:\n"
            f"- destination: Target destination city, state, country, or region.\n"
            f"- month: Specific travel month (e.g. 'December', 'November') if mentioned, otherwise null.\n"
            f"- duration_days: Total trip length in days (e.g. 'weekend' -> 2, 'a week' -> 7, '5 days' -> 5). Default to 3 if unspecified.\n"
            f"- duration_nights: Overnight stays (typically duration_days - 1, minimum 1).\n"
            f"- traveler_profile: e.g. 'Couple', 'Family', 'Solo', 'Friends'.\n"
            f"- budget_cap_inr: Explicit total budget ceiling in INR if specified by the user (e.g. '80k' -> 80000.0, '6000' -> 6000.0). "
            f"If NO budget ceiling was mentioned, set to null. NEVER invent or assume a budget number.\n"
            f"- exclude_adventure: Set to true if the user explicitly asks to avoid adventure sports/activities. Otherwise false.\n"
            f"- pace: 'relaxed' (if unhurried, non-hectic, slow), 'fast' (if packed, cover everything), otherwise 'moderate'.\n"
            f"- special_interests: List of themes mentioned (e.g. ['scenic', 'culinary', 'beach', 'heritage', 'wildlife'])."
        )

        system_instruction = (
            "You are an expert travel intent parser. "
            "Extract user goals strictly into the required JSON schema without guessing unmentioned constraints."
        )

        constraints: ParsedConstraints = client.extract_structured(
            prompt=prompt,
            schema=ParsedConstraints,
            system_instruction=system_instruction,
        )

        return constraints

    def build_initial_dag(self) -> Dict[str, TaskStep]:
        """Constructs the 6-stage Task DAG."""
        return {
            "T1_STAGING": TaskStep(
                task_id="T1_STAGING",
                name="Geographic & Temporal Stager",
                description="Query regional accessibility and partition days into locked geographic hubs.",
                dependencies=[],
                status="pending",
            ),
            "T2_STAYS": TaskStep(
                task_id="T2_STAYS",
                name="Accommodation Sourcing Worker",
                description="Source verified heated accommodations strictly for the staged hubs.",
                dependencies=["T1_STAGING"],
                status="pending",
            ),
            "T3_ACTIVITIES": TaskStep(
                task_id="T3_ACTIVITIES",
                name="Activity Curation Worker",
                description="Source non-adventure scenic and culinary experiences strictly per hub.",
                dependencies=["T1_STAGING"],
                status="pending",
            ),
            "T4_TRANSIT": TaskStep(
                task_id="T4_TRANSIT",
                name="Mountain Logistics Worker",
                description="Compute required intercity transfer legs, transit times, and vehicle specs.",
                dependencies=["T1_STAGING"],
                status="pending",
            ),
            "T5_AUDIT": TaskStep(
                task_id="T5_AUDIT",
                name="Deterministic Financial Auditor",
                description="Execute pure mathematical audit (GST, buffers, subtotal) against locked budget cap.",
                dependencies=["T2_STAYS", "T3_ACTIVITIES", "T4_TRANSIT"],
                status="pending",
            ),
            "T6_CRITIC": TaskStep(
                task_id="T6_CRITIC",
                name="Constraint Critic & Evaluator",
                description="Evaluate budget compliance; trigger targeted replan or constraint relaxation policy.",
                dependencies=["T5_AUDIT"],
                status="pending",
            ),
            "T7_COMPILER": TaskStep(
                task_id="T7_COMPILER",
                name="Type-Safe Itinerary Compiler",
                description="Curate day mapping and assemble TripPlanResponse directly from state objects.",
                dependencies=["T6_CRITIC"],
                status="pending",
            ),
        }

    def initialize_state(self, user_query: str) -> WorkingMemoryState:
        """Creates the initial WorkingMemoryState with locked constraints and Task DAG."""
        constraints = self.parse_user_constraints(user_query)
        tasks = self.build_initial_dag()
        state = WorkingMemoryState(
            user_query=user_query,
            constraints=constraints,
            tasks=tasks,
        )

        cap_text = f"₹{constraints.budget_cap_inr:,.0f}" if constraints.budget_cap_inr else "Uncapped"
        state.log_milestone(
            "Milestone 0: Plan Ingestion",
            "completed",
            f"Locked parameters: Destination '{constraints.destination}', {constraints.duration_days} days, "
            f"Budget: {cap_text}, Pace: {constraints.pace}. DAG initialized with {len(tasks)} tasks."
        )
        return state
