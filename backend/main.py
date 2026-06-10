import asyncio
import json
import time
from contextlib import asynccontextmanager
from typing import Optional

import aiosqlite
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

import database
from agent import SessionState, run_agent_turn, _now_iso
from config import get_settings

log = structlog.get_logger("nova.main")
settings = get_settings()

SESSIONS: dict[str, SessionState] = {}
QUEUES: dict[str, asyncio.Queue] = {}
RATE: dict[str, list[float]] = {}

MAX_SESSIONS = 100
RATE_LIMIT = 30
RATE_WINDOW = 60.0


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        policy_len = len(settings.get_policy_text())
    except Exception as e:
        policy_len = 0
        log.error("policy_load_failed", error=str(e))
    log.info("startup", model=settings.model_name, policy_chars=policy_len)
    yield
    log.info("shutdown")


app = FastAPI(title="NovaMart AI Refund Agent", version="2.0", lifespan=lifespan)

origins = ["*"] if settings.allow_all_origins else ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False if origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    customer_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    final_decision: Optional[str] = None
    trace_count: int


def _evict_if_needed() -> None:
    if len(SESSIONS) <= MAX_SESSIONS:
        return
    oldest = sorted(SESSIONS.values(), key=lambda s: s.last_active)
    for s in oldest[: len(SESSIONS) - MAX_SESSIONS]:
        SESSIONS.pop(s.session_id, None)
        QUEUES.pop(s.session_id, None)


def _check_rate_limit(session_id: str) -> bool:
    now = time.monotonic()
    bucket = [t for t in RATE.get(session_id, []) if now - t < RATE_WINDOW]
    if len(bucket) >= RATE_LIMIT:
        RATE[session_id] = bucket
        return False
    bucket.append(now)
    RATE[session_id] = bucket
    return True


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message must not be empty.")
    if len(message) > 2000:
        message = message[:2000]

    if not _check_rate_limit(req.session_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    session = SESSIONS.get(req.session_id)
    if session is None:
        now = _now_iso()
        session = SessionState(
            session_id=req.session_id, created_at=now, last_active=now
        )
        SESSIONS[req.session_id] = session
        _evict_if_needed()

    if req.customer_id and not session.customer_id:
        session.customer_id = req.customer_id

    async def trace_cb(step) -> None:
        session.trace.append(step)
        q = QUEUES.get(req.session_id)
        if q is not None:
            await q.put(step.model_dump())

    reply, decision = await run_agent_turn(session, message, trace_cb)
    session.last_active = _now_iso()

    return ChatResponse(
        session_id=req.session_id,
        reply=reply,
        final_decision=decision,
        trace_count=len(session.trace),
    )


@app.get("/api/trace/{session_id}")
async def get_trace(session_id: str):
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return [step.model_dump() for step in session.trace]


@app.get("/api/trace-stream/{session_id}")
async def trace_stream(session_id: str, request: Request):
    queue: asyncio.Queue = QUEUES.setdefault(session_id, asyncio.Queue())

    async def event_generator():
        try:
            session = SESSIONS.get(session_id)
            if session is not None:
                for step in session.trace:
                    yield {"data": json.dumps(step.model_dump())}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    step = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"data": json.dumps(step)}
                except asyncio.TimeoutError:
                    continue
        finally:
            QUEUES.pop(session_id, None)

    return EventSourceResponse(event_generator(), ping=15)


@app.get("/api/sessions")
async def list_sessions():
    summaries = []
    for s in sorted(SESSIONS.values(), key=lambda x: x.last_active, reverse=True):
        summaries.append(
            {
                "session_id": s.session_id,
                "customer_id": s.customer_id,
                "created_at": s.created_at,
                "last_active": s.last_active,
                "message_count": len([m for m in s.messages if m.get("role") == "user" and isinstance(m.get("content"), str)]),
                "final_decision": s.final_decision,
                "trace_count": len(s.trace),
            }
        )
    return summaries


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    SESSIONS.pop(session_id, None)
    QUEUES.pop(session_id, None)
    RATE.pop(session_id, None)
    return {"deleted": True}


@app.get("/api/policy")
async def get_policy():
    return {"text": settings.get_policy_text()}


@app.get("/api/tickets")
async def get_tickets():
    return await database.get_all_refund_requests()


@app.get("/health")
async def health():
    db_status = "connected"
    try:
        async with aiosqlite.connect(database.DB_PATH) as db:
            async with db.execute("SELECT 1") as cur:
                await cur.fetchone()
    except Exception:
        db_status = "error"
    return {
        "status": "ok",
        "model": settings.model_name,
        "db": db_status,
        "active_sessions": len(SESSIONS),
    }


@app.get("/api/metrics")
async def metrics():
    total_sessions = len(SESSIONS)
    approved = denied = escalated = 0
    total_decisions = 0
    latencies: list[float] = []
    total_tokens = 0
    injection_attempts = 0

    for s in SESSIONS.values():
        if s.final_decision == "approved":
            approved += 1
            total_decisions += 1
        elif s.final_decision == "denied":
            denied += 1
            total_decisions += 1
        elif s.final_decision == "escalated_human":
            escalated += 1
            total_decisions += 1
        for step in s.trace:
            if step.latency_ms:
                latencies.append(step.latency_ms)
            if step.llm_input_tokens:
                total_tokens += step.llm_input_tokens
            if step.llm_output_tokens:
                total_tokens += step.llm_output_tokens
            if step.step_type == "injection_detected":
                injection_attempts += 1

    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0.0
    avg_tokens = round(total_tokens / total_sessions, 1) if total_sessions else 0.0

    return {
        "total_sessions": total_sessions,
        "total_decisions": total_decisions,
        "approved": approved,
        "denied": denied,
        "escalated": escalated,
        "avg_latency_ms": avg_latency,
        "avg_tokens_per_session": avg_tokens,
        "injection_attempts_detected": injection_attempts,
    }
