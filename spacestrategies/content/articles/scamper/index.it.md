---
id: "6.3"
category_id: "6"
category: "Structured Thinking & Problem Solving"
title: "SCAMPER: Provocazione Sistematica per l'Innovazione Incrementale"
slug: "scamper"
target_audience: "Designer di Prodotto e Leader dell'Innovazione"
strategic_utility: "Adattare tecnologie terrestri (come IoT o AI) per ambienti spaziali estremi attraverso innovazione incrementale."
description: "Una tecnica di brainstorming creativo che usa sette prompt (Substitute, Combine, Adapt, Modify, Put to another use, Eliminate, Reverse) per innovare su idee esistenti."
date: 2026-01-13
draft: false
---

## 1. Genesi Metodologica e Logica Fondamentale

Sviluppato da Bob Eberle (1971) come checklist educativa basata sui principi di brainstorming di Alex Osborn, **SCAMPER** ha codificato sette operatori cognitivi per l'ideazione sistematica. A differenza di metodi che pretendono di generare innovazione "breakthrough", SCAMPER mira esplicitamente al miglioramento *incrementale* attraverso manipolazione strutturata di concetti esistenti.

* **Traduzione Spaziale:** I sistemi spaziali raramente coinvolgono invenzione pura—la maggior parte dei progressi risulta dall'adattamento intelligente di tecnologie terrestri o ricombinazione di componenti provati. SCAMPER fornisce un protocollo disciplinato per chiedere "Come possiamo adattare X per lo spazio?" piuttosto che defaultare a sviluppo custom costoso. Critico nell'aerospaziale vincolato da heritage dove il bias "flight-proven" blocca il pensiero laterale.
* **Funzione Epistemologica:** Produce **variazione di design attraverso rilassamento vincoli**—mettendo sistematicamente in discussione ogni assunzione embedded nel design corrente. Il metodo non scopre fisica fondamentalmente nuova; scopre nuove *applicazioni* di fisica esistente sfidando ortodossie di design.
* **Logica Fondamentale:** L'innovazione è spesso ricombinazione, non creazione ex nihilo. Ogni design incorpora centinaia di scelte implicite ("L'abbiamo sempre fatto così"). SCAMPER forza l'esame esplicito di ogni scelta attraverso sette lenti provocatorie. La maggior parte dei prompt non produce nulla; il 5-10% produce miglioramenti attuabili—ma non si può predire quali prompt avranno successo.
* **Limitazione Critica:** SCAMPER *non* è un metodo di innovazione radicale. Migliora soluzioni esistenti; non scopre nuovi paradigmi di soluzione. Per vera discontinuità, accoppiare con analisi morfologica o analogie forzate. SCAMPER è incrementale by design.

---

## 2. Componenti Strutturali

Il framework opera attraverso sette operatori cognitivi sequenziali, ciascuno che targeting dimensioni di design diverse:

### **S - Substitute: Sostituire Componenti o Attributi**
- **Operazione Cognitiva:** Quali elementi possono essere scambiati con alternative?
- **Categorie Prompt:**
  - Materiali: "Sostituire alluminio con compositi, acciaio con ceramiche, silicio con nitruro di gallio"
  - Processi: "Sostituire manifattura additiva per sottrattiva, automatizzato per manuale, centralizzato per distribuito"
  - Fonti energia: "Sostituire batterie con celle a combustibile, solare con nucleare, cablato con wireless"
  - Personale: "Sostituire AI per operatori umani, remoto per on-site, specialisti per generalisti"
- **Esempio Spaziale (Controllo Termico Satelliti):**
  - Attuale: Radiatori passivi (honeycomb alluminio + coating)
  - SCAMPER-S: "Sostituire materiali elettrocromici per coating statici" (controllo termico dinamico)
  - Risultato: Emissività variabile abilita regolazione temperatura attiva senza heater energivori
- **Test Qualità:** Il sostituto è *funzionalmente equivalente* o cambia l'architettura sistema? (Quest'ultimo può essere prezioso ma eccede la "sostituzione")
- **Modalità Fallimento:** Sostituire senza validare compatibilità vincoli (es. "Usare elettronica commerciale"—ignora ambiente radiazioni)

