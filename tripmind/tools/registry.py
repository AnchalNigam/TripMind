"""Dynamic Tool Registry & JSON Schema Auto-Extractor.

AGENTIC AI CONCEPT — Tool Reflection & Safe Dispatch:
1. What is Tool Reflection?
   In Agentic AI, tools are not hardcoded prompt text. Instead, code inspects
   Python functions (their signatures, type hints, and docstrings) and automatically
   generates standard JSON Schema definitions (OpenAPI 3.0 / Gemini FunctionDeclaration).
2. The Runtime Sandbox:
   When an LLM outputs an action `{"name": "search_regions", "arguments": {...}}`,
   the ToolRegistry resolves the function, deserializes & validates the arguments
   via Pydantic, executes the deterministic Python code, and wraps errors into
   friendly Observation strings so the model can self-heal without crashing the server.
"""

import inspect
import json
from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, create_model


class Tool:
    """Encapsulates a registered Python tool with its metadata and JSON Schema."""

    def __init__(self, func: Callable, name: Optional[str] = None, description: Optional[str] = None):
        self.func = func
        self.name = name or func.__name__
        self.description = description or (func.__doc__ or "").strip().split("\n\n")[0]
        self.schema = self._generate_schema()

    def _generate_schema(self) -> Dict[str, Any]:
        """Auto-extract standard JSON Schema from Python type hints and docstrings."""
        # inspect module helps in knowing about code during runtime like whats type, what functioms, what arguments this 
        # function take etc like below line 34 asking for arguments that this func need
        sig = inspect.signature(self.func) 
        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls"]:
                continue
            default_val = ... if param.default == inspect.Parameter.empty else param.default
            param_type = param.annotation if param.annotation != inspect.Parameter.empty else Any
            fields[param_name] = (param_type, default_val)

        # Create a dynamic Pydantic model to generate standard OpenAPI JSON Schema
        dynamic_model = create_model(f"{self.name}_Args", **fields)
        json_schema = dynamic_model.model_json_schema()

        properties = json_schema.get("properties", {})
        required = json_schema.get("required", [])

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

    def execute(self, **kwargs) -> Any:
        """Execute the tool with validated arguments."""
        return self.func(**kwargs)


class ToolRegistry:
    """Central repository of callable tools available to the ReAct agent."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, func: Callable = None, *, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator or function to register a tool."""
        def decorator(f: Callable):
            tool = Tool(f, name=name, description=description)
            self._tools[tool.name] = tool
            return f

        if func is not None:
            return decorator(func)
        return decorator

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        return list(self._tools.values())

    def get_schemas(self) -> List[Dict[str, Any]]:
        """Return list of JSON schemas ready to be sent to LLMs (Gemini / Groq / OpenAI)."""
        return [tool.schema for tool in self._tools.values()]

    def execute(self, tool_name: str, arguments: Dict[str, Any] | str) -> str:
        """Safely execute a tool and return observation string.
        
        Catches exceptions and returns error messages so the agent can learn and self-correct.
        """
        tool = self.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found. Available tools are: {list(self._tools.keys())}"

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception as e:
                return f"Error: Failed to parse tool arguments JSON: {str(e)}"

        try:
            result = tool.execute(**arguments)
            if isinstance(result, BaseModel):
                return result.model_dump_json(indent=2)
            elif isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            else:
                return str(result)
        except Exception as e:
            # Self-healing observation: return detailed error back to LLM
            return f"Error executing tool '{tool_name}': {type(e).__name__}: {str(e)}. Please correct your arguments and retry."


# Global singleton registry
default_registry = ToolRegistry()
register_tool = default_registry.register
