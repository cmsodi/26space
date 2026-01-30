# Recipe System — Implementation Plan

## Context

The strategic orchestrator currently supports a multi-phase workflow (`--run`) that separates concerns into Analysts (methodology), Synthesizers (domain integration), and Templates (output structure). This plan adds a **direct article generation mode** via **Recipes** — self-contained analytical pipelines that fuse methodology, synthesis, and output format into a single entity.

### What is a Recipe?

A recipe combines:
- **Analytical methodology** (what the current system splits across analysts)
- **Synthesis approach** (what synthesizers do)
- **Output template** (what outline templates define)

into one self-contained, reusable package. Each recipe defines its own steps, prompts, and output format.

### Reference Examples (in `qualcosa/` folder)

| Example | Complexity | Steps | Python? | Key Pattern |
|---------|-----------|-------|---------|-------------|
| `four-causes` | Simple | 1 LLM call | No | system.yml + user.yml → markdown |
| `nine-windows` | Simple | 1 LLM call | No | system.yml + user.yml → JSON |
| `four-pillars` | Complex | 8 steps | Yes (Zwicky engine) | Multi-step pipeline with Python + LLM |

---

## Architecture Overview

```
CLI: python strategic_orchestrator.py --recipe four-causes [--topic "..."] [--context briefing.yaml]
                    │
                    ▼
         ┌──────────────────┐
         │  Entry Point     │  strategic_orchestrator.py
         │  --recipe flag   │
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │  RecipeRunner     │  src/recipe.py (NEW)
         │  - discover()     │
         │  - load()         │
         │  - run(topic)     │
         └────────┬─────────┘
                  │
          ┌───────┴───────┐
          │               │
          ▼               ▼
    ┌───────────┐  ┌────────────┐
    │ llm_call  │  │ Python fn  │
    │ (existing)│  │ (engines)  │
    └───────────┘  └────────────┘
```

### Key Design Decisions

1. **Separate class** (`RecipeRunner`), NOT added to `StrategicOrchestrator` — keeps existing orchestrator untouched
2. **Shared utilities** extracted from orchestrator into `src/utils.py` — both classes use them
3. **Recipe definitions** stored in `.claude/recipes/` — follows existing `.claude/agents/` and `.claude/skills/` pattern
4. **Step-based execution** — each recipe defines ordered steps (LLM calls or Python functions)
5. **Context chaining** — multi-step recipes pass outputs between steps via `inject_context`
6. **Optional context documents** — recipes can receive L0 sources via CLI flag

---

## File Structure

### New Files

```
_research/
├── .claude/
│   └── recipes/                          # NEW: Recipe definitions
│       ├── four-causes/
│       │   ├── recipe.yaml               # Manifest: steps, metadata
│       │   └── prompts/
│       │       ├── system.yml            # Copied from qualcosa/four-causes/
│       │       └── user.yml              # Copied from qualcosa/four-causes/
│       ├── nine-windows/
│       │   ├── recipe.yaml
│       │   └── prompts/
│       │       ├── system.yml            # Copied from qualcosa/nine-windows/
│       │       └── user.yml              # Copied from qualcosa/nine-windows/
│       └── four-pillars/
│           ├── recipe.yaml
│           ├── prompts/                  # 8 step prompt files (future task)
│           │   ├── step1_matrix.yml
│           │   ├── step2_features.yml
│           │   ├── ...
│           │   └── step8_report.yml
│           └── references/
│               ├── 4dimensions_ontology.md
│               ├── triz_principles.md
│               └── minto_templates.md
│
├── src/
│   ├── utils.py                          # NEW: Shared utilities
│   ├── recipe.py                         # NEW: RecipeRunner + models
│   └── engines/                          # NEW: Python step functions
│       ├── __init__.py
│       └── zwicky.py                     # Adapted from qualcosa/four-pillars/scripts/
```

### Modified Files

```
├── src/
│   ├── __init__.py                       # Add recipe exports
│   ├── config.py                         # Add RECIPES_PATH constant
│   └── orchestrator.py                   # Import utilities from src/utils.py
│                                         # (replace internal methods with shared functions)
│
├── strategic_orchestrator.py             # Add --recipe, --list-recipes, --topic flags
└── CLAUDE.md                             # Document recipe system
```

---

## Recipe Definition Format (`recipe.yaml`)

### Simple Recipe (four-causes)

