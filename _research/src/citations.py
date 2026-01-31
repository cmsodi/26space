"""
Phase 4.3: Citation enrichment engine.

Provides CitationsMixin with citation mapping, Exa L2 gap filling,
and citation validation/recovery.
All methods access orchestrator state through self.state, self._vprint, etc.
"""

import yaml

from .config import Step, MODEL_DEFAULT
from .models import CitationEntry
from .llm import llm_call
from .exa import (
    EXA_AVAILABLE, EXA_MAX_SEARCHES,
    get_exa_search_count, exa_search_for_citation
)
from .ui import confirm, section_header
from .validation import validate_citation_map


class CitationsMixin:
    """
    Phase 4.3: citation enrichment methods for StrategicOrchestrator.

    Handles: source-to-outline mapping, citation map parsing,
    L2 Exa web search for gaps, and citation recovery.
    """

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
        remaining_searches = EXA_MAX_SEARCHES - get_exa_search_count()
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
