# TripMind Level 2.5: Model Context Protocol (MCP) Specification

> **Full Architecture & Blueprint Guide:** See [LEVEL_2_5_MCP_ARCHITECTURE.md](./LEVEL_2_5_MCP_ARCHITECTURE.md) for complete technical architecture, sequence diagrams, and host configurations.

## 1. Goal & Paradigm
Level 2.5 elevates TripMind from an internal Python library into a **Universal Model Context Protocol (MCP) Server & Agent-as-a-Tool**.

1. **Protocol Decoupling:** Decouples all verified leaf domain tools (stays, activities, transit, budget, regional accessibility) from the agent runtime using the open JSON-RPC 2.0 standard.
2. **Agent-as-a-Tool (AaaT):** Exposes the complete Level 2 Plan-and-Solve DAG Engine as a single composite tool (`plan_trip`) to external hosts like **Claude Desktop**, **Antigravity IDE**, and **Cursor**.
3. **Dual Transports:** Supports both local zero-port `stdio` child processes and cloud-ready `SSE` (Server-Sent Events over HTTP).
4. **Dedicated Observability:** Implements structured file logging (`logs/mcp_server.log`) avoiding protocol corruption on `stdout`.

---

## 2. Directory Structure
```text
tripmind/
├── mcp/
│   ├── __init__.py
│   ├── server.py        # Official MCPServer exposing 6 tools & Kashmir advisory resource
│   └── client.py        # High-level TripMindMCPClient for DAG worker integration
tests/
└── test_mcp.py          # 5 integration tests covering sync/async invocation & resources
specs/
└── mcp/
    ├── LEVEL_2_5_MCP_ARCHITECTURE.md   # Comprehensive architectural specification & sequence diagrams
    ├── MCP_SPECIFICATION.md            # Executive overview & quick reference
    └── tripmind-mcp-architecture.svg   # Architectural blueprint vector diagram
```
