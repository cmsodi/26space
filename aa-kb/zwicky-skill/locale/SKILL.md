---
name: zwicky-strategic-analyst
description: |
  Generate strategic reports using Advanced Morphological Analysis (Zwicky Box), 
  4Dimensions© ontology, TRIZ problem-solving, and Minto Pyramid communication.
  
  Use when:
  - Creating strategic analysis on complex topics (space, defense, policy, technology)
  - Generating scenario analysis for decision-making
  - Building executive reports with morphological methodology
  - Analyzing trade-offs and contradictions using TRIZ principles
  - User mentions "Zwicky", "morphological analysis", "4Dimensions", "strategic scenarios"
  
  Output: Professional reports in Markdown, Word (.docx), PowerPoint (.pptx), or Excel (.xlsx)
---

# Zwicky Strategic Analyst

Generate executive-ready strategic reports using Advanced Morphological Analysis.

## Overview

This skill transforms complex strategic topics into structured analysis using:
- **4Dimensions© Ontology**: Material, Formal, Efficient, Final causes across 4 levels
- **Zwicky Box**: Morphological analysis for scenario generation
- **TRIZ**: Inventive problem-solving for contradiction resolution
- **Minto Pyramid**: Clear communication structure

## Workflow

Execute the full pipeline in a single pass. Do not ask for "OK" between steps.

### Step 1: Generate 4×4 Strategic Matrix

Create a 16-cell matrix mapping the topic through:

**Columns (Levels)**:
- Foundational: Universal substrates, basic principles
- Subsystem: Components, specifications
- System: Integrated platforms, processes
- Supersystem: Networks, governance, coordination

**Rows (Dimensions)**:
- Material: Physical assets, hardware, technologies
- Formal: Frameworks, software, standards, laws
- Efficient: ONLY human agents/organizations
- Final: Purposes, missions, objectives

**Output**: Markdown table with 5+ bullet points per cell.

### Step 2: Select Strategic Features

From the matrix, identify 3 Features (variables) with strategic optionality:
- Each Feature has exactly 3 Variants (mutually exclusive options)
- Features must be independent of each other
- Check: Constants (fixed) vs Variables (genuine choices)

**Output format per Feature**:
1. Feature Name
2. Source Cell (e.g., Material/System)
3. Strategic Question
4. Justification
5. Three Variants listed

### Step 3: Generate Scenarios YAML

Transform features into YAML configuration:

```yaml
topic: "{topic}"
dimensions:
  Feature1:
    - {name: "Variant_A", weight: 9}
    - {name: "Variant_B", weight: 6}
    - {name: "Variant_C", weight: 3}
  Feature2:
    - {name: "Variant_X", weight: 8}
    - {name: "Variant_Y", weight: 5}
    - {name: "Variant_Z", weight: 2}
  Feature3:
    - {name: "Option_1", weight: 7}
    - {name: "Option_2", weight: 4}
    - {name: "Option_3", weight: 1}
constraints:
  - ["Variant_A", "Variant_X"]  # Physically/logically incompatible
```

**Weight assignment**: 1-10 based on alignment with stated objective. Higher = better fit.

### Step 4: Run Zwicky Engine

Execute `scripts/zwicky_engine.py` with the YAML to generate:
- All valid combinations (excluding constrained pairs)
- Scenarios ranked by total score
- Top 3 scenarios for detailed analysis

### Step 5: TRIZ Brainstorming (Top 3 Scenarios)

For EACH of the top 3 scenarios:

1. **Scenario Visualization**: Describe how the combination works in practice
2. **4Dimensions Check**: Map back to System/Supersystem levels
3. **TRIZ Analysis**:
   - Identify the contradiction (e.g., "High X but low Y")
   - Select a TRIZ principle to resolve it:
     - #1 Segmentation
     - #2 Taking out
     - #10 Action in advance
     - #15 Dynamics
     - #25 Self-service
     - (or any of the 40 principles)
   - Apply the solution concretely

### Step 6: Strategic Merging

Compare the 3 scenarios:

1. **Overlap Matrix**: Shared dimensions per pair (X/3), difference type (incremental/radical)
2. **Compatibility Verdict**: COMPATIBLE / ALTERNATIVE / PARTIAL
3. **Structure Selection**:
   - Structure A (Alternatives): For mutually exclusive options
   - Structure B (Integrated): For compatible components
4. **Minto Premises**:
   - Situation: Current undeniable state
   - Complication: Why action is needed now
   - Solution: Core recommendation

### Step 7: Create 3×3×3 Outline

Structure following Minto Pyramid:

```
Introduction (S-C-Q-A)
├── Section 1: Primary Component/Argument
│   ├── 1.1 [Specific content]
│   ├── 1.2 [Specific content]
│   └── 1.3 [Specific content]
├── Section 2: Secondary Component/Argument
│   ├── 2.1 [Specific content]
│   ├── 2.2 [Specific content]
│   └── 2.3 [Specific content]
└── Section 3: Evolution/Impact/Forward-Looking
    ├── 3.1 [Specific content]
    ├── 3.2 [Specific content]
    └── 3.3 [Specific content]
```

### Step 8: Write Final Report

Expand outline into full prose:
- Executive Summary at top
- Reference 4Dimensions in each section
- Concrete Roadmap (Who/What/When)
- Minimum 2000 words
- Authoritative, concise, insightful tone

## Output Format Selection

Based on user request and environment, generate appropriate output:

### In Claude.ai (cloud)

- **Markdown (default)**: Full report in chat
- **Word (.docx)**: Use docx skill for professional formatting
- **PowerPoint (.pptx)**: Use pptx skill for 10-slide executive deck
- **Excel (.xlsx)**: Use xlsx skill for interactive matrix

### In Claude Code (local)

Use `scripts/convert_output.py` for local conversion via pandoc:

```bash
# Generate report as Markdown first, then convert
python scripts/convert_output.py report.md --format docx
python scripts/convert_output.py report.md --format pptx
python scripts/convert_output.py report.md --format pdf
python scripts/convert_output.py report.md --format all
```

**Requirements**: pandoc installed (`brew install pandoc` / `apt install pandoc`)

**Workflow for Claude Code**:
1. Write full report to `report.md`
2. Run conversion script
3. Output files created in same directory

**PowerPoint note**: Pandoc creates slides from headers:
- `# H1` → Title slide
- `## H2` → New slide
- `### H3` and bullets → Slide content

For best pptx results, structure the Markdown with clear H2 sections.

## Ontological Rules (STRICT)

- **Material Cause**: Hardware, resources, technologies. Test benches are Material/Formal composites.
- **Formal Cause**: Software, algorithms, standards, laws, designs. Software is ALWAYS Formal.
- **Efficient Cause**: ONLY humans/organizations. AI/robots are NEVER Efficient causes.
- **Final Cause**: Purposes, missions, strategic goals.

## References

For detailed guidance on specific aspects:
- `references/4dimensions_ontology.md`: Full ontology documentation
- `references/triz_principles.md`: All 40 TRIZ principles with examples
- `references/minto_templates.md`: Minto Pyramid templates

## Scripts

- `scripts/zwicky_engine.py`: Scenario generator (no dependencies)
- `scripts/convert_output.py`: Markdown to docx/pptx/pdf converter (requires pandoc)

## Example Invocation

User: "Create a strategic report on European Space Launch Autonomy for EU policy makers. 
       Focus on 5-year horizon with budget constraints."

Claude: [Executes full pipeline, generates report with specific recommendations]
