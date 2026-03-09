---
name: agent-delegator
description: >
  Vollständiger Delegation-Workflow: Analysiere einen Task, entscheide ob er
  an einen günstigeren Agenten delegiert werden kann, führe die Delegation aus
  und konsolidiere das Ergebnis.

  Trigger — verwende diesen Skill immer wenn:
  - "delegiere das", "schick das an ein günstigeres Modell", "spare Tokens"
  - "nutze Ollama", "lass das GPT-4o-mini machen", "weiterleiten"
  - "delegiere und konsolidiere", "merge die Ergebnisse", "prüfe das Delegationsergebnis"
  - Claude eine komplexe Aufgabe in Subtasks zerlegt und prüfen soll, welche Teile
    offloaded werden können
  - "delegate", "route to cheaper model", "consolidate results"

  Trigger auch automatisch, wenn der User Token-Kosten sparen will oder einen
  Task beschreibt, der klar abgegrenzt und repetitiv ist.
version: 0.5.1
---

# Agent Delegator

Claude ist das Orchestrierungsgehirn. Es delegiert klar abgegrenzte, repetitive
Subtasks an günstigere Agenten und behält komplexes Reasoning, strategische
Entscheidungen und die Qualitätssicherung selbst.

```
Aufgabe
  │
  ▼
[Phase 1: Analyse & Routing]
  ├── einfach/mittel ──► [Günstiger Agent ausführen]
  │                               │
  │                               ▼
  │                      [Phase 2: Prüfen & Konsolidieren]
  │                               │
  └── komplex ──► [Claude direkt] ┘
                                  │
                                  ▼
                         Ergebnis an User
```

> **Hinweis:** Dieser Skill funktioniert vollständig ohne externe Scripts.
> Alle Logik ist in diesen Anweisungen eingebettet.

---

## Setup: API-Keys finden

Beim Start diesen Block ausführen — er sucht .env automatisch in bekannten Pfaden:

```bash
# .env automatisch suchen und laden
_env_loaded=false
for _p in \
  "$SKILL_DIR/.env" \
  "$(find /sessions/*/mnt/*/agent-delegator-config -name '.env' 2>/dev/null | head -1)" \
  "$(find /sessions -maxdepth 8 -name '.env' -path '*/agent-delegator*' 2>/dev/null | head -1)" \
  "$(find ~/.skills ~/.local-plugins -name '.env' 2>/dev/null | head -1)"
do
  if [[ -f "$_p" ]]; then
    set -a && source "$_p" && set +a
    echo "✅ .env geladen: $_p"
    _env_loaded=true
    break
  fi
done
[[ "$_env_loaded" == false ]] && echo "⚠️  Keine .env gefunden — API-Keys müssen manuell gesetzt werden."

# Status ausgeben
echo ""
echo "API-Keys Status:"
[[ -n "$INCEPTION_API_KEY" ]] && echo "  ✅ INCEPTION_API_KEY (${#INCEPTION_API_KEY} Zeichen)" || echo "  ❌ INCEPTION_API_KEY nicht gesetzt"
[[ -n "$OLLAMA_API_KEY"  ]] && echo "  ✅ OLLAMA_API_KEY  (${#OLLAMA_API_KEY} Zeichen)" || echo "  ❌ OLLAMA_API_KEY  nicht gesetzt"
[[ -n "$OPENAI_API_KEY"  ]] && echo "  ✅ OPENAI_API_KEY  (${#OPENAI_API_KEY} Zeichen)" || echo "  ❌ OPENAI_API_KEY  nicht gesetzt"
[[ -n "$GEMINI_API_KEY"  ]] && echo "  ✅ GEMINI_API_KEY  (${#GEMINI_API_KEY} Zeichen)" || echo "  ❌ GEMINI_API_KEY  nicht gesetzt"
[[ -n "$GROQ_API_KEY"    ]] && echo "  ✅ GROQ_API_KEY    (${#GROQ_API_KEY} Zeichen)" || echo "  ❌ GROQ_API_KEY    nicht gesetzt"
[[ -n "$OPENROUTER_API_KEY" ]] && echo "  ✅ OPENROUTER_API_KEY (${#OPENROUTER_API_KEY} Zeichen)" || echo "  ❌ OPENROUTER_API_KEY nicht gesetzt"
```

Falls kein Key gefunden: User fragen welchen Provider er nutzen möchte,
und Key im Chat nennen lassen. Dann direkt als env-Variable exportieren:
```bash
export OLLAMA_API_KEY="key-hier"   # Beispiel
```

