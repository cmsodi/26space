"""
Validation functions for analyst outputs, citations, and documents.
"""

import re
from typing import Optional

import yaml

from .models import Source, AnalystOutput, CitationEntry


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
