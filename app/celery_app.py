"""
Celery App - Async Task Queue

Connects to Upstash Redis (rediss:// = TLS required by Upstash).
Workers pick up jobs and run the full orchestration pipeline.

Assignment requirement: Section C - Async Processing
  - Background jobs
  - Long-running tasks
  - Retry handling
  - Failure recovery
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "agent_in",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # Upstash Redis uses TLS — broker_use_ssl enables it for the connection
    broker_use_ssl={"ssl_cert_reqs": "none"} if settings.redis_url.startswith("rediss://") else None,
    redis_backend_use_ssl={"ssl_cert_reqs": "none"} if settings.redis_url.startswith("rediss://") else None,

    # Resilient Redis settings for Upstash/Serverless stability
    redis_socket_timeout=5.0,
    redis_socket_connect_timeout=5.0,
    broker_pool_limit=10,
    broker_connection_retry_on_startup=True,
    broker_transport_options={
        "socket_timeout": 5.0,
        "socket_connect_timeout": 5.0,
        "retry_on_timeout": True,
        "visibility_timeout": 3600,
    },

    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,          # Re-queue if worker dies before ack
    worker_prefetch_multiplier=1, # One task per worker at a time (AI tasks are heavy)

    # Retry policy — exponential backoff, max 3 attempts
    task_max_retries=3,
    task_default_retry_delay=10,  # seconds

    # Prevent silent task accumulation in the queue
    task_soft_time_limit=600,     # 10 min soft limit → raises SoftTimeLimitExceeded
    task_time_limit=660,          # 11 min hard limit → SIGKILL

    # Result expiry — keep results for 1 hour
    result_expires=3600,

    # Auto-discover tasks from app.tasks
    include=["app.tasks"],
)
