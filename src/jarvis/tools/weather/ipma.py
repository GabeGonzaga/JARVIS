from __future__ import annotations

import json
import os
import time
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

IPMA_BASE = "https://api.ipma.pt/open-data"
DEFAULT_TIMEOUT = 20.0
DEFAULT_CITY_ID = 1110600  # Lisbon

WEEKDAYS_EN = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = " ".join(s.split())
    return s


def _get_json(url: str, timeout: float = DEFAULT_TIMEOUT) -> Any:
    with httpx.Client(timeout=timeout) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()


def _cache_dir() -> str:
    base = os.path.expanduser(os.getenv("JARVIS_CACHE_DIR", "~/.jarvis"))
    os.makedirs(base, exist_ok=True)
    return base


def _load_cache(path: str, max_age_seconds: int) -> Optional[Any]:
    try:
        st = os.stat(path)
        if time.time() - st.st_mtime > max_age_seconds:
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(path: str, data: Any) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _city_list() -> List[Dict[str, Any]]:
    cache_path = os.path.join(_cache_dir(), "ipma_distrits_islands.json")
    cached = _load_cache(cache_path, max_age_seconds=7 * 24 * 3600)
    if isinstance(cached, list):
        return cached

    data = _get_json(f"{IPMA_BASE}/distrits-islands.json")
    if isinstance(data, list):
        _save_cache(cache_path, data)
        return data
    return []


def _weather_types() -> Dict[int, str]:
    cache_path = os.path.join(_cache_dir(), "ipma_weather_types.json")
    cached = _load_cache(cache_path, max_age_seconds=30 * 24 * 3600)
    if isinstance(cached, dict):
        out: Dict[int, str] = {}
        for k, v in cached.items():
            try:
                out[int(k)] = str(v)
            except Exception:
                continue
        if out:
            return out

    data = _get_json(f"{IPMA_BASE}/weather-type-classe.json")
    mapping: Dict[int, str] = {}
    if isinstance(data, dict):
        arr = data.get("data")
        if isinstance(arr, list):
            for item in arr:
                if not isinstance(item, dict):
                    continue
                _id = item.get("idWeatherType")
                if _id is None:
                    continue
                try:
                    wid = int(_id)
                except Exception:
                    continue
                pt = item.get("descWeatherTypePT") or item.get("descIdWeatherTypePT")
                en = item.get("descWeatherTypeEN") or item.get("descIdWeatherTypeEN")
                mapping[wid] = str(en or pt or wid)
    if mapping:
        _save_cache(cache_path, {str(k): v for k, v in mapping.items()})
    return mapping


def _extract_location_and_mode(query: str) -> Tuple[str, str]:
    qn = _norm(query)
    mode = "default"

    if any(w in qn for w in ["week", "weekly", "7 days", "7d", "next days", "semana", "7 dias", "proximos dias", "próximos dias", "todos"]):
        mode = "week"
    elif any(w in qn for w in ["tomorrow", "amanha", "amanhã"]):
        mode = "tomorrow"

    for prefix in ["weather", "tempo", "previsao", "previsão", "meteo", "meteorologia"]:
        if qn.startswith(prefix + " "):
            qn = qn[len(prefix) + 1 :]

    for w in ["week", "weekly", "tomorrow", "7 days", "7d", "next days", "semana", "amanha", "amanhã", "7 dias", "todos", "proximos dias", "próximos dias"]:
        qn = qn.replace(w, " ")
    qn = " ".join(qn.split())

    return qn.strip(), mode


def _find_city_id(location_text: str) -> Tuple[int, str]:
    if not location_text:
        return DEFAULT_CITY_ID, "Lisbon"

    locn = _norm(location_text)
    if locn in ["lisboa", "lisbon"]:
        return DEFAULT_CITY_ID, "Lisbon"

    cities = _city_list()
    best_score = 0
    best_id = DEFAULT_CITY_ID
    best_name = "Lisbon"

    for item in cities:
        if not isinstance(item, dict):
            continue
        name = str(item.get("local") or "").strip()
        gid = item.get("globalIdLocal")
        if not name or gid is None:
            continue
        try:
            gid_int = int(gid)
        except Exception:
            continue

        nn = _norm(name)
        score = 0
        if nn == locn:
            score = 1000 + len(nn)
        elif nn and locn and (nn in locn or locn in nn):
            score = 100 + min(len(nn), len(locn))

        if score > best_score:
            best_score = score
            best_id = gid_int
            best_name = name

    return best_id, best_name


def _weekday_en(date_str: str) -> str:
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return WEEKDAYS_EN[dt.weekday()]
    except Exception:
        return ""


def weather_ipma(args: Dict[str, Any]) -> Dict[str, Any]:
    query = str(args.get("query") or "").strip()
    location_text, mode = _extract_location_and_mode(query)

    city_id, city_name = _find_city_id(location_text)

    url = f"{IPMA_BASE}/forecast/meteorology/cities/daily/{city_id}.json"
    try:
        payload = _get_json(url)
    except Exception as e:
        return {"ok": False, "source": "IPMA", "error": str(e), "url": url}

    if not isinstance(payload, dict):
        return {"ok": False, "source": "IPMA", "error": "unexpected_response", "url": url}

    types = _weather_types()
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        return {"ok": False, "source": "IPMA", "error": "no_data", "url": url}

    days: List[Dict[str, Any]] = []
    for d in data:
        if not isinstance(d, dict):
            continue
        date_str = str(d.get("forecastDate") or "").strip()
        wid_raw = d.get("idWeatherType")
        try:
            wid = int(wid_raw) if wid_raw is not None else -1
        except Exception:
            wid = -1

        days.append(
            {
                "date": date_str,
                "weekday": _weekday_en(date_str),
                "tMin": d.get("tMin"),
                "tMax": d.get("tMax"),
                "precipitaProb": d.get("precipitaProb"),
                "windDir": d.get("predWindDir"),
                "weatherTypeId": wid,
                "weatherType": types.get(wid, str(wid_raw) if wid_raw is not None else ""),
            }
        )

    if mode == "tomorrow":
        days_out = days[1:2]
    elif mode == "week":
        days_out = days[:]
    else:
        days_out = days[:3]

    return {
        "ok": True,
        "source": "IPMA",
        "location": city_name,
        "globalIdLocal": city_id,
        "mode": mode,
        "days": days_out,
        "days_available": len(days),
        "fetched_from": url,
    }
