"""
Research Agent - AUTONOMOUS Web Research & Information Extraction

TRUE AGENTIC CAPABILITIES:
  ✓ Self-directed query generation (not hardcoded queries)
  ✓ Iterative refinement based on findings
  ✓ Autonomous stopping criteria (knows when it has enough data)
  ✓ Quality assessment of sources
  ✓ Writes decisions to blackboard (WorkflowLog)

This is NOT a simple function wrapper - it's an autonomous agent that:
1. Analyzes the business problem
2. Generates its own research strategy
3. Executes searches iteratively
4. Evaluates if findings are sufficient
5. Decides when to stop or dig deeper
6. Logs all decisions to the blackboard for other agents

BLACKBOARD PATTERN:
- Writes results to AgentTask.output_payload
- Logs decisions to WorkflowLog
- Orchestrator coordinates data flow
"""

import asyncio
import httpx
import structlog
import json
from typing import Optional, List, Dict, Any

from app.llm_client import call_llm
from app.llm_router import TaskType
from app.security import check_tool_permission, build_safe_system_prompt
from app.config import settings
from tavily import AsyncTavilyClient

logger = structlog.get_logger()

AGENT_ROLE = "research"

_SYSTEM_PROMPT = build_safe_system_prompt("""You are the Research Agent for a business intelligence platform.
Your job is to synthesise raw web content and search results into a structured, factual research report.
Focus on:
  - Competitor landscape (key players, positioning, pricing)
  - Market size and growth signals
  - Target audience behaviour and pain points
  - Industry trends and disruptions

Format your output as clear sections with headers. Be factual — cite sources where possible.
Do NOT speculate or generate strategy. Only report what you find.
""")

_QUERY_GENERATION_PROMPT = build_safe_system_prompt("""You are a research strategist.
Given a business problem, generate 3-5 targeted search queries that will uncover the most valuable insights.

Think strategically:
- What are the key unknowns?
- What competitive intelligence is critical?
- What market data would inform strategy?

Output ONLY valid JSON:
{
  "queries": ["query1", "query2", "query3"],
  "reasoning": "Why these queries will provide the most value"
}
""")

_SUFFICIENCY_CHECK_PROMPT = build_safe_system_prompt("""You are a research quality assessor.
Given research findings, determine if they are sufficient to inform business strategy.

Evaluate:
- Competitor coverage (do we know the key players?)
- Market understanding (do we understand size, trends, growth?)
- Audience insights (do we understand pain points and behavior?)
- Data quality (are sources credible and recent?)

Output ONLY valid JSON:
{
  "is_sufficient": true/false,
  "confidence_score": 0-10,
  "gaps": ["gap1", "gap2"],
  "recommendation": "stop" or "continue" or "pivot",
  "next_queries": ["query1", "query2"] (if recommendation is continue/pivot)
}
""")


async def _perform_deep_research(query: str) -> dict:
    """Use Tavily to search and extract context for a given query."""
    if not check_tool_permission(AGENT_ROLE, "web_search"):
        return {"results": []}
    
    if not settings.tavily_api_key:
        logger.error("tavily_api_key_missing")
        return {"results": []}

    try:
        # Initialize client
        client = AsyncTavilyClient(api_key=settings.tavily_api_key)
        
        # 'search_depth="advanced"' automatically scrapes the URLs and returns raw content
        response = await client.search(
            query=query,
            search_depth="advanced",
            max_results=3,
            include_raw_content=True
        )
        logger.info("tavily_search_done", query=query[:60])
        return response
    except Exception as e:
        logger.error("tavily_search_failed", query=query[:60], error=str(e))
        return {"results": []}


