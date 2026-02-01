import httpx
from typing import Any, Dict, List

OLLAMA_URL = "http://localhost:11434/api/chat"

def chat(model: str, messages: List[Dict[str, str]]) -> str:
    payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": False}
    with httpx.Client(timeout=120) as client:
        r = client.post(OLLAMA_URL, json=payload)
        if r.status_code != 200:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(f"Ollama {r.status_code}: {detail}")
        data = r.json()
        return data["message"]["content"]
