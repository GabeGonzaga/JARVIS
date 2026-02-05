# src/jarvis/tools/macos/shortcuts.py
# sourcery skip: reintroduce-else, assign-if-exp
from __future__ import annotations

import subprocess
from typing import Any, Dict, List


def list_shortcuts(_: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Returns list of Shortcuts names available on this Mac.
    """
    try:
        p = subprocess.run(
            ["shortcuts", "list"],
            check=False,
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            return {"ok": False, "returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

        names: List[str] = [line.strip() for line in p.stdout.splitlines() if line.strip()]
        return {"ok": True, "shortcuts": names}
    except FileNotFoundError as e:
        return {"ok": False, "error": f"'shortcuts' CLI not found: {e}"}


def run_shortcut(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a shortcut by name, optionally passing a text input.

    Uses Shortcuts Events via osascript because it reliably passes plain text.
    """
    name = str(args.get("name") or "").strip()
    if not name:
        return {"ok": False, "error": "Missing arg: name"}

    input_text = args.get("input")
    input_str = "" if input_text is None else str(input_text)

    # AppleScript: tell application "Shortcuts Events" to run shortcut "X" with input "Y"
    # Use shlex.quote to keep shell safe, but we still build a single AppleScript string.
    as_name = name.replace('"', '\\"')
    as_input = input_str.replace('"', '\\"')

    applescript = f'tell application "Shortcuts Events" to run shortcut "{as_name}" with input "{as_input}"'
    try:
        p = subprocess.run(
            ["osascript", "-e", applescript],
            check=False,
            capture_output=True,
            text=True,
        )
        # osascript often returns "missing value" when shortcut has no explicit output. Treat as ok.
        stdout = (p.stdout or "").strip()
        ok = p.returncode == 0

        if ok and stdout == "missing value":
            stdout = ""

        return {
            "ok": ok,
            "shortcut": name,
            "input": input_str,
            "returncode": p.returncode,
            "stdout": stdout,
            "stderr": (p.stderr or "").strip(),
            "method": "osascript/Shortcuts Events",
            "debug": {"applescript": applescript},
        }
    except FileNotFoundError as e:
        return {"ok": False, "error": f"'osascript' not found: {e}"}
