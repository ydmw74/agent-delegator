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
version: 0.2.0
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

---

## Pfad-Setup

Beim Laden dieses Skills siehst du oben: `Base directory for this skill: /pfad/zum/skill`

Setze diesen Pfad für alle Befehle:
```bash
SKILL_DIR="/pfad/zum/skill"   # <── ersetze durch den Pfad oben
```

---

## Erstkonfiguration (einmalig)

Beim ersten Einsatz prüfe zuerst den Status:

```bash
python "$SKILL_DIR/scripts/setup.py"
```

Falls `.env` fehlt oder keine Agenten aktiv sind, führe Claude durch die Konfiguration:

### API-Keys einrichten

1. Claude liest die Vorlage:
```bash
cat "$SKILL_DIR/.env.example"
```

2. Claude erstellt `.env` aus der Vorlage und fragt den User nach seinen Keys:
```bash
cp "$SKILL_DIR/.env.example" "$SKILL_DIR/.env"
```

3. Claude trägt die Keys direkt in die Datei ein (der User nennt sie im Chat):
```bash
# Claude editiert $SKILL_DIR/.env mit den genannten Keys
# Beispiel für Ollama Cloud:
# OLLAMA_API_KEY=928baa...
```

4. Status nochmals prüfen — sollte jetzt grün sein:
```bash
python "$SKILL_DIR/scripts/setup.py"
```

### Agenten aktivieren/deaktivieren

Direkt in der Konfigurationsdatei:
```bash
cat "$SKILL_DIR/config/agents.json"   # zeigen
# Claude setzt "enabled": true/false für gewünschte Agenten
```

---

## Phase 1: Task klassifizieren

```bash
python "$SKILL_DIR/scripts/task_classifier.py" \
  --task "TASK-BESCHREIBUNG HIER" \
  --config "$SKILL_DIR/config/agents.json" \
  --pretty
```

Das JSON enthält:
- `complexity`: `simple` | `medium` | `complex`
- `delegate`: `true` | `false`
- `recommended_agents`: empfohlene Agenten-IDs
- `recommended_model`: bestes Modell für diesen Task (z.B. `gemma3:4b`)
- `model_reasoning`: Begründung der Modellwahl
- `model_alternatives`: Fallbacks
- `fine_categories`: erkannte Kategorien (z.B. `["code", "documentation"]`)
- `warnings`: Hinweise bei sicherheitsrelevanten Keywords

### Wann delegieren?

**EINFACH → sicher delegieren**
Textformatierung, Übersetzung, Template-Befüllung, Codekommentare / Docstrings,
Changelog aus Commit-Messages, Meeting-Protokoll aus Stichpunkten,
Datums- und Zeitformatierung, einfache Zusammenfassungen.

**MITTEL → delegieren mit anschließender Prüfung**
Unit-Test-Generierung, einfache Code-Reviews, README / API-Dokumentation,
User Stories aus Feature-Briefings, RACI-Matrix-Entwürfe, Meeting-Agenden,
Risiko-Templates befüllen.

**KOMPLEX → Claude direkt**
Architektur- und Technologieentscheidungen, Risikoanalyse und -bewertung,
Stakeholder-Kommunikation, Sicherheits- und Compliance-Prüfungen,
strategische Roadmaps, Change Management, mehrstufiges Debugging.

---

## Phase 2: Delegation ausführen

### Option A: OpenAI-kompatible API (GPT-4o-mini, Gemini Flash, Groq, etc.)

```bash
python "$SKILL_DIR/scripts/call_openai.py" \
  --agent-id gpt-4o-mini \
  --config "$SKILL_DIR/config/agents.json" \
  --prompt "AUFGABE HIER" \
  --output-file /tmp/delegate_result.txt \
  --verbose
```

### Option B: Ollama (Cloud oder lokal) — mit automatischer Modell-Wahl

```bash
bash "$SKILL_DIR/scripts/call_ollama.sh" \
  --prompt "AUFGABE HIER" \
  --model RECOMMENDED_MODEL \
  --output-file /tmp/delegate_result.txt \
  --verbose

# Verfügbare Modelle prüfen:
bash "$SKILL_DIR/scripts/call_ollama.sh" --list-models
```

### Option C: Mehrere Subtasks parallel

```bash
python "$SKILL_DIR/scripts/call_openai.py" \
  --agent-id gpt-4o-mini --prompt "Subtask 1: ..." \
  --output-file /tmp/result_1.txt &

python "$SKILL_DIR/scripts/call_openai.py" \
  --agent-id gpt-4o-mini --prompt "Subtask 2: ..." \
  --output-file /tmp/result_2.txt &

wait
cat /tmp/result_1.txt /tmp/result_2.txt
```

---

## Phase 3: Ergebnis prüfen & konsolidieren

```bash
cat /tmp/delegate_result.txt
# oder bei mehreren:
for f in /tmp/result_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
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

---

## Referenzen

- `references/agent-capabilities.md` — Stärken, Grenzen und Kosten jedes Agenten
- `references/consolidation-patterns.md` — Prüfkriterien und Beispiele nach Aufgabentyp
