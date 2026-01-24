# Trasformazione del Progetto Zwicky con Claude Skills

## Executive Summary

Il progetto Zwicky Workflow può essere radicalmente trasformato da un sistema di prompt YAML + Python in una **Claude Skill nativa** che sfrutta l'ecosistema di skills Anthropic. Questa trasformazione elimina la necessità di esecuzione locale di Python, integra nativamente la generazione di documenti professionali (docx, pptx, xlsx), e abilita visualizzazioni interattive tramite artifacts.

**Beneficio chiave**: L'utente otterrà report strategici esecutivi con un singolo comando, senza dover gestire file YAML intermedi o eseguire codice localmente.

---

## 1. Analisi dello Stato Attuale

### Architettura Corrente

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKFLOW ATTUALE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  User → flux.yaml → [8 step prompts] → Claude → Output     │
│                          ↓                                  │
│                    4_main.py (locale)                       │
│                          ↓                                  │
│                    zwickyBox.md                             │
│                          ↓                                  │
│                    Report finale (testo)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Punti di Frizione

| Problema | Impatto | Soluzione Skills |
|----------|---------|------------------|
| Esecuzione Python locale | Richiede ambiente configurato | Script embedded nella skill |
| Output solo Markdown | Non professionale per executive | Integration con docx/pptx skills |
| 8 step manuali con "OK" | Workflow lento e frammentato | Single-command workflow |
| Visualizzazioni assenti | Nessun supporto visivo | jsvis-map + React artifacts |

---

## 2. Architettura Target con Claude Skills

### Struttura della Zwicky Skill

```
zwicky-strategic-analyst/
├── SKILL.md                         # Core instructions + workflow
├── scripts/
│   ├── zwicky_engine.py             # Generatore scenari (attuale 4_main.py)
│   ├── triz_analyzer.py             # TRIZ contradiction resolver
│   └── minto_formatter.py           # Minto pyramid structurer
├── references/
│   ├── 4dimensions_ontology.md      # Ontologia 4D completa
│   ├── triz_principles.md           # 40 principi TRIZ con esempi
│   └── minto_templates.md           # Template Minto Pyramid
└── assets/
    ├── matrix_template.xlsx         # Template matrice 4×4
    ├── report_template.docx         # Template report esecutivo
    └── presentation_template.pptx   # Template presentazione
```

### SKILL.md Proposto

```yaml
---
name: zwicky-strategic-analyst
description: |
  Generate strategic reports using Advanced Morphological Analysis (Zwicky Box), 
  4Dimensions© ontology, TRIZ problem-solving, and Minto Pyramid communication.
  
  Use when:
  - Creating strategic analysis on complex topics
  - Generating scenario analysis for decision-making
  - Building executive reports with morphological methodology
  - Analyzing trade-offs using TRIZ principles
  
  Output formats: Markdown, Word (.docx), PowerPoint (.pptx), Excel (.xlsx)
---
```

---

## 3. Workflow Trasformato

### Single-Command Execution

**Vecchio workflow** (8 step + "OK" manuale):
```
User: "Topic: X" → Step 1 → OK → Step 2 → OK → ... → Step 8 → Output
```

**Nuovo workflow** (single skill invocation):
```
User: "Create a strategic report on [Topic] for [Audience]"
      
      ↓ Zwicky Skill auto-triggers
      
Claude: Executes full pipeline:
        1. Generate 4×4 Matrix (internal)
        2. Select Features (internal)
        3. Generate YAML + Run Engine (scripts/zwicky_engine.py)
        4. TRIZ Analysis (scripts/triz_analyzer.py)
        5. Merging (scripts/minto_formatter.py)
        6. Generate Outline
        7. Write Report
        8. Format Output → docx/pptx skill integration
```

### Integrazione con Skills Pubbliche

```
┌─────────────────────────────────────────────────────────────┐
│                    SKILL ECOSYSTEM                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     ┌─────────────────┐               │
│  │  zwicky-skill   │────▶│   docx skill    │───▶ Report.docx│
│  │  (main logic)   │     └─────────────────┘               │
│  │                 │     ┌─────────────────┐               │
│  │                 │────▶│   pptx skill    │───▶ Slides.pptx│
│  │                 │     └─────────────────┘               │
│  │                 │     ┌─────────────────┐               │
│  │                 │────▶│   xlsx skill    │───▶ Matrix.xlsx│
│  │                 │     └─────────────────┘               │
│  │                 │     ┌─────────────────┐               │
│  │                 │────▶│  jsvis-map      │───▶ Network.html│
│  └─────────────────┘     └─────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Output Potenziati

### 4.1 Report Word Professionale

Usando la `docx` skill, il report finale include:
- Cover page con branding
- Table of Contents automatica
- Executive Summary con box colorati
- Grafici embedded
- Footnotes e citazioni formattate

### 4.2 Presentazione Executive

Usando la `pptx` skill:
- Slide di titolo
- Agenda
- 3-5 slide per scenario (con layout predefiniti)
- Slide di raccomandazioni
- Appendice con matrice completa

### 4.3 Matrice Interattiva Excel

Usando la `xlsx` skill:
- Foglio "Matrix 4×4" con formattazione condizionale
- Foglio "Scenarios" con filtri automatici
- Foglio "TRIZ Analysis" con dropdown
- Formule per calcolo automatico score

### 4.4 Network Map Interattiva

Usando la `jsvis-map` skill:
- Visualizzazione della matrice come grafo
- Nodi cliccabili per research
- Esportabile come HTML standalone

---

## 5. Implementazione Tecnica

### 5.1 Script zwicky_engine.py (Ottimizzato)

```python
"""
Zwicky Box Engine - Versione per Claude Skill
Eseguibile direttamente dalla skill senza dipendenze esterne
"""

