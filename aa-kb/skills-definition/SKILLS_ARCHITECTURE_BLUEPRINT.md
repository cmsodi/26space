---
title: Strategic Analysis Architecture Blueprint
subtitle: Modular Analytical Framework for Strategic Research
version: 2.0
date: 2026-01-24
purpose: Consolidation of architectural decisions for implementation
changelog:
  v2.0: Phase 3 orchestrator CREATED (strategic-orchestrator SKILL.md); complete 4-phase user workflow; decision logic implemented; all tiers operational
  v1.9: Phase 2 synthesizers CREATED (4/4 priority); END-TO-END TEST PASSED (space-strategy-synthesizer); 2-step output validated; output folder structure defined
  v1.8: ALL PREREQUISITES RESOLVED (BEFORE PHASE 2, 3, 4 complete); 2-step output generation (outline→approval→full text); outline templates integration; metadata schema defined; Exa MCP integration for citations; tuning parameters (thresholds, triggers, retries)
  v1.7: Phase 1 core analysts COMPLETE (8/8 AGENT.md created); updated implementation structure with phase markers
  v1.6: Hard cap 4 analysts/synthesizer; Option C hybrid architecture (AGENT.md templates); directory structure agents/ + skills/
  v1.5: Reorganized OPEN QUESTIONS by implementation phase (prerequisite ordering)
  v1.4: Flexible analyst structure (Fixed 2-3, Optional Pool 1-3, max 2 activated)
  v1.3: Tier 1 converted to Sub-Agents; enriched methodology descriptions; added sub-agent specifications (output format, timeout, retry, caching)
  v1.2: Added Problem-First user interaction workflow for orchestrator
  v1.1: Integrated tools from Task.md; added Fixed+Optional analyst structure for synthesizers
  v1.0: Initial architecture definition
---

# STRATEGIC ANALYSIS ARCHITECTURE BLUEPRINT
## Modular Analytical Framework for Strategic Research

---

## EXECUTIVE SUMMARY

Three-tier hybrid architecture for strategic analysis workflow:
- **Tier 1 - ANALYSTS (Sub-Agents):** 15 autonomous analytical agents (single methodology experts, parallel execution)
- **Tier 2 - SYNTHESIZERS (Skills):** 7 thematic integration workflows (domain-specific synthesis, coordinates sub-agents)
- **Tier 3 - ORCHESTRATOR (Skill):** Meta-decision layer (selects synthesizer + decides extensions + manages retries)

**Design Philosophy:**
- Modular composition (LEGO blocks principle)
- Fixed pipelines with predefined optional extensions
- Clear separation of concerns
- LLM-based soft logic, not deterministic hard-coding
- Sub-agents for parallelism and isolation (Tier 1)
- Skills for coordination and synthesis (Tier 2/3)

**Analyst Structure:**
- Each analyst runs as **autonomous sub-agent**
- Produces **markdown output with YAML frontmatter metadata**
- Subject to **timeout handling** (managed by synthesizer)
- **Caching** evaluated at execution time based on input stability

**Synthesizer Structure:**
- Each synthesizer has **Fixed Analysts (2-3)**: always called, minimum for triangulation
- Each synthesizer has **Optional Pool (1-2)**: predefined extensions, varies by domain
- **Max 4 total analysts** per execution (hard constraint aligned with parallelism limit)
- **Retry logic** for failed sub-agents (synthesizer or orchestrator decision)

**Target Workflow:**
```
User Problem → [Clarification] → Proposal (Synthesizer + Outline Template)
     ↓
→ USER APPROVAL #1 (confirms approach)
     ↓
Synthesizer → Sub-Agents (parallel) → Integration → OUTLINE
     ↓
→ USER APPROVAL #2 (confirms structure)
     ↓
Synthesizer → FULL TEXT → Markdown Output → [Manual Publishing]
```

**Interaction Model:** Problem-First with On-Demand Clarification (minimal overhead)

---

## TIER 1: ANALYSTS (SUB-AGENTS)
### Autonomous Analytical Agents

Each analyst sub-agent:
- Focuses on ONE methodology (atomic specialization)
- Runs **autonomously** in parallel with other analysts
- Produces **structured markdown output with YAML frontmatter**
- No awareness of other analysts (isolation principle)
- Called by Synthesizers (not directly by users)

### SUB-AGENT SPECIFICATIONS

**Output Format:**
```yaml
---
analyst: [analyst-name]
methodology: [methodology-name]
entity: "[ENTITY analyzed]"
timestamp: [ISO 8601]
status: complete | partial | failed
confidence: high | medium | low
---

# [Analyst Title] Analysis

[Structured markdown content...]
```

**Execution Model:**
- **Timeout:** Configurable per-analyst (default: 60s for complex analysis)
- **Retry Logic:** Synthesizer or Orchestrator decides whether to retry failed agents
- **Caching:** Evaluated at runtime based on input stability and entity consistency
  - Cache HIT: Same entity + same methodology + unchanged context window
  - Cache MISS: New entity, methodology update, or context refresh requested
- **Parallelism:** Multiple analysts can execute simultaneously when launched by synthesizer

**Error Handling:**
- On timeout: Return partial output with `status: partial`
- On failure: Return error context with `status: failed`
- Synthesizer receives all outputs (complete, partial, failed) and integrates accordingly

---

### CONFIRMED ANALYSTS (15)

---

#### 1. Strategic Analysis & Context

##### 1.1 pestle-analyst
**Methodology Family:** PEST, STEEP, STEEPLE, PESTEL

Systematic examination of macro-environmental factors affecting the [ENTITY]:

| Factor | Analysis Focus |
|--------|----------------|
| **P**olitical | Government stability, policies, trade regulations, taxation |
| **E**conomic | Growth rates, inflation, exchange rates, economic cycles |
| **S**ocial | Demographics, cultural trends, education, lifestyle changes |
| **T**echnological | Innovation, R&D activity, automation, technology transfer |
| **L**egal | Legislation, regulatory frameworks, compliance requirements |
| **E**nvironmental | Climate, sustainability, resource availability, ecological constraints |

**Application:** Policy context assessment, regulatory landscape mapping, trend identification
**Output:** Macro-environmental assessment organized by PESTLE factors

---

##### 1.2 morphological-analyst
**Methodology:** Morphological Analysis / Zwicky Box / Morphological Matrix

Systematic exploration of solution/configuration spaces through:
1. **Decomposition:** Break problem into independent parameters
2. **Value Enumeration:** Identify possible values for each parameter
3. **Cross-Consistency Analysis:** Generate combinations systematically
4. **Incompatibility Elimination:** Remove infeasible configurations
5. **Cluster Identification:** Group viable solution clusters

**Application:** Architecture trade-offs, alternative configurations, scenario generation
**Output:** Parameter matrix, viable configuration clusters, trade-off analysis

---

##### 1.3 swot-analyst
**Methodology:** SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats)

Internal-external assessment matrix for the [ENTITY]:

| Dimension | Scope | Focus |
|-----------|-------|-------|
| **Strengths** | Internal | Capabilities and advantages |
| **Weaknesses** | Internal | Limitations and gaps |
| **Opportunities** | External | Favorable conditions |
| **Threats** | External | Challenges and risks |

**Application:** Strategic positioning, capability gap analysis, competitive assessment
**Output:** 2x2 SWOT matrix with actionable implications

---

#### 2. Geopolitical & Power Assessment

##### 2.1 geopolitical-theorist
**Methodology:** Classical Geopolitical Theories + Levels of Analysis (Waltz)

**Classical Theories Applied:**

| Theory | Theorist | Core Thesis |
|--------|----------|-------------|
| **Heartland** | Mackinder | Control of Eurasian center as key to world dominance |
| **Sea Power** | Mahan | Naval supremacy and sea lanes as foundation of national power |
| **Rimland** | Spykman | Coastal periphery control more strategic than Heartland |

**Levels of Analysis (Waltz Framework):**
- **Individual level:** Leader psychology, decision-making patterns
- **State level:** Domestic politics, regime type, institutional structure
- **System level:** International power distribution, anarchy, alliance structures