```yaml
name: four-causes
description: "Exhaustive analysis using Aristotelean 4-Causes framework"
version: "1.0"
methodology: "Four Causes (4Dimensions Ontology)"
output_type: analysis          # analysis | outline | report
tags: [space, strategy, brainstorming]

steps:
  - id: analysis
    type: llm_call
    system_prompt: prompts/system.yml
    user_prompt: prompts/user.yml
    max_tokens: 8000
    temperature: 0.7

# Optional reference documents (loaded into system context for all LLM steps)
references: []
```

### Simple Recipe (nine-windows)

```yaml
name: nine-windows
description: "Article outline using TRIZ 9-Windows system operator"
version: "1.0"
methodology: "TRIZ 9-Windows (System Operator)"
output_type: outline
tags: [space, triz, outlining]

steps:
  - id: outline
    type: llm_call
    system_prompt: prompts/system.yml
    user_prompt: prompts/user.yml
    max_tokens: 8000
    temperature: 0.7
    # Optional: parse output as JSON for validation
    output_format: json

references: []
```

### Complex Recipe (four-pillars)

```yaml
name: four-pillars
description: "Morphological analysis with Zwicky Box, TRIZ, and Minto Pyramid"
version: "1.0"
methodology: "Zwicky Morphological Analysis + TRIZ + Minto Pyramid"
output_type: report
tags: [space, strategy, scenarios, executive]

steps:
  - id: matrix
    type: llm_call
    system_prompt: prompts/step1_matrix.yml
    user_prompt: prompts/step1_matrix.yml  # Can be same file with system/user sections
    model: complex                         # Only step needing Opus — heavy matrix generation
    max_tokens: 8000

  - id: features
    type: llm_call
    system_prompt: prompts/step2_features.yml
    user_prompt: prompts/step2_features.yml
    inject_context: [matrix]   # Inject output of 'matrix' step
    max_tokens: 4000

  - id: scenarios_yaml
    type: llm_call
    system_prompt: prompts/step3_yaml.yml
    user_prompt: prompts/step3_yaml.yml
    inject_context: [features]
    max_tokens: 2000
    output_format: yaml        # Extract YAML from response

  - id: zwicky_engine
    type: python
    function: zwicky_generate   # Registered function name
    input_from: scenarios_yaml  # Feed previous step's output
    args:
      top: 3
      format: md

  - id: triz
    type: llm_call
    system_prompt: prompts/step5_triz.yml
    user_prompt: prompts/step5_triz.yml
    inject_context: [matrix, zwicky_engine]
    max_tokens: 6000

  - id: merge
    type: llm_call
    system_prompt: prompts/step6_merge.yml
    user_prompt: prompts/step6_merge.yml
    inject_context: [triz, zwicky_engine]
    max_tokens: 4000

  - id: outline
    type: llm_call
    system_prompt: prompts/step7_outline.yml
    user_prompt: prompts/step7_outline.yml
    inject_context: [merge]
    max_tokens: 4000

  - id: report
    type: llm_call
    system_prompt: prompts/step8_report.yml
    user_prompt: prompts/step8_report.yml
    inject_context: [outline, matrix]
    model: complex                         # Final report benefits from Opus
    max_tokens: 12000

references:
  - references/4dimensions_ontology.md
  - references/triz_principles.md
  - references/minto_templates.md
```

### recipe.yaml Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Recipe identifier (must match folder name) |
| `description` | string | yes | Human-readable description |
| `version` | string | yes | Semver version |
| `methodology` | string | yes | Analytical framework used (e.g., "Four Causes", "TRIZ 9-Windows") |
| `output_type` | string | yes | What it produces: `analysis`, `outline`, or `report` |
| `tags` | list[str] | no | Searchable tags for categorization |
| `steps` | list | yes | Ordered list of execution steps |
| `references` | list | no | Paths to reference documents (relative to recipe folder) |

**Note**: There is no recipe-level `model` field. All LLM steps use the system default model (`MODEL_DEFAULT` from `src/config.py`). Only steps that genuinely require a more capable model (e.g., final report generation) specify a per-step `model: complex` override.

### Step Specification

| Field | Type | Required | For | Description |
|-------|------|----------|-----|-------------|
| `id` | string | yes | all | Unique step identifier |
| `type` | string | yes | all | `llm_call` or `python` |
| `system_prompt` | string | yes | llm_call | Path to system prompt file (relative to recipe folder) |
| `user_prompt` | string | yes | llm_call | Path to user prompt file (relative to recipe folder) |
| `model` | string | no | llm_call | Override: `complex` for steps needing Opus (default: system default) |
| `max_tokens` | int | no | llm_call | Max tokens (default: 4000) |
| `temperature` | float | no | llm_call | Temperature (default: 0.7) |
| `inject_context` | list[str] | no | llm_call | Step IDs whose outputs to inject into the prompt |
| `output_format` | string | no | llm_call | Expected output format: `text`, `json`, `yaml` (default: `text`) |
| `function` | string | yes | python | Registered function name |
| `input_from` | string | no | python | Step ID to use as input |
| `args` | dict | no | python | Additional arguments for the function |

