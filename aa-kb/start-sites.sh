#!/bin/bash

# Script per avviare entrambi i siti Hugo
# SpaceStrategies su porta 1313
# SpacePolicies su porta 1314

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Ottieni l'indirizzo IP locale
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo "Avvio dei siti Hugo..."

# Cleanup preventivo: se le porte sono in uso, prova a liberarle
if lsof -i :1313 > /dev/null 2>&1 || lsof -i :1314 > /dev/null 2>&1; then
    echo "Porte già in uso. Eseguo cleanup..."
    "$SCRIPT_DIR/stop-sites.sh"
    sleep 2

    # Verifica nuovamente dopo il cleanup
    if lsof -i :1313 > /dev/null 2>&1; then
        echo "✗ Errore: porta 1313 ancora occupata dopo cleanup"
        exit 1
    fi

    if lsof -i :1314 > /dev/null 2>&1; then
        echo "✗ Errore: porta 1314 ancora occupata dopo cleanup"
        exit 1
    fi

    echo "✓ Porte liberate con successo"
fi

# Avvia SpaceStrategies su porta 1313
echo "Avvio SpaceStrategies su http://localhost:1313"
cd "$ROOT_DIR/spacestrategies"
hugo server --bind 0.0.0.0 --disableFastRender --port 1313 > /dev/null 2>&1 &

# Avvia SpacePolicies su porta 1314
echo "Avvio SpacePolicies su http://localhost:1314"
cd "$ROOT_DIR/spacepolicies"
hugo server --bind 0.0.0.0 --disableFastRender --port 1314 > /dev/null 2>&1 &

# Attendi e verifica che i server siano partiti
echo "Attendo avvio dei server..."
sleep 3

# Verifica più robusta con retry
max_retries=5
retry=0
both_running=false

while [ $retry -lt $max_retries ]; do
    if lsof -i :1313 -sTCP:LISTEN > /dev/null 2>&1 && lsof -i :1314 -sTCP:LISTEN > /dev/null 2>&1; then
        both_running=true
        break
    fi
    echo "   Attesa avvio... (tentativo $((retry + 1))/$max_retries)"
    sleep 2
    retry=$((retry + 1))
done

echo ""
if [ "$both_running" = true ]; then
    echo "✓ Entrambi i siti sono attivi!"
    echo ""
    echo "Accesso locale:"
    echo "   SpaceStrategies: http://localhost:1313"
    echo "   SpacePolicies:   http://localhost:1314"
    echo ""
    echo "Accesso dalla rete locale:"
    echo "   SpaceStrategies: http://$LOCAL_IP:1313"
    echo "   SpacePolicies:   http://$LOCAL_IP:1314"
    echo ""
    echo "Per fermare i server, esegui: ./stop-sites.sh"
else
    echo "✗ Errore nell'avvio di uno o entrambi i server."

    # Diagnostica
    if ! lsof -i :1313 -sTCP:LISTEN > /dev/null 2>&1; then
        echo "   SpaceStrategies (porta 1313) non è partito"
    fi
    if ! lsof -i :1314 -sTCP:LISTEN > /dev/null 2>&1; then
        echo "   SpacePolicies (porta 1314) non è partito"
    fi

    echo ""
    echo "Eseguo cleanup dei processi falliti..."
    "$SCRIPT_DIR/stop-sites.sh"
    exit 1
fi
