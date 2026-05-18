"""
Planner Agent - Execution Task Generation

Responsibilities:
  - Convert the approved strategy report into a concrete execution timeline
  - Break strategy into 30/60/90-day actionable tasks with owners and KPIs
  - Output structured task list (JSON)

Assignment requirement: Multi-Agent Architecture — Planner Agent
  - Converts strategy into execution tasks
"""

import json
import structlog
from app.llm_client import call_llm
from app.llm_router import TaskType
from app.security import build_safe_system_prompt

logger = structlog.get_logger()

AGENT_ROLE = "planner"

_SYSTEM_PROMPT = build_safe_system_prompt("""You are the Planner Agent for a business intelligence platform.
You receive an approved strategic report and convert it into a concrete, time-bound execution plan.

Output ONLY valid JSON in this exact structure:
{
  "execution_plan": {
    "phase_30_days": [
      {
        "task": "string",
        "owner": "string (e.g. Marketing, Engineering, Founder)",
        "priority": "HIGH|MEDIUM|LOW",
        "kpi": "string (measurable success metric)",
        "dependencies": ["task names this depends on"]
      }
    ],
    "phase_60_days": [...],
    "phase_90_days": [...]
  },
  "critical_path": ["ordered list of the highest-priority tasks"],
  "success_metrics": {
    "30_day": "string",
    "60_day": "string",
    "90_day": "string"
  }
}

Be specific and actionable. Each task must have a clear, measurable KPI.
""")


async def run(job_id: str, payload: dict) -> dict:
    """
    Main entry point called by the Orchestrator.

    Payload keys:
      - strategy_report: str
      - company_description: str
      - goals: str
      - constraints: str

    Returns:
      - execution_plan: dict with 30/60/90-day phases
      - critical_path: list
      - success_metrics: dict
    """
    strategy = payload.get("strategy_report", "")
    company = payload.get("company_description", "")
    goals = payload.get("goals", "")
    constraints = payload.get("constraints", "")

    user_prompt = f"""
Company: {company}
Goals: {goals}
Constraints: {constraints}

Approved Strategy Report:
{strategy[:5000]}

Convert this strategy into a structured 30/60/90-day execution plan.
Return ONLY the JSON object, no markdown fences.
"""

    raw_response = await call_llm(
        task_type=TaskType.STRUCTURED_EXTRACTION,
        job_id=job_id,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.4,
    )

    if not raw_response:
        logger.error("planner_agent_llm_failed", job_id=job_id)
        return {"status": "error", "message": "LLM call failed during planning"}

    # Parse structured JSON output
    try:
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        plan_data = json.loads(clean.strip())
    except (json.JSONDecodeError, IndexError) as e:
        logger.warning("planner_json_parse_failed", job_id=job_id, error=str(e))
        # Return raw text if JSON parse fails — still valuable
        return {
            "status": "completed_raw",
            "execution_plan_raw": raw_response,
            "execution_plan": {},
            "critical_path": [],
            "success_metrics": {},
        }

    logger.info("planner_agent_done", job_id=job_id)
    return {
        "status": "completed",
        "execution_plan": plan_data.get("execution_plan", {}),
        "critical_path": plan_data.get("critical_path", []),
        "success_metrics": plan_data.get("success_metrics", {}),
    }
