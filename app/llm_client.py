"""
LLM Clients - Provider-specific API wrappers

Wraps Gemini and Groq behind a unified async interface.
Both SDKs are synchronous — wrapped in asyncio.to_thread() to avoid blocking the event loop.
"""

import asyncio
import structlog
import math
from typing import Optional
# Hardening build 2026-05-16
from google import genai
from groq import Groq

from app.config import settings
from app.llm_router import ModelConfig, TaskType, llm_router
import json
import hashlib

logger = structlog.get_logger()

# Simple in-memory caches to protect quotas
_LLM_CACHE: dict[str, str] = {}
_EMBED_CACHE: dict[str, list[float]] = {}

def _generate_cache_key(*args) -> str:
    """Generate a deterministic hash key for caching."""
    key_str = json.dumps(args, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()



async def stateful_summarize(text: str, job_id: str, max_chunks: int = 3) -> str:
    """
    Stateful rolling-window summarizer. 
    Splits text into a maximum of 3 chunks to protect RPM limits, 
    and passes the previous summary along with the next chunk to preserve context.
    """
    if not text:
        return ""
        
    text_len = len(text)
    # If text is small, process it in a single safe request (roughly < 1000 tokens)
    if text_len <= 5000:
        return text

    # Calculate optimal chunk size to split into max 3 pieces
    chunk_size = math.ceil(text_len / max_chunks)
    chunks = [text[i:i + chunk_size] for i in range(0, text_len, chunk_size)]
    
    current_summary = ""
    
    logger.info("stateful_summarization_triggered", job_id=job_id, text_len=text_len, chunks=len(chunks))
    
    for idx, chunk in enumerate(chunks):
        system_prompt = (
            "You are a precise, stateful business intelligence analyst.\n"
            "Your task is to compile a highly dense, structured facts sheet.\n"
            "Preserve all pricing metrics, percentages, currency metrics, and competitor names."
        )
        
        # Build stateful user prompt
        if idx == 0:
            user_prompt = f"Analyze the first segment of the report and extract a dense fact sheet:\n\n{chunk}"
        else:
            user_prompt = (
                f"Here is the dense fact sheet from the previous segments:\n"
                f"### CURRENT FACT SHEET:\n{current_summary}\n\n"
                f"--- \n\n"
                f"Now, analyze the next segment of the report. UPDATE and INTEGRATE all new findings, "
                f"metrics, and competitor details into the existing fact sheet. Do not lose the previous findings:\n\n{chunk}"
            )
            
        updated_summary = await call_llm(
            task_type=TaskType.STRUCTURED_EXTRACTION,
            job_id=job_id,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.1
        )
        
        if updated_summary:
            current_summary = updated_summary.strip()
            
    logger.info("stateful_summarization_complete", job_id=job_id, summary_len=len(current_summary))
    return current_summary


async def call_llm(
    task_type: TaskType,
    job_id: str,
    system_prompt: str,
    user_prompt: str,
    temperature: Optional[float] = None,
) -> Optional[str]:
    """
    Unified LLM call interface with robust multi-provider fallback.
    Loops through available models for the task until one succeeds or all fail.
    """
    exclude_providers = []
    
    while True:
        # Select the best model, excluding previously failed providers in this loop
        model_config = llm_router.select_model(task_type, job_id)
        
        # If we already tried this provider and it failed, we need to manually skip it
        # or rely on the circuit breaker. However, to force immediate fallback across
        # multiple models, we'll use a modified selection strategy or track exclusions.
        
        # Actually, let's just get the list of models and try them one by one.
        from app.llm_router import TASK_ROUTING, MODEL_REGISTRY
        logger.info("routing_table_check", keys=[k.name for k in TASK_ROUTING.keys()], looking_for=task_type.name)
        model_keys = TASK_ROUTING.get(task_type, [])
        logger.info("routing_debug", task_type=task_type, model_keys=model_keys)
        
        for model_key in model_keys:
            config = MODEL_REGISTRY.get(model_key)
            if not config:
                logger.warning("model_not_in_registry", model_key=model_key)
                continue
                
            if config.provider in exclude_providers:
                logger.info("skipping_failed_provider", provider=config.provider)
                continue
            
            temp = temperature if temperature is not None else config.temperature
            
            # --- Check cache first to protect free-tier quota ---
            cache_key = _generate_cache_key(config.model, system_prompt, user_prompt, temp)
            if cache_key in _LLM_CACHE:
                logger.info("llm_cache_hit", model=config.model, job_id=job_id)
                return _LLM_CACHE[cache_key]
            
            try:
                logger.info("attempting_llm_call", provider=config.provider, model=config.model, job_id=job_id)
                
                if config.provider == "gemini":
                    res, i_tok, o_tok = await _call_gemini(config, system_prompt, user_prompt, temp, job_id=job_id)
                elif config.provider == "groq":
                    res, i_tok, o_tok = await _call_groq(config, system_prompt, user_prompt, temp, job_id=job_id)
                elif config.provider == "openrouter":
                    res, i_tok, o_tok = await _call_openrouter(config, system_prompt, user_prompt, temp, job_id=job_id)
                else:
                    logger.warning("unknown_provider", provider=config.provider)
                    continue

                llm_router.record_usage(job_id, config, i_tok, o_tok, success=True)
                _LLM_CACHE[cache_key] = res
                return res

            except Exception as e:
                error_msg = str(e)
                logger.error(
                    "provider_failed",
                    provider=config.provider,
                    model=config.model,
                    error=error_msg,
                    job_id=job_id,
                )
                llm_router.record_usage(job_id, config, 0, 0, success=False)
                exclude_providers.append(config.provider)
                continue
        
        logger.error("all_models_failed_final", task_type=task_type.value, job_id=job_id)
        return None


async def _dispatch_call(
    model_config: ModelConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    job_id: str,
) -> Optional[str]:
    """Dispatch a call to the appropriate provider (used for fallback)."""
    cache_key = _generate_cache_key(model_config.model, system_prompt, user_prompt, temperature)
    if cache_key in _LLM_CACHE:
        logger.info("llm_cache_hit", model=model_config.model, job_id=job_id)
        return _LLM_CACHE[cache_key]

    try:
        if model_config.provider == "gemini":
            text, i_tok, o_tok = await _call_gemini(model_config, system_prompt, user_prompt, temperature)
        elif model_config.provider == "groq":
            text, i_tok, o_tok = await _call_groq(model_config, system_prompt, user_prompt, temperature)
        elif model_config.provider == "openrouter":
            text, i_tok, o_tok = await _call_openrouter(model_config, system_prompt, user_prompt, temperature)
        else:
            return None

        llm_router.record_usage(job_id, model_config, i_tok, o_tok, success=True)
        _LLM_CACHE[cache_key] = text
        return text
    except Exception as e:
        logger.error("fallback_also_failed", error=str(e))
        llm_router.record_usage(job_id, model_config, 0, 0, success=False)
        return None


async def _call_gemini(
    config: ModelConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    job_id: str = "unknown"
) -> tuple[str, int, int]:
    """
    Call Google Gemini API with verified intra-provider fallbacks and exponential backoff retry on 429s.
    """
    from app.llm_router import GEMINI_FALLBACKS
    from app.observability import workflow_logger
    
    models_to_try = [config.model] + [m for m in GEMINI_FALLBACKS if m != config.model]
    
    last_error = None
    for idx, model_name in enumerate(models_to_try):
        retries = 3
        delay = 3.0
        for attempt in range(retries):
            try:
                if idx > 0 and attempt == 0:
                    workflow_logger.info(
                        job_id=job_id,
                        agent="system",
                        message=f"Gemini fallback triggered: Switching to {model_name}",
                        details={"primary_model": config.model, "current_model": model_name}
                    )

                def _sync_call():
                    client = genai.Client(api_key=settings.gemini_api_key)
                    return client.models.generate_content(
                        model=model_name,
                        contents=user_prompt,
                        config=genai.types.GenerateContentConfig(
                            system_instruction=system_prompt,
                            temperature=temperature,
                            max_output_tokens=config.max_tokens,
                        ),
                    )

                response = await asyncio.to_thread(_sync_call)
                text = response.text or ""
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
                return text, input_tokens, output_tokens

            except Exception as e:
                last_error = e
                err_str = str(e)
                # Check for rate limits, but distinguish transient rate limits from hard quota/resource exhaustion
                is_rate_limit = "429" in err_str or "quota" in err_str.lower() or "resource_exhausted" in err_str.lower()
                is_hard_quota = "quota exceeded" in err_str.lower() or "quota_exceeded" in err_str.lower() or "resource_exhausted" in err_str.lower()
                is_static_size = "413" in err_str or "too large" in err_str.lower() or "context_length" in err_str.lower() or "request payload" in err_str.lower()
                
                if is_rate_limit and not is_static_size and not is_hard_quota:
                    if attempt < retries - 1:
                        logger.warning(
                            "gemini_rate_limited_retrying",
                            model=model_name,
                            attempt=attempt + 1,
                            delay=delay,
                            error=err_str
                        )
                        await asyncio.sleep(delay)
                        delay *= 2.0
                        continue
                logger.warning("gemini_variant_failed", model=model_name, error=err_str)
                break  # If not a retryable rate-limit error or all retries failed, switch to fallback model
            
    raise last_error

async def _call_groq(
    config: ModelConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    job_id: str = "unknown"
) -> tuple[str, int, int]:
    """
    Call Groq API with verified intra-provider fallbacks and exponential backoff retry on 429s.
    """
    from app.llm_router import GROQ_FALLBACKS
    from app.observability import workflow_logger

    models_to_try = [config.model] + [m for m in GROQ_FALLBACKS if m != config.model]

    last_error = None
    for idx, model_name in enumerate(models_to_try):
        retries = 3
        delay = 3.0
        for attempt in range(retries):
            try:
                if idx > 0 and attempt == 0:
                    workflow_logger.info(
                        job_id=job_id,
                        agent="system",
                        message=f"Groq fallback triggered: Switching to {model_name}",
                        details={"primary_model": config.model, "current_model": model_name}
                    )

                def _sync_call():
                    client = Groq(api_key=settings.groq_api_key)
                    return client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=temperature,
                        max_tokens=config.max_tokens,
                    )

                response = await asyncio.to_thread(_sync_call)
                text = response.choices[0].message.content or ""
                input_tokens = response.usage.prompt_tokens if response.usage else 0
                output_tokens = response.usage.completion_tokens if response.usage else 0
                return text, input_tokens, output_tokens

            except Exception as e:
                last_error = e
                err_str = str(e)
                # Check for rate limits, but distinguish transient rate limits from hard quota/resource exhaustion
                is_rate_limit = "429" in err_str or "limit exceeded" in err_str.lower() or "rate_limit" in err_str.lower()
                is_hard_quota = "quota" in err_str.lower() or "quota_exceeded" in err_str.lower() or "resource_exhausted" in err_str.lower() or "exhausted" in err_str.lower()
                is_static_size = "413" in err_str or "too large" in err_str.lower() or "context_length" in err_str.lower() or "request payload" in err_str.lower() or "tpm" in err_str.lower()
                
                if is_rate_limit and not is_static_size and not is_hard_quota:
                    if attempt < retries - 1:
                        logger.warning(
                            "groq_rate_limited_retrying",
                            model=model_name,
                            attempt=attempt + 1,
                            delay=delay,
                            error=err_str
                        )
                        await asyncio.sleep(delay)
                        delay *= 2.0
                        continue
                logger.warning("groq_variant_failed", model=model_name, error=err_str)
                break  # If not a rate limit error or retries exhausted, switch to fallback model

    raise last_error