### **C - Combine: Unire Funzioni o Elementi**
- **Operazione Cognitiva:** Quali componenti separati possono essere integrati?
- **Categorie Prompt:**
  - Integrazione funzionale: "Combinare struttura + gestione termica, potenza + propulsione, comunicazione + navigazione"
  - Multi-funzionalità: "Far servire al componente 2-3 scopi simultaneamente"
  - Consolidamento supply chain: "Combinare vendor, integrare sottosistemi"
- **Esempio Spaziale (Design CubeSat):**
  - Attuale: Sistema controllo assetto separato (reaction wheel) + gestione momentum (magnetorquer)
  - SCAMPER-C: "Combinare reaction wheel con barre torque magnetiche in singola unità"
  - Risultato: Risparmio massa 15-20%, ridotta complessità integrazione
- **Trade-Off:** La combinazione aumenta accoppiamento (modalità guasto propagano), riduce modularità (più difficile aggiornare)
- **Valore Space-Specific:** Alto—costo lancio penalizza massa; combinazione è mass-efficient

### **A - Adapt: Adattare a Nuovo Contesto o Scopo**
- **Operazione Cognitiva:** Come possono soluzioni esistenti da altri domini essere modificate per questa applicazione?
- **Categorie Prompt:**
  - Cross-industry: "Adattare dispositivi medicali, sistemi automotive, tecnologia marina"
  - Cross-domain: "Cosa fanno sottomarini/aeromobili/data center che potremmo applicare?"
  - Scaling: "Adattare terrestrial large-scale a space small-scale, o viceversa"
- **Esempio Spaziale (Sistemi Life Support):**
  - Analogo terrestre: Scrubber CO2 sottomarini (canister idrossido di litio)
  - SCAMPER-A: "Adattare per microgravità + lunga durata + vincoli rifornimento"
  - Risultato: Sistema rimozione CO2 ISS—scrubber amminici rigenerativi adattati da tech sottomarini + modifiche per fluidodinamica zero-g
- **Domanda Critica:** Quali differenze ambientali richiedono adattamento? (Gravità, radiazione, vuoto, estremi termici, accessibilità manutenzione)
- **Errore Comune:** Trapianto diretto senza adattamento (ricevitori GPS terrestri falliscono in orbite ad alta radiazione)

### **M - Modify/Magnify/Minify: Cambiare Scala, Forma o Attributi**
- **Operazione Cognitiva:** E se lo rendessimo più grande, più piccolo, più veloce, più lento, più forte, più debole?
- **Categorie Prompt:**
  - Scala: "10x più grande? 10x più piccolo? Cosa cambia?"
  - Frequenza: "Operare più veloce, più lento, intermittentemente?"
  - Quantità: "Più unità, meno unità, singolo vs. distribuito?"
  - Attributi: "Più rigido, più flessibile, più caldo, più freddo, più leggero, più denso?"
- **Esempio Spaziale (Sistemi Propulsione):**
  - Attuale: Grandi motori monolitici (F-1, RS-25)
  - SCAMPER-M (Minify): "E se usassimo 100 motori piccoli invece di 9 grandi?"
  - Risultato: Clustering Raptor SpaceX—tolleranza engine-out, produzione parallela, testing incrementale
- **Effetti Non-Lineari:** Lo scaling spesso cambia la fisica (rapporto superficie-volume, costanti tempo termiche, risonanze strutturali)
- **Sfida Space-Specific:** Miniaturizzazione colpisce limiti fisici (guadagno antenna ∝ apertura, efficienza propellente ∝ pressione camera)

### **P - Put to Other Uses: Riutilizzare o Trovare Nuove Applicazioni**
- **Operazione Cognitiva:** Per cos'altro potrebbe essere usato? Quali problemi risolve accidentalmente?
- **Categorie Prompt:**
  - Funzione Primaria → Secondaria: "Quali sottoprodotti stiamo sprecando?"
  - Single-use → Multi-mission: "Può servire clienti/scopi multipli?"
  - Rifiuto → Risorsa: "Cosa buttiamo che ha valore?"
- **Esempio Spaziale (Stadi Razzo Esauriti):**
  - Attuale: Deorbitati/abbandonati post-missione
  - SCAMPER-P: "Riutilizzare come deposito carburante orbitale, modulo stazione spaziale, scudo radiazioni"
  - Risultato: Molteplici studi su concetti "Wet Workshop" (usare serbatoi carburante come volume abitabile)