---

## Prompt File Format

Recipe prompts are YAML files. Two approaches depending on complexity:

### Single-step prompt files (four-causes, nine-windows)

System and user prompts are separate files. The YAML content is loaded and composed into a prompt string.

**System prompt** (`prompts/system.yml`):
```yaml
role: "Expert in the space sector..."
attitude: "Maintain professionalism..."
approach: "Approach this analysis..."
mission: "to create a strategic document..."
```

**User prompt** (`prompts/user.yml`):
```yaml
task: |
  Analyze "{title}" through the Four Causes framework...
Output_Format: |
  Provide a structured analysis that...
Output_Standard: |
  ```markdown
  # Strategic Analysis: [Subject Name]
  ...
  ```
```

### Prompt loading logic

1. Read YAML file
2. If it contains a single string value at root → use as-is
3. If it contains multiple keys → concatenate all values into a single text block, separated by double newlines
4. Replace template variables: `{title}` → topic, `{language}` → detected language

### Template Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `{title}` | User input (topic) | The analysis topic/problem |
| `{language}` | Auto-detected | `en` or `it` |
| `{date}` | System | Today's date ISO format |
| `{context_documents}` | Optional CLI flag | Formatted L0 source list |

---

## Python Implementation

### 1. `src/utils.py` (NEW)

Extract shared utilities from `StrategicOrchestrator`:

```python
"""Shared utility functions for orchestrator and recipe runner."""

import re
from pathlib import Path


def detect_language(text: str) -> str:
    """Simple language detection based on common patterns."""
    italian_indicators = [
        "analizza", "valuta", "strategia", "l'", "è", "perché",
        "quali", "come", "dello", "della", "degli", "delle",
        "europeo", "italiano", "spaziale"
    ]
    text_lower = text.lower()
    italian_count = sum(1 for ind in italian_indicators if ind in text_lower)
    return "it" if italian_count >= 2 else "en"


def generate_slug(text: str) -> str:
    """Generate kebab-case slug from text."""
    text = text[:60].lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text


def generate_unique_slug(text: str, output_base: Path = Path("output")) -> str:
    """Generate unique slug with progressive numbering if folder exists."""
    base_slug = generate_slug(text)
    output_dir = output_base / base_slug

    if not output_dir.exists():
        return base_slug

    counter = 1
    while True:
        numbered_slug = f"{base_slug}_{counter}"
        if not (output_base / numbered_slug).exists():
            return numbered_slug
        counter += 1
        if counter > 1000:
            raise RuntimeError(f"Too many existing folders for slug: {base_slug}")


def get_document_filename(language: str) -> str:
    """Get final document filename based on language."""
    return "index.it.md" if language == "it" else "index.md"
```

### 2. `src/recipe.py` (NEW)

Core recipe system implementation.

