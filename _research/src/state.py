"""
State serialization and prompt loading for the Strategic Orchestrator.
"""

from datetime import datetime
from pathlib import Path

from .config import SKILLS_PATH, AGENTS_PATH, OUTPUT_GEN_PATH, Step
from .models import Source, AnalystOutput, CitationEntry, WorkflowState, TextDocument


# ============== STATE SERIALIZATION ==============

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


def text_document_to_dict(td: TextDocument) -> dict:
    """Convert TextDocument to serializable dict."""
    return {
        "filename": td.filename,
        "content": td.content,
        "label": td.label
    }


def text_document_from_dict(d: dict) -> TextDocument:
    """Restore TextDocument from dict."""
    return TextDocument(
        filename=d.get("filename", ""),
        content=d.get("content", ""),
        label=d.get("label", "")
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
        "text_documents": [text_document_to_dict(td) for td in state.text_documents],

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
        text_documents=[text_document_from_dict(td) for td in d.get("text_documents", [])],

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


# ============== PROMPT LOADING ==============

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
