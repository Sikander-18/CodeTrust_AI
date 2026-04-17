"""
FastAPI backend for Agentic Trust Laboratory.

Endpoints:
  POST /api/generate  —  SSE stream of pipeline events
  GET  /health        —  Health check

Run from the project ROOT:
  uvicorn backend.main:app --reload --port 8000

Or from inside backend/:
  uvicorn main:app --reload --port 8000
"""
import json
import sys
import os

# ── Make backend/ the Python path root so all sibling imports resolve ─
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from orchestrator import Orchestrator


app = FastAPI(
    title="Agentic Trust Laboratory API",
    description="SSE streaming backend for the multi-agent code verification system.",
    version="1.0.0",
)

# Allow all origins in dev (React dev server on :5173, or file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    problem: str
    max_retries: int = 3


@app.post("/api/generate")
async def generate_stream(request: GenerateRequest):
    """
    SSE endpoint that streams pipeline events to the browser.
    Each event is a JSON object sent in the SSE data field.

    Event schema:
      data: {"type": "log",       "agent": "...", "message": "...", "timestamp": "..."}
      data: {"type": "progress",  "iteration": 1, "max_retries": 3, "step": "architect"}
      data: {"type": "code",      "content": "..."}
      data: {"type": "tests",     "content": "..."}
      data: {"type": "execution", "stdout": "...", "stderr": "..."}
      data: {"type": "metrics",   "data": {"passed": 6, "total": 8, ...}}
      data: {"type": "report",    "data": {...EvaluationReport fields...}}
      data: {"type": "done",      "result": {...full result dict...}}
      data: {"type": "error",     "message": "..."}
    """
    def event_stream():
        orch = Orchestrator()
        try:
            for event in orch.run_pipeline_stream(
                request.problem, max_retries=request.max_retries
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "message": f"Pipeline crashed: {str(e)}"}
            yield f"data: {json.dumps(error_event)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'result': None})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
            "Connection": "keep-alive",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Agentic Trust Laboratory", "version": "1.0.0"}
