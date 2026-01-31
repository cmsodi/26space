# CLAUDE.md — Strategic Research System

## Scope
Sistema di analisi strategica multi-agent per generare report approfonditi su tematiche space/geopolitical/policy.

## Project Structure
```
_research/
├── .claude/
│   ├── agents/          # 15 analyst methodologies (PESTLE, SWOT, etc.)
│   ├── skills/          # 8 synthesizers + orchestrator
│   └── recipes/         # Self-contained analytical pipelines
├── context_documents/   # Input: research briefings (YAML)
├── output/              # Output: generated reports
├── editorial_plan.yaml  # 100 article topics with status tracking
├── src/
│   ├── editorial.py     # Editorial workflow (--editorial mode)
│   ├── recipe.py        # RecipeRunner — direct article generation
│   ├── engines/         # Python step functions (Zwicky, etc.)
│   └── utils.py         # Shared utilities
├── run.py  # Main Python orchestrator
├── START_HERE.md        # Quick start guide
└── SKILLS_ARCHITECTURE_BLUEPRINT.md  # Full system spec
```

---

## Quick Start

```bash
# Set API keys
export ANTHROPIC_API_KEY="your-key"
export EXA_API_KEY="your-key"  # Optional, enables L2 web search

# New analysis (full orchestrator workflow)
python run.py --run

# Direct article generation via recipe
python run.py --recipe four-causes --topic "European Launch Autonomy"
python run.py --list-recipes

# Editorial mode (topic selection + NotebookLM research + analysis)
python run.py --editorial

# Reuse analyst reports (try different templates/synthesizers)
python run.py --from-folder output/{slug}_1

# Resume from checkpoint
python run.py --resume output/workflow_state.yaml
```

See `START_HERE.md` for detailed usage.

---

## Analytical Frameworks

### Agents (`.claude/agents/`)
| Agent | Methodology |
|-------|-------------|
| `pestle-analyst` | Political, Economic, Social, Tech, Legal, Environmental |
| `swot-analyst` | Strengths, Weaknesses, Opportunities, Threats |
| `stakeholder-mapper` | Actor mapping, power/interest grids |
| `scenario-planner` | Future scenarios, driving forces |
| `morphological-analyst` | Zwicky box, configuration space |
| `first-principles-analyst` | Assumption decomposition |
| `ecosystem-analyst` | Value chains, network effects |
| `geopolitical-theorist` | Power dynamics, strategic competition |
| `horizon-analyst` | Technology trajectories, S-curves |
| `power-analyst` | Influence networks, leverage points |
| `depth-analyst` | Causal Layered Analysis |
| `perspectives-analyst` | Multi-stakeholder viewpoints |
| `threat-analyst` | Risk assessment, vulnerabilities |
| `red-teamer` | Adversarial analysis, counterarguments |
| `triz-solver` | Inventive problem solving |

### Synthesizers (`.claude/skills/`)
| Synthesizer | Best For |
|-------------|----------|
| `geopolitical-synthesizer` | Power dynamics, alliances |
| `industrial-synthesizer` | Markets, supply chains |
| `policy-synthesizer` | Governance, regulation |
| `security-synthesizer` | Defense, threat assessment |
| `futures-synthesizer` | Long-term scenarios |
| `tech-innovation-synthesizer` | Technology trajectories |
| `space-strategy-synthesizer` | Space sector analysis |

---

## Workflow

1. **Input** — Topic or research briefing YAML from `context_documents/`
2. **Phase 1** — Language detection, synthesizer recommendation
3. **Phase 1.5** — Source assessment, L0 context loading (improved UX)
4. **Phase 3** — Configuration proposal (user approval)
5. **Phase 4.1** — Parallel analyst execution (saved individually)
6. **Phase 4.2** — Outline generation (user approval, template selection)
7. **Phase 4.3** — Citation enrichment (L2 Exa search)
8. **Phase 4.4** — Full text generation
9. **Output** — `output/{slug}/` (progressive numbering: `_1`, `_2` if exists)

### Resume Options
- **Full workflow**: `--run` (creates new numbered folder if slug exists)
- **From checkpoint**: `--resume state.yaml` (any phase)
- **From analyst reports**: `--from-folder output/{slug}/` (Phase 4.2+, allows template/synthesizer changes)

### Editorial Workflow (`--editorial`)

End-to-end flow from editorial plan to published analysis:

1. **Topic Selection** — Pick from `editorial_plan.yaml` (status=tbd) or create new topic
2. **Status Update** — Item set to `drafting`
3. **Context Folder** — `context_documents/{slug}/` created
4. **NotebookLM Research** (optional) — Deep web research via `notebooklm-py`:
   - Creates notebook, runs deep research query
   - Imports discovered sources, extracts structured YAML
   - Saves to `context_documents/{slug}/sources.yaml`
