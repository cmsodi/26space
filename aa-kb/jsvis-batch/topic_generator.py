#!/usr/bin/env python3
"""
Phase 1: Topic Generator
Generates generic topics for each tag in the 4dimensions© taxonomy.
Supports incremental generation (merge with existing topics.yaml).
"""

import os
import sys
import yaml
import argparse
import time
from pathlib import Path
from anthropic import Anthropic

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_prompt(prompts_dir: str, prompt_name: str) -> dict:
    """Load a prompt template from YAML file."""
    prompt_path = Path(prompts_dir) / f"{prompt_name}.yaml"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# -----------------------------------------------------------------------------
# LLM Interaction
# -----------------------------------------------------------------------------

def build_system_prompt(system_template: dict) -> str:
    """Build system prompt string from template."""
    parts = []
    if 'role' in system_template:
        parts.append(f"Role: {system_template['role']}")
    if 'context' in system_template:
        parts.append(f"\n{system_template['context']}")
    if 'principles' in system_template:
        parts.append("\nPrinciples:")
        for p in system_template['principles']:
            parts.append(f"- {p}")
    if 'constraints' in system_template:
        c = system_template['constraints']
        if 'forbidden_patterns' in c:
            parts.append("\nForbidden (DO NOT USE):")
            for f in c['forbidden_patterns']:
                parts.append(f"- {f}")
        if 'required_patterns' in c:
            parts.append("\nRequired patterns:")
            for r in c['required_patterns']:
                parts.append(f"- {r}")
    return "\n".join(parts)

def build_user_prompt(user_template: dict, **kwargs) -> str:
    """Build user prompt string from template with variable substitution."""
    # Format existing_topics for display
    existing = kwargs.get('existing_topics', [])
    if existing:
        existing_str = "\n".join(f"- {t}" for t in existing)
    else:
        existing_str = "(none)"
    kwargs['existing_topics'] = existing_str
    
    parts = []
    if 'task' in user_template:
        parts.append(user_template['task'].format(**kwargs))
    if 'input' in user_template:
        parts.append("\nInput:")
        for k, v in user_template['input'].items():
            parts.append(f"  {k}: {v.format(**kwargs)}")
    if 'instructions' in user_template:
        parts.append(f"\n{user_template['instructions'].format(**kwargs)}")
    if 'existing_topics' in user_template:
        parts.append(f"\nExisting topics:\n{existing_str}")
    if 'merge_instruction' in user_template:
        parts.append(f"\n{user_template['merge_instruction'].format(**kwargs)}")
    if 'output_format' in user_template:
        parts.append(f"\n{user_template['output_format']}")
    return "\n".join(parts)

def call_llm(client: Anthropic, model: str, system_prompt: str, user_prompt: str) -> str:
    """Call Claude API and return response text."""
    response = client.messages.create(
        model=model,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def parse_topics_response(response: str) -> list:
    """Parse YAML list from LLM response."""
    # Clean response (remove markdown code blocks if present)
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1])
    
    # Parse YAML
    try:
        topics = yaml.safe_load(response)
        if isinstance(topics, list):
            return [str(t).strip() for t in topics if t]
        return []
    except yaml.YAMLError:
        # Fallback: parse as simple list
        topics = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                topics.append(line[2:].strip())
            elif line and not line.startswith("#"):
                topics.append(line)
        return topics

# -----------------------------------------------------------------------------
# Topic Generation
# -----------------------------------------------------------------------------

def generate_topics_for_tag(
    client: Anthropic,
    model: str,
    system_template: dict,
    user_template: dict,
    category: str,
    category_desc: str,
    tag: str,
    topics_count: int,
    existing_topics: list = None
) -> list:
    """Generate topics for a single tag."""
    system_prompt = build_system_prompt(system_template)
    user_prompt = build_user_prompt(
        user_template,
        category=category,
        category_description=category_desc,
        tag=tag,
        topics_count=topics_count,
        existing_topics=existing_topics or []
    )
    
    response = call_llm(client, model, system_prompt, user_prompt)
    new_topics = parse_topics_response(response)
    
    # Merge with existing (deduplicate)
    if existing_topics:
        existing_lower = {t.lower() for t in existing_topics}
        new_topics = [t for t in new_topics if t.lower() not in existing_lower]
        return existing_topics + new_topics
    
    return new_topics

def load_existing_topics(topics_path: str) -> dict:
    """Load existing topics.yaml if it exists."""
    if os.path.exists(topics_path):
        with open(topics_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_topics(topics: dict, topics_path: str):
    """Save topics to YAML file."""
    with open(topics_path, 'w', encoding='utf-8') as f:
        yaml.dump(topics, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate topics for 4dimensions© taxonomy")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--model", help="Override default model")
    parser.add_argument("--category", help="Generate only for specific category")
    parser.add_argument("--tag", help="Generate only for specific tag")
    parser.add_argument("--count", type=int, help="Override topics per tag count")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling API")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    prompts_dir = config['paths']['prompts_dir']
    topics_path = config['paths']['topics_yaml']
    
    # Model selection
    model = args.model or config['models']['topic_generator']['default']
    topics_count = args.count or config['generation']['topics_per_tag']
    batch_delay = config['generation'].get('batch_delay', 1.0)
    
    # Load prompts
    system_template = load_prompt(prompts_dir, "topic_generator_system")
    user_template = load_prompt(prompts_dir, "topic_generator_user")
    
    # Load existing topics (for incremental generation)
    existing_data = load_existing_topics(topics_path)
    
    # Initialize Anthropic client
    client = Anthropic()
    
    # Generate topics for each category/tag
    taxonomy = config['taxonomy']
    result = {}
    
    for category, cat_data in taxonomy.items():
        # Filter by category if specified
        if args.category and category != args.category:
            continue
        
        cat_desc = cat_data['description']
        result[category] = existing_data.get(category, {})
        
        for tag in cat_data['tags']:
            # Filter by tag if specified
            if args.tag and tag != args.tag:
                continue
            
            existing_topics = result[category].get(tag, [])
            
            print(f"Generating topics for {category}/{tag}...", end=" ", flush=True)
            
            if args.dry_run:
                print("[DRY RUN]")
                system_prompt = build_system_prompt(system_template)
                user_prompt = build_user_prompt(
                    user_template,
                    category=category,
                    category_description=cat_desc,
                    tag=tag,
                    topics_count=topics_count,
                    existing_topics=existing_topics
                )
                print(f"\n--- SYSTEM PROMPT ---\n{system_prompt}")
                print(f"\n--- USER PROMPT ---\n{user_prompt}\n")
                continue
            
            try:
                topics = generate_topics_for_tag(
                    client, model, system_template, user_template,
                    category, cat_desc, tag, topics_count, existing_topics
                )
                result[category][tag] = topics
                print(f"OK ({len(topics)} topics)")
                
                # Rate limiting
                time.sleep(batch_delay)
                
            except Exception as e:
                print(f"ERROR: {e}")
                result[category][tag] = existing_topics
    
    # Save results
    if not args.dry_run:
        save_topics(result, topics_path)
        print(f"\nTopics saved to {topics_path}")
        
        # Summary
        total = sum(len(tags) for cat in result.values() for tags in cat.values())
        print(f"Total topics: {total}")

if __name__ == "__main__":
    main()
