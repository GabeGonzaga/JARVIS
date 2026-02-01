from pathlib import Path
from typing import Any, Dict, List

def _expand(p: str) -> Path:
    return Path(p).expanduser().resolve()

def _is_allowed(path: Path, allowed_roots: List[str]) -> bool:
    for r in allowed_roots:
        root = _expand(r)
        try:
            path.relative_to(root)
            return True
        except Exception:
            continue
    return False

def list_dir(args: Dict[str, Any], allowed_roots: List[str]) -> Dict[str, Any]:
    p = _expand(str(args.get("path", "~")))
    if not _is_allowed(p, allowed_roots):
        return {"ok": False, "error": "path not allowed"}
    if not p.is_dir():
        return {"ok": False, "error": "not a directory"}
    items = [x.name for x in sorted(p.iterdir())][:200]
    return {"ok": True, "path": str(p), "items": items}

def read_file(args: Dict[str, Any], allowed_roots: List[str]) -> Dict[str, Any]:
    p = _expand(str(args.get("path", "")))
    if not _is_allowed(p, allowed_roots):
        return {"ok": False, "error": "path not allowed"}
    if not p.is_file():
        return {"ok": False, "error": "not a file"}
    text = p.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "path": str(p), "content": text[:8000]}
