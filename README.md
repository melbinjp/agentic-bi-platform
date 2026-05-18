# 🌟 Agent_in — Hardened Agentic BI Platform

Repository: `agentic-bi-platform` | **Status: Production Hardened & Verified**

[![Build Status](https://img.shields.io/badge/Tests-93%20Passed-success?style=for-the-badge&logo=pytest)](https://github.com/)
[![Architecture](https://img.shields.io/badge/Architecture-Blackboard%20%2F%20Ledger-blue?style=for-the-badge)](./AGENTIC_CAPABILITIES.md)
[![Docker Support](https://img.shields.io/badge/Docker-100%25%20Sandboxed-blueviolet?style=for-the-badge&logo=docker)](./docker-compose.yml)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)

**Agent_in** is a state-of-the-art, production-hardened **autonomous multi-agent business intelligence platform** built on a true **Blackboard / Shared State Ledger** architecture. Unlike basic LLM wrappers that execute static, linear pipelines, Agent_in utilizes specialized autonomous capsules that coordinate, critique, self-assess, and refine their own execution paths.

---


## 🛡️ Production Hardening & Architectural Upgrades

During our strict production hardening phase, we resolved key agentic edge cases, securing the platform for high-stress business intelligence workloads:

### 1. Stateful Rolling-Window Summarizer (`stateful_summarize`)
To combat large context token-bloat and protect API token quotas (TPM/RPM limits), we built a modular, rolling-window MapReduce text compactor:
* **The Squeeze Problem**: Traditional bulk text slicing crashes models with `HTTP 413 Request Too Large` or triggers daily `HTTP 429 Rate Limit` errors.
* **Our Solution**: Automatically slices report texts into a maximum of 3 segments (safeguarding Requests Per Minute) and slides an accumulated facts sheet along with the next segment. Coreferences and narrative continuity are preserved without "blind spots."

### 2. Bounded Critic Iteration & Quality Gates
* **Air-Tight Rejections**: We eliminated the silent-pass loophole. If the Critic or QA Agent encounters parsing or model failures, it enforces a strict rejection verdict (`passed: False`, `overall_quality_score: 1`) rather than letting corrupted data slide.
* **Logical Consistency**: Rigorous safeguards ensure that any quality score below `7` automatically forces a `REJECTED` state, preventing contradictory logs.

### 3. Fail-Fast Model Routing & Circuit Breakers
* **Fast-Fail Exception Routing**: The model router distinguishes transient HTTP 429 rate limit errors from static HTTP 413 payload limit errors. It instantly bypasses futile retry delays and routes the request to fallback models.
* **Circuit Breakers**: If a specific LLM provider (e.g., Gemini) registers 3 consecutive network/rate failures, the system trips the breaker and routes downstream steps to Groq or OpenRouter variants dynamically.

### 4. 100% Sandboxed Local Compose Testing
* **The Security Isolation**: In the past, container instances read `.env` values and executed queries against public cloud Neon databases or Upstash Redis.
* **The Solution**: We hardened `docker-compose.yml` to override container environment contexts, strictly forcing `DATABASE_URL` and `REDIS_URL` to local Compose PostgreSQL and Redis services. Your local testing is blazingly fast, private, and 100% sandboxed. Only LLM inference and Tavily web scraping go external!

---

## 🏗️ Platform Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                 User Streamlit Web UI                  │
       └───────────────────────────┬────────────────────────────┘
                                   │ (REST API / SSE Streams)
       ┌───────────────────────────▼────────────────────────────┐
       │                   FastAPI Backend API                  │
       └───────────────────────────┬────────────────────────────┘
                                   │ (Async Workflows)
       ┌───────────────────────────▼────────────────────────────┐
       │              Celery Async Task Workers                 │
       └───────────────────────────┬────────────────────────────┘
                                   │ (Shared State Blackboard)
 ┌─────────────────────────────────┼─────────────────────────────────┐
 │               Persistent Shared Memory Ledger                     │
 │  ┌────────────────────────┐           ┌────────────────────────┐  │
 │  │    Local PostgreSQL    │◄─────────►│     Chroma Vector      │  │
 │  │     State Ledger       │           │      Store Memory      │  │
 │  └────────────────────────┘           └────────────────────────┘  │
 └─────────────────────────────────▲─────────────────────────────────┘
                                   │ (Autonomous Pull/Push)
 ┌─────────────────────────────────┴─────────────────────────────────┐
 │                     Autonomous Agent Capsules                     │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
 │  │ Orchestrator │  │   Research   │  │   Strategy   │             │
 │  └──────────────┘  └──────────────┘  └──────────────┘             │
 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
 │  │    Critic    │  │   Planner    │  │  QA Guard    │             │
 │  └──────────────┘  └──────────────┘  └──────────────┘             │
 └───────────────────────────────────────────────────────────────────┘
```

---

## 📁 Repository Structure

```text
alembic/                    Database migrations & schema version history
app/
  api/routes.py             FastAPI endpoints, CORS, & job streaming
  agents/                   Specialized autonomous agent capsules
    orchestrator.py         State ledger loop manager & dynamic retry router
    research.py             Tavily scraper & semantic information aggregator
    strategy.py             Target audience & marketing blueprint creator
    critic.py               Gaps reviewer & iterative prompt editor
    planner.py              30/60/90 execution roadmap compiler
    qa.py                   Final quality validator & safety check guard
  memory/vector_store.py    Chroma DB persistence and semantic cross-job recall
  config.py                 Pydantic env variable parser & runtime cost ceilings
  database.py               Asyncpg / synchronous SQL Alchemy transaction sessions
  llm_router.py             Task-complexity router, fail-fast circuit breakers
  observability.py          Structlog engine & unified Langfuse traces
  security.py               Doppler integration, prompt inject guard, permissions
frontend/
  app.py                    Streamlit premium UI dashboard
  design_system.py          Glassmomorphic CSS, alert systems, & custom metrics
tests/                      93 comprehensive unit & integration tests
docker-compose.yml          Sandboxed multi-container full-stack composition
render.yaml                 Automated hosted deployment configuration
```

---

## ⚙️ Environment Configuration

Create a `.env` file at the root directory from `.env.example`:

```env
# --- Required LLM Providers ---
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...

# --- Optional Web Search & Fallbacks ---
TAVILY_API_KEY=tvly-...
OPENROUTER_API_KEY=sk-...

# --- Local Defaults (Overridden automatically by docker-compose) ---
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_in
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/agent_in
DB_SSL_MODE=disable
REDIS_URL=redis://localhost:6379/0

# --- Optional Langfuse Observability Traces ---
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_BASE_URL=https://jp.cloud.langfuse.com
```

---

## 🚀 Running the Platform

### Option A: Local Docker (Recommended & 100% Sandboxed)

This is the fastest, cleanest environment setup. It spins up API, Worker, UI, private PostgreSQL, and private Redis instances automatically:

```bash
docker compose up --build
```

Access the premium local interfaces:
* **Streamlit UI Dashboard**: `http://localhost:8501`
* **Swagger API Documentation**: `http://localhost:8000/docs`
* **Local Backend API**: `http://localhost:8000`

### Option B: Local Running without Container Stack

To run locally outside of containers (using Python 3.12 virtual environment):

1. **Spin up sandboxed services** (PostgreSQL & Redis):
   ```bash
   docker compose up -d postgres redis
   ```
2. **Setup virtual environment & run migrations**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   python -m pip install -r requirements.txt
   alembic upgrade head
   ```
3. **Start API in Terminal 1**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
4. **Start Worker in Terminal 2**:
   ```bash
   celery -A app.celery_app.celery_app worker --loglevel=info -c 1
   ```
5. **Start UI in Terminal 3**:
   ```bash
   streamlit run frontend/app.py
   ```

---

## 🧪 Validating with the Test Suite

We maintain a rigorous test-driven codebase. The suite tests active agent decision chains, fallbacks, token calculations, and regression loops:

```bash
.venv\Scripts\python -m pytest -v -s --no-cov
```

**All 93 tests pass successfully with 0 failures, validating your platform with high confidence.**

---

## 💎 Key Production Design Principles

* **True Modularity**: Every agent operates as an isolated capsule executing a strict contract with the state ledger. They can be added, updated, or removed with zero edits to neighboring files.
* **Deterministic Circuit Breakers**: Protects against model failures without introducing untraceable logic loops.
* **Human-in-the-Loop Integration**: The orchestrator can dynamically pause jobs (status: `AWAITING_INPUT`) to collect clarifying goals from the user on the Streamlit dashboard, preventing wasted API costs on incomplete directives.
* **Micro-Cent Cost Observability**: Tracks input and output token consumption dynamically across fallback routing tables using LiteLLM pricing charts.

---
*Developed as a premium multi-agent Business Intelligence platform.*
