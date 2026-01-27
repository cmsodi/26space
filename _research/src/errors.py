"""
Error handling and retry logic for the Strategic Orchestrator.
"""

import asyncio
import time
from dataclasses import dataclass

from .logging_setup import logger


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class RetryableError(OrchestratorError):
    """
    Transient error that can be retried.
    Examples: rate limits, timeouts, network errors
    """
    pass


class FatalError(OrchestratorError):
    """
    Permanent error that cannot be recovered.
    Examples: invalid API key, malformed input, missing files
    """
    pass


class AnalystError(OrchestratorError):
    """Error during analyst execution."""
    def __init__(self, analyst_name: str, message: str, retryable: bool = True):
        self.analyst_name = analyst_name
        self.retryable = retryable
        super().__init__(f"{analyst_name}: {message}")


@dataclass
class RetryPolicy:
    """
    Configurable retry policy with exponential backoff.

    Attributes:
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds (default 1.0)
        max_delay: Maximum delay cap in seconds (default 60.0)
        exponential_base: Multiplier for exponential backoff (default 2.0)
        jitter: Add randomness to prevent thundering herd (default True)
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number (0-indexed)."""
        import random
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        if self.jitter:
            delay = delay * (0.5 + random.random())
        return delay


# Default policies for different operations
RETRY_POLICY_API = RetryPolicy(max_retries=3, base_delay=1.0, max_delay=30.0)
RETRY_POLICY_ANALYST = RetryPolicy(max_retries=2, base_delay=2.0, max_delay=60.0)
RETRY_POLICY_EXA = RetryPolicy(max_retries=2, base_delay=1.0, max_delay=15.0)


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable based on type and message.

    Retryable conditions:
    - Rate limit errors (429)
    - Timeout errors
    - Temporary network errors
    - Server errors (500-599)
    - Overloaded errors
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()

    # Explicit retryable patterns
    retryable_patterns = [
        "rate_limit", "rate limit", "429",
        "timeout", "timed out", "time out",
        "overloaded", "overload",
        "connection", "network",
        "500", "502", "503", "504",
        "server error", "internal error",
        "temporarily unavailable",
        "try again",
    ]

    # Check against patterns
    for pattern in retryable_patterns:
        if pattern in error_str or pattern in error_type:
            return True

    # Check for anthropic-specific errors
    if hasattr(error, 'status_code'):
        status = getattr(error, 'status_code')
        if status in (429, 500, 502, 503, 504, 529):
            return True

    return False


def classify_error(error: Exception) -> OrchestratorError:
    """
    Classify a generic exception into RetryableError or FatalError.
    """
    if isinstance(error, OrchestratorError):
        return error

    if is_retryable_error(error):
        return RetryableError(str(error))

    return FatalError(str(error))


def with_retry(
    func,
    policy: RetryPolicy = RETRY_POLICY_API,
    operation_name: str = "operation"
):
    """
    Execute a function with retry logic.

    Args:
        func: Callable to execute (no arguments)
        policy: RetryPolicy to use
        operation_name: Name for logging

    Returns:
        Result of func()

    Raises:
        FatalError: If all retries exhausted or non-retryable error
    """
    last_error = None

    for attempt in range(policy.max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e

            if not is_retryable_error(e):
                logger.error(f"{operation_name} failed (non-retryable): {e}")
                raise FatalError(f"{operation_name} failed: {e}")

            if attempt < policy.max_retries:
                delay = policy.calculate_delay(attempt)
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{policy.max_retries + 1}): {e}"
                )
                logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
            else:
                logger.error(
                    f"{operation_name} failed after {policy.max_retries + 1} attempts: {e}"
                )

    raise FatalError(f"{operation_name} failed after {policy.max_retries + 1} attempts: {last_error}")


async def with_retry_async(
    coro_func,
    policy: RetryPolicy = RETRY_POLICY_API,
    operation_name: str = "operation"
):
    """
    Execute an async coroutine with retry logic.

    Args:
        coro_func: Callable that returns a coroutine
        policy: RetryPolicy to use
        operation_name: Name for logging

    Returns:
        Result of awaiting coro_func()

    Raises:
        FatalError: If all retries exhausted or non-retryable error
    """
    last_error = None

    for attempt in range(policy.max_retries + 1):
        try:
            return await coro_func()
        except Exception as e:
            last_error = e

            if not is_retryable_error(e):
                logger.error(f"{operation_name} failed (non-retryable): {e}")
                raise FatalError(f"{operation_name} failed: {e}")

            if attempt < policy.max_retries:
                delay = policy.calculate_delay(attempt)
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{policy.max_retries + 1}): {e}"
                )
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"{operation_name} failed after {policy.max_retries + 1} attempts: {e}"
                )

    raise FatalError(f"{operation_name} failed after {policy.max_retries + 1} attempts: {last_error}")
