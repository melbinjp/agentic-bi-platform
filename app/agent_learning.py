"""
Agent Learning from Past Executions

Enables agents to learn from historical job data and improve their strategies over time.
Agents query past successful patterns and adapt their behavior accordingly.

This implements true learning capability - agents get better with more data.
"""

import structlog
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, func

from app.models import JobLearning, AgentRole, Job, JobStatus, AgentTask, TaskStatus

logger = structlog.get_logger()


def record_learning(
    db: Session,
    job_id: str,
    agent_role: AgentRole,
    learning_type: str,
    pattern: str,
    context: Dict[str, Any],
    outcome: str,
    confidence_score: float
) -> str:
    """
    Record a learning from a completed task.
    
    Args:
        db: Database session
        job_id: Job ID
        agent_role: Agent that learned this pattern
        learning_type: "strategy", "query_pattern", "tool_usage", "outcome"
        pattern: Description of what was learned
        context: Context in which this pattern occurred
        outcome: "success", "failure", "partial"
        confidence_score: 0.0 to 1.0
    
    Returns:
        Learning ID
    
    Example:
        # Research agent records successful query pattern
        record_learning(
            db=db,
            job_id=job_id,
            agent_role=AgentRole.RESEARCH,
            learning_type="query_pattern",
            pattern="Queries about 'competitor pricing' yield high-quality results",
            context={
                "industry": "fitness",
                "product_type": "app",
                "query": "fitness app competitor pricing"
            },
            outcome="success",
            confidence_score=0.9
        )
    """
    learning = JobLearning(
        job_id=job_id,
        agent_role=agent_role,
        learning_type=learning_type,
        pattern=pattern,
        context=context,
        outcome=outcome,
        confidence_score=confidence_score,
        times_applied=0,
        success_count=0
    )
    
    db.add(learning)
    db.commit()
    db.refresh(learning)
    
    logger.info(
        "learning_recorded",
        job_id=job_id,
        agent=agent_role.value,
        learning_type=learning_type,
        pattern=pattern[:100],
        confidence=confidence_score
    )
    
    return learning.id


