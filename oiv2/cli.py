import asyncio, json, argparse
from .cli_utils import Text, Spinner
from .interpreter import Interpreter
from .conversation import Message
from .structured import TaggedResponse, ToolCall
from .tools.tools import ToolRegistry
from .streamed_tag_parser import StreamTaggedResponse

# Save builtin input before tools import (tools may monkey‑patch input)
builtin_input = input

def confirm_tool(tool_name: str, tool_args: dict) -> bool:
    """Ask the user whether to execute a tool. Returns *True* if confirmed."""
    print(f"Execute {tool_name}({tool_args})? (y/n): ", end="")
    return builtin_input().lower().startswith("y")

def execute_tool_with_confirmation(tool_call, unsafe: bool = False):
    """Run *tool_call* after optional confirmation. Returns tool result or *None*."""
    if not unsafe and not confirm_tool(tool_call.tool, tool_call.tool_args):
        return None

    return ToolRegistry.dispatch({
        "function": {
            "name": tool_call.tool,
            "arguments": json.dumps(tool_call.tool_args)
        }
    })

async def async_main(raw_mode: bool = False, unsafe: bool = False):
    # Import all tools so they register with *ToolRegistry*.
    # from .tools import screen, jupyter, files, input, list_tools, python_runner, terminal
    
    interpreter = Interpreter()
    parser = StreamTaggedResponse()

    try:
        while True:
            # Get user input unless the last message came from a tool.
            if interpreter.conversation.messages[-1].role != "tool":
                try: user_input = builtin_input(Text(text="You: ", color="blue"))
                except KeyboardInterrupt: print("\n\nGoodbye!")
                interpreter.conversation.messages.append(Message(role="user", message=user_input))

            # Output from LLM
            thinker = Spinner(msg="Thinking ", color="green"); thinker.start()
            
            async for chunk in interpreter.respond():
                printable = parser.feed(chunk)
                if raw_mode or printable:
                    if thinker.running: thinker.stop(); print(Text("Assistant: ", color="green"), end="")
                    print(printable if not raw_mode else chunk, end="", flush=True)

            print("\n")
            interpreter.conversation.messages.append(Message(role="assistant", message=parser.message))

            # Handle tool calls
            for name, args in parser.tool_calls:
                tool_call = ToolCall(tool=name, tool_args=args)
                tool_result = execute_tool_with_confirmation(tool_call)
                print(Text("Tool: ", color="yellow"), tool_result)
                interpreter.conversation.messages.append(tool_result)

    except KeyboardInterrupt:
        print("\n\nGoodbye!")


def main() -> None:
    parser = argparse.ArgumentParser(description="OIV2 AI Assistant CLI")
    parser.add_argument("--raw", action="store_true", help="Stream assistant tokens directly (disable spinner)")
    parser.add_argument("--unsafe", action="store_true", help="Skip confirmation prompts when executing tools")
    args = parser.parse_args()

    import colorama
    colorama.init()

    asyncio.run(async_main(raw_mode=args.raw, unsafe=args.unsafe))


if __name__ == "__main__":
    main()