```python
"""
Recipe system — self-contained analytical pipelines.

A recipe fuses methodology, synthesis, and output format into one entity.
Each recipe defines ordered steps (LLM calls or Python functions) that
execute sequentially, with outputs chained between steps.
"""

import re
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional, Any

import yaml

from .config import RECIPES_PATH, MODEL_DEFAULT, MODEL_COMPLEX
from .llm import llm_call
from .logging_setup import logger, LogTimer
from .ui import get_input, print_section_header, confirm
from .utils import detect_language, generate_unique_slug, get_document_filename


# ============== DATA MODELS ==============

@dataclass
class RecipeStep:
    """Single step in a recipe pipeline."""
    id: str
    type: str  # "llm_call" or "python"

    # LLM step fields
    system_prompt: str = ""       # Path relative to recipe folder
    user_prompt: str = ""         # Path relative to recipe folder
    model: str = ""               # Override: "complex" for Opus steps, empty = system default
    max_tokens: int = 4000
    temperature: float = 0.7
    inject_context: list[str] = field(default_factory=list)
    output_format: str = "text"   # text, json, yaml

    # Python step fields
    function: str = ""            # Registered function name
    input_from: str = ""          # Step ID to use as input
    args: dict = field(default_factory=dict)


@dataclass
class RecipeDefinition:
    """Parsed recipe.yaml contents."""
    name: str
    description: str
    version: str
    methodology: str                  # Analytical framework (e.g., "Four Causes")
    output_type: str                  # analysis | outline | report
    tags: list[str] = field(default_factory=list)
    steps: list[RecipeStep] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    folder: Path = field(default_factory=Path)  # Absolute path to recipe folder


# ============== RECIPE DISCOVERY & LOADING ==============

def discover_recipes() -> list[str]:
    """Scan .claude/recipes/ and return list of available recipe names."""
    ...

def load_recipe(name: str) -> RecipeDefinition:
    """Load and validate recipe.yaml from .claude/recipes/{name}/."""
    ...

def _parse_step(step_dict: dict) -> RecipeStep:
    """Parse a step definition from recipe.yaml."""
    ...

def _load_prompt_file(recipe_folder: Path, prompt_path: str) -> str:
    """
    Load a YAML prompt file and compose it into a single prompt string.

    Handles:
    - Single root string → use as-is
    - Multiple YAML keys → concatenate values with double newlines
    - Template variables are NOT replaced here (done at execution time)
    """
    ...

def _load_references(recipe_folder: Path, ref_paths: list[str]) -> str:
    """Load and concatenate all reference documents into a single context string."""
    ...


# ============== PYTHON FUNCTION REGISTRY ==============

# Registry of Python functions available to recipe steps.
# Key: function name (as used in recipe.yaml)
# Value: callable(input_text: str, **args) -> str
_PYTHON_FUNCTIONS: dict[str, callable] = {}


def register_engine(name: str):
    """Decorator to register a Python function for use in recipe steps."""
    def decorator(func):
        _PYTHON_FUNCTIONS[name] = func
        return func
    return decorator


def _run_python_step(step: RecipeStep, input_text: str) -> str:
    """Execute a registered Python function."""
    func = _PYTHON_FUNCTIONS.get(step.function)
    if func is None:
        raise ValueError(f"Unknown python function: {step.function}. "
                         f"Available: {list(_PYTHON_FUNCTIONS.keys())}")
    return func(input_text, **step.args)


# ============== RECIPE EXECUTION ==============

class RecipeRunner:
    """
    Executes recipes — self-contained analytical pipelines.

    Usage:
        runner = RecipeRunner(recipe_name="four-causes")
        result = runner.run(topic="European Launch Autonomy")
        # Result is saved to output/{slug}/index.md
    """

    def __init__(
        self,
        recipe_name: str,
        verbose: bool = False,
        context_yaml: Optional[str] = None,  # Path to context_documents YAML
    ):
        self.recipe = load_recipe(recipe_name)
        self.verbose = verbose
        self.context_yaml = context_yaml

        # Runtime state
        self.topic: str = ""
        self.language: str = "en"
        self.slug: str = ""
        self.step_outputs: dict[str, str] = {}   # step_id → output text
        self.context_documents: list = []         # Loaded L0 sources
        self.references_text: str = ""            # Loaded reference docs

    def run(self, topic: str) -> str:
        """
        Execute the full recipe pipeline.

        Args:
            topic: The analysis topic/problem

        Returns:
            Final document text
        """
        self.topic = topic
        self.language = detect_language(topic)
        self.slug = generate_unique_slug(topic)

        # Load references (once, for all LLM steps)
        self.references_text = _load_references(
            self.recipe.folder, self.recipe.references
        )

        # Load context documents if provided
        if self.context_yaml:
            self._load_context_documents()

        # Print header
        self._vprint(f"Recipe: {self.recipe.name}")
        self._vprint(f"Methodology: {self.recipe.methodology}")
        self._vprint(f"Output type: {self.recipe.output_type}")
        self._vprint(f"Topic: {self.topic}")
        self._vprint(f"Language: {self.language}")
        self._vprint(f"Steps: {len(self.recipe.steps)}")

        # Execute steps sequentially
        for i, step in enumerate(self.recipe.steps, 1):
            self._vprint(f"\n  Step {i}/{len(self.recipe.steps)}: {step.id}")

            with LogTimer(f"Recipe step: {step.id}"):
                if step.type == "llm_call":
                    output = self._execute_llm_step(step)
                elif step.type == "python":
                    input_text = self.step_outputs.get(step.input_from, "")
                    output = _run_python_step(step, input_text)
                else:
                    raise ValueError(f"Unknown step type: {step.type}")

                self.step_outputs[step.id] = output
                self._vprint(f"    Done ({len(output)} chars)")

        # The last step's output is the final document
        final_step_id = self.recipe.steps[-1].id
        final_document = self.step_outputs[final_step_id]

        # Add frontmatter if not present
        if not final_document.strip().startswith("---"):
            final_document = self._generate_frontmatter() + "\n\n" + final_document

        # Save output
        doc_path = self._save_document(final_document)
        self._vprint(f"\n  Saved to: {doc_path}")

        return final_document

    def _execute_llm_step(self, step: RecipeStep) -> str:
        """Execute a single LLM step."""
        # Load and compose prompts
        system_text = _load_prompt_file(self.recipe.folder, step.system_prompt)
        user_text = _load_prompt_file(self.recipe.folder, step.user_prompt)

        # Inject reference documents into system prompt
        if self.references_text:
            system_text += "\n\n## Reference Documents\n\n" + self.references_text

        # Inject context documents (L0 sources)
        context_docs_section = self._format_context_documents()

        # Inject outputs from previous steps
        context_section = ""
        if step.inject_context:
            context_section = "\n\n## Previous Analysis Outputs\n"
            for ctx_id in step.inject_context:
                ctx_output = self.step_outputs.get(ctx_id, "")
                if ctx_output:
                    context_section += f"\n### Output from '{ctx_id}':\n\n{ctx_output}\n"

        # Replace template variables in user prompt
        user_text = self._substitute_variables(user_text)
        user_text += context_docs_section + context_section

        # Select model (system default unless step specifies override)
        model = self._resolve_model(step.model)

        # Make LLM call
        response = llm_call(
            system=system_text,
            user=user_text,
            max_tokens=step.max_tokens,
            model=model,
            temperature=step.temperature,
        )

        # Optional output format extraction
        if step.output_format == "yaml":
            response = _extract_fenced_block(response, "yaml")
        elif step.output_format == "json":
            response = _extract_fenced_block(response, "json")

        return response

    def _substitute_variables(self, text: str) -> str:
        """Replace template variables in prompt text."""
        replacements = {
            "{title}": self.topic,
            "{language}": self.language,
            "{date}": date.today().isoformat(),
        }
        for var, val in replacements.items():
            text = text.replace(var, val)
        return text

    def _resolve_model(self, model_key: str) -> str:
        """Map optional model override to actual model ID.

        Only used when a step explicitly sets model: complex.
        Empty/missing model_key → system default (MODEL_DEFAULT).
        """
        if not model_key:
            return MODEL_DEFAULT
        if model_key == "complex":
            return MODEL_COMPLEX
        return MODEL_DEFAULT

    def _load_context_documents(self):
        """Load L0 context documents from YAML file."""
        ...  # Reuse logic from orchestrator's YAML loading

    def _format_context_documents(self) -> str:
        """Format loaded context documents as prompt section."""
        if not self.context_documents:
            return ""
        ...  # Return formatted markdown section

    def _generate_frontmatter(self) -> str:
        """Generate YAML frontmatter for recipe output."""
        frontmatter = {
            "title": self.topic[:100],
            "description": self.topic[:200],
            "slug": self.slug,
            "date": date.today().isoformat(),
            "version": "1.0",
            "recipe": self.recipe.name,
            "methodology": self.recipe.methodology,
            "output_type": self.recipe.output_type,
            "recipe_version": self.recipe.version,
            "status": "final",
            "language": self.language,
        }
        yaml_text = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)
        return f"---\n{yaml_text}---"

    def _save_document(self, document: str) -> Path:
        """Save final document to output/{slug}/index.md."""
        output_dir = Path("output") / self.slug
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = get_document_filename(self.language)
        filepath = output_dir / filename
        filepath.write_text(document, encoding="utf-8")
        return filepath

    def _vprint(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)


# ============== HELPERS ==============

def _extract_fenced_block(text: str, lang: str) -> str:
    """Extract content from a fenced code block (```yaml ... ``` or ```json ... ```)."""
    pattern = rf"```{lang}\s*\n(.*?)\n\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: return full text if no fenced block found
    return text
