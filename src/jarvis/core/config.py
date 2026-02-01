import json
from pathlib import Path
from typing import Any, Dict

def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def load_settings() -> Dict[str, Any]:
    base = Path("config/settings.example.json")
    user = Path("config/settings.json")

    data = _read_json(base) if base.exists() else {}
    if user.exists():
        u = _read_json(user)
        data = deep_merge(data, u)
    return data

def deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out
