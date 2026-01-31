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
python run.py --run
```

Enter your analysis topic when prompted. The system handles everything else.

---

## Option A: Quick Analysis (No L0 Context)

```bash
python run.py --run
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

Create a YAML file with your pre-researched sources. **See [doc/research_briefing_template.yaml](doc/research_briefing_template.yaml) for a complete template with examples.**

**Quick example:**
```yaml
# context_documents/your_topic.yaml
research_briefing:
  topic: "Your Topic"
  date: "2026-01-29"
  researcher: "NotebookLM"
  language: "en"

sources:
  - title: "Policy on Celestial Time Standardization"
    url: "https://example.com/policy.pdf"
    type: "official_document"
    date: "2024-04-02"
    takeaways:
      - "Key technical finding"
      - "Policy implication"
    relevance: "Establishes regulatory framework for the domain"
    anchor_suggestion: "as mandated in the White House's April 2024 policy directive"
```

**IMPORTANT**: Use natural anchor text, not just citations. See [doc/anchor_text_guide.md](doc/anchor_text_guide.md) for best practices.

### Step 2: Run Analysis

```bash
python run.py --run
```

At the proposal review stage, select **"Add context documents"** and then:
- Choose option 1: "Load from YAML file"
- System lists all YAML files in `context_documents/`
- Enter filename(s): `your_topic.yaml` (or multiple: `file1.yaml, file2.yaml`)
- Press Enter to skip if you change your mind

---

## CLI Options

### Execution Modes

```bash
# Interactive mode (default, parallel analysts)
python run.py --run

# Sequential mode (one analyst at a time)
python run.py --run --seq

# Auto-save checkpoints
python run.py --run --save

# Resume from saved state
python run.py --resume output/workflow_state.yaml

# Reuse analyst reports from existing folder
python run.py --from-folder output/my-analysis_1
```

### Error Recovery

```bash
# Abort on failures (no partial results)
python run.py --run --no-graceful

# Automatic recovery (no prompts)
python run.py --run --auto-recovery

# Set max analyst retries
python run.py --run --max-retries 3
```

### Logging

```bash
# Verbose (DEBUG level)
python run.py --run -v

# Quiet (WARNING+ only)
python run.py --run -q

# Log to file
python run.py --run --log-file output/analysis.log
```

---

## Workflow Summary

```
┌─────────────────────────────────────────────────────────┐
│  1. USER INPUT                                          │
│     python run.py --run              │
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

Reports saved automatically to slug-based directories with **progressive numbering**:
```
output/{slug}/
├── pestle-analyst.md         # Individual analyst reports
├── stakeholder-mapper.md
├── outline.md                # Structured outline
├── index.md                  # Final document
└── workflow_state.yaml       # State checkpoint (if --save)
```

**Progressive Numbering**: If the folder already exists, a number suffix is automatically added:
```
First run:   output/european-space-launch-autonomy/
Second run:  output/european-space-launch-autonomy_1/
Third run:   output/european-space-launch-autonomy_2/
```

This prevents overwriting previous analyses and keeps all runs organized.

---

## Reusing Analyst Reports

**Use Case**: Expensive analyst analyses completed, want to try different outline templates or synthesizers without re-running analysts.

### Load from Folder

```bash
python run.py --from-folder output/lunar-analysis_1
```

The system will:
1. Load all analyst reports (`*.md` files) from the folder
2. Extract metadata from existing `outline.md` or `index.md` (if present)
3. Show current configuration and allow modifications:
   - Change synthesizer
   - Change template
   - Keep or modify other settings
4. Continue from outline generation with your new configuration

### Example Workflow

```bash
# Original analysis with BLUF template
python run.py --run
# Problem: "Lunar PNT standardization"
# Template: BLUF
# Output: output/lunar-pnt-standardization/

# Try Hypothesis-Driven template with same analysts
python run.py --from-folder output/lunar-pnt-standardization
# Select: Change template → Hypothesis-Driven
# Output: Same folder, regenerated outline and final document

# Or run fresh analysis (gets numbered folder)
python run.py --run
# Same problem creates: output/lunar-pnt-standardization_1/
```

**Benefits**:
- Saves API costs (no re-running expensive analyst LLM calls)
- Experiment with different narrative structures
- Iterate on report format without losing analytical depth

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

### User Guides
- **`doc/research_briefing_template.yaml`** — Complete YAML template with examples
- **`doc/anchor_text_guide.md`** — Guide for writing natural citation anchor text
- **`doc/README.md`** — Documentation index and quick reference

### System Documentation
- `CLAUDE.md` — Project overview, quick start, key features
- `SKILLS_ARCHITECTURE_BLUEPRINT.md` — Full system specification
- `tools.md` — Analytical methodologies catalog
- `outline_templates.md` — Document structure templates

### Legacy/Advanced
- `legacy/PYTHON_ORCHESTRATOR_PLAN.md` — Implementation plan (completed)
- `legacy/flow_weaknesses.md` — Original weakness analysis (resolved)
- `.claude/skills/` — Synthesizer prompts
- `.claude/agents/` — Analyst prompts
