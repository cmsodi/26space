# Python Orchestrator Implementation Plan

> **North Star Document** — Updated: 2026-01-25
> This document guides the migration from pure-markdown skills to a hybrid Python orchestrator architecture.

## 🚀 NEXT SESSION: Start Here

**Current status:** Phase A, B, C, D1, D2, D3, D4 complete ✅

**What's done:**
- Full workflow from problem input to final document
- All checkpoints enforced (outline approval, citation validation, frontmatter)
- L2 Exa web search integrated (max 3 searches per analysis)
- **D1 Async analysts**: Parallel execution via asyncio (default), sequential fallback
- **D2 State persistence**: Save/resume workflow with YAML serialization
- **D3 Logging**: Configurable logging with verbose/quiet modes and file output
- **D4 Error recovery**: Retry logic with exponential backoff, graceful degradation, partial analyst recovery
- Run `python strategic_orchestrator.py` for tests
- Run `python strategic_orchestrator.py --run` for interactive mode (parallel)
- Run `python strategic_orchestrator.py --run --seq` for sequential mode
- Run `python strategic_orchestrator.py --run --save` for auto-checkpoint mode
- Run `python strategic_orchestrator.py --resume FILE` to resume from saved state
- Use `-v` for verbose/DEBUG, `-q` for quiet, `--log-file FILE` for file logging
- Use `--no-graceful` to abort on failures, `--auto-recovery` for automatic recovery

**Environment variables:**
- `ANTHROPIC_API_KEY` — Required for LLM calls
- `EXA_API_KEY` — Optional, enables L2 web search

**Next steps (Phase D):**
1. ~~**D1**: Async analysts~~ ✅
2. ~~**D2**: State persistence~~ ✅
3. ~~**D3**: Logging and debugging~~ ✅
4. ~~**D4**: Error recovery~~ ✅
5. **D5**: Integration with Claude Code skills (optional)

**File:** `strategic_orchestrator.py` (~2900 lines)

---

## 1. Problem Statement

The current all-markdown skill architecture relies on LLM discipline for:
- State persistence (citation_map, analyst_outputs)
- Checkpoint enforcement (outline approval, validation)
- Sequential step execution
- Data validation

**Result:** Probabilistic compliance. The LLM may skip steps, lose state, or proceed without proper validation.

### Critical Weaknesses (from flow_weaknesses.md)

| # | Issue | Impact |
|---|-------|--------|
| 1 | `citation_map` not persisted as artifact | End-list citations instead of woven inline |
| 2 | No checkpoint after analyst execution | Hallucinated integration from empty outputs |
| 3 | `[Source: analyst-X]` removal timing unclear | Inconsistent markers in final output |
| 4 | `context_documents` handoff gap | L0 sources ignored |

---

## 2. Target Architecture

```
Python orchestrator (strategic_orchestrator.py)
  ├── WorkflowState (dataclass)          # Persistent state
  │   ├── context_documents: List[Source]
  │   ├── analyst_outputs: Dict[str, AnalystOutput]
  │   ├── approved_outline: str
  │   ├── citation_map: List[CitationEntry]
  │   └── current_step: Enum
  │
  ├── run_analysis(problem: str)
  │   ├── phase_1_parse_problem()        → LLM call
  │   ├── phase_1_5_fresh_sources()      → user prompt, BLOCKS
  │   ├── phase_2_clarify()              → LLM + user if needed
  │   ├── phase_3_propose()              → LLM + user approval, BLOCKS
  │   ├── phase_4_execute()
  │   │   ├── launch_analysts()          → sequential LLM calls
  │   │   ├── validate_outputs()         → schema check, ENFORCED
  │   │   ├── integrate()                → LLM call
  │   │   ├── generate_outline()         → LLM call
  │   │   ├── user_approval()            → BLOCKS until approved
  │   │   ├── citation_enrichment()      → LLM + Exa
  │   │   ├── validate_citation_map()    → ENFORCED, raises if empty
  │   │   └── generate_full_text()       → LLM call
  │   └── return final_document
```

### What Stays in Markdown
- Skill/agent prompts (templates injected by Python)
- Content generation logic
- Flexible analyst reasoning

### What Moves to Python
- Flow control and orchestration
- State persistence
- Validation and checkpoints
- User interaction (CLI)

---

