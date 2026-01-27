# T4: Full Pipeline Test Template

## Test Configuration

```yaml
test_id: T4_full_pipeline
test_type: end-to-end
configuration:
  L0_context_injection: enabled
  L1_exa_gap_fill: enabled
  L2_web_fallback: optional (fallback only)
```

## Pipeline Stages

```
┌─────────────────┐
│ Research Brief  │  ← Input YAML
└────────┬────────┘
         ▼
┌─────────────────┐
│  ORCHESTRATOR   │  ← Parse brief, select analysts, distribute
└────────┬────────┘
         ▼
┌─────────────────────────────────────────┐
│         PARALLEL AGENTS                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ PESTLE   │ │Stakeholder│ │Value-Chain│ │
│  │ Analyst  │ │ Analyst  │ │ Analyst  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │            │            │        │
│       └────────────┼────────────┘        │
└────────────────────┼────────────────────┘
                     ▼
┌─────────────────────────────────────────┐
│            SYNTHESIZER                   │
│  Step 1: Generate Outline + Markers     │
│  Step 1.5: Citation Enrichment          │
│  Step 2: Full Text with Links           │
└────────────────────┬────────────────────┘
                     ▼
┌─────────────────┐
│  Final Output   │  ← Markdown report
└─────────────────┘
```

---

## Test Input: Research Brief

```yaml
# test_research_brief.yaml
research_brief:
  topic: "European Autonomous Access to Space"
  scope: "Strategic assessment of Europe's space launch capability"

  entity_focus:
    primary: "European space transportation ecosystem"
    secondary:
      - "Ariane 6 program"
      - "Themis reusable demonstrator"
      - "European Launcher Challenge"

  analysts_required:
    - pestle-analyst
    - stakeholder-analyst
    - value-chain-analyst

  output_requirements:
    format: markdown
    length: 3000-5000 words
    citation_style: inline_markdown

  L0_context:
    - source: "ESA Space Transportation"
      url: "https://www.esa.int/Enabling_Support/Space_Transportation"
    - source: "EU Space Act"
      url: "https://commission.europa.eu/..."
    - source: "ESA CM25"
      url: "https://www.esa.int/About_Us/Ministerial_Council_2025/..."
```

---

## Stage 1: Orchestrator Validation

### Input Processing
- [ ] Research brief parsed correctly
- [ ] Entity focus extracted
- [ ] Analysts selected per brief requirements

### Agent Distribution
- [ ] Each agent receives appropriate entity slice
- [ ] L0 context distributed to all agents
- [ ] Parallel execution configured

### Expected Orchestrator Output
```yaml
orchestrator_output:
  agents_dispatched:
    - agent: pestle-analyst
      entity: "European space transportation ecosystem"
      dimensions: [political, economic, social, technological, legal, environmental]
    - agent: stakeholder-analyst
      entity: "European space actors"
      focus: [ESA, national agencies, industry primes, startups]
    - agent: value-chain-analyst
      entity: "European launcher value chain"
      focus: [manufacturing, launch services, ground segment]

  L0_sources_injected: 5
  execution_mode: parallel
```

---

## Stage 2: Agent Execution Validation

### Per-Agent Checks

#### PESTLE Analyst
- [ ] All 6 dimensions covered
- [ ] L0 sources cited where applicable
- [ ] L1 Exa queries for gaps
- [ ] Structured output format

#### Stakeholder Analyst
- [ ] Key actors identified
- [ ] Power/interest mapping
- [ ] Relationship dynamics
- [ ] L0/L1 source integration

#### Value-Chain Analyst
- [ ] Upstream/downstream mapping
- [ ] Bottleneck identification
- [ ] Competitive positioning
- [ ] L0/L1 source integration

### Agent Output Schema
```yaml
agent_output:
  agent_id: pestle-analyst
  entity: "..."
  analysis:
    sections:
      - dimension: political
        content: "..."
        citations:
          - text: "quote or reference"
            source: L0|L1
            url: "..."

  sources_used:
    L0: 3
    L1: 4

  gaps_remaining:
    - "description of unfilled gap"
```