```

### 3. `src/engines/__init__.py` (NEW)

```python
"""Python engines for recipe steps."""

from .zwicky import zwicky_generate
```

### 4. `src/engines/zwicky.py` (NEW)

Adapted from `qualcosa/four-pillars/scripts/zwicky_engine.py` — same logic, exposed as a registered function:

```python
"""Zwicky Box Engine — callable from recipe steps."""

from ..recipe import register_engine

# Import the core logic functions from the existing script:
# parse_yaml_simple, is_consistent, generate_scenarios, format_markdown, format_json

@register_engine("zwicky_generate")
def zwicky_generate(yaml_input: str, top: int = 3, format: str = "md") -> str:
    """
    Generate morphological analysis scenarios from YAML configuration string.

    Args:
        yaml_input: YAML string with dimensions, variants, weights, constraints
        top: Number of top scenarios to detail (default: 3)
        format: Output format 'md' or 'json' (default: 'md')

    Returns:
        Formatted scenario analysis (markdown or JSON string)
    """
    config = parse_yaml_simple(yaml_input)
    scenarios = generate_scenarios(config)

    if format == "json":
        return format_json(config, scenarios, top)
    return format_markdown(config, scenarios, top)
```

### 5. `src/config.py` (MODIFY)

Add one constant:

```python
# After existing path definitions:
RECIPES_PATH = _BASE_DIR / ".claude" / "recipes"
```

### 6. `src/__init__.py` (MODIFY)

Add recipe exports:

```python
# Add imports:
from .config import RECIPES_PATH
from .utils import detect_language, generate_slug, generate_unique_slug, get_document_filename
from .recipe import RecipeRunner, discover_recipes, load_recipe

