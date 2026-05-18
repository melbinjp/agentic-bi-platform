"""
LLM Router - Intelligent Multi-Model Routing

Routes tasks to the optimal model/provider based on task type.
Implements fallback chains, cost tracking, and latency optimization.

Assignment requirement: Section E - LLM Routing
  - Cost optimization
  - Latency optimization
  - Model selection logic
  - Fallback handling
"""

import time
import structlog
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from app.config import settings

logger = structlog.get_logger()


class TaskType(str, Enum):
    """Categories of tasks that map to different model tiers."""
    SUMMARIZATION = "summarization"          # Cheap, fast
    STRATEGIC_REASONING = "strategic_reasoning"  # Expensive, high-quality
    STRUCTURED_EXTRACTION = "structured_extraction"  # Function calling
    CRITIQUE = "critique"                    # Separate evaluator model
    ORCHESTRATION = "orchestration"          # Routing decisions
    EMBEDDING = "embedding"                  # Vector embeddings


@dataclass
class ModelConfig:
    """Configuration for a specific model endpoint."""
    provider: str
    model: str
    cost_per_1m_input: float  # USD per 1M input tokens
    cost_per_1m_output: float  # USD per 1M output tokens
    max_tokens: int = 4096
    temperature: float = 0.7
    supports_function_calling: bool = False


@dataclass
class TokenUsage:
    """Tracks token usage and cost for a single job."""
    job_id: str
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    call_count: int = 0
    last_model_used: str = ""

    def add_usage(self, input_tokens: int, output_tokens: int, cost: float, model: str = ""):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
        self.call_count += 1
        if model:
            self.last_model_used = model

    def exceeds_budget(self) -> bool:
        return (
            self.total_cost_usd >= settings.max_dollars_per_job
            or (self.total_input_tokens + self.total_output_tokens) >= settings.max_tokens_per_job
        )


# ============================================================
# Model Registry - All available models and their configs
# ============================================================

MODEL_REGISTRY: dict[str, ModelConfig] = {
    # --- Tier 1 (Fast & Cheap) ---
    "groq-llama-8b": ModelConfig(
        provider="groq",
        model="llama-3.1-8b-instant",
        cost_per_1m_input=0.05,  # Real Groq pricing
        cost_per_1m_output=0.08,
        max_tokens=8192,
        temperature=0.7,
        supports_function_calling=False,
    ),
    "gemini-flash": ModelConfig(
        provider="gemini",
        model="gemini-2.0-flash",
        cost_per_1m_input=0.075,  # Real Gemini Flash pricing
        cost_per_1m_output=0.30,
        max_tokens=8192,
        temperature=0.7,
        supports_function_calling=True,
    ),
    "openrouter-free": ModelConfig(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        cost_per_1m_input=0.075,
        cost_per_1m_output=0.30,
        max_tokens=2048,
        temperature=0.7,
    ),
    "openrouter-flash": ModelConfig(
        provider="openrouter",
        model="google/gemini-2.5-flash",
        cost_per_1m_input=0.075,
        cost_per_1m_output=0.30,
        max_tokens=2048,
        temperature=0.7,
    ),
    "openrouter-pro": ModelConfig(
        provider="openrouter",
        model="meta-llama/llama-3.3-70b-instruct",
        cost_per_1m_input=0.59,
        cost_per_1m_output=0.79,
        max_tokens=2048,
        temperature=0.7,
    ),
    # --- Tier 3 (Heavy Reasoning) ---
    "groq-llama-70b": ModelConfig(
        provider="groq",
        model="llama-3.3-70b-versatile",
        cost_per_1m_input=0.59,  # Real Groq 70B pricing
        cost_per_1m_output=0.79,
        max_tokens=8192,
        temperature=0.7,
        supports_function_calling=True,
    ),
    "gemini-pro": ModelConfig(
        provider="gemini",
        model="gemini-2.5-pro",
        cost_per_1m_input=1.25,  # Real Gemini Pro pricing
        cost_per_1m_output=5.00,
        max_tokens=8192,
        temperature=0.7,
        supports_function_calling=True,
    ),
    # --- Embeddings ---
    "gemini-embedding": ModelConfig(
        provider="gemini",
        model="gemini-embedding-001",
        cost_per_1m_input=0.0,
        cost_per_1m_output=0.0,
        max_tokens=2048,
        temperature=0.0,
    ),
    "openrouter-embedding": ModelConfig(
        provider="openrouter",
        model="text-embedding-3-small",
        cost_per_1m_input=0.02,  # Real OpenAI embedding pricing
        cost_per_1m_output=0.0,
        max_tokens=2048,
        temperature=0.0,
    ),
}

# --- Intra-provider Fallback Sequences (Priority Order) ---
GEMINI_FALLBACKS = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]
GROQ_FALLBACKS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "meta-llama/llama-4-scout-17b-16e-instruct"]


# ============================================================
# Task → Model Routing Table
# ============================================================

TASK_ROUTING: dict[TaskType, list[str]] = {
    # Lightweight tasks (Tier 1 -> Tier 2 -> Fallback)
    TaskType.SUMMARIZATION: ["groq-llama-8b", "gemini-flash", "openrouter-flash"],
    TaskType.ORCHESTRATION: ["groq-llama-8b", "gemini-flash", "openrouter-flash"],
    TaskType.STRUCTURED_EXTRACTION: ["gemini-flash", "groq-llama-8b", "openrouter-flash"],
    
    # Complex tasks (Tier 3 -> Tier 2 -> Fallback)
    TaskType.STRATEGIC_REASONING: ["groq-llama-70b", "gemini-flash", "openrouter-pro"],
    TaskType.CRITIQUE: ["groq-llama-70b", "gemini-flash", "openrouter-pro"],
    
    # Embeddings
    TaskType.EMBEDDING: ["openrouter-embedding", "gemini-embedding"],
}