- **Insight Dual-Use:** La tecnologia spaziale ha spesso applicazioni terrestri (GPS, satelliti meteo, scienza materiali)
- **Limitazione:** Riutilizzare spesso richiede design-for-reuse dall'inizio (retrofit è più difficile)

### **E - Eliminate: Rimuovere Componenti o Vincoli**
- **Operazione Cognitiva:** Cosa possiamo eliminare senza perdere funzionalità core? Quali regole possiamo violare?
- **Categorie Prompt:**
  - Eliminazione fisica: "Rimuovere parti, ridurre feature, semplificare"
  - Eliminazione processi: "Saltare step, rimuovere approvazioni, eliminare fasi testing"
  - Rilassamento vincoli: "E se ignorassimo lo standard X, la regolamentazione Y, l'assunzione Z?"
- **Esempio Spaziale (Design Razzo):**
  - Tradizionale: Fairing usa-e-getta (gusci protettivi per payload)
  - SCAMPER-E: "Eliminare fairing—progettare payload per resistere ambiente ascesa"
  - Risultato: Alcuni piccoli satelliti ora volano "nudi" (risparmio massa/costo, ma richiede design payload robusto)
- **Prompt Pericoloso:** L'eliminazione può rimuovere margini sicurezza essenziali (classica modalità fallimento aerospaziale)
- **Euristica:** Eliminare nel *design* ma ripristinare nella *validazione* se test rivelano necessità

### **R - Reverse/Rearrange: Invertire Sequenza o Configurazione**
- **Operazione Cognitiva:** E se lo facessimo al contrario? Sottosopra? In ordine opposto?
- **Categorie Prompt:**
  - Inversione sequenza: "Assemblare-poi-lanciare vs. lanciare-poi-assemblare"
  - Riarrangiamento spaziale: "Interno-esterno, scambio alto-basso"
  - Inversione processo: "Centralizzato → distribuito, push → pull"
  - Inversione assunzione: "Invece di portare X nello spazio, portare lo spazio a X"
- **Esempio Spaziale (Manifattura In-Space):**
  - Tradizionale: Manifatturare sulla Terra → Lanciare nello spazio
  - SCAMPER-R (Reverse): "Lanciare materiali grezzi → Manifatturare nello spazio"
  - Razionale: Evitare vincoli gravità/atmosferici durante fabbricazione, evitare carichi lancio su strutture delicate
- **Sfida Cognitiva:** L'inversione spesso richiede riconcettualizzare l'intera catena valore (non solo swap locale)
- **Ricchezza Dominio Spaziale:** Molte assunzioni sono gravity-based ("su/giù", "pesante/leggero", "cadere")—microgravità le inverte

---

## 3. Protocollo di Implementazione

**Pre-requisiti:**
- Design/sistema baseline chiaramente definito (SCAMPER richiede qualcosa da manipolare—non può operare su lavagna bianca)
- Team cross-funzionale (5-10 partecipanti): designer, ingegneri, operatori, utenti
- Blocchi workshop 2-4 ore (SCAMPER esaustivo richiede tempo)
- Permesso psicologico di mettere in discussione vacche sacre (metodo richiede sfidare "come l'abbiamo sempre fatto")

**Sequenza Esecutiva:**

**Fase I: Documentazione Baseline (30 minuti)**
- Presentare design/sistema corrente in dettaglio
- Decomporre in componenti, processi, vincoli, assunzioni
- Creare rappresentazione visuale (diagramma blocchi, flusso processo, rendering CAD)
- **Requisito Esplicito:** Documentare *perché* ogni scelta di design è stata fatta (razionale diventa target per interrogazione SCAMPER)

**Fase II: Prompt SCAMPER Sequenziali (90-120 minuti)**
- Lavorare attraverso S-C-A-M-P-E-R sequenzialmente (non saltare—cervello necessita consistenza modalità)
- **Per ogni lettera (15-20 minuti):**
  - Facilitatore presenta categoria prompt
  - Ideazione silenziosa (5 min): Ogni partecipante scrive 3-5 idee
  - Condivisione round-robin (10 min): Cattura idee rapid-fire (nessun dibattito ancora)
  - Clustering (5 min): Raggruppare idee simili
- **Output per lettera:** 10-25 idee distinte (prima del filtraggio)
- **Ruolo Facilitatore:** Far rispettare modalità cognitiva (durante S, solo idee sostituzione; differire idee combinazione a C)