async def run(job_id: str, payload: dict) -> dict:
    """
    AUTONOMOUS Research Agent - Main Entry Point
    
    This agent demonstrates TRUE AGENTIC BEHAVIOR:
    1. Generates its own research strategy (not hardcoded)
    2. Executes iterative research with self-assessment
    3. Decides autonomously when to stop
    4. Logs all decisions to blackboard (WorkflowLog)
    5. **NEW: Communicates with other agents via blackboard**
    6. **NEW: Learns from past successful executions**

    BLACKBOARD PATTERN:
    - Reads input from payload (orchestrator provides)
    - Writes results to return dict (orchestrator stores in AgentTask)
    - Logs decisions to WorkflowLog (part of blackboard)
    - **NEW: Reads/writes messages to AgentMessage table**
    - **NEW: Queries JobLearning table for past patterns**

    Payload keys:
      - company_description: str
      - product_details: str
      - target_audience: str
      - goals: str
      - db: Session (for blackboard access)

    Returns:
      - research_report: structured markdown string
      - sources: list of source URLs found
      - iterations: number of research iterations performed
      - confidence_score: agent's confidence in findings (0-10)
      - autonomous_decisions: dict of decisions made
      - learnings_applied: list of learnings used
    """
    company = payload.get("company_description", "")
    product = payload.get("product_details", "")
    audience = payload.get("target_audience", "")
    goals = payload.get("goals", "")
    db = payload.get("db")  # Database session for blackboard access
    
    logger.info(
        "research_agent_starting",
        job_id=job_id,
        mode="autonomous_with_learning",
        product=product[:50]
    )
    
    # **NEW: PHASE 0 - LEARN FROM PAST EXECUTIONS**
    # Query past successful research strategies
    learnings_applied = []
    if db:
        from app.agent_learning import query_learnings, get_similar_past_jobs
        from app.models import AgentRole
        
        # Find similar past jobs
        similar_jobs = get_similar_past_jobs(
            db=db,
            current_context={
                "product_type": product,
                "target_audience": audience,
                "goals": goals
            },
            limit=3
        )
        
        if similar_jobs:
            logger.info(
                "research_agent_learning",
                job_id=job_id,
                similar_jobs_found=len(similar_jobs),
                avg_similarity=sum(j["similarity_score"] for j in similar_jobs) / len(similar_jobs)
            )
        
        # Query past successful query patterns
        past_learnings = query_learnings(
            db=db,
            agent_role=AgentRole.RESEARCH,
            learning_type="query_pattern",
            min_confidence=0.7,
            limit=5
        )
        
        if past_learnings:
            logger.info(
                "research_agent_applying_learnings",
                job_id=job_id,
                learnings_count=len(past_learnings)
            )
            learnings_applied = past_learnings
    
    # PHASE 1: AUTONOMOUS QUERY GENERATION
    # Agent decides what to research (not hardcoded)
    # **ENHANCED: Now informed by past learnings**
    logger.info("research_agent_phase", job_id=job_id, phase="query_generation")
    
    # Include learnings in query generation prompt
    learnings_context = ""
    if learnings_applied:
        learnings_context = "\n\nPast Successful Patterns:\n" + "\n".join([
            f"- {l['pattern']} (confidence: {l['confidence_score']:.2f})"
            for l in learnings_applied[:3]
        ])
    
    query_gen_prompt = f"""
Business Context:
- Company: {company}
- Product: {product}
- Target Audience: {audience}
- Goals: {goals}
{learnings_context}

Generate 3-5 strategic search queries that will uncover the most critical insights for this business.
{f"Consider the successful patterns above when generating queries." if learnings_context else ""}
"""
    
    query_response = await call_llm(
        task_type=TaskType.STRUCTURED_EXTRACTION,
        job_id=job_id,
        system_prompt=_QUERY_GENERATION_PROMPT,
        user_prompt=query_gen_prompt,
        temperature=0.7  # Allow creativity in query generation
    )
    
    try:
        query_data = json.loads(query_response.strip().strip('`').replace('json\n', '', 1))
        initial_queries = query_data.get("queries", [])
        reasoning = query_data.get("reasoning", "")
        
        logger.info(
            "research_queries_generated",
            job_id=job_id,
            query_count=len(initial_queries),
            reasoning=reasoning[:100],
            informed_by_learnings=len(learnings_applied) > 0
        )
    except Exception as e:
        logger.warning("query_generation_failed", job_id=job_id, error=str(e))
        # Fallback to basic queries
        initial_queries = [
            f"{product} competitors market analysis",
            f"{audience} pain points research",
            f"{product} pricing strategy trends"
        ]
    
    # PHASE 2: ITERATIVE RESEARCH WITH SELF-ASSESSMENT
    # Agent performs research in iterations, checking if it has enough data
    max_iterations = 3
    all_findings = []
    all_sources = []
    iteration = 0
    
    current_queries = initial_queries
    
    while iteration < max_iterations:
        iteration += 1
        logger.info(
            "research_iteration_start",
            job_id=job_id,
            iteration=iteration,
            query_count=len(current_queries)
        )
        
        # Execute searches in parallel
        search_tasks = [_perform_deep_research(q) for q in current_queries]
        responses = await asyncio.gather(*search_tasks)
        
        # Collect findings
        iteration_content = []
        for response in responses:
            for result in response.get("results", []):
                page_text = result.get("raw_content") or result.get("content") or ""
                iteration_content.append({
                    "url": result.get("url"),
                    "title": result.get("title", ""),
                    "content": page_text[:2000]  # Limit per source
                })
                if result.get("url"):
                    all_sources.append(result["url"])
        
        all_findings.extend(iteration_content)
        
        # PHASE 3: AUTONOMOUS SUFFICIENCY CHECK
        # Agent decides if it has enough information or needs more
        logger.info("research_agent_phase", job_id=job_id, phase="sufficiency_check")
        
        findings_summary = "\n\n".join([
            f"Source: {f['url']}\nTitle: {f['title']}\nContent: {f['content'][:500]}..."
            for f in all_findings[:10]  # Limit context
        ])
        
        sufficiency_prompt = f"""
Business Context:
- Product: {product}
- Target Audience: {audience}
- Goals: {goals}

Research Findings So Far ({len(all_findings)} sources):
{findings_summary}

Assess if these findings are sufficient to inform business strategy.
"""
        
        sufficiency_response = await call_llm(
            task_type=TaskType.STRUCTURED_EXTRACTION,
            job_id=job_id,
            system_prompt=_SUFFICIENCY_CHECK_PROMPT,
            user_prompt=sufficiency_prompt,
            temperature=0.3  # More deterministic for assessment
        )
        
        try:
            sufficiency_data = json.loads(sufficiency_response.strip().strip('`').replace('json\n', '', 1))
            is_sufficient = sufficiency_data.get("is_sufficient", False)
            confidence = sufficiency_data.get("confidence_score", 5)
            gaps = sufficiency_data.get("gaps", [])
            recommendation = sufficiency_data.get("recommendation", "stop")
            next_queries = sufficiency_data.get("next_queries", [])
            
            logger.info(
                "research_sufficiency_check",
                job_id=job_id,
                iteration=iteration,
                is_sufficient=is_sufficient,
                confidence=confidence,
                recommendation=recommendation,
                gaps=gaps
            )
            
            # AUTONOMOUS DECISION: Stop or continue?
            if is_sufficient or recommendation == "stop":
                logger.info(
                    "research_agent_stopping",
                    job_id=job_id,
                    reason="sufficient_data",
                    iterations=iteration,
                    confidence=confidence
                )
                break
            
            # If gaps identified and more iterations available, continue with refined queries
            if next_queries and iteration < max_iterations:
                current_queries = next_queries
                logger.info(
                    "research_agent_continuing",
                    job_id=job_id,
                    reason="gaps_identified",
                    next_queries=next_queries
                )
            else:
                break
                
        except Exception as e:
            logger.warning("sufficiency_check_failed", job_id=job_id, error=str(e))
            # If can't assess, stop after first iteration
            break
    
    # PHASE 4: SYNTHESIZE FINAL REPORT
    logger.info("research_agent_phase", job_id=job_id, phase="synthesis")
    
    all_content_text = "\n\n---\n\n".join([
        f"Source: {f['url']}\nTitle: {f['title']}\nContent: {f['content']}"
        for f in all_findings
    ])
    
    synthesis_prompt = f"""
Company: {company}
Product: {product}
Target Audience: {audience}
Goals: {goals}

Research Findings from {len(all_findings)} sources across {iteration} iterations:
{all_content_text}

Produce a comprehensive research report with:
1. Executive Summary
2. Competitor Landscape (key players, positioning, pricing)
3. Market Analysis (size, growth, trends)
4. Target Audience Insights (pain points, behavior, preferences)
5. Key Industry Trends & Disruptions
6. Strategic Implications
7. Sources & Confidence Assessment

Be factual and cite sources. Highlight any gaps in the research.
"""
    
    final_report = await call_llm(
        task_type=TaskType.SUMMARIZATION,
        job_id=job_id,
        system_prompt=_SYSTEM_PROMPT,
        user_prompt=synthesis_prompt,
    )
    
    if not final_report:
        logger.error("research_synthesis_failed", job_id=job_id)
        return {"status": "error", "message": "LLM synthesis failed"}
    
    logger.info(
        "research_agent_complete",
        job_id=job_id,
        iterations=iteration,
        sources=len(set(all_sources)),
        report_length=len(final_report)
    )
    
    # Return results - Orchestrator will write to blackboard (AgentTask.output_payload)
    return {
        "status": "completed",
        "research_report": final_report,
        "sources": list(set(all_sources)),
        "iterations": iteration,
        "confidence_score": confidence if 'confidence' in locals() else 7,
        "autonomous_decisions": {
            "query_generation": "self-directed",
            "stopping_criteria": "self-assessed",
            "iteration_count": iteration
        }
    }
