#!/usr/bin/env bash
# =============================================================================
# Agent Delegator — Ollama Wrapper (lokal & Cloud)
# =============================================================================
# Unterstützt sowohl lokale Ollama-Installationen als auch Ollama Cloud.
# Wechselt automatisch zwischen nativem /api/chat (lokal) und
# OpenAI-kompatiblem /v1/chat/completions (Cloud) je nach Kontext.
#
# Lokal:
#   ./call_ollama.sh --prompt "..." [--model llama3.2]
#
# Ollama Cloud:
#   export OLLAMA_API_KEY=ollama_...   # von https://ollama.com/settings/keys
#   export OLLAMA_HOST=https://api.ollama.com
#   ./call_ollama.sh --prompt "..." --model llama3.2
#
# Eigene Cloud-Instanz:
#   export OLLAMA_HOST=https://mein-server.example.com
#   export OLLAMA_API_KEY=mein-token   # falls auth konfiguriert
#   ./call_ollama.sh --prompt "..."
#
# Sonstiges:
#   ./call_ollama.sh --list-models     # verfügbare Modelle anzeigen
#
# Environment variables:
#   OLLAMA_HOST       Ollama-URL. Wenn mit https:// → Cloud-Modus (Auth + /v1)
#                     Default: http://localhost:11434
#   OLLAMA_API_KEY    API-Key für Cloud oder auth-gesicherte Instanzen
#   OLLAMA_MODEL      Standard-Modell wenn --model nicht gesetzt (default: llama3.2)
#
# Empfohlene Modelle für Delegation (lokal & Cloud):
#   llama3.2          3.2B  — sehr schnell, einfache Formatting-Tasks
#   qwen2.5:7b        7B    — gut für Texte, Code, Dokumente
#   qwen2.5:14b       14B   — stark, empfohlen für mittlere Tasks (~10GB RAM lokal)
#   mistral           7B    — gut für Sprache und strukturierte Ausgaben
#   phi4              14B   — Microsoft, sehr effizient
#   deepseek-r1:8b    8B    — Reasoning-optimiert
# =============================================================================

set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
OLLAMA_API_KEY="${OLLAMA_API_KEY:-}"
MODEL="${OLLAMA_MODEL:-llama3.2}"
PROMPT=""
OUTPUT_FILE=""
VERBOSE=false
TIMEOUT_SECS=120
LIST_MODELS=false
SYSTEM_PROMPT="Du bist ein präziser Assistent. Erledige die gegebene Aufgabe genau und effizient. Antworte nur mit dem Ergebnis, ohne Erklärungen oder Kommentare, außer wenn explizit gefordert."

# ── Argument-Parsing ────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt)        PROMPT="$2";        shift 2 ;;
    --model|-m)      MODEL="$2";         shift 2 ;;
    --output-file)   OUTPUT_FILE="$2";   shift 2 ;;
    --system)        SYSTEM_PROMPT="$2"; shift 2 ;;
    --verbose)       VERBOSE=true;       shift   ;;
    --timeout)       TIMEOUT_SECS="$2";  shift 2 ;;
    --list-models)   LIST_MODELS=true;   shift   ;;
    --help|-h)
      grep '^#' "$0" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Modus-Erkennung ─────────────────────────────────────────────────────────
