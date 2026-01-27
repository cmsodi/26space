# CLAUDE.md — Strategic Research System

## Scope
Sistema di analisi strategica multi-agent per generare report approfonditi su tematiche space/geopolitical/policy.

## Project Structure
```
_research/
├── .claude/
│   ├── agents/          # 15 analyst methodologies (PESTLE, SWOT, etc.)
│   └── skills/          # 8 synthesizers + orchestrator
├── context_documents/   # Input: research briefings (YAML)
├── output/              # Output: generated reports
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

# Run orchestrator
python strategic_orchestrator.py --run
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

1. **Input** — Topic or research briefing YAML
2. **Phase 1** — Language detection, synthesizer recommendation
3. **Phase 1.5** — Source assessment, L0 context loading
4. **Phase 3** — Configuration proposal (user approval)
5. **Phase 4.1** — Parallel analyst execution
6. **Phase 4.2** — Outline generation (user approval)
7. **Phase 4.3** — Citation enrichment (L2 Exa search)
8. **Phase 4.4** — Full text generation
9. **Output** — `output/{slug}/index.md`

---

## Reference Documents

- `START_HERE.md` — Quick start, CLI options
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
