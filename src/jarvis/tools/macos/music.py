from __future__ import annotations

from typing import Any, Dict, Optional
import subprocess


def _escape_as(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _run_osascript(script: str) -> Dict[str, Any]:
    p = subprocess.run(
        ["osascript", "-e", script],
        text=True,
        capture_output=True,
    )
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    ok = p.returncode == 0 and out != "NOT_FOUND"
    return {
        "ok": ok,
        "returncode": p.returncode,
        "stdout": out,
        "stderr": err,
    }


def music_control(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tool único para controlar Apple Music (macOS Music.app).

    args:
      action: open|play|pause|toggle|next|previous|forward|rewind|status|
              play_song|play_artist|play_album|play_playlist
      query: string (para play_*)
      seconds: int (para forward/rewind) default 15
      queue_all: bool (para play_album/play_artist) default False
    """
    action = str(args.get("action") or "").strip().lower()
    query = str(args.get("query") or "").strip()
    seconds = int(args.get("seconds") or 15)
    queue_all = bool(args.get("queue_all") or False)

    if action == "open":
        p = subprocess.run(["open", "-a", "Music"], text=True, capture_output=True)
        return {
            "ok": p.returncode == 0,
            "action": "open",
            "returncode": p.returncode,
            "stdout": (p.stdout or "").strip(),
            "stderr": (p.stderr or "").strip(),
        }

    if action in {"play", "pause", "toggle", "next", "previous"}:
        cmd_map = {
            "play": "play",
            "pause": "pause",
            "toggle": "playpause",
            "next": "next track",
            "previous": "previous track",
        }
        script = f'tell application "Music" to {cmd_map[action]}'
        r = _run_osascript(script)
        r["action"] = action
        return r

    if action in {"forward", "rewind"}:
        delta = abs(seconds)
        if action == "rewind":
            delta = -delta
        script = f'''
tell application "Music"
    if not (exists current track) then return "NOT_FOUND"
    set p to player position
    set player position to (p + ({delta}))
    return "OK"
end tell
'''.strip()
        r = _run_osascript(script)
        r["action"] = action
        r["seconds"] = seconds
        return r

    if action == "status":
        script = '''
tell application "Music"
    if not (exists current track) then return "NOT_FOUND"
    set tName to name of current track
    set tArtist to artist of current track
    set tAlbum to album of current track
    set tPos to player position
    return tName & " — " & tArtist & " | " & tAlbum & " | " & (tPos as text)
end tell
'''.strip()
        r = _run_osascript(script)
        r["action"] = "status"
        return r

    # --- Find & play from local Library
    if action in {"play_song", "play_artist", "play_album"}:
        if not query:
            return {"ok": False, "error": "missing_query", "action": action}

        q = _escape_as(query)

        if action == "play_song":
            where = f'name contains "{q}"'
        elif action == "play_artist":
            where = f'artist contains "{q}"'
        else:  # play_album
            where = f'album contains "{q}"'

        if action in {"play_artist", "play_album"} and queue_all:
            # queue multiple tracks (best-effort)
            script = f'''
tell application "Music"
    set lib to library playlist 1
    set ts to (every track of lib whose {where})
    if (count of ts) is 0 then return "NOT_FOUND"
    play item 1 of ts
    repeat with i from 2 to (count of ts)
        add item i of ts to playlist "Up Next"
    end repeat
    return "OK"
end tell
'''.strip()
        else:
            script = f'''
tell application "Music"
    set lib to library playlist 1
    set ts to (every track of lib whose {where})
    if (count of ts) is 0 then return "NOT_FOUND"
    play item 1 of ts
    return "OK"
end tell
'''.strip()

        r = _run_osascript(script)
        r["action"] = action
        r["query"] = query
        r["queue_all"] = queue_all
        return r

    if action == "play_playlist":
        if not query:
            return {"ok": False, "error": "missing_query", "action": action}
        q = _escape_as(query)
        script = f'''
tell application "Music"
    set ps to (every playlist whose name contains "{q}")
    if (count of ps) is 0 then return "NOT_FOUND"
    play item 1 of ps
    return "OK"
end tell
'''.strip()
        r = _run_osascript(script)
        r["action"] = action
        r["query"] = query
        return r

    return {"ok": False, "error": "unknown_action", "action": action}
