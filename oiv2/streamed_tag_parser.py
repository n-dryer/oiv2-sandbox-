import re
from typing import List, Optional
import json

class StreamTaggedResponse:
    """Incremental parser for assistant XML-style tags with chunk-level routing."""
    
    REASONING_TAGS = {"think", "thinking", "reasoning"}
    TOOL_NAME_TAG = "tool_name"
    TOOL_ARGS_TAG = "tool_args"
    PRINTABLE_TAGS = {"message"}

    def __init__(self):
        self.in_potential_tag = False
        self.buffer = ""
        self.current_tag: Optional[str] = None
        self.message_out: str = ""
        self.reasoning_out: str = ""
        self.tool_names: List[str] = []
        self.tool_args: List[str] = []
        self._current_tool_args: str = ""  # Accumulate tool_args text

    @property
    def message(self) -> str:
        return self.message_out

    @property
    def reasoning(self) -> str:
        return self.reasoning_out

    @property
    def tool_calls(self) -> List[dict]:
        return [{"name": name, "args": args} for name, args in zip(self.tool_names, self.tool_args)]

    def _process_tag(self, tag_str: str) -> None:
        """Toggle context based on full tag string."""
        #print(f"Processing tag: {tag_str!r}", flush=True)
        is_close = tag_str.startswith("</")
        tag_name = re.sub(r"[</> ]", "", tag_str)
        if is_close and tag_name == self.TOOL_ARGS_TAG and self._current_tool_args:
            # Finalize tool_args when closing tag is processed
            self.tool_args.append(self._current_tool_args)
            self._current_tool_args = ""
        self.current_tag = None if is_close else tag_name

    def feed(self, chunk: str) -> str:
        """Feed an atomic chunk and return it immediately if printable."""
        #print(f"Received chunk: {chunk!r}", flush=True)

        # Append chunk to buffer
        self.buffer += chunk

        # Process all complete tags in the buffer
        while True:
            match = re.search(r"<[^>]+>", self.buffer)
            if not match:
                if self.buffer.startswith("<"):
                    #print(f"Buffering incomplete tag: {self.buffer!r}", flush=True)
                    self.in_potential_tag = True
                break
            tag_str = match.group(0)
            tag_start, tag_end = match.span()
            # Extract and route text before the tag
            text_before = self.buffer[:tag_start]
            if text_before:
                printable = self._route_text(text_before)
                #if printable:
                    #print(f"Printable text: {printable!r}", flush=True)
            # Validate tag
            if not re.match(r"</?[^>]+>", tag_str):
                #print(f"Invalid tag: {tag_str!r}", flush=True)
                self.buffer = self.buffer[tag_end:]
                continue
            # Process the tag
            self._process_tag(tag_str)
            # Remove processed portion from buffer
            self.buffer = self.buffer[tag_end:]

        # If no tags remain and buffer is not empty, process as text
        if self.buffer and not self.buffer.startswith("<"):
            text = self.buffer
            self.buffer = ""
            self.in_potential_tag = False
            if text:
                printable = self._route_text(text)
                #if printable:
                    #print(f"Printable text: {printable!r}", flush=True)
                return printable
        
        self.in_potential_tag = self.buffer.startswith("<")
        return ""

    def _route_text(self, text: str) -> str:
        """Route text based on current_tag and return printable text."""
        #print(f"Routing text: {text!r}, current_tag: {self.current_tag!r}", flush=True)
        if self.current_tag in self.REASONING_TAGS:
            self.reasoning_out += text
            return ""
        if self.current_tag == self.TOOL_NAME_TAG:
            self.tool_names.append(text.strip())
            return ""
        if self.current_tag == self.TOOL_ARGS_TAG:
            self._current_tool_args += text
            return ""
        if self.current_tag is None or self.current_tag in self.PRINTABLE_TAGS:
            self.message_out += text
            return text
        return ""