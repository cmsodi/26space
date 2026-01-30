# Context Documents (L0 Sources)

Drop your research briefings here. The orchestrator will automatically load all `.yaml` and `.md` files from this folder.

## Accepted Formats

| Extension | Format | Notes |
|-----------|--------|-------|
| `.yaml` | YAML briefing | Preferred. Structured for automatic parsing. |
| `.md` | Markdown | Supported. Less structured but flexible. |

## Naming Convention

Any name works. Suggested patterns:

```
[topic]_briefing.yaml
[topic]_research.md
[date]_[topic].yaml
```

Examples:
```
india_eo_satellites.yaml
european_launchers_research.md
2026-01-25_space_policy.yaml
```

## Multiple Documents

Multiple files are supported and merged automatically:

```
context_documents/
├── regulatory_framework.yaml    ← Theme A
├── market_analysis.yaml         ← Theme B
└── technology_status.md         ← Theme C
```

All sources from all files are concatenated and routed to relevant analysts.

## Priority Rules

When same topic covered by multiple files:
1. `.yaml` takes precedence over `.md`
2. More recent `date:` field wins
3. `type: official` > `report` > `news`

## Workflow

```
1. Run NotebookLM/Perplexity with prompt template
2. Save output here as .yaml
3. Start orchestrator
4. Orchestrator auto-loads all files from this folder
5. Sources injected as L0 context
```
