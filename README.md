# TripMind 🏔️ — Autonomous Adaptive Trip Planner

> *An end-to-end, multi-level educational masterclass across the 7 progressive levels of Agentic AI.*

---

## 🎯 The Core Philosophy: Goal-Driven, Adaptive, and Intuitively Verifiable

Most AI trip planners are glorified search engines that regurgitate static lists. **TripMind** is an **autonomous, adaptive agent** designed to solve goal-oriented travel with real-life constraints:
- **Goals over Destinations:** Instead of asking for a pre-selected checklist, the user provides high-level desires, constraints, and budgets.
- **Adaptive Replanning (Human-in-the-Loop):** When a user provides feedback (*"My wife gets motion sickness on winding hill roads, drop mountain drives"*), the agent dynamically adapts and recalculates the itinerary without starting from scratch.
- **Zero-Math Intuitive Verification:** You don't need complex equations to evaluate quality. Anyone can look at an itinerary in 10 seconds and verify whether it followed constraints:
  - Did it violate the ₹80,000 budget?
  - Did it accidentally schedule adventure activities (skiing/paragliding) when the user said "no adventure"?
  - Are hotel rooms guaranteed to have heating for December sub-zero winter?
  - Are driving times realistic given snowy mountain conditions?

---

## ❄️ The Benchmark Scenario: A 5-Day Kashmir Winter Journey

**User Prompt:**
> *"I want to visit Kashmir in December for 5 days. I'm going with my wife. We don't want a hectic trip. We love scenic places and food, but aren't interested in adventure activities. Budget around ₹80k excluding flights."*

### What the Agent Must Autonomously Reason & Plan:
1. **Pace & Region Selection:** Sonamarg is closed due to snow in December. Attempting Srinagar + Gulmarg + Pahalgam in 5 days is too hectic. The agent recommends either *Srinagar (3N) + Gulmarg (2N)* or *Srinagar (3N) + Pahalgam (2N)*.
2. **Winter Suitability:** Recommends boutique stays with central heating and electric blankets; factors in winter daylight (sunset at 5:15 PM) and chain-taxi requirements for snow-covered roads.
3. **Scenic & Culinary Curation:** Replaces generic spots with authentic experiences: private sunset Shikara ride on Dal Lake, saffron Kahwa tea at a glass cottage, traditional Wazwan dinner at Ahdoos, and riverside strolls.
4. **Budget Breakdown:** Transparent allocation across boutique stays, private winter cab, scenic experiences, and meals fitting strictly within ₹80,000.
5. **Replanning on Feedback:** Dynamically updates routes, costs, and bookings if the traveler changes preferences.

---

## 🗺️ The 7-Version Evolutionary Roadmap

| Level | Agentic AI Concept | What TripMind Implements |
| :--- | :--- | :--- |
| **V1** | **Multi-Turn Reactive Tool Calling** | ReAct loop dynamically calling tools for regional weather, mountain transit times, heated stays, scenic spots, and budget calculation. |
| **V2** | **Self-Reflection & Auto-Healing** | LLM-as-a-Judge critique loop auditing tentative plans against pace, adventure exclusions, December weather suitability, and budget caps. |
| **V3** | **Plan-and-Solve with Scratchpad Memory & Dynamic Replanning** | Structured 3-option blueprint decomposition with an in-memory scratchpad and real-time Human-in-the-Loop (HITL) replanning engine. |
| **V4** | **Hybrid RAG for Unstructured Knowledge** | Vector database indexing raw traveler trip reports, authentic culinary guides, and winter mountain road advisories. |
| **V5** | **Model Context Protocol (MCP) — Client & Server** | Consumes external Weather & Distance MCP servers, and exposes TripMind itself as a standalone MCP server via FastMCP for Claude Desktop & Cursor. |
| **V6** | **Multi-Agent Collaboration Crew** | Specialized agent team: Route & Transit Specialist, Hospitality Expert, Food & Scenic Curator, and Budget Compliance Auditor. |
| **V7** | **Production Observability & Automated Evals** | Automated benchmark test suite evaluating 10 diverse traveler personas on constraint satisfaction rate, feasibility score, and token latency. |

---

## 🏗️ System Architecture

```
                                USER REQUEST
                                     │
                                     ▼
                      +-----------------------------+
                      |      TripMind Engine        |
                      |   (FastAPI + Pydantic v2)   |
                      +--------------+--------------+
                                     │
           ┌─────────────────────────┼─────────────────────────┐
           ▼                         ▼                         ▼
+---------------------+   +---------------------+   +---------------------+
|   V1-V3: Core ReAct |   | V4: Unstructured RAG|   | V5-V6: MCP & Agents |
| • Dynamic Tooling   |   | • Local Food Guides |   | • Weather MCP Client|
| • Reflection Loop   |   | • Winter Advisories |   | • Distance MCP Client|
| • Replanning Engine |   | • Vector Store      |   | • FastMCP Server    |
+---------------------+   +---------------------+   +---------------------+
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     ▼
                       +---------------------------+
                       | Verified 5-Day Itinerary  |
                       |  & Visual Route Map       |
                       +---------------------------+
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend dashboard)
- Git

### Installation
```bash
# Clone the repository
git clone git@github.com:AnchalNigam/TripMind.git
cd TripMind

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

---

## 📜 License
MIT License. Built for deep exploration and mastery of Agentic AI architectures.
