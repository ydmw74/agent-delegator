---
name: task-router
description: >
  This skill should be used whenever Claude needs to decide whether a subtask
  can be delegated to a cheaper agent (Ollama, GPT-4o-mini, Gemini Flash,
  opencode CLI) instead of handling it directly.

  Trigger phrases: "delegiere das", "weiterleiten an günstigeres Modell",
  "spare Tokens", "nutze einen anderen Agenten", "schicke das an opencode",
  "lass das Ollama machen", "delegate this subtask", "route to cheaper model".

  Also trigger automatically when Claude breaks down a complex task into
  subtasks and should evaluate which parts can be offloaded.
version: 0.1.0
---

# Task Router

Der Task Router entscheidet, welche Subtasks an günstigere Agenten delegiert
werden und welche Claude direkt bearbeiten soll. Er ist das Herzstück des
Agent Delegator Plugins.

## Kernprinzip

Claude ist das Orchestrierungs-Gehirn. Es delegiert repetitive, klar abgegrenzte
Subtasks und behält komplexes Reasoning, strategische Entscheidungen und die
Konsolidierung der Ergebnisse selbst.

```
Aufgabe
  │
  ▼
[Task Router]  ─── einfach/mittel ──►  [Günstiger Agent]  ──►  Ergebnis
  │                                                                 │
  │ komplex                                                         │
  ▼                                                                 ▼
[Claude direkt]                                          [Result Consolidator]
                                                                    │
                                                                    ▼
                                                          Gesamtergebnis an User
```

## Schritt 1: Task analysieren

Bevor du etwas delegierst, lasse den Classifier laufen:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/task_classifier.py \
  --task "TASK-BESCHREIBUNG HIER" \
  --config "${CLAUDE_PLUGIN_ROOT}/config/agents.json" \
  --pretty
```

Das JSON-Ergebnis enthält:
- `complexity`: `simple` | `medium` | `complex`
- `delegate`: `true` | `false`
- `recommended_agents`: Liste der empfohlenen Agenten-IDs (aus agents.json)
- `recommended_model`: Bestes Ollama-Modell für diesen Task (z.B. `"llama3.2"` oder `"qwen2.5:7b"`)
- `model_reasoning`: Begründung für die Modell-Empfehlung
- `model_alternatives`: Fallback-Modelle falls das primäre nicht verfügbar ist
- `fine_categories`: Erkannte Fein-Kategorien (z.B. `["code", "documentation"]`)
- `reasoning`: Begründung für die Delegation
- `warnings`: Warnhinweise (z.B. bei Sicherheits-Keywords)

**Modell-Auswahl**: Wenn `recommended_model` gesetzt ist, verwende dieses Modell beim
Aufruf von `call_ollama.sh` oder wenn du das Modell bei `call_openai.py` manuell
überschreiben willst. Das ist besonders nützlich für Ollama, da dort viele Modelle
verfügbar sind und die Wahl des Modells die Qualität stark beeinflusst.

## Schritt 2: Klassifizierungs-Rubrik

Wenn du die Entscheidung manuell treffen oder überschreiben willst:

### EINFACH → Delegieren (sicher)
Alle diese Tasks sind klar abgegrenzt und liefern bei günstigen Modellen
gleichwertige Ergebnisse wie Claude:

- **Textformatierung**: Markdown, Tabellen, Listen, Überschriften vereinheitlichen
- **Übersetzung**: Dokumente oder Texte übersetzen
- **Template-Befüllung**: Vorlagen mit gegebenen Daten ausfüllen
- **Regex/Parsing**: Daten aus strukturierten Texten extrahieren
- **Einfache Zusammenfassungen**: Wenn der Inhalt vollständig mitgegeben wird
- **Codekommentare**: Docstrings und Inline-Kommentare für bekannten Code
- **Changelog-Generierung**: Aus Commit-Messages oder Diff-Listen
- **Statusbericht formatieren**: Rohdaten in ein PM-Standardformat bringen
- **Meeting-Protokoll strukturieren**: Stichpunkte in Fließtext umwandeln
- **Datums- und Zeitformatierung**: Datumsangaben konvertieren oder harmonisieren

### MITTEL → Delegieren (mit Prüfung)
Diese Tasks können gute günstige Modelle erledigen, aber Claude sollte das
Ergebnis prüfen bevor es an den User geht:

- **Unit-Test-Generierung**: Für klar spezifizierten, beigegebenen Code
- **Code-Review** einfacher Dateien: Style, offensichtliche Bugs
- **README und API-Dokumentation** schreiben: Für bekannten Code
- **User Stories**: Aus einem Feature-Briefing generieren
- **RACI-Matrix-Entwurf**: Aus einer Projektbeschreibung
- **Meeting-Agenda**: Aus vorgegebenen Themen strukturieren
- **Risiko-Template ausfüllen**: Wenn die Risiken bereits bekannt sind

### KOMPLEX → Claude direkt
Diese Tasks nie delegieren — sie brauchen Claudes tiefes Reasoning:

- **Architektur- und Technologieentscheidungen**
- **Risikoanalyse und -bewertung** (nicht nur Template-Befüllung)
- **Stakeholder-Kommunikation** auf Führungsebene
- **Sicherheits- und Compliance-Prüfungen**
- **Strategische Roadmaps und Konzepte**
- **Change Management** und Eskalationsmanagement
- **Mehrstufige Debugging-Diagnose**
- **Kreative Problemlösung** und Novel-Ansätze

## Schritt 3: Delegation ausführen

### Option A: OpenAI-kompatible API (GPT-4o-mini, Gemini Flash, Groq, etc.)

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id gpt-4o-mini \
  --config "${CLAUDE_PLUGIN_ROOT}/config/agents.json" \
  --prompt "AUFGABE HIER EINFÜGEN" \
  --output-file /tmp/delegate_result.txt \
  --verbose
```

