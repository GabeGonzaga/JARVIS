from __future__ import annotations

import json
import plistlib
import re
import subprocess
import time
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Paths / cache
JARVIS_DIR = Path.home() / ".jarvis"
JARVIS_DIR.mkdir(parents=True, exist_ok=True)

CACHE_FILE = JARVIS_DIR / "music_library_cache.json"
STATE_FILE = JARVIS_DIR / "music_state.json"

DEFAULT_XML_CANDIDATES = [
    Path.home() / "Music" / "Music" / "Media.localized" / "Music Library.xml",
    Path.home() / "Music" / "Music Library.xml",
    Path.home() / "Music" / "iTunes" / "iTunes Music Library.xml",
    Path.home() / "Downloads" / "Music Library.xml",
    Path.home() / "Downloads" / "Library.xml",
]

# In-memory choices for numeric selection (one per session)
_CHOICES: Dict[str, Dict[str, Any]] = {}


@dataclass(frozen=True)
class Track:
    pid: str
    name: str
    artist: str
    album: str
    album_artist: str


@dataclass(frozen=True)
class Playlist:
    pid: str
    name: str
    track_pids: List[str]


@dataclass(frozen=True)
class Album:
    name: str
    album_artist: str
    track_pids: List[str]


def _as_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _strip_diacritics(s: str) -> str:
    norm = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in norm if not unicodedata.combining(ch))


def _norm(s: str) -> str:
    s2 = _strip_diacritics(str(s or "")).lower()
    s2 = re.sub(r"[^0-9a-z\s]+", " ", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2


def _tokens(s: str) -> List[str]:
    s2 = _norm(s)
    return [t for t in s2.split(" ") if t]


def _run_osascript(script: str) -> str:
    p = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=False,
    )
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    if p.returncode != 0:
        raise RuntimeError(err or out or f"osascript failed ({p.returncode})")
    return out


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: Dict[str, Any]) -> None:
    try:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _music_player_state() -> str:
    script = 'tell application "Music" to get player state as text'
    try:
        return _run_osascript(script).strip().lower()
    except Exception:
        return ""


def _music_current_track_pid() -> str:
    script = """
tell application "Music"
    if player state is stopped then return ""
    try
        return persistent ID of current track
    on error
        return ""
    end try
end tell
"""
    try:
        return _run_osascript(script).strip()
    except Exception:
        return ""


def _set_shuffle(enabled: bool) -> None:
    val = "true" if enabled else "false"
    script = f'tell application "Music" to set shuffle enabled to {val}'
    subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)


def _control_stop() -> None:
    pid = _music_current_track_pid()
    st = _load_json(STATE_FILE)
    if pid:
        st["last_track_pid"] = pid
        _save_json(STATE_FILE, st)
    _run_osascript('tell application "Music" to stop')


def _control_play() -> None:
    state = _music_player_state()
    if state == "stopped":
        st = _load_json(STATE_FILE)
        last_pid = str(st.get("last_track_pid") or "").strip()
        if last_pid:
            _play_track_pid(last_pid)
            return
    _run_osascript('tell application "Music" to play')


def _control_pause() -> None:
    _run_osascript('tell application "Music" to pause')


def _control_next() -> None:
    _run_osascript('tell application "Music" to next track')


def _control_previous() -> None:
    _run_osascript('tell application "Music" to previous track')


def _control_seek(delta_seconds: int) -> None:
    # Robust seek: only when not stopped, clamp at 0
    d = int(delta_seconds)
    script = f"""
tell application "Music"
    if player state is not stopped then
        set pos to player position
        set newPos to pos + ({d})
        if newPos < 0 then set newPos to 0
        set player position to newPos
    end if
end tell
"""
    _run_osascript(script)


