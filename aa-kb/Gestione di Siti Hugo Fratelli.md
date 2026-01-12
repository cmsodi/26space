# Manuale Operativo: Architettura Hugo a 2 Livelli (Module + Monorepo)

## 1. Visione del Sistema

Architettura a "sovrapposizione" per due siti fratelli.

1. **Livello Base:** Tema **Zen** (caricato come Hugo Module). Immutabile.
2. **Livello Specifico:** Cartelle /spacestrategies/ e /spacepolicies/. Contengono asset, configurazioni e contenuti esclusivi che sovrascrivono il tema Zen.

## 2. Struttura del File System



```
/26space                    <-- Root della monorepo
│
├── /spacestrategies/       <-- Sito spacestrategies.org
│   ├── /assets/scss/       <-- _custom.scss (esclusivo per spacestrategies)
│   ├── /content/           <-- Markdown di spacestrategies
│   ├── /layouts/           <-- Override layouts specifici
│   ├── /static/            <-- logo.png e risorse statiche
│   └── hugo.yaml           <-- Configurazione e Moduli
│
├── /spacepolicies/         <-- Sito spacepolicies.org
│   ├── /assets/scss/       <-- _custom.scss (esclusivo per spacepolicies)
│   ├── /content/           <-- Markdown di spacepolicies
│   ├── /layouts/           <-- Override layouts specifici
│   ├── /static/            <-- logo.png e risorse statiche
│   └── hugo.yaml           <-- Configurazione e Moduli
```

## 3. Logica degli Asset (Specifiche Tema Zen)

### CSS / SCSS

Il tema Zen è progettato per caricare file di personalizzazione.

- **SCSS:** Zen cerca tipicamente assets/sass/_custom.scss.
- **CSS:** Se non si usa SCSS, si interviene su assets/css/custom.css.
- **Regola IA:** Per modifiche grafiche specifiche di un sito, scrivi in /sito-X/assets/scss/_custom.scss. Hugo darà priorità al file del sito rispetto al tema Zen.

**Nota:** Se entrambi i siti condividono molti stili comuni, questi vanno duplicati in entrambi i file _custom.scss. In futuro, se emergono molte duplicazioni, si potrà valutare l'introduzione di una cartella condivisa.

### JavaScript

Zen non ha un hook "standard" per un custom.js senza toccare i layout.

- **Regola IA:** Per aggiungere JS personalizzato, sovrascrivi il partial layouts/partials/head-custom.html o body-end-custom.html (se presenti in Zen) o direttamente head.html.
- Posiziona il file JS in /sito-X/assets/js/ per ciascun sito.

### Static (Loghi e Media)

- I file in static/ vengono copiati nella root del sito.
- Se il partial del logo cerca img/logo.png, l'IA deve sapere che posizionando due file diversi in /spacestrategies/static/img/logo.png e /spacepolicies/static/img/logo.png, ogni sito avrà il suo logo corretto nonostante il codice HTML sia identico nel tema.

## 4. Configurazione hugo.yaml (La Catena di Montaggio)

Ogni sito deve dichiarare il tema Zen nel proprio file di configurazione.

**Esempio per /spacestrategies/hugo.yaml:**

```yaml
module:
  imports:
    - path: github.com/frjo/hugo-theme-zen
```

**Esempio per /spacepolicies/hugo.yaml:**

```yaml
module:
  imports:
    - path: github.com/frjo/hugo-theme-zen
```

*Nota: Hugo applica gli override automaticamente. La cartella locale del sito ha SEMPRE la precedenza assoluta rispetto al tema.*

## 5. Regole Decisionali per l'IA

Quando l'utente chiede una modifica, l'IA deve seguire questo processo logico:

1. **È una modifica di contenuto?** → Agisci solo in /sito-X/content/.
2. **È una modifica estetica per un sito?** → Crea/modifica _custom.scss in /sito-X/assets/scss/.
3. **È una modifica estetica per entrambi i siti?** → Applica la modifica in entrambi i file /spacestrategies/assets/scss/_custom.scss e /spacepolicies/assets/scss/_custom.scss.
4. **È un asset (logo, favicon)?** → Va in /sito-X/static/ (ogni sito ha i suoi asset).
5. **È una funzione strutturale (layout)?** → Verifica se Zen lo permette via config; se no, sovrascrivi il partial in /sito-X/layouts/partials/.

## 6. Comandi Utili

**Inizializzazione Hugo Modules (eseguire nella cartella di ciascun sito):**
```bash
cd /26space/spacestrategies
hugo mod init github.com/tuousername/26space/spacestrategies
hugo mod get -u

cd /26space/spacepolicies
hugo mod init github.com/tuousername/26space/spacepolicies
hugo mod get -u
```

**Server di sviluppo locale:**
```bash
cd /26space/spacestrategies && hugo server -D
cd /26space/spacepolicies && hugo server -D
```

**Build siti:**
```bash
cd /26space/spacestrategies && hugo
cd /26space/spacepolicies && hugo
```

**Aggiornare tema Zen:**
```bash
hugo mod get -u github.com/frjo/hugo-theme-zen
```

------

**Fine del Manuale.**
*L'IA è ora istruita a rispettare la separazione tra il Modulo Zen (base) e le cartelle dei due siti (identità specifiche).*
