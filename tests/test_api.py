"""
Integration tests for FastAPI endpoints.

Tests API routes with real database but mocked LLM calls.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_sync_session
from app.models import Job, JobStatus, AgentTask, WorkflowLog


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for tests."""
    db = get_sync_session()
    try:
        yield db
    finally:
        db.close()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_submit_analysis_structured_input(client):
    """Test submitting analysis with structured input."""
    payload = {
        "company_description": "ACME Corp",
        "product_details": "AI fitness app",
        "target_audience": "working professionals",
        "goals": "Create GTM strategy",
        "constraints": "Budget under 5000 USD"
    }
    
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code in [200, 202]
    
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert data["status"] in ["pending", "running"]


def test_submit_analysis_raw_prompt(client):
    """Test submitting analysis with raw prompt."""
    payload = {
        "prompt": "We are launching an AI fitness app for professionals in India. Create a GTM strategy."
    }
    
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code in [200, 202]
    
    data = response.json()
    assert "job_id" in data



def test_get_job_status(client, db_session):
    """Test retrieving job status."""
    # Create a test job
    job = Job(
        company_description="Test Corp",
        product_details="Test Product",
        target_audience="Test Audience",
        goals="Test Goals",
        status=JobStatus.PENDING
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    response = client.get(f"/api/v1/status/{job.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job.id
    assert data["status"] == "pending"


def test_get_job_status_not_found(client):
    """Test retrieving non-existent job."""
    response = client.get("/api/v1/status/nonexistent-job-id")
    assert response.status_code == 404


def test_list_jobs(client, db_session):
    """Test listing all jobs."""
    # Create test jobs
    for i in range(3):
        job = Job(
            company_description=f"Company {i}",
            product_details=f"Product {i}",
            target_audience="Audience",
            goals="Goals",
            status=JobStatus.PENDING
        )
        db_session.add(job)
    db_session.commit()
    
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3


def test_get_agent_tasks(client, db_session):
    """Test retrieving agent tasks for a job."""
    # Create job and tasks
    job = Job(
        company_description="Test",
        product_details="Test",
        target_audience="Test",
        goals="Test",
        status=JobStatus.RUNNING
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    from app.models import AgentRole, TaskStatus
    task = AgentTask(
        job_id=job.id,
        agent_role=AgentRole.RESEARCH,
        status=TaskStatus.COMPLETED
    )
    db_session.add(task)
    db_session.commit()
    
    response = client.get(f"/api/v1/agents/{job.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["agent"] == "research"


def test_get_workflow_logs(client, db_session):
    """Test retrieving workflow logs for a job."""
    # Create job and logs
    job = Job(
        company_description="Test",
        product_details="Test",
        target_audience="Test",
        goals="Test",
        status=JobStatus.RUNNING
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    from app.models import AgentRole
    log = WorkflowLog(
        job_id=job.id,
        agent_role=AgentRole.ORCHESTRATOR,
        level="INFO",
        event_type="workflow_start",
        message="Starting workflow"
    )
    db_session.add(log)
    db_session.commit()
    
    response = client.get(f"/api/v1/logs/{job.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["event_type"] == "workflow_start"


def test_cancel_job(client, db_session):
    """Test cancelling a running job."""
    # Create running job
    job = Job(
        company_description="Test",
        product_details="Test",
        target_audience="Test",
        goals="Test",
        status=JobStatus.RUNNING
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    response = client.post(f"/api/v1/cancel/{job.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "aborted"
    
    # Verify job status changed
    db_session.refresh(job)
    assert job.status == JobStatus.ABORTED


def test_cancel_completed_job(client, db_session):
    """Test cancelling an already completed job."""
    # Create completed job
    job = Job(
        company_description="Test",
        product_details="Test",
        target_audience="Test",
        goals="Test",
        status=JobStatus.COMPLETED
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    
    response = client.post(f"/api/v1/cancel/{job.id}")
    assert response.status_code == 400


def test_invalid_payload(client):
    """Test submitting invalid payload."""
    # Missing required fields
    payload = {
        "company_description": "Test"
        # Missing other required fields
    }
    
    response = client.post("/api/v1/analyze", json=payload)
    # Should reject with 400 or 422
    assert response.status_code in [400, 422]


def test_rate_limiting(client):
    """Test API rate limiting."""
    # Make multiple rapid requests
    responses = []
    for _ in range(10):
        response = client.get("/api/v1/health")
        responses.append(response.status_code)
    
    # Should have at least some successful requests
    assert 200 in responses
    # May have rate limit errors (429) if rate limiter is strict
    # This is a basic test - actual rate limiting depends on configuration