def _detect_control(query: str) -> Optional[str]:
    q = _norm(query)

    if q in ("play", "resume", "continue", "retomar", "continua"):
        return "play"
    if q in ("pause", "pausa", "pausar"):
        return "pause"
    if q in ("stop", "parar"):
        return "stop"
    if q in ("next", "skip", "seguinte", "proxima", "próxima"):
        return "next"
    if q in ("previous", "prev", "anterior"):
        return "previous"

    # 15s seek (accept many forms)
    if ">>15" in query or "+15" in query or "forward 15" in q or "avancar 15" in q or "avançar 15" in q:
        return "forward15"
    if "<<15" in query or "-15" in query or "back 15" in q or "rewind 15" in q or "voltar 15" in q or "retroceder 15" in q:
        return "back15"

    return None


def _strip_leading_verbs(raw: str) -> str:
    q = raw.strip()
    qn = _norm(q)

    if qn.startswith("jarvis "):
        q = q.split(" ", 1)[1].strip()
        qn = _norm(q)

    prefixes = [
        "play me ",
        "play my ",
        "play the ",
        "play a ",
        "play ",
        "toca ",
        "poe ",
        "põe ",
    ]
    for p in prefixes:
        if qn.startswith(_norm(p)):
            q = q[len(p):].strip()
            break
    return q.strip()


def _parse_music_request(query: str) -> Tuple[str, str, bool]:
    raw = _strip_leading_verbs(query)
    qn = _norm(raw)

    shuffle = bool(re.search(r"\b(shuffle|random|aleatorio|aleatório)\b", qn))

    # Explicit category keywords
    if qn.startswith("playlist "):
        return ("playlist", _norm(raw[len("playlist "):]), shuffle)
    if qn.startswith("album "):
        return ("album", _norm(raw[len("album "):]), shuffle)
    if qn.startswith("artist "):
        return ("artist", _norm(raw[len("artist "):]), shuffle)
    if qn.startswith("song "):
        return ("song", _norm(raw[len("song "):]), shuffle)

    # Keyword anywhere
    if "playlist" in qn or "lista" in qn:
        txt = re.sub(r"\b(playlist|playlists|lista|lista de reprodução|lista de reproduçao)\b", " ", qn).strip()
        return ("playlist", txt, shuffle)
    if "album" in qn or "álbum" in qn or "disco" in qn:
        txt = re.sub(r"\b(album|álbum|disco)\b", " ", qn).strip()
        return ("album", txt, shuffle)
    if "artist" in qn or "artista" in qn or "songs by" in qn or "musicas de" in qn or "músicas de" in qn:
        txt = re.sub(r"\b(artist|artista|songs by|musicas de|músicas de)\b", " ", qn).strip()
        return ("artist", txt, shuffle)

    return ("auto", qn.strip(), shuffle)


def _get_xml_path() -> Path:
    env = str((__import__("os").environ.get("JARVIS_MUSIC_LIBRARY_XML") or "")).strip()
    if env:
        p = Path(env).expanduser()
        if p.exists():
            return p

    for p in DEFAULT_XML_CANDIDATES:
        if p.exists():
            return p

    # last resort: search Downloads shallow
    dl = Path.home() / "Downloads"
    if dl.exists():
        for p in dl.glob("*.xml"):
            if "library" in p.name.lower():
                return p

    raise FileNotFoundError("Music Library.xml not found. Set JARVIS_MUSIC_LIBRARY_XML or copy to ~/Music/Music/Media.localized/Music Library.xml")


def _cache_is_valid(xml_path: Path, ttl_hours: int = 24) -> bool:
    if not CACHE_FILE.exists():
        return False
    c = _load_json(CACHE_FILE)
    if str(c.get("source_path", "")) != str(xml_path):
        return False
    try:
        if float(c.get("source_mtime", 0.0)) != float(xml_path.stat().st_mtime):
            return False
    except Exception:
        return False
    built = float(c.get("built_at_unix", 0.0))
    if not built:
        return False
    return (time.time() - built) <= ttl_hours * 3600


