import asyncio
import json
import sys
import uuid
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from jarvis.core.orchestrator import Orchestrator


WEB_DIR = Path(__file__).resolve().parent / "web"
INDEX_HTML = WEB_DIR / "index.html"
STATIC_DIR = WEB_DIR / "static"


@dataclass
class ChatEvent:
    role: str  # "user" | "jarvis" | "system"
    text: str
    source: str  # "terminal" | "gui"
    client_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "text": self.text,
            "source": self.source,
            "client_id": self.client_id,
        }


class ConnectionManager:
    def __init__(self) -> None:
        self._clients: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> str:
        await ws.accept()
        client_id = uuid.uuid4().hex
        async with self._lock:
            self._clients[client_id] = ws
        return client_id

    async def disconnect(self, client_id: str) -> None:
        async with self._lock:
            self._clients.pop(client_id, None)

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        async with self._lock:
            clients = list(self._clients.items())

        dead: list[str] = []
        for cid, ws in clients:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(cid)

        for cid in dead:
            await self.disconnect(cid)


app = FastAPI(title="JARVIS GUI")
manager = ConnectionManager()
jarvis = Orchestrator()

# Static mount
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> HTMLResponse:
    html = INDEX_HTML.read_text(encoding="utf-8")
    return HTMLResponse(html)


async def _handle_message(text: str, source: str, client_id: Optional[str] = None) -> None:
    text = text.strip()
    if not text:
        return

    # broadcast user message
    evt_user = ChatEvent(role="user", text=text, source=source, client_id=client_id)
    await manager.broadcast(evt_user.to_dict())
    _print_terminal("You", text)

    # run jarvis (blocking) in thread to not freeze the server
    reply = await asyncio.to_thread(jarvis.handle, text)
    reply = (reply or "").strip()

    evt_bot = ChatEvent(role="jarvis", text=reply, source=source, client_id=client_id)
    await manager.broadcast(evt_bot.to_dict())
    _print_terminal("JARVIS", reply)


def _print_terminal(who: str, text: str) -> None:
    if not text:
        return
    sys.stdout.write(f"{who}> {text}\n")
    sys.stdout.flush()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    client_id = await manager.connect(ws)
    await manager.broadcast(ChatEvent(role="system", text="GUI connected", source="gui", client_id=client_id).to_dict())

    try:
        while True:
            raw = await ws.receive_text()
            with _suppress():
                data = json.loads(raw)
                text = str(data.get("text", "")).strip()
            if not text:
                # also accept raw string messages
                text = raw.strip()
            await _handle_message(text=text, source="gui", client_id=client_id)
    except WebSocketDisconnect:
        await manager.disconnect(client_id)
        await manager.broadcast(ChatEvent(role="system", text="GUI disconnected", source="gui").to_dict())


class _suppress:
    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc, tb) -> bool:
        return True


async def _terminal_input_loop() -> None:
    # terminal input that feeds the same orchestrator + broadcasts to GUI
    while True:
        try:
            text = await asyncio.to_thread(input, "")
        except (EOFError, KeyboardInterrupt):
            break

        text = text.strip()
        if not text:
            continue

        if text.lower() in {"/quit", "/exit"}:
            break

        await _handle_message(text=text, source="terminal", client_id=None)


async def main(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    url = f"http://{host}:{port}/"
    _print_terminal("SYSTEM", f"Starting GUI on {url}")

    if open_browser:
        with _suppress():
            webbrowser.open(url, new=1, autoraise=True)

    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)

    terminal_task = asyncio.create_task(_terminal_input_loop())
    server_task = asyncio.create_task(server.serve())

    done, pending = await asyncio.wait(
        {terminal_task, server_task},
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
