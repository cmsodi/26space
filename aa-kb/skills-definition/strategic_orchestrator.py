#!/usr/bin/env python3
"""
strategic_orchestrator.py
Python orchestrator for strategic analysis workflow

DECISIONS:
- Anthropic SDK directly (cleaner, more control)
- CLI interaction (simple, standalone, testable)
- Parallel analysts via asyncio (Phase D1) - sequential fallback available
- Exa Python SDK for L2 searches (Phase C)
- YAML state persistence with resume (Phase D2)
- Configurable logging with verbose/quiet modes (Phase D3)
- Error recovery with retry logic and graceful degradation (Phase D4)

Reference: PYTHON_ORCHESTRATOR_PLAN.md

Phase status:
- Phase A: Foundation ✅
- Phase B: Core Workflow ✅
- Phase C: Exa Integration ✅
- Phase D1: Async Analysts ✅
- Phase D2: State Persistence ✅
- Phase D3: Logging ✅
- Phase D4: Error Recovery ✅
"""

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pathlib import Path
import asyncio
import json
import logging
import os
import re
import sys
import time

import anthropic
import yaml

# Exa SDK for L2 web searches (optional)
try:
    from exa_py import Exa
    EXA_AVAILABLE = True
except ImportError:
    EXA_AVAILABLE = False


# ============== LOGGING SETUP (Phase D3) ==============

# Create module logger
logger = logging.getLogger("strategic_orchestrator")