def _build_cache(xml_path: Path) -> Dict[str, Any]:
    with xml_path.open("rb") as f:
        data = plistlib.load(f)

    tracks_raw: Dict[str, Any] = data.get("Tracks") or {}
    playlists_raw: List[Dict[str, Any]] = data.get("Playlists") or []

    # Map Track ID -> Persistent ID, and build track rows
    trackid_to_pid: Dict[str, str] = {}
    tracks: List[Dict[str, str]] = []

    for track_id, t in tracks_raw.items():
        tid = str(track_id)
        pid = str(t.get("Persistent ID") or "").strip()
        if not pid:
            continue
        name = str(t.get("Name") or "").strip()
        artist = str(t.get("Artist") or "").strip()
        album = str(t.get("Album") or "").strip()
        album_artist = str(t.get("Album Artist") or "").strip()
        trackid_to_pid[tid] = pid
        tracks.append(
            {
                "pid": pid,
                "name": name,
                "artist": artist,
                "album": album,
                "album_artist": album_artist,
                "n_name": _norm(name),
                "n_artist": _norm(artist),
                "n_album": _norm(album),
                "n_album_artist": _norm(album_artist),
            }
        )

    # Artists (unique)
    artists_set = set()
    for r in tracks:
        if r["n_artist"]:
            artists_set.add(r["n_artist"])
        if r["n_album_artist"]:
            artists_set.add(r["n_album_artist"])

    # Albums (group)
    albums_map: Dict[str, Dict[str, Any]] = {}
    for r in tracks:
        n_album = r["n_album"]
        if not n_album:
            continue
        n_ar = r["n_album_artist"] or r["n_artist"]
        key = f"{n_album}||{n_ar}"
        if key not in albums_map:
            albums_map[key] = {"n_album": n_album, "n_album_artist": n_ar, "album": r["album"], "album_artist": r["album_artist"] or r["artist"], "pids": []}
        albums_map[key]["pids"].append(r["pid"])

    albums = list(albums_map.values())

    # Playlists
    playlists: List[Dict[str, Any]] = []
    for pl in playlists_raw:
        name = str(pl.get("Name") or "").strip()
        pid = str(pl.get("Playlist Persistent ID") or "").strip()
        items = pl.get("Playlist Items") or []
        pids: List[str] = []
        for it in items:
            tid = str(it.get("Track ID") or "").strip()
            if tid and tid in trackid_to_pid:
                pids.append(trackid_to_pid[tid])
        if name and pid:
            playlists.append(
                {
                    "pid": pid,
                    "name": name,
                    "n_name": _norm(name),
                    "pids": pids,
                }
            )

    cache = {
        "source_path": str(xml_path),
        "source_mtime": float(xml_path.stat().st_mtime),
        "built_at_unix": float(time.time()),
        "tracks": tracks,
        "artists": sorted(list(artists_set)),
        "albums": albums,
        "playlists": playlists,
    }
    _save_json(CACHE_FILE, cache)
    return cache


def _load_library(ttl_hours: int = 24) -> Dict[str, Any]:
    xml_path = _get_xml_path()
    if _cache_is_valid(xml_path, ttl_hours=ttl_hours):
        return _load_json(CACHE_FILE)
    return _build_cache(xml_path)


def _score_text(n_text: str, q_tokens: List[str], q_norm: str) -> float:
    if not n_text:
        return 0.0
    tokset = set(n_text.split(" "))
    common = sum(1 for t in q_tokens if t in tokset)
    bonus = 1.0 if q_norm and q_norm in n_text else 0.0
    return common / max(1, len(q_tokens)) + bonus


def _top_matches(items: List[Tuple[float, Any]], limit: int) -> List[Any]:
    items_sorted = sorted(items, key=lambda x: x[0], reverse=True)
    return [it for s, it in items_sorted[:limit] if s > 0.0]