**Analysis Elements:** Chokepoints, spheres of influence, strategic geography, territorial constraints
**Application:** Geographic constraints analysis, strategic positioning, long-term structural factors
**Output:** Geo-strategic positioning analysis through classical theoretical lenses

---

##### 2.2 power-analyst
**Methodology:** DIME Framework + Hard/Soft/Smart Power (Nye)

**DIME Instruments of National Power:**

| Instrument | Components |
|------------|------------|
| **D**iplomatic | Treaties, alliances, international organizations, negotiations |
| **I**nformational | Propaganda, media, cyber influence, intelligence operations |
| **M**ilitary | Armed forces, defense capabilities, deterrence, force projection |
| **E**conomic | Trade, sanctions, aid, financial instruments |

**Power Typology (Joseph Nye):**
- **Hard Power:** Coercion through military force or economic pressure
- **Soft Power:** Attraction through culture, values, policy legitimacy
- **Smart Power:** Strategic combination optimizing hard and soft power

**Extended Frameworks Referenced:** MIDLIFE, PMESII-PT
**Application:** Capability assessment, influence mechanism analysis, balance of power evaluation
**Output:** Power instruments inventory, influence levers assessment, hard/soft power balance

---

#### 3. Problem-Solving & Innovation

##### 3.1 triz-solver
**Methodology:** TRIZ (Teoriya Resheniya Izobretatelskikh Zadatch)

Systematic innovation methodology applying:

| TRIZ Tool | Function |
|-----------|----------|
| **Contradiction Analysis** | Identify technical and physical contradictions |
| **40 Inventive Principles** | Apply standardized solution patterns |
| **Contradiction Matrix** | Map problem characteristics to applicable principles |
| **Substance-Field Analysis** | Model system interactions (Su-Field) |
| **Trends of Evolution** | Predict technology development trajectories |

**Application:** Technical breakthrough identification, innovation pattern recognition, R&D strategy
**Output:** Contradiction identification, applicable inventive principles, solution directions

---

##### 3.2 first-principles-analyst
**Methodology:** First Principles Thinking

Fundamental reasoning through systematic deconstruction:
1. **Identify Assumptions:** List all beliefs about the problem
2. **Break to Fundamentals:** Reduce to basic, undeniable truths
3. **Rebuild from Foundation:** Construct new understanding from basics
4. **Challenge Orthodoxy:** Question "how things have always been done"

**Application:** Disruptive innovation assessment, challenging conventional wisdom, fundamental feasibility
**Output:** Assumption inventory, first principles identified, reconstructed logic chain

---

#### 4. Foresight & Futures

##### 4.1 scenario-planner
**Methodology:** Scenario Planning

Structured future exploration process:
1. **Driving Forces:** Identify key factors shaping the future
2. **Critical Uncertainties:** Isolate high-impact, high-uncertainty factors
3. **2x2 Matrix Construction:** Two critical uncertainties as axes
4. **Narrative Development:** Rich stories for each quadrant scenario
5. **Wildcard Identification:** Low-probability, high-impact events
6. **Strategy Testing:** Robustness evaluation across all scenarios

**Application:** Long-term planning, strategic hedging, contingency preparation
**Output:** Scenario matrix (4 narratives), driving forces map, strategy robustness assessment

---

##### 4.2 horizon-analyst
**Methodology:** Three Horizons Framework + Futures Wheel + Cross-Impact Analysis + Weak Signals

**Three Horizons Framework:**
| Horizon | Focus | Time Frame |
|---------|-------|------------|
| **H1** | Maintaining and defending current core business/capabilities | Present - 2 years |
| **H2** | Developing emerging opportunities, scaling innovations | 2 - 5 years |
| **H3** | Exploring radical innovation, future options, experiments | 5+ years |

**Supplementary Tools:**
- **Futures Wheel:** Radial impact mapping (event → direct → indirect → tertiary effects)
- **Cross-Impact Analysis:** Matrix of how trends/events influence each other's probability
- **Weak Signals Detection:** Early indicators of emerging changes

**Application:** Strategic foresight, innovation portfolio balance, ripple effect analysis
**Output:** Three-horizon mapping, futures wheel diagram, cross-impact matrix

---

##### 4.3 depth-analyst
**Methodology:** Causal Layered Analysis (CLA)

Deep structural analysis across four layers:

| Layer | Depth | Focus |
|-------|-------|-------|
| **Litany** | Surface | Visible events, headlines, "what happened" |
| **Systems** | Structural | Underlying institutions, policies causing litany |
| **Worldview** | Paradigmatic | Cultural assumptions, mental models, paradigms |
| **Myth/Metaphor** | Deep | Unconscious beliefs, archetypes, foundational narratives |

**Analysis Direction:** Surface → Deep (understanding) OR Deep → Surface (transformation design)
**Application:** Understanding root causes, paradigm shift identification, deep transformation analysis
**Output:** Four-layer CLA decomposition, paradigm identification, transformation levers

---

#### 5. Security & Risk

##### 5.1 red-teamer
**Methodology:** Red Team - Blue Team Analysis

Adversarial thinking methodology:

| Team | Role |
|------|------|
| **Red Team** | Actively challenges plans, identifies weaknesses, simulates adversary |
| **Blue Team** | Defends current strategy, implements countermeasures |
| **Purple Team** | Collaborative improvement integrating both perspectives |

**Techniques Applied:**
- Devil's advocacy (systematic opposition)
- Alternative analysis (competing hypotheses)
- Pre-mortem analysis (imagining failure)
- Assumption stress-testing

**Application:** Security posture testing, strategy validation, assumption challenging
**Output:** Vulnerability map, attack scenarios, recommended countermeasures

---

##### 5.2 threat-analyst
**Methodology:** Threat & Risk Assessment Matrix

Systematic risk quantification framework:

| Assessment Element | Components |
|-------------------|------------|
| **Threat Identification** | State actors, non-state actors, cyber, economic, environmental |
| **Likelihood Assessment** | Probability of occurrence (1-5 scale) |
| **Impact Assessment** | Severity of consequences (1-5 scale) |
| **Vulnerability Analysis** | Exposure and susceptibility factors |
| **Resilience Evaluation** | Recovery and adaptation capability |

**Risk Score Formula:** Likelihood × Impact × Vulnerability Factor

**Distinction from red-teamer:** This is structured quantitative assessment; red-teamer is adversarial simulation
**Application:** Security prioritization, resource allocation, mitigation planning
**Output:** Risk matrix, prioritized threat list, mitigation recommendations

---

#### 6. Multi-Perspective & Creativity

##### 6.1 perspectives-analyst
**Methodology:** Six Thinking Hats (de Bono) + SCAMPER + Forced Analogies

**Six Thinking Hats:**

| Hat | Color | Mode | Focus |
|-----|-------|------|-------|
| **White** | ⚪ | Data | Facts, information (neutral) |
| **Red** | 🔴 | Emotion | Feelings, intuition (no justification) |
| **Black** | ⚫ | Caution | Risks, difficulties (critical) |
| **Yellow** | 🟡 | Benefit | Value, feasibility (optimistic) |
| **Green** | 🟢 | Creativity | Alternatives, new ideas (generative) |
| **Blue** | 🔵 | Process | Organization, meta-thinking (control) |

**SCAMPER Creativity Triggers:**
- **S**ubstitute → **C**ombine → **A**dapt → **M**odify/Magnify/Minimize → **P**ut to other uses → **E**liminate → **R**everse/Rearrange

**Forced Analogies:** Drawing parallels with unrelated domains to spark solutions

**Application:** Comprehensive multi-angle exploration, breaking mental blocks, creative ideation
**Output:** Six-perspective analysis, SCAMPER-generated alternatives, analogical insights

---

#### 7. Ecosystem & Stakeholders

##### 7.1 stakeholder-mapper
**Methodology:** Power-Interest Matrix + Actor Network Analysis + Alliance Mapping

**Power-Interest Matrix:**

|  | Low Interest | High Interest |
|--|--------------|---------------|
| **High Power** | Keep Satisfied | Key Players (Manage Closely) |
| **Low Power** | Monitor | Keep Informed |

**Actor Network Analysis:**
1. Identify all relevant actors
2. Map relationships and influence flows
3. Assess coalition potential
4. Evaluate alliance strength and reliability