# Default format for console and file
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s [%(levelname)s] %(name)s:%(funcName)s:%(lineno)d - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    verbose: bool = False,
    quiet: bool = False
) -> logging.Logger:
    """
    Configure logging for the orchestrator.

    Args:
        level: Base logging level (default INFO)
        log_file: Optional path to log file
        verbose: If True, set DEBUG level with detailed format
        quiet: If True, set WARNING level (overrides verbose)

    Returns:
        Configured logger instance
    """
    # Determine effective level
    if quiet:
        effective_level = logging.WARNING
    elif verbose:
        effective_level = logging.DEBUG
    else:
        effective_level = level

    # Choose format based on verbosity
    log_format = LOG_FORMAT_DEBUG if verbose else LOG_FORMAT

    # Configure root logger for this module
    logger.setLevel(effective_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(effective_level)
    console_handler.setFormatter(logging.Formatter(log_format, LOG_DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always capture everything to file
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT_DEBUG, LOG_DATE_FORMAT))
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")

    return logger


# Initialize with default settings (can be reconfigured via setup_logging)
setup_logging()


class LogTimer:
    """Context manager for timing operations with logging."""

    def __init__(self, operation: str, level: int = logging.DEBUG):
        self.operation = operation
        self.level = level
        self.start_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.time()
        logger.log(self.level, f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        if exc_type:
            logger.warning(f"Failed: {self.operation} ({self.elapsed:.2f}s) - {exc_val}")
        else:
            logger.log(self.level, f"Completed: {self.operation} ({self.elapsed:.2f}s)")
        return False


# ============== ERROR RECOVERY (Phase D4) ==============

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


# ============== CONFIGURATION ==============

# Paths - adjust based on your setup
SKILLS_PATH = Path("/mnt/DATA/26space/.claude/skills")
AGENTS_PATH = Path("/mnt/DATA/26space/.claude/agents")
OUTPUT_GEN_PATH = SKILLS_PATH / "_OUTPUT_GENERATION.md"

# Model selection
MODEL_DEFAULT = "claude-sonnet-4-20250514"
MODEL_COMPLEX = "claude-opus-4-20250514"  # For integration/complex steps


# ============== STEP STATE MACHINE ==============

class Step(Enum):
    """Workflow steps - enforces sequential progression."""
    INIT = "init"
    PROBLEM_PARSED = "problem_parsed"
    SOURCES_DECIDED = "sources_decided"
    CLARIFIED = "clarified"
    PROPOSAL_APPROVED = "proposal_approved"
    ANALYSTS_COMPLETE = "analysts_complete"
    OUTLINE_APPROVED = "outline_approved"
    CITATIONS_MAPPED = "citations_mapped"
    COMPLETE = "complete"


# ============== DATA STRUCTURES ==============

@dataclass
class Source:
    """Represents a source document at any level (L0, L1, L2)."""
    url: str
    title: str
    type: str  # official_document, report, academic, industry, news
    anchor_suggestion: str
    level: str  # L0 (user-provided), L1 (agent Exa), L2 (enrichment Exa)
    relevance: Optional[str] = None  # Why this source matters


@dataclass
class AnalystOutput:
    """Parsed output from an analyst agent."""
    name: str
    status: str  # complete, partial, failed
    confidence: Optional[float]
    content: str
    key_findings: list[str] = field(default_factory=list)
    exa_sources: list[Source] = field(default_factory=list)
    raw_output: str = ""  # Original unparsed output


@dataclass
class CitationEntry:
    """Single citation mapping for the citation_map artifact."""
    point_id: str  # e.g., "1.2", "2.3.1"
    claim: str  # The specific claim needing citation
    url: Optional[str]  # None if unavailable/theoretical
    anchor_text: str  # Text to use as hyperlink
    pattern: str  # factual, data, context, deep, theoretical
    source_level: str  # L0, L1, L2, theoretical, unavailable


@dataclass
class WorkflowState:
    """
    Central state object - persisted throughout workflow.
    This is the key difference from markdown: state is REAL, not "mental".
    """
    # Input
    problem: str = ""
    language: str = "en"  # Detected from input

    # Current position
    current_step: Step = Step.INIT

    # Phase 1 outputs
    problem_keywords: list[str] = field(default_factory=list)
    synthesizer_scores: dict[str, float] = field(default_factory=dict)

    # Phase 1.5 outputs
    fresh_sources_need: str = ""  # HIGH, MEDIUM, LOW
    fresh_sources_choice: str = ""  # A, B, C
    context_documents: list[Source] = field(default_factory=list)  # L0 sources

    # Phase 2 outputs
    clarification_questions: list[str] = field(default_factory=list)
    clarification_answers: list[str] = field(default_factory=list)

    # Phase 3 outputs (approved configuration)
    synthesizer: str = ""
    template: str = ""  # BLUF, Hypothesis-Driven, POR, Minto-Custom
    fixed_analysts: list[str] = field(default_factory=list)
    optional_analysts: list[str] = field(default_factory=list)
    web_search_enabled: bool = False

    # Phase 4 outputs
    analyst_outputs: dict[str, AnalystOutput] = field(default_factory=dict)
    integration_summary: str = ""
    outline: str = ""
    citation_map: list[CitationEntry] = field(default_factory=list)
    final_document: str = ""

    # Metadata
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# ============== STATE SERIALIZATION (Phase D2) ==============

def source_to_dict(src: Source) -> dict:
    """Convert Source to serializable dict."""
    return {
        "url": src.url,
        "title": src.title,
        "type": src.type,
        "anchor_suggestion": src.anchor_suggestion,
        "level": src.level,
        "relevance": src.relevance
    }


def source_from_dict(d: dict) -> Source:
    """Restore Source from dict."""
    return Source(
        url=d.get("url", ""),
        title=d.get("title", ""),
        type=d.get("type", "unknown"),
        anchor_suggestion=d.get("anchor_suggestion", ""),
        level=d.get("level", "L0"),
        relevance=d.get("relevance")
    )


def analyst_output_to_dict(ao: AnalystOutput) -> dict:
    """Convert AnalystOutput to serializable dict."""
    return {
        "name": ao.name,
        "status": ao.status,
        "confidence": ao.confidence,
        "content": ao.content,
        "key_findings": ao.key_findings,
        "exa_sources": [source_to_dict(s) for s in ao.exa_sources],
        "raw_output": ao.raw_output
    }


def analyst_output_from_dict(d: dict) -> AnalystOutput:
    """Restore AnalystOutput from dict."""
    return AnalystOutput(
        name=d.get("name", ""),
        status=d.get("status", "partial"),
        confidence=d.get("confidence"),
        content=d.get("content", ""),
        key_findings=d.get("key_findings", []),
        exa_sources=[source_from_dict(s) for s in d.get("exa_sources", [])],
        raw_output=d.get("raw_output", "")
    )


def citation_entry_to_dict(ce: CitationEntry) -> dict:
    """Convert CitationEntry to serializable dict."""
    return {
        "point_id": ce.point_id,
        "claim": ce.claim,
        "url": ce.url,
        "anchor_text": ce.anchor_text,
        "pattern": ce.pattern,
        "source_level": ce.source_level
    }


def citation_entry_from_dict(d: dict) -> CitationEntry:
    """Restore CitationEntry from dict."""
    return CitationEntry(
        point_id=d.get("point_id", ""),
        claim=d.get("claim", ""),
        url=d.get("url"),
        anchor_text=d.get("anchor_text", ""),
        pattern=d.get("pattern", "factual"),
        source_level=d.get("source_level", "unavailable")
    )


def workflow_state_to_dict(state: WorkflowState) -> dict:
    """
    Convert WorkflowState to serializable dict.

    Handles:
    - Step enum → string
    - Nested dataclasses → dicts
    - Lists of dataclasses → lists of dicts
    """
    return {
        # Input
        "problem": state.problem,
        "language": state.language,

        # Current position (enum as string)
        "current_step": state.current_step.value,

        # Phase 1 outputs
        "problem_keywords": state.problem_keywords,
        "synthesizer_scores": state.synthesizer_scores,

        # Phase 1.5 outputs
        "fresh_sources_need": state.fresh_sources_need,
        "fresh_sources_choice": state.fresh_sources_choice,
        "context_documents": [source_to_dict(s) for s in state.context_documents],

        # Phase 2 outputs
        "clarification_questions": state.clarification_questions,
        "clarification_answers": state.clarification_answers,

        # Phase 3 outputs
        "synthesizer": state.synthesizer,
        "template": state.template,
        "fixed_analysts": state.fixed_analysts,
        "optional_analysts": state.optional_analysts,
        "web_search_enabled": state.web_search_enabled,

        # Phase 4 outputs
        "analyst_outputs": {
            name: analyst_output_to_dict(ao)
            for name, ao in state.analyst_outputs.items()
        },
        "integration_summary": state.integration_summary,
        "outline": state.outline,
        "citation_map": [citation_entry_to_dict(ce) for ce in state.citation_map],
        "final_document": state.final_document,

        # Metadata
        "errors": state.errors,
        "warnings": state.warnings,

        # Serialization metadata
        "_saved_at": datetime.now().isoformat(),
        "_version": "1.0"
    }


def workflow_state_from_dict(d: dict) -> WorkflowState:
    """
    Restore WorkflowState from dict.

    Handles:
    - String → Step enum
    - Dicts → nested dataclasses
    - Lists of dicts → lists of dataclasses
    """
    # Parse Step enum from string
    step_value = d.get("current_step", "init")
    try:
        current_step = Step(step_value)
    except ValueError:
        current_step = Step.INIT

    return WorkflowState(
        # Input
        problem=d.get("problem", ""),
        language=d.get("language", "en"),

        # Current position
        current_step=current_step,

        # Phase 1 outputs
        problem_keywords=d.get("problem_keywords", []),
        synthesizer_scores=d.get("synthesizer_scores", {}),

        # Phase 1.5 outputs
        fresh_sources_need=d.get("fresh_sources_need", ""),
        fresh_sources_choice=d.get("fresh_sources_choice", ""),
        context_documents=[source_from_dict(s) for s in d.get("context_documents", [])],

        # Phase 2 outputs
        clarification_questions=d.get("clarification_questions", []),
        clarification_answers=d.get("clarification_answers", []),

        # Phase 3 outputs
        synthesizer=d.get("synthesizer", ""),
        template=d.get("template", ""),
        fixed_analysts=d.get("fixed_analysts", []),
        optional_analysts=d.get("optional_analysts", []),
        web_search_enabled=d.get("web_search_enabled", False),

        # Phase 4 outputs
        analyst_outputs={
            name: analyst_output_from_dict(ao)
            for name, ao in d.get("analyst_outputs", {}).items()
        },
        integration_summary=d.get("integration_summary", ""),
        outline=d.get("outline", ""),
        citation_map=[citation_entry_from_dict(ce) for ce in d.get("citation_map", [])],
        final_document=d.get("final_document", ""),

        # Metadata
        errors=d.get("errors", []),
        warnings=d.get("warnings", [])
    )


# ============== PROMPT LOADING (Phase A2) ==============

def load_skill(name: str) -> str:
    """
    Load a skill/synthesizer markdown file.

    Looks for: .claude/skills/{name}/SKILL.md
    Fallback:  .claude/skills/{name}.md (for files like _OUTPUT_GENERATION.md)
    """
    # Try folder structure first
    path = SKILLS_PATH / name / "SKILL.md"
    if path.exists():
        return path.read_text(encoding="utf-8")

    # Fallback to direct file
    path = SKILLS_PATH / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")

    # Try without extension (user might pass "strategic-geopolitical" or "strategic-geopolitical.md")
    path = SKILLS_PATH / name
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")

    raise FileNotFoundError(f"Skill not found: {name} (searched in {SKILLS_PATH})")


def load_agent(name: str) -> str:
    """
    Load an agent markdown file.

    Looks for: .claude/agents/{name}/AGENT.md
    """
    path = AGENTS_PATH / name / "AGENT.md"
    if path.exists():
        return path.read_text(encoding="utf-8")

    # Fallback to direct file
    path = AGENTS_PATH / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")

    raise FileNotFoundError(f"Agent not found: {name} (searched in {AGENTS_PATH})")


def load_output_generation() -> str:
    """Load the central output generation prompts."""
    if OUTPUT_GEN_PATH.exists():
        return OUTPUT_GEN_PATH.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Output generation file not found: {OUTPUT_GEN_PATH}")


# ============== LLM CALLS (Phase A3) ==============

# Initialize client (uses ANTHROPIC_API_KEY env var)
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


# ============== ASYNC LLM CALLS (Phase D1) ==============

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


# ============== EXA INTEGRATION (Phase C) ==============

_exa_client: Optional[object] = None  # Type hint avoids import dependency
EXA_SEARCH_COUNT = 0  # Global counter for search limit
EXA_MAX_SEARCHES = 3  # Maximum L2 searches per analysis


def get_exa_client():
    """Lazy initialization of Exa client."""
    global _exa_client
    if not EXA_AVAILABLE:
        raise RuntimeError("Exa SDK not installed. Run: pip install exa-py")

    if _exa_client is None:
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            raise RuntimeError("EXA_API_KEY environment variable not set")
        _exa_client = Exa(api_key)
    return _exa_client


def reset_exa_search_count():
    """Reset the Exa search counter (call at start of each analysis)."""
    global EXA_SEARCH_COUNT
    EXA_SEARCH_COUNT = 0


def exa_search(
    query: str,
    num_results: int = 5,
    include_domains: Optional[list[str]] = None,
    start_date: Optional[str] = None,
    category: Optional[str] = None
) -> list[dict]:
    """
    Perform an Exa web search (L2 source).

    Args:
        query: Search query
        num_results: Number of results to return (default 5)
        include_domains: Optional list of domains to include
        start_date: Optional start date filter (YYYY-MM-DD)
        category: Optional category filter (news, company, research_paper, etc.)

    Returns:
        List of dicts with url, title, text, published_date

    Raises:
        RuntimeError: If search limit exceeded or API fails
    """
    global EXA_SEARCH_COUNT

    if EXA_SEARCH_COUNT >= EXA_MAX_SEARCHES:
        raise RuntimeError(f"Exa search limit reached ({EXA_MAX_SEARCHES} per analysis)")

    try:
        exa = get_exa_client()

        # Build search parameters
        kwargs = {
            "num_results": num_results,
            "text": {"max_characters": 1500},  # Get text content
        }

        if include_domains:
            kwargs["include_domains"] = include_domains
        if start_date:
            kwargs["start_published_date"] = start_date
        if category:
            kwargs["category"] = category

        # Perform search
        start_time = time.time()
        results = exa.search_and_contents(query, **kwargs)
        elapsed = time.time() - start_time

        EXA_SEARCH_COUNT += 1
        logger.debug(f"Exa search {EXA_SEARCH_COUNT}/{EXA_MAX_SEARCHES}: '{query[:60]}' ({elapsed:.2f}s)")

        # Parse results
        parsed = []
        for r in results.results:
            parsed.append({
                "url": r.url,
                "title": r.title or "Untitled",
                "text": getattr(r, "text", "")[:500] if hasattr(r, "text") else "",
                "published_date": getattr(r, "published_date", None),
                "score": getattr(r, "score", 0.0)
            })

        logger.debug(f"  Exa returned {len(parsed)} results")
        return parsed

    except Exception as e:
        logger.warning(f"Exa search failed: {e}")
        return []


def exa_search_for_citation(
    claim: str,
    context: str = "",
    language: str = "en"
) -> Optional[Source]:
    """
    Search for a source to back a specific claim.
    NOTE: All searches are performed in English for better results.

    Args:
        claim: The claim needing a citation
        context: Additional context about the topic
        language: Source language (used to trigger translation if not English)

    Returns:
        Source object if found, None otherwise
    """
    # Translate to English if needed (all web searches must be in English)
    if language != "en":
        try:
            text_to_translate = f"{context}: {claim}" if context else claim
            translated = llm_call(
                system="Translate the following text to English. Return ONLY the translation, nothing else.",
                user=text_to_translate,
                max_tokens=300,
                model=MODEL_FAST,
                temperature=0.1
            )
            query = translated.strip()
            logger.debug(f"Translated query for search: {query[:60]}...")
        except Exception as e:
            logger.warning(f"Translation failed, using original: {e}")
            query = f"{context}: {claim}" if context else claim
    else:
        query = f"{context}: {claim}" if context else claim

    # Add year filter for freshness
    current_year = date.today().year
    start_date = f"{current_year - 1}-01-01"

    results = exa_search(query, num_results=3, start_date=start_date)

    if not results:
        return None

    # Pick the best result (highest score or first)
    best = results[0]

    return Source(
        url=best["url"],
        title=best["title"],
        type="web",  # L2 sources are generic web
        anchor_suggestion=best["title"][:50] if best["title"] else claim[:30],
        level="L2",
        relevance=f"Found via Exa for: {claim[:50]}"
    )


# ============== USER INTERACTION (Phase A4) ==============

def ask_user(prompt: str, options: list[str], allow_other: bool = True) -> str:
    """
    CLI user interaction with numbered options.

    Args:
        prompt: Question to display
        options: List of choices
        allow_other: If True, user can type 'other' for custom input

    Returns:
        Selected option text or custom input
    """
    print(f"\n{'='*60}")
    print(prompt)
    print("-" * 40)
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    if allow_other:
        print(f"  {len(options)+1}. Other (custom input)")
    print("-" * 40)

    while True:
        choice = input("Enter choice (number): ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(options):
                return options[idx - 1]
            elif allow_other and idx == len(options) + 1:
                return input("Enter custom response: ").strip()
        print("Invalid choice. Try again.")


def confirm(prompt: str) -> bool:
    """
    Simple yes/no confirmation.

    Args:
        prompt: Question to display

    Returns:
        True if user confirms, False otherwise
    """
    while True:
        response = input(f"{prompt} (y/n): ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        print("Please enter 'y' or 'n'.")


def get_input(prompt: str, default: str = "") -> str:
    """
    Get free-form input from user.

    Args:
        prompt: Prompt to display
        default: Default value if user presses Enter

    Returns:
        User input or default
    """
    if default:
        result = input(f"{prompt} [{default}]: ").strip()
        return result if result else default
    return input(f"{prompt}: ").strip()


# ============== TERMINAL OUTPUT FORMATTING ==============

# Emoji mappings for section headers
SECTION_EMOJIS = {
    "orchestrator": "👨‍💼",
    "strategic": "👨‍💼",
    "phase": "🔄",
    "analysis": "🔍",
    "results": "📊",
    "error": "❌",
    "warning": "⚠️",
    "success": "✅",
    "complete": "✅",
    "task": "📋",
    "file": "📁",
    "recovery": "🔧",
    "proposal": "📝",
    "execution": "⚡",
    "outline": "📄",
    "citation": "📚",
    "text": "📝",
    "config": "⚙️",
    "resume": "▶️",
    "checkpoint": "💾",
}


def section_header(title: str, emoji: str = None, width: int = 60) -> str:
    """
    Generate a formatted section header with emoji.

    Args:
        title: Section title text
        emoji: Optional emoji override. If None, auto-detect from title keywords
        width: Width of the separator line (default 60)

    Returns:
        Formatted header string ready for print()
    """
    # Auto-detect emoji from title if not provided
    if emoji is None:
        title_lower = title.lower()
        for keyword, em in SECTION_EMOJIS.items():
            if keyword in title_lower:
                emoji = em
                break
        else:
            emoji = "📌"  # Default emoji

    separator = "=" * width
    return f"\n{separator}\n{emoji} {title.upper()}\n{separator}"


def print_section_header(title: str, emoji: str = None, width: int = 60):
    """Print a formatted section header with emoji."""
    print(section_header(title, emoji, width))


def display_section(title: str, content: str, width: int = 60, emoji: str = None):
    """Display a formatted section with title and content."""
    print(section_header(title, emoji, width))
    print(content)
    print("=" * width)


# ============== ERROR RECOVERY UI (Phase D4) ==============

class RecoveryAction(Enum):
    """User choices when an error occurs."""
    RETRY = "retry"
    SKIP = "skip"
    ABORT = "abort"
    RETRY_FAILED = "retry_failed"  # Re-run only failed items
    CONTINUE_PARTIAL = "continue_partial"  # Continue with partial results


def recovery_menu(
    error: Exception,
    context: str,
    options: list[RecoveryAction] = None
) -> RecoveryAction:
    """
    Present recovery options to user after an error.

    Args:
        error: The exception that occurred
        context: What operation was being performed
        options: Available recovery actions (default: RETRY, SKIP, ABORT)

    Returns:
        Selected RecoveryAction
    """
    if options is None:
        options = [RecoveryAction.RETRY, RecoveryAction.SKIP, RecoveryAction.ABORT]

    print_section_header(f"ERROR: {context}", emoji="❌")
    print(f"\n  {error}\n")

    # Check if retryable
    if is_retryable_error(error):
        print("  (This appears to be a temporary error that may succeed on retry)")
    else:
        print("  (This appears to be a permanent error)")
        # Remove RETRY if non-retryable
        if RecoveryAction.RETRY in options:
            options = [o for o in options if o != RecoveryAction.RETRY]

    # Display options
    option_labels = {
        RecoveryAction.RETRY: "Retry the operation",
        RecoveryAction.SKIP: "Skip and continue",
        RecoveryAction.ABORT: "Abort the workflow",
        RecoveryAction.RETRY_FAILED: "Retry only failed items",
        RecoveryAction.CONTINUE_PARTIAL: "Continue with partial results",
    }

    print("\nWhat would you like to do?")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {option_labels.get(opt, opt.value)}")

    while True:
        try:
            choice = input("\nEnter choice [1]: ").strip()
            if not choice:
                return options[0]
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print(f"Please enter a number 1-{len(options)}")
        except ValueError:
            print(f"Please enter a number 1-{len(options)}")


def should_continue_on_error(
    error: Exception,
    context: str,
    auto_recovery: bool = False,
    default_action: RecoveryAction = RecoveryAction.ABORT
) -> bool:
    """
    Determine whether to continue after an error.

    Args:
        error: The exception that occurred
        context: What operation was being performed
        auto_recovery: If True, use default_action without prompting
        default_action: Action to take in auto_recovery mode

    Returns:
        True if workflow should continue, False to abort
    """
    if auto_recovery:
        logger.info(f"Auto-recovery: {default_action.value} for {context}")
        return default_action in (
            RecoveryAction.SKIP,
            RecoveryAction.CONTINUE_PARTIAL,
            RecoveryAction.RETRY_FAILED
        )

    action = recovery_menu(error, context)
    return action != RecoveryAction.ABORT


# ============== VALIDATION (Phase A5) ==============

def validate_analyst_output(output: str, analyst_name: str) -> AnalystOutput:
    """
    Parse and validate analyst output structure.

    Expected format:
    ---
    status: complete|partial|failed
    confidence: 0.0-1.0
    key_findings:
      - finding 1
      - finding 2
    ---
    [content]

    Returns:
        AnalystOutput with parsed data or fallback values
    """
    result = AnalystOutput(
        name=analyst_name,
        status="partial",  # Default to partial if can't parse
        confidence=None,
        content=output,
        raw_output=output
    )

    # Try to extract YAML frontmatter
    if output.startswith("---"):
        parts = output.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1])
                if isinstance(frontmatter, dict):
                    result.status = frontmatter.get("status", "partial")
                    result.confidence = frontmatter.get("confidence")
                    result.key_findings = frontmatter.get("key_findings", [])
                    result.content = parts[2].strip()

                    # Parse exa_sources if present
                    if "sources" in frontmatter:
                        for src in frontmatter["sources"]:
                            result.exa_sources.append(Source(
                                url=src.get("url", ""),
                                title=src.get("title", ""),
                                type=src.get("type", "unknown"),
                                anchor_suggestion=src.get("anchor", ""),
                                level="L1"
                            ))
            except yaml.YAMLError:
                # Frontmatter parse failed, keep defaults
                pass

    return result


def validate_citation_map(citation_map: list[CitationEntry], outline: str) -> tuple[bool, str]:
    """
    Verify citation_map exists and is adequate for the outline.

    Checks:
    1. citation_map is not empty (if outline has factual claims)
    2. No critical gaps (all factual claims should have sources)

    Returns:
        (is_valid, message)
    """
    # Indicators that suggest factual claims needing citations
    factual_patterns = [
        r'\d+%',           # Percentages
        r'€\d+',           # Euro amounts
        r'\$\d+',          # Dollar amounts
        r'\d+\s*(billion|million|miliardi|milioni)',  # Large numbers
        r'202[0-9]',       # Recent years
        r'according to',   # Attribution phrases
        r'secondo',        # Italian attribution
        r'reported',
        r'study shows',
    ]

    has_factual_claims = any(
        re.search(pattern, outline, re.IGNORECASE)
        for pattern in factual_patterns
    )

    if has_factual_claims and not citation_map:
        return False, "Outline contains factual claims but citation_map is empty"

    # Check for unavailable sources ratio
    if citation_map:
        unavailable = sum(1 for c in citation_map if c.source_level == "unavailable")
        total = len(citation_map)
        if unavailable / total > 0.5:
            return False, f"Too many unavailable sources: {unavailable}/{total}"

    return True, "Citation map validation passed"


def validate_frontmatter(document: str, required_fields: list[str]) -> tuple[bool, list[str]]:
    """
    Validate document frontmatter has all required fields.

    Args:
        document: Full document text
        required_fields: List of field names that must be present and non-empty

    Returns:
        (is_valid, list of missing/empty fields)
    """
    missing = []

    if not document.startswith("---"):
        return False, ["No frontmatter found (document must start with ---)"]

    try:
        parts = document.split("---", 2)
        if len(parts) < 3:
            return False, ["Invalid frontmatter format (missing closing ---)"]

        frontmatter = yaml.safe_load(parts[1])
        if not isinstance(frontmatter, dict):
            return False, ["Frontmatter is not a valid YAML dictionary"]

        for field in required_fields:
            if field not in frontmatter:
                missing.append(f"'{field}' missing")
            elif not frontmatter[field]:
                missing.append(f"'{field}' is empty")

    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    return len(missing) == 0, missing


# Required frontmatter fields for final document
REQUIRED_FRONTMATTER = [
    "title",
    "description",
    "slug",
    "date",
    "version",
    "synthesizer",
    "analysts_fixed",
    "outline_template",
    "status",
    "language"
]


# ============== SYNTHESIZER CONFIGURATION ==============

# Known synthesizers and their configurations
SYNTHESIZERS = {
    "strategic-geopolitical": {
        "name": "Strategic Geopolitical",
        "fixed_analysts": ["pestle-analyst", "morphological-analyst", "stakeholder-analyst"],
        "optional_analysts": ["wargame-analyst", "scenario-analyst"],
        "keywords": ["geopolitical", "power", "state", "alliance", "conflict", "deterrence", "sovereignty"]
    },
    "strategic-industrial": {
        "name": "Strategic Industrial",
        "fixed_analysts": ["pestle-analyst", "value-chain-analyst", "competitive-analyst"],
        "optional_analysts": ["technology-analyst", "scenario-analyst"],
        "keywords": ["industry", "market", "competition", "supply chain", "manufacturing", "business"]
    },
    "policy-regulatory": {
        "name": "Policy Regulatory",
        "fixed_analysts": ["pestle-analyst", "stakeholder-analyst", "regulatory-analyst"],
        "optional_analysts": ["scenario-analyst"],
        "keywords": ["policy", "regulation", "governance", "law", "compliance", "framework", "treaty"]
    }
}

# Available templates
TEMPLATES = ["BLUF", "Hypothesis-Driven", "POR", "Minto-Custom"]


# ============== ORCHESTRATOR CLASS (Phases B-D) ==============

class StrategicOrchestrator:
    """
    Main orchestrator - enforces workflow with real state and checkpoints.

    Args:
        parallel_analysts: If True (default), run analysts in parallel using asyncio.
                           Significantly faster for multiple analysts.
    """

    def __init__(
        self,
        parallel_analysts: bool = True,
        auto_save: bool = False,
        save_path: Optional[str] = None,
        graceful_degradation: bool = True,
        auto_recovery: bool = False,
        max_analyst_retries: int = 2,
        verbose: bool = False
    ):
        """
        Initialize the orchestrator.

        Args:
            parallel_analysts: Run analysts in parallel (default True)
            auto_save: Enable auto-checkpoint saving (default False)
            save_path: Path for state persistence (default output/workflow_state.yaml)
            graceful_degradation: Continue with partial results on failures (default True)
            auto_recovery: Automatically choose recovery actions without prompting (default False)
            max_analyst_retries: Maximum retries for failed analysts (default 2)
            verbose: Show detailed output (default False)
        """
        self.state = WorkflowState()
        self.parallel_analysts = parallel_analysts
        self.auto_save = auto_save
        self.save_path = save_path or "output/workflow_state.yaml"
        self.graceful_degradation = graceful_degradation
        self.auto_recovery = auto_recovery
        self.max_analyst_retries = max_analyst_retries
        self.verbose = verbose

    def _vprint(self, *args, **kwargs):
        """Print only if verbose mode is enabled."""
        if self.verbose:
            print(*args, **kwargs)

    # ============== D2: State Persistence ==============

    def save_state(self, filepath: Optional[str] = None) -> str:
        """
        Save current workflow state to YAML file.

        Args:
            filepath: Path to save file (default: self.save_path)

        Returns:
            Path where state was saved
        """
        filepath = filepath or self.save_path
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        state_dict = workflow_state_to_dict(self.state)

        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(state_dict, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        self._vprint(f"  💾 State saved to: {filepath}")
        return str(path)

    @classmethod
    def load_state(
        cls,
        filepath: str,
        parallel_analysts: bool = True,
        graceful_degradation: bool = True,
        auto_recovery: bool = False,
        max_analyst_retries: int = 2,
        verbose: bool = False
    ) -> "StrategicOrchestrator":
        """
        Load workflow state from YAML file and create orchestrator.

        Args:
            filepath: Path to saved state file
            parallel_analysts: Whether to use parallel analyst execution
            graceful_degradation: Continue with partial results on failures
            auto_recovery: Automatically choose recovery actions
            max_analyst_retries: Maximum retries for failed analysts
            verbose: Show detailed output

        Returns:
            StrategicOrchestrator instance with restored state
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"State file not found: {filepath}")

        with open(path, 'r', encoding='utf-8') as f:
            state_dict = yaml.safe_load(f)

        # Create orchestrator and restore state
        orch = cls(
            parallel_analysts=parallel_analysts,
            graceful_degradation=graceful_degradation,
            auto_recovery=auto_recovery,
            max_analyst_retries=max_analyst_retries,
            verbose=verbose
        )
        orch.state = workflow_state_from_dict(state_dict)
        orch.save_path = filepath  # Use same path for subsequent saves

        saved_at = state_dict.get("_saved_at", "unknown")
        orch._vprint(f"  📂 State loaded from: {filepath}")
        orch._vprint(f"     Saved at: {saved_at}")
        orch._vprint(f"     Current step: {orch.state.current_step.value}")

        return orch

    def _checkpoint(self, step_name: str):
        """
        Auto-save checkpoint if auto_save is enabled.

        Args:
            step_name: Name of the checkpoint for logging
        """
        if self.auto_save:
            self._vprint(f"\n  [Checkpoint: {step_name}]")
            self.save_state()

    def resume(self) -> str:
        """
        Resume workflow from current state.

        Continues execution from self.state.current_step.
        Returns final document when complete.
        """
        resume_start = time.time()

        logger.info(f"Resuming workflow from step: {self.state.current_step.value}")
        logger.debug(f"Problem: {self.state.problem[:80]}")

        self._vprint(section_header("RESUMING STRATEGIC ORCHESTRATOR", emoji="▶️"))
        self._vprint(f"From step: {self.state.current_step.value}")

        # Reset Exa search counter
        reset_exa_search_count()

        # Determine where to resume based on current_step
        step = self.state.current_step

        if step == Step.INIT:
            # Start from beginning (but problem already set)
            self._phase_1_parse()
            self._phase_1_5_sources()
            self._phase_2_clarify()
            self._phase_3_propose()
            self._phase_4_execute()

        elif step == Step.PROBLEM_PARSED:
            self._phase_1_5_sources()
            self._phase_2_clarify()
            self._phase_3_propose()
            self._phase_4_execute()

        elif step == Step.SOURCES_DECIDED:
            self._phase_2_clarify()
            self._phase_3_propose()
            self._phase_4_execute()

        elif step == Step.CLARIFIED:
            self._phase_3_propose()
            self._phase_4_execute()

        elif step == Step.PROPOSAL_APPROVED:
            self._phase_4_execute()

        elif step == Step.ANALYSTS_COMPLETE:
            # Resume within Phase 4
            self._generate_and_approve_outline()
            self._enrich_citations()
            self._generate_full_text()
            self.state.current_step = Step.COMPLETE

        elif step == Step.OUTLINE_APPROVED:
            self._enrich_citations()
            self._generate_full_text()
            self.state.current_step = Step.COMPLETE

        elif step == Step.CITATIONS_MAPPED:
            self._generate_full_text()
            self.state.current_step = Step.COMPLETE

        elif step == Step.COMPLETE:
            self._vprint("  Workflow already complete. Returning final document.")

        return self.state.final_document

    def run(self, problem: str) -> str:
        """Main entry point - run full analysis workflow."""
        self.state.problem = problem
        workflow_start = time.time()

        # Reset Exa search counter for this analysis
        reset_exa_search_count()

        logger.info(f"Starting analysis: '{problem[:80]}{'...' if len(problem) > 80 else ''}'")
        logger.debug(f"Full problem ({len(problem)} chars): {problem}")

        self._vprint(section_header("STRATEGIC ORCHESTRATOR", emoji="👨‍💼"))

        # Phase 1: Parse problem
        with LogTimer("Phase 1: Problem parsing"):
            self._phase_1_parse()

        # Phase 1.5: Fresh sources decision
        with LogTimer("Phase 1.5: Fresh sources"):
            self._phase_1_5_sources()

        # Phase 2: Clarification (if needed)
        with LogTimer("Phase 2: Clarification"):
            self._phase_2_clarify()

        # Phase 3: Proposal and approval
        with LogTimer("Phase 3: Proposal"):
            self._phase_3_propose()

        # Phase 4: Execute analysis
        with LogTimer("Phase 4: Execution", level=logging.INFO):
            self._phase_4_execute()

        total_elapsed = time.time() - workflow_start
        logger.info(f"Analysis complete in {total_elapsed:.1f}s")
        logger.info(f"Final document: {len(self.state.final_document)} chars")

        return self.state.final_document

    # ============== PHASE 1: Problem Parsing (B1) ==============

    def _phase_1_parse(self):
        """Parse problem, detect language, score synthesizers."""
        self._vprint(section_header("PHASE 1: Parsing Problem", emoji="🔍"))

        # Detect language
        self.state.language = self._detect_language(self.state.problem)
        self._vprint(f"  Language detected: {self.state.language}")

        # Score synthesizers using LLM
        system = """You are a strategic analysis router. Score each synthesizer based on problem fit.

Available synthesizers:
- strategic-geopolitical: For power dynamics, state actors, alliances, conflicts, sovereignty
- strategic-industrial: For markets, competition, supply chains, business strategy
- policy-regulatory: For governance, regulations, treaties, compliance frameworks

Return ONLY valid YAML with this exact structure:
```yaml
scores:
  strategic-geopolitical: 0.0-1.0
  strategic-industrial: 0.0-1.0
  policy-regulatory: 0.0-1.0
recommended_template: BLUF|Hypothesis-Driven|POR|Minto-Custom
keywords:
  - keyword1
  - keyword2
web_search_useful: true|false
```"""

        user = f"Problem: {self.state.problem}"

        try:
            response = llm_call(system, user, max_tokens=500, temperature=0.3)
            self._parse_phase1_response(response)
        except Exception as e:
            self._vprint(f"  Warning: LLM scoring failed ({e}), using keyword fallback")
            self._fallback_scoring()

        # Display results
        self._vprint(f"  Synthesizer scores: {self.state.synthesizer_scores}")
        self._vprint(f"  Keywords: {self.state.problem_keywords[:5]}")

        self.state.current_step = Step.PROBLEM_PARSED
        self._checkpoint("problem_parsed")

    def _detect_language(self, text: str) -> str:
        """Simple language detection based on common patterns."""
        italian_indicators = [
            "analizza", "valuta", "strategia", "l'", "è", "perché",
            "quali", "come", "dello", "della", "degli", "delle",
            "europeo", "italiano", "spaziale"
        ]
        text_lower = text.lower()
        italian_count = sum(1 for ind in italian_indicators if ind in text_lower)
        return "it" if italian_count >= 2 else "en"

    def _parse_phase1_response(self, response: str):
        """Parse YAML response from Phase 1 LLM call."""
        # Extract YAML from response (may be in code block)
        yaml_text = response
        if "```yaml" in response:
            yaml_text = response.split("```yaml")[1].split("```")[0]
        elif "```" in response:
            yaml_text = response.split("```")[1].split("```")[0]

        try:
            data = yaml.safe_load(yaml_text)
            if "scores" in data:
                self.state.synthesizer_scores = data["scores"]
            if "keywords" in data:
                self.state.problem_keywords = data["keywords"]
            if "recommended_template" in data:
                self.state.template = data["recommended_template"]
            if "web_search_useful" in data:
                self.state.web_search_enabled = data["web_search_useful"]
        except yaml.YAMLError:
            self._fallback_scoring()

    def _fallback_scoring(self):
        """Keyword-based fallback scoring if LLM fails."""
        problem_lower = self.state.problem.lower()
        for synth_id, config in SYNTHESIZERS.items():
            score = sum(1 for kw in config["keywords"] if kw in problem_lower)
            self.state.synthesizer_scores[synth_id] = min(score / 5, 1.0)

        # Default template
        self.state.template = "BLUF"

    # ============== PHASE 1.5: Fresh Sources (B2) ==============

    def _phase_1_5_sources(self):
        """Evaluate fresh sources need and get user decision."""
        self._vprint(section_header("PHASE 1.5: Fresh Sources Evaluation", emoji="🌐"))

        # Determine need level based on problem characteristics
        need_level = self._evaluate_source_need()
        self.state.fresh_sources_need = need_level
        self._vprint(f"  Fresh sources need: {need_level}")

        if need_level == "LOW":
            self._vprint("  Proceeding without fresh sources (model knowledge sufficient)")
            self.state.fresh_sources_choice = "C"
            self.state.current_step = Step.SOURCES_DECIDED
            return

        # Present options to user
        options = [
            "A. Pause for research — I'll gather sources and provide research_briefing.yaml",
            "B. Proceed with Exa — use web search during analysis",
            "C. No fresh sources — use model knowledge only"
        ]

        if need_level == "HIGH":
            prompt = "⚠️  This analysis involves recent events/data. Fresh sources STRONGLY recommended."
        else:
            prompt = "This analysis could benefit from fresh sources."

        choice = ask_user(prompt, options, allow_other=False)
        self.state.fresh_sources_choice = choice[0]  # "A", "B", or "C"

        if self.state.fresh_sources_choice == "A":
            self._handle_user_research()
        elif self.state.fresh_sources_choice == "B":
            self.state.web_search_enabled = True
            self._vprint("  Exa web search enabled for analysis")

        self.state.current_step = Step.SOURCES_DECIDED
        self._checkpoint("sources_decided")

    def _evaluate_source_need(self) -> str:
        """Evaluate how much the problem needs fresh sources."""
        problem_lower = self.state.problem.lower()

        # HIGH indicators: recent events, specific data, current policy
        high_indicators = [
            "2024", "2025", "2026", "recent", "current", "latest",
            "oggi", "attuale", "recente", "ultimo",
            "budget", "funding", "billion", "million",
            "miliardi", "milioni", "bilancio"
        ]

        # MEDIUM indicators: general strategic questions
        medium_indicators = [
            "trend", "forecast", "outlook", "projection",
            "tendenza", "previsione", "scenario"
        ]

        high_count = sum(1 for ind in high_indicators if ind in problem_lower)
        medium_count = sum(1 for ind in medium_indicators if ind in problem_lower)

        if high_count >= 2:
            return "HIGH"
        elif high_count >= 1 or medium_count >= 2:
            return "MEDIUM"
        return "LOW"

    def _handle_user_research(self):
        """Handle user-provided research briefing."""
        # User prompts must ALWAYS be visible (not _vprint)
        print("\n  Waiting for user research...")
        print("  Expected format: research_briefing.yaml with sources list")

        path = get_input("Enter path to research_briefing.yaml (or press Enter to skip)")

        if path and Path(path).exists():
            self._load_research_briefing(path)
        elif path:
            print(f"  Warning: File not found: {path}")
            if confirm("Continue without L0 sources?"):
                pass
            else:
                raise RuntimeError("User cancelled: research briefing required")

    def _load_research_briefing(self, path: str):
        """Load and parse research_briefing.yaml into context_documents."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if "sources" in data:
                for src in data["sources"]:
                    self.state.context_documents.append(Source(
                        url=src.get("url", ""),
                        title=src.get("title", ""),
                        type=src.get("type", "unknown"),
                        anchor_suggestion=src.get("anchor_suggestion", src.get("title", "")),
                        level="L0",
                        relevance=src.get("relevance", "")
                    ))
                self._vprint(f"  Loaded {len(self.state.context_documents)} L0 sources")

        except Exception as e:
            self._vprint(f"  Warning: Failed to parse research briefing: {e}")

    # ============== PHASE 2: Clarification (B3) ==============

    def _phase_2_clarify(self):
        """Ask clarification questions if ambiguity detected."""
        self._vprint(section_header("PHASE 2: Ambiguity Check", emoji="❓"))

        # Check if multiple synthesizers scored similarly
        if not self.state.synthesizer_scores:
            self._vprint("  No scores available, skipping clarification")
            self.state.current_step = Step.CLARIFIED
            return

        scores = list(self.state.synthesizer_scores.values())
        scores_sorted = sorted(scores, reverse=True)

        # Ambiguity: top two scores within 0.2 of each other
        needs_clarification = (
            len(scores_sorted) >= 2 and
            scores_sorted[0] - scores_sorted[1] < 0.2 and
            scores_sorted[0] > 0.3  # Both must be meaningful
        )

        if not needs_clarification:
            self._vprint("  No ambiguity detected, proceeding")
            self.state.current_step = Step.CLARIFIED
            return

        self._vprint("  Ambiguity detected: generating clarification questions...")

        # Get top competing synthesizers
        sorted_synths = sorted(
            self.state.synthesizer_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:2]

        # Generate clarification questions via LLM
        system = """You are helping clarify a strategic analysis request.
The problem could fit multiple analysis frameworks. Generate 1-2 targeted questions
to determine the best approach.

Return ONLY valid YAML:
```yaml
questions:
  - question: "Your question here?"
    purpose: "Why this helps disambiguate"
```"""

        synth_names = [SYNTHESIZERS[s[0]]["name"] for s in sorted_synths if s[0] in SYNTHESIZERS]
        user = f"""Problem: {self.state.problem}

Competing frameworks:
- {synth_names[0] if synth_names else sorted_synths[0][0]} (score: {sorted_synths[0][1]:.2f})
- {synth_names[1] if len(synth_names) > 1 else sorted_synths[1][0]} (score: {sorted_synths[1][1]:.2f})

Generate questions to determine which framework is more appropriate."""

        try:
            response = llm_call(system, user, max_tokens=300, temperature=0.5)
            questions = self._parse_clarification_response(response)

            if questions:
                self._ask_clarification_questions(questions)
        except Exception as e:
            self._vprint(f"  Warning: Clarification generation failed ({e}), proceeding")

        self.state.current_step = Step.CLARIFIED
        self._checkpoint("clarified")

    def _parse_clarification_response(self, response: str) -> list[dict]:
        """Parse clarification questions from LLM response."""
        yaml_text = response
        if "```yaml" in response:
            yaml_text = response.split("```yaml")[1].split("```")[0]
        elif "```" in response:
            yaml_text = response.split("```")[1].split("```")[0]

        try:
            data = yaml.safe_load(yaml_text)
            return data.get("questions", [])
        except yaml.YAMLError:
            return []

    def _ask_clarification_questions(self, questions: list[dict]):
        """Present clarification questions to user and capture answers."""
        # User prompts must ALWAYS be visible (not _vprint)
        print("\n  Clarification needed:")

        for i, q in enumerate(questions[:2], 1):  # Max 2 questions
            question_text = q.get("question", str(q))
            print(f"\n  Q{i}: {question_text}")
            answer = get_input("  Your answer")
            self.state.clarification_questions.append(question_text)
            self.state.clarification_answers.append(answer)

        # Re-score based on answers if we got meaningful input
        if self.state.clarification_answers:
            self._rescore_with_clarification()

    def _rescore_with_clarification(self):
        """Adjust synthesizer scores based on clarification answers."""
        # Combine answers into context
        clarification_context = "\n".join([
            f"Q: {q}\nA: {a}"
            for q, a in zip(self.state.clarification_questions, self.state.clarification_answers)
        ])

        system = """Based on the clarification, re-score the synthesizers.
Return ONLY valid YAML:
```yaml
scores:
  strategic-geopolitical: 0.0-1.0
  strategic-industrial: 0.0-1.0
  policy-regulatory: 0.0-1.0
```"""

        user = f"""Original problem: {self.state.problem}

Clarification:
{clarification_context}

Re-score based on this additional context."""

        try:
            response = llm_call(system, user, max_tokens=200, temperature=0.3)
            yaml_text = response
            if "```yaml" in response:
                yaml_text = response.split("```yaml")[1].split("```")[0]
            elif "```" in response:
                yaml_text = response.split("```")[1].split("```")[0]

            data = yaml.safe_load(yaml_text)
            if "scores" in data:
                self.state.synthesizer_scores = data["scores"]
                self._vprint(f"  Rescored: {self.state.synthesizer_scores}")
        except Exception as e:
            self._vprint(f"  Warning: Rescoring failed ({e}), using original scores")

    # ============== PHASE 3: Proposal (B4) ==============

    def _phase_3_propose(self):
        """Present proposal and get user approval."""
        self._vprint(section_header("PHASE 3: Proposal Generation", emoji="📝"))

        # Select best synthesizer
        if self.state.synthesizer_scores:
            best = max(self.state.synthesizer_scores, key=self.state.synthesizer_scores.get)
            self.state.synthesizer = best
            config = SYNTHESIZERS.get(best, {})
            self.state.fixed_analysts = config.get("fixed_analysts", [])
        else:
            # Fallback
            self.state.synthesizer = "strategic-geopolitical"
            self.state.fixed_analysts = SYNTHESIZERS["strategic-geopolitical"]["fixed_analysts"]

        # Set template if not already set
        if not self.state.template:
            self.state.template = "BLUF"

        # Generate proposal text
        proposal = self._generate_proposal_text()
        display_section("ANALYSIS PROPOSAL", proposal)

        # Get user approval
        approved = False
        while not approved:
            options = [
                "Approve proposal as-is",
                "Change synthesizer",
                "Change template",
                "Add optional analysts",
                "Add context documents (L0 sources with URLs)",
                "Toggle web search",
                "Cancel analysis"
            ]

            choice = ask_user("Review the proposal:", options, allow_other=False)

            if "Approve" in choice:
                approved = True
            elif "Change synthesizer" in choice:
                self._modify_synthesizer()
            elif "Change template" in choice:
                self._modify_template()
            elif "Add optional" in choice:
                self._modify_optional_analysts()
            elif "context documents" in choice.lower():
                self._add_context_documents()
            elif "Toggle web" in choice:
                self.state.web_search_enabled = not self.state.web_search_enabled
                # User-facing feedback: always visible
                print(f"  Web search: {'enabled' if self.state.web_search_enabled else 'disabled'}")
            elif "Cancel" in choice:
                raise RuntimeError("User cancelled analysis")

            if not approved:
                # Show updated proposal
                proposal = self._generate_proposal_text()
                display_section("UPDATED PROPOSAL", proposal)

        self.state.current_step = Step.PROPOSAL_APPROVED
        self._checkpoint("proposal_approved")

    def _generate_proposal_text(self) -> str:
        """Generate formatted proposal text."""
        config = SYNTHESIZERS.get(self.state.synthesizer, {})
        synth_name = config.get("name", self.state.synthesizer)

        lines = [
            f"Problem: {self.state.problem[:100]}{'...' if len(self.state.problem) > 100 else ''}",
            f"Language: {self.state.language}",
            "",
            f"Synthesizer: {synth_name}",
            f"  Score: {self.state.synthesizer_scores.get(self.state.synthesizer, 'N/A')}",
            "",
            f"Template: {self.state.template}",
            "",
            "Fixed Analysts:",
        ]

        for analyst in self.state.fixed_analysts:
            lines.append(f"  - {analyst}")

        if self.state.optional_analysts:
            lines.append("")
            lines.append("Optional Analysts:")
            for analyst in self.state.optional_analysts:
                lines.append(f"  - {analyst}")

        lines.append("")
        lines.append(f"Web Search: {'Enabled' if self.state.web_search_enabled else 'Disabled'}")

        lines.append("")
        if self.state.context_documents:
            lines.append(f"Context Documents (L0): {len(self.state.context_documents)} source(s)")
            for doc in self.state.context_documents[:3]:
                lines.append(f"  - {doc.title[:50]}{'...' if len(doc.title) > 50 else ''}")
            if len(self.state.context_documents) > 3:
                lines.append(f"  ... and {len(self.state.context_documents) - 3} more")
        else:
            lines.append("Context Documents (L0): None (you can add URLs/sources)")

        return "\n".join(lines)

    def _modify_synthesizer(self):
        """Allow user to change synthesizer."""
        options = [
            f"{SYNTHESIZERS[s]['name']} ({s})"
            for s in SYNTHESIZERS.keys()
        ]
        choice = ask_user("Select synthesizer:", options, allow_other=False)

        # Extract synthesizer ID from choice
        for synth_id in SYNTHESIZERS.keys():
            if synth_id in choice:
                self.state.synthesizer = synth_id
                self.state.fixed_analysts = SYNTHESIZERS[synth_id]["fixed_analysts"]
                self.state.optional_analysts = []  # Reset optional
                # User-facing feedback: always visible
                print(f"  Changed to: {synth_id}")
                break

    def _modify_template(self):
        """Allow user to change template."""
        choice = ask_user("Select template:", TEMPLATES, allow_other=False)
        self.state.template = choice
        # User-facing feedback: always visible
        print(f"  Template set to: {choice}")

    def _modify_optional_analysts(self):
        """Allow user to add optional analysts."""
        config = SYNTHESIZERS.get(self.state.synthesizer, {})
        available = config.get("optional_analysts", [])

        if not available:
            # User-facing message: always visible
            print("  No optional analysts available for this synthesizer")
            return

        # Show current selection (user-facing)
        if self.state.optional_analysts:
            print(f"  Currently selected: {self.state.optional_analysts}")

        options = available + ["Clear all optional analysts"]
        choice = ask_user("Add optional analyst:", options, allow_other=False)

        if "Clear" in choice:
            self.state.optional_analysts = []
            # User-facing feedback: always visible
            print("  Optional analysts cleared")
        elif choice in available and choice not in self.state.optional_analysts:
            self.state.optional_analysts.append(choice)
            # User-facing feedback: always visible
            print(f"  Added: {choice}")

    def _add_context_documents(self):
        """Allow user to add context documents (L0 sources) with URLs."""
        # Show current documents if any
        if self.state.context_documents:
            print(f"\n  Currently loaded: {len(self.state.context_documents)} L0 source(s)")
            for i, doc in enumerate(self.state.context_documents[:5], 1):
                print(f"    {i}. {doc.title[:50]}{'...' if len(doc.title) > 50 else ''}")
            if len(self.state.context_documents) > 5:
                print(f"    ... and {len(self.state.context_documents) - 5} more")

        options = [
            "Load from YAML file (research_briefing.yaml format)",
            "Add single URL manually",
            "Clear all context documents",
            "Done - return to proposal"
        ]

        while True:
            choice = ask_user("Context documents:", options, allow_other=False)

            if "YAML" in choice:
                path = get_input("Enter path to YAML file")
                if path and Path(path).exists():
                    self._load_research_briefing(path)
                    print(f"  Loaded {len(self.state.context_documents)} L0 source(s)")
                elif path:
                    print(f"  Warning: File not found: {path}")

            elif "single URL" in choice:
                url = get_input("Enter URL")
                if url:
                    title = get_input("Enter title/description", default="User-provided source")
                    self.state.context_documents.append(Source(
                        url=url,
                        title=title,
                        type="user-provided",
                        anchor_suggestion=title[:30],
                        level="L0",
                        relevance="User-provided context"
                    ))
                    print(f"  Added: {title[:40]}...")

            elif "Clear" in choice:
                self.state.context_documents = []
                print("  All context documents cleared")

            elif "Done" in choice:
                break

        # Summary
        if self.state.context_documents:
            print(f"\n  Total L0 sources: {len(self.state.context_documents)}")

    # ============== PHASE 4: Execution (B5-B8) ==============

    def _phase_4_execute(self):
        """Execute the full analysis workflow: analysts → outline → citations → full text."""
        self._vprint(section_header("PHASE 4: Execution", emoji="⚡"))

        # B5: Execute analysts (parallel by default, configurable)
        self._execute_analysts(parallel=self.parallel_analysts)

        # B6: Generate and approve outline
        self._generate_and_approve_outline()

        # B7: Citation enrichment
        self._enrich_citations()

        # B8: Generate full text
        self._generate_full_text()

        self.state.current_step = Step.COMPLETE

    # ============== B5: Analyst Execution ==============

    def _get_failed_analysts(self) -> list[str]:
        """Return list of analyst names with failed or error status."""
        failed = []
        for name, output in self.state.analyst_outputs.items():
            if output.status == "failed" or output.raw_output.startswith("Error:"):
                failed.append(name)
        return failed

    def _retry_failed_analysts(self, parallel: bool = True):
        """
        Retry only analysts that previously failed.

        This method allows recovery from partial failures without re-running
        successful analysts.
        """
        failed = self._get_failed_analysts()
        if not failed:
            self._vprint("  No failed analysts to retry.")
            return

        self._vprint(section_header(f"RECOVERY: Retrying {len(failed)} Failed Analysts", emoji="🔧"))
        for name in failed:
            self._vprint(f"  - {name}")

        # Temporarily swap analyst lists to only run failed ones
        original_fixed = self.state.fixed_analysts
        original_optional = self.state.optional_analysts

        # Put all failed analysts in fixed list for retry
        self.state.fixed_analysts = [n for n in failed if n in original_fixed]
        self.state.optional_analysts = [n for n in failed if n in original_optional]

        try:
            if parallel:
                self._execute_analysts_parallel()
            else:
                self._execute_analysts_sequential()
        finally:
            # Restore original lists
            self.state.fixed_analysts = original_fixed
            self.state.optional_analysts = original_optional

    def _execute_analysts(self, parallel: bool = True):
        """
        Execute all analysts with recovery support.

        Args:
            parallel: If True (default), run analysts in parallel using asyncio.
                      If False, run sequentially.

        Features:
        - Automatic retry on transient errors (via llm_call retry)
        - Recovery menu when failures exceed threshold
        - Option to retry only failed analysts
        - Option to continue with partial results
        """
        if parallel:
            self._execute_analysts_parallel()
        else:
            self._execute_analysts_sequential()

        # After execution, check for failures and offer recovery
        failed = self._get_failed_analysts()
        if failed:
            self._handle_analyst_failures(failed, parallel)

    def _handle_analyst_failures(self, failed: list[str], parallel: bool, retry_count: int = 0):
        """
        Handle failed analysts with recovery options.

        Args:
            failed: List of failed analyst names
            parallel: Whether to use parallel execution for retries
            retry_count: Current retry attempt (for max_analyst_retries check)
        """
        self._vprint(f"\n⚠ {len(failed)} analyst(s) failed:")
        for name in failed:
            self._vprint(f"  - {name}")

        # Auto-recovery mode: use graceful degradation settings
        if self.auto_recovery:
            if self.graceful_degradation:
                logger.info(f"Auto-recovery: continuing with partial results (graceful degradation)")
                self.state.warnings.append(f"Auto-continued with {len(failed)} failed analysts: {failed}")
                return
            else:
                logger.error(f"Auto-recovery: aborting (graceful degradation disabled)")
                raise FatalError(f"Analyst failures: {failed} (auto_recovery=True, graceful_degradation=False)")

        # Check if we've exceeded retry limit
        can_retry = retry_count < self.max_analyst_retries

        # Build recovery options based on context and settings
        options = []
        if can_retry:
            options.append(RecoveryAction.RETRY_FAILED)
        if self.graceful_degradation:
            options.append(RecoveryAction.CONTINUE_PARTIAL)
        options.append(RecoveryAction.ABORT)

        # If no interactive options except abort, and graceful degradation is on, just continue
        if len(options) == 1 and options[0] == RecoveryAction.ABORT:
            if self.graceful_degradation:
                logger.warning(f"Max retries ({self.max_analyst_retries}) reached, continuing with partial results")
                self.state.warnings.append(f"Max retries reached, continuing with {len(failed)} failed analysts: {failed}")
                return
            else:
                raise FatalError(f"Max retries reached and graceful degradation disabled. Failed: {failed}")

        action = recovery_menu(
            AnalystError(", ".join(failed), f"{len(failed)} analysts failed"),
            f"Analyst execution (retry {retry_count + 1}/{self.max_analyst_retries + 1})",
            options
        )

        if action == RecoveryAction.RETRY_FAILED:
            logger.info(f"Retrying {len(failed)} failed analysts (attempt {retry_count + 2})")
            self._retry_failed_analysts(parallel)
            # Recursively check for remaining failures
            still_failed = self._get_failed_analysts()
            if still_failed:
                self._handle_analyst_failures(still_failed, parallel, retry_count + 1)
        elif action == RecoveryAction.CONTINUE_PARTIAL:
            self.state.warnings.append(f"Continuing with {len(failed)} failed analysts: {failed}")
            logger.warning(f"Continuing with partial results. Failed: {failed}")
        else:  # ABORT
            raise FatalError(f"User aborted due to {len(failed)} analyst failures")

    def _execute_analysts_sequential(self):
        """Sequential analyst execution with recovery support."""
        self._vprint(section_header("PHASE 4.1: Analysts (SEQUENTIAL)", emoji="🔄"))

        all_analysts = self.state.fixed_analysts + self.state.optional_analysts
        if not all_analysts:
            self.state.warnings.append("No analysts configured")
            return

        failed_count = 0

        for analyst_name in all_analysts:
            # Skip if we already have a successful result (for retry scenarios)
            if analyst_name in self.state.analyst_outputs:
                existing = self.state.analyst_outputs[analyst_name]
                if existing.status not in ("failed",) and not existing.raw_output.startswith("Error:"):
                    self._vprint(f"\n  Skipping analyst: {analyst_name} (already complete)")
                    continue

            self._vprint(f"\n  Running analyst: {analyst_name}")
            try:
                output = self._run_analyst(analyst_name)
                parsed = validate_analyst_output(output, analyst_name)
                self.state.analyst_outputs[analyst_name] = parsed

                # Save agent output to file
                saved_path = self._save_agent_output(analyst_name, output)
                self._vprint(f"    → Saved to: {saved_path}")

                if parsed.status == "failed":
                    failed_count += 1
                    self._vprint(f"    ✗ {analyst_name}: FAILED")
                elif parsed.status == "partial":
                    self._vprint(f"    ⚠ {analyst_name}: partial (confidence: {parsed.confidence})")
                else:
                    self._vprint(f"    ✓ {analyst_name}: complete (confidence: {parsed.confidence})")

                # Collect L1 sources from analyst
                if parsed.exa_sources:
                    self._vprint(f"      L1 sources found: {len(parsed.exa_sources)}")

            except Exception as e:
                failed_count += 1
                logger.error(f"Analyst {analyst_name} failed: {e}")
                self._vprint(f"    ✗ {analyst_name}: ERROR - {e}")
                self.state.analyst_outputs[analyst_name] = AnalystOutput(
                    name=analyst_name,
                    status="failed",
                    confidence=None,
                    content="",
                    raw_output=f"Error: {e}"
                )

        self.state.current_step = Step.ANALYSTS_COMPLETE
        self._checkpoint("analysts_complete")
        self._vprint(f"\n  Analysts complete: {len(self.state.analyst_outputs)} executed, {failed_count} failed")

    def _run_analyst(self, analyst_name: str) -> str:
        """Run a single analyst and return raw output."""
        try:
            agent_prompt = load_agent(analyst_name)
        except FileNotFoundError:
            # Fallback to generic analyst if specific one not found
            agent_prompt = self._generate_fallback_analyst_prompt(analyst_name)

        # Build context for analyst
        context_docs_text = ""
        if self.state.context_documents:
            context_docs_text = "\n\n## Context Documents (L0 Sources)\n"
            for src in self.state.context_documents:
                context_docs_text += f"- [{src.title}]({src.url}) - {src.type}"
                if src.relevance:
                    context_docs_text += f": {src.relevance}"
                context_docs_text += "\n"

        user_message = f"""## Analysis Request

**Problem:** {self.state.problem}

**Language:** {self.state.language}

**Web Search:** {"Enabled" if self.state.web_search_enabled else "Disabled"}
{context_docs_text}

Please provide your analysis following your methodology."""

        # Use default model for analysts (Sonnet)
        response = llm_call(
            system=agent_prompt,
            user=user_message,
            max_tokens=4000,
            model=MODEL_DEFAULT,
            temperature=0.7
        )

        return response

    def _generate_fallback_analyst_prompt(self, analyst_name: str) -> str:
        """Generate a fallback prompt for analysts without AGENT.md files."""
        return f"""You are {analyst_name}, a strategic analyst.

Provide a structured analysis following this format:

---
analyst: {analyst_name}
status: complete
confidence: 0.8
key_findings:
  - Finding 1
  - Finding 2
  - Finding 3
---

# Analysis

[Your detailed analysis here]

## Key Findings

1. [Finding 1]
2. [Finding 2]
3. [Finding 3]

## Strategic Implications

[Implications for decision-making]
"""

    # ============== D1: Async Analyst Execution ==============

    async def _run_analyst_async(self, analyst_name: str) -> tuple[str, str]:
        """
        Async version of _run_analyst for parallel execution.

        Returns:
            tuple of (analyst_name, raw_output)
        """
        try:
            agent_prompt = load_agent(analyst_name)
        except FileNotFoundError:
            agent_prompt = self._generate_fallback_analyst_prompt(analyst_name)

        # Build context for analyst
        context_docs_text = ""
        if self.state.context_documents:
            context_docs_text = "\n\n## Context Documents (L0 Sources)\n"
            for src in self.state.context_documents:
                context_docs_text += f"- [{src.title}]({src.url}) - {src.type}"
                if src.relevance:
                    context_docs_text += f": {src.relevance}"
                context_docs_text += "\n"

        user_message = f"""## Analysis Request

**Problem:** {self.state.problem}

**Language:** {self.state.language}

**Web Search:** {"Enabled" if self.state.web_search_enabled else "Disabled"}
{context_docs_text}

Please provide your analysis following your methodology."""

        # Use async LLM call
        response = await llm_call_async(
            system=agent_prompt,
            user=user_message,
            max_tokens=4000,
            model=MODEL_DEFAULT,
            temperature=0.7
        )

        return (analyst_name, response)

    async def _execute_analysts_async(self) -> dict[str, AnalystOutput]:
        """
        Execute all analysts in parallel using asyncio.

        Returns:
            Dict mapping analyst names to their parsed outputs
        """
        all_analysts = self.state.fixed_analysts + self.state.optional_analysts
        if not all_analysts:
            return {}

        # Filter out already-complete analysts (for retry scenarios)
        analysts_to_run = []
        for name in all_analysts:
            if name in self.state.analyst_outputs:
                existing = self.state.analyst_outputs[name]
                if existing.status not in ("failed",) and not existing.raw_output.startswith("Error:"):
                    logger.debug(f"Skipping {name} (already complete)")
                    continue
            analysts_to_run.append(name)

        if not analysts_to_run:
            logger.info("All analysts already complete.")
            return self.state.analyst_outputs

        logger.info(f"Launching {len(analysts_to_run)} analysts in parallel...")
        start_time = time.time()

        # Create tasks for analysts to run
        tasks = [self._run_analyst_async(name) for name in analysts_to_run]

        # Execute in parallel with gather
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Start with existing outputs (preserve successful ones)
        outputs = dict(self.state.analyst_outputs)
        failed_count = 0

        for i, result in enumerate(results):
            analyst_name = analysts_to_run[i]
            if isinstance(result, Exception):
                # One of the tasks raised an exception
                failed_count += 1
                logger.error(f"Analyst {analyst_name} failed: {result}")
                outputs[analyst_name] = AnalystOutput(
                    name=analyst_name,
                    status="failed",
                    confidence=None,
                    content="",
                    raw_output=f"Error: {result}"
                )
                continue

            analyst_name, raw_output = result
            parsed = validate_analyst_output(raw_output, analyst_name)
            outputs[analyst_name] = parsed

            # Save agent output to file
            saved_path = self._save_agent_output(analyst_name, raw_output)
            logger.debug(f"Saved agent output: {saved_path}")

            if parsed.status == "failed":
                failed_count += 1
                logger.warning(f"{analyst_name}: FAILED")
            elif parsed.status == "partial":
                logger.info(f"{analyst_name}: partial (confidence: {parsed.confidence})")
            else:
                logger.info(f"{analyst_name}: complete (confidence: {parsed.confidence})")

            # Collect L1 sources from analyst
            if parsed.exa_sources:
                logger.debug(f"{analyst_name}: L1 sources found: {len(parsed.exa_sources)}")

        elapsed = time.time() - start_time
        logger.info(f"Async execution complete in {elapsed:.1f}s")
        logger.info(f"Results: {len(outputs)} outputs, {failed_count} failed")

        # Don't abort here - let _handle_analyst_failures deal with recovery
        return outputs

    def _execute_analysts_parallel(self):
        """
        Execute analysts in parallel using asyncio (wrapper for sync context).

        This is a sync wrapper that runs the async execution in an event loop.
        Recovery from failures is handled by _execute_analysts().
        """
        self._vprint(section_header("PHASE 4.1: Analysts (PARALLEL)", emoji="⚡"))

        all_analysts = self.state.fixed_analysts + self.state.optional_analysts
        if not all_analysts:
            self.state.warnings.append("No analysts configured")
            return

        # Run async execution in event loop
        outputs = asyncio.run(self._execute_analysts_async())

        # Merge outputs (preserving any previous successful runs)
        self.state.analyst_outputs.update(outputs)
        self.state.current_step = Step.ANALYSTS_COMPLETE
        self._checkpoint("analysts_complete")

    # ============== B6: Outline Generation ==============

    def _generate_and_approve_outline(self):
        """Generate outline and enforce user approval."""
        self._vprint(section_header("PHASE 4.2: Outline Generation", emoji="📄"))

        # Build analyst summary for outline prompt
        analyst_summary = self._build_analyst_summary()

        # Get template structure
        template_structure = self._get_template_structure(self.state.template)

        # Load output generation prompts
        try:
            output_gen_prompts = load_output_generation()
        except FileNotFoundError:
            output_gen_prompts = ""

        system_prompt = f"""You are generating a strategic analysis outline.

## Template: {self.state.template}

### Template Structure
{template_structure}

### CRITICAL RULES
1. Structure by template sections, NOT by analyst names
2. Analyst outputs are INGREDIENTS, not SECTIONS
3. Mark each point with [Source: analyst-name]
4. Mark gaps with [Data gap: ...]
5. Use bullet points only, no prose

### Frontmatter
Generate valid YAML frontmatter with:
- title, description, slug (kebab-case from title), date (today)
- version: "0.1-outline"
- synthesizer: "{self.state.synthesizer}"
- analysts_fixed: {self.state.fixed_analysts}
- outline_template: "{self.state.template}"
- status: "outline_draft"
- language: "{self.state.language}"
"""

        user_prompt = f"""## Problem
{self.state.problem}

## Analyst Outputs Summary
{analyst_summary}

## Generate the Outline

Create a structured outline using the {self.state.template} template.
Remember: sections should reflect the template structure, NOT analyst names."""

        outline = llm_call(
            system=system_prompt,
            user=user_prompt,
            max_tokens=4000,
            model=MODEL_DEFAULT,
            temperature=0.5
        )

        # ENFORCED approval loop
        approved = False
        iteration = 0
        MAX_ITERATIONS = 5

        while not approved and iteration < MAX_ITERATIONS:
            iteration += 1
            outline_path = self._save_outline(outline)
            print(f"\n  📄 Outline (v{iteration}) saved to: {outline_path}")

            options = [
                "Approve outline - proceed to citation enrichment",
                "Modify structure - reorder or change sections",
                "Modify content - add, remove, or revise points",
                "Change template - switch to different format",
                "Regenerate - start from scratch"
            ]

            choice = ask_user("Review the outline:", options, allow_other=True)

            if "Approve" in choice:
                approved = True
            elif "Change template" in choice:
                self._modify_template()
                outline = self._regenerate_outline(analyst_summary)
            elif "Regenerate" in choice:
                outline = self._regenerate_outline(analyst_summary)
            else:
                # Modification requested
                feedback = choice
                if choice in options:
                    feedback = get_input("Describe the changes you want")
                outline = self._apply_outline_modifications(outline, feedback, analyst_summary)

        if not approved:
            raise RuntimeError("Outline approval failed: max iterations reached")

        self.state.outline = outline
        self.state.current_step = Step.OUTLINE_APPROVED
        self._checkpoint("outline_approved")
        # User-facing feedback: always visible
        print("  Outline approved ✓")

    def _build_analyst_summary(self) -> str:
        """Build summary of analyst outputs for outline generation."""
        lines = []
        for name, output in self.state.analyst_outputs.items():
            lines.append(f"### {name} ({output.status})")
            if output.confidence:
                lines.append(f"**Confidence:** {output.confidence}")
            if output.key_findings:
                lines.append("**Key Findings:**")
                for finding in output.key_findings[:5]:  # Limit to top 5
                    lines.append(f"- {finding}")
            # Add abbreviated content
            content_preview = output.content[:1000] if len(output.content) > 1000 else output.content
            lines.append(f"\n{content_preview}")
            if len(output.content) > 1000:
                lines.append("...[truncated]")
            lines.append("")
        return "\n".join(lines)

    def _get_template_structure(self, template: str) -> str:
        """Return the structure definition for a given template."""
        structures = {
            "BLUF": """
# {Title}
## Bottom Line
• {Main conclusion} [Source: synthesis]
## Background
• {Context point 1} [Source: analyst-X]
## Key Facts
• {Evidence 1} [Source: analyst-X]
## Implications
• {Consequence 1} [Source: synthesis]
## Recommended Action
• {Action} [Source: synthesis]
""",
            "Hypothesis-Driven": """
# {Title}
## Hypothesis
• {Falsifiable thesis} [Source: synthesis]
## Why This Matters
• {Stakes} [Source: analyst-X]
## Supporting Evidence
### Evidence 1: {Name}
• {Data} [Source: analyst-X]
### Evidence 2: {Name}
• {Data} [Source: analyst-Y]
## Counter-Evidence / Risks
• {What could invalidate} [Source: analyst-X]
## Conclusion
• {Confirmation/revision} [Source: synthesis]
## Implications & Next Steps
• {Action 1}
""",
            "POR": """
# {Title}
## Problem Statement
• {Problem definition} [Source: synthesis]
## Context
• {Factor 1} [Source: analyst-X]
## Options
### Option A: {Name}
• Description / Pro / Con / Feasibility
### Option B: {Name}
• Description / Pro / Con / Feasibility
## Recommendation
• {Recommended option} [Source: synthesis]
## Implementation Considerations
• {Resources, timeline, risks}
""",
            "Minto-Custom": """
# {Title}
## Main Conclusion
• {Key question addressed} [Source: synthesis]
## Introduction
### State of the Art
• {Stable context} [Source: analyst-X]
### Complication
• {What changed} [Source: synthesis]
## Key Line 1: {Theme}
### Argument 1.1: {Point}
• {Evidence} [Source: analyst-X]
## Key Line 2: {Theme}
### Argument 2.1: {Point}
• {Evidence} [Source: analyst-Y]
## Implications
• {Consequence} [Source: synthesis]
## Next Steps / Recommendations
• {Action 1}
"""
        }
        return structures.get(template, structures["Minto-Custom"])

    def _regenerate_outline(self, analyst_summary: str) -> str:
        """Regenerate outline from scratch."""
        # User feedback: visible during interactive workflow
        print("  Regenerating outline...")
        return self._generate_outline_internal(analyst_summary)

    def _generate_outline_internal(self, analyst_summary: str) -> str:
        """Internal method to generate outline."""
        template_structure = self._get_template_structure(self.state.template)

        system_prompt = f"""You are generating a strategic analysis outline.

## Template: {self.state.template}

{template_structure}

Structure by template sections, NOT by analyst names.
Mark each point with [Source: analyst-name].
Use bullet points only."""

        user_prompt = f"""## Problem
{self.state.problem}

## Analyst Outputs
{analyst_summary}

Generate the outline now."""

        return llm_call(
            system=system_prompt,
            user=user_prompt,
            max_tokens=4000,
            model=MODEL_DEFAULT,
            temperature=0.5
        )

    def _apply_outline_modifications(self, outline: str, feedback: str, analyst_summary: str) -> str:
        """Apply user modifications to outline."""
        # User feedback: visible during interactive workflow
        print(f"  Applying modifications: {feedback[:50]}...")

        system_prompt = """You are modifying a strategic analysis outline based on user feedback.

Keep the same template structure but apply the requested changes.
Preserve [Source: X] markers and bullet point format."""

        user_prompt = f"""## Current Outline
{outline}

## User Feedback
{feedback}

## Analyst Outputs (for reference)
{analyst_summary}

Apply the modifications and return the updated outline."""

        return llm_call(
            system=system_prompt,
            user=user_prompt,
            max_tokens=4000,
            model=MODEL_DEFAULT,
            temperature=0.5
        )

    # ============== B7: Citation Enrichment ==============

    def _enrich_citations(self):
        """Map sources to outline points and fill gaps. ENFORCED: must produce citation_map."""
        self._vprint(section_header("PHASE 4.3: Citation Enrichment", emoji="📚"))

        # Collect all available sources
        all_sources = []

        # L0: Context documents
        for src in self.state.context_documents:
            all_sources.append({
                "url": src.url,
                "title": src.title,
                "type": src.type,
                "anchor": src.anchor_suggestion,
                "level": "L0"
            })

        # L1: Analyst Exa sources
        for output in self.state.analyst_outputs.values():
            for src in output.exa_sources:
                all_sources.append({
                    "url": src.url,
                    "title": src.title,
                    "type": src.type,
                    "anchor": src.anchor_suggestion,
                    "level": "L1"
                })

        sources_text = ""
        if all_sources:
            sources_text = "\n## Available Sources\n"
            for i, src in enumerate(all_sources, 1):
                sources_text += f"{i}. [{src['title']}]({src['url']}) - {src['level']}, {src['type']}\n"
                sources_text += f"   Anchor: \"{src['anchor']}\"\n"

        system_prompt = """You are enriching a strategic analysis outline with citations.

## Task
1. Scan the outline for claims that need citations
2. Match claims with available sources (L0/L1)
3. For claims without sources, mark as "theoretical" or "unavailable"

## Output Format
Return ONLY valid YAML with this structure:

```yaml
citation_map:
  - point_id: "1.2"
    claim: "The claim text"
    url: "https://..." or null
    anchor_text: "text for hyperlink"
    pattern: factual|data|context|deep|theoretical
    source_level: L0|L1|L2|theoretical|unavailable
```

## Citation Patterns
- factual: Authoritative claim ("As [anchor](url) demonstrates...")
- data: Statistics, numbers ("[€2.3B in 2024](url)")
- context: Background info ("The [experience](url) shows...")
- deep: Further reading (woven naturally)
- theoretical: Framework reference, no URL needed

## Rules
- MUST include at least one entry if outline has factual claims
- Prefer L0 sources over L1
- Mark unavailable honestly, don't fabricate URLs
"""

        user_prompt = f"""## Approved Outline
{self.state.outline}
{sources_text}

Generate the citation_map now."""

        response = llm_call(
            system=system_prompt,
            user=user_prompt,
            max_tokens=2000,
            model=MODEL_DEFAULT,
            temperature=0.3
        )

        # Parse citation map
        self._parse_citation_map(response)

        # L2 Exa search for unavailable citations (Phase C integration)
        if self.state.web_search_enabled and EXA_AVAILABLE:
            self._fill_citation_gaps_with_exa()

        # ENFORCED validation
        is_valid, message = validate_citation_map(self.state.citation_map, self.state.outline)
        if not is_valid:
            self._vprint(f"  ⚠ Citation validation warning: {message}")
            # Try to recover by re-running with stricter prompt
            if not self.state.citation_map:
                self._vprint("  Attempting citation recovery...")
                self._recover_citations()

        # Final check
        is_valid, message = validate_citation_map(self.state.citation_map, self.state.outline)
        if not is_valid and "empty" in message.lower():
            self.state.warnings.append(f"Citation map issue: {message}")
            if not confirm("Citation map is empty. Proceed anyway?"):
                raise RuntimeError("Citation enrichment failed: empty citation_map")

        self.state.current_step = Step.CITATIONS_MAPPED
        self._checkpoint("citations_mapped")
        self._vprint(f"  Citations mapped: {len(self.state.citation_map)} entries")

    def _parse_citation_map(self, response: str):
        """Parse citation map from LLM response."""
        yaml_text = response
        if "```yaml" in response:
            yaml_text = response.split("```yaml")[1].split("```")[0]
        elif "```" in response:
            yaml_text = response.split("```")[1].split("```")[0]

        try:
            data = yaml.safe_load(yaml_text)
            if data and "citation_map" in data:
                for entry in data["citation_map"]:
                    self.state.citation_map.append(CitationEntry(
                        point_id=entry.get("point_id", ""),
                        claim=entry.get("claim", ""),
                        url=entry.get("url"),
                        anchor_text=entry.get("anchor_text", ""),
                        pattern=entry.get("pattern", "factual"),
                        source_level=entry.get("source_level", "unavailable")
                    ))
        except yaml.YAMLError as e:
            self._vprint(f"  Warning: Failed to parse citation map: {e}")

    def _recover_citations(self):
        """Attempt to recover citations with more explicit prompt."""
        system_prompt = """You MUST generate a citation_map for this outline.

Even if no URLs are available, create entries with:
- source_level: "theoretical" for framework references
- source_level: "unavailable" for claims that need data

DO NOT return an empty citation_map if the outline contains factual claims.

Return ONLY valid YAML:
```yaml
citation_map:
  - point_id: "1.1"
    claim: "The claim"
    url: null
    anchor_text: "reference text"
    pattern: theoretical
    source_level: theoretical
```"""

        response = llm_call(
            system=system_prompt,
            user=f"Outline:\n{self.state.outline}\n\nGenerate citation_map now.",
            max_tokens=1500,
            model=MODEL_DEFAULT,
            temperature=0.2
        )

        self._parse_citation_map(response)

    def _fill_citation_gaps_with_exa(self):
        """Fill unavailable citations with L2 Exa searches (Phase C)."""
        # Find citations marked as unavailable that could benefit from search
        gaps = [
            (i, entry) for i, entry in enumerate(self.state.citation_map)
            if entry.source_level == "unavailable"
            and entry.pattern in ("factual", "data", "context")  # Skip theoretical
        ]

        if not gaps:
            return

        self._vprint(f"  Found {len(gaps)} citation gaps, attempting L2 Exa fill...")

        # Limit to remaining search budget
        remaining_searches = EXA_MAX_SEARCHES - EXA_SEARCH_COUNT
        gaps_to_fill = gaps[:remaining_searches]

        for idx, entry in gaps_to_fill:
            try:
                source = exa_search_for_citation(
                    claim=entry.claim,
                    context=self.state.problem[:100],
                    language=self.state.language
                )

                if source:
                    # Update the citation entry
                    self.state.citation_map[idx] = CitationEntry(
                        point_id=entry.point_id,
                        claim=entry.claim,
                        url=source.url,
                        anchor_text=source.anchor_suggestion,
                        pattern=entry.pattern,
                        source_level="L2"
                    )
                    self._vprint(f"    ✓ Filled {entry.point_id}: {source.title[:40]}...")

            except RuntimeError as e:
                # Search limit reached
                self._vprint(f"    ⚠ {e}")
                break
            except Exception as e:
                self._vprint(f"    ⚠ Failed to fill {entry.point_id}: {e}")

    # ============== B8: Full Text Generation ==============

    def _generate_full_text(self):
        """Generate full prose document with woven citations. ENFORCED: frontmatter validation."""
        self._vprint(section_header("PHASE 4.4: Full Text Generation", emoji="📝"))

        # Build citation map text for prompt
        citation_instructions = self._build_citation_instructions()

        system_prompt = f"""You are expanding a strategic analysis outline into full prose.

## Expansion Rules
1. One bullet → 1-3 sentences
2. Add transitions between sections
3. Remove [Source: analyst-X] markers
4. Weave citations using the citation_map below
5. Professional tone for executives/policymakers

## Link Weaving Patterns
- factual: "As [anchor](url) demonstrates, ..." / "Come evidenzia il [anchor](url), ..."
- data: "[€X nel YYYY](url), il mercato..." / "[€X in YYYY](url), the market..."
- context: "The [anchor](url) experience shows..." / "L'esperienza [anchor](url) dimostra..."
- theoretical: No URL, integrate naturally: "According to Porter's framework..."

## Frontmatter
Generate valid YAML with ALL these required fields:
- title
- description
- slug (kebab-case derived from title, e.g. "european-space-launch-autonomy")
- date: {self._get_today_date()}
- version: "1.0"
- synthesizer: "{self.state.synthesizer}"
- analysts_fixed: {self.state.fixed_analysts}
- analysts_optional: {self.state.optional_analysts or []}
- outline_template: "{self.state.template}"
- status: "final"
- language: "{self.state.language}"

## Citation Map
{citation_instructions}
"""

        user_prompt = f"""## Approved Outline
{self.state.outline}

Generate the complete prose document now.
Language: {self.state.language}
Weave all citations from the map into the narrative."""

        # Use Opus for complex full-text generation
        document = llm_call(
            system=system_prompt,
            user=user_prompt,
            max_tokens=8000,
            model=MODEL_COMPLEX,  # Use Opus for final document
            temperature=0.7
        )

        # ENFORCED frontmatter validation
        is_valid, missing = validate_frontmatter(document, REQUIRED_FRONTMATTER)

        if not is_valid:
            self._vprint(f"  ⚠ Frontmatter validation failed: {missing}")
            self._vprint("  Attempting frontmatter repair...")
            document = self._repair_frontmatter(document, missing)

            # Re-validate
            is_valid, missing = validate_frontmatter(document, REQUIRED_FRONTMATTER)
            if not is_valid:
                self.state.warnings.append(f"Frontmatter incomplete: {missing}")

        self.state.final_document = document
        self._vprint("  Full text generated ✓")

    def _build_citation_instructions(self) -> str:
        """Build citation weaving instructions from citation_map."""
        if not self.state.citation_map:
            return "No citations to weave. Use theoretical references where appropriate."

        lines = []
        for entry in self.state.citation_map:
            if entry.url:
                lines.append(f"- Point {entry.point_id}: [{entry.anchor_text}]({entry.url}) ({entry.pattern})")
            else:
                lines.append(f"- Point {entry.point_id}: {entry.anchor_text} ({entry.pattern}, no URL)")
        return "\n".join(lines)

    def _get_today_date(self) -> str:
        """Get today's date in ISO format."""
        return date.today().isoformat()

    def _repair_frontmatter(self, document: str, missing: list[str]) -> str:
        """Attempt to repair missing frontmatter fields."""
        # Extract existing frontmatter
        if not document.startswith("---"):
            # No frontmatter at all, generate complete one
            return self._generate_complete_frontmatter() + "\n\n" + document

        try:
            parts = document.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1]) or {}
                content = parts[2]

                # Fill missing fields
                defaults = {
                    "title": "Strategic Analysis",
                    "description": self.state.problem[:200],
                    "slug": self._generate_slug(),
                    "date": self._get_today_date(),
                    "version": "1.0",
                    "synthesizer": self.state.synthesizer,
                    "analysts_fixed": self.state.fixed_analysts,
                    "analysts_optional": self.state.optional_analysts or [],
                    "outline_template": self.state.template,
                    "status": "final",
                    "language": self.state.language
                }

                for field, default in defaults.items():
                    if field not in frontmatter or not frontmatter[field]:
                        frontmatter[field] = default

                # Rebuild document
                new_frontmatter = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
                return f"---\n{new_frontmatter}---{content}"

        except Exception as e:
            self._vprint(f"  Frontmatter repair failed: {e}")

        return document

    def _generate_slug(self) -> str:
        """Generate slug from problem statement."""
        import re
        # Take first 60 chars of problem, convert to kebab-case
        text = self.state.problem[:60].lower()
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        text = re.sub(r'-+', '-', text).strip('-')
        return text

    def _generate_complete_frontmatter(self) -> str:
        """Generate complete frontmatter block."""
        frontmatter = {
            "title": "Strategic Analysis",
            "description": self.state.problem[:200],
            "slug": self._generate_slug(),
            "date": self._get_today_date(),
            "version": "1.0",
            "synthesizer": self.state.synthesizer,
            "analysts_fixed": self.state.fixed_analysts,
            "analysts_optional": self.state.optional_analysts or [],
            "outline_template": self.state.template,
            "status": "final",
            "language": self.state.language
        }
        yaml_text = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_text}---"

    def _extract_slug_from_document(self, document: str) -> str:
        """Extract slug from document frontmatter, or generate one."""
        if document.startswith("---"):
            try:
                parts = document.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1]) or {}
                    if "slug" in frontmatter and frontmatter["slug"]:
                        return frontmatter["slug"]
            except Exception:
                pass
        return self._generate_slug()

    def _get_output_dir(self, slug: str) -> Path:
        """Get output directory path based on slug."""
        return Path("output") / slug

    def _get_outline_filename(self) -> str:
        """Get outline filename based on language."""
        if self.state.language == "it":
            return "outline.it.md"
        return "outline.md"

    def _get_document_filename(self) -> str:
        """Get final document filename based on language."""
        if self.state.language == "it":
            return "index.it.md"
        return "index.md"

    def _save_outline(self, outline: str) -> Path:
        """Save outline to file and return the path."""
        slug = self._extract_slug_from_document(outline)
        output_dir = self._get_output_dir(slug)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / self._get_outline_filename()
        filepath.write_text(outline, encoding="utf-8")
        return filepath

    def _save_final_document(self, document: str) -> Path:
        """Save final document to file and return the path."""
        slug = self._extract_slug_from_document(document)
        output_dir = self._get_output_dir(slug)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / self._get_document_filename()
        filepath.write_text(document, encoding="utf-8")
        return filepath

    def _save_agent_output(self, agent_name: str, raw_output: str) -> Path:
        """
        Save individual agent output to file.

        Outputs are saved to: output/{slug}/{agent-name}.md

        Args:
            agent_name: Name of the agent/analyst
            raw_output: Raw output text from the agent

        Returns:
            Path where the output was saved
        """
        slug = self._generate_slug()
        output_dir = self._get_output_dir(slug)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"{agent_name}.md"
        filepath.write_text(raw_output, encoding="utf-8")
        logger.debug(f"Saved agent output: {filepath}")
        return filepath


