"""Generic Asynchronous DAG Execution Engine for Multi-Agent Architectures.

AGENTIC AI CONCEPT — Directed Acyclic Graph (DAG) Kernel:
1. In Level 1 (ReAct), single agents run an unstructured conversational loop where
   tools are called serially, blowing context windows and creating 15-30s latencies.
2. In Level 2 (DAG-Based Agent Engine), tasks are modeled as a Directed Acyclic Graph:
   - Nodes represent specialized Deliberative Agents or Deterministic Auditors.
   - Edges define causal dependencies (Node B cannot run until Node A completes).
   - In-degree resolution (Kahn's algorithm) dynamically finds all ready nodes.
   - Parallel Fan-Out: Independent nodes (e.g. Stays, Activities, Transit) run
     concurrently via asyncio.gather().
   - Join Barrier: Dependent downstream nodes (e.g. Financial Auditor) block until all
     upstream dependencies have successfully converged.
   - Dynamic Conditional Routing: The Critic agent acts as an edge router, dynamically
     triggering Selective Sub-Graph Invalidation without re-running unaffected nodes.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)
from pydantic import BaseModel, Field

from tripmind.v2.state import WorkingMemoryState, TaskStep

logger = logging.getLogger("tripmind.v2.graph")


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    INVALIDATED = "invalidated"


class RoutingAction(str, Enum):
    CONTINUE = "continue"
    REPLAN = "replan"
    TERMINATE = "terminate"


class RoutingDecision(BaseModel):
    """Dynamic routing output emitted by router nodes (such as the Critic)."""
    action: RoutingAction = RoutingAction.CONTINUE
    target_nodes: List[str] = Field(
        default_factory=list,
        description="List of node IDs to selectively invalidate during a replan."
    )
    next_node: Optional[str] = None
    reason: str = ""


NodeCallable = Callable[
    [WorkingMemoryState],
    Union[WorkingMemoryState, Awaitable[WorkingMemoryState]],
]
RouterCallable = Callable[
    [WorkingMemoryState],
    Union[RoutingDecision, Awaitable[RoutingDecision]],
]


class GraphNode:
    """A distinct vertex in the Agent Graph representing an agent, worker, or evaluator."""

    def __init__(
        self,
        node_id: str,
        name: str,
        func: NodeCallable,
        dependencies: Optional[List[str]] = None,
        description: str = "",
    ):
        self.node_id = node_id
        self.name = name
        self.func = func
        self.dependencies: List[str] = list(dependencies or [])
        self.description = description
        self.status: NodeStatus = NodeStatus.PENDING
        self.result_summary: Optional[str] = None
        self.error: Optional[str] = None

    async def execute(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Executes the node logic, supporting both synchronous and asynchronous functions."""
        self.status = NodeStatus.RUNNING
        state.mark_task_running(self.node_id)
        try:
            if inspect.iscoroutinefunction(self.func):
                result_state = await self.func(state)
            else:
                # Run sync functions in thread pool to avoid blocking the async event loop
                loop = asyncio.get_running_loop()
                result_state = await loop.run_in_executor(None, self.func, state)
                if inspect.iscoroutine(result_state):
                    result_state = await result_state

            self.status = NodeStatus.COMPLETED
            summary = self.result_summary or f"Node '{self.node_id}' completed."
            result_state.mark_task_completed(self.node_id, summary=summary)
            return result_state
        except Exception as exc:
            self.status = NodeStatus.FAILED
            self.error = str(exc)
            state.mark_task_failed(self.node_id, error=str(exc))
            logger.exception(f"Node '{self.node_id}' failed with exception: {exc}")
            raise


class ConditionalEdge:
    """A dynamic edge whose traversal is computed at runtime based on working state."""

    def __init__(self, source_node: str, router: RouterCallable):
        self.source_node = source_node
        self.router = router

    async def evaluate(self, state: WorkingMemoryState) -> RoutingDecision:
        if inspect.iscoroutinefunction(self.router):
            return await self.router(state)
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.router, state)


