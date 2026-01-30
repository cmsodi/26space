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
├── src/
│   ├── recipe.py        # RecipeRunner — direct article generation
│   ├── engines/         # Python step functions (Zwicky, etc.)
│   └── utils.py         # Shared utilities
├── strategic_orchestrator.py  # Main Python orchestrator
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
python strategic_orchestrator.py --run

# Direct article generation via recipe
python strategic_orchestrator.py --recipe four-causes --topic "European Launch Autonomy"
python strategic_orchestrator.py --list-recipes

# Reuse analyst reports (try different templates/synthesizers)
python strategic_orchestrator.py --from-folder output/{slug}_1

# Resume from checkpoint
python strategic_orchestrator.py --resume output/workflow_state.yaml
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
python strategic_orchestrator.py --from-folder output/my-analysis_1
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
python strategic_orchestrator.py --list-recipes

# Run a recipe (interactive topic prompt)
python strategic_orchestrator.py --recipe four-causes

# Run with topic specified
python strategic_orchestrator.py --recipe four-causes --topic "European Launch Autonomy"

# Run with context documents
python strategic_orchestrator.py --recipe nine-windows --topic "Lunar PNT" --context context_documents/briefing.yaml
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

---

## Operating Instructions

- Use web search (Exa) for current data when analyzing recent events
- Challenge weak arguments, flag logical inconsistencies
- Maintain analytical rigor — no unsupported claims
- Python code: commented, incremental changes

## NotebookLM — Procedura blindata (solo CLI `nlm`)

> **DIVIETO ASSOLUTO**: NON usare MAI i tool MCP `notebooklm-mcp` (notebook_create,
> notebook_query, source_add, studio_create, ecc.). Il server MCP dà SEMPRE
> "Authentication expired" indipendentemente da refresh_auth, save_auth_tokens,
> reload VSCode, o qualsiasi altro tentativo. NON perdere tempo a riprovare.
> Usare ESCLUSIVAMENTE il CLI `nlm` via Bash.

### Avvio sessione — Eseguire SEMPRE all'inizio

Quando l'utente chiede operazioni NotebookLM, eseguire questi step **nell'ordine esatto**.
Prerequisito: Chrome deve essere aperto con una sessione Google attiva su notebooklm.google.com.

```bash
# STEP 1 — Estrarre cookies freschi da Chrome
#   Richiede Chrome aperto. Connette via Chrome DevTools Protocol.
notebooklm-mcp-auth
```

Attendere output "SUCCESS". Se fallisce, l'utente deve aprire Chrome su notebooklm.google.com e riprovare.

```bash
# STEP 2 — Convertire auth.json in formato cookie-string per nlm CLI
python3 -c "
import json
with open('/home/cms/.notebooklm-mcp-cli/auth.json') as f:
    d = json.load(f)
cookie_str = '; '.join(f'{k}={v}' for k,v in d['cookies'].items())
with open('/tmp/nlm_cookie_str.txt', 'w') as f:
    f.write(cookie_str)
print(f'OK: {len(cookie_str)} chars')
"
```

```bash
# STEP 3 — Importare nel profilo nlm CLI
nlm login --manual -f /tmp/nlm_cookie_str.txt
```

Attendere output "Successfully authenticated!".

```bash
# STEP 4 — Verificare che funziona
nlm notebook list
```

Se restituisce la lista dei notebook in JSON, l'autenticazione è attiva.
Se dà errore, ripetere da STEP 1 (i cookies potrebbero essere scaduti).

### Comandi `nlm` CLI — Riferimento completo

```bash
# ── Notebook ──
nlm notebook list                                    # Lista tutti i notebook
nlm notebook create "Titolo Notebook"                # Crea notebook
nlm notebook get NOTEBOOK_ID                         # Dettagli notebook

# ── Fonti ──
nlm source list NOTEBOOK_ID                          # Lista fonti nel notebook
nlm source add NOTEBOOK_ID --url "https://..."       # Aggiungi fonte da URL
nlm source add NOTEBOOK_ID --text "contenuto" --title "Titolo"  # Fonte testo

# ── Ricerca web ──
nlm research start "query" -n NOTEBOOK_ID -m fast    # ~30s, ~10 fonti
nlm research start "query" -n NOTEBOOK_ID -m deep    # ~5min, ~40 fonti
nlm research status NOTEBOOK_ID                      # Polling stato ricerca
nlm research import NOTEBOOK_ID TASK_ID              # Importa fonti trovate

# ── Query (la funzione principale) ──
nlm query notebook NOTEBOOK_ID "domanda"             # Query sulle fonti
nlm query notebook NOTEBOOK_ID "domanda" -c CONV_ID  # Follow-up conversazione

# ── Studio (generazione artefatti) ──
nlm studio create NOTEBOOK_ID --type audio           # Podcast
nlm studio create NOTEBOOK_ID --type report          # Report
nlm studio status NOTEBOOK_ID                        # Stato generazione
```

### Note operative per Claude

1. **Ad ogni nuova sessione**: eseguire STEP 1–4 prima di qualsiasi comando `nlm`.
   I cookies Google scadono frequentemente (~ore). Non dare per scontato che
   l'auth della sessione precedente sia ancora valida.

2. **Timeout query**: le query `nlm query notebook` possono richiedere fino a
   120 secondi. Usare `--timeout 300000` nel tool Bash.

3. **Output JSON**: i comandi `nlm` restituiscono JSON. Per processarli in pipe
   usare `python3 -c "import json,sys; ..."` (NON `jq`, potrebbe non essere installato).

4. **Conversation ID**: `nlm query` restituisce un `Conversation ID` alla fine
   dell'output. Salvarlo per follow-up con `-c CONV_ID`.

5. **Ricerca web**: dopo `research start`, fare polling con `research status`
   fino a `status: completed`, poi `research import` per aggiungere le fonti.

### Path dei file (riferimento interno)

| Cosa | Path |
|------|------|
| `notebooklm-mcp-auth` output | `~/.notebooklm-mcp-cli/auth.json` |
| `nlm` CLI profilo default | `~/.notebooklm-mcp-cli/profiles/default/` |
| Server MCP (IGNORARE) | `~/.notebooklm-mcp/auth.json` |

---

## Context Management

Stop working and notify the user when context usage exceeds 60%.
Report current progress, list remaining tasks, and save any necessary
state so work can resume in a fresh conversation.