---

## Phase 1: Task klassifizieren (Claude-Reasoning)

**Kein Script nötig.** Claude bewertet den Task nach diesen Kriterien:

### Komplexitäts-Rubrik

| Kriterium | EINFACH → delegieren | MITTEL → delegieren + prüfen | KOMPLEX → Claude direkt |
|-----------|---------------------|------------------------------|------------------------|
| Reasoning | Keine Schlussfolgerungen | Begrenzte Schlussfolgerungen | Mehrstufige Analyse |
| Kontext | Self-contained, wenig Kontext | Mäßig kontextabhängig | Tiefer Projekt-Kontext |
| Fehlerfolgen | Leicht korrigierbar | Korrigierbar mit Aufwand | Schwer rückgängig |
| Kreativität | Formatierung, Transformation | Template, Strukturierung | Strategische Entscheidung |

### EINFACH → sicher delegieren
Textformatierung, Übersetzung, Template-Befüllung, Codekommentare/Docstrings,
Changelog aus Commit-Messages, Meeting-Protokoll aus Stichpunkten,
Datums-/Zeitformatierung, einfache Zusammenfassungen, Tabellenkonvertierung.

### MITTEL → delegieren mit anschließender Prüfung
Unit-Test-Generierung, einfache Code-Reviews, README/API-Dokumentation,
User Stories aus Feature-Briefings, RACI-Matrix-Entwürfe, Meeting-Agenden,
Risiko-Templates befüllen.

### KOMPLEX → Claude direkt (nicht delegieren)
Architektur- und Technologieentscheidungen, Risikoanalyse und -bewertung,
Stakeholder-Kommunikation, Sicherheits-/Compliance-Prüfungen,
strategische Roadmaps, Change Management, mehrstufiges Debugging.

### Modell-Empfehlung
- **Mercury 2 (Inception)** — ⚡ Primär: ~1000 tok/s, 128K Kontext, OpenAI-kompatibel, sehr günstig
- **OpenRouter → inception/mercury-2** — Fallback für Mercury 2 ohne direkten API-Key
- **Ollama gemma3:4b** — Schnell, gut für Formatierung, Übersetzung, einfache Umwandlungen
- **Ollama gemma3:12b** — Besser für Code, Dokumentation, strukturierte Ausgaben
- **gpt-4o-mini** — Wenn Ollama nicht verfügbar, gute Allround-Option
- **Groq Llama** — Sehr schnell, günstig, für repetitive Tasks
- **OpenRouter (free tier)** — Kostenlos, 300+ Modelle, ideal zum Ausprobieren
- **OpenRouter Llama/Mistral** — Günstig, breite Modellauswahl, ein einziger API-Key

---

## Phase 2: Delegation ausführen

### Option A — Mercury 2 / Inception Labs ⚡ (Primär — schnellstes Modell)

Mercury 2 ist ein Diffusion-LLM mit ~1000 Tokens/Sek und 128K Kontext.
API-Key: https://platform.inceptionlabs.ai → API Keys (neue Accounts: 10M kostenlose Tokens)

**Fallback:** Falls kein `INCEPTION_API_KEY`, automatisch auf OpenRouter umleiten:
`MODEL="inception/mercury-2"` + `BASE_URL="https://openrouter.ai/api/v1"` + `API_KEY="$OPENROUTER_API_KEY"`

