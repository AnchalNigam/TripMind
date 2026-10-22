"""Comprehensive Unit & Stress Tests for TripMind Level 2 True DAG Engine.

Verifies:
1. Mathematical cycle detection & acyclic graph validation.
2. Async parallel fan-out and join barrier synchronization.
3. Sub-agent persona deliberation & rationale recording.
4. Selective sub-graph invalidation during dynamic replan loops.
5. Dynamic DAG topology adaptation (e.g. single-day excursion omitting stays).
"""

import pytest
import asyncio
from typing import Set

from tripmind.v2.state import WorkingMemoryState, ParsedConstraints, TaskStep
from tripmind.v2.graph import (
    AgentGraph,
    DAGScheduler,
    GraphNode,
    NodeStatus,
    RoutingDecision,
    RoutingAction,
)
from tripmind.v2.engine import PlanAndSolveEngine
from tripmind.v2.planner import StrategicPlanner
from tripmind.v2.workers.staging import StagingWorker
from tripmind.v2.workers.stays import StayWorker
from tripmind.v2.workers.activities import ActivityWorker
from tripmind.v2.workers.transit import TransitWorker
from tripmind.v2.auditor import FinancialAuditor
from tripmind.v2.critic import CriticAgent
from tripmind.schemas.itinerary import TripPlanResponse


BENCHMARK_QUERY = (
    "I want to visit Kashmir in December for 5 days. I'm going with my wife. "
    "We don't want a hectic trip. We love scenic places and food, but aren't "
    "interested in adventure activities. Budget around ₹80k excluding flights."
)


def test_agent_graph_cycle_detection():
    """Verify that AgentGraph mathematical validation prevents circular dependency deadlocks."""
    graph = AgentGraph()
    graph.add_node("A", "Node A", lambda s: s, dependencies=[])
    graph.add_node("B", "Node B", lambda s: s, dependencies=["A"])
    graph.add_node("C", "Node C", lambda s: s, dependencies=["B"])
    
    # Static graph is acyclic initially
    graph.validate_acyclic()

    # Introduce circular dependency: A depends on C
    graph.add_edge(from_node="C", to_node="A")
    with pytest.raises(ValueError, match="Circular dependency detected"):
        graph.validate_acyclic()


@pytest.mark.asyncio
async def test_dag_parallel_fanout_and_barrier():
    """Verify that independent nodes execute concurrently in parallel and the join barrier holds."""
    execution_order = []
    concurrency_counter = 0
    max_concurrency_observed = 0

    async def mock_staging(state: WorkingMemoryState) -> WorkingMemoryState:
        execution_order.append("staging")
        return state

    async def mock_parallel_worker(state: WorkingMemoryState, name: str) -> WorkingMemoryState:
        nonlocal concurrency_counter, max_concurrency_observed
        concurrency_counter += 1
        max_concurrency_observed = max(max_concurrency_observed, concurrency_counter)
        await asyncio.sleep(0.05)  # Simulate non-blocking async network/LLM I/O
        execution_order.append(name)
        concurrency_counter -= 1
        return state

    async def mock_barrier_node(state: WorkingMemoryState) -> WorkingMemoryState:
        execution_order.append("barrier_audit")
        return state

    graph = AgentGraph()
    graph.add_node("STAGING", "Staging", mock_staging, dependencies=[])
    graph.add_node("STAYS", "Stays", lambda s: mock_parallel_worker(s, "stays"), dependencies=["STAGING"])
    graph.add_node("ACTIVITIES", "Activities", lambda s: mock_parallel_worker(s, "activities"), dependencies=["STAGING"])
    graph.add_node("TRANSIT", "Transit", lambda s: mock_parallel_worker(s, "transit"), dependencies=["STAGING"])
    graph.add_node("AUDIT", "Audit", mock_barrier_node, dependencies=["STAYS", "ACTIVITIES", "TRANSIT"])

    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(BENCHMARK_QUERY)

    scheduler = DAGScheduler(graph=graph)
    final_state = await scheduler.execute(state)

    # 1. Staging must be first
    assert execution_order[0] == "staging"
    # 2. Audit must be last (after all parallel workers converge)
    assert execution_order[-1] == "barrier_audit"
    # 3. Parallel concurrency must have reached 3 during the parallel batch
    assert max_concurrency_observed == 3
    # 4. All 3 parallel nodes executed
    parallel_batch = set(execution_order[1:4])
    assert parallel_batch == {"stays", "activities", "transit"}


