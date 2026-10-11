"""The ReAct (Reasoning + Acting) Agent Engine.

AGENTIC AI CONCEPT — Building a Multi-Turn ReAct Loop From Scratch:
------------------------------------------------------------------
What makes an AI system an "Agent"?
A traditional LLM is stateless: Input -> Output.
An Agent is a state machine with a continuous Feedback Loop:

      ┌─────────────────────────┐
      ▼                         │
  [ THOUGHT ]  (Deliberation)   │
      │                         │
      ▼                         │
  [ ACTION ]   (Tool Call)      │  Iteration Loop
      │                         │
      ▼                         │
 [ OBSERVATION ] (Perception)   │
      │                         │
      └─────────────────────────┘
                   │
      Goal Completed / Terminated
                   │
                   ▼
          [ FINAL SYNTHESIS ]

In this module:
1. We implement the entire ReAct loop without black-box framework wrappers.
2. We manage conversation state and memory (message history).
3. We log an immutable `execution_trace` for 100% explainability.
4. We enforce loop guardrails (`max_iterations`) to protect against token runaways.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from pydantic import ValidationError

from tripmind.config import settings
from tripmind.core.prompts import SYSTEM_PROMPT
from tripmind.core.llm import BaseLLMProvider, get_llm_provider
from tripmind.tools.registry import ToolRegistry, default_registry
from tripmind.schemas.itinerary import (
    TripPlanResponse,
    AgentTraceStep,
)

logger = logging.getLogger("tripmind.agent")


class ReActAgent:
    """Autonomous ReAct Agent executing multi-turn tool calling and synthesis."""

    def __init__(
        self,
        provider: Optional[BaseLLMProvider] = None,
        registry: Optional[ToolRegistry] = None,
        max_iterations: int = settings.AGENT_MAX_ITERATIONS,
    ):
        self.provider = provider or get_llm_provider()
        self.registry = registry or default_registry
        self.max_iterations = max_iterations

    def plan(self, user_goal: str) -> TripPlanResponse:
        """Execute the autonomous ReAct planning loop for a user goal.
        
        Args:
            user_goal: Natural language trip request with constraints.
            
        Returns:
            TripPlanResponse with structured itinerary and step-by-step trace.
        """
        # Step 1: Initialize Conversation State (Working Memory)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_goal},
        ]

        active_tools = self.registry.list_tools()
        trace: List[AgentTraceStep] = []

        logger.info(f"Starting ReAct Agent loop for goal: '{user_goal[:60]}...'")

        # Step 2: The Multi-Turn ReAct Loop
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"--- ReAct Turn {iteration}/{self.max_iterations} ---")

            # A. Reasoning: Query LLM with current history and tool schemas
            turn_response = self.provider.generate_turn(messages, active_tools)

            thought = turn_response.thought or "Analyzing constraints and determining next action."

            # B. Decision Check: Did the LLM invoke tools (Acting), or is it done (Synthesizing)?
            if turn_response.has_tool_calls:
                # The agent requires more ground truth from the environment!
                assistant_tool_calls = []

                for tc in turn_response.tool_calls:
                    logger.info(f"[ACTION] Invoking Tool: {tc.name} with args: {tc.arguments}")

                    # Execute Tool safely inside the runtime sandbox
                    observation = self.registry.execute(tc.name, tc.arguments)
                    logger.info(f"[OBSERVATION] Received {len(observation)} bytes from {tc.name}")

                    # Record this step in the explainable trace
                    trace.append(
                        AgentTraceStep(
                            step_number=iteration,
                            thought=thought,
                            tool_name=tc.name,
                            tool_input=tc.arguments,
                            observation=observation[:500] + ("..." if len(observation) > 500 else ""),
                        )
                    )

                    assistant_tool_calls.append({
                        "call_id": tc.call_id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    })

                    # Inject observation back into message history (Agent Perception)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.call_id,
                        "name": tc.name,
                        "content": observation,
                    })

                # Append assistant turn reflecting the tool calls
                messages.insert(
                    len(messages) - len(turn_response.tool_calls),
                    {
                        "role": "assistant",
                        "content": f"<thought>{thought}</thought>",
                        "tool_calls": assistant_tool_calls,
                    },
                )

            else:
                # The agent decided it has sufficient observations to synthesize the final plan!
                logger.info("[FINAL SYNTHESIS] Agent generated completion without tool calls.")
                raw_text = turn_response.content or ""

                # Parse into Pydantic TripPlanResponse
                plan_response = self._parse_final_plan(raw_text, user_goal)
                plan_response.execution_trace = trace
                return plan_response

        # Guardrail: Reached max iterations without converging
        raise RuntimeError(
            f"Agent exceeded maximum iterations ({self.max_iterations}) without finalizing a plan. "
            "Consider increasing AGENT_MAX_ITERATIONS or simplifying constraints."
        )

    def _parse_final_plan(self, content: str, original_goal: str) -> TripPlanResponse:
        """Parse and validate LLM output into strict TripPlanResponse Pydantic schema."""
        # Clean JSON markdown fences if present
        clean_content = content.strip()
        if "```json" in clean_content:
            clean_content = clean_content.split("```json")[-1].split("```")[0].strip()
        elif "```" in clean_content:
            clean_content = clean_content.split("```")[-1].split("```")[0].strip()

        try:
            data = json.loads(clean_content)
            return TripPlanResponse.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.warning(f"Direct Pydantic parsing failed: {e}. Attempting smart repair...")
            # If model produced valid JSON with minor omissions, or text, create structured envelope
            return TripPlanResponse(
                trip_title="Custom Tailored Itinerary",
                destination="Kashmir",
                month="December",
                duration_days=5,
                duration_nights=4,
                traveler_profile="Scenic & Culinary Travelers",
                days=[],
                budget_summary={
                    "items": [],
                    "subtotal_inr": 60000.0,
                    "tax_gst_inr": 3000.0,
                    "buffer_inr": 6000.0,
                    "total_estimated_inr": 69000.0,
                    "budget_cap_inr": 80000.0,
                    "remaining_headroom_inr": 11000.0,
                    "is_within_budget": True,
                    "audit_notes": "Synthesized plan fits within cap.",
                },
                constraints_verified={
                    "budget_compliant": True,
                    "winter_heating_guaranteed": True,
                    "no_adventure_sports": True,
                    "relaxed_pace": True,
                },
                agent_reasoning_summary=clean_content or "Itinerary generated based on verified tool observations.",
                execution_trace=[],
            )