```bash
# .env laden
[[ -z "$INCEPTION_API_KEY" ]] && for _p in $(find /sessions ~/.local-plugins -name '.env' -path '*agent-delegator*' 2>/dev/null); do source "$_p" && break; done

# Auto-Fallback: Inception direkt, oder OpenRouter als Fallback
if [[ -n "$INCEPTION_API_KEY" ]]; then
  _BASE_URL="https://api.inceptionlabs.ai/v1"
  _API_KEY="$INCEPTION_API_KEY"
  _MODEL="mercury-2"
  echo "▶ Mercury 2 via Inception Labs (direkt)"
elif [[ -n "$OPENROUTER_API_KEY" ]]; then
  _BASE_URL="https://openrouter.ai/api/v1"
  _API_KEY="$OPENROUTER_API_KEY"
  _MODEL="inception/mercury-2"
  echo "▶ Mercury 2 via OpenRouter (Fallback)"
else
  echo "❌ Kein API-Key für Mercury 2. Bitte INCEPTION_API_KEY oder OPENROUTER_API_KEY setzen." >&2
  exit 1
fi

PROMPT="AUFGABE HIER"

RESPONSE=$(curl -sfL \
  --max-time 120 \
  -H "Authorization: Bearer ${_API_KEY}" \
  -H "Content-Type: application/json" \
  $([ "$_BASE_URL" = "https://openrouter.ai/api/v1" ] && echo '-H "HTTP-Referer: https://github.com/ydmw74/agent-delegator" -H "X-Title: Agent Delegator"') \
  -d "$(python3 -c "
import json, sys
model, prompt = sys.argv[1], sys.argv[2]
payload = {
  'model': model,
  'messages': [
    {'role': 'system', 'content': 'Du bist ein präziser Assistent. Erledige die Aufgabe genau. Antworte nur mit dem Ergebnis.'},
    {'role': 'user', 'content': prompt}
  ],
  'temperature': 0.75, 'max_tokens': 8192  # Mercury 2: temp range 0.5-1.0 (default 0.75)
}
# reasoning_effort: 'instant' für maximale Geschwindigkeit, 'low'/'medium'/'high' für mehr Tiefe
if 'mercury' in model:
    payload['reasoning_effort'] = 'low'  # 'instant' für reine Speed-Tasks
print(json.dumps(payload))
)" "$_MODEL" "$PROMPT")" \
  "${_BASE_URL}/chat/completions")

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

### Option B — Ollama Cloud (wenn OLLAMA_API_KEY gesetzt)

```bash
# .env laden (falls noch nicht geschehen)
[[ -f "$SKILL_DIR/.env" ]] && set -a && source "$SKILL_DIR/.env" && set +a
[[ -z "$OLLAMA_API_KEY" ]] && for _p in $(find /sessions ~/.local-plugins -name '.env' -path '*agent-delegator*' 2>/dev/null); do source "$_p" && break; done

MODEL="gemma3:4b"   # oder gemma3:12b für komplexere Tasks
PROMPT="AUFGABE HIER"

RESPONSE=$(curl -sfL \
  --max-time 120 \
  -H "Authorization: Bearer ${OLLAMA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [
    {'role': 'system', 'content': 'Du bist ein präziser Assistent. Erledige die Aufgabe genau. Antworte nur mit dem Ergebnis.'},
    {'role': 'user', 'content': sys.argv[2]}
  ],
  'temperature': 0.3, 'max_tokens': 4096, 'stream': False
}))" "$MODEL" "$PROMPT")" \
  "https://ollama.com/v1/chat/completions")

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

**Verfügbare Ollama-Modelle anzeigen:**
```bash
curl -sfL -H "Authorization: Bearer ${OLLAMA_API_KEY}" \
  "https://ollama.com/v1/models" | python3 -c "
import json, sys
for m in json.load(sys.stdin).get('data', []):
    print(m['id'])
" | sort
```

### Option C — OpenAI-kompatible API (GPT-4o-mini, Gemini Flash, Groq)

```bash
# Konfiguration pro Agent:
# GPT-4o-mini:   BASE_URL="https://api.openai.com/v1"      API_KEY="$OPENAI_API_KEY"  MODEL="gpt-4o-mini"
# Gemini Flash:  BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"  API_KEY="$GEMINI_API_KEY"  MODEL="gemini-2.0-flash"
# Groq Llama:    BASE_URL="https://api.groq.com/openai/v1"  API_KEY="$GROQ_API_KEY"    MODEL="llama-3.1-8b-instant"

BASE_URL="https://api.openai.com/v1"
API_KEY="$OPENAI_API_KEY"
MODEL="gpt-4o-mini"
PROMPT="AUFGABE HIER"

curl -sfL --max-time 120 \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [{'role': 'user', 'content': sys.argv[2]}],
  'temperature': 0.3
}))" "$MODEL" "$PROMPT")" \
  "${BASE_URL}/chat/completions" \
  | python3 -c "
import json, sys
print(json.load(sys.stdin)['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

### Option D — Lokales Ollama (kein API-Key nötig)

```bash
PROMPT="AUFGABE HIER"
MODEL="gemma3:4b"

curl -sf --max-time 120 \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [{'role': 'user', 'content': sys.argv[2]}],
  'stream': False
}))" "$MODEL" "$PROMPT")" \
  "http://localhost:11434/api/chat" \
  | python3 -c "
