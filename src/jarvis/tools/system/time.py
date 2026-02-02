from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

_PT_WEEKDAYS = {
    0: "segunda-feira",
    1: "terça-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sábado",
    6: "domingo",
}


def now(args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    args = args or {}
    what = str(args.get("what", "datetime")).strip().lower()

    dt = datetime.now().astimezone()
    tzname = dt.tzname() or ""

    date_str = dt.strftime("%d-%m-%Y")
    time_str = dt.strftime("%H:%M")  # HH:MM only
    weekday = _PT_WEEKDAYS.get(dt.weekday(), dt.strftime("%A"))

    # canonical “datetime” string used by /now or “date and time”
    datetime_str = f"{date_str} {time_str}"

    return {
        "ok": True,
        "what": what,
        "date": date_str,
        "time": time_str,
        "weekday": weekday,
        "day": f"{weekday}, {date_str}",
        "datetime": datetime_str,
        "tzname": tzname,
    }
