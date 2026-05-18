"""
Agent Communication via Blackboard Pattern

Enables agents to communicate with each other through the blackboard (database).
Agents write messages to the blackboard, other agents read and respond.

This maintains the blackboard architecture while enabling true agent collaboration.
"""

import structlog
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models import AgentMessage, AgentRole

logger = structlog.get_logger()


def send_message(
    db: Session,
    job_id: str,
    from_agent: AgentRole,
    to_agent: Optional[AgentRole],
    message_type: str,
    subject: str,
    content: Dict[str, Any],
    in_response_to: Optional[str] = None
) -> str:
    """
    Send a message from one agent to another via the blackboard.
    
    Args:
        db: Database session
        job_id: Job ID
        from_agent: Sending agent role
        to_agent: Receiving agent role (None = broadcast to all)
        message_type: "request", "response", "broadcast", "notification"
        subject: Brief message subject
        content: Message payload (flexible JSON structure)
        in_response_to: ID of message this is responding to
    
    Returns:
        Message ID
    
    Example:
        # Research agent requests help from Strategy agent
        msg_id = send_message(
            db=db,
            job_id=job_id,
            from_agent=AgentRole.RESEARCH,
            to_agent=AgentRole.STRATEGY,
            message_type="request",
            subject="Need pricing strategy guidance",
            content={
                "question": "What pricing models work for fitness apps?",
                "context": {"market": "B2C", "audience": "professionals"}
            }
        )
    """
    message = AgentMessage(
        job_id=job_id,
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        subject=subject,
        content=content,
        in_response_to=in_response_to,
        is_read=0
    )
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    logger.info(
        "agent_message_sent",
        job_id=job_id,
        from_agent=from_agent.value,
        to_agent=to_agent.value if to_agent else "broadcast",
        message_type=message_type,
        subject=subject
    )
    
    return message.id


def read_messages(
    db: Session,
    job_id: str,
    to_agent: AgentRole,
    mark_as_read: bool = True,
    unread_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Read messages addressed to a specific agent from the blackboard.
    
    Args:
        db: Database session
        job_id: Job ID
        to_agent: Agent role reading messages
        mark_as_read: Whether to mark messages as read
        unread_only: Only return unread messages
    
    Returns:
        List of message dictionaries
    
    Example:
        # Strategy agent checks for messages
        messages = read_messages(
            db=db,
            job_id=job_id,
            to_agent=AgentRole.STRATEGY
        )
        
        for msg in messages:
            if msg["message_type"] == "request":
                # Process request and send response
                response = generate_response(msg["content"])
                send_message(
                    db=db,
                    job_id=job_id,
                    from_agent=AgentRole.STRATEGY,
                    to_agent=msg["from_agent"],
                    message_type="response",
                    subject=f"Re: {msg['subject']}",
                    content=response,
                    in_response_to=msg["id"]
                )
    """
    query = select(AgentMessage).where(
        and_(
            AgentMessage.job_id == job_id,
            AgentMessage.to_agent == to_agent
        )
    )
    
    if unread_only:
        query = query.where(AgentMessage.is_read == 0)
    
    query = query.order_by(AgentMessage.created_at)
    
    messages = db.execute(query).scalars().all()
    
    result = []
    for msg in messages:
        result.append({
            "id": msg.id,
            "from_agent": msg.from_agent.value,
            "to_agent": msg.to_agent.value if msg.to_agent else None,
            "message_type": msg.message_type,
            "subject": msg.subject,
            "content": msg.content,
            "in_response_to": msg.in_response_to,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        })
        
        if mark_as_read and msg.is_read == 0:
            msg.is_read = 1
            msg.read_at = datetime.now(timezone.utc)
    
    if mark_as_read and messages:
        db.commit()
    
    if result:
        logger.info(
            "agent_messages_read",
            job_id=job_id,
            agent=to_agent.value,
            count=len(result)
        )
    
    return result


def broadcast_message(
    db: Session,
    job_id: str,
    from_agent: AgentRole,
    subject: str,
    content: Dict[str, Any]
) -> str:
    """
    Broadcast a message to all agents.
    
    Useful for sharing findings or notifications.
    
    Example:
        # Research agent shares findings with all agents
        broadcast_message(
            db=db,
            job_id=job_id,
            from_agent=AgentRole.RESEARCH,
            subject="Key competitor findings",
            content={
                "competitors": ["Competitor A", "Competitor B"],
                "key_insight": "Market is highly competitive"
            }
        )
    """
    return send_message(
        db=db,
        job_id=job_id,
        from_agent=from_agent,
        to_agent=None,  # None = broadcast
        message_type="broadcast",
        subject=subject,
        content=content
    )


def get_conversation_thread(
    db: Session,
    message_id: str
) -> List[Dict[str, Any]]:
    """
    Get entire conversation thread for a message.
    
    Returns the original message and all responses in chronological order.
    
    Example:
        # Get full conversation about a request
        thread = get_conversation_thread(db, original_message_id)
        # Returns: [original_request, response1, response2, ...]
    """
    # Get original message
    original = db.get(AgentMessage, message_id)
    if not original:
        return []
    
    # Find root message if this is a response
    root_id = original.in_response_to or message_id
    
    # Get all messages in thread
    query = select(AgentMessage).where(
        or_(
            AgentMessage.id == root_id,
            AgentMessage.in_response_to == root_id
        )
    ).order_by(AgentMessage.created_at)
    
    messages = db.execute(query).scalars().all()
    
    return [
        {
            "id": msg.id,
            "from_agent": msg.from_agent.value,
            "to_agent": msg.to_agent.value if msg.to_agent else None,
            "message_type": msg.message_type,
            "subject": msg.subject,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() if msg.created_at else None
        }
        for msg in messages
    ]
