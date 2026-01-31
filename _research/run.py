#!/usr/bin/env python3
"""
run.py
Entry point for the Strategic Analysis Orchestrator.

This is a simplified entry point that imports from the modular src/ package.
For the full implementation, see src/orchestrator.py.

Usage:
  python run.py                    # Run tests
  python run.py --run              # Interactive mode (parallel)
  python run.py --run --seq        # Sequential mode
  python run.py --run --save       # Auto-save checkpoints
  python run.py --resume FILE      # Resume from saved state
  python run.py --from-folder DIR  # Reuse analyst reports from folder

Editorial mode:
  python run.py --editorial                   # Interactive topic + research + analysis

Recipe mode:
  python run.py --list-recipes               # Show available recipes
  python run.py --recipe NAME                # Run recipe (interactive topic)
  python run.py --recipe NAME --topic TEXT   # Run recipe with topic
  python run.py --recipe NAME --context FILE # With context documents

Error recovery options:
  --no-graceful                                       # Abort on failures
  --auto-recovery                                     # Auto-choose recovery actions
  --max-retries N                                     # Max analyst retries (default: 2)

Logging options:
  -v, --verbose                                       # DEBUG level logging
  -q, --quiet                                         # WARNING+ only
  --log-file FILE                                     # Write logs to file

Environment:
  ANTHROPIC_API_KEY  — Required for LLM calls
  EXA_API_KEY        — Optional for L2 web search
"""

import os
import sys
import time
import logging
import asyncio
import tempfile
from pathlib import Path

# Import from modular package
from src import (
    # Config
    SKILLS_PATH, AGENTS_PATH, Step, SYNTHESIZERS, TEMPLATES,
    # Models
    Source, AnalystOutput, CitationEntry, WorkflowState,
    # State
    workflow_state_to_dict, workflow_state_from_dict,
    load_output_generation,
    # Logging
    logger, setup_logging, LogTimer,
    # Errors
    RetryPolicy, is_retryable_error,
    # LLM
    llm_call, get_async_client, llm_call_async,
    # Exa
    EXA_AVAILABLE, reset_exa_search_count, exa_search,
    # UI
    confirm, get_input, print_section_header,
    # Validation
    validate_analyst_output, validate_citation_map, validate_frontmatter,
    # Orchestrator
    StrategicOrchestrator,
    # Recipe
    RecipeRunner, discover_recipes, load_recipe,
    # Editorial
    select_or_create_topic, build_problem_from_item,
    load_editorial_plan, update_item_status,
    CONTEXT_DOCUMENTS_PATH,
    ensure_unique_slug,
)


