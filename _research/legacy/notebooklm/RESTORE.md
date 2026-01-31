# NotebookLM Integration — Restore Guide

Questa cartella contiene tutto il necessario per ripristinare l'integrazione
NotebookLM nel progetto _research. L'integrazione è stata disattivata perché
il server MCP dava costantemente "Authentication expired", rendendo inutilizzabili
i tool MCP diretti. L'unico metodo funzionante era il CLI `nlm` via Bash.

## Contenuto di questa cartella

| File | Descrizione |
|------|-------------|
| `RESTORE.md` | Questo file |
| `CLAUDE_MD_SECTION.md` | Sezione da aggiungere a CLAUDE.md |
| `mcp_template.json` | Template `.mcp.json` (senza cookies) |

## Come ripristinare

### 1. Ripristinare .mcp.json (server MCP)

Copiare il template nella root del progetto:

```bash
cp legacy/notebooklm/mcp_template.json .mcp.json
```

Poi aggiornare i valori di autenticazione. Per ottenerli:

```bash
# Prerequisito: Chrome aperto su notebooklm.google.com
notebooklm-mcp-auth
```

Poi estrarre cookies, CSRF token e session ID dal file
`~/.notebooklm-mcp-cli/auth.json` e inserirli in `.mcp.json`.

> **Nota**: il server MCP ha storicamente dato problemi di autenticazione.
> Il metodo CLI (`nlm`) è risultato molto piu affidabile.

### 2. Aggiungere la sezione a CLAUDE.md

Aprire `CLAUDE.md` e incollare il contenuto di `CLAUDE_MD_SECTION.md`
dopo la sezione "## Operating Instructions", prima di "## Context Management".

### 3. Verificare che il CLI funziona

```bash
# Step 1 — Estrarre cookies da Chrome
notebooklm-mcp-auth

# Step 2 — Convertire per nlm CLI
python3 -c "
import json
with open('/home/cms/.notebooklm-mcp-cli/auth.json') as f:
    d = json.load(f)
cookie_str = '; '.join(f'{k}={v}' for k,v in d['cookies'].items())
with open('/tmp/nlm_cookie_str.txt', 'w') as f:
    f.write(cookie_str)
print(f'OK: {len(cookie_str)} chars')
"

# Step 3 — Login
nlm login --manual -f /tmp/nlm_cookie_str.txt

# Step 4 — Test
nlm notebook list
```

Se restituisce JSON con la lista dei notebook, l'integrazione e attiva.

## Dipendenze esterne

- `notebooklm-mcp-auth` — Estrae cookies da Chrome via DevTools Protocol
- `nlm` — CLI NotebookLM (`pip install notebooklm-mcp` o equivalente)
- Chrome con sessione Google attiva su notebooklm.google.com

## Path di riferimento

| Cosa | Path |
|------|------|
| Auth CLI | `~/.notebooklm-mcp-cli/auth.json` |
| Profilo CLI | `~/.notebooklm-mcp-cli/profiles/default/` |
| Auth MCP server | `~/.notebooklm-mcp/auth.json` |
| Config MCP progetto | `_research/.mcp.json` (gitignored) |
