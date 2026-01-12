#!/bin/bash

# Script per avviare entrambi i siti Hugo
# SpaceStrategies su porta 1313
# SpacePolicies su porta 1314

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PID_FILE="$SCRIPT_DIR/.hugo-pids"

echo "🚀 Avvio dei siti Hugo..."

# Rimuovi file PID precedente se esistente
rm -f "$PID_FILE"

# Avvia SpaceStrategies su porta 1313
echo "📡 Avvio SpaceStrategies su http://localhost:1313"
cd "$ROOT_DIR/spacestrategies"
hugo server --disableFastRender --port 1313 > /dev/null 2>&1 &
STRATEGIES_PID=$!
echo "$STRATEGIES_PID" >> "$PID_FILE"
echo "   PID: $STRATEGIES_PID"

# Avvia SpacePolicies su porta 1314
echo "📡 Avvio SpacePolicies su http://localhost:1314"
cd "$ROOT_DIR/spacepolicies"
hugo server --disableFastRender --port 1314 > /dev/null 2>&1 &
POLICIES_PID=$!
echo "$POLICIES_PID" >> "$PID_FILE"
echo "   PID: $POLICIES_PID"

echo ""
echo "✅ Entrambi i siti sono attivi!"
echo "   SpaceStrategies: http://localhost:1313"
echo "   SpacePolicies:   http://localhost:1314"
echo ""
echo "Per fermare i server, esegui: ./stop-sites.sh"
