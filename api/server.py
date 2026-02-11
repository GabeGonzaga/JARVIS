"""
JARVIS FastAPI Backend Server
Handles requests from the web interface
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="JARVIS API",
    version="1.0.0",
    description="Backend API for JARVIS AI Assistant"
)

# CORS configuration for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:24678",  # Nuxt dev server alternative port
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


# Global orchestrator instance
orchestrator = None


@app.on_event("startup")
async def startup_event():
    """Initialize JARVIS orchestrator on startup."""
    global orchestrator
    try:
        from jarvis.core.orchestrator import Orchestrator
        orchestrator = Orchestrator()
        print("🤖 JARVIS API Server started successfully")
        print("📡 Listening on http://0.0.0.0:8000")
        print("🌐 CORS enabled for web interface")
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize orchestrator: {e}")
        print("   API will run in demo mode")


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Handle chat requests from the web interface.
    
    Args:
        request: ChatRequest with message and language
        
    Returns:
        ChatResponse with the assistant's response
    """
    try:
        if orchestrator is None:
            # Demo mode response
            response_text = f"Sir, I received your message in {request.language}: '{request.message}'"
        else:
            # Set language if different
            if orchestrator.current_language != request.language:
                orchestrator.current_language = request.language
            
            # Process message through orchestrator
            response_text = orchestrator.handle(request.message)
        
        return ChatResponse(
            ok=True,
            response=response_text,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "JARVIS API",
        "version": "1.0.0",
        "orchestrator_loaded": orchestrator is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/languages")
async def get_languages():
    """Get supported languages."""
    return {
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "pt", "name": "Português (Portugal)"},
            {"code": "es", "name": "Español"},
            {"code": "fr", "name": "Français"}
        ],
        "default": "pt"
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "JARVIS API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "POST /api/chat",
            "health": "GET /api/health",
            "languages": "GET /api/languages"
        }
    }


def main():
    """Run the FastAPI server."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
