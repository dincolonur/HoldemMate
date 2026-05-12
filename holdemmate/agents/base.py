"""Shared Anthropic client + small helpers for individual agents."""

from __future__ import annotations

import json
from typing import Any

from anthropic import Anthropic

from ..config import get_settings


def get_client() -> Anthropic:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Anthropic(api_key=settings.anthropic_api_key)


def call_claude(
    system: str,
    user: str,
    *,
    max_tokens: int = 800,
    temperature: float = 0.4,
    cache_system: bool = True,
) -> str:
    """Send a single-turn message to Claude and return the text response.

    Args:
        system: System prompt. By default it's marked as cacheable, so when
            the same system prompt is reused across calls within ~5 minutes,
            the input tokens are billed at ~10% of the normal rate and the
            time-to-first-token is reduced.
        user: User message.
        max_tokens: Cap on output tokens.
        temperature: Sampling temperature.
        cache_system: If True (default), sends the system prompt as a
            cache-marked content block. Set False to disable per call.
    """
    settings = get_settings()
    client = get_client()

    # Prompt caching uses the "structured" form of the system parameter — a
    # list of content blocks rather than a plain string. The block carries
    # cache_control={"type": "ephemeral"}, which marks it cacheable for
    # ~5 minutes. Subsequent calls with the *exact* same system text get a
    # cache hit. Falling back to the plain-string form keeps things simple
    # when caching isn't desired (e.g., one-off prompts).
    if cache_system:
        system_param: Any = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]
    else:
        system_param = system

    msg = client.messages.create(
        model=settings.model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_param,
        messages=[{"role": "user", "content": user}],
    )
    parts: list[str] = []
    for block in msg.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def parse_json_block(text: str) -> dict[str, Any]:
    """Best-effort JSON extraction from a Claude response.

    Tolerates ```json fences and surrounding prose.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # strip leading fence (``` or ```json)
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1 :]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # If there's prose around the JSON, find the first '{' and last '}'.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise
