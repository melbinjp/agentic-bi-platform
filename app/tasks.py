"""
Background Job Execution

The project supports two execution modes:
  - Celery worker mode for full async infrastructure.
  - FastAPI background-task mode for zero-cost hosted demos.
"""

import asyncio
from datetime import datetime, timezone

import structlog
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.database import get_sync_session
from app.models import Job, JobStatus

logger = structlog.get_logger()


class OrchestratorTask(Task):
    """Custom Celery task base with failure hooks."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get("job_id") or (args[0] if args else None)
        if job_id:
            _mark_failed(job_id, str(exc))


def _mark_failed(job_id: str, error: str):
    db = get_sync_session()
    try:
        job = db.get(Job, job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.error("task_failed_updating_db", job_id=job_id, error=error)
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=OrchestratorTask,
    name="app.tasks.run_analysis",
    max_retries=3,
    default_retry_delay=10,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    acks_late=True,
)
def run_analysis(self, job_id: str):
    """
    Celery task wrapper for the full multi-agent analysis pipeline.
    
    Retry Configuration:
    - max_retries=3: Retry up to 3 times on failure
    - autoretry_for=(Exception,): Automatically retry on any exception
    - retry_backoff=True: Use exponential backoff (10s, 20s, 40s, ...)
    - retry_backoff_max=600: Cap backoff at 10 minutes
    - retry_jitter=True: Add randomness to prevent thundering herd
    - acks_late=True: Only acknowledge after completion (prevents message loss)
    """
    return execute_analysis(job_id, task_context=self)


def execute_analysis(job_id: str, task_context=None):
    """
    Execute the full multi-agent analysis pipeline.

    `task_context` is supplied by Celery. When omitted, this runs as a normal
    sync function, which is useful for FastAPI BackgroundTasks on Render Free.
    """
    db = get_sync_session()
    try:
        job = db.get(Job, job_id)
        if not job:
            logger.error("task_job_not_found", job_id=job_id)
            return {"error": "Job not found"}

        if job.status in (JobStatus.COMPLETED, JobStatus.ABORTED):
            logger.info("task_already_done_skipping", job_id=job_id, status=job.status)
            return {"skipped": True, "status": job.status}

        retries = getattr(getattr(task_context, "request", None), "retries", 0)
        if job.status == JobStatus.FAILED and retries == 0:
            job.status = JobStatus.PENDING
            db.commit()

        from app.agents.orchestrator import run as orchestrate

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(orchestrate(job_id, db))
        finally:
            loop.close()

        logger.info("task_completed", job_id=job_id)
        return result

    except SoftTimeLimitExceeded:
        logger.error("task_soft_time_limit", job_id=job_id)
        job = db.get(Job, job_id)
        if job:
            job.status = JobStatus.FAILED
            db.commit()
        return {"error": "Task exceeded time limit"}

    except Exception as exc:
        logger.error("task_exception", job_id=job_id, error=str(exc))
        if task_context is not None:
            try:
                raise task_context.retry(exc=exc)
            except task_context.MaxRetriesExceededError:
                pass

        job = db.get(Job, job_id)
        if job:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
        return {"error": f"Analysis failed: {exc}"}

    finally:
        db.close()
