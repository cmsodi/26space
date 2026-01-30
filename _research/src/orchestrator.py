"""
Main StrategicOrchestrator class - the core workflow engine.
"""

import asyncio
import logging
import re
import time
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from .config import (
    Step, SYNTHESIZERS, TEMPLATES,
    MODEL_DEFAULT, MODEL_COMPLEX
)
from .models import (
    Source, TextDocument, AnalystOutput, CitationEntry, WorkflowState
)
from .state import (
    workflow_state_to_dict, workflow_state_from_dict,
    load_agent, load_output_generation
)
from .logging_setup import logger, LogTimer
from .errors import FatalError, AnalystError
from .llm import llm_call, llm_call_async
from .exa import (
    EXA_AVAILABLE, EXA_MAX_SEARCHES,
    reset_exa_search_count, get_exa_search_count,
    exa_search_for_citation
)
from .ui import (
    ask_user, confirm, get_input,
    section_header, print_section_header, display_section,
    RecoveryAction, recovery_menu
)
from .validation import (
    validate_analyst_output, validate_citation_map,
    validate_frontmatter, REQUIRED_FRONTMATTER
)
from .utils import (
    detect_language as _detect_language_fn,
    generate_slug as _generate_slug_fn,
    generate_unique_slug as _generate_unique_slug_fn,
    get_document_filename as _get_document_filename_fn,
)


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

    # ============== State Persistence ==============

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

        # Ensure slug is generated (backward compatibility for old state files)
        if not orch.state.slug and orch.state.problem:
            orch.state.slug = orch._generate_slug()

        saved_at = state_dict.get("_saved_at", "unknown")
        orch._vprint(f"  📂 State loaded from: {filepath}")
        orch._vprint(f"     Saved at: {saved_at}")
        orch._vprint(f"     Current step: {orch.state.current_step.value}")

        return orch

    @classmethod
    def load_from_folder(
        cls,
        folder_path: str,
        parallel_analysts: bool = True,
        graceful_degradation: bool = True,
        auto_recovery: bool = False,
        max_analyst_retries: int = 2,
        verbose: bool = False
    ) -> "StrategicOrchestrator":
        """
        Load analyst reports from an output folder and resume workflow.

        Reconstructs the workflow state by reading agent output files from
        a previous analysis. Useful for reusing analyst reports with different
        outline templates or synthesizers.

        Args:
            folder_path: Path to output folder (e.g., output/my-analysis_1)
            parallel_analysts: Whether to use parallel analyst execution
            graceful_degradation: Continue with partial results on failures
            auto_recovery: Automatically choose recovery actions
            max_analyst_retries: Maximum retries for failed analysts
            verbose: Show detailed output

        Returns:
            StrategicOrchestrator instance ready to continue from outline generation
        """
        folder = Path(folder_path)
        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        if not folder.is_dir():
            raise ValueError(f"Not a directory: {folder_path}")

        # Create orchestrator
        orch = cls(
            parallel_analysts=parallel_analysts,
            graceful_degradation=graceful_degradation,
            auto_recovery=auto_recovery,
            max_analyst_retries=max_analyst_retries,
            verbose=verbose
        )

        orch._vprint(f"\n  📂 Loading analyst reports from: {folder_path}")

        # Extract slug from folder name
        slug = folder.name
        orch.state.slug = slug

        # Try to load metadata from existing outline or index.md
        metadata_loaded = False
        for filename in ["outline.md", "index.md"]:
            filepath = folder / filename
            if filepath.exists():
                try:
                    content = filepath.read_text(encoding='utf-8')
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            frontmatter = yaml.safe_load(parts[1]) or {}

                            # Extract metadata
                            orch.state.problem = frontmatter.get("description", "")
                            orch.state.language = frontmatter.get("language", "en")
                            orch.state.synthesizer = frontmatter.get("synthesizer", "")
                            orch.state.template = frontmatter.get("outline_template", "")
                            orch.state.fixed_analysts = frontmatter.get("analysts_fixed", [])
                            orch.state.optional_analysts = frontmatter.get("analysts_optional", [])

                            metadata_loaded = True
                            orch._vprint(f"  ✓ Metadata loaded from {filename}")
                            break
                except Exception as e:
                    orch._vprint(f"  ⚠ Could not parse {filename}: {e}")

        if not metadata_loaded:
            orch._vprint("  ⚠ No metadata found in outline.md or index.md")
            # Will prompt user for missing info later

        # Load all agent output files
        agent_files = list(folder.glob("*.md"))
        # Filter out special files
        agent_files = [f for f in agent_files if f.stem not in ["outline", "index"]]

        if not agent_files:
            raise ValueError(f"No agent output files (*.md) found in {folder_path}")

        orch._vprint(f"\n  Found {len(agent_files)} agent output file(s):")

        # Parse each agent output file
        for agent_file in sorted(agent_files):
            agent_name = agent_file.stem
            try:
                content = agent_file.read_text(encoding='utf-8')
                parsed = validate_analyst_output(content, agent_name)
                orch.state.analyst_outputs[agent_name] = parsed
                orch._vprint(f"    ✓ {agent_name} (confidence: {parsed.confidence})")
            except Exception as e:
                orch._vprint(f"    ✗ {agent_name}: {e}")
                if not graceful_degradation:
                    raise

        if not orch.state.analyst_outputs:
            raise ValueError("Failed to load any valid analyst outputs")

        # Update fixed_analysts list if empty
        if not orch.state.fixed_analysts:
            orch.state.fixed_analysts = list(orch.state.analyst_outputs.keys())

        orch._vprint(f"\n  ✓ Loaded {len(orch.state.analyst_outputs)} analyst report(s)")

        # Show current configuration and allow modifications
        orch._vprint("\n" + "=" * 60)
        orch._vprint("Current Configuration:")
        orch._vprint("-" * 40)
        orch._vprint(f"  Problem: {orch.state.problem[:80]}..." if len(orch.state.problem) > 80 else f"  Problem: {orch.state.problem}")
        orch._vprint(f"  Synthesizer: {orch.state.synthesizer or '(not set)'}")
        orch._vprint(f"  Template: {orch.state.template or '(not set)'}")
        orch._vprint(f"  Language: {orch.state.language}")
        orch._vprint(f"  Analysts: {', '.join(orch.state.fixed_analysts)}")
        orch._vprint("-" * 40)

        # Allow user to modify configuration before continuing
        while True:
            options = [
                "Continue with current configuration",
                "Change synthesizer",
                "Change template",
                "Cancel and exit"
            ]

            choice = ask_user("Review configuration:", options, allow_other=False)

            if "Continue" in choice:
                break
            elif "Change synthesizer" in choice:
                orch._modify_synthesizer()
            elif "Change template" in choice:
                orch._modify_template()
            elif "Cancel" in choice:
                orch._vprint("\n  Cancelled by user")
                raise KeyboardInterrupt()

        # Set current step to just before outline generation
        orch.state.current_step = Step.ANALYSTS_COMPLETE
        orch._vprint(f"\n  📍 Ready to continue from: {orch.state.current_step.value}")

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
        self.state.slug = self._generate_unique_slug()  # Generate unique slug with numbering if needed
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

    # ============== PHASE 1: Problem Parsing ==============

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
        return _detect_language_fn(text)

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

    # ============== PHASE 1.5: Fresh Sources ==============

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

    # ============== PHASE 2: Clarification ==============

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

        # Generate clarification question via LLM
        system = """You are helping clarify a strategic analysis request.
The problem could fit multiple analysis frameworks. Generate exactly 1 targeted question
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
        """Present single clarification question to user and capture answer."""
        # User prompts must ALWAYS be visible (not _vprint)
        q = questions[0]
        question_text = q.get("question", str(q))
        print(f"\n  Clarification needed:\n  {question_text}")
        print("  (any format: plain text, markdown, yaml...)")
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

    # ============== PHASE 3: Proposal ==============

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

        if self.state.text_documents:
            lines.append(f"Text Documents (inline): {len(self.state.text_documents)} file(s)")
            for td in self.state.text_documents:
                label = f" ({td.label})" if td.label else ""
                lines.append(f"  - {td.filename}{label} [{len(td.content)} chars]")

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
        """Allow user to add context documents (L0 sources) with URLs or text files."""
        # Show current documents if any
        if self.state.context_documents:
            print(f"\n  Currently loaded: {len(self.state.context_documents)} L0 source(s)")
            for i, doc in enumerate(self.state.context_documents[:5], 1):
                print(f"    {i}. {doc.title[:50]}{'...' if len(doc.title) > 50 else ''}")
            if len(self.state.context_documents) > 5:
                print(f"    ... and {len(self.state.context_documents) - 5} more")
        if self.state.text_documents:
            print(f"  Text documents: {len(self.state.text_documents)} file(s)")
            for td in self.state.text_documents:
                label = f" ({td.label})" if td.label else ""
                print(f"    - {td.filename}{label} [{len(td.content)} chars]")

        options = [
            "Load from YAML file (research_briefing.yaml format)",
            "Load text file (.md or .txt for inline context)",
            "Add single URL manually",
            "Clear all context documents",
            "Done - return to proposal"
        ]

        while True:
            choice = ask_user("Context documents:", options, allow_other=False)

            if "YAML" in choice:
                # List available YAML files in context_documents/
                context_dir = Path("context_documents")
                if context_dir.exists():
                    yaml_files = sorted([f.name for f in context_dir.glob("*.yaml")] +
                                      [f.name for f in context_dir.glob("*.yml")])
                    if yaml_files:
                        print(f"\n  Available YAML files in context_documents/:")
                        for f in yaml_files:
                            print(f"    - {f}")
                    else:
                        print(f"  No YAML files found in context_documents/")
                else:
                    print(f"  Warning: context_documents/ directory not found")

                # Prompt for file(s)
                print(f"\n  Enter one or more filenames (comma-separated)")
                print(f"  Example: test.yaml  or  test.yaml, briefing.yaml")
                filenames = get_input("Filenames (or press Enter to skip)")

                if not filenames:
                    # User chose to skip
                    continue

                # Process comma-separated list
                loaded_count = 0
                for filename in [f.strip() for f in filenames.split(",")]:
                    if not filename:
                        continue

                    # Always look in context_documents/
                    file_path = context_dir / filename

                    if file_path.exists():
                        try:
                            self._load_research_briefing(str(file_path))
                            loaded_count += 1
                            print(f"  ✓ Loaded: {filename}")
                        except Exception as e:
                            print(f"  ✗ Error loading {filename}: {e}")
                    else:
                        print(f"  ✗ File not found: {filename}")

                if loaded_count > 0:
                    print(f"\n  Total loaded: {loaded_count} file(s), {len(self.state.context_documents)} L0 source(s)")

            elif "text file" in choice.lower():
                # List available .md and .txt files in context_documents/
                context_dir = Path("context_documents")
                if context_dir.exists():
                    text_files = sorted(
                        [f.name for f in context_dir.glob("*.md")] +
                        [f.name for f in context_dir.glob("*.txt")]
                    )
                    if text_files:
                        print(f"\n  Available text files in context_documents/:")
                        for f in text_files:
                            print(f"    - {f}")
                    else:
                        print(f"  No .md or .txt files found in context_documents/")
                else:
                    print(f"  Warning: context_documents/ directory not found")

                print(f"\n  Enter one or more filenames (comma-separated)")
                print(f"  Example: notes.md  or  notes.md, background.txt")
                filenames = get_input("Filenames (or press Enter to skip)")

                if not filenames:
                    continue

                loaded_count = 0
                for filename in [f.strip() for f in filenames.split(",")]:
                    if not filename:
                        continue
                    file_path = context_dir / filename
                    if file_path.exists() and file_path.suffix in (".md", ".txt"):
                        try:
                            content = file_path.read_text(encoding="utf-8")
                            self.state.text_documents.append(TextDocument(
                                filename=filename,
                                content=content
                            ))
                            loaded_count += 1
                            print(f"  ✓ Loaded: {filename} ({len(content)} chars)")
                        except Exception as e:
                            print(f"  ✗ Error loading {filename}: {e}")
                    elif file_path.exists():
                        print(f"  ✗ Unsupported extension: {filename} (only .md and .txt)")
                    else:
                        print(f"  ✗ File not found: {filename}")

                if loaded_count > 0:
                    print(f"\n  Total text documents: {len(self.state.text_documents)}")

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
                self.state.text_documents = []
                print("  All context documents cleared")

            elif "Done" in choice:
                break

        # Summary
        if self.state.context_documents:
            print(f"\n  Total L0 sources: {len(self.state.context_documents)}")
        if self.state.text_documents:
            print(f"  Total text documents: {len(self.state.text_documents)}")

    # ============== PHASE 4: Execution ==============

    def _phase_4_execute(self):
        """Execute the full analysis workflow: analysts → outline → citations → full text."""
        self._vprint(section_header("PHASE 4: Execution", emoji="⚡"))

        # Execute analysts (parallel by default, configurable)
        self._execute_analysts(parallel=self.parallel_analysts)

        # Generate and approve outline
        self._generate_and_approve_outline()

        # Citation enrichment
        self._enrich_citations()

        # Generate full text
        self._generate_full_text()

        self.state.current_step = Step.COMPLETE

    # ============== Analyst Execution ==============

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

        text_docs_text = ""
        if self.state.text_documents:
            text_docs_text = "\n\n## Inline Context Documents\n"
            text_docs_text += "Use the following documents as background context for your analysis. "
            text_docs_text += "These are NOT citable URL sources — they provide direction and depth.\n"
            for td in self.state.text_documents:
                label = f" — {td.label}" if td.label else ""
                text_docs_text += f"\n### {td.filename}{label}\n\n{td.content}\n"

        user_message = f"""## Analysis Request

**Problem:** {self.state.problem}

**Language:** {self.state.language}

**Web Search:** {"Enabled" if self.state.web_search_enabled else "Disabled"}
{context_docs_text}{text_docs_text}

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

    # ============== Async Analyst Execution ==============

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

        text_docs_text = ""
        if self.state.text_documents:
            text_docs_text = "\n\n## Inline Context Documents\n"
            text_docs_text += "Use the following documents as background context for your analysis. "
            text_docs_text += "These are NOT citable URL sources — they provide direction and depth.\n"
            for td in self.state.text_documents:
                label = f" — {td.label}" if td.label else ""
                text_docs_text += f"\n### {td.filename}{label}\n\n{td.content}\n"

        user_message = f"""## Analysis Request

**Problem:** {self.state.problem}

**Language:** {self.state.language}

**Web Search:** {"Enabled" if self.state.web_search_enabled else "Disabled"}
{context_docs_text}{text_docs_text}

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

    # ============== Outline Generation ==============

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

    # ============== Citation Enrichment ==============

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