import json
import itertools
from typing import Dict, List, Any

def parse_yaml_simple(yaml_string: str) -> Dict[str, Any]:
    """Parser YAML minimale senza dipendenze"""
    # [implementazione inline senza import yaml]
    pass

def generate_scenarios(config: Dict) -> List[Dict]:
    """Genera scenari filtrati e ordinati"""
    dim_names = list(config['dimensions'].keys())
    dim_variants = [config['dimensions'][d] for d in dim_names]
    
    scenarios = []
    for combo in itertools.product(*dim_variants):
        names = [v['name'] for v in combo]
        if is_consistent(names, config.get('constraints', [])):
            score = sum(v['weight'] for v in combo)
            scenarios.append({
                'configuration': dict(zip(dim_names, names)),
                'score': score
            })
    
    return sorted(scenarios, key=lambda x: x['score'], reverse=True)

def is_consistent(variant_names: List[str], constraints: List) -> bool:
    """Verifica vincoli"""
    for constraint in constraints:
        if all(item in variant_names for item in constraint):
            return False
    return True

def main(yaml_content: str) -> str:
    """Entry point per la skill"""
    config = parse_yaml_simple(yaml_content)
    scenarios = generate_scenarios(config)
    return format_output(config, scenarios)
```

### 5.2 React Artifact per Visualizzazione Interattiva

La skill può generare un artifact React per:
- Visualizzare la matrice 4×4 interattiva
- Mostrare lo score degli scenari in tempo reale
- Permettere "what-if" analysis modificando pesi

```jsx
// Esempio di artifact generabile dalla skill
function ZwickyMatrix({ dimensions, scenarios }) {
  const [selectedScenario, setSelectedScenario] = useState(0);
  
  return (
    <div className="grid grid-cols-2 gap-4">
      <MatrixView dimensions={dimensions} />
      <ScenarioList 
        scenarios={scenarios}
        selected={selectedScenario}
        onSelect={setSelectedScenario}
      />
    </div>
  );
}
```

---

## 6. Vantaggi della Trasformazione

| Aspetto | Prima | Dopo |
|---------|-------|------|
| **Setup** | Python + YAML + 8 file | Upload singola .skill |
| **Esecuzione** | 8 step manuali | Single command |
| **Output** | Solo Markdown | docx, pptx, xlsx, html |
| **Visualizzazioni** | Nessuna | Grafici + Network map |
| **Portabilità** | Richiede ambiente | Funziona ovunque |
| **Manutenzione** | 12 file separati | 1 skill bundle |

---

## 7. Roadmap Implementazione

### Fase 1: Core Skill (1-2 giorni)
- [ ] Creare struttura `zwicky-strategic-analyst/`
- [ ] Migrare logica da YAML prompts a SKILL.md
- [ ] Convertire `4_main.py` in script skill-compatible

### Fase 2: Integration (1 giorno)
- [ ] Documentare integrazione con `docx` skill
- [ ] Documentare integrazione con `pptx` skill
- [ ] Creare template assets

### Fase 3: Visualization (1 giorno)
- [ ] Creare pattern per React artifact
- [ ] Integrare con `jsvis-map` per network visualization

### Fase 4: Testing & Refinement
- [ ] Test end-to-end con topic reale
- [ ] Raffinamento prompt in SKILL.md
- [ ] Package finale `.skill`

---

## 8. Esempio d'Uso Trasformato

### Input Utente
```
Create a strategic report on "European Space Launch Autonomy" 
for EU Commission executives.
Constraints: 5-year horizon, budget-conscious approach
Output: Full report (docx) + Executive slides (pptx) + Scenario matrix (xlsx)
```

### Output Automatico

1. **Report.docx** (2000+ words)
   - Executive Summary
   - 4×4 Strategic Matrix
   - Top 3 Scenarios con TRIZ analysis
   - Recommendations

2. **Slides.pptx** (10 slides)
   - Title + Agenda
   - Key findings (3 slides)
   - Scenario comparison
   - Recommendations

3. **Matrix.xlsx**
   - Full 4×4 matrix con pesi
   - Scenario ranking
   - What-if calculator

4. **Network.html** (via jsvis-map)
   - Mappa interattiva esplorabile

---

## Conclusione

La trasformazione del progetto Zwicky in una Claude Skill rappresenta un salto qualitativo:

1. **Efficienza**: Da 8 step manuali a esecuzione automatica
2. **Professionalità**: Output nativi in formati executive
3. **Scalabilità**: Riutilizzabile su qualsiasi topic
4. **Manutenibilità**: Single source of truth

**Prossimo passo consigliato**: Procedere con la Fase 1 creando lo scheletro della skill.