## 3. Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM API | Anthropic SDK directly | Cleaner, more control than wrapping Task tool |
| User interaction | CLI with `input()` | Simple, testable, no dependencies |
| Analysts | Sequential (MVP) | Simpler; asyncio easy to add later |
| Exa | Direct Python SDK | Cleaner than MCP, explicit control |
| Prompts | Load from existing .md files | Reuse existing skill/agent definitions |

---

## 4. Implementation Phases

### Phase A: Foundation (MVP)
**Goal:** Basic orchestrator that enforces checkpoints

- [x] **A1.** Create `strategic_orchestrator.py` skeleton ✓
  - [x] Data structures (WorkflowState, Source, AnalystOutput, CitationEntry)
  - [x] Step enum for state machine
  - [x] Configuration (paths, model selection)

- [x] **A2.** Implement prompt loading ✓
  - [x] `load_skill(name)` → read from `.claude/skills/`
  - [x] `load_agent(name)` → read from `.claude/agents/`
  - [x] `load_output_generation()` → read `_OUTPUT_GENERATION.md`

- [x] **A3.** Implement LLM wrapper ✓
  - [x] `llm_call(system, user, max_tokens)` → Anthropic SDK
  - [x] Error handling and retries
  - [ ] Token tracking (optional, deferred)

- [x] **A4.** Implement user interaction ✓
  - [x] `ask_user(prompt, options)` → numbered CLI choices
  - [x] `confirm(prompt)` → yes/no
  - [x] `get_input(prompt, default)` → free-form with default
  - [x] `display_section(title, content)` → formatted output

- [x] **A5.** Implement validation functions ✓
  - [x] `validate_analyst_output()` → parse YAML frontmatter
  - [x] `validate_citation_map()` → non-empty for factual content
  - [x] `validate_frontmatter()` → required fields check
  - [x] `REQUIRED_FRONTMATTER` constant defined

### Phase B: Core Workflow
**Goal:** Complete flow from problem to document

- [x] **B1.** Phase 1: Problem parsing ✓
  - [x] Language detection (Italian/English patterns)
  - [x] Synthesizer scoring (LLM + keyword fallback)
  - [x] Template recommendation
  - [x] SYNTHESIZERS config dict

- [x] **B2.** Phase 1.5: Fresh sources ✓
  - [x] Source need evaluation (HIGH/MEDIUM/LOW)
  - [x] User choice (A/B/C) with ask_user
  - [x] `research_briefing.yaml` loading into context_documents

- [x] **B3.** Phase 2: Clarification ✓
  - [x] Detect ambiguity (top scores within 0.2)
  - [x] Generate targeted questions via LLM
  - [x] Capture responses and rescore

- [x] **B4.** Phase 3: Proposal ✓
  - [x] Generate proposal text
  - [x] Present for approval (loop until approved)
  - [x] Handle modifications (synthesizer, template, analysts, web search)

- [x] **B5.** Phase 4: Execution ✓
  - [x] Sequential analyst execution
  - [x] Output collection and validation
  - [x] Failure threshold check (2+ = abort)

- [x] **B6.** Outline generation ✓
  - [x] Template-specific formatting
  - [x] Analyst integration
  - [x] **ENFORCED** user approval loop

- [x] **B7.** Citation enrichment ✓
  - [x] Map L0/L1 sources to outline points
  - [x] Identify gaps
  - [x] **ENFORCED** citation_map output

- [x] **B8.** Full text generation ✓
  - [x] Prose expansion
  - [x] Inline citation weaving
  - [x] Source marker removal
  - [x] **ENFORCED** frontmatter validation

### Phase C: Exa Integration ✅
**Goal:** L2 web search capability

- [x] **C1.** Exa SDK setup ✓
  - [x] API key configuration (EXA_API_KEY env var)
  - [x] Basic search wrapper (exa_search, exa_search_for_citation)
  - [x] Lazy client initialization

- [x] **C2.** L2 search integration ✓
  - [x] Max 3 searches per analysis (EXA_MAX_SEARCHES)
  - [x] Result parsing into citation_map
  - [x] Source level tagging (L2)
  - [x] Gap filling in _fill_citation_gaps_with_exa()

### Phase D: Enhancements
**Goal:** Production readiness