**Application:** Governance analysis, political feasibility, partnership strategy
**Output:** Stakeholder matrix, actor network map, coalition assessment

---

##### 7.2 ecosystem-analyst
**Methodology:** Porter's Five Forces + Value Chain Analysis

**Porter's Five Forces:**

| Force | Analysis Focus |
|-------|----------------|
| **Rivalry** | Intensity of competition among existing competitors |
| **New Entrants** | Threat level, barriers to entry |
| **Substitutes** | Alternative solutions threatening the market |
| **Supplier Power** | Upstream leverage and bargaining position |
| **Buyer Power** | Downstream leverage and bargaining position |

**Value Chain Analysis:**
- **Primary Activities:** Inbound logistics → Operations → Outbound logistics → Marketing → Service
- **Support Activities:** Infrastructure, HR, Technology development, Procurement

**Application:** Market dynamics, competitive positioning, supply chain analysis
**Output:** Five forces assessment, value chain decomposition, competitive position map

---

### NAMING CONVENTION
- Singular form: `[method]-analyst` or `[function]-[role]`
- Invocation: Sub-agent launched by synthesizer via Task tool
- Collective term: **analysts** (sub-agents)

### IMPLEMENTATION STRUCTURE
```
/mnt/DATA/26space/.claude/
├── agents/                          # Tier 1: Analyst sub-agents
│   ├── _AGENT_TEMPLATE.md           # ✓ Standard template
│   ├── pestle-analyst/AGENT.md      # ✓ Phase 1
│   ├── morphological-analyst/AGENT.md  # ✓ Phase 1
│   ├── scenario-planner/AGENT.md    # ✓ Phase 1
│   ├── stakeholder-mapper/AGENT.md  # ✓ Phase 1
│   ├── geopolitical-theorist/AGENT.md  # ✓ Phase 1
│   ├── power-analyst/AGENT.md       # ✓ Phase 1
│   ├── first-principles-analyst/AGENT.md  # ✓ Phase 1
│   ├── triz-solver/AGENT.md         # ✓ Phase 1
│   ├── threat-analyst/AGENT.md      # Phase 4
│   ├── red-teamer/AGENT.md          # Phase 4
│   ├── horizon-analyst/AGENT.md     # Phase 4
│   ├── depth-analyst/AGENT.md       # Phase 4
│   ├── perspectives-analyst/AGENT.md  # Phase 4
│   ├── swot-analyst/AGENT.md        # Phase 4
│   └── ecosystem-analyst/AGENT.md   # Phase 4
│
└── skills/                          # Tier 2-3: Synthesizers + Orchestrator
    ├── _SKILL_TEMPLATE.md                      # ✓ Standard template
    ├── _OUTPUT_GENERATION.md                   # ✓ 2-step output prompts
    ├── space-strategy-synthesizer/SKILL.md     # ✓ Phase 2 COMPLETE
    ├── geopolitical-synthesizer/SKILL.md       # ✓ Phase 2 COMPLETE
    ├── tech-innovation-synthesizer/SKILL.md    # ✓ Phase 2 COMPLETE
    ├── security-synthesizer/SKILL.md           # ✓ Phase 2 COMPLETE (needs Phase 4 agents)
    ├── policy-synthesizer/SKILL.md             # Phase 4
    ├── industrial-synthesizer/SKILL.md         # Phase 4
    ├── futures-synthesizer/SKILL.md            # Phase 4
    └── strategic-orchestrator/SKILL.md         # ✓ Phase 3 COMPLETE
```

**Invocation Pattern (Option C - Hybrid):**
```
Synthesizer:
1. Read("/mnt/.../agents/[analyst-name]/AGENT.md")
2. Task(subagent_type: "general-purpose", prompt: "{AGENT.md content}\n\nAnalyze: {entity}")
```

---

## TIER 2: SYNTHESIZERS (SKILLS)
### Thematic Integration Workflows

Each synthesizer skill:
- **Launches sub-agents** (Fixed + Optional analysts) in parallel
- Has **Fixed Analysts (2-3)**: always launched, core methodology for the domain
- Has **Optional Pool (1-2)**: predefined extensions, inversely related to fixed count
- **Max 4 analysts total** per execution (hard constraint aligned with parallelism limit)
- **Collects sub-agent outputs** (including partial/failed status)
- Applies domain-specific **integration logic**
- Produces thematic synthesis, not mechanical aggregation
- **Resolves contradictions** between analyst outputs
- Generates **emergent insights** from combination

### SUB-AGENT COORDINATION

**Launch Pattern:**
```
Synthesizer receives from Orchestrator:
  • Problem context
  • Approved outline template (from outline_templates.md)
  • Active optional analysts (if any)
    ↓
Launch Fixed analysts (parallel execution)
    ↓
[If orchestrator activated] Launch Optional analysts (parallel)
    ↓
Await all sub-agent outputs (with timeout handling)
    ↓
Collect: complete + partial + failed outputs
    ↓
Integration and synthesis (internal)
```

### 2-STEP OUTPUT GENERATION

**Rationale:** Generating a full document (5-20 pages) without user validation risks significant rework. The 2-step process allows course correction before prose expansion.

**Step 1: OUTLINE Generation**
```
Synthesizer produces OUTLINE (populated template):
  • Uses approved template structure (BLUF/Hypothesis/POR/Minto)
  • Fills sections with bullet-point summaries (not prose)
  • Shows key findings, arguments, evidence as concise points
  • Includes placeholder notes: "[Source: analyst-X]", "[Data needed]"
    ↓
→ USER APPROVAL CHECKPOINT
  • User reviews structure and content selection
  • May request: reorder sections, add/remove points, shift emphasis
  • May request: switch to different template
    ↓
[If approved] Proceed to Step 2
[If changes requested] Regenerate outline with modifications
```

**Step 2: FULL TEXT Generation**
```
Synthesizer expands approved outline into final document:
  • Transforms bullets into flowing prose
  • Adds transitions between sections
  • Inserts citations and references
  • Applies professional tone appropriate to audience
  • Formats according to template conventions
    ↓
Return markdown document to Orchestrator
```

**Outline Template Reference:** See `outline_templates.md` for available structures:
- **BLUF** — Bottom Line Up Front (executive, time-critical)
- **Hypothesis-Driven** — Test thesis with evidence (persuasive, rigorous)
- **POR** — Problem-Options-Recommendation (decision-oriented)
- **Minto-Custom** — Pyramid structure (default, scalable)

**Timeout Handling:**
- Each sub-agent has configurable timeout
- On timeout: synthesizer receives partial output
- Synthesizer proceeds with available data, noting gaps

**Retry Decision:**
- Synthesizer MAY retry a failed sub-agent once if:
  - Output is critical for synthesis quality
  - Failure was transient (not structural)
- Orchestrator MAY override retry decisions

**Extension Mechanism:**
The orchestrator decides whether to activate optional analysts based on:
- Problem complexity and scope
- User request for deeper analysis
- Multi-domain overlap detected

### CONFIRMED SYNTHESIZERS (7)

**Summary Table:**

| Synthesizer | Fixed | Optional Pool | Max Opt Activated | Max Total |
|-------------|-------|---------------|-------------------|-----------|
| space-strategy | 3 | 1 | 1 | 4 |
| tech-innovation | 2 | 2 | 2 | 4 |
| geopolitical | 3 | 1 | 1 | 4 |
| security | 3 | 1 | 1 | 4 |
| policy | 2 | 2 | 2 | 4 |
| industrial | 2 | 2 | 2 | 4 |
| futures | 3 | 1 | 1 | 4 |

> **Hard Constraint:** Max 4 analysts per synthesizer execution (aligned with parallelism limit)

---

#### 1. space-strategy-synthesizer
**Thematic Focus:** Space programs, national strategies, international cooperation/competition

**Fixed Analysts (3) - always called:**
1. pestle-analyst (geopolitical context, regulatory environment)
2. morphological-analyst (capability options, architecture trade-offs)
3. stakeholder-mapper (international actors, coalitions)