def _queue_playlist(track_pids: List[str], *, shuffle: bool) -> None:
    # Build/replace "JARVIS Queue" playlist, then play it
    pids = [p for p in track_pids if p][:250]
    if not pids:
        raise RuntimeError("Empty queue")

    _set_shuffle(shuffle)

    # AppleScript list literal
    lit = "{" + ",".join(f'"{_as_escape(p)}"' for p in pids) + "}"
    script = f"""
tell application "Music"
    ignoring case and diacriticals
        set lib to library playlist 1
        set qname to "JARVIS Queue"
        if not (exists playlist qname) then
            make new playlist with properties {{name:qname}}
        end if
        set q to playlist qname
        try
            delete every track of q
        end try
        set pidList to {lit}
        repeat with pid in pidList
            try
                set t to (first track of lib whose persistent ID is (pid as text))
                duplicate t to q
            end try
        end repeat
        play q
    end ignoring
end tell
"""
    _run_osascript(script)


def _play_track_pid(pid: str) -> None:
    p = _as_escape(pid)
    script = f"""
tell application "Music"
    ignoring case and diacriticals
        set lib to library playlist 1
        set t to (first track of lib whose persistent ID is "{p}")
        play t
    end ignoring
end tell
"""
    _run_osascript(script)


def _play_playlist_pid(pid: str, *, shuffle: bool) -> None:
    _set_shuffle(shuffle)
    p = _as_escape(pid)
    script = f"""
tell application "Music"
    ignoring case and diacriticals
        set pl to (first playlist whose persistent ID is "{p}")
        play pl
    end ignoring
end tell
"""
    _run_osascript(script)


