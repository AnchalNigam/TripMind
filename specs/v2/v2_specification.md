# TripMind V2 Specification: Plan-and-Solve Hierarchical Engine

> **Full Architecture & Blueprint Guide:** See [LEVEL_2_PLAN_AND_SOLVE_ARCHITECTURE.md](./LEVEL_2_PLAN_AND_SOLVE_ARCHITECTURE.md) for complete details.

## 1. Goal & Architectural Paradigm
V2 elevates TripMind from a single-turn reactive loop into a **Hierarchical Plan-and-Solve Multi-Agent Architecture**.

Unlike V1 (where a single ReAct prompt iteratively called tools and attempted a massive monolithic JSON synthesis), V2 introduces:
1. **Strategic Planner:** Parses user intent into a typed Task DAG and spatial-temporal city partitions (e.g., Srinagar → Gulmarg) upfront.
2. **Specialized Worker Pool:** Dedicated asynchronous sub-agents for Accommodations, Curated Activities, and Intercity Mountain Transit.
3. **Structured Blackboard State Machine (`tripmind/v2/state.py`):** Replaces chat-dump memory with typed Pydantic objects, preventing context explosion and `HTTP 413` errors.
4. **Deterministic Financial Auditor (`tripmind/v2/auditor.py`):** Pure Python arithmetic for GST, buffers, and budget checks against the locked user cap.
5. **Critic & Bounded Replanner (`tripmind/v2/critic.py`):** Fixes slight overruns (targeted replan depth 1) or applies the Constraint Relaxation Policy for impossible budgets (e.g., ₹6k winter trip) without endless looping.
6. **Type-Safe Itinerary Compiler (`tripmind/v2/compiler.py`):** Hybrid curation (100-token LLM mapping) + deterministic Python object assembly. Eliminates all hallucinated fallbacks and token truncations.

---

## 2. Directory Structure
```text
tripmind/
├── v2/
│   ├── __init__.py
│   ├── state.py            # Typed Working Memory Blackboard & Task DAG Schemas
│   ├── planner.py          # Strategic Planner & Spatial-Temporal Hub Stager
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── staging.py      # Regional Accessibility & Hub Partitioning Worker
│   │   ├── stays.py        # Dedicated Heated Accommodation Sourcing Worker
│   │   ├── activities.py   # Dedicated Negative-Constraint Activity Worker
│   │   └── transit.py      # Dedicated Mountain Logistics & Routing Worker
│   ├── auditor.py          # Pure Deterministic Financial Arithmetic
│   ├── critic.py           # Constraint Critic & Bounded Replanning Engine
│   ├── compiler.py         # Type-Safe Hybrid Itinerary Compiler (Zero Fallbacks)
│   └── engine.py           # Plan-and-Solve Pipeline Orchestrator
```
