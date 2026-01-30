"""Zwicky Box Engine — callable from recipe steps.

Generates morphological analysis scenarios from YAML configuration.
Adapted from qualcosa/four-pillars/scripts/zwicky_engine.py.
No external dependencies required (stdlib only).
"""

import re
import itertools
import json
from typing import Dict, List, Any

from ..recipe import register_engine


def parse_yaml_simple(yaml_string: str) -> Dict[str, Any]:
    """
    Minimal YAML parser for the specific scenarios.yaml structure.
    Handles: topic, dimensions with variants, constraints.
    No external dependencies.
    """
    config = {
        'topic': '',
        'dimensions': {},
        'constraints': []
    }

    lines = yaml_string.strip().split('\n')
    current_dimension = None
    in_constraints = False

    for line in lines:
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Topic
        topic_match = re.match(r'^topic:\s*["\']?(.+?)["\']?\s*$', line)
        if topic_match:
            config['topic'] = topic_match.group(1)
            continue

        # Dimensions section
        if re.match(r'^dimensions:', line):
            in_constraints = False
            continue

        # Constraints section
        if re.match(r'^constraints:', line):
            in_constraints = True
            continue

        # Constraint item: - ["A", "B"]
        if in_constraints and stripped.startswith('-'):
            constraint_match = re.search(r'\[([^\]]+)\]', line)
            if constraint_match:
                items = [s.strip().strip('"\'')
                        for s in constraint_match.group(1).split(',')]
                config['constraints'].append(items)
            continue

        # Dimension name (2 spaces indent)
        dim_match = re.match(r'^  (\w[\w\s]*?):\s*$', line)
        if dim_match and not in_constraints:
            current_dimension = dim_match.group(1).strip()
            config['dimensions'][current_dimension] = []
            continue

        # Variant item (4+ spaces indent)
        variant_match = re.search(
            r'name:\s*["\']?([^"\',$}]+)["\']?,\s*weight:\s*(\d+)',
            line
        )
        if variant_match and current_dimension:
            config['dimensions'][current_dimension].append({
                'name': variant_match.group(1).strip(),
                'weight': int(variant_match.group(2))
            })

    return config


def is_consistent(variant_names: List[str], constraints: List[List[str]]) -> bool:
    """Check if a combination violates any constraints."""
    for constraint in constraints:
        if all(item in variant_names for item in constraint):
            return False
    return True


def generate_scenarios(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate all valid combinations, filter by constraints, sort by score.

    Returns list of scenarios with:
        - configuration: dict mapping dimension -> variant
        - score: sum of weights
    """
    dimensions = config.get('dimensions', {})
    constraints = config.get('constraints', [])

    if not dimensions:
        return []

    dim_names = list(dimensions.keys())
    dim_variants = [dimensions[d] for d in dim_names]

    # Generate all combinations
    all_combos = list(itertools.product(*dim_variants))

    scenarios = []
    for combo in all_combos:
        names = [v['name'] for v in combo]

        if is_consistent(names, constraints):
            score = sum(v['weight'] for v in combo)
            scenarios.append({
                'configuration': dict(zip(dim_names, names)),
                'score': score
            })

    # Sort by score descending
    scenarios.sort(key=lambda x: x['score'], reverse=True)
    return scenarios


def format_markdown(config: Dict[str, Any], scenarios: List[Dict], top_n: int = 3) -> str:
    """Format output as Markdown."""
    dimensions = config.get('dimensions', {})
    dim_names = list(dimensions.keys())

    lines = []

    # Header
    lines.append(f"# Zwicky Box: {config.get('topic', 'Strategic Analysis')}")
    lines.append("")

    # Statistics
    total_possible = 1
    for d in dimensions.values():
        total_possible *= len(d)

    lines.append("## Statistics")
    lines.append("")
    lines.append(f"- **Possible combinations:** {total_possible}")
    lines.append(f"- **Valid scenarios:** {len(scenarios)}")
    lines.append(f"- **Excluded (constraints):** {total_possible - len(scenarios)}")
    lines.append(f"- **Constraints applied:** {len(config.get('constraints', []))}")
    lines.append("")

    # Full ranking table
    lines.append("## Scenarios Ranked by Score")
    lines.append("")

    headers = ["Rank", "Score"] + dim_names
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for i, s in enumerate(scenarios, 1):
        row = [str(i), str(s['score'])]
        row += [s['configuration'][d] for d in dim_names]
        lines.append("| " + " | ".join(row) + " |")

    lines.append("")

    # Top N detailed
    lines.append(f"## Top {top_n} Scenarios for Analysis")
    lines.append("")

    for i, s in enumerate(scenarios[:top_n], 1):
        lines.append(f"### Scenario {i} (Score: {s['score']})")
        lines.append("")
        for dim, val in s['configuration'].items():
            lines.append(f"- **{dim}:** {val}")
        lines.append("")

    return "\n".join(lines)


def format_json(config: Dict[str, Any], scenarios: List[Dict], top_n: int = 3) -> str:
    """Format output as JSON."""
    dimensions = config.get('dimensions', {})

    total_possible = 1
    for d in dimensions.values():
        total_possible *= len(d)

    output = {
        'topic': config.get('topic', 'Strategic Analysis'),
        'statistics': {
            'total_possible': total_possible,
            'valid_scenarios': len(scenarios),
            'excluded': total_possible - len(scenarios),
            'constraints_count': len(config.get('constraints', []))
        },
        'all_scenarios': scenarios,
        'top_scenarios': scenarios[:top_n]
    }

    return json.dumps(output, indent=2)


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