def music_control(args: Dict[str, Any]) -> Dict[str, Any]:
    # numeric selection continuation
    token = str(args.get("token") or "").strip()
    pick_raw = args.get("pick", None)

    if token and pick_raw is not None:
        try:
            pick = int(pick_raw)
        except Exception:
            return {"ok": False, "error": "Invalid choice"}

        entry = _CHOICES.get(token) or {}
        options = entry.get("options") or []
        shuffle = bool(entry.get("shuffle") or False)
        if pick < 1 or pick > len(options):
            return {"ok": False, "error": "Choice out of range"}

        opt = options[pick - 1]
        typ = str(opt.get("type") or "")
        if typ == "song":
            _play_track_pid(str(opt.get("pid") or ""))
        elif typ == "playlist":
            _play_playlist_pid(str(opt.get("pid") or ""), shuffle=shuffle)
        elif typ == "album":
            _queue_playlist(list(opt.get("pids") or []), shuffle=shuffle)
        elif typ == "artist":
            _queue_playlist(list(opt.get("pids") or []), shuffle=shuffle)
        else:
            return {"ok": False, "error": "Unknown option type"}

        _CHOICES.pop(token, None)
        return {"ok": True, "played": {"type": typ, "name": opt.get("name"), "artist": opt.get("artist"), "album": opt.get("album")}}

    query = str(args.get("query") or "").strip()
    if not query:
        return {"ok": False, "error": "Missing query"}

    ctrl = _detect_control(query)
    if ctrl:
        if ctrl == "play":
            _control_play()
        elif ctrl == "pause":
            _control_pause()
        elif ctrl == "stop":
            _control_stop()
        elif ctrl == "next":
            _control_next()
        elif ctrl == "previous":
            _control_previous()
        elif ctrl == "forward15":
            _control_seek(15)
        elif ctrl == "back15":
            _control_seek(-15)
        else:
            return {"ok": False, "error": "Unknown control"}
        return {"ok": True, "action": ctrl}

    category, text, shuffle = _parse_music_request(query)
    if not text:
        _control_play()
        return {"ok": True, "action": "play"}

    q_norm = text
    q_tokens = _tokens(text)
    if not q_tokens:
        return {"ok": False, "error": "Could not parse request"}

    lib = _load_library(ttl_hours=24)

    tracks = lib.get("tracks") or []
    artists = lib.get("artists") or []
    albums = lib.get("albums") or []
    playlists = lib.get("playlists") or []

    options: List[Dict[str, Any]] = []

    def add_song_matches(limit: int = 10) -> None:
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for r in tracks:
            s = _score_text(str(r.get("n_name") or ""), q_tokens, q_norm)
            if s > 0.0:
                scored.append((s, r))
        for r in _top_matches(scored, limit):
            options.append({"type": "song", "pid": r["pid"], "name": r["name"], "artist": r["artist"], "album": r["album"]})

    def add_artist_matches(limit: int = 6) -> None:
        scored: List[Tuple[float, str]] = []
        for a in artists:
            scored.append((_score_text(a, q_tokens, q_norm), a))
        for a_norm in _top_matches(scored, limit):
            # collect pids for that artist
            pids: List[str] = []
            for r in tracks:
                if r.get("n_artist") == a_norm or r.get("n_album_artist") == a_norm:
                    pids.append(r["pid"])
            # pick display name from first track
            disp = ""
            for r in tracks:
                if r.get("n_artist") == a_norm and r.get("artist"):
                    disp = r["artist"]
                    break
                if r.get("n_album_artist") == a_norm and r.get("album_artist"):
                    disp = r["album_artist"]
                    break
            if disp and pids:
                options.append({"type": "artist", "name": disp, "artist": disp, "album": "", "pids": pids})

    def add_album_matches(limit: int = 6) -> None:
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for a in albums:
            n_album = str(a.get("n_album") or "")
            n_ar = str(a.get("n_album_artist") or "")
            s = max(_score_text(n_album, q_tokens, q_norm), _score_text(f"{n_album} {n_ar}", q_tokens, q_norm))
            if s > 0.0:
                scored.append((s, a))
        for a in _top_matches(scored, limit):
            options.append({"type": "album", "name": a.get("album"), "artist": a.get("album_artist"), "album": a.get("album"), "pids": a.get("pids") or []})

    def add_playlist_matches(limit: int = 6) -> None:
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for p in playlists:
            s = _score_text(str(p.get("n_name") or ""), q_tokens, q_norm)
            if s > 0.0:
                scored.append((s, p))
        for p in _top_matches(scored, limit):
            options.append({"type": "playlist", "pid": p.get("pid"), "name": p.get("name"), "artist": "", "album": ""})

    # category routing
    if category == "song":
        add_song_matches()
    elif category == "artist":
        add_artist_matches()
    elif category == "album":
        add_album_matches()
    elif category == "playlist":
        add_playlist_matches()
    else:
        # auto: prefer song, then artist, album, playlist
        add_song_matches(limit=8)
        add_artist_matches(limit=4)
        add_album_matches(limit=4)
        add_playlist_matches(limit=4)

    if not options:
        return {"ok": False, "error": f'Nothing found for: "{text}"'}

    if len(options) == 1:
        opt = options[0]
        typ = opt["type"]
        if typ == "song":
            _play_track_pid(str(opt["pid"]))
        elif typ == "playlist":
            _play_playlist_pid(str(opt["pid"]), shuffle=shuffle)
        elif typ in ("album", "artist"):
            _queue_playlist(list(opt.get("pids") or []), shuffle=shuffle)
        else:
            return {"ok": False, "error": "Unknown option type"}
        return {"ok": True, "played": {"type": typ, "name": opt.get("name"), "artist": opt.get("artist"), "album": opt.get("album")}}

    tok = uuid.uuid4().hex
    _CHOICES[tok] = {"options": options, "shuffle": shuffle}

    numbered = []
    for i, opt in enumerate(options, start=1):
        numbered.append(
            {
                "n": i,
                "type": opt.get("type"),
                "name": opt.get("name"),
                "artist": opt.get("artist"),
                "album": opt.get("album"),
            }
        )

    return {
        "ok": True,
        "needs_choice": True,
        "token": tok,
        "original_query": text,
        "options": numbered,
    }
