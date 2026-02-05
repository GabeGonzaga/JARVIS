import json
import subprocess
from typing import Any, Dict, Optional


def weather_apple(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs a macOS Shortcut that prints JSON to stdout.

    args:
      - shortcut: optional string (default: jarvis_weather_now)
    """
    shortcut = str(args.get("shortcut") or "jarvis_weather_now").strip()

    try:
        p = subprocess.run(
            ["shortcuts", "run", shortcut],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return {"ok": False, "error": "shortcuts CLI not found (macOS Shortcuts missing?)"}
    except subprocess.CalledProcessError as e:
        return {
            "ok": False,
            "error": f"Shortcut failed: {shortcut}",
            "stderr": (e.stderr or "").strip(),
        }

    out = (p.stdout or "").strip()
    if not out:
        return {"ok": False, "error": f"Shortcut produced no output: {shortcut}"}

    # Try JSON; if not JSON, return as text
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data.setdefault("ok", True)
            return data
        return {"ok": True, "provider": "apple_shortcuts", "data": data}
    except Exception:
        return {"ok": True, "provider": "apple_shortcuts", "text": out}