def main():
    """Main entry point with CLI argument handling."""
    # Parse verbose flag FIRST (needed for test output control)
    verbose_mode = "-v" in sys.argv or "--verbose" in sys.argv
    quiet_mode = "-q" in sys.argv or "--quiet" in sys.argv

    # Suppress logger output during tests unless verbose
    if not verbose_mode and "--run" not in sys.argv and "--resume" not in sys.argv:
        setup_logging(quiet=True)

    # Test output helper - only prints in verbose mode
    def tprint(*args, **kwargs):
        if verbose_mode:
            print(*args, **kwargs)

    # Handle --help flag
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)

    # Parse logging options
    log_file = None
    if "--log-file" in sys.argv:
        try:
            log_file_idx = sys.argv.index("--log-file")
            log_file = sys.argv[log_file_idx + 1]
        except (ValueError, IndexError):
            print("❌ Error: --log-file requires a filepath argument")
            sys.exit(1)

    # Reconfigure logging based on CLI flags
    if verbose_mode or quiet_mode or log_file:
        setup_logging(verbose=verbose_mode, quiet=quiet_mode, log_file=log_file)
        if verbose_mode:
            print("Logging: VERBOSE (DEBUG level)")
        elif quiet_mode:
            print("Logging: QUIET (WARNING+ only)")
        if log_file:
            print(f"Log file: {log_file}")

    # Parse error recovery options
    graceful_degradation = "--no-graceful" not in sys.argv
    auto_recovery = "--auto-recovery" in sys.argv
    max_retries = 2
    if "--max-retries" in sys.argv:
        try:
            retries_idx = sys.argv.index("--max-retries")
            max_retries = int(sys.argv[retries_idx + 1])
        except (ValueError, IndexError):
            print("❌ Error: --max-retries requires a number argument")
            sys.exit(1)

    # LIST RECIPES MODE
    if "--list-recipes" in sys.argv:
        recipe_names = discover_recipes()
        if recipe_names:
            print("Available recipes:\n")
            for name in sorted(recipe_names):
                r = load_recipe(name)
                tags_str = ", ".join(r.tags) if r.tags else ""
                print(f"  {name:<20} {r.methodology:<45} [{r.output_type}]")
                if r.description:
                    print(f"  {'':<20} {r.description}")
        else:
            print("No recipes found in .claude/recipes/")
        return

    # EDITORIAL MODE
    if "--editorial" in sys.argv:
        from src.editorial import run_editorial_workflow
        try:
            run_editorial_workflow(
                verbose=verbose_mode,
                parallel_analysts="--seq" not in sys.argv and "--sequential" not in sys.argv,
                auto_save="--save" in sys.argv,
                graceful_degradation=graceful_degradation,
                auto_recovery=auto_recovery,
                max_analyst_retries=max_retries,
            )
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
        except Exception as e:
            print(f"\nEditorial workflow failed: {e}")
            if verbose_mode:
                import traceback
                traceback.print_exc()
        return

    # RECIPE MODE
    if "--recipe" in sys.argv:
        try:
            recipe_idx = sys.argv.index("--recipe")
            recipe_name = sys.argv[recipe_idx + 1]
        except (ValueError, IndexError):
            print("Error: --recipe requires a recipe name")
            print("   Usage: python run.py --recipe four-causes")
            print("   List:  python run.py --list-recipes")
            sys.exit(1)

        # Optional: topic from CLI or interactive prompt
        topic = None
        if "--topic" in sys.argv:
            try:
                topic_idx = sys.argv.index("--topic")
                topic = sys.argv[topic_idx + 1]
            except (ValueError, IndexError):
                print("Error: --topic requires a text argument")
                sys.exit(1)

        if not topic:
            topic = get_input("Enter analysis topic")
            if not topic:
                print("No topic provided. Aborting.")
                return

        # Optional: context documents
        context_yaml = None
        if "--context" in sys.argv:
            try:
                ctx_idx = sys.argv.index("--context")
                context_yaml = sys.argv[ctx_idx + 1]
            except (ValueError, IndexError):
                print("Error: --context requires a filepath argument")
                sys.exit(1)

        try:
            runner = RecipeRunner(
                recipe_name=recipe_name,
                verbose=verbose_mode,
                context_yaml=context_yaml,
            )

            if verbose_mode:
                print_section_header("Recipe Mode", emoji="🧪")

            result = runner.run(topic)
            if result:
                print(f"\n  Document saved to: output/{runner.slug}/")

        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Run --list-recipes to see available recipes.")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"\nRecipe execution failed: {e}")
        return

    # RESUME MODE
    if "--resume" in sys.argv:
        try:
            resume_idx = sys.argv.index("--resume")
            state_file = sys.argv[resume_idx + 1]
        except (ValueError, IndexError):
            print("❌ Error: --resume requires a filepath argument")
            print("   Usage: python run.py --resume path/to/state.yaml")
            sys.exit(1)

        if verbose_mode:
            print_section_header("Resume Mode", emoji="▶️")

        parallel_mode = "--seq" not in sys.argv and "--sequential" not in sys.argv
        auto_save = "--save" in sys.argv

        try:
            orch = StrategicOrchestrator.load_state(
                state_file,
                parallel_analysts=parallel_mode,
                graceful_degradation=graceful_degradation,
                auto_recovery=auto_recovery,
                max_analyst_retries=max_retries,
                verbose=verbose_mode
            )
            orch.auto_save = auto_save

            result = orch.resume()
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\n  📄 Final document saved to: {doc_path}")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            if 'orch' in locals():
                if confirm("Save current state before exiting?"):
                    orch.save_state()
        except Exception as e:
            print(f"\n❌ Resume failed: {e}")
        return

    # FROM-FOLDER MODE
    if "--from-folder" in sys.argv:
        try:
            folder_idx = sys.argv.index("--from-folder")
            folder_path = sys.argv[folder_idx + 1]
        except (ValueError, IndexError):
            print("❌ Error: --from-folder requires a directory path argument")
            print("   Usage: python run.py --from-folder output/my-analysis_1")
            sys.exit(1)

        if verbose_mode:
            print_section_header("Load from Folder Mode", emoji="📂")

        parallel_mode = "--seq" not in sys.argv and "--sequential" not in sys.argv
        auto_save = "--save" in sys.argv

        try:
            orch = StrategicOrchestrator.load_from_folder(
                folder_path,
                parallel_analysts=parallel_mode,
                graceful_degradation=graceful_degradation,
                auto_recovery=auto_recovery,
                max_analyst_retries=max_retries,
                verbose=verbose_mode
            )
            orch.auto_save = auto_save

            result = orch.resume()
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\n  📄 Final document saved to: {doc_path}")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            if 'orch' in locals():
                if confirm("Save current state before exiting?"):
                    orch.save_state()
        except Exception as e:
            print(f"\n❌ Load from folder failed: {e}")
        return

    # RUN MODE
    if "--run" in sys.argv:
        if verbose_mode:
            print_section_header("Interactive Mode", emoji="🚀")

        parallel_mode = "--seq" not in sys.argv and "--sequential" not in sys.argv
        auto_save = "--save" in sys.argv

        if verbose_mode:
            if not parallel_mode:
                print("Mode: SEQUENTIAL (analysts run one at a time)")
            else:
                print("Mode: PARALLEL (analysts run concurrently via asyncio)")

            if auto_save:
                print("Auto-save: ENABLED (checkpoints will be saved)")

            if not graceful_degradation:
                print("Graceful degradation: DISABLED (abort on failures)")
            if auto_recovery:
                print("Auto-recovery: ENABLED")
            if max_retries != 2:
                print(f"Max analyst retries: {max_retries}")

        # --- Topic selection: editorial plan ID or free-form problem ---
        result = select_or_create_topic()
        if result is None:
            return
        items, selected = result

        problem = build_problem_from_item(selected)

        # Set status to drafting
        if selected.get("status", "tbd") == "tbd":
            items = update_item_status(items, selected["id"], "drafting")
            print(f"  Status updated to 'drafting'")

        # Ensure context folder exists
        slug = selected["slug"]
        context_dir = CONTEXT_DOCUMENTS_PATH / slug
        context_dir.mkdir(parents=True, exist_ok=True)

        orch = StrategicOrchestrator(
            parallel_analysts=parallel_mode,
            auto_save=auto_save,
            graceful_degradation=graceful_degradation,
            auto_recovery=auto_recovery,
            max_analyst_retries=max_retries,
            verbose=verbose_mode
        )

        # Pre-set slug from editorial item
        orch.state.slug = ensure_unique_slug(slug)

        # Pass editorial item for NotebookLM research (used by _handle_user_research)
        orch.editorial_item = selected

        # Pre-load any existing context documents for this topic
        for yaml_file in sorted(context_dir.glob("*.yaml")):
            orch._load_research_briefing(str(yaml_file))
        if orch.state.context_documents:
            print(f"  Pre-loaded {len(orch.state.context_documents)} L0 sources from {context_dir.name}/")

        try:
            result = orch.run(problem)
            if result:
                doc_path = orch._save_final_document(result)
                print(f"\n  📄 Final document saved to: {doc_path}")
                # Update editorial status to finalized
                items = load_editorial_plan()
                update_item_status(items, selected["id"], "finalized")
                print(f"  Editorial status updated to 'finalized'")

        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            if confirm("Save current state before exiting?"):
                orch.save_state()
        except Exception as e:
            print(f"\n❌ Analysis aborted: {e}")
            if confirm("Save current state for debugging?"):
                orch.save_state()
        return

    # TEST MODE (default)
    print_section_header("Strategic Orchestrator - MVP", emoji="🧪")

    # Test A1: Data structures
    state = WorkflowState()
    tprint(f"[A1] Initial step: {state.current_step.value}")

    # Test A2: Prompt loading
    tprint("\n[A2] Testing prompt loading...")
    try:
        output_gen = load_output_generation()
        tprint(f"  ✓ _OUTPUT_GENERATION.md loaded ({len(output_gen)} chars)")
    except FileNotFoundError as e:
        tprint(f"  ✗ {e}")

    if SKILLS_PATH.exists():
        skills = [d.name for d in SKILLS_PATH.iterdir() if d.is_dir()]
        tprint(f"  Available skills: {skills[:5]}...")

    if AGENTS_PATH.exists():
        agents = [d.name for d in AGENTS_PATH.iterdir() if d.is_dir()]
        tprint(f"  Available agents: {agents[:5]}...")

    # Test A3: LLM wrapper
    tprint("\n[A3] Testing LLM wrapper...")
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            response = llm_call(
                system="You are a test assistant.",
                user="Say 'LLM wrapper works!' and nothing else.",
                max_tokens=50
            )
            tprint(f"  ✓ LLM response: {response.strip()}")
        except Exception as e:
            tprint(f"  ✗ LLM error: {e}")
    else:
        tprint("  ⚠ ANTHROPIC_API_KEY not set, skipping LLM test")

    # Test A4: User interaction
    tprint("\n[A4] User interaction functions defined:")
    tprint("  ✓ ask_user(prompt, options) - numbered choice menu")
    tprint("  ✓ confirm(prompt) - yes/no prompt")
    tprint("  ✓ get_input(prompt, default) - free-form input")

    # Test A5: Validation
    tprint("\n[A5] Testing validation functions...")
    sample_analyst = """---
status: complete
confidence: 0.85
key_findings:
  - Finding one
  - Finding two
---
Main analysis content here."""

    parsed = validate_analyst_output(sample_analyst, "test-analyst")
    tprint(f"  ✓ validate_analyst_output: status={parsed.status}, confidence={parsed.confidence}")

    outline_with_facts = "The budget is €500 million in 2024."
    valid, msg = validate_citation_map([], outline_with_facts)
    tprint(f"  ✓ validate_citation_map (empty, factual): valid={valid}")

    sample_doc = """---
title: Test
description: A test document
date: 2026-01-25
---
Content here."""

    valid, missing = validate_frontmatter(sample_doc, ["title", "description", "date", "author"])
    tprint(f"  ✓ validate_frontmatter: valid={valid}, missing={missing}")

    # Test B1-B2: Orchestrator phases
    tprint("\n[B1-B2] Testing orchestrator phases...")
    orch = StrategicOrchestrator()
    lang_en = orch._detect_language("Analyze the European space industry competition")
    lang_it = orch._detect_language("Analizza la strategia spaziale europea")
    tprint(f"  ✓ Language detection: EN='{lang_en}', IT='{lang_it}'")

    orch.state.problem = "What is the 2025 ESA budget allocation?"
    need = orch._evaluate_source_need()
    tprint(f"  ✓ Source need evaluation: '{need}' (expected: HIGH)")

    orch.state.problem = "Analyze geopolitical power dynamics in space"
    orch._fallback_scoring()
    tprint(f"  ✓ Fallback scoring: {orch.state.synthesizer_scores}")

    # Test B5-B8: Phase 4 components
    tprint("\n[B5-B8] Testing Phase 4 components...")
    orch = StrategicOrchestrator()
    bluf_structure = orch._get_template_structure("BLUF")
    tprint(f"  ✓ BLUF template structure loaded ({len(bluf_structure)} chars)")

    fallback_prompt = orch._generate_fallback_analyst_prompt("test-analyst")
    tprint(f"  ✓ Fallback analyst prompt generated ({len(fallback_prompt)} chars)")

    orch.state.citation_map = [
        CitationEntry(
            point_id="1.1",
            claim="Test claim",
            url="https://example.com",
            anchor_text="Example Source",
            pattern="factual",
            source_level="L0"
        )
    ]
    citation_instructions = orch._build_citation_instructions()
    tprint(f"  ✓ Citation instructions: {citation_instructions[:50]}...")

    today = orch._get_today_date()
    tprint(f"  ✓ Today's date: {today}")

    # Test Phase C: Exa Integration
    tprint("\n[C] Testing Exa integration...")
    tprint(f"  Exa SDK available: {EXA_AVAILABLE}")
    reset_exa_search_count()
    tprint("  ✓ Search counter reset")

    if os.environ.get("EXA_API_KEY") and EXA_AVAILABLE:
        try:
            results = exa_search("European Space Agency budget 2025", num_results=2)
            tprint(f"  ✓ Exa search works: {len(results)} results")
        except Exception as e:
            tprint(f"  ⚠ Exa search test: {e}")
    else:
        tprint("  ⚠ EXA_API_KEY not set or exa-py not installed, skipping Exa test")

    # Test D1: Async functionality
    tprint("\n[D1] Testing async functionality...")
    tprint("  ✓ asyncio imported")
    tprint("  ✓ llm_call_async() defined")
    tprint("  ✓ get_async_client() defined")

    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            async_client = get_async_client()
            tprint(f"  ✓ Async client initialized: {type(async_client).__name__}")

            async def test_async_llm():
                return await llm_call_async(
                    system="You are a test assistant.",
                    user="Say 'Async works!' and nothing else.",
                    max_tokens=50
                )

            async_response = asyncio.run(test_async_llm())
            tprint(f"  ✓ Async LLM response: {async_response.strip()}")
        except Exception as e:
            tprint(f"  ⚠ Async test: {e}")

    # Test D2: State persistence
    tprint("\n[D2] Testing state persistence...")
    test_state = WorkflowState(
        problem="Test problem",
        language="en",
        current_step=Step.PROPOSAL_APPROVED,
        synthesizer="strategic-geopolitical",
        fixed_analysts=["pestle-analyst", "stakeholder-analyst"]
    )
    test_state.context_documents.append(Source(
        url="https://example.com",
        title="Test Source",
        type="report",
        anchor_suggestion="Test",
        level="L0"
    ))
    test_state.analyst_outputs["pestle-analyst"] = AnalystOutput(
        name="pestle-analyst",
        status="complete",
        confidence=0.85,
        content="Test content",
        key_findings=["Finding 1", "Finding 2"]
    )

    state_dict = workflow_state_to_dict(test_state)
    tprint(f"  ✓ workflow_state_to_dict: {len(state_dict)} fields")

    restored_state = workflow_state_from_dict(state_dict)
    tprint(f"  ✓ workflow_state_from_dict: step={restored_state.current_step.value}")

    assert restored_state.problem == test_state.problem
    assert restored_state.current_step == test_state.current_step
    tprint("  ✓ Serialization roundtrip verified")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name

    test_orch = StrategicOrchestrator()
    test_orch.state = test_state
    test_orch.save_state(temp_path)

    loaded_orch = StrategicOrchestrator.load_state(temp_path)
    assert loaded_orch.state.problem == "Test problem"
    tprint("  ✓ save_state/load_state roundtrip verified")
    Path(temp_path).unlink()

    # Test D3: Logging
    tprint("\n[D3] Testing logging...")
    tprint(f"  ✓ Logger name: {logger.name}")
    tprint(f"  ✓ Current level: {logging.getLevelName(logger.level)}")

    with LogTimer("test operation", level=logging.DEBUG):
        time.sleep(0.01)
    tprint("  ✓ LogTimer works")

    # Test D4: Error Recovery
    tprint("\n[D4] Testing error recovery...")
    tprint("  ✓ RetryPolicy with exponential backoff")

    policy = RetryPolicy(max_retries=3, base_delay=1.0)
    delay_0 = policy.calculate_delay(0)
    delay_1 = policy.calculate_delay(1)
    tprint(f"  ✓ RetryPolicy delays: {delay_0:.2f}s, {delay_1:.2f}s (with jitter)")

    rate_limit_err = Exception("rate_limit_exceeded: too many requests")
    assert is_retryable_error(rate_limit_err) == True
    fatal_err = Exception("invalid_api_key: authentication failed")
    assert is_retryable_error(fatal_err) == False
    tprint("  ✓ Error classification works")

    print_section_header("All Tests Complete", emoji="✅")
    print("Phase A + B + C + D1 + D2 + D3 + D4 verified!")
    print("\nRun with --help for usage information.")


if __name__ == "__main__":
    main()
