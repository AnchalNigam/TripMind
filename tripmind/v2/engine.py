"""Master Plan-and-Solve Orchestrator Engine for Level 2 (TripMind V2).

AGENTIC AI CONCEPT — Hierarchical Plan-and-Solve Pipeline:
1. Ingests user goal and initializes the typed Blackboard state (`WorkingMemoryState`).
2. Executes Stage 1: Strategic Stager partitions days into locked geographic hubs.
3. Executes Stage 2: Specialized Worker Pool (Stays, Activities, Transit) populates domain facts.
4. Executes Stage 3: Deterministic Financial Auditor calculates exact totals & GST.
5. Executes Stage 4: Constraint Critic evaluates invariants & triggers targeted replan or relaxation.
6. Executes Stage 5: Hybrid Curation & Type-Safe Compiler binds validated Pydantic objects into TripPlanResponse.
"""

import asyncio
from typing import Optional

from tripmind.v2.state import WorkingMemoryState
from tripmind.v2.planner import StrategicPlanner
from tripmind.v2.workers.staging import StagingWorker
from tripmind.v2.workers.stays import StayWorker
from tripmind.v2.workers.activities import ActivityWorker
from tripmind.v2.workers.transit import TransitWorker
from tripmind.v2.auditor import FinancialAuditor
from tripmind.v2.critic import CriticAgent
from tripmind.v2.compiler import ItineraryCompiler
from tripmind.schemas.itinerary import TripPlanResponse
from tripmind.core.llm import LLMClient
from tripmind.config import settings


class PlanAndSolveEngine:
    """The Level 2 Plan-and-Solve Multi-Agent Engine."""

    def __init__(self, provider: Optional[str] = None):
        chosen_provider = provider or settings.TRIPMIND_LLM_PROVIDER
        self.llm_client = LLMClient(provider=chosen_provider) if chosen_provider != "mock" else None
        self.planner = StrategicPlanner(llm_client=self.llm_client)
        self.staging_worker = StagingWorker()
        self.stay_worker = StayWorker()
        self.activity_worker = ActivityWorker()
        self.transit_worker = TransitWorker()
        self.auditor = FinancialAuditor()
        self.critic = CriticAgent()
        self.compiler = ItineraryCompiler(llm_client=self.llm_client)

    def plan(self, user_query: str) -> TripPlanResponse:
        """Executes the synchronous 5-stage Plan-and-Solve pipeline."""
        # Step 0: Ingestion & Blackboard Initialization
        state: WorkingMemoryState = self.planner.initialize_state(user_query)

        # Stage 1: Regional Accessibility & Day Staging
        state = self.staging_worker.run(state)

        # Stage 2: Worker Pool (Stays, Activities, Transit)
        state = self.stay_worker.run(state)
        state = self.activity_worker.run(state)
        state = self.transit_worker.run(state)

        # Stage 3: Deterministic Financial Audit
        state = self.auditor.run(state)

        # Stage 4: Constraint Critic & Bounded Replanning
        state = self.critic.evaluate_and_replan(state)

        # Stage 5: Type-Safe Compilation
        state = self.compiler.compile(state)

        if not state.final_response:
            raise RuntimeError("Level 2 Engine failed to compile final TripPlanResponse.")

        return state.final_response

    async def plan_async(self, user_query: str) -> TripPlanResponse:
        """Executes the asynchronous Plan-and-Solve pipeline with parallel worker dispatch."""
        # Step 0: Ingestion & Blackboard Initialization
        state: WorkingMemoryState = self.planner.initialize_state(user_query)

        # Stage 1: Regional Accessibility & Day Staging
        state = self.staging_worker.run(state)

        # Stage 2: Parallel Worker Pool Dispatch via asyncio
        loop = asyncio.get_event_loop()
        state = await loop.run_in_executor(None, self.stay_worker.run, state)
        state = await loop.run_in_executor(None, self.activity_worker.run, state)
        state = await loop.run_in_executor(None, self.transit_worker.run, state)

        # Stage 3: Deterministic Financial Audit
        state = self.auditor.run(state)

        # Stage 4: Constraint Critic & Bounded Replanning
        state = self.critic.evaluate_and_replan(state)

        # Stage 5: Type-Safe Compilation
        state = self.compiler.compile(state)

        if not state.final_response:
            raise RuntimeError("Level 2 Engine failed to compile final TripPlanResponse.")

        return state.final_response
