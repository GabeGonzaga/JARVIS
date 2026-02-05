#!/usr/bin/env python3
"""
Ollama client wrapper used by JARVIS.

Goals:
- Work with multiple Ollama base URL styles:
  - http://127.0.0.1:11434
  - http://127.0.0.1:11434/api
- Prefer /api/chat (messages) and fall back cleanly to /api/generate (prompt).
- Optional final fallback to OpenAI-compatible /v1/chat/completions if enabled.
- Keep return type as a plain string (what the rest of the code expects).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


DEFAULT_TIMEOUT = 60.0


def _normalize_host(host: str) -> str:
    h = (host or "").strip()
    if not h:
        return "http://127.0.0.1:11434"
    if "://" not in h:
        h = f"http://{h}"
    return h.rstrip("/")


def _api_base(host: str) -> str:
    h = _normalize_host(host)
    return h if h.endswith("/api") else f"{h}/api"


def _v1_base(host: str) -> str:
    h = _normalize_host(host)
    return h if h.endswith("/v1") else f"{h}/v1"


def _post_json(url: str, payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    with httpx.Client(timeout=timeout) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if isinstance(data, dict):
            return data
        return {"data": data}


def _messages_to_prompt(messages: List[Dict[str, Any]]) -> str:
    # Minimal prompt fallback for /api/generate
    parts: List[str] = []
    for m in messages:
        role = str(m.get("role", "")).strip() or "user"
        content = str(m.get("content", "")).strip()
        if not content:
            continue
        parts.append(f"{role}: {content}")
    return "\n".join(parts).strip() or "user: ping"


def chat(model: str, messages: List[Dict[str, Any]], *, base_url: str | None = None) -> str:
    """
    Send a chat-style request to Ollama and return assistant text.

    Raises httpx.RequestError / httpx.HTTPStatusError for non-404 failures.
    For 404s, tries alternate endpoints.
    """
    host = base_url or os.getenv("OLLAMA_BASE_URL") or os.getenv("OLLAMA_HOST") or "http://127.0.0.1:11434"
    api = _api_base(host)

    payload_chat: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }

    # 1) Preferred: /api/chat
    try:
        data = _post_json(f"{api}/chat", payload_chat)
        msg = data.get("message") or {}
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        resp = data.get("response")
        return resp.strip() if isinstance(resp, str) else str(data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            raise
    except httpx.RequestError:
        raise

    # 2) Fallback: /api/generate
    prompt = _messages_to_prompt(messages)
    payload_gen: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        data = _post_json(f"{api}/generate", payload_gen)
        resp = data.get("response")
        return resp.strip() if isinstance(resp, str) else str(data)

    except httpx.HTTPStatusError as e:
        if e.response.status_code != 404:
            raise
    except httpx.RequestError:
        raise

    # 3) Optional fallback: /v1/chat/completions (only if your Ollama build exposes it)
    v1 = _v1_base(host)
    payload_v1: Dict[str, Any] = {"model": model, "messages": messages}

    data = _post_json(f"{v1}/chat/completions", payload_v1)
    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        message = (choices[0] or {}).get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content.strip()
    return str(data)
