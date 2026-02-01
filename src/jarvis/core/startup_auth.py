from __future__ import annotations

import subprocess
from pathlib import Path


class StartupAuthError(RuntimeError):
    pass


def _find_repo_root(start: Path) -> Path:
    # Prefer explicit markers
    for p in (start, *start.parents):
        if (p / "pyproject.toml").exists() or (p / ".git").exists():
            return p
    # Fallback: parent of "src"
    for p in (start, *start.parents):
        if p.name == "src":
            return p.parent
    # Last resort: previous assumption
    return start.parents[3]


def require_touchid_once() -> None:
    repo_root = _find_repo_root(Path(__file__).resolve())
    tool = repo_root / "bin" / "jarvis-auth"

    if not tool.exists():
        raise StartupAuthError(f"TouchID helper missing at: {tool}. Run: scripts/build_macos_auth.sh")

    r = subprocess.run([str(tool)], capture_output=True, text=True)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip()
        raise StartupAuthError(f"TouchID authentication failed/unavailable. {detail}")