class AgentGraph:
    """Declarative Graph structure holding nodes, dependencies, and dynamic routers."""

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.adjacency: Dict[str, List[str]] = {}  # source -> list of targets
        self.conditional_routers: Dict[str, ConditionalEdge] = {}

    def add_node(
        self,
        node_id: str,
        name: str,
        func: NodeCallable,
        dependencies: Optional[List[str]] = None,
        description: str = "",
    ) -> GraphNode:
        """Registers a node in the graph."""
        deps = list(dependencies or [])
        node = GraphNode(
            node_id=node_id,
            name=name,
            func=func,
            dependencies=deps,
            description=description,
        )
        self.nodes[node_id] = node
        if node_id not in self.adjacency:
            self.adjacency[node_id] = []

        # Update adjacency from declared dependencies
        for dep in deps:
            if dep not in self.adjacency:
                self.adjacency[dep] = []
            if node_id not in self.adjacency[dep]:
                self.adjacency[dep].append(node_id)

        return node

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Adds a directed dependency edge (from_node must complete before to_node)."""
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError(f"Both nodes must exist: '{from_node}' -> '{to_node}'")

        if to_node not in self.nodes[to_node].dependencies:
            self.nodes[to_node].dependencies.append(from_node)

        if from_node not in self.adjacency:
            self.adjacency[from_node] = []
        if to_node not in self.adjacency[from_node]:
            self.adjacency[from_node].append(to_node)

    def add_conditional_router(
        self,
        source_node: str,
        router: RouterCallable,
    ) -> None:
        """Attaches a dynamic decision router to a node."""
        if source_node not in self.nodes:
            raise ValueError(f"Source node '{source_node}' does not exist.")
        self.conditional_routers[source_node] = ConditionalEdge(source_node, router)

    def validate_acyclic(self) -> None:
        """Verifies that the static graph has no circular dependencies using DFS cycle detection."""
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def dfs(node_id: str) -> bool:
            visited[node_id] = 1
            for neighbor in self.adjacency.get(node_id, []):
                if visited.get(neighbor) == 1:
                    return False  # Cycle detected
                if visited.get(neighbor, 0) == 0:
                    if not dfs(neighbor):
                        return False
            visited[node_id] = 2
            return True

        for node_id in self.nodes:
            if visited.get(node_id, 0) == 0:
                if not dfs(node_id):
                    raise ValueError(f"Circular dependency detected in graph involving node '{node_id}'.")

    def get_downstream_nodes(self, node_id: str) -> Set[str]:
        """Returns all transitive downstream dependents of a given node."""
        dependents: Set[str] = set()
        queue = [node_id]
        while queue:
            curr = queue.pop(0)
            for downstream in self.adjacency.get(curr, []):
                if downstream not in dependents:
                    dependents.add(downstream)
                    queue.append(downstream)
        return dependents


class DAGScheduler:
    """Asynchronous runtime scheduler that drives DAG execution with Kahn's Algorithm,

    Parallel Fan-Out, Join Barriers, and Selective Sub-Graph Invalidation.
    """

    def __init__(self, graph: AgentGraph, max_replan_epochs: int = 2):
        self.graph = graph
        self.max_replan_epochs = max_replan_epochs
        self.graph.validate_acyclic()

    async def execute(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Executes the graph asynchronously to completion."""
        # Synchronize graph task definitions with state blackboard
        for node_id, node in self.graph.nodes.items():
            if node_id not in state.tasks:
                state.tasks[node_id] = TaskStep(
                    task_id=node_id,
                    name=node.name,
                    description=node.description,
                    dependencies=node.dependencies,
                    status="pending",
                )

        epoch = 0
        while epoch <= self.max_replan_epochs:
            # 1. Find all ready nodes: in-degree dependencies satisfied and status is PENDING or INVALIDATED
            ready_nodes = self._get_ready_nodes(state)

            if not ready_nodes:
                # Check if all nodes are completed
                all_done = all(
                    self.graph.nodes[n].status == NodeStatus.COMPLETED
                    for n in self.graph.nodes
                )
                if all_done:
                    logger.info("DAG execution successfully completed: all nodes reached COMPLETED.")
                    break
                
                # Check if we are deadlocked or terminated
                pending_nodes = [
                    n for n, node in self.graph.nodes.items()
                    if node.status in (NodeStatus.PENDING, NodeStatus.INVALIDATED)
                ]
                if pending_nodes:
                    raise RuntimeError(
                        f"DAG Deadlock detected! Nodes {pending_nodes} could not resolve dependencies: "
                        f"{[(n, self.graph.nodes[n].dependencies) for n in pending_nodes]}"
                    )
                break

            # 2. Parallel Fan-Out: Execute all ready nodes concurrently
            logger.info(
                f"[DAGScheduler] Spawning parallel batch of {len(ready_nodes)} nodes: "
                f"{[n.node_id for n in ready_nodes]}"
            )
            state.log_milestone(
                "DAG Dispatch",
                "running",
                f"Executing parallel batch: {', '.join([n.name for n in ready_nodes])}"
            )

            # Concurrent execution barrier
            async def _run_node_isolated(node: GraphNode) -> Tuple[str, WorkingMemoryState]:
                res_state = await node.execute(state)
                return node.node_id, res_state

            tasks = [_run_node_isolated(node) for node in ready_nodes]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for node exceptions
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    failed_node = ready_nodes[idx]
                    logger.error(f"Node '{failed_node.node_id}' failed: {res}")
                    raise res

            # Join Barrier passed — Evaluate any conditional edge routers attached to completed nodes
            replan_requested = False
            for node in ready_nodes:
                if node.node_id in self.graph.conditional_routers:
                    router = self.graph.conditional_routers[node.node_id]
                    decision = await router.evaluate(state)
                    logger.info(f"Router on '{node.node_id}' emitted decision: {decision}")

                    if decision.action == RoutingAction.REPLAN:
                        epoch += 1
                        if epoch > self.max_replan_epochs:
                            logger.warning(
                                f"Max replan epochs ({self.max_replan_epochs}) reached. Aborting replan loop."
                            )
                            break

                        replan_requested = True
                        self._apply_selective_invalidation(decision.target_nodes, state)
                        break

                    elif decision.action == RoutingAction.TERMINATE:
                        logger.info(f"Router requested graph termination: {decision.reason}")
                        return state

            if replan_requested:
                continue

        return state

    def _get_ready_nodes(self, state: WorkingMemoryState) -> List[GraphNode]:
        """Identifies all nodes whose dependency nodes are completed."""
        ready: List[GraphNode] = []
        for node_id, node in self.graph.nodes.items():
            if node.status in (NodeStatus.PENDING, NodeStatus.INVALIDATED):
                deps_satisfied = True
                for dep_id in node.dependencies:
                    dep_node = self.graph.nodes.get(dep_id)
                    if not dep_node or dep_node.status != NodeStatus.COMPLETED:
                        deps_satisfied = False
                        break
                if deps_satisfied:
                    ready.append(node)
        return ready

    def _apply_selective_invalidation(
        self,
        target_node_ids: List[str],
        state: WorkingMemoryState,
    ) -> None:
        """Selectively invalidates target nodes and their downstream dependents.

        AGENTIC AI CONCEPT — Subgraph Invalidation:
        When a hotel budget overruns, we do NOT throw away curated activities or
        mountain transit routes. We invalidate ONLY the accommodation node and its
        downstream auditor/critic nodes, preserving valid working memory!
        """
        all_to_invalidate: Set[str] = set(target_node_ids)
        for target in target_node_ids:
            downstream = self.graph.get_downstream_nodes(target)
            all_to_invalidate.update(downstream)

        logger.info(f"[DAGScheduler] Selectively invalidating nodes: {list(all_to_invalidate)}")
        state.log_milestone(
            "Selective Invalidation",
            "running",
            f"Invalidating nodes: {', '.join(all_to_invalidate)} for targeted re-execution."
        )

        for nid in all_to_invalidate:
            if nid in self.graph.nodes:
                self.graph.nodes[nid].status = NodeStatus.INVALIDATED
                state.tasks[nid].status = "pending"
                state.tasks[nid].result_summary = None

    def execute_sync(self, state: WorkingMemoryState) -> WorkingMemoryState:
        """Synchronous wrapper to run the async DAG in standard thread contexts."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already inside an async loop (e.g. FastAPI / Jupyter), run via runner in a new thread or task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                def _runner():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(self.execute(state))
                    finally:
                        new_loop.close()

                return pool.submit(_runner).result()
        else:
            return asyncio.run(self.execute(state))
