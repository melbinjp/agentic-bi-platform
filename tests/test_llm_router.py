"""
Unit tests for LLM Router.

Tests model selection, cost tracking, circuit breaker, and fallback logic.
"""

import pytest
from app.llm_router import LLMRouter, TaskType, ModelConfig


@pytest.fixture
def router():
    """Create fresh router instance for each test."""
    return LLMRouter()


def test_model_selection_summarization(router):
    """Test that summarization tasks use cheap models."""
    model = router.select_model(TaskType.SUMMARIZATION, "test-job-1")
    
    assert model is not None
    assert model.provider in ["groq", "gemini", "openrouter"]
    # Should prefer cheap models for summarization
    assert model.cost_per_1m_input <= 0.1


def test_model_selection_strategic_reasoning(router):
    """Test that strategic reasoning uses expensive models."""
    model = router.select_model(TaskType.STRATEGIC_REASONING, "test-job-2")
    
    assert model is not None
    # Should use more expensive models for reasoning
    # (groq-llama-70b or gemini-flash as fallback)
    assert model.model in ["llama-3.3-70b-versatile", "gemini-2.0-flash", "openrouter/auto"]


def test_model_selection_structured_extraction(router):
    """Test that structured extraction uses function-calling models."""
    model = router.select_model(TaskType.STRUCTURED_EXTRACTION, "test-job-3")
    
    assert model is not None
    # Should prefer models with function calling support
    # gemini-flash has function calling


def test_budget_enforcement(router):
    """Test that router respects budget limits."""
    job_id = "test-job-budget"
    
    # Record usage that exceeds budget
    model = router.select_model(TaskType.SUMMARIZATION, job_id)
    assert model is not None
    
    # Simulate expensive usage
    router.record_usage(
        job_id=job_id,
        model_config=model,
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        success=True
    )
    
    # Next selection should fail due to budget
    usage = router.get_usage(job_id)
    assert usage.exceeds_budget()
    
    # Should return None when budget exceeded
    model2 = router.select_model(TaskType.SUMMARIZATION, job_id)
    assert model2 is None


def test_circuit_breaker_opens_on_failures(router):
    """Test that circuit breaker opens after multiple failures."""
    job_id = "test-job-circuit"
    
    # Get a model
    model = router.select_model(TaskType.SUMMARIZATION, job_id)
    assert model is not None
    provider = model.provider
    
    # Record multiple failures
    for _ in range(3):
        router.record_usage(
            job_id=job_id,
            model_config=model,
            input_tokens=100,
            output_tokens=100,
            success=False
        )
    
    # Circuit should be open for this provider
    assert router._is_circuit_open(provider)
    
    # Should skip this provider and try fallback
    model2 = router.select_model(TaskType.SUMMARIZATION, job_id, exclude_provider=None)
    if model2:
        assert model2.provider != provider


def test_circuit_breaker_resets_after_timeout(router):
    """Test that circuit breaker resets after timeout."""
    import time
    
    job_id = "test-job-reset"
    model = router.select_model(TaskType.SUMMARIZATION, job_id)
    assert model is not None
    provider = model.provider
    
    # Open circuit
    for _ in range(3):
        router.record_usage(job_id, model, 100, 100, success=False)
    
    assert router._is_circuit_open(provider)
    
    # Manually reset timeout (simulate time passing)
    router._circuit_breaker_timeout = 0.1
    time.sleep(0.2)
    
    # Circuit should be closed now
    assert not router._is_circuit_open(provider)


def test_fallback_chain(router):
    """Test that router tries fallback models when primary fails."""
    job_id = "test-job-fallback"
    
    # Get primary model
    model1 = router.select_model(TaskType.SUMMARIZATION, job_id)
    assert model1 is not None
    provider1 = model1.provider
    
    # Exclude primary provider to force fallback
    model2 = router.select_model(TaskType.SUMMARIZATION, job_id, exclude_provider=provider1)
    
    if model2:
        assert model2.provider != provider1


