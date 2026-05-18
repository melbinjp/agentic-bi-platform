"""
QA Agent - Output Validation

Responsibilities:
  - Validate completeness and structure of the final report
  - Check all required sections are present and non-empty
  - Validate JSON schemas for structured outputs (execution plan)
  - Return a pass/fail result with specific gaps listed

Assignment requirement: Multi-Agent Architecture — QA Agent
  - Validates completeness and structure
"""

import structlog
from typing import Any
from app.llm_client import call_llm, stateful_summarize
from app.llm_router import TaskType
from app.security import build_safe_system_prompt

logger = structlog.get_logger()

AGENT_ROLE = "qa"

_SYSTEM_PROMPT = build_safe_system_prompt("""You are the QA Agent for a business intelligence platform.
Your role is to validate the final assembled report for completeness.

Check that the final report contains ALL of the following sections:
  1. Research Findings (competitor landscape, market signals, audience insights)
  2. Strategic Recommendations (GTM, pricing, differentiation, content, growth experiments)
  3. Execution Plan (30/60/90-day tasks with KPIs)
  4. Risk Assessment

For each section, check:
  - It exists and is non-empty
  - It contains specific, actionable content (not placeholder text)
  - It directly addresses the original business goals and constraints

Respond in this EXACT JSON format:
{
  "passed": true | false,
  "section_results": {
    "research_findings": {"present": bool, "adequate": bool, "notes": "string"},
    "strategic_recommendations": {"present": bool, "adequate": bool, "notes": "string"},
    "execution_plan": {"present": bool, "adequate": bool, "notes": "string"},
    "risk_assessment": {"present": bool, "adequate": bool, "notes": "string"}
  },
  "gaps": ["list of specific missing or inadequate items"],
  "overall_quality_score": <integer 1-10>
}
""")


# ─── Schema Validators ────────────────────────────────────────────────────────

def _validate_execution_plan_schema(plan: dict) -> list[str]:
    """Validate the Planner Agent's JSON output against expected schema."""
    gaps = []
    if not plan:
        return ["Execution plan is empty"]

    for phase in ["phase_30_days", "phase_60_days", "phase_90_days"]:
        tasks = plan.get("execution_plan", {}).get(phase, [])
        if not tasks:
            gaps.append(f"Missing tasks in {phase}")
        else:
            for i, task in enumerate(tasks):
                for required_key in ["task", "owner", "priority", "kpi"]:
                    if not task.get(required_key):
                        gaps.append(f"{phase}[{i}] missing '{required_key}'")

    if not plan.get("critical_path"):
        gaps.append("Missing critical_path")
    if not plan.get("success_metrics"):
        gaps.append("Missing success_metrics")

    return gaps


async def run(job_id: str, payload: dict) -> dict:
    """
    Main entry point called by the Orchestrator.

    Payload keys:
      - research_report: str
      - strategy_report: str
      - execution_plan: dict (from Planner Agent)
      - goals: str
      - constraints: str

    Returns:
      - passed: bool
      - gaps: list of gap descriptions
      - section_results: per-section pass/fail
      - overall_quality_score: int
    """
    import json

    research_raw = payload.get("research_report", "")
    strategy_raw = payload.get("strategy_report", "")
    execution_plan = payload.get("execution_plan", {})
    goals = payload.get("goals", "")
    constraints = payload.get("constraints", "")

    # 🗺️ Stateful rolling summarization under tight TPM rate bounds
    logger.info("qa_agent_context_compaction_start", job_id=job_id, research_len=len(research_raw), strategy_len=len(strategy_raw))
    research = await stateful_summarize(research_raw, job_id, max_chunks=3)
    strategy = await stateful_summarize(strategy_raw, job_id, max_chunks=3)
    logger.info("qa_agent_context_compaction_complete", job_id=job_id, research_len=len(research), strategy_len=len(strategy))

    # Programmatic schema check first (no LLM needed)
    schema_gaps = _validate_execution_plan_schema(execution_plan)

    # LLM-based content quality check
    user_prompt = f"""
Goals: {goals}
Constraints: {constraints}

RESEARCH REPORT:
{research}

STRATEGY REPORT:
{strategy}

EXECUTION PLAN (summary):
{str(execution_plan)[:2000]}

Validate completeness and return the JSON verdict.
"""

    raw_response = await call_llm(
        task_type=TaskType.STRUCTURED_EXTRACTION,
        job_id=job_id,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.2,
    )

    if not raw_response:
        logger.error("qa_agent_llm_failed_enforcing_fail", job_id=job_id)
        return {
            "status": "completed",
            "passed": False,
            "gaps": schema_gaps + ["System Error: QA validation model check failed or timed out. Text quality could not be verified."],
            "section_results": {},
            "overall_quality_score": 1,
        }

    try:
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        qa_data = json.loads(clean.strip())
    except (json.JSONDecodeError, IndexError) as e:
        logger.error("qa_json_parse_failed_enforcing_fail", job_id=job_id, error=str(e))
        qa_data = {
            "passed": False,
            "gaps": ["System Error: QA validation output was corrupted or failed to parse as JSON."],
            "section_results": {},
            "overall_quality_score": 1
        }

    # Merge schema gaps into QA result
    all_gaps = qa_data.get("gaps", []) + schema_gaps
    passed = qa_data.get("passed", True) and len(schema_gaps) == 0

    logger.info(
        "qa_agent_done",
        job_id=job_id,
        passed=passed,
        score=qa_data.get("overall_quality_score"),
        gap_count=len(all_gaps),
    )

    return {
        "status": "completed",
        "passed": passed,
        "gaps": all_gaps,
        "section_results": qa_data.get("section_results", {}),
        "overall_quality_score": qa_data.get("overall_quality_score", 7),
    }
