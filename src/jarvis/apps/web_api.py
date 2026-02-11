from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis.core.orchestrator import Orchestrator

app = FastAPI(title="JARVIS Web")

# Local-only usage; CORS kept permissive for simplicity.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orch = Orchestrator()


class ChatIn(BaseModel):
    text: str


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    # Single-file UI. No external assets. No Node.
    return r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>JARVIS</title>
  <style>
    :root { color-scheme: dark; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      background: radial-gradient(1200px 800px at 30% 20%, rgba(59,130,246,0.18), transparent 60%),
                  radial-gradient(900px 700px at 80% 70%, rgba(16,185,129,0.12), transparent 60%),
                  linear-gradient(160deg, #020617, #0b1220 40%, #020617);
      color: #e5e7eb;
      height: 100vh;
      overflow: hidden;
    }
    .glow {
      position: fixed;
      width: 520px;
      height: 520px;
      border-radius: 9999px;
      pointer-events: none;
      background: radial-gradient(circle, rgba(59,130,246,0.14) 0%, rgba(59,130,246,0.0) 70%);
      transform: translate(-50%, -50%);
      opacity: 0.8;
      filter: blur(2px);
    }
    .wrap {
      max-width: 980px;
      margin: 0 auto;
      padding: 28px 18px;
      height: 100vh;
      display: flex;
      flex-direction: column;
      gap: 14px;
      box-sizing: border-box;
    }
    .top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .badge {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, rgba(59,130,246,1), rgba(37,99,235,1));
      display: grid;
      place-items: center;
      font-weight: 800;
      font-size: 22px;
      color: white;
    }
    .title {
      display: flex;
      flex-direction: column;
      line-height: 1.1;
    }
    .title h1 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0.6px;
    }
    .title p {
      margin: 2px 0 0 0;
      font-size: 12px;
      color: rgba(229,231,235,0.6);
    }
    .card {
      background: rgba(2,6,23,0.55);
      border: 1px solid rgba(148,163,184,0.15);
      border-radius: 18px;
      backdrop-filter: blur(14px);
      box-shadow: 0 20px 60px rgba(0,0,0,0.35);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      min-height: 0;
      flex: 1;
    }
    .messages {
      padding: 16px;
      overflow: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .row {
      display: flex;
      width: 100%;
    }
    .row.user { justify-content: flex-end; }
    .row.assistant { justify-content: flex-start; }

    .bubble {
      max-width: 78%;
      border-radius: 16px;
      padding: 10px 12px;
      font-size: 13px;
      line-height: 1.35;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .bubble.user {
      background: rgba(37,99,235,0.85);
      border: 1px solid rgba(37,99,235,0.40);
      color: white;
    }
    .bubble.assistant {
      background: rgba(15,23,42,0.75);
      border: 1px solid rgba(148,163,184,0.18);
      color: rgba(229,231,235,0.95);
    }
    .bar {
      display: flex;
      gap: 10px;
      padding: 14px;
      border-top: 1px solid rgba(148,163,184,0.12);
      background: rgba(2,6,23,0.35);
    }
    input {
      flex: 1;
      background: rgba(15,23,42,0.7);
      border: 1px solid rgba(148,163,184,0.18);
      border-radius: 12px;
      padding: 12px 12px;
      color: rgba(229,231,235,0.95);
      outline: none;
      font-size: 13px;
    }
    button {
      background: rgba(37,99,235,0.9);
      border: 1px solid rgba(37,99,235,0.45);
      color: white;
      padding: 12px 14px;
      border-radius: 12px;
      font-weight: 650;
      cursor: pointer;
      font-size: 13px;
    }
    button:disabled {
      opacity: 0.5;
      cursor: default;
    }
    .hint {
      font-size: 12px;
      color: rgba(229,231,235,0.55);
    }
  </style>
</head>
<body>
  <div id="glow" class="glow"></div>

  <div class="wrap">
    <div class="top">
      <div class="brand">
        <div class="badge">J</div>
        <div class="title">
          <h1>JARVIS</h1>
          <p class="hint">Local web UI</p>
        </div>
      </div>
      <div class="hint">http://127.0.0.1:8000</div>
    </div>

    <div class="card">
      <div id="messages" class="messages"></div>
      <div class="bar">
        <input id="input" placeholder="Type a message" autocomplete="off" />
        <button id="send">Send</button>
      </div>
    </div>
  </div>

  <script>
    const glow = document.getElementById('glow');
    document.addEventListener('mousemove', (e) => {
      glow.style.left = e.clientX + 'px';
      glow.style.top = e.clientY + 'px';
    });

    const messagesEl = document.getElementById('messages');
    const inputEl = document.getElementById('input');
    const sendBtn = document.getElementById('send');

    function add(role, text) {
      const row = document.createElement('div');
      row.className = 'row ' + role;

      const bubble = document.createElement('div');
      bubble.className = 'bubble ' + role;
      bubble.textContent = text;

      row.appendChild(bubble);
      messagesEl.appendChild(row);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    add('assistant', 'Sir, web interface ready.');

    async function send() {
      const text = (inputEl.value || '').trim();
      if (!text) return;
      inputEl.value = '';
      sendBtn.disabled = true;

      add('user', text);
      add('assistant', 'Working...');

      const last = messagesEl.lastChild;
      try {
        const res = await fetch('/api/chat', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({text})
        });
        const data = await res.json();
        last.querySelector('.bubble').textContent = data.reply || 'No reply.';
      } catch (e) {
        last.querySelector('.bubble').textContent = 'Backend error.';
      } finally {
        sendBtn.disabled = false;
        inputEl.focus();
      }
    }

    sendBtn.addEventListener('click', send);
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') send();
    });
  </script>
</body>
</html>
"""


@app.post("/api/chat")
def chat_api(payload: ChatIn) -> JSONResponse:
    text = (payload.text or "").strip()
    reply = orch.handle(text) if text else ""
    return JSONResponse({"reply": reply})
