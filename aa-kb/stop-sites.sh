#!/bin/bash

# Script per fermare entrambi i siti Hugo

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.hugo-pids"

echo "🛑 Arresto dei siti Hugo..."

if [ ! -f "$PID_FILE" ]; then
    echo "❌ Nessun file PID trovato. I server potrebbero essere già spenti."
    exit 1
fi

# Leggi e termina ogni processo
while read -r pid; do
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "   Arresto processo $pid"
        kill "$pid"
    else
        echo "   Processo $pid già terminato"
    fi
done < "$PID_FILE"

# Rimuovi il file PID
rm -f "$PID_FILE"

echo "✅ Tutti i server Hugo sono stati arrestati"
