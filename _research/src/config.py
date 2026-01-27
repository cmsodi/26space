"""
Configuration constants and enums for the Strategic Orchestrator.
"""

from enum import Enum
from pathlib import Path


# ============== PATHS ==============

# Paths - relative to this file's location (src/config.py -> _research/.claude/)
_BASE_DIR = Path(__file__).parent.parent  # _research/
SKILLS_PATH = _BASE_DIR / ".claude" / "skills"
AGENTS_PATH = _BASE_DIR / ".claude" / "agents"
OUTPUT_GEN_PATH = SKILLS_PATH / "_OUTPUT_GENERATION.md"


# ============== MODEL SELECTION ==============

MODEL_DEFAULT = "claude-sonnet-4-20250514"
MODEL_COMPLEX = "claude-opus-4-20250514"  # For integration/complex steps
MODEL_FAST = "claude-sonnet-4-20250514"   # For quick tasks like translation


# ============== STEP STATE MACHINE ==============

class Step(Enum):
    """Workflow steps - enforces sequential progression."""
    INIT = "init"
    PROBLEM_PARSED = "problem_parsed"
    SOURCES_DECIDED = "sources_decided"
    CLARIFIED = "clarified"
    PROPOSAL_APPROVED = "proposal_approved"
    ANALYSTS_COMPLETE = "analysts_complete"
    OUTLINE_APPROVED = "outline_approved"
    CITATIONS_MAPPED = "citations_mapped"
    COMPLETE = "complete"


# ============== SYNTHESIZER CONFIGURATION ==============

# Known synthesizers and their configurations
SYNTHESIZERS = {
    "strategic-geopolitical": {
        "name": "Strategic Geopolitical",
        "fixed_analysts": ["pestle-analyst", "morphological-analyst", "stakeholder-mapper"],
        "optional_analysts": ["scenario-planner", "geopolitical-theorist"],
        "keywords": ["geopolitical", "power", "state", "alliance", "conflict", "deterrence", "sovereignty"]
    },
    "strategic-industrial": {
        "name": "Strategic Industrial",
        "fixed_analysts": ["pestle-analyst", "ecosystem-analyst", "swot-analyst"],
        "optional_analysts": ["horizon-analyst", "scenario-planner"],
        "keywords": ["industry", "market", "competition", "supply chain", "manufacturing", "business"]
    },
    "policy-regulatory": {
        "name": "Policy Regulatory",
        "fixed_analysts": ["pestle-analyst", "stakeholder-mapper", "perspectives-analyst"],
        "optional_analysts": ["scenario-planner"],
        "keywords": ["policy", "regulation", "governance", "law", "compliance", "framework", "treaty"]
    }
}

# Available templates
TEMPLATES = ["BLUF", "Hypothesis-Driven", "POR", "Minto-Custom"]
