"""
Tool definition + registry that works out-of-the-box with DSPy.

• Decorate any function with @function_tool
• The original OpenAI-style JSON schema is kept (ToolRegistry._tools)
• A matching dspy.Tool wrapper is created automatically (ToolRegistry._dspy_tools)
"""

from __future__ import annotations
from typing import Dict, Any, Callable, Type, List, get_type_hints
import inspect
import json
from pydantic import BaseModel
import dspy

# -------------------------------------------------------------------- #
#  Internal representation of a tool                                   #
# -------------------------------------------------------------------- #

class Tool(BaseModel):
    type: str = "function"
    function: Dict[str, Any]      # OpenAI / LiteLLM JSON schema spec
    func: Callable                # actual Python callable

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


# -------------------------------------------------------------------- #
#  Registry                                                            #
# -------------------------------------------------------------------- #

class ToolRegistry:
    _tools: Dict[str, Tool] = {}          # our own JSON-schema tools
    _dspy_tools: List[dspy.Tool] = []     # thin wrappers for DSPy

    _TYPE_MAP: Dict[Type, str] = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    # ---------------- decorator ------------------------------------- #
    @classmethod
    def register(cls, func: Callable) -> Tool:
        """Decorator: turn *func* into a registry entry **and** a dspy.Tool."""
        sig = inspect.signature(func)
        hints = get_type_hints(func)

        # Build JSON Schema for OpenAI/LiteLLM function calling
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if name in {"self", "cls"}:
                continue

            param_type = hints.get(name, str)
            json_type = cls._TYPE_MAP.get(param_type, "string")

            properties[name] = {
                "type": json_type,
                "description": f"Parameter {name} of type {param_type.__name__}",
            }

            if param.default == inspect.Parameter.empty:
                required.append(name)

        schema = {
            "name": func.__name__,
            "description": func.__doc__ or f"Function {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

        # Our canonical tool object
        tool_obj = Tool(function=schema, func=func)

        # ------------ DSPy wrapper (single line does all the magic) ----
        dsp_tool = dspy.Tool(
            func,                                   # callable
            name=schema["name"],
            desc=schema["description"],
            args=schema["parameters"]["properties"],  # arg -> json schema
        )

        # Register
        cls._tools[schema["name"]] = tool_obj
        cls._dspy_tools.append(dsp_tool)
        return tool_obj

    # ---------------- helpers --------------------------------------- #
    @classmethod
    def get(cls, name: str) -> Tool | None:
        return cls._tools.get(name)

    @classmethod
    def list_schema(cls) -> Dict[str, Any]:
        """Return all tool JSON schemas (for OpenAI-style function calling)."""
        return {n: t.function for n, t in cls._tools.items()}

    @classmethod
    def get_dspy_tools(cls) -> List[dspy.Tool]:
        """Return tools ready to hand to DSPy ReAct."""
        return cls._dspy_tools
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, Dict[str, str]]: 
        return {
            name: {
                param: "your input here"  # Simplified to just show it needs input
                for param in tool.function['parameters']['properties']
            }
            for name, tool in cls._tools.items()
        }

    @classmethod
    def dispatch(cls, call: Dict[str, Any]) -> Any:
        try:
            tool_name = call["function"]["name"]
            args = json.loads(call["function"]["arguments"]) if isinstance(call["function"]["arguments"], str) else call["function"]["arguments"]
            return cls._tools.get(tool_name, lambda **_: {"role": "tool", "message": f"Tool {tool_name} not found"})(**args)
        except Exception as e:
            return {"role": "tool", "message": f"Error executing tool {tool_name}: {str(e)}"}


# Convenience alias so users can simply write `@function_tool`
function_tool = ToolRegistry.register