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

## Phase 1: Task klassifizieren

Starte immer mit dem Classifier — er empfiehlt Komplexität, Agent und Modell:

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/task_classifier.py \
  --task "TASK-BESCHREIBUNG HIER" \
  --config "${CLAUDE_PLUGIN_ROOT}/config/agents.json" \
  --pretty
```

Das JSON enthält:
- `complexity`: `simple` | `medium` | `complex`
- `delegate`: `true` | `false`
- `recommended_agents`: empfohlene Agenten-IDs aus agents.json
- `recommended_model`: bestes Modell für diesen Task (z.B. `gemma3:4b`)
- `model_reasoning`: Begründung der Modellwahl
- `model_alternatives`: Fallbacks falls Primärmodell nicht verfügbar
- `fine_categories`: erkannte Kategorien (z.B. `["code", "documentation"]`)
- `warnings`: Hinweise bei sicherheitsrelevanten Keywords

### Wann delegieren?

**EINFACH → sicher delegieren**
Klar abgegrenzte Tasks, bei denen günstige Modelle gleichwertige Ergebnisse liefern:
Textformatierung, Übersetzung, Template-Befüllung, Codekommentare / Docstrings,
Changelog aus Commit-Messages, Meeting-Protokoll aus Stichpunkten,
Datums- und Zeitformatierung, einfache Zusammenfassungen.

**MITTEL → delegieren mit anschließender Prüfung**
Günstige Modelle können das — aber Claude sollte das Ergebnis vor der Ausgabe prüfen:
Unit-Test-Generierung, einfache Code-Reviews, README / API-Dokumentation,
User Stories aus Feature-Briefings, RACI-Matrix-Entwürfe, Meeting-Agenden,
Risiko-Templates befüllen.

**KOMPLEX → Claude direkt bearbeiten**
Nie delegieren — diese Tasks brauchen tiefes Reasoning:
Architektur- und Technologieentscheidungen, Risikoanalyse und -bewertung,
Stakeholder-Kommunikation auf Führungsebene, Sicherheits- und Compliance-Prüfungen,
strategische Roadmaps, Change Management, mehrstufiges Debugging, kreative Problemlösung.

---

## Phase 2: Delegation ausführen

### Option A: OpenAI-kompatible API (GPT-4o-mini, Gemini Flash, Groq, etc.)

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id gpt-4o-mini \
  --config "${CLAUDE_PLUGIN_ROOT}/config/agents.json" \
  --prompt "AUFGABE HIER" \
  --output-file /tmp/delegate_result.txt \
  --verbose
```

### Option B: Ollama (lokal oder Cloud) — mit automatischer Modell-Wahl

Verwende `recommended_model` aus dem Classifier-Ergebnis:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh \
  --prompt "AUFGABE HIER" \
  --model RECOMMENDED_MODEL \
  --output-file /tmp/delegate_result.txt \
  --verbose
```

Verfügbare Modelle prüfen:
```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/call_ollama.sh --list-models
```

### Option C: Mehrere Subtasks parallel

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id gpt-4o-mini --prompt "Subtask 1: ..." \
  --output-file /tmp/result_1.txt &

python ${CLAUDE_PLUGIN_ROOT}/scripts/call_openai.py \
  --agent-id gpt-4o-mini --prompt "Subtask 2: ..." \
  --output-file /tmp/result_2.txt &

wait  # auf alle warten

cat /tmp/result_1.txt /tmp/result_2.txt
```

---

## Phase 3: Ergebnis prüfen & konsolidieren

Lies das Ergebnis:
```bash
cat /tmp/delegate_result.txt
# oder bei mehreren:
for f in /tmp/result_*.txt; do echo "=== $f ==="; cat "$f"; echo; done
```

Beurteile das Ergebnis anhand von vier Kriterien:

**Vollständigkeit** — Wurde die Aufgabe vollständig erledigt? Fehlen explizit angeforderte Teile?

**Korrektheit** — Bei Text: Struktur korrekt? Bei Code: syntaktisch und logisch korrekt? Bei Übersetzungen: Bedeutung beibehalten?

**Halluzinations-Check** — Wurden Fakten erfunden, die nicht im Input standen? Wurden Zahlen, Namen und Daten korrekt übertragen?

**Format-Konformität** — Stimmt das Ausgabeformat mit der Anforderung überein?

### Konsolidierungsmuster

**Muster A — Direkt übernehmen**: Ergebnis ist vollständig und korrekt, ggf. mit geringen Korrekturen.

**Muster B — Korrigieren und integrieren**: Ergebnis ist größtenteils gut, aber mit Lücken. Fehlende Felder ergänzen, Format korrigieren, halluzinierte Fakten durch korrekte Werte ersetzen.

**Muster C — Neu bearbeiten**: Ergebnis ist unbrauchbar (>30% falsch, fundamental falsches Format, sicherheitsrelevante Fehler). Claude bearbeitet den Task direkt.

**Muster D — Mehrere Subtasks zusammenführen**: Redundanzen entfernen, Widersprüche auflösen (im Zweifel konservativere Version), Übergangsformulierungen hinzufügen, Struktur harmonisieren.

### Transparenz gegenüber dem User

Kurz erwähnen wenn Delegation stattfand — besonders bei Korrekturen:
- *"Ich habe einen günstigeren Agenten für die Formatierung eingesetzt und das Ergebnis geprüft."*
- *"Die Protokollstruktur wurde von einem Hilfsmodell erstellt; ich habe zwei Format-Fehler korrigiert."*

Nicht erwähnen wenn das Ergebnis direkt und ohne Korrekturen übernehmbar war.

---

## Setup & Referenzen

Setup-Status prüfen:
```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/setup.py
```

Referenzdokumente:
- `references/agent-capabilities.md` — Stärken, Grenzen und Kosten jedes Agenten
- `references/consolidation-patterns.md` — Detaillierte Prüfkriterien und Beispiele nach Aufgabentyp
