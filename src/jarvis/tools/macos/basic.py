from __future__ import annotations

import subprocess
from typing import Any, Dict, Tuple


def _run(cmd: list[str]) -> Tuple[int, str, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()


def open_app(args: Dict[str, Any]) -> Dict[str, Any]:
    app = str(args.get("app", "")).strip()
    if not app:
        return {"ok": False, "error": "Missing 'app'."}

    rc, out, err = _run(["open", "-a", app])
    return {"ok": rc == 0, "app": app, "returncode": rc, "stdout": out, "stderr": err}


def open_url(args: Dict[str, Any]) -> Dict[str, Any]:
    url = str(args.get("url", "")).strip()
    if not url:
        return {"ok": False, "error": "Missing 'url'."}

    rc, out, err = _run(["open", url])
    return {"ok": rc == 0, "url": url, "returncode": rc, "stdout": out, "stderr": err}


def _as_as_string(s: str) -> str:
    # AppleScript string literal escaping
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def create_note(args: Dict[str, Any]) -> Dict[str, Any]:
    title = str(args.get("title", "")).strip() or "JARVIS"
    body = str(args.get("body", "")).strip() or ""

    # Hard default: iCloud → folder "JARVIS"
    # (if iCloud doesn't exist, fall back to account 1)
    acct_name = str(args.get("account", "")).strip() or "iCloud"
    folder_name = str(args.get("folder", "")).strip() or "JARVIS"

    a_title = _as_as_string(title)
    a_body = _as_as_string(body)
    a_acct = _as_as_string(acct_name)
    a_folder = _as_as_string(folder_name)

    script = f'''
tell application "Notes"
    set acctName to {a_acct}
    set folderName to {a_folder}
    set noteTitle to {a_title}
    set bodyText to {a_body}

    set targetAccount to missing value
    repeat with a in accounts
        if (name of a as text) is acctName then
            set targetAccount to a
            exit repeat
        end if
    end repeat
    if targetAccount is missing value then
        set targetAccount to account 1
    end if

    set targetFolder to missing value
    repeat with f in folders of targetAccount
        if (name of f as text) is folderName then
            set targetFolder to f
            exit repeat
        end if
    end repeat
    if targetFolder is missing value then
        set targetFolder to make new folder at targetAccount with properties {{name:folderName}}
    end if

    set richBody to "<div>" & bodyText & "</div>"
    set createdNote to make new note at targetFolder with properties {{name:noteTitle, body:richBody}}
    return "ok"
end tell
'''

    rc, out, err = _run(["osascript", "-e", script])
    ok = (rc == 0) and (out.strip().lower() == "ok")

    return {
        "ok": ok,
        "title": title,
        "account": acct_name,
        "folder": folder_name,
        "returncode": rc,
        "stdout": out,
        "stderr": err,
    }