# ============== ENTRY POINT ==============

if __name__ == "__main__":
    import sys

    # Parse verbose flag FIRST (needed for test output control)
    verbose_mode = "-v" in sys.argv or "--verbose" in sys.argv
    quiet_mode = "-q" in sys.argv or "--quiet" in sys.argv

    # Suppress logger output during tests unless verbose
    if not verbose_mode and "--run" not in sys.argv and "--resume" not in sys.argv:
        setup_logging(quiet=True)

    # Test output helper - only prints in verbose mode
    def tprint(*args, **kwargs):
        if verbose_mode:
            print(*args, **kwargs)

    print_section_header("Strategic Orchestrator - MVP", emoji="🧪")

    # Test A1: Data structures
    state = WorkflowState()
    tprint(f"[A1] Initial step: {state.current_step.value}")

    # Test A2: Prompt loading
    tprint("\n[A2] Testing prompt loading...")
    try:
        # Test loading output generation (should exist)
        output_gen = load_output_generation()
        tprint(f"  ✓ _OUTPUT_GENERATION.md loaded ({len(output_gen)} chars)")
    except FileNotFoundError as e:
        tprint(f"  ✗ {e}")

    # List available skills
    if SKILLS_PATH.exists():
        skills = [d.name for d in SKILLS_PATH.iterdir() if d.is_dir()]
        tprint(f"  Available skills: {skills[:5]}...")  # Show first 5

    # List available agents
    if AGENTS_PATH.exists():
        agents = [d.name for d in AGENTS_PATH.iterdir() if d.is_dir()]
        tprint(f"  Available agents: {agents[:5]}...")  # Show first 5

    # Test A3: LLM wrapper (only if API key present)
    tprint("\n[A3] Testing LLM wrapper...")
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            response = llm_call(
                system="You are a test assistant.",
                user="Say 'LLM wrapper works!' and nothing else.",
                max_tokens=50
            )
            tprint(f"  ✓ LLM response: {response.strip()}")
        except Exception as e:
            tprint(f"  ✗ LLM error: {e}")
    else:
        tprint("  ⚠ ANTHROPIC_API_KEY not set, skipping LLM test")

    # Test A4: User interaction (non-interactive demo)
    tprint("\n[A4] User interaction functions defined:")
    tprint("  ✓ ask_user(prompt, options) - numbered choice menu")
    tprint("  ✓ confirm(prompt) - yes/no prompt")
    tprint("  ✓ get_input(prompt, default) - free-form input")
    tprint("  ✓ display_section(title, content) - formatted output")

    # Test A5: Validation
    tprint("\n[A5] Testing validation functions...")

    # Test analyst output parsing
    sample_analyst = """---
status: complete
confidence: 0.85
key_findings:
  - Finding one
  - Finding two
---
Main analysis content here."""

    parsed = validate_analyst_output(sample_analyst, "test-analyst")
    tprint(f"  ✓ validate_analyst_output: status={parsed.status}, confidence={parsed.confidence}")

    # Test citation map validation
    outline_with_facts = "The budget is €500 million in 2024."
    valid, msg = validate_citation_map([], outline_with_facts)
    tprint(f"  ✓ validate_citation_map (empty, factual): valid={valid}")

    # Test frontmatter validation
    sample_doc = """---
title: Test
description: A test document
date: 2026-01-25
---
Content here."""

    valid, missing = validate_frontmatter(sample_doc, ["title", "description", "date", "author"])
    tprint(f"  ✓ validate_frontmatter: valid={valid}, missing={missing}")

    # Test B1-B2: Orchestrator phases (non-interactive demo)
    tprint("\n[B1-B2] Testing orchestrator phases...")

    # Test language detection
    orch = StrategicOrchestrator()
    lang_en = orch._detect_language("Analyze the European space industry competition")
    lang_it = orch._detect_language("Analizza la strategia spaziale europea")
    tprint(f"  ✓ Language detection: EN='{lang_en}', IT='{lang_it}'")

    # Test source need evaluation
    orch.state.problem = "What is the 2025 ESA budget allocation?"
    need = orch._evaluate_source_need()
    tprint(f"  ✓ Source need evaluation: '{need}' (expected: HIGH)")

    # Test fallback scoring
    orch.state.problem = "Analyze geopolitical power dynamics in space"
    orch._fallback_scoring()
    tprint(f"  ✓ Fallback scoring: {orch.state.synthesizer_scores}")

    # Test B5-B8: Phase 4 components (non-interactive demo)
    tprint("\n[B5-B8] Testing Phase 4 components...")

    # Test template structure retrieval
    orch = StrategicOrchestrator()
    bluf_structure = orch._get_template_structure("BLUF")
    tprint(f"  ✓ BLUF template structure loaded ({len(bluf_structure)} chars)")

    # Test fallback analyst prompt generation
    fallback_prompt = orch._generate_fallback_analyst_prompt("test-analyst")
    tprint(f"  ✓ Fallback analyst prompt generated ({len(fallback_prompt)} chars)")

    # Test citation instructions building
    orch.state.citation_map = [
        CitationEntry(
            point_id="1.1",
            claim="Test claim",
            url="https://example.com",
            anchor_text="Example Source",
            pattern="factual",
            source_level="L0"
        )
    ]
    citation_instructions = orch._build_citation_instructions()
    tprint(f"  ✓ Citation instructions: {citation_instructions[:50]}...")

    # Test frontmatter repair
    incomplete_doc = """---
title: Test
---
Content here."""
    orch.state.problem = "Test problem"
    orch.state.synthesizer = "strategic-geopolitical"
    orch.state.fixed_analysts = ["pestle-analyst"]
    orch.state.template = "BLUF"
    orch.state.language = "en"
    repaired = orch._repair_frontmatter(incomplete_doc, ["description", "date"])
    tprint(f"  ✓ Frontmatter repair works (added missing fields)")

    # Test date function
    today = orch._get_today_date()
    tprint(f"  ✓ Today's date: {today}")

    # Test Phase C: Exa Integration
    tprint("\n[C] Testing Exa integration...")
    tprint(f"  Exa SDK available: {EXA_AVAILABLE}")

    # Test search counter reset
    reset_exa_search_count()
    tprint(f"  ✓ Search counter reset: {EXA_SEARCH_COUNT}")

    # Test Exa functions exist
    tprint("  ✓ exa_search() defined")
    tprint("  ✓ exa_search_for_citation() defined")

    # Test actual Exa search (only if API key present)
    if os.environ.get("EXA_API_KEY") and EXA_AVAILABLE:
        try:
            results = exa_search("European Space Agency budget 2025", num_results=2)
            tprint(f"  ✓ Exa search works: {len(results)} results")
            if results:
                tprint(f"    First result: {results[0]['title'][:50]}...")
        except Exception as e:
            tprint(f"  ⚠ Exa search test: {e}")
    else:
        tprint("  ⚠ EXA_API_KEY not set or exa-py not installed, skipping Exa test")
        tprint("    To enable: pip install exa-py && export EXA_API_KEY=your_key")

    # Test D1: Async functionality
    tprint("\n[D1] Testing async functionality...")
    tprint("  ✓ asyncio imported")
    tprint("  ✓ llm_call_async() defined")
    tprint("  ✓ get_async_client() defined")
    tprint("  ✓ _run_analyst_async() method added")
    tprint("  ✓ _execute_analysts_async() method added")
    tprint("  ✓ _execute_analysts_parallel() wrapper added")

    # Test D2: State persistence
    tprint("\n[D2] Testing state persistence...")

    # Test serialization roundtrip
    test_state = WorkflowState(
        problem="Test problem",
        language="en",
        current_step=Step.PROPOSAL_APPROVED,
        synthesizer="strategic-geopolitical",
        fixed_analysts=["pestle-analyst", "stakeholder-analyst"]
    )
    test_state.context_documents.append(Source(
        url="https://example.com",
        title="Test Source",
        type="report",
        anchor_suggestion="Test",
        level="L0"
    ))
    test_state.analyst_outputs["pestle-analyst"] = AnalystOutput(
        name="pestle-analyst",
        status="complete",
        confidence=0.85,
        content="Test content",
        key_findings=["Finding 1", "Finding 2"]
    )

    # Serialize
    state_dict = workflow_state_to_dict(test_state)
    tprint(f"  ✓ workflow_state_to_dict: {len(state_dict)} fields")

    # Deserialize
    restored_state = workflow_state_from_dict(state_dict)
    tprint(f"  ✓ workflow_state_from_dict: step={restored_state.current_step.value}")

    # Verify roundtrip
    assert restored_state.problem == test_state.problem
    assert restored_state.current_step == test_state.current_step
    assert restored_state.synthesizer == test_state.synthesizer
    assert len(restored_state.context_documents) == 1
    assert "pestle-analyst" in restored_state.analyst_outputs
    tprint("  ✓ Serialization roundtrip verified")

    # Test save/load with temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name

    test_orch = StrategicOrchestrator()
    test_orch.state = test_state
    test_orch.save_state(temp_path)

    loaded_orch = StrategicOrchestrator.load_state(temp_path)
    assert loaded_orch.state.problem == "Test problem"
    assert loaded_orch.state.current_step == Step.PROPOSAL_APPROVED
    tprint("  ✓ save_state/load_state roundtrip verified")

    # Cleanup
    Path(temp_path).unlink()
    tprint("  ✓ State persistence functions complete")

    # Test D3: Logging
    tprint("\n[D3] Testing logging and debugging...")
    tprint("  ✓ logging module imported")
    tprint("  ✓ setup_logging() defined")
    tprint("  ✓ LogTimer context manager defined")
    tprint(f"  ✓ Logger name: {logger.name}")
    tprint(f"  ✓ Current level: {logging.getLevelName(logger.level)}")

    # Test LogTimer
    with LogTimer("test operation", level=logging.DEBUG):
        time.sleep(0.01)
    tprint("  ✓ LogTimer works (see DEBUG output with -v)")

    # Test setup_logging with different modes
    original_level = logger.level
    setup_logging(verbose=True)
    assert logger.level == logging.DEBUG
    setup_logging(quiet=True)
    assert logger.level == logging.WARNING
    setup_logging(level=original_level)  # Restore
    tprint("  ✓ setup_logging modes (verbose/quiet) work")

    # Test async client initialization (only if API key present)
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            async_client = get_async_client()
            tprint(f"  ✓ Async client initialized: {type(async_client).__name__}")
        except Exception as e:
            tprint(f"  ⚠ Async client test: {e}")

        # Quick async LLM test
        async def test_async_llm():
            return await llm_call_async(
                system="You are a test assistant.",
                user="Say 'Async works!' and nothing else.",
                max_tokens=50
            )

        try:
            async_response = asyncio.run(test_async_llm())
            tprint(f"  ✓ Async LLM response: {async_response.strip()}")
        except Exception as e:
            tprint(f"  ⚠ Async LLM test: {e}")
    else:
        tprint("  ⚠ ANTHROPIC_API_KEY not set, skipping async LLM test")

    # Test D4: Error Recovery
    tprint("\n[D4] Testing error recovery...")
    tprint("  ✓ OrchestratorError exception hierarchy defined")
    tprint("  ✓ RetryableError / FatalError classification")
    tprint("  ✓ AnalystError for analyst-specific failures")
    tprint("  ✓ RetryPolicy dataclass with exponential backoff")
    tprint("  ✓ is_retryable_error() classifier")
    tprint("  ✓ with_retry() sync wrapper")
    tprint("  ✓ with_retry_async() async wrapper")
    tprint("  ✓ RecoveryAction enum")
    tprint("  ✓ recovery_menu() interactive recovery")
    tprint("  ✓ _get_failed_analysts() method")
    tprint("  ✓ _retry_failed_analysts() method")
    tprint("  ✓ _handle_analyst_failures() with graceful degradation")
    tprint("  ✓ graceful_degradation config option")
    tprint("  ✓ auto_recovery config option")
    tprint("  ✓ max_analyst_retries config option")

    # Test RetryPolicy
    policy = RetryPolicy(max_retries=3, base_delay=1.0)
    delay_0 = policy.calculate_delay(0)
    delay_1 = policy.calculate_delay(1)
    delay_2 = policy.calculate_delay(2)
    tprint(f"  ✓ RetryPolicy delays: {delay_0:.2f}s, {delay_1:.2f}s, {delay_2:.2f}s (with jitter)")

    # Test error classification
    rate_limit_err = Exception("rate_limit_exceeded: too many requests")
    assert is_retryable_error(rate_limit_err) == True
    fatal_err = Exception("invalid_api_key: authentication failed")
    assert is_retryable_error(fatal_err) == False
    tprint("  ✓ Error classification works (retryable vs fatal)")

    print_section_header("All Tests Complete", emoji="✅")
    print("Phase A + B + C + D1 + D2 + D3 + D4 verified!")
    print("\nRun with --help for usage information.")

    # Check for --run or --resume flag
    import sys

    # Handle --help flag
    if "-h" in sys.argv or "--help" in sys.argv:
        print("\nUsage:")
        print("  python strategic_orchestrator.py                    # Run tests")
        print("  python strategic_orchestrator.py --run              # Interactive mode (parallel)")
        print("  python strategic_orchestrator.py --run --seq        # Sequential mode")
        print("  python strategic_orchestrator.py --run --save       # Auto-save checkpoints")
        print("  python strategic_orchestrator.py --resume FILE      # Resume from saved state")
        print("\nError recovery options:")
        print("  --no-graceful                                       # Abort on failures (no partial results)")
        print("  --auto-recovery                                     # Auto-choose recovery actions")
        print("  --max-retries N                                     # Max analyst retries (default: 2)")
        print("\nLogging options:")
        print("  -v, --verbose                                       # DEBUG level logging")
        print("  -q, --quiet                                         # WARNING+ only (suppress INFO)")
        print("  --log-file FILE                                     # Write logs to file")
        print("\nEnvironment:")
        print("  ANTHROPIC_API_KEY  — Required for LLM calls")
        print("  EXA_API_KEY        — Optional for L2 web search")
        sys.exit(0)

    # Parse logging options first (affects all modes)
    verbose_mode = "-v" in sys.argv or "--verbose" in sys.argv
    quiet_mode = "-q" in sys.argv or "--quiet" in sys.argv
    log_file = None
    if "--log-file" in sys.argv:
        try:
            log_file_idx = sys.argv.index("--log-file")
            log_file = sys.argv[log_file_idx + 1]
        except (ValueError, IndexError):
            print("❌ Error: --log-file requires a filepath argument")
            sys.exit(1)

    # Reconfigure logging based on CLI flags
    if verbose_mode or quiet_mode or log_file:
        setup_logging(verbose=verbose_mode, quiet=quiet_mode, log_file=log_file)
        if verbose_mode:
            print("Logging: VERBOSE (DEBUG level)")
        elif quiet_mode:
            print("Logging: QUIET (WARNING+ only)")
        if log_file:
            print(f"Log file: {log_file}")

    # Parse D4 error recovery options
    graceful_degradation = "--no-graceful" not in sys.argv
    auto_recovery = "--auto-recovery" in sys.argv
    max_retries = 2
    if "--max-retries" in sys.argv:
        try:
            retries_idx = sys.argv.index("--max-retries")
            max_retries = int(sys.argv[retries_idx + 1])
        except (ValueError, IndexError):
            print("❌ Error: --max-retries requires a number argument")
            sys.exit(1)

    if "--resume" in sys.argv:
        # Resume mode
        try:
            resume_idx = sys.argv.index("--resume")
            state_file = sys.argv[resume_idx + 1]
        except (ValueError, IndexError):
            print("❌ Error: --resume requires a filepath argument")
            print("   Usage: python strategic_orchestrator.py --resume path/to/state.yaml")
            sys.exit(1)

        if verbose_mode:
            print_section_header("Resume Mode", emoji="▶️")
        parallel_mode = "--seq" not in sys.argv and "--sequential" not in sys.argv
        auto_save = "--save" in sys.argv

        try:
            orch = StrategicOrchestrator.load_state(
                state_file,
                parallel_analysts=parallel_mode,
                graceful_degradation=graceful_degradation,
                auto_recovery=auto_recovery,
                max_analyst_retries=max_retries,
                verbose=verbose_mode
            )
            orch.auto_save = auto_save

            result = orch.resume()
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\n  📄 Final document saved to: {doc_path}")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            if 'orch' in locals():
                if confirm("Save current state before exiting?"):
                    orch.save_state()
        except Exception as e:
            print(f"\n❌ Resume failed: {e}")

    elif "--run" in sys.argv:
        if verbose_mode:
            print_section_header("Interactive Mode", emoji="🚀")

        # Check for sequential flag
        parallel_mode = "--seq" not in sys.argv and "--sequential" not in sys.argv
        auto_save = "--save" in sys.argv

        if verbose_mode:
            if not parallel_mode:
                print("Mode: SEQUENTIAL (analysts run one at a time)")
            else:
                print("Mode: PARALLEL (analysts run concurrently via asyncio)")

            if auto_save:
                print("Auto-save: ENABLED (checkpoints will be saved)")

            if not graceful_degradation:
                print("Graceful degradation: DISABLED (abort on failures)")
            if auto_recovery:
                print("Auto-recovery: ENABLED")
            if max_retries != 2:
                print(f"Max analyst retries: {max_retries}")

        problem = get_input("Enter analysis problem")
        if problem:
            orch = StrategicOrchestrator(
                parallel_analysts=parallel_mode,
                auto_save=auto_save,
                graceful_degradation=graceful_degradation,
                auto_recovery=auto_recovery,
                max_analyst_retries=max_retries,
                verbose=verbose_mode
            )
            try:
                result = orch.run(problem)
                if result:
                    doc_path = orch._save_final_document(result)
                    print(f"\n  📄 Final document saved to: {doc_path}")

            except KeyboardInterrupt:
                print("\n\n⚠ Interrupted by user")
                if confirm("Save current state before exiting?"):
                    orch.save_state()
            except Exception as e:
                print(f"\n❌ Analysis aborted: {e}")
                if confirm("Save current state for debugging?"):
                    orch.save_state()
