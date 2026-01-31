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


def ensure_unique_slug(slug: str, output_base: Path = Path("output")) -> str:
    """Like generate_unique_slug but takes an existing slug directly.

    Used when the slug comes from editorial_plan.yaml instead of being
    generated from text.
    """
    output_dir = output_base / slug
    if not output_dir.exists():
        return slug
    counter = 1
    while counter <= 1000:
        numbered = f"{slug}_{counter}"
        if not (output_base / numbered).exists():
            return numbered
        counter += 1
    raise RuntimeError(f"Too many existing folders for slug: {slug}")


def get_document_filename(language: str) -> str:
    """Get final document filename based on language."""
    return "index.it.md" if language == "it" else "index.md"
