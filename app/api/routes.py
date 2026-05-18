"""
API Routes - FastAPI Endpoints

Exposes:
  POST /analyze          → Submit a business analysis job
  GET  /status/{job_id}  → Poll job status and results
  POST /cancel/{job_id}  → Cancel a running job
  GET  /jobs             → List all jobs
  GET  /logs/{job_id}    → Get workflow logs for a job
  GET  /health           → Health check

Assignment requirement:
  - Present everything through APIs
  - Streaming responses (SSE endpoint)
  - Status dashboard data
  - Data isolation (per-job namespacing)
  - API authentication (optional, enabled via API_KEYS env var)
"""

import json
import asyncio
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Security
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.config import settings
from app.database import get_async_session
from app.models import Job, JobStatus, AgentTask, WorkflowLog, APIKey
from app.security import sanitize_user_input, api_rate_limiter
from app.tasks import execute_analysis, run_analysis
from app.celery_app import celery_app
from app.auth import get_current_user  # Import authentication

logger = structlog.get_logger()
router = APIRouter()


# ─── Request / Response Schemas ───────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    company_description: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    product_details: Optional[str] = Field(default=None, min_length=1, max_length=2000)
    target_audience: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    goals: Optional[str] = Field(default=None, min_length=1, max_length=1000)
    constraints: Optional[str] = Field(default="", max_length=500)
    prompt: Optional[str] = Field(default=None, min_length=10, max_length=5000)


class ClarifyRequest(BaseModel):
    answers: str = Field(..., min_length=5, max_length=5000)


class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    final_report: Optional[dict] = None
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/health")
async def health(db: AsyncSession = Depends(get_async_session)):
    """
    Comprehensive health check that verifies all critical dependencies.
    
    Returns:
    - 200 OK if all dependencies are healthy
    - 503 Service Unavailable if any dependency is unhealthy
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {}
    }
    
    # Check database connectivity
    try:
        await db.execute(select(1))
        health_status["checks"]["database"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
    
    # Check Redis connectivity
    try:
        from app.celery_app import celery_app
        # Try to ping Redis through Celery
        celery_app.backend.client.ping()
        health_status["checks"]["redis"] = {"status": "healthy", "message": "Connected"}
    except Exception as e:
        if not settings.run_jobs_inline:
            health_status["status"] = "unhealthy"
            health_status["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
        else:
            # Under inline execution, redis is non-blocking for core workflows
            health_status["checks"]["redis"] = {
                "status": "degraded",
                "message": f"Non-blocking connection failure in inline mode: {str(e)}"
            }
    
    # Check LLM providers (basic check - just verify keys are configured)
    llm_checks = {}
    if settings.gemini_api_key:
        llm_checks["gemini"] = "configured"
    if settings.groq_api_key:
        llm_checks["groq"] = "configured"
    if settings.openrouter_api_key:
        llm_checks["openrouter"] = "configured"
    
    health_status["checks"]["llm_providers"] = {
        "status": "healthy" if llm_checks else "unhealthy",
        "providers": llm_checks
    }
    
    # Return appropriate status code
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(content=health_status, status_code=status_code)


@router.post("/analyze", response_model=JobResponse, status_code=202)
async def submit_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    body: AnalysisRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),  # Add authentication
):
    """
    Submit a business analysis job.
    Returns immediately with job_id — analysis runs in background via Celery.
    
    Authentication:
    - Requires X-API-Key header if API_KEYS is configured
    - If API_KEYS is empty (development mode), no authentication required
    """
    # Rate limiting (now per-user if authenticated)
    user_id = current_user.get("user_id", "anonymous")
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"{user_id}:{client_ip}"
    
    if not await api_rate_limiter.is_allowed(rate_limit_key):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Max 5 requests per minute.")

    # Prompt injection protection on all user inputs
    try:
        if body.prompt:
            company = sanitize_user_input(body.prompt, "prompt")
            product = "PENDING_EXTRACTION"
            audience = "PENDING_EXTRACTION"
            goals = "PENDING_EXTRACTION"
            constraints = ""
            raw_prompt = company
        else:
            if not all([body.company_description, body.product_details, body.target_audience, body.goals]):
                raise HTTPException(status_code=400, detail="Missing required business details or 'prompt'")
                
            company = sanitize_user_input(body.company_description or "", "company_description")
            product = sanitize_user_input(body.product_details or "", "product_details")
            audience = sanitize_user_input(body.target_audience or "", "target_audience")
            goals = sanitize_user_input(body.goals or "", "goals")
            constraints = sanitize_user_input(body.constraints or "", "constraints")
            raw_prompt = None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create job record
    job = Job(
        company_description=company,
        product_details=product,
        target_audience=audience,
        goals=goals,
        constraints=constraints,
        raw_prompt=raw_prompt,
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Dispatch to Celery, or use FastAPI's background runner for free hosted demos.
    if settings.run_jobs_inline:
        background_tasks.add_task(execute_analysis, job.id)
    else:
        run_analysis.delay(job_id=job.id)

    logger.info("job_submitted", job_id=job.id, client=client_ip)
    return JobResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("/status/{job_id}", response_model=JobResponse)
async def get_status(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Poll job status. Returns final_report when completed."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(
        job_id=job.id,
        status=job.status,
        created_at=job.created_at,
        final_report=job.final_report,
        total_tokens_used=job.total_tokens_used,
        total_cost_usd=job.total_cost_usd,
    )


@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """
    Cancel a running job.
    Revokes the Celery task and marks the job as ABORTED in the DB.
    The Orchestrator's cancellation check will stop execution cleanly.
    """
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in (JobStatus.PENDING, JobStatus.RUNNING):
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in status: {job.status}")

    # Mark as aborted — Orchestrator polls this on every step
    job.status = JobStatus.ABORTED
    job.completed_at = datetime.now(timezone.utc)
    await db.commit()

    # Revoke from Celery queue (terminate if already running)
    celery_app.control.revoke(job_id, terminate=True, signal="SIGTERM")

    logger.info("job_cancelled", job_id=job_id)
    return {"job_id": job_id, "status": "aborted"}


@router.get("/jobs")
async def list_jobs(
    limit: int = 20,
    db: AsyncSession = Depends(get_async_session),
):
    """List recent jobs for the status dashboard."""
    result = await db.execute(
        select(Job).order_by(desc(Job.created_at)).limit(limit)
    )
    jobs = result.scalars().all()
    return [
        {
            "job_id": j.id,
            "status": j.status,
            "created_at": j.created_at,
            "completed_at": j.completed_at,
            "company": j.company_description[:60],
            "total_cost_usd": j.total_cost_usd,
        }
        for j in jobs
    ]


@router.get("/logs/{job_id}")
async def get_logs(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Get all workflow log events for a job (for the frontend logs panel)."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(
        select(WorkflowLog)
        .where(WorkflowLog.job_id == job_id)
        .order_by(WorkflowLog.created_at)
    )
    logs = result.scalars().all()
    return [
        {
            "agent": log.agent_role,
            "level": log.level,
            "event_type": log.event_type,
            "message": log.message,
            "details": log.details,
            "timestamp": log.created_at,
        }
        for log in logs
    ]


@router.get("/agents/{job_id}")
async def get_agent_tasks(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Get agent task statuses for the execution timeline view."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    result = await db.execute(
        select(AgentTask)
        .where(AgentTask.job_id == job_id)
        .order_by(AgentTask.created_at)
    )
    tasks = result.scalars().all()
    return [
        {
            "agent": task.agent_role,
            "status": task.status,
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "model_used": task.model_used,
            "tokens_used": task.tokens_used,
            "execution_time_ms": task.execution_time_ms,
            "cost_usd": task.cost_usd,
            "error_message": task.error_message,
        }
        for task in tasks
    ]


@router.get("/stream/{job_id}")
async def stream_logs(job_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time log streaming.
    Frontend connects once and receives events as agents complete.
    """
    async def event_generator():
        seen_ids = set()
        max_polls = 300  # 5 min max stream

        for _ in range(max_polls):
            # Dynamically open and close database session for each query chunk
            from app.database import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                job = await db.get(Job, job_id)
                if not job:
                    yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                    break

                result = await db.execute(
                    select(WorkflowLog)
                    .where(WorkflowLog.job_id == job_id)
                    .order_by(WorkflowLog.created_at)
                )
                logs = result.scalars().all()

                for log in logs:
                    if log.id not in seen_ids:
                        seen_ids.add(log.id)
                        payload = {
                            "type": "log",
                            "agent": log.agent_role,
                            "event": log.event_type,
                            "message": log.message,
                            "timestamp": log.created_at.isoformat(),
                        }
                        yield f"data: {json.dumps(payload)}\n\n"

                if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.ABORTED):
                    yield f"data: {json.dumps({'type': 'done', 'status': job.status})}\n\n"
                    break

            # Sleep outside of the session context to release connection to the pool
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ─── API Key Management Endpoints ─────────────────────────────────────────────

class CreateAPIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable name for the API key")


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: Optional[str] = None  # Only returned on creation
    created_at: datetime
    last_used_at: Optional[datetime] = None
    is_active: bool


@router.post("/admin/api-keys", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    body: CreateAPIKeyRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new API key.
    
    Returns the plaintext key only once - it cannot be retrieved later.
    The key is stored as a SHA-256 hash in the database.
    """
    # Generate a secure random API key
    api_key = f"sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create database record
    new_key = APIKey(
        key_hash=key_hash,
        name=body.name,
        is_active=1,
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)
    
    logger.info("api_key_created", key_id=new_key.id, name=new_key.name, created_by=current_user.get("user_id"))
    
    return APIKeyResponse(
        id=new_key.id,
        name=new_key.name,
        key=api_key,  # Only returned on creation
        created_at=new_key.created_at,
        last_used_at=new_key.last_used_at,
        is_active=bool(new_key.is_active),
    )


@router.get("/admin/api-keys", response_model=list[APIKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
):
    """List all API keys (without plaintext keys)."""
    result = await db.execute(select(APIKey).order_by(desc(APIKey.created_at)))
    keys = result.scalars().all()
    
    return [
        APIKeyResponse(
            id=k.id,
            name=k.name,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            is_active=bool(k.is_active),
        )
        for k in keys
    ]


@router.delete("/admin/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user),
):
    """Revoke an API key (soft delete - sets is_active to 0)."""
    key = await db.get(APIKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    
    key.is_active = 0
    await db.commit()
    
    logger.info("api_key_revoked", key_id=key_id, name=key.name, revoked_by=current_user.get("user_id"))
    
    return {"key_id": key_id, "status": "revoked"}
