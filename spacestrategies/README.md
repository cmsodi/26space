# Space Policies

A Hugo-based website for analysis and insights on space programs, governance, and industry dynamics.

## Features

- **Hugo Static Site Generator** with [Zen theme](https://github.com/frjo/hugo-theme-zen)
- **Custom Taxonomy System** with 4 filter groups:
  - Frameworks (space-law, international-treaties, space-policy, standards)
  - Technologies (transport-systems, spacecrafts, ground-systems, planetary-infrastructures)
  - Stakeholders (governments, space-industry, agencies-institutions, international-entities)
  - Purposes (knowledge-expansion, terrestrial-services, economic-development, space-exploration)
- **Interactive Tag Filter** with AND/OR logic powered by [List.js](https://listjs.com/)
- **Dark/Light Theme Toggle**

## Filter Logic

The tag filter on `/tags/` uses:
- **OR** within the same group (e.g., selecting "space-law" AND "standards" shows articles with either)
- **AND** between different groups (e.g., selecting a Framework AND a Technology shows only articles matching both)

## Quick Start

```bash
# Install Hugo (if not already installed)
# https://gohugo.io/installation/

# Clone the repository
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO

# Install theme module
hugo mod get

# Run development server
hugo server
```

Visit `http://localhost:1313`

## Project Structure

```
.
├── assets/
│   └── sass/_custom.scss    # Custom styles overriding Zen theme
├── content/
│   ├── article/             # Articles
│   └── report/              # Reports
├── layouts/
│   ├── tags/terms.html      # Tag filter page
│   └── ...                  # Other custom layouts
├── static/
│   └── js/
│       ├── tagfilter.js     # Filter logic (AND/OR)
│       └── theme-toggle.js  # Dark/light mode
└── hugo.yaml                # Site configuration
```

## Configuration

Taxonomies are defined in `hugo.yaml`:

```yaml
taxonomies:
  tag: "tags"
  stakeholders: "stakeholders"
  frameworks: "frameworks"
  technologies: "technologies"
  purposes: "purposes"
```

## Article Front Matter

```yaml
---
title: "Article Title"
date: 2025-01-08
frameworks:
  - space-policy
  - standards
technologies:
  - ground-systems
stakeholders:
  - space-industry
purposes:
  - economic-development
---
```

## License

MIT