**Fase III: Screening Fattibilità Rapido (30 minuti)**
- Per ogni idea generata SCAMPER, classificazione rapida:
  - **Verde:** Fattibile, attuabile, vale la pena perseguire
  - **Giallo:** Interessante ma richiede investigazione
  - **Rosso:** Non fattibile (fisica, regolamentazioni, costo) o già provato e fallito
- **Euristica:** Tipicamente 60-70% Rosso, 20-30% Giallo, 5-15% Verde
- **Disciplina Critica:** Classificazione rossa deve citare *ragione* (non solo "non mi piace")

**Fase IV: Sviluppo Concetti (60 minuti)**
- Selezionare top 5-8 idee Verdi per esplorazione più profonda
- Per ciascuna: Schizzare implementazione, identificare cambiamenti richiesti, stimare impatto
- Segnalare sinergie: "Idea S3 + Idea C7 = combinazione superiore"
- Identificare showstopper: "Questo richiede tecnologia che non esiste ancora"

**Fase V: Prioritizzazione & Action Planning (30 minuti)**
- Classificare per matrice sforzo-impatto (2×2: Basso Sforzo/Alto Impatto = Fare Prima)
- Assegnare ownership per raffinamento concetto
- Definire criteri valutazione: "Perseguiremo questo se [soglia specifica raggiunta]"
- Schedulare follow-up: Ciclo review 30-60 giorni

**Formato Output:**
- Inventario idee SCAMPER (50-100 idee totali attraverso 7 categorie)
- Classificazione fattibilità con razionali
- Top 5-8 concetti con schizzi implementazione
- Action plan con owner e timeline

---

## 4. Modalità di Fallimento e Vincoli

**Bias Cognitivi:**
- **Ancoraggio su Prime Idee:** Prompt SCAMPER iniziali (S, C) ricevono più attenzione; prompt successivi (E, R) affrettati. **Rimedio:** Allocazione tempo uguale forzata; considerare randomizzare ordine SCAMPER.
- **Conservatorismo Incrementale:** Team generano solo variazioni minori ("Sostituire alluminio 6061 con 7075") piuttosto che sostituzioni audaci ("Sostituire metallo con strutture gonfiabili"). **Rimedio:** Facilitatore spinge per "pensiero 10x" in ogni categoria.
- **Tirannia Expertise:** Esperti di dominio scartano idee come "già provato" o "non funzionerà" durante fase divergente. **Rimedio:** Separazione stretta di ideazione (nessuna critica) da valutazione (critica strutturata).

**Patologie Strutturali:**
- **Misapplicazione Metodo:** Usare SCAMPER per innovazione radicale (strumento sbagliato). **Esempio:** "Rivoluzionare propulsione spaziale" richiede breakthrough fisica, non manipolazione design. **Uso Corretto:** "Migliorare efficienza propulsione elettrica esistente 15-20%."
- **Mentalità Checklist:** Attraversare meccanicamente prompt senza genuino ingaggio cognitivo. **Sintomo:** Tutte le idee sono triviali o ovvie. **Rimedio:** Primeare team con esempi esterni di applicazioni SCAMPER di successo.
- **Ideazione Context-Free:** Generare idee senza considerare impatti integrazione. **Esempio:** "Eliminare ridondanza" (E) può risparmiare massa ma creare single-point failure catastrofici nello spazio.

**Condizioni di Invalidazione:**
- **Design Greenfield:** SCAMPER richiede design esistente da manipolare. Per sistemi veramente nuovi (missioni first-of-kind), usare prima analisi morfologica o pensiero first principles.
- **Sistemi Maturi Ottimizzati:** Quando il design ha subito decenni di raffinamento, SCAMPER produce rendimenti decrescenti—frutta bassa già raccolta. **Esempio:** Motori razzi chimici (60+ anni di ottimizzazione).
- **Design Congelati Regolamentari:** Quando cambiamenti design richiedono ri-certificazione così costosa da essere proibitiva, le idee SCAMPER diventano "interessanti ma non fattibili." Comune in sistemi human-rated.

**Pattern di Uso Improprio:** Usare SCAMPER per *giustificare* cambiamenti design predeterminati ("Eseguiamo SCAMPER per provare che dovremmo usare la mia tecnologia preferita"). SCAMPER genuino deve essere aperto a direzioni inaspettate.