import json, sys
print(json.load(sys.stdin)['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

### Option F — OpenRouter (300+ Modelle, inkl. kostenlose)

OpenRouter gibt Zugang zu über 300 Modellen mit einem einzigen API-Key.
Kostenlose Tier-Modelle: `google/gemma-3-4b-it:free`, `meta-llama/llama-3.1-8b-instruct:free`, `mistralai/mistral-7b-instruct:free`

```bash
# .env laden (falls noch nicht geschehen)
[[ -z "$OPENROUTER_API_KEY" ]] && for _p in $(find /sessions ~/.local-plugins -name '.env' -path '*agent-delegator*' 2>/dev/null); do source "$_p" && break; done

MODEL="google/gemma-3-4b-it:free"   # kostenlos — oder: meta-llama/llama-3.1-8b-instruct:free
# Günstige Alternativen:              mistralai/mistral-small-3.1-24b-instruct | qwen/qwen-2.5-72b-instruct
PROMPT="AUFGABE HIER"

RESPONSE=$(curl -sfL \
  --max-time 120 \
  -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
  -H "Content-Type: application/json" \
  -H "HTTP-Referer: https://github.com/ydmw74/agent-delegator" \
  -H "X-Title: Agent Delegator" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [
    {'role': 'system', 'content': 'Du bist ein präziser Assistent. Erledige die Aufgabe genau. Antworte nur mit dem Ergebnis.'},
    {'role': 'user', 'content': sys.argv[2]}
  ],
  'temperature': 0.3, 'max_tokens': 4096
}))" "$MODEL" "$PROMPT")" \
  "https://openrouter.ai/api/v1/chat/completions")

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

**Verfügbare kostenlose OpenRouter-Modelle anzeigen:**
```bash
curl -sfL -H "Authorization: Bearer ${OPENROUTER_API_KEY}" \
  "https://openrouter.ai/api/v1/models" | python3 -c "
import json, sys
models = json.load(sys.stdin).get('data', [])
free = [m for m in models if ':free' in m.get('id', '') or m.get('pricing', {}).get('prompt') == '0']
for m in sorted(free, key=lambda x: x['id']):
    print(m['id'])
"
```

### Option G — Mehrere Subtasks parallel

```bash
# Subtasks parallel ausführen (Ollama Cloud Beispiel):
for i in 1 2 3; do
  PROMPT_VAR="SUBTASK_$i"  # Prompt pro Subtask setzen
  ( curl -sfL --max-time 120 \
      -H "Authorization: Bearer ${OLLAMA_API_KEY}" \
      -H "Content-Type: application/json" \
      -d "$(python3 -c "import json,sys; print(json.dumps({'model':'gemma3:4b','messages':[{'role':'user','content':sys.argv[1]}],'stream':False}))" "$PROMPT_VAR")" \
      "https://ollama.com/v1/chat/completions" \
    | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])" \
    > "/tmp/result_${i}.txt"
  ) &
done
wait
for f in /tmp/result_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
```

---

## Phase 3: Ergebnis prüfen & konsolidieren

```bash
cat /tmp/delegate_result.txt
```

Beurteile nach vier Kriterien:

**Vollständigkeit** — Wurde die Aufgabe vollständig erledigt?

**Korrektheit** — Text: Struktur korrekt? Code: syntaktisch und logisch ok? Übersetzung: Bedeutung beibehalten?

**Halluzinations-Check** — Wurden Fakten erfunden? Zahlen, Namen, Daten korrekt übertragen?

**Format-Konformität** — Stimmt das Ausgabeformat mit der Anforderung überein?

### Konsolidierungsmuster

**Muster A — Direkt übernehmen**: Ergebnis vollständig und korrekt, ggf. Kleinkorrekturen.

**Muster B — Korrigieren**: Größtenteils gut, aber Lücken oder Formatfehler — gezielt nachbessern.

**Muster C — Neu bearbeiten**: Unbrauchbar (>30% falsch, fundamental falsches Format). Claude bearbeitet direkt.

**Muster D — Zusammenführen**: Mehrere Subtask-Ergebnisse → Redundanzen entfernen, Widersprüche auflösen, Struktur harmonisieren.

### Transparenz

Kurz erwähnen wenn delegiert wurde — besonders bei Korrekturen:
- *"Ich habe einen günstigeren Agenten für die Formatierung eingesetzt und das Ergebnis geprüft."*
- *"Das Protokoll wurde von einem Hilfsmodell strukturiert; ich habe zwei Fehler korrigiert."*

Nicht erwähnen wenn das Ergebnis direkt und ohne Korrekturen übernommen wurde.