5. **Orchestrator Handoff** — Continues with normal analysis phases (sources pre-loaded)
6. **Finalization** — Status updated to `finalized` on completion

```bash
python run.py --editorial
```

**Editorial Plan Status Values**: `tbd` → `drafting` → `finalized`

**Custom Topics**: New topics get IDs starting from 10001 and are persisted in `editorial_plan.yaml`.

---

## Key Features

### 1. Progressive Folder Numbering
Output folders automatically get numbered suffixes if they already exist:
- First run: `output/lunar-pnt-analysis/`
- Second run: `output/lunar-pnt-analysis_1/`
- Third run: `output/lunar-pnt-analysis_2/`

Prevents overwriting previous analyses and preserves all work.

### 2. Analyst Report Reuse (`--from-folder`)
Expensive analyst LLM calls are saved individually. Reuse them to try:
- Different outline templates (BLUF → Hypothesis-Driven)
- Different synthesizers (geopolitical → industrial)
- Different configurations without re-running analysis

```bash
python run.py --from-folder output/my-analysis_1
# Review configuration → Change template → Continue from outline
```

### 3. Improved Context Document Loading
When adding L0 sources during proposal review:
- System lists all YAML files in `context_documents/`
- Enter just filename(s): `briefing.yaml` or multiple: `file1.yaml, file2.yaml`
- Press Enter to skip if you change your mind
- No more path confusion!

### 4. State Persistence
Auto-save checkpoints (with `--save`) or manual save on interrupt:
- Resume from exact point where workflow stopped
- Preserves all analyst outputs, configuration, and progress
- Enables long-running analyses with interruption safety

---

## Recipes (`.claude/recipes/`)

Recipes are self-contained analytical pipelines that fuse methodology, synthesis, and output format into a single reusable package. Each recipe defines ordered steps (LLM calls or Python functions) that execute sequentially.

| Recipe | Methodology | Type | Steps |
|--------|-------------|------|-------|
| `four-causes` | Four Causes (4Dimensions Ontology) | analysis | 1 LLM call |
| `nine-windows` | TRIZ 9-Windows (System Operator) | outline | 1 LLM call |
| `four-pillars` | Zwicky + TRIZ + Minto Pyramid | report | 8 steps (LLM + Python) |

### Recipe CLI

```bash
# List available recipes
python run.py --list-recipes

# Run a recipe (interactive topic prompt)
python run.py --recipe four-causes

# Run with topic specified
python run.py --recipe four-causes --topic "European Launch Autonomy"

# Run with context documents
python run.py --recipe nine-windows --topic "Lunar PNT" --context context_documents/briefing.yaml
```

### Adding a New Recipe

1. Create folder `.claude/recipes/{recipe-name}/`
2. Create `recipe.yaml` with metadata and steps
3. Add prompt files in `prompts/` subfolder
4. (Optional) Add reference documents in `references/`
5. (Optional) For Python steps: add function to `src/engines/`, decorate with `@register_engine`

No core code changes needed.

---

## Reference Documents

### User Guides
- **`doc/research_briefing_template.yaml`** — Complete YAML template with examples
- **`doc/anchor_text_guide.md`** — Guide for writing natural citation anchor text
- **`doc/README.md`** — Documentation index
- `START_HERE.md` — Quick start, CLI options

### System Documentation
- `SKILLS_ARCHITECTURE_BLUEPRINT.md` — Full system specification
- `tools.md` — Analytical methodologies catalog
- `outline_templates.md` — Document structure templates

### Legacy (historical)
- `legacy/PYTHON_ORCHESTRATOR_PLAN.md` — Implementation plan (completed)
- `legacy/flow_weaknesses.md` — Original weakness analysis (resolved)
- `legacy/tests/` — Phase D test suite (passed)
- `legacy/notebooklm/` — NotebookLM integration (disabled, see `RESTORE.md` to re-enable)

---

## Operating Instructions

- Use web search (Exa) for current data when analyzing recent events
- Challenge weak arguments, flag logical inconsistencies
- Maintain analytical rigor — no unsupported claims
- Python code: commented, incremental changes

## Context Management

After completing each major task or multi-step workflow, remind the user
to check context usage (`/context` or the pie chart). If the conversation
is long (>10 exchanges), suggest checking before starting new tasks.
When the user reports context is above 60%, stop working: report current
progress, list remaining tasks, and save any necessary state so work
can resume in a fresh conversation.
