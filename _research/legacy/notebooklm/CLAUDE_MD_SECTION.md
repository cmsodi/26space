## NotebookLM — Procedura blindata (solo CLI `nlm`)

> **DIVIETO ASSOLUTO**: NON usare MAI i tool MCP `notebooklm-mcp` (notebook_create,
> notebook_query, source_add, studio_create, ecc.). Il server MCP dà SEMPRE
> "Authentication expired" indipendentemente da refresh_auth, save_auth_tokens,
> reload VSCode, o qualsiasi altro tentativo. NON perdere tempo a riprovare.
> Usare ESCLUSIVAMENTE il CLI `nlm` via Bash.

### Avvio sessione — Eseguire SEMPRE all'inizio

Quando l'utente chiede operazioni NotebookLM, eseguire questi step **nell'ordine esatto**.
Prerequisito: Chrome deve essere aperto con una sessione Google attiva su notebooklm.google.com.

```bash
# STEP 1 — Estrarre cookies freschi da Chrome
#   Richiede Chrome aperto. Connette via Chrome DevTools Protocol.
notebooklm-mcp-auth
```

Attendere output "SUCCESS". Se fallisce, l'utente deve aprire Chrome su notebooklm.google.com e riprovare.

```bash
# STEP 2 — Convertire auth.json in formato cookie-string per nlm CLI
python3 -c "
import json
with open('/home/cms/.notebooklm-mcp-cli/auth.json') as f:
    d = json.load(f)
cookie_str = '; '.join(f'{k}={v}' for k,v in d['cookies'].items())
with open('/tmp/nlm_cookie_str.txt', 'w') as f:
    f.write(cookie_str)
print(f'OK: {len(cookie_str)} chars')
"
```

```bash
# STEP 3 — Importare nel profilo nlm CLI
nlm login --manual -f /tmp/nlm_cookie_str.txt
```

Attendere output "Successfully authenticated!".

```bash
# STEP 4 — Verificare che funziona
nlm notebook list
```

Se restituisce la lista dei notebook in JSON, l'autenticazione è attiva.
Se dà errore, ripetere da STEP 1 (i cookies potrebbero essere scaduti).

### Comandi `nlm` CLI — Riferimento completo

```bash
# ── Notebook ──
nlm notebook list                                    # Lista tutti i notebook
nlm notebook create "Titolo Notebook"                # Crea notebook
nlm notebook get NOTEBOOK_ID                         # Dettagli notebook

# ── Fonti ──
nlm source list NOTEBOOK_ID                          # Lista fonti nel notebook
nlm source add NOTEBOOK_ID --url "https://..."       # Aggiungi fonte da URL
nlm source add NOTEBOOK_ID --text "contenuto" --title "Titolo"  # Fonte testo

# ── Ricerca web ──
nlm research start "query" -n NOTEBOOK_ID -m fast    # ~30s, ~10 fonti
nlm research start "query" -n NOTEBOOK_ID -m deep    # ~5min, ~40 fonti
nlm research status NOTEBOOK_ID                      # Polling stato ricerca
nlm research import NOTEBOOK_ID TASK_ID              # Importa fonti trovate

# ── Query (la funzione principale) ──
nlm query notebook NOTEBOOK_ID "domanda"             # Query sulle fonti
nlm query notebook NOTEBOOK_ID "domanda" -c CONV_ID  # Follow-up conversazione

# ── Studio (generazione artefatti) ──
nlm studio create NOTEBOOK_ID --type audio           # Podcast
nlm studio create NOTEBOOK_ID --type report          # Report
nlm studio status NOTEBOOK_ID                        # Stato generazione
```

### Note operative per Claude

1. **Ad ogni nuova sessione**: eseguire STEP 1–4 prima di qualsiasi comando `nlm`.
   I cookies Google scadono frequentemente (~ore). Non dare per scontato che
   l'auth della sessione precedente sia ancora valida.

2. **Timeout query**: le query `nlm query notebook` possono richiedere fino a
   120 secondi. Usare `--timeout 300000` nel tool Bash.

3. **Output JSON**: i comandi `nlm` restituiscono JSON. Per processarli in pipe
   usare `python3 -c "import json,sys; ..."` (NON `jq`, potrebbe non essere installato).

4. **Conversation ID**: `nlm query` restituisce un `Conversation ID` alla fine
   dell'output. Salvarlo per follow-up con `-c CONV_ID`.

5. **Ricerca web**: dopo `research start`, fare polling con `research status`
   fino a `status: completed`, poi `research import` per aggiungere le fonti.

### Path dei file (riferimento interno)

| Cosa | Path |
|------|------|
| `notebooklm-mcp-auth` output | `~/.notebooklm-mcp-cli/auth.json` |
| `nlm` CLI profilo default | `~/.notebooklm-mcp-cli/profiles/default/` |
| Server MCP (IGNORARE) | `~/.notebooklm-mcp/auth.json` |
