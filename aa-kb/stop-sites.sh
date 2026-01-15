#!/bin/bash

# Script per fermare entrambi i siti Hugo
# Trova e termina i processi hugo sulle porte 1313 e 1314
# Con terminazione robusta: SIGTERM -> attesa -> SIGKILL se necessario

echo "Arresto dei siti Hugo..."

stopped=0

# Funzione per terminare un processo in modo robusto
# Parametri: $1=porta, $2=nome del sito
stop_hugo_on_port() {
    local port=$1
    local sitename=$2
    local pid

    pid=$(lsof -ti :$port -sTCP:LISTEN 2>/dev/null)

    if [ -n "$pid" ]; then
        echo "   Arresto $sitename (porta $port, PID: $pid)"

        # Prova con SIGTERM (terminazione gentile)
        kill $pid 2>/dev/null

        # Attendi fino a 5 secondi che il processo termini
        local waited=0
        while [ $waited -lt 5 ]; do
            if ! kill -0 $pid 2>/dev/null; then
                echo "   ✓ $sitename terminato correttamente"
                return 0
            fi
            sleep 0.5
            waited=$((waited + 1))
        done

        # Se ancora attivo dopo 5 secondi, usa SIGKILL (terminazione forzata)
        if kill -0 $pid 2>/dev/null; then
            echo "   Terminazione forzata di $sitename (SIGKILL)"
            kill -9 $pid 2>/dev/null
            sleep 1

            if ! kill -0 $pid 2>/dev/null; then
                echo "   ✓ $sitename terminato forzatamente"
                return 0
            else
                echo "   ✗ Impossibile terminare $sitename (PID: $pid)"
                return 1
            fi
        fi
    else
        return 2  # Nessun processo su questa porta
    fi
}

# Ferma processo su porta 1313 (SpaceStrategies)
stop_hugo_on_port 1313 "SpaceStrategies"
result_1313=$?
[ $result_1313 -eq 0 ] && stopped=$((stopped + 1))

# Ferma processo su porta 1314 (SpacePolicies)
stop_hugo_on_port 1314 "SpacePolicies"
result_1314=$?
[ $result_1314 -eq 0 ] && stopped=$((stopped + 1))

# Cleanup finale: verifica che le porte siano libere
sleep 1
port_1313_free=$(lsof -ti :1313 2>/dev/null)
port_1314_free=$(lsof -ti :1314 2>/dev/null)

if [ -n "$port_1313_free" ] || [ -n "$port_1314_free" ]; then
    echo ""
    echo "⚠ Attenzione: alcune porte sono ancora occupate"
    [ -n "$port_1313_free" ] && echo "   Porta 1313 ancora in uso da PID: $port_1313_free"
    [ -n "$port_1314_free" ] && echo "   Porta 1314 ancora in uso da PID: $port_1314_free"
    echo ""
    echo "Eseguo cleanup completo di tutti i processi Hugo..."

    # Cleanup drastico: termina TUTTI i processi hugo
    pkill -TERM hugo 2>/dev/null
    sleep 2
    pkill -KILL hugo 2>/dev/null
    sleep 1

    echo "Cleanup completato"
fi

echo ""
if [ $stopped -eq 0 ]; then
    echo "Nessun server Hugo attivo sulle porte 1313/1314"
else
    echo "✓ Arrestati $stopped server Hugo"
fi
