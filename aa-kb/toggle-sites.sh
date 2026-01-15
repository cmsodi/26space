#!/bin/bash

# Script toggle per avviare/fermare i siti Hugo
# Controlla se i server sono attivi e li avvia/ferma di conseguenza

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Controlla se almeno uno dei server è attivo
if lsof -i :1313 -sTCP:LISTEN > /dev/null 2>&1 || lsof -i :1314 -sTCP:LISTEN > /dev/null 2>&1; then
    # Server attivi - ferma
    zenity --info --title="Hugo Sites" --text="Arresto dei server Hugo..." --timeout=2 2>/dev/null || \
    notify-send "Hugo Sites" "Arresto dei server Hugo..." 2>/dev/null || \
    echo "Arresto dei server Hugo..."

    "$SCRIPT_DIR/stop-sites.sh"

    zenity --info --title="Hugo Sites" --text="Server Hugo arrestati" --timeout=3 2>/dev/null || \
    notify-send "Hugo Sites" "Server Hugo arrestati" 2>/dev/null
else
    # Server non attivi - avvia
    zenity --info --title="Hugo Sites" --text="Avvio dei server Hugo..." --timeout=2 2>/dev/null || \
    notify-send "Hugo Sites" "Avvio dei server Hugo..." 2>/dev/null || \
    echo "Avvio dei server Hugo..."

    "$SCRIPT_DIR/start-sites.sh"

    zenity --info --title="Hugo Sites" --text="Server Hugo avviati!\n\nSpaceStrategies: http://localhost:1313\nSpacePolicies: http://localhost:1314" --timeout=5 2>/dev/null || \
    notify-send "Hugo Sites" "Server Hugo avviati!\nSpaceStrategies: http://localhost:1313\nSpacePolicies: http://localhost:1314" 2>/dev/null
fi
