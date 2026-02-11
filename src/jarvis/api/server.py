from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="JARVIS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:24678",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    language: str = "pt"

class ChatResponse(BaseModel):
    ok: bool
    response: Optional[str] = None
    error: Optional[str] = None
    timestamp: str

orchestrator = None

@app.on_event("startup")
async def startup_event():
    global orchestrator
    try:
        from jarvis.core.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        print("JARVIS API: ready on http://127.0.0.1:8000")
    except Exception as e:
        orchestrator = None
        print(f"JARVIS API: orchestrator not loaded (demo mode): {e}")

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    try:
        if orchestrator is None:
            response_text = f"Sir, demo mode: '{request.message}'"
        else:
            if hasattr(orchestrator, "current_language"):
                if getattr(orchestrator, "current_language") != request.language:
                    setattr(orchestrator, "current_language", request.language)
            response_text = orchestrator.handle(request.message)

        return ChatResponse(
            ok=True,
            response=response_text,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "orchestrator_loaded": orchestrator is not None,
        "timestamp": datetime.now().isoformat(),
    }

def main():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