# Add to __all__:
'RECIPES_PATH',
'detect_language', 'generate_slug', 'generate_unique_slug', 'get_document_filename',
'RecipeRunner', 'discover_recipes', 'load_recipe',
```

### 7. `src/orchestrator.py` (MODIFY — minimal)

Replace internal utility methods with imports from `src/utils.py`:

```python
# In imports, add:
from .utils import detect_language, generate_slug, generate_unique_slug, get_document_filename

# In the class, update methods to delegate:
def _detect_language(self, text: str) -> str:
    return detect_language(text)

def _generate_slug(self) -> str:
    return generate_slug(self.state.problem)

def _generate_unique_slug(self) -> str:
    return generate_unique_slug(self.state.problem)

def _get_document_filename(self) -> str:
    return get_document_filename(self.state.language)
```

This keeps backward compatibility (methods still exist on the class) while sharing the logic.

### 8. `strategic_orchestrator.py` (MODIFY)

Add recipe CLI handling:

```python
# In imports, add:
from src import RecipeRunner, discover_recipes

# In main(), add BEFORE the --run block:

    # LIST RECIPES MODE
    if "--list-recipes" in sys.argv:
        from src import load_recipe
        recipe_names = discover_recipes()
        if recipe_names:
            print("Available recipes:\n")
            for name in sorted(recipe_names):
                r = load_recipe(name)
                tags_str = ", ".join(r.tags) if r.tags else ""
                print(f"  {name:<20} {r.methodology:<45} [{r.output_type}]")
                if tags_str:
                    print(f"  {'':<20} {r.description}")
        else:
            print("No recipes found in .claude/recipes/")
        return

    # RECIPE MODE
    if "--recipe" in sys.argv:
        try:
            recipe_idx = sys.argv.index("--recipe")
            recipe_name = sys.argv[recipe_idx + 1]
        except (ValueError, IndexError):
            print("Error: --recipe requires a recipe name")
            print("   Usage: python strategic_orchestrator.py --recipe four-causes")
            print("   List:  python strategic_orchestrator.py --list-recipes")
            sys.exit(1)

        # Optional: topic from CLI or interactive prompt
        topic = None
        if "--topic" in sys.argv:
            try:
                topic_idx = sys.argv.index("--topic")
                topic = sys.argv[topic_idx + 1]
            except (ValueError, IndexError):
                print("Error: --topic requires a text argument")
                sys.exit(1)

        if not topic:
            topic = get_input("Enter analysis topic")
            if not topic:
                print("No topic provided. Aborting.")
                return

        # Optional: context documents
        context_yaml = None
        if "--context" in sys.argv:
            try:
                ctx_idx = sys.argv.index("--context")
                context_yaml = sys.argv[ctx_idx + 1]
            except (ValueError, IndexError):
                print("Error: --context requires a filepath argument")
                sys.exit(1)

        try:
            runner = RecipeRunner(
                recipe_name=recipe_name,
                verbose=verbose_mode,
                context_yaml=context_yaml,
            )
            result = runner.run(topic)
            if result:
                print(f"\n  Document saved to: output/{runner.slug}/")

        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Run --list-recipes to see available recipes.")
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"\nRecipe execution failed: {e}")
        return
```

---

## CLI Interface

### New Commands

```bash
# List available recipes
python strategic_orchestrator.py --list-recipes

# Run a recipe (interactive topic prompt)
python strategic_orchestrator.py --recipe four-causes

# Run with topic specified
python strategic_orchestrator.py --recipe four-causes --topic "European Launch Autonomy"

# Run with context documents
python strategic_orchestrator.py --recipe nine-windows --topic "Lunar PNT" --context context_documents/briefing.yaml

# Verbose mode (works with all existing flags)
python strategic_orchestrator.py --recipe four-pillars --topic "..." -v
```

### Complete CLI (updated)

```
python strategic_orchestrator.py [MODE] [OPTIONS]

