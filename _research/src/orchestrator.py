"""
Main StrategicOrchestrator class - the core workflow engine.
"""

import logging
import time
from pathlib import Path
from typing import Optional

import yaml

from .config import Step, SYNTHESIZERS, TEMPLATES
from .models import WorkflowState
from .state import workflow_state_to_dict, workflow_state_from_dict
from .logging_setup import logger, LogTimer
from .llm import llm_call
from .exa import reset_exa_search_count
from .ui import (
    ask_user, get_input,
    section_header, display_section
)
from .validation import validate_analyst_output
from .utils import detect_language as _detect_language_fn
from .execution import ExecutionMixin
from .context_loader import ContextLoaderMixin


class StrategicOrchestrator(ExecutionMixin, ContextLoaderMixin):
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
        self.editorial_item = None  # Set externally for NotebookLM research

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
        self.state.slug = self.state.slug or self._generate_unique_slug()  # Skip if pre-set (e.g. --editorial)
        workflow_start = time.time()

        # Reset Exa search counter for this analysis
        reset_exa_search_count()

        logger.info(f"Starting analysis: '{problem[:80]}{'...' if len(problem) > 80 else ''}'")
        logger.debug(f"Full problem ({len(problem)} chars): {problem}")

        self._vprint(section_header("STRATEGIC ORCHESTRATOR", emoji="👨‍💼"))

        # Phase 1.5: Fresh sources decision (before parsing so research
        # results are available for subsequent phases)
        with LogTimer("Phase 1.5: Fresh sources"):
            self._phase_1_5_sources()

        # Phase 1: Parse problem
        with LogTimer("Phase 1: Problem parsing"):
            self._phase_1_parse()

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
        """Run NotebookLM deep research. Warn and continue on failure."""
        # Lazy import to avoid circular dependency (editorial imports orchestrator)
        from .notebooklm_client import NOTEBOOKLM_AVAILABLE
        from .editorial import run_notebooklm_research

        if not NOTEBOOKLM_AVAILABLE:
            print("\n  ⚠ NotebookLM not available (notebooklm-py not installed)")
            print("  Continuing without NotebookLM research. You can create a notebook manually.")
            return

        if not self.editorial_item:
            print("\n  ⚠ No editorial item context available for research")
            print("  Continuing without NotebookLM research.")
            return

        print("\n  Starting NotebookLM deep research...")
        sources_path = None
        research_failed = False
        try:
            # run_notebooklm_research handles its own event loop and client cleanup
            sources_path = run_notebooklm_research(self.editorial_item)
        except Exception as e:
            print(f"  ⚠ NotebookLM research failed: {e}")
            logger.exception("NotebookLM research failed")
            research_failed = True

        if sources_path and sources_path.exists():
            self._load_research_briefing(str(sources_path))
            print(f"  Loaded {len(self.state.context_documents)} L0 sources")
            return

        if not research_failed:
            print("  ⚠ NotebookLM research returned no sources.")
        print("  Continuing without NotebookLM research. You can create a notebook manually.")

    # ============== PHASE 2: Clarification ==============

    def _phase_2_clarify(self):
        """Ask clarification questions if ambiguity detected."""
        self._vprint(section_header("PHASE 2: Ambiguity Check", emoji="❓"))

        # Skip clarification if editorial item has a detailed deep_prompt
        editorial = getattr(self, 'editorial_item', None)
        if editorial and isinstance(editorial, dict) and editorial.get('deep_prompt'):
            self._vprint("  Editorial deep_prompt is already specific, skipping clarification")
            self.state.current_step = Step.CLARIFIED
            return

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
