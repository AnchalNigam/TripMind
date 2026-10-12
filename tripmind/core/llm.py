"""LLM Provider Abstraction Layer (Gemini, Groq, Mock).

AGENTIC AI CONCEPT — Model-Agnostic Agentic Protocols:
An industrial-grade agent should never be married to a single model vendor.
Vendors differ in tool schemas, token limits, and function calling conventions:
- Google Gemini: Uses native FunctionDeclaration / types.Content
- Groq / OpenAI: Uses JSON Schema inside `{"type": "function", "function": ...}`
This abstraction layer normalizes diverse LLM providers into a uniform,
clean ReAct turn protocol.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from tripmind.config import settings
from tripmind.tools.registry import Tool, default_registry

logger = logging.getLogger("tripmind.llm")


class ToolCallItem(BaseModel):
    """Normalized tool call emitted by an LLM."""
    call_id: str
    name: str
    arguments: Dict[str, Any]
    thought_signature: Optional[Any] = Field(default=None, exclude=True)


class LLMTurnResponse(BaseModel):
    """Normalized response of a single LLM turn."""
    thought: Optional[str] = None
    content: Optional[str] = None
    tool_calls: List[ToolCallItem] = []

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers supporting function calling."""

    @abstractmethod
    def generate_turn(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Tool],
    ) -> LLMTurnResponse:
        """Execute a single inference turn given conversation history and active tools."""
        pass


# ---------------------------------------------------------------------------
# 1. Google Gemini Provider (Official google-genai SDK)
# ---------------------------------------------------------------------------
class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider using official `google-genai` SDK."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        from google import genai

        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please set it in your .env file or environment, "
                "or switch TRIPMIND_LLM_PROVIDER to 'mock' or 'groq'."
            )
        self.client = genai.Client(api_key=self.api_key)
        self.model = model or settings.GEMINI_MODEL

    def generate_turn(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Tool],
    ) -> LLMTurnResponse:
        from google.genai import types

        # Convert tool schemas to Gemini format
        callable_tools = [t.func for t in tools]
        config = types.GenerateContentConfig(
            tools=callable_tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=True
            ),
            temperature=0.2,  # Low temperature for deterministic planning
        )

        # Build contents from message history
        contents = []
        for msg in messages:
            role = msg.get("role")
            content_str = msg.get("content", "")
            if role == "system":
                # In Gemini SDK, system instructions can be added to config or as user preamble
                config.system_instruction = content_str
            elif role == "user":
                contents.append(types.Content(role="user", parts=[types.Part.from_text(text=content_str)]))
            elif role == "assistant":
                parts = []
                if content_str:
                    parts.append(types.Part.from_text(text=content_str))
                for tc in msg.get("tool_calls", []):
                    fn_name = tc["name"]
                    fn_args = tc["arguments"]
                    p = types.Part.from_function_call(name=fn_name, args=fn_args)
                    sig = tc.get("thought_signature")
                    if sig:
                        p.thought_signature = sig
                    parts.append(p)
                contents.append(types.Content(role="model", parts=parts))
            elif role == "tool":
                fn_name = msg.get("name", "")
                result_str = msg.get("content", "")
                try:
                    result_json = json.loads(result_str)
                except Exception:
                    result_json = {"output": result_str}
                part = types.Part.from_function_response(name=fn_name, response={"result": result_json})
                contents.append(types.Content(role="user", parts=[part]))

        import time
        resp = None
        max_retries = 4
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                break
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries:
                    wait_sec = attempt * 5  # 5s, 10s, 15s backoff
                    logger.warning(
                        f"Gemini Free Tier rate limit (429) hit. Backing off for {wait_sec}s before retry (attempt {attempt}/{max_retries})..."
                    )
                    time.sleep(wait_sec)
                else:
                    raise e

        # Parse Gemini response for function calls vs final text
        tool_calls = []
        text_content = ""
        thought_trace = ""

        if resp.candidates and resp.candidates[0].content and resp.candidates[0].content.parts:
            for idx, part in enumerate(resp.candidates[0].content.parts):
                if getattr(part, "function_call", None):
                    fc = part.function_call
                    tool_calls.append(
                        ToolCallItem(
                            call_id=f"call_{idx}_{fc.name}",
                            name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                            thought_signature=getattr(part, "thought_signature", None),
                        )
                    )

        if resp.text:
            text_content = resp.text
            # Extract thought if delimited
            if "<thought>" in text_content and "</thought>" in text_content:
                parts = text_content.split("</thought>")
                thought_trace = parts[0].replace("<thought>", "").strip()
        try:
            logger.info(f"--- [LLM RAW RESPONSE: Gemini] ---\n{resp}")
        except Exception:
            pass
        turn_res = LLMTurnResponse(
            thought=thought_trace or "Reasoning over travel constraints and determining next action.",
            content=text_content,
            tool_calls=tool_calls,
        )
        try:
            logger.info(f"--- [NORMALIZED LLM TURN RESPONSE] ---\n{turn_res.model_dump_json(indent=2)}")
        except Exception:
            logger.info(f"--- [NORMALIZED LLM TURN RESPONSE] --- (tool_calls={len(tool_calls)})")
        return turn_res