def test_sub_agent_persona_deliberation():
    """Verify that StayWorker and ActivityWorker record explicit deliberation rationales in state."""
    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(BENCHMARK_QUERY)

    # Execute Staging
    state = StagingWorker().run(state)
    assert len(state.day_stages) > 0

    # Execute StayWorker with deliberation
    stay_worker = StayWorker(llm_client=None)
    state = stay_worker.run(state)

    # Verify stays deliberation rationale is stored
    assert "stay_Srinagar" in state.deliberation_rationales
    srinagar_stay_rationale = state.deliberation_rationales["stay_Srinagar"]
    assert len(srinagar_stay_rationale) > 20
    assert "rating" in srinagar_stay_rationale.lower() or "heating" in srinagar_stay_rationale.lower()

    # Execute ActivityWorker with deliberation
    activity_worker = ActivityWorker(llm_client=None)
    state = activity_worker.run(state)

    # Verify activities deliberation rationale is stored
    assert "activities_Srinagar" in state.deliberation_rationales
    srinagar_act_rationale = state.deliberation_rationales["activities_Srinagar"]
    assert len(srinagar_act_rationale) > 20
    assert "pace" in srinagar_act_rationale.lower() or "scenic" in srinagar_act_rationale.lower()


@pytest.mark.asyncio
async def test_selective_subgraph_invalidation():
    """Verify that targeted replan invalidates ONLY stays and downstream, preserving activities and transit."""
    planner = StrategicPlanner(llm_client=None)
    state = planner.initialize_state(BENCHMARK_QUERY)
    
    engine = PlanAndSolveEngine(provider="mock")
    graph = engine.build_execution_graph(state)

    scheduler = DAGScheduler(graph=graph, max_replan_epochs=2)

    # Simulate T1, T2, T3, T4 completed
    state = engine.staging_worker.run(state)
    graph.nodes["T1_STAGING"].status = NodeStatus.COMPLETED

    state = engine.stay_worker.run(state)
    graph.nodes["T2_STAYS"].status = NodeStatus.COMPLETED

    state = engine.activity_worker.run(state)
    graph.nodes["T3_ACTIVITIES"].status = NodeStatus.COMPLETED

    state = engine.transit_worker.run(state)
    graph.nodes["T4_TRANSIT"].status = NodeStatus.COMPLETED

    # Now apply selective invalidation targeted at T2_STAYS
    scheduler._apply_selective_invalidation(["T2_STAYS"], state)

    # Verify: T2_STAYS is invalidated
    assert graph.nodes["T2_STAYS"].status == NodeStatus.INVALIDATED
    # Verify: Downstream nodes (T5_AUDIT, T6_CRITIC, T7_COMPILER) are invalidated
    assert graph.nodes["T5_AUDIT"].status == NodeStatus.INVALIDATED
    assert graph.nodes["T6_CRITIC"].status == NodeStatus.INVALIDATED
    assert graph.nodes["T7_COMPILER"].status == NodeStatus.INVALIDATED

    # CRITICAL CHECK: T3_ACTIVITIES and T4_TRANSIT MUST REMAIN COMPLETED!
    assert graph.nodes["T3_ACTIVITIES"].status == NodeStatus.COMPLETED
    assert graph.nodes["T4_TRANSIT"].status == NodeStatus.COMPLETED


@pytest.mark.asyncio
async def test_dynamic_dag_async_plan():
    """Verify end-to-end asynchronous plan_async execution over the full DAG."""
    engine = PlanAndSolveEngine(provider="mock")
    plan: TripPlanResponse = await engine.plan_async(BENCHMARK_QUERY)

    assert plan.destination == "Kashmir"
    assert plan.duration_days == 5
    assert len(plan.days) == 5
    assert plan.budget_summary.budget_cap_inr == 80000.0
    assert plan.budget_summary.is_within_budget is True


def test_dynamic_dag_single_day_tailoring():
    """Verify that for a 1-day excursion with 0 nights, the Planner dynamically omits T2_STAYS."""
    day_query = "1 day excursion in Jaipur visiting palaces and local street food. Budget ₹5000."
    planner = StrategicPlanner(llm_client=None)
    constraints = planner.parse_user_constraints(day_query)

    # If duration_days == 1 and duration_nights == 0, T2_STAYS is omitted
    single_day_constraints = ParsedConstraints(
        destination="Jaipur",
        duration_days=1,
        duration_nights=0,
        budget_cap_inr=5000.0,
        pace="moderate",
    )
    dag_tasks = planner.build_initial_dag(constraints=single_day_constraints)

    assert "T2_STAYS" not in dag_tasks
    assert "T3_ACTIVITIES" in dag_tasks
    assert "T4_TRANSIT" in dag_tasks
    assert "T2_STAYS" not in dag_tasks["T5_AUDIT"].dependencies
