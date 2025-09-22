import json
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    message: str
    image: Optional[str]

class Conversation(BaseModel):
    messages: List[Message]

    def get_messages(self) -> List[Dict]:
        return [{
            "role": msg.role, 
            "content": msg.message,
            **({"image_url": msg.image} if msg.image else {})
        } for i, msg in enumerate(self.messages)]

    def save(self, filename: str):
        with open(filename, "w") as f: json.dump([msg.model_dump() for msg in self.messages], f)

    def load(self, filename: str):
        with open(filename, "r") as f: self.messages = [Message(**msg) for msg in json.load(f)]