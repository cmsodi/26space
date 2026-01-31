"""
Phase 4.4: Full text generation and file I/O.

Provides OutputMixin with document generation, frontmatter management,
slug generation, and file save operations.
All methods access orchestrator state through self.state, self._vprint, etc.
"""

from datetime import date
from pathlib import Path

import yaml

from .config import MODEL_COMPLEX
from .logging_setup import logger
from .llm import llm_call
from .ui import section_header
from .validation import validate_frontmatter, REQUIRED_FRONTMATTER
from .utils import (
    generate_slug as _generate_slug_fn,
    generate_unique_slug as _generate_unique_slug_fn,
    get_document_filename as _get_document_filename_fn,
)


class OutputMixin:
    """
    Phase 4.4: full text generation and file I/O for StrategicOrchestrator.

    Handles: prose document generation, citation weaving, frontmatter
    validation/repair, slug generation, and file save operations.
    """

    # ============== Full Text Generation ==============

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
- slug: "{self.state.slug}"
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
                    "slug": self.state.slug,
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

    # ============== Slug & File I/O ==============

    def _generate_slug(self) -> str:
        """Generate slug from problem statement."""
        return _generate_slug_fn(self.state.problem)

    def _generate_unique_slug(self) -> str:
        """Generate a unique slug by adding progressive numbers if folder exists."""
        return _generate_unique_slug_fn(self.state.problem)

    def _generate_complete_frontmatter(self) -> str:
        """Generate complete frontmatter block."""
        frontmatter = {
            "title": "Strategic Analysis",
            "description": self.state.problem[:200],
            "slug": self.state.slug,
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
        return _get_document_filename_fn(self.state.language)

    def _save_outline(self, outline: str) -> Path:
        """Save outline to file and return the path."""
        output_dir = self._get_output_dir(self.state.slug)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / self._get_outline_filename()
        filepath.write_text(outline, encoding="utf-8")
        return filepath

    def _save_final_document(self, document: str) -> Path:
        """Save final document to file and return the path."""
        output_dir = self._get_output_dir(self.state.slug)
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
        output_dir = self._get_output_dir(self.state.slug)
        output_dir.mkdir(parents=True, exist_ok=True)

        filepath = output_dir / f"{agent_name}.md"
        filepath.write_text(raw_output, encoding="utf-8")
        logger.debug(f"Saved agent output: {filepath}")
        return filepath
