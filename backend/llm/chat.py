"""Single function for chat completion: OpenAI, Ollama, or Groq."""
from __future__ import annotations
import httpx
from openai import OpenAI
from config import get_settings


def chat_completion(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> str:
    """Return the assistant message content. Uses OpenAI, Ollama, or Groq from config."""
    settings = get_settings()
    provider = getattr(settings, "llm_provider", "openai")
    model = model or settings.llm_model

    if provider == "groq":
        return _groq_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)
    if provider == "ollama":
        return _ollama_chat(messages, model=model, temperature=temperature)
    return _openai_chat(messages, model=model, temperature=temperature, max_tokens=max_tokens)


def _openai_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> str:
    client = OpenAI(api_key=get_settings().openai_api_key)
    kwargs: dict = {"model": model, "messages": messages, "temperature": temperature}
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _groq_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float = 0,
    max_tokens: int | None = None,
) -> str:
    from groq import Groq
    s = get_settings()
    client = Groq(api_key=s.groq_api_key)
    kwargs: dict = {"model": model, "messages": messages, "temperature": temperature, "stream": False}
    if max_tokens is not None:
        kwargs["max_completion_tokens"] = max_tokens
    resp = client.chat.completions.create(**kwargs)
    return (resp.choices[0].message.content or "").strip()


def _ollama_chat(
    messages: list[dict[str, str]],
    model: str,
    temperature: float = 0,
) -> str:
    base = get_settings().ollama_base_url.rstrip("/")
    url = f"{base}/api/chat"
    payload = {"model": model, "messages": messages, "stream": False, "options": {"temperature": temperature}}
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
    data = resp.json()
    return (data.get("message") or {}).get("content") or ""