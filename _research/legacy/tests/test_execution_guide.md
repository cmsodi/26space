# Test Execution Guide

## Overview

This guide explains how to execute the Phase D test suite for the L0/L1/L2 source cascade system.

## Test Matrix Summary

| Test | L0 Context | L1 Exa | Purpose |
|------|------------|--------|---------|
| T1 | ✓ | ✗ | Baseline L0-only coverage |
| T2 | ✗ | ✓ | Baseline L1-only capability |
| T3 | ✓ | ✓ | L0+L1 integration (reference) |
| T4 | ✓ | ✓ | Full pipeline end-to-end |

---

## Prerequisites

### Required Tools
- Claude Code with MCP Exa integration
- Access to skills-definition directory
- L0 source documents available

### L0 Context Sources
Ensure these are accessible for L0 tests:
1. ESA Space Transportation Strategy
2. EU Space Act Framework
3. ESA Ministerial Council 2025
4. EU Vision for Space Economy
5. McKinsey European Space Report

---

## Execution Commands

### T1: L0 Only

```
Invoke analyst with L0 context injection ONLY.
Disable all Exa/web search capabilities.

Prompt:
[TEST MODE: L0 ONLY]
Entity: "European Autonomous Access to Space"
Analyst: pestle-analyst

Use ONLY the following L0 sources:
[paste L0 source list]

DO NOT use Exa search.
Mark gaps as [GAP: description].
```

**Expected Duration**: 3-5 minutes
**Output**: `output/T1_L0_only_pestle.md`

---

### T2: L1 Only

```
Invoke analyst with Exa search ONLY.
No L0 context injection.

Prompt:
[TEST MODE: L1 ONLY]
Entity: "European Autonomous Access to Space"
Analyst: pestle-analyst

You have NO pre-injected sources.
Use Exa search (mcp__exa__web_search_exa) for ALL sources.
Document all queries and sources in frontmatter.
```

**Expected Duration**: 5-8 minutes (Exa latency)
**Output**: `output/T2_L1_only_pestle.md`

---

### T3: L0 + L1 Combined

```
Full L0 → L1 cascade.

Prompt:
[TEST MODE: L0+L1]
Entity: "European Autonomous Access to Space"
Analyst: pestle-analyst

L0 sources available:
[paste L0 source list]

Use L0 as primary.
Use Exa ONLY for gaps not covered by L0.
Track source provenance (L0 vs L1).
```

**Reference Output**: `output/TEST_L0L1_pestle_analyst.md` (already exists)

---

### T4: Full Pipeline

```
Complete orchestrator → agents → synthesizer flow.

Prompt:
[TEST MODE: FULL PIPELINE]

Research Brief:
- Topic: European Autonomous Access to Space
- Analysts: pestle, stakeholder, value-chain
- L0 sources: [list]
- Output: Synthesized report with citations

Execute:
1. Orchestrator distributes to agents
2. Agents analyze in parallel
3. Synthesizer generates outline
4. Synthesizer enriches citations
5. Synthesizer produces final text
```

**Expected Duration**: 10-15 minutes
**Output**: `output/T4_full_pipeline_report.md`

---

## Validation Procedures

### Post-Test Checklist

#### All Tests
- [ ] Output file created
- [ ] Frontmatter complete and valid YAML
- [ ] No broken markdown syntax
- [ ] Appropriate test_type documented

#### T1 Specific
- [ ] Only L0 URLs present
- [ ] [GAP:] markers for missing data
- [ ] No Exa sources in frontmatter

#### T2 Specific
- [ ] No L0 URLs present
- [ ] exa_sources populated in frontmatter
- [ ] exa_queries_executed documented
- [ ] Source diversity verified

#### T3 Specific
- [ ] Both L0 and L1 sources present
- [ ] L0 prioritized over L1 for same topic
- [ ] Source provenance tracked

#### T4 Specific
- [ ] All agent outputs collected
- [ ] Synthesizer stages completed
- [ ] Citation map generated
- [ ] Final narrative coherent

---

## Link Verification

Run after each test:

```bash
# Extract URLs from output
grep -oE '\[.*?\]\((https?://[^\)]+)\)' output_file.md | \
  sed 's/.*(\(.*\))/\1/' | \
  while read url; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    echo "$status $url"
  done
```

All links should return 200 or 301/302.

---

## Comparison Analysis

After running T1, T2, T3:

### Metrics Comparison Table

| Metric | T1 (L0) | T2 (L1) | T3 (L0+L1) |
|--------|---------|---------|------------|
| Total citations | | | |
| Official sources | | | |
| Report sources | | | |
| News sources | | | |
| Gaps documented | | | |
| Analysis depth | | | |

### Quality Assessment

1. **Coverage**: Which test covered most PESTLE dimensions adequately?
2. **Authority**: Which had highest proportion of tier-1 sources?
3. **Recency**: Which had most current data?
4. **Gaps**: Which had fewest unresolved gaps?

---

## Troubleshooting

### Exa Not Responding
- Check MCP server status
- Verify API credentials
- Fall back to L0-only mode

### L0 Sources Not Found
- Verify URLs still valid
- Check network connectivity
- Update source list if URLs changed

### Agent Timeout
- Increase timeout threshold
- Reduce entity scope
- Run sequentially instead of parallel

### Citation Resolution Failures
- Check if source domain accessible
- Verify markdown link syntax
- Document as limitation if persistent

---

## Results Storage

```
skills-definition/
├── tests/
│   ├── test_scenarios.yaml
│   ├── test_execution_guide.md
│   ├── T1_L0_only_template.md
│   ├── T2_L1_only_template.md
│   └── T4_full_pipeline_template.md
│
└── output/
    ├── T1_L0_only_pestle.md
    ├── T2_L1_only_pestle.md
    ├── TEST_L0L1_pestle_analyst.md  (T3 reference)
    └── T4_full_pipeline_report.md
```

---

## Next Steps After Testing

1. **Analyze Results**: Compare metrics across T1/T2/T3
2. **Identify Weaknesses**: Note where L0 or L1 alone fails
3. **Tune Configuration**: Adjust L0 source selection based on gaps
4. **Document Findings**: Update agent/synthesizer docs with learnings
5. **Production Readiness**: If all tests pass, proceed to live use
