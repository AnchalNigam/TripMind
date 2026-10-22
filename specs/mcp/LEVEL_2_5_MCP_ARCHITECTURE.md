# TripMind Level 2.5: Model Context Protocol (MCP) & Agent-as-a-Tool Architecture

> **Repository:** [TripMind (GitHub)](https://github.com/AnchalNigam/TripMind)  
> **Evolutionary Stage:** Level 2.5 (Decoupled Tool Protocol & Agent-as-a-Tool)  
> **Status:** Production-Ready & Tested (41/41 passing tests)

---

## 1. Architectural Motivation & Paradigm Shift

In **Level 1** (ReAct) and **Level 2** (Plan-and-Solve DAG Engine), tools were directly imported in Python (`from tripmind.tools import ...`). While powerful for a monolithic local script, direct Python imports suffer from critical architectural coupling:

1. **Runtime & Language Lock-in:** The agent engine and tools must live in the exact same Python process, virtual environment, and dependency tree.
2. **Credential & Host Exposure:** Every host environment (desktop IDE, web backend, test script) must possess all API credentials, databases, and filesystem access.
3. **No External Interoperability:** An external AI host (such as **Claude Desktop**, **Antigravity**, **Cursor**, or a cloud multi-agent system) cannot utilize TripMind's verified travel tools without re-implementing them.

### The Solution: Model Context Protocol (MCP 2.x)
TripMind Level 2.5 introduces the **Model Context Protocol (Anthropic / Linux Foundation open standard)**, decoupling the agentic system into:
- **MCP Server (`tripmind/mcp/server.py`):** Exposes tools, resources, and end-to-end agents over standardized JSON-RPC 2.0.
- **MCP Client (`tripmind/mcp/client.py`):** Enables TripMind's DAG workers to consume tools dynamically across protocol boundaries.
- **Agent-as-a-Tool (AaaT):** Encapsulates the entire Level 2 DAG Pipeline as a single composite tool (`plan_trip`), allowing any external MCP host to invoke TripMind as an autonomous travel specialist.

---

## 2. System Architecture

![TripMind MCP Architecture](./tripmind-mcp-architecture.svg)

```mermaid
flowchart TD
    subgraph ExternalHosts ["External MCP Hosts (AI Clients)"]
        Claude["Claude Desktop"]
        AGY["Antigravity IDE"]
        Cursor["Cursor AI"]
        CustomAgent["Custom Agent / Python Client"]
    end

    subgraph ProtocolBoundary ["JSON-RPC 2.0 Protocol Boundary (stdio / SSE)"]
        JSONRPC{{"Standardized Messages<br>tools/list | tools/call | resources/read"}}
    end

    subgraph MCPServer ["TripMind MCP Server (tripmind/mcp/server.py)"]
        Dispatcher["MCP Request Dispatcher & Validator"]
        
        subgraph GranularTools ["Granular Domain Tools (The Hands)"]
            T_Stays["search_accommodations"]
            T_Act["get_activities"]
            T_Transit["calculate_travel_route"]
            T_Audit["calculate_budget_breakdown"]
            T_Regions["search_regions"]
        end

        subgraph CompositeTools ["Composite Agentic Tool (Agent-as-a-Tool)"]
            T_PlanTrip["plan_trip(user_query)"]
        end

        subgraph Resources ["Read-Only Context Resources"]
            R_Advisory["tripmind://advisories/kashmir"]
        end
    end

    subgraph InternalEngine ["TripMind V2 DAG Execution Kernel"]
        DAG["DAGScheduler (Kahn's Topological Sort)"]
        Workers["Parallel Deliberative Workers<br>(Stays, Activities, Transit)"]
        Auditor["Deterministic Financial Auditor"]
        Critic["Dynamic Critic & Router"]
        Compiler["Type-Safe Hybrid Compiler"]
    end

    Claude ==> JSONRPC
    AGY ==> JSONRPC
    Cursor ==> JSONRPC
    CustomAgent ==> JSONRPC

    JSONRPC --> Dispatcher
    Dispatcher --> GranularTools
    Dispatcher --> CompositeTools
    Dispatcher --> Resources

    T_PlanTrip --> InternalEngine
    DAG --> Workers --> Auditor --> Critic --> Compiler
```

---

## 3. The Dual Tooling Topology

TripMind's MCP Server provides two distinct tiers of capabilities:

### Tier 1: Granular Domain Tools (The "Hands")
Pure leaf functions with deterministic verification, negative constraint filtering, and zero-hallucination arithmetic:

| Tool Name | Parameters | Responsibility | Deterministic Guard |
| :--- | :--- | :--- | :--- |
| `search_accommodations` | `region`, `min_rating`, `required_amenities`, `max_nightly_rate_inr` | Sources verified hotels, boutique cottages, and houseboats. | Verifies central heating / electric blankets for winter sub-zero safety. |
| `get_activities` | `region`, `month`, `preferred_categories`, `exclude_adventure` | Discovers verified scenic, culinary, and cultural experiences. | Strict negative constraint filtering (purges heli-skiing, snowmobiling when `exclude_adventure=True`). |
| `calculate_travel_route` | `origin`, `destination`, `month` | Calculates mountain road distances, drive durations, and costs. | Enforces mandatory 4x4 snow chain vehicles for mountain switchbacks. |
| `calculate_budget_breakdown` | `stays_cost`, `transit_cost`, `food_cost`, `activities_cost`, `max_budget_cap_inr` | Pure Python financial auditor. | Computes 5% GST, 10% emergency buffer, and audits headroom against user budget cap. |
| `search_regions` | `destination`, `month` | Analyzes regional accessibility, seasonal passes, and daylight windows. | Detects seasonal closures (e.g. Sonamarg/Zojila winter pass shutdowns). |

### Tier 2: Composite Agentic Tool (Agent-as-a-Tool — AaaT)
* **Tool Name:** `plan_trip`
* **Input Schema:** `{"user_query": str}`
* **Description:** An external host calls this single tool with natural language intent (e.g. *"Plan a 5-day winter trip to Kashmir with ₹80,000 budget"*). The MCP server launches the entire **Level 2 Plan-and-Solve DAG Engine**:
  1. Staging worker partitions destinations into locked city hubs.
  2. Stays, Activities, and Transit workers execute in parallel via Kahn's algorithm (`asyncio.gather`).
  3. Financial Auditor checks deterministic budget compliance.
  4. Dynamic Critic evaluates constraints or triggers bounded replanning.
  5. Type-Safe Compiler synthesizes the final verified `TripPlanResponse`.

---

## 4. Circular Import & Recursion Guards

A critical architectural challenge when implementing **Agent-as-a-Tool**:
* The **MCP Server** (`server.py`) exposes `plan_trip`, which imports `PlanAndSolveEngine`.
* The **PlanAndSolveEngine** (`engine.py`) initializes workers that can optionally use `TripMindMCPClient` to call leaf tools.
* The **TripMindMCPClient** (`client.py`) connects back to `server.py`.

### Engineering Solution:
1. **Lazy Engine Import:** `server.py` lazily imports `PlanAndSolveEngine` inside `plan_trip()` only at invocation time.
2. **Re-Entrant Guard Flag (`use_mcp=False`):** When `server.py` executes `PlanAndSolveEngine`, it passes `use_mcp=False`. This forces the internal workers to use fast in-memory direct calls, completely preventing infinite recursive process-spawning loops while still allowing external hosts to treat the entire agent as a tool.

---

## 5. Transports & Host Lifecycle

The MCP specification defines two transports. TripMind supports both:

### A. `stdio` Transport (Default for Local Desktop Hosts)
* **Mechanics:** The Host (Antigravity IDE, Claude Desktop, Cursor) spawns `.venv/bin/python -m tripmind.mcp.server` as a private child process using OS pipes (`stdin`/`stdout`).
* **Tenancy:** 1 Host : 1 Private Subprocess.
* **Network Ports:** None required (zero network exposure).
* **Protocol Rule:** `stdout` is strictly reserved for JSON-RPC bytes. Raw `print()` statements are forbidden.

#### Host Configuration (`.mcp.json` or Claude Desktop Config):
```json
{
  "mcpServers": {
    "tripmind-travel": {
      "command": "/Users/anchalnigam/Documents/AI_WORLD/tripMind/.venv/bin/python",
      "args": ["-m", "tripmind.mcp.server"],
      "env": {
        "PYTHONPATH": "/Users/anchalnigam/Documents/AI_WORLD/tripMind"
      }
    }
  }
}
```

### B. `SSE` Transport (Server-Sent Events over HTTP)
* **Mechanics:** The MCP Server runs as a persistent web service (Starlette/FastAPI) on a dedicated port (e.g. `http://localhost:8001/sse`).
* **Tenancy:** Many Hosts : 1 Shared Server Instance.
* **Remote Deployment:** Allows TripMind to be deployed to AWS/GCP as a centralized AI microservice with Bearer token authentication.

#### Host Configuration (SSE Mode):
```json
{
  "mcpServers": {
    "tripmind-cloud": {
      "url": "http://localhost:8001/sse",
      "headers": {
        "Authorization": "Bearer sk-tripmind-enterprise-key"
      }
    }
  }
}
```

---

## 6. Observability & Validation Framework

Because `stdout` cannot be used for application logging in `stdio` mode, TripMind implements an enterprise three-tier observability stack:

1. **Persistent File Logging (`logs/mcp_server.log`):**
   * Configured via Python's standard `logging` with structured timestamps and tool metadata.
   * Developers inspect calls in real time using:
     ```bash
     tail -f logs/mcp_server.log
     ```
2. **Standard Error Stream (`stderr`):**
   * Per MCP specification, `stderr` is passed through by the host process into IDE debug logs.
3. **The Official MCP Inspector:**
   * Used for interactive Postman-style schema validation and manual invocation:
     ```bash
     npx @modelcontextprotocol/inspector .venv/bin/python -m tripmind.mcp.server
     ```

---

## 7. Test Suite & Verification

The MCP implementation is covered by automated regression tests in [`tests/test_mcp.py`](../../tests/test_mcp.py):

* `test_mcp_server_initialization`: Verifies server registration and versioning.
* `test_mcp_tools_registration`: Asserts all 6 tools are registered with valid schemas.
* `test_mcp_client_tool_execution`: Tests asynchronous client execution across leaf tools.
* `test_mcp_client_sync_invocation`: Tests synchronous wrapper bridging sync worker runtimes.
* `test_mcp_resource_read`: Tests markdown context resource retrieval (`tripmind://advisories/kashmir`).

**Current Status:** `41 passed in 13.12s` (100% test pass rate across V1, V2 DAG, and MCP suites).
