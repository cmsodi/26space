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
    if not RECIPES_PATH.exists():
        return []
    return [
        d.name for d in sorted(RECIPES_PATH.iterdir())
        if d.is_dir() and (d / "recipe.yaml").exists()
    ]


def load_recipe(name: str) -> RecipeDefinition:
    """Load and validate recipe.yaml from .claude/recipes/{name}/."""
    recipe_folder = RECIPES_PATH / name
    recipe_file = recipe_folder / "recipe.yaml"

    if not recipe_file.exists():
        raise FileNotFoundError(
            f"Recipe '{name}' not found at {recipe_file}"
        )

    with open(recipe_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # Parse steps
    steps = [_parse_step(s) for s in data.get("steps", [])]

    return RecipeDefinition(
        name=data["name"],
        description=data["description"],
        version=data["version"],
        methodology=data["methodology"],
        output_type=data["output_type"],
        tags=data.get("tags", []),
        steps=steps,
        references=data.get("references", []),
        folder=recipe_folder,
    )


def _parse_step(step_dict: dict) -> RecipeStep:
    """Parse a step definition from recipe.yaml."""
    return RecipeStep(
        id=step_dict["id"],
        type=step_dict["type"],
        system_prompt=step_dict.get("system_prompt", ""),
        user_prompt=step_dict.get("user_prompt", ""),
        model=step_dict.get("model", ""),
        max_tokens=step_dict.get("max_tokens", 4000),
        temperature=step_dict.get("temperature", 0.7),
        inject_context=step_dict.get("inject_context", []),
        output_format=step_dict.get("output_format", "text"),
        function=step_dict.get("function", ""),
        input_from=step_dict.get("input_from", ""),
        args=step_dict.get("args", {}),
    )


def _load_prompt_file(recipe_folder: Path, prompt_path: str) -> str:
    """
    Load a YAML prompt file and compose it into a single prompt string.

    Handles:
    - Single root string -> use as-is
    - Multiple YAML keys -> concatenate values with double newlines
    - Template variables are NOT replaced here (done at execution time)
    """
    filepath = recipe_folder / prompt_path
    if not filepath.exists():
        raise FileNotFoundError(f"Prompt file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if isinstance(data, str):
        return data

    # Dict: concatenate all values
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


def _load_references(recipe_folder: Path, ref_paths: list[str]) -> str:
    """Load and concatenate all reference documents into a single context string."""
    if not ref_paths:
        return ""

    parts = []
    for ref_path in ref_paths:
        filepath = recipe_folder / ref_path
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8")
            parts.append(content)
        else:
            logger.warning(f"Reference file not found: {filepath}")

    return "\n\n---\n\n".join(parts)


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
        self.step_outputs: dict[str, str] = {}   # step_id -> output text
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
        self._vprint(f"  Recipe: {self.recipe.name}")
        self._vprint(f"  Methodology: {self.recipe.methodology}")
        self._vprint(f"  Output type: {self.recipe.output_type}")
        self._vprint(f"  Topic: {self.topic}")
        self._vprint(f"  Language: {self.language}")
        self._vprint(f"  Steps: {len(self.recipe.steps)}")

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
        Empty/missing model_key -> system default (MODEL_DEFAULT).
        """
        if not model_key:
            return MODEL_DEFAULT
        if model_key == "complex":
            return MODEL_COMPLEX
        return MODEL_DEFAULT

    def _load_context_documents(self):
        """Load L0 context documents from YAML file."""
        context_path = Path(self.context_yaml)
        if not context_path.exists():
            logger.warning(f"Context file not found: {context_path}")
            return

        with open(context_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict):
            # Handle both flat and nested YAML structures
            sources = data.get("sources", data.get("context_documents", []))
            if isinstance(sources, list):
                self.context_documents = sources
            else:
                self.context_documents = [data]
        elif isinstance(data, list):
            self.context_documents = data

    def _format_context_documents(self) -> str:
        """Format loaded context documents as prompt section."""
        if not self.context_documents:
            return ""

        parts = ["\n\n## Context Documents (L0 Sources)\n"]
        for i, doc in enumerate(self.context_documents, 1):
            if isinstance(doc, dict):
                title = doc.get("title", doc.get("name", f"Source {i}"))
                url = doc.get("url", "")
                desc = doc.get("description", doc.get("summary", ""))
                parts.append(f"\n### {i}. {title}")
                if url:
                    parts.append(f"- URL: {url}")
                if desc:
                    parts.append(f"- {desc}")
            elif isinstance(doc, str):
                parts.append(f"\n- {doc}")

        return "\n".join(parts)

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
