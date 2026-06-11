# NovaMart AI Refund Agent

An agentic refund-processing demo. An LLM agent (**NOVA**) handles customer refund requests, bound strictly by a written policy and backed by a **deterministic policy guard** the model cannot override. Every agent step (LLM call, tool call, guard check, injection detection) is streamed live to an admin trace panel over Server-Sent Events.

Built with FastAPI + raw Anthropic tool-calling (no LangGraph, no Docker) and a Vite/React frontend.

## Stack

| Layer | Tech |
|-------|------|
| Model | `Groq llama` |
| Backend | FastAPI · SQLite (aiosqlite) · sse-starlette |
| Frontend | React 18 · Vite · Tailwind CSS |
| Agent | Hand-rolled Anthropic tool-calling loop |

## Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key



| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## How it works

1. The agent receives a refund request and must call `lookup_order`, then `check_refund_eligibility` before any decision.
2. `check_refund_eligibility` runs `PolicyGuard` — a pure-Python rule engine evaluating all ten policy sections with priority `escalate > deny > approve`.
3. The agent **cannot** override the guard. If the guard denies, the agent denies; if it escalates, the agent escalates.
4. `create_refund_ticket` persists the resolution to SQLite.

Prompt-injection attempts, emotional appeals, threats, and authority claims are detected and logged, but never change the outcome — the policy is the sole source of truth.

## Test orders

| Order | Scenario | Expected |
|-------|----------|----------|
| ORD-001 | Normal, 10 days | Approve |
| ORD-002 | 35 days old | Deny §1 |
| ORD-003 | Final sale | Deny §2 |
| ORD-004 | Digital license | Deny §3 |
| ORD-005 | $649 order | Escalate §4 |
| ORD-007 | Defective item | Approve §5 |
| ORD-008 | Still in transit | Deny §7 |
| ORD-012 | Abuse history (3+ refunds) | Escalate §6 |

## Project layout

```
refund-agent/
├── data/                   policy, schema + seed, db init
├── backend/                FastAPI app, agent loop, policy guard, tools
└── frontend/               React UI (chat, admin trace, policy viewer)
```