---

## 5. Punti di Integrazione

**Feeder Upstream:**
- **Morphological Analysis (6.2):** Usare morphological box per identificare configurazione baseline, poi SCAMPER ogni parametro per generare variazioni
- **Analisi SWOT (2.3):** SWOT identifica debolezze (W) e minacce (T)—usare SCAMPER per generare idee mitigazione

**Amplificatore Downstream:**
- **Trade Study Analysis:** SCAMPER genera design alternativi; trade study forniscono framework confronto rigoroso
- **Technology Readiness Assessment:** Idee SCAMPER sono ipotetiche—valutazione TRL determina rischio sviluppo

**Accoppiamento Sinergico:**
- **Forced Analogies (6.4):** SCAMPER adatta (A) dentro dominio aerospaziale; Forced Analogies porta concetti da domini *completamente non correlati*
- **Six Thinking Hats (6.1):** Usare SCAMPER durante fase Green Hat (creatività), poi valutare con Black/Yellow Hat

**Logica Sequenziale:**
Baseline Design → SCAMPER (generare variazioni) → Feasibility Screening → Concept Refinement → Trade Study → Down-Selection

---

## 6. Caso Esemplare

**Contesto:** Redesign tuta spaziale lunare NASA per programma Artemis (2020-2021). Baseline: Architettura EMU (Extravehicular Mobility Unit) Apollo/Shuttle modificata.

**Problema:** Tute correnti progettate per microgravità (ISS) o camminata superficie lunare (Apollo). Artemis richiede tute per: camminata superficie (EVA 6-8 ore), ambiente polvere lunare, range più ampio taglie corporee, mobilità migliorata, vita operativa 15 anni.

**Workshop SCAMPER (30 partecipanti: ingegneri, astronauti, operations, specialisti life support):**

**S - Substitute:**
- Sostituire torso superiore rigido (rigido) → Torso superiore tessuto morbido (miglioramento mobilità)
- Sostituire life support closed-loop → Open-loop con ossigeno ISRU (se O2 lunare disponibile)
- Sostituire materiale vescica pressione: gomma → elastomeri avanzati con migliore resistenza fatica
- Sostituire stivali: suola rigida → battistrada adattivo (ispirato rock-climbing)
- **Top Idea:** Sostituire coating termico tradizionale "bianco" → Coating emissività variabile (controllo termico dinamico)

**C - Combine:**
- Combinare life support portatile + sistema rigenerativo habitat (condividere scrubber CO2 durante permanenza airlock)
- Combinare sensori pressione tuta + monitor biomedici → Monitoraggio salute integrato
- Combinare guanto + interfaccia tool (ridurre cicli don/doff)
- **Top Idea:** Combinare tuta + ausilio mobilità (elementi esoscheletro in struttura gambe per load-bearing durante operazioni 1/6g)

**A - Adapt:**
- Adattare giunti tuta immersione profonda (differenziale pressione simile, mobilità provata)
- Adattare tecnologia esoscheletro industriale (dispositivi assist lavoratore → gestione carico astronauta)
- Adattare indumenti compressione medicali → Tute mechanical counter-pressure (concetto ricerca)
- Adattare dati sizing crash-test dummy automotive → Accomodazione antropometrica
- **Top Idea:** Adattare raccordi quick-disconnect immersioni → Connessioni ombelicali semplificate (ridurre tempo pre-breathe)

**M - Modify:**
- Modify (minify) zaino life support: Attuale 130kg → Target 80kg (1/6g permette peso terrestre più pesante)
- Modify (magnify) dimensione visiera: Campo visivo più ampio (astronauti Apollo citavano visione ristretta)
- Modify pressione operativa: 8 psi (heritage) → 4-6 psi? (Migliore mobilità ma pre-breathe più lungo)
- Modify sizing tuta: Attuali ~15 configurazioni → Sistema modulare con 100+ combinazioni taglie
- **Top Idea:** Modify (magnify) capacità dust-shedding—Repulsione elettrostatica (mitigazione polvere attiva)

**P - Put to Other Uses:**
- Tuta come rifugio emergenza: Se rover fallisce, tuta diventa pod sopravvivenza 48 ore (richiede estensione life support)
- Dati tuta come strumento scienza: Dati biomedici → Ricerca adattamento astronauta
- Tuta come relay comunicazioni: Astronauta diventa nodo repeater mobile
- **Top Idea:** Wear-testing tuta come piattaforma sviluppo esoscheletro terrestre (pathway tecnologia dual-use)