Dann Ergebnis lesen:
```bash
cat /tmp/delegate_result.txt
```

### Option B: Ollama (lokal oder Cloud) — mit automatischer Modell-Wahl

Verwende das `recommended_model` aus dem Classifier-Ergebnis:

```bash
# RECOMMENDED_MODEL aus dem Classifier-JSON übernehmen (z.B. "qwen2.5:7b")
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh \
  --prompt "AUFGABE HIER EINFÜGEN" \
  --model RECOMMENDED_MODEL \
  --output-file /tmp/delegate_result.txt \
  --verbose
```

Wenn `recommended_model` nicht verfügbar ist, nutze die `model_alternatives` als Fallback.
Verfügbare Modelle prüfen:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh --list-models
```

**Typische Modell-Zuordnung** (laut Classifier):
- Textformatierung, Übersetzung, Zusammenfassungen → `llama3.2` (schnell, kostengünstig)
- Docstrings, einfache Code-Tasks → `qwen2.5:7b` (besser für Code)
- Unit Tests → `qwen2.5:7b`
- Refactoring, komplexere Code-Docs → `qwen2.5:14b` (höhere Qualität)
- User Stories, strukturierte Dokumente → `mistral`

### Option C: opencode CLI (Code-Tasks)

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_opencode.sh \
  --prompt "AUFGABE HIER EINFÜGEN" \
  --model claude-haiku-4-5-20251001 \
  --output-file /tmp/delegate_result.txt
```

## Schritt 4: Parallele Delegation (mehrere Subtasks gleichzeitig)

Wenn du mehrere Subtasks parallel delegieren willst, starte mehrere Prozesse
und warte auf alle:

```bash
# Alle parallel starten
python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id gpt-4o-mini \
  --prompt "Subtask 1: ..." \
  --output-file /tmp/result_1.txt &

python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id gpt-4o-mini \
  --prompt "Subtask 2: ..." \
  --output-file /tmp/result_2.txt &

# Auf alle warten
wait

# Ergebnisse zusammenführen
cat /tmp/result_1.txt
cat /tmp/result_2.txt
```

## Schritt 5: Ergebnis prüfen

Nach der Delegation immer prüfen:
- Ist das Ergebnis vollständig und sinnvoll?
- Gibt es offensichtliche Fehler oder Halluzinationen?
- Passt das Format zur Anforderung?

Bei Mängeln: Entweder den Subtask mit verbessertem Prompt erneut delegieren
oder direkt von Claude bearbeiten lassen.

Danach: `result-consolidator` Skill für die Zusammenführung verwenden.

## Setup-Status prüfen

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
```

## Referenzen

- `references/complexity-rubric.md` — Detaillierte Entscheidungstabelle
- `references/agent-capabilities.md` — Stärken und Grenzen jedes Agenten
