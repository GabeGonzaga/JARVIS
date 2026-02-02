from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict


def new_trace() -> str:
    return str(uuid.uuid4())


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    candidates = (here, *here.parents)

    for p in candidates:
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p

    for p in candidates:
        if p.name == "src":
            return p.parent

    # last-resort fallback
    return here.parents[3] if len(here.parents) >= 4 else here.parent


def log_event(trace_id: str, event: str, **fields: Any) -> None:
    payload: Dict[str, Any] = {
        "ts": time.time(),
        "trace_id": trace_id,
        "event": event,
        **fields,
    }

    root = _repo_root()
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "jarvis.jsonl"

    log_file.write_text("", encoding="utf-8") if not log_file.exists() else None
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    if os.getenv("JARVIS_LOG_CONSOLE") == "1":
        print(json.dumps(payload, ensure_ascii=False))
