# Strategic Analysis System — Quick Start

## Prerequisites

```bash
# Required
export ANTHROPIC_API_KEY="your-key"

# Optional (enables L2 web search)
export EXA_API_KEY="your-key"
```

Working directory: `skills-definition/`

---

## Quick Start

```bash
cd /mnt/DATA/26space/aa-kb/skills-definition

# Run the orchestrator
python strategic_orchestrator.py --run
```

Enter your analysis topic when prompted. The system handles everything else.

---

## Option A: Quick Analysis (No L0 Context)

```bash
python strategic_orchestrator.py --run
```

When prompted, enter your topic:
```
Enter analysis problem: European space launch autonomy challenges
```

The system will:
1. Detect language, recommend synthesizer
2. Assess fresh sources need
3. Propose configuration → you approve
4. Execute analysts in parallel
5. Generate outline → you approve
6. Enrich citations (L2 Exa if available)
7. Produce final document

---

## Option B: Deep Analysis (With L0 Context)

### Step 1: Prepare Research Briefing

Create a YAML file with your pre-researched sources:

```yaml
# context_documents/your_topic.yaml
research_briefing:
  topic: "Your Topic"
  date: "2026-01-25"
  researcher: "NotebookLM"

sources:
  - title: "Source Title"
    url: "https://example.com/source"
    type: official  # official | report | news | academic
    date: "2026-01-20"
    key_facts:
      - "Key fact 1"
      - "Key fact 2"
    quotes:
      - "Relevant direct quote"

key_findings:
  category_1:
    - "Finding 1"
  category_2:
    - "Finding 2"
```

### Step 2: Run Analysis

```bash
python strategic_orchestrator.py --run
```

The system will detect files in `context_documents/` and offer to load them.

---

## CLI Options

### Execution Modes

```bash
# Interactive mode (default, parallel analysts)
python strategic_orchestrator.py --run

# Sequential mode (one analyst at a time)
python strategic_orchestrator.py --run --seq

# Auto-save checkpoints
python strategic_orchestrator.py --run --save

# Resume from saved state
python strategic_orchestrator.py --resume output/workflow_state.yaml
```

### Error Recovery

```bash
# Abort on failures (no partial results)
python strategic_orchestrator.py --run --no-graceful

# Automatic recovery (no prompts)
python strategic_orchestrator.py --run --auto-recovery

# Set max analyst retries
python strategic_orchestrator.py --run --max-retries 3
```

### Logging

```bash
# Verbose (DEBUG level)
python strategic_orchestrator.py --run -v

# Quiet (WARNING+ only)
python strategic_orchestrator.py --run -q

# Log to file
python strategic_orchestrator.py --run --log-file output/analysis.log
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│  1. USER INPUT                                          │
│     python strategic_orchestrator.py --run              │
│     "European space launch autonomy challenges"         │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  2. PHASE 1: PROBLEM PARSING                            │
│     • Language detection (EN/IT)                        │
│     • Synthesizer scoring                               │
│     • Template recommendation                           │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  3. PHASE 1.5: FRESH SOURCES                            │
│     • Assess need (HIGH/MEDIUM/LOW)                     │
│     • Load research_briefing.yaml (if available)        │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  4. PHASE 3: PROPOSAL                                   │
│     • Synthesizer + Template + Analysts                 │
│     ► USER APPROVAL #1                                  │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  5. PHASE 4.1: ANALYSTS (parallel)                      │
│     • Execute methodology                               │
│     • Use L0 context (if provided)                      │
│     • Automatic retry on failures                       │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  6. PHASE 4.2: OUTLINE                                  │
│     • Template-based structure                          │
│     • Citation markers [Source: analyst-X]              │
│     ► USER APPROVAL #2                                  │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  7. PHASE 4.3: CITATION ENRICHMENT                      │
│     • Map L0/L1 sources to markers                      │
│     • L2 Exa search for gaps (max 3)                    │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  8. PHASE 4.4: FULL TEXT                                │
│     • Prose expansion                                   │
│     • Inline citation weaving                           │
│     • Frontmatter validation                            │
└────────────────────────┬────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────┐
│  9. OUTPUT                                              │
│     • Auto-saved to output/{slug}/index.md              │
│     • Outline at output/{slug}/outline.md               │
└─────────────────────────────────────────────────────────┘
```

---

## Output Location

Reports saved automatically to slug-based directories:
```
output/{slug}/
├── outline.md       # English outline
├── outline.it.md    # Italian outline
├── index.md         # English final document
└── index.it.md      # Italian final document

output/workflow_state.yaml   # State checkpoint (if --save)
```

Example: for "European space launch autonomy challenges":
```
output/european-space-launch-autonomy/index.md
```

---

## Available Synthesizers

| Synthesizer | Best For |
|-------------|----------|
| `strategic-geopolitical` | Power dynamics, alliances, strategic competition |
| `strategic-industrial` | Markets, supply chains, business ecosystems |
| `policy-regulatory` | Governance, regulation, institutional analysis |

---

## Available Templates

| Template | Use When |
|----------|----------|
| **Minto-Custom** | Comprehensive analysis, scalable (default) |
| **BLUF** | Executive briefing, time-critical |
| **Hypothesis-Driven** | Testing controversial thesis |
| **POR** | Decision among discrete options |

---

## Reference Documents

- `PYTHON_ORCHESTRATOR_PLAN.md` — Implementation details, progress log
- `SKILLS_ARCHITECTURE_BLUEPRINT.md` — Original system specification
- `flow_weaknesses.md` — Why Python orchestrator was needed
- `.claude/skills/` — Synthesizer prompts
- `.claude/agents/` — Analyst prompts
