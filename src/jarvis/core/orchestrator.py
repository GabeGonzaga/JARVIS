import json
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from jarvis.core.config import load_settings
from jarvis.core.registry import Tool, ToolRegistry
from jarvis.core.security import SecurityManager
from jarvis.llm.ollama import chat
from jarvis.observability.logging import log_event, new_trace
from jarvis.tools.macos import basic as macos_basic
from jarvis.tools.system import files as sys_files
from jarvis.tools.system import time as sys_time


@dataclass
class ToolSpec:
    name: str
    risk: str
    args: Dict[str, str]


class Orchestrator:
    def __init__(self) -> None:
        self.trace = new_trace()
        self.settings = load_settings()
        self.model = self.settings["llm"]["model"]
        self.allowed_roots = self.settings.get("file_access", {}).get("allowed_roots", ["~"])
        self.perms = self.settings.get("tool_permissions", {})
        self.security = SecurityManager(
            auth_window_seconds=int(self.settings.get("security", {}).get("auth_window_seconds", 60))
        )
        self.registry = ToolRegistry()
        self._register_tools()

    def _register_tools(self) -> None:
        self.registry.register(Tool("macos.open_app", macos_basic.open_app, risk="med"))
        self.registry.register(Tool("macos.open_url", macos_basic.open_url, risk="low"))
        self.registry.register(Tool("macos.create_note", macos_basic.create_note, risk="med"))

        self.registry.register(
            Tool("system.list_dir", lambda a: sys_files.list_dir(a, self.allowed_roots), risk="low")
        )
        self.registry.register(
            Tool("system.read_file", lambda a: sys_files.read_file(a, self.allowed_roots), risk="low")
        )

        # date/time (local wall-clock)
        self.registry.register(Tool("system.now", sys_time.now, risk="low"))

    def handle(self, user_text: str) -> str:
        user_text = user_text.strip()
        if not user_text:
            return ""

        lower = user_text.lower()

        # local command: model switch
        if lower.startswith("/model "):
            self.model = user_text.split(" ", 1)[1].strip()
            return f"Active model: {self.model}"

        # local shortcuts (no LLM)
        if lower in {"/now", "/date", "/time"}:
            what = {"/now": "datetime", "/date": "date", "/time": "time"}[lower]
            return self._format_now(sys_time.now({"what": what}))

        if lower == "/tools":
            return "\n".join(self.registry.list())

        log_event(self.trace, "user_input", text=user_text, model=self.model)

        decision = self._decide(user_text)
        if decision.get("type") != "tool":
            return str(decision.get("content") or "")

        tool_name = str(decision.get("name", "")).strip()
        args = decision.get("args") or {}
        return self._run_tool_flow(user_text, tool_name, args)

    def _decide(self, user_text: str) -> Dict[str, Any]:
        tools = self._tool_specs()

        sys = (
            "You are JARVIS. Your name is JARVIS. When asked your name, answer: 'My name is JARVIS.'\n"
            "Always respond in JSON only (no markdown, no extra text).\n"
            "Choose exactly one:\n"
            '1) {"type":"chat","content":"..."}\n'
            '2) {"type":"tool","name":"<tool_name>","args":{...},"reason":"..."}\n'
            "Rules:\n"
            "- If the user asks for date/time/now/current time/current date, you MUST use tool system.now.\n"
            '- Use args {"what":"datetime"} for both, {"what":"date"} for date only, {"what":"time"} for time only.\n'
            "- Only use tools from the list below and respect their args.\n"
            "Tools:\n"
            + json.dumps(tools, ensure_ascii=False)
        )

        raw = chat(self.model, [{"role": "system", "content": sys}, {"role": "user", "content": user_text}])
        parsed = _parse_json_best_effort(raw)
        return parsed if parsed else {"type": "chat", "content": raw}

    def _tool_specs(self) -> List[Dict[str, Any]]:
        return [
            {"name": "macos.open_app", "args": {"app": "string"}, "risk": "med"},
            {"name": "macos.open_url", "args": {"url": "string"}, "risk": "low"},
            {"name": "macos.create_note", "args": {"title": "string", "body": "string"}, "risk": "med"},
            {"name": "system.list_dir", "args": {"path": "string"}, "risk": "low"},
            {"name": "system.read_file", "args": {"path": "string"}, "risk": "low"},
            {"name": "system.now", "args": {"what": "string"}, "risk": "low"},
        ]

    def _run_tool_flow(self, user_text: str, tool_name: str, args: Dict[str, Any]) -> str:
        if not self.perms.get(tool_name, False):
            return f"Blocked by permissions: {tool_name}"

        tool = self.registry.get(tool_name)
        log_event(self.trace, "tool_call", tool=tool_name, args=args, risk=tool.risk)

        if tool.risk in ("med", "high"):
            self.security.authorize(f"{tool_name} | {user_text}")

        try:
            result = tool.run(args)
        except Exception as e:
            log_event(self.trace, "tool_error", tool=tool_name, error=str(e))
            return f"Tool error ({tool_name}): {e}"

        log_event(self.trace, "tool_result", tool=tool_name, ok=result.get("ok", True))

        # deterministic formatting for date/time
        if tool_name == "system.now":
            return self._format_now(result)

        sys = "Respond in English, short and correct. Use only the tool result. Do not invent."
        msg = (
            f"User request: {user_text}\n"
            f"Tool: {tool_name}\n"
            f"Result (JSON): {json.dumps(result, ensure_ascii=False)}"
        )
        return chat(self.model, [{"role": "system", "content": sys}, {"role": "user", "content": msg}])

    def _format_now(self, result: Dict[str, Any]) -> str:
        dt = str(result.get("datetime", "")).strip()
        date_str = str(result.get("date", "")).strip()
        time_str = str(result.get("time", "")).strip()
        tzname = str(result.get("tzname", "") or "").strip()

        line1 = f"Date & time: {dt}" + (f" ({tzname})" if tzname and tzname not in dt else "")
        return "\n".join([line1, f"Date: {date_str}", f"Time: {time_str}"])


def _parse_json_best_effort(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()

    with suppress(Exception):
        return json.loads(text)

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    chunk = text[start : end + 1]
    with suppress(Exception):
        return json.loads(chunk)

    return None
