from __future__ import annotations

import json
from contextlib import suppress
from typing import Any, Dict, List, Optional

from jarvis.core.config import load_settings
from jarvis.core.registry import Tool, ToolRegistry
from jarvis.core.security import SecurityManager
from jarvis.llm.ollama import chat
from jarvis.observability.logging import log_event, new_trace
from jarvis.tools.macos import basic as macos_basic
from jarvis.tools.macos import music_control as macos_music
from jarvis.tools.macos import shortcuts as macos_shortcuts
from jarvis.tools.system import files as sys_files
from jarvis.tools.system import time as sys_time


def _safe_import_weather() -> tuple[Optional[Any], Optional[Any]]:
    ipma_fn = None
    apple_fn = None
    with suppress(Exception):
        from jarvis.tools.weather.ipma import weather_ipma  # type: ignore

        ipma_fn = weather_ipma
    with suppress(Exception):
        from jarvis.tools.weather.apple import weather_apple  # type: ignore

        apple_fn = weather_apple
    return ipma_fn, apple_fn


class Orchestrator:
    def __init__(self) -> None:
        self.trace = new_trace()
        self.settings = load_settings()

        llm_cfg = self.settings.get("llm", {})
        self.model = llm_cfg.get("chat_model") or llm_cfg.get("model") or "qwen3:4b-instruct"
        self.router_model = llm_cfg.get("router_model") or self.model

        self.allowed_roots = self.settings.get("file_access", {}).get("allowed_roots", ["~"])
        self.perms = self.settings.get("tool_permissions", {})

        self.security = SecurityManager(
            auth_window_seconds=int(self.settings.get("security", {}).get("auth_window_seconds", 60))
        )

        self.registry = ToolRegistry()
        self._has_weather_ipma = False
        self._has_weather_apple = False

        self.memory: List[Dict[str, str]] = []
        self._pending_music: Dict[str, Any] = {}

        self._register_tools()

    def _register_tools(self) -> None:
        self.registry.register(Tool("macos.open_app", macos_basic.open_app, risk="med"))
        self.registry.register(Tool("macos.open_url", macos_basic.open_url, risk="low"))
        self.registry.register(Tool("macos.create_note", macos_basic.create_note, risk="med"))

        self.registry.register(Tool("macos.music_control", macos_music.music_control, risk="low"))

        self.registry.register(Tool("macos.list_shortcuts", macos_shortcuts.list_shortcuts, risk="low"))
        self.registry.register(Tool("macos.run_shortcut", macos_shortcuts.run_shortcut, risk="med"))

        self.registry.register(Tool("system.list_dir", lambda a: sys_files.list_dir(a, self.allowed_roots), risk="low"))
        self.registry.register(Tool("system.read_file", lambda a: sys_files.read_file(a, self.allowed_roots), risk="low"))

        self.registry.register(Tool("system.now", sys_time.now, risk="low"))

        ipma_fn, apple_fn = _safe_import_weather()
        if ipma_fn is not None:
            self.registry.register(Tool("weather.ipma", ipma_fn, risk="low"))
            self._has_weather_ipma = True
        if apple_fn is not None:
            self.registry.register(Tool("weather.apple", apple_fn, risk="low"))
            self._has_weather_apple = True

    def handle(self, user_text: str) -> str:
        user_text = user_text.strip()
        if not user_text:
            return ""

        cmd = user_text.lower().strip()

        if cmd == "/tools":
            return "\n".join(self.registry.list())

        shortcut_map = {
            "/now": "datetime",
            "/date": "date",
            "/time": "time",
            "/weekday": "weekday",
            "/day": "day",
            "now": "datetime",
            "date": "date",
            "time": "time",
            "weekday": "weekday",
            "day": "day",
        }
        if cmd in shortcut_map:
            what = shortcut_map[cmd]
            return self._format_now(sys_time.now({"what": what}), what=what)

        if self._pending_music and cmd.isdigit():
            pick = int(cmd)
            token = str(self._pending_music.get("token", "")).strip()
            original_query = str(self._pending_music.get("original_query", "")).strip()
            result = macos_music.music_control({"token": token, "pick": pick, "original_query": original_query})
            self._pending_music = {}
            return self._format_music_result(result)

        log_event(self.trace, "user_input", text=user_text, model=self.model)
        self._remember("user", user_text)

        decision = self._decide(user_text)
        if decision.get("type") != "tool":
            content = str(decision.get("content") or "")
            self._remember("assistant", content)
            return content

        tool_name = str(decision.get("name", "")).strip()
        args = decision.get("args") or {}
        out = self._run_tool_flow(user_text, tool_name, args)
        self._remember("assistant", out)
        return out

    def _remember(self, role: str, content: str) -> None:
        self.memory.append({"role": role, "content": content})
        self.memory = self.memory[-6:]

    def _recent_messages(self) -> List[Dict[str, str]]:
        return self.memory[-6:]

    def _decide(self, user_text: str) -> Dict[str, Any]:
        tools = self._tool_specs()

        sys_prompt = (
            "You are JARVIS. Always address the user as Sir.\n"
            "Always respond in JSON only (no markdown, no extra text).\n"
            "Choose exactly one:\n"
            '1) {"type":"chat","content":"..."}\n'
            '2) {"type":"tool","name":"<tool_name>","args":{...},"reason":"..."}\n'
            "Rules:\n"
            "- For date/time/now/current time/current date/day of week/weekday, you MUST use tool system.now.\n"
            '- Use args {"what":"datetime"} for both, {"what":"date"} for date only, {"what":"time"} for time only, '
            '{"what":"weekday"} for weekday only, {"what":"day"} for weekday + date.\n'
            "- For music requests and controls (play, resume, pause, stop, next, previous, skip, forward/back 15 seconds, "
            "play song/artist/album/playlist, shuffle), you MUST use tool macos.music_control with args "
            '{"query":"<the user request>"} and keep the user words.\n'
            "- Only use tools from the list below and respect their args.\n"
            "Tools:\n"
            + json.dumps(tools, ensure_ascii=False)
        )

        messages = [{"role": "system", "content": sys_prompt}] + self._recent_messages() + [
            {"role": "user", "content": user_text}
        ]

        raw = chat(self.router_model, messages)
        parsed = _parse_json_best_effort(raw)
        if parsed is None:
            return {"type": "chat", "content": raw}
        return parsed

    def _tool_specs(self) -> List[Dict[str, Any]]:
        specs: List[Dict[str, Any]] = [
            {"name": "macos.open_app", "args": {"app": "string"}, "risk": "med"},
            {"name": "macos.open_url", "args": {"url": "string"}, "risk": "low"},
            {"name": "macos.create_note", "args": {"title": "string", "body": "string"}, "risk": "med"},
            {"name": "macos.music_control", "args": {"query": "string"}, "risk": "low"},
            {"name": "macos.list_shortcuts", "args": {}, "risk": "low"},
            {"name": "macos.run_shortcut", "args": {"name": "string", "input": "string"}, "risk": "med"},
            {"name": "system.list_dir", "args": {"path": "string"}, "risk": "low"},
            {"name": "system.read_file", "args": {"path": "string"}, "risk": "low"},
            {"name": "system.now", "args": {"what": "string"}, "risk": "low"},
        ]
        if self._has_weather_ipma:
            specs.append({"name": "weather.ipma", "args": {"query": "string"}, "risk": "low"})
        if self._has_weather_apple:
            specs.append({"name": "weather.apple", "args": {"query": "string"}, "risk": "low"})
        return specs

    def _run_tool_flow(self, user_text: str, tool_name: str, args: Dict[str, Any]) -> str:
        if not self.perms.get(tool_name, False):
            return f"Sir, blocked by permissions: {tool_name}"

        tool = self.registry.get(tool_name)
        log_event(self.trace, "tool_call", tool=tool_name, args=args, risk=tool.risk)

        if tool.risk in ("med", "high"):
            self.security.authorize(f"{tool_name} | {user_text}")

        try:
            result = tool.run(args)
        except Exception as e:
            log_event(self.trace, "tool_error", tool=tool_name, error=str(e))
            return f"Sir, tool error ({tool_name}): {e}"

        log_event(self.trace, "tool_result", tool=tool_name, ok=result.get("ok", True))

        if tool_name == "system.now":
            what = str(args.get("what") or result.get("what") or "datetime").lower()
            return self._format_now(result, what=what)

        if tool_name == "macos.music_control":
            return self._format_music_result(result)

        sys_prompt = "Respond in Portuguese (PT-PT). Always address the user as Sir. Use only the tool result. Do not invent."
        msg = (
            f"User request: {user_text}\n"
            f"Tool: {tool_name}\n"
            f"Result (JSON): {json.dumps(result, ensure_ascii=False)}"
        )
        return chat(self.model, [{"role": "system", "content": sys_prompt}, {"role": "user", "content": msg}])

    def _format_music_result(self, result: Dict[str, Any]) -> str:
        if not result.get("ok", False):
            err = str(result.get("error") or "Unknown error")
            return f"Sir, {err}"

        if result.get("needs_choice"):
            token = str(result.get("token", "")).strip()
            original_query = str(result.get("original_query", "")).strip()
            options = result.get("options") or []

            self._pending_music = {"token": token, "original_query": original_query}

            lines = ["Sir, choose one option by number:"]
            for opt in options:
                n = opt.get("n")
                typ = opt.get("type")
                name = opt.get("name") or ""
                artist = opt.get("artist") or ""
                album = opt.get("album") or ""
                if typ == "song":
                    lines.append(f"{n}. {name} - {artist} ({album})")
                elif typ == "album":
                    lines.append(f"{n}. Album: {album} - {artist}")
                elif typ == "artist":
                    lines.append(f"{n}. Artist: {artist}")
                elif typ == "playlist":
                    lines.append(f"{n}. Playlist: {name}")
                else:
                    lines.append(f"{n}. {name}")
            return "\n".join(lines)

        if "action" in result:
            a = str(result.get("action") or "").strip()
            if a == "next":
                return "Sir, next track."
            if a == "previous":
                return "Sir, previous track."
            if a == "pause":
                return "Sir, paused."
            if a == "stop":
                return "Sir, stopped."
            if a == "play":
                return "Sir, playing."
            if a == "forward15":
                return "Sir, forward 15 seconds."
            if a == "back15":
                return "Sir, back 15 seconds."
            return f"Sir, done: {a}"

        played = result.get("played") or {}
        if isinstance(played, dict):
            name = str(played.get("name") or "")
            artist = str(played.get("artist") or "")
            album = str(played.get("album") or "")
            if name and artist:
                return f"Sir, playing: {name} - {artist} ({album})"
            if name:
                return f"Sir, playing: {name}"
        return "Sir, done."

    def _format_now(self, result: Dict[str, Any], what: str = "datetime") -> str:
        what = (what or "datetime").strip().lower()

        date_str = str(result.get("date", "")).strip()
        time_str = str(result.get("time", "")).strip()
        weekday = str(result.get("weekday", "")).strip()
        day = str(result.get("day", "")).strip()
        tzname = str(result.get("tzname", "")).strip()
        dt_str = str(result.get("datetime", "")).strip()

        if what == "time":
            return f"Sir, hora: {time_str}"
        if what == "date":
            return f"Sir, data: {date_str}"
        if what == "weekday":
            return f"Sir, dia da semana: {weekday}"
        if what == "day":
            return f"Sir, dia: {day}"
        return f"Sir, data e hora: {dt_str} ({tzname})" if tzname else f"Sir, data e hora: {dt_str}"


def _parse_json_best_effort(text: str) -> Optional[Dict[str, Any]]:
    t = (text or "").strip()
    with suppress(Exception):
        return json.loads(t)

    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = t[start : end + 1]
        with suppress(Exception):
            return json.loads(chunk)

    return None
