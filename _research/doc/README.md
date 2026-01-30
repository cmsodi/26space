# Documentation

This folder contains guides and templates for using the Strategic Analysis Orchestrator.

## Quick Links

### For Creating Research Briefings

- **[research_briefing_template.yaml](research_briefing_template.yaml)** - Complete YAML template with examples
  - Shows proper formatting for all source types
  - Includes best practices for anchor text
  - Demonstrates effective takeaways and relevance statements

- **[anchor_text_guide.md](anchor_text_guide.md)** - Comprehensive guide to writing natural anchor text
  - Quick reference formulas
  - Examples by source type
  - Testing techniques
  - Common mistakes to avoid

### System Documentation

See the main project folder for:
- `START_HERE.md` - Quick start guide and CLI options
- `SKILLS_ARCHITECTURE_BLUEPRINT.md` - Full system specification
- `CLAUDE.md` - Project overview and workflow
- `tools.md` - Analytical methodologies catalog
- `outline_templates.md` - Document structure templates

## File Overview

| File | Purpose |
|------|---------|
| `research_briefing_template.yaml` | Template for creating L0 context documents with proper anchor text |
| `anchor_text_guide.md` | Guide for writing natural, prose-friendly citation anchors |
| `README.md` | This file - documentation index |

## Key Concepts

### What is a Research Briefing?

A research briefing is a YAML file placed in `context_documents/` that provides:
- Curated sources (L0 level) with URLs
- Key takeaways from each source
- Natural anchor text for citation embedding
- Relevance statements for analyst guidance

### Why Does Anchor Text Matter?

The orchestrator weaves citations naturally into prose. Good anchor text enables:

**❌ Awkward (short citation):**
> "The time standard must maintain UTC traceability (Gramling 2024)."

**✅ Natural (descriptive anchor):**
> "The time standard, as mandated in the White House's April 2024 policy directive, must maintain UTC traceability while operating independently in the lunar gravitational environment."

### Workflow

1. **Create briefing**: Use `research_briefing_template.yaml` as starting point
2. **Add sources**: Follow examples for your source types
3. **Write anchor text**: Use `anchor_text_guide.md` for best practices
4. **Place in context_documents/**: Save as `your-topic.yaml`
5. **Load during analysis**: Select "Add context documents" at proposal review

## Examples

### Minimal Source Entry
```yaml
- title: "Policy on Celestial Time Standardization"
  url: "https://example.com/policy.pdf"
  type: "official_document"
  date: "2024-04-02"
  takeaways:
    - "Key finding 1"
    - "Key finding 2"
  relevance: "Why this matters for the analysis"
  anchor_suggestion: "as mandated in the White House policy directive"
```

### With Italian Language
```yaml
research_briefing:
  language: "it"

sources:
  - title: "Artemis Accord – A Critical Analysis"
    # ... rest of fields ...
    takeaways:
      - "Gli Accordi Artemis operano come strumenti di soft law"
    anchor_suggestion: "secondo l'analisi critica di Boamah"
```

## Tips

1. **Be specific**: Include author names, organizations, dates in anchor text
2. **Test readability**: Read your anchor text in a sentence - does it flow?
3. **Avoid redundancy**: Don't repeat the full title in the anchor text
4. **Use action verbs**: "according to", "as detailed in", "per", etc.
5. **Match language**: If research_briefing.language is "it", write Italian anchor text

## Need Help?

- See real examples: Check `context_documents/test.yaml` (though it uses short citations)
- Read the guide: `anchor_text_guide.md` has formulas and examples
- Study the template: `research_briefing_template.yaml` shows all source types
- Check the workflow: `START_HERE.md` explains how to load context documents
