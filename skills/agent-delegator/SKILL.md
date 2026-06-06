---
name: agent-delegator
description: >
  Vollständiger Delegation-Workflow: Analysiere einen Task, entscheide ob er
  an einen günstigeren Agenten delegiert werden kann, führe die Delegation aus
  und konsolidiere das Ergebnis.

  Trigger — verwende diesen Skill immer wenn:
  - "delegiere das", "schick das an ein günstigeres Modell", "spare Tokens"
  - "nutze Ollama", "lass das Mercury machen", "lokal/sensibel verarbeiten", "weiterleiten"
  - "delegiere und konsolidiere", "merge die Ergebnisse", "prüfe das Delegationsergebnis"
  - Claude eine komplexe Aufgabe in Subtasks zerlegt und prüfen soll, welche Teile
    offloaded werden können
  - "delegate", "route to cheaper model", "consolidate results"

  Trigger auch automatisch, wenn der User Token-Kosten sparen will oder einen
  Task beschreibt, der klar abgegrenzt und repetitiv ist.
version: 0.6.3
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

# Status ausgeben (auf drei reale Ziele beschränkt)
echo ""
echo "Delegationsziele:"
[[ -n "$OLLAMA_API_KEY"   ]] && echo "  ✅ OLLAMA_API_KEY    (${#OLLAMA_API_KEY} Zeichen) — PRIMÄR (Ollama Cloud)" || echo "  ❌ OLLAMA_API_KEY    nicht gesetzt (primäres Ziel!)"
[[ -n "$INCEPTION_API_KEY" ]] && echo "  ✅ INCEPTION_API_KEY (${#INCEPTION_API_KEY} Zeichen) — optional (Mercury 2, ⚡)" || echo "  ⚠️  INCEPTION_API_KEY nicht gesetzt (optional)"
# GX10/DGX-Spark: lokal im Heimnetz, kein Key — nur Erreichbarkeit prüfen
if curl -sf --max-time 4 "http://gx10-74ac.amhomenet.de:8080/health" >/dev/null 2>&1; then
  echo "  ✅ GX10 lokal         erreichbar (gx10-74ac.amhomenet.de:8080) — für sensible Aufgaben"
else
  echo "  ⚠️  GX10 lokal         nicht erreichbar (nur im Heimnetz; llama-server gestartet?)"
fi
```

Falls der Ollama-Key fehlt: User fragen und im Chat nennen lassen, dann exportieren:
```bash
export OLLAMA_API_KEY="key-hier"   # primäres Ziel
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

### Ziel- & Modell-Empfehlung

Nur drei reale Ziele (Stand 2026-06).

> **Kostenmodell (wichtig fürs Routing):** Ollama Cloud läuft auf einer **monatlichen Flatrate** →
> keine Token-Kosten, egal welches Modell. Mercury 2 ist per-Token (günstig). GX10 ist lokal/gratis.
> Sinn der Delegation ist, teure **Claude-/Anthropic-Tokens** zu sparen → großzügig an Ollama Cloud
> delegieren, auch mit starken Modellen.

- **Ollama Cloud** — 🟢 PRIMÄR. OpenAI-kompatibel, monatliche Flatrate (keine Token-Kosten). Modell frei wählbar:
  - einfach: `gemma3:4b`, `ministral-3:3b` ← Default (schnellste Antwort)
  - mittel: `gemma3:12b`, `ministral-3:8b`
  - stark/Code: `gemma4:31b`, `gpt-oss:20b`, `qwen3-coder:480b`, `glm-4.7`
  - starkes Reasoning: `nemotron-3-ultra` (550B MoE, 1M Kontext, Top-Open-Weight)
  - Vision (Bild/Video): `kimi-k2.6` (1T MoE, nativ multimodal) — einziges Cloud-Modell mit Vision
  - (Katalog ändert sich — Live-Liste via `--list-models`, siehe Option A)
  - Modellwahl nach **Eignung & Geschwindigkeit**, nicht nach Kosten: kleine Modelle = schnellere
    Antwort; `nemotron-3-ultra`/`kimi-k2.6` ohne Mehrkosten, aber langsamer → nur wo Qualität/Vision nötig.
- **Inception Mercury 2** — ⚡ optional, schnellste Option (~1000 tok/s, 128K Kontext), `mercury-2`. Für reine Speed-Tasks.
- **GX10 / DGX-Spark (lokal)** — 🔒 für sensible/datenschutzkritische Aufgaben, läuft komplett im Heimnetz.
  - Nur **llama-server** (Router-Modus, kein vLLM): `GLM-4.7-Flash` (Tool-Calling, Default) · `Qwen3.6-27B-MTP` (Reasoning)

