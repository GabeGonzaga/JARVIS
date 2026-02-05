import json
from typing import Any, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def get_json(url: str, timeout: int = 8, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    h = {"User-Agent": "jarvis/0.1", "Accept": "application/json"}
    if headers:
        h.update(headers)

    req = Request(url, headers=h)
    try:
        with urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}", "url": url}
    except URLError as e:
        return {"ok": False, "error": f"Network error: {e.reason}", "url": url}
    except json.JSONDecodeError:
        return {"ok": False, "error": "Invalid JSON response", "url": url}