- [x] **D1.** Async analysts (asyncio) ✓
  - [x] Async Anthropic client (`get_async_client()`)
  - [x] Async LLM wrapper (`llm_call_async()`)
  - [x] Async analyst methods (`_run_analyst_async()`, `_execute_analysts_async()`)
  - [x] Sync wrapper (`_execute_analysts_parallel()`)
  - [x] Configuration flag (`parallel_analysts` param)
  - [x] CLI flag (`--seq` / `--sequential` for fallback)
- [x] **D2.** State persistence (save/resume) ✓
  - [x] Serialization helpers (`workflow_state_to_dict()`, `workflow_state_from_dict()`)
  - [x] Dataclass serializers for `Source`, `AnalystOutput`, `CitationEntry`
  - [x] `save_state(filepath)` → YAML with metadata
  - [x] `load_state(filepath)` → classmethod, restores full state
  - [x] `resume()` → continue workflow from `current_step`
  - [x] `_checkpoint()` → auto-save at key steps (7 checkpoints)
  - [x] CLI flags: `--save` (auto-checkpoint), `--resume FILE`
  - [x] Interrupt handling: save state on Ctrl+C
- [x] **D3.** Logging and debugging ✓
  - [x] Python `logging` module integration
  - [x] `setup_logging()` with level/file config
  - [x] `LogTimer` context manager for performance timing
  - [x] LLM call logging (model, tokens, timing)
  - [x] Exa search logging (query, results, timing)
  - [x] Phase timing with `LogTimer`
  - [x] CLI flags: `-v`/`--verbose`, `-q`/`--quiet`, `--log-file FILE`
- [x] **D4.** Error recovery ✓
  - [x] Custom exception hierarchy (`OrchestratorError`, `RetryableError`, `FatalError`, `AnalystError`)
  - [x] `RetryPolicy` dataclass with exponential backoff and jitter
  - [x] `is_retryable_error()` classifier for transient vs permanent errors
  - [x] `with_retry()` sync wrapper with configurable policy
  - [x] `with_retry_async()` async wrapper for parallel execution
  - [x] `RecoveryAction` enum for user choices (RETRY, SKIP, ABORT, RETRY_FAILED, CONTINUE_PARTIAL)
  - [x] `recovery_menu()` interactive recovery with context-aware options
  - [x] `_get_failed_analysts()` for identifying failed analysts
  - [x] `_retry_failed_analysts()` for selective re-execution
  - [x] `_handle_analyst_failures()` with graceful degradation support
  - [x] Config options: `graceful_degradation`, `auto_recovery`, `max_analyst_retries`
  - [x] CLI flags: `--no-graceful`, `--auto-recovery`, `--max-retries N`
  - [x] Automatic retry in `llm_call()` and `llm_call_async()` for transient API errors
- [ ] **D5.** Integration with Claude Code skills (optional)

---

## 5. File Structure

```
aa-kb/skills-definition/
├── PYTHON_ORCHESTRATOR_PLAN.md    # This file (North Star)
├── flow_weaknesses.md             # Original analysis
├── strategic_orchestrator.py      # Main implementation
├── tests/
│   ├── test_orchestrator.py
│   └── fixtures/
│       ├── sample_problem.txt
│       └── expected_outputs/
└── prompts/                       # Extracted prompt templates (optional)
    ├── phase1_parse.md
    ├── phase3_proposal.md
    └── citation_enrichment.md
```

**Dependencies on existing files:**
- `.claude/skills/*/SKILL.md` — Synthesizer prompts
- `.claude/agents/*/AGENT.md` — Analyst prompts
- `.claude/skills/_OUTPUT_GENERATION.md` — Output generation rules

---

## 6. Success Criteria

### MVP (Phase A+B) ✅
- [x] Orchestrator runs end-to-end without crashing
- [x] User approval checkpoint enforced (cannot skip)
- [x] citation_map validated before full text (cannot proceed if empty)
- [x] Analyst failures counted and abort triggered at threshold
- [x] Final document has valid frontmatter

### Full Implementation (Phase C+D)
- [x] L2 Exa searches integrated ✓
- [x] State can be saved and resumed ✓
- [x] All 4 high-risk weaknesses eliminated ✓
- [x] Error recovery with retry logic and graceful degradation ✓
- [ ] Test coverage for critical paths (optional)
- [ ] Integration with Claude Code skills (optional)

---

## 7. Estimated Effort