**Optional Pool (1) - orchestrator activates max 1:**
1. scenario-planner (future evolution paths, OR geopolitical-theorist if geo-strategic focus needed)

**Integration Logic:**
- Geopolitical constraints shape feasible configurations
- Stakeholder dynamics filter viable partnerships
- Output emphasizes strategic autonomy, sovereignty, collaboration options

**Use Cases:**
- National space program analysis
- International cooperation assessment
- Strategic capability gaps

---

#### 2. tech-innovation-synthesizer
**Thematic Focus:** Technology assessment, R&D strategies, innovation pathways

**Fixed Analysts (2) - always called:**
1. first-principles-analyst (fundamental feasibility)
2. triz-solver (technical contradictions, breakthrough patterns)

**Optional Pool (2) - orchestrator activates max 2:**
1. morphological-analyst (solution space exploration)
2. scenario-planner (technology evolution trajectories)

**Integration Logic:**
- First-principles validates technical foundations
- TRIZ identifies innovation opportunities
- [If morphological activated] Maps viable configurations

**Use Cases:**
- New technology evaluation
- R&D priority setting
- Disruptive innovation assessment

---

#### 3. geopolitical-synthesizer
**Thematic Focus:** Security, conflicts, power dynamics, strategic competition

**Fixed Analysts (3) - always called:**
1. geopolitical-theorist (classical frameworks, geographic constraints)
2. power-analyst (DIME, hard/soft power assessment)
3. stakeholder-mapper (power dynamics, alliances)

**Optional Pool (1) - orchestrator activates max 1:**
1. scenario-planner (conflict/cooperation scenarios, OR red-teamer if adversarial stress-testing needed)

**Integration Logic:**
- Classical theories provide structural framework
- Power assessment reveals capabilities and leverage
- Stakeholder analysis maps alliance dynamics

**Use Cases:**
- Strategic competition analysis
- Balance of power assessment
- Dual-use technology implications

---

#### 4. security-synthesizer
**Thematic Focus:** Threat assessment, vulnerability analysis, security posture

**Fixed Analysts (3) - always called:**
1. threat-analyst (risk matrix, likelihood/impact)
2. red-teamer (adversarial thinking, attack scenarios)
3. stakeholder-mapper (threat actors, defensive coalitions)

**Optional Pool (1) - orchestrator activates max 1:**
1. scenario-planner (threat evolution scenarios, OR power-analyst if defensive capabilities focus needed)

**Integration Logic:**
- Threat analyst provides systematic risk mapping
- Red-teamer stress-tests defenses
- Stakeholder analysis identifies threat actors and allies

**Use Cases:**
- Security posture assessment
- Vulnerability analysis
- Threat modeling and countermeasures

---

#### 5. policy-synthesizer
**Thematic Focus:** Regulation, governance, institutional analysis, policy impact

**Fixed Analysts (2) - always called:**
1. pestle-analyst (regulatory environment)
2. stakeholder-mapper (institutional actors, interests)

**Optional Pool (2) - orchestrator activates max 2:**
1. swot-analyst (policy strengths/weaknesses)
2. scenario-planner (policy evolution paths)

**Integration Logic:**
- PESTLE provides legal/political context
- Stakeholder analysis reveals implementation feasibility
- [If SWOT activated] Assesses policy robustness

**Use Cases:**
- Regulatory impact assessment
- Policy effectiveness evaluation
- Governance reform analysis

---

#### 6. industrial-synthesizer
**Thematic Focus:** Markets, competition, supply chains, business ecosystems

**Fixed Analysts (2) - always called:**
1. ecosystem-analyst (Porter's forces, value chains)
2. stakeholder-mapper (industry actors, consolidation dynamics)

**Optional Pool (2) - orchestrator activates max 2:**
1. morphological-analyst (business model options)
2. scenario-planner (market evolution trajectories)

**Integration Logic:**
- Porter framework maps competitive landscape
- Stakeholder analysis shows M&A/partnership opportunities
- [If morphological activated] Explores business model variations

**Use Cases:**
- Competitive landscape assessment
- Market entry strategies
- Supply chain resilience analysis

---

#### 7. futures-synthesizer
**Thematic Focus:** Long-term foresight (10+ years), paradigm shifts, transformative change

**Fixed Analysts (3) - always called:**
1. horizon-analyst (Three Horizons, Futures Wheel, weak signals)
2. depth-analyst (CLA: worldview/metaphor shifts)
3. scenario-planner (long-range narrative scenarios)

**Optional Pool (1) - orchestrator activates max 1:**
1. perspectives-analyst (Six Hats divergent exploration, OR first-principles-analyst if paradigm questioning needed)

**Integration Logic:**
- Horizon analysis maps multi-timeframe evolution
- CLA explores deep structural/paradigm changes
- Scenarios create rich future narratives

**Use Cases:**
- Vision 2040+ exercises
- Paradigm shift anticipation
- Strategic foresight programs

---

### NAMING CONVENTION
- Structure: `[domain]-synthesizer`
- Implementation: Claude Code Skill (`/mnt/DATA/26space/.claude/skills/[name]/SKILL.md`)
- Collective term: **synthesizers (skills)**

---

## TIER 3: ORCHESTRATOR (SKILL)
### Meta-Decision Layer

**Name:** `strategic-orchestrator`
**Implementation:** Claude Code Skill

**Purpose:**
1. Select appropriate synthesizer based on user problem characteristics
2. Decide whether to activate optional analysts for extended analysis
3. **Manage sub-agent execution** (timeouts, retries, caching strategy)
4. **Handle synthesizer failures** and coordinate recovery

---

### USER INTERACTION WORKFLOW (Problem-First)

**Design Principle:** Minimal overhead, questions only when they add value

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: PROBLEM                                               │
│  User describes problem/question freely (no imposed structure)  │
│  "Analizza la competizione sino-americana nel settore spaziale" │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Orchestrator parses]
                              ↓
              ┌───────────────┴───────────────┐
              │                               │
        Problem CLEAR                   Problem AMBIGUOUS
        (score > 0.7)                   (multiple 0.4-0.6)
              │                               │
              ↓                               ↓
