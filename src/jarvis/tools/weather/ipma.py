import unicodedata
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from jarvis.tools.net.http import get_json


_IPMA_BASE = "https://api.ipma.pt/open-data"
_IPMA_LOCALITIES = f"{_IPMA_BASE}/distrits-islands.json"
_IPMA_DAILY_FMT = f"{_IPMA_BASE}/forecast/meteorology/cities/daily/{{gid}}.json"


def _norm(s: str) -> str:
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch))


@lru_cache(maxsize=1)
def _load_localities() -> List[Dict[str, Any]]:
    data = get_json(_IPMA_LOCALITIES, timeout=8)
    items = data.get("data", [])
    return items if isinstance(items, list) else []


def resolve_global_id(location: str) -> Optional[Tuple[int, str]]:
    """
    Accepts:
      - numeric string: "1110600"
      - locality name: "Lisboa" (case/accents tolerant)
    Returns: (globalIdLocal, canonical_local_name) or None
    """
    loc = location.strip()
    if not loc:
        return None

    if loc.isdigit():
        gid = int(loc)
        for it in _load_localities():
            if int(it.get("globalIdLocal", -1)) == gid:
                return gid, str(it.get("local", loc))
        return gid, loc

    target = _norm(loc)
    best: Optional[Tuple[int, str]] = None

    for it in _load_localities():
        name = str(it.get("local", "")).strip()
        if not name:
            continue
        if _norm(name) == target:
            return int(it["globalIdLocal"]), name

        # fallback: startswith match (e.g. "Ponta" -> "Ponta Delgada")
        if _norm(name).startswith(target) and best is None:
            best = int(it["globalIdLocal"]), name

    return best


def _pick_today(forecast: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    data = forecast.get("data")
    if not isinstance(data, list) or not data:
        return None
    return data[0] if isinstance(data[0], dict) else None


def weather_ipma(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    args:
      - location: string (name or globalIdLocal)
    """
    location = str(args.get("location", "")).strip()
    if not location:
        return {"ok": False, "error": "Missing arg: location"}

    resolved = resolve_global_id(location)
    if not resolved:
        return {"ok": False, "error": f"Unknown location: {location}"}

    gid, canonical = resolved
    url = _IPMA_DAILY_FMT.format(gid=gid)

    forecast = get_json(url, timeout=8)
    today = _pick_today(forecast)
    if not today:
        return {
            "ok": False,
            "provider": "ipma",
            "location": canonical,
            "globalIdLocal": gid,
            "error": "No forecast data",
        }

    # Keep it simple + stable: raw numbers are reliable
    return {
        "ok": True,
        "provider": "ipma",
        "location": canonical,
        "globalIdLocal": gid,
        "date": str(today.get("forecastDate", "")),
        "t_min": today.get("tMin"),
        "t_max": today.get("tMax"),
        "precip_prob": today.get("precipitaProb"),
        "wind_dir": today.get("predWindDir"),
        "wind_speed_class": today.get("classWindSpeed"),
        "raw": today,
    }
