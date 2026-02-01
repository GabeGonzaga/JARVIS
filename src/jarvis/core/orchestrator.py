import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from jarvis.core.config import load_settings
from jarvis.core.registry import Tool, ToolRegistry
from jarvis.core.security import SecurityManager
from jarvis.llm.ollama import chat
from jarvis.observability.logging import log_event, new_trace
from jarvis.tools.macos import basic as macos_basic
from jarvis.tools.system import files as sys_files

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

        # wrap system tools with allowed_roots bound
        self.registry.register(Tool("system.list_dir", lambda a: sys_files.list_dir(a, self.allowed_roots), risk="low"))
        self.registry.register(Tool("system.read_file", lambda a: sys_files.read_file(a, self.allowed_roots), risk="low"))

    def handle(self, user_text: str) -> str:
        user_text = user_text.strip()
        if not user_text:
            return ""

        # local command: model switch
        if user_text.lower().startswith("/model "):
            self.model = user_text.split(" ", 1)[1].strip()
            return f"Modelo ativo: {self.model}"

        if user_text.lower() == "/tools":
            return "\n".join(self.registry.list())

        log_event(self.trace, "user_input", text=user_text, model=self.model)

        decision = self._decide(user_text)
        if decision.get("type") != "tool":
            content = decision.get("content") or ""
            return content

        tool_name = str(decision.get("name", "")).strip()
        args = decision.get("args") or {}
        return self._run_tool_flow(user_text, tool_name, args)

    def _decide(self, user_text: str) -> Dict[str, Any]:
        tools = self._tool_specs()
        sys = (
            "Responde SEMPRE em JSON puro.\n"
            "Escolhe UMA opção:\n"
            '1) {"type":"chat","content":"..."}\n'
            '2) {"type":"tool","name":"<tool_name>","args":{...},"reason":"..."}\n'
            "Só podes escolher tools desta lista (respeita os args):\n"
            + json.dumps(tools, ensure_ascii=False)
        )
        raw = chat(self.model, [{"role": "system", "content": sys}, {"role": "user", "content": user_text}])
        parsed = _parse_json_best_effort(raw)
        if not parsed:
            return {"type": "chat", "content": raw}
        return parsed

    def _tool_specs(self) -> List[Dict[str, Any]]:
        # declaração minimalista de args para o LLM
        return [
            {"name": "macos.open_app", "args": {"app": "string"}, "risk": "med"},
            {"name": "macos.open_url", "args": {"url": "string"}, "risk": "low"},
            {"name": "macos.create_note", "args": {"title": "string", "body": "string"}, "risk": "med"},
            {"name": "system.list_dir", "args": {"path": "string"}, "risk": "low"},
            {"name": "system.read_file", "args": {"path": "string"}, "risk": "low"}
        ]

    def _run_tool_flow(self, user_text: str, tool_name: str, args: Dict[str, Any]) -> str:
        if not self.perms.get(tool_name, False):
            return f"Bloqueado por permissões: {tool_name}"

        tool = self.registry.get(tool_name)
        log_event(self.trace, "tool_call", tool=tool_name, args=args, risk=tool.risk)

        if tool.risk in ("med", "high"):
            self.security.authorize(f"{tool_name} | {user_text}")

        try:
            result = tool.run(args)
        except Exception as e:
            log_event(self.trace, "tool_error", tool=tool_name, error=str(e))
            return f"Erro na tool {tool_name}: {e}"

        log_event(self.trace, "tool_result", tool=tool_name, ok=result.get("ok", True))

        # segunda chamada: transformar output técnico em resposta natural
        sys = "Responde em PT-PT, curto e claro. Usa o resultado da tool. Não inventes."
        msg = (
            f"Pedido: {user_text}\n"
            f"Tool: {tool_name}\n"
            f"Resultado (JSON): {json.dumps(result, ensure_ascii=False)}"
        )
        return chat(self.model, [{"role": "system", "content": sys}, {"role": "user", "content": msg}])

def _parse_json_best_effort(text: str) -> Optional[Dict[str, Any]]:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # fallback: tenta extrair o primeiro bloco {...}
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        chunk = text[start : end + 1]
        try:
            return json.loads(chunk)
        except Exception:
            return None
    return None
