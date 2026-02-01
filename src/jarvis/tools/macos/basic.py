import subprocess
from typing import Any, Dict

def _osascript(script: str) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "osascript failed")
    return r.stdout.strip()

def open_app(args: Dict[str, Any]) -> Dict[str, Any]:
    app = str(args.get("app", "")).strip()
    if not app:
        return {"ok": False, "error": "missing app"}
    _osascript(f'tell application "{app}" to activate')
    return {"ok": True, "app": app}

def open_url(args: Dict[str, Any]) -> Dict[str, Any]:
    url = str(args.get("url", "")).strip()
    if not url:
        return {"ok": False, "error": "missing url"}
    subprocess.run(["open", url], check=True)
    return {"ok": True, "url": url}

def create_note(args: Dict[str, Any]) -> Dict[str, Any]:
    title = str(args.get("title", "JARVIS")).replace('"', '\\"')
    body = str(args.get("body", "")).replace('"', '\\"')
    script = f'''
    tell application "Notes"
        tell account 1
            tell folder 1
                make new note with properties {{name:"{title}", body:"{body}"}}
            end tell
        end tell
    end tell
    '''
    _osascript(script)
    return {"ok": True, "title": title}
