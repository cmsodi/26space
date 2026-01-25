# T2: L1 Only Test Template

## Test Configuration

```yaml
test_id: T2_L1_only
analyst: pestle-analyst
entity: "European Autonomous Access to Space"
configuration:
  L0_context_injection: DISABLED
  L1_exa_gap_fill: enabled
  L2_web_fallback: DISABLED
```

## Purpose

Test analyst capability using ONLY Exa search (no pre-injected L0 context).
Simulates scenario where curated sources unavailable or analyst starting fresh.

---

## Required Exa Queries

Analyst must construct effective Exa queries for:

### Political Dimension
```
Query: "European space autonomy policy 2025 ESA EU Commission"
Expected: Official strategy documents, policy announcements
```

### Economic Dimension
```
Query: "European launcher market share SpaceX Ariane competition 2024 2025"
Expected: Market analysis, competitive data
```

### Social Dimension
```
Query: "European space workforce skills talent aerospace"
Expected: Industry reports, HR analyses
```

### Technological Dimension
```
Query: "Ariane 6 Themis reusable rocket development status 2025"
Expected: Technical updates, milestone announcements
```

### Legal Dimension
```
Query: "EU Space Act regulation framework 2025"
Expected: Regulatory documents, legal analyses
```

### Environmental Dimension
```
Query: "European space sustainability debris mitigation green propulsion"
Expected: Environmental policies, Clean Space initiative
```

---

## Source Quality Requirements

### Preferred Domains (Tier 1-2)
- esa.int
- ec.europa.eu
- mckinsey.com
- brookings.edu
- csis.org
- spacenews.com

### Acceptable Domains (Tier 3)
- europeanspaceflight.com
- spacenews.com
- nasaspaceflight.com

### Avoid
- Personal blogs
- Reddit/social media
- Unverified aggregators
- Sources older than 2023

---

## Expected Analyst Behavior

### MUST DO:
- Use Exa search for ALL source discovery
- Execute minimum 4-6 targeted queries
- Document all Exa sources in frontmatter
- Verify source recency (2024-2026 preferred)
- Cross-reference multiple sources for key claims

### MUST NOT:
- Use any pre-injected L0 context
- Rely on single source for critical data
- Accept low-quality or outdated sources

---

## Frontmatter Schema

```yaml
---
analyst: pestle-analyst
methodology: PESTLE Analysis
entity: "European Autonomous Access to Space"
timestamp: 2026-01-25T00:00:00Z
test_type: L1_only
exa_queries_executed:
  - query: "European space autonomy policy 2025"
    results_used: 2
  - query: "Ariane 6 Themis development status"
    results_used: 1
exa_sources:
  - title: "Source Title"
    url: "https://..."
    used_for: "What this source provided"
    authority_tier: 1  # 1=official, 2=report, 3=news
---
```

---

## Validation Checklist

After T2 test execution, verify:

- [ ] No L0 context sources used
- [ ] Minimum 4 Exa sources retrieved
- [ ] Source diversity (not all from same domain)
- [ ] Authority tier documented for each source
- [ ] Recency check passed (sources 2024-2026)
- [ ] All citations have working URLs
- [ ] Analysis quality comparable to L0+L1 baseline

---

## Execution Command

```
[TEST MODE: L1 ONLY]
Analyze "European Autonomous Access to Space" using PESTLE methodology.

CONSTRAINT: You have NO pre-injected L0 context.
Use Exa search (mcp__exa__web_search_exa) to discover ALL sources.
Execute targeted queries for each PESTLE dimension.

Document all Exa queries and sources in frontmatter.
Generate structured PESTLE analysis with inline citations.
```

---

## Comparison Metrics

After execution, compare T2 results against T3 (L0+L1) reference:

| Metric | T2 (L1 only) | T3 (L0+L1) | Delta |
|--------|--------------|------------|-------|
| Total citations | ? | 12 | ? |
| Official sources | ? | 4 | ? |
| Report sources | ? | 3 | ? |
| News sources | ? | 5 | ? |
| Analysis depth | ? | High | ? |
| Source recency | ? | 2024-2026 | ? |

---

## Quality Degradation Expectations

Without L0 curated context, expect:
- Slightly lower official source coverage
- More reliance on news/analysis sources
- Potential for less authoritative citations
- Higher variance in source quality

This test establishes baseline for Exa-only capability.
