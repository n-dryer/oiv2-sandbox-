import platform, locale, os
from litellm import acompletion
from .conversation import Conversation, Message
from .tools.tools import ToolRegistry

def get_system_message():
    return f"""You are a helpful tool calling assistant.

Use XML tags to structure responses:
<think>Your reasoning about what to do next</think>
<tool_name>tool_name</tool_name>
<tool_args>{{"arg": "value"}}</tool_args>
<message>Your response to the user if needed</message>

Flow:
- Think about what you need to do
- Use tools when you need information
- Provide messages to help the user
- Continue the conversation naturally

You decide what to do based on the situation:
- Need info? Use tools
- Got results? Explain them
- Bad results? Try again differently  
- User unclear? Ask for clarification
- Ready to answer? Provide final response

OS: {platform.platform(terse=True)}
Locale: {locale.getlocale()[0]}
Current folder: {os.getcwd()}
Tools: {ToolRegistry.get_all_tools()}"""

class Interpreter:
    def __init__(self, model: str = "openai/local"):
        self.model = model
        self.conversation = Conversation(messages=[Message(role="system", message=get_system_message())])

    async def respond(self):
        response = await acompletion(
            model=self.model, 
            base_url="http://localhost:1234/v1", 
            api_key="dummy", 
            messages=self.conversation.get_messages(), 
            max_tokens=1000, 
            temperature=0.0,
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content: yield chunk.choices[0].delta.content