# Cloud-Modus: wenn Host mit https:// beginnt ODER OLLAMA_API_KEY gesetzt ist
IS_CLOUD=false
if [[ "$OLLAMA_HOST" == https://* ]] || [[ -n "$OLLAMA_API_KEY" ]]; then
  IS_CLOUD=true
fi

# ── Auth-Header ─────────────────────────────────────────────────────────────
AUTH_HEADER=""
if [[ -n "$OLLAMA_API_KEY" ]]; then
  AUTH_HEADER="-H \"Authorization: Bearer ${OLLAMA_API_KEY}\""
fi

# ── Hilfsfunktionen ─────────────────────────────────────────────────────────

curl_with_auth() {
  if [[ -n "$OLLAMA_API_KEY" ]]; then
    curl -sf -H "Authorization: Bearer ${OLLAMA_API_KEY}" "$@"
  else
    curl -sf "$@"
  fi
}

check_reachable() {
  local check_url
  if [[ "$IS_CLOUD" == true ]]; then
    check_url="${OLLAMA_HOST}/v1/models"
  else
    check_url="${OLLAMA_HOST}/api/tags"
  fi

  if ! curl_with_auth "$check_url" > /dev/null 2>&1; then
    if [[ "$IS_CLOUD" == true ]]; then
      echo "Error: Ollama Cloud nicht erreichbar unter ${OLLAMA_HOST}" >&2
      echo "" >&2
      echo "Lösung:" >&2
      echo "  1. API-Key prüfen: export OLLAMA_API_KEY=ollama_..." >&2
      echo "  2. API-Keys verwalten: https://ollama.com/settings/keys" >&2
      echo "  3. Host prüfen: export OLLAMA_HOST=https://api.ollama.com" >&2
    else
      echo "Error: Ollama nicht erreichbar unter ${OLLAMA_HOST}" >&2
      echo "" >&2
      echo "Lösung:" >&2
      echo "  1. Ollama installieren: https://ollama.ai" >&2
      echo "  2. Ollama starten: ollama serve (oder öffne die Ollama-App)" >&2
      echo "  3. Modell laden: ollama pull ${MODEL}" >&2
    fi
    return 1
  fi
  return 0
}

list_models() {
  if [[ "$IS_CLOUD" == true ]]; then
    echo "Verfügbare Cloud-Modelle (${OLLAMA_HOST}):"
    curl_with_auth "${OLLAMA_HOST}/v1/models" | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('data', [])
if not models:
    print('  (keine Modelle gefunden)')
for m in models:
    print(f'  {m.get(\"id\", \"?\")}')
"
  else
    echo "Verfügbare lokale Modelle:"
    curl_with_auth "${OLLAMA_HOST}/api/tags" | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('models', [])
if not models:
    print('  (keine Modelle — lade: ollama pull llama3.2)')
for m in models:
    name = m.get('name', '?')
    size_gb = round(m.get('size', 0) / 1024**3, 1)
    print(f'  {name:<35} {size_gb} GB')
"
  fi
}

# ── Modell-Liste ─────────────────────────────────────────────────────────────
if [[ "$LIST_MODELS" == true ]]; then
  check_reachable && list_models
  exit 0
fi

# ── Eingabe-Validierung ──────────────────────────────────────────────────────
if [[ -z "$PROMPT" ]]; then
  echo "Error: --prompt ist erforderlich" >&2
  exit 1
fi

check_reachable || exit 1

MODE_LABEL="lokal"
[[ "$IS_CLOUD" == true ]] && MODE_LABEL="cloud (${OLLAMA_HOST})"
[[ "$VERBOSE" == true ]] && echo "[delegate/ollama] Modus: $MODE_LABEL | Modell: $MODEL" >&2

# ── API-Aufruf ───────────────────────────────────────────────────────────────
# Cloud: OpenAI-kompatibler Endpunkt /v1/chat/completions
# Lokal: Nativer Endpunkt /api/chat (kennt Ollama-spezifische Felder wie num_predict)

if [[ "$IS_CLOUD" == true ]]; then
  # OpenAI-kompatibler Endpunkt (Cloud + neues Ollama-Format)
  PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({
    'model': sys.argv[1],
    'messages': [
        {'role': 'system', 'content': sys.argv[2]},
        {'role': 'user',   'content': sys.argv[3]},
    ],
    'temperature': 0.3,
    'max_tokens': 4096,
    'stream': False,
}))
" "$MODEL" "$SYSTEM_PROMPT" "$PROMPT")

  ENDPOINT="${OLLAMA_HOST}/v1/chat/completions"

  RESPONSE=$(
    timeout "$TIMEOUT_SECS" curl_with_auth \
      -X POST "$ENDPOINT" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD"
  ) || { handle_timeout_or_error "$?"; exit 1; }

  RESULT=$(echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['choices'][0]['message']['content'])
")
  TOKENS_INFO=$(echo "$RESPONSE" | python3 -c "
import json, sys
u = json.load(sys.stdin).get('usage', {})
print(f\"prompt={u.get('prompt_tokens','?')} completion={u.get('completion_tokens','?')}\")
" 2>/dev/null || echo "n/a")

else
  # Nativer Endpunkt (lokal)
  PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({
    'model': sys.argv[1],
    'messages': [
        {'role': 'system', 'content': sys.argv[2]},
        {'role': 'user',   'content': sys.argv[3]},
    ],
    'stream': False,
    'options': {'temperature': 0.3, 'num_predict': 4096},
}))
" "$MODEL" "$SYSTEM_PROMPT" "$PROMPT")

  RESPONSE=$(
    timeout "$TIMEOUT_SECS" curl -sf \
      -X POST "${OLLAMA_HOST}/api/chat" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD"
  ) || {
    EXIT_CODE=$?
    [[ $EXIT_CODE -eq 124 ]] && echo "Error: Timeout nach ${TIMEOUT_SECS}s — kleineres Modell wählen" >&2 \
      || echo "Error: Ollama-API-Aufruf fehlgeschlagen — ollama pull $MODEL" >&2
    exit 1
  }

  RESULT=$(echo "$RESPONSE" | python3 -c "
import json, sys
print(json.load(sys.stdin)['message']['content'])
")
  TOKENS_INFO=$(echo "$RESPONSE" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(f\"prompt={d.get('prompt_eval_count','?')} completion={d.get('eval_count','?')}\")
" 2>/dev/null || echo "n/a")
fi

# ── Ergebnis ausgeben ────────────────────────────────────────────────────────
if [[ -z "$RESULT" ]]; then
  echo "Error: Leere Antwort von Ollama" >&2
  exit 1
fi

[[ "$VERBOSE" == true ]] && echo "[delegate/ollama] Tokens: $TOKENS_INFO" >&2

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$RESULT" > "$OUTPUT_FILE"
  [[ "$VERBOSE" == true ]] && echo "[delegate/ollama] Gespeichert: $OUTPUT_FILE" >&2
else
  echo "$RESULT"
fi