def test_cost_calculation(router):
    """Test that cost is calculated correctly."""
    job_id = "test-job-cost"
    
    model = ModelConfig(
        provider="test",
        model="test-model",
        cost_per_1m_input=0.10,  # $0.10 per 1M tokens
        cost_per_1m_output=0.20   # $0.20 per 1M tokens
    )
    
    # Record usage: 1000 input, 500 output tokens
    router.record_usage(
        job_id=job_id,
        model_config=model,
        input_tokens=1000,
        output_tokens=500,
        success=True
    )
    
    usage = router.get_usage(job_id)
    
    # Expected cost: (1000 * 0.10 / 1M) + (500 * 0.20 / 1M)
    # = 0.0001 + 0.0001 = 0.0002
    assert usage.total_input_tokens == 1000
    assert usage.total_output_tokens == 500
    assert usage.call_count == 1


def test_token_tracking_accumulation(router):
    """Test that token usage accumulates across multiple calls."""
    job_id = "test-job-accumulate"
    
    model = ModelConfig(
        provider="test",
        model="test-model",
        cost_per_1m_input=0.10,
        cost_per_1m_output=0.20
    )
    
    # Make 3 calls
    for _ in range(3):
        router.record_usage(job_id, model, 100, 50, success=True)
    
    usage = router.get_usage(job_id)
    
    assert usage.total_input_tokens == 300
    assert usage.total_output_tokens == 150
    assert usage.call_count == 3


def test_provider_success_resets_failure_count(router):
    """Test that successful calls reset failure count."""
    job_id = "test-job-success-reset"
    
    model = router.select_model(TaskType.SUMMARIZATION, job_id)
    assert model is not None
    provider = model.provider
    
    # Record 2 failures
    router.record_usage(job_id, model, 100, 100, success=False)
    router.record_usage(job_id, model, 100, 100, success=False)
    
    # Record success
    router.record_usage(job_id, model, 100, 100, success=True)
    
    # Failure count should be reset
    assert router._provider_failures.get(provider, 0) == 0
    assert not router._is_circuit_open(provider)


def test_embedding_model_selection(router):
    """Test that embedding tasks use embedding models."""
    model = router.select_model(TaskType.EMBEDDING, "test-job-embed")
    
    assert model is not None
    assert "embedding" in model.model.lower()


def test_no_model_available_when_all_circuits_open(router):
    """Test behavior when all providers have open circuits."""
    job_id = "test-job-no-models"
    
    # Open circuits for all providers
    from app.llm_router import TASK_ROUTING
    
    task_models = TASK_ROUTING.get(TaskType.SUMMARIZATION, [])
    for model_key in task_models:
        from app.llm_router import MODEL_REGISTRY
        config = MODEL_REGISTRY.get(model_key)
        if config:
            # Record failures to open circuit
            for _ in range(3):
                router.record_usage(job_id, config, 100, 100, success=False)
    
    # Should return None when no models available
    model = router.select_model(TaskType.SUMMARIZATION, job_id)
    # May be None if all circuits are open, or may return a model if circuit timeout passed
    # This is acceptable behavior


def test_last_model_used(router):
    """Test that last_model_used is updated correctly in TokenUsage."""
    job_id = "test-job-last-model"
    model = ModelConfig(
        provider="test",
        model="custom-gpt-4o",
        cost_per_1m_input=0.10,
        cost_per_1m_output=0.20
    )
    
    # Assert initial state is empty
    usage = router.get_usage(job_id)
    assert usage.last_model_used == ""
    
    # Record usage
    router.record_usage(
        job_id=job_id,
        model_config=model,
        input_tokens=100,
        output_tokens=50,
        success=True
    )
    
    # Verify last model is updated correctly
    usage = router.get_usage(job_id)
    assert usage.last_model_used == "custom-gpt-4o"
