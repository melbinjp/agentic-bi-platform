"""
Memory Agent - Context Storage & Retrieval

Responsibilities:
  - Store agent outputs into vector DB for semantic recall
  - Store structured facts into the relational state ledger
  - Retrieve relevant past context given a query
  - Summarise stored context to prevent context bloat

Assignment requirement:
  - Memory Agent (dedicated agent role)
  - Section B: Conversation memory, persistent vector memory, retrieval, context recall
"""

import structlog
from typing import Optional
from sqlalchemy.orm import Session

from app.llm_client import call_llm, get_embedding
from app.llm_router import TaskType
from app.memory.vector_store import upsert_document, query_similar
from app.security import check_tool_permission

logger = structlog.get_logger()

AGENT_ROLE = "memory"

SYSTEM_PROMPT = """You are the Memory Agent for a multi-agent business intelligence platform.
Your sole responsibility is to summarise information clearly and concisely for storage and retrieval.
When given raw agent output, produce a compact, factual summary that preserves all key insights.
Do not add opinions or strategies — only compress and clarify what was provided.
"""


async def store(
    job_id: str,
    content: str,
    source_agent: str,
    collection: str = "research_findings",
) -> Optional[str]:
    """
    Embed and store a piece of content in the vector store.

    Args:
        job_id: Parent job ID for namespacing
        content: Text content to embed and store
        source_agent: Which agent produced this content
        collection: ChromaDB collection name

    Returns:
        Document ID if stored, None on failure.
    """
    if not check_tool_permission(AGENT_ROLE, "vector_store_upsert"):
        return None

    # First: summarise to avoid storing bloated raw outputs
    summary = await call_llm(
        task_type=TaskType.SUMMARIZATION,
        job_id=job_id,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=f"Summarise this for storage (keep all key facts):\n\n{content}",
    )
    text_to_store = summary or content  # fallback to raw if summarisation fails

    embedding = await get_embedding(text_to_store, job_id)
    if embedding is None:
        logger.error("memory_store_failed_no_embedding", job_id=job_id, source=source_agent)
        return None

    doc_id = upsert_document(
        collection_name=f"{job_id}_{collection}",
        text=text_to_store,
        embedding=embedding,
        metadata={"job_id": job_id, "source_agent": source_agent},
    )

    logger.info("memory_stored", job_id=job_id, doc_id=doc_id, source=source_agent)
    return doc_id


async def recall(
    job_id: str,
    query: str,
    collection: str = "research_findings",
    n_results: int = 3,
) -> list[str]:
    """
    Retrieve semantically relevant documents from the vector store.

    Args:
        job_id: Parent job ID for namespacing
        query: Natural language query to match against stored content
        collection: ChromaDB collection to search
        n_results: How many results to return

    Returns:
        List of matching document strings (most relevant first).
    """
    if not check_tool_permission(AGENT_ROLE, "vector_store_query"):
        return []

    embedding = await get_embedding(query, job_id)
    if embedding is None:
        logger.error("memory_recall_failed_no_embedding", job_id=job_id)
        return []

    results = query_similar(
        collection_name=f"{job_id}_{collection}",
        query_embedding=embedding,
        n_results=n_results,
    )

    docs = [r["document"] for r in results]
    logger.info("memory_recalled", job_id=job_id, query_preview=query[:60], count=len(docs))
    return docs


async def run(job_id: str, payload: dict) -> dict:
    """
    Main entry point called by the Orchestrator.

    Payload keys:
      - action: "store" | "recall"
      - content: (for store) text to embed
      - query: (for recall) retrieval query
      - source_agent: (for store) agent that produced the content
      - collection: optional collection name
    """
    action = payload.get("action")
    collection = payload.get("collection", "research_findings")

    if action == "store":
        content = payload.get("content", "")
        source_agent = payload.get("source_agent", "unknown")
        doc_id = await store(job_id, content, source_agent, collection)
        return {"status": "stored", "doc_id": doc_id}

    elif action == "recall":
        query = payload.get("query", "")
        n = payload.get("n_results", 3)
        docs = await recall(job_id, query, collection, n)
        return {"status": "recalled", "documents": docs}

    else:
        logger.error("memory_unknown_action", action=action, job_id=job_id)
        return {"status": "error", "message": f"Unknown action: {action}"}
