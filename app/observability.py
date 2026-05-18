"""
Observability - Langfuse + Structured Logging

Sets up:
  - Langfuse client for LLM tracing (traces, spans, token costs)
  - structlog for structured JSON logging across all modules

Assignment requirement: Section D - Observability
  - Agent tracing
  - Prompt logging
  - Token tracking
  - Error tracking
  - Latency monitoring
  - Workflow visualization (via Langfuse trace tree)
"""

import logging
import structlog
from typing import Optional
from langfuse import Langfuse

from app.config import settings


# ─── Structured Logging Setup ────────────────────────────────────────────────

def configure_logging():
    """Configure structlog for structured JSON output."""
    log_level = getattr(logging, settings.log_level.upper(), logging.DEBUG)

    logging.basicConfig(
        format="%(message)s",
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )


# ─── Langfuse Client ─────────────────────────────────────────────────────────

def get_langfuse() -> Optional[Langfuse]:
    """
    Return a Langfuse client if credentials are configured.
    Returns None (silently) if not configured — system still runs without tracing.
    """
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
    return Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )


# Singleton — one client for the process lifetime
_langfuse: Optional[Langfuse] = None


def get_tracer() -> Optional[Langfuse]:
    global _langfuse
    if _langfuse is None:
        _langfuse = get_langfuse()
    return _langfuse


class TraceContext:
    """
    Context manager for a single job's Langfuse trace.

    Usage:
        async with TraceContext(job_id, "orchestrator_run") as ctx:
            span = ctx.span("research_agent")
            ...
            span.end()
    """

    def __init__(self, job_id: str, name: str, metadata: Optional[dict] = None):
        self.job_id = job_id
        self.name = name
        self.metadata = metadata or {}
        self._trace = None
        self._lf = get_tracer()

    def __enter__(self):
        if self._lf and hasattr(self._lf, "trace"):
            self._trace = self._lf.trace(
                id=self.job_id,
                name=self.name,
                metadata=self.metadata,
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._lf:
            self._lf.flush()

    def span(self, name: str, input_data: Optional[dict] = None):
        """Create a child span within this trace."""
        if self._trace:
            return self._trace.span(name=name, input=input_data or {})
        return _NoopSpan()

    def generation(
        self,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        input_tokens: int,
        output_tokens: int,
    ):
        """Log an LLM generation with full token details."""
        if self._trace and hasattr(self._trace, "generation"):
            self._trace.generation(
                name=name,
                model=model,
                input=prompt,
                output=completion,
                usage={
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                },
            )


class _NoopSpan:
    """Fallback span when Langfuse is not configured — all methods are no-ops."""
    def end(self, output=None, **kwargs): pass
    def update(self, **kwargs): pass

# --- Workflow Logging for Real-time Feedback ---

def log_workflow_event(job_id: str, agent: str, message: str, event_type: str = "info", level: str = "INFO", details: Optional[dict] = None):
    """
    Directly insert a log entry into the WorkflowLog table.
    Used for non-intrusive messaging during agent execution (e.g. fallback notifications).
    """
    from app.database import sync_engine as engine
    from app.models import WorkflowLog, AgentRole
    from sqlalchemy.orm import Session

    # Map the agent string to AgentRole enum members
    role = None
    if agent:
        try:
            role = AgentRole(agent.lower())
        except ValueError:
            role = AgentRole.SYSTEM

    try:
        with Session(engine) as session:
            log = WorkflowLog(
                job_id=job_id,
                agent_role=role,
                level=level,
                event_type=event_type,
                message=message,
                details=details or {}
            )
            session.add(log)
            session.commit()
    except Exception as e:
        # Fallback to standard logging if DB write fails
        structlog.get_logger().error("workflow_log_failed", error=str(e), job_id=job_id)

class WorkflowLogger:
    def info(self, job_id: str, agent: str, message: str, details: Optional[dict] = None):
        log_workflow_event(job_id, agent, message, "info", "INFO", details)
    
    def warning(self, job_id: str, agent: str, message: str, details: Optional[dict] = None):
        log_workflow_event(job_id, agent, message, "warning", "WARNING", details)

    def error(self, job_id: str, agent: str, message: str, details: Optional[dict] = None):
        log_workflow_event(job_id, agent, message, "error", "ERROR", details)

# Real workflow logger instance
workflow_logger = WorkflowLogger()