def query_learnings(
    db: Session,
    agent_role: AgentRole,
    learning_type: Optional[str] = None,
    context_filter: Optional[Dict[str, Any]] = None,
    min_confidence: float = 0.7,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Query past learnings to inform current strategy.
    
    Args:
        db: Database session
        agent_role: Agent querying learnings
        learning_type: Filter by learning type
        context_filter: Filter by context (e.g., {"industry": "fitness"})
        min_confidence: Minimum confidence score
        limit: Maximum number of results
    
    Returns:
        List of learning dictionaries, sorted by confidence and success rate
    
    Example:
        # Research agent queries past successful strategies for fitness apps
        learnings = query_learnings(
            db=db,
            agent_role=AgentRole.RESEARCH,
            learning_type="query_pattern",
            context_filter={"industry": "fitness"},
            min_confidence=0.7
        )
        
        for learning in learnings:
            print(f"Pattern: {learning['pattern']}")
            print(f"Success rate: {learning['success_rate']}")
            # Adapt current strategy based on this learning
    """
    query = select(JobLearning).where(
        and_(
            JobLearning.agent_role == agent_role,
            JobLearning.confidence_score >= min_confidence,
            JobLearning.outcome == "success"
        )
    )
    
    if learning_type:
        query = query.where(JobLearning.learning_type == learning_type)
    
    # Context filtering (simple JSON containment check)
    if context_filter:
        for key, value in context_filter.items():
            # This is a simplified filter - in production, use proper JSON querying
            query = query.where(
                JobLearning.context[key].astext == str(value)
            )
    
    # Order by confidence and success rate
    query = query.order_by(
        desc(JobLearning.confidence_score),
        desc(JobLearning.success_count)
    ).limit(limit)
    
    learnings = db.execute(query).scalars().all()
    
    result = []
    for learning in learnings:
        success_rate = (
            learning.success_count / learning.times_applied
            if learning.times_applied > 0
            else 0.0
        )
        
        result.append({
            "id": learning.id,
            "pattern": learning.pattern,
            "context": learning.context,
            "confidence_score": learning.confidence_score,
            "times_applied": learning.times_applied,
            "success_count": learning.success_count,
            "success_rate": success_rate,
            "created_at": learning.created_at.isoformat() if learning.created_at else None
        })
    
    if result:
        logger.info(
            "learnings_queried",
            agent=agent_role.value,
            learning_type=learning_type,
            count=len(result)
        )
    
    return result


def apply_learning(
    db: Session,
    learning_id: str,
    success: bool
) -> None:
    """
    Record that a learning was applied and track its success.
    
    This updates the learning's usage statistics, helping agents identify
    which patterns are most reliable.
    
    Args:
        db: Database session
        learning_id: Learning ID
        success: Whether applying this learning led to success
    
    Example:
        # Agent applies a learned pattern
        learnings = query_learnings(db, AgentRole.RESEARCH, "query_pattern")
        learning_id = learnings[0]["id"]
        
        # Try the learned pattern
        result = execute_with_learned_pattern(learnings[0])
        
        # Record whether it worked
        apply_learning(db, learning_id, success=result.was_successful)
    """
    learning = db.get(JobLearning, learning_id)
    if not learning:
        return
    
    learning.times_applied += 1
    if success:
        learning.success_count += 1
    learning.last_used_at = datetime.now(timezone.utc)
    
    db.commit()
    
    success_rate = learning.success_count / learning.times_applied
    
    logger.info(
        "learning_applied",
        learning_id=learning_id,
        success=success,
        times_applied=learning.times_applied,
        success_rate=success_rate
    )


def analyze_past_jobs(
    db: Session,
    agent_role: AgentRole,
    context_filter: Optional[Dict[str, Any]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Analyze past completed jobs to extract patterns and insights.
    
    This is a higher-level function that looks at completed jobs and
    identifies what strategies worked well.
    
    Args:
        db: Database session
        agent_role: Agent analyzing past jobs
        context_filter: Filter jobs by context (e.g., {"industry": "fitness"})
        limit: Number of past jobs to analyze
    
    Returns:
        Analysis summary with patterns and recommendations
    
    Example:
        # Research agent analyzes past fitness app research jobs
        analysis = analyze_past_jobs(
            db=db,
            agent_role=AgentRole.RESEARCH,
            context_filter={"product_type": "fitness app"}
        )
        
        print(f"Success rate: {analysis['success_rate']}")
        print(f"Common patterns: {analysis['patterns']}")
        print(f"Recommendations: {analysis['recommendations']}")
    """
    # Query completed jobs
    query = select(Job).where(
        Job.status == JobStatus.COMPLETED
    ).order_by(desc(Job.completed_at)).limit(limit)
    
    jobs = db.execute(query).scalars().all()
    
    if not jobs:
        return {
            "jobs_analyzed": 0,
            "success_rate": 0.0,
            "patterns": [],
            "recommendations": []
        }
    
    # Analyze agent tasks for this agent role
    successful_tasks = 0
    total_tasks = 0
    patterns = []
    
    for job in jobs:
        task_query = select(AgentTask).where(
            and_(
                AgentTask.job_id == job.id,
                AgentTask.agent_role == agent_role
            )
        )
        tasks = db.execute(task_query).scalars().all()
        
        for task in tasks:
            total_tasks += 1
            if task.status == TaskStatus.COMPLETED:
                successful_tasks += 1
                
                # Extract patterns from successful tasks
                if task.output_payload:
                    # Look for patterns in output
                    if "iterations" in task.output_payload:
                        patterns.append({
                            "type": "iteration_count",
                            "value": task.output_payload["iterations"],
                            "job_id": job.id
                        })
                    if "confidence_score" in task.output_payload:
                        patterns.append({
                            "type": "confidence",
                            "value": task.output_payload["confidence_score"],
                            "job_id": job.id
                        })
    
    success_rate = successful_tasks / total_tasks if total_tasks > 0 else 0.0
    
    # Generate recommendations based on patterns
    recommendations = []
    if success_rate > 0.8:
        recommendations.append("Current strategies are working well - continue with similar approach")
    elif success_rate < 0.5:
        recommendations.append("Low success rate - consider trying different strategies")
    
    # Analyze iteration patterns
    iteration_counts = [p["value"] for p in patterns if p["type"] == "iteration_count"]
    if iteration_counts:
        avg_iterations = sum(iteration_counts) / len(iteration_counts)
        if avg_iterations > 2:
            recommendations.append(f"Average {avg_iterations:.1f} iterations - consider more targeted initial queries")
    
    result = {
        "jobs_analyzed": len(jobs),
        "total_tasks": total_tasks,
        "successful_tasks": successful_tasks,
        "success_rate": success_rate,
        "patterns": patterns[:10],  # Limit to top 10
        "recommendations": recommendations
    }
    
    logger.info(
        "past_jobs_analyzed",
        agent=agent_role.value,
        jobs_analyzed=len(jobs),
        success_rate=success_rate
    )
    
    return result


def get_similar_past_jobs(
    db: Session,
    current_context: Dict[str, Any],
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find similar past jobs based on context.
    
    Useful for agents to see how similar problems were solved before.
    
    Args:
        db: Database session
        current_context: Current job context (product, audience, goals, etc.)
        limit: Number of similar jobs to return
    
    Returns:
        List of similar job summaries
    
    Example:
        # Find similar fitness app jobs
        similar_jobs = get_similar_past_jobs(
            db=db,
            current_context={
                "product_type": "fitness app",
                "target_audience": "professionals",
                "goals": "GTM strategy"
            }
        )
        
        for job in similar_jobs:
            print(f"Past job: {job['id']}")
            print(f"Outcome: {job['status']}")
            print(f"Key learnings: {job['learnings']}")
    """
    # Query completed jobs
    query = select(Job).where(
        Job.status == JobStatus.COMPLETED
    ).order_by(desc(Job.completed_at)).limit(limit * 2)  # Get more to filter
    
    jobs = db.execute(query).scalars().all()
    
    # Simple similarity scoring based on text matching
    # In production, use vector embeddings for better similarity
    scored_jobs = []
    for job in jobs:
        similarity_score = 0.0
        
        # Check product similarity
        if "product_type" in current_context:
            if current_context["product_type"].lower() in job.product_details.lower():
                similarity_score += 0.4
        
        # Check audience similarity
        if "target_audience" in current_context:
            if current_context["target_audience"].lower() in job.target_audience.lower():
                similarity_score += 0.3
        
        # Check goals similarity
        if "goals" in current_context:
            if current_context["goals"].lower() in job.goals.lower():
                similarity_score += 0.3
        
        if similarity_score > 0.3:  # Threshold for similarity
            scored_jobs.append((job, similarity_score))
    
    # Sort by similarity and take top N
    scored_jobs.sort(key=lambda x: x[1], reverse=True)
    top_jobs = scored_jobs[:limit]
    
    result = []
    for job, score in top_jobs:
        # Get learnings for this job
        learnings_query = select(JobLearning).where(
            JobLearning.job_id == job.id
        )
        learnings = db.execute(learnings_query).scalars().all()
        
        result.append({
            "id": job.id,
            "status": job.status.value,
            "similarity_score": score,
            "product_details": job.product_details[:200],
            "target_audience": job.target_audience[:100],
            "goals": job.goals[:100],
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "learnings": [
                {
                    "pattern": l.pattern,
                    "confidence": l.confidence_score
                }
                for l in learnings[:3]  # Top 3 learnings
            ]
        })
    
    if result:
        logger.info(
            "similar_jobs_found",
            count=len(result),
            avg_similarity=sum(j["similarity_score"] for j in result) / len(result)
        )
    
    return result
