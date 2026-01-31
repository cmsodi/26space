"""
Strategic Orchestrator - Modular Package

This package provides a multi-agent strategic analysis system.
"""

from .config import (
    SKILLS_PATH,
    AGENTS_PATH,
    OUTPUT_GEN_PATH,
    RECIPES_PATH,
    MODEL_DEFAULT,
    MODEL_COMPLEX,
    MODEL_FAST,
    Step,
    SYNTHESIZERS,
    TEMPLATES,
)

from .utils import (
    detect_language,
    generate_slug,
    generate_unique_slug,
    ensure_unique_slug,
    get_document_filename,
)

from .models import (
    Source,
    TextDocument,
    AnalystOutput,
    CitationEntry,
    WorkflowState,
)

from .state import (
    source_to_dict,
    source_from_dict,
    text_document_to_dict,
    text_document_from_dict,
    analyst_output_to_dict,
    analyst_output_from_dict,
    citation_entry_to_dict,
    citation_entry_from_dict,
    workflow_state_to_dict,
    workflow_state_from_dict,
    load_skill,
    load_agent,
    load_output_generation,
)

from .logging_setup import (
    logger,
    LOG_FORMAT,
    LOG_FORMAT_DEBUG,
    LOG_DATE_FORMAT,
    setup_logging,
    LogTimer,
)

from .errors import (
    OrchestratorError,
    RetryableError,
    FatalError,
    AnalystError,
    RetryPolicy,
    RETRY_POLICY_API,
    RETRY_POLICY_ANALYST,
    RETRY_POLICY_EXA,
    is_retryable_error,
    classify_error,
    with_retry,
    with_retry_async,
)

from .llm import (
    get_client,
    get_async_client,
    llm_call,
    llm_call_async,
)

from .exa import (
    EXA_AVAILABLE,
    EXA_MAX_SEARCHES,
    get_exa_client,
    reset_exa_search_count,
    get_exa_search_count,
    exa_search,
    exa_search_for_citation,
)

from .ui import (
    ask_user,
    confirm,
    get_input,
    SECTION_EMOJIS,
    section_header,
    print_section_header,
    display_section,
    RecoveryAction,
    recovery_menu,
    should_continue_on_error,
)

from .validation import (
    validate_analyst_output,
    validate_citation_map,
    validate_frontmatter,
    REQUIRED_FRONTMATTER,
)

from .orchestrator import StrategicOrchestrator

from .recipe import (
    RecipeRunner,
    discover_recipes,
    load_recipe,
)

from .editorial import (
    run_editorial_workflow,
    select_or_create_topic,
    build_problem_from_item,
    load_editorial_plan,
    update_item_status,
    CONTEXT_DOCUMENTS_PATH,
)

# Import engines to trigger registration
import src.engines  # noqa: F401

__all__ = [
    # Config
    'SKILLS_PATH', 'AGENTS_PATH', 'OUTPUT_GEN_PATH', 'RECIPES_PATH',
    'MODEL_DEFAULT', 'MODEL_COMPLEX', 'MODEL_FAST',
    'Step', 'SYNTHESIZERS', 'TEMPLATES',
    # Utils
    'detect_language', 'generate_slug', 'generate_unique_slug', 'ensure_unique_slug',
    'get_document_filename',
    # Models
    'Source', 'TextDocument', 'AnalystOutput', 'CitationEntry', 'WorkflowState',
    # State
    'source_to_dict', 'source_from_dict',
    'text_document_to_dict', 'text_document_from_dict',
    'analyst_output_to_dict', 'analyst_output_from_dict',
    'citation_entry_to_dict', 'citation_entry_from_dict',
    'workflow_state_to_dict', 'workflow_state_from_dict',
    'load_skill', 'load_agent', 'load_output_generation',
    # Logging
    'logger', 'LOG_FORMAT', 'LOG_FORMAT_DEBUG', 'LOG_DATE_FORMAT',
    'setup_logging', 'LogTimer',
    # Errors
    'OrchestratorError', 'RetryableError', 'FatalError', 'AnalystError',
    'RetryPolicy', 'RETRY_POLICY_API', 'RETRY_POLICY_ANALYST', 'RETRY_POLICY_EXA',
    'is_retryable_error', 'classify_error', 'with_retry', 'with_retry_async',
    # LLM
    'get_client', 'get_async_client', 'llm_call', 'llm_call_async',
    # Exa
    'EXA_AVAILABLE', 'EXA_MAX_SEARCHES',
    'get_exa_client', 'reset_exa_search_count', 'get_exa_search_count',
    'exa_search', 'exa_search_for_citation',
    # UI
    'ask_user', 'confirm', 'get_input',
    'SECTION_EMOJIS', 'section_header', 'print_section_header', 'display_section',
    'RecoveryAction', 'recovery_menu', 'should_continue_on_error',
    # Validation
    'validate_analyst_output', 'validate_citation_map', 'validate_frontmatter',
    'REQUIRED_FRONTMATTER',
    # Orchestrator
    'StrategicOrchestrator',
    # Recipe
    'RecipeRunner', 'discover_recipes', 'load_recipe',
    # Editorial
    'run_editorial_workflow',
    'select_or_create_topic', 'build_problem_from_item',
    'load_editorial_plan', 'update_item_status',
    'CONTEXT_DOCUMENTS_PATH',
]
