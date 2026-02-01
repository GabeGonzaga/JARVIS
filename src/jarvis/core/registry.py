from dataclasses import dataclass
from typing import Any, Callable, Dict

@dataclass(frozen=True)
class Tool:
    name: str
    run: Callable[[Dict[str, Any]], Dict[str, Any]]
    risk: str = "low"  # low|med|high

class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        return self._tools[name]

    def list(self) -> list[str]:
        return sorted(self._tools.keys())
