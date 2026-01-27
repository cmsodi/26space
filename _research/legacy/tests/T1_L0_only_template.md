# T1: L0 Only Test Template

## Test Configuration

```yaml
test_id: T1_L0_only
analyst: pestle-analyst
entity: "European Autonomous Access to Space"
configuration:
  L0_context_injection: enabled
  L1_exa_gap_fill: DISABLED
  L2_web_fallback: DISABLED
```

## Injected L0 Context

The following sources are provided as L0 context injection:

### Official Sources
1. **ESA Space Transportation Strategy**
   - URL: https://www.esa.int/Enabling_Support/Space_Transportation/Ensuring_autonomous_access_to_space_for_Europe
   - Content: Europe's strategic approach to autonomous access

2. **EU Space Act Framework**
   - URL: https://commission.europa.eu/news-and-media/news/eu-space-act-enhancing-market-access-and-space-safety-2025-06-25_en
   - Content: New regulatory framework for European space activities

3. **ESA Ministerial Council 2025**
   - URL: https://www.esa.int/About_Us/Ministerial_Council_2025/CM25_Strengthen_European_autonomy_and_resilience
   - Content: Budget allocations and strategic decisions

4. **EU Vision for Space Economy**
   - URL: https://defence-industry-space.ec.europa.eu/vision-european-space-economy_en
   - Content: Long-term policy direction

### Report Sources
5. **McKinsey: European Space Ecosystem**
   - URL: https://www.mckinsey.com/industries/aerospace-and-defense/our-insights/is-europe-still-on-the-launchpad-reshaping-its-space-ecosystem-to-lead
   - Content: Competitive assessment and recommendations

---

## Expected Analyst Behavior

### MUST DO:
- Use ONLY the 5 L0 sources listed above
- Cite sources with inline markdown links
- Document gaps where information not available in L0

### MUST NOT:
- Use Exa search
- Fabricate data not in sources
- Use external URLs not in L0 list

---

## Gap Documentation Format

When L0 sources insufficient, document as:

```markdown
[GAP: Current SpaceX launch market share data - not available in L0 sources]
```

---

## Expected Gaps (L0 Limitations)

Based on L0 sources, the following will be gaps:

1. **Quantitative market data**
   - SpaceX launch share percentage
   - European market value figures
   - Cost comparison metrics

2. **Current development status**
   - Themis demonstrator latest milestone
   - Micro-launcher startup progress

3. **Geopolitical context**
   - US-China competition dynamics
   - Recent policy developments (post-source dates)

---

## Validation Checklist

After T1 test execution, verify:

- [ ] All citations link to L0 sources only
- [ ] No Exa-sourced URLs present
- [ ] Minimum 5 citations from L0 sources
- [ ] Gaps clearly documented with [GAP:] markers
- [ ] Analysis coherent despite limited sources
- [ ] No fabricated data or statistics

---

## Execution Command

```
[TEST MODE: L0 ONLY]
Analyze "European Autonomous Access to Space" using PESTLE methodology.

CONSTRAINT: Use ONLY the L0 context sources provided above.
DO NOT use Exa search or any external sources.
Where information is unavailable, mark as [GAP: description].

Generate structured PESTLE analysis with inline citations.
```

---

## Sample Output Structure

```markdown
---
analyst: pestle-analyst
test_type: L0_only
sources_used:
  L0: 5
  L1: 0
  gaps_documented: X
---

# PESTLE Analysis: European Autonomous Access to Space

## Political Factors

As stated in the [ESA space transportation strategy](L0-URL), "Europe's
independent access to space has never been as crucial as today."

[GAP: Current political leadership statements on space autonomy - not in L0]

...
```
