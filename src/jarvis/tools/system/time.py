from __future__ import annotations

import subprocess
from typing import Any, Dict


def _run_date(fmt: str) -> str:
    # No shell, fixed format strings only -> no injection risk
    out = subprocess.check_output(["/bin/date", fmt], text=True)
    return out.strip()


def _fmt_offset(z: str) -> str:
    # macOS: +0000 / -0130  ->  +00:00 / -01:30
    z = z.strip()
    if len(z) == 5 and (z[0] in "+-") and z[1:].isdigit():
        return f"{z[0]}{z[1:3]}:{z[3:5]}"
    return z


def now(args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Returns macOS wall-clock time (exactly what your Mac reports).
    args:
      - what: "datetime" | "date" | "time" (optional; kept for compatibility)
    """
    args = args or {}
    what = str(args.get("what", "datetime")).strip().lower()

    date_str = _run_date("+%d-%m-%Y")
    time_str = _run_date("+%H:%M:%S")
    tzname = _run_date("+%Z")
    offset = _fmt_offset(_run_date("+%z"))

    return {
        "ok": True,
        "what": what,
        "date": date_str,                 # DD-MM-YYYY
        "time": time_str,                 # HH:MM:SS (wall-clock)
        "datetime": f"{date_str} {time_str}",
        "tzname": tzname,
        "utc_offset": offset,             # +HH:MM
    }
