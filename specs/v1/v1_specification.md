# TripMind V1 Specification: Reactive Tool-Calling Engine

## 1. Goal & Overview
V1 establishes the foundational layer of TripMind: an autonomous **ReAct (Reasoning + Acting) Agent** capable of dynamic, multi-turn tool calling to formulate a tailored, constraint-compliant itinerary from a high-level user goal.

---

## 2. Benchmark Evaluation Scenario
**User Request:**
> *"I want to visit Kashmir in December for 5 days. I'm going with my wife. We don't want a hectic trip. We love scenic places and food, but aren't interested in adventure activities. Budget around ₹80k excluding flights."*

### Key Constraints to Verify:
1. **Duration:** Exactly 5 days (4 nights).
2. **Season Alignment:** December winter conditions (sub-zero temperatures, snowbound passes, sunset at 5:15 PM).
3. **Pace:** Non-hectic ($\le 2$ regions total, maximum 2.5 hours transit per travel day).
4. **Theme:** Scenic views and authentic culinary experiences.
5. **Negative Constraint:** Zero adventure sports (no skiing, no paragliding, no high-altitude trekking).
6. **Budget:** Total trip cost $\le ₹80,000$ (excluding flights).

---

## 3. Tool Suite Architecture
The V1 agent is equipped with 5 atomic, deterministic Python tools:

### `search_regions`
- **Parameters:** `destination: str`, `month: str`
- **Returns:** List of accessible sub-regions, seasonal status (open/snowbound), daylight hours, temperature range, and winter travel warnings.

### `calculate_travel_route`
- **Parameters:** `origin: str`, `destination: str`, `month: str`
- **Returns:** Distance in km, estimated drive time factoring in snow/ice, road conditions, and chain-taxi requirements.

### `search_accommodations`
- **Parameters:** `region: str`, `min_rating: float`, `required_amenities: list[str]`, `max_nightly_rate: float`
- **Returns:** Verified boutique/heritage stays with heating guarantees (electric blankets, central heating, bukhari) and couple ratings.

### `get_scenic_and_culinary_activities`
- **Parameters:** `region: str`, `month: str`, `activity_types: list[str]`, `exclude_adventure: bool`
- **Returns:** Curated non-hectic activities (sunset Shikara rides, Wazwan dining, saffron farm visits, Betab Valley walks).

### `calculate_budget_breakdown`
- **Parameters:** `stays_cost: float`, `cab_cost: float`, `food_cost: float`, `activities_cost: float`, `buffer_pct: float`
- **Returns:** Itemized cost table, GST estimate, total amount, and remaining budget headroom against ₹80,000 cap.

---

## 4. Expected V1 Deliverables
1. **Backend:** FastAPI service with `POST /api/v1/planner/plan` endpoint.
2. **Agent Engine:** Provider-agnostic LLM client (Groq / OpenAI / Gemini) executing multi-turn tool-calling loops.
3. **Itinerary Output:** Structured JSON response + human-readable markdown brief with daily schedule, travel times, heating confirmations, and budget audit.
4. **Automated Unit Tests:** 100% test coverage for all 5 tools and agent response validation.