---

## Stage 3: Synthesizer Validation

### Step 1: Outline Generation
- [ ] Outline structure logical
- [ ] [CITE:] markers placed correctly
- [ ] [DATA:] markers for statistics
- [ ] [REF:] markers for background

### Step 1.5: Citation Enrichment
- [ ] All markers resolved
- [ ] L0 sources matched first
- [ ] L1 Exa fills remaining gaps
- [ ] Citation map generated

### Step 2: Full Text
- [ ] Links woven naturally
- [ ] No raw URLs in prose
- [ ] Citation density adequate
- [ ] Smooth narrative flow

### Synthesizer Output Validation
```yaml
synthesizer_output:
  outline_markers_count: 15
  citations_resolved: 14
  citations_unresolved: 1  # Documented as limitation

  source_breakdown:
    L0_official: 4
    L0_report: 2
    L1_exa: 6
    L2_fallback: 0

  word_count: 4200
  sections: 8
```

---

## Final Output Validation

### Frontmatter Completeness
```yaml
---
title: "Strategic Assessment: European Autonomous Access to Space"
date: 2026-01-25
analysts:
  - pestle-analyst
  - stakeholder-analyst
  - value-chain-analyst
methodology: "Multi-framework synthesis"
entity: "European space transportation ecosystem"
status: complete
confidence: high

sources_summary:
  total: 12
  L0_official: 4
  L0_report: 2
  L1_exa: 6
  L2_fallback: 0

exa_sources:
  - title: "..."
    url: "..."
    used_for: "..."
---
```

### Content Quality
- [ ] Executive summary present
- [ ] All analyst perspectives integrated
- [ ] Citations properly formatted
- [ ] No broken links
- [ ] Coherent narrative arc
- [ ] Strategic implications clear

### Link Verification
```bash
# Extract and verify all URLs
grep -oP 'https?://[^\)]+' output.md | while read url; do
  curl -s -o /dev/null -w "%{http_code}" "$url"
done
```

---

## Execution Sequence

```
1. Load research brief YAML
2. Initialize orchestrator with brief
3. Orchestrator parses and distributes to agents
4. Agents execute in parallel:
   a. Load L0 context
   b. Analyze assigned entity
   c. Query L1 Exa for gaps
   d. Return structured output
5. Synthesizer collects agent outputs
6. Synthesizer Step 1: Generate outline
7. Synthesizer Step 1.5: Enrich citations
8. Synthesizer Step 2: Generate full text
9. Validate final output
10. Write to output directory
```

---

## Success Criteria

| Criterion | Threshold | Critical |
|-----------|-----------|----------|
| All agents complete | 100% | ✓ |
| Citations resolved | ≥90% | ✓ |
| L0 source utilization | ≥50% of available | |
| Link validity | 100% | ✓ |
| Word count | 3000-5000 | |
| Frontmatter complete | 100% | ✓ |
| Narrative coherence | Subjective review | |

---

## Error Handling

### Agent Failure
- Retry once with extended timeout
- If persistent, proceed with available agents
- Document missing perspective in output

### Citation Resolution Failure
- Document as `[Source unavailable for: topic]`
- Do not fabricate citations
- Flag in synthesizer output

### L1 Exa Unavailable
- Fall back to L0-only mode
- Document coverage limitations
- Set confidence: medium

---

## Test Artifacts

After T4 execution, collect:

```
tests/
├── T4_full_pipeline_template.md  (this file)
├── T4_execution_log.md           (runtime log)
└── T4_results/
    ├── orchestrator_output.yaml
    ├── agent_pestle_output.md
    ├── agent_stakeholder_output.md
    ├── agent_valuechain_output.md
    ├── synthesizer_outline.md
    ├── synthesizer_citations.yaml
    └── final_output.md
```
