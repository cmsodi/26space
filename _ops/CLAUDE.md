# CLAUDE.md — Hugo Site Operations

## Scope
Gestione e manutenzione dei siti Hugo: **spacepolicies.com** e **spacestrategies.org**

## Project Structure
```
26space/
├── shared/              # Layouts/i18n comuni (priorità massima)
├── spacepolicies/       # spacepolicies.com
├── spacestrategies/     # spacestrategies.org
└── _ops/                # Questa cartella (operazioni Hugo)
    └── .claude/
        ├── commands/    # Slash commands (new-article, en2it, etc.)
        ├── docs/        # Documentazione tema Zen
        └── rules.md     # Reference estesa
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
# Correct (even in .it.md files)
frameworks:
  - space-policy
technologies:
  - transport-systems

# NEVER
frameworks:
  - politica-spaziale    # Breaks filtering
```

**Available taxonomies:** `frameworks`, `technologies`, `stakeholders`, `purposes`

### 2. UI Strings via i18n
```html
<!-- Never hardcode -->
<h1>Latest Articles</h1>

<!-- Always use -->
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
cd ../spacepolicies  # o ../spacestrategies
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
cd ..
./start-sites.sh
# SpaceStrategies: http://localhost:1313/
# SpacePolicies: http://localhost:1314/
```

---

## Slash Commands
- `/new-article` — Crea nuovo articolo con frontmatter corretto
- `/en2it` — Traduci articolo da inglese a italiano
- `/it2en` — Traduci articolo da italiano a inglese
- `/image-prompt` — Genera prompt per immagini articolo
- `/publish-check` — Checklist pre-pubblicazione

---

## Reference Docs
- `.claude/docs/multilingual-implementation-plan.md` — Architettura i18n
- `.claude/docs/zen-theme-*.md` — Documentazione tema
- `.claude/docs/PROTECTED-FILES.md` — File da non modificare
- `.claude/rules.md` — Reference estesa e troubleshooting

---

## Operating Instructions
- Adapt tone to target audience specified per article
- Document revisions: **diff only**, no full rewrites
- Challenge weak arguments, flag logical flaws
- No unsolicited details
