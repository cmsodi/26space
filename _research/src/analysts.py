"""
Phase 4.1: Analyst execution engine.

Provides AnalystsMixin with sequential, parallel (async), and recovery logic.
All methods access orchestrator state through self.state, self._vprint, etc.
"""

import asyncio
import time

from .config import Step, MODEL_DEFAULT
from .models import AnalystOutput
from .state import load_agent
from .logging_setup import logger
from .errors import FatalError, AnalystError
from .llm import llm_call, llm_call_async
from .ui import section_header, RecoveryAction, recovery_menu
from .validation import validate_analyst_output


class AnalystsMixin:
    """
    Phase 4.1: analyst execution methods for StrategicOrchestrator.

    Handles: sequential and parallel (asyncio) analyst execution,
    failure detection, retry logic, and recovery menus.
    """

    # ============== Recovery & Dispatch ==============

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

    # ============== Sequential Execution ==============

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

    # ============== Single Analyst Runner ==============

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