**E - Eliminate:**
- Eliminare protocollo pre-breathe: Transizione diretta habitat 1-atm → EVA (richiede pressione tuta più alta—trade sicurezza)
- Eliminare Maximum Absorbency Garment (pannolino): Migliore gestione rifiuti o pause igiene tuta
- Eliminare PLSS separato: Distribuire life support attraverso struttura tuta (ridurre concentrazione massa montata su schiena)
- Eliminare requisito colore bianco: Modeling termico mostra pattern colore selettivi viabili
- **Top Idea:** Eliminare don/doff guanti: Guanti permanentemente attaccati con migliore destrezza (controverso—ridotta igiene)

**R - Reverse/Rearrange:**
- Reverse concetto pressione: Invece di pressione interna + vuoto esterno, usare mechanical counter-pressure (tuta skin-tight)—RADICALE
- Rearrange posizione life support: PLSS su torace (anteriore) invece di schiena (migliorare centro-massa)
- Reverse ingresso: Tuta rear-entry (heritage Apollo) → Tuta front-entry (self-donning più facile)
- Rearrange layer: Layer termico più esterno (attuale) → Layer abrasione più esterno (protezione polvere)
- **Top Idea:** Rearrange sequenza assemblaggio—Lanciare componenti tuta separatamente, assemblare in orbita/superficie lunare (ridurre volume lancio)

**Riepilogo Risultati SCAMPER:**
- **Idee Totali Generate:** 127 attraverso tutte le categorie
- **Screening Fattibilità:**
  - Verde (perseguire): 18 idee
  - Giallo (investigare): 34 idee
  - Rosso (non fattibile): 75 idee
- **Top 8 Concetti Avanzati:**
  1. Coating emissività variabile (S)
  2. Elementi esoscheletro integrati (C)
  3. Ombelicali quick-disconnect (A)
  4. Mitigazione polvere elettrostatica (M)
  5. Sistema sizing modulare (M)
  6. Architettura front-entry (R)
  7. Gestione termica attiva (combinazione S+M)
  8. Life support distribuito (E)

**Implementazione (2021-2024):**
- **Adottato:** Concetti 3, 5, 6 integrati nel design tuta lunare Axiom Space (contractor NASA)
- **In Sviluppo:** Concetti 1, 4, 7 (TRL 4-6, possono integrare in iterazioni successive)
- **Differito:** Concetti 2, 8 (troppo radicali per Artemis near-term, potenzialmente per tute Marte)

**Validazione:**
- Metodo SCAMPER ha generato 18 miglioramenti attuabili—5 adottati entro 3 anni
- Concetto 6 (front-entry) si è rivelato più prezioso: Riduce tempo vestizione da 45 min → 15 min, abilita operazioni solo
- Concetto 4 (mitigazione polvere) in testing analogo lunare (2024)—risultati pendenti

**Critica Red Team:**
- Sessione SCAMPER può essere stata troppo conservativa—solo 18/127 idee Verdi suggerisce filtraggio fattibilità eccessivo durante ideazione (avrebbe dovuto differire più a Giallo)
- Categoria SCAMPER mancante per dominio spaziale: "Transform" (adattare per ambiente diverso)—avrebbe catturato meglio idee transizione microgravità→gravità
- Partecipazione astronauti insufficiente (solo 3 di 30 partecipanti)—voce end-user sotto-rappresentata
- Metodo non ha generato partenza veramente radicale (tuta mechanical counter-pressure)—SCAMPER intrinsecamente incrementale, avrebbe necessitato metodo diverso per paradigm shift

---

> **Avvertimento per Professionisti:** SCAMPER è il "coltellino svizzero" dei metodi innovazione—versatile, accessibile, ma non specializzato per nessuna sfida particolare. Il suo punto di forza è velocità e semplicità; la sua debolezza è mancanza di profondità. Le organizzazioni dovrebbero usare SCAMPER per ideazione rapida (design review, sessioni brainstorming), non come sostituzione per systems engineering rigoroso. Il metodo genera *candidati* per innovazione, non innovazioni *validate*. Ogni idea SCAMPER deve sopravvivere alla successiva analisi fattibilità, prototipazione e testing. Tre
