"""Strategic Planner & Upfront Task DAG Generator for Level 2 (Plan-and-Solve).

AGENTIC AI CONCEPT — Goal Normalization & Invariant Locking:
1. In Level 1, the LLM was asked repeatedly about the budget cap, causing hallucinated
   caps like ₹30,000 to creep into the system.
2. In Level 2, the Strategic Planner extracts and HARD-LOCKS all user constraints upfront.
3. The Planner generates a Directed Acyclic Graph (DAG) of typed tasks with explicit
   dependency relations.
"""

import re
from typing import Optional, Dict, Any, List
from pydantic import BaseModel

from tripmind.v2.state import ParsedConstraints, TaskStep, WorkingMemoryState
from tripmind.core.llm import LLMClient


class StrategicPlanner:
    """Ingests raw user intent, locks hard constraints, and initializes the Task DAG."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client

    def parse_user_constraints(self, user_query: str) -> ParsedConstraints:
        """Extracts and locks constraints from user query with deterministic fallbacks."""
        # Rule-based regex extraction guarantees budget numbers are never hallucinated
        budget_cap = self._extract_budget_inr(user_query)
        duration_days = self._extract_duration_days(user_query)
        duration_nights = max(1, duration_days - 1)
        month = self._extract_month(user_query)
        destination = self._extract_destination(user_query)
        
        exclude_adventure = (
            "not interested in adventure" in user_query.lower()
            or "no adventure" in user_query.lower()
            or "aren't interested in adventure" in user_query.lower()
            or "avoid adventure" in user_query.lower()
        )
        
        pace = "relaxed" if any(p in user_query.lower() for p in ["not hectic", "non-hectic", "don't want a hectic", "relaxed", "slow"]) else "moderate"
        
        traveler_profile = "Couple" if any(w in user_query.lower() for w in ["wife", "husband", "partner", "couple", "honeymoon"]) else "Solo / Group"
        
        interests: List[str] = []
        if "scenic" in user_query.lower() or "nature" in user_query.lower() or "views" in user_query.lower():
            interests.append("scenic")
        if "food" in user_query.lower() or "culinary" in user_query.lower() or "dining" in user_query.lower():
            interests.append("culinary")
        if not interests:
            interests = ["scenic", "culinary"]

        # If LLM client is available and user query is complex, we can refine destination/month
        # but ALWAYS keep the regex-extracted budget_cap to prevent hallucinations
        if self.llm_client:
            try:
                prompt = (
                    f"Extract travel parameters from this request as JSON: '{user_query}'\n"
                    f"Keys: destination, month, duration_days, budget_cap_inr.\n"
                    f"Example: {{\"destination\": \"Kashmir\", \"month\": \"December\", \"duration_days\": 5, \"budget_cap_inr\": 80000.0}}"
                )
                res = self.llm_client.call_fast(
                    prompt=prompt,
                    system_instruction="You are a strict JSON data extractor. Output only valid JSON."
                )
                import json
                parsed = json.loads(res.strip("` \n").replace("json\n", ""))
                if "destination" in parsed and parsed["destination"]:
                    destination = parsed["destination"]
                if "month" in parsed and parsed["month"]:
                    month = parsed["month"]
                if "duration_days" in parsed and isinstance(parsed["duration_days"], (int, float)):
                    duration_days = int(parsed["duration_days"])
                    duration_nights = max(1, duration_days - 1)
                # Only take LLM budget if regex didn't find one
                if budget_cap == 80000.0 and "budget_cap_inr" in parsed and isinstance(parsed["budget_cap_inr"], (int, float)):
                    budget_cap = float(parsed["budget_cap_inr"])
            except Exception:
                pass  # Fall back reliably to rule-based constraints

        return ParsedConstraints(
            destination=destination,
            month=month,
            duration_days=duration_days,
            duration_nights=duration_nights,
            traveler_profile=traveler_profile,
            budget_cap_inr=budget_cap,
            exclude_adventure=exclude_adventure,
            pace=pace,
            special_interests=interests,
        )

    def _extract_budget_inr(self, text: str) -> float:
        """Extracts exact budget cap in INR without ambiguity."""
        # Check patterns like ₹80k, 80k, 6k, ₹6,000, 80000
        k_match = re.search(r'(?:₹|rs\.?|inr)?\s*([0-9]+(?:\.[0-9]+)?)\s*k\b', text, re.IGNORECASE)
        if k_match:
            return float(k_match.group(1)) * 1000.0

        num_match = re.search(r'(?:₹|rs\.?|inr|budget\s*(?:around|of|is)?)\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]{4,7})', text, re.IGNORECASE)
        if num_match:
            clean_str = num_match.group(1).replace(',', '')
            return float(clean_str)

        return 80000.0  # Default benchmark budget

    def _extract_duration_days(self, text: str) -> int:
        match = re.search(r'([0-9]+)\s*days?', text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 5

    def _extract_month(self, text: str) -> str:
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        for m in months:
            if re.search(rf'\b{m}\b', text, re.IGNORECASE):
                return m
        return "December"

    def _extract_destination(self, text: str) -> str:
        destinations = ["Kashmir", "Goa", "Himachal", "Kerala", "Ladakh", "Rajasthan", "Paris", "Kyoto"]
        for d in destinations:
            if re.search(rf'\b{d}\b', text, re.IGNORECASE):
                return d
        return "Kashmir"

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
        state.log_milestone(
            "Milestone 0: Plan Ingestion",
            "completed",
            f"Locked budget cap ₹{constraints.budget_cap_inr:,.0f}, {constraints.duration_days} days in {constraints.destination} ({constraints.month}). DAG initialized with {len(tasks)} tasks."
        )
        return state