| Component | Lines | Time |
|-----------|-------|------|
| State dataclasses | ~80 | 15 min |
| Prompt loader | ~30 | 10 min |
| Anthropic API wrapper | ~50 | 15 min |
| Exa integration | ~40 | 15 min |
| Validation functions | ~60 | 20 min |
| User interaction (CLI) | ~50 | 15 min |
| Main orchestration flow | ~200 | 45 min |
| **Total** | **~500 lines** | **~2-3 hours** |

**MVP version:** ~300 lines, ~1.5 hours

---

## 8. Open Questions

1. **Model selection per phase?**
   - Use Sonnet for most phases, Opus for complex integration?
   - Or single model throughout?

2. **State persistence format?**
   - YAML file for human readability?
   - JSON for programmatic access?
   - SQLite for complex queries?

3. **Integration with Claude Code?**
   - Standalone CLI tool?
   - Or invoke via slash command that calls Python?

4. **Testing strategy?**
   - Mock LLM responses for unit tests?
   - Integration tests with real API?

---

## 9. Progress Log

| Date | Phase | Notes |
|------|-------|-------|
| 2026-01-25 | — | Plan created |
| 2026-01-25 | A1 | Skeleton + data structures complete |
| 2026-01-25 | A2-A3 | Prompt loading + LLM wrapper complete |
| 2026-01-25 | A4-A5 | User interaction + validation complete |
| 2026-01-25 | **A** | **Phase A complete** (~300 lines) |
| 2026-01-25 | B1-B2 | Problem parsing + fresh sources complete |
| 2026-01-25 | B3-B4 | Clarification + proposal complete |
| 2026-01-25 | B5 | Analyst execution with validation complete |
| 2026-01-25 | B6 | Outline generation with ENFORCED approval complete |
| 2026-01-25 | B7 | Citation enrichment with ENFORCED map complete |
| 2026-01-25 | B8 | Full text with frontmatter validation complete |
| 2026-01-25 | **B** | **Phase B complete** (~1850 lines) |
| 2026-01-25 | C1 | Exa SDK setup (lazy client, env var config) |
| 2026-01-25 | C2 | L2 search integration (gap filling, max 3 limit) |
| 2026-01-25 | **C** | **Phase C complete** (~2100 lines) |
| 2026-01-25 | D1 | Async analysts: `llm_call_async()`, `get_async_client()` |
| 2026-01-25 | D1 | Parallel execution: `_execute_analysts_async()` with `asyncio.gather()` |
| 2026-01-25 | D1 | Config flag `parallel_analysts`, CLI `--seq` fallback |
| 2026-01-25 | **D1** | **Phase D1 complete** (~2250 lines) |
| 2026-01-25 | D2 | Serialization helpers for all dataclasses |
| 2026-01-25 | D2 | `save_state()`, `load_state()`, `resume()` methods |
| 2026-01-25 | D2 | Auto-checkpoint at 7 workflow steps |
| 2026-01-25 | D2 | CLI flags `--save`, `--resume FILE` |
| 2026-01-25 | **D2** | **Phase D2 complete** (~2450 lines) |
| 2026-01-25 | D3 | `setup_logging()`, `LogTimer` context manager |
| 2026-01-25 | D3 | LLM/Exa call logging with timing and token tracking |
| 2026-01-25 | D3 | CLI flags `-v`/`--verbose`, `-q`/`--quiet`, `--log-file` |
| 2026-01-25 | **D3** | **Phase D3 complete** (~2600 lines) |
| 2026-01-25 | D4 | Error classification: `OrchestratorError`, `RetryableError`, `FatalError` |
| 2026-01-25 | D4 | `RetryPolicy` with exponential backoff and jitter |
| 2026-01-25 | D4 | `with_retry()` and `with_retry_async()` wrappers |
| 2026-01-25 | D4 | `recovery_menu()` interactive error recovery UI |
| 2026-01-25 | D4 | Partial analyst recovery: `_retry_failed_analysts()` |
| 2026-01-25 | D4 | Graceful degradation config options |
| 2026-01-25 | D4 | CLI flags `--no-graceful`, `--auto-recovery`, `--max-retries` |
| 2026-01-25 | **D4** | **Phase D4 complete** (~2900 lines) |
| | | |

---

## 10. Reference

- [flow_weaknesses.md](flow_weaknesses.md) — Original weakness analysis
- [Python skeleton code](flow_weaknesses.md#L197-L729) — Draft implementation
- `.claude/skills/` — Existing skill definitions
- `.claude/agents/` — Existing agent definitions
