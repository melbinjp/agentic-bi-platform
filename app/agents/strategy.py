"""
Strategy Agent - Business Recommendations

Responsibilities:
  - Consume research report from the Research Agent
  - Generate GTM strategy, pricing strategy, content plan, growth experiments
  - Output structured strategic recommendations

Assignment requirement: Multi-Agent Architecture — Strategy Agent
  - Business recommendations
  - Uses STRATEGIC_REASONING model tier (Groq Llama 70B)
"""

import structlog
from app.llm_client import call_llm
from app.llm_router import TaskType
from app.security import build_safe_system_prompt

logger = structlog.get_logger()

AGENT_ROLE = "strategy"

_SYSTEM_PROMPT = build_safe_system_prompt("""You are the Strategy Agent for a business intelligence platform.
You receive verified research findings and produce a comprehensive strategic playbook.
Your output must be actionable, specific, and grounded in the research provided.

Structure your response with these exact sections:
1. Go-To-Market (GTM) Strategy
2. Competitor Positioning & Differentiation
3. Pricing Strategy
4. Target Audience Engagement Plan
5. Content & Marketing Plan
6. Growth Experiments (3–5 testable hypotheses)
7. Key Risks & Mitigations

Be specific: include timelines, metrics, and decision criteria where relevant.
Do NOT repeat research findings verbatim — synthesise them into strategy.
""")


async def run(job_id: str, payload: dict) -> dict:
    """
    Main entry point called by the Orchestrator.

    Payload keys:
      - company_description: str
      - product_details: str
      - target_audience: str
      - goals: str
      - constraints: str
      - research_report: str (from Research Agent)
      - memory_context: list[str] (optional, from Memory Agent recall)

    Returns:
      - strategy_report: structured markdown string
    """
    company = payload.get("company_description", "")
    product = payload.get("product_details", "")
    audience = payload.get("target_audience", "")
    goals = payload.get("goals", "")
    constraints = payload.get("constraints", "None specified")
    research = payload.get("research_report", "")
    memory_ctx = payload.get("memory_context", [])

    memory_section = ""
    if memory_ctx:
        memory_section = "\n\nRelated context from previous analyses:\n" + "\n---\n".join(memory_ctx)

    user_prompt = f"""
Business Context:
  Company: {company}
  Product: {product}
  Target Audience: {audience}
  Goals: {goals}
  Constraints: {constraints}

Research Findings:
{research}
{memory_section}

Produce the full strategic playbook as described in your instructions.
"""

    strategy = await call_llm(
        task_type=TaskType.STRATEGIC_REASONING,
        job_id=job_id,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        temperature=0.6,
    )

    if not strategy:
        logger.error("strategy_agent_llm_failed", job_id=job_id)
        return {"status": "error", "message": "LLM call failed during strategy generation"}

    logger.info("strategy_agent_done", job_id=job_id, report_len=len(strategy))
    return {
        "status": "completed",
        "strategy_report": strategy,
    }
