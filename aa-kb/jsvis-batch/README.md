# jsvis-batch: Batch Generation of jsvis Knowledge Maps

Automated generation of interactive knowledge maps for the 4dimensions© framework.

## Overview

This toolkit generates 320+ jsvis knowledge maps organized by the 4dimensions© taxonomy:
- **4 categories**: Technologies, Frameworks, Stakeholders, Purposes
- **16 tags**: 4 tags per category
- **20 topics per tag**: Generic, searchable topics
- **Total**: 320 interactive maps

## Directory Structure

```
/aa-kb/jsvis-batch/
├── config.yaml                 # Main configuration
├── topics.yaml                 # Generated topics (Phase 1 output)
├── topic_generator.py          # Phase 1: Generate topics
├── outline_generator.py        # Phase 2: Generate outlines → HUGO files
├── prompts/
│   ├── topic_generator_system.yaml
│   ├── topic_generator_user.yaml
│   ├── outline_system.yaml
│   └── outline_user.yaml
└── README.md

/spacestrategies/content/maps/
├── technologies/
│   ├── transport-systems/
│   │   ├── expendable-launch-vehicle.md
│   │   ├── reusable-rocket.md
│   │   └── ...
│   ├── spacecrafts/
│   └── ...
├── frameworks/
├── stakeholders/
└── purposes/
```

## Prerequisites

```bash
pip install anthropic pyyaml
export ANTHROPIC_API_KEY="your-api-key"
```

## Usage

### Phase 1: Generate Topics

First run (creates topics.yaml):
```bash
python topic_generator.py
```

Incremental run (adds non-duplicate topics):
```bash
python topic_generator.py
```

Options:
```bash
# Use specific model
python topic_generator.py --model claude-opus-4-0-20250115

# Generate for specific category/tag only
python topic_generator.py --category technologies --tag spacecrafts

# Override topics count
python topic_generator.py --count 30

# Dry run (show prompts without API calls)
python topic_generator.py --dry-run
```

### Phase 2: Generate Outlines

After topics.yaml exists:
```bash
python outline_generator.py
```

Options:
```bash
# Use specific model
python outline_generator.py --model claude-opus-4-0-20250115

# Generate for specific category/tag/topic
python outline_generator.py --category technologies
python outline_generator.py --category technologies --tag spacecrafts
python outline_generator.py --topic "telecommunications satellite"

# Skip existing files (incremental generation)
python outline_generator.py --skip-existing

# Dry run
python outline_generator.py --dry-run
```

## Configuration

Edit `config.yaml` to customize:

```yaml
paths:
  hugo_content: "/spacestrategies/content/maps"
  topics_yaml: "./topics.yaml"
  prompts_dir: "./prompts"

models:
  topic_generator:
    default: "claude-sonnet-4-20250514"
  outline_generator:
    default: "claude-sonnet-4-20250514"

generation:
  topics_per_tag: 20
  batch_delay: 1.0

hugo:
  shortcode_name: "jsvis-map1"
  background_color: "white"
  background_image: ""
```

## Workflow

### Initial Batch (320 maps)

```bash
cd /aa-kb/jsvis-batch

# Phase 1: Generate all topics (~16 API calls)
python topic_generator.py

# Review topics.yaml if needed
# Edit manually to remove/add topics

# Phase 2: Generate all outlines (~320 API calls)
python outline_generator.py

# Build HUGO site
cd /spacestrategies
hugo --minify

# Deploy
rsync -avz public/ server:/path/
```

### Incremental Addition

```bash
cd /aa-kb/jsvis-batch

# Add more topics to existing tags
python topic_generator.py --count 10

# Generate only new outlines
python outline_generator.py --skip-existing
```

## Cost Estimation

With Claude Sonnet:
- Phase 1: ~16 calls × ~$0.003 = ~$0.05
- Phase 2: ~320 calls × ~$0.01 = ~$3.20
- **Total: ~$3.25 for 320 maps**

With Claude Opus (higher quality):
- Phase 1: ~16 calls × ~$0.015 = ~$0.24
- Phase 2: ~320 calls × ~$0.05 = ~$16.00
- **Total: ~$16.24 for 320 maps**

## Troubleshooting

### Rate Limits
Increase `batch_delay` in config.yaml if hitting rate limits.

### Empty or Malformed Outlines
Check `prompts/outline_user.yaml` examples match your expected format.

### Missing Topics
Run topic_generator.py again - it merges without duplicating.

## Customization

### Adding New Categories/Tags
Edit `taxonomy` section in config.yaml, then re-run both phases.

### Changing Outline Structure
Edit `prompts/outline_user.yaml` to modify:
- Number of hierarchy levels
- Label length constraints
- Search query format