async def _call_openrouter(
    config: ModelConfig,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    job_id: str = "unknown"
) -> tuple[str, int, int]:
    """Execute call via OpenRouter API."""
    import httpx
    if not settings.openrouter_api_key:
        raise ValueError("Missing OpenRouter API Key")
        
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
                "max_tokens": config.max_tokens or 2048
            },
            timeout=45.0
        )
        response.raise_for_status()
        data = response.json()
        
        text = data["choices"][0]["message"]["content"]
        i_tok = data.get("usage", {}).get("prompt_tokens", 0)
        o_tok = data.get("usage", {}).get("completion_tokens", 0)
        return text, i_tok, o_tok


async def get_embedding(text: str, job_id: str) -> Optional[list[float]]:
    """
    Generate embeddings using OpenRouter (text-embedding-3-small).
    Bypasses Gemini completely since the API key was invalid.
    """
    cache_key = _generate_cache_key("embedding", text)
    if cache_key in _EMBED_CACHE:
        logger.info("embed_cache_hit", job_id=job_id)
        return _EMBED_CACHE[cache_key]

    import httpx
    if not settings.openrouter_api_key:
        logger.error("missing_openrouter_key", job_id=job_id)
        return [0.0] * 768

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "text-embedding-3-small",
                    "input": text
                },
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            if "data" in data and len(data["data"]) > 0:
                vector = data["data"][0]["embedding"]
                _EMBED_CACHE[cache_key] = vector
                return vector
            else:
                logger.warning("empty_openrouter_embedding", job_id=job_id)
                return [0.0] * 768
    except Exception as e:
        logger.error("openrouter_embedding_failed", error=str(e), job_id=job_id)
        return [0.0] * 768
