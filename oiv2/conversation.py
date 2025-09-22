# Compatibility import for tools that expect conversation.py
from .conversations import Message, Conversation

__all__ = ['Message', 'Conversation']