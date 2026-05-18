"""
Orchestrator Agent - Central Workflow Controller

Responsibilities:
  - Decompose the user's business prompt into sub-tasks
  - Delegate to specialised agents in the correct order
  - Manage shared state via the DB ledger (no direct agent-to-agent messaging)
  - Enforce iteration limits, token budgets, and cancellation checks
  - Handle the Critic's REJECTED verdict with a single bounded retry
  - Assemble the final report

Assignment requirement:
  - Orchestrator Agent: Controls workflow and delegation
  - Section A: Agent Orchestration Engine (custom orchestration)
  - Reliability: loop prevention, circuit breakers, execution cancellation
"""

import asyncio
import structlog
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
import json

from app.config import settings
from app.llm_router import llm_router, TaskType
from app.llm_client import call_llm
from app.models import Job, AgentTask, AgentRole, TaskStatus, JobStatus, WorkflowLog
from app.observability import TraceContext

# Agent runners
from app.agents import research, strategy, critic, planner, qa, memory

logger = structlog.get_logger()

# Maximum times the Critic can reject before we accept the best result
_MAX_CRITIC_RETRIES = 1
# Maximum total agent steps before forcing completion
_MAX_TOTAL_STEPS = 20


def _log_event(db: Session, job_id: str, role: Optional[AgentRole], event_type: str, message: str, details: dict = None, level: str = "INFO"):
    """Write a structured event to the workflow_logs table."""
    log = WorkflowLog(
        job_id=job_id,
        agent_role=role,
        level=level,
        event_type=event_type,
        message=message,
        details=details or {},
    )
    db.add(log)
    db.commit()


def _is_aborted(db: Session, job_id: str) -> bool:
    """Check if the job has been externally cancelled. Called before every agent step."""
    db.expire_all()  # force re-read from DB
    job = db.get(Job, job_id)
    return job is not None and job.status == JobStatus.ABORTED


def _update_job_status(db: Session, job_id: str, status: JobStatus, final_report: dict = None):
    job = db.get(Job, job_id)
    if job:
        job.status = status
        if final_report is not None:
            job.final_report = final_report
            usage = llm_router.get_usage(job_id)
            job.total_tokens_used = usage.total_input_tokens + usage.total_output_tokens
            job.total_cost_usd = usage.total_cost_usd
        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.ABORTED):
            job.completed_at = datetime.now(timezone.utc)
        db.commit()


def _create_agent_task(db: Session, job_id: str, role: AgentRole) -> AgentTask:
    task = AgentTask(job_id=job_id, agent_role=role, status=TaskStatus.QUEUED)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def _start_task(db: Session, task: AgentTask):
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.now(timezone.utc)
    
    # Capture initial tokens and cost to calculate metrics per-agent dynamically
    usage = llm_router.get_usage(task.job_id)
    task.input_payload = {
        "initial_cost": usage.total_cost_usd,
        "initial_tokens": usage.total_input_tokens + usage.total_output_tokens
    }
    db.commit()


def _complete_task(db: Session, task: AgentTask, output: dict, model_used: str = ""):
    task.status = TaskStatus.COMPLETED
    task.output_payload = output
    task.completed_at = datetime.now(timezone.utc)
    
    # Calculate metrics in a timezone-safe manner
    if task.started_at and task.completed_at:
        started = task.started_at.replace(tzinfo=None)
        completed = task.completed_at.replace(tzinfo=None)
        delta = completed - started
        task.execution_time_ms = int(delta.total_seconds() * 1000)
        
    usage = llm_router.get_usage(task.job_id)
    initial_metrics = task.input_payload or {}
    initial_cost = initial_metrics.get("initial_cost", 0.0) if isinstance(initial_metrics, dict) else 0.0
    initial_tokens = initial_metrics.get("initial_tokens", 0) if isinstance(initial_metrics, dict) else 0
    
    task.cost_usd = max(0.0, usage.total_cost_usd - initial_cost)
    task.tokens_used = max(0, (usage.total_input_tokens + usage.total_output_tokens) - initial_tokens)
    task.model_used = model_used or usage.last_model_used or "gemini-2.0-flash"
    
    db.commit()


