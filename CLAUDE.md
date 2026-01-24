# CLAUDE.md — 26space Multi-Site Project

## Project Structure
```
26space/
├── shared/              # Layouts/i18n comuni (priorità massima)
├── spacepolicies/       # spacepolicies.com
├── spacestrategies/     # spacestrategies.org
├── aa-kb/               # Knowledge base personale (leggere solo se richiesto)
└── .claude/docs/        # Reference tecnica tema Zen
```

## Sites & Content Differentiation
| spacestrategies.org | spacepolicies.com |
|---------------------|-------------------|
| Geopolitical risk, power dynamics | Regulatory frameworks, treaties |
| Industrial competition, value chains | Governance models, stakeholder mapping |
| Technology trajectories, defense | Policy cycles, institutional analysis |

---

## CRITICAL RULES

### 1. Taxonomies ALWAYS in English
**Non-negotiable.** Values must be English kebab-case in ALL posts (including Italian).

```yaml
# ✅ Correct (even in .it.md files)
frameworks:
  - space-policy
technologies:
  - transport-systems

# ❌ NEVER
frameworks:
  - politica-spaziale    # Breaks filtering
```

**Available taxonomies:** `frameworks`, `technologies`, `stakeholders`, `purposes`

### 2. UI Strings via i18n
```html
<!-- ❌ Never hardcode -->
<h1>Latest Articles</h1>

<!-- ✅ Always use -->
<h1>{{ i18n "latest_articles" }}</h1>
```

### 3. URL Structure
- English: root `/` (NO `/en/` prefix)
- Italian: `/it/` prefix
- Config: `defaultContentLanguageInSubdir: false`

### 4. Protected Files — DO NOT MODIFY
- `layouts/_default/baseof.html`
- `_vendor/*`
- `js/tagfilter.js`

See `.claude/docs/PROTECTED-FILES.md` for full list.

---

## Hugo Workflow

### New Post
```bash
hugo new content/article/my-post/index.md
# Italian translation: content/article/my-post/index.it.md
```

### Frontmatter Template
```yaml
---
title: "Post Title"
date: 2025-01-22
description: "..."
frameworks:
  - space-policy
technologies:
  - transport-systems
stakeholders:
  - governments
purposes:
  - knowledge-expansion
featured: false
---
```

### Local Dev
```bash
# Both sites
./start-sites.sh
# SpaceStrategies: http://localhost:1313/
# SpacePolicies: http://localhost:1314/
```

---

## Analytical Frameworks (use sparingly)
- **Macro/Geopolitics**: PESTLE, Causal Layered Analysis
- **Industry**: Porter's Five Forces, Value Chain, Ecosystem Mapping
- **Technology**: TRL, S-Curve, Horizon Scanning
- **Policy**: Regulatory Impact Assessment, Stakeholder Power Mapping
- **Foresight**: Scenario Planning, Backcasting
- **Problem Solving**: First Principles, MECE, Zwicky Box

---

## Operating Instructions
- Adapt tone to target audience specified per article
- Document revisions: **diff only**, no full rewrites
- Challenge weak arguments, flag logical flaws
- No unsolicited details
- Python/JS code: commented, incremental

---

## Skills
- `.claude/skills/` — Context-triggered skills
- `.claude/commands/` — Explicit slash commands

---



## Reference Docs

- `.claude/docs/multilingual-implementation-plan.md` — Full i18n architecture
- `.claude/docs/zen-theme-*.md` — Theme documentation
- `.claude/docs/PROTECTED-FILES.md` — Files to never modify
- `.claude/rules.md` — Extended reference & troubleshooting
