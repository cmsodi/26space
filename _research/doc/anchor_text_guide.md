# Anchor Text Writing Guide

## Quick Reference

### The Problem with Short Citations

**❌ BAD** - Just author and year:
```yaml
anchor_suggestion: "Boamah 2025"
```

This forces the LLM to write awkward sentences like:
> "The Artemis Accords operate as soft law instruments (Boamah 2025)."

**✅ GOOD** - Descriptive phrase:
```yaml
anchor_suggestion: "according to Boamah's critical analysis"
```

This enables natural prose:
> "The Artemis Accords, according to Boamah's critical analysis, operate as soft law instruments that influence international norm-making."

---

## Anchor Text Formula

```
[Action Verb] + [Source Description/Authority] + [Optional Context]
```

### Action Verbs
- according to
- as detailed in
- per
- as outlined by
- as demonstrated in
- following
- based on
- drawing from
- as argued in
- per specifications in

### Source Description
- Author name + credential/role
- Organization + document type
- Study/report descriptor

### Optional Context
- Year/date reference
- Subject area
- Methodology

---

## Examples by Source Type

### 1. Official Government Documents

**Format:** `as [action] in [organization]'s [date] [document type]`

```yaml
# White House Policy
anchor_suggestion: "as mandated in the White House's April 2024 policy directive"

# NASA Technical Document
anchor_suggestion: "according to NASA's 2023 communications architecture white paper"

# DOD Strategic Plan
anchor_suggestion: "as outlined in the Department of Transportation's December 2024 PNT strategic plan"
```

### 2. Academic/Research Papers

**Format:** `according to [author]'s [descriptor] [study/analysis]`

```yaml
# Single author
anchor_suggestion: "according to Kothapalli's engineering assessment"

# Multiple authors
anchor_suggestion: "per Israel et al.'s LunaNet architecture study"

# Institution-led research
anchor_suggestion: "as detailed in the MIT study on cislunar economics"
```

### 3. Standards & Specifications

**Format:** `per [standards body] [document type]`

```yaml
# Blue Books
anchor_suggestion: "per the CCSDS Blue Book standards"

# Green Books
anchor_suggestion: "as outlined in CCSDS informational reports"

# Technical specifications
anchor_suggestion: "following the IEEE 802.11 specifications"
```

### 4. News & Journalism

**Format:** `as [reported/announced] by [organization] in [timeframe]`

```yaml
# Press release
anchor_suggestion: "as announced by NASA in September 2024"

# News article
anchor_suggestion: "according to a Space.com analysis from November 2025"

# Expert commentary
anchor_suggestion: "as Cross argues in his September 2025 analysis"
```

### 5. Industry Reports

**Format:** `according to [organization]'s [descriptor] [report/vision/study]`

```yaml
# Commercial roadmap
anchor_suggestion: "according to the Space Settlement Progress industrial vision"

# Market analysis
anchor_suggestion: "per Morgan Stanley's 2025 space economy forecast"

# Technical proposal
anchor_suggestion: "as outlined in SpaceX's Starship lunar variant proposal"
```

### 6. Strategic/Geopolitical Analysis

**Format:** `as [author] [argues/demonstrates/examines] in [descriptor]`

```yaml
# Policy analysis
anchor_suggestion: "as Vermeylen argues in his analysis of orbital rivalry"

# Strategic assessment
anchor_suggestion: "according to the U.S.-China Economic and Security Review Commission's 2025 report"

# Expert opinion
anchor_suggestion: "as Di Pippo demonstrates in her diplomatic assessment"
```

### 7. Legal Analysis

**Format:** `as [author/organization] [demonstrates/argues] in [legal descriptor]`

```yaml
# Treaty analysis
anchor_suggestion: "as Santos demonstrates in his legal analysis"

# Regulatory framework
anchor_suggestion: "per the European Space Agency's regulatory compliance framework"

# Case study
anchor_suggestion: "following the precedent established in the Luxembourg space resources law"
```

---

## Testing Your Anchor Text

Ask yourself: **Can this phrase fit naturally mid-sentence?**

### Test Template:
```
"The [topic], [YOUR ANCHOR TEXT], [continues with substance]."
```

### Example Tests:

✅ **GOOD:**
> "The time standard, **as mandated in the White House's April 2024 policy directive**, must maintain traceability to UTC."

✅ **GOOD:**
> "LunaNet infrastructure, **according to Israel et al.'s architecture study**, provides delay-tolerant networking."

❌ **BAD:**
> "The time standard, **Gramling 2024**, must maintain traceability to UTC."

❌ **BAD:**
> "LunaNet infrastructure, **Israel 2020**, provides delay-tolerant networking."

---

## Advanced Techniques

### 1. Emphasize Authority
When the source's credibility is important:
```yaml
anchor_suggestion: "according to the authoritative CCSDS standards body"
anchor_suggestion: "as detailed in NASA's definitive architecture white paper"
```

### 2. Add Temporal Context
When recency matters:
```yaml
anchor_suggestion: "according to ESA's recently published strategic vision"
anchor_suggestion: "as outlined in the latest OSTP policy directive"
```

### 3. Specify Document Type
When the format matters:
```yaml
anchor_suggestion: "per the technical specifications outlined in the CCSDS Blue Book"
anchor_suggestion: "according to the peer-reviewed study by Melman et al."
```

### 4. Multiple Authors - Variations
```yaml
# Two authors
anchor_suggestion: "as Becker and Smith demonstrate"

# Three or more authors
anchor_suggestion: "according to Israel et al.'s study"

# Organization as author
anchor_suggestion: "per the Moon Village Association workshop findings"
```

---

## Common Mistakes to Avoid

### ❌ 1. Parenthetical Citations
```yaml
# Don't write:
anchor_suggestion: "(NASA 2024)"
anchor_suggestion: "[Santos, 2026]"
```

### ❌ 2. URLs or DOIs
```yaml
# Don't write:
anchor_suggestion: "https://nasa.gov/report"
anchor_suggestion: "doi:10.1234/example"
```

### ❌ 3. Generic Phrases Without Source
```yaml
# Don't write:
anchor_suggestion: "according to recent research"
anchor_suggestion: "studies have shown"
```

### ❌ 4. Overly Long Descriptions
```yaml
# Don't write:
anchor_suggestion: "according to the comprehensive analysis conducted by the International Lunar Research Station Working Group in their extensive 2025 technical assessment report"

# Instead:
anchor_suggestion: "according to the ILRS Working Group's 2025 assessment"
```

---

## Template Checklist

Before finalizing your research briefing YAML:

- [ ] Every source has an `anchor_suggestion` field
- [ ] Each anchor text includes source attribution (author/org)
- [ ] Phrases read naturally when inserted mid-sentence
- [ ] No bare citations (e.g., "Author 2024")
- [ ] Descriptive context provided where helpful
- [ ] Action verbs used appropriately
- [ ] No URLs or technical identifiers in anchor text

---

## See Also

- `doc/research_briefing_template.yaml` - Full YAML template with examples
- `START_HERE.md` - Quick start guide for the orchestrator
- `SKILLS_ARCHITECTURE_BLUEPRINT.md` - System specification including citation architecture
