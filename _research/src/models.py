"""
Data models (dataclasses) for the Strategic Orchestrator.
"""

from dataclasses import dataclass, field
from typing import Optional

from .config import Step


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
class TextDocument:
    """Inline text document loaded from .md or .txt file for background context."""
    filename: str       # Original filename (e.g., "briefing.md")
    content: str        # Full text content
    label: str = ""     # Optional user-provided label


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
    slug: str = ""  # Generated from problem, used for output directory

    # Current position
    current_step: Step = Step.INIT

    # Phase 1 outputs
    problem_keywords: list[str] = field(default_factory=list)
    synthesizer_scores: dict[str, float] = field(default_factory=dict)

    # Phase 1.5 outputs
    fresh_sources_need: str = ""  # HIGH, MEDIUM, LOW
    fresh_sources_choice: str = ""  # A, B, C
    context_documents: list[Source] = field(default_factory=list)  # L0 sources
    text_documents: list[TextDocument] = field(default_factory=list)  # Inline text context (.md/.txt)

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
