"""Unified LLM interface: OpenAI or Ollama (open-source, local)."""
from .chat import chat_completion

__all__ = ["chat_completion"]