Modes (mutually exclusive):
  (none)              Run test suite
  --run               Full orchestrator workflow (analysts → synthesizer → output)
  --resume FILE       Resume from saved state
  --from-folder DIR   Reuse analyst reports
  --recipe NAME       Direct article generation via recipe      ← NEW
  --list-recipes      Show available recipes                    ← NEW

Recipe options:
  --topic TEXT        Analysis topic (prompted if omitted)       ← NEW
  --context FILE      Context documents YAML (L0 sources)       ← NEW

Common options:
  -v, --verbose       Debug output
  -q, --quiet         Warnings only
  --log-file FILE     Log to file
  -h, --help          Show help
```

---

## Implementation Steps (Ordered)

### Phase 1: Foundation (no behavioral changes)

1. **Create `src/utils.py`** — Extract `detect_language`, `generate_slug`, `generate_unique_slug`, `get_document_filename` from orchestrator
2. **Modify `src/orchestrator.py`** — Import from utils, delegate internal methods
3. **Add `RECIPES_PATH` to `src/config.py`**
4. **Verify existing tests pass** — No behavior should change

### Phase 2: Recipe Core

5. **Create `src/recipe.py`** — Data models (`RecipeStep`, `RecipeDefinition`), discovery, loading, validation
6. **Create `src/engines/__init__.py`** and `src/engines/zwicky.py` — Adapt zwicky_engine.py as a registered function
7. **Implement `RecipeRunner`** — Step execution, prompt loading, variable substitution, context chaining, output saving
8. **Update `src/__init__.py`** — Add recipe exports

### Phase 3: CLI Integration

9. **Add `--recipe`, `--list-recipes`, `--topic`, `--context` to `strategic_orchestrator.py`**
10. **Test with simple recipe** (four-causes): end-to-end execution

### Phase 4: Recipe Content

11. **Create `.claude/recipes/` directory structure**
12. **Migrate four-causes** — Copy prompts from `qualcosa/`, create `recipe.yaml`
13. **Migrate nine-windows** — Copy prompts from `qualcosa/`, create `recipe.yaml`
14. **Migrate four-pillars** — Create `recipe.yaml`, copy references, split SKILL.md into step prompts (separate task — document structure only in this phase)

### Phase 5: Documentation

15. **Update `CLAUDE.md`** — Add recipe section
16. **Update `START_HERE.md`** — Add recipe quick start
17. **Add recipe test** to default test mode in `strategic_orchestrator.py`

---

## Key Challenges & Mitigations

### 1. Heterogeneous Prompt Formats

**Problem**: four-causes uses `role:`, `attitude:`, `approach:`, `mission:` keys. nine-windows uses `role:`, `capabilities:`, `constraints:` keys. User prompts use `task:`, `Output_Format:`, etc.

**Solution**: The prompt loader doesn't enforce a specific YAML schema. It loads the YAML file and concatenates all values into a single text string, separated by section headers derived from the keys. This handles any YAML key structure.

```python
def _load_prompt_file(recipe_folder, prompt_path):
    data = yaml.safe_load(path.read_text())
    if isinstance(data, str):
        return data
    # Dict: concatenate all values with key as header
    parts = []
    for key, value in data.items():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.append("\n".join(f"- {item}" for item in value))
        elif isinstance(value, dict):
            # Nested dict: flatten
            for subkey, subval in value.items():
                if isinstance(subval, list):
                    parts.append(f"{subkey}:\n" + "\n".join(f"  - {item}" for item in subval))
                else:
                    parts.append(f"{subkey}: {subval}")
    return "\n\n".join(parts)
