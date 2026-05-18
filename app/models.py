"""
Database Models - Shared State Ledger

Implements the Blackboard/Shared State pattern.
All agent communication goes through these tables — no direct message passing.

Tables:
  - jobs: Top-level workflow tracking
  - agent_tasks: Per-agent sub-task state
  - workflow_logs: Complete audit trail
  - api_keys: API key management with audit trail
"""

import uuid
import hashlib
from datetime import datetime, timezone
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, Enum, ForeignKey, JSON, Index
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class JobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"
    AWAITING_INPUT = "awaiting_input"


class AgentRole(str, PyEnum):
    ORCHESTRATOR = "orchestrator"
    RESEARCH = "research"
    STRATEGY = "strategy"
    CRITIC = "critic"
    PLANNER = "planner"
    QA = "qa"
    MEMORY = "memory"
    SYSTEM = "system"


class TaskStatus(str, PyEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Job(Base):
    """
    Top-level workflow job.
    Created when a user submits a business prompt.
    """
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)

    # User input
    company_description = Column(Text, nullable=False)
    product_details = Column(Text, nullable=False)
    target_audience = Column(Text, nullable=False)
    goals = Column(Text, nullable=False)
    constraints = Column(Text, default="")
    raw_prompt = Column(Text, nullable=True)

    # Results
    final_report = Column(JSON, nullable=True)

    # Cost tracking
    total_tokens_used = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Version counter for optimistic locking
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    agent_tasks = relationship("AgentTask", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("WorkflowLog", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_status", "status"),
    )


class AgentTask(Base):
    """
    Per-agent sub-task within a job.
    Orchestrator creates these; agents claim, execute, and write results back.
    """
    __tablename__ = "agent_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    agent_role = Column(Enum(AgentRole), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.QUEUED, nullable=False)

    # Input/Output
    input_payload = Column(JSON, nullable=True)   # What the agent receives
    output_payload = Column(JSON, nullable=True)   # What the agent produces

    # Execution metadata
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    execution_time_ms = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Version for concurrency control
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    job = relationship("Job", back_populates="agent_tasks")

    __table_args__ = (
        Index("ix_agent_tasks_job_status", "job_id", "status"),
        Index("ix_agent_tasks_role", "agent_role"),
    )


class WorkflowLog(Base):
    """
    Complete audit trail for observability.
    Every agent action, LLM call, and state transition is logged here.
    
    Part of the Blackboard Pattern:
    - Agents write their decisions and reasoning here
    - Provides complete audit trail
    - Enables workflow visualization
    """
    __tablename__ = "workflow_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    agent_role = Column(Enum(AgentRole), nullable=True)
    level = Column(String(10), default="INFO")  # INFO, WARN, ERROR

    # Event details
    event_type = Column(String(50), nullable=False)  # e.g., "llm_call", "tool_execution", "state_transition"
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    job = relationship("Job", back_populates="logs")

    __table_args__ = (
        Index("ix_workflow_logs_job", "job_id"),
    )


class AgentMessage(Base):
    """
    Agent-to-Agent Communication via Blackboard Pattern.
    
    Agents write messages to the blackboard when they need help or want to share findings.
    Other agents read messages and respond by writing new messages.
    Orchestrator facilitates but doesn't block communication.
    
    Example Flow:
    1. Research agent writes: "Need pricing strategy guidance"
    2. Strategy agent reads message
    3. Strategy agent writes response: "Here's pricing recommendation..."
    4. Research agent reads response and continues
    
    This enables true agent collaboration while maintaining blackboard architecture.
    """
    __tablename__ = "agent_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    
    # Communication metadata
    from_agent = Column(Enum(AgentRole), nullable=False)
    to_agent = Column(Enum(AgentRole), nullable=True)  # None = broadcast to all
    message_type = Column(String(50), nullable=False)  # "request", "response", "broadcast", "notification"
    
    # Message content
    subject = Column(String(200), nullable=False)
    content = Column(JSON, nullable=False)  # Flexible structure for different message types
    
    # Response tracking
    in_response_to = Column(String(36), ForeignKey("agent_messages.id"), nullable=True)
    is_read = Column(Integer, default=0)  # 0 = unread, 1 = read
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job")
    parent_message = relationship("AgentMessage", remote_side=[id], backref="responses")

    __table_args__ = (
        Index("ix_agent_messages_job", "job_id"),
        Index("ix_agent_messages_to_agent_unread", "to_agent", "is_read"),
    )


class JobLearning(Base):
    """
    Learning from Past Executions.
    
    Stores patterns, strategies, and outcomes from completed jobs.
    Agents query this table to learn from past successes and failures.
    
    Example:
    - "For fitness app research, queries about 'competitor pricing' had 90% success rate"
    - "Strategy agent's 'freemium model' recommendation worked well for B2C products"
    
    This enables agents to improve over time by learning from historical data.
    """
    __tablename__ = "job_learnings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    
    # Learning metadata
    agent_role = Column(Enum(AgentRole), nullable=False)
    learning_type = Column(String(50), nullable=False)  # "strategy", "query_pattern", "tool_usage", "outcome"
    
    # Learning content
    pattern = Column(Text, nullable=False)  # What pattern was observed
    context = Column(JSON, nullable=False)  # Context in which it occurred
    outcome = Column(String(50), nullable=False)  # "success", "failure", "partial"
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Usage tracking
    times_applied = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    job = relationship("Job")

    __table_args__ = (
        Index("ix_job_learnings_agent_type", "agent_role", "learning_type"),
        Index("ix_job_learnings_confidence", "confidence_score"),
    )


class APIKey(Base):
    """
    API Key management with audit trail.
    
    Stores hashed API keys for authentication with metadata for tracking usage,
    rotation, and revocation. Enables scalable multi-tenant API access without
    requiring application restarts for key management.
    """
    __tablename__ = "api_keys"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)  # Human-readable name/description
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Integer, default=1, nullable=False)  # 1=active, 0=revoked
    
    __table_args__ = (
        Index("ix_api_keys_active", "is_active"),
    )

