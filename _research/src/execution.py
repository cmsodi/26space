"""
Phase 4 execution engine — barrel module.

Composes all Phase 4 mixins into a single ExecutionMixin for
StrategicOrchestrator to inherit.

Sub-modules:
  - analysts.py   — Phase 4.1: analyst execution (sync + async + recovery)
  - outline.py    — Phase 4.2: outline generation and approval
  - citations.py  — Phase 4.3: citation enrichment and Exa L2 fill
  - output.py     — Phase 4.4: full text generation, frontmatter, file I/O
"""

from .analysts import AnalystsMixin
from .outline import OutlineMixin
from .citations import CitationsMixin
from .output import OutputMixin


class ExecutionMixin(AnalystsMixin, OutlineMixin, CitationsMixin, OutputMixin):
    """
    Composite mixin that provides all Phase 4 execution methods.

    Mixed into StrategicOrchestrator — the public API is unchanged.
    """
    pass