# ---------------------------------------------------------------------------
# 2. Groq Provider (Fast Llama-3.3-70b via groq SDK)
# ---------------------------------------------------------------------------
class GroqProvider(BaseLLMProvider):
    """Groq Provider for ultra-fast open models (Llama 3.3 70B)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        import groq

        self.api_key = api_key or settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Please set it in your .env file or environment, "
                "or switch TRIPMIND_LLM_PROVIDER to 'mock' or 'gemini'."
            )
        self.client = groq.Groq(api_key=self.api_key)
        self.model = model or settings.GROQ_MODEL

    def generate_turn(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Tool],
    ) -> LLMTurnResponse:
        groq_tools = [
            {
                "type": "function",
                "function": tool.schema,
            }
            for tool in tools
        ]

        # Standard OpenAI/Groq message history format
        formatted_msgs = []
        for msg in messages:
            role = msg.get("role")
            if role in ["system", "user"]:
                formatted_msgs.append({"role": role, "content": msg.get("content", "")})
            elif role == "assistant":
                item: Dict[str, Any] = {"role": "assistant", "content": msg.get("content") or ""}
                if msg.get("tool_calls"):
                    item["tool_calls"] = [
                        {
                            "id": tc["call_id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": json.dumps(tc["arguments"]),
                            },
                        }
                        for tc in msg["tool_calls"]
                    ]
                formatted_msgs.append(item)
            elif role == "tool":
                formatted_msgs.append({
                    "role": "tool",
                    "tool_call_id": msg.get("tool_call_id", "call_default"),
                    "name": msg.get("name"),
                    "content": msg.get("content", ""),
                })

        # Dynamic Token Allocation:
        # Tool turns only emit short function calls (~50 tokens), so 800 keeps us under the OTPM limit.
        # The final synthesis turn produces a multi-day itinerary in JSON, requiring 2048 tokens.
        extra_kwargs: Dict[str, Any] = {}
        if groq_tools:
            extra_kwargs["tools"] = groq_tools
            extra_kwargs["max_tokens"] = 800
        else:
            extra_kwargs["max_tokens"] = 2048

        import time
        resp = None
        max_retries = 4
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_msgs,
                    temperature=0.2,
                    **extra_kwargs,
                )
                break
            except Exception as e:
                err_str = str(e)
                if ("413" in err_str or "payload too large" in err_str.lower()) and attempt < max_retries:
                    logger.warning("Groq 413 Payload Too Large. Compacting payload and retrying immediately...")
                    for m in formatted_msgs:
                        if m.get("role") == "tool" and len(m.get("content", "")) > 250:
                            m["content"] = m["content"][:250] + "... [compacted]"
                    continue

                if ("429" in err_str or "rate_limit" in err_str.lower()) and attempt < max_retries:
                    import re
                    wait_sec = 10.0 * attempt
                    match = re.search(r"try again in (\d+(\.\d+)?)s", err_str)
                    if match:
                        wait_sec = float(match.group(1)) + 1.5
                    elif hasattr(e, "response") and getattr(e, "response", None) is not None:
                        ra = e.response.headers.get("retry-after")
                        if ra:
                            try:
                                wait_sec = max(float(ra) + 1.0, wait_sec)
                            except ValueError:
                                pass
                    logger.warning(
                        f"Groq rate limit hit. Backing off for {wait_sec:.1f}s before retry (attempt {attempt}/{max_retries})..."
                    )
                    time.sleep(wait_sec)
                else:
                    raise e

        choice = resp.choices[0]
        raw_tool_calls = choice.message.tool_calls or []
        parsed_tcs = []
        for tc in raw_tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}
            parsed_tcs.append(
                ToolCallItem(
                    call_id=tc.id,
                    name=tc.function.name,
                    arguments=args,
                )
            )

        content = choice.message.content or ""
        thought = "Deliberating on route, constraints, and budget."
        if "<thought>" in content and "</thought>" in content:
            parts = content.split("</thought>")
            thought = parts[0].replace("<thought>", "").strip()
            content = parts[1].strip()

        logger.info(f"--- [LLM RAW RESPONSE: Groq] ---\n{choice.message}")
        turn_res = LLMTurnResponse(
            thought=thought,
            content=content,
            tool_calls=parsed_tcs,
        )
        logger.info(f"--- [NORMALIZED LLM TURN RESPONSE] ---\n{turn_res.model_dump_json(indent=2)}")
        return turn_res


# ---------------------------------------------------------------------------
# 3. Deterministic Mock Provider (Zero-Cost Offline Replay Driver)
# ---------------------------------------------------------------------------
class MockProvider(BaseLLMProvider):
    """Deterministic Replay Engine for Kashmir & Goa benchmarks.
    
    AGENTIC AI CONCEPT — Simulation & Regression Testing:
    In professional agent engineering, automated tests should not burn tokens
    or flake because of external provider latency. The MockProvider simulates
    the authentic multi-step reasoning progression of a top-tier LLM.
    """

    def __init__(self):
        self._turn_counter = 0

    def generate_turn(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Tool],
    ) -> LLMTurnResponse:
        # Determine how many tool responses have been collected
        tool_responses = [m for m in messages if m.get("role") == "tool"]
        num_tools_called = len(tool_responses)

        # Inspect user query to see destination
        user_query = ""
        for m in messages:
            if m.get("role") == "user":
                user_query = m.get("content", "").lower()
                break

        is_assam = "assam" in user_query
        is_goa = "goa" in user_query
        is_kashmir = not (is_assam or is_goa)

        if num_tools_called == 0:
            # Step 1: Perception — Search regions and seasonal weather
            if is_assam:
                dest, month = "Assam", "November"
            elif is_goa:
                dest, month = "Goa", "November"
            else:
                dest, month = "Kashmir", "December"

            return LLMTurnResponse(
                thought=f"I need to check accessible sub-regions, weather conditions, and seasonal hazards for {dest} in {month}.",
                tool_calls=[
                    ToolCallItem(
                        call_id="call_mock_1",
                        name="search_regions",
                        arguments={"destination": dest, "month": month},
                    )
                ],
            )

        elif num_tools_called == 1:
            # Step 2: Transit calculation
            if is_assam:
                return LLMTurnResponse(
                    thought="The user is in Delhi and has only 2 days in Assam. A train takes 28-36 hours one-way, which would consume the entire trip. Direct flight is mandatory. Checking flight options.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_2",
                            name="calculate_travel_route",
                            arguments={
                                "origin": "New Delhi (DEL)",
                                "destination": "Guwahati (GAU)",
                                "month": "November",
                                "mode": "flight",
                            },
                        )
                    ],
                )
            elif is_goa:
                return LLMTurnResponse(
                    thought="Calculating transit from Dabolim airport to South Goa.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_2",
                            name="calculate_travel_route",
                            arguments={
                                "origin": "Dabolim Airport",
                                "destination": "South Goa",
                                "month": "November",
                                "mode": "road",
                            },
                        )
                    ],
                )
            else:
                return LLMTurnResponse(
                    thought="Sonamarg is closed in December. To avoid a hectic pace, 5 days is best split between Srinagar (3N) and Gulmarg (2N) or Pahalgam. Let's calculate mountain driving transit times and check for snow-chain requirements.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_2",
                            name="calculate_travel_route",
                            arguments={
                                "origin": "Srinagar",
                                "destination": "Gulmarg",
                                "month": "December",
                                "mode": "road",
                            },
                        )
                    ],
                )

        elif num_tools_called == 2:
            # Step 3: Search accommodations
            if is_assam:
                return LLMTurnResponse(
                    thought="User has 1 night stay in Guwahati with remaining budget headroom. Let's find a top-rated boutique/luxury stay on the Brahmaputra banks.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_3",
                            name="search_accommodations",
                            arguments={
                                "region": "Guwahati",
                                "min_rating": 4.5,
                                "max_nightly_rate_inr": 7000.0,
                            },
                        )
                    ],
                )
            else:
                region = "South Goa" if is_goa else "Srinagar"
                amenities = ["ac", "swimming_pool"] if is_goa else ["central_heating", "electric_blanket"]
                return LLMTurnResponse(
                    thought="Accommodations query with verified amenities.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_3",
                            name="search_accommodations",
                            arguments={
                                "region": region,
                                "min_rating": 4.5,
                                "required_amenities": amenities,
                                "max_nightly_rate_inr": 8000.0,
                            },
                        )
                    ],
                )

        elif num_tools_called == 3:
            # Step 4: Curate activities with negative constraint (NO adventure)
            region = "Guwahati" if is_assam else ("South Goa" if is_goa else "Srinagar")
            return LLMTurnResponse(
                thought="The user explicitly requested authentic culinary dining and stated 'no adventure sports'. Query activities while strictly setting exclude_adventure=True.",
                tool_calls=[
                    ToolCallItem(
                        call_id="call_mock_4",
                        name="get_activities",
                        arguments={
                            "region": region,
                            "month": "November" if (is_assam or is_goa) else "December",
                            "preferred_categories": ["scenic", "culinary"],
                            "exclude_adventure": True,
                        },
                    )
                ],
            )

        elif num_tools_called == 4:
            # Step 5: Audit budget deterministically
            if is_assam:
                return LLMTurnResponse(
                    thought="Flights (~₹11,500), 1 night stay (~₹6,200), local cab (~₹4,500), authentic meals (~₹3,500), cruise (~₹1,800). Verifying 5% GST and ₹35,000 budget cap.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_5",
                            name="calculate_budget_breakdown",
                            arguments={
                                "stays_cost_inr": 6200.0,
                                "transit_cost_inr": 16000.0,
                                "food_cost_inr": 3500.0,
                                "activities_cost_inr": 1800.0,
                                "emergency_buffer_pct": 10.0,
                                "max_budget_cap_inr": 35000.0,
                            },
                        )
                    ],
                )
            else:
                return LLMTurnResponse(
                    thought="Audit budget deterministically against cap.",
                    tool_calls=[
                        ToolCallItem(
                            call_id="call_mock_5",
                            name="calculate_budget_breakdown",
                            arguments={
                                "stays_cost_inr": 30000.0,
                                "transit_cost_inr": 7000.0,
                                "food_cost_inr": 12000.0,
                                "activities_cost_inr": 5000.0,
                                "emergency_buffer_pct": 10.0,
                                "max_budget_cap_inr": 80000.0,
                            },
                        )
                    ],
                )

        else:
            # Final Synthesis Turn: Output complete valid TripPlanResponse JSON
            if is_assam:
                final_json = {
                    "trip_title": "2-Day Relaxing Assam Culinary & Riverfront Escape",
                    "destination": "Assam (Guwahati & Brahmaputra)",
                    "month": "November",
                    "duration_days": 2,
                    "duration_nights": 1,
                    "traveler_profile": "Solo/Couple traveler seeking authentic Assamese cuisine & scenic river relaxation from Delhi",
                    "days": [
                        {
                            "day_number": 1,
                            "title": "Day 1: Arrival, Golden Sunset River Cruise & Grand Parampara Thali",
                            "region": "Guwahati",
                            "stay": {
                                "name": "Vivanta Guwahati",
                                "region": "Guwahati",
                                "rating": 4.7,
                                "price_per_night_inr": 6200.0,
                                "heating_verified": False,
                                "amenities": ["ac", "tea_lounge", "spa", "authentic_dining"],
                                "couple_suitability": "Tranquil luxury resort surrounded by tea gardens and hills.",
                                "address_or_area": "Khanapara, GS Road, Guwahati"
                            },
                            "activities": [
                                {
                                    "name": "Traditional Assamese Khaar & Thali at Paradise Restaurant",
                                    "region": "Guwahati",
                                    "category": "culinary",
                                    "is_adventure": False,
                                    "estimated_duration_hours": 1.5,
                                    "cost_inr": 1200.0,
                                    "description": "Authentic Parampara Thali: Khar (alkaline papaya), Masor Tenga (tangy river fish curry), Joha rice, and Payas.",
                                    "best_time_of_day": "Lunch (1:30 PM)"
                                },
                                {
                                    "name": "Sunset Brahmaputra River Cruise (Alfresco Grand)",
                                    "region": "Guwahati",
                                    "category": "scenic",
                                    "is_adventure": False,
                                    "estimated_duration_hours": 2.0,
                                    "cost_inr": 1500.0,
                                    "description": "Gentle cruise on the Brahmaputra river watching the golden 4:48 PM sunset with live Assamese folk flute.",
                                    "best_time_of_day": "3:30 PM - 5:30 PM"
                                }
                            ],
                            "transit": {
                                "origin": "New Delhi (DEL)",
                                "destination": "Guwahati (GAU)",
                                "mode": "flight",
                                "distance_km": 1460.0,
                                "estimated_duration_hours": 2.4,
                                "estimated_cost_inr": 5800.0,
                                "road_condition": "Air corridor direct flight.",
                                "requires_special_vehicle": False,
                                "advisory": "Morning departure DEL -> GAU (departs 06:10 AM, lands 08:35 AM)."
                            },
                            "daily_cost_inr": 14700.0,
                            "pace_notes": "Very relaxed pace. Mid-morning check-in, authentic feast, early sunset cruise on the river."
                        },
                        {
                            "day_number": 2,
                            "title": "Day 2: Tea Garden Tasting, Ropeway Panorama & Evening Flight Home",
                            "region": "Guwahati",
                            "stay": {
                                "name": "Vivanta Guwahati",
                                "region": "Guwahati",
                                "rating": 4.7,
                                "price_per_night_inr": 0.0,
                                "heating_verified": False,
                                "amenities": [],
                                "couple_suitability": "Day checkout",
                                "address_or_area": "Khanapara, GS Road, Guwahati"
                            },
                            "activities": [
                                {
                                    "name": "Guwahati Aerial Ropeway to Peacock Island",
                                    "region": "Guwahati",
                                    "category": "scenic",
                                    "is_adventure": False,
                                    "estimated_duration_hours": 1.5,
                                    "cost_inr": 300.0,
                                    "description": "Scenic cable car glide over the Brahmaputra offering panoramic aerial views.",
                                    "best_time_of_day": "Morning (11:00 AM)"
                                },
                                {
                                    "name": "Ethnic Smoked Duck & Bamboo Shoot Dining at Khorikaa",
                                    "region": "Guwahati",
                                    "category": "culinary",
                                    "is_adventure": False,
                                    "estimated_duration_hours": 1.5,
                                    "cost_inr": 1400.0,
                                    "description": "Specialty bamboo hollow smoked duck curry, roasted sesame pork, and fresh local herb chutneys.",
                                    "best_time_of_day": "Early Dinner (5:00 PM)"
                                }
                            ],
                            "transit": {
                                "origin": "Guwahati (GAU)",
                                "destination": "New Delhi (DEL)",
                                "mode": "flight",
                                "distance_km": 1460.0,
                                "estimated_duration_hours": 2.4,
                                "estimated_cost_inr": 5700.0,
                                "road_condition": "Air corridor direct flight.",
                                "requires_special_vehicle": False,
                                "advisory": "Evening flight GAU -> DEL (departs 19:40 PM, arrives 22:20 PM)."
                            },
                            "daily_cost_inr": 7400.0,
                            "pace_notes": "Leisurely day in Guwahati, ethnic dinner, airport transfer with 2-hour check-in buffer."
                        }
                    ],
                    "budget_summary": {
                        "items": [
                            {"category": "Direct Flights (Round trip DEL-GAU)", "amount_inr": 11500.0, "notes": "IndiGo / Air India direct flights."},
                            {"category": "Accommodations", "amount_inr": 6200.0, "notes": "1 Night Vivanta Guwahati 5-star resort."},
                            {"category": "Transit & Local Cabs", "amount_inr": 4500.0, "notes": "Airport cab transfers & city chauffeur."},
                            {"category": "Dining & Authentic Cuisine", "amount_inr": 3500.0, "notes": "Paradise Parampara Thali & Khorikaa ethnic feast."},
                            {"category": "Curated Experiences", "amount_inr": 1800.0, "notes": "Alfresco Grand sunset cruise & ropeway."},
                            {"category": "Taxes (GST 5%)", "amount_inr": 1375.0, "notes": "Standard hospitality tax."},
                            {"category": "Emergency Cushion", "amount_inr": 2750.0, "notes": "10% contingency cushion."}
                        ],
                        "subtotal_inr": 27500.0,
                        "tax_gst_inr": 1375.0,
                        "buffer_inr": 2750.0,
                        "total_estimated_inr": 31625.0,
                        "budget_cap_inr": 35000.0,
                        "remaining_headroom_inr": 3375.0,
                        "is_within_budget": True,
                        "audit_notes": "COMPLIANT: Total of ₹31,625 is comfortably within ₹35,000 cap with ₹3,375 buffer."
                    },
                    "constraints_verified": {
                        "budget_compliant": True,
                        "winter_heating_guaranteed": True,
                        "no_adventure_sports": True,
                        "relaxed_pace": True
                    },
                    "agent_reasoning_summary": (
                        "Formulated an optimized 2-day relaxed Assam itinerary from Delhi within ₹35,000: "
                        "1. Replaced 30+ hour train with direct flights (DEL-GAU roundtrip ~₹11,500). "
                        "2. Avoided long 9-hour road trips to Kaziranga, focusing on Guwahati riverfront. "
                        "3. Curated authentic culinary institutions (Paradise Restaurant & Khorikaa). "
                        "4. Factored in early eastern winter sunset at 4:48 PM for the Brahmaputra cruise. "
                        "5. Total cost ₹31,625 preserves ₹3,375 emergency headroom."
                    )
                }
                return LLMTurnResponse(
                    thought="All constraints, transit times, heated stays, and budget math have been deterministically verified. Synthesizing the final structured itinerary.",
                    content=json.dumps(final_json),
                    tool_calls=[],
                )
            final_json = {
                "trip_title": "Enchanting 5-Day Kashmir Winter Sojourn",
                "destination": "Kashmir (Srinagar & Gulmarg)",
                "month": "December",
                "duration_days": 5,
                "duration_nights": 4,
                "traveler_profile": "Couple seeking slow-paced scenic views & culinary depth (zero adventure sports)",
                "days": [
                    {
                        "day_number": 1,
                        "title": "Day 1: Arrival, Heated Boutique Check-in & Sunset Shikara",
                        "region": "Srinagar",
                        "stay": {
                            "name": "The Chinar Resort & Spa",
                            "region": "Srinagar",
                            "rating": 4.7,
                            "price_per_night_inr": 7500.0,
                            "heating_verified": True,
                            "amenities": ["central_heating", "electric_blanket", "hot_water_24x7"],
                            "couple_suitability": "Romantic boutique resort, warm insulated rooms.",
                            "address_or_area": "Harwan, Srinagar"
                        },
                        "activities": [
                            {
                                "name": "Sunset Shikara Ride on Dal & Nigeen Lake",
                                "region": "Srinagar",
                                "category": "scenic",
                                "is_adventure": False,
                                "estimated_duration_hours": 2.0,
                                "cost_inr": 1500.0,
                                "description": "Private covered shikara ride with hot Kangri coal heater under blankets, exploring floating gardens during golden hour.",
                                "best_time_of_day": "3:00 PM - 5:00 PM"
                            }
                        ],
                        "transit": {
                            "origin": "Srinagar Airport",
                            "destination": "Srinagar",
                            "mode": "road",
                            "distance_km": 18.0,
                            "estimated_duration_hours": 0.75,
                            "estimated_cost_inr": 1000.0,
                            "road_condition": "Paved city roads, clear.",
                            "requires_special_vehicle": False,
                            "advisory": "Pre-paid airport cab counter available outside terminal."
                        },
                        "daily_cost_inr": 10000.0,
                        "pace_notes": "Very relaxed pace. Rest after flight, sunset on Dal Lake before 5:15 PM winter dusk."
                    },
                    {
                        "day_number": 2,
                        "title": "Day 2: Heritage Wooden Architecture & Grand Wazwan Feast",
                        "region": "Srinagar",
                        "stay": {
                            "name": "The Chinar Resort & Spa",
                            "region": "Srinagar",
                            "rating": 4.7,
                            "price_per_night_inr": 7500.0,
                            "heating_verified": True,
                            "amenities": ["central_heating", "electric_blanket"],
                            "couple_suitability": "Romantic boutique resort.",
                            "address_or_area": "Harwan, Srinagar"
                        },
                        "activities": [
                            {
                                "name": "Chai Jaai Tea Room & Saffron Scented Kahwa",
                                "region": "Srinagar",
                                "category": "culinary",
                                "is_adventure": False,
                                "estimated_duration_hours": 1.0,
                                "cost_inr": 600.0,
                                "description": "Artisanal tea room on the Jhelum bund serving Kashmiri Kahwa with crushed almonds.",
                                "best_time_of_day": "11:00 AM"
                            },
                            {
                                "name": "Traditional Wazwan Feast at Ahdoos",
                                "region": "Srinagar",
                                "category": "culinary",
                                "is_adventure": False,
                                "estimated_duration_hours": 1.5,
                                "cost_inr": 1800.0,
                                "description": "Authentic multi-course Kashmiri Wazwan: Rogan Josh, Rista, Gushtaba, and saffron Phirni.",
                                "best_time_of_day": "Dinner"
                            }
                        ],
                        "transit": None,
                        "daily_cost_inr": 9900.0,
                        "pace_notes": "Leisurely city exploration with focused culinary highlights; no high-altitude strain."
                    },
                    {
                        "day_number": 3,
                        "title": "Day 3: Scenic Winter Drive to Snowbound Gulmarg (4x4 Chain Taxi)",
                        "region": "Gulmarg",
                        "stay": {
                            "name": "Hotel Highlands Park",
                            "region": "Gulmarg",
                            "rating": 4.6,
                            "price_per_night_inr": 7500.0,
                            "heating_verified": True,
                            "amenities": ["central_heating", "electric_blanket", "classic_heritage_fireplace"],
                            "couple_suitability": "Cozy vintage alpine cottage hotel.",
                            "address_or_area": "Circular Road, Gulmarg"
                        },
                        "activities": [
                            {
                                "name": "Winter Pine Forest Walk & St. Mary's Church",
                                "region": "Gulmarg",
                                "category": "scenic",
                                "is_adventure": False,
                                "estimated_duration_hours": 1.5,
                                "cost_inr": 0.0,
                                "description": "Peaceful couple stroll through snow-draped pine woods around the vintage Victorian stone church.",
                                "best_time_of_day": "2:30 PM"
                            }
                        ],
                        "transit": {
                            "origin": "Srinagar",
                            "destination": "Gulmarg",
                            "mode": "road",
                            "distance_km": 52.0,
                            "estimated_duration_hours": 2.2,
                            "estimated_cost_inr": 2800.0,
                            "road_condition": "Highway until Tangmarg, icy switchbacks to Gulmarg.",
                            "requires_special_vehicle": True,
                            "advisory": "Tangmarg-to-Gulmarg requires mandatory 4x4 snow chains."
                        },
                        "daily_cost_inr": 10300.0,
                        "pace_notes": "Morning highway drive, smooth transfer at Tangmarg to chain-taxi, arrival into winter wonderland."
                    },
                    {
                        "day_number": 4,
                        "title": "Day 4: Gondola Phase 1 Viewpoint & Alpine Glass Cafe",
                        "region": "Gulmarg",
                        "stay": {
                            "name": "Hotel Highlands Park",
                            "region": "Gulmarg",
                            "rating": 4.6,
                            "price_per_night_inr": 7500.0,
                            "heating_verified": True,
                            "amenities": ["central_heating", "electric_blanket"],
                            "couple_suitability": "Alpine cottage.",
                            "address_or_area": "Circular Road, Gulmarg"
                        },
                        "activities": [
                            {
                                "name": "Gulmarg Gondola Ride (Phase 1 to Kongdoori)",
                                "region": "Gulmarg",
                                "category": "scenic",
                                "is_adventure": False,
                                "estimated_duration_hours": 2.5,
                                "cost_inr": 1700.0,
                                "description": "Ascend via enclosed cable car to Kongdoori bowl for panoramic snow-capped views. High-altitude skiing strictly excluded per user preference.",
                                "best_time_of_day": "10:30 AM"
                            }
                        ],
                        "transit": None,
                        "daily_cost_inr": 9200.0,
                        "pace_notes": "Slow mountain morning. Phase 1 provides spectacular viewing without extreme altitude or sports."
                    },
                    {
                        "day_number": 5,
                        "title": "Day 5: Downhill Scenic Return & Airport Departure",
                        "region": "Srinagar",
                        "stay": {
                            "name": "The Chinar Resort & Spa",
                            "region": "Srinagar",
                            "rating": 4.7,
                            "price_per_night_inr": 0.0,
                            "heating_verified": True,
                            "amenities": [],
                            "couple_suitability": "Day-use checkout",
                            "address_or_area": "Harwan, Srinagar"
                        },
                        "activities": [],
                        "transit": {
                            "origin": "Gulmarg",
                            "destination": "Srinagar Airport",
                            "mode": "road",
                            "distance_km": 56.0,
                            "estimated_duration_hours": 2.5,
                            "estimated_cost_inr": 3000.0,
                            "road_condition": "Snowy descent from Gulmarg to Tangmarg, smooth thereafter.",
                            "requires_special_vehicle": True,
                            "advisory": "Keep a 4-hour departure buffer before flights due to possible snowfall traffic delays."
                        },
                        "daily_cost_inr": 3000.0,
                        "pace_notes": "Early checkout leaving ample 4-hour cushion for snow clearance and airport security."
                    }
                ],
                "budget_summary": {
                    "items": [
                        {"category": "Accommodations", "amount_inr": 30000.0, "notes": "4 nights heated stays @ ₹7,500/night."},
                        {"category": "Transit & Transfers", "amount_inr": 7000.0, "notes": "Airport cabs, Tangmarg 4x4 snow chains, intercity cabs."},
                        {"category": "Dining & Culinary", "amount_inr": 12000.0, "notes": "Authentic Ahdoos Wazwan feast, Kahwa teas, all meals."},
                        {"category": "Curated Experiences", "amount_inr": 5000.0, "notes": "Private sunset Shikara, Gondola Phase 1 tickets."},
                        {"category": "Taxes (GST 5%)", "amount_inr": 2700.0, "notes": "Composite tourism tax."},
                        {"category": "Emergency Cushion", "amount_inr": 5400.0, "notes": "10% contingency cushion for winter weather."}
                    ],
                    "subtotal_inr": 54000.0,
                    "tax_gst_inr": 2700.0,
                    "buffer_inr": 5400.0,
                    "total_estimated_inr": 62100.0,
                    "budget_cap_inr": 80000.0,
                    "remaining_headroom_inr": 17900.0,
                    "is_within_budget": True,
                    "audit_notes": "COMPLIANT: Total of ₹62,100 is comfortably within ₹80,000 cap with ₹17,900 headroom."
                },
                "constraints_verified": {
                    "budget_compliant": True,
                    "winter_heating_guaranteed": True,
                    "no_adventure_sports": True,
                    "relaxed_pace": True
                },
                "agent_reasoning_summary": (
                    "Constructed an unhurried 5-day winter plan adhering strictly to all user constraints: "
                    "1. Avoided closed Sonamarg pass and split duration between Srinagar (2N) and Gulmarg (2N). "
                    "2. Excluded all adventure sports (skiing, snowmobiles) in favor of sunset Shikara on Dal Lake, "
                    "panoramic Gondola Phase 1, and Ahdoos Wazwan feast. "
                    "3. Guaranteed central heating / electric blankets across all boutique stays. "
                    "4. Factor in 4x4 snow chain transit above Tangmarg. "
                    "5. Total cost ₹62,100 leaves a healthy ₹17,900 buffer under the ₹80,000 budget cap."
                ),
            }

            return LLMTurnResponse(
                thought="All constraints, transit times, heated stays, and budget math have been deterministically verified. Synthesizing the final structured itinerary.",
                content=json.dumps(final_json),
                tool_calls=[],
            )


def get_llm_provider(provider_name: Optional[str] = None) -> BaseLLMProvider:
    """Factory function resolving active LLM provider."""
    name = (provider_name or settings.TRIPMIND_LLM_PROVIDER).lower()
    if name == "gemini":
        if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.strip() == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is not configured in your .env file! "
                "Please add your Gemini API key to .env, or switch to 'Mock Replay' in the LLM dropdown."
            )
        return GeminiProvider()
    elif name == "groq":
        if not settings.GROQ_API_KEY or settings.GROQ_API_KEY.strip() == "your_groq_api_key_here":
            raise ValueError(
                "GROQ_API_KEY is not configured in your .env file! "
                "Please add your Groq API key to .env, or switch to 'Mock Replay' in the LLM dropdown."
            )
        return GroqProvider()
    elif name == "mock":
        return MockProvider()
    else:
        return MockProvider()


class LLMClient:
    """Convenience wrapper around BaseLLMProvider providing helper methods for Level 2."""

    def __init__(self, provider: Optional[Any] = None):
        if isinstance(provider, BaseLLMProvider):
            self.provider = provider
        elif isinstance(provider, str):
            self.provider = get_llm_provider(provider)
        else:
            self.provider = get_llm_provider()

    def call_fast(self, prompt: str, system_instruction: str = "", max_tokens: int = 800) -> str:
        """Executes a lightweight, single-turn completion."""
        messages: List[Dict[str, Any]] = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        response = self.provider.generate_turn(messages=messages, tools=[])
        return response.content or ""

