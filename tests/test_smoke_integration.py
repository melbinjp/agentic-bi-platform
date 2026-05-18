import asyncio
import json
import pytest
from app.database import get_sync_session
from app.models import Job, JobStatus


@pytest.mark.asyncio
async def test_end_to_end_orchestration(monkeypatch):
    """End-to-end orchestration smoke test using stubbed LLMs and vector-store.

    This test runs the `orchestrator.run` flow asynchronously against a local SQLite
    DB, with `call_llm`, `get_embedding`, and the vector store operations mocked
    to deterministic values. It validates the workflow completes and the job
    record is updated to `COMPLETED` with a final report structure.
    """

    # --- Stub LLM client functions ---
    from app.llm_router import TaskType


    async def fake_call_llm(task_type, job_id, system_prompt, user_prompt, temperature=None):
        t = task_type
        if t == TaskType.SUMMARIZATION:
            return "Research summary: key facts."
        if t == TaskType.STRATEGIC_REASONING:
            return "Strategy report: do X, measure Y."
        if t == TaskType.CRITIQUE:
            # Critic must return JSON string
            return json.dumps({
                "verdict": "APPROVED",
                "score": 9,
                "issues": [],
                "improvement_prompt": "",
            })
        if t == TaskType.STRUCTURED_EXTRACTION:
            # Used by Planner and QA — return planner JSON structure
            return json.dumps({
                "execution_plan": {
                    "phase_30_days": [{
                        "task": "Onboard early users",
                        "owner": "Founders",
                        "priority": "HIGH",
                        "kpi": "10 signups",
                        "dependencies": [],
                    }],
                    "phase_60_days": [],
                    "phase_90_days": [],
                },
                "critical_path": ["Onboard early users"],
                "success_metrics": {"30_day": "10 signups"},
            })
        # Default fallback
        return "OK"


    async def fake_get_embedding(text, job_id):
        return [0.01] * 8


    monkeypatch.setattr("app.llm_client.call_llm", fake_call_llm)
    monkeypatch.setattr("app.llm_client.get_embedding", fake_get_embedding)

    # --- Stub vector store operations ---
    def fake_upsert(collection_name, text, embedding, metadata=None, doc_id=None):
        return "docid-test"


    def fake_query(collection_name, query_embedding, n_results=5, where=None):
        return [{
            "id": "docid-test",
            "document": "Previously stored research summary.",
            "metadata": {},
            "distance": 0.1,
        }]


    monkeypatch.setattr("app.memory.vector_store.upsert_document", fake_upsert)
    monkeypatch.setattr("app.memory.vector_store.query_similar", fake_query)

    # --- Create job in DB ---
    db = get_sync_session()
    try:
        job = Job(
            company_description="ACME corp",
            product_details="AI fitness app",
            target_audience="working professionals",
            goals="Create GTM strategy",
            constraints="Budget < 5000 USD",
            status="pending",
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id

        # Run orchestrator
        from app.agents.orchestrator import run as orchestrator_run

        result = await orchestrator_run(job_id, db)

        # Reload job from DB and assert completion
        db.refresh(job)
        assert job.status == JobStatus.COMPLETED
        assert isinstance(result, dict)
        assert "strategy" in result
        assert "execution_plan" in result
    finally:
        db.close()
