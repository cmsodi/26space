---
title: Confirmed Analysts Reference
subtitle: Analytical Tools Inventory
version: 1.0
date: 2026-01-22
purpose: Consolidated list of analytical tools aligned with Skills Architecture Blueprint
reference: SKILLS_ARCHITECTURE_BLUEPRINT.md v1.2
analysts_count: 15
categories_count: 7
---

# CONFIRMED ANALYSTS (15)

Consolidated list of analytical tools for strategic research, aligned with Skills Architecture Blueprint v1.2.

---

## 1. Strategic Analysis & Context

### 1.1 pestle-analyst
**Methodology:** PESTLE Family (PEST, STEEP, STEEPLE, PESTEL)
Analyzes Political, Economic, Social, Technological, Legal, and Environmental macro-trends impacting the [ENTITY]. Essential for understanding the broad operating context.

### 1.2 morphological-analyst
**Methodology:** Morphological Analysis / Zwicky Box
Breaks a complex problem down into key parameters and explores all possible combinations to generate a wide range of solutions or scenarios systematically. Configuration space exploration.

### 1.3 swot-analyst
**Methodology:** SWOT Analysis
Identifies internal Strengths and Weaknesses, and external Opportunities and Threats facing the [ENTITY]. A crucial synthesis tool for competitive positioning assessment.

---

## 2. Geopolitical & Power Assessment

### 2.1 geopolitical-theorist
**Methodology:** Classical Geopolitical Theories (Mackinder, Mahan, Spykman) + Levels of Analysis (Waltz)
Examines the influence of geography, location, resources, and control of strategic areas (Heartland, Rimland, Sea Lanes, chokepoints, spheres of influence) on a state's power and options. Analyzes drivers at Individual, State, and System levels.

### 2.2 power-analyst
**Methodology:** DIME (Diplomatic, Informational, Military, Economic) + Hard/Soft/Smart Power (Nye)
Categorizes and assesses the state's instruments of power. Evaluates whether influence is based on coercion (hard) or attraction (soft), and the effectiveness of their combination (smart power).

---

## 3. Problem-Solving & Innovation

### 3.1 triz-solver
**Methodology:** Theory of Inventive Problem Solving (TRIZ)
Contradiction analysis, inventive principles application. Identifies patterns of innovation and breakthrough solutions for technical contradictions.

### 3.2 first-principles-analyst
**Methodology:** First Principles Thinking
Fundamental assumptions deconstruction. Rebuilds logic from foundations to challenge orthodoxy and find non-obvious solutions.

---

## 4. Foresight & Futures

### 4.1 scenario-planner
**Methodology:** Scenario Planning
Develops plausible alternative futures based on key driving forces and uncertainties (2x2 matrices, narrative scenarios, wildcard events). Helps strategize for a range of potential outcomes.

### 4.2 horizon-analyst
**Methodology:** Three Horizons Framework + Futures Wheel + Cross-Impact Analysis + Weak Signals
Maps strategic initiatives across time horizons (H1: core, H2: emerging, H3: radical). Explores ripple effects and examines how trends influence each other's probability and impact.

### 4.3 depth-analyst
**Methodology:** Causal Layered Analysis (CLA)
Explores deeper layers beyond surface 'litany': systemic causes → underlying worldviews → foundational myths/metaphors. Understanding deep-rooted narratives and paradigm shifts.

---

## 5. Security & Risk

### 5.1 red-teamer
**Methodology:** Red Team - Blue Team Analysis
Adversarial approach where a 'Red Team' actively challenges plans, strategies, or security postures to identify weaknesses and untested assumptions. Stress-testing through adversarial thinking.

### 5.2 threat-analyst
**Methodology:** Threat & Risk Assessment Matrix (Likelihood × Impact × Vulnerability)
Identifies specific threats (state/non-state actors, cyber, economic, environmental), assesses their probability and impact, evaluates vulnerability and resilience gaps. Systematic risk quantification.

---

## 6. Multi-Perspective & Creativity

### 6.1 perspectives-analyst
**Methodology:** Six Thinking Hats (De Bono) + SCAMPER + Forced Analogies
Separates thinking into distinct modes (facts, feelings, caution, benefits, creativity, process). Includes creativity triggers (Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse) and analogical reasoning.

---

## 7. Ecosystem & Stakeholders

### 7.1 stakeholder-mapper
**Methodology:** Stakeholder Power-Interest Matrix + Actor Network Analysis + Alliance Mapping
Maps key actors based on their interest and power to influence outcomes. Evaluates bilateral/multilateral relationships (allies, partners, rivals). Identifies coalition dynamics and partnership opportunities.

### 7.2 ecosystem-analyst
**Methodology:** Porter's Five Forces + Value Chain Analysis
Competitive forces analysis, industrial structure assessment. Examines suppliers, buyers, substitutes, new entrants, and rivalry intensity.

---

## EXCLUDED FROM IMPLEMENTATION

The following tools from the original list are **not implemented as standalone analysts** due to architectural constraints:

| Tool | Reason |
|------|--------|
| **Delphi Method** | Requires iterative human expert consultation - not suitable for single-pass LLM analysis |
| **War-gaming** | Too interactive/simulation-based - partially covered by scenario-planner + red-teamer combination |
| **Security Sector Analysis** | Domain rather than methodology - covered by power-analyst + threat-analyst combination |

---

## CROSS-REFERENCE

| # | Analyst | Blueprint Section |
|---|---------|-------------------|
| 1.1 | pestle-analyst | Strategic Analysis & Context |
| 1.2 | morphological-analyst | Strategic Analysis & Context |
| 1.3 | swot-analyst | Strategic Analysis & Context |
| 2.1 | geopolitical-theorist | Geopolitical & Power Assessment |
| 2.2 | power-analyst | Geopolitical & Power Assessment |
| 3.1 | triz-solver | Problem-Solving & Innovation |
| 3.2 | first-principles-analyst | Problem-Solving & Innovation |
| 4.1 | scenario-planner | Foresight & Futures |
| 4.2 | horizon-analyst | Foresight & Futures |
| 4.3 | depth-analyst | Foresight & Futures |
| 5.1 | red-teamer | Security & Risk |
| 5.2 | threat-analyst | Security & Risk |
| 6.1 | perspectives-analyst | Multi-Perspective & Creativity |
| 7.1 | stakeholder-mapper | Ecosystem & Stakeholders |
| 7.2 | ecosystem-analyst | Ecosystem & Stakeholders |

---

**Reference:** SKILLS_ARCHITECTURE_BLUEPRINT.md v1.2