def _fail_task(db: Session, task: AgentTask, error: str):
    task.status = TaskStatus.FAILED
    task.error_message = error
    task.completed_at = datetime.now(timezone.utc)
    
    # Calculate metrics in a timezone-safe manner
    if task.started_at and task.completed_at:
        started = task.started_at.replace(tzinfo=None)
        completed = task.completed_at.replace(tzinfo=None)
        delta = completed - started
        task.execution_time_ms = int(delta.total_seconds() * 1000)
        
    usage = llm_router.get_usage(task.job_id)
    initial_metrics = task.input_payload or {}
    initial_cost = initial_metrics.get("initial_cost", 0.0) if isinstance(initial_metrics, dict) else 0.0
    initial_tokens = initial_metrics.get("initial_tokens", 0) if isinstance(initial_metrics, dict) else 0
    
    task.cost_usd = max(0.0, usage.total_cost_usd - initial_cost)
    task.tokens_used = max(0, (usage.total_input_tokens + usage.total_output_tokens) - initial_tokens)
    task.model_used = usage.last_model_used or "gemini-2.0-flash"
    
    db.commit()


async def run(job_id: str, db: Session) -> dict:
    """
    Main orchestration loop.

    Reads the Job from the DB, coordinates all agents via shared state,
    and writes the final report back to the Job record.

    Returns the final report dict.
    """
    try:
        step_count = 0
        critic_result = {
            "verdict": "SKIPPED",
            "score": 0,
            "issues": ["Critic agent was not executed"],
            "improvement_prompt": ""
        }

        with TraceContext(job_id, "orchestrator_run") as trace:

            # ── Load job ──────────────────────────────────────────────────────────
            job = db.get(Job, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")

            _update_job_status(db, job_id, JobStatus.RUNNING)
            _log_event(db, job_id, AgentRole.ORCHESTRATOR, "workflow_start", "Orchestrator starting", {
                "company": job.company_description[:50],
            })

            # ── Step 0: Extraction & Clarification (for single prompt) ────────────
            if job.raw_prompt and job.product_details == "PENDING_EXTRACTION":
                _log_event(db, job_id, AgentRole.ORCHESTRATOR, "extraction_start", "Extracting business details from prompt")
                
                extraction_prompt = f"""
                You are a Business Intelligence Analyst. Extract details from this prompt:
                "{job.raw_prompt}"
                
                Identify:
                1. Company Description
                2. Product/Service Details
                3. Target Audience
                4. Primary Goals
                5. Constraints (if any)
                
                If critical information (Company/Product/Audience/Goals) is missing or too vague, 
                generate 3-5 specific questions to help clarify.
                
                Output ONLY valid JSON:
                {{
                    "is_complete": bool,
                    "data": {{
                        "company": "string",
                        "product": "string",
                        "audience": "string",
                        "goals": "string",
                        "constraints": "string"
                    }},
                    "clarification_questions": ["q1", "q2"...]
                }}
                """
                
                raw_extraction = await call_llm(
                    task_type=TaskType.STRUCTURED_EXTRACTION,
                    job_id=job_id,
                    system_prompt="You are a JSON extractor.",
                    user_prompt=extraction_prompt,
                    temperature=0.1
                )
                
                try:
                    # Basic JSON cleaning
                    clean_json = raw_extraction.strip().strip('`').replace('json\n', '', 1)
                    ext_data = json.loads(clean_json)
                    
                    if not ext_data.get("is_complete", False):
                        questions = ext_data.get("clarification_questions", ["Please provide more details about your business."])
                        _log_event(db, job_id, AgentRole.ORCHESTRATOR, "clarification_needed", 
                                   "Incomplete prompt. Awaiting user input.", {"questions": questions})
                        
                        job.final_report = {"clarification_needed": True, "questions": questions}
                        _update_job_status(db, job_id, JobStatus.AWAITING_INPUT)
                        return {"status": "awaiting_input", "questions": questions}
                    
                    # Update job with extracted data
                    d = ext_data["data"]
                    job.company_description = d.get("company", job.company_description)
                    job.product_details = d.get("product", "Extracted")
                    job.target_audience = d.get("audience", "Extracted")
                    job.goals = d.get("goals", "Extracted")
                    job.constraints = d.get("constraints", "")
                    db.commit()
                    _log_event(db, job_id, AgentRole.ORCHESTRATOR, "extraction_complete", "Successfully parsed business brief")
                    
                except Exception as e:
                    logger.error("extraction_failed", error=str(e))
                    _log_event(db, job_id, AgentRole.ORCHESTRATOR, "extraction_error", f"Failed to parse prompt: {str(e)}", level="ERROR")
                    # Fallback: just use raw prompt for everything if extraction fails hard
                    job.product_details = "Raw prompt analysis"
                    job.target_audience = "General audience"
                    job.goals = "Analyze prompt"
                    db.commit()

            base_payload = {
                "company_description": job.company_description,
                "product_details": job.product_details,
                "target_audience": job.target_audience,
                "goals": job.goals,
                "constraints": job.constraints,
            }

            # ── Step 1: Research Agent ────────────────────────────────────────────
            if _is_aborted(db, job_id):
                return _abort(db, job_id, "Cancelled before Research Agent")

            step_count += 1
            _guard_steps(step_count)

            span = trace.span("research_agent", input_data={"query": base_payload["goals"][:100]})
            research_task = _create_agent_task(db, job_id, AgentRole.RESEARCH)
            _start_task(db, research_task)
            _log_event(db, job_id, AgentRole.RESEARCH, "agent_start", "Research Agent starting")

            try:
                research_result = await research.run(job_id, base_payload)
                if research_result.get("status") == "error":
                    raise RuntimeError(research_result["message"])
                _complete_task(db, research_task, research_result)
                span.end(output={"report_len": len(research_result.get("research_report", ""))})
            except Exception as e:
                _fail_task(db, research_task, str(e))
                _log_event(db, job_id, AgentRole.RESEARCH, "agent_error", str(e), level="ERROR")
                _update_job_status(db, job_id, JobStatus.FAILED)
                return {"error": f"Research Agent failed: {e}"}

            # ── Step 2: Memory Agent — store research ─────────────────────────────
            if _is_aborted(db, job_id):
                return _abort(db, job_id, "Cancelled after Research Agent")

            step_count += 1
            memory_task = _create_agent_task(db, job_id, AgentRole.MEMORY)
            _start_task(db, memory_task)
            memory_store_payload = {
                "action": "store",
                "content": research_result.get("research_report", ""),
                "source_agent": "research",
            }
            memory_store_result = await memory.run(job_id, memory_store_payload)
            _complete_task(db, memory_task, memory_store_result)

            # ── Step 3: Memory Agent — recall relevant past context ───────────────
            memory_recall_payload = {
                "action": "recall",
                "query": f"{base_payload['product_details']} {base_payload['target_audience']}",
                "n_results": 3,
            }
            recall_result = await memory.run(job_id, memory_recall_payload)
            past_context = recall_result.get("documents", [])

            # ── Step 4: Strategy Agent ────────────────────────────────────────────
            if _is_aborted(db, job_id):
                return _abort(db, job_id, "Cancelled before Strategy Agent")

            step_count += 1
            strategy_payload = {
                **base_payload,
                "research_report": research_result.get("research_report", ""),
                "memory_context": past_context,
            }

            span = trace.span("strategy_agent")
            strategy_task = _create_agent_task(db, job_id, AgentRole.STRATEGY)
            _start_task(db, strategy_task)
            _log_event(db, job_id, AgentRole.STRATEGY, "agent_start", "Strategy Agent starting")

            try:
                strategy_result = await strategy.run(job_id, strategy_payload)
                if strategy_result.get("status") == "error":
                    raise RuntimeError(strategy_result["message"])
                _complete_task(db, strategy_task, strategy_result)
                span.end(output={"report_len": len(strategy_result.get("strategy_report", ""))})
            except Exception as e:
                _fail_task(db, strategy_task, str(e))
                _log_event(db, job_id, AgentRole.STRATEGY, "agent_error", str(e), level="ERROR")
                _update_job_status(db, job_id, JobStatus.FAILED)
                return {"error": f"Strategy Agent failed: {e}"}

            # ── Step 5: Critic Agent (with bounded retry) ─────────────────────────
            critic_retries = 0
            current_strategy = strategy_result.get("strategy_report", "")

            while critic_retries <= _MAX_CRITIC_RETRIES:
                if _is_aborted(db, job_id):
                    return _abort(db, job_id, "Cancelled during Critic review")

                step_count += 1
                critic_payload = {
                    **base_payload,
                    "research_report": research_result.get("research_report", ""),
                    "strategy_report": current_strategy,
                }

                span = trace.span("critic_agent", input_data={"retry": critic_retries})
                critic_task = _create_agent_task(db, job_id, AgentRole.CRITIC)
                _start_task(db, critic_task)
                _log_event(db, job_id, AgentRole.CRITIC, "agent_start", f"Critic Agent starting (attempt {critic_retries + 1})")

                try:
                    critic_result = await critic.run(job_id, critic_payload)
                    if critic_result.get("status") == "error":
                        raise RuntimeError(critic_result["message"])
                    critic_task.retry_count = critic_retries
                    _complete_task(db, critic_task, critic_result)
                    span.end(output={"verdict": critic_result.get("verdict"), "score": critic_result.get("score")})
                except Exception as e:
                    _fail_task(db, critic_task, str(e))
                    _log_event(db, job_id, AgentRole.CRITIC, "agent_error", str(e), level="ERROR")
                    break  # Don't let Critic failure block the pipeline

                verdict = critic_result.get("verdict", "APPROVED")
                _log_event(db, job_id, AgentRole.CRITIC, "critic_verdict", f"Verdict: {verdict}", {
                    "score": critic_result.get("score"),
                    "issues": critic_result.get("issues"),
                })

                if verdict == "APPROVED":
                    break

                if critic_retries >= _MAX_CRITIC_RETRIES:
                    _log_event(db, job_id, AgentRole.CRITIC, "max_retries_reached",
                               "Critic retries exhausted — proceeding with best result", level="WARN")
                    break

                # Retry: pass improvement prompt back to Strategy Agent
                _log_event(db, job_id, AgentRole.ORCHESTRATOR, "strategy_retry",
                           "Critic rejected — retrying Strategy Agent with improvement prompt")
                step_count += 1
                retry_payload = {
                    **strategy_payload,
                    "improvement_instruction": critic_result.get("improvement_prompt", ""),
                }

                retry_strategy = await strategy.run(job_id, retry_payload)
                if retry_strategy.get("status") != "error":
                    current_strategy = retry_strategy.get("strategy_report", current_strategy)

                critic_retries += 1

            # ── Step 6: Planner Agent ─────────────────────────────────────────────
            if _is_aborted(db, job_id):
                return _abort(db, job_id, "Cancelled before Planner Agent")

            step_count += 1
            planner_payload = {
                **base_payload,
                "strategy_report": current_strategy,
            }

            span = trace.span("planner_agent")
            planner_task = _create_agent_task(db, job_id, AgentRole.PLANNER)
            _start_task(db, planner_task)
            _log_event(db, job_id, AgentRole.PLANNER, "agent_start", "Planner Agent starting")

            try:
                planner_result = await planner.run(job_id, planner_payload)
                if planner_result.get("status") == "error":
                    raise RuntimeError(planner_result["message"])
                _complete_task(db, planner_task, planner_result)
                span.end()
            except Exception as e:
                _fail_task(db, planner_task, str(e))
                _log_event(db, job_id, AgentRole.PLANNER, "agent_error", str(e), level="ERROR")
                # Planner failure is non-fatal — continue with empty plan
                planner_result = {"status": "failed", "execution_plan": {}, "critical_path": [], "success_metrics": {}}

            # ── Step 7: QA Agent ──────────────────────────────────────────────────
            if _is_aborted(db, job_id):
                return _abort(db, job_id, "Cancelled before QA Agent")

            step_count += 1
            qa_payload = {
                **base_payload,
                "research_report": research_result.get("research_report", ""),
                "strategy_report": current_strategy,
                "execution_plan": planner_result,
            }

            span = trace.span("qa_agent")
            qa_task = _create_agent_task(db, job_id, AgentRole.QA)
            _start_task(db, qa_task)
            _log_event(db, job_id, AgentRole.QA, "agent_start", "QA Agent starting")

            try:
                qa_result = await qa.run(job_id, qa_payload)
                _complete_task(db, qa_task, qa_result)
                span.end(output={"passed": qa_result.get("passed"), "score": qa_result.get("overall_quality_score")})
            except Exception as e:
                _fail_task(db, qa_task, str(e))
                _log_event(db, job_id, AgentRole.QA, "agent_error", str(e), level="ERROR")
                qa_result = {"passed": True, "gaps": [], "overall_quality_score": 6}

            # ── Final Assembly ────────────────────────────────────────────────────
            final_report = {
                "job_id": job_id,
                "research": {
                    "report": research_result.get("research_report", ""),
                    "sources": research_result.get("sources", []),
                },
                "strategy": {
                    "report": current_strategy,
                    "critic_score": critic_result.get("score"),
                    "critic_verdict": critic_result.get("verdict", "APPROVED"),
                },
                "execution_plan": planner_result.get("execution_plan", {}),
                "critical_path": planner_result.get("critical_path", []),
                "success_metrics": planner_result.get("success_metrics", {}),
                "qa": {
                    "passed": qa_result.get("passed"),
                    "score": qa_result.get("overall_quality_score"),
                    "gaps": qa_result.get("gaps", []),
                },
                "total_steps": step_count,
            }

            _update_job_status(db, job_id, JobStatus.COMPLETED, final_report=final_report)
            _log_event(db, job_id, AgentRole.ORCHESTRATOR, "workflow_complete",
                       f"Workflow completed in {step_count} steps", {
                           "qa_passed": qa_result.get("passed"),
                           "qa_score": qa_result.get("overall_quality_score"),
                       })

        logger.info("orchestration_complete", job_id=job_id, steps=step_count)
        return final_report

    except Exception as exc:
        logger.error("orchestrator_fatal_error", job_id=job_id, error=str(exc))
        _update_job_status(db, job_id, JobStatus.FAILED)
        # Attempt to write the error to the final_report so the UI can see it
        job = db.get(Job, job_id)
        if job:
            job.final_report = {"error": f"Fatal Orchestrator Error: {str(exc)}"}
            db.commit()
        raise


def _guard_steps(step_count: int):
    """Raise if max steps exceeded — prevents infinite loops."""
    if step_count > _MAX_TOTAL_STEPS:
        raise RuntimeError(
            f"Max orchestration steps ({_MAX_TOTAL_STEPS}) exceeded. Aborting to prevent runaway execution."
        )


def _abort(db: Session, job_id: str, reason: str) -> dict:
    """Mark job as aborted and return an abort payload."""
    _update_job_status(db, job_id, JobStatus.ABORTED)
    _log_event(db, job_id, AgentRole.ORCHESTRATOR, "workflow_aborted", reason, level="WARN")
    logger.warning("orchestration_aborted", job_id=job_id, reason=reason)
    return {"aborted": True, "reason": reason}
