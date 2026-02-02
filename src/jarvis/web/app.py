from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel

from jarvis.core.orchestrator import Orchestrator

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI()

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

jarvis = Orchestrator()
_history: List[Dict[str, Any]] = []


class ChatIn(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/history")
def history():
    return _history


@app.post("/api/chat")
def chat_api(payload: ChatIn):
    text = (payload.text or "").strip()
    if not text:
        return {"ok": False, "reply": ""}

    _history.append({"role": "user", "content": text})
    reply = jarvis.handle(text)
    _history.append({"role": "assistant", "content": reply})

    return {"ok": True, "reply": reply}
