from pydantic import BaseModel, Field
from typing import Optional, List
from .conversation import Message
import re, json

class ToolCall(BaseModel):
    tool: str = Field(..., description="The tool to use")
    tool_args: dict = Field(..., description="The arguments to pass to the tool")
    def to_message(self) -> Message: return Message(role="tool", message=f"{self.tool} {self.tool_args}")

class TaggedResponse:
    def __init__(self, raw: str):
        self.raw = raw
        self.reasoning = self._tag("think") or self._tag("thinking") or self._tag("reasoning")
        self.message = self._tag("message") or ""
        self.tool_call = self._tool()  # First tool call for backward compatibility
        self.tool_calls = self._all_tools()  # All tool calls
    
    def _tag(self, tag: str) -> Optional[str]:
        m = re.search(f"<{tag}>(.*?)</{tag}>", self.raw, re.DOTALL)
        return m.group(1).strip() if m else None
    
    def _tool(self) -> Optional[ToolCall]:
        name, args = self._tag("tool_name"), self._tag("tool_args")
        if not name: return None
        try: return ToolCall(tool=name, tool_args=json.loads(args) if args else {})
        except: return None
    
    def _all_tools(self) -> List[ToolCall]:
        """Find all tool calls in the response"""
        tools = []
        tool_names = re.findall(r"<tool_name>(.*?)</tool_name>", self.raw, re.DOTALL)
        tool_args = re.findall(r"<tool_args>(.*?)</tool_args>", self.raw, re.DOTALL)
        
        # Pair up tool names and args
        for i, name in enumerate(tool_names):
            name = name.strip()
            if i < len(tool_args):
                try:
                    args = json.loads(tool_args[i].strip()) if tool_args[i].strip() else {}
                except:
                    args = {}
            else:
                args = {}
            tools.append(ToolCall(tool=name, tool_args=args))
        
        return tools
    
    def to_message(self) -> Message: return Message(role="assistant", message=self.message)