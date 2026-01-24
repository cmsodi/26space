#!/usr/bin/env python3
"""
Phase 2: Outline Generator
Generates jsvis map outlines for each topic and creates HUGO markdown files.
"""

import os
import sys
import yaml
import argparse
import time
import re
from pathlib import Path
from datetime import datetime
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

def load_topics(topics_path: str) -> dict:
    """Load topics from YAML file."""
    with open(topics_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# -----------------------------------------------------------------------------
# LLM Interaction
# -----------------------------------------------------------------------------

def build_system_prompt(system_template: dict) -> str:
    """Build system prompt string from template."""
    parts = []
    if 'role' in system_template:
        parts.append(f"Role: {system_template['role']}")
    if 'capabilities' in system_template:
        parts.append("\nCapabilities:")
        for c in system_template['capabilities']:
            parts.append(f"- {c}")
    if 'target_audience' in system_template:
        parts.append("\nTarget audience:")
        for t in system_template['target_audience']:
            parts.append(f"- {t}")
    if 'methodology' in system_template:
        parts.append(f"\nMethodology:\n{system_template['methodology']}")
    if 'context' in system_template:
        parts.append(f"\n{system_template['context']}")
    return "\n".join(parts)

def build_user_prompt(user_template: dict, **kwargs) -> str:
    """Build user prompt string from template with variable substitution."""
    parts = []

    if 'task' in user_template:
        parts.append(user_template['task'].format(**kwargs))

    if 'input' in user_template:
        parts.append("\nInput:")
        for k, v in user_template['input'].items():
            parts.append(f"  {k}: {v.format(**kwargs)}")

    if 'mece_requirements' in user_template:
        parts.append(f"\n{user_template['mece_requirements']}")

    if 'structure_requirements' in user_template:
        sr = user_template['structure_requirements']
        parts.append("\nStructure requirements:")
        if 'mandatory_structure' in sr:
            parts.append(f"  MANDATORY STRUCTURE: {sr['mandatory_structure']}")
        if 'total_nodes' in sr:
            parts.append(f"  TOTAL NODES: {sr['total_nodes']}")
        for level in sr.get('levels', []):
            parts.append(f"  Level {level['level']}: {level['prefix']} - {level['content']} ({level['count']})")
    
    if 'line_format' in user_template:
        parts.append(f"\nLine format:\n{user_template['line_format']}")
    
    if 'search_query_rules' in user_template:
        parts.append("\nSearch query rules:")
        rules = user_template['search_query_rules']
        for node_type, rule in rules.items():
            parts.append(f"  {node_type}: {rule.get('format', '')} (max {rule.get('max_keywords', 'N/A')} keywords)")
            if 'example' in rule:
                parts.append(f"    Example: {rule['example'].format(**kwargs)}")
    
    if 'output_constraints' in user_template:
        parts.append("\nOutput constraints:")
        for c in user_template['output_constraints']:
            parts.append(f"- {c}")
    
    if 'example_output' in user_template:
        parts.append(f"\nExample output:\n{user_template['example_output']}")
    
    if 'final_instruction' in user_template:
        parts.append(f"\n{user_template['final_instruction'].format(**kwargs)}")
    
    return "\n".join(parts)

def call_llm(client: Anthropic, model: str, system_prompt: str, user_prompt: str) -> str:
    """Call Claude API and return response text."""
    response = client.messages.create(
        model=model,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    return response.content[0].text

def clean_outline(response: str) -> str:
    """Clean LLM response to extract only the outline."""
    # Remove markdown code blocks if present
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        # Find end of code block
        end_idx = len(lines)
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "```":
                end_idx = i
                break
        response = "\n".join(lines[1:end_idx])
    
    # Remove any leading/trailing explanations
    lines = response.split("\n")
    outline_lines = []
    in_outline = False
    
    for line in lines:
        stripped = line.strip()
        # Start capturing when we see a heading
        if stripped.startswith("#"):
            in_outline = True
        if in_outline:
            # Skip empty lines
            if stripped:
                outline_lines.append(line)
    
    return "\n".join(outline_lines)

# -----------------------------------------------------------------------------
# File Generation
# -----------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    return text

def create_hugo_frontmatter(topic: str, category: str, tag: str) -> str:
    """Create HUGO frontmatter for the markdown file."""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""---
title: "{topic}"
category: "{category}"
tag: "{tag}"
date: {today}
draft: false
---
"""

def create_hugo_file(
    topic: str,
    category: str,
    tag: str,
    outline: str,
    hugo_content_path: str,
    shortcode_name: str,
    bg_color: str,
    bg_image: str
) -> str:
    """Create HUGO markdown file with shortcode."""
    # Create directory structure
    dir_path = Path(hugo_content_path) / category / tag
    dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create file
    slug = slugify(topic)
    file_path = dir_path / f"{slug}.md"
    
    # Build content
    frontmatter = create_hugo_frontmatter(topic, category, tag)
    
    # Wrap outline in shortcode
    bg_image_param = f' "{bg_image}"' if bg_image else ' ""'
    shortcode_open = f'{{{{< {shortcode_name} "{bg_color}"{bg_image_param} >}}}}'
    shortcode_close = f'{{{{< /{shortcode_name} >}}}}'
    
    content = f"{frontmatter}\n{shortcode_open}\n{outline}\n{shortcode_close}\n"
    
    # Write file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(file_path)

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate jsvis map outlines and HUGO files")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument("--model", help="Override default model")
    parser.add_argument("--category", help="Generate only for specific category")
    parser.add_argument("--tag", help="Generate only for specific tag")
    parser.add_argument("--topic", help="Generate only for specific topic")
    parser.add_argument("--dry-run", action="store_true", help="Print prompts without calling API")
    parser.add_argument("--skip-existing", action="store_true", help="Skip if .md file already exists")
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    prompts_dir = config['paths']['prompts_dir']
    topics_path = config['paths']['topics_yaml']
    hugo_content_path = config['paths']['hugo_content']
    
    # Model selection
    model = args.model or config['models']['outline_generator']['default']
    batch_delay = config['generation'].get('batch_delay', 1.0)
    
    # HUGO settings
    shortcode_name = config['hugo']['shortcode_name']
    bg_color = config['hugo']['background_color']
    bg_image = config['hugo']['background_image']
    
    # Load prompts
    system_template = load_prompt(prompts_dir, "outline_system")
    user_template = load_prompt(prompts_dir, "outline_user")
    
    # Load topics
    topics_data = load_topics(topics_path)
    
    # Initialize Anthropic client
    client = Anthropic()
    
    # Statistics
    stats = {"generated": 0, "skipped": 0, "errors": 0}
    
    # Process each topic
    for category, tags in topics_data.items():
        # Filter by category if specified
        if args.category and category != args.category:
            continue
        
        for tag, topics in tags.items():
            # Filter by tag if specified
            if args.tag and tag != args.tag:
                continue
            
            for topic in topics:
                # Filter by topic if specified
                if args.topic and topic.lower() != args.topic.lower():
                    continue
                
                # Check if file already exists
                if args.skip_existing:
                    slug = slugify(topic)
                    file_path = Path(hugo_content_path) / category / tag / f"{slug}.md"
                    if file_path.exists():
                        print(f"SKIP (exists): {category}/{tag}/{topic}")
                        stats["skipped"] += 1
                        continue
                
                print(f"Generating: {category}/{tag}/{topic}...", end=" ", flush=True)
                
                if args.dry_run:
                    print("[DRY RUN]")
                    system_prompt = build_system_prompt(system_template)
                    user_prompt = build_user_prompt(
                        user_template,
                        topic=topic,
                        category=category,
                        tag=tag
                    )
                    print(f"\n--- SYSTEM PROMPT ---\n{system_prompt[:500]}...")
                    print(f"\n--- USER PROMPT ---\n{user_prompt[:500]}...\n")
                    continue
                
                try:
                    # Build prompts
                    system_prompt = build_system_prompt(system_template)
                    user_prompt = build_user_prompt(
                        user_template,
                        topic=topic,
                        category=category,
                        tag=tag
                    )
                    
                    # Call LLM
                    response = call_llm(client, model, system_prompt, user_prompt)
                    outline = clean_outline(response)
                    
                    # Create HUGO file
                    file_path = create_hugo_file(
                        topic, category, tag, outline,
                        hugo_content_path, shortcode_name, bg_color, bg_image
                    )
                    
                    print(f"OK → {file_path}")
                    stats["generated"] += 1
                    
                    # Rate limiting
                    time.sleep(batch_delay)
                    
                except Exception as e:
                    print(f"ERROR: {e}")
                    stats["errors"] += 1
    
    # Summary
    if not args.dry_run:
        print(f"\n--- Summary ---")
        print(f"Generated: {stats['generated']}")
        print(f"Skipped:   {stats['skipped']}")
        print(f"Errors:    {stats['errors']}")

if __name__ == "__main__":
    main()
