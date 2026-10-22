"""Master Plan-and-Solve Orchestrator Engine for Level 2 (TripMind V2).

AGENTIC AI CONCEPT — Real DAG Kernel & Asynchronous Multi-Agent Execution:
1. Ingests user goal and locks non-negotiable constraints into `WorkingMemoryState`.
2. Dynamically constructs an `AgentGraph` with explicit dependencies and conditional edge routers.
3. Dispatches execution via `DAGScheduler`:
   - Stage 1: StagingWorker partitions days into spatial-temporal regional hubs.
   - Stage 2: Parallel Fan-Out: StayWorker, ActivityWorker, and TransitWorker execute
     concurrently via `asyncio.gather()`, running persona deliberations over tool observations.
   - Stage 3: Join Barrier synchronizes parallel branches before FinancialAuditor runs.
   - Stage 4: FinancialAuditor calculates exact deterministic arithmetic (GST, buffers).
   - Stage 5: CriticAgent evaluates constraints and acts as a Dynamic Graph Router.
     If a fixable budget overrun occurs, it selectively invalidates `T2_STAYS` and loops;
     if mathematically impossible, it applies the Constraint Relaxation Policy.
   - Stage 6: ItineraryCompiler curates and compiles the final validated `TripPlanResponse`.
"""

import asyncio
from typing import Optional

from tripmind.v2.state import WorkingMemoryState
from tripmind.v2.graph import AgentGraph, DAGScheduler, RoutingAction
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


from tripmind.mcp.client import TripMindMCPClient


class PlanAndSolveEngine:
    """The Level 2 Plan-and-Solve Multi-Agent Engine powered by an Asynchronous DAG and MCP."""

    def __init__(self, provider: Optional[str] = None, use_mcp: bool = True):
        chosen_provider = provider or settings.TRIPMIND_LLM_PROVIDER
        self.llm_client = LLMClient(provider=chosen_provider) if chosen_provider != "mock" else None
        self.mcp_client = TripMindMCPClient() if use_mcp else None

        self.planner = StrategicPlanner(llm_client=self.llm_client)
        self.staging_worker = StagingWorker(llm_client=self.llm_client, mcp_client=self.mcp_client)
        self.stay_worker = StayWorker(llm_client=self.llm_client, mcp_client=self.mcp_client)
        self.activity_worker = ActivityWorker(llm_client=self.llm_client, mcp_client=self.mcp_client)
        self.transit_worker = TransitWorker(llm_client=self.llm_client, mcp_client=self.mcp_client)
        self.auditor = FinancialAuditor(mcp_client=self.mcp_client)
        self.critic = CriticAgent()
        self.compiler = ItineraryCompiler(llm_client=self.llm_client)

    def build_execution_graph(self, state: WorkingMemoryState) -> AgentGraph:
        """Constructs the executable AgentGraph based on locked state constraints."""
        graph = AgentGraph()

        # Node 1: Spatial & Temporal Staging
        graph.add_node(
            node_id="T1_STAGING",
            name="Geographic & Temporal Stager",
            func=self.staging_worker.run,
            dependencies=[],
            description="Query regional accessibility and partition days into locked geographic hubs."
        )

        # Check if lodging is needed
        has_stays = not (state.constraints.duration_days == 1 and state.constraints.duration_nights == 0)

        if has_stays:
            # Node 2: Stay Specialist Agent (Perception + Deliberation)
            graph.add_node(
                node_id="T2_STAYS",
                name="Accommodation Sourcing Specialist",
                func=lambda s: self.stay_worker.run(s, prefer_budget_tier=(s.replan_count > 0)),
                dependencies=["T1_STAGING"],
                description="Source and deliberate verified heated accommodations strictly for the staged hubs."
            )

        # Node 3: Activity Specialist Agent (Perception + Deliberation)
        graph.add_node(
            node_id="T3_ACTIVITIES",
            name="Activity Curation Specialist",
            func=self.activity_worker.run,
            dependencies=["T1_STAGING"],
            description="Source and deliberate scenic and culinary experiences strictly per hub."
        )

        # Node 4: Mountain Logistics Worker
        graph.add_node(
            node_id="T4_TRANSIT",
            name="Mountain Logistics Worker",
            func=self.transit_worker.run,
            dependencies=["T1_STAGING"],
            description="Compute required intercity transfer legs, transit times, and vehicle specs."
        )

        # Node 5: Deterministic Financial Auditor (Join Barrier on Stays, Activities, Transit)
        audit_deps = ["T2_STAYS", "T3_ACTIVITIES", "T4_TRANSIT"] if has_stays else ["T3_ACTIVITIES", "T4_TRANSIT"]
        graph.add_node(
            node_id="T5_AUDIT",
            name="Deterministic Financial Auditor",
            func=self.auditor.run,
            dependencies=audit_deps,
            description="Execute pure mathematical audit (GST, buffers, subtotal) against locked budget cap."
        )

        # Node 6: Constraint Critic & Evaluator
        graph.add_node(
            node_id="T6_CRITIC",
            name="Constraint Critic & Evaluator",
            func=self.critic.evaluate,
            dependencies=["T5_AUDIT"],
            description="Evaluate safety, heating, adventure exclusion, and budget compliance."
        )

        # Attach Dynamic Conditional Router to Critic Node
        graph.add_conditional_router(
            source_node="T6_CRITIC",
            router=self.critic.route
        )

        # Node 7: Final Type-Safe Compiler
        graph.add_node(
            node_id="T7_COMPILER",
            name="Type-Safe Itinerary Compiler",
            func=self.compiler.compile,
            dependencies=["T6_CRITIC"],
            description="Assemble final schema-validated TripPlanResponse from state artifacts."
        )

        return graph

    def plan(self, user_query: str) -> TripPlanResponse:
        """Executes the Plan-and-Solve pipeline synchronously via the DAG Scheduler."""
        # Step 0: Ingestion & Blackboard Initialization
        state: WorkingMemoryState = self.planner.initialize_state(user_query)

        # Step 1: Build execution graph
        graph = self.build_execution_graph(state)

        # Step 2: Drive execution with the DAGScheduler
        scheduler = DAGScheduler(graph=graph, max_replan_epochs=2)
        state = scheduler.execute_sync(state)

        if not state.final_response:
            raise RuntimeError("Level 2 DAG Engine failed to compile final TripPlanResponse.")

        return state.final_response

    async def plan_async(self, user_query: str) -> TripPlanResponse:
        """Executes the Plan-and-Solve pipeline asynchronously with real parallel fan-out."""
        # Step 0: Ingestion & Blackboard Initialization
        state: WorkingMemoryState = self.planner.initialize_state(user_query)

        # Step 1: Build execution graph
        graph = self.build_execution_graph(state)

        # Step 2: Drive execution with the DAGScheduler
        scheduler = DAGScheduler(graph=graph, max_replan_epochs=2)
        state = await scheduler.execute(state)

        if not state.final_response:
            raise RuntimeError("Level 2 DAG Engine failed to compile final TripPlanResponse.")

        return state.final_response
