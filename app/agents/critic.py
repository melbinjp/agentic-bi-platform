"""
Critic Agent - Adversarial Review

Responsibilities:
  - Review the strategy report for hallucinations, logic gaps, weak reasoning
  - Flag unsupported claims not grounded in the research
  - Return APPROVED or REJECTED with specific feedback
  - Trigger a bounded single-retry if rejected

Assignment requirement: Multi-Agent Architecture — Critic Agent
  - Reviews hallucinations, logic gaps, weak reasoning
  - Uses CRITIQUE model tier (Groq Llama — separate evaluator model)
"""

import structlog
from app.llm_client import call_llm, stateful_summarize
from app.llm_router import TaskType
from app.security import build_safe_system_prompt

logger = structlog.get_logger()

AGENT_ROLE = "critic"

_SYSTEM_PROMPT = build_safe_system_prompt("""You are the Critic Agent — an adversarial reviewer for a business intelligence platform.
Your job is to evaluate strategic reports with extreme scrutiny.

Check for:
1. HALLUCINATIONS: claims not supported by the provided research
2. LOGIC GAPS: strategy recommendations that contradict the stated constraints
3. WEAK REASONING: vague recommendations without actionable specifics
4. MISSING SECTIONS: any of the 7 required sections is absent or superficial
5. INTERNAL CONTRADICTIONS: advice that conflicts with itself

Respond in this EXACT JSON format:
{
  "verdict": "APPROVED" | "REJECTED",
  "score": <integer 1-10>,
  "issues": [
    {"type": "HALLUCINATION|LOGIC_GAP|WEAK_REASONING|MISSING_SECTION|CONTRADICTION", "description": "...", "location": "section name"}
  ],
  "improvement_prompt": "<specific instruction to fix the issues, or empty string if APPROVED>"
}

Be strict. A score below 7 must always result in REJECTED.
""")


async def run(job_id: str, payload: dict) -> dict:
    """
    Main entry point called by the Orchestrator.

    Payload keys:
      - research_report: str
      - strategy_report: str
      - company_description: str
      - goals: str
      - constraints: str

    Returns:
      - verdict: "APPROVED" | "REJECTED"
      - score: int
      - issues: list
      - improvement_prompt: str
    """
    import json

    research_raw = payload.get("research_report", "")
    strategy_raw = payload.get("strategy_report", "")
    company = payload.get("company_description", "")
    goals = payload.get("goals", "")
    constraints = payload.get("constraints", "")

    # 🗺️ Stateful rolling summarization under tight TPM rate bounds
    logger.info("critic_agent_context_compaction_start", job_id=job_id, research_len=len(research_raw), strategy_len=len(strategy_raw))
    research = await stateful_summarize(research_raw, job_id, max_chunks=3)
    strategy = await stateful_summarize(strategy_raw, job_id, max_chunks=3)
    logger.info("critic_agent_context_compaction_complete", job_id=job_id, research_len=len(research), strategy_len=len(strategy))

    user_prompt = f"""
Review this strategic report for quality and accuracy.

Original Business Context:
  Company: {company}
  Goals: {goals}
  Constraints: {constraints}

Research Findings (ground truth):
{research}

Strategy Report to Review:
{strategy}

Evaluate strictly and return the JSON verdict as instructed.
"""

    raw_response = await call_llm(
        task_type=TaskType.CRITIQUE,
        job_id=job_id,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.3,  # low temperature for consistent evaluation
    )

    if not raw_response:
        logger.error("critic_agent_llm_failed_enforcing_reject", job_id=job_id)
        return {
            "status": "completed",
            "verdict": "REJECTED",
            "score": 1,
            "issues": [{"type": "CONTRADICTION", "description": "System Error: Critic validation model check failed or timed out.", "location": "System"}],
            "improvement_prompt": "Please rerun the analysis. The LLM check during critique failed.",
        }

    # Parse JSON verdict
    try:
        # Strip markdown fences if present
        clean = raw_response.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        verdict_data = json.loads(clean.strip())
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(
            "critic_json_parse_failed_enforcing_reject",
            job_id=job_id,
            error=str(e),
            raw_preview=raw_response[:200],
        )
        # Fallback: treat as rejected with a score of 1 to trigger retry / flag failure strictly
        verdict_data = {
            "verdict": "REJECTED",
            "score": 1,
            "issues": [{"type": "CONTRADICTION", "description": "System Error: Critic validation output failed to parse.", "location": "System"}],
            "improvement_prompt": "The adversarial critique output was corrupted. Retrying strategy generation.",
        }

    verdict = verdict_data.get("verdict", "REJECTED")
    # Safeguard contradiction (if score < 7, verdict MUST be REJECTED)
    score = verdict_data.get("score", 1)
    if score < 7:
        verdict = "REJECTED"

    logger.info(
        "critic_verdict",
        job_id=job_id,
        verdict=verdict,
        score=score,
        issue_count=len(verdict_data.get("issues", [])),
    )

    return {
        "status": "completed",
        "verdict": verdict,
        "score": score,
        "issues": verdict_data.get("issues", []),
        "improvement_prompt": verdict_data.get("improvement_prompt", ""),
    }