```

### 2. Context Chaining in Multi-Step Recipes

**Problem**: In four-pillars, step 5 (TRIZ) needs outputs from both step 1 (matrix) and step 4 (zwicky engine). Steps must execute in order, and outputs must be stored and retrievable by ID.

**Solution**: `RecipeRunner.step_outputs` dict stores each step's output keyed by `step.id`. The `inject_context` field on each step lists which previous step IDs to inject. The executor concatenates requested outputs into a "Previous Analysis Outputs" section appended to the user prompt.

### 3. YAML/JSON Extraction from LLM Responses

**Problem**: When a step asks the LLM to generate YAML (step 3 of four-pillars), the response may contain markdown fencing (\`\`\`yaml ... \`\`\`), explanation text, or other wrapping.

**Solution**: The `_extract_fenced_block()` helper strips fenced code blocks. If no fenced block is found, the full response is used. This makes Python steps resilient to LLM formatting variations.

### 4. Python Step Function Registration

**Problem**: Need a clean way to make Python functions available to recipe steps without hardcoding.

**Solution**: A `@register_engine("name")` decorator pattern. Functions register themselves at import time. The recipe runner looks up functions by name from the registry. New engines are added by creating a new file in `src/engines/` with decorated functions, and importing it in `src/engines/__init__.py`.

### 5. Template Variable Edge Cases

**Problem**: `{title}` appears inside YAML-formatted prompt content. Python's `.format()` would fail on YAML braces `{}`. Using `.replace()` is safer but less flexible.

**Solution**: Use targeted `.replace()` for known variables (`{title}`, `{language}`, `{date}`, `{context_documents}`), NOT Python's `.format()` or f-strings. This avoids conflicts with YAML/JSON syntax in prompt content.

### 6. Keeping Orchestrator Changes Minimal

**Problem**: `src/orchestrator.py` is 2247 lines. Large refactors risk breaking existing functionality.

**Solution**: The orchestrator changes are minimal — only extract 4 utility functions to `src/utils.py` and have the class methods delegate to them. No logic changes, no structural changes. The recipe system lives entirely in new files.

---

## Testing Strategy

### Unit Tests (add to default test mode)

```python
# Test R1: Recipe discovery
recipes = discover_recipes()
assert "four-causes" in recipes  # After migration

# Test R2: Recipe loading
recipe = load_recipe("four-causes")
assert recipe.name == "four-causes"
assert recipe.methodology == "Four Causes (4Dimensions Ontology)"
assert recipe.output_type == "analysis"
assert len(recipe.steps) == 1
assert recipe.steps[0].type == "llm_call"
assert recipe.steps[0].model == ""  # No override, uses system default

# Test R3: Prompt loading
prompt = _load_prompt_file(recipe.folder, "prompts/system.yml")
assert len(prompt) > 0

# Test R4: Variable substitution
runner = RecipeRunner("four-causes")
result = runner._substitute_variables("Analyze {title} in {language}")
# Verify variables replaced

# Test R5: Python function registry
from src.engines.zwicky import zwicky_generate
assert "zwicky_generate" in _PYTHON_FUNCTIONS

# Test R6: Zwicky engine
yaml_input = """
topic: "Test"
dimensions:
  Feature1:
    - {name: "A", weight: 9}
    - {name: "B", weight: 5}
  Feature2:
    - {name: "X", weight: 8}
    - {name: "Y", weight: 3}
constraints: []
"""
result = zwicky_generate(yaml_input, top=2, format="md")
assert "Scenario" in result
```

### Integration Test

```bash
# Requires ANTHROPIC_API_KEY
python strategic_orchestrator.py --recipe four-causes --topic "Test topic" -v
# Verify: output/test-topic/index.md exists and has valid frontmatter
```

---

## Future Extensibility

### Adding a New Recipe

1. Create folder `.claude/recipes/{recipe-name}/`
2. Create `recipe.yaml` with metadata and steps
3. Add prompt files in `prompts/` subfolder
4. (Optional) Add reference documents in `references/`
5. (Optional) If recipe needs Python: add function to `src/engines/`, decorate with `@register_engine`

No code changes needed in the core system.

### Possible Future Enhancements (NOT in scope)

- **Recipe chaining**: Run recipe A, then feed its output to recipe B
- **Interactive recipes**: Steps with `type: user_approval` for mid-pipeline review
- **Parallel steps**: Independent steps that can run concurrently
- **Recipe state persistence**: Checkpoint/resume for long multi-step recipes
- **Recipe marketplace**: Share recipes across projects

---

## Summary of All Changes

| File | Action | Description |
|------|--------|-------------|
| `src/utils.py` | CREATE | Shared utilities (detect_language, slugs, etc.) |
| `src/recipe.py` | CREATE | RecipeRunner, data models, discovery, loading, execution |
| `src/engines/__init__.py` | CREATE | Engine module init |
| `src/engines/zwicky.py` | CREATE | Zwicky engine as registered function |
| `src/config.py` | MODIFY | Add `RECIPES_PATH` constant |
| `src/__init__.py` | MODIFY | Add recipe + utils exports |
| `src/orchestrator.py` | MODIFY | Import from utils, delegate 4 methods |
| `strategic_orchestrator.py` | MODIFY | Add --recipe, --list-recipes, --topic, --context flags |
| `.claude/recipes/four-causes/` | CREATE | recipe.yaml + prompts (from qualcosa) |
| `.claude/recipes/nine-windows/` | CREATE | recipe.yaml + prompts (from qualcosa) |
| `.claude/recipes/four-pillars/` | CREATE | recipe.yaml + references (prompts = future task) |
| `CLAUDE.md` | MODIFY | Document recipe system |