┌─────────────────────────┐   ┌─────────────────────────────────┐
│  SKIP to PHASE 3        │   │  PHASE 2: CLARIFICATION         │
│                         │   │  1-2 targeted questions MAX     │
│                         │   │                                 │
│                         │   │  Examples:                      │
│                         │   │  • "Focus on security threats   │
│                         │   │    or industrial competition?"  │
│                         │   │  • "Short-term (2-3y) or        │
│                         │   │    long-term (10+y) horizon?"   │
│                         │   │  • "Focused analysis or         │
│                         │   │    comprehensive deep-dive?"    │
└─────────────────────────┘   └─────────────────────────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: PROPOSAL                                              │
│                                                                 │
│  Orchestrator presents:                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ A. SYNTHESIZER                                             │ │
│  │ RECOMMENDED: [geopolitical-synthesizer]                    │ │
│  │ • Fixed: geopolitical-theorist, power-analyst,             │ │
│  │          stakeholder-mapper                                │ │
│  │ • Extension: +scenario-planner (long-term projection)      │ │
│  │                                                            │ │
│  │ WHY: Your question focuses on strategic competition        │ │
│  │ between state actors, with power dynamics and alliance     │ │
│  │ implications.                                              │ │
│  │                                                            │ │
│  │ ALTERNATIVE: [space-strategy-synthesizer] if you want      │ │
│  │ to focus specifically on space program capabilities        │ │
│  │ rather than broader geopolitical dynamics.                 │ │
│  │                                                            │ │
│  │ ────────────────────────────────────────────────────────── │ │
│  │                                                            │ │
│  │ B. OUTLINE TEMPLATE (see: outline_templates.md)            │ │
│  │ RECOMMENDED: [Minto-Custom] (default)                      │ │
│  │ • 3 Key Lines, 3 Arguments each, 3 bullet points each      │ │
│  │ • Best for: comprehensive strategic analysis, scalable     │ │
│  │                                                            │ │
│  │ ALTERNATIVES:                                              │ │
│  │ • [BLUF] — if time-critical, executive briefing            │ │
│  │ • [Hypothesis-Driven] — if testing controversial thesis    │ │
│  │ • [POR] — if decision required among discrete options      │ │
│  │                                                            │ │
│  │ ────────────────────────────────────────────────────────── │ │
│  │                                                            │ │
│  │ C. WEB SEARCH (Exa)                                        │ │
│  │ RECOMMENDED: Enabled for pestle-analyst, scenario-planner  │ │
│  │ • Semantic search for: economic data, regulations, trends  │ │
│  │ • Citations will include real URLs                         │ │
│  │                                                            │ │
│  │ [ ] Disable web search (use only provided context/model)   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  → User approves or modifies (Synthesizer + Outline + Search)   │
│  → Only after approval: Orchestrator launches Synthesizer       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: EXECUTION                                             │
│  Orchestrator → Synthesizer (with approved template)            │
│                                                                 │
│  Sub-Agent Execution:                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Fixed Analysts ──┬── analyst-1 ──┐                      │   │
│  │                  ├── analyst-2 ──┼── await outputs ──┐  │   │
│  │                  └── analyst-3 ──┘                   │  │   │
│  │ Optional (if active) ──┬── analyst-4 ──┤ (parallel)  │  │   │
│  │                        └── analyst-5 ──┘             │  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                  │
│  Synthesizer 2-Step Output:                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ STEP 1: Generate OUTLINE (populated template)           │   │
│  │         • Section headings from approved template       │   │
│  │         • Key points as bullet summaries                │   │
│  │         • No full prose yet                             │   │
│  │                         ↓                               │   │
│  │         → USER APPROVAL (Checkpoint #2)                 │   │
│  │         → User may request: reorder, add/remove section │   │
│  │                         ↓                               │   │
│  │ STEP 2: Generate FULL TEXT                              │   │
│  │         • Expand bullets into prose                     │   │
│  │         • Add transitions, citations, formatting        │   │
│  │         • Final markdown document                       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

**Clarification Triggers (when to ask):**
- Ambiguous domain (geopolitical vs security vs industrial)
- Unclear time horizon (affects scenario-planner activation)
- Multi-domain overlap without clear priority
- Missing entity/actor specification

**Clarification Skip (proceed directly):**
- Clear single-domain problem
- Explicit depth request ("analisi approfondita", "quick overview")
- Well-specified entity and scope

---

### INPUT/OUTPUT

**Input:**
- User question/problem statement (free-form)
- Optional: desired output format, target audience, depth level
- Optional: time/resource constraints

**Output:**
- Markdown document (complete but unpublished)
- Structured, ready for human review
- Not yet formatted for Hugo/docx/pptx

**Sub-Agent Management Outputs:**
- Execution log (which sub-agents ran, status, timing)
- Cache status report (hits/misses)
- Partial output handling notes (if any sub-agent timed out)

---

### DECISION LOGIC: Soft Probabilistic (NOT deterministic Zwicky)

```
DECISION FRAMEWORK:

1. Parse user problem
   - Extract domain keywords
   - Identify problem characteristics
   - Assess scope and time horizon
   - Evaluate complexity level (simple/standard/deep)

2. Score each synthesizer on relevance (0.0-1.0):

   space-strategy-synthesizer:
   → keywords: [program, capability, autonomy, mission, launcher, satellite, collaboration, space agency]

   tech-innovation-synthesizer:
   → keywords: [breakthrough, R&D, feasibility, technology, innovation, disruption, technical]

   geopolitical-synthesizer:
   → keywords: [sovereignty, power, influence, competition, alliance, balance, geopolitics]

   security-synthesizer:
   → keywords: [threat, vulnerability, attack, defense, risk, security, cyber, resilience]

   policy-synthesizer:
   → keywords: [governance, regulation, compliance, legislation, mandate, institutional, reform]

   industrial-synthesizer:
   → keywords: [market, supply chain, competition, consolidation, business model, ecosystem, industry]

   futures-synthesizer:
   → keywords: [long-term, 2040, paradigm, vision, transformation, futures, horizon]

3. Synthesizer Selection Rules:

   IF clear winner (score > 0.7):
   → Use that synthesizer

   IF ambiguous (multiple scores 0.4-0.6):
   → ASK USER: "I see aspects X and Y. Which should I prioritize?"

   IF multi-domain (2+ scores > 0.6):
   → SUGGEST: "This is multi-domain. I recommend [Synthesizer-A] focused on [aspect],
                OR we could run parallel analyses"

   IF no good match (all scores < 0.3):
   → FALLBACK: Use space-strategy-synthesizer (most generic)
              OR call individual analysts directly

4. Extension Decision (Optional Analysts):

   ACTIVATE optional analysts when:
   - Problem explicitly requests "deep analysis" or "comprehensive"
   - Multiple domains overlap significantly
   - Time horizon is long-term (5+ years)
   - User asks for scenarios or future projections
   - Security/risk aspects are mentioned alongside main domain

   DEFAULT: Run with fixed analysts only (faster, focused)
   EXTENDED: Add 1-2 optional analysts (deeper, broader)

5. Orchestrator MUST ALWAYS decide
   - Find best available compromise
   - Explain reasoning transparently
   - Never refuse due to "imperfect match"

6. Sub-Agent Management:

   TIMEOUT CONFIGURATION:
   - Default: 60 seconds per analyst
   - Complex analysts (scenario-planner, horizon-analyst): 90 seconds
   - Simple analysts (swot-analyst): 30 seconds

   RETRY STRATEGY:
   - Max 1 retry per sub-agent per execution
   - Retry only if: failure was transient AND output is critical
   - Skip retry if: structural failure OR time budget exhausted

   CACHING EVALUATION:
   - Check cache key: [analyst-name]:[entity-hash]:[context-hash]
   - Cache TTL: Session-scoped (invalidate on new session)
   - Force refresh: When user requests "updated analysis"
```

**Template Output Structure:**
Defined within orchestrator skill, includes:
- Executive summary
- Methodology used (transparent about which synthesizer/analysts activated)
- Main findings organized by theme
- Scenario analysis (if optional scenario-planner activated)
- Recommendations / Implications
- Limitations / Uncertainties

**Relationship to Publishing:**
- Orchestrator stops at markdown generation
- User reviews output
- User manually triggers publishing tools (docx, pptx, Hugo)
- Clear handoff point prevents scope creep

---

## ARCHITECTURAL DECISIONS

### KEY CHOICES MADE

**1. Hybrid Architecture: Sub-Agents (Tier 1) + Skills (Tier 2/3)**
- **Why:** Optimal separation of concerns
- **Tier 1 as Sub-Agents:** Enables parallel execution, isolation, independent timeouts, caching
- **Tier 2/3 as Skills:** Coordination logic benefits from full context awareness
- **Rationale:** Analysts are stateless, methodology-focused → perfect for sub-agent isolation

**2. Flexible Fixed + Optional Structure with Hard Cap**
- **Why:** Balances simplicity with domain-specific flexibility while respecting parallelism limits
- **Structure:** Each synthesizer has Fixed (2-3) + Optional Pool (1-2), **max 4 total**
- **Fixed analysts (2-3):** Always launched, minimum 2 for triangulation
- **Optional Pool (1-2):** Predefined, varies inversely with fixed count
- **Hard cap:** Max 4 analysts per synthesizer execution (aligned with parallelism limit)
- **Rationale:** 3 fixed → 1 optional; 2 fixed → max 2 optional
- **Override mechanism:** None. If user needs custom combination → call analysts manually

**3. LLM Soft Logic over Deterministic Hard-Coding**
- **Why:** Handles ambiguity, multi-domain problems, evolves with prompt updates
- **Rejected:** Zwicky-style decision matrices (would rigidify orchestrator)
- **Exception:** Zwicky methodology CAN be used INSIDE analysts/synthesizers for their specific tasks

**4. Orchestrator Controls Extension Depth + Sub-Agent Management**
- **Why:** Single decision point for analysis scope and execution management
- **Default:** Fixed analysts only (focused, efficient)
- **Extended:** + Optional analysts (deeper, broader)
- **Triggers:** Complexity, multi-domain, long-term horizon, explicit user request
- **Sub-Agent Management:** Timeout configuration, retry decisions, caching strategy

**5. Sub-Agent Output Standardization**
- **Why:** Consistent interface for synthesizer integration
- **Format:** Markdown with YAML frontmatter (analyst, methodology, entity, status, confidence)
- **Status Types:** complete | partial | failed
- **Benefit:** Synthesizer can gracefully handle incomplete outputs

**6. Manual Publishing Handoff**
- **Why:** User must verify analytical quality before formatting
- **Separation:** Analysis ≠ Presentation
- **Next phase:** Integration with existing docx/pptx/Hugo skills

**7. Analysts as Specialists, Not Generalists**
- **Why:** Each sub-agent does ONE thing well
- **Granularity:** 15 analysts (expanded from original 10-12 to cover geopolitical/power/threat domains)
- **Naming:** Technical precision over marketing appeal

**8. Synthesizers as Interpreters, Not Aggregators**
- **Why:** Generate emergent insights, resolve contradictions
- **Not:** Copy-paste analyst outputs
- **Role:** Coordinate sub-agents, integrate outputs, produce synthesis

### NAMING CONVENTIONS

| Level | Type | Pattern | Example | Collective Term |
|-------|------|---------|---------|-----------------|
| Tier 1 | Sub-Agent | `[method]-analyst` or `[function]-[role]` | `pestle-analyst`, `red-teamer` | analysts (sub-agents) |
| Tier 2 | Skill | `[domain]-synthesizer` | `geopolitical-synthesizer` | synthesizers (skills) |
| Tier 3 | Skill | `strategic-orchestrator` | N/A (single skill) | orchestrator (skill) |

### SCOPE BOUNDARIES

**IN SCOPE (this architecture):**
- Analytical methodology
- Content synthesis
- Strategic insight generation
- Markdown output

**OUT OF SCOPE (Phase 4 - separate):**
- Document formatting (docx, pptx)
- Web publishing (Hugo)
- Visual design
- Citation management
- Final editing/proofreading

---

## IMPLEMENTATION ROADMAP

### PHASE 1: Sub-Agent Infrastructure + Core Analysts
**Build sub-agent execution framework:**
- Sub-agent launcher (parallel execution)
- Output collector (with timeout handling)
- Status aggregator (complete/partial/failed)
- Caching infrastructure (key generation, TTL management)

**Build first 8 essential analyst sub-agents:**
1. pestle-analyst
2. morphological-analyst
3. scenario-planner
4. stakeholder-mapper
5. geopolitical-theorist
6. power-analyst
7. first-principles-analyst
8. triz-solver

**Validation:** Test each sub-agent individually; verify output format compliance

---

### PHASE 2: Priority Synthesizers (Skills)
**Build 4 most-used synthesizer skills:**
1. space-strategy-synthesizer (highest frequency use)
2. geopolitical-synthesizer (security/power focus)
3. tech-innovation-synthesizer (technical assessment)
4. security-synthesizer (threat/vulnerability focus)

**Synthesizer capabilities:**
- Launch and coordinate sub-agents
- Handle timeout and partial outputs
- Integrate analyst outputs into synthesis
- Resolve contradictions between outputs

**Validation:** Test pipelines end-to-end with Fixed analysts only

---

### PHASE 3: Orchestrator (Skill)
**Build decision engine skill:**
- Implement soft probabilistic logic (synthesizer selection)
- Extension decision logic (optional analyst activation)
- User interaction prompts (Problem-First workflow)
- Sub-agent management (timeout config, retry strategy, caching decisions)
- Template markdown output

**Validation:** Test on ambiguous/multi-domain problems, verify extension triggers, test retry logic

---

### PHASE 4: Completion & Polish
**Remaining analyst sub-agents:**
- threat-analyst
- red-teamer
- horizon-analyst
- depth-analyst
- perspectives-analyst
- swot-analyst
- ecosystem-analyst

**Remaining synthesizer skills:**
- policy-synthesizer
- industrial-synthesizer
- futures-synthesizer

**Integration:**
- Connect to existing publishing skills
- Documentation
- Usage examples
- Test optional analyst extension paths
- Performance tuning (timeout optimization, cache hit ratio)

---

## OPEN QUESTIONS (Ordered by Implementation Phase)

> **Note:** Clarify these questions BEFORE starting the corresponding phase.
> In future conversations, begin from the relevant phase's questions.

---

### BEFORE PHASE 1: Sub-Agent Infrastructure ✓ RESOLVED
*Prerequisite for building sub-agent execution framework and first analysts*

1. ✓ **Sub-agent invocation method:** Claude Code Task tool (confirmed)
2. ✓ **Output collection mechanism:** Parallel with await, Task tool `run_in_background: true`
3. ✓ **Caching implementation:** Deferred to later phase (not Phase 1 scope)
4. ✓ **Parallelism limits:** Max 4 concurrent sub-agents per execution

**Implementation Approach (Option C - Hybrid):**
- AGENT.md files as methodology templates in `/mnt/DATA/26space/.claude/agents/`
- SKILL.md files for synthesizers/orchestrator in `/mnt/DATA/26space/.claude/skills/`
- Task tool reads AGENT.md, passes content as prompt to sub-agent
- True isolation maintained: each sub-agent receives full methodology in prompt

---

### BEFORE PHASE 2: Synthesizers
*Prerequisite for building synthesizer skills*

5. ~~**Standard sections** for output document (markdown template)~~ ✓ RESOLVED
   → See `outline_templates.md` — 4 templates available (BLUF, Hypothesis-Driven, POR, Minto-Custom)
   → Orchestrator proposes template in PHASE 3: PROPOSAL
   → Synthesizer uses 2-step output: outline approval → full text
6. ~~**Metadata tags** for downstream publishing~~ ✓ RESOLVED
   ```yaml
   # Document identification
   title: "..."
   description: "..."
   date: 2025-01-23
   version: "1.0"

   # Methodological traceability
   synthesizer: "geopolitical-synthesizer"
   analysts_fixed: ["power-analyst", "stakeholder-mapper", "geopolitical-theorist"]
   analysts_optional: ["scenario-planner"]  # empty if none activated
   outline_template: "Minto-Custom"  # BLUF | Hypothesis-Driven | POR | Minto-Custom

   # External sources
   web_search_enabled: true  # Exa search active for eligible analysts
   context_documents: ["notebooklm_report.md"]  # user-provided sources (optional)

   # Document status
   status: "final"  # outline_draft | outline_approved | final
   language: "it"   # it | en
   ```
   → Framework names derived from analysts via lookup table (1:1 mapping)
   → Hugo frontmatter defined separately in publishing phase
7. ~~**Citation/reference handling** (especially for PESTLE, scenarios)~~ ✓ RESOLVED

   **Hybrid 2-Level Approach:**

   | Level | Source | When | Citations |
   |-------|--------|------|-----------|
   | **1. Context Injection** | User provides NotebookLM/DeepResearch report | Deep analysis, many sources needed | References to report + original sources |
   | **2. On-Demand Exa Search** | Analyst calls Exa API (semantic search) | Specific data needed (economic, regulatory) | Real URLs, standard format |
   | **3. No external source** | Model knowledge only | Conceptual/methodological analysis | Theoretical references ("according to Porter...") |

   **Exa-enabled analysts:**
   - ✓ `pestle-analyst` (economic data, regulations, trends)
   - ✓ `scenario-planner` (forecasts, projections)
   - ✓ `horizon-analyst` (emerging technologies)
   - ✗ `morphological-analyst` (logical structures, no external data)
   - ✗ `swot-analyst` (synthesis, not research)

   **Authorization:** Orchestrator proposes in PHASE 3: PROPOSAL (section C. WEB SEARCH), user approves.

   **Citation format (when Exa active):**
   ```markdown
   ## References
   [1] "Title" - Source, Year
       https://url...
   ```

   **Implementation:** MCP server `exa-labs/exa-mcp-server` (recommended)
   → GitHub: https://github.com/exa-labs/exa-mcp-server
   → Requires: Exa API key (free tier available)

8. ~~**Methodology transparency** (how to document which sub-agents were activated?)~~ ✓ RESOLVED
   → Covered by `analysts_fixed` + `analysts_optional` in metadata above

---

### BEFORE PHASE 3: Orchestrator
*Prerequisite for building orchestrator decision logic*

9. ~~**Exact prompt structure** for decision logic~~ ✓ RESOLVED

   See **ORCHESTRATOR DECISION PROMPT** below:

   <details>
   <summary>ORCHESTRATOR DECISION PROMPT (click to expand)</summary>

   ```markdown
   # STRATEGIC ORCHESTRATOR - DECISION PROMPT

   You are the strategic orchestrator. Analyze the user's problem and produce a PROPOSAL for approval.

   ---

   ## INPUT

   **User Problem:**
   """
   {user_problem}
   """

   **Context Documents (if provided):**
   {context_documents_list or "None"}

   ---

   ## TASK: Produce a PROPOSAL with 3 decisions

   ### DECISION A: SYNTHESIZER SELECTION

   **Available Synthesizers:**
   1. `space-strategy-synthesizer` — space programs, national strategies, international cooperation
      Keywords: program, capability, autonomy, mission, launcher, satellite, space agency

   2. `tech-innovation-synthesizer` — technology assessment, R&D strategy, disruption analysis
      Keywords: breakthrough, R&D, feasibility, innovation, disruption, technical

   3. `geopolitical-synthesizer` — power dynamics, alliances, strategic competition
      Keywords: sovereignty, power, influence, competition, alliance, balance

   4. `security-synthesizer` — threats, vulnerabilities, defense, resilience
      Keywords: threat, vulnerability, attack, defense, risk, cyber

   5. `policy-synthesizer` — governance, regulation, institutional analysis
      Keywords: governance, regulation, compliance, legislation, institutional

   6. `industrial-synthesizer` — markets, supply chains, business ecosystems
      Keywords: market, supply chain, consolidation, business model, ecosystem

   7. `futures-synthesizer` — long-term scenarios, paradigm shifts, horizon scanning
      Keywords: long-term, 2040, paradigm, transformation, futures

   **Selection Rules:**
   - Score each 0.0-1.0 based on keyword match + problem fit
   - IF one score > 0.7 → SELECT (high confidence)
   - IF multiple 0.4-0.6 → ASK clarification ("Focus on X or Y?")
   - IF 2+ scores > 0.6 → SUGGEST primary, note alternative
   - IF all < 0.3 → FALLBACK to space-strategy-synthesizer

   **Your Analysis:**
   - Primary domain detected: ___
   - Scores: [list top 3 with scores]
   - Selected: `{synthesizer}`
   - Confidence: {high | medium-needs-clarification | low-fallback}
   - Extensions: {list optional analysts to activate, or "none"}

   ---

   ### DECISION B: OUTLINE TEMPLATE

   **Available Templates** (see outline_templates.md):

   | Template | Use When | Length |
   |----------|----------|--------|
   | BLUF | Executive briefing, time-critical, action-oriented | 1-2 pages |
   | Hypothesis-Driven | Testing controversial thesis, persuading skeptics | 3-6 pages |
   | POR | Decision required among discrete options | 3-5 pages |
   | Minto-Custom | Comprehensive strategic analysis (DEFAULT) | 2-20 pages |

   **Selection Criteria:**
   - Audience: {executive | technical | policy | mixed}
   - Purpose: {inform | persuade | decide | explore}
   - Depth: {quick | standard | comprehensive}

   **Your Selection:**
   - Template: `{template}`
   - Rationale: {1 sentence}

   ---

   ### DECISION C: WEB SEARCH (Exa)

   **Enable IF:**
   - Problem requires current data (2024-2025 events, statistics, regulations)
   - Selected synthesizer includes Exa-eligible analysts:
     - ✓ pestle-analyst
     - ✓ scenario-planner
     - ✓ horizon-analyst

   **Your Decision:**
   - Web Search: {enabled | disabled}
   - Analysts with search: {list or "n/a"}
   - Search focus: {economic data | regulatory updates | technology trends | "n/a"}

   ---

   ## OUTPUT FORMAT

   Present the PROPOSAL to the user:

   ## PROPOSAL

   ### A. SYNTHESIZER
   **Recommended:** [{synthesizer}]
   - Fixed analysts: [list]
   - Optional extensions: [list or "none"]

   **Why:** [2-3 sentences explaining the fit]

   **Alternative:** [{alternative-synthesizer}] if you prefer to focus on [aspect]

   ---

   ### B. OUTLINE TEMPLATE
   **Recommended:** [{template}]
   - Structure: [brief description]
   - Expected length: [pages]

   **Why:** [1 sentence]

   **Alternatives:** [list other options with 1-line description]

   ---

   ### C. WEB SEARCH
   **Recommended:** [{enabled/disabled}]
   - Analysts with search: [list or "n/a"]

   **Why:** [1 sentence]

   ---

   → Please confirm or modify this proposal.
   ```

   </details>

10. ~~**Threshold tuning** for score-based selection~~ ✓ RESOLVED

    | Scenario | Threshold | Action |
    |----------|-----------|--------|
    | Clear winner | > 0.7 | Select directly |
    | Ambiguous | 0.4 - 0.7 (2+ synth) | Ask clarification |
    | Multi-domain | > 0.6 (2+ synth) | Suggest primary + alternative |
    | No match | < 0.3 (all) | Fallback to space-strategy |

    *Tunable with experience: raise to 0.8 if too many false positives, lower to 0.6 if too many clarifications*

11. ~~**Extension trigger refinement**~~ ✓ RESOLVED

    **Triggers that activate optional analysts:**
    - Explicit depth request ("analisi approfondita", "comprehensive", "deep dive")
    - Long-term horizon (5+ years, "2030", "lungo termine")
    - Multi-domain overlap (2+ synthesizers score > 0.5)
    - Scenario/projection request ("scenari", "what if")
    - Security + another domain mentioned together

    **Trigger → Extension mapping:**
    | Trigger | Preferred extension |
    |---------|---------------------|
    | Long-term horizon | scenario-planner |
    | Security cross-domain | threat-analyst, red-teamer |
    | Technology disruption | horizon-analyst |
    | Multi-stakeholder | perspectives-analyst |

    *Default: fixed analysts only. Extensions add depth but increase execution time.*

12. ~~**Retry decision criteria**~~ ✓ RESOLVED

    ```
    MAX_RETRIES = 1 per agent per execution

    RETRY IF:
      failure_type IN [timeout, partial_output, error]
      AND retry_count < MAX_RETRIES
      AND agent is fixed (not optional)

    DO NOT RETRY IF:
      failure_type = structural
      OR agent is optional (proceed without)

    ON FINAL FAILURE:
      Synthesizer proceeds with available outputs
      Notes gap: "[agent-X] output unavailable"
    ```

    **Timeout values:**
    | Agent type | Timeout | Retry timeout |
    |------------|---------|---------------|
    | Simple (swot-analyst) | 30s | 45s |
    | Standard (most) | 60s | 90s |
    | Complex (scenario-planner, horizon) | 90s | 120s |

    *Tunable: set MAX_RETRIES=0 for faster graceful degradation, =2 if network unstable*

---

### BEFORE/DURING PHASE 4: Completion & Integration
*Can be refined iteratively during final phase*

**Publishing Integration:**
13. **Handoff mechanism** to docx/pptx/Hugo skills — OUT OF SCOPE (separate phase)
14. ~~**Automated vs manual formatting** decisions~~ ✓ RESOLVED
    → Markdown già formattato (opinionated): headings, tables, callouts pre-applied
    → User does minor tweaks only
15. ~~**Style presets** for different audiences~~ ✓ RESOLVED
    → Single "professional" style (executives, policy-makers, analysts)
    → Variation handled by: outline template (BLUF/Minto/etc.) + depth level
    → No separate presets needed for this homogeneous target audience

**Edge Cases:**
16. ~~**User bypasses orchestrator**~~ ✓ RESOLVED
    → User can override ANY decision in PHASE 3: PROPOSAL
    → Synthesizer, template, extensions, web search — all modifiable
    → Orchestrator proposes, user disposes

17. ~~**Contradictory outputs** from analysts~~ ✓ RESOLVED
    → Synthesizer presents contradictions as "diverse perspectives"
    → Does NOT force artificial reconciliation
    → Example: "Analyst A suggests X due to [rationale], while Analyst B argues Y because [rationale]"

18. ~~**Extension overhead**~~ ✓ RESOLVED
    → Extensions add ~1-2 min per analyst
    → PROPOSAL notes if extensions active: "Extended analysis (longer execution)"
    → Cost threshold: < $5/article acceptable, no micro-optimization needed

19. ~~**All sub-agents fail**~~ ✓ RESOLVED
    → Process ABORTS (no partial output without analyst data)
    → User receives detailed diagnostic:
      - Which agents failed
      - Error type per agent (timeout, error, structural)
      - Timestamp of failures
      - Suggested action (retry, simplify scope, check connectivity)

---

## CONSTRAINTS & DESIGN PRINCIPLES

### Technical Constraints
- LLM context window limits (manage token budget)
- Sub-agent execution overhead (parallel launch cost)
- Network/API call efficiency (sub-agents multiply API calls)
- Timeout management (balance completeness vs responsiveness)

### User Experience Principles
- **Transparency:** Always explain which methods are being used
- **Flexibility:** Allow override when needed (but don't complicate default path)
- **Quality over speed:** Better to ask clarifying questions than produce irrelevant analysis
- **Professional tone:** Output suitable for executives/policymakers

### Maintenance Principles
- **Modularity:** Update one skill without breaking others
- **Documentation:** Each skill documents its methodology clearly
- **Versioning:** Track skill updates (especially for reproducibility)
- **Testability:** Each component testable in isolation

---

## REFERENCE INFORMATION

### User Profile (Context)
- **Background:** Electrical engineer, former ASI/CNR executive, classical studies
- **Expertise:** Space policy, strategy, security (senior generalist, not hyper-specialist)
- **Methodology:** Integrates ancient philosophy with engineering frameworks
- **Independence:** No institutional bias, rigorous fact-checking
- **Target audience:** Professionals, executives, policymakers in space sector
- **Domain coverage:** Strategic-organizational (primary), technical-scientific (secondary)
- **Technical skills:** Python/JavaScript (sufficient to follow LLM instructions)

### Analytical Frameworks (User-familiar)
Categories user references regularly:
- Macro-Environmental: PESTLE, Geopolitical Theories, CLA
- Geopolitical/Strategic Power: Risk Mapping, Sphere of Influence, Chokepoints
- Industrial/Competitive: Porter's Five Forces, Value Chain, Ecosystem Mapping
- Technology/Innovation: TRLs, S-Curve, Horizon Scanning
- Policy/Governance: Regulatory Impact, Policy Cycle, Stakeholder Power
- Security/Defense/Risk: Threat Modeling, Scenario-Based Risk, Red Teaming
- Futures/Foresight: Scenario Planning, Delphi, Backcasting
- Economic/Financial: Cost-Benefit, TCO, Real Options
- Organizational: IAD Framework, Design Models, Principal-Agent
- Structured Thinking: First Principles, MECE, Systems Thinking, Design Thinking, TRIZ

### Existing Skills (Available)
- **zwicky-strategic-analyst:** Current monolithic skill (DEPRECATED - being decomposed into this architecture)
- **docx:** Document creation/editing (publishing phase integration)
- **pptx:** Presentation creation (publishing phase integration)
- **pdf:** PDF manipulation (publishing phase integration)
- **xlsx:** Spreadsheet work
- **jsvis-map:** Interactive network visualization
- **product-self-knowledge:** Anthropic product info
- **frontend-design:** Web UI design

---

## SUCCESS CRITERIA

### For Implementation
✓ Each analyst sub-agent produces high-quality output in its domain
✓ Sub-agent outputs conform to standardized format (YAML frontmatter + markdown)
✓ Parallel execution improves throughput without quality loss
✓ Timeout handling gracefully degrades to partial outputs
✓ Synthesizers generate insights beyond simple aggregation
✓ Orchestrator selects correct synthesizer >85% of time
✓ Extension decisions (optional analysts) add value when activated
✓ Retry logic recovers from transient failures effectively
✓ Markdown output requires minimal editing before publishing
✓ System handles ambiguous/multi-domain problems gracefully

### For User Adoption
✓ Faster "brainstorming → analysis → publication" cycle
✓ Consistent quality across different problem types
✓ Transparent methodology (user understands which sub-agents activated)
✓ Flexible depth: quick focused analysis OR extended deep-dive
✓ Professional output suitable for target audience (executives, policymakers)
✓ Sub-agent status visibility (user can see what ran, what timed out)

---

## NEXT STEPS

**Completed (v2.0):**
- ✓ Directory structure created (`agents/` + `skills/`)
- ✓ AGENT.md template defined (`_AGENT_TEMPLATE.md`)
- ✓ **Phase 1 core analysts COMPLETE (8/8 AGENT.md created):**
  - pestle-analyst, morphological-analyst, scenario-planner, stakeholder-mapper
  - geopolitical-theorist, power-analyst, first-principles-analyst, triz-solver
- ✓ **Phase 2 priority synthesizers COMPLETE (4/4 SKILL.md created):**
  - space-strategy-synthesizer, geopolitical-synthesizer
  - tech-innovation-synthesizer, security-synthesizer
- ✓ **2-Step Output Generation VALIDATED:**
  - `_OUTPUT_GENERATION.md` with Step 1/Step 2 prompts
  - Outline templates integration working
  - User approval checkpoint functional
- ✓ **Phase 3 orchestrator COMPLETE (1/1 SKILL.md created):**
  - strategic-orchestrator with 4-phase workflow
  - Synthesizer scoring and selection logic
  - Extension decision triggers
  - Template and web search proposals
- ✓ **END-TO-END TEST PASSED:**
  - Test case: "Strategia italiana per l'accesso autonomo allo spazio"
  - 3 analysts launched in parallel (~70s total)
  - Outline generated → User approval → Full text expanded
  - Output saved to `output/` folder (OUTLINE + REPORT)

**For Next Conversation - Options:**

**Option A: Test Orchestrator End-to-End** (RECOMMENDED)
1. Test PROPOSAL generation with different problem types
2. Validate synthesizer selection on ambiguous/multi-domain problems
3. Test clarification flow (when scores are ambiguous)
4. Verify handoff to synthesizer works correctly

**Option B: Complete Phase 4 Agents (7 remaining)**
- threat-analyst, red-teamer, horizon-analyst, depth-analyst
- perspectives-analyst, swot-analyst, ecosystem-analyst
- Note: security-synthesizer needs threat-analyst + red-teamer to be fully functional

**Option C: Complete Phase 4 Synthesizers (3 remaining)**
- policy-synthesizer, industrial-synthesizer, futures-synthesizer
- Note: futures-synthesizer needs horizon-analyst + depth-analyst

**Option D: Setup Exa MCP Server**
- Install `exa-labs/exa-mcp-server`
- Configure API key
- Test web search integration for pestle-analyst, scenario-planner

**Option E: Test Other Synthesizers**
- Run geopolitical-synthesizer or tech-innovation-synthesizer end-to-end
- Validate different outline templates (BLUF, Hypothesis-Driven, POR)

**Architecture Status:**
- Tier 1: 15 analyst sub-agents defined; **8/15 AGENT.md created** (Phase 1 complete)
- Tier 2: 7 synthesizer skills defined; **4/7 SKILL.md created** (Phase 2 priority complete)
- Tier 3: Orchestrator skill defined; **1/1 SKILL.md created** (Phase 3 COMPLETE)

**Output Structure:**
```
skills-definition/
├── output/                              # Generated documents
│   ├── [topic]_OUTLINE.md               # Step 1: Bullet-point outline
│   └── [topic]_REPORT.md                # Step 2: Full prose document
```

**Bring This Document:**
Use as complete context reference - all key decisions documented here.

**Related Documents:**
- `outline_templates.md` — 4 document structure templates (BLUF, Hypothesis-Driven, POR, Minto-Custom)
- `tools.md` — Framework/methodology reference (1:1 mapping with analysts)
- `.claude/skills/_OUTPUT_GENERATION.md` — 2-step output prompts and templates

---

**END OF BLUEPRINT**
