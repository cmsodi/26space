"""
LLM (Anthropic) client and API call wrappers.
"""

import os
import time
from typing import Optional

import anthropic

from .config import MODEL_DEFAULT
from .errors import FatalError, with_retry, with_retry_async, RETRY_POLICY_API
from .logging_setup import logger


# ============== SYNC CLIENT ==============

_client: Optional[anthropic.Anthropic] = None


def get_client() -> anthropic.Anthropic:
    """Lazy initialization of Anthropic client."""
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _llm_call_inner(
    client: anthropic.Anthropic,
    system: str,
    user: str,
    max_tokens: int,
    model: str,
    temperature: float
) -> str:
    """Inner LLM call (no retry). Used by with_retry wrapper."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response


def llm_call(
    system: str,
    user: str,
    max_tokens: int = 4096,
    model: str = MODEL_DEFAULT,
    temperature: float = 0.7,
    retry: bool = True
) -> str:
    """
    LLM call wrapper with automatic retry for transient errors.

    Args:
        system: System prompt
        user: User message
        max_tokens: Max response tokens (default 4096)
        model: Model to use (default MODEL_DEFAULT)
        temperature: Sampling temperature (default 0.7)
        retry: Enable automatic retry (default True)

    Returns:
        Response text

    Raises:
        FatalError: If API call fails after retries
        RuntimeError: If API call fails (retry=False)
    """
    client = get_client()
    model_short = model.split("-")[1] if "-" in model else model

    logger.debug(f"LLM call: model={model_short}, max_tokens={max_tokens}, temp={temperature}")
    logger.debug(f"  System prompt: {len(system)} chars, User prompt: {len(user)} chars")

    start_time = time.time()

    def do_call():
        return _llm_call_inner(client, system, user, max_tokens, model, temperature)

    try:
        if retry:
            response = with_retry(do_call, RETRY_POLICY_API, f"LLM call ({model_short})")
        else:
            response = do_call()

        elapsed = time.time() - start_time
        result = response.content[0].text

        # Log usage stats
        input_tokens = getattr(response.usage, 'input_tokens', 0)
        output_tokens = getattr(response.usage, 'output_tokens', 0)
        logger.debug(f"  Response: {len(result)} chars, {output_tokens} tokens in {elapsed:.2f}s")
        logger.debug(f"  Usage: input={input_tokens}, output={output_tokens} tokens")

        return result

    except FatalError:
        raise
    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        raise RuntimeError(f"Anthropic API error: {e}")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise RuntimeError(f"LLM call failed: {e}")


# ============== ASYNC CLIENT ==============

_async_client: Optional[anthropic.AsyncAnthropic] = None


def get_async_client() -> anthropic.AsyncAnthropic:
    """Lazy initialization of async Anthropic client."""
    global _async_client
    if _async_client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")
        _async_client = anthropic.AsyncAnthropic(api_key=api_key)
    return _async_client


async def _llm_call_async_inner(
    client: anthropic.AsyncAnthropic,
    system: str,
    user: str,
    max_tokens: int,
    model: str,
    temperature: float
):
    """Inner async LLM call (no retry). Used by with_retry_async wrapper."""
    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user}]
    )
    return response


async def llm_call_async(
    system: str,
    user: str,
    max_tokens: int = 4096,
    model: str = MODEL_DEFAULT,
    temperature: float = 0.7,
    retry: bool = True
) -> str:
    """
    Async LLM call wrapper with automatic retry for transient errors.

    Args:
        system: System prompt
        user: User message
        max_tokens: Max response tokens (default 4096)
        model: Model to use (default MODEL_DEFAULT)
        temperature: Sampling temperature (default 0.7)
        retry: Enable automatic retry (default True)

    Returns:
        Response text

    Raises:
        FatalError: If API call fails after retries
        RuntimeError: If API call fails (retry=False)
    """
    client = get_async_client()
    model_short = model.split("-")[1] if "-" in model else model

    logger.debug(f"Async LLM call: model={model_short}, max_tokens={max_tokens}")

    start_time = time.time()

    async def do_call():
        return await _llm_call_async_inner(client, system, user, max_tokens, model, temperature)

    try:
        if retry:
            response = await with_retry_async(do_call, RETRY_POLICY_API, f"Async LLM call ({model_short})")
        else:
            response = await do_call()

        elapsed = time.time() - start_time
        result = response.content[0].text

        input_tokens = getattr(response.usage, 'input_tokens', 0)
        output_tokens = getattr(response.usage, 'output_tokens', 0)
        logger.debug(f"  Async response: {len(result)} chars, {output_tokens} tokens in {elapsed:.2f}s")

        return result

    except FatalError:
        raise
    except anthropic.APIError as e:
        logger.error(f"Async Anthropic API error: {e}")
        raise RuntimeError(f"Anthropic API error: {e}")
    except Exception as e:
        logger.error(f"Async LLM call failed: {e}")
        raise RuntimeError(f"Async LLM call failed: {e}")