---

## Phase 2: Delegation ausführen

> Drei Ziele. Reihenfolge: **Ollama Cloud (primär)** → Mercury 2 (Speed) → GX10 lokal (sensibel).
> Alle drei sind OpenAI-kompatibel (`/v1/chat/completions`).

### Option A — Ollama Cloud 🟢 (Primär)

```bash
# .env laden (falls noch nicht geschehen)
[[ -f "$SKILL_DIR/.env" ]] && set -a && source "$SKILL_DIR/.env" && set +a
[[ -z "$OLLAMA_API_KEY" ]] && for _p in $(find /sessions ~/.local-plugins ~/.claude -name '.env' -path '*agent-delegator*' 2>/dev/null); do source "$_p" && break; done

MODEL="gemma3:4b"   # einfach: gemma3:4b/ministral-3:3b · mittel: gemma3:12b · stark: gemma4:31b/gpt-oss:20b
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
print(json.load(sys.stdin)['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

**Verfügbare Ollama-Cloud-Modelle anzeigen** (Katalog ändert sich — immer prüfen):
```bash
curl -sfL -H "Authorization: Bearer ${OLLAMA_API_KEY}" \
  "https://ollama.com/v1/models" | python3 -c "
import json, sys
for m in json.load(sys.stdin).get('data', []):
    print(m['id'])
" | sort
```

### Option B — Inception Mercury 2 ⚡ (optional, schnellste Option)

Diffusion-LLM mit ~1000 Tokens/Sek und 128K Kontext.
API-Key: https://platform.inceptionlabs.ai → API Keys (neue Accounts: kostenlose Tokens).

```bash
[[ -z "$INCEPTION_API_KEY" ]] && for _p in $(find /sessions ~/.local-plugins ~/.claude -name '.env' -path '*agent-delegator*' 2>/dev/null); do source "$_p" && break; done
[[ -z "$INCEPTION_API_KEY" ]] && { echo "❌ Kein INCEPTION_API_KEY — nutze Ollama Cloud (Option A)." >&2; exit 1; }

MODEL="mercury-2"
PROMPT="AUFGABE HIER"

RESPONSE=$(curl -sfL \
  --max-time 120 \
  -H "Authorization: Bearer ${INCEPTION_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [
    {'role': 'system', 'content': 'Du bist ein präziser Assistent. Erledige die Aufgabe genau. Antworte nur mit dem Ergebnis.'},
    {'role': 'user', 'content': sys.argv[2]}
  ],
  'temperature': 0.75, 'max_tokens': 8192,
  'reasoning_effort': 'low'   # 'instant' = max Speed · 'medium'/'high' = mehr Tiefe
}))" "$MODEL" "$PROMPT")" \
  "https://api.inceptionlabs.ai/v1/chat/completions")

echo "$RESPONSE" | python3 -c "
import json, sys
print(json.load(sys.stdin)['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

### Option C — GX10 / DGX-Spark 🔒 (lokal, für sensible Aufgaben)

Läuft komplett im Heimnetz, kein externer API-Call, kein API-Key. Repo: `ydmw74/spark-74ac`.

> Lokal läuft **nur llama-server** (Router-Modus, Port 8080 — kein vLLM):
> - `MODEL="GLM-4.7-Flash"` (Tool-Calling, Default)
> - `MODEL="Qwen3.6-27B-MTP"` (Reasoning)
>
> Laufendes Modell prüfen: `curl -s http://gx10-74ac.amhomenet.de:8080/v1/models`

```bash
BASE_URL="http://gx10-74ac.amhomenet.de:8080/v1"
MODEL="GLM-4.7-Flash"   # Reasoning-Tasks: Qwen3.6-27B-MTP
PROMPT="AUFGABE HIER"

curl -sf --max-time 180 \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "
import json, sys
print(json.dumps({
  'model': sys.argv[1],
  'messages': [
    {'role': 'system', 'content': 'Du bist ein präziser Assistent. Erledige die Aufgabe genau. Antworte nur mit dem Ergebnis.'},
    {'role': 'user', 'content': sys.argv[2]}
  ],
  'temperature': 0.3, 'max_tokens': 8192
}))" "$MODEL" "$PROMPT")" \
  "${BASE_URL}/chat/completions" \
  | python3 -c "
import json, sys
print(json.load(sys.stdin)['choices'][0]['message']['content'])
" > /tmp/delegate_result.txt

cat /tmp/delegate_result.txt
```

### Option D — Mehrere Subtasks parallel (Ollama Cloud)

```bash
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
