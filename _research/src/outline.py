"""
Phase 4.2: Outline generation and approval.

Provides OutlineMixin with outline generation, template management,
and enforced user approval loop.
All methods access orchestrator state through self.state, self._vprint, etc.
"""

from .config import Step, MODEL_DEFAULT
from .state import load_output_generation
from .llm import llm_call
from .ui import ask_user, get_input, section_header


class OutlineMixin:
    """
    Phase 4.2: outline generation methods for StrategicOrchestrator.

    Handles: outline generation from analyst outputs, template structure
    definitions, user approval loop, and outline modifications.
    """

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
- title, description, date (today)
- slug: "{self.state.slug}"
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