class LLMRouter:
    """
    Intelligent LLM router that selects the optimal model for each task.
    Handles fallback chains, cost tracking, and circuit-breaking.
    """

    def __init__(self):
        self._usage_ledger: dict[str, TokenUsage] = {}
        self._provider_failures: dict[str, int] = {}
        self._provider_circuit_open: dict[str, float] = {}
        self._circuit_breaker_threshold = 3   # failures before opening circuit
        self._circuit_breaker_timeout = 60.0   # seconds before retrying

    def get_usage(self, job_id: str) -> TokenUsage:
        """Get or create token usage tracker for a job."""
        if job_id not in self._usage_ledger:
            self._usage_ledger[job_id] = TokenUsage(job_id=job_id)
        return self._usage_ledger[job_id]

    def _is_circuit_open(self, provider: str) -> bool:
        """Check if a provider's circuit breaker is open (too many failures)."""
        if provider not in self._provider_circuit_open:
            return False
        opened_at = self._provider_circuit_open[provider]
        if time.time() - opened_at > self._circuit_breaker_timeout:
            # Reset circuit breaker after timeout (half-open state)
            del self._provider_circuit_open[provider]
            self._provider_failures[provider] = 0
            logger.info("circuit_breaker_reset", provider=provider)
            return False
        return True

    def _record_failure(self, provider: str):
        """Record a provider failure and potentially open the circuit breaker."""
        self._provider_failures[provider] = self._provider_failures.get(provider, 0) + 1
        if self._provider_failures[provider] >= self._circuit_breaker_threshold:
            self._provider_circuit_open[provider] = time.time()
            logger.warning(
                "circuit_breaker_opened",
                provider=provider,
                failure_count=self._provider_failures[provider],
            )

    def _record_success(self, provider: str):
        """Reset failure count on success."""
        self._provider_failures[provider] = 0

    def select_model(self, task_type: TaskType, job_id: str, exclude_provider: Optional[str] = None) -> Optional[ModelConfig]:
        """
        Select the best available model for a given task type.

        Considers:
          - Task-to-model routing table
          - Circuit breaker state per provider
          - Job budget limits
          - exclude_provider (used for immediate fallback)

        Returns None if budget exceeded or no models available.
        """
        usage = self.get_usage(job_id)

        # Budget guard
        if usage.exceeds_budget():
            logger.error(
                "budget_exceeded",
                job_id=job_id,
                total_cost=usage.total_cost_usd,
                total_tokens=usage.total_input_tokens + usage.total_output_tokens,
            )
            return None

        model_keys = TASK_ROUTING.get(task_type, [])

        for model_key in model_keys:
            config = MODEL_REGISTRY.get(model_key)
            if config is None:
                continue
            if exclude_provider and config.provider == exclude_provider:
                continue
            if self._is_circuit_open(config.provider):
                logger.info("skipping_provider", provider=config.provider, reason="circuit_open")
                continue
            logger.info(
                "model_selected",
                task_type=task_type.value,
                provider=config.provider,
                model=config.model,
                job_id=job_id,
            )
            return config

        logger.error("no_model_available", task_type=task_type.value, job_id=job_id)
        return None

    def record_usage(
        self,
        job_id: str,
        model_config: ModelConfig,
        input_tokens: int,
        output_tokens: int,
        success: bool = True,
    ):
        """Record token usage and update circuit breaker state."""
        import json
        import os
        
        cost = 0.0
        try:
            import litellm
            from litellm import cost_per_token
            
            model_name_for_cost = model_config.model
            if model_config.provider == "openrouter":
                model_name_for_cost = f"openrouter/{model_config.model}"
            elif model_config.provider == "groq":
                model_name_for_cost = f"groq/{model_config.model}"
            elif model_config.provider == "gemini":
                model_name_for_cost = f"gemini/{model_config.model}"

            cost, _ = cost_per_token(
                model=model_name_for_cost,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens
            )
        except Exception as e:
            logger.debug("litellm_cost_failed", model=model_config.model)
            
            # Fallback to custom_pricing.json
            try:
                pricing_path = os.path.join(os.path.dirname(__file__), "custom_pricing.json")
                if os.path.exists(pricing_path):
                    with open(pricing_path, "r") as f:
                        custom_pricing = json.load(f)
                    
                    # Try to lookup model
                    lookup_key = f"{model_config.provider}/{model_config.model}"
                    if lookup_key in custom_pricing:
                        rates = custom_pricing[lookup_key]
                        cost = (input_tokens * rates["input_cost_per_token"]) + (output_tokens * rates["output_cost_per_token"])
                    else:
                        logger.warning("model_not_in_custom_pricing", model=lookup_key)
                        cost = 0.0
            except Exception as read_e:
                logger.error("custom_pricing_read_failed", error=str(read_e))
                cost = 0.0

        usage = self.get_usage(job_id)
        usage.add_usage(input_tokens, output_tokens, cost, model_config.model)

        if success:
            self._record_success(model_config.provider)
        else:
            self._record_failure(model_config.provider)

        logger.info(
            "usage_recorded",
            job_id=job_id,
            provider=model_config.provider,
            model=model_config.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=f"${cost:.6f}",
            cumulative_cost=f"${usage.total_cost_usd:.6f}",
        )


# Singleton router instance
llm_router = LLMRouter()
