from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")


def chat(model: str, messages: List[Dict[str, str]], *, json_mode: bool = False) -> str:
    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"  # forces valid JSON output from many Ollama models

    r = httpx.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120.0)
    r.raise_for_status()
    data = r.json()
    return data["message"]["content"]